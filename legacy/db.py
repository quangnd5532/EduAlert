import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .models import Settings

DB_PATH = Path(os.environ.get('EDUALERT_DB', Path(__file__).resolve().parent.parent / 'data' / 'edualert.db'))


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS students (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS terms (student_id TEXT REFERENCES students(id), year INTEGER, semester INTEGER, payload TEXT NOT NULL, PRIMARY KEY(student_id, year, semester));
            CREATE TABLE IF NOT EXISTS interventions (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT REFERENCES students(id), payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL);
        ''')
        db.execute('INSERT OR IGNORE INTO settings VALUES (1, ?)', (json.dumps(Settings().model_dump()),))


def load_settings(db):
    return Settings(**json.loads(db.execute('SELECT payload FROM settings WHERE id=1').fetchone()[0]))


def get_terms(db, student_id):
    return [json.loads(r[0]) for r in db.execute('SELECT payload FROM terms WHERE student_id=? ORDER BY year, semester', (student_id,))]


def seed_demo():
    from .demo import records
    from .models import Student, Term, Intervention
    students, interventions = records()
    with connect() as db:
        if db.execute('SELECT COUNT(*) FROM students').fetchone()[0]:
            return False
        for record in students:
            student = Student(**record)
            db.execute('INSERT INTO students VALUES (?,?)', (student.id, student.model_dump_json()))
            for data in record['terms']:
                term = Term(**data)
                db.execute('INSERT INTO terms VALUES (?,?,?,?)', (student.id, term.year, term.semester, term.model_dump_json()))
        for data in reversed(interventions):
            item = Intervention(**data)
            db.execute('INSERT INTO interventions(student_id,payload,created_at) VALUES (?,?,?)', (item.student_id, item.model_dump_json(), data['created_at']))
    return True
