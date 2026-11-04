from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Student(BaseModel):
    id: str = Field(min_length=1, max_length=30, pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1, max_length=120)
    class_name: str = Field(min_length=1, max_length=60)
    major: str = Field(min_length=1, max_length=100)
    cohort: str = Field(min_length=1, max_length=30)
    advisor: str = Field(min_length=1, max_length=100)
    admission_score: float | None = Field(default=None, ge=0)
    admission_scale: float = Field(default=30, gt=0, le=1000)
    admission_method: str = Field(default='THPT', max_length=100)

    @model_validator(mode='after')
    def score_within_scale(self):
        if self.admission_score is not None and self.admission_score > self.admission_scale:
            raise ValueError('Điểm tuyển sinh vượt thang điểm')
        for key in ('name', 'class_name', 'major', 'cohort', 'advisor'):
            value = getattr(self, key).strip()
            if not value:
                raise ValueError(f'{key} không được để trống')
            setattr(self, key, value)
        return self


class Term(BaseModel):
    year: int = Field(ge=2000, le=2100)
    semester: int = Field(ge=1, le=3)
    gpa: float = Field(ge=0, le=4)
    cumulative_gpa: float = Field(ge=0, le=4)
    registered: int = Field(ge=1, le=60)
    passed: int = Field(ge=0, le=60)
    failed: int = Field(ge=0, le=60)
    debt: int = Field(default=0, ge=0, le=200)
    conduct: float | None = Field(default=None, ge=0, le=100)
    previous_warnings: int = Field(default=0, ge=0, le=30)

    @model_validator(mode='after')
    def credits(self):
        if self.passed + self.failed != self.registered:
            raise ValueError('Tín chỉ đạt + không đạt phải bằng tín chỉ đăng ký')
        return self


class Settings(BaseModel):
    name: str = Field(default='Bộ quy tắc minh họa', min_length=1, max_length=120)
    cohort: str = Field(default='*', min_length=1, max_length=30)
    academic_gpa: float = Field(default=1.2, ge=0, le=4)
    academic_cumulative: float = Field(default=1.8, ge=0, le=4)
    academic_failed_ratio: float = Field(default=0.5, gt=0, le=1)
    low_gpa: float = Field(default=2.0, ge=0, le=4)
    low_gpa_weight: int = Field(default=30, ge=0, le=100)
    decline_weight: int = Field(default=25, ge=0, le=100)
    failed_weight: int = Field(default=20, ge=0, le=100)
    repeat_weight: int = Field(default=15, ge=0, le=100)
    conduct_weight: int = Field(default=10, ge=0, le=100)
    attention: int = Field(default=30, ge=1, le=99)
    high: int = Field(default=60, ge=2, le=100)

    @model_validator(mode='after')
    def thresholds(self):
        if self.attention >= self.high:
            raise ValueError('Ngưỡng cần chú ý phải nhỏ hơn ngưỡng nguy cơ cao')
        return self


class Intervention(BaseModel):
    student_id: str
    advisor: str = Field(min_length=1, max_length=100)
    note: str = Field(min_length=1, max_length=3000)
    action: str = Field(min_length=1, max_length=2000)
    due_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    status: Literal['planned', 'ongoing', 'completed'] = 'planned'
    outcome: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def valid_date(self):
        from datetime import date
        date.fromisoformat(self.due_date)
        if not all(x.strip() for x in (self.advisor, self.note, self.action)):
            raise ValueError('Cố vấn, ghi chú và biện pháp không được để trống')
        return self
