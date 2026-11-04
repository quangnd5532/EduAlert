"""Run only with EDUALERT_DEMO=true and an explicit demo password."""
import os
from copy import deepcopy
from datetime import date,timedelta
from sqlalchemy import select
from .db import SessionLocal
from .models import *
from .security import hasher
from .services.assessment import DEFAULT
from .services.data import assessment
from .demo_data import SEMESTERS, academic_data

def seed(db,password):
    if db.scalar(select(User).where(User.username=='admin')):
        return False
    if db.scalar(select(Student.id).limit(1)):
        raise RuntimeError('Chỉ seed vào cơ sở dữ liệu trống; không trộn dữ liệu thật.')
    if not 10<=len(password)<=128: raise ValueError('Mật khẩu demo cần 10–128 ký tự')
    db.add_all([User(id=1,username='admin',name='Quản trị Demo',role='admin',password_hash=hasher.hash(password)),
                User(id=2,username='advisor1',name='Cố vấn Demo A',role='advisor',password_hash=hasher.hash(password)),
                User(id=3,username='advisor2',name='Cố vấn Demo B',role='advisor',password_hash=hasher.hash(password))]);db.flush()
    db.add_all([Major(id='CNTT',name='Công nghệ thông tin'),Major(id='QTKD',name='Quản trị kinh doanh'),Cohort(id='K23',name='Khóa 2023'),Cohort(id='K22',name='Khóa 2022')]);db.flush()
    for i,(major,cohort) in enumerate([('CNTT','K23'),('CNTT','K22'),('QTKD','K23'),('QTKD','K22')],1):
        db.add(Classroom(id=f'L{i}',name=f'{major} {cohort}',major_id=major,cohort_id=cohort))
    for row in SEMESTERS: db.add(Semester(**row))
    db.add_all([Course(id='HP01',name='Toán ứng dụng (giả lập)',credits=3),Course(id='HP02',name='Kỹ năng học thuật (giả lập)',credits=2)])
    c=ConfigVersion(name='Bộ quy tắc minh họa phục vụ demo',active=True,activated_at=now(),payload=deepcopy(DEFAULT));db.add(c);db.flush()
    given=['An','Bình','Chi','Dũng','Giang','Hà','Khôi','Lan','Minh','Ngọc']
    for n in range(1,61):
        sid=f'{n:06}';class_id=f'L{(n-1)%4+1}';advisor=2 if (n-1)%4<2 else 3
        s=Student(id=sid,name=f'Sinh viên mô phỏng {n:02} — {given[(n-1)%10]}',class_id=class_id,advisor_id=advisor,admission_score=22+(n%6),admission_scale=30,admission_method='THPT giả lập');db.add(s);db.flush()
        results,warnings,debts=academic_data(n)
        db.add_all([AcademicResult(**r) for r in results])
        db.add_all([WarningHistory(**r) for r in warnings])
        db.add_all([Debt(**r) for r in debts])
        db.flush()
    for s in db.scalars(select(Student)):
        for seq in range(1,7): assessment(db,s,seq,save=True)
    for sid,term,goal,status,delta in [('000006',4,'Ổn định kế hoạch học và tiến độ tích lũy','Hoàn tất',-60),('000008',6,'Rà soát các học phần cần hỗ trợ','Đang hỗ trợ',-3),('000005',6,'Trao đổi kế hoạch học kỳ tiếp theo','Chưa xử lý',3)]:
        e=db.scalars(select(Evaluation).where(Evaluation.student_id==sid,Evaluation.semester_id==term)).first()
        s=db.get(Student,sid);p=Intervention(student_id=sid,evaluation_id=e.id,owner_id=s.advisor_id,goal=goal,action='Hẹn tư vấn; rà soát môn nợ; lập lịch học hàng tuần',status=status,due_date=date.today()+timedelta(days=delta));db.add(p);db.flush()
        db.add(Followup(intervention_id=p.id,author_id=s.advisor_id,note='Ghi chú giả lập: đã trao đổi mục tiêu và thống nhất buổi theo dõi.'))
    db.add(Audit(user_id=1,action='seed_demo',detail={'students':60,'synthetic':True}));db.commit();return True
def main():
    if os.getenv('EDUALERT_DEMO')!='true': raise RuntimeError('Chỉ chạy seed khi EDUALERT_DEMO=true')
    password=os.getenv('EDUALERT_DEMO_PASSWORD','')
    with SessionLocal() as db: print('Đã tạo 60 hồ sơ giả lập.' if seed(db,password) else 'Dữ liệu demo đã tồn tại; không nhân đôi.')
if __name__=='__main__': main()
