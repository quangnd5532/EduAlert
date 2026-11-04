from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime, Date, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
def now():
    return datetime.now(timezone.utc)
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    __table_args__ = (CheckConstraint("role in ('admin','advisor')"),)
class Major(Base):
    __tablename__ = 'majors'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
class Cohort(Base):
    __tablename__ = 'cohorts'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
class Classroom(Base):
    __tablename__ = 'classrooms'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    major_id = Column(ForeignKey('majors.id'), nullable=False)
    cohort_id = Column(ForeignKey('cohorts.id'), nullable=False)
class Semester(Base):
    __tablename__ = 'semesters'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sequence = Column(Integer, unique=True, nullable=False)
    kind = Column(String, default='regular', nullable=False)
    completed = Column(Boolean, default=True, nullable=False)
class Student(Base):
    __tablename__ = 'students'
    id = Column(String(30), primary_key=True)
    name = Column(String(120), nullable=False)
    class_id = Column(ForeignKey('classrooms.id'), nullable=False)
    advisor_id = Column(ForeignKey('users.id'), nullable=False)
    admission_score = Column(Float)
    admission_scale = Column(Float)
    admission_method = Column(String)
class AcademicResult(Base):
    __tablename__ = 'academic_results'
    id = Column(Integer, primary_key=True)
    student_id = Column(ForeignKey('students.id'), nullable=False)
    semester_id = Column(ForeignKey('semesters.id'), nullable=False)
    gpa = Column(Float)
    cumulative_gpa = Column(Float)
    registered = Column(Integer, nullable=False)
    passed = Column(Integer, nullable=False)
    failed = Column(Integer, nullable=False)
    accumulated = Column(Integer)
    conduct = Column(Float)
    status = Column(String, default='completed', nullable=False)
    __table_args__ = (UniqueConstraint('student_id','semester_id'), CheckConstraint('registered >= 0 AND passed >= 0 AND failed >= 0 AND passed + failed = registered'), CheckConstraint('gpa IS NULL OR (gpa >= 0 AND gpa <= 4)'), CheckConstraint('cumulative_gpa IS NULL OR (cumulative_gpa >= 0 AND cumulative_gpa <= 4)'))
class Course(Base):
    __tablename__ = 'courses'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
class Debt(Base):
    __tablename__ = 'debts'
    id = Column(Integer, primary_key=True)
    student_id = Column(ForeignKey('students.id'), nullable=False)
    course_id = Column(ForeignKey('courses.id'), nullable=False)
    semester_id = Column(ForeignKey('semesters.id'), nullable=False)
    __table_args__ = (UniqueConstraint('student_id','course_id','semester_id'),)
class WarningHistory(Base):
    __tablename__ = 'warning_history'
    id = Column(Integer, primary_key=True)
    student_id = Column(ForeignKey('students.id'), nullable=False)
    semester_id = Column(ForeignKey('semesters.id'), nullable=False)
    warned = Column(Boolean, nullable=False)
    __table_args__ = (UniqueConstraint('student_id','semester_id'),)
class ConfigVersion(Base):
    __tablename__ = 'config_versions'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    major_id = Column(ForeignKey('majors.id'))
    cohort_id = Column(ForeignKey('cohorts.id'))
    active = Column(Boolean, default=False, nullable=False)
    activated_at = Column(DateTime)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=now)
class Evaluation(Base):
    __tablename__ = 'evaluations'
    id = Column(Integer, primary_key=True)
    student_id = Column(ForeignKey('students.id'), nullable=False)
    semester_id = Column(ForeignKey('semesters.id'), nullable=False)
    config_id = Column(ForeignKey('config_versions.id'))
    input_data = Column(JSON, nullable=False)
    output = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=now)
class Intervention(Base):
    __tablename__ = 'interventions'
    id = Column(Integer, primary_key=True)
    student_id = Column(ForeignKey('students.id'), nullable=False)
    evaluation_id = Column(ForeignKey('evaluations.id'), nullable=False)
    owner_id = Column(ForeignKey('users.id'), nullable=False)
    goal = Column(String, nullable=False)
    action = Column(String, nullable=False)
    status = Column(String, default='Chưa xử lý', nullable=False)
    due_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=now)
class Followup(Base):
    __tablename__ = 'followups'
    id = Column(Integer, primary_key=True)
    intervention_id = Column(ForeignKey('interventions.id'), nullable=False)
    author_id = Column(ForeignKey('users.id'), nullable=False)
    note = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)
class Audit(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.id'))
    action = Column(String, nullable=False)
    detail = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=now)
class ImportBatch(Base):
    __tablename__ = 'import_batches'
    id = Column(String, primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    kind = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    rows = Column(JSON, nullable=False)
    errors = Column(JSON, nullable=False)
    consumed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)
