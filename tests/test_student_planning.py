from copy import deepcopy

import pytest
from sqlalchemy import select,func

from app.models import AcademicResult,Evaluation
from app.services.student_planning import learning_guidance,student_outlook
from tests.conftest import login


def model():
    return {'semester_id':6,'current':{'gpa':1.9,'cumulative_gpa':2.68,'registered':20,'failed':8},
        'history':[{'gpa':gpa,'status':'completed'} for gpa in (2.8,2.3,1.9)],
        'debts':[{'course_id':'old','name':'Học phần chưa hoàn thành','credits':4}],
        'courses':[{'id':'weak','name':'Môn điểm thấp','credits':3,'grade':1.5},
                   {'id':'failed','name':'Môn chưa đạt','credits':2,'grade':0},
                   {'id':'good','name':'Môn học tốt','credits':4,'grade':3.8}]}


def goal(**overrides):
    return {'gpa':3,'registered':18,'failed':3,'previous_gpa_credits':76,
            'no_repeats':True,'all_registered_count':True,**overrides}


def test_goal_explains_required_grades_and_real_gpa_change():
    before=model();data=goal();saved=deepcopy((before,data))
    result=student_outlook(before,data,{'cumulative_gpa':2.7413})
    assert result['feasible']
    assert result['required_passing_gpa']==3.6
    assert result['difference']==1.1 and result['passed']==15
    assert '3.60/4' in result['title'] and '15 tín chỉ' in result['message']
    assert result['cumulative_gpa']==2.7413
    assert (before,data)==saved


def test_impossible_target_never_promises_reachable_cumulative_gpa():
    result=student_outlook(model(),goal(gpa=3.8),{'cumulative_gpa':3.1})
    assert not result['feasible']
    assert result['maximum_gpa']==pytest.approx(3.3333)
    assert result['required_passing_gpa']==pytest.approx(4.56)
    assert result['cumulative_gpa'] is None
    assert '3.33/4' in result['message']
    assert any('điều chỉnh' in text or 'đặt lại' in text for text in result['next_steps'])


@pytest.mark.parametrize('gpa,feasible',[(3,False),(0,True)])
def test_no_passing_credits_avoids_division_by_zero(gpa,feasible):
    result=student_outlook(model(),goal(gpa=gpa,failed=18),{})
    assert result['feasible']==feasible
    assert result['required_passing_gpa'] is None
    assert result['maximum_gpa']==0 and result['next_steps']


def test_lower_target_is_not_presented_as_improvement():
    result=student_outlook(model(),goal(gpa=1.5,failed=0),{})
    assert result['difference']==-.4
    assert any('thấp hơn GPA của kỳ đang xem' in text for text in result['next_steps'])


def test_missing_current_gpa_is_never_filled_with_zero():
    data=model();data['current']={'gpa':None,'cumulative_gpa':None,'registered':20,'failed':0}
    result=student_outlook(data,goal(),{})
    assert result['current_gpa'] is None and result['difference'] is None
    assert 'chưa có GPA tích lũy' in result['cumulative_reason']
    assert 'Kiểm tra bảng điểm' in learning_guidance(data)['actions'][0]['title']


def test_course_priorities_follow_actual_records_and_credit_load():
    source=model();saved=deepcopy(source)
    guidance=learning_guidance(source)
    assert [course['id'] for course in guidance['courses']]==['old','failed','weak']
    assert all(course['id']!='good' for course in guidance['courses'])
    assert any('GPA ba kỳ' in action['reason'] for action in guidance['actions'])
    assert len(guidance['weekly_steps'])==3
    assert source==saved
    outlook=student_outlook(source,goal(registered=24,failed=0),{})
    assert any('nhiều hơn' in note and 'cố vấn' in note for note in outlook['next_steps'])


def test_student_planning_api_and_native_form_share_human_readable_results(env):
    client,factory=env;token=login(client,'student')
    with factory() as db:
        before=[db.scalar(select(func.count()).select_from(entity)) for entity in (AcademicResult,Evaluation)]
    response=client.post('/api/me/simulate?semester_id=6',json=goal())
    assert response.status_code==200,response.text
    result=response.json();html=result['student_html']
    assert result['outlook']['required_passing_gpa']==3.6
    for expected in ('3.60/4','15 tín chỉ','2.74/4','Bạn cần làm gì','GPA học kỳ đang xem'):
        assert expected in html
    for internal in ('Đóng góp','Điểm hỗ trợ','kỳ giả định','Cấu hình #','UTC'):
        assert internal not in html
    native=client.post('/student/planning?semester_id=6',data={**goal(),'csrf':token})
    assert native.status_code==200
    assert html in native.text
    assert 'Bạn nên ưu tiên điều gì?' in native.text
    assert 'Học phần nên dành thêm thời gian' in native.text
    assert 'Việc bạn có thể bắt đầu tuần này' in native.text
    assert 'Đóng góp giả định' not in native.text and 'Điểm hỗ trợ' not in native.text
    with factory() as db:
        after=[db.scalar(select(func.count()).select_from(entity)) for entity in (AcademicResult,Evaluation)]
    assert after==before


def test_optional_cumulative_gpa_and_impossible_goal_have_clear_next_steps(env):
    client,_=env;login(client,'student')
    result=client.post('/api/me/simulate?semester_id=6',json=goal(no_repeats=False)).json()
    assert result['outlook']['cumulative_gpa'] is None
    assert 'môn học lại' in result['student_html']
    result=client.post('/api/me/simulate?semester_id=6',json=goal(gpa=3.8)).json()
    assert not result['outlook']['feasible']
    assert 'Kiểm tra lại mục tiêu' in result['student_html']
    assert 'Nếu đạt mục tiêu này' not in result['student_html']


def test_planning_guidance_escapes_course_names_and_is_own_account_only(env):
    client,factory=env;login(client,'student')
    from app.models import Debt,Course
    with factory() as db:
        course_id=db.scalar(select(Debt.course_id).where(Debt.student_id=='2351000005',Debt.semester_id==6).order_by(Debt.id))
        db.get(Course,course_id).name='<img src=x onerror=alert(1)>'
        db.commit()
    page=client.get('/student/planning').text
    assert '<img src=x' not in page and '&lt;img src=x' in page
    assert '2351000005' in page and '2352000003' not in page
    login(client,'advisor1')
    assert client.post('/api/me/simulate?semester_id=6',json=goal()).status_code==403
