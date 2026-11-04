from datetime import date
from fastapi import HTTPException
from sqlalchemy import select
from ..models import Student, Classroom, Semester, AcademicResult, WarningHistory, ConfigVersion, Evaluation, Intervention, Debt, Course, Audit, now
from .assessment import evaluate

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
    mapping={s['id']:s['sequence'] for s in semesters}
    results=[{**asdict(r),'sequence':mapping[r.semester_id]} for r in db.scalars(select(AcademicResult).where(AcademicResult.student_id==sid).order_by(AcademicResult.semester_id))]
    warnings=[{'sequence':mapping[w.semester_id],'warned':w.warned} for w in db.scalars(select(WarningHistory).where(WarningHistory.student_id==sid).order_by(WarningHistory.semester_id))]
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
    if user.role!='admin': q=q.where(Student.advisor_id==user.id)
    return list(db.scalars(q))
def filtered(db,user,params,config=None,override=False):
    latest=db.scalars(select(Semester).where(Semester.completed==True,Semester.kind=='regular').order_by(Semester.sequence.desc())).first()
    try: sid=int(params.get('semester_id') or (latest.id if latest else 0))
    except (ValueError,TypeError): raise HTTPException(422,'semester_id cần là mã học kỳ dạng số')
    if not db.get(Semester,sid): return [],sid
    items=[]
    for s in scoped_students(db,user):
        cls=db.get(Classroom,s.class_id)
        if any(params.get(k) and str(getattr(cls,k if k!='class_id' else 'id'))!=str(params[k]) for k in ('class_id','major_id','cohort_id')): continue
        if params.get('q') and params['q'].casefold() not in (s.name+' '+s.id).casefold(): continue
        r=assessment(db,s,sid,config,override)
        plans=list(db.scalars(select(Intervention).where(Intervention.student_id==s.id)))
        if params.get('level') and r['level']!=params['level']: continue
        if params.get('rule') and (r.get('rule') or {}).get('state','none')!=params['rule']: continue
        if params.get('status') and not any(p.status==params['status'] for p in plans): continue
        items.append({**asdict(s),'major_id':cls.major_id,'cohort_id':cls.cohort_id,'assessment':r,'statuses':[p.status for p in plans]})
    sort=params.get('sort','risk')
    items.sort(key=(lambda s:s['name']) if sort=='name' else ((lambda s:s['id']) if sort=='id' else lambda s:-(s['assessment']['score'] if s['assessment']['score'] is not None else -1)))
    return items,sid
def summary(db,user,params):
    items,sid=filtered(db,user,params)
    levels={x:sum(s['assessment']['level']==x for s in items) for x in ['Bình thường','Cần chú ý','Nguy cơ cao','Chưa đủ dữ liệu']}
    ids={s['id'] for s in items}
    plans=[p for p in db.scalars(select(Intervention)) if p.student_id in ids]
    return {'total':len(items),'assessed':len(items)-levels['Chưa đủ dữ liệu'],'levels':levels,'open':sum(p.status!='Hoàn tất' for p in plans),
            'overdue':sum(p.status!='Hoàn tất' and p.due_date<date.today() for p in plans),'semester_id':sid,
            'priority':sorted(items,key=lambda s:-(s['assessment']['score'] if s['assessment']['score'] is not None else -1))[:8],
            'interventions':{st:sum(p.status==st for p in plans) for st in ['Chưa xử lý','Đang hỗ trợ','Chờ theo dõi','Hoàn tất']}}
def debt_list(db,sid,semester_id):
    return [{'course_id':c.id,'name':c.name,'credits':c.credits} for d,c in db.execute(select(Debt,Course).join(Course,Debt.course_id==Course.id).where(Debt.student_id==sid,Debt.semester_id==semester_id))]
