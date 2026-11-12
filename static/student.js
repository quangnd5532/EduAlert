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
  const form=$('#my-simulation'),output=$('#my-simulation-result');
  let revision=0,hasResult=!!output.innerHTML.trim();
  const markChanged=()=>{
   revision++;
   if(hasResult)output.innerHTML='<p class="notice" role="status">Bạn đã thay đổi mục tiêu. Bấm “Xem kết quả mục tiêu” để tính lại với thông tin mới.</p>';
  };
  form.addEventListener('input',markChanged);
  form.addEventListener('change',markChanged);
  onForm('#my-simulation',async form=>{
   const submittedRevision=revision;
   const data=numbers(formData(form),['gpa','registered','failed','previous_gpa_credits']);
   delete data.csrf;
   data.no_repeats=form.elements.no_repeats.checked;
   data.all_registered_count=form.elements.all_registered_count.checked;
   const result=await api('/api/me/simulate?semester_id='+model.semester_id,{method:'POST',body:data});
   if(submittedRevision!==revision){output.innerHTML='<p class="notice" role="status">Bạn vừa thay đổi mục tiêu trong lúc tính. Bấm “Xem kết quả mục tiêu” để tính lại.</p>';hasResult=true;return;}
   if(typeof result.student_html!=='string')throw Error('Chưa tải được phần hướng dẫn. Vui lòng tải lại trang và thử lại.');
   output.innerHTML=result.student_html;
   hasResult=true;
   output.scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
  });
  form.addEventListener('reset',()=>{revision++;hasResult=false;output.innerHTML='';});
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
