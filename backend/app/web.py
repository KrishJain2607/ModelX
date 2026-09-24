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
      <button class="secondary" onclick="loadHealth()">Refresh status</button>
    </section>

    <section class="card">
      <h2>Stock search</h2>
      <p class="muted">Search NSE equities and select one for analysis.</p>
      <input id="query" placeholder="RELIANCE, TCS, HDFC..." onkeydown="if(event.key==='Enter') searchStock()">
      <button onclick="searchStock()">Search</button>
      <div id="searchResults" class="results"></div>
    </section>

    <section class="card">
      <h2>Selected stock analysis</h2>
      <div id="selected">No stock selected.</div>
      <input id="token" type="hidden">
      <button onclick="analyze()">Run analysis</button>
      <button class="secondary" onclick="sendApproval()">Send trade approval email</button>
      <div id="score"></div>
      <div id="metrics" class="metrics"></div>
      <div id="factors"></div>
      <pre id="analysisResult">No analysis run yet.</pre>
    </section>

    <section class="card">
      <h2>Watchlist scan</h2>
      <p class="muted">Maximum 10 NSE symbols. Results are ranked by technical score, not by predicted return.</p>
      <input id="watchlist" value="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK">
      <button onclick="scan()">Run scan</button>
      <button class="secondary" onclick="emailScan()">Email scan</button>
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
      <button onclick="riskPlan()">Calculate risk plan</button>
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
      <button onclick="openPaperTrade()">Open paper trade</button>
      <button class="secondary" onclick="loadPaperTrades()">Refresh paper trades</button>
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

<script>
async function getJson(url, options) {
  const r = await fetch(url, options);
  const data = await r.json();
  return {r, data};
}
function show(id, value) {
  const el=document.getElementById(id);
  el.textContent=typeof value==="string" ? value : JSON.stringify(value,null,2);
}
async function loadHealth() {
  const {data}=await getJson('/health'); show('health',data);
}
async function searchStock() {
  const q=document.getElementById('query').value.trim(); if(!q)return;
  const {r,data}=await getJson('/api/market/search?q='+encodeURIComponent(q));
  const box=document.getElementById('searchResults'); box.innerHTML='';
  if(!r.ok){show('searchResults',data);return;}
  (data.results||[]).forEach(item=>{
    const div=document.createElement('div'); div.className='result';
    div.innerHTML='<strong>'+item.tradingsymbol+'</strong><br><span class="muted">'+(item.name||'')+'</span>';
    div.onclick=()=>selectStock(item); box.appendChild(div);
  });
  if(!data.results?.length) box.textContent='No matching NSE equity found.';
}
function selectStock(item){
  document.getElementById('token').value=item.instrument_token;
  document.getElementById('selected').textContent=item.tradingsymbol+' — '+(item.name||'');
  document.getElementById('paperSymbol').value=item.tradingsymbol;
}
async function analyze(){
  const token=document.getElementById('token').value;
  if(!token){show('analysisResult',{error:'Search and select a stock first'});return;}
  const {r,data}=await getJson('/api/analysis/'+encodeURIComponent(token)+'?interval=day');
  show('analysisResult',data);
  if(!r.ok)return;
  document.getElementById('score').innerHTML='<div class="score">'+data.score+'/100</div><div class="signal">'+data.signal+'</div>';
  const v=data.latest_values||{};
  document.getElementById('metrics').innerHTML=[
    ['Regime',data.market_regime],['Data quality',data.data_quality],
    ['Close',v.close],['RSI14',v.rsi14],['ATR%',v.atr_pct],
    ['Volume ratio',v.volume_ratio]
  ].map(x=>'<div class="metric">'+x[0]+'<b>'+String(x[1]??'—')+'</b></div>').join('');
  const factors=[...(data.bullish_factors||[]).map(x=>'<div class="factor ok">✓ '+x+'</div>'),
                 ...(data.risks||[]).map(x=>'<div class="factor warn">⚠ '+x+'</div>')];
  document.getElementById('factors').innerHTML=factors.join('');
}
async function scan(){
  const symbols=document.getElementById('watchlist').value.trim(); if(!symbols)return;
  const {r,data}=await getJson('/api/analysis/scan?symbols='+encodeURIComponent(symbols));
  if(!r.ok){show('scanRaw',data);return;}
  const box=document.getElementById('scanResults'); box.innerHTML='';
  (data.results||[]).forEach(item=>{
    const div=document.createElement('div');div.className='result';
    div.innerHTML='<strong>'+item.symbol+'</strong><span class="pill">'+
      (item.score!==undefined?item.score+'/100':item.status)+'</span><br><span class="muted">'+
      (item.signal||item.message||'')+'</span>';
    box.appendChild(div);
  });
  show('scanRaw',data);
}
async function riskPlan(){
  const p=new URLSearchParams({
    entry_price:document.getElementById('entry').value,
    stop_loss:document.getElementById('stop').value,
    target_price:document.getElementById('target').value,
    available_capital:document.getElementById('capital').value
  });
  const {data}=await getJson('/api/analysis/risk-plan?'+p.toString()); show('riskResult',data);
}
async function openPaperTrade(){
  const p=new URLSearchParams({
    symbol:document.getElementById('paperSymbol').value,
    quantity:document.getElementById('paperQty').value,
    entry_price:document.getElementById('paperEntry').value,
    stop_loss:document.getElementById('paperStop').value,
    target_price:document.getElementById('paperTarget').value,
    available_capital:document.getElementById('paperCapital').value
  });
  const {data}=await getJson('/api/analysis/paper-trades?'+p.toString(),{method:'POST'});
  show('paperRaw',data); await loadPaperTrades();
}
async function loadPaperTrades(){
  const {data}=await getJson('/api/analysis/paper-trades');
  show('paperRaw',data);
  const box=document.getElementById('paperTrades'); box.innerHTML='';
  (data.trades||[]).forEach(t=>{
    const div=document.createElement('div');div.className='result';
    div.innerHTML='<strong>'+t.symbol+'</strong><span class="pill">'+t.status+'</span><br>'+
      '<span class="muted">Qty '+t.quantity+' · Entry '+t.entry_price+' · SL '+t.stop_loss+' · Target '+t.target_price+
      (t.realized_pnl!==null?' · P&L '+t.realized_pnl:'')+'</span>'+
      (t.status==='OPEN'?'<button class="secondary" onclick="markTrade(\\''+t.trade_id+'\\')">Mark price</button>':'');
    box.appendChild(div);
  });
}
async function markTrade(id){
  const price=prompt('Current price / simulated exit price:'); if(price===null)return;
  const p=new URLSearchParams({price});
  const {data}=await getJson('/api/analysis/paper-trades/'+encodeURIComponent(id)+'/mark?'+p.toString(),{method:'POST'});
  show('paperRaw',data); await loadPaperTrades();
}
async function sendApproval(){
  const token=document.getElementById('token').value;
  if(!token){show('analysisResult',{error:'Search and select a stock first'});return;}
  const ratingText=document.querySelector('#score .score')?.textContent||'0';
  const rating=parseInt(ratingText,10);
  const entry=parseFloat(document.getElementById('paperEntry').value);
  const stop=parseFloat(document.getElementById('paperStop').value);
  const target=parseFloat(document.getElementById('paperTarget').value);
  const quantity=parseInt(document.getElementById('paperQty').value,10);
  const riskPerShare=entry-stop;
  const riskReward=(target-entry)/riskPerShare;
  const capitalAtRisk=quantity*riskPerShare;
  const signal=document.querySelector('#score .signal')?.textContent||'BUY_CANDIDATE';
  const p=new URLSearchParams({
    symbol:document.getElementById('paperSymbol').value,
    rating:String(rating),
    signal,
    market_regime:'BULLISH_TREND',
    entry_price:String(entry),
    stop_loss:String(stop),
    target_price:String(target),
    quantity:String(quantity),
    risk_reward:String(riskReward),
    capital_at_risk:String(capitalAtRisk)
  });
  const {data}=await getJson('/api/approvals/send?'+p.toString(),{method:'POST'});
  show('analysisResult',data);
}
async function emailScan(){
  const symbols=document.getElementById('watchlist').value.trim(); if(!symbols)return;
  const {data}=await getJson('/api/analysis/email-scan?symbols='+encodeURIComponent(symbols),{method:'POST'});
  show('scanRaw',data);
}
loadHealth();
loadPaperTrades();
</script>
</body>
</html>
"""


def page() -> HTMLResponse:
    return HTMLResponse(PAGE)
