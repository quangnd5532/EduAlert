'use strict';
const $=(s,root=document)=>root.querySelector(s), $$=(s,root=document)=>[...root.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const page=document.body.dataset.page, sid=document.body.dataset.student;
const catalogs=JSON.parse($('#catalog-data').textContent), charts={}, csrf=$('meta[name="csrf-token"]').content;
let detailData=null, currentPage=1, board=false, importId=null;
const statuses=['Chưa xử lý','Đang hỗ trợ','Chờ theo dõi','Hoàn tất'];
const levels=['Bình thường','Cần chú ý','Nguy cơ cao','Chưa đủ dữ liệu'];
const colors=['#36856b','#b47b1e','#c54f65','#8d9bb2'];
function feedback(message,error=false){const el=$('#feedback');el.className='notice '+(error?'error':'success');el.textContent=message;el.scrollIntoView({block:'nearest',behavior:'smooth'});}
async function api(url,options={}){
 const headers={'X-CSRF-Token':csrf,...options.headers};
 if(options.body && !(options.body instanceof FormData)){headers['Content-Type']='application/json';options.body=JSON.stringify(options.body);}
 const r=await fetch(url,{...options,headers}); let result;try{result=await r.json();}catch{throw Error('Máy chủ trả về dữ liệu không hợp lệ.');}
 if(!r.ok){if(r.status===401&&window.location)window.location.assign('/login');const d=result.detail;if(Array.isArray(d))throw Object.assign(Error(d.map(x=>(x.loc?.join('.')||x.column||'Dòng '+x.line)+': '+(x.msg||x.message)).join('\n')),{issues:d});throw Error(typeof d==='string'?d:JSON.stringify(d));}
 return result;
}
function formData(form){return Object.fromEntries(new FormData(form));}
function numbers(o,keys){for(const k of keys)if(k in o)o[k]=o[k]===''?null:Number(o[k]);return o;}
function onForm(id,handler){const form=$(id);if(!form)return;form.addEventListener('submit',async e=>{e.preventDefault();$$('.inline-error',form).forEach(x=>x.remove());const b=$('button[type="submit"],button:not([type])',form);if(b)b.disabled=true;try{await handler(form);}catch(err){feedback(err.message,true);for(const issue of err.issues||[]){const key=issue.loc?.at(-1)||issue.column;const el=form.elements.namedItem(key);if(el){const msg=document.createElement('span');msg.className='inline-error';msg.textContent=issue.msg||issue.message;el.after(msg);el.setAttribute('aria-invalid','true');}}}finally{if(b)b.disabled=false;}});}
function badge(level){return `<span class="badge ${['normal','attention','high','missing'][levels.indexOf(level)]||'missing'}">${esc(level)}</span>`;}
function table(headers,rows){return `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.length?rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="${headers.length}" class="empty">Không có dữ liệu phù hợp.</td></tr>`}</tbody></table></div>`;}
function dataIssues(r){
 const issues=r.data_issues||r.missing.map(reason=>({kind:'missing',reason,action:''}));
 return ['missing','history'].map(kind=>{
  const subset=issues.filter(issue=>issue.kind===kind);if(!subset.length)return '';
  return `<details class="data-issues"><summary>${kind==='missing'?'Thông tin cần bổ sung':'Cần thêm thời gian theo dõi'} (${subset.length})</summary><ul>${subset.map(issue=>`<li>${issue.factor?`<b>${esc(issue.factor)}</b><br>`:''}${esc(issue.reason)}${issue.action?`<p>${esc(issue.action)}</p>`:''}</li>`).join('')}</ul></details>`;
 }).join('');
}
function studentTable(items){return table(['Sinh viên','Lớp / khóa','GPA học kỳ','Tín chỉ không đạt','Ưu tiên hỗ trợ /100','Điều kiện học vụ','Lý do và hướng xử lý'],items.map(s=>[
 `<a href="/students/${encodeURIComponent(s.id)}"><strong>${esc(s.name)}</strong></a><small>${esc(s.id)}</small>`,`${esc(s.class_name||s.class_id)}<small>${esc(s.cohort_id)}</small>`,
 s.academic?.gpa==null?'—':Number(s.academic.gpa).toFixed(2),s.academic?.failed==null?'—':`${s.academic.failed}/${s.academic.registered}`,
 `<span class="score">${s.assessment.score==null?'—':s.assessment.score.toFixed(1)}</span> ${badge(s.assessment.level)}`,esc(s.assessment.rule_label),
 `<div class="student-reason"><p>${esc(s.assessment.summary||(s.assessment.missing.length?s.assessment.missing[0]:s.assessment.factors.find(f=>f.contribution>0)?.reason||'Chưa ghi nhận yếu tố cần ưu tiên hỗ trợ.'))}</p>${dataIssues(s.assessment)}</div>`]));}
function filterParams(){return new URLSearchParams($('#filters')?new FormData($('#filters')):undefined);}
function chart(id,type,data,options={}){const el=$('#'+id);if(!el)return;if(charts[id])charts[id].destroy();if(!window.Chart){el.closest('.chart-wrap').innerHTML='<p class="notice">Chưa cài Chart.js cục bộ. Xem bảng dữ liệu tương ứng bên dưới; chạy scripts/vendor_assets.py khi có mạng.</p>';return;}charts[id]=new Chart(el,{type,data,options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{family:'Segoe UI'}}},tooltip:{enabled:true}},...options}});}
async function loadOverview(){const params=filterParams();const [s,t]=await Promise.all([api('/api/summary?'+params),api('/api/trend?'+params)]);
 $('#report-context').textContent='Báo cáo tại '+new Date().toLocaleString('vi-VN')+' · '+[...$('#filters').querySelectorAll('select')].filter(x=>x.value).map(x=>x.selectedOptions[0].textContent).join(' · ');
 $('#metrics').innerHTML=[['Sinh viên trong bộ lọc',s.total,'Đúng phạm vi được phân công'],['Đủ dữ liệu đánh giá',s.assessed,`${s.total-s.assessed} hồ sơ chưa đủ dữ liệu`],['Cần ưu tiên hỗ trợ',s.levels['Nguy cơ cao'],`Mẫu số: ${s.assessed} sinh viên đủ dữ liệu`],['Hồ sơ cần xử lý',s.open,`${s.overdue} lịch hẹn quá hạn`]].map(([label,n,note])=>`<div class="metric"><span>${label}</span><b>${n}</b><small>${note}</small></div>`).join('');
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
async function loadStudents(){const p=filterParams();p.set('page',currentPage);$('#list').innerHTML='<p class="loading">Đang tải sinh viên…</p>';const r=await api('/api/students?'+p);$('#list').innerHTML=studentTable(r.items);$('#pagination').innerHTML=`<span>${r.total} sinh viên · trang ${r.page}/${r.pages}</span><div><button id="previous" ${r.page<=1?'disabled':''}>Trước</button><button id="next" ${r.page>=r.pages?'disabled':''}>Tiếp</button></div>`;$('#previous').onclick=()=>{currentPage--;safe(loadStudents);};$('#next').onclick=()=>{currentPage++;safe(loadStudents);};}
function ruleTree(r){if(!r)return '<p>Chưa có cấu hình áp dụng</p>';if(r.children)return `<p><b>${r.op==='OR'?'Thỏa ít nhất một điều kiện':'Thỏa tất cả điều kiện'}</b> · ${stateLabel(r.state)}</p><ul class="rule-list">${r.children.map(x=>`<li>${ruleTree(x)}</li>`).join('')}</ul>`;return `<span class="badge">${stateLabel(r.state)}</span> ${esc(r.reason)}`;}
function stateLabel(s){return {true:'Thỏa',false:'Không thỏa',unknown:'Không đủ dữ liệu'}[s]||s;}
function explanation(r){return `<div class="explain-grid"><section class="panel"><h2>A. Kiểm tra cảnh báo học vụ</h2><p><b>${esc(r.rule_label)}</b></p><p class="muted">Đối chiếu kết quả với điều kiện học vụ đang áp dụng.</p>${ruleTree(r.rule)}</section><section class="panel"><h2>B. Điểm cảnh báo sớm</h2><div class="score-large">${r.score==null?'—':r.score.toFixed(2)} <small>/100</small></div>${badge(r.level)}<p class="muted">Chỉ số ưu tiên hỗ trợ, không phải xác suất.</p>${r.summary?`<p>${esc(r.summary)}</p>`:''}${r.factors.map(f=>`<div class="factor"><strong>${esc(f.name)}</strong><span>${f.contribution==null?'Chưa đánh giá':f.contribution.toFixed(2)+' / '+f.weight}</span><p>${esc(f.reason)}</p></div>`).join('')}${dataIssues(r)}</section></div><p class="muted">Cấu hình #${esc(r.config_id??'—')}: ${esc(r.config_name||'')} · Tính lúc ${esc(r.evaluated_at||'—')} · ${r.persisted?'Phiên đã lưu #'+esc(r.evaluation_id):'Kết quả tính trực tiếp, chưa lưu phiên mới.'}</p>`;}
function renderPlans(plans){
 if(!plans.length)return '<p class="empty">Chưa có hồ sơ can thiệp.</p>';
 return plans.map(p=>`<article class="plan"><div class="plan-header"><div><a href="/students/${encodeURIComponent(p.student_id)}"><b>${esc(p.student_name)}</b></a><small> · ${esc(p.student_id)} · Hồ sơ #${p.id}</small><p>${esc(p.goal)}</p></div><span class="badge ${p.overdue?'high':'normal'}">${esc(p.overdue?'Lịch hẹn quá hạn':p.status)}</span></div>
 <p><b>Biện pháp:</b> ${esc(p.action)}</p>
 <p class="muted">GPA kỳ gắn hồ sơ: ${esc(p.comparison?.before?.gpa??'Chưa có')} (${esc(p.comparison?.before?.semester??'—')}); kỳ chính hoàn thành tiếp theo: ${esc(p.comparison?.after?.gpa??'Chưa có')} (${esc(p.comparison?.after?.semester??'—')}). So sánh mô tả, không kết luận quan hệ nhân quả.</p>
 <time>Hẹn ${esc(p.due_date)} · ${esc(p.owner)} · Đánh giá #${p.evaluation_id}</time>
 <form class="plan-update form-grid" data-plan="${p.id}"><label>Trạng thái<select name="status">${statuses.map(s=>`<option ${s===p.status?'selected':''}>${s}</option>`).join('')}</select></label><label>Ghi chú theo dõi<textarea name="note" rows="2" maxlength="3000" placeholder="Nội dung trao đổi, kết quả, việc cần theo dõi"></textarea></label><label>Mục tiêu<input name="goal" value="${esc(p.goal)}" required minlength="3"></label><label>Biện pháp<input name="action" value="${esc(p.action)}" required minlength="3"></label><label>Ngày hẹn<input name="due_date" type="date" value="${esc(p.due_date)}" required></label><button class="primary">Lưu cập nhật</button></form><div class="notes">${p.notes.length?p.notes.map(n=>`<p><small>${esc(n.created_at)}</small><br>${esc(n.note)}</p>`).join(''):'<small>Chưa có ghi chú theo dõi.</small>'}</div></article>`).join('');
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
 $('#warning-data').innerHTML='<h2>Lịch sử quyết định cảnh báo đã cung cấp</h2><p class="muted">Dữ liệu giả lập được nhập riêng; không đồng nhất với kết quả quy tắc đang áp dụng. F_repeat chỉ dùng ba kỳ chính trước kỳ đang xét.</p>'+table(['Học kỳ','Xác nhận lịch sử'],d.semesters.filter(p=>p.kind==='regular'&&p.sequence<=currentSeq).map(p=>{
  const warning=d.warnings.find(w=>w.sequence===p.sequence);
  return [esc(p.name),warning?(warning.warned?'Đã có cảnh báo':'Đã xác nhận không cảnh báo'):'Chưa được cung cấp'];
 }));
 $('#explanation').innerHTML=explanation(r);
 $('#evaluation-history').innerHTML=d.history.length?d.history.map(e=>`<details><summary>Đánh giá #${e.id} · ${esc(e.created_at)}</summary><p>${esc(e.output.config_name||'')} · ${esc(e.output.rule_label)}</p>${table(['Yếu tố','Điểm đóng góp','Lý do'],(e.output.factors||[]).map(f=>[esc(f.name),f.contribution??'Chưa đánh giá',esc(f.reason)]))}</details>`).join(''):'<p>Chưa có phiên đánh giá đã lưu.</p>';
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
 onForm('#student-form',async f=>{const data=numbers(formData(f),['advisor_id','admission_score','admission_scale']);data.admission_method||=null;try{await api('/api/students',{method:'POST',body:data});}catch(e){if(e.message!=='Mã sinh viên đã tồn tại')throw e;if(!confirm(`Cập nhật hồ sơ ${data.id}: ${data.name}, lớp ${data.class_id}, cố vấn #${data.advisor_id}?`))return;await api('/api/students/'+encodeURIComponent(data.id),{method:'PUT',body:data});}feedback('Đã lưu sinh viên và phân công.');});
 if($('#lookup-student'))$('#lookup-student').onclick=()=>safe(async()=>{
  const form=$('#student-form'),id=form.elements.id.value.trim();
  if(!id)throw Error('Nhập mã sinh viên cần tải trước.');
  const response=await api('/api/students/'+encodeURIComponent(id));
  for(const [key,value] of Object.entries(response.student)){
   const input=form.elements.namedItem(key);if(input)input.value=value??'';
  }
  feedback('Đã tải hồ sơ '+id+'. Sửa các trường và bấm Lưu để cập nhật.');
 });
 onForm('#account-form',async f=>{await api('/api/accounts',{method:'POST',body:formData(f)});f.reset();feedback('Đã tạo tài khoản. Tải lại trang để cập nhật danh sách.');});
 $$('[data-toggle-user]').forEach(b=>b.onclick=()=>safe(async()=>{await api('/api/accounts/'+b.dataset.toggleUser,{method:'PATCH',body:{active:b.dataset.active==='true'}});location.reload();}));
 onForm('#catalog-form',async f=>{const data=numbers(formData(f),['credits','sequence']);const kind=data.catalog_kind;delete data.catalog_kind;data.major_id||=null;data.cohort_id||=null;await api('/api/catalog/'+kind,{method:'POST',body:data});feedback('Đã lưu danh mục. Tải lại trang để cập nhật các lựa chọn.');});
 if($('#print'))$('#print').onclick=()=>window.print();
}
safe(init);
