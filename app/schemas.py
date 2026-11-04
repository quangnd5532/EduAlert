from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict
from .services.assessment import validate_config
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)
class StudentInput(Strict):
    id: str=Field(pattern=r'^[A-Za-z0-9_-]{1,30}$')
    name: str=Field(min_length=2,max_length=120)
    class_id: str
    advisor_id: int
    admission_score: float|None=None
    admission_scale: float|None=Field(default=None,gt=0)
    admission_method: str|None=None
    @model_validator(mode='after')
    def admission(self):
        if self.admission_score is not None and (not self.admission_method or not self.admission_scale or not 0<=self.admission_score<=self.admission_scale): raise ValueError('Điểm xét tuyển cần phương thức, thang điểm và nằm trong thang')
        return self
class ResultInput(Strict):
    student_id:str
    semester_id:int
    gpa:float|None=Field(default=None,ge=0,le=4)
    cumulative_gpa:float|None=Field(default=None,ge=0,le=4)
    registered:int=Field(ge=0,le=60)
    passed:int=Field(ge=0,le=60)
    failed:int=Field(ge=0,le=60)
    accumulated:int|None=Field(default=None,ge=0)
    conduct:float|None=Field(default=None,ge=0,le=100)
    status:Literal['completed','leave']='completed'
    @model_validator(mode='after')
    def credits(self):
        if self.passed+self.failed!=self.registered: raise ValueError('Đạt + không đạt phải bằng đăng ký')
        if self.status=='leave' and (self.registered or self.gpa is not None): raise ValueError('Nghỉ học: 0 tín chỉ, GPA trống')
        return self
class SimulationInput(Strict):
    gpa:float=Field(ge=0,le=4)
    registered:int=Field(ge=1,le=60)
    failed:int=Field(ge=0,le=60)
    previous_gpa_credits:int|None=Field(default=None,ge=1,le=600)
    no_repeats:bool=False
    all_registered_count:bool=False
    @model_validator(mode='after')
    def credits(self):
        if self.failed>self.registered: raise ValueError('Không đạt không vượt đăng ký')
        return self
class InterventionInput(Strict):
    student_id:str
    evaluation_id:int
    goal:str=Field(min_length=3,max_length=2000)
    action:str=Field(min_length=3,max_length=3000)
    due_date:date
class InterventionUpdate(Strict):
    status:Literal['Chưa xử lý','Đang hỗ trợ','Chờ theo dõi','Hoàn tất']
    note:str=Field(default='',max_length=3000)
    goal:str|None=Field(default=None,min_length=3,max_length=2000)
    action:str|None=Field(default=None,min_length=3,max_length=3000)
    due_date:date|None=None
class ConfigInput(Strict):
    name:str=Field(min_length=3,max_length=120)
    major_id:str|None=None
    cohort_id:str|None=None
    payload:dict
    @model_validator(mode='after')
    def configuration(self):
        validate_config(self.payload)
        return self
