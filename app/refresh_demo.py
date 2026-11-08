"""Upgrade a recognized demo database atomically, with a backup. Standard library only.

Run with: python -m app.refresh_demo
Existing staff passwords, custom students and evaluation snapshots are preserved.
"""
import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from .schema_v2 import upgrade_sqlite
from .demo_data import student_profile, detailed_academics, course_catalog, CLASS_NAMES

def refresh_database(path):
    path=Path(path).resolve()
    if not path.is_file(): raise ValueError('Chưa có DB. Chạy migration và seed trước.')
    db=sqlite3.connect(path,timeout=20)
    db.row_factory=sqlite3.Row
    try:
        if not db.execute("SELECT 1 FROM audit_logs WHERE action='seed_demo' LIMIT 1").fetchone():
            raise ValueError('DB không được nhận diện là dữ liệu demo; không tự thay dữ liệu thật.')
        version=db.execute('SELECT version_num FROM alembic_version').fetchone()
        if not version or version[0] not in ('0001','0002'): raise ValueError('Phiên bản database chưa được hỗ trợ')
        if db.execute("SELECT 1 FROM audit_logs WHERE action='demo_upgrade_v2' LIMIT 1").fetchone():
            return {'updated':False,'message':'Dữ liệu phiên bản mới đã có; giữ nguyên các thao tác của người dùng.'}
        folder=path.parent/'backups';folder.mkdir(exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        backup=folder/f'{path.stem}-before-portal-{stamp}.db'
        with closing(sqlite3.connect(backup)) as dest: db.backup(dest)
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('BEGIN IMMEDIATE')
        upgrade_sqlite(db)
        db.execute("UPDATE alembic_version SET version_num='0002'")
        admin=db.execute("SELECT id,password_hash FROM users WHERE username='admin'").fetchone()
        if not admin: raise ValueError('Thiếu tài khoản quản trị demo')
        db.execute("UPDATE users SET name='Quản trị học vụ' WHERE username='admin' AND name='Quản trị Demo'")
        for username,name in [('advisor1','Trần Hải Nam'),('advisor2','Phạm Thu Hương')]:
            db.execute("UPDATE users SET name=? WHERE username=? AND name LIKE 'Cố vấn Demo%'",(name,username))
        for cid,name in CLASS_NAMES.items(): db.execute('UPDATE classrooms SET name=? WHERE id=?',(name,cid))
        for c in course_catalog():
            db.execute('INSERT OR IGNORE INTO courses(id,name,credits) VALUES(:id,:name,:credits)',c)
        changed=0
        for n in range(1,61):
            p=student_profile(n)
            original=db.execute('SELECT name FROM students WHERE id=?',(p['id'],)).fetchone()
            if not original or not original[0].startswith('Sinh viên mô phỏng'): continue
            # Names are a positive demo marker. User-created or renamed profiles are untouched.
            db.execute('UPDATE students SET name=:name,admission_score=:admission_score,admission_scale=:admission_scale,admission_method=:admission_method WHERE id=:id',p)
            rows,warnings,debts,grades=detailed_academics(n)
            for r in rows:
                db.execute('''UPDATE academic_results SET gpa=:gpa,cumulative_gpa=:cumulative_gpa,
                 registered=:registered,passed=:passed,failed=:failed,accumulated=:accumulated,conduct=:conduct
                 WHERE student_id=:student_id AND semester_id=:semester_id''',r)
            db.execute('DELETE FROM debts WHERE student_id=?',(p['id'],))
            for d in debts: db.execute('INSERT INTO debts(student_id,semester_id,course_id) VALUES(:student_id,:semester_id,:course_id)',d)
            for g in grades: db.execute('INSERT INTO course_results(student_id,semester_id,course_id,grade) VALUES(:student_id,:semester_id,:course_id,:grade)',g)
            username='student' if n==5 else 'sv'+p['id']
            if db.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone(): raise ValueError('Tên tài khoản đã tồn tại: '+username)
            cursor=db.execute("INSERT INTO users(username,name,password_hash,role,active) VALUES(?,?,?,'student',1)",(username,p['name'],admin['password_hash']))
            db.execute('INSERT INTO student_accounts(user_id,student_id) VALUES(?,?)',(cursor.lastrowid,p['id']))
            changed+=1
        violations=db.execute('PRAGMA foreign_key_check').fetchall()
        if violations: raise ValueError('Phát hiện tham chiếu không hợp lệ; rollback toàn bộ.')
        db.execute('INSERT INTO audit_logs(user_id,action,detail,created_at) VALUES(?,?,?,?)',
                   (admin['id'],'demo_upgrade_v2',json.dumps({'profiles':changed,'synthetic':True,'backup':backup.name}),datetime.now(timezone.utc).isoformat()))
        db.commit()
        return {'updated':True,'profiles':changed,'backup':str(backup),'student_login':'student / 000005','password':'Giống mật khẩu admin demo hiện tại; không đổi mật khẩu quản trị.'}
    except Exception:
        db.rollback();raise
    finally:
        db.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',default='data/edualert-v2.db')
    args=parser.parse_args()
    print(json.dumps(refresh_database(args.database),ensure_ascii=False,indent=2))
