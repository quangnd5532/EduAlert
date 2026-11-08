'use strict';
(function(){
 if(document.body.dataset.page!=='student')return;
 const model=JSON.parse(document.querySelector('#student-model').textContent);
 const view=document.body.dataset.view;
 const fmt=value=>value==null?'—':Number(value).toFixed(2);
 if(view==='overview'){
  chart('my-gpa','line',{labels:model.chart.map(p=>p.name),datasets:[{label:'GPA học kỳ /4',data:model.chart.map(p=>p.gpa),borderColor:'#215f9a',backgroundColor:'#215f9a',pointRadius:4,borderWidth:2,tension:0,spanGaps:false}]},{scales:{y:{min:0,max:4,title:{display:true,text:'GPA /4'}}}});
 }
 if(view==='planning'){
  onForm('#my-simulation',async form=>{
   const data=numbers(formData(form),['gpa','registered','failed','previous_gpa_credits']);
   delete data.csrf;
   data.no_repeats=form.elements.no_repeats.checked;
   data.all_registered_count=form.elements.all_registered_count.checked;
   const result=await api('/api/me/simulate?semester_id='+model.semester_id,{method:'POST',body:data});
   $('#my-simulation-result').innerHTML=`<section class="panel"><div class="panel-heading"><h2>Đối chiếu kịch bản</h2></div><p>${esc(result.notice)}</p><div class="simulation-comparison"><div>Điểm hỗ trợ hiện tại<strong>${fmt(result.before.score)}</strong>${badge(result.before.level)}</div><div>Điểm hỗ trợ kỳ giả định<strong>${fmt(result.after.score)}</strong>${badge(result.after.level)}</div></div>${table(['Yếu tố','Đóng góp hiện tại','Đóng góp giả định'],result.after.factors.map((f,i)=>[esc(f.name),fmt(result.before.factors[i]?.contribution),fmt(f.contribution)]))}<p>GPA tích lũy giả định: <b>${fmt(result.cumulative_gpa)}</b></p><p class="muted">${esc(result.cumulative_note)}</p></section>`+explanation(result.after);
   $('#my-simulation-result').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  });
  $('#my-simulation').addEventListener('reset',()=>{$('#my-simulation-result').innerHTML='';});
 }
 if(view==='appointments'){
  onForm('#my-appointment-form',async form=>{
   const data=formData(form);delete data.csrf;
   const response=await api('/api/me/appointments',{method:'POST',body:data});
   // One redirect after a successful write; the next page is rendered from the database.
   const url=new URL(window.location.href);url.hash='';url.searchParams.set('sent',String(response.id));
   window.location.assign(url.pathname+url.search);
  });
  const sent=new URLSearchParams(window.location.search).get('sent');
  if(sent&&/^\d+$/.test(sent)&&model.appointments.some(p=>String(p.id)===sent)){
   feedback('Đã gửi đề nghị tư vấn #'+sent+'. Vui lòng chờ cố vấn xác nhận.');
   const url=new URL(window.location.href);url.searchParams.delete('sent');window.history.replaceState(null,'',url.pathname+url.search);
  }
 }
})();
