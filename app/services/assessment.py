"""Pure, deterministic scoring. No database, web framework or execution of user code."""
import math
import operator
from copy import deepcopy

DEFAULT = {'weights': [35,25,25,15], 'attention':30, 'high':60,
           'gpa_target':2.5,'gpa_span':1.5,'fail_span':0.5,'trend_span':1.0,'repeat_span':2,
           'rule': {'op':'OR','children':[{'field':'gpa','op':'lt','value':1.2},
                    {'field':'cumulative_gpa','op':'lt','value':1.8},
                    {'field':'failed_ratio','op':'ge','value':0.5}]}}
OPS = {'lt':operator.lt,'le':operator.le,'gt':operator.gt,'ge':operator.ge,'eq':operator.eq}
FIELDS = {'gpa':(0,4), 'cumulative_gpa':(0,4),'failed_ratio':(0,1),'conduct':(0,100)}
FIELD_LABELS = {'gpa':'GPA học kỳ','cumulative_gpa':'GPA tích lũy','failed_ratio':'Tỷ lệ tín chỉ không đạt','conduct':'Điểm rèn luyện'}
OP_LABELS = {'lt':'nhỏ hơn','le':'không vượt quá','gt':'lớn hơn','ge':'từ','eq':'bằng'}

def validate_rule(rule, depth=0):
    if not isinstance(rule,dict): raise ValueError('Điều kiện cần là đối tượng JSON')
    if depth > 6: raise ValueError('Nhóm điều kiện quá sâu (tối đa 6)')
    if rule.get('op') in ('AND','OR'):
        children=rule.get('children',[])
        if not isinstance(children,list): raise ValueError('children cần là danh sách')
        if not 1 <= len(children) <= 20: raise ValueError('Nhóm cần 1–20 điều kiện')
        for child in children: validate_rule(child,depth+1)
    else:
        if rule.get('field') not in FIELDS or rule.get('op') not in OPS: raise ValueError('Trường hoặc toán tử không được phép')
        lo,hi=FIELDS[rule['field']]
        v=rule.get('value')
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi: raise ValueError('Ngưỡng '+FIELD_LABELS[rule['field']]+' không hợp lệ')

def validate_config(c):
    if not isinstance(c,dict) or set(c)!=set(DEFAULT): raise ValueError('Cấu hình cần đúng các khóa trong mẫu mặc định')
    w=c.get('weights',[])
    if not isinstance(w,list): raise ValueError('weights cần là danh sách')
    if len(w)!=4 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in w) or not math.isclose(sum(w),100,rel_tol=0,abs_tol=1e-6):
        raise ValueError('Bốn trọng số không âm phải có tổng bằng 100')
    if any(isinstance(c[k],bool) or not isinstance(c[k],(int,float)) or not math.isfinite(c[k]) for k in ('attention','high','gpa_target')): raise ValueError('Ngưỡng cần là số hữu hạn')
    if not 0<c['attention']<c['high']<=100: raise ValueError('Cần 0 < ngưỡng chú ý < ngưỡng cao ≤ 100')
    for k in ('gpa_span','fail_span','trend_span','repeat_span'):
        labels={'gpa_span':'Khoảng giảm GPA','fail_span':'Tỷ lệ tín chỉ không đạt','trend_span':'Mức giảm xu hướng GPA','repeat_span':'Số lần cảnh báo'}
        if isinstance(c[k],bool) or not isinstance(c[k],(int,float)) or not math.isfinite(c[k]) or c[k]<=0: raise ValueError(labels[k]+' phải lớn hơn 0')
    if c['gpa_span']>4 or c['trend_span']>4: raise ValueError('Mức giảm GPA không vượt quá thang điểm 4.')
    if c['fail_span']>1: raise ValueError('Mốc tỷ lệ tín chỉ không đạt không vượt quá 100%.')
    if c['repeat_span']>3 or c['repeat_span']!=int(c['repeat_span']): raise ValueError('Số lần cảnh báo cần là số nguyên từ 1 đến 3.')
    if not 0<=c['gpa_target']<=4: raise ValueError('Mốc GPA phải từ 0 đến 4')
    validate_rule(c['rule'])
    return c

def rule_result(rule, data):
    if rule['op'] in ('AND','OR'):
        children=[rule_result(x,data) for x in rule['children']]
        states=[x['state'] for x in children]
        if rule['op']=='AND': state='false' if 'false' in states else ('unknown' if 'unknown' in states else 'true')
        else: state='true' if 'true' in states else ('unknown' if 'unknown' in states else 'false')
        return {'op':rule['op'],'state':state,'children':children}
    actual=data.get(rule['field'])
    state='unknown' if actual is None else ('true' if OPS[rule['op']](actual,rule['value']) else 'false')
    label=FIELD_LABELS[rule['field']]
    def formatted(value):
        return f'{value*100:g}%' if rule['field']=='failed_ratio' else f'{value:g}'
    reason='Chưa có '+label.lower()+' của học kỳ đang xem.' if actual is None else f"{label}: {formatted(actual)}; điều kiện {OP_LABELS[rule['op']]} {formatted(rule['value'])} — "+('thỏa điều kiện.' if state=='true' else 'không thỏa điều kiện.')
    return {**rule,'actual':actual,'state':state,'reason':reason}

def clamp(x): return max(0,min(1,x))
def classify(score,c):
    return 'Nguy cơ cao' if score>=c['high'] else ('Cần chú ý' if score>=c['attention'] else 'Bình thường')

def evaluate(semesters, results, warnings, target, config=None):
    """Summer excluded; regular gaps/leave break trend. Repetition uses last 3 regular slots."""
    periods=sorted([s for s in semesters if s['sequence']<=target and s['kind']=='regular'],key=lambda x:x['sequence'])
    periods=periods if periods and periods[-1]['sequence']==target and periods[-1]['completed'] else []
    rs={r['sequence']:r for r in results if r['sequence']<=target}
    for r in rs.values():
        for key in ('gpa','cumulative_gpa'):
            if r.get(key) is not None and (not math.isfinite(r[key]) or not 0<=r[key]<=4): raise ValueError('GPA phải từ 0 đến 4')
        if any(r.get(k,0)<0 for k in ('registered','passed','failed')) or r.get('passed',0)+r.get('failed',0)!=r.get('registered',0): raise ValueError('Tín chỉ không nhất quán')
    current=rs.get(target,{}) if periods else {}
    if current.get('status')!='completed': current={}
    data={k:current.get(k) for k in FIELDS}
    data['failed_ratio']=current['failed']/current['registered'] if current.get('registered',0)>0 else None
    empty={'score':None,'level':'Chưa đủ dữ liệu','factors':[],'missing':[],'rule':None}
    if config is None: return {**empty,'rule_label':'Chưa có cấu hình áp dụng','missing':['Chưa có cấu hình áp dụng']}
    c=validate_config(config)
    term_name=periods[-1]['name'] if periods else 'học kỳ đang chọn'
    issues=[]
    values=[None]*4; reasons=[f'Chưa có GPA của {term_name}.',f'Chưa có số tín chỉ đăng ký hợp lệ của {term_name}.','Chưa đủ lịch sử để đánh giá xu hướng GPA.','Chưa đủ lịch sử quyết định cảnh báo.']
    actions=['Bổ sung GPA trong kết quả học kỳ; kiểm tra đồng bộ bảng điểm.', 'Bổ sung tín chỉ đăng ký, đạt và không đạt; tổng đạt + không đạt phải bằng đăng ký.', '', '']
    kinds=['missing','missing','history','history']
    used=[[],[],[],[]]
    if data['gpa'] is not None:
        values[0]=clamp((c['gpa_target']-data['gpa'])/c['gpa_span'])
        reasons[0]=f"GPA {term_name} đạt {data['gpa']:.2f}/4; "+(f"thấp hơn mốc hỗ trợ {c['gpa_target']:g} là {c['gpa_target']-data['gpa']:.2f} điểm." if data['gpa']<c['gpa_target'] else f"đạt mốc hỗ trợ {c['gpa_target']:g}; yếu tố này không cộng điểm ưu tiên.")
        used[0]=[target]
    if data['failed_ratio'] is not None:
        values[1]=clamp(data['failed_ratio']/c['fail_span']);reasons[1]=f"{current['failed']}/{current['registered']} tín chỉ không đạt ({data['failed_ratio']*100:.1f}%) trong {term_name}.";used[1]=[target]
    recent=periods[-3:]
    if len(recent)<3:
        reasons[2]=f'Mới có {len(recent)}/3 học kỳ chính trong thời gian theo học; chưa đủ để nhận xét xu hướng.'
        actions[2]='Tiếp tục theo dõi đến khi có 3 học kỳ chính hoàn thành. Không cần bổ sung học kỳ trước khi nhập học.'
    else:
        incomplete=[s['name'] for s in recent if not s['completed'] or rs.get(s['sequence'],{}).get('status')!='completed' or rs.get(s['sequence'],{}).get('gpa') is None]
        if incomplete:
            kinds[2]='missing'
            reasons[2]='Chưa đủ GPA hoàn chỉnh của '+', '.join(incomplete)+' để đối chiếu 3 kỳ liên tiếp.'
            actions[2]='Kiểm tra trạng thái học và bổ sung GPA cho các kỳ nêu trên; không tự điền điểm 0 cho dữ liệu chưa có.'
    if len(recent)==3 and all(s['completed'] for s in recent):
        rr=[rs.get(s['sequence'],{}) for s in recent]
        if all(r.get('status')=='completed' and r.get('gpa') is not None for r in rr):
            a,b,d=[r['gpa'] for r in rr];values[2]=clamp((a-d)/c['trend_span']) if a>b>d else 0
            reasons[2]=f"GPA {a:g} → {b:g} → {d:g} qua "+', '.join(s['name'] for s in recent)+(f'; giảm liên tiếp {a-d:.2f} điểm, cần trao đổi kế hoạch học tập.' if a>b>d else '; không giảm liên tiếp trong cả hai lần chuyển kỳ.')
            used[2]=[s['sequence'] for s in recent]
    prior=periods[:-1][-3:]; wh={w['sequence']:w['warned'] for w in warnings if w['sequence']<target}
    if len(prior)<3:
        reasons[3]=f'Mới có {len(prior)}/3 học kỳ chính trước kỳ đang xét để theo dõi cảnh báo lặp lại.'
        actions[3]='Tiếp tục theo dõi quyết định học vụ ở các kỳ tiếp theo; không suy diễn học kỳ chưa theo học là không cảnh báo.'
    else:
        absent=[s['name'] for s in prior if not s['completed'] or s['sequence'] not in wh]
        if absent:
            kinds[3]='missing'
            reasons[3]='Chưa có xác nhận quyết định cảnh báo của '+', '.join(absent)+'.'
            actions[3]='Nhập lịch sử cảnh báo cho các kỳ nêu trên: có cảnh báo hoặc đã xác nhận không cảnh báo; để trống không được xem là không cảnh báo.'
    if len(prior)==3 and all(s['completed'] and s['sequence'] in wh for s in prior):
        count=sum(bool(wh[s['sequence']]) for s in prior);values[3]=min(count/c['repeat_span'],1)
        decisions='; '.join(s['name']+': '+('cảnh báo' if wh[s['sequence']] else 'đã xác nhận không cảnh báo') for s in prior)
        reasons[3]=f"Có {count}/3 kỳ trước đã nhận cảnh báo. {decisions}.";used[3]=[s['sequence'] for s in prior]
    names=['GPA học kỳ','Tín chỉ không đạt','Xu hướng GPA','Cảnh báo lặp lại']
    factors=[{'name':n,'value':v,'weight':w,'contribution':round(v*w,4) if v is not None else None,'reason':r,'semesters':u} for n,v,w,r,u in zip(names,values,c['weights'],reasons,used)]
    for i,factor in enumerate(factors):
        if factor['value'] is None:
            issues.append({'factor':factor['name'],'kind':kinds[i],'reason':reasons[i],'action':actions[i]})
    score=round(sum(v*w for v,w in zip(values,c['weights'])),4) if all(v is not None for v in values) else None
    rule=rule_result(c['rule'],data)
    def rule_gaps(node):
        if 'children' in node:
            for child in node['children']: rule_gaps(child)
        elif node['state']=='unknown' and node['field'] not in ('gpa','failed_ratio'):
            label=FIELD_LABELS[node['field']]
            if not any(issue['factor']==label for issue in issues):
                issues.append({'factor':label,'kind':'missing','reason':f'Chưa có {label.lower()} của {term_name} để đối chiếu điều kiện học vụ.',
                               'action':f'Bổ sung {label.lower()} trong kết quả học kỳ {term_name}.'})
    rule_gaps(rule)
    contributing=sorted([f for f in factors if f['contribution'] is not None and f['contribution']>0],key=lambda f:-f['contribution'])
    summary=' '.join(f['reason'] for f in contributing[:2]) if contributing else ('Kết quả học tập ổn định; chưa ghi nhận yếu tố làm tăng điểm ưu tiên hỗ trợ.' if score is not None else 'Đã ghi nhận thông tin hiện có; cần thêm dữ liệu hoặc thời gian theo dõi để kết luận đầy đủ.')
    return {'score':score,'level':classify(score,c) if score is not None else 'Chưa đủ dữ liệu', 'factors':factors,
            'missing':list(dict.fromkeys(issue['reason'] for issue in issues)), 'data_issues':issues,'summary':summary,
            'completeness':{'available':sum(v is not None for v in values),'total':4},'rule':rule,
            'rule_label':{'true':'Thỏa điều kiện cảnh báo','false':'Không thỏa điều kiện','unknown':'Không đủ dữ liệu'}[rule['state']]}

def simulate(semesters,results,warnings,current_sequence,scenario,config):
    semesters=deepcopy([s for s in semesters if s['sequence']<=current_sequence])
    next_seq=max(s['sequence'] for s in semesters)+1
    semesters.append({'sequence':next_seq,'name':'Kỳ giả định tiếp theo','kind':'regular','completed':True})
    rows=deepcopy([r for r in results if r['sequence']<=current_sequence])
    rows.append({**scenario,'sequence':next_seq,'status':'completed','passed':scenario['registered']-scenario['failed']})
    return evaluate(semesters,rows,warnings,next_seq,config)
