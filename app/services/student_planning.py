"""Student-facing next steps from recorded grades, with explicit calculation limits."""


def learning_guidance(model):
    current=model.get('current') or {}
    gpa=current.get('gpa')
    failed=current.get('failed',0)
    registered=current.get('registered',0)
    actions=[]
    if gpa is None:
        actions.append({'title':'Kiểm tra bảng điểm trước khi đặt mục tiêu',
            'reason':'Chưa có GPA của học kỳ đang xem để so sánh mức cải thiện.',
            'todo':'Kiểm tra các môn chưa có điểm. Nếu bảng điểm chưa đầy đủ, trao đổi với bộ phận học vụ.',
            'link':'results','link_label':'Kiểm tra bảng điểm'})
    elif failed:
        actions.append({'title':'Ưu tiên những môn chưa đạt',
            'reason':f'Học kỳ đang xem có {failed}/{registered} tín chỉ chưa đạt. Môn nhiều tín chỉ ảnh hưởng nhiều hơn đến GPA của kỳ học.',
            'todo':'Xem các học phần bên dưới, chọn phần kiến thức chưa vững và hỏi giảng viên cách ôn tập. Trao đổi với cố vấn trước khi đăng ký học lại.',
            'link':'results','link_label':'Xem học phần chưa đạt'})
    elif gpa<2.5:
        actions.append({'title':'Củng cố các môn có điểm còn thấp',
            'reason':f'GPA học kỳ đang xem là {gpa:.2f}/4; bạn có thể bắt đầu từ các môn có điểm thấp và nhiều tín chỉ.',
            'todo':'Xác định nội dung hay làm sai, làm lại bài tập và mang các câu hỏi chưa giải được đến buổi trao đổi với giảng viên.',
            'link':'results','link_label':'Xem điểm từng môn'})
    else:
        actions.append({'title':'Giữ nhịp học ở các môn nhiều tín chỉ',
            'reason':f'GPA học kỳ đang xem là {gpa:.2f}/4 và chưa ghi nhận tín chỉ không đạt trong kỳ.',
            'todo':'Duy trì cách học đang hiệu quả, chuẩn bị bài trước buổi học và theo dõi điểm thành phần để điều chỉnh sớm.',
            'link':'results','link_label':'Xem kết quả gần nhất'})
    recent=[row for row in model.get('history',[]) if row.get('status')=='completed'][-3:]
    declining=len(recent)==3 and all(row.get('gpa') is not None for row in recent) and recent[0]['gpa']>recent[1]['gpa']>recent[2]['gpa']
    if declining:
        actions.append({'title':'Tìm nguyên nhân điểm giảm qua các kỳ',
            'reason':'GPA ba kỳ gần nhất: '+' → '.join(f'{row["gpa"]:.2f}' for row in recent)+'.',
            'todo':'So sánh lịch học, thời gian tự học và kết quả kiểm tra. Chọn một thay đổi cụ thể cho tuần tới và trao đổi sớm với cố vấn.',
            'link':'appointments','link_label':'Đặt lịch trao đổi'})
    else:
        actions.append({'title':'Chọn khối lượng học vừa sức',
            'reason':'Kế hoạch học cần tính cả thời gian tự học, bài tập và các học phần còn phải hoàn thành.',
            'todo':'Kiểm tra lịch kiểm tra và điều kiện tiên quyết trước khi đăng ký; nhờ cố vấn rà soát nếu bạn dự định học nhiều hơn kỳ trước.',
            'link':'appointments','link_label':'Trao đổi kế hoạch với cố vấn'})
    priorities={}
    for course in model.get('debts',[]):
        priorities[course['course_id']]={'id':course['course_id'],'name':course['name'],'credits':course['credits'],
            'grade':None,'status':'Chưa hoàn thành','unfinished':True}
    for course in model.get('courses',[]):
        grade=course.get('grade')
        if grade is None: continue
        if grade<2.5 or course['id'] in priorities:
            entry=priorities.get(course['id']) or {'id':course['id'],'name':course['name'],'credits':course['credits'],
                'status':'Chưa đạt' if grade==0 else 'Điểm còn thấp','unfinished':grade==0}
            entry['grade']=grade
            priorities[course['id']]=entry
    priorities=sorted(priorities.values(),key=lambda course:(not course['unfinished'],-course['credits'],course['grade'] if course['grade'] is not None else -1,course['id']))
    return {'actions':actions,'courses':priorities[:5],'course_count':len(priorities),
        'course_note':'Danh sách dựa trên học phần còn nợ và điểm dưới 2.50/4 ở kỳ đang xem; ưu tiên môn chưa hoàn thành, sau đó đến số tín chỉ. Đây không phải danh sách đăng ký kỳ tới.',
        'weekly_steps':[
            'Đầu tuần: chọn hai phần kiến thức chưa vững ở môn ưu tiên và xếp thời gian ôn vào lịch cá nhân.',
            'Trong tuần: làm lại bài tập và bài kiểm tra đã sai; ghi câu hỏi để nhờ giảng viên hoặc nhóm học giải thích.',
            'Cuối tuần: kiểm tra bài đã hoàn thành, điểm thành phần mới và điều chỉnh lịch học tuần sau.',
        ]}


def student_outlook(model,scenario,simulation):
    current=model.get('current') or {}
    gpa=scenario['gpa'];registered=scenario['registered'];failed=scenario['failed']
    passed=registered-failed
    maximum=4*passed/registered
    required=gpa*registered/passed if passed else None
    feasible=gpa<=maximum+1e-9
    now_gpa=current.get('gpa')
    difference=round(gpa-now_gpa,2) if now_gpa is not None else None
    notes=[]
    if not feasible:
        title='Cần điều chỉnh mục tiêu hoặc số tín chỉ chưa đạt'
        message=f'Với {failed}/{registered} tín chỉ không đạt tính điểm 0, GPA học kỳ cao nhất có thể đạt là {maximum:.2f}/4.'
        notes.append('Thử giảm số tín chỉ bạn lo chưa đạt hoặc đặt lại mục tiêu GPA, rồi xem kết quả lần nữa.')
    elif not passed:
        title='Bạn cần đặt mục tiêu hoàn thành học phần'
        message='Nếu toàn bộ tín chỉ đều không đạt, GPA học kỳ bằng 0. Hãy bắt đầu từ các môn bạn có thể cải thiện và trao đổi với cố vấn.'
        notes.append('Chọn học phần ưu tiên để ôn tập; cân nhắc khối lượng đăng ký phù hợp với thời gian học của bạn.')
    elif failed:
        title=f'Các môn đạt cần trung bình khoảng {required:.2f}/4'
        message=f'Để GPA cả kỳ đạt {gpa:.2f}/4 khi có {failed} tín chỉ không đạt, {passed} tín chỉ còn lại cần đạt mức trung bình này.'
        notes.append(f'Ưu tiên ôn tập để giảm {failed} tín chỉ bạn đang lo chưa đạt; nếu qua được thêm học phần, áp lực điểm ở các môn còn lại sẽ giảm.')
    else:
        title=f'Nhắm mức trung bình {gpa:.2f}/4 trên {registered} tín chỉ'
        message='Đây là mức trung bình có tính số tín chỉ: môn nhiều tín chỉ ảnh hưởng nhiều hơn đến GPA cả kỳ.'
        notes.append('Theo dõi điểm thành phần ở từng môn và ưu tiên dành thêm thời gian cho môn nhiều tín chỉ, nhất là môn bạn còn yếu.')
    if difference is not None and difference<0:
        notes.append(f'Mục tiêu đang thấp hơn GPA của kỳ đang xem {abs(difference):.2f} điểm. Nếu bạn muốn tăng GPA, hãy thử mức cao hơn {now_gpa:.2f}/4.')
    elif difference is not None and difference==0:
        notes.append('Mục tiêu hiện tại giữ nguyên GPA học kỳ. Bạn có thể thử mức cao hơn nếu muốn cải thiện.')
    if registered>current.get('registered',registered) and current.get('failed',0)>0:
        notes.append(f'Bạn dự định đăng ký {registered} tín chỉ, nhiều hơn {current["registered"]} tín chỉ kỳ trước dù còn học phần chưa đạt. Nên rà soát lịch học cùng cố vấn.')
    if not scenario.get('no_repeats'):
        cumulative_reason='Chưa ước tính GPA tích lũy vì bạn chưa xác nhận kỳ tới không có môn học lại. Cách thay điểm môn học lại cần đối chiếu quy định của trường.'
    elif not scenario.get('all_registered_count'):
        cumulative_reason='Chưa ước tính GPA tích lũy vì bạn chưa xác nhận toàn bộ tín chỉ đăng ký đều được tính vào GPA.'
    elif not scenario.get('previous_gpa_credits'):
        cumulative_reason='Chưa ước tính GPA tích lũy vì còn thiếu số tín chỉ đã được tính GPA trong bảng điểm.'
    elif current.get('cumulative_gpa') is None:
        cumulative_reason='Chưa ước tính GPA tích lũy vì bảng điểm hiện chưa có GPA tích lũy của kỳ đang xem.'
    else:
        cumulative_reason=f'Tính từ GPA tích lũy {current["cumulative_gpa"]:.2f} trên {scenario["previous_gpa_credits"]} tín chỉ đã tính GPA, cộng với mục tiêu của {registered} tín chỉ kỳ tới.'
    # An impossible semester target must not be presented as a reachable cumulative GPA.
    can_estimate=feasible and current.get('cumulative_gpa') is not None and scenario.get('previous_gpa_credits') and scenario.get('no_repeats') and scenario.get('all_registered_count')
    cumulative=simulation.get('cumulative_gpa') if can_estimate else None
    if not feasible: cumulative_reason='Hãy điều chỉnh mục tiêu học kỳ trước khi ước tính GPA tích lũy.'
    return {'current_gpa':now_gpa,'target_gpa':gpa,'difference':difference,'registered':registered,
        'failed':failed,'passed':passed,'failed_percent':failed/registered*100,
        'required_passing_gpa':round(required,4) if required is not None else None,
        'maximum_gpa':round(maximum,4),'feasible':feasible,'title':title,'message':message,
        'next_steps':notes,'current_cumulative':current.get('cumulative_gpa'),
        'cumulative_gpa':cumulative,'cumulative_reason':cumulative_reason,'semester_id':model['semester_id']}
