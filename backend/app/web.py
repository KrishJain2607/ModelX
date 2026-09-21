from fastapi.responses import HTMLResponse

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ModelX — Market Research POC</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin:0; background:#0b1020; color:#e8ecf7; }
    .wrap { max-width:1180px; margin:0 auto; padding:32px 20px 56px; }
    .hero { display:flex; justify-content:space-between; gap:24px; align-items:flex-start; margin-bottom:24px; }
    h1 { margin:0 0 8px; font-size:34px; } h2 { margin-top:0; font-size:20px; }
    p { color:#9ca8c0; line-height:1.5; }
    .badge { border:1px solid #34405a; border-radius:999px; padding:8px 12px; color:#9fe3b1; white-space:nowrap; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); gap:16px; }
    .card { background:#121a2d; border:1px solid #25314b; border-radius:16px; padding:20px; box-shadow:0 10px 30px rgba(0,0,0,.18); }
    label { display:block; color:#aab4c9; font-size:13px; margin:12px 0 6px; }
    input,button { width:100%; box-sizing:border-box; border-radius:10px; border:1px solid #34415e; padding:11px 12px; font:inherit; }
    input { background:#0d1425; color:#fff; }
    button { background:#edf2ff; color:#0b1020; cursor:pointer; font-weight:700; margin-top:14px; }
    button.secondary { background:#1a2640; color:#e8ecf7; }
    pre { white-space:pre-wrap; word-break:break-word; background:#0a0f1c; padding:14px; border-radius:10px; min-height:70px; color:#c9d4eb; }
    .score { font-size:44px; font-weight:800; margin:10px 0; }
    .signal { font-weight:800; }
    .muted { color:#7f8aa1; font-size:13px; }
    .results { display:grid; gap:10px; margin-top:14px; }
    .result { border:1px solid #2c3852; border-radius:12px; padding:12px; background:#0d1425; }
    .result strong { font-size:17px; } .pill { float:right; font-weight:800; }
    a { color:#b7c8ff; }
  </style>
</head>
<body>
<main class="wrap">
  <section class="hero">
    <div><h1>ModelX</h1><p>Read-only market research POC — Kite data → indicators → transparent technical signal.</p></div>
    <div class="badge">LIVE TRADING: OFF</div>
  </section>

  <div class="grid">
    <section class="card">
      <h2>1. Connect Kite</h2>
      <p>Login happens on Kite. ModelX never asks for your Kite password or OTP.</p>
      <button onclick="connectKite()">Login with Kite</button>
      <button class="secondary" onclick="checkProfile()">Check connection</button>
      <pre id="authResult">Not connected.</pre>
    </section>

    <section class="card">
      <h2>2. Find a stock</h2>
      <p class="muted">Search the NSE instrument list by symbol or company name.</p>
      <label for="query">Symbol / company</label>
      <input id="query" placeholder="RELIANCE, TCS, HDFC..." onkeydown="if(event.key==='Enter') searchStock()">
      <button onclick="searchStock()">Search</button>
      <div id="searchResults" class="results"></div>
    </section>

    <section class="card">
      <h2>3. Analyze selected stock</h2>
      <p class="muted">Daily candles, 365-day lookback. No order is placed.</p>
      <input id="token" type="hidden">
      <div id="selected">No stock selected.</div>
      <button onclick="analyze()">Run analysis</button>
      <div id="score"></div>
      <pre id="analysisResult">No analysis run yet.</pre>
    </section>

    <section class="card">
      <h2>4. Scan a watchlist</h2>
      <p class="muted">Enter up to 10 NSE equity symbols, comma-separated. ModelX ranks the returned technical scores.</p>
      <input id="watchlist" placeholder="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK">
      <button onclick="scan()">Run scan</button>
      <div id="scanResults" class="results"></div>
      <pre id="scanRaw">No scan run yet.</pre>
    </section>
  </div>

  <section class="card" style="margin-top:16px">
    <h2>POC status</h2>
    <pre id="health">Checking...</pre>
    <p class="muted">API documentation: <a href="/docs">/docs</a></p>
  </section>
</main>
<script>
async function connectKite() {
  const r = await fetch('/api/broker/login-url'); const data = await r.json();
  if (!r.ok) return show('authResult', data); window.location.href = data.login_url;
}
async function checkProfile() {
  const r = await fetch('/api/broker/profile'); show('authResult', await r.json());
}
async function searchStock() {
  const q = document.getElementById('query').value.trim();
  if (!q) return;
  const r = await fetch('/api/market/search?q=' + encodeURIComponent(q));
  const data = await r.json(); const box = document.getElementById('searchResults'); box.innerHTML = '';
  if (!r.ok) return show('searchResults', data);
  if (!data.results.length) { box.textContent = 'No matching NSE equity found.'; return; }
  data.results.forEach(item => {
    const div = document.createElement('div'); div.className='result';
    div.innerHTML = '<strong>' + item.tradingsymbol + '</strong><br><span class="muted">' + (item.name || '') + '</span>';
    div.onclick = () => selectStock(item); box.appendChild(div);
  });
}
function selectStock(item) {
  document.getElementById('token').value = item.instrument_token;
  document.getElementById('selected').textContent = item.tradingsymbol + ' — ' + (item.name || '');
}
async function analyze() {
  const token = document.getElementById('token').value;
  if (!token) return show('analysisResult', {error:'Search and select a stock first'});
  const r = await fetch('/api/analysis/' + encodeURIComponent(token) + '?interval=day');
  const data = await r.json(); show('analysisResult', data);
  document.getElementById('score').innerHTML = data.score !== undefined
    ? '<div class="score">' + data.score + '/100</div><div class="signal">' + (data.signal || '') + '</div>' : '';
}
async function scan() {
  const symbols = document.getElementById('watchlist').value.trim();
  if (!symbols) return;
  const r = await fetch('/api/analysis/scan?symbols=' + encodeURIComponent(symbols));
  const data = await r.json(); const box = document.getElementById('scanResults'); box.innerHTML='';
  if (!r.ok) return show('scanRaw', data);
  (data.results || []).forEach(item => {
    const div = document.createElement('div'); div.className='result';
    div.innerHTML = '<strong>' + item.symbol + '</strong><span class="pill">' +
      (item.score !== undefined ? item.score + '/100' : item.status) + '</span><br>' +
      '<span class="muted">' + (item.signal || item.message || '') + '</span>';
    box.appendChild(div);
  });
  show('scanRaw', data);
}
async function loadHealth() { const r = await fetch('/health'); show('health', await r.json()); }
function show(id, value) {
  const el = document.getElementById(id);
  if (typeof value === 'string') el.textContent=value; else el.textContent=JSON.stringify(value,null,2);
}
loadHealth();
const params = new URLSearchParams(window.location.search);
if (params.get('auth') === 'success') show('authResult', {status:'authenticated', user_id:params.get('user_id') || 'connected'});
if (params.get('auth') === 'error') show('authResult', {status:'failed', message:params.get('message') || 'Kite authentication failed'});
if (params.has('auth')) history.replaceState({}, '', '/');
</script>
</body>
</html>
"""

def page() -> HTMLResponse:
    return HTMLResponse(PAGE)
