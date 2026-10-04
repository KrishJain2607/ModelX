from fastapi.responses import HTMLResponse

from app.config.settings import settings


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
    .auto-summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; margin:12px 0 16px; }
    .auto-hero { background:#0d1425; border:1px solid #293650; border-radius:14px; padding:14px; }
    .auto-hero .eyebrow { color:#8e9bb5; font-size:12px; text-transform:uppercase; letter-spacing:.06em; }
    .auto-hero .big { font-size:24px; font-weight:800; margin-top:4px; }
    .progress { height:9px; border-radius:99px; background:#202b42; overflow:hidden; margin-top:8px; }
    .progress > div { height:100%; background:#7187c7; width:0; transition:width .25s ease; }
    .decision { border-left:3px solid #52658d; padding:10px 12px; margin-top:8px; background:#0d1425; border-radius:8px; }
    .decision.buy { border-left-color:#67b87d; } .decision.watch { border-left-color:#d7ad57; } .decision.blocked { border-left-color:#a85d68; }
    .section-title { margin-top:18px; margin-bottom:6px; font-size:14px; font-weight:700; }
    .details { margin-top:12px; }
    .details summary { cursor:pointer; color:#9ca8c0; font-size:13px; }
    .small-note { font-size:12px; color:#7f8aa1; }
    .toast { position:fixed; right:18px; bottom:18px; z-index:20; max-width:360px; padding:12px 15px; border:1px solid #34415e; border-radius:12px; background:#121a2d; box-shadow:0 12px 35px rgba(0,0,0,.3); color:#e8ecf7; opacity:0; transform:translateY(12px); pointer-events:none; transition:opacity .2s ease, transform .2s ease; }
    .toast.show { opacity:1; transform:translateY(0); } .toast.success { border-color:#39704b; } .toast.error { border-color:#783d48; }
    @keyframes spin { to { transform:rotate(360deg); } }
    @keyframes flash { 0% { box-shadow:0 0 0 0 rgba(120,150,255,0); } 35% { box-shadow:0 0 0 5px rgba(120,150,255,.18); } 100% { box-shadow:0 0 0 0 rgba(120,150,255,0); } }
    @keyframes rise { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
    @media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms !important; transition-duration:.01ms !important; } }
    .autonomous-dashboard{padding:24px;background:linear-gradient(145deg,#0f172a 0%,#111b33 58%,#101827 100%)}
    .dashboard-heading{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;padding-bottom:20px;border-bottom:1px solid #263553}
    .dashboard-heading h2{font-size:26px;margin:5px 0 4px}.eyebrow{color:#7f9bd4;font-size:11px;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
    .dashboard-status{display:flex;align-items:center;gap:8px;border:1px solid #2d3b5a;background:#0a1222;border-radius:12px;padding:10px 13px;white-space:nowrap}
    .dashboard-status span:last-child{color:#8491aa;font-size:12px}.status-dot{width:9px;height:9px;border-radius:50%;background:#718096;box-shadow:0 0 0 4px rgba(113,128,150,.12)}
    .status-dot.good{background:#42d17d;box-shadow:0 0 0 4px rgba(66,209,125,.12)}.status-dot.warn{background:#f2b84b;box-shadow:0 0 0 4px rgba(242,184,75,.12)}
    .kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin:18px 0 12px}.kpi-card{position:relative;overflow:hidden;min-height:108px;padding:15px;border:1px solid #293754;border-radius:13px;background:#0c1527;box-shadow:0 8px 24px rgba(0,0,0,.12)}
    .kpi-card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:#64748b}.accent-blue:before{background:#5b8def}.accent-purple:before{background:#9b7bf5}.accent-cyan:before{background:#38bdf8}.accent-green:before{background:#45c77a}.accent-amber:before{background:#e9b949}.accent-red:before{background:#e86d7a}
    .kpi-label{color:#8f9bb3;font-size:11px;text-transform:uppercase;letter-spacing:.08em}.kpi-value{font-size:24px;font-weight:850;margin-top:8px;letter-spacing:-.03em}.kpi-foot{color:#64718a;font-size:11px;margin-top:5px}
    .dashboard-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}.panel{border:1px solid #293754;border-radius:13px;padding:16px;background:#0b1425}.panel-title{display:flex;justify-content:space-between;color:#b8c3d7;font-size:13px;font-weight:700}.panel-title span:last-child{color:#8ca8e5}
    .big-progress{height:10px;border-radius:99px;background:#1c2942;overflow:hidden;margin:12px 0 15px}.big-progress>div{height:100%;width:0;border-radius:99px;background:linear-gradient(90deg,#4f7eea,#6f9cff);transition:width .45s ease}
    .mini-grid,.scan-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.mini-grid div,.scan-meta div{padding:9px;border-radius:9px;background:#101b30}.mini-grid span,.scan-meta span{display:block;color:#65728b;font-size:10px;text-transform:uppercase;letter-spacing:.05em}.mini-grid b,.scan-meta b{display:block;margin-top:4px;font-size:15px}
    .insight-strip{margin-top:12px;padding:14px 16px;border:1px solid #293754;border-radius:13px;background:#0b1425}.insight-title{font-size:12px;font-weight:800;color:#aab7ce;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}.pipeline{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
    .pipe{padding:11px 12px;border-radius:9px;background:#101b30;border:1px solid #24324d}.pipe b{display:block;font-size:20px}.pipe span{color:#68758d;font-size:11px}.pipe.buy{border-color:#315d49;background:#0e211a}.pipe.buy b{color:#69d494}.pipe.watch{border-color:#66542b;background:#201b0f}.pipe.watch b{color:#efc15a}.pipe.no{border-color:#473243;background:#1d1420}.pipe.no b{color:#d39ab9}.pipe.err{border-color:#5a3138;background:#201216}.pipe.err b{color:#ed8894}
    .section-header{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin-top:22px;margin-bottom:10px}.section-header h3,.rules-panel h3{margin:4px 0 0;font-size:18px}.section-header.compact{margin-top:20px}
    .decision-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.decision-card{padding:13px;border-radius:11px;border:1px solid #293754;background:#0c1527}.decision-card.buy{border-left:3px solid #4ac77c}.decision-card.watch{border-left:3px solid #e2b64d}.decision-card.blocked{border-left:3px solid #9b6170}.decision-top{display:flex;justify-content:space-between;gap:10px;align-items:center}.decision-symbol{font-size:16px;font-weight:850}.decision-rating{font-weight:800;color:#93b0ef}.decision-card p{margin:7px 0 0;font-size:12px}.decision-explain{color:#9ba8be}
    .candidate-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.candidate-card{border:1px solid #293754;border-radius:11px;background:#0c1527;padding:13px}.candidate-head{display:flex;justify-content:space-between;align-items:center}.candidate-score{font-size:18px;font-weight:850}.score-track{height:6px;border-radius:99px;background:#1c2942;margin:10px 0;overflow:hidden}.score-track i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#5b8def,#58c98a)}.candidate-card p{font-size:12px;margin:4px 0}.candidate-card .tag{display:inline-block;padding:4px 7px;border-radius:99px;background:#15223a;color:#8ea8d9;font-size:10px;font-weight:700;margin-top:5px}
    .trade-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.trade-card{border:1px solid #293754;border-radius:11px;background:#0c1527;padding:14px}.trade-head{display:flex;justify-content:space-between;align-items:center}.trade-head strong{font-size:17px}.open-badge{color:#68d692;background:#10261b;border:1px solid #285c3e;border-radius:99px;padding:4px 8px;font-size:10px;font-weight:800}.trade-values{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:11px}.trade-values div{background:#101b30;padding:8px;border-radius:8px}.trade-values span{display:block;color:#68758d;font-size:9px;text-transform:uppercase}.trade-values b{display:block;margin-top:3px;font-size:12px}
    .rules-panel{display:grid;grid-template-columns:260px 1fr;gap:18px;margin-top:20px;padding:16px;border:1px solid #293754;border-radius:13px;background:#0b1425}.rules-list{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.rule{padding:10px;border-radius:9px;background:#101b30;color:#a7b3c8;font-size:12px}.rule strong{color:#edf2ff}.dashboard-refresh{max-width:210px;margin-top:13px}
    .report-placeholder{padding:18px;border:1px dashed #33425f;border-radius:12px;color:#74819a;background:#0d1425}.analysis-report{margin-top:13px}.analysis-banner{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px;border-radius:12px;background:#0d1729;border:1px solid #293754}.analysis-score{font-size:34px;font-weight:900}.analysis-signal{font-weight:800;color:#8eaceb}.analysis-copy{font-size:12px;color:#98a5bb;max-width:680px}.analysis-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:9px}.analysis-kpi{padding:10px;border:1px solid #293754;border-radius:9px;background:#0d1425}.analysis-kpi span{display:block;color:#68758d;font-size:10px;text-transform:uppercase}.analysis-kpi b{display:block;margin-top:4px;font-size:15px}.analysis-columns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:9px}.analysis-list{padding:12px;border-radius:10px;background:#0d1425;border:1px solid #293754}.analysis-list h4{margin:0 0 7px;font-size:12px;text-transform:uppercase;letter-spacing:.06em}.analysis-list div{font-size:12px;padding:7px 0;border-bottom:1px solid #202b42}.analysis-list div:last-child{border-bottom:0}
    @media(max-width:1000px){.kpi-grid{grid-template-columns:repeat(3,1fr)}.candidate-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:700px){.dashboard-heading{display:block}.dashboard-status{margin-top:12px;width:max-content}.kpi-grid,.dashboard-grid,.decision-grid,.candidate-grid,.trade-grid,.analysis-columns{grid-template-columns:1fr}.mini-grid,.scan-meta{grid-template-columns:repeat(2,1fr)}.pipeline,.rules-list{grid-template-columns:1fr 1fr}.rules-panel{grid-template-columns:1fr}.trade-values{grid-template-columns:repeat(2,1fr)}.analysis-kpis{grid-template-columns:repeat(2,1fr)}}
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
    <div class="badge">VERSION __MODELX_VERSION__ · LIVE TRADING: OFF</div>
  </section>

  <div class="grid">
    <section class="card">
      <h2>System status</h2>
      <p class="muted">Current provider, authentication and safety state.</p>
      <details class="details"><summary>Technical response</summary><pre id="health">Checking...</pre></details>
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
      <div id="analysisNarrative" class="analysis-report"><div class="report-placeholder">Run an analysis to see the plain-English market readout.</div></div>
    </section>

    <section class="card">
      <h2>Watchlist scan</h2>
      <p class="muted">Maximum 10 NSE symbols. Results are ranked by technical score, not by predicted return.</p>
      <input id="watchlist" value="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK">
      <div id="scanStatus" class="action-status">Ready.</div>
      <button onclick="scan(this)">Run scan</button>
      <button class="secondary" onclick="emailScan(this)">Email scan</button>
      <div id="scanResults" class="results"></div>
      <details class="details"><summary>Technical scan response</summary><pre id="scanRaw">No scan run yet.</pre></details>
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
      <details class="details"><summary>Technical risk response</summary><pre id="riskResult">No risk plan calculated.</pre></details>
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
      <details class="details"><summary>Technical paper-trade response</summary><pre id="paperRaw">No paper trades loaded.</pre></details>
    </section>


    <section class="card wide autonomous-dashboard">
      <div class="dashboard-heading">
        <div><div class="eyebrow">MODELX AUTONOMOUS DESK</div><h2>Paper Trading Command Center</h2><p class="muted">A Power BI-style snapshot of capital, decisions, risk and the latest market intelligence — written for humans, not machines.</p></div>
        <div class="dashboard-status"><span id="autoLiveDot" class="status-dot"></span><strong id="autoMode">Loading…</strong><span id="autoModeNote">Checking configuration</span></div>
      </div>
      <div class="kpi-grid">
        <div class="kpi-card accent-blue"><div class="kpi-label">Total paper capital</div><div class="kpi-value" id="kpiCapital">—</div><div class="kpi-foot">Configured test bankroll</div></div>
        <div class="kpi-card accent-purple"><div class="kpi-label">Funds deployed</div><div class="kpi-value" id="kpiUsed">—</div><div class="kpi-foot" id="kpiUsedPct">0% of capital</div></div>
        <div class="kpi-card accent-cyan"><div class="kpi-label">Funds available</div><div class="kpi-value" id="kpiAvailable">—</div><div class="kpi-foot">Ready for new positions</div></div>
        <div class="kpi-card accent-green"><div class="kpi-label">Open trades</div><div class="kpi-value" id="kpiOpen">—</div><div class="kpi-foot" id="kpiOpenNote">Maximum configured positions</div></div>
        <div class="kpi-card accent-amber"><div class="kpi-label">Realised P&amp;L</div><div class="kpi-value" id="kpiPnl">—</div><div class="kpi-foot" id="kpiPnlNote">Closed trades only</div></div>
        <div class="kpi-card accent-red"><div class="kpi-label">Capital at risk</div><div class="kpi-value" id="kpiRisk">—</div><div class="kpi-foot">If all open stops are hit</div></div>
      </div>
      <div class="dashboard-grid">
        <div class="panel"><div class="panel-title"><span>Portfolio utilisation</span><span id="utilisationLabel">—</span></div><div class="big-progress"><div id="utilisationBar"></div></div><div class="mini-grid">
          <div><span>Open exposure</span><b id="exposureValue">—</b></div><div><span>Closed trades</span><b id="closedTradesValue">—</b></div><div><span>Winning trades</span><b id="winningTradesValue">—</b></div><div><span>Losing trades</span><b id="losingTradesValue">—</b></div>
        </div></div>
        <div class="panel"><div class="panel-title"><span>Scan progress</span><span id="scanProgressLabel">Not started</span></div><div class="big-progress"><div id="autoProgressBar"></div></div><div class="scan-meta">
          <div><span>Stocks processed</span><b id="processedValue">—</b></div><div><span>Technical candidates</span><b id="candidateValue">—</b></div><div><span>AI evaluations</span><b id="aiEvaluatedValue">—</b></div><div><span>Last cycle</span><b id="lastCycleValue">—</b></div>
        </div></div>
      </div>
      <div class="insight-strip"><div class="insight-title">Decision pipeline</div><div class="pipeline" id="decisionPipeline"></div></div>
      <div class="section-header"><div><div class="eyebrow">LATEST INTELLIGENCE</div><h3>What ModelX is seeing</h3></div><div class="small-note" id="lastUpdated">Waiting for first scan</div></div>
      <div id="autoDecisions" class="decision-grid"></div>
      <div class="section-header compact"><div><div class="eyebrow">TOP TECHNICAL SETUPS</div><h3>Stocks worth watching</h3></div><div class="small-note">Ranked by technical evidence, not predicted returns</div></div>
      <div id="autoCandidates" class="candidate-grid"></div>
      <div class="section-header compact"><div><div class="eyebrow">LIVE PAPER BOOK</div><h3>Open positions</h3></div><div class="small-note">Paper only · no broker order</div></div>
      <div id="autoTrades" class="trade-grid"></div>
      <div class="rules-panel"><div><div class="eyebrow">WEEKEND TEST RULES</div><h3>How a trade gets through the gate</h3></div><div id="autoRules" class="rules-list">Loading test rules…</div></div>
      <div id="automationStatus" class="action-status">Loading autonomous status…</div>
      <button class="secondary dashboard-refresh" onclick="loadAutomation(this)">Refresh dashboard</button>
      <details class="details"><summary>Developer diagnostics</summary><pre id="automationRaw">No autonomous scan run yet.</pre></details>
    </section>

    <section class="card wide">
      <h2>What this stage does</h2>
      <div class="metrics">
        <div class="metric">Market data<b>Read-only</b></div>
        <div class="metric">Signal engine<b>Deterministic</b></div>
        <div class="metric">Risk engine<b>Guardrailed</b></div>
        <div class="metric">Execution<b>Disabled</b></div>
        <div class="metric">Persistence<b>Process state</b></div>
      </div>
      <p class="muted">API documentation: <a href="/docs">/docs</a>. This dashboard is paper-only and keeps broker execution disabled.</p>
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

async function loadAutomation(button){
  if(button)setBusy(button,true,'Refreshing…');
  try{
    const {r,data}=await getJson('/api/automation/status');
    if(!r.ok)throw new Error(data.detail||'Automation status failed');
    const last=data.last_scan||{}, weekend=Boolean(data.weekend_test_mode&&last.window_status==='WEEKEND_TEST'), active=data.enabled&&!data.live_trading_enabled;
    const tr=await getJson('/api/analysis/paper-trades'), trades=tr.data?.trades||[], open=trades.filter(t=>t.status==='OPEN'), closed=trades.filter(t=>String(t.status||'').startsWith('CLOSED_'));
    const capital=Number(data.paper_trading_capital||0), used=open.reduce((a,t)=>a+Number(t.entry_price||0)*Number(t.quantity||0),0), available=Math.max(0,capital-used), risk=open.reduce((a,t)=>a+Number(t.planned_capital_at_risk||0),0), pnl=closed.reduce((a,t)=>a+Number(t.realized_pnl||0),0), wins=closed.filter(t=>Number(t.realized_pnl||0)>0).length, losses=closed.filter(t=>Number(t.realized_pnl||0)<0).length, util=capital?Math.min(100,used/capital*100):0;
    const money=n=>'₹'+Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:2});
    document.getElementById('autoMode').textContent=active?(weekend?'PAPER · WEEKEND TEST':'PAPER'):'CHECK CONFIG';
    document.getElementById('autoModeNote').textContent=active?'Live broker execution is disabled':'Safety configuration needs attention';
    document.getElementById('autoLiveDot').className='status-dot '+(active?'good':'warn');
    document.getElementById('kpiCapital').textContent=money(capital);document.getElementById('kpiUsed').textContent=money(used);document.getElementById('kpiUsedPct').textContent=util.toFixed(1)+'% of capital deployed';document.getElementById('kpiAvailable').textContent=money(available);document.getElementById('kpiOpen').textContent=open.length;document.getElementById('kpiOpenNote').textContent='of '+data.max_open_positions+' max positions';document.getElementById('kpiPnl').textContent=(pnl>=0?'+':'')+money(pnl);document.getElementById('kpiPnl').style.color=pnl>0?'#69d494':pnl<0?'#ed8894':'#edf2ff';document.getElementById('kpiPnlNote').textContent=closed.length+' closed trade'+(closed.length===1?'':'s');document.getElementById('kpiRisk').textContent=money(risk);
    document.getElementById('utilisationLabel').textContent=util.toFixed(1)+'% deployed';document.getElementById('utilisationBar').style.width=util+'%';document.getElementById('exposureValue').textContent=money(used);document.getElementById('closedTradesValue').textContent=closed.length;document.getElementById('winningTradesValue').textContent=wins;document.getElementById('losingTradesValue').textContent=losses;
    const universe=Number(last.universe_ranked||0), processed=Number(last.processed||0), progress=universe?Math.min(100,processed/universe*100):0;
    document.getElementById('scanProgressLabel').textContent=universe?processed.toLocaleString('en-IN')+' / '+universe.toLocaleString('en-IN'):'Not started';document.getElementById('autoProgressBar').style.width=progress+'%';document.getElementById('processedValue').textContent=processed?processed.toLocaleString('en-IN'):'—';document.getElementById('candidateValue').textContent=last.technical_candidates??0;document.getElementById('aiEvaluatedValue').textContent=last.ai_candidates??0;document.getElementById('lastCycleValue').textContent=last.current_batch!==undefined?last.current_batch+'/'+(last.total_batches??'—'):'—';
    const buy=Number(last.council_buy_candidates??0),watch=Number(last.council_watch??0),no=Number(last.council_no_signal??0),err=Number(last.council_errors??0);
    document.getElementById('decisionPipeline').innerHTML=[['buy','BUY candidates',buy],['watch','WATCH',watch],['no','No signal',no],['err','AI issues',err]].map(x=>'<div class="pipe '+x[0]+'"><b>'+x[2]+'</b><span>'+x[1]+'</span></div>').join('');
    const decisions=last.decision_log||[];
    document.getElementById('autoDecisions').innerHTML=decisions.length?decisions.slice().reverse().slice(0,8).map(d=>{const cls=d.trade_eligible?'buy':d.decision==='WATCH'?'watch':'blocked',rating=d.ai_rating==null?'AI unavailable':'AI confidence '+d.ai_rating+'/100',human=d.trade_eligible?'Passed the ModelX gates and is eligible for a paper position.':d.decision==='WATCH'?'Worth watching, but it did not clear the full paper-trade gate.':'ModelX kept this out of the paper book after reviewing the evidence.';return '<div class="decision-card '+cls+'"><div class="decision-top"><span class="decision-symbol">'+d.symbol+'</span><span class="decision-rating">'+rating+'</span></div><p><strong>'+String(d.decision||'REVIEW').replaceAll('_',' ')+'</strong> · Technical score '+(d.technical_score??'—')+'/100</p><p class="decision-explain">'+human+'</p><p class="small-note">'+(d.reason||'No additional explanation recorded.')+'</p></div>'}).join(''):'<div class="muted">No completed AI decisions yet. The next autonomous batch will appear here.</div>';
    const candidates=last.top_technical||[];
    document.getElementById('autoCandidates').innerHTML=candidates.length?candidates.slice(0,9).map(x=>{const score=Number(x.technical_score||0),interpretation=score>=70?'Strong technical setup':score>=50?'Mixed but worth watching':'Early / weak technical setup';return '<div class="candidate-card"><div class="candidate-head"><strong>'+x.symbol+'</strong><span class="candidate-score">'+score+'/100</span></div><div class="score-track"><i style="width:'+Math.min(100,score)+'%"></i></div><p>'+interpretation+'</p><span class="tag">'+String(x.signal||'NO SIGNAL').replaceAll('_',' ')+'</span> <span class="tag">'+String(x.market_regime||'UNKNOWN').replaceAll('_',' ')+'</span></div>'}).join(''):'<div class="muted">No qualifying technical candidates in the latest scan.</div>';
    document.getElementById('autoTrades').innerHTML=open.length?open.map(t=>{const notional=Number(t.entry_price||0)*Number(t.quantity||0);return '<div class="trade-card"><div class="trade-head"><strong>'+t.symbol+'</strong><span class="open-badge">OPEN · PAPER</span></div><div class="trade-values"><div><span>Qty</span><b>'+t.quantity+'</b></div><div><span>Capital used</span><b>'+money(notional)+'</b></div><div><span>Stop loss</span><b>₹'+Number(t.stop_loss||0).toFixed(2)+'</b></div><div><span>Target</span><b>₹'+Number(t.target_price||0).toFixed(2)+'</b></div></div><p class="small-note">Entry ₹'+Number(t.entry_price||0).toFixed(2)+' · Planned downside ₹'+Number(t.planned_capital_at_risk||0).toFixed(2)+' · Risk/reward '+Number(t.planned_risk_reward||0).toFixed(2)+'</p></div>'}).join(''):'<div class="muted">No open paper positions. The book is currently flat.</div>';
    const wt=data.weekend_min_technical_score??'—',wf=data.weekend_min_final_rating??'—',ww=data.weekend_watch_trade_min_rating??'—';
    document.getElementById('autoRules').innerHTML=weekend?'<div class="rule"><strong>1 · Technical screen</strong><br>At least <strong>'+wt+'/100</strong> technical evidence.</div><div class="rule"><strong>2 · AI judgement</strong><br>BUY candidates need <strong>'+wf+'/100</strong> or higher.</div><div class="rule"><strong>3 · Risk gate</strong><br>Position size, exposure, open positions and daily loss limits must pass.</div><div class="rule"><strong>WATCH exception</strong><br>AI and technical evidence must both reach <strong>'+ww+'/100</strong>.</div>':'<div class="rule"><strong>Normal automation</strong><br>Technical '+data.min_technical_score+'/100 · Final rating '+data.min_final_rating+'/100.</div>';
    const cycle=last.status==='COMPLETED'?'Scan complete':last.status==='BATCH_COMPLETE'?'Batch complete — continuing automatically':'No completed autonomous cycle yet';document.getElementById('lastUpdated').textContent=last.ist_time?'Last update · '+new Date(last.ist_time).toLocaleString('en-IN'):'Waiting for first scan';setStatus('automationStatus',cycle+' · '+(last.window_status||'—'),last.status==='COMPLETED'||last.status==='BATCH_COMPLETE'?'success':'active');show('automationRaw',data);
  }catch(e){setStatus('automationStatus',e.message||'Automation status failed','error');toast(e.message||'Automation status failed','error')}finally{if(button)setBusy(button,false)}
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
  if(!r.ok){document.getElementById('analysisNarrative').innerHTML='<div class="report-placeholder">'+(data.detail||'Analysis failed')+'</div>';setBusy(button,false);setStatus('analysisStatus',data.detail||'Analysis failed','error');toast(data.detail||'Analysis failed','error');return;}
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
  const regimeText=String(data.market_regime||'UNKNOWN').replaceAll('_',' '),score=Number(data.score||0),outlook=score>=70?'The technical picture is strong enough to keep this stock high on the research list.':score>=50?'The evidence is mixed. ModelX sees some positives, but this is not a clean setup.':'The technical evidence is currently weak, so ModelX would stay cautious.',quality=data.data_quality?.status?String(data.data_quality.status).replaceAll('_',' '):'Not specified';
  document.getElementById('analysisNarrative').innerHTML='<div class="analysis-banner"><div><div class="eyebrow">PLAIN-ENGLISH MARKET READ</div><div class="analysis-signal">'+String(data.signal||'REVIEW').replaceAll('_',' ')+' · '+regimeText+'</div><div class="analysis-copy">'+outlook+'</div></div><div class="analysis-score">'+score+'/100</div></div><div class="analysis-kpis"><div class="analysis-kpi"><span>Latest price</span><b>₹'+Number(v.close||0).toFixed(2)+'</b></div><div class="analysis-kpi"><span>Momentum (RSI)</span><b>'+Number(v.rsi14||0).toFixed(1)+'</b></div><div class="analysis-kpi"><span>Volatility (ATR)</span><b>'+Number(v.atr_pct||0).toFixed(2)+'%</b></div><div class="analysis-kpi"><span>Data quality</span><b>'+quality+'</b></div></div><div class="analysis-columns"><div class="analysis-list"><h4>Why ModelX likes it</h4>'+((data.bullish_factors||[]).length?data.bullish_factors.map(x=>'<div class="ok">✓ '+x+'</div>').join(''):'<div class="muted">No major positive factor was recorded.</div>')+'</div><div class="analysis-list"><h4>What could go wrong</h4>'+((data.risks||[]).length?data.risks.map(x=>'<div class="warn">⚠ '+x+'</div>').join(''):'<div class="muted">No major risk flag was recorded.</div>')+'</div></div>';
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
  const decision=String(c.council?.decision||'REVIEW').replaceAll('_',' '),aiScore=Number(c.final_rating||0);
  document.getElementById('analysisNarrative').innerHTML='<div class="analysis-banner"><div><div class="eyebrow">AI COUNCIL READOUT</div><div class="analysis-signal">'+decision+'</div><div class="analysis-copy">'+(c.council?.summary||'The council has reviewed the available technical and market evidence.')+'</div></div><div class="analysis-score">'+aiScore+'/100</div></div><div class="analysis-columns"><div class="analysis-list"><h4>Strongest evidence</h4>'+((c.council?.strongest_evidence||[]).length?c.council.strongest_evidence.map(x=>'<div class="ok">✓ '+x+'</div>').join(''):'<div class="muted">No strongest-evidence notes returned.</div>')+'</div><div class="analysis-list"><h4>Devil’s advocate</h4>'+((c.devil_advocate?.contradictions||[]).length?c.devil_advocate.contradictions.map(x=>'<div class="bad">✕ '+x+'</div>').join(''):'<div class="muted">No major contradiction was returned.</div>')+'</div></div>';
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
      (t.realized_pnl!==null?' · P&L '+t.realized_pnl:'')+'</span>';
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
loadAutomation();
setInterval(loadAutomation, 30000);
</script>
</body>
</html>
"""


def page() -> HTMLResponse:
    return HTMLResponse(PAGE.replace("__MODELX_VERSION__", settings.modelx_version))
