import csv,io,json
from copy import deepcopy
from sqlalchemy import select,func
from tests.conftest import login
from app.models import *
from app.services.assessment import DEFAULT
from app.services.csv_import import HEADERS,csv_bytes

def count(factory,model):
    with factory() as db:return db.scalar(select(func.count()).select_from(model))
def test_auth_and_csrf(env):
    c,f=env;assert c.get('/api/students').status_code==401
    assert c.post('/api/configs',json={}).status_code==403
    login(c);assert c.get('/api/students').json()['total']==60
    cookie=c.cookies.get('edualert_session');assert cookie
def test_advisor_resource_isolation(env):
    c,f=env;login(c,'advisor1')
    assert c.get('/api/students').json()['total']==30
    for path in ['/api/students/000003','/students/000003']:
        assert c.get(path).status_code==404
    for path in ['/api/students/000003/evaluate?semester_id=6','/api/students/000003/simulate?semester_id=6']:
        assert c.post(path,json={'gpa':3,'registered':20,'failed':0}).status_code==404
    assert c.put('/api/students/000003',json={'id':'000003','name':'Demo','class_id':'L3','advisor_id':2}).status_code==403
    assert c.get('/api/export?q=000003').content.decode('utf-8-sig').count('\n')==1
    assert c.get('/api/configs').status_code==403;assert c.get('/admin').status_code==403
def test_nine_pages_and_api_docs(env):
    c,f=env;login(c)
    for path in ['/login','/dashboard','/students','/students/000005','/import','/settings','/interventions','/reports','/admin','/docs','/openapi.json']:
        r=c.get(path);assert r.status_code==200,(path,r.text)
        assert 'Traceback' not in r.text
def test_saved_config_and_snapshot(env):
    c,f=env;login(c)
    before=c.post('/api/students/000005/evaluate?semester_id=6').json()
    config=deepcopy(DEFAULT);config['weights']=[100,0,0,0]
    r=c.post('/api/configs',json={'name':'Nháp thử nghiệm','payload':config});assert r.status_code==201
    cid=r.json()['id'];preview=c.post(f'/api/configs/{cid}/preview').json();assert preview['changed']>0
    assert c.post(f'/api/configs/{cid}/activate').status_code==200
    after=c.post('/api/students/000005/evaluate?semester_id=6').json();assert after['config_id']==cid
    assert after['evaluation_id']!=before['evaluation_id']
    with f() as db:
        old=db.get(Evaluation,before['evaluation_id']);assert old.config_id==before['config_id'];assert old.output['score']==71.5
def test_scope_priority(env):
    c,f=env;login(c)
    ids=[]
    for scope in [{'cohort_id':'K23'},{'major_id':'CNTT'},{'major_id':'CNTT','cohort_id':'K23'}]:
        r=c.post('/api/configs',json={'name':'Phạm vi demo','payload':DEFAULT,**scope});assert r.status_code==201
        cid=r.json()['id'];ids.append(cid);assert c.post(f'/api/configs/{cid}/activate').status_code==200
    r=c.get('/api/students/000001').json();assert r['assessment']['config_id']==ids[-1]
    with f() as db: assert db.scalar(select(func.count()).select_from(ConfigVersion).where(ConfigVersion.active==True))==4
def test_simulation_leaves_database_unchanged(env):
    c,f=env;login(c,'advisor1');before=(count(f,AcademicResult),count(f,Evaluation))
    r=c.post('/api/students/000005/simulate?semester_id=6',json={'gpa':3,'registered':20,'failed':0})
    assert r.status_code==200;assert r.json()['before']['score']==71.5;assert r.json()['after']['score']<71.5
    assert before==(count(f,AcademicResult),count(f,Evaluation))
    assert c.post('/api/students/000005/simulate?semester_id=6',json={'gpa':5,'registered':20,'failed':0}).status_code==422
def test_simulation_cumulative_requires_explicit_assumptions(env):
    c,f=env;login(c,'advisor1')
    before=(count(f,AcademicResult),count(f,Evaluation))
    scenario={'gpa':3,'registered':20,'failed':0,'previous_gpa_credits':120}
    assert c.post('/api/students/000005/simulate?semester_id=6',json=scenario).json()['cumulative_gpa'] is None
    scenario.update(no_repeats=True,all_registered_count=True)
    response=c.post('/api/students/000005/simulate?semester_id=6',json=scenario)
    assert response.status_code==200
    out=response.json();assert out['cumulative_gpa']==2.7257
    assert out['before']['config_id']==out['after']['config_id']
    assert out['after']['evaluated_at'] and out['after']['persisted'] is False
    assert before==(count(f,AcademicResult),count(f,Evaluation))
def test_intervention_persistence_and_permissions(env):
    c,f=env;login(c,'advisor1');e=c.post('/api/students/000005/evaluate?semester_id=6').json()
    r=c.post('/api/interventions',json={'student_id':'000005','evaluation_id':e['evaluation_id'],'goal':'Mục tiêu demo','action':'Lập lịch học','due_date':'2026-01-01'});assert r.status_code==201
    pid=r.json()['id'];r=c.patch(f'/api/interventions/{pid}',json={'status':'Chờ theo dõi','note':'Đã trao đổi kế hoạch'});assert r.status_code==200;assert r.json()['overdue']
    with f() as db:assert db.get(Intervention,pid).status=='Chờ theo dõi';assert db.scalar(select(Followup).where(Followup.intervention_id==pid)).note=='Đã trao đổi kế hoạch'
    login(c,'advisor2');assert c.patch(f'/api/interventions/{pid}',json={'status':'Hoàn tất'}).status_code==404
def upload(c,kind,rows,mode='skip'):
    raw=csv_bytes(HEADERS[kind],rows)
    return c.post('/api/import/preview',data={'kind':kind,'mode':mode},files={'file':('data.csv',raw,'text/csv')})
def test_csv_atomic_errors_duplicates_and_confirm(env):
    c,f=env;login(c);before=count(f,Student)
    rows=[['009001','Hồ sơ giả lập','L1',2,'24','30','THPT'],['009002','Lỗi giả lập','NOCLASS',2,'24','30','THPT']]
    r=upload(c,'students',rows);assert r.status_code==200;b=r.json();assert b['errors']
    assert c.post('/api/import/'+b['id']+'/confirm').status_code==422;assert count(f,Student)==before
    r=upload(c,'students',[rows[0],rows[0]]);assert r.json()['errors'][0]['line']==3
    r=upload(c,'students',[rows[0]]);bid=r.json()['id'];assert c.post('/api/import/'+bid+'/confirm').json()['saved']==1
    assert count(f,Student)==before+1;assert c.post('/api/import/'+bid+'/confirm').status_code==409
    r=upload(c,'students',[rows[0]],'skip');assert r.json()['existing']==1;assert c.post('/api/import/'+r.json()['id']+'/confirm').json()['saved']==0
    rows[0][1]='Đã cập nhật giả lập';r=upload(c,'students',[rows[0]],'update');assert c.post('/api/import/'+r.json()['id']+'/confirm').status_code==200
    with f() as db:assert db.get(Student,'009001').name=='Đã cập nhật giả lập'
def test_csv_revalidates_on_confirm(env):
    c,f=env;login(c);rows=[['009002','Hồ sơ mới','L1',2,'24','30','THPT']]
    bid=upload(c,'students',rows).json()['id']
    with f() as db:db.get(User,2).active=False;db.commit()
    assert c.post('/api/import/'+bid+'/confirm').status_code==422
    with f() as db:assert db.get(Student,'009002') is None
def test_csv_invalid_gpa_rollback(env):
    c,f=env;login(c);rows=[['000001',6,5,3,20,20,0,120,80,'completed']]
    r=upload(c,'results',rows);assert r.status_code==200;assert r.json()['errors']
    with f() as db:assert db.scalar(select(AcademicResult).where(AcademicResult.student_id=='000001',AcademicResult.semester_id==6)).gpa==3.4
def test_consistent_filters_csv_chart_list(env):
    c,f=env;login(c,'advisor1');p='class_id=L1&semester_id=6&level='+ 'Nguy cơ cao'
    listing=c.get('/api/students?'+p).json();s=c.get('/api/summary?'+p).json();t=c.get('/api/trend?'+p).json()
    exported=list(csv.reader(io.StringIO(c.get('/api/export?'+p).content.decode('utf-8-sig'))))
    assert listing['total']==s['total']==sum(t[-1][l] for l in ['Bình thường','Cần chú ý','Nguy cơ cao','Chưa đủ dữ liệu'])==len(exported)-1
    assert all(row[2]=='L1' for row in exported[1:])
def test_csv_injection_escape():
    out=csv_bytes(['text'],[['=SUM(A1)'],['  @formula'],['normal']]).decode('utf-8-sig')
    assert "'=SUM(A1)" in out and "'  @formula" in out
def test_seed_idempotent(env):
    from app.seed import seed
    c,f=env
    with f() as db:assert seed(db,'TestOnlyDemo!2026') is False
    assert count(f,Student)==60
