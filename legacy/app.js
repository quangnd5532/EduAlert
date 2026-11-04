'use strict';
const $ = (s, root = document) => root.querySelector(s);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icons = {
 dashboard:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
 students:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M17 4a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-3.87',
 results:'M5 3h14v18H5zM9 7h6M9 11h6M9 15h2M9 18h5',
 warnings:'m12 3 10 18H2zM12 9v4M12 17h.01',
 interventions:'M9 5H5v16h14V5h-4M9 3h6v4H9zM8 12l2 2 5-5M8 18h8',
 import:'M12 16V3M7 8l5-5 5 5M3 16v5h18v-5',
 reports:'M4 3v18h17M8 16v-5M13 16V7M18 16v-8',
 settings:'M4 7h16M4 17h16M8 4v6M16 14v6',
 plus:'M12 5v14M5 12h14', download:'M12 3v13M7 11l5 5 5-5M3 17v4h18v-4',
 arrow:'M5 12h14M14 7l5 5-5 5', calendar:'M4 5h16v16H4zM8 3v4M16 3v4M4 11h16',
 leaf:'M19 4C6 2 2 11 8 17s15-2 11-13zM7 19l8-9', check:'M5 12l4 4L19 6', search:'M21 21l-5-5M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16'
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${icons[name] || icons.results}"/></svg>`;
const routes = [['dashboard','Tổng quan'],['students','Sinh viên'],['results','Kết quả học tập'],['warnings','Cảnh báo sớm'],['interventions','Theo dõi can thiệp'],['import','Nhập dữ liệu'],['reports','Báo cáo & thống kê'],['settings','Cấu hình đánh giá']];
const labels = {normal:'Bình thường',attention:'Cần chú ý',high:'Nguy cơ cao',no_data:'Chưa có dữ liệu',out_of_scope:'Ngoài phạm vi'};
const statuses = {planned:'Chưa bắt đầu',ongoing:'Đang theo dõi',completed:'Đã hoàn thành'};
const state = {students:[], interventions:[], settings:{}, filters:{}, page:1, route:'dashboard'};
const main = $('#main');
let toastTimer;
function toast(message) { $('#toast').textContent=message; $('#toast').classList.add('visible'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),4500); }
function errorText(detail) {
 if (Array.isArray(detail)) return detail.map(x => `${x.loc?.slice(1).join(' › ') || 'Dữ liệu'}: ${x.msg}`).join('\n');
 if (detail?.errors) return `${detail.message}\n${detail.errors.map(x=>`Dòng ${x.line}: ${x.message}`).join('\n')}`;
 return typeof detail === 'string' ? detail : detail?.message || 'Có lỗi xảy ra. Hãy thử lại.';
}
async function api(path, options={}) {
 const response = await fetch('/api'+path, { ...options, headers:{'Content-Type':'application/json',...options.headers} });
 const data = await response.json().catch(()=>({detail:'Phản hồi máy chủ không hợp lệ'}));
 if (!response.ok) throw new Error(errorText(data.detail));
 return data;
}
async function refresh() { [state.students,state.interventions,state.settings]=await Promise.all([api('/students'),api('/interventions'),api('/settings')]); }
const initials = name => name.split(' ').slice(-2).map(x=>x[0]).join('');
const badge = level => `<span class="badge ${esc(level)}">${esc(labels[level] || statuses[level] || level)}</span>`;
const fmt = value => value == null ? '—' : Number(value).toFixed(2);
const latestLabel = s => s.latest ? `HK${s.latest.semester} · ${s.latest.year}–${s.latest.year+1}` : 'Chưa có học kỳ';
const dateText = value => new Date(value+'T00:00:00').toLocaleDateString('vi-VN');
const sorted = list => [...list].sort((a,b)=>(b.risk.score ?? -1)-(a.risk.score ?? -1));
const byId = id => state.students.find(s=>s.id===id);
const studentName = s => `<div class="student-cell"><span class="avatar tone-${Number(s.id.slice(-1))%3}">${esc(initials(s.name))}</span><div><a href="#student/${encodeURIComponent(s.id)}">${esc(s.name)}</a><small>${esc(s.id)}</small></div></div>`;
const pageHead = (title,description,actions='') => `<div class="page-head"><div><h1>${esc(title)}</h1><p>${esc(description)}</p></div><div class="actions">${actions}</div></div>`;
const downloadButton = '<a class="btn" href="/api/export">'+icon('download')+'Xuất báo cáo</a>';
function table(list, options={}) {
 return `<div class="table-wrap"><table><thead><tr><th>SINH VIÊN</th><th>LỚP</th><th>GPA HỌC KỲ</th><th>ĐIỂM NGUY CƠ</th><th>PHÂN LOẠI SỚM</th><th>${options.academic?'ĐIỀU KIỆN QUY CHẾ':'THEO DÕI CAN THIỆP'}</th><th></th></tr></thead><tbody>${list.map(s=>{
 const intervention=state.interventions.find(x=>x.student_id===s.id);
 return `<tr><td>${studentName(s)}</td><td>${esc(s.class_name)}</td><td><strong class="${s.latest?.gpa<2?'text-red':''}">${fmt(s.latest?.gpa)}</strong></td><td><span class="score">${s.risk.score??'—'}</span>${s.risk.score!=null?`<span class="score-track"><i style="width:${s.risk.score}%;background:${s.risk.level==='high'?'#c47074':s.risk.level==='attention'?'#d3a45a':'#69a590'}"></i></span>`:''}</td><td>${badge(s.risk.level)}</td><td>${options.academic?`<span class="${s.risk.academic.length?'text-red':'inline-note'}">${s.risk.level==='no_data'?'Chưa có dữ liệu':s.risk.level==='out_of_scope'?'Ngoài phạm vi':s.risk.academic.length?'Có điều kiện cảnh báo':'Không có điều kiện'}</span>`:intervention?badge(intervention.status):'<span class="inline-note">Chưa có hồ sơ</span>'}</td><td><a class="row-link" href="#student/${encodeURIComponent(s.id)}" aria-label="Xem hồ sơ ${esc(s.name)}">${icon('arrow')}</a></td></tr>`;
 }).join('') || '<tr><td colspan="7"><div class="empty">Không có sinh viên phù hợp với bộ lọc.</div></td></tr>'}</tbody></table></div>`;
}
function counts(list=state.students) { return Object.fromEntries(Object.keys(labels).map(k=>[k,list.filter(s=>s.risk.level===k).length])); }
function stats() {
 const c=counts(); const active=state.interventions.filter(x=>x.status!=='completed').length;
 return `<div class="stats"><div class="stat"><div class="stat-label">Tổng sinh viên ${icon('students')}</div><div class="stat-value">${state.students.length}<small>sinh viên</small></div><div class="stat-caption">Trong danh sách quản lý</div></div><div class="stat"><div class="stat-label">Nguy cơ cao ${icon('warnings')}</div><div class="stat-value text-red">${c.high}<small>sinh viên</small></div><div class="stat-caption">Ưu tiên trao đổi và hỗ trợ</div></div><div class="stat"><div class="stat-label">Cần chú ý ${icon('results')}</div><div class="stat-value text-amber">${c.attention}<small>sinh viên</small></div><div class="stat-caption">Theo dõi thêm diễn biến học tập</div></div><div class="stat"><div class="stat-label">Đang can thiệp ${icon('interventions')}</div><div class="stat-value text-teal">${active}<small>hồ sơ</small></div><div class="stat-caption">Kế hoạch hỗ trợ chưa hoàn thành</div></div></div>`;
}
function lineChart(series, compare=null) {
 if(!series.length) return '<div class="empty">Chưa có dữ liệu để vẽ biểu đồ.</div>';
 const x=i=>52+(series.length===1?240:i*480/(series.length-1)); const y=v=>170-v/4*135;
 const coords=series.map((s,i)=>`${x(i)},${y(s.value)}`);
 return `<svg class="chart" viewBox="0 0 570 220" role="img" aria-label="Biểu đồ GPA theo học kỳ trên thang 4"><title>GPA theo học kỳ: ${series.map(s=>`${s.label}: ${fmt(s.value)}`).join('; ')}</title>${[0,1,2,3,4].map(n=>`<line x1="42" y1="${y(n)}" x2="548" y2="${y(n)}"/><text x="18" y="${y(n)+4}">${n}.0</text>`).join('')}<path class="area" d="M${x(0)},170 L${coords.join(' L')} L${x(series.length-1)},170 Z"/>${compare?`<polyline class="compare-line" points="${compare.map((v,i)=>`${x(i)},${y(v)}`).join(' ')}"/>`:''}<polyline class="gpa-line" points="${coords.join(' ')}"/>${series.map((s,i)=>`<circle cx="${x(i)}" cy="${y(s.value)}" r="4" fill="#fff" stroke="#087f76" stroke-width="2"/><text x="${x(i)}" y="${y(s.value)-12}" text-anchor="middle">${fmt(s.value)}</text><text x="${x(i)}" y="197" text-anchor="middle">${esc(s.label)}</text>`).join('')}</svg>`;
}
function distribution(list=state.students) {
 const c=counts(list), colors={normal:'#559483',attention:'#d6ac61',high:'#c77a7e',no_data:'#b7c7c3',out_of_scope:'#929fba'};
 let offset=0; const arcs=Object.keys(labels).map(k=>{const length=list.length?c[k]/list.length*100:0;const arc=`<circle cx="80" cy="80" r="64" fill="none" stroke="${colors[k]}" stroke-width="17" pathLength="100" stroke-dasharray="${length} ${100-length}" stroke-dashoffset="${-offset}"/>`;offset+=length;return arc;}).join('');
 return `<div class="distribution"><div class="donut"><svg viewBox="0 0 160 160" role="img" aria-label="Phân bố mức nguy cơ"><circle cx="80" cy="80" r="64" fill="none" stroke="#edf1ee" stroke-width="17"/>${arcs}</svg><div class="donut-center"><strong>${list.length}</strong><small>sinh viên</small></div></div><div class="distribution-list">${Object.keys(labels).filter(k=>c[k]||['normal','attention','high'].includes(k)).map(k=>`<div class="distribution-item"><span><i class="dot" style="background:${colors[k]}"></i>${labels[k]}</span><b>${c[k]} <span class="inline-note">(${list.length?Math.round(c[k]/list.length*100):0}%)</span></b></div>`).join('')}</div></div>`;
}
function aggregateSeries() {
 const periods = [...new Set(state.students.flatMap(s=>s.terms.map(t=>`${t.year}-${t.semester}`)))].sort();
 return periods.map(key=>{const terms=state.students.flatMap(s=>s.terms.filter(t=>`${t.year}-${t.semester}`===key));const [year,semester]=key.split('-');return {label:`HK${semester} · ${year}`,value:terms.reduce((v,t)=>v+t.gpa,0)/terms.length};});
}
function dashboard() {
 const c=counts(), priority=sorted(state.students.filter(s=>['high','attention'].includes(s.risk.level)));
 if(!state.students.length) return `${pageHead('Chào mừng đến với EduAlert','Không gian đồng hành của cố vấn học tập.')}<section class="panel intro-empty"><span class="brand-mark" style="margin:auto">${icon('leaf')}</span><h1>Bắt đầu từ việc hiểu sinh viên.</h1><p>Nhập kết quả học tập để nhận diện dấu hiệu sa sút, xem lý do cảnh báo và tổ chức hỗ trợ đúng lúc.</p><div class="actions"><button class="btn primary" data-action="demo">Khám phá với 24 hồ sơ minh họa</button><a class="btn" href="#import">Nhập dữ liệu CSV</a></div><p class="inline-note">Dữ liệu mẫu chỉ được tạo khi danh sách đang trống.</p></section>`;
 return `${pageHead('Tổng quan học tập','Một góc nhìn đầy đủ hơn. Một sự hỗ trợ kịp thời hơn.',downloadButton+'<a class="btn primary" href="#import">'+icon('plus')+'Nhập dữ liệu</a>')}
 <div class="welcome-strip"><div class="welcome-copy"><span class="round-icon">${icon('leaf')}</span><div><strong>${c.high+c.attention} sinh viên cần được quan tâm thêm</strong><p>Ưu tiên các trường hợp nguy cơ cao và bắt đầu bằng một cuộc trao đổi.</p></div></div><a href="#warnings" class="btn">Xem danh sách ${icon('arrow')}</a></div>
 ${stats()}<div class="dashboard-grid"><section class="panel"><div class="panel-head"><div><h2>Diễn biến kết quả học tập</h2><p class="panel-sub">GPA trung bình theo học kỳ · thang điểm 4</p></div><span class="legend"><span><i class="dot"></i>GPA học kỳ</span></span></div>${lineChart(aggregateSeries())}<div class="panel-note">Mỗi điểm là trung bình của các sinh viên có dữ liệu trong học kỳ đó.</div></section>
 <section class="panel"><div class="panel-head"><div><h2>Phân bố mức nguy cơ</h2><p class="panel-sub">Theo học kỳ mới nhất của từng sinh viên</p></div></div>${distribution()}<div class="panel-note">Điểm cảnh báo sớm được tính độc lập với điều kiện cảnh báo theo quy chế.</div></section></div>
 <section class="panel table-panel"><div class="panel-head"><div><h2>Sinh viên cần ưu tiên hỗ trợ</h2><p class="panel-sub">Sắp xếp theo điểm nguy cơ từ cao xuống thấp</p></div><a class="link-small" href="#warnings">Xem tất cả ${icon('arrow')}</a></div>${table(priority.slice(0,5))}<div class="table-foot"><span>Hiển thị ${Math.min(5,priority.length)} / ${priority.length} sinh viên cần hỗ trợ</span><span>Cập nhật từ dữ liệu đã lưu</span></div></section>`;
}
const optionList = (values,selected,placeholder) => `<option value="">${esc(placeholder)}</option>${values.map(v=>`<option value="${esc(v)}" ${v===selected?'selected':''}>${esc(v)}</option>`).join('')}`;
const unique = key => [...new Set(state.students.map(s=>s[key]))].sort();
function filters() {
 const f=state.filters;
 return `<div class="filter-bar"><input id="search" type="search" aria-label="Tìm sinh viên" placeholder="Tìm theo tên hoặc mã sinh viên…" value="${esc(f.search||'')}"><select data-filter="class_name" aria-label="Lọc lớp">${optionList(unique('class_name'),f.class_name,'Tất cả lớp')}</select><select data-filter="major" aria-label="Lọc ngành">${optionList(unique('major'),f.major,'Tất cả ngành')}</select><select data-filter="cohort" aria-label="Lọc khóa">${optionList(unique('cohort'),f.cohort,'Tất cả khóa')}</select><select data-filter="level" aria-label="Lọc mức nguy cơ"><option value="">Tất cả mức nguy cơ</option>${Object.keys(labels).map(k=>`<option value="${k}" ${f.level===k?'selected':''}>${labels[k]}</option>`).join('')}</select><button class="btn" data-action="clear-filters">Đặt lại</button></div>`;
}
function filteredStudents() {
 const f=state.filters, query=(f.search||'').toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');
 return state.students.filter(s=>`${s.name} ${s.id}`.toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').includes(query) && ['class_name','major','cohort'].every(k=>!f[k]||s[k]===f[k]) && (!f.level||s.risk.level===f.level) && (state.route!=='warnings'||['high','attention'].includes(s.risk.level)));
}
function renderListBody() {
 let list=filteredStudents(); if(state.route==='warnings') list=sorted(list);
 const perPage=10,totalPages=Math.max(1,Math.ceil(list.length/perPage)); state.page=Math.min(state.page,totalPages);
 $('#list-body').innerHTML=table(list.slice((state.page-1)*perPage,state.page*perPage),{academic:state.route==='warnings'})+`<div class="table-foot"><span>${list.length} sinh viên phù hợp</span><div class="pagination"><button class="btn" data-action="prev" ${state.page<=1?'disabled':''}>Trước</button><span>${state.page} / ${totalPages}</span><button class="btn" data-action="next" ${state.page>=totalPages?'disabled':''}>Sau</button></div></div>`;
}
function studentList(warnings=false) {
 return `${pageHead(warnings?'Cảnh báo sớm':'Danh sách sinh viên',warnings?'Nhận diện dấu hiệu sa sút, ưu tiên hỗ trợ theo từng trường hợp.':'Quản lý hồ sơ và kết quả học tập trong không gian cố vấn.',warnings?downloadButton:'<button class="btn primary" data-action="add-student">'+icon('plus')+'Thêm sinh viên</button>')}${warnings?'<div class="notice warning">Điểm nguy cơ là tín hiệu hỗ trợ. Cột điều kiện quy chế sử dụng bộ quy tắc cấu hình, không tự động ban hành quyết định cảnh báo học vụ.</div>':''}${filters()}<section class="panel table-panel" id="list-body"></section>`;
}
function results() {
 return `${pageHead('Kết quả học tập','Xem và cập nhật dữ liệu từng học kỳ của sinh viên.','<button class="btn primary" data-action="add-term">'+icon('plus')+'Nhập kết quả học kỳ</button>')}<div class="notice">Bảng dưới hiển thị học kỳ mới nhất của từng sinh viên. Mở hồ sơ để xem đầy đủ lịch sử và diễn biến GPA.</div>${filters()}<section class="panel table-panel" id="list-body"></section>`;
}
function studentDetail(id) {
 const s=byId(id); if(!s) return `${pageHead('Không tìm thấy sinh viên','Mã sinh viên không tồn tại trong danh sách.')}<a class="btn" href="#students">Về danh sách sinh viên</a>`;
 const risk=s.risk, items=state.interventions.filter(x=>x.student_id===id);
 return `${pageHead('Hồ sơ sinh viên','Kết nối dữ liệu học tập với quá trình hỗ trợ.','<button class="btn" data-action="add-term" data-id="'+esc(id)+'">'+icon('plus')+'Thêm học kỳ</button><button class="btn primary" data-action="add-intervention" data-id="'+esc(id)+'">'+icon('plus')+'Tạo can thiệp</button>')}
 <section class="panel"><div class="detail-top"><span class="avatar">${esc(initials(s.name))}</span><div><h2 style="font-size:21px">${esc(s.name)}</h2><span class="inline-note">${esc(s.id)} · ${esc(s.class_name)}</span></div><div style="margin-left:auto">${badge(risk.level)}</div></div><dl class="meta-list">${[['Ngành',s.major],['Khóa',s.cohort],['Cố vấn phụ trách',s.advisor],['Điểm tuyển sinh',`${s.admission_score??'Chưa nhập'} / ${s.admission_scale} · ${s.admission_method}`],['Học kỳ mới nhất',latestLabel(s)],['GPA tích lũy',fmt(s.latest?.cumulative_gpa)]].map(([k,v])=>`<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl></section>
 <div class="detail-grid"><section class="panel"><h2>Điểm cảnh báo sớm</h2><div class="big-score">${risk.score??'—'}<small> / 100 điểm</small></div>${badge(risk.level)}<div style="margin-top:14px">${risk.reasons.map(r=>`<div class="reason"><span>${esc(r.text)}</span><b>+${r.points} điểm</b></div>`).join('')||'<p class="inline-note">'+(risk.level==='normal'?'Chưa ghi nhận yếu tố nguy cơ theo cấu hình hiện tại.':risk.level==='out_of_scope'?'Khóa của sinh viên nằm ngoài phạm vi bộ quy tắc.':'Cần nhập kết quả học kỳ để đánh giá.')+'</p>'}</div><div class="panel-note">Tổng các yếu tố được giới hạn ở 100. ${s.terms.length<3?'Chưa đủ 3 học kỳ để đánh giá xu hướng giảm qua hai kỳ.':''} ${s.latest?.conduct==null?'Chưa có điểm rèn luyện; yếu tố này chưa được chấm.':''}</div></section>
 <section class="panel"><h2>Kiểm tra điều kiện theo quy chế</h2><p class="panel-sub">${esc(risk.rule_name)}</p><div class="notice ${risk.academic.length?'warning':''}" style="margin-top:20px">${risk.level==='no_data'?'Chưa có dữ liệu học kỳ.':risk.level==='out_of_scope'?'Ngoài phạm vi áp dụng của bộ quy tắc.':risk.academic.length?'Có điều kiện cảnh báo theo bộ quy tắc đã cấu hình.':'Không có điều kiện cảnh báo theo bộ quy tắc đã cấu hình.'}</div>${risk.academic.map(r=>`<div class="reason">${esc(r)}</div>`).join('')}<div class="panel-note">Bộ quy tắc mặc định là minh họa. Cố vấn cần đối chiếu quy chế chính thức trước khi sử dụng kết quả.</div></section></div>
 <section class="panel" style="margin-bottom:22px"><div class="panel-head"><h2>Diễn biến GPA</h2><div class="legend"><span><i class="dot"></i>Học kỳ</span><span><i class="dot gray"></i>Tích lũy</span></div></div>${lineChart(s.terms.map(t=>({label:`HK${t.semester} · ${t.year}`,value:t.gpa})),s.terms.map(t=>t.cumulative_gpa))}</section>
 <section class="panel table-panel" style="margin-bottom:22px"><div class="panel-head"><h2>Lịch sử học tập</h2><span class="inline-note">Chọn chỉnh sửa để cập nhật kỳ đã nhập</span></div><div class="table-wrap"><table><thead><tr><th>HỌC KỲ</th><th>GPA</th><th>TÍCH LŨY</th><th>TC ĐĂNG KÝ</th><th>ĐẠT / KHÔNG ĐẠT</th><th>HỌC PHẦN NỢ</th><th>RÈN LUYỆN</th><th>CẢNH BÁO TRƯỚC KỲ</th><th></th></tr></thead><tbody>${s.terms.map(t=>`<tr><td>HK${t.semester} · ${t.year}–${t.year+1}</td><td>${fmt(t.gpa)}</td><td>${fmt(t.cumulative_gpa)}</td><td>${t.registered}</td><td>${t.passed} / ${t.failed}</td><td>${t.debt}</td><td>${t.conduct??'—'}</td><td>${t.previous_warnings}</td><td><button class="btn" data-action="edit-term" data-id="${esc(id)}" data-year="${t.year}" data-semester="${t.semester}">Sửa</button></td></tr>`).join('')||'<tr><td colspan="9"><div class="empty">Chưa nhập học kỳ nào.</div></td></tr>'}</tbody></table></div></section>
 <section class="panel"><div class="panel-head"><h2>Quá trình can thiệp</h2><button class="btn" data-action="add-intervention" data-id="${esc(id)}">Thêm ghi nhận</button></div>${items.map(interventionCard).join('')||'<p class="inline-note">Chưa có hồ sơ. Bắt đầu ghi nhận khi cố vấn trao đổi với sinh viên.</p>'}</section>`;
}
function interventionCard(item) {
 const s=byId(item.student_id), overdue=item.status!=='completed' && item.due_date < new Date().toLocaleDateString('sv-SE');
 return `<article class="timeline-item"><div class="timeline-title"><strong><a href="#student/${encodeURIComponent(item.student_id)}">${esc(s?.name||item.student_id)}</a> <span class="inline-note">· ${esc(s?.class_name||'')}</span></strong>${badge(item.status)}</div><p>${esc(item.note)}</p><p><strong>Biện pháp:</strong> ${esc(item.action)}</p>${item.outcome?`<p><strong>Kết quả:</strong> ${esc(item.outcome)}</p>`:''}<div class="timeline-actions"><small>Cố vấn: ${esc(item.advisor)} · <span class="${overdue?'text-red':''}">${overdue?'Quá hạn theo dõi':'Hẹn theo dõi'}: ${dateText(item.due_date)}</span></small><button class="btn" data-action="edit-intervention" data-id="${item.id}">Cập nhật</button></div></article>`;
}
function interventions() {
 return `${pageHead('Theo dõi can thiệp','Ghi nhận trao đổi, kế hoạch hỗ trợ và những tiến bộ nhỏ.','<button class="btn primary" data-action="add-intervention">'+icon('plus')+'Tạo hồ sơ can thiệp</button>')}<div class="filter-bar"><select id="intervention-status" aria-label="Trạng thái can thiệp"><option value="">Tất cả trạng thái</option>${Object.entries(statuses).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select><span class="count-label">${state.interventions.length} hồ sơ can thiệp</span><a class="btn" style="margin-left:auto" href="/api/export/interventions">${icon('download')}Xuất hồ sơ CSV</a></div><section class="panel" id="intervention-list">${state.interventions.map(interventionCard).join('')||'<div class="empty">Chưa có hồ sơ can thiệp. Chọn “Tạo hồ sơ can thiệp” để bắt đầu.</div>'}</section>`;
}
function importPage() {
 return `${pageHead('Nhập dữ liệu','Đưa dữ liệu vào EduAlert, bắt đầu từ một tệp CSV.','<a class="btn" href="/api/import/template">'+icon('download')+'Tải mẫu CSV</a>')}<section class="panel"><h2>Nhập sinh viên & kết quả học tập</h2><p class="panel-sub">Mỗi dòng là một sinh viên trong một học kỳ. Có thể nhập nhiều học kỳ trong cùng tệp.</p><form id="import-form"><div class="upload-area">${icon('import')}<h2>Chọn tệp dữ liệu của bạn</h2><p>CSV mã hóa UTF-8 · tối đa 2 MB và 5.000 dòng</p><input id="csv-file" name="file" type="file" accept=".csv,text/csv" required aria-label="Chọn tệp CSV"><button class="btn primary" type="submit">Kiểm tra & nhập dữ liệu</button></div><div id="import-result" aria-live="polite"></div></form><div class="notice warning">Dữ liệu cùng mã sinh viên và học kỳ sẽ được cập nhật. Toàn bộ tệp được kiểm tra trước khi lưu; nếu có dòng lỗi, không dòng nào được nhập.</div><div class="steps"><div><h3>1. Chuẩn bị theo mẫu</h3><p>Giữ nguyên tên cột. Ghi đầy đủ phương thức và thang điểm tuyển sinh.</p></div><div><h3>2. Kiểm tra kết quả</h3><p>GPA thang 4, rèn luyện thang 100. Tín chỉ đạt + không đạt phải bằng số đăng ký.</p></div><div><h3>3. Xem cảnh báo</h3><p>Sau khi lưu, hệ thống tính lại điểm nguy cơ và hiển thị các lý do.</p></div></div></section>`;
}
function reports() {
 const c=counts(), classes=unique('class_name');
 return `${pageHead('Báo cáo & thống kê','Nhìn rõ tình hình học tập trong từng lớp và ngành.',downloadButton)}${stats()}<div class="dashboard-grid"><section class="panel"><div class="panel-head"><h2>Sinh viên cần hỗ trợ theo lớp</h2><span class="inline-note">Cần chú ý + Nguy cơ cao</span></div>${classes.map(name=>{const list=state.students.filter(s=>s.class_name===name),n=list.filter(s=>['high','attention'].includes(s.risk.level)).length;return `<div class="report-row"><span>${esc(name)}</span><div class="report-bar"><i style="width:${n/list.length*100}%"></i></div><strong>${n}/${list.length}</strong></div>`;}).join('')||'<div class="empty">Chưa có dữ liệu.</div>'}<div class="panel-note">Độ dài thanh biểu thị tỷ lệ sinh viên cần hỗ trợ trong lớp.</div></section><section class="panel"><h2>Phân bố mức nguy cơ</h2>${distribution()}</section></div><section class="panel table-panel"><div class="panel-head"><h2>Thống kê theo ngành</h2></div><div class="table-wrap"><table><thead><tr><th>NGÀNH</th><th>SINH VIÊN</th><th>GPA TRUNG BÌNH</th><th>CẦN CHÚ Ý</th><th>NGUY CƠ CAO</th><th>CÓ ĐIỀU KIỆN QUY CHẾ</th></tr></thead><tbody>${unique('major').map(major=>{const list=state.students.filter(s=>s.major===major),withTerms=list.filter(s=>s.latest),countsBy=counts(list);return `<tr><td>${esc(major)}</td><td>${list.length}</td><td>${withTerms.length?fmt(withTerms.reduce((a,s)=>a+s.latest.gpa,0)/withTerms.length):'—'}</td><td>${countsBy.attention}</td><td>${countsBy.high}</td><td>${list.filter(s=>s.risk.academic.length).length}</td></tr>`;}).join('')||'<tr><td colspan="6"><div class="empty">Chưa có dữ liệu.</div></td></tr>'}</tbody></table></div><div class="table-foot">GPA thống kê từ học kỳ mới nhất của mỗi sinh viên có dữ liệu. Quy chế và nguy cơ sớm được đếm độc lập.</div></section>`;
}
function field(name,label,value='',type='text',attrs='',hint='') {
 return `<label class="field"><span>${esc(label)}</span><input name="${name}" type="${type}" value="${esc(value)}" ${attrs}>${hint?`<small>${esc(hint)}</small>`:''}</label>`;
}
function settingsPage() {
 const s=state.settings;
 return `${pageHead('Cấu hình đánh giá','Các ngưỡng rõ ràng, các kết quả có thể giải thích.')}<div class="settings-layout"><div class="notice warning">Các giá trị mặc định chỉ phục vụ minh họa đồ án. Nhập ngưỡng đã được trường xác nhận trước khi sử dụng thực tế. MVP hỗ trợ một bộ quy tắc đang hoạt động, áp dụng cho tất cả khóa hoặc một khóa cụ thể.</div><form id="settings-form"><section class="panel"><div class="form-section"><h2>Phạm vi áp dụng</h2><div class="form-grid">${field('name','Tên bộ quy tắc',s.name,'text','required maxlength="120"')}${field('cohort','Khóa áp dụng',s.cohort,'text','required maxlength="30"','Nhập * để áp dụng cho tất cả khóa.')}</div></div><h2>Điều kiện cảnh báo theo quy chế</h2><p class="panel-sub" style="margin-bottom:20px">Một trong các điều kiện sau đúng thì kết quả ghi nhận có điều kiện cảnh báo.</p><div class="form-grid">${field('academic_gpa','GPA học kỳ nhỏ hơn',s.academic_gpa,'number','required min="0" max="4" step="0.01"')}${field('academic_cumulative','GPA tích lũy nhỏ hơn',s.academic_cumulative,'number','required min="0" max="4" step="0.01"')}${field('academic_failed_ratio','Tỷ lệ tín chỉ không đạt từ',s.academic_failed_ratio,'number','required min="0.01" max="1" step="0.01"','Giá trị 0.5 tương ứng 50%.')}</div></section><section class="panel"><h2>Điểm cảnh báo sớm</h2><p class="panel-sub" style="margin-bottom:20px">Cộng điểm của các yếu tố thỏa mãn, giới hạn tổng ở 100.</p><div class="form-grid">${field('low_gpa','Ngưỡng GPA thấp',s.low_gpa,'number','required min="0" max="4" step="0.01"')}${field('low_gpa_weight','Điểm khi GPA thấp hơn ngưỡng',s.low_gpa_weight,'number','required min="0" max="100" step="1"')}${field('decline_weight','Điểm khi GPA giảm liên tiếp qua hai kỳ',s.decline_weight,'number','required min="0" max="100" step="1"','Cần ít nhất 3 học kỳ có dữ liệu.')}${field('failed_weight','Điểm khi tín chỉ không đạt tăng',s.failed_weight,'number','required min="0" max="100" step="1"','So với học kỳ đã nhập liền trước.')}${field('repeat_weight','Điểm khi đã có cảnh báo trước kỳ này',s.repeat_weight,'number','required min="0" max="100" step="1"')}${field('conduct_weight','Điểm khi rèn luyện dưới 50/100',s.conduct_weight,'number','required min="0" max="100" step="1"')}${field('attention','Cần chú ý: điểm từ',s.attention,'number','required min="1" max="99" step="1"')}${field('high','Nguy cơ cao: điểm từ',s.high,'number','required min="2" max="100" step="1"')}</div><div class="panel-note">Bình thường: dưới ngưỡng cần chú ý. Điểm tuyển sinh chỉ dùng làm thông tin bối cảnh, không được chấm vào điểm nguy cơ.</div><div class="form-error" role="alert"></div><div class="form-footer"><button class="btn primary" type="submit">Lưu cấu hình & tính lại</button></div></section></form></div>`;
}
function render() {
 const [route,id]=location.hash.slice(1).split('/');
 const previous=state.route; state.route=route||'dashboard';
 if(previous!==state.route){state.filters={};state.page=1;}
 const active=state.route==='student'?'students':state.route;
 $('#navigation').innerHTML=routes.map(([key,label])=>`<a href="#${key}" class="${active===key?'active':''}" ${active===key?'aria-current="page"':''}>${icon(key)}${label}</a>`).join('');
 $('#breadcrumb').textContent=state.route==='student'?'Hồ sơ sinh viên':routes.find(x=>x[0]===state.route)?.[1]||'Trang không tồn tại';
 const views={dashboard,students:()=>studentList(),warnings:()=>studentList(true),results,student:()=>studentDetail(decodeURIComponent(id||'')),interventions,import:importPage,reports,settings:settingsPage};
 main.innerHTML=views[state.route]?.()||`${pageHead('Trang không tồn tại','Chọn một mục trong thanh điều hướng để tiếp tục.')}<a class="btn" href="#dashboard">Về tổng quan</a>`;
 if(['students','warnings','results'].includes(state.route)) renderListBody();
 document.title=`${$('#breadcrumb').textContent} · EduAlert`;
}
function openDialog(title,body,onSubmit) {
 const dialog=$('#form-dialog');
 $('#dialog-content').innerHTML=`<div class="dialog-head"><h2 id="dialog-title">${esc(title)}</h2><button type="button" class="close-btn" aria-label="Đóng biểu mẫu">×</button></div><form id="dialog-form">${body}<div class="form-error" role="alert"></div><div class="form-footer"><button type="button" class="btn cancel">Hủy</button><button class="btn primary" type="submit">Lưu thông tin</button></div></form>`;
 $('.close-btn',dialog).onclick=()=>dialog.close();$('.cancel',dialog).onclick=()=>dialog.close();
 $('#dialog-form').onsubmit=async event=>{event.preventDefault();const form=event.currentTarget;$('.form-error',form).textContent='';const button=$('[type=submit]',form);button.disabled=true;
 try { await onSubmit(Object.fromEntries(new FormData(form))); await refresh(); dialog.close(); render(); toast('Đã lưu thông tin.'); }
 catch(error){$('.form-error',form).textContent=error.message;}finally{button.disabled=false;}};
 dialog.showModal();
}
function studentForm() {
 openDialog('Thêm sinh viên',`<div class="form-grid">${field('id','Mã sinh viên','','text','required maxlength="30" pattern="[A-Za-z0-9_-]+"')}${field('name','Họ và tên','','text','required maxlength="120"')}${field('class_name','Lớp','','text','required maxlength="60"')}${field('major','Ngành','Công nghệ thông tin','text','required maxlength="100"')}${field('cohort','Khóa','2023','text','required maxlength="30"')}${field('advisor','Cố vấn phụ trách','','text','required maxlength="100"')}${field('admission_score','Điểm tuyển sinh (không bắt buộc)','','number','min="0" step="0.01"')}${field('admission_scale','Thang điểm tuyển sinh',30,'number','required min="0.01" max="1000" step="0.01"')}${field('admission_method','Phương thức xét tuyển','THPT','text','maxlength="100"')}</div>`, data=>{data.admission_score=data.admission_score===''?null:Number(data.admission_score);data.admission_scale=Number(data.admission_scale);return api('/students',{method:'POST',body:JSON.stringify(data)});});
}
function studentSelect(selected='',disabled=false) {
 return `<label class="field full"><span>Sinh viên</span><select name="student_id" required ${disabled?'disabled':''}><option value="">Chọn sinh viên…</option>${state.students.map(s=>`<option value="${esc(s.id)}" ${selected===s.id?'selected':''}>${esc(s.name)} · ${esc(s.id)}</option>`).join('')}</select></label>`;
}
function termForm(id='',year=null,semester=null) {
 if(!state.students.length){toast('Thêm sinh viên trước khi nhập kết quả học kỳ.');return;}
 const term=byId(id)?.terms.find(t=>t.year===Number(year)&&t.semester===Number(semester))||{};
 const editing=!!term.year;
 openDialog(editing?'Cập nhật học kỳ':'Nhập kết quả học kỳ',`<div class="notice">Năm là năm bắt đầu của năm học. Ví dụ: 2025 tương ứng 2025–2026. Lưu cùng sinh viên, năm và học kỳ sẽ cập nhật dữ liệu cũ.</div><div class="form-grid">${studentSelect(id,editing)}${field('year','Năm bắt đầu',term.year||2025,'number',`required min="2000" max="2100" ${editing?'readonly':''}`)}${field('semester','Học kỳ (1–3)',term.semester||1,'number',`required min="1" max="3" ${editing?'readonly':''}`)}${field('gpa','GPA học kỳ',term.gpa??'','number','required min="0" max="4" step="0.01"')}${field('cumulative_gpa','GPA tích lũy',term.cumulative_gpa??'','number','required min="0" max="4" step="0.01"')}${field('registered','Tín chỉ đăng ký',term.registered??18,'number','required min="1" max="60"')}${field('passed','Tín chỉ đạt',term.passed??18,'number','required min="0" max="60"')}${field('failed','Tín chỉ không đạt',term.failed??0,'number','required min="0" max="60"')}${field('debt','Số học phần còn nợ',term.debt??0,'number','required min="0" max="200"')}${field('conduct','Điểm rèn luyện (không bắt buộc)',term.conduct??'','number','min="0" max="100" step="0.1"')}${field('previous_warnings','Số cảnh báo trước kỳ này',term.previous_warnings??0,'number','required min="0" max="30"')}</div>`, data=>{
 const sid=editing?id:data.student_id;delete data.student_id;for(const k of Object.keys(data)) data[k]=data[k]===''?null:Number(data[k]);
 return api(`/students/${encodeURIComponent(sid)}/terms`,{method:'PUT',body:JSON.stringify(data)});
 });
}
function interventionForm(sid='',editId=null) {
 if(!state.students.length){toast('Thêm sinh viên trước khi tạo hồ sơ can thiệp.');return;}
 const item=state.interventions.find(x=>x.id===Number(editId))||{}, student=byId(item.student_id||sid);
 openDialog(editId?'Cập nhật can thiệp':'Tạo hồ sơ can thiệp',`<div class="form-grid">${studentSelect(item.student_id||sid,!!editId)}${field('advisor','Cố vấn thực hiện',item.advisor||student?.advisor||'','text','required maxlength="100"')}${field('due_date','Ngày hẹn theo dõi',item.due_date||new Date(Date.now()+7*86400000).toLocaleDateString('sv-SE'),'date','required')}<label class="field full"><span>Ghi chú trao đổi</span><textarea name="note" required maxlength="3000">${esc(item.note||'')}</textarea></label><label class="field full"><span>Biện pháp hỗ trợ</span><textarea name="action" required maxlength="2000">${esc(item.action||'')}</textarea></label><label class="field"><span>Trạng thái</span><select name="status">${Object.entries(statuses).map(([k,v])=>`<option value="${k}" ${item.status===k?'selected':''}>${v}</option>`).join('')}</select></label><label class="field full"><span>Kết quả theo dõi</span><textarea name="outcome" maxlength="2000">${esc(item.outcome||'')}</textarea></label></div>`,data=>{if(editId)data.student_id=item.student_id;return api('/interventions'+(editId?'/'+editId:''),{method:editId?'PUT':'POST',body:JSON.stringify(data)});});
 const select=$('[name=student_id]',$('#form-dialog'));
 if(!editId) select.addEventListener('change',()=>{const advisor=$('[name=advisor]',$('#form-dialog'));advisor.value=byId(select.value)?.advisor||'';});
}
document.addEventListener('click', async event=>{
 const button=event.target.closest('[data-action]');if(!button)return;
 const {action,id,year,semester}=button.dataset;
 if(action==='add-student')studentForm();
 if(action==='add-term')termForm(id);
 if(action==='edit-term')termForm(id,year,semester);
 if(action==='add-intervention')interventionForm(id);
 if(action==='edit-intervention')interventionForm('',id);
 if(action==='clear-filters'){state.filters={};state.page=1;render();}
 if(action==='prev'||action==='next'){state.page+=action==='next'?1:-1;renderListBody();}
 if(action==='demo'){button.disabled=true;try{await api('/demo',{method:'POST'});await refresh();render();toast('Đã tạo 24 hồ sơ minh họa.');}catch(error){toast(error.message);button.disabled=false;}}
});
document.addEventListener('input',event=>{if(event.target.id==='search'){state.filters.search=event.target.value;state.page=1;renderListBody();}});
document.addEventListener('change',event=>{
 if(event.target.dataset.filter){state.filters[event.target.dataset.filter]=event.target.value;state.page=1;renderListBody();}
 if(event.target.id==='intervention-status'){const items=state.interventions.filter(x=>!event.target.value||x.status===event.target.value);$('#intervention-list').innerHTML=items.map(interventionCard).join('')||'<div class="empty">Không có hồ sơ ở trạng thái này.</div>';}
});
document.addEventListener('submit',async event=>{
 const form=event.target;if(!['settings-form','import-form'].includes(form.id))return;event.preventDefault();
 const button=$('[type=submit]',form);button.disabled=true;
 try{
 if(form.id==='settings-form'){
 const data=Object.fromEntries(new FormData(form));for(const k of Object.keys(data)) if(!['name','cohort'].includes(k))data[k]=Number(data[k]);
 await api('/settings',{method:'PUT',body:JSON.stringify(data)});await refresh();render();toast('Đã lưu cấu hình và tính lại kết quả.');
 }else{
 const file=$('#csv-file').files[0];if(!file)throw new Error('Chọn tệp CSV trước khi nhập.');if(file.size>2000000)throw new Error('Tệp vượt quá 2 MB. Hãy chia nhỏ tệp.');
 const result=await api('/import',{method:'POST',headers:{'Content-Type':'text/csv'},body:file});
 await refresh();$('#import-result').innerHTML=`<div class="notice">Đã lưu ${result.rows} học kỳ cho ${result.students} sinh viên. <a href="#warnings">Xem kết quả cảnh báo →</a></div>`;form.reset();
 }
 }catch(error){if(form.id==='settings-form')$('.form-error',form).textContent=error.message;else $('#import-result').innerHTML=`<div class="notice error error-details">${esc(error.message)}</div>`;}finally{button.disabled=false;}
});
window.addEventListener('hashchange',()=>{render();window.scrollTo({top:0});});
$('#today').textContent=new Date().toLocaleDateString('vi-VN',{day:'numeric',month:'long',year:'numeric'});
async function boot(){try{await refresh();render();}catch(error){main.innerHTML=`${pageHead('Chưa kết nối được máy chủ','Khởi động FastAPI rồi tải lại trang để tiếp tục.')}<div class="notice error">${esc(error.message)}</div><button class="btn primary" id="retry">Thử kết nối lại</button>`;$('#retry').onclick=boot;}}
boot();
