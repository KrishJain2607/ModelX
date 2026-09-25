from fastapi.responses import HTMLResponse


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ModelX — Research & Paper Trading</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin:0; background:#0b1020; color:#e8ecf7; }
    .wrap { max-width:1240px; margin:0 auto; padding:30px 18px 56px; }
    .hero { display:flex; justify-content:space-between; gap:24px; align-items:flex-start; margin-bottom:20px; }
    h1 { margin:0 0 7px; font-size:34px; } h2 { margin:0 0 8px; font-size:20px; }
    p { color:#9ca8c0; line-height:1.45; margin:7px 0; }
    .badge { border:1px solid #34405a; border-radius:999px; padding:8px 12px; color:#9fe3b1; white-space:nowrap; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:15px; }
    .card { background:#121a2d; border:1px solid #25314b; border-radius:16px; padding:18px; box-shadow:0 10px 30px rgba(0,0,0,.16); }
    .wide { grid-column:1/-1; }
    label { display:block; color:#aab4c9; font-size:13px; margin:11px 0 5px; }
    input,button { width:100%; box-sizing:border-box; border-radius:10px; border:1px solid #34415e; padding:10px 11px; font:inherit; }
    input { background:#0d1425; color:#fff; }
    button { background:#edf2ff; color:#0b1020; cursor:pointer; font-weight:700; margin-top:11px; }
    button.secondary { background:#1a2640; color:#e8ecf7; }
    button.danger { background:#3a1d29; color:#ffd7df; }
    pre { white-space:pre-wrap; word-break:break-word; background:#0a0f1c; padding:12px; border-radius:10px; min-height:55px; color:#c9d4eb; }
    .score { font-size:42px; font-weight:800; margin:8px 0 2px; }
    .signal { font-weight:800; }
    .muted { color:#7f8aa1; font-size:13px; }
    .results { display:grid; gap:9px; margin-top:12px; }
    .result { border:1px solid #2c3852; border-radius:12px; padding:11px; background:#0d1425; cursor:pointer; }
    .result strong { font-size:16px; } .pill { float:right; font-weight:800; }
    .metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(125px,1fr)); gap:8px; margin:12px 0; }
    .metric { background:#0d1425; border:1px solid #293650; border-radius:10px; padding:10px; }
    .metric b { display:block; font-size:18px; margin-top:3px; }
    .factor { padding:7px 0; border-bottom:1px solid #202b42; }
    .factor:last-child { border-bottom:0; }
    .ok { color:#9fe3b1; } .warn { color:#ffd78f; } .bad { color:#ff9fae; }
    .row { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; }
    a { color:#b7c8ff; }
    button { position:relative; overflow:hidden; transition:transform .14s ease, box-shadow .18s ease, opacity .18s ease, border-color .18s ease; }
    button:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 8px 20px rgba(80,120,255,.16); border-color:#52658d; }
    button:active:not(:disabled) { transform:scale(.98); }
    button:disabled { cursor:wait; opacity:.65; }
    button.loading { padding-left:38px; }
    button.loading::before { content:""; position:absolute; left:13px; top:50%; width:13px; height:13px; margin-top:-7px; border:2px solid rgba(11,16,32,.25); border-top-color:#0b1020; border-radius:50%; animation:spin .75s linear infinite; }
    button.secondary.loading::before { border-color:rgba(232,236,247,.22); border-top-color:#e8ecf7; }
    .action-status { min-height:20px; margin-top:10px; padding:0 2px; color:#8e9bb5; font-size:13px; }
    .action-status.active { color:#b7c8ff; } .action-status.success { color:#9fe3b1; } .action-status.error { color:#ff9fae; }
    .flash { animation:flash .65s ease; }
    .result { transition:transform .16s ease, border-color .16s ease, background .16s ease; animation:rise .28s ease both; }
    .result:hover { transform:translateX(3px); border-color:#52658d; background:#111b31; }
    .metric { transition:transform .16s ease, border-color .16s ease; }
    .metric:hover { transform:translateY(-2px); border-color:#465a82; }
    .toast { position:fixed; right:18px; bottom:18px; z-index:20; max-width:360px; padding:12px 15px; border:1px solid #34415e; border-radius:12px; background:#121a2d; box-shadow:0 12px 35px rgba(0,0,0,.3); color:#e8ecf7; opacity:0; transform:translateY(12px); pointer-events:none; transition:opacity .2s ease, transform .2s ease; }
    .toast.show { opacity:1; transform:translateY(0); } .toast.success { border-color:#39704b; } .toast.error { border-color:#783d48; }
    @keyframes spin { to { transform:rotate(360deg); } }
    @keyframes flash { 0% { box-shadow:0 0 0 0 rgba(120,150,255,0); } 35% { box-shadow:0 0 0 5px rgba(120,150,255,.18); } 100% { box-shadow:0 0 0 0 rgba(120,150,255,0); } }
    @keyframes rise { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
    @media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms !important; transition-duration:.01ms !important; } }
    @media(max-width:600px){ .hero{display:block}.badge{display:inline-block;margin-top:10px}.row{grid-template-columns:1fr} }
  </style>
</head>
<body>
<main class="wrap">
  <section class="hero">
    <div>
      <h1>ModelX</h1>
      <p>Research → risk plan → paper trade. Market data is read-only and live trading is hard-disabled.</p>
    </div>
    <div class="badge">LIVE TRADING: OFF</div>
  </section>

  <div class="grid">
    <section class="card">
      <h2>System status</h2>
      <p class="muted">Current provider, authentication and safety state.</p>
      <pre id="health">Checking...</pre>
      <div id="healthStatus" class="action-status">Checking system health…</div>
      <button class="secondary" onclick="loadHealth(this)">Refresh status</button>
    </section>

    <section class="card">
      <h2>Stock search</h2>
      <p class="muted">Search NSE equities and select one for analysis.</p>
      <input id="query" placeholder="RELIANCE, TCS, HDFC..." onkeydown="if(event.key==='Enter') searchStock()">
      <button onclick="searchStock(this)">Search</button>
      <div id="searchResults" class="results"></div>
    </section>

    <section class="card">
      <h2>Selected stock analysis</h2>
      <div id="selected">No stock selected.</div>
      <input id="token" type="hidden">
      <div id="analysisStatus" class="action-status">Ready.</div>
      <button onclick="analyze(this)">Run analysis</button>
      <button class="secondary" onclick="runCouncil(this)">Run AI Council</button>
      <button class="secondary" onclick="sendApproval(this)">Send trade approval email</button>
      <div id="score"></div>
      <div id="metrics" class="metrics"></div>
      <div id="factors"></div>
      <pre id="analysisResult">No analysis run yet.</pre>
    </section>

    <section class="card">
      <h2>Watchlist scan</h2>
      <p class="muted">Maximum 10 NSE symbols. Results are ranked by technical score, not by predicted return.</p>
      <input id="watchlist" value="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK">
      <div id="scanStatus" class="action-status">Ready.</div>
      <button onclick="scan(this)">Run scan</button>
      <button class="secondary" onclick="emailScan(this)">Email scan</button>
      <div id="scanResults" class="results"></div>
      <pre id="scanRaw">No scan run yet.</pre>
    </section>

    <section class="card">
      <h2>Risk planner</h2>
      <p class="muted">Long-trade position sizing using the configured risk limits.</p>
      <div class="row">
        <div><label>Entry</label><input id="entry" type="number" step="0.01" value="1000"></div>
        <div><label>Stop loss</label><input id="stop" type="number" step="0.01" value="950"></div>
        <div><label>Target</label><input id="target" type="number" step="0.01" value="1100"></div>
        <div><label>Available capital</label><input id="capital" type="number" step="1000" value="100000"></div>
      </div>
      <button onclick="riskPlan(this)">Calculate risk plan</button>
      <pre id="riskResult">No risk plan calculated.</pre>
    </section>

    <section class="card">
      <h2>Paper trade</h2>
      <p class="muted">No broker order is sent. The requested quantity is checked against ModelX's risk-derived maximum.</p>
      <div class="row">
        <div><label>Symbol</label><input id="paperSymbol" value="SUZLON"></div>
        <div><label>Quantity</label><input id="paperQty" type="number" min="1" value="1"></div>
        <div><label>Entry</label><input id="paperEntry" type="number" step="0.01" value="100"></div>
        <div><label>Stop loss</label><input id="paperStop" type="number" step="0.01" value="95"></div>
        <div><label>Target</label><input id="paperTarget" type="number" step="0.01" value="110"></div>
        <div><label>Available capital</label><input id="paperCapital" type="number" step="1000" value="100000"></div>
      </div>
      <div id="paperStatus" class="action-status">Ready.</div>
      <button onclick="openPaperTrade(this)">Open paper trade</button>
      <button class="secondary" onclick="loadPaperTrades(this)">Refresh paper trades</button>
      <div id="paperTrades" class="results"></div>
      <pre id="paperRaw">No paper trades loaded.</pre>
    </section>

    <section class="card wide">
      <h2>What this stage does</h2>
      <div class="metrics">
        <div class="metric">Market data<b>Read-only</b></div>
        <div class="metric">Signal engine<b>Deterministic</b></div>
        <div class="metric">Risk engine<b>Guardrailed</b></div>
        <div class="metric">Execution<b>Disabled</b></div>
        <div class="metric">Persistence<b>None yet</b></div>
      </div>
      <p class="muted">API documentation: <a href="/docs">/docs</a>. Paper trades currently live only in the running process and disappear if the service restarts.</p>
    </section>
  </div>
</main>
<div id="toast" class="toast"></div>

<script>
async function getJson(url, options) {
  const r = await fetch(url, options);
  const text = await r.text();
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch { data = {detail:text || 'Empty response'}; }
  return {r, data};
}
function show(id, value) {
  const el=document.getElementById(id);
  el.textContent=typeof value==="string" ? value : JSON.stringify(value,null,2);
  el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
}
function setBusy(button, busy, label='Processing…') {
  if(!button)return;
  if(busy) {
    if(!button.dataset.originalLabel) button.dataset.originalLabel=button.textContent;
    button.disabled=true; button.classList.add('loading'); button.textContent=label;
  } else {
    button.disabled=false; button.classList.remove('loading');
    if(button.dataset.originalLabel) button.textContent=button.dataset.originalLabel;
  }
}
function setStatus(id, text, type='active') {
  const el=document.getElementById(id); if(!el)return;
  el.textContent=text; el.className='action-status '+type;
}
function toast(message, type='success') {
  const el=document.getElementById('toast'); el.textContent=message; el.className='toast show '+type;
  clearTimeout(window.modelXToastTimer);
  window.modelXToastTimer=setTimeout(()=>el.className='toast',2600);
}
async function loadHealth(button) {
  setBusy(button,true,'Checking…'); setStatus('healthStatus','Checking system health…');
  try {
    const {data}=await getJson('/health'); show('health',data);
    setStatus('healthStatus',data.status==='ok'?'System healthy':'System check returned a warning',data.status==='ok'?'success':'error');
  } catch(e) { setStatus('healthStatus','Health check failed','error'); toast('Health check failed','error'); }
  finally { setBusy(button,false); }
}
async function searchStock(button) {
  const q=document.getElementById('query').value.trim(); if(!q)return;
  setBusy(button,true,'Searching…'); setStatus('analysisStatus','Searching NSE…');
  const {r,data}=await getJson('/api/market/search?q='+encodeURIComponent(q));
  const box=document.getElementById('searchResults'); box.innerHTML='';
  if(!r.ok){show('searchResults',data);setBusy(button,false);setStatus('analysisStatus',data.detail||'Search failed','error');return;}
  (data.results||[]).forEach(item=>{
    const div=document.createElement('div'); div.className='result';
    div.innerHTML='<strong>'+item.tradingsymbol+'</strong><br><span class="muted">'+(item.name||'')+'</span>';
    div.onclick=()=>selectStock(item); box.appendChild(div);
  });
  if(!data.results?.length) box.textContent='No matching NSE equity found.';
  setBusy(button,false); setStatus('analysisStatus',data.results?.length?'Search complete':'No matching equity found',data.results?.length?'success':'error');
}
function selectStock(item){
  window.modelXSelected=item;
  window.modelXCouncil=null;
  document.getElementById('token').value=item.instrument_token;
  document.getElementById('selected').textContent=item.tradingsymbol+' — '+(item.name||'');
  document.getElementById('paperSymbol').value=item.tradingsymbol;
}
async function analyze(button){
  const token=document.getElementById('token').value;
  if(!token){show('analysisResult',{error:'Search and select a stock first'});return;}
  setBusy(button,true,'Analyzing…'); setStatus('analysisStatus','Fetching market data and calculating indicators…');
  const {r,data}=await getJson('/api/analysis/'+encodeURIComponent(token)+'?interval=day');
  show('analysisResult',data);
  if(!r.ok){setBusy(button,false);setStatus('analysisStatus',data.detail||'Analysis failed','error');toast(data.detail||'Analysis failed','error');return;}
  window.modelXAnalysis=data;
  document.getElementById('score').innerHTML='<div class="score">'+data.score+'/100</div><div class="signal">'+data.signal+'</div>';
  const v=data.latest||{};
  if(v.close){
    const atr=Number(v.atr14||0);
    document.getElementById('paperEntry').value=Number(v.close).toFixed(2);
    document.getElementById('paperStop').value=Math.max(0,Number(v.close)-1.5*atr).toFixed(2);
    document.getElementById('paperTarget').value=(Number(v.close)+3*atr).toFixed(2);
  }
  document.getElementById('metrics').innerHTML=[
    ['Regime',data.market_regime],['Data quality',data.data_quality?.status],
    ['Close',v.close],['RSI14',v.rsi14],['ATR%',v.atr_pct],
    ['Volume ratio',v.volume_ratio20]
  ].map(x=>'<div class="metric">'+x[0]+'<b>'+String(x[1]??'—')+'</b></div>').join('');
  const factors=[...(data.bullish_factors||[]).map(x=>'<div class="factor ok">✓ '+x+'</div>'),
                 ...(data.risks||[]).map(x=>'<div class="factor warn">⚠ '+x+'</div>')];
  document.getElementById('factors').innerHTML=factors.join('');
  setBusy(button,false); setStatus('analysisStatus','Analysis complete','success'); toast('Analysis completed','success');
}
async function runCouncil(button){
  const token=document.getElementById('token').value;
  if(!token){show('analysisResult',{error:'Search and select a stock first'});return;}
  setBusy(button,true,'Thinking…'); setStatus('analysisStatus','AI Council is processing… this may take a little while.');
  const selected=window.modelXSelected||{};
  const body={
    symbol:selected.trading_symbol||selected.tradingsymbol||document.getElementById('paperSymbol').value,
    instrument_key:token,
    news:[],
    sentiment:{}
  };
  const {r,data}=await getJson('/api/ai/council',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!r.ok){show('analysisResult',data);setBusy(button,false);setStatus('analysisStatus',data.detail||'AI Council failed','error');toast(data.detail||'AI Council failed','error');return;}
  window.modelXCouncil=data.council;
  const c=data.council;
  document.getElementById('score').innerHTML='<div class="score">'+c.final_rating+'/100</div><div class="signal">'+c.council.decision+' · AI Council</div>';
  const factors=[
    ...(c.council.strongest_evidence||[]).map(x=>'<div class="factor ok">✓ '+x+'</div>'),
    ...(c.council.risks||[]).map(x=>'<div class="factor warn">⚠ '+x+'</div>'),
    ...(c.devil_advocate.contradictions||[]).map(x=>'<div class="factor bad">✕ '+x+'</div>')
  ];
  document.getElementById('factors').innerHTML=factors.join('');
  show('analysisResult',c);
  setBusy(button,false); setStatus('analysisStatus','AI Council completed','success'); toast('AI Council completed','success');
}
async function scan(button){
  const symbols=document.getElementById('watchlist').value.trim(); if(!symbols)return;
  setBusy(button,true,'Scanning…'); setStatus('scanStatus','Scanning watchlist…');
  const {r,data}=await getJson('/api/analysis/scan?symbols='+encodeURIComponent(symbols));
  if(!r.ok){show('scanRaw',data);setBusy(button,false);setStatus('scanStatus',data.detail||'Scan failed','error');return;}
  const box=document.getElementById('scanResults'); box.innerHTML='';
  (data.results||[]).forEach(item=>{
    const div=document.createElement('div');div.className='result';
    div.innerHTML='<strong>'+item.symbol+'</strong><span class="pill">'+
      (item.score!==undefined?item.score+'/100':item.status)+'</span><br><span class="muted">'+
      (item.signal||item.message||'')+'</span>';
    box.appendChild(div);
  });
  show('scanRaw',data); setBusy(button,false); setStatus('scanStatus','Scan complete','success'); toast('Watchlist scan completed','success');
}
async function riskPlan(button){
  setBusy(button,true,'Calculating…');
  const p=new URLSearchParams({
    entry_price:document.getElementById('entry').value,
    stop_loss:document.getElementById('stop').value,
    target_price:document.getElementById('target').value,
    available_capital:document.getElementById('capital').value
  });
  const {data}=await getJson('/api/analysis/risk-plan?'+p.toString()); show('riskResult',data); setBusy(button,false); toast('Risk plan calculated','success');
}
async function openPaperTrade(button){
  setBusy(button,true,'Opening…'); setStatus('paperStatus','Validating paper trade against risk limits…');
  const p=new URLSearchParams({
    symbol:document.getElementById('paperSymbol').value,
    quantity:document.getElementById('paperQty').value,
    entry_price:document.getElementById('paperEntry').value,
    stop_loss:document.getElementById('paperStop').value,
    target_price:document.getElementById('paperTarget').value,
    available_capital:document.getElementById('paperCapital').value
  });
  const {data}=await getJson('/api/analysis/paper-trades?'+p.toString(),{method:'POST'});
  show('paperRaw',data); await loadPaperTrades(); setBusy(button,false); setStatus('paperStatus',data.trade?'Paper trade opened':'Paper trade request failed',data.trade?'success':'error'); if(data.trade) toast('Paper trade opened','success');
}
async function loadPaperTrades(button){
  const {data}=await getJson('/api/analysis/paper-trades');
  show('paperRaw',data);
  const box=document.getElementById('paperTrades'); box.innerHTML='';
  (data.trades||[]).forEach(t=>{
    const div=document.createElement('div');div.className='result';
    div.innerHTML='<strong>'+t.symbol+'</strong><span class="pill">'+t.status+'</span><br>'+
      '<span class="muted">Qty '+t.quantity+' · Entry '+t.entry_price+' · SL '+t.stop_loss+' · Target '+t.target_price+
      (t.realized_pnl!==null?' · P&L '+t.realized_pnl:'')+'</span>'+
    if(t.status==='OPEN'){
      const action=document.createElement('button');
      action.className='secondary';
      action.textContent='Mark price';
      action.onclick=()=>markTrade(t.trade_id);
      div.appendChild(action);
    }
    box.appendChild(div);
  });
  setBusy(button,false);
}
async function markTrade(id){
  const price=prompt('Current price / simulated exit price:'); if(price===null)return;
  const p=new URLSearchParams({price});
  const {data}=await getJson('/api/analysis/paper-trades/'+encodeURIComponent(id)+'/mark?'+p.toString(),{method:'POST'});
  show('paperRaw',data); await loadPaperTrades();
}
async function sendApproval(button){
  const token=document.getElementById('token').value;
  if(!token){show('analysisResult',{error:'Search and select a stock first'});return;}
  setBusy(button,true,'Sending…'); setStatus('analysisStatus','Sending approval email…');
  const ratingText=document.querySelector('#score .score')?.textContent||'0';
  const rating=window.modelXCouncil?.final_rating ?? parseInt(ratingText,10);
  const entry=parseFloat(document.getElementById('paperEntry').value);
  const stop=parseFloat(document.getElementById('paperStop').value);
  const target=parseFloat(document.getElementById('paperTarget').value);
  const quantity=parseInt(document.getElementById('paperQty').value,10);
  const riskPerShare=entry-stop;
  const riskReward=(target-entry)/riskPerShare;
  const capitalAtRisk=quantity*riskPerShare;
  const signal=window.modelXCouncil?.council?.decision||window.modelXAnalysis?.signal||document.querySelector('#score .signal')?.textContent||'BUY_CANDIDATE';
  const regime=window.modelXAnalysis?.market_regime||'RANGE_OR_TRANSITION';
  const p=new URLSearchParams({
    symbol:document.getElementById('paperSymbol').value,
    rating:String(rating),
    signal,
    market_regime:regime,
    entry_price:String(entry),
    stop_loss:String(stop),
    target_price:String(target),
    quantity:String(quantity),
    risk_reward:String(riskReward),
    capital_at_risk:String(capitalAtRisk),
    available_capital:document.getElementById('paperCapital').value
  });
  const {r,data}=await getJson('/api/approvals/send?'+p.toString(),{method:'POST'});
  show('analysisResult',data); setBusy(button,false);
  if(r.ok){setStatus('analysisStatus','Approval email sent','success');toast('Approval email sent','success');}
  else {setStatus('analysisStatus',data.detail||'Approval email failed','error');toast(data.detail||'Approval email failed','error');}
}
async function emailScan(button){
  const symbols=document.getElementById('watchlist').value.trim(); if(!symbols)return;
  setBusy(button,true,'Emailing…'); setStatus('scanStatus','Sending scan by email…');
  const {r,data}=await getJson('/api/analysis/email-scan?symbols='+encodeURIComponent(symbols),{method:'POST'});
  show('scanRaw',data); setBusy(button,false);
  if(r.ok){setStatus('scanStatus','Scan email sent','success');toast('Scan email sent','success');}
  else {setStatus('scanStatus',data.detail||'Email failed','error');toast(data.detail||'Email failed','error');}
}
loadHealth();
loadPaperTrades();
</script>
</body>
</html>
"""


def page() -> HTMLResponse:
    return HTMLResponse(PAGE)
