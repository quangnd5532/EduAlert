import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from app.demo_data import course_catalog, detailed_academics, student_profile
from app.refresh_demo import refresh_database

def old_database(path):
    db=sqlite3.connect(path)
    db.executescript('''
      CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role in ('admin','advisor')),active BOOLEAN NOT NULL);
      CREATE TABLE classrooms(id TEXT PRIMARY KEY,name TEXT);
      CREATE TABLE semesters(id INTEGER PRIMARY KEY);
      CREATE TABLE students(id TEXT PRIMARY KEY,name TEXT,class_id TEXT,advisor_id INTEGER REFERENCES users(id),admission_score REAL,admission_scale REAL,admission_method TEXT);
      CREATE TABLE academic_results(id INTEGER PRIMARY KEY,student_id TEXT REFERENCES students(id),semester_id INTEGER,gpa REAL,cumulative_gpa REAL,registered INTEGER,passed INTEGER,failed INTEGER,accumulated INTEGER,conduct REAL);
      CREATE TABLE courses(id TEXT PRIMARY KEY,name TEXT,credits INTEGER);
      CREATE TABLE debts(id INTEGER PRIMARY KEY,student_id TEXT REFERENCES students(id),semester_id INTEGER,course_id TEXT REFERENCES courses(id));
      CREATE TABLE audit_logs(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),action TEXT,detail TEXT,created_at TEXT);
      CREATE TABLE alembic_version(version_num TEXT PRIMARY KEY);
      INSERT INTO alembic_version VALUES('0001');
      INSERT INTO users VALUES(1,'admin','Quản trị Demo','fake-test-hash','admin',1);
      INSERT INTO users VALUES(2,'advisor1','Cố vấn Demo A','fake-test-hash','advisor',1);
      INSERT INTO users VALUES(3,'advisor2','Cố vấn Demo B','fake-test-hash','advisor',1);
      INSERT INTO audit_logs(user_id,action,detail) VALUES(1,'seed_demo','{"synthetic":true}');
    ''')
    for i in range(1,5):db.execute('INSERT INTO classrooms VALUES(?,?)',(f'L{i}',f'Lớp {i}'))
    for i in range(1,8):db.execute('INSERT INTO semesters VALUES(?)',(i,))
    for n in range(1,61):
        p=student_profile(n);db.execute('INSERT INTO students(id,name,class_id,advisor_id) VALUES(?,?,?,?)',(p['id'],f'Sinh viên mô phỏng {n}',p['class_id'],p['advisor_id']))
        for r in detailed_academics(n)[0]:
            db.execute('INSERT INTO academic_results(student_id,semester_id,gpa,cumulative_gpa,registered,passed,failed,accumulated,conduct) VALUES(:student_id,:semester_id,:gpa,:cumulative_gpa,:registered,:passed,:failed,:accumulated,:conduct)',r)
    db.execute("INSERT INTO students(id,name,class_id,advisor_id) VALUES('CUSTOM','Hồ sơ được tạo riêng','L1',2)")
    db.commit();db.close()

class PortalDataTests(unittest.TestCase):
    def test_sixty_transcripts_reconcile(self):
        catalog={c['id']:c for c in course_catalog()}
        for n in range(1,61):
            rows,_,debts,grades=detailed_academics(n)
            total_registered=0
            for r in rows:
                with self.subTest(student=n,semester=r['semester_id']):
                    attempts=[g for g in grades if g['semester_id']==r['semester_id']]
                    self.assertEqual(sum(catalog[g['course_id']]['credits'] for g in attempts),r['registered'])
                    self.assertEqual(sum(catalog[g['course_id']]['credits'] for g in attempts if g['grade']==0),r['failed'])
                    self.assertTrue(all(g['grade'] is None or 0<=g['grade']<=4 for g in attempts))
                    if r['gpa'] is not None:
                        weighted=sum(g['grade']*catalog[g['course_id']]['credits'] for g in attempts)/r['registered']
                        self.assertAlmostEqual(weighted,r['gpa'],places=5)
                    total_registered+=r['registered']
                    outstanding=[d for d in debts if d['semester_id']==r['semester_id']]
                    self.assertEqual(len(outstanding),len({d['course_id'] for d in outstanding}))
                    self.assertEqual(sum(catalog[d['course_id']]['credits'] for d in outstanding)+r['accumulated'],total_registered)

    def test_admission_scales_and_natural_names(self):
        profiles=[student_profile(n) for n in range(1,61)]
        self.assertEqual(len({p['name'] for p in profiles}),60)
        self.assertEqual({p['admission_scale'] for p in profiles},{30,1200})
        self.assertTrue(all(0<=p['admission_score']<=p['admission_scale'] for p in profiles))
        self.assertTrue(all('mô phỏng' not in p['name'] for p in profiles))

    def test_cumulative_gpa_is_credit_weighted_and_missing_stays_unknown(self):
        for n in range(1,61):
            points=0;credits=0;known=True
            for r in detailed_academics(n)[0]:
                credits+=r['registered']
                if r['gpa'] is None:known=False
                else:points+=r['gpa']*r['registered']
                self.assertEqual(r['cumulative_gpa'],round(points/credits,2) if known else None)

    def test_upgrade_is_backed_up_atomic_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'demo.db';old_database(path)
            result=refresh_database(path)
            self.assertEqual(result['profiles'],60);self.assertTrue(Path(result['backup']).is_file())
            with closing(sqlite3.connect(path)) as db, db:
                self.assertEqual(db.execute('SELECT count(*) FROM student_accounts').fetchone()[0],60)
                self.assertEqual(db.execute("SELECT name FROM students WHERE id='CUSTOM'").fetchone()[0],'Hồ sơ được tạo riêng')
                self.assertEqual(db.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()[0],'fake-test-hash')
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
                self.assertEqual(db.execute('SELECT version_num FROM alembic_version').fetchone()[0],'0002')
            self.assertFalse(refresh_database(path)['updated'])
            self.assertEqual(len(list((Path(folder)/'backups').glob('*.db'))),1)

    def test_conflict_rolls_back_schema_and_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'demo.db';old_database(path)
            with closing(sqlite3.connect(path)) as db, db:db.execute("INSERT INTO users VALUES(99,'student','Existing account','hash','advisor',1)")
            with self.assertRaises(ValueError):refresh_database(path)
            with closing(sqlite3.connect(path)) as db, db:
                self.assertEqual(db.execute("SELECT name FROM students WHERE id='000001'").fetchone()[0],'Sinh viên mô phỏng 1')
                self.assertEqual(db.execute('SELECT version_num FROM alembic_version').fetchone()[0],'0001')
                self.assertIsNone(db.execute("SELECT 1 FROM sqlite_master WHERE name='student_accounts'").fetchone())

    def test_unmarked_database_is_not_modified(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'demo.db';old_database(path)
            with closing(sqlite3.connect(path)) as db, db:db.execute('DELETE FROM audit_logs')
            with self.assertRaises(ValueError):refresh_database(path)
            self.assertFalse((Path(folder)/'backups').exists())

if __name__=='__main__':unittest.main()
