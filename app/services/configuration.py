"""Editable reference presets; institutions supply and approve their own policies."""
from copy import deepcopy
from sqlalchemy import select
from ..models import ConfigVersion
from .assessment import DEFAULT

PRESETS = [
    {'id':'balanced','name':'Cân bằng các yếu tố','description':'Theo dõi đồng thời GPA, tín chỉ, xu hướng và lịch sử cảnh báo.','payload':deepcopy(DEFAULT)},
    {'id':'gpa','name':'Ưu tiên theo dõi GPA','description':'Tăng trọng số GPA học kỳ; giữ nguyên các yếu tố còn lại.','payload':{**deepcopy(DEFAULT),'weights':[45,20,20,15]}},
    {'id':'progress','name':'Ưu tiên tiến độ tín chỉ','description':'Tăng trọng số học phần không đạt để lên kế hoạch hỗ trợ.','payload':{**deepcopy(DEFAULT),'weights':[30,35,20,15]}},
    {'id':'academic','name':'Theo dõi học vụ và rèn luyện','description':'Thêm điều kiện điểm rèn luyện dưới 50 để cố vấn kiểm tra.','payload':{**deepcopy(DEFAULT),'rule':{'op':'OR','children':deepcopy(DEFAULT['rule']['children'])+[{'field':'conduct','op':'lt','value':50}]}}},
]


def add_examples(db):
    for preset,year in zip(PRESETS[1:],(23,24,25)):
        name=preset['name']+f' — Khóa {year}'
        if not db.scalar(select(ConfigVersion.id).where(ConfigVersion.name==name)):
            db.add(ConfigVersion(name=name,cohort_id=f'K{year}',payload=deepcopy(preset['payload']),active=False))
