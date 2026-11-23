const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const path=require('node:path');

test('Google callback carries an invitation across tabs without joining or putting tokens in a URL',async()=>{
  const origin='https://example.streamlit.app';const parent={postMessage:v=>messages.push(v)};
  const messages=[],handlers={},storage=new Map();let popupUrl;
  const popup={location:{replace:url=>popupUrl=url},close:()=>{}};
  const button={addEventListener:(name,fn)=>handlers[name]=fn};
  const context={window:{parent,location:{href:origin+'/component'},open:()=>popup,addEventListener:(name,fn)=>handlers[name]=fn},
    document:{referrer:origin+'/',getElementById:id=>id==='google'?button:{}},
    localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
    URL,URLSearchParams,TextEncoder,Uint8Array,Date,JSON,crypto:webcrypto,
    btoa:v=>Buffer.from(v,'binary').toString('base64'),
    fetch:async()=>({ok:true,json:async()=>({access_token:'fixture-access',refresh_token:'fixture-refresh'})})};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../auth_component/oauth.js'),'utf8'),context);
  const invitation={kind:'squad',code:'ABCDEF12'};
  const render=args=>handlers.message({source:parent,origin,data:{type:'streamlit:render',args:{enabled:true,supabase_url:'https://fixture.supabase.co',public_key:'fixture',redirect_url:origin+'/',...args}}});
  render({invitation});await handlers.click();
  assert.deepEqual(JSON.parse(storage.values().next().value).invitation,invitation);
  assert(!popupUrl.includes('fixture-access')&&!popupUrl.includes('ABCDEF12'));
  render({code:'fixture-code'});await new Promise(resolve=>setImmediate(resolve));
  const reply=messages.find(m=>m.value?.access_token);
  assert.deepEqual(JSON.parse(JSON.stringify(reply.value.invitation)),invitation);
  assert.equal(storage.size,0);
});
