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
    cumulative_rule=next(c for c in out['after']['rule']['children'] if c.get('field')=='cumulative_gpa')
    assert cumulative_rule['actual']==2.7257 and cumulative_rule['state']=='false'
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

def test_student_portal_is_private_and_staff_writes_are_forbidden(env):
    c,f=env;login(c,'student')
    me=c.get('/api/me').json()
    assert me['profile']['id']=='000005' and me['assessment']['score']==71.5
    assert me['courses'] and all('notes' not in p for p in me['appointments'])
    assert c.get('/api/me?student_id=000003').json()['profile']['id']=='000005'
    for path in ['/api/students','/api/summary','/api/export','/api/interventions','/students','/admin','/reports']:
        assert c.get(path).status_code==403,path
    assert c.post('/api/interventions',json={'student_id':'000005','evaluation_id':1,'goal':'Test goal','action':'Test action','due_date':'2027-01-01'}).status_code==403
    assert c.post('/api/students/000003/simulate?semester_id=6',json={'gpa':3,'registered':20,'failed':0}).status_code==404
    exported=c.get('/api/me/export').content.decode('utf-8-sig')
    assert '000005' in exported and '000003' not in exported
    html=c.get('/dashboard').text
    assert 'Không gian sinh viên' in html and 'Nhóm 5A' not in html

def test_student_simulation_and_appointment(env):
    from datetime import date,timedelta
    c,f=env;login(c,'000005')
    before=count(f,AcademicResult)
    r=c.post('/api/me/simulate?semester_id=6',json={'gpa':3,'registered':20,'failed':0})
    assert r.status_code==200 and r.json()['after']['score']==15
    assert count(f,AcademicResult)==before
    r=c.post('/api/me/appointments',json={'due_date':(date.today()+timedelta(days=7)).isoformat(),'message':'Em muốn trao đổi kế hoạch đăng ký học phần.'})
    assert r.status_code==201
    with f() as db:assert db.get(Intervention,r.json()['id']).student_id=='000005'

def test_student_pages_are_distinct_server_rendered_documents(env):
    import re
    from html.parser import HTMLParser
    class IDs(HTMLParser):
        def __init__(self):super().__init__();self.values=[]
        def handle_starttag(self,tag,attrs):
            self.values.extend(value for name,value in attrs if name=='id')
    c,f=env;login(c,'student')
    pages={'overview':'Tổng quan','results':'Kết quả học tập','analysis':'Phân tích học tập',
           'planning':'Kế hoạch học tập','appointments':'Cố vấn &amp; lịch hẹn','profile':'Thông tin sinh viên'}
    for view,title in pages.items():
        response=c.get('/student/'+view)
        assert response.status_code==200,(view,response.text)
        html=response.text
        assert '<h1>'+title+'</h1>' in html
        assert 'Nhóm 5A' not in html and '2351010170' not in html
        assert ('id="my-simulation"' in html)==(view=='planning')
        assert ('id="my-appointment-form"' in html)==(view=='appointments')
        assert ('class="transcript"' in html)==(view=='results')
        assert ('id="my-gpa"' in html)==(view=='overview')
        assert ('id="semester-filter"' in html)==(view!='profile')
        parser=IDs();parser.feed(html);assert len(parser.values)==len(set(parser.values)),view
        assert '/student/results?semester_id=6' in html
    assert c.get('/student/not-a-page').status_code==404
    assert c.get('/dashboard',follow_redirects=False).headers['location']=='/student/overview'

def test_transcript_filters_and_export_match_on_selected_semester(env):
    import re
    c,f=env;login(c,'student')
    source=c.get('/api/me?semester_id=4').json()
    course=source['courses'][0]
    params={'semester_id':4,'q':course['name']}
    response=c.get('/student/results',params=params)
    assert response.status_code==200
    transcript=re.search(r'<table class="transcript">(.*?)</table>',response.text,re.S).group(1)
    assert course['id'] in transcript and 'Hiển thị 1 /' in response.text
    assert '/student/analysis?semester_id=4' in response.text
    exported=list(csv.reader(io.StringIO(c.get('/api/me/export',params=params).content.decode('utf-8-sig'))))
    assert len(exported)==2 and exported[1][3]==course['id']
    assert exported[1][2]==source['semester_name']
    empty=c.get('/student/results',params={'q':'không có học phần này'})
    assert empty.status_code==200 and 'Không có học phần phù hợp' in empty.text

def test_student_pages_permissions_and_invalid_semesters(env):
    c,f=env;login(c,'advisor1')
    assert c.get('/student/results').status_code==403
    login(c,'student')
    assert c.get('/student/results?semester_id=7').status_code==422
    assert c.get('/student/results?semester_id=999').status_code==404
    assert c.get('/student/results?course_status=invalid').status_code==422
    assert c.post('/api/me/simulate?semester_id=7',json={'gpa':3,'registered':20,'failed':0}).status_code==422

def test_native_student_forms_work_without_javascript(env):
    import re
    from datetime import date,timedelta
    c,f=env;token=login(c,'student');c.headers.pop('X-CSRF-Token')
    html=c.get('/student/planning').text
    assert re.search(r'<form[^>]+id="my-simulation"[^>]+method="post"',html)
    before=count(f,AcademicResult)
    response=c.post('/student/planning?semester_id=6',data={'csrf':token,'gpa':3,'registered':20,'failed':0,
                   'previous_gpa_credits':120,'no_repeats':'on','all_registered_count':'on'})
    assert response.status_code==200 and 'Đối chiếu kịch bản' in response.text and '2.73' in response.text
    assert count(f,AcademicResult)==before
    response=c.post('/student/appointments?semester_id=6',data={'csrf':token,
                    'due_date':(date.today()+timedelta(days=7)).isoformat(),'message':'Em cần hỗ trợ kế hoạch học tập kỳ tiếp theo.'},follow_redirects=False)
    assert response.status_code==303
    assert 'sent=' in response.headers['location'] and 'message' not in response.headers['location']
    page=c.get(response.headers['location']);assert 'Em cần hỗ trợ kế hoạch học tập kỳ tiếp theo.' in page.text
    assert c.post('/student/appointments',data={'due_date':'2027-01-01','message':'Không có mã CSRF'}).status_code==403
    for padded in ['          ','  short   ']:
        assert c.post('/student/appointments',data={'csrf':token,'due_date':'2027-01-01','message':padded}).status_code==422

def test_summer_result_keeps_its_name_in_history(env):
    c,f=env;login(c,'student')
    with f() as db:
        db.add(Semester(id=8,name='HK1 · 2026–2027',sequence=8,kind='regular',completed=True))
        db.add(AcademicResult(student_id='000005',semester_id=7,gpa=3,cumulative_gpa=2.7,registered=3,passed=3,failed=0,accumulated=109,status='completed'))
        db.commit()
    response=c.get('/student/results?semester_id=8')
    assert response.status_code==200
    assert '<td>Hè 2026 (không tính xu hướng)</td>' in response.text
