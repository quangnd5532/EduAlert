"""Shared sort choices for the list, dashboard and CSV export."""
import unicodedata

SORT_OPTIONS = [
    ('risk','Điểm hỗ trợ: cao đến thấp'), ('risk_asc','Điểm hỗ trợ: thấp đến cao'),
    ('gpa_asc','GPA học kỳ: thấp đến cao'), ('gpa_desc','GPA học kỳ: cao đến thấp'),
    ('cumulative_asc','GPA tích lũy: thấp đến cao'), ('cumulative_desc','GPA tích lũy: cao đến thấp'),
    ('failed_desc','Tín chỉ không đạt: nhiều đến ít'), ('failed_asc','Tín chỉ không đạt: ít đến nhiều'),
    ('accumulated_desc','Tín chỉ tích lũy: nhiều đến ít'), ('accumulated_asc','Tín chỉ tích lũy: ít đến nhiều'),
    ('name','Họ tên: A–Z'), ('name_desc','Họ tên: Z–A'),
    ('id','Mã sinh viên: tăng dần'), ('id_desc','Mã sinh viên: giảm dần'),
    ('class','Lớp học'), ('cohort','Khóa tuyển sinh'), ('missing','Hồ sơ cần bổ sung trước'),
]


def text_key(value):
    return ''.join(c for c in unicodedata.normalize('NFD',str(value).casefold().replace('đ','d')) if unicodedata.category(c)!='Mn')


def sort_students(items, choice):
    numeric = {'risk':('score',True),'risk_asc':('score',False),
               'gpa_asc':('gpa',False),'gpa_desc':('gpa',True),
               'cumulative_asc':('cumulative_gpa',False),'cumulative_desc':('cumulative_gpa',True),
               'failed_desc':('failed',True),'failed_asc':('failed',False),
               'accumulated_desc':('accumulated',True),'accumulated_asc':('accumulated',False)}
    if choice in numeric:
        field, reverse=numeric[choice]
        def key(student):
            value=student['assessment'].get('score') if field=='score' else student.get('academic',{}).get(field)
            return (value is None, -value if reverse and value is not None else value or 0, student['id'])
        return sorted(items,key=key)
    if choice=='missing':
        return sorted(items,key=lambda s:(-sum(i['kind']=='missing' for i in s['assessment'].get('data_issues',[])),-len(s['assessment'].get('missing',[])),s['id']))
    field={'name':'name','name_desc':'name','id':'id','id_desc':'id','class':'class_name','cohort':'cohort_id'}[choice]
    return sorted(items,key=lambda s:(text_key(s[field]),s['id']),reverse=choice.endswith('_desc'))
