"""Backed-up, atomic refresh of recognized seeded profiles, never a database reset."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .demo_catalog import CLASSES, student_profile, detailed_academics, course_catalog
from .demo_data import student_profile as old_profile


def upgrade_database(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError('Database chưa tồn tại; chạy migration và seed trước.')
    with closing(sqlite3.connect(path, timeout=20)) as db:
        db.row_factory = sqlite3.Row
        if not db.execute("SELECT 1 FROM audit_logs WHERE action='seed_demo'").fetchone():
            raise ValueError('Chỉ cập nhật database có dấu nhận diện seed demo.')
        if db.execute("SELECT 1 FROM audit_logs WHERE action='demo_upgrade_v3'").fetchone():
            return {'updated': False, 'message': 'Đã có dữ liệu khóa 23–25; giữ nguyên các chỉnh sửa tiếp theo.'}
        version = db.execute('SELECT version_num FROM alembic_version').fetchone()
        if not version or version[0] != '0003':
            raise ValueError('Chạy alembic upgrade head trước khi cập nhật dữ liệu demo.')
        recognized = []
        for number in range(1, 61):
            old = old_profile(number)
            row = db.execute('SELECT * FROM students WHERE id=?', (old['id'],)).fetchone()
            if row and (row['name'] == old['name'] or row['name'] == f'Sinh viên mô phỏng {number}'):
                recognized.append((number, old['id'], student_profile(number)))
        if not recognized:
            raise ValueError('Không tìm thấy hồ sơ demo cũ phù hợp; không tự thay hồ sơ đã chỉnh sửa.')
        old_ids = {old for _, old, _ in recognized}
        for cid, (name, _, cohort) in CLASSES.items():
            existing = db.execute('SELECT name,cohort_id FROM classrooms WHERE id=?', (cid,)).fetchone()
            if existing and existing['cohort_id'] != cohort:
                occupants = db.execute('SELECT id FROM students WHERE class_id=?', (cid,)).fetchall()
                if any(row['id'] not in old_ids for row in occupants):
                    raise ValueError('Lớp '+cid+' có hồ sơ riêng; cần chuyển lớp riêng trước khi cập nhật demo.')
        folder = path.parent / 'backups'
        folder.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        backup = folder / f'{path.stem}-before-cohorts-{stamp}.db'
        with closing(sqlite3.connect(backup)) as target:
            db.backup(target)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            db.execute('PRAGMA defer_foreign_keys=ON')
            for year in (23, 24, 25):
                db.execute('INSERT OR IGNORE INTO cohorts(id,name) VALUES(?,?)', (f'K{year}', f'Khóa 20{year}'))
            for cid, (name, major, cohort) in CLASSES.items():
                db.execute('INSERT INTO classrooms(id,name,major_id,cohort_id) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,major_id=excluded.major_id,cohort_id=excluded.cohort_id', (cid, name, major, cohort))
            for course in course_catalog():
                db.execute('INSERT OR IGNORE INTO courses(id,name,credits) VALUES(:id,:name,:credits)', course)
            from .services.configuration import PRESETS
            for preset,year in zip(PRESETS[1:],(23,24,25)):
                name=preset['name']+f' — Khóa {year}'
                if not db.execute('SELECT 1 FROM config_versions WHERE name=?',(name,)).fetchone():
                    db.execute('INSERT INTO config_versions(name,cohort_id,active,payload,created_at) VALUES(?,?,0,?,?)',
                               (name,f'K{year}',json.dumps(preset['payload']),datetime.now(timezone.utc).isoformat()))
            db.execute("UPDATE config_versions SET name='Đánh giá học tập chung' WHERE name='Bộ quy tắc minh họa phục vụ demo'")
            for number, old_id, profile in recognized:
                new_id = profile['id']
                if db.execute('SELECT 1 FROM students WHERE id=?', (new_id,)).fetchone():
                    raise ValueError('Mã sinh viên đích đã tồn tại: '+new_id)
                db.execute('UPDATE students SET id=:id,class_id=:class_id WHERE id=:old', {**profile, 'old': old_id})
                for table in ('student_accounts','academic_results','course_results','debts','warning_history','evaluations','interventions'):
                    db.execute('UPDATE '+table+' SET student_id=? WHERE student_id=?', (new_id, old_id))
                # Keep all account IDs, passwords, registered contacts, existing sessions and staff data.
                db.execute('UPDATE users SET username=? WHERE username=?', ('sv'+new_id, 'sv'+old_id))
                for table in ('academic_results','course_results','debts','warning_history'):
                    db.execute('DELETE FROM '+table+' WHERE student_id=?', (new_id,))
                rows, warnings, debts, grades = detailed_academics(number)
                for row in rows:
                    db.execute('INSERT INTO academic_results(student_id,semester_id,gpa,cumulative_gpa,registered,passed,failed,accumulated,conduct,status) VALUES(:student_id,:semester_id,:gpa,:cumulative_gpa,:registered,:passed,:failed,:accumulated,:conduct,:status)', row)
                for row in warnings:
                    db.execute('INSERT INTO warning_history(student_id,semester_id,warned) VALUES(:student_id,:semester_id,:warned)', row)
                for row in debts:
                    db.execute('INSERT INTO debts(student_id,semester_id,course_id) VALUES(:student_id,:semester_id,:course_id)', row)
                for row in grades:
                    db.execute('INSERT INTO course_results(student_id,semester_id,course_id,grade) VALUES(:student_id,:semester_id,:course_id,:grade)', row)
            # Historical evaluations and their original numeric inputs remain immutable.
            # The student_id references on the evaluation itself are already remapped above.
            db.execute("DELETE FROM cohorts WHERE id='K22' AND NOT EXISTS(SELECT 1 FROM classrooms WHERE cohort_id='K22') AND NOT EXISTS(SELECT 1 FROM config_versions WHERE cohort_id='K22')")
            violations = db.execute('PRAGMA foreign_key_check').fetchall()
            if violations:
                raise ValueError('Tham chiếu không hợp lệ; hủy toàn bộ cập nhật.')
            admin = db.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()[0]
            db.execute('INSERT INTO audit_logs(user_id,action,detail,created_at) VALUES(?,?,?,?)',
                (admin, 'demo_upgrade_v3', json.dumps({'profiles': len(recognized), 'backup': backup.name}), datetime.now(timezone.utc).isoformat()))
            db.commit()
        except Exception:
            db.rollback()
            raise
        return {'updated': True, 'profiles': len(recognized), 'backup': str(backup)}


if __name__ == '__main__':
    from .db import engine
    print(json.dumps(upgrade_database(engine.url.database), ensure_ascii=False, indent=2))
