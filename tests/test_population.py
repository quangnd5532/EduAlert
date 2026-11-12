import csv
import io
import json
import sqlite3
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from sqlalchemy import select,func

from app.demo_catalog import CLASSES,START,detailed_academics,student_id,student_profile,course_catalog
from app.models import *
from app.services.assessment import DEFAULT,evaluate,validate_config
from app.services.csv_import import HEADERS,parse_file,validate_rows
from app.services.import_samples import sample_rows
from app.services.sorting import SORT_OPTIONS
from app.upgrade_demo import upgrade_database
from tests.conftest import login


def test_admission_year_ids_and_transcripts_are_distinct_and_consistent():
    catalog={course['id']:course for course in course_catalog()}
    histories=[]
    for number in range(1,61):
        profile=student_profile(number)
        _,_,cohort=CLASSES[profile['class_id']]
        assert profile['id'].startswith(cohort[1:]) and len(profile['id'])==10
        rows,warnings,debts,grades=detailed_academics(number)
        assert rows[0]['semester_id']==START[cohort]
        assert len(rows)==7-START[cohort]
        assert all(row['student_id']==profile['id'] for row in [*rows,*warnings,*debts,*grades])
        histories.append(tuple(row['gpa'] for row in rows))
        registered=0
        for row in rows:
            attempts=[grade for grade in grades if grade['semester_id']==row['semester_id']]
            assert sum(catalog[grade['course_id']]['credits'] for grade in attempts)==row['registered']
            assert sum(catalog[grade['course_id']]['credits'] for grade in attempts if grade['grade']==0)==row['failed']
            if row['gpa'] is not None:
                assert sum(catalog[g['course_id']]['credits']*g['grade'] for g in attempts)/row['registered']==pytest.approx(row['gpa'],abs=1e-5)
            registered+=row['registered']
            assert sum(catalog[d['course_id']]['credits'] for d in debts if d['semester_id']==row['semester_id'])+row['accumulated']==registered
    assert len(set(histories))>50


def test_filters_sorts_pagination_and_export_have_same_order(env):
    client,_=env;login(client)
    for choice,_ in SORT_OPTIONS:
        response=client.get('/api/students',params={'sort':choice,'page_size':60})
        assert response.status_code==200,(choice,response.text)
        data=response.json();assert data['total']==60 and len(data['items'])==60
        if choice in ('gpa_asc','gpa_desc','risk','risk_asc','failed_desc','failed_asc','cumulative_desc','cumulative_asc'):
            field,reverse={'gpa_asc':('gpa',False),'gpa_desc':('gpa',True),'risk':('score',True),'risk_asc':('score',False),'failed_desc':('failed',True),'failed_asc':('failed',False),'cumulative_desc':('cumulative_gpa',True),'cumulative_asc':('cumulative_gpa',False)}[choice]
            values=[item['assessment']['score'] if field=='score' else item['academic'].get(field) for item in data['items']]
            known=[v for v in values if v is not None]
            assert known==sorted(known,reverse=reverse)
            assert values[:len(known)]==known
    params={'sort':'gpa_asc','cohort_id':'K24','page_size':60}
    listed=client.get('/api/students',params=params).json()
    exported=list(csv.reader(io.StringIO(client.get('/api/export',params=params).content.decode('utf-8-sig'))))
    assert [row[0] for row in exported[1:]]==[item['id'] for item in listed['items']]
    assert all(item['id'].startswith('24') for item in listed['items'])
    summary=client.get('/api/summary',params=params).json()
    assert [item['id'] for item in summary['priority']]==[item['id'] for item in listed['items'][:12]]
    assert client.get('/api/students?sort=bad').status_code==422
    assert client.get('/api/students?page_size=5000').status_code==422
    page=client.get('/api/students?page_size=24&page=9999').json()
    assert page['page']==3 and len(page['items'])==12


def test_missing_information_is_separate_from_insufficient_enrollment_history(env):
    client,_=env;login(client)
    new_student=next(student_id(n) for n in range(1,61) if CLASSES[student_profile(n)['class_id']][2]=='K25')
    result=client.get('/api/students/'+new_student).json()
    assert result['assessment']['score'] is None
    issues=result['assessment']['data_issues']
    assert issues and all(issue['kind']=='history' for issue in issues)
    assert all(issue['action'] for issue in issues)
    assert all('2023' not in issue['reason'] and '2024' not in issue['reason'] for issue in issues)
    assert len(result['semesters'])==3  # two regular semesters plus summer
    missing=client.get('/api/students/'+student_id(7)).json()['assessment']
    assert any(issue['kind']=='missing' and 'HK1' in issue['reason'] for issue in missing['data_issues'])
    assert all('clamp(' not in factor['reason'] for factor in missing['factors'])
    stable=client.get('/api/students/'+student_id(1)).json()['assessment']
    assert stable['score']==0 and 'ổn định' in stable['summary'] and not stable['missing']
    data=client.get('/api/students?data_quality=history&page_size=60').json()
    assert data['total']==20
    assert client.get('/api/students?data_quality=missing').json()['total']==1
    # No students are counted before they enrolled.
    assert client.get('/api/students?semester_id=1&page_size=60').json()['total']==22


def test_rule_missing_conduct_is_named_with_remediation():
    periods=[{'sequence':n,'name':f'HK{n}','kind':'regular','completed':True} for n in range(1,5)]
    rows=[{'sequence':n,'gpa':3,'cumulative_gpa':3,'registered':20,'passed':20,'failed':0,'status':'completed'} for n in range(1,5)]
    config=deepcopy(DEFAULT);config['rule']={'field':'conduct','op':'lt','value':50}
    result=evaluate(periods,rows,[{'sequence':n,'warned':False} for n in range(1,4)],4,config)
    assert result['score']==0 and result['rule']['state']=='unknown'
    assert any(issue['factor']=='Điểm rèn luyện' and 'Bổ sung' in issue['action'] for issue in result['data_issues'])
    assert 'conduct' not in result['rule']['reason']


def test_four_downloaded_samples_import_end_to_end(env):
    client,factory=env;login(client)
    for kind in ('students','results','debts','warnings'):
        response=client.get('/api/import/template/'+kind)
        rows=parse_file(response.content,kind)
        assert len(rows)==len(sample_rows()[kind]) and rows
        preview=client.post('/api/import/preview',data={'kind':kind,'mode':'skip'},files={'file':(kind+'.csv',response.content,'text/csv')})
        assert preview.status_code==200,preview.text
        result=preview.json();assert not result['errors'],result
        assert result['new']==len(rows) and result['save_count']==len(rows)
        saved=client.post('/api/import/'+result['id']+'/confirm')
        assert saved.status_code==200 and saved.json()['saved']==len(rows)
        repeat=client.post('/api/import/preview',data={'kind':kind,'mode':'skip'},files={'file':(kind+'.csv',response.content,'text/csv')}).json()
        assert repeat['skipped']==len(rows) and repeat['save_count']==0
        blank=list(csv.reader(io.StringIO(client.get('/api/import/template/'+kind+'?filled=false').content.decode('utf-8-sig'))))
        assert blank==[HEADERS[kind]]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Student))==66
        for sid in ('2351999001','2451999002','2551999005'):
            assert db.get(Student,sid)
            assert db.scalar(select(AcademicResult).where(AcademicResult.student_id==sid))


def test_csv_examples_reconcile_debts_to_accumulated_credits():
    examples=sample_rows();catalog={course['id']:course['credits'] for course in course_catalog()}
    for student in examples['students']:
        registered=0
        for row in (r for r in examples['results'] if r['student_id']==student['id']):
            registered+=row['registered']
            debts=sum(catalog[d['course_id']] for d in examples['debts'] if d['student_id']==row['student_id'] and d['semester_id']==row['semester_id'])
            assert debts+row['accumulated']==registered
    for kind in HEADERS:
        assert parse_file(Path('samples',kind+'_valid.csv').read_bytes(),kind)


def test_csv_errors_are_actionable_and_columns_can_be_reordered(env):
    client,factory=env
    with factory() as db:
        row=deepcopy(sample_rows()['students'][0]);row['id']='2451999999'
        _,errors,_=validate_rows(db,'students',[row],'skip')
        assert any(error['column']=='id' and '23' in error['message'] for error in errors)
        _,errors,_=validate_rows(db,'warnings',[{'student_id':student_id(1),'semester_id':6,'warned':''}],'skip')
        assert errors and 'true' in errors[0]['message']
    text='semester_id;warned;student_id\n6;false;'+student_id(1)+'\n'
    assert parse_file(text.encode(),'warnings')[0]['warned']=='false'
    with pytest.raises(ValueError,match='Thiếu cột'):
        parse_file(b'student_id,warned\na,false','warnings')
    with pytest.raises(ValueError,match='Dòng 2'):
        parse_file(b'student_id,semester_id,warned\na,6,false,extra','warnings')


def test_config_drafts_edit_copy_preview_and_activation_preserve_history(env):
    client,factory=env;login(client)
    versions=client.get('/api/configs').json();assert len(versions)==4
    draft=next(version for version in versions if not version['active'])
    body={key:draft[key] for key in ('name','major_id','cohort_id','payload')}
    body['payload']['weights']=[40,30,20,10]
    edited=client.put('/api/configs/'+str(draft['id']),json=body)
    assert edited.status_code==200
    with factory() as db: before=db.scalar(select(func.count()).select_from(Evaluation))
    preview=client.post(f'/api/configs/{draft["id"]}/preview?semester_id=6').json()
    assert preview['total']==60 and preview['applicable']>0
    assert sum(row['after'] for row in preview['distribution'])==preview['total']
    assert preview['score_changed']>=preview['changed']
    assert 'semester_name' in preview and 'examples' in preview
    with factory() as db: assert db.scalar(select(func.count()).select_from(Evaluation))==before
    assert client.post('/api/configs/'+str(draft['id'])+'/activate').status_code==200
    assert client.put('/api/configs/'+str(draft['id']),json=body).status_code==409
    assert client.post(f'/api/configs/{draft["id"]}/preview?semester_id=7').status_code==422
    login(client,'advisor1')
    assert client.put('/api/configs/'+str(draft['id']),json=body).status_code==403


@pytest.mark.parametrize('field,value',[('weights',[True,25,25,49]),('fail_span',1.1),('repeat_span',3.5),('gpa_span',5),('attention',True)])
def test_invalid_configuration_values_rejected(field,value):
    config=deepcopy(DEFAULT);config[field]=value
    with pytest.raises(ValueError): validate_config(config)


def test_settings_and_import_render_human_forms(env):
    client,_=env;login(client)
    settings=client.get('/settings').text
    assert 'id="rule-editor"' in settings and 'name="fail_percent"' in settings
    assert 'name="payload"' not in settings and 'config-json' not in settings
    assert '/static/configuration.js' in settings and 'Khóa 2025' in settings
    imports=client.get('/import').text
    assert imports.count('Tải mẫu có dữ liệu')==4 and 'Tra mã lớp' in imports
    assert 'true' in imports and 'false' in imports
    assert 'GPA học kỳ: thấp đến cao' in client.get('/students').text


def test_refresh_preserves_accounts_contacts_history_and_is_idempotent(env,tmp_path):
    _,factory=env
    path=tmp_path/'legacy-population.db'
    source=sqlite3.connect(factory.kw['bind'].url.database);target=sqlite3.connect(path)
    source.backup(target);source.close();target.close()
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('CREATE TABLE alembic_version(version_num TEXT PRIMARY KEY)')
        db.execute("INSERT INTO alembic_version VALUES('0003')")
        db.execute("DELETE FROM audit_logs WHERE action='demo_upgrade_v3'")
        for number in range(1,61):
            old=f'{number:06}';new=student_id(number)
            db.execute('UPDATE students SET id=? WHERE id=?',(old,new))
            for table in ('student_accounts','academic_results','course_results','debts','warning_history','evaluations','interventions'):
                db.execute('UPDATE '+table+' SET student_id=? WHERE student_id=?',(old,new))
        uid=db.execute("SELECT id FROM users WHERE username='student'").fetchone()[0]
        db.execute('UPDATE student_accounts SET email=?,phone=? WHERE user_id=?',('registered@example.edu','+84912345678',uid))
        password=db.execute('SELECT password_hash FROM users WHERE id=?',(uid,)).fetchone()[0]
        old_history=db.execute('SELECT id,input_data,output FROM evaluations ORDER BY id').fetchall()
    result=upgrade_database(path)
    assert result['profiles']==60 and Path(result['backup']).is_file()
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert db.execute('SELECT password_hash FROM users WHERE id=?',(uid,)).fetchone()[0]==password
        assert db.execute('SELECT student_id,email,phone FROM student_accounts WHERE user_id=?',(uid,)).fetchone()==(student_id(5),'registered@example.edu','+84912345678')
        assert db.execute('SELECT id,input_data,output FROM evaluations ORDER BY id').fetchall()==old_history
    assert not upgrade_database(path)['updated']
