"""Four mutually compatible import examples, with enrollment-aware histories."""
from .csv_import import HEADERS

NAMES=['Nguyễn Minh Khôi','Trần Bảo Trâm','Lê Hoàng Phúc','Phạm Ngọc Mai','Võ Gia Hân','Đặng Đức Anh']
SPECS=[('2351999001','L1',2,1),('2451999002','L2',2,3),('2352999003','L3',3,1),
       ('2452999004','L4',3,3),('2551999005','L5',2,5),('2552999006','L6',3,5)]


def sample_rows():
    output={kind:[] for kind in HEADERS}
    for index,(sid,cls,advisor,start) in enumerate(SPECS):
        output['students'].append(dict(zip(HEADERS['students'],[sid,NAMES[index],cls,advisor,24+index*.5,30,'THPT'])))
        points=0;credits=0;accumulated=0;outstanding=[]
        for seq in range(start,7):
            gpa=round(3.4-index*.22-(seq-start)*.12,2)
            failed=0 if gpa>=3 else 2 if gpa>=2.5 else 4
            passed=20-failed;credits+=20;points+=gpa*20;accumulated+=passed
            output['results'].append(dict(zip(HEADERS['results'],[sid,seq,gpa,round(points/credits,2),20,passed,failed,accumulated,88-index*3,'completed'])))
            output['warnings'].append({'student_id':sid,'semester_id':seq,'warned':gpa<1.2 or failed>=10})
            prefix='IT' if sid[2:4]=='51' else 'BA'
            outstanding.extend(f'{prefix}{seq:02}{position:02}' for position in range(5,5+failed//2))
            output['debts'].extend({'student_id':sid,'semester_id':seq,'course_id':cid} for cid in outstanding)
    return output


LABELS={
    'students':{'title':'Hồ sơ sinh viên','description':'6 sinh viên thuộc khóa 23, 24, 25; ngành, lớp và cố vấn phù hợp.','order':'Nhập đầu tiên'},
    'results':{'title':'Kết quả học kỳ','description':'GPA, tín chỉ và rèn luyện theo từng kỳ trong thời gian theo học.','order':'Nhập sau hồ sơ sinh viên'},
    'debts':{'title':'Học phần còn nợ','description':'Học phần chưa hoàn thành ở kỳ đang xét; mã học phần có trong danh mục.','order':'Nhập sau kết quả học kỳ'},
    'warnings':{'title':'Lịch sử cảnh báo','description':'Quyết định có / không cảnh báo; không để trống thay cho “không cảnh báo”.','order':'Nhập sau hồ sơ sinh viên'},
}

FIELD_GUIDE={
 'students':{'id':'Mã sinh viên dạng chuỗi, bắt đầu bằng năm tuyển sinh (23/24/25).','name':'Họ và tên có dấu, ít nhất 2 ký tự.','class_id':'Mã lớp có trong danh mục.','advisor_id':'Mã cố vấn đang hoạt động.','admission_score':'Điểm xét tuyển; có thể để trống.','admission_scale':'Thang điểm, bắt buộc khi có điểm xét tuyển.','admission_method':'Phương thức xét tuyển, ví dụ THPT.'},
 'results':{'student_id':'Mã sinh viên đã được nhập.','semester_id':'Mã học kỳ có trong danh mục.','gpa':'GPA học kỳ: 0–4; để trống nếu chưa có.','cumulative_gpa':'GPA tích lũy: 0–4; để trống nếu chưa có.','registered':'Tín chỉ đăng ký: số nguyên 0–60.','passed':'Tín chỉ đạt: số nguyên, đạt + không đạt = đăng ký.','failed':'Tín chỉ không đạt: số nguyên.','accumulated':'Tổng tín chỉ đã đạt đến hết kỳ đang nhập.','conduct':'Điểm rèn luyện: 0–100; có thể để trống.','status':'completed: hoàn thành; leave: nghỉ học (0 tín chỉ, GPA trống).'},
 'debts':{'student_id':'Mã sinh viên đã tồn tại.','semester_id':'Kỳ xác nhận học phần còn nợ.','course_id':'Mã học phần có trong danh mục; mỗi học phần một dòng.'},
 'warnings':{'student_id':'Mã sinh viên đã tồn tại.','semester_id':'Kỳ có quyết định cảnh báo.','warned':'true: có cảnh báo; false: đã xác nhận không cảnh báo. Không để trống.'},
}
