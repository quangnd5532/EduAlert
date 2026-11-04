"""Illustrative data shared by SQLite seed and dependency-free visual preview."""
from datetime import date, timedelta


def records():
    names = ['Nguyễn Minh Anh', 'Trần Hoàng Nam', 'Lê Thảo Nguyên', 'Phạm Gia Huy', 'Võ Ngọc Linh', 'Đặng Quốc Bảo', 'Bùi Phương Thảo', 'Hoàng Đức Minh', 'Đỗ Khánh Vy', 'Nguyễn Tuấn Kiệt', 'Trần Hà My', 'Lê Anh Khoa', 'Phan Bảo Ngọc', 'Vũ Thành Đạt', 'Ngô Quỳnh Chi', 'Dương Hải Đăng', 'Mai Thanh Trúc', 'Lý Nhật Hào', 'Hồ Diệu Linh', 'Cao Minh Quân', 'Trương Ngọc Anh', 'Đinh Đức Huy', 'Nguyễn Yến Nhi', 'Trần Quốc Khánh']
    patterns = [[2.8, 2.2, 1.45], [3.1, 2.5, 1.8], [3.2, 3.3, 3.45], [2.1, 2.0, 1.1], [2.5, 2.6, 2.8], [2.8, 2.4, 2.1]]
    students, interventions = [], []
    for i, name in enumerate(names):
        sid = str(2351010101 + i)
        student = dict(id=sid, name=name, class_name=['CNTT23A', 'CNTT23B', 'KTPM24A'][i % 3], major='Kỹ thuật phần mềm' if i % 3 == 2 else 'Công nghệ thông tin', cohort='2024' if i % 3 == 2 else '2023', advisor=['Nguyễn Thu Hà', 'Trần Minh Đức'][i % 2], admission_score=23 + i % 5, admission_scale=30, admission_method='THPT')
        terms = []
        pattern = patterns[i % len(patterns)]
        for j, gpa in enumerate(pattern):
            failed = j * 3 if i % 6 in (0, 1, 3) else 0
            terms.append(dict(year=2024 + int(j == 2), semester=[1, 2, 1][j], gpa=gpa, cumulative_gpa=round(sum(pattern[:j + 1]) / (j + 1), 2), registered=18, passed=18-failed, failed=failed, debt=failed // 3, conduct=45 if i % 6 == 3 and j == 2 else 80, previous_warnings=1 if i % 6 == 3 else 0))
        students.append({**student, 'terms': terms})
        if i in (0, 1, 3, 6, 9):
            interventions.append(dict(id=len(interventions)+1, student_id=sid, advisor=student['advisor'], note='Trao đổi về khó khăn trong các học phần chuyên ngành.', action='Lập kế hoạch học tập và kết nối nhóm phụ đạo.', due_date=str(date.today() + timedelta(days=i-2)), status='completed' if i == 9 else 'ongoing', outcome='Đã tham gia nhóm học tập.' if i == 9 else '', created_at=str(date.today())))
    return students, list(reversed(interventions))
