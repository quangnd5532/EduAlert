import csv
import io
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from . import db
from .models import Student, Term, Settings, Intervention
from .risk import evaluate

ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app):
    db.initialize()
    yield


app = FastAPI(title='EduAlert API', version='1.0.0', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


@app.get('/')
def index():
    return FileResponse(ROOT / 'static' / 'index.html')


def student_result(conn, row, settings):
    student = json.loads(row['payload'])
    terms = db.get_terms(conn, student['id'])
    return {**student, 'terms': terms, 'latest': terms[-1] if terms else None,
            'risk': evaluate(terms, settings, student['cohort'])}


@app.get('/api/students')
def students():
    with db.connect() as conn:
        settings = db.load_settings(conn)
        return [student_result(conn, row, settings) for row in conn.execute('SELECT * FROM students ORDER BY id')]


@app.get('/api/students/{student_id}')
def get_student(student_id: str):
    with db.connect() as conn:
        row = conn.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Không tìm thấy sinh viên')
        return student_result(conn, row, db.load_settings(conn))


@app.post('/api/students', status_code=201)
def create_student(student: Student):
    with db.connect() as conn:
        if conn.execute('SELECT 1 FROM students WHERE id=?', (student.id,)).fetchone():
            raise HTTPException(409, 'Mã sinh viên đã tồn tại')
        conn.execute('INSERT INTO students VALUES (?,?)', (student.id, student.model_dump_json()))
    return student


@app.put('/api/students/{student_id}/terms')
def save_term(student_id: str, term: Term):
    with db.connect() as conn:
        if not conn.execute('SELECT 1 FROM students WHERE id=?', (student_id,)).fetchone():
            raise HTTPException(404, 'Không tìm thấy sinh viên')
        conn.execute('INSERT INTO terms VALUES (?,?,?,?) ON CONFLICT(student_id,year,semester) DO UPDATE SET payload=excluded.payload',
                     (student_id, term.year, term.semester, term.model_dump_json()))
    return term


@app.get('/api/settings')
def get_settings():
    with db.connect() as conn:
        return db.load_settings(conn)


@app.put('/api/settings')
def update_settings(settings: Settings):
    with db.connect() as conn:
        conn.execute('UPDATE settings SET payload=? WHERE id=1', (settings.model_dump_json(),))
    return settings


@app.get('/api/interventions')
def interventions():
    with db.connect() as conn:
        return [{**json.loads(row['payload']), 'id': row['id'], 'created_at': row['created_at']}
                for row in conn.execute('SELECT * FROM interventions ORDER BY id DESC')]


def validate_student(conn, sid):
    if not conn.execute('SELECT 1 FROM students WHERE id=?', (sid,)).fetchone():
        raise HTTPException(404, 'Không tìm thấy sinh viên')


@app.post('/api/interventions', status_code=201)
def create_intervention(item: Intervention):
    with db.connect() as conn:
        validate_student(conn, item.student_id)
        cursor = conn.execute('INSERT INTO interventions(student_id,payload,created_at) VALUES (?,?,?)',
                              (item.student_id, item.model_dump_json(), datetime.now(timezone.utc).isoformat()))
        return {**item.model_dump(), 'id': cursor.lastrowid}


@app.put('/api/interventions/{item_id}')
def update_intervention(item_id: int, item: Intervention):
    with db.connect() as conn:
        row = conn.execute('SELECT student_id FROM interventions WHERE id=?', (item_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Không tìm thấy hồ sơ can thiệp')
        if item.student_id != row[0]:
            raise HTTPException(422, 'Không được đổi sinh viên của hồ sơ can thiệp')
        conn.execute('UPDATE interventions SET payload=? WHERE id=?', (item.model_dump_json(), item_id))
    return item


CSV_FIELDS = list(Student.model_fields) + list(Term.model_fields)


def csv_response(rows, fields, filename):
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({key: ("'" + str(value) if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')) else value) for key, value in row.items()})
    return Response(buffer.getvalue().encode('utf-8-sig'), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@app.get('/api/import/template')
def template():
    return csv_response([{'id': '2351010999', 'name': 'Sinh viên mẫu', 'class_name': 'CNTT23A', 'major': 'Công nghệ thông tin', 'cohort': '2023', 'advisor': 'Nguyễn Thu Hà', 'admission_score': 25, 'admission_scale': 30, 'admission_method': 'THPT', 'year': 2025, 'semester': 1, 'gpa': 2.5, 'cumulative_gpa': 2.6, 'registered': 18, 'passed': 15, 'failed': 3, 'debt': 1, 'conduct': 80, 'previous_warnings': 0}], CSV_FIELDS, 'edualert-mau.csv')


@app.post('/api/import')
async def import_csv(request: Request):
    # Raw CSV avoids multipart dependencies. Read with a strict size bound.
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 2_000_000:
            raise HTTPException(413, 'Tệp tối đa 2 MB')
    try:
        content = body.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise HTTPException(422, 'Hãy lưu CSV với mã hóa UTF-8')
    reader = csv.DictReader(io.StringIO(content, newline=''))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not set(CSV_FIELDS).issubset(reader.fieldnames):
        raise HTTPException(422, 'Cột CSV không đúng mẫu. Tải mẫu và giữ nguyên hàng tiêu đề.')
    parsed, errors, seen, identities = [], [], set(), {}
    try:
        for line, row in enumerate(reader, 2):
            if line > 5001:
                raise HTTPException(422, 'Tối đa 5.000 dòng mỗi lần nhập')
            try:
                values = {k: v.strip() for k, v in row.items() if k in CSV_FIELDS and v is not None}
                values = {k: v for k, v in values.items() if v != ''}
                student = Student(**{k: v for k, v in values.items() if k in Student.model_fields})
                term = Term(**{k: v for k, v in values.items() if k in Term.model_fields})
                key = (student.id, term.year, term.semester)
                if key in seen:
                    raise ValueError('Trùng mã sinh viên và học kỳ trong tệp')
                if student.id in identities and identities[student.id] != student.model_dump():
                    raise ValueError('Thông tin sinh viên không nhất quán giữa các dòng')
                seen.add(key)
                identities[student.id] = student.model_dump()
                parsed.append((student, term))
            except (ValidationError, ValueError) as exc:
                errors.append({'line': line, 'message': str(exc)[:700]})
    except csv.Error:
        raise HTTPException(422, 'Cấu trúc CSV không hợp lệ')
    if errors:
        raise HTTPException(422, {'message': 'Chưa lưu dữ liệu. Sửa các dòng lỗi rồi nhập lại.', 'errors': errors[:30]})
    if not parsed:
        raise HTTPException(422, 'Tệp không có dữ liệu')
    with db.connect() as conn:
        for student, term in parsed:
            conn.execute('INSERT INTO students VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (student.id, student.model_dump_json()))
            conn.execute('INSERT INTO terms VALUES (?,?,?,?) ON CONFLICT(student_id,year,semester) DO UPDATE SET payload=excluded.payload',
                         (student.id, term.year, term.semester, term.model_dump_json()))
    return {'rows': len(parsed), 'students': len(identities)}


@app.get('/api/export')
def export_report():
    levels = {'high': 'Nguy cơ cao', 'attention': 'Cần chú ý', 'normal': 'Bình thường', 'no_data': 'Chưa có dữ liệu', 'out_of_scope': 'Ngoài phạm vi'}
    rows = []
    for s in students():
        rows.append({'mssv': s['id'], 'ho_ten': s['name'], 'lop': s['class_name'], 'nganh': s['major'], 'khoa': s['cohort'], 'gpa': (s['latest'] or {}).get('gpa', ''), 'diem_nguy_co': s['risk']['score'], 'muc_nguy_co': levels[s['risk']['level']], 'dieu_kien_quy_che': '; '.join(s['risk']['academic']), 'ly_do': '; '.join(r['text'] for r in s['risk']['reasons'])})
    return csv_response(rows, ['mssv', 'ho_ten', 'lop', 'nganh', 'khoa', 'gpa', 'diem_nguy_co', 'muc_nguy_co', 'dieu_kien_quy_che', 'ly_do'], 'edualert-bao-cao.csv')


@app.get('/api/export/interventions')
def export_interventions():
    return csv_response(interventions(), ['id', 'student_id', 'advisor', 'note', 'action', 'due_date', 'status', 'outcome', 'created_at'], 'edualert-can-thiep.csv')


@app.post('/api/demo')
def demo():
    if not db.seed_demo():
        raise HTTPException(409, 'Chỉ tạo dữ liệu minh họa khi danh sách sinh viên đang trống')
    return {'message': 'Đã tạo 24 hồ sơ sinh viên minh họa'}
