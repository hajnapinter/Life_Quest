const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { webcrypto } = require('node:crypto');
const path = require('node:path');

function harness({stored = null, fetchResponse = {access_token: 'verified-token'}} = {}) {
  const messages = [], handlers = {}, storage = new Map();
  const button = {disabled: true, addEventListener: (name, fn) => handlers[name] = fn};
  const status = {textContent: ''};
  const popup = {opener: {}, location: {replace: url => popup.url = url}, close: () => popup.closed = true};
  let requests = 0;
  const origin = 'http://127.0.0.1:8502';
  const parent = {postMessage: value => messages.push(value)};
  const key = 'lifequest.pkce.project.supabase.co';
  if (stored) storage.set(key, JSON.stringify(stored));
  const window = {parent, location: {href: origin + '/component/lifequest_google'},
    open: () => popup, addEventListener: (name, fn) => handlers[name] = fn};
  const context = vm.createContext({window, document: {referrer: origin + '/', getElementById: id => id === 'google' ? button : status},
    URL, URLSearchParams, TextEncoder, Uint8Array, Date, JSON, crypto: webcrypto,
    btoa: value => Buffer.from(value, 'binary').toString('base64'),
    localStorage: {getItem: k => storage.get(k), setItem: (k,v) => storage.set(k,v), removeItem: k => storage.delete(k)},
    fetch: async (url, options) => { requests++; context.lastRequest = {url, options}; return {ok:true, json:async () => fetchResponse}; }
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../auth_component/oauth.js'), 'utf8'), context);
  const render = (code = null, source = parent) => handlers.message({source, origin, data: {type:'streamlit:render', args:{enabled:true, code,
    supabase_url:'https://project.supabase.co', public_key:'publishable', redirect_url:origin + '/'}}});
  return {render, handlers, button, status, popup, storage, key, messages, context, requests: () => requests};
}
const tick = () => new Promise(resolve => setImmediate(resolve));
async function runTests() {
  let h = harness();
  h.render(null, {});
  assert.equal(h.button.disabled, true, 'foreign postMessage ignored');
  h.render();
  await h.handlers.click();
  const authUrl = new URL(h.popup.url);
  assert.equal(authUrl.searchParams.get('provider'), 'google');
  assert.equal(authUrl.searchParams.get('code_challenge_method'), 's256');
  const saved = JSON.parse(h.storage.get(h.key));
  assert.equal(saved.verifier.length, 43);
  assert(!h.popup.url.includes(saved.verifier), 'verifier must not be in authorize URL');
  const expected = Buffer.from(await webcrypto.subtle.digest('SHA-256', new TextEncoder().encode(saved.verifier))).toString('base64url');
  assert.equal(authUrl.searchParams.get('code_challenge'), expected);
  // Simulate a fresh callback page after Streamlit session is lost.
  h = harness({stored: saved}); h.render('one-time-code'); await tick();
  assert.equal(h.requests(), 1);
  assert.deepEqual(JSON.parse(h.context.lastRequest.options.body), {auth_code:'one-time-code', code_verifier:saved.verifier});
  assert.equal(h.storage.has(h.key), false, 'remove verifier after success');
  assert(h.messages.some(m => m.value?.access_token === 'verified-token'));
  h.render('one-time-code'); await tick(); assert.equal(h.requests(), 1, 'do not redeem a code twice');
  h = harness(); h.render('foreign-code'); await tick();
  assert.equal(h.requests(), 0, 'reject callback without browser verifier');
  assert(h.messages.some(m => m.value?.error));
  h = harness({stored: {verifier:'old',created:Date.now()-700000}});
  h.render('expired-code'); await tick(); assert.equal(h.requests(), 0);
  h = harness({stored:saved,fetchResponse:{error:'invalid_grant'}});
  h.render('invalid-code'); await tick();
  assert(!h.messages.some(m => m.value?.access_token));
  return 'OAuth checks passed: PKCE SHA-256, new-session callback, replay guard, foreign message, missing/expired verifier, failed exchange.';
}
module.exports = {runTests};
if (require.main === module) runTests().then(console.log).catch(error => {console.error(error); process.exitCode=1;});
