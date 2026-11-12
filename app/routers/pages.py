from fastapi import APIRouter,Depends,Request,HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from ..security import current_user,staff,admin,student_access,csrf_token
from ..db import get_db
from ..models import *
from ..services.data import asdict
from ..services.assessment import DEFAULT
from ..services.sorting import SORT_OPTIONS
from ..services.import_samples import LABELS,FIELD_GUIDE,sample_rows
from ..services.configuration import PRESETS
router=APIRouter(include_in_schema=False)
templates=Jinja2Templates(directory='app/templates')
NAV=[('/dashboard','Tổng quan','dashboard'),('/students','Sinh viên','students'),('/import','Nhập CSV','import'),('/settings','Cấu hình đánh giá','settings'),('/interventions','Can thiệp & lịch hẹn','interventions'),('/reports','Báo cáo & thống kê','reports'),('/admin','Quản trị hệ thống','admin')]
def render(request,page,title,user,db,student_id=None):
    catalogs={name:[asdict(o) for o in db.scalars(select(model))] for name,model in [('majors',Major),('cohorts',Cohort),('classes',Classroom),('semesters',Semester),('courses',Course)]}
    if user.role!='admin':
        allowed={s.class_id for s in db.scalars(select(Student).where(Student.advisor_id==user.id))}
        catalogs['classes']=[c for c in catalogs['classes'] if c['id'] in allowed]
        catalogs['majors']=[m for m in catalogs['majors'] if m['id'] in {c['major_id'] for c in catalogs['classes']}]
        catalogs['cohorts']=[m for m in catalogs['cohorts'] if m['id'] in {c['cohort_id'] for c in catalogs['classes']}]
    catalogs['semesters'].sort(key=lambda s:s['sequence'])
    users=[{'id':u.id,'username':u.username,'name':u.name,'role':u.role,'active':u.active} for u in db.scalars(select(User))] if user.role=='admin' else []
    advisors=[{'id':u.id,'name':u.name} for u in db.scalars(select(User).where(User.role=='advisor',User.active==True)) if user.role=='admin' or u.id==user.id]
    return templates.TemplateResponse(request=request,name='app.html',context={'page':page,'title':title,'user':user,'nav':NAV,'csrf':csrf_token(request),'catalogs':catalogs,'users':users,'student_id':student_id,'default_config':DEFAULT,'sort_options':SORT_OPTIONS,'advisors':advisors,
        'import_samples':LABELS,'field_guide':FIELD_GUIDE,'sample_rows':sample_rows() if page=='import' else {},'config_presets':PRESETS})
@router.get('/')
def home(): return RedirectResponse('/dashboard',303)
@router.get('/dashboard')
def dashboard(request:Request,user=Depends(current_user),db=Depends(get_db)):
    if user.role=='student':
        from .student import portal_page
        return portal_page(request,user,db)
    return render(request,'dashboard','Tổng quan học tập',user,db)
@router.get('/students')
def students(request:Request,user=Depends(staff),db=Depends(get_db)): return render(request,'students','Danh sách sinh viên',user,db)
@router.get('/students/{sid}')
def detail(sid:str,request:Request,user=Depends(staff),db=Depends(get_db)):
    s=student_access(db,user,sid);return render(request,'detail',s.name,user,db,sid)
@router.get('/import')
def imports(request:Request,user=Depends(admin),db=Depends(get_db)): return render(request,'import','Nhập và kiểm tra CSV',user,db)
@router.get('/settings')
def settings(request:Request,user=Depends(admin),db=Depends(get_db)): return render(request,'settings','Cấu hình đánh giá',user,db)
@router.get('/interventions')
def interventions(request:Request,user=Depends(staff),db=Depends(get_db)): return render(request,'interventions','Can thiệp & lịch hẹn',user,db)
@router.get('/reports')
def reports(request:Request,user=Depends(staff),db=Depends(get_db)): return render(request,'reports','Báo cáo & thống kê',user,db)
@router.get('/admin')
def administration(request:Request,user=Depends(admin),db=Depends(get_db)): return render(request,'admin','Quản trị hệ thống',user,db)
