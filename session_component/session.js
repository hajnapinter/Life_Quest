/* Tab-scoped storage: no access token, URL credential, third-party script or persistent localStorage. */
const parentOrigin = new URL(document.referrer || window.location.href).origin;
let readSent = false, clearSent = false;
const nonce = crypto.randomUUID();
function send(type, extra = {}) {
  window.parent.postMessage({isStreamlitMessage:true,type,...extra}, parentOrigin);
}
function result(value) { send('streamlit:setComponentValue',{value:{...value,nonce},dataType:'json'}); }
window.addEventListener('message', event => {
  if (event.source !== window.parent || event.origin !== parentOrigin || event.data.type !== 'streamlit:render') return;
  const args = event.data.args || {};
  let host;
  try { host = new URL(args.project).hostname; } catch (_) { return; }
  const key = 'lifequest.session.' + host;
  try {
    if (args.mode === 'clear') {
      sessionStorage.removeItem(key);
      if (!clearSent) { clearSent = true; readSent = true; result({action:'clear'}); }
    } else if (args.mode === 'write' && typeof args.refresh_token === 'string') {
      sessionStorage.setItem(key,args.refresh_token);
      clearSent = false;
    } else if (args.mode === 'read' && !readSent) {
      readSent = true;
      result({action:'read',refresh_token:sessionStorage.getItem(key)});
    }
  } catch (_) {
    if (!readSent) { readSent=true; result({action:'unavailable'}); }
  }
  send('streamlit:setFrameHeight',{height:0});
});
send('streamlit:componentReady',{apiVersion:1});
send('streamlit:setFrameHeight',{height:0});
