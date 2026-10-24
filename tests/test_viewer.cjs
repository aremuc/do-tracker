const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{constructor(tag='div'){this.tagName=tag;this.children=[];this.value='';this.textContent='';this.checked=false;this.hidden=false;this.listeners={};this.attributes={}}append(...nodes){this.children.push(...nodes)}replaceChildren(...nodes){this.children=[...nodes]}addEventListener(type,fn){this.listeners[type]=fn}setAttribute(k,v){this.attributes[k]=v}}
const ids=['search','sort','category','tier','benefits','workplace','language','verified','count','jobs','data','updated','stale','saved-count','all-tab','saved-tab','save-status','storage-note','reset','load-more'];
const sample=(id,title,date,benefits,workplace,more={})=>({id,title,posted_date:date,benefits,workplace,category:'Administration',tier:'Review',status:'Unverified',company:'Example',location:'Toronto',salary:'Unknown',flags:[],sources:['Test'],url:'https://example.org/job',...more});
const samples=[sample('a','Older','2026-10-01','Advertised — confirm coverage','Hybrid advertised',{bilingual_signal:true,preference_score:9}),sample('b','Newest','2026-10-23','Not stated / not extracted','In-person advertised',{preference_score:3}),sample('c','No benefits','2026-10-20','Not offered in text','Remote advertised',{tier:'Fallback',preference_score:1})];
const storage=new Map();
function boot(data=samples,blocked=false){const nodes=Object.fromEntries(ids.map(id=>[id,new Element()]));nodes.sort.value='newest';nodes.data.textContent=JSON.stringify(data);const html=fs.readFileSync('tracker/viewer.html','utf8').replaceAll('__TODAY__','2026-10-24').replaceAll('__DISCOVERED__','2026-10-24T12:00:00-04:00');const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]);const context=vm.createContext({document:{getElementById:id=>nodes[id],createElement:tag=>new Element(tag)},localStorage:{getItem:key=>{if(blocked)throw Error('blocked');return storage.get(key)||null},setItem:(key,val)=>storage.set(key,val)}});vm.runInContext(scripts.at(-1),context);return {nodes,context}}
let {nodes,context}=boot();
const descendants=n=>[n,...n.children.flatMap(descendants)];
const titles=()=>nodes.jobs.children.filter(x=>x.tagName==='article').map(x=>descendants(x).find(x=>x.tagName==='h2').textContent);
function change(id,value){if(id==='language')nodes[id].checked=Boolean(value);else nodes[id].value=value;vm.runInContext('render()',context)}
assert.deepStrictEqual(titles(),['Newest','No benefits','Older']);
change('benefits','advertised');assert.deepStrictEqual(titles(),['Older']);
change('benefits','unknown');assert.deepStrictEqual(titles(),['Newest']);
change('benefits','unavailable');assert.deepStrictEqual(titles(),['No benefits']);
change('benefits','');change('language',true);assert.deepStrictEqual(titles(),['Older']);
change('language',false);change('workplace','Remote');assert.deepStrictEqual(titles(),['No benefits']);
change('workplace','');change('sort','signals');assert.deepStrictEqual(titles(),['Older','Newest','No benefits']);
change('search','none-found');assert.strictEqual(titles().length,0);
nodes.reset.listeners.click();assert.deepStrictEqual(titles(),['Newest','No benefits','Older']);
vm.runInContext("toggleSaved('b')",context);assert.ok(storage.values().next().value.includes('b'));
nodes['saved-tab'].listeners.click();assert.deepStrictEqual(titles(),['Newest']);
({nodes,context}=boot());nodes['saved-tab'].listeners.click();assert.deepStrictEqual(titles(),['Newest']);
vm.runInContext("toggleSaved('b')",context);assert.strictEqual(titles().length,0);
({nodes,context}=boot(samples,true));assert.strictEqual(nodes['storage-note'].hidden,false);vm.runInContext("toggleSaved('a')",context);nodes['saved-tab'].listeners.click();assert.deepStrictEqual(titles(),['Older']);
({nodes,context}=boot(Array.from({length:24},(_,i)=>sample('job'+i,'Role '+i,'2026-10-23','Not stated','Hybrid advertised'))));assert.strictEqual(titles().length,20);assert.strictEqual(nodes['load-more'].hidden,false);nodes['load-more'].listeners.click();assert.strictEqual(titles().length,24);assert.strictEqual(nodes['load-more'].hidden,true);
({nodes,context}=boot([sample('unsafe','Unsafe link','2026-10-23','Not stated','Hybrid advertised',{url:'javascript:alert(1)'})]));assert.strictEqual(descendants(nodes.jobs).filter(x=>x.tagName==='a').length,0);
console.log('Viewer checks passed: filters, sort, reset, saved jobs, reload persistence, blocked storage, pagination and unsafe links.');
