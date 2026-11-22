/* PKCE verifier stays in this browser; Supabase verifies the Google identity. */
const button = document.getElementById('google');
const status = document.getElementById('status');
let args, processedCode, busy = false;
const parentOrigin = new URL(document.referrer || window.location.href).origin;
function send(type, extra = {}) {
  window.parent.postMessage({isStreamlitMessage: true, type, ...extra}, parentOrigin);
}
function result(value) { send('streamlit:setComponentValue', {value, dataType: 'json'}); }
function b64(bytes) { return btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/, ''); }
function storageKey() { return 'lifequest.pkce.' + new URL(args.supabase_url).hostname; }
async function exchange(code) {
  if (processedCode === code || busy) return;
  processedCode = code; busy = true; button.disabled = true;
  status.textContent = 'Completing Google sign-in…';
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey()) || 'null');
    if (!saved || Date.now() - saved.created > 600000) throw new Error('expired');
    const response = await fetch(args.supabase_url + '/auth/v1/token?grant_type=pkce', {
      method: 'POST', headers: {'apikey': args.public_key, 'Content-Type':'application/json'},
      body: JSON.stringify({auth_code: code, code_verifier: saved.verifier})
    });
    const session = await response.json();
    if (!response.ok || !session.access_token) throw new Error('exchange_failed');
    localStorage.removeItem(storageKey());
    // Tokens are sent through the component channel, never in a URL or localStorage.
    result({access_token: session.access_token, refresh_token: session.refresh_token, expires_in: session.expires_in, code});
    status.textContent = 'Signed in. Loading your quests…';
  } catch (_) {
    localStorage.removeItem(storageKey());
    result({error: 'Google sign-in could not be completed. Start again in the same browser.', code});
    status.textContent = 'Please start Google sign-in again.';
    button.disabled = false;
  } finally { busy = false; }
}
button.addEventListener('click', async () => {
  if (!args || busy) return;
  // Open synchronously to avoid popup blockers during the SHA-256 await.
  const popup = window.open('about:blank', '_blank');
  if (!popup) { status.textContent = 'Allow a new tab for Google sign-in, then try again.'; return; }
  try {
    popup.opener = null;
    const verifier = b64(crypto.getRandomValues(new Uint8Array(32)));
    const challenge = b64(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))));
    localStorage.setItem(storageKey(), JSON.stringify({verifier, created: Date.now()}));
    const url = new URL(args.supabase_url + '/auth/v1/authorize');
    url.search = new URLSearchParams({provider:'google', redirect_to:args.redirect_url,
      code_challenge:challenge, code_challenge_method:'s256', scopes:'email profile'});
    popup.location.replace(url.toString());
    status.textContent = 'Continue in the new tab. Starting again replaces the previous sign-in attempt.';
  } catch (_) {
    popup.close(); status.textContent = 'Your browser must allow local storage and secure connections for Google sign-in.';
  }
});
window.addEventListener('message', event => {
  if (event.source !== window.parent || event.origin !== parentOrigin || event.data.type !== 'streamlit:render') return;
  args = event.data.args;
  button.disabled = !args.enabled || busy;
  if (args.code) exchange(args.code);
  fit();
});
send('streamlit:componentReady', {apiVersion:1});
// Size the iframe to its content (button + status line) instead of a fixed 110px.
function fit() {
  const body = document.body;
  const height = body && body.getBoundingClientRect ? Math.ceil(body.getBoundingClientRect().height) : 0;
  send('streamlit:setFrameHeight', {height: height || 110});
}
if (typeof ResizeObserver === 'function' && document.body) new ResizeObserver(fit).observe(document.body);
fit();
