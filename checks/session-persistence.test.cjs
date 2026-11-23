const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../session_component/session.js'),'utf8');
function runtime(local=new Map(), tab=new Map(), time=1000, blocked={}) {
  let listener; const messages=[]; const parent={postMessage:m=>messages.push(m)};
  function storage(map, unavailable) {return {getItem:k=>{if(unavailable)throw Error('blocked');return map.get(k)||null},setItem:(k,v)=>{if(unavailable)throw Error('blocked');map.set(k,v)},removeItem:k=>{if(unavailable)throw Error('blocked');map.delete(k)}}}
  const context={URL,Date:{now:()=>time},document:{referrer:'https://app.example.com/'},crypto:{randomUUID:()=>String(Math.random())},window:{parent,location:{href:'https://app.example.com/component'},addEventListener:(name,fn)=>{if(name==='message')listener=fn}},localStorage:storage(local,blocked.local),sessionStorage:storage(tab,blocked.tab)};
  vm.runInNewContext(source,context);
  return {local,tab,messages,render:args=>listener({source:parent,origin:'https://app.example.com',data:{type:'streamlit:render',args}}),storageEvent:e=>context.window.onstorage(e),last:()=>messages.filter(m=>m.type==='streamlit:setComponentValue').at(-1)?.value};
}
const project='https://project.supabase.co',key='lifequest.session.project.supabase.co';
test('a refresh credential survives reload and a new tab without persisting an access token',()=>{
 const a=runtime();a.render({project,mode:'write',refresh_token:'fixture-refresh'});
 assert.equal(a.last().action,'write');assert.equal(a.last().storage,'persistent');
 assert.equal(a.tab.size,0);const saved=JSON.parse(a.local.get(key));assert.equal(saved.refresh_token,'fixture-refresh');assert.equal(saved.access_token,undefined);
 const fresh=runtime(a.local);fresh.render({project,mode:'read'});assert.equal(fresh.last().refresh_token,'fixture-refresh');
 const other=runtime(a.local);other.render({project:'https://other.supabase.co',mode:'read'});assert.equal(other.last().refresh_token,null);
});
test('expired and malformed saved credentials are discarded',()=>{
 const a=runtime();a.render({project,mode:'write',refresh_token:'fixture'});
 const old=runtime(a.local,new Map(),1000+31*86400000);old.render({project,mode:'read'});assert.equal(old.last().refresh_token,null);assert.equal(a.local.size,0);
 a.local.set(key,'not-json');const bad=runtime(a.local);bad.render({project,mode:'read'});assert.equal(bad.last().refresh_token,null);
});
test('logout removes persistent and legacy credentials and signals other tabs',()=>{
 const a=runtime();a.render({project,mode:'write',refresh_token:'fixture'});a.tab.set(key,'old');a.local.set('unrelated','keep');a.render({project,mode:'clear'});
 assert.equal(a.local.has(key),false);assert.equal(a.tab.has(key),false);assert.equal(a.local.get('unrelated'),'keep');
 const b=runtime();b.render({project,mode:'read'});b.storageEvent({key,newValue:null});assert.equal(b.last().action,'logout');
});
test('blocked persistent storage falls back to this tab; blocked browser storage is reported',()=>{
 const a=runtime(new Map(),new Map(),1000,{local:true});a.render({project,mode:'write',refresh_token:'fixture'});assert.equal(a.last().storage,'tab');
 const reload=runtime(a.local,a.tab,1000,{local:true});reload.render({project,mode:'read'});assert.equal(reload.last().refresh_token,'fixture');
 const blocked=runtime(new Map(),new Map(),1000,{local:true,tab:true});blocked.render({project,mode:'read'});assert.equal(blocked.last().action,'unavailable');
});
