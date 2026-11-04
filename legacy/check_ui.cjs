// Dependency-free smoke checks for route rendering and filter logic, with fixture data.
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const html=fs.readFileSync('preview.html','utf8');
const data=JSON.parse(html.match(/const PREVIEW_DATA = (.*);/)[1]);
const elements=new Map();
const element=()=>({innerHTML:'',textContent:'',value:'',disabled:false,classList:{add(){},remove(){}},addEventListener(){}});
const document={querySelector(key){if(!elements.has(key))elements.set(key,element());return elements.get(key);},addEventListener(){},title:''};
const context=vm.createContext({document,location:{hash:''},window:{addEventListener(){},scrollTo(){}},setTimeout(){},clearTimeout(){},console,fetch:async url=>({ok:true,json:async()=>data[url.replace('/api/','')]})});
vm.runInContext(fs.readFileSync('static/app.js','utf8'),context);
vm.runInContext(`state.students=${JSON.stringify(data.students)};state.interventions=${JSON.stringify(data.interventions)};state.settings=${JSON.stringify(data.settings)};`,context);
for(const route of ['dashboard','students','student/2351010101','results','warnings','interventions','import','reports','settings']){
 context.location.hash='#'+route;vm.runInContext('render()',context);
 const result=elements.get('#main').innerHTML;
 assert.ok(result.length>500,route+' failed to render');
 assert.ok(!result.includes('undefined'),route+' leaked undefined');
 console.log('PASS route '+route);
}
context.location.hash='#students';vm.runInContext('render();state.filters.search="nguyen minh anh";',context);
assert.equal(vm.runInContext('filteredStudents().length',context),1);
vm.runInContext('state.filters={class_name:"CNTT23A",level:"high"};',context);
assert.ok(vm.runInContext('filteredStudents().every(s=>s.class_name==="CNTT23A"&&s.risk.level==="high")',context));
assert.equal(vm.runInContext('esc("<img onerror=evil()>")',context),'&lt;img onerror=evil()&gt;');
console.log('PASS accent-insensitive search, combined filters, HTML escaping');
