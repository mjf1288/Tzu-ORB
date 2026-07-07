from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from public_client import PublicClient
from orb_engine import ORBEngine


# --- Configure your Public client & ORB engine ---

PUBLIC_BASE_URL = "https://api.public.com"
PUBLIC_API_KEY = "YOUR_PUBLIC_API_KEY"  # TODO: put your real key or read from env

universe = ["SPY", "QQQ", "AAPL", "MSFT"]

public_client = PublicClient(
    base_url=PUBLIC_BASE_URL,
    api_key=I54u3RPUYoWGcso4NW51Nl8bqAAkC7pa,
)

engine = ORBEngine(
    public_client=public_client,
    universe=universe,
    orb_minutes=30,
    routing_mode="paper",  # change to 'live' when you’re ready
)

# --- Create the FastAPI app ---

app = FastAPI()


# --- ORB engine endpoints ---

@app.get("/engine/state")
def engine_state():
    """
    Returns the current state of the ORB engine,
    including any generated signals.
    """
    return engine.to_dict()


# --- Simple HTML dashboard (ORB Desk) ---

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
  <head>
    <title>ORB Desk</title>
    <style>
      body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; background: #050816; color: #e5e7eb; }
      h1 { font-size: 2rem; margin-bottom: 0.5rem; }
      p  { color: #9ca3af; }
      table { border-collapse: collapse; width: 100%; margin-top: 1.5rem; }
      th, td { border-bottom: 1px solid #1f2937; padding: 0.5rem 0.75rem; text-align: left; }
      th { background: #111827; color: #e5e7eb; font-weight: 500; }
      tr:nth-child(even) { background: #030712; }
      .pill { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; }
      .pill-long { background: #064e3b; color: #bbf7d0; }
      .pill-short { background: #7f1d1d; color: #fecaca; }
      .pill-neutral { background: #374151; color: #e5e7eb; }
    </style>
  </head>
  <body>
    <h1>ORB Desk</h1>
    <p>Live view of ORB signals powered by your Public client.</p>

    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Side</th>
          <th>Entry</th>
          <th>Stop</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody id="signals-body">
        <tr>
          <td colspan="5">Loading signals…</td>
        </tr>
      </tbody>
    </table>

    <script>
      async function refreshSignals() {
        try {
          const res = await fetch("/engine/state");
          const data = await res.json();

          const tbody = document.getElementById("signals-body");
          tbody.innerHTML = "";

          const signals = data.signals || [];

          if (!signals.length) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 5;
            td.textContent = "No signals yet.";
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
          }

          for (const s of signals) {
            const tr = document.createElement("tr");

            const sideClass =
              s.side === "LONG" ? "pill pill-long"
              : s.side === "SHORT" ? "pill pill-short"
              : "pill pill-neutral";

            tr.innerHTML = `
              <td>${s.symbol || ""}</td>
              <td><span class="${sideClass}">${s.side || ""}</span></td>
              <td>${s.entry_price ?? ""}</td>
              <td>${s.stop_price ?? ""}</td>
              <td>${s.timestamp || ""}</td>
            `;
            tbody.appendChild(tr);
          }
        } catch (err) {
          const tbody = document.getElementById("signals-body");
          tbody.innerHTML = "";
          const tr = document.createElement("tr");
          const td = document.createElement("td");
          td.colSpan = 5;
          td.textContent = "Error loading engine state.";
          tr.appendChild(td);
          tbody.appendChild(tr);
        }
      }

      refreshSignals();
      setInterval(refreshSignals, 5000);
    </script>
  </body>
</html>
"""


@app.get("/")
def dashboard() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)
