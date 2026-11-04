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
    reader=csv.DictReader(io.StringIO(text,newline=''))
    if reader.fieldnames!=HEADERS[kind]: raise ValueError('Cột không đúng thứ tự mẫu: '+', '.join(HEADERS[kind]))
    rows=list(reader)
    if not 1<=len(rows)<=5000: raise ValueError('Tệp cần 1–5000 dòng dữ liệu')
    return rows
def validate_rows(db,kind,rows,mode):
    if kind not in KINDS or mode not in ('skip','update'): raise ValueError('Loại dữ liệu/chế độ không hợp lệ')
    schema,model,keys=KINDS[kind];clean=[];errors=[];seen=set();existing=0
    for line,row in enumerate(rows,2):
        try:
            data={k:(None if v=='' and schema.model_fields[k].default is None else v) for k,v in row.items()}
            obj=schema.model_validate(data);data=obj.model_dump()
            identity=tuple(data[k] for k in keys)
            if identity in seen: raise ValueError('Trùng khóa trong tệp; xóa dòng lặp')
            seen.add(identity)
            if kind=='students':
                if not db.get(Classroom,data['class_id']): raise ValueError('class_id: lớp chưa tồn tại; tạo lớp trước')
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
            for er in e.errors(): errors.append({'line':line,'column':'.'.join(map(str,er['loc'])) or 'row','message':er['msg']+'; sửa theo mẫu và thử lại'})
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
