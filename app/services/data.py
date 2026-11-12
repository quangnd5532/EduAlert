from datetime import date
import re
from fastapi import HTTPException
from sqlalchemy import select
from ..models import Student, StudentAccount, Classroom, Semester, AcademicResult, WarningHistory, ConfigVersion, Evaluation, Intervention, Debt, Course, Audit, now
from .assessment import evaluate
from .sorting import SORT_OPTIONS,sort_students

def asdict(obj):
    return {c.name:getattr(obj,c.name) for c in obj.__table__.columns}
def audit(db,user,action,detail):
    db.add(Audit(user_id=user.id if user else None,action=action,detail=detail))
def select_config(db,student):
    cls=db.get(Classroom,student.class_id)
    candidates=[c for c in db.scalars(select(ConfigVersion).where(ConfigVersion.active==True))
                if (not c.major_id or c.major_id==cls.major_id) and (not c.cohort_id or c.cohort_id==cls.cohort_id)]
    # Exact major+cohort > major > cohort > global. No equal-scope active duplicates.
    return max(candidates,key=lambda c:(2*bool(c.major_id)+bool(c.cohort_id),c.id),default=None)
def inputs(db,sid):
    semesters=[asdict(s) for s in db.scalars(select(Semester).order_by(Semester.sequence))]
    student=db.get(Student,sid)
    classroom=db.get(Classroom,student.class_id) if student else None
    # Admission-year cohorts must never require records from before enrollment.
    match=re.fullmatch(r'K(\d{2})',classroom.cohort_id) if classroom else None
    if match:
        year='20'+match[1]
        start=next((s['sequence'] for s in semesters if s['kind']=='regular' and re.search(r'20\d{2}',s['name']) and re.search(r'20\d{2}',s['name'])[0]==year),None)
        if start is not None: semesters=[s for s in semesters if s['sequence']>=start]
    mapping={s['id']:s['sequence'] for s in semesters}
    results=[{**asdict(r),'sequence':mapping[r.semester_id]} for r in db.scalars(select(AcademicResult).where(AcademicResult.student_id==sid).order_by(AcademicResult.semester_id)) if r.semester_id in mapping]
    warnings=[{'sequence':mapping[w.semester_id],'warned':w.warned} for w in db.scalars(select(WarningHistory).where(WarningHistory.student_id==sid).order_by(WarningHistory.semester_id)) if w.semester_id in mapping]
    return semesters,results,warnings
def assessment(db,student,semester_id,config=None,override=False,save=False):
    term=db.get(Semester,semester_id)
    c=config if override else select_config(db,student)
    semesters,results,warnings=inputs(db,student.id)
    # Snapshot includes only information at/before target; future records cannot leak.
    snapshot={'semesters':[s for s in semesters if s['sequence']<=term.sequence],
              'results':[r for r in results if r['sequence']<=term.sequence],
              'warnings':[w for w in warnings if w['sequence']<term.sequence]}
    output=evaluate(**snapshot,target=term.sequence,config=c.payload if c else None)
    output['config_id']=c.id if c else None
    output['config_name']=c.name if c else 'Chưa có cấu hình áp dụng'
    if save:
        latest=db.scalars(select(Evaluation).where(Evaluation.student_id==student.id,Evaluation.semester_id==semester_id).order_by(Evaluation.id.desc())).first()
        if not latest or latest.input_data!=snapshot or latest.config_id!=output['config_id'] or latest.output!=output:
            latest=Evaluation(student_id=student.id,semester_id=semester_id,config_id=output['config_id'],input_data=snapshot,output=output)
            db.add(latest);db.flush()
        output={**output,'evaluation_id':latest.id,'evaluated_at':latest.created_at.isoformat(),'persisted':True}
    else:
        output={**output,'evaluation_id':None,'evaluated_at':now().isoformat(),'persisted':False}
    return output
def scoped_students(db,user):
    q=select(Student)
    if user.role=='advisor': q=q.where(Student.advisor_id==user.id)
    elif user.role=='student': q=q.join(StudentAccount,StudentAccount.student_id==Student.id).where(StudentAccount.user_id==user.id)
    return list(db.scalars(q))
def filtered(db,user,params,config=None,override=False):
    latest=db.scalars(select(Semester).where(Semester.completed==True,Semester.kind=='regular').order_by(Semester.sequence.desc())).first()
    try: sid=int(params.get('semester_id') or (latest.id if latest else 0))
    except (ValueError,TypeError): raise HTTPException(422,'semester_id cần là mã học kỳ dạng số')
    if not db.get(Semester,sid): return [],sid
    sort=params.get('sort') or 'risk'
    if sort not in dict(SORT_OPTIONS): raise HTTPException(422,'Kiểu sắp xếp không hợp lệ; chọn lại trong danh sách.')
    if params.get('data_quality') not in (None,'','complete','missing','history'): raise HTTPException(422,'Bộ lọc dữ liệu không hợp lệ')
    items=[]
    for s in scoped_students(db,user):
        cls=db.get(Classroom,s.class_id)
        periods,results,_=inputs(db,s.id)
        if not any(p['id']==sid for p in periods): continue
        if any(params.get(k) and str(getattr(cls,k if k!='class_id' else 'id'))!=str(params[k]) for k in ('class_id','major_id','cohort_id')): continue
        if params.get('advisor_id') and str(s.advisor_id)!=str(params['advisor_id']): continue
        if params.get('q') and params['q'].strip().casefold() not in (s.name+' '+s.id).casefold(): continue
        r=assessment(db,s,sid,config,override)
        plans=list(db.scalars(select(Intervention).where(Intervention.student_id==s.id)))
        if params.get('level') and r['level']!=params['level']: continue
        if params.get('rule') and (r.get('rule') or {}).get('state','none')!=params['rule']: continue
        if params.get('status') and not any(p.status==params['status'] for p in plans): continue
        quality=params.get('data_quality')
        if quality=='complete' and (r['score'] is None or r['missing']): continue
        if quality in ('missing','history') and not any(i['kind']==quality for i in r.get('data_issues',[])): continue
        academic=next((row for row in results if row['semester_id']==sid),{})
        items.append({**asdict(s),'class_name':cls.name,'major_id':cls.major_id,'cohort_id':cls.cohort_id,'assessment':r,'academic':academic,'statuses':[p.status for p in plans]})
    return sort_students(items,sort),sid
def summary(db,user,params):
    items,sid=filtered(db,user,params)
    levels={x:sum(s['assessment']['level']==x for s in items) for x in ['Bình thường','Cần chú ý','Nguy cơ cao','Chưa đủ dữ liệu']}
    ids={s['id'] for s in items}
    plans=[p for p in db.scalars(select(Intervention)) if p.student_id in ids]
    return {'total':len(items),'assessed':len(items)-levels['Chưa đủ dữ liệu'],'levels':levels,'open':sum(p.status!='Hoàn tất' for p in plans),
            'overdue':sum(p.status!='Hoàn tất' and p.due_date<date.today() for p in plans),'semester_id':sid,
            'priority':items[:12],
            'interventions':{st:sum(p.status==st for p in plans) for st in ['Chưa xử lý','Đang hỗ trợ','Chờ theo dõi','Hoàn tất']}}
def debt_list(db,sid,semester_id):
    return [{'course_id':c.id,'name':c.name,'credits':c.credits} for d,c in db.execute(select(Debt,Course).join(Course,Debt.course_id==Course.id).where(Debt.student_id==sid,Debt.semester_id==semester_id))]
