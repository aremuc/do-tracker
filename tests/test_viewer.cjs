const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{constructor(tag='div'){this.tagName=tag;this.children=[];this.value='';this.textContent='';this.listeners={};}append(...nodes){this.children.push(...nodes)}replaceChildren(...nodes){this.children=[...nodes]}addEventListener(type,fn){this.listeners[type]=fn}}
const ids=['search','sort','category','tier','benefits','workplace','language','verified','count','jobs','data'];
const elements=Object.fromEntries(ids.map(id=>[id,new Element()]));elements.sort.value='newest';
const sample=(title,date,benefits,workplace,more={})=>({title,posted_date:date,benefits,workplace,category:'Administration',tier:'Review',status:'Unverified',company:'Example',location:'Toronto',salary:'Unknown',flags:[],sources:['Test'],url:'https://example.org/job',...more});
elements.data.textContent=JSON.stringify([
 sample('Older','2026-10-01','Advertised — confirm coverage','Hybrid advertised',{bilingual_signal:true,preference_score:9}),
 sample('Newest','2026-10-23','Not stated / not extracted','In-person advertised',{preference_score:3}),
 sample('No benefits','2026-10-20','Not offered in text','Remote advertised',{tier:'Fallback',preference_score:1})]);
const html=fs.readFileSync('tracker/viewer.html','utf8').replace('__TODAY__','2026-10-24');
const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
const context=vm.createContext({document:{getElementById:id=>elements[id],createElement:tag=>new Element(tag)}});
vm.runInContext(scripts.at(-1),context);
function titles(){return elements.jobs.children.filter(x=>x.tagName==='article').map(x=>x.children[0].textContent)}
function change(id,value){elements[id].value=value;vm.runInContext('render()',context)}
assert.deepStrictEqual(titles(),['Newest','No benefits','Older']);
change('benefits','advertised');assert.deepStrictEqual(titles(),['Older']);
change('benefits','unknown');assert.deepStrictEqual(titles(),['Newest']);
change('benefits','unavailable');assert.deepStrictEqual(titles(),['No benefits']);
change('benefits','');change('language','french');assert.deepStrictEqual(titles(),['Older']);
change('language','');change('workplace','Remote');assert.deepStrictEqual(titles(),['No benefits']);
change('workplace','');change('sort','signals');assert.deepStrictEqual(titles(),['Older','Newest','No benefits']);
change('search','none-found');assert.strictEqual(titles().length,0);
console.log('Viewer functional tests passed: sorting, benefit states, French signal, workplace and search. DOM harness only; no browser screenshot test.');
