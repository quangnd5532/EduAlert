"""Frozen SQLite DDL shared by Alembic and the local demo upgrader."""
UPGRADE_SQL = (
    """CREATE TABLE users_v2 (
      id INTEGER PRIMARY KEY, username VARCHAR(80) NOT NULL UNIQUE,
      name VARCHAR(120) NOT NULL, password_hash VARCHAR NOT NULL,
      role VARCHAR NOT NULL CONSTRAINT ck_users_role CHECK(role IN ('admin','advisor','student')),
      active BOOLEAN NOT NULL DEFAULT 1)""",
    'INSERT INTO users_v2 SELECT id,username,name,password_hash,role,active FROM users',
    'DROP TABLE users',
    'ALTER TABLE users_v2 RENAME TO users',
    """CREATE TABLE student_accounts (
      user_id INTEGER PRIMARY KEY REFERENCES users(id),
      student_id VARCHAR(30) NOT NULL UNIQUE REFERENCES students(id))""",
    """CREATE TABLE course_results (
      id INTEGER PRIMARY KEY, student_id VARCHAR(30) NOT NULL REFERENCES students(id),
      semester_id INTEGER NOT NULL REFERENCES semesters(id),
      course_id VARCHAR NOT NULL REFERENCES courses(id), grade FLOAT,
      CONSTRAINT ck_course_grade CHECK(grade IS NULL OR (grade >= 0 AND grade <= 4)),
      UNIQUE(student_id,semester_id,course_id))""",
)

def upgrade_sqlite(connection):
    """Caller owns transaction; foreign_keys must be OFF before BEGIN."""
    sql = connection.execute("SELECT sql FROM sqlite_master WHERE name='student_accounts'").fetchone()
    if sql:
        return False
    for statement in UPGRADE_SQL:
        connection.execute(statement)
    return True
