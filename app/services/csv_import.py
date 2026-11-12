import csv
import io
from sqlalchemy import select
from pydantic import ValidationError
from ..models import Student, AcademicResult, Debt, WarningHistory, Classroom, User, Semester, Course
from ..schemas import StudentInput,ResultInput, Strict
from pydantic import Field

class DebtInput(Strict):
    student_id:str
    semester_id:int
    course_id:str
class WarningInput(Strict):
    student_id:str
    semester_id:int
    warned:bool
KINDS={'students':(StudentInput,Student,('id',)), 'results':(ResultInput,AcademicResult,('student_id','semester_id')),
       'debts':(DebtInput,Debt,('student_id','semester_id','course_id')), 'warnings':(WarningInput,WarningHistory,('student_id','semester_id'))}
HEADERS={k:list(schema.model_fields) for k,(schema,_,_) in KINDS.items()}
def safe_cell(value):
    text=str(value) if value is not None else ''
    return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) else text
def csv_bytes(headers,rows):
    out=io.StringIO(newline='');w=csv.writer(out);w.writerow(headers)
    w.writerows([[safe_cell(v) for v in r] for r in rows])
    return ('\ufeff'+out.getvalue()).encode('utf-8')
def parse_file(raw,kind):
    if kind not in KINDS: raise ValueError('Loại mẫu không hợp lệ')
    if len(raw)>2*1024*1024: raise ValueError('Tệp vượt quá 2 MB')
    try: text=raw.decode('utf-8-sig')
    except UnicodeDecodeError: raise ValueError('Hãy lưu tệp UTF-8 hoặc UTF-8 BOM')
    delimiter=';' if text.splitlines() and text.splitlines()[0].count(';')>text.splitlines()[0].count(',') else ','
    reader=csv.DictReader(io.StringIO(text,newline=''),delimiter=delimiter)
    fields=[name.strip() for name in reader.fieldnames or []]
    if len(fields)!=len(set(fields)): raise ValueError('Tiêu đề có cột trùng nhau; giữ mỗi cột đúng một lần theo mẫu.')
    missing=set(HEADERS[kind])-set(fields);extra=set(fields)-set(HEADERS[kind])
    if missing or extra:
        raise ValueError(('Thiếu cột: '+', '.join(sorted(missing))+'. ' if missing else '')+('Cột không hỗ trợ: '+', '.join(sorted(extra))+'. ' if extra else '')+'Tải lại mẫu của đúng loại dữ liệu.')
    reader.fieldnames=fields
    rows=list(reader)
    for line,row in enumerate(rows,2):
        if None in row or any(value is None for value in row.values()): raise ValueError(f'Dòng {line}: số ô không khớp tiêu đề. Kiểm tra dấu phân cách và ngoặc kép quanh nội dung có dấu phẩy.')
    if not 1<=len(rows)<=5000: raise ValueError('Tệp cần 1–5000 dòng dữ liệu')
    return rows
def validate_rows(db,kind,rows,mode):
    if kind not in KINDS or mode not in ('skip','update'): raise ValueError('Loại dữ liệu/chế độ không hợp lệ')
    schema,model,keys=KINDS[kind];clean=[];errors=[];seen=set();existing=0
    for line,row in enumerate(rows,2):
        try:
            if None in row: raise ValueError('Số ô không khớp tiêu đề; kiểm tra dấu phân cách và ngoặc kép.')
            row={key:value.strip() if isinstance(value,str) else value for key,value in row.items()}
            if kind=='warnings' and str(row.get('warned','')).strip().casefold() not in ('true','false','1','0'):
                raise ValueError('warned: dùng true (có cảnh báo) hoặc false (đã xác nhận không cảnh báo).')
            data={k:(None if v=='' and schema.model_fields[k].default is None else v) for k,v in row.items()}
            obj=schema.model_validate(data);data=obj.model_dump()
            identity=tuple(data[k] for k in keys)
            if identity in seen: raise ValueError('Trùng khóa trong tệp; xóa dòng lặp')
            seen.add(identity)
            if kind=='students':
                classroom=db.get(Classroom,data['class_id'])
                if not classroom: raise ValueError('class_id: lớp chưa tồn tại; chọn mã trong danh mục lớp bên dưới.')
                if data['id'].isdigit() and len(data['id'])>=8 and classroom.cohort_id in ('K23','K24','K25') and not data['id'].startswith(classroom.cohort_id[1:]):
                    raise ValueError('id: mã sinh viên phải bắt đầu bằng '+classroom.cohort_id[1:]+' theo khóa của lớp đã chọn.')
                u=db.get(User,data['advisor_id'])
                if not u or not u.active or u.role!='advisor': raise ValueError('advisor_id: cần tài khoản cố vấn hoạt động')
            else:
                if not db.get(Student,data['student_id']): raise ValueError('student_id: chưa tồn tại; nhập sinh viên trước')
                if not db.get(Semester,data['semester_id']): raise ValueError('semester_id: học kỳ chưa tồn tại')
            if kind=='debts' and not db.get(Course,data['course_id']): raise ValueError('course_id: học phần chưa tồn tại')
            found=db.scalars(select(model).filter_by(**{k:data[k] for k in keys})).first()
            if found: existing+=1
            clean.append((data,found))
        except ValidationError as e:
            messages={'float_parsing':'Cần là số; dùng dấu chấm cho phần thập phân, ví dụ 2.75.','int_parsing':'Cần là số nguyên, ví dụ 20.','bool_parsing':'Dùng true hoặc false.','missing':'Ô bắt buộc chưa có dữ liệu.','string_too_short':'Nội dung quá ngắn.','literal_error':'Trạng thái chỉ nhận completed hoặc leave.'}
            for er in e.errors(): errors.append({'line':line,'column':'.'.join(map(str,er['loc'])) or 'row','message':messages.get(er['type'],er['msg'].removeprefix('Value error, '))+' Kiểm tra hướng dẫn cột và nhập lại.'})
        except (ValueError,TypeError,KeyError) as e:
            message=str(e);prefix=message.split(':',1)[0]
            errors.append({'line':line,'column':prefix if prefix in schema.model_fields else ', '.join(keys),'message':message})
    return clean,errors,existing
def apply_rows(db,kind,rows,mode):
    clean,errors,existing=validate_rows(db,kind,rows,mode)
    if errors: return errors,0
    model=KINDS[kind][1];count=0
    for data,found in clean:
        if found:
            if mode=='skip': continue
            for k,v in data.items(): setattr(found,k,v)
        else: db.add(model(**data))
        count+=1
    db.flush()
    return [],count
