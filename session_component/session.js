/* Remember only a rotating refresh credential; Supabase re-verifies it on every restore. */
// Only talk to the app's own origin: a page that frames this component elsewhere gets nothing.
const parentOrigin = new URL(window.location.href).origin;
const MAX_AGE = 30 * 24 * 60 * 60 * 1000;
let readSent = false, clearSent = false, lastWritten = null, activeKey = null;
function send(type, extra = {}) {
  window.parent.postMessage({isStreamlitMessage:true,type,...extra}, parentOrigin);
}
function result(value) {
  send('streamlit:setComponentValue',{value:{...value,nonce:crypto.randomUUID()},dataType:'json'});
}
function removeSaved(key) {
  try { localStorage.removeItem(key); } catch (_) {}
  try { sessionStorage.removeItem(key); } catch (_) {}
}
function readSaved(key) {
  let available = false;
  try {
    const raw = localStorage.getItem(key);
    available = true;
    if (raw) {
      try {
        const saved = JSON.parse(raw);
        if (saved.version === 1 && typeof saved.refresh_token === 'string' &&
            saved.refresh_token.length > 0 && saved.refresh_token.length <= 4096 &&
            Number.isFinite(saved.expires_at) && saved.expires_at > Date.now() &&
            saved.expires_at <= Date.now() + MAX_AGE) return {token:saved.refresh_token};
      } catch (_) {}
      localStorage.removeItem(key);
    }
  } catch (_) {}
  // Migrate a session saved by an older app; also support browsers blocking persistent storage.
  try { return {token:sessionStorage.getItem(key)}; } catch (_) {}
  return {token:null, unavailable:!available};
}
function writeSaved(key, token) {
  try {
    localStorage.setItem(key,JSON.stringify({version:1,refresh_token:token,expires_at:Date.now()+MAX_AGE}));
    try { sessionStorage.removeItem(key); } catch (_) {}
    return 'persistent';
  } catch (_) {}
  try { sessionStorage.setItem(key,token); return 'tab'; } catch (_) {}
  return 'unavailable';
}
window.onstorage = event => {
  if (activeKey && event.key === activeKey && event.newValue === null) {
    // Logging out in another tab must not leave this app showing a signed-in account.
    try { sessionStorage.removeItem(activeKey); } catch (_) {}
    lastWritten = null;
    result({action:'logout'});
  }
};
window.addEventListener('message', event => {
  if (event.source !== window.parent || event.origin !== parentOrigin || event.data.type !== 'streamlit:render') return;
  const args = event.data.args || {};
  let host;
  try { host = new URL(args.project).hostname; } catch (_) { return; }
  const key = 'lifequest.session.' + host;
  activeKey = key;
  if (args.mode === 'clear') {
    removeSaved(key);
    lastWritten = null;
    if (!clearSent) { clearSent = true; readSent = true; result({action:'clear'}); }
  } else if (args.mode === 'write' && typeof args.refresh_token === 'string' &&
             args.refresh_token.length > 0 && args.refresh_token.length <= 4096) {
    clearSent = false;
    if (lastWritten !== args.refresh_token) {
      const storage = writeSaved(key,args.refresh_token);
      lastWritten = args.refresh_token;
      result({action:'write',storage});
    }
  } else if (args.mode === 'read' && !readSent) {
    const saved = readSaved(key);
    readSent = true;
    result({action:saved.unavailable?'unavailable':'read',refresh_token:saved.token});
  }
  send('streamlit:setFrameHeight',{height:0});
});
send('streamlit:componentReady',{apiVersion:1});
send('streamlit:setFrameHeight',{height:0});
