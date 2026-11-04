import os
import tempfile
from pathlib import Path
import pytest

# Dependency failures remain collection errors; never silently skipped.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
os.environ.setdefault('EDUALERT_SECRET','test-only-session-secret-with-at-least-32-chars')
from app.db import Base,get_db
from app.main import app
from app.seed import seed

@pytest.fixture
def env(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'test.db'),connect_args={'check_same_thread':False})
    from sqlalchemy import event
    @event.listens_for(engine,'connect')
    def fk(conn,_):conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine);factory=sessionmaker(engine,expire_on_commit=False)
    with factory() as db:seed(db,'TestOnlyDemo!2026')
    def override():
        with factory() as db:yield db
    app.dependency_overrides[get_db]=override
    with TestClient(app) as client:yield client,factory
    app.dependency_overrides.clear();engine.dispose()

def login(client,username='admin'):
    import re
    page=client.get('/login');token=re.search('name="csrf" value="([^"]+)"',page.text)[1]
    response=client.post('/login',data={'username':username,'password':'TestOnlyDemo!2026','csrf':token},follow_redirects=False)
    assert response.status_code==303
    page=client.get('/dashboard');token=re.search('name="csrf-token" content="([^"]+)"',page.text)[1]
    client.headers['X-CSRF-Token']=token
    return token
