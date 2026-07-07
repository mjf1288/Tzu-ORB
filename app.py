# app.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from public_client import PublicClient
from orb_engine import ORBEngine


# --- Configure Public client and engine ---

PUBLIC_BASE_URL = "https://api.public.com"  # adjust to actual base URL
PUBLIC_API_KEY = "YOUR_PUBLIC_API_KEY"      # inject via env in real use

universe = ["SPY", "QQQ", "AAPL", "MSFT"]   # initial trading universe

public_client = PublicClient(
    base_url=PUBLIC_BASE_URL,
    api_key=PUBLIC_API_KEY,
)

engine = ORBEngine(
    public_client=public_client,
    universe=universe,
    orb_minutes=30,
    routing_mode="paper",
)


# --- FastAPI app ---

app = FastAPI()


@app.get("/engine/state")
def engine_state():
    """
    JSON endpoint for the dashboard: ORB engine state.
    """
    return engine.to_dict()


DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Tzu ORB Desk</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {
      margin: 0;
      background: #05080c;
      color: #e8eef2;
      font-family: system-ui, -apple-system, BlinkMacSystemFont,
                   "SF Pro Text", "Helvetica Neue", sans-serif;
    }
    .wrap { min-height: 100vh; display: flex; flex-direction: column; }
    header {
      padding: 16px 24px 12px;
      border-bottom: 1px solid #233040;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    h1 { margin: 2px 0 6px; font-size: 22px; }
    .muted { color: #99a4ac; font-size: 13px; }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      background: #163138;
      color: #63a9b1;
    }
    main {
      padding: 16px 24px 20px;
      display: grid;
      grid-template-columns: 2fr 1.2fr 1.3fr;
      gap: 14px;
    }
    .card {
      background: #10151f;
      border-radius: 10px;
      border: 1px solid #233040;
      padding: 12px 14px 14px;
    }
    .card h2 { margin: 0 0 4px; font-size: 16px; }
    .card small {
      display: block;
      margin-bottom: 6px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #66707b;
    }
    .list { font-size: 12px; }
    .list div {
      display: flex;
      justify-content: space-between;
      padding: 3px 0;
      border-bottom: 1px solid #161f29;
    }
    .list div:last-child { border-bottom: none; }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 7px;
      border-radius: 999px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      background: #261d12;
      color: #deb35a;
    }
    .badge.bull { background: #13281b; color: #76bf8a; }
    .badge.bear { background: #2a1717; color: #d47171; }
    code {
      font-size: 10px;
      white-space: pre;
      line-height: 1.4;
      display: block;
      max-height: 260px;
      overflow: auto;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <span class="pill">tzu orb · public api</span>
        <h1>Opening range desk</h1>
        <p class="muted">Live ORB signals and routing state from the engine.</p>
      </div>
      <div>
        <div class="muted">Routing mode</div>
        <div id="routing_mode" style="font-size:18px; font-weight:600;">paper</div>
      </div>
    </header>
    <main>
      <section class="card">
        <small>Scanner</small>
        <h2>Signals</h2>
        <div class="list" id="signals_list"></div>
      </section>
      <section class="card">
        <small>Summary</small>
        <h2>Engine state</h2>
        <p class="muted">
          Proposals · <span id="proposals_val">0</span><br/>
          Staged orders · <span id="staged_val">0</span>
        </p>
      </section>
      <section class="card">
        <small>Debug</small>
        <h2>Raw JSON</h2>
        <code id="json_dump">{}</code>
      </section>
    </main>
  </div>
  <script>
    async function fetchState() {
      const r = await fetch('/engine/state');
      return await r.json();
    }

    function render(data) {
      document.getElementById('routing_mode').textContent =
        data.routing_mode || 'paper';
      document.getElementById('proposals_val').textContent =
        data.proposals ?? 0;
      document.getElementById('staged_val').textContent =
        data.staged_orders ?? 0;

      const signalsEl = document.getElementById('signals_list');
      signalsEl.innerHTML = '';
      (data.signals || []).forEach((s) => {
        const row = document.createElement('div');
        const dir = (s.direction || '').toLowerCase();
        const dirClass = dir === 'bull' ? 'bull' : dir === 'bear' ? 'bear' : '';
        row.innerHTML =
          '<span>' + s.symbol + '</span>' +
          '<span><span class="badge ' + dirClass + '">' +
          (s.direction || '') +
          '</span> · ' + (s.score || 0).toFixed(1) +
          '</span>';
        signalsEl.appendChild(row);
      });

      document.getElementById('json_dump').textContent =
        JSON.stringify(data, null, 2);
    }

    fetchState().then(render);
    // Optional: live updates
    // setInterval(() => fetchState().then(render), 5000);
  </script>
</body>
</html>
"""


@app.get("/")
def dashboard() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)
