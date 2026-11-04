"""Integration tests: run after installing requirements.txt. Uses an isolated DB."""
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import db
from app.main import app


@pytest.fixture
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setattr(db, 'DB_PATH', Path(directory) / 'test.db')
        with TestClient(app) as client:
            yield client


def test_demo_and_persistence(client):
    assert client.get('/api/students').json() == []
    assert client.post('/api/demo').status_code == 200
    students = client.get('/api/students').json()
    assert len(students) == 24
    assert len(students[0]['terms']) == 3
    assert client.post('/api/demo').status_code == 409
    assert client.get('/').status_code == 200
    assert client.get('/static/app.js').status_code == 200


def test_csv_atomicity_and_upsert(client):
    sample = client.get('/api/import/template').content.decode('utf-8-sig')
    invalid = sample + sample.splitlines()[1].replace('2351010999', '2351010998').replace(',2.5,', ',8.5,') + '\r\n'
    assert client.post('/api/import', content=invalid.encode()).status_code == 422
    assert client.get('/api/students').json() == []
    assert client.post('/api/import', content=sample.encode()).status_code == 200
    assert client.post('/api/import', content=sample.encode()).status_code == 200
    students = client.get('/api/students').json()
    assert len(students) == 1
    assert len(students[0]['terms']) == 1


def test_validation_and_intervention_update(client):
    client.post('/api/demo')
    student = client.get('/api/students').json()[0]
    term = student['latest'] | {'passed': 0, 'failed': 0}
    assert client.put(f"/api/students/{student['id']}/terms", json=term).status_code == 422
    item = dict(student_id=student['id'], advisor='Cố vấn', note='Trao đổi', action='Phụ đạo', due_date='2026-11-20')
    result = client.post('/api/interventions', json=item)
    assert result.status_code == 201
    item_id = result.json()['id']
    assert client.put(f'/api/interventions/{item_id}', json=item | {'status':'completed', 'outcome':'Đã cải thiện'}).status_code == 200
    saved = next(x for x in client.get('/api/interventions').json() if x['id'] == item_id)
    assert saved['status'] == 'completed'
    assert client.post('/api/interventions', json=item | {'due_date':'2026-02-30'}).status_code == 422
    assert client.put('/api/settings', json={'attention':70,'high':60}).status_code == 422


def test_export_is_utf8_and_formula_safe(client):
    student = dict(id='ST01',name='=1+1',class_name='A',major='CNTT',cohort='2023',advisor='CV')
    assert client.post('/api/students', json=student).status_code == 201
    assert client.post('/api/students', json=student).status_code == 409
    response = client.get('/api/export')
    assert response.content.startswith(b'\xef\xbb\xbf')
    assert "'=1+1" in response.content.decode('utf-8-sig')
