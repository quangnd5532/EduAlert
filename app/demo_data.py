"""Synthetic academic data shared by the seed command and dependency-free checks."""

SEMESTERS = [
    {
        'id': n,
        'name': f'HK{1 + (n - 1) % 2} · {2023 + (n - 1) // 2}–{2024 + (n - 1) // 2}',
        'sequence': n,
        'kind': 'regular',
        'completed': True,
    }
    for n in range(1, 7)
] + [{'id': 7, 'name': 'Hè 2026 (không tính xu hướng)', 'sequence': 7, 'kind': 'summer', 'completed': True}]

GIVEN_NAMES = ['Minh Anh','Ngọc Bảo','Gia Linh','Đức Huy','Thanh Hà','Khánh An','Quỳnh Chi','Nhật Minh','Thu Trang','Bảo Ngọc',
               'Tuấn Kiệt','Phương Thảo','Hải Đăng','Mai Anh','Quốc Bảo','Thùy Dương','Anh Khoa','Ngọc Hân','Hoài Nam','Lan Phương']
CLASS_NAMES = {'L1':'CNTT23A','L2':'CNTT22B','L3':'QTKD23A','L4':'QTKD22B'}
CREDIT_PATTERN = [4,4,3,3,2,2,2,2,2]
SUBJECTS = {
 'CNTT': [
 ['Toán cao cấp','Nhập môn lập trình','Triết học Mác – Lênin','Tiếng Anh 1','Tin học cơ sở','Kỹ năng học đại học','Giáo dục thể chất 1','Tư duy sáng tạo','Kỹ năng giao tiếp'],
 ['Cấu trúc dữ liệu và giải thuật','Toán rời rạc','Kiến trúc máy tính','Tiếng Anh 2','Pháp luật đại cương','Kỹ năng làm việc nhóm','Giáo dục thể chất 2','Nhập môn dữ liệu','Kỹ năng viết học thuật'],
 ['Cơ sở dữ liệu','Lập trình hướng đối tượng','Mạng máy tính','Xác suất thống kê','Tiếng Anh chuyên ngành','Hệ điều hành','Đạo đức nghề nghiệp','Thiết kế giao diện','Phân tích yêu cầu'],
 ['Công nghệ phần mềm','Lập trình ứng dụng web','Phân tích thiết kế hệ thống','An toàn thông tin','Quản lý dự án','Kiểm thử phần mềm','Thiết kế trải nghiệm','Kỹ năng thuyết trình','Điện toán đám mây'],
 ['Phát triển ứng dụng di động','Khai phá dữ liệu','Trí tuệ nhân tạo cơ sở','Cơ sở dữ liệu nâng cao','Kiến trúc phần mềm','DevOps cơ bản','Thương mại điện tử','Ứng dụng mã nguồn mở','Phát triển nghề nghiệp'],
 ['Đồ án chuyên ngành','Hệ thống phân tán','Học máy ứng dụng','Bảo mật ứng dụng','Thực hành dự án','Khởi nghiệp công nghệ','Seminar chuyên ngành','Nghiên cứu khoa học','Chuẩn bị thực tập']],
 'QTKD': [
 ['Toán kinh tế','Kinh tế vi mô','Triết học Mác – Lênin','Tiếng Anh 1','Tin học ứng dụng','Kỹ năng học đại học','Giáo dục thể chất 1','Tư duy sáng tạo','Kỹ năng giao tiếp'],
 ['Kinh tế vĩ mô','Nguyên lý kế toán','Quản trị học','Tiếng Anh 2','Pháp luật đại cương','Kỹ năng làm việc nhóm','Giáo dục thể chất 2','Kinh tế số','Viết học thuật'],
 ['Marketing căn bản','Thống kê kinh doanh','Tài chính doanh nghiệp','Hành vi tổ chức','Tiếng Anh kinh doanh','Luật kinh tế','Đạo đức kinh doanh','Kỹ năng đàm phán','Phân tích thị trường'],
 ['Quản trị nhân lực','Quản trị marketing','Quản trị vận hành','Hành vi người tiêu dùng','Phân tích kinh doanh','Thương mại điện tử','Kỹ năng lãnh đạo','Quản lý chất lượng','Thuyết trình kinh doanh'],
 ['Quản trị chiến lược','Quản trị dự án','Quản trị chuỗi cung ứng','Nghiên cứu marketing','Quản trị rủi ro','Khởi sự doanh nghiệp','Chuyển đổi số','Kỹ năng bán hàng','Phát triển nghề nghiệp'],
 ['Đồ án kinh doanh','Kinh doanh quốc tế','Quản trị tài chính','Quản trị đổi mới','Thực hành doanh nghiệp','Phân tích đầu tư','Seminar quản trị','Nghiên cứu khoa học','Chuẩn bị thực tập']]
}

def student_profile(number):
    sid=f'{number:06}'; class_id=f'L{(number-1)%4+1}'
    methods=[('THPT',30,round(21.5+(number%13)*.45,2)),('Học bạ',30,round(24+(number%9)*.4,2)),('Đánh giá năng lực',1200,720+(number%17)*19)]
    method,scale,score=methods[(number-1)%3]
    return {'id':sid,'name':['Trần','Phạm','Hoàng'][(number-1)//20]+' '+GIVEN_NAMES[(number-1)%20],
            'class_id':class_id,'advisor_id':2 if (number-1)%4<2 else 3,
            'admission_score':score,'admission_scale':scale,'admission_method':method}

def course_catalog():
    return [{'id':f'{"IT" if major=="CNTT" else "BA"}{sem:02}{i:02}', 'name':name, 'credits':CREDIT_PATTERN[i-1]}
            for major,terms in SUBJECTS.items() for sem,names in enumerate(terms,1) for i,name in enumerate(names,1)]


def academic_data(number):
    """Return result, confirmed-warning and debt rows for one fictional student."""
    if not 1 <= number <= 60:
        raise ValueError('Demo chỉ có số thứ tự 1–60')
    examples = {
        1: [3.2, 3.3, 3.1, 3.2, 3.3, 3.4],
        2: [3, 3.1, 3, 2.8, 2.3, 1.9],
        3: [2.9, 2.8, 2.7, 2.6, 2.1, 1.1],
        4: [2.5, 2.4, 2.3, 1.8, 1.5, 1.3],
        5: [3, 3.1, 3, 2.8, 2.3, 1.9],
        6: [3, 2.6, 2.1, 1.6, 2.3, 2.9],
        7: [None, 3, 2.9, 2.7, None, 2.2],
    }
    mode = number % 5
    default = (
        [3, 3.1, 3, 3.2, 3.3, 3.2] if mode == 0 else
        [3, 2.8, 2.7, 2.6, 2.2, 1.6] if mode == 1 else
        [2.5, 2.3, 2.1, 1.8, 1.4, 1.0] if mode == 2 else
        [2.4, 2.6, 2.7, 2.8, 2.8, 3.1]
    )
    gpas = examples.get(number, default)
    student_id = f'{number:06}'
    results, warnings, debts = [], [], []
    accumulated = 0
    weighted_points = 0
    total_gpa_credits = 0
    complete_history = True
    for sequence, gpa in enumerate(gpas, 1):
        registered = 20 if number<=8 else [18,20,22,24][(number+sequence)%4]
        failed = (0 if gpa is None or gpa >= 3 else 2 if gpa >= 2.5 else
                  4 if gpa >= 2 else 8 if gpa >= 1.5 else 12)
        if gpa is not None:
            failed=max(f for f in range(0,failed+1,2) if f<=registered*(1-gpa/4)+1e-9)
        passed = registered - failed
        accumulated += passed  # Demo assumption: no repeated passed courses.
        total_gpa_credits+=registered
        if gpa is None: complete_history=False
        else: weighted_points+=gpa*registered
        cumulative=round(weighted_points/total_gpa_credits,2) if complete_history else None
        results.append({
            'student_id': student_id, 'semester_id': sequence, 'gpa': gpa,
            'cumulative_gpa': cumulative, 'registered': registered, 'passed': passed,
            'failed': failed, 'accumulated': accumulated, 'conduct': 65+(number*3+sequence*7)%31,
            'status': 'completed',
        })
        # These are supplied historical decisions, not today's rule-engine output.
        if number != 7:
            warnings.append({
                'student_id': student_id, 'semester_id': sequence,
                'warned': (number in (4, 5) and sequence in (3, 4, 5)) or
                          (gpa is not None and gpa < 1.2),
            })
        if failed >= 8:
            debts.append({'student_id': student_id, 'course_id': 'HP01', 'semester_id': sequence})
    return results, warnings, debts

def detailed_academics(number):
    """Course grades reconcile to semester aggregates; outstanding required courses carry forward."""
    from itertools import combinations
    results,warnings,_=academic_data(number)
    major='CNTT' if (number-1)%4<2 else 'QTKD'
    prefix='IT' if major=='CNTT' else 'BA'
    attempts=[]; debts=[]; outstanding=[]
    for r in results:
        credits=[]
        for credit in CREDIT_PATTERN:
            if sum(credits)==r['registered']: break
            credits.append(credit)
        failed_set=next((set(group) for size in range(len(credits)+1) for group in combinations(range(len(credits)),size)
                         if sum(credits[i] for i in group)==r['failed']),None)
        if failed_set is None: raise ValueError('Không thể đối soát tín chỉ không đạt')
        pass_grade=r['gpa']*r['registered']/r['passed'] if r['gpa'] is not None and r['passed'] else None
        grades={i:pass_grade for i in range(len(credits)) if i not in failed_set}
        passing=list(grades)
        if pass_grade is not None:
            for pair in range(0,len(passing)-1,2):
                a,b=passing[pair:pair+2]
                if (number+r['semester_id']+pair)%2: a,b=b,a
                transfer=min(.6*min(credits[a],credits[b]),(4-pass_grade)*credits[a],(pass_grade-1)*credits[b])
                transfer=max(0,transfer)*(.5+.1*((number+r['semester_id']+pair)%5))
                grades[a]+=transfer/credits[a];grades[b]-=transfer/credits[b]
        for i,credit in enumerate(credits):
            cid=f'{prefix}{r["semester_id"]:02}{i+1:02}'
            grade=0.0 if i in failed_set else round(grades[i],6) if pass_grade is not None else None
            attempts.append({'student_id':r['student_id'],'semester_id':r['semester_id'],'course_id':cid,'grade':grade})
            if grade==0: outstanding.append(cid)
        debts.extend({'student_id':r['student_id'],'semester_id':r['semester_id'],'course_id':cid} for cid in outstanding)
    return results,warnings,debts,attempts
