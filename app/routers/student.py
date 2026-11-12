"""Personal portal. The student identity always comes from the signed session."""
from datetime import date
from typing import Literal
from fastapi import APIRouter,Depends,Request,HTTPException,Form
from fastapi.responses import Response,RedirectResponse
from fastapi.encoders import jsonable_encoder
from pydantic import Field
from sqlalchemy import select,or_,update
from ..db import get_db
from ..models import StudentAccount,User,Classroom,Major,Cohort,Course,CourseResult,Intervention,AcademicResult,PasswordRecovery
from ..schemas import Strict,SimulationInput
from ..security import current_user,own_student,csrf_token,check_password,login_allowed,login_succeeded
from ..services.data import asdict,assessment,audit
from ..services.csv_import import csv_bytes
from ..services.student_planning import learning_guidance,student_outlook
from .api import detail,simulation
from .pages import templates

router=APIRouter(tags=['Sinh viên'])

STUDENT_PAGES = {
    'overview': ('Tổng quan', 'Theo dõi tình hình học tập và những việc cần ưu tiên.'),
    'results': ('Kết quả học tập', 'Tra cứu bảng điểm, tín chỉ và học phần chưa hoàn thành.'),
    'analysis': ('Phân tích học tập', 'Hiểu điều kiện học vụ và từng yếu tố tạo nên chỉ số hỗ trợ.'),
    'planning': ('Kế hoạch học tập', 'Biết nên cải thiện điều gì và đặt mục tiêu cho học kỳ tới.'),
    'appointments': ('Cố vấn & lịch hẹn', 'Gửi yêu cầu tư vấn và theo dõi kế hoạch hỗ trợ.'),
    'profile': ('Thông tin sinh viên', 'Thông tin hồ sơ học tập và cố vấn phụ trách.'),
}

def filter_courses(courses,q='',course_status=''):
    def matches(c):
        state='pending' if c['grade'] is None else 'failed' if c['grade']==0 else 'passed'
        return (not q.strip() or q.strip().casefold() in (c['id']+' '+c['name']).casefold()) and (not course_status or state==course_status)
    return [c for c in courses if matches(c)]

def grade(value,digits=2):
    return '—' if value is None else f'{value:.{digits}f}'

def vietnamese_date(value):
    if not value:return '—'
    if isinstance(value,str):value=date.fromisoformat(value[:10])
    return value.strftime('%d/%m/%Y')

templates.env.filters['grade']=grade
templates.env.filters['date_vi']=vietnamese_date

def portal_page(request,user,db):
    own_student(db,user)
    suffix=('?'+request.url.query) if request.url.query else ''
    return RedirectResponse('/student/overview'+suffix,303)

@router.get('/student/{view}',include_in_schema=False,name='student_page')
def student_page(view:str,request:Request,semester_id:int|None=None,q:str='',
                 course_status:Literal['','passed','failed','pending']='',
                 user=Depends(current_user),db=Depends(get_db)):
    return render_student(view,request,user,db,semester_id,q,course_status)

def render_student(view,request,user,db,semester_id=None,q='',course_status='',simulation_result=None,simulation_inputs=None,contact_error=None,contact_values=None):
    if view not in STUDENT_PAGES:raise HTTPException(404,'Trang không tồn tại')
    model=jsonable_encoder(me(semester_id,user,db))
    title,description=STUDENT_PAGES[view]
    return templates.TemplateResponse(request=request,name=f'student/{view}.html',context={
        'user':user,'csrf':csrf_token(request),'model':model,'view':view,
        'title':title,'description':description,'student_pages':STUDENT_PAGES,
        'courses':filter_courses(model['courses'],q,course_status),'q':q,'course_status':course_status,
        'today':date.today(),'period_names':{int(k):v for k,v in model['period_names'].items()},
        'simulation_result':jsonable_encoder(simulation_result),'simulation_inputs':simulation_inputs or {},
        'contact_error':contact_error,'contact_values':contact_values or {},
        'planning_guidance':learning_guidance(model) if view=='planning' else None,
        'contact_message':request.session.pop('contact_message',None) if view=='profile' else None},status_code=400 if contact_error else 200)

@router.get('/api/me')
def me(semester_id:int|None=None,user=Depends(current_user),db=Depends(get_db)):
    s=own_student(db,user)
    d=detail(s.id,semester_id,user,db)
    cls=db.get(Classroom,s.class_id);advisor=db.get(User,s.advisor_id)
    account=db.get(StudentAccount,user.id)
    term=next(p for p in d['semesters'] if p['id']==d['semester_id'])
    if term['kind']!='regular' or not term['completed']:
        raise HTTPException(422,'Vui lòng chọn học kỳ chính đã hoàn thành')
    current=next((r for r in d['results'] if r['semester_id']==term['id']),None)
    courses=[]
    for r,c in db.execute(select(CourseResult,Course).join(Course,CourseResult.course_id==Course.id).where(CourseResult.student_id==s.id,CourseResult.semester_id==term['id']).order_by(CourseResult.course_id)):
        courses.append({'id':c.id,'name':c.name,'credits':c.credits,'grade':r.grade,
                        'status':'Chưa đồng bộ điểm' if r.grade is None else 'Không đạt' if r.grade==0 else 'Đạt'})
    plans=[{'id':p['id'],'goal':p['goal'],'action':p['action'],'due_date':p['due_date'],'status':p['status'],'overdue':p['overdue'],'owner':p['owner']} for p in d['interventions']]
    return {'profile':{'id':s.id,'name':s.name,'class_name':cls.name,'major':db.get(Major,cls.major_id).name,
                       'cohort':db.get(Cohort,cls.cohort_id).name,'advisor':advisor.name,
                       'admission_score':s.admission_score,'admission_scale':s.admission_scale,'admission_method':s.admission_method,
                       'email':account.email,'phone':account.phone},
            'semesters':[p for p in d['semesters'] if p['kind']=='regular' and p['completed']],
            'period_names':{p['sequence']:p['name'] for p in d['semesters']},
            'semester_id':term['id'],'semester_name':term['name'],'current':current,
            'history':[r for r in d['results'] if r['sequence']<=term['sequence']],
            'assessment':d['assessment'],'chart':d['chart'],'courses':courses,'debts':d['debts'],'appointments':plans,
            'data_notice':'Hồ sơ và bảng điểm trong môi trường này là dữ liệu giả lập, không phải hồ sơ sinh viên thật.'}

@router.post('/student/profile/contacts',include_in_schema=False)
def update_contacts(request:Request,email:str=Form(''),phone:str=Form(''),current_password:str=Form(''),
                    user=Depends(current_user),db=Depends(get_db)):
    from .recovery import normalize_contact
    own_student(db,user)
    values={'email':email[:254],'phone':phone[:30]}
    def invalid(message):
        return render_student('profile',request,user,db,contact_error=message,contact_values=values)
    key=('contacts',request.client.host,user.id)
    login_allowed(key)
    if len(current_password)>128 or not check_password(user.password_hash,current_password):
        return invalid('Mật khẩu hiện tại chưa đúng. Vui lòng kiểm tra lại để lưu thông tin khôi phục.')
    try:
        email=normalize_contact('email',email) if email.strip() else None
        phone=normalize_contact('phone',phone) if phone.strip() else None
    except ValueError as exc:
        return invalid(str(exc))
    if not email and not phone:
        return invalid('Vui lòng cung cấp ít nhất một email hoặc số điện thoại để khôi phục tài khoản.')
    duplicate=db.scalar(select(StudentAccount.user_id).where(StudentAccount.user_id!=user.id,
        or_(StudentAccount.email==email if email else False,StudentAccount.phone==phone if phone else False)))
    if duplicate:
        return invalid('Thông tin liên hệ này đã được sử dụng. Vui lòng kiểm tra hoặc liên hệ bộ phận học vụ.')
    account=db.get(StudentAccount,user.id)
    account.email=email;account.phone=phone
    user.session_version+=1
    db.execute(update(PasswordRecovery).where(PasswordRecovery.user_id==user.id).values(consumed=True))
    audit(db,user,'recovery_contacts_updated',{'email_registered':bool(email),'phone_registered':bool(phone)})
    db.commit()
    login_succeeded(key)
    request.session['session_version']=user.session_version
    request.session['contact_message']='Đã lưu thông tin khôi phục tài khoản của bạn.'
    return RedirectResponse('/student/profile#recovery-contacts',303)

@router.post('/api/me/simulate')
def what_if(data:SimulationInput,semester_id:int,user=Depends(current_user),db=Depends(get_db)):
    s=own_student(db,user)
    model=me(semester_id,user,db)
    result=simulation(s.id,data,semester_id,user,db)
    result['outlook']=student_outlook(model,data.model_dump(),result)
    result['student_html']=templates.get_template('student/simulation_result.html').render(simulation_result=result)
    return result

class AppointmentInput(Strict):
    due_date:date
    message:str=Field(min_length=10,max_length=2000)

@router.post('/api/me/appointments',status_code=201)
def appointment(data:AppointmentInput,user=Depends(current_user),db=Depends(get_db)):
    s=own_student(db,user)
    if data.due_date<date.today(): raise HTTPException(422,'Ngày đề nghị không được nằm trong quá khứ')
    d=me(None,user,db)
    ev=assessment(db,s,d['semester_id'],save=True)
    p=Intervention(student_id=s.id,evaluation_id=ev['evaluation_id'],owner_id=s.advisor_id,
                   goal=data.message,action='Sinh viên đề nghị trao đổi. Cố vấn sẽ xác nhận lịch và thống nhất kế hoạch hỗ trợ.',
                   due_date=data.due_date,status='Chưa xử lý')
    db.add(p);db.flush();audit(db,user,'student_appointment_request',{'id':p.id,'student_id':s.id});db.commit()
    return {'id':p.id,'message':'Đã gửi yêu cầu lịch hẹn. Vui lòng chờ cố vấn xác nhận.'}

@router.post('/student/appointments',include_in_schema=False)
def appointment_form(request:Request,semester_id:int|None=None,due_date:date=Form(...),
                     message:str=Form(...,min_length=10,max_length=2000),user=Depends(current_user),db=Depends(get_db)):
    message=message.strip()
    if len(message)<10:raise HTTPException(422,'Nội dung cần hỗ trợ phải có ít nhất 10 ký tự, không tính khoảng trắng ở đầu/cuối')
    result=appointment(AppointmentInput(due_date=due_date,message=message),user,db)
    suffix=f'&semester_id={semester_id}' if semester_id is not None else ''
    return RedirectResponse(f'/student/appointments?sent={result["id"]}'+suffix,303)

@router.post('/student/planning',include_in_schema=False)
def planning_form(request:Request,semester_id:int,gpa:float=Form(...,ge=0,le=4),
                  registered:int=Form(...,ge=1,le=60),failed:int=Form(...,ge=0,le=60),
                  previous_gpa_credits:int|None=Form(None,ge=1,le=600),no_repeats:bool=Form(False),
                  all_registered_count:bool=Form(False),user=Depends(current_user),db=Depends(get_db)):
    if failed>registered:raise HTTPException(422,'Tín chỉ không đạt không được vượt tín chỉ đăng ký')
    data=SimulationInput(gpa=gpa,registered=registered,failed=failed,previous_gpa_credits=previous_gpa_credits,
                         no_repeats=no_repeats,all_registered_count=all_registered_count)
    result=what_if(data,semester_id,user,db)
    return render_student('planning',request,user,db,semester_id,simulation_result=result,simulation_inputs=data.model_dump())

@router.get('/api/me/export')
def export_me(semester_id:int|None=None,q:str='',course_status:Literal['','passed','failed','pending']='',user=Depends(current_user),db=Depends(get_db)):
    d=me(semester_id,user,db)
    rows=[[d['profile']['id'],d['profile']['name'],d['semester_name'],c['id'],c['name'],c['credits'],c['grade'],c['status']] for c in filter_courses(d['courses'],q,course_status)]
    audit(db,user,'student_export',{'student_id':d['profile']['id'],'semester_id':d['semester_id']});db.commit()
    return Response(csv_bytes(['Mã SV','Họ tên','Học kỳ','Mã học phần','Học phần','Tín chỉ','Điểm /4','Kết quả'],rows),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=my-results.csv'})
