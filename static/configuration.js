'use strict';
// Named controls and a condition editor keep policy authoring out of JSON.
let configVersions=[], editingConfig=null, currentRule=null, previewedConfig=null;
const configPresets=JSON.parse(document.querySelector('#config-presets').textContent);
const policyFields={gpa:{label:'GPA học kỳ',max:4,step:.01,value:1.2},cumulative_gpa:{label:'GPA tích lũy',max:4,step:.01,value:1.8},failed_ratio:{label:'Tín chỉ không đạt (%)',max:100,step:.1,value:.5},conduct:{label:'Điểm rèn luyện',max:100,step:1,value:50}};
const policyOps={lt:'Nhỏ hơn',le:'Nhỏ hơn hoặc bằng',gt:'Lớn hơn',ge:'Lớn hơn hoặc bằng',eq:'Bằng'};
const clonePolicy=value=>JSON.parse(JSON.stringify(value));
function policyNode(path){return path.reduce((node,index)=>node.children[index],currentRule);}
function conditionMarkup(node,path=[]){
 const key=path.join('.');
 if(node.children){
  return `<div class="condition-group"><div class="condition-heading"><label>Cách kết hợp<select data-rule-group="${key}"><option value="OR" ${node.op==='OR'?'selected':''}>Thỏa ít nhất một điều kiện</option><option value="AND" ${node.op==='AND'?'selected':''}>Thỏa tất cả điều kiện</option></select></label>${path.length?`<button type="button" data-remove-rule="${key}" ${policyNode(path.slice(0,-1)).children.length===1?'disabled':''}>Bỏ nhóm</button>`:''}</div><div>${node.children.map((child,index)=>conditionMarkup(child,[...path,index])).join('')}</div><div class="actions"><button type="button" data-add-condition="${key}" ${node.children.length>=20?'disabled':''}>Thêm điều kiện</button><button type="button" data-add-group="${key}" ${path.length>=5||node.children.length>=20?'disabled':''}>Thêm nhóm</button></div></div>`;
 }
 const field=policyFields[node.field],value=node.field==='failed_ratio'?Number((node.value*100).toFixed(6)):node.value;
 return `<div class="condition-row"><label>Chỉ tiêu<select data-rule-field="${key}">${Object.entries(policyFields).map(([name,item])=>`<option value="${name}" ${node.field===name?'selected':''}>${item.label}</option>`).join('')}</select></label><label>So sánh<select data-rule-op="${key}">${Object.entries(policyOps).map(([name,label])=>`<option value="${name}" ${node.op===name?'selected':''}>${label}</option>`).join('')}</select></label><label>Ngưỡng<input type="number" data-rule-value="${key}" min="0" max="${field.max}" step="${field.step}" value="${value}" required></label><button type="button" data-remove-rule="${key}" ${path.length===0||policyNode(path.slice(0,-1)).children.length===1?'disabled':''} aria-label="Bỏ điều kiện ${esc(field.label)}">Bỏ</button></div>`;
}
function renderConditions(){ $('#rule-editor').innerHTML=conditionMarkup(currentRule); }
function decodePath(value){return value===''?[]:value.split('.').map(Number);}
function updateWeightTotal(){
 const sum=[0,1,2,3].reduce((total,index)=>total+Number($('#config-form').elements['weight_'+index].value),0);
 const node=$('#weight-total');node.textContent=`Tổng trọng số: ${Number(sum.toFixed(4))}/100`;
 node.className=Math.abs(sum-100)<.000001?'weight-valid':'weight-invalid';
}
function readConfiguration(form){
 return {name:form.elements.name.value.trim(),major_id:form.elements.major_id.value||null,cohort_id:form.elements.cohort_id.value||null,
  payload:{weights:[0,1,2,3].map(index=>Number(form.elements['weight_'+index].value)),
   ...Object.fromEntries(['attention','high','gpa_target','gpa_span','trend_span','repeat_span'].map(name=>[name,Number(form.elements[name].value)])),
   fail_span:Number(form.elements.fail_percent.value)/100,rule:clonePolicy(currentRule)}};
}
function policyValidation(payload){
 if(payload.weights.some(value=>!Number.isFinite(value)||value<0)||Math.abs(payload.weights.reduce((a,b)=>a+b,0)-100)>.000001)return 'Tổng bốn trọng số phải bằng 100.';
 if(!(0<payload.attention&&payload.attention<payload.high&&payload.high<=100))return 'Ngưỡng cần chú ý phải nhỏ hơn ngưỡng nguy cơ cao, trong khoảng 0–100.';
 if(!(payload.gpa_span>0&&payload.trend_span>0&&payload.fail_span>0&&payload.repeat_span>0))return 'Các mốc tính điểm phải lớn hơn 0.';
 return '';
}
function fillConfiguration(version=null,copy=false){
 const form=$('#config-form');form.reset();
 const source=version||configPresets.find(p=>p.id===$('#config-preset').value)||configPresets[0];
 const payload=source.payload;
 editingConfig=version&&!copy?version.id:null;
 form.elements.name.value=version?(copy?version.name.slice(0,105)+' — Bản sao':version.name):'';
 form.elements.major_id.value=version?.major_id||'';form.elements.cohort_id.value=version?.cohort_id||'';
 payload.weights.forEach((value,index)=>{form.elements['weight_'+index].value=value;});
 for(const name of ['attention','high','gpa_target','gpa_span','trend_span','repeat_span'])form.elements[name].value=payload[name];
 form.elements.fail_percent.value=Number((payload.fail_span*100).toFixed(6));
 currentRule=clonePolicy(payload.rule);
 if(!currentRule.children)currentRule={op:'OR',children:[currentRule]};
 renderConditions();updateWeightTotal();
 $('#config-editor-title').textContent=editingConfig?'Chỉnh sửa bản nháp':'Tạo phiên bản đánh giá';
 $('#config-editor-status').textContent=editingConfig?version.name:'Bản nháp mới';
 $('#save-config').textContent=editingConfig?'Lưu thay đổi bản nháp':'Lưu bản nháp mới';
 $('#config-form-error').hidden=true;
 previewedConfig=null;$('#config-preview').innerHTML='<p class="empty">Lưu bản nháp rồi xem trước ảnh hưởng trước khi áp dụng.</p>';
}
function readablePolicy(node){
 if(node.children)return '('+node.children.map(readablePolicy).join(node.op==='AND'?' và ':' hoặc ')+')';
 const value=node.field==='failed_ratio'?Number((node.value*100).toFixed(4))+'%':node.value;
 return `${policyFields[node.field].label} ${policyOps[node.op].toLowerCase()} ${value}`;
}
function scopeName(version){
 const major=catalogs.majors.find(item=>item.id===version.major_id)?.name||'Tất cả ngành';
 const cohort=catalogs.cohorts.find(item=>item.id===version.cohort_id)?.name||'Tất cả khóa';
 return major+' · '+cohort;
}
async function loadConfigurationVersions(){
 configVersions=await api('/api/configs');
 $('#config-list').innerHTML=configVersions.length?table(['Phiên bản và nội dung','Phạm vi áp dụng','Trạng thái','Thao tác'],configVersions.map(version=>[
  `<strong>${esc(version.name)}</strong><details><summary>Xem các thông số</summary><dl class="policy-summary"><dt>Trọng số GPA / không đạt / xu hướng / cảnh báo</dt><dd>${version.payload.weights.map(esc).join(' / ')}%</dd><dt>Ngưỡng cần chú ý / nguy cơ cao</dt><dd>${esc(version.payload.attention)} / ${esc(version.payload.high)} điểm</dd><dt>Mốc GPA / khoảng giảm tối đa</dt><dd>${esc(version.payload.gpa_target)} / ${esc(version.payload.gpa_span)} điểm</dd><dt>Tín chỉ không đạt / xu hướng / số lần cảnh báo đạt điểm tối đa</dt><dd>${Number((version.payload.fail_span*100).toFixed(4))}% / ${esc(version.payload.trend_span)} điểm / ${esc(version.payload.repeat_span)} lần</dd><dt>Điều kiện học vụ</dt><dd>${esc(readablePolicy(version.payload.rule))}</dd></dl></details>`,esc(scopeName(version)),
  `<span class="badge ${version.active?'normal':'missing'}">${version.active?'Đang áp dụng':version.activated_at?'Đã ngừng áp dụng':'Bản nháp'}</span>`,
  `<div class="config-row-actions"><button type="button" data-preview-config="${version.id}">Xem trước</button><button type="button" data-copy-config="${version.id}">Sao chép</button>${!version.active&&!version.activated_at?`<button type="button" data-edit-config="${version.id}">Chỉnh sửa</button>`:''}</div>`])):'<p class="empty">Chưa có phiên bản đánh giá. Tạo bản nháp từ mẫu ở trên để bắt đầu.</p>';
}
async function showConfigPreview(id){
 const version=configVersions.find(item=>item.id===id);if(!version)return;
 $('#config-preview').innerHTML='<p class="loading">Đang đối chiếu kết quả đánh giá…</p>';
 const semester=$('#config-preview-semester').value;
 const result=await api(`/api/configs/${id}/preview?semester_id=${encodeURIComponent(semester)}`,{method:'POST'});
 previewedConfig=id;
 const score=value=>value==null?'Chưa đủ dữ liệu':Number(value).toFixed(2);
 $('#config-preview').innerHTML=`<h3>${esc(version.name)}</h3><p>${esc(scopeName(version))} · ${esc(result.semester_name)}</p><p><b>${result.applicable}/${result.total}</b> sinh viên sẽ dùng phiên bản này. <b>${result.changed}</b> đổi mức hỗ trợ; <b>${result.score_changed}</b> đổi điểm; <b>${result.rule_changed}</b> đổi kết luận học vụ. <b>${result.missing}</b> hồ sơ chưa đủ dữ liệu.</p>${table(['Mức hỗ trợ','Trước','Sau'],result.distribution.map(row=>[esc(row.label),row.before,row.after]))}<h3>Sinh viên có kết quả thay đổi</h3>${table(['Sinh viên','Điểm trước → sau','Mức trước → sau','Điều kiện học vụ trước → sau'],result.examples.map(row=>[`${esc(row.name)}<small>${esc(row.id)} · ${esc(row.class_name)}</small>`,`${score(row.before_score)} → ${score(row.after_score)}`,`${esc(row.before_level)} → ${esc(row.after_level)}`,`${esc(row.before_rule)} → ${esc(row.after_rule)}`]))}<p class="muted">${result.examples_total>result.examples.length?`Hiển thị ${result.examples.length}/${result.examples_total} trường hợp. `:''}${esc(result.note)}</p>${!version.active?`<button class="primary" type="button" id="apply-previewed-config">Áp dụng “${esc(version.name)}”</button>`:'<p class="notice">Phiên bản này đang được áp dụng.</p>'}`;
 const apply=$('#apply-previewed-config');
 if(apply)apply.onclick=()=>safe(async()=>{
  if(previewedConfig!==id)throw Error('Vui lòng xem trước lại phiên bản và học kỳ đã chọn.');
  apply.disabled=true;
  try{await api(`/api/configs/${id}/activate`,{method:'POST'});feedback('Đã áp dụng phiên bản '+version.name+'. Các đánh giá đã lưu được giữ nguyên.');await loadConfigurationVersions();await showConfigPreview(id);}finally{apply.disabled=false;}
 });
 $('#config-impact').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
}
async function initConfiguration(){
 fillConfiguration();
 $('#config-preset').onchange=()=>{const preset=configPresets.find(item=>item.id===$('#config-preset').value);$('#config-preset-description').textContent=preset.description;fillConfiguration();};
 $('#reset-config').onclick=()=>fillConfiguration();
 $('#config-form').addEventListener('input',event=>{if(event.target.name?.startsWith('weight_'))updateWeightTotal();});
 $('#rule-editor').addEventListener('change',event=>{
  const target=event.target;
  if(target.hasAttribute('data-rule-group'))policyNode(decodePath(target.dataset.ruleGroup)).op=target.value;
  if(target.hasAttribute('data-rule-op'))policyNode(decodePath(target.dataset.ruleOp)).op=target.value;
  if(target.hasAttribute('data-rule-value')){const node=policyNode(decodePath(target.dataset.ruleValue));node.value=Number(target.value)/(node.field==='failed_ratio'?100:1);}
  if(target.hasAttribute('data-rule-field')){const node=policyNode(decodePath(target.dataset.ruleField));node.field=target.value;node.value=policyFields[target.value].value;renderConditions();}
 });
 $('#rule-editor').addEventListener('input',event=>{
  if(event.target.hasAttribute('data-rule-value')){const node=policyNode(decodePath(event.target.dataset.ruleValue));node.value=Number(event.target.value)/(node.field==='failed_ratio'?100:1);}
 });
 $('#rule-editor').addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button)return;
  if(button.hasAttribute('data-add-condition'))policyNode(decodePath(button.dataset.addCondition)).children.push({field:'gpa',op:'lt',value:1.2});
  if(button.hasAttribute('data-add-group'))policyNode(decodePath(button.dataset.addGroup)).children.push({op:'AND',children:[{field:'gpa',op:'lt',value:1.2}]});
  if(button.hasAttribute('data-remove-rule')){const path=decodePath(button.dataset.removeRule);const parent=policyNode(path.slice(0,-1));if(parent.children.length>1)parent.children.splice(path.at(-1),1);}
  renderConditions();
 });
 $('#config-list').addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button)return;
  if(button.dataset.previewConfig)safe(()=>showConfigPreview(Number(button.dataset.previewConfig)));
  const id=Number(button.dataset.editConfig||button.dataset.copyConfig);
  if(id){fillConfiguration(configVersions.find(item=>item.id===id),!!button.dataset.copyConfig);$('#config-editor-title').scrollIntoView({block:'start'});$('#config-form').elements.name.focus();}
 });
 $('#config-preview-semester').onchange=()=>{if(previewedConfig)safe(()=>showConfigPreview(previewedConfig));};
 onForm('#config-form',async form=>{
  const data=readConfiguration(form),error=policyValidation(data.payload);
  if(error){$('#config-form-error').textContent=error;$('#config-form-error').hidden=false;throw Error(error);}
  const saved=await api(editingConfig?`/api/configs/${editingConfig}`:'/api/configs',{method:editingConfig?'PUT':'POST',body:data});
  editingConfig=saved.id;$('#config-form-error').hidden=true;$('#save-config').textContent='Lưu thay đổi bản nháp';
  $('#config-editor-status').textContent=saved.name;feedback('Đã lưu bản nháp. Xem trước ảnh hưởng rồi áp dụng khi phù hợp.');
  await loadConfigurationVersions();await showConfigPreview(saved.id);
 });
 await loadConfigurationVersions();
}
safe(initConfiguration);
