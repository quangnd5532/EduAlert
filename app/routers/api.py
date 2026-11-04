import json
import secrets
from datetime import datetime,timezone,date
from fastapi import APIRouter,Depends,Request,HTTPException,UploadFile,File,Form
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel,Field
from ..db import get_db
from ..models import *
from ..schemas import *
from ..security import current_user,admin,student_access,hasher
from ..services.data import asdict,filtered,summary,assessment,inputs,select_config,audit,debt_list
from ..services.assessment import simulate,DEFAULT
from ..services.csv_import import parse_file,validate_rows,apply_rows,csv_bytes,HEADERS
router=APIRouter(prefix='/api',tags=['EduAlert'])

@router.get('/students')
def students(request:Request,user=Depends(current_user),db=Depends(get_db)):
    items,sid=filtered(db,user,request.query_params)
    try: page=max(1,min(int(request.query_params.get('page',1)),10000))
    except ValueError: raise HTTPException(422,'Số trang không hợp lệ')
    size=12
    return {'items':items[(page-1)*size:page*size],'total':len(items),'page':page,'pages':max(1,(len(items)+size-1)//size),'semester_id':sid}
@router.get('/summary')
def dashboard(request:Request,user=Depends(current_user),db=Depends(get_db)):
    return summary(db,user,request.query_params)
@router.get('/trend')
def trend(request:Request,user=Depends(current_user),db=Depends(get_db)):
    params=dict(request.query_params);items=[]
    max_id=params.get('semester_id');chosen=db.get(Semester,int(max_id)) if max_id else None
    for term in db.scalars(select(Semester).where(Semester.completed==True,Semester.kind=='regular').order_by(Semester.sequence)):
        if chosen and term.sequence>chosen.sequence: continue
        s=summary(db,user,{**params,'semester_id':term.id});items.append({'name':term.name,**s['levels']})
    return items
@router.get('/report-groups')
def report_groups(request:Request,user=Depends(current_user),db=Depends(get_db)):
    items,sid=filtered(db,user,request.query_params);out={}
    for key in ('class_id','major_id','cohort_id'):
        groups={}
        for s in items:
            g=groups.setdefault(s[key],{'total':0,'Bình thường':0,'Cần chú ý':0,'Nguy cơ cao':0,'Chưa đủ dữ liệu':0})
            g['total']+=1;g[s['assessment']['level']]+=1
        out[key]=groups
    return out
@router.get('/students/{sid}')
def detail(sid:str,semester_id:int|None=None,user=Depends(current_user),db=Depends(get_db)):
    s=student_access(db,user,sid);periods,results,warnings=inputs(db,sid)
    term=db.get(Semester,semester_id) if semester_id else db.scalars(select(Semester).where(Semester.kind=='regular',Semester.completed==True).order_by(Semester.sequence.desc())).first()
    if not term: raise HTTPException(404,'Học kỳ không tồn tại')
    plans=list(db.scalars(select(Intervention).where(Intervention.student_id==sid).order_by(Intervention.id.desc())))
    history=[asdict(e) for e in db.scalars(select(Evaluation).where(Evaluation.student_id==sid).order_by(Evaluation.id.desc()))]
    chart=[]
    for p in periods:
        if p['sequence']>term.sequence or p['kind']!='regular' or not p['completed']: continue
        r=next((r for r in results if r['sequence']==p['sequence']),{})
        ev=assessment(db,s,p['id'])
        chart.append({'name':p['name'],'gpa':r.get('gpa'),'failed_ratio':r['failed']/r['registered']*100 if r.get('registered',0) else None,'score':ev['score'],
                      'interventions':sum(1 for i in plans if any(e['id']==i.evaluation_id and e['semester_id']==p['id'] for e in history))})
    return {'student':asdict(s),'semesters':periods,'results':results,'warnings':warnings,'assessment':assessment(db,s,term.id),
            'debts':debt_list(db,sid,term.id),'interventions':[plan_dict(db,p) for p in plans],'history':history,'chart':chart,'semester_id':term.id,
            'suggestion':'Rà soát môn nợ; trao đổi kế hoạch đăng ký' if debt_list(db,sid,term.id) else 'Lập lịch học và hẹn tư vấn định kỳ'}
@router.post('/students/{sid}/evaluate')
def save_evaluation(sid:str,semester_id:int,user=Depends(current_user),db=Depends(get_db)):
    s=student_access(db,user,sid)
    if not db.get(Semester,semester_id): raise HTTPException(404,'Học kỳ không tồn tại')
    out=assessment(db,s,semester_id,save=True);audit(db,user,'evaluate',{'student_id':sid,'evaluation_id':out['evaluation_id']});db.commit();return out
@router.post('/students/{sid}/simulate')
def simulation(sid:str,data:SimulationInput,semester_id:int,user=Depends(current_user),db=Depends(get_db)):
    s=student_access(db,user,sid);term=db.get(Semester,semester_id)
    if not term: raise HTTPException(404,'Không tìm thấy kỳ học')
    periods,results,warnings=inputs(db,sid);config=select_config(db,s)
    scenario={k:getattr(data,k) for k in ('gpa','registered','failed')}
    result=simulate(periods,results,warnings,term.sequence,scenario,config.payload if config else None)
    result.update(config_id=config.id if config else None,config_name=config.name if config else 'Chưa có cấu hình áp dụng',evaluated_at=now().isoformat(),persisted=False)
    before=assessment(db,s,semester_id,config,True);current=next((r for r in results if r['sequence']==term.sequence),{})
    cumulative=None
    note='Chưa tính GPA tích lũy: cần GPA tích lũy hiện có, số tín chỉ đã tính GPA, xác nhận không học lại và mọi tín chỉ đăng ký đều tính GPA.'
    if current.get('cumulative_gpa') is not None and data.previous_gpa_credits and data.no_repeats and data.all_registered_count:
        credits=data.previous_gpa_credits
        cumulative=round((current['cumulative_gpa']*credits+data.gpa*data.registered)/(credits+data.registered),4)
        note=f"({current['cumulative_gpa']} × {credits} + {data.gpa} × {data.registered}) / ({credits} + {data.registered}). Giả định không học lại; toàn bộ tín chỉ đăng ký tính GPA, kể cả không đạt. Số tín chỉ tính GPA do người dùng cung cấp; không dùng tổng tín chỉ tích lũy thay thế."
    return {'before':before,'after':result,'cumulative_gpa':cumulative,'cumulative_note':note,'notice':'Kịch bản giả định, không phải dự đoán chắc chắn. Không lưu vào dữ liệu thật.'}
@router.post('/students',status_code=201)
def create_student(data:StudentInput,user=Depends(admin),db=Depends(get_db)):
    rows,errors,_=validate_rows(db,'students',[data.model_dump()], 'update')
    if errors: raise HTTPException(422,errors)
    if db.get(Student,data.id): raise HTTPException(409,'Mã sinh viên đã tồn tại')
    db.add(Student(**data.model_dump()));audit(db,user,'create_student',{'student_id':data.id});db.commit();return {'ok':True}
@router.put('/students/{sid}')
def update_student(sid:str,data:StudentInput,user=Depends(admin),db=Depends(get_db)):
    if sid!=data.id: raise HTTPException(422,'Không đổi mã sinh viên')
    student_access(db,user,sid)
    errors,count=apply_rows(db,'students',[data.model_dump()], 'update')
    if errors: raise HTTPException(422,errors)
    audit(db,user,'update_student',data.model_dump());db.commit();return {'ok':True}
@router.put('/results')
def update_result(data:ResultInput,user=Depends(admin),db=Depends(get_db)):
    errors,count=apply_rows(db,'results',[data.model_dump()], 'update')
    if errors: raise HTTPException(422,errors)
    audit(db,user,'update_result',data.model_dump());db.commit();return {'ok':True}
def plan_dict(db,p):
    e=db.get(Evaluation,p.evaluation_id);base_term=db.get(Semester,e.semester_id)
    rows=list(db.execute(select(AcademicResult,Semester).join(Semester,AcademicResult.semester_id==Semester.id).where(AcademicResult.student_id==p.student_id,Semester.kind=='regular',Semester.completed==True,AcademicResult.status=='completed').order_by(Semester.sequence)))
    before=next(((r,t) for r,t in rows if t.id==base_term.id),None)
    after=next(((r,t) for r,t in rows if t.sequence>base_term.sequence),None)
    comparison={'before':{'semester':before[1].name,'gpa':before[0].gpa} if before else None,'after':{'semester':after[1].name,'gpa':after[0].gpa} if after else None}
    return {**asdict(p),'student_name':db.get(Student,p.student_id).name,'owner':db.get(User,p.owner_id).name,
            'comparison':comparison,
            'overdue':p.status!='Hoàn tất' and p.due_date<date.today(),
            'notes':[asdict(n) for n in db.scalars(select(Followup).where(Followup.intervention_id==p.id).order_by(Followup.id))]}
@router.get('/interventions')
def plans(user=Depends(current_user),db=Depends(get_db)):
    return [plan_dict(db,p) for p in db.scalars(select(Intervention).order_by(Intervention.id.desc())) if user.role=='admin' or db.get(Student,p.student_id).advisor_id==user.id]
@router.post('/interventions',status_code=201)
def create_plan(data:InterventionInput,user=Depends(current_user),db=Depends(get_db)):
    s=student_access(db,user,data.student_id);e=db.get(Evaluation,data.evaluation_id)
    if not e or e.student_id!=s.id: raise HTTPException(422,'Đánh giá không thuộc sinh viên')
    p=Intervention(**data.model_dump(),owner_id=s.advisor_id);db.add(p);db.flush();audit(db,user,'create_intervention',{'id':p.id});db.commit();return plan_dict(db,p)
@router.patch('/interventions/{pid}')
def update_plan(pid:int,data:InterventionUpdate,user=Depends(current_user),db=Depends(get_db)):
    p=db.get(Intervention,pid)
    if not p: raise HTTPException(404,'Không tìm thấy hồ sơ')
    student_access(db,user,p.student_id)
    p.status=data.status
    for k in ('goal','action','due_date'):
        if getattr(data,k) is not None: setattr(p,k,getattr(data,k))
    if data.note.strip(): db.add(Followup(intervention_id=pid,author_id=user.id,note=data.note.strip()))
    audit(db,user,'update_intervention',{'id':pid,'status':data.status});db.commit();return plan_dict(db,p)
@router.get('/export')
def export(request:Request,user=Depends(current_user),db=Depends(get_db)):
    items,sid=filtered(db,user,request.query_params)
    audit(db,user,'export',{'filters':dict(request.query_params),'count':len(items)});db.commit()
    return Response(csv_bytes(['Mã sinh viên','Họ tên','Lớp','Ngành','Khóa','Kỳ','Điểm hỗ trợ /100','Mức nguy cơ','Kết quả quy tắc','Phiên bản','Can thiệp'],
        [[s['id'],s['name'],s['class_id'],s['major_id'],s['cohort_id'],sid,s['assessment']['score'],s['assessment']['level'],s['assessment']['rule_label'],s['assessment']['config_id'],'; '.join(s['statuses'])] for s in items]),
        media_type='text/csv',headers={'Content-Disposition':'attachment; filename=edualert-report.csv'})
@router.get('/configs')
def configs(user=Depends(admin),db=Depends(get_db)):
    return [asdict(c) for c in db.scalars(select(ConfigVersion).order_by(ConfigVersion.id.desc()))]
@router.post('/configs',status_code=201)
def create_config(data:ConfigInput,user=Depends(admin),db=Depends(get_db)):
    if data.major_id and not db.get(Major,data.major_id) or data.cohort_id and not db.get(Cohort,data.cohort_id): raise HTTPException(422,'Phạm vi không tồn tại')
    c=ConfigVersion(**data.model_dump());db.add(c);db.flush();audit(db,user,'config_draft',{'id':c.id,'payload':c.payload});db.commit();return asdict(c)
@router.post('/configs/{cid}/preview')
def preview_config(cid:int,user=Depends(admin),db=Depends(get_db)):
    c=db.get(ConfigVersion,cid)
    if not c: raise HTTPException(404,'Không tìm thấy phiên bản')
    before,sid=filtered(db,user,{});after=[]
    for s in before:
        student=db.get(Student,s['id']);cls=db.get(Classroom,student.class_id)
        # Preview exact activation priority, including more-specific active scopes.
        candidates=[x for x in db.scalars(select(ConfigVersion).where(ConfigVersion.active==True)) if (x.major_id,x.cohort_id)!=(c.major_id,c.cohort_id)] + [c]
        candidates=[x for x in candidates if (not x.major_id or x.major_id==cls.major_id) and (not x.cohort_id or x.cohort_id==cls.cohort_id)]
        selected=max(candidates,key=lambda x:(2*bool(x.major_id)+bool(x.cohort_id),x.id),default=None)
        after.append(assessment(db,student,sid,selected,True))
    return {'total':len(before),'changed':sum(s['assessment']['level']!=a['level'] for s,a in zip(before,after)), 'missing':sum(a['score'] is None for a in after),'note':'Xem trước kỳ chính mới nhất; không sửa lịch sử.'}
@router.post('/configs/{cid}/activate')
def activate(cid:int,user=Depends(admin),db=Depends(get_db)):
    # SQLite writer reservation serializes same-scope activation.
    if db.bind.dialect.name=='sqlite':
        from sqlalchemy import text
        db.execute(text('BEGIN IMMEDIATE'))
    c=db.get(ConfigVersion,cid)
    if not c: raise HTTPException(404,'Không tìm thấy phiên bản')
    if c.active: return {'ok':True,'id':cid}
    for old in db.scalars(select(ConfigVersion).where(ConfigVersion.active==True)):
        if (old.major_id,old.cohort_id)==(c.major_id,c.cohort_id): old.active=False
    c.active=True;c.activated_at=now();audit(db,user,'config_activate',{'id':cid,'scope':[c.major_id,c.cohort_id]});db.commit();return {'ok':True,'id':cid}
@router.get('/import/template/{kind}')
def template_csv(kind:str,user=Depends(admin)):
    if kind not in HEADERS: raise HTTPException(404,'Mẫu không tồn tại')
    return Response(csv_bytes(HEADERS[kind],[]),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename={kind}.csv'})
@router.post('/import/preview')
async def import_preview(file:UploadFile=File(...),kind:str=Form(...),mode:str=Form(...),user=Depends(admin),db=Depends(get_db)):
    raw=await file.read(2*1024*1024+1)
    try:
        rows=parse_file(raw,kind);_,errors,existing=validate_rows(db,kind,rows,mode)
    except ValueError as e: raise HTTPException(422,str(e))
    b=ImportBatch(id=secrets.token_urlsafe(24),user_id=user.id,kind=kind,mode=mode,rows=rows,errors=errors);db.add(b);db.commit()
    return {'id':b.id,'rows':rows[:10],'count':len(rows),'errors':errors,'existing':existing,'mode':mode,'notice':f'{existing} bản ghi đã tồn tại: '+('bỏ qua' if mode=='skip' else 'cập nhật toàn bộ trường từ tệp')}
def get_batch(db,user,bid):
    b=db.get(ImportBatch,bid)
    if not b or b.user_id!=user.id: raise HTTPException(404,'Không tìm thấy phiên nhập')
    if (datetime.now(timezone.utc)-b.created_at.replace(tzinfo=timezone.utc)).total_seconds()>3600: raise HTTPException(410,'Phiên xem trước hết hạn; nhập lại tệp')
    return b
@router.post('/import/{bid}/confirm')
def confirm_import(bid:str,user=Depends(admin),db=Depends(get_db)):
    if db.bind.dialect.name=='sqlite':
        from sqlalchemy import text
        db.execute(text('BEGIN IMMEDIATE'))
    b=get_batch(db,user,bid)
    if b.consumed: raise HTTPException(409,'Phiên nhập đã được lưu')
    errors,count=apply_rows(db,b.kind,b.rows,b.mode)
    if errors: db.rollback();raise HTTPException(422,errors)
    b.consumed=True;audit(db,user,'import_confirm',{'id':bid,'kind':b.kind,'count':count,'mode':b.mode});db.commit();return {'ok':True,'saved':count}
@router.get('/import/{bid}/errors')
def error_file(bid:str,user=Depends(admin),db=Depends(get_db)):
    b=get_batch(db,user,bid)
    return Response(csv_bytes(['Dòng','Cột','Lỗi và cách sửa'],[[e['line'],e['column'],e['message']] for e in b.errors]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=errors.csv'})
class AccountInput(BaseModel):
    username:str=Field(pattern=r'^[a-zA-Z0-9_.-]{3,50}$')
    name:str=Field(min_length=2,max_length=120)
    password:str=Field(min_length=10,max_length=128)
@router.post('/accounts')
def create_account(data:AccountInput,user=Depends(admin),db=Depends(get_db)):
    if db.scalar(select(User).where(User.username==data.username)): raise HTTPException(409,'Tên đăng nhập đã tồn tại')
    u=User(username=data.username,name=data.name,password_hash=hasher.hash(data.password),role='advisor');db.add(u);audit(db,user,'create_account',{'username':data.username});db.commit();return {'ok':True}
class AccountUpdate(BaseModel):
    active:bool
@router.patch('/accounts/{uid}')
def toggle_account(uid:int,data:AccountUpdate,user=Depends(admin),db=Depends(get_db)):
    u=db.get(User,uid)
    if not u or u.role!='advisor': raise HTTPException(422,'Chỉ thay đổi tài khoản cố vấn')
    u.active=data.active;audit(db,user,'account_status',{'id':uid,'active':data.active});db.commit();return {'ok':True}
class CatalogInput(BaseModel):
    id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,30}$')
    name:str=Field(min_length=2,max_length=120)
    major_id:str|None=None
    cohort_id:str|None=None
    credits:int|None=Field(default=None,ge=1,le=20)
    sequence:int|None=Field(default=None,ge=1)
    kind:Literal['regular','summer']='regular'
    completed:bool=True
@router.post('/catalog/{kind}')
def catalog(kind:str,data:CatalogInput,user=Depends(admin),db=Depends(get_db)):
    models={'majors':Major,'cohorts':Cohort,'classes':Classroom,'courses':Course,'semesters':Semester}
    if kind not in models: raise HTTPException(404,'Danh mục không tồn tại')
    values={'id':data.id,'name':data.name}
    if kind=='classes':
        if not db.get(Major,data.major_id) or not db.get(Cohort,data.cohort_id): raise HTTPException(422,'Ngành/khóa chưa tồn tại')
        values.update(major_id=data.major_id,cohort_id=data.cohort_id)
    if kind=='courses':
        if data.credits is None: raise HTTPException(422,'Cần số tín chỉ')
        values['credits']=data.credits
    if kind=='semesters':
        if data.sequence is None or not data.id.isdigit(): raise HTTPException(422,'Mã học kỳ cần là số và có thứ tự')
        values.update(id=int(data.id),sequence=data.sequence,kind=data.kind,completed=data.completed)
    model=models[kind];obj=db.get(model,values['id'])
    if obj:
        if kind=='semesters': raise HTTPException(409,'Không sửa thứ tự học kỳ đã tồn tại; tạo kỳ mới')
        for k,v in values.items(): setattr(obj,k,v)
    else: db.add(model(**values))
    audit(db,user,'catalog_save',{'kind':kind,**values});db.commit();return {'ok':True}
