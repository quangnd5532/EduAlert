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
from .demo_catalog import SEMESTERS,detailed_academics,student_profile,student_id,course_catalog,CLASSES

def seed(db,password):
    if db.scalar(select(User).where(User.username=='admin')):
        return False
    if db.scalar(select(Student.id).limit(1)):
        raise RuntimeError('Chỉ seed vào cơ sở dữ liệu trống; không trộn dữ liệu thật.')
    if not 10<=len(password)<=128: raise ValueError('Mật khẩu demo cần 10–128 ký tự')
    demo_hash=hasher.hash(password)
    db.add_all([User(id=1,username='admin',name='Quản trị học vụ',role='admin',password_hash=demo_hash),
                User(id=2,username='advisor1',name='Trần Hải Nam',role='advisor',password_hash=hasher.hash(password)),
                User(id=3,username='advisor2',name='Phạm Thu Hương',role='advisor',password_hash=hasher.hash(password))]);db.flush()
    db.add_all([Major(id='CNTT',name='Công nghệ thông tin'),Major(id='QTKD',name='Quản trị kinh doanh')])
    db.add_all([Cohort(id=f'K{year}',name=f'Khóa 20{year}') for year in (23,24,25)]);db.flush()
    for cid,(name,major,cohort) in CLASSES.items():
        db.add(Classroom(id=cid,name=name,major_id=major,cohort_id=cohort))
    for row in SEMESTERS: db.add(Semester(**row))
    db.add_all([Course(id='HP01',name='Toán ứng dụng (giả lập)',credits=3),Course(id='HP02',name='Kỹ năng học thuật (giả lập)',credits=2)])
    db.add_all([Course(**row) for row in course_catalog()])
    c=ConfigVersion(name='Đánh giá học tập chung',active=True,activated_at=now(),payload=deepcopy(DEFAULT));db.add(c)
    from .services.configuration import add_examples
    add_examples(db);db.flush()
    for n in range(1,61):
        sid=student_id(n)
        s=Student(**student_profile(n));db.add(s);db.flush()
        login_user=User(username='student' if n==5 else 'sv'+sid,name=s.name,password_hash=demo_hash,role='student',active=True)
        db.add(login_user);db.flush();db.add(StudentAccount(user_id=login_user.id,student_id=sid))
        results,warnings,debts,grades=detailed_academics(n)
        db.add_all([AcademicResult(**r) for r in results])
        db.add_all([WarningHistory(**r) for r in warnings])
        db.add_all([Debt(**r) for r in debts])
        db.add_all([CourseResult(**r) for r in grades])
        db.flush()
    for s in db.scalars(select(Student)):
        for row in db.scalars(select(AcademicResult).where(AcademicResult.student_id==s.id)): assessment(db,s,row.semester_id,save=True)
    for number,term,goal,status,delta in [(6,4,'Ổn định kế hoạch học và tiến độ tích lũy','Hoàn tất',-60),(8,6,'Rà soát các học phần cần hỗ trợ','Đang hỗ trợ',-3),(5,6,'Trao đổi kế hoạch học kỳ tiếp theo','Chưa xử lý',3)]:
        sid=student_id(number)
        e=db.scalars(select(Evaluation).where(Evaluation.student_id==sid,Evaluation.semester_id==term)).first()
        s=db.get(Student,sid);p=Intervention(student_id=sid,evaluation_id=e.id,owner_id=s.advisor_id,goal=goal,action='Hẹn tư vấn; rà soát môn nợ; lập lịch học hàng tuần',status=status,due_date=date.today()+timedelta(days=delta));db.add(p);db.flush()
        db.add(Followup(intervention_id=p.id,author_id=s.advisor_id,note='Ghi chú giả lập: đã trao đổi mục tiêu và thống nhất buổi theo dõi.'))
    db.add(Audit(user_id=1,action='seed_demo',detail={'students':60,'synthetic':True}))
    db.add(Audit(user_id=1,action='demo_upgrade_v2',detail={'profiles':60,'synthetic':True}))
    db.add(Audit(user_id=1,action='demo_upgrade_v3',detail={'profiles':60,'synthetic':True}));db.commit();return True
def main():
    if os.getenv('EDUALERT_DEMO')!='true': raise RuntimeError('Chỉ chạy seed khi EDUALERT_DEMO=true')
    password=os.getenv('EDUALERT_DEMO_PASSWORD','')
    with SessionLocal() as db:
        created=seed(db,password)
        database_path=db.bind.url.database
    if created: print('Đã tạo 60 hồ sơ, bảng điểm học phần và tài khoản sinh viên.')
    else:
        from .refresh_demo import refresh_database
        import json
        print(json.dumps(refresh_database(database_path),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
