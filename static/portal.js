'use strict';
const $=(s,root=document)=>root.querySelector(s), $$=(s,root=document)=>[...root.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const page=document.body.dataset.page, sid=document.body.dataset.student;
const catalogs=JSON.parse($('#catalog-data').textContent), charts={}, csrf=$('meta[name="csrf-token"]').content;
let detailData=null, currentPage=1, board=false, importId=null;
const statuses=['Chưa xử lý','Đang hỗ trợ','Chờ theo dõi','Hoàn tất'];
const levels=['Bình thường','Cần chú ý','Nguy cơ cao','Chưa đủ dữ liệu'];
const colors=['#36856b','#b47b1e','#c54f65','#8d9bb2'];
const fieldLabels={gpa:'GPA học kỳ',cumulative_gpa:'GPA tích lũy',registered:'Tín chỉ đăng ký',passed:'Tín chỉ đạt',failed:'Tín chỉ không đạt',accumulated:'Tín chỉ tích lũy',conduct:'Điểm rèn luyện',name:'Họ và tên',username:'Tên đăng nhập',password:'Mật khẩu',class_id:'Lớp',advisor_id:'Cố vấn',student_id:'Mã sinh viên',semester_id:'Học kỳ',due_date:'Ngày hẹn',message:'Nội dung',goal:'Mục tiêu',action:'Biện pháp',payload:'Điều kiện đánh giá'};
function displayText(value){const labels={'Bộ quy tắc minh họa phục vụ demo':'Đánh giá học tập chung','Ghi chú giả lập: đã trao đổi mục tiêu và thống nhất buổi theo dõi.':'Đã trao đổi mục tiêu và thống nhất buổi theo dõi.'};return Object.prototype.hasOwnProperty.call(labels,value)?labels[value]:value;}
function displayDate(value){if(!value)return 'Chưa có thời gian cập nhật';const date=new Date(value);return Number.isNaN(date.getTime())?'Chưa có thời gian cập nhật':date.toLocaleString('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});}
function displayDay(value){const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(value||'');return match?`${match[3]}/${match[2]}/${match[1]}`:displayDate(value);}
function feedback(message,error=false){const el=$('#feedback');el.className='notice '+(error?'error':'success');el.textContent=message;el.setAttribute?.('role',error?'alert':'status');el.scrollIntoView({block:'nearest',behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}
function issueMessage(issue){
 const key=issue.loc?.at(-1)||issue.column,label=fieldLabels[key]||key||'Thông tin nhập';
 let message=issue.msg||issue.message||'Vui lòng kiểm tra lại.';
 if(issue.type==='missing')message='Vui lòng nhập thông tin này.';
 else if(issue.type==='greater_than_equal')message='Giá trị tối thiểu là '+issue.ctx.ge+'.';
 else if(issue.type==='less_than_equal')message='Giá trị tối đa là '+issue.ctx.le+'.';
 else if(issue.type==='float_parsing'||issue.type==='int_parsing')message='Vui lòng nhập một số hợp lệ.';
 return (issue.line?'Dòng '+issue.line+' · ':'')+label+': '+message.replace(/^Value error, /,'');
}
async function api(url,options={}){
 const headers={'X-CSRF-Token':csrf,...options.headers};
 if(options.body && !(options.body instanceof FormData)){headers['Content-Type']='application/json';options.body=JSON.stringify(options.body);}
 let r;try{r=await fetch(url,{...options,headers});}catch{throw Error('Chưa kết nối được với hệ thống. Kiểm tra kết nối mạng rồi thử lại.');}
 let result;try{result=await r.json();}catch{throw Error('Chưa đọc được kết quả. Vui lòng tải lại trang và thử lại.');}
 if(!r.ok){if(r.status===401&&window.location?.assign)window.location.assign('/login');const d=result.detail;if(Array.isArray(d))throw Object.assign(Error(d.map(issueMessage).join('\n')),{issues:d});if(r.status===403&&typeof d==='string'&&d.includes('CSRF'))throw Error('Trang đã hết hiệu lực. Vui lòng tải lại trang trước khi lưu.');throw Error(typeof d==='string'?d:'Chưa thực hiện được yêu cầu. Vui lòng thử lại.');}
 return result;
}
function formData(form){return Object.fromEntries(new FormData(form));}
function numbers(o,keys){for(const k of keys)if(k in o)o[k]=o[k]===''?null:Number(o[k]);return o;}
function onForm(id,handler){const form=$(id);if(!form)return;let submitting=false;form.addEventListener('submit',async e=>{
 e.preventDefault();if(submitting)return;submitting=true;$$('.inline-error',form).forEach(x=>x.remove());$$('[aria-invalid]',form).forEach(x=>x.removeAttribute('aria-invalid'));
 const b=$('button[type="submit"],button:not([type])',form),original=b?.innerHTML,loading=form.dataset?.loadingLabel||'Đang xử lý…';
 if(b){b.disabled=true;b.setAttribute?.('aria-busy','true');b.textContent=loading;}
 try{await handler(form);}catch(err){feedback(err.message,true);for(const issue of err.issues||[]){const key=issue.loc?.at(-1)||issue.column;const el=form.elements.namedItem(key);if(el){const msg=document.createElement('span');msg.className='inline-error';msg.textContent=issueMessage(issue);el.after(msg);el.setAttribute('aria-invalid','true');}}}
 finally{submitting=false;if(b){b.disabled=false;b.removeAttribute?.('aria-busy');if(b.textContent===loading)b.innerHTML=original;}}
});}
function badge(level){return `<span class="badge ${['normal','attention','high','missing'][levels.indexOf(level)]||'missing'}">${esc(level)}</span>`;}
function table(headers,rows){return `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.length?rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="${headers.length}" class="empty">Không có dữ liệu phù hợp.</td></tr>`}</tbody></table></div>`;}
function dataIssues(r){
 const issues=r.data_issues||r.missing.map(reason=>({kind:'missing',reason,action:''}));
 return ['missing','history'].map(kind=>{
  const subset=issues.filter(issue=>issue.kind===kind);if(!subset.length)return '';
  return `<details class="data-issues"><summary>${kind==='missing'?'Thông tin cần bổ sung':'Cần thêm thời gian theo dõi'} (${subset.length})</summary><ul>${subset.map(issue=>`<li>${issue.factor?`<b>${esc(issue.factor)}</b><br>`:''}${esc(issue.reason)}${issue.action?`<p>${esc(issue.action)}</p>`:''}</li>`).join('')}</ul></details>`;
 }).join('');
}
function studentTable(items){if(!items.length)return '<div class="empty"><h3>Chưa tìm thấy sinh viên phù hợp</h3><p>Thử tìm bằng tên hoặc mã sinh viên khác, hoặc xóa bớt bộ lọc.</p></div>';return table(['Sinh viên','Lớp / khóa','GPA học kỳ','Tín chỉ không đạt','Ưu tiên hỗ trợ /100','Điều kiện học vụ','Lý do và hướng xử lý'],items.map(s=>[
 `<a href="/students/${encodeURIComponent(s.id)}"><strong>${esc(s.name)}</strong></a><small>${esc(s.id)}</small>`,`${esc(s.class_name||s.class_id)}<small>${esc(s.cohort_id)}</small>`,
 s.academic?.gpa==null?'—':Number(s.academic.gpa).toFixed(2),s.academic?.failed==null?'—':`${s.academic.failed}/${s.academic.registered}`,
 `<span class="score">${s.assessment.score==null?'—':s.assessment.score.toFixed(1)}</span> ${badge(s.assessment.level)}`,esc(s.assessment.rule_label),
 `<div class="student-reason"><p>${esc(s.assessment.summary||(s.assessment.missing.length?s.assessment.missing[0]:s.assessment.factors.find(f=>f.contribution>0)?.reason||'Chưa ghi nhận yếu tố cần ưu tiên hỗ trợ.'))}</p>${dataIssues(s.assessment)}</div>`]));}
function filterParams(){return new URLSearchParams($('#filters')?new FormData($('#filters')):undefined);}
function chart(id,type,data,options={}){const el=$('#'+id);if(!el)return;if(charts[id])charts[id].destroy();if(!window.Chart){el.closest('.chart-wrap').innerHTML='<p class="notice">Biểu đồ chưa tải được. Bạn vẫn có thể xem số liệu trong bảng bên dưới.</p>';return;}charts[id]=new Chart(el,{type,data,options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{family:'Segoe UI',size:12}}},tooltip:{enabled:true}},...options}});}
async function loadOverview(){const params=filterParams();const [s,t]=await Promise.all([api('/api/summary?'+params),api('/api/trend?'+params)]);
 $('#report-context').textContent='Báo cáo tại '+new Date().toLocaleString('vi-VN')+' · '+[...$('#filters').querySelectorAll('select')].filter(x=>x.value).map(x=>x.selectedOptions[0].textContent).join(' · ');
 $('#metrics').innerHTML=[['Sinh viên',s.total,'Trong phạm vi và bộ lọc đang chọn'],['Đã có đánh giá',s.assessed,`${s.total-s.assessed} hồ sơ chưa đủ dữ liệu`],['Cần ưu tiên hỗ trợ',s.levels['Nguy cơ cao'],`Trong ${s.assessed} hồ sơ đã có đánh giá`],['Đang theo dõi',s.open,`${s.overdue} lịch hẹn quá hạn`]].map(([label,n,note])=>`<div class="metric"><span>${label}</span><b>${n}</b><small>${note}</small></div>`).join('');
 chart('distribution','doughnut',{labels:levels,datasets:[{data:levels.map(l=>s.levels[l]),backgroundColor:colors,borderWidth:0}]},{cutout:'72%'});
 $('#distribution-table').innerHTML=table(['Mức nguy cơ','Sinh viên','Tỷ lệ trên tập bộ lọc'],levels.map(l=>[badge(l),s.levels[l],s.total?(100*s.levels[l]/s.total).toFixed(1)+'%':'—']));
 chart('trend','line',{labels:t.map(x=>x.name),datasets:levels.map((l,i)=>({label:l,data:t.map(x=>x[l]),borderColor:colors[i],backgroundColor:colors[i],tension:.25,spanGaps:false}))},{scales:{y:{beginAtZero:true,title:{display:true,text:'Sinh viên'},ticks:{precision:0}}}});
 $('#trend-table').innerHTML=table(['Học kỳ',...levels],t.map(x=>[esc(x.name),...levels.map(l=>x[l])]));
 $('#denominator').textContent=`${s.total} sinh viên · ${s.assessed} đủ dữ liệu`;$('#list').innerHTML=studentTable(s.priority);
 if($('#plan-summary')){
  const groups=await api('/api/report-groups?'+params);
  $('#plan-summary').innerHTML=table(['Trạng thái','Số hồ sơ'],Object.entries(s.interventions).map(([k,v])=>[esc(k),v]))+Object.entries(groups).map(([key,g])=>'<h3>'+({class_id:'Theo lớp',major_id:'Theo ngành',cohort_id:'Theo khóa'}[key])+'</h3>'+table(['Nhóm','Tổng',...levels],Object.entries(g).map(([name,x])=>[esc(name),x.total,...levels.map(l=>x[l])]))).join('');
 }
}
async function loadStudents(){
 const params=filterParams();params.set('page',currentPage);
 $('#list').innerHTML='<p class="loading" role="status">Đang tải danh sách sinh viên…</p>';
 try{
  const result=await api('/api/students?'+params);$('#list').innerHTML=studentTable(result.items);
  $('#pagination').innerHTML=`<span>${result.total} sinh viên · trang ${result.page}/${result.pages}</span><div><button id="previous" ${result.page<=1?'disabled':''}>Trước</button><button id="next" ${result.page>=result.pages?'disabled':''}>Tiếp</button></div>`;
  $('#previous').onclick=()=>{currentPage=Math.max(1,result.page-1);safe(loadStudents);};
  $('#next').onclick=()=>{currentPage=Math.min(result.pages,result.page+1);safe(loadStudents);};
 }catch(error){$('#list').innerHTML='<p class="notice error">Chưa tải được danh sách. Kiểm tra kết nối rồi bấm “Áp dụng bộ lọc” để thử lại.</p>';$('#pagination').innerHTML='';throw error;}
}
function ruleTree(r){if(!r)return '<p>Chưa có cấu hình áp dụng</p>';if(r.children)return `<p><b>${r.op==='OR'?'Thỏa ít nhất một điều kiện':'Thỏa tất cả điều kiện'}</b> · ${stateLabel(r.state)}</p><ul class="rule-list">${r.children.map(x=>`<li>${ruleTree(x)}</li>`).join('')}</ul>`;return `<span class="badge">${stateLabel(r.state)}</span> ${esc(r.reason)}`;}
function stateLabel(s){return {true:'Thỏa',false:'Không thỏa',unknown:'Không đủ dữ liệu'}[s]||s;}
function explanation(r){return `<div class="explain-grid"><section class="panel"><h2>Điều kiện học vụ</h2><p><b>${esc(r.rule_label)}</b></p><p class="muted">Đối chiếu với bộ điều kiện đang áp dụng.</p>${ruleTree(r.rule)}</section><section class="panel"><h2>Ưu tiên hỗ trợ học tập</h2><div class="score-large">${r.score==null?'—':r.score.toFixed(2)} <small>/100</small></div>${badge(r.level)}<p class="muted">Điểm cao hơn thể hiện nhiều yếu tố cần chú ý hơn.</p>${r.summary?`<p>${esc(r.summary)}</p>`:''}${r.factors.map(f=>`<div class="factor"><strong>${esc(f.name)}</strong><span>${f.contribution==null?'Chưa đánh giá':f.contribution.toFixed(2)+' / '+f.weight}</span><p>${esc(f.reason)}</p></div>`).join('')}${dataIssues(r)}</section></div><details class="assessment-meta"><summary>Thông tin lần đánh giá</summary><dl><dt>Bộ đánh giá</dt><dd>${esc(displayText(r.config_name)||'Chưa có bộ đánh giá')}</dd><dt>Thời gian cập nhật</dt><dd>${esc(displayDate(r.evaluated_at))}</dd><dt>Trạng thái lưu</dt><dd>${r.persisted?'Đã lưu kết quả, mã '+esc(r.evaluation_id):'Chưa lưu kết quả này'}</dd></dl></details>`;}
function renderPlans(plans){
 if(!plans.length)return '<p class="empty">Chưa có hồ sơ can thiệp.</p>';
 return plans.map(p=>`<article class="plan"><div class="plan-header"><div><a href="/students/${encodeURIComponent(p.student_id)}"><b>${esc(p.student_name)}</b></a><small> · ${esc(p.student_id)} · Hồ sơ #${p.id}</small><p>${esc(p.goal)}</p></div><span class="badge ${p.overdue?'high':'normal'}">${esc(p.overdue?'Lịch hẹn quá hạn':p.status)}</span></div>
 <p><b>Biện pháp:</b> ${esc(p.action)}</p>
 <p class="muted">GPA kỳ gắn hồ sơ: ${esc(p.comparison?.before?.gpa??'Chưa có')} (${esc(p.comparison?.before?.semester??'—')}); kỳ chính hoàn thành tiếp theo: ${esc(p.comparison?.after?.gpa??'Chưa có')} (${esc(p.comparison?.after?.semester??'—')}). Thay đổi GPA cần được xem cùng tình hình học tập của sinh viên.</p>
 <time>Hẹn ${esc(displayDay(p.due_date))} · ${esc(p.owner)} · Đánh giá #${p.evaluation_id}</time>
 <form class="plan-update form-grid" data-plan="${p.id}"><label>Trạng thái<select name="status">${statuses.map(s=>`<option ${s===p.status?'selected':''}>${s}</option>`).join('')}</select></label><label>Ghi chú theo dõi<textarea name="note" rows="2" maxlength="3000" placeholder="Nội dung trao đổi, kết quả, việc cần theo dõi"></textarea></label><label>Mục tiêu<input name="goal" value="${esc(p.goal)}" required minlength="3"></label><label>Biện pháp<input name="action" value="${esc(p.action)}" required minlength="3"></label><label>Ngày hẹn<input name="due_date" type="date" value="${esc(p.due_date)}" required></label><button class="primary">Lưu cập nhật</button></form><div class="notes">${p.notes.length?p.notes.map(n=>`<p><small>${esc(displayDate(n.created_at))}</small><br>${esc(displayText(n.note))}</p>`).join(''):'<small>Chưa có ghi chú theo dõi.</small>'}</div></article>`).join('');
}
function bindPlanForms(){ $$('.plan-update').forEach(f=>f.addEventListener('submit',async e=>{e.preventDefault();const b=$('button',f);b.disabled=true;try{await api('/api/interventions/'+f.dataset.plan,{method:'PATCH',body:formData(f)});feedback('Đã lưu trạng thái và ghi chú theo dõi.');if(page==='detail')await loadDetail();else await loadPlans();}catch(err){feedback(err.message,true);}finally{b.disabled=false;}}));}
async function loadDetail(){const sem=$('#detail-semester').value;detailData=await api(`/api/students/${encodeURIComponent(sid)}?semester_id=${sem}`);const d=detailData,s=d.student,r=d.assessment;
 $('#profile').innerHTML=`<div class="profile-strip"><div><h2>${esc(s.name)}</h2><small>${esc(s.id)} · ${esc(s.class_id)}</small></div><div><small>Điểm xét tuyển (${esc(s.admission_method||'Chưa cung cấp')})</small>${s.admission_score==null?'Chưa có':esc(s.admission_score)+' / '+esc(s.admission_scale)}</div><div><small>Ưu tiên hỗ trợ</small>${badge(r.level)}</div><div><small>Kiểm tra quy tắc</small>${esc(r.rule_label)}</div></div>`;
 chart('gpa-chart','line',{labels:d.chart.map(x=>x.name),datasets:[{label:'GPA /4',data:d.chart.map(x=>x.gpa),borderColor:'#087f78',backgroundColor:'#087f78',spanGaps:false,yAxisID:'y'},{label:'Số mốc can thiệp',type:'bar',data:d.chart.map(x=>x.interventions),backgroundColor:'#bdd8d1',yAxisID:'markers'}]},{scales:{y:{min:0,max:4,title:{display:true,text:'GPA /4'}},markers:{position:'right',beginAtZero:true,ticks:{precision:0},grid:{drawOnChartArea:false},title:{display:true,text:'Mốc can thiệp'}}}});
 chart('risk-chart','line',{labels:d.chart.map(x=>x.name),datasets:[{label:'Tín chỉ không đạt (%)',data:d.chart.map(x=>x.failed_ratio),borderColor:'#d3972e',spanGaps:false},{label:'Điểm hỗ trợ /100',data:d.chart.map(x=>x.score),borderColor:'#cd5369',spanGaps:false}]},{scales:{y:{min:0,max:100,title:{display:true,text:'% / điểm'}}}});
 $('#chart-data').innerHTML='<h2>Dữ liệu biểu đồ theo học kỳ</h2><p class="muted">Ô “—” là thiếu dữ liệu; đường biểu đồ không nối qua khoảng trống. Điểm tính theo cấu hình hiện hành; phiên đánh giá đã lưu xem trong tab Giải thích. Mốc can thiệp gắn với kỳ của đánh giá tạo hồ sơ.</p>'+table(['Học kỳ','GPA /4','Không đạt %','Nguy cơ /100','Mốc can thiệp'],d.chart.map(x=>[esc(x.name),x.gpa??'—',x.failed_ratio==null?'—':x.failed_ratio.toFixed(1),x.score??'—',x.interventions]));
 const currentSeq=d.semesters.find(x=>x.id===Number(sem)).sequence;
 const rows=d.results.filter(x=>x.sequence<=currentSeq).sort((a,b)=>a.sequence-b.sequence);
 $('#academic-data').innerHTML='<h2>Kết quả học tập</h2>'+table(['Học kỳ','GPA','GPA tích lũy','Đăng ký','Đạt','Không đạt','Tích lũy','Rèn luyện','Trạng thái'],rows.map(x=>[esc(d.semesters.find(s=>s.id===x.semester_id)?.name),x.gpa??'—',x.cumulative_gpa??'—',x.registered,x.passed,x.failed,x.accumulated??'—',x.conduct??'—',esc(x.status)]));
 $('#debt-data').innerHTML='<h2>Học phần còn nợ tại kỳ đang xét</h2>'+table(['Mã học phần','Tên học phần','Tín chỉ'],d.debts.map(c=>[esc(c.course_id),esc(c.name),c.credits]));
 $('#warning-data').innerHTML='<h2>Lịch sử quyết định học vụ</h2><p class="muted">Các quyết định đã được ghi nhận theo từng học kỳ. Lịch sử này được đối chiếu riêng với điều kiện đánh giá hiện tại.</p>'+table(['Học kỳ','Quyết định đã ghi nhận'],d.semesters.filter(p=>p.kind==='regular'&&p.sequence<=currentSeq).map(p=>{
  const warning=d.warnings.find(w=>w.sequence===p.sequence);
  return [esc(p.name),warning?(warning.warned?'Đã có cảnh báo':'Đã xác nhận không cảnh báo'):'Chưa được cung cấp'];
 }));
 $('#explanation').innerHTML=explanation(r);
 $('#evaluation-history').innerHTML=d.history.length?d.history.map(e=>`<details><summary>Đánh giá #${e.id} · ${esc(displayDate(e.created_at))}</summary><p>${esc(displayText(e.output.config_name)||'')} · ${esc(e.output.rule_label)}</p>${table(['Yếu tố','Điểm đóng góp','Lý do'],(e.output.factors||[]).map(f=>[esc(f.name),f.contribution??'Chưa đánh giá',esc(f.reason)]))}</details>`).join(''):'<p>Chưa có phiên đánh giá đã lưu.</p>';
 $('#suggestion').value=d.suggestion;$('#student-plans').innerHTML=renderPlans(d.interventions);bindPlanForms();
}
async function loadPlans(){const plans=await api('/api/interventions');$('#plans').innerHTML=board?`<div class="board">${statuses.map(s=>`<section class="board-col"><h2>${esc(s)} · ${plans.filter(p=>p.status===s).length}</h2>${renderPlans(plans.filter(p=>p.status===s))}</section>`).join('')}</div>`:renderPlans(plans);bindPlanForms();}
async function safe(fn){try{await fn();}catch(e){feedback(e.message,true);}}
function bindTabs(){const tabs=$$('[role="tab"]');for(const b of tabs){
 b.tabIndex=b.getAttribute('aria-selected')==='true'?0:-1;
 b.id='tab-'+b.dataset.tab;b.setAttribute('aria-controls',b.dataset.tab);
 const panel=$('#'+b.dataset.tab);panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',b.id);
 b.onclick=()=>{tabs.forEach(x=>{const active=x===b;x.setAttribute('aria-selected',String(active));x.tabIndex=active?0:-1;$('#'+x.dataset.tab).hidden=!active;});Object.values(charts).forEach(c=>c.resize());};b.onkeydown=e=>{let i=tabs.indexOf(b);if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();i=(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[i].click();tabs[i].focus();}if(e.key==='Home'){tabs[0].click();tabs[0].focus();}if(e.key==='End'){tabs.at(-1).click();tabs.at(-1).focus();}};
}}
async function init(){bindTabs();
 if($('#filters')){$('#filters').onsubmit=e=>{e.preventDefault();currentPage=1;const p=filterParams();history.replaceState(null,'','?'+p);$('#export').href='/api/export?'+p;safe(page==='students'?loadStudents:loadOverview);};const p=new URLSearchParams(location.search);for(const [k,v] of p){const el=$('#filters').elements.namedItem(k);if(el)el.value=v;}$('#export').href='/api/export?'+filterParams();}
 if(page==='dashboard'||page==='reports')await loadOverview();if(page==='students')await loadStudents();if(page==='detail'){await loadDetail();$('#detail-semester').onchange=()=>safe(loadDetail);$('#evaluate').onclick=()=>safe(async()=>{const r=await api(`/api/students/${encodeURIComponent(sid)}/evaluate?semester_id=${$('#detail-semester').value}`,{method:'POST'});feedback(`Đã lưu đánh giá #${r.evaluation_id}, cấu hình #${r.config_id??'—'}.`);await loadDetail();});}
 if(page==='interventions'){await loadPlans();$('#board-toggle').onclick=()=>{board=!board;safe(loadPlans);};}
 onForm('#simulation-form',async f=>{
  const body=numbers(formData(f),['gpa','registered','failed','previous_gpa_credits']);
  body.no_repeats=f.elements.no_repeats.checked;body.all_registered_count=f.elements.all_registered_count.checked;
  const r=await api(`/api/students/${encodeURIComponent(sid)}/simulate?semester_id=${$('#detail-semester').value}`,{method:'POST',body});
  $('#simulation-output').innerHTML=`<section class="panel"><h2>So sánh kịch bản</h2><p>${esc(r.notice)}</p>${table(['Chỉ số','Trước','Kỳ giả định'],[['Điểm tổng',r.before.score??'Chưa đủ dữ liệu',r.after.score??'Chưa đủ dữ liệu'],...r.after.factors.map((x,i)=>[esc(x.name),r.before.factors[i]?.contribution??'—',x.contribution??'—'])])}<h3>GPA tích lũy giả định: ${r.cumulative_gpa??'Chưa đủ điều kiện tính'}</h3><p>${esc(r.cumulative_note)}</p></section>`+explanation(r.after);
 });
 const sim=$('#simulation-form');if(sim)sim.onreset=()=>{$('#simulation-output').innerHTML='';};
 onForm('#plan-form',async f=>{const evaluated=await api(`/api/students/${encodeURIComponent(sid)}/evaluate?semester_id=${$('#detail-semester').value}`,{method:'POST'});await api('/api/interventions',{method:'POST',body:{...formData(f),student_id:sid,evaluation_id:evaluated.evaluation_id}});feedback('Đã tạo hồ sơ, gắn với phiên đánh giá #'+evaluated.evaluation_id);f.reset();await loadDetail();});
 onForm('#result-form',async f=>{const body=numbers(formData(f),['semester_id','gpa','cumulative_gpa','registered','passed','failed','accumulated','conduct']);await api('/api/results',{method:'PUT',body});feedback('Đã lưu kết quả học kỳ.');await loadDetail();});
 onForm('#import-form',async f=>{
  const file=f.elements.file.files[0];if(file.size>2097152)throw Error('Tệp vượt 2 MB.');
  const r=await api('/api/import/preview',{method:'POST',body:new FormData(f)});importId=r.id;
  $('#import-preview').innerHTML=`<p><b>${r.count} dòng được kiểm tra · ${r.errors.length} lỗi cần sửa.</b></p><div class="import-summary"><span><strong>${r.new}</strong>Thêm mới</span><span><strong>${r.updated}</strong>Cập nhật</span><span><strong>${r.skipped}</strong>Giữ nguyên</span></div><p>${esc(r.notice)}</p><p class="muted">Xem trước ${r.preview_count}/${r.count} dòng đầu. Chưa ghi dữ liệu vào hệ thống.</p>${r.rows.length?table(Object.keys(r.rows[0]),r.rows.map(x=>Object.values(x).map(esc))):''}${r.errors.length?table(['Dòng','Cột','Lỗi và cách sửa'],r.errors.map(e=>[e.line,esc(e.column),esc(e.message)])):''}<div class="actions"><a class="button" href="/api/import/${encodeURIComponent(r.id)}/errors">Tải danh sách lỗi</a><button id="confirm-import" class="primary" ${r.errors.length?'disabled':''}>Xác nhận ${r.save_count} bản ghi cần lưu</button></div>`;
  $('#confirm-import').onclick=()=>safe(async()=>{
   const button=$('#confirm-import');button.disabled=true;
   try{const result=await api('/api/import/'+encodeURIComponent(importId)+'/confirm',{method:'POST'});feedback(`Đã lưu ${result.saved} bản ghi.`);$('#import-preview').innerHTML='<p class="notice success">Đã hoàn tất nhập CSV. Bạn có thể tra cứu dữ liệu trong danh sách sinh viên.</p><a class="button" href="/students">Xem danh sách sinh viên</a>';}catch(error){button.disabled=false;throw error;}
  });
 });
 onForm('#student-form',async f=>{const data=numbers(formData(f),['advisor_id','admission_score','admission_scale']);data.admission_method||=null;try{await api('/api/students',{method:'POST',body:data});}catch(e){if(e.message!=='Mã sinh viên đã tồn tại')throw e;if(!confirm(`Cập nhật hồ sơ ${data.id}: ${data.name}, lớp ${data.class_id}, cố vấn #${data.advisor_id}?`))return;await api('/api/students/'+encodeURIComponent(data.id),{method:'PUT',body:data});}feedback('Đã lưu hồ sơ sinh viên và cố vấn phụ trách.');});
 if($('#lookup-student'))$('#lookup-student').onclick=()=>safe(async()=>{
  const form=$('#student-form'),id=form.elements.id.value.trim();
  if(!id)throw Error('Nhập mã sinh viên cần tải trước.');
  const response=await api('/api/students/'+encodeURIComponent(id));
  for(const [key,value] of Object.entries(response.student)){
   const input=form.elements.namedItem(key);if(input)input.value=value??'';
  }
  feedback('Đã tải hồ sơ '+id+'. Sửa các trường và bấm Lưu để cập nhật.');
 });
 onForm('#account-form',async f=>{await api('/api/accounts',{method:'POST',body:formData(f)});f.reset();feedback('Đã tạo tài khoản cố vấn. Tải lại trang để xem danh sách mới.');});
 $$('[data-toggle-user]').forEach(b=>b.onclick=()=>safe(async()=>{await api('/api/accounts/'+b.dataset.toggleUser,{method:'PATCH',body:{active:b.dataset.active==='true'}});location.reload();}));
 onForm('#catalog-form',async f=>{const data=numbers(formData(f),['credits','sequence']);const kind=data.catalog_kind;delete data.catalog_kind;data.major_id||=null;data.cohort_id||=null;await api('/api/catalog/'+kind,{method:'POST',body:data});feedback('Đã lưu danh mục. Tải lại trang để xem các lựa chọn mới.');});
 if($('#print'))$('#print').onclick=()=>window.print();
}
safe(init);
