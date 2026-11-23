const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
function runtime(storage=new Map()) {
  let listener; const messages=[]; const parent={postMessage:m=>messages.push(m)};
  const context={URL,document:{referrer:'https://app.example.com/'},crypto:{randomUUID:()=>String(Math.random())},
    window:{parent,location:{href:'https://app.example.com/component'},addEventListener:(name,fn)=>listener=fn},
    sessionStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../session_component/session.js'),'utf8'),context);
  return {storage,messages,render:args=>listener({source:parent,origin:'https://app.example.com',data:{type:'streamlit:render',args}}),
    foreign:args=>listener({source:{},origin:'https://evil.example',data:{type:'streamlit:render',args}})};
}
test('refresh token survives a same-tab reload, is project-scoped and cleared by logout',()=>{
  const first=runtime();first.render({project:'https://project.supabase.co',mode:'write',refresh_token:'fixture-refresh'});
  const reloaded=runtime(first.storage);reloaded.render({project:'https://project.supabase.co',mode:'read'});
  assert.equal(reloaded.messages.find(m=>m.type==='streamlit:setComponentValue').value.refresh_token,'fixture-refresh');
  const other=runtime(first.storage);other.render({project:'https://other.supabase.co',mode:'read'});
  assert.equal(other.messages.find(m=>m.type==='streamlit:setComponentValue').value.refresh_token,null);
  reloaded.render({project:'https://project.supabase.co',mode:'clear'});
  assert.equal(first.storage.size,0);
});
test('foreign messages cannot write authentication state',()=>{
  const env=runtime();env.foreign({project:'https://project.supabase.co',mode:'write',refresh_token:'injected'});
  assert.equal(env.storage.size,0);
});
