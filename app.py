from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
import requests
import time

app = FastAPI()

# -- LIVE DASHBOARD with Delta OHLC fetch form --
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return f"""
    <h2>Delta Exchange Backtest Dashboard</h2>
    <form action='/backtest' method='post'>
        <label>Market: </label>
        <select name="symbol">
            <option value="BTCUSD">BTCUSD</option>
            <option value="ETHUSD">ETHUSD</option>
        </select>
        <label>Resolution:</label>
        <select name="res">
            <option>1m</option><option>5m</option><option>1h</option><option>1d</option>
        </select>
        <label>Period (days):</label>
        <input name="days" type="number" value="7" min="1" max="180"/>
        <button>Run Backtest</button>
    </form>
    <div>
      <h3>Chart Links:</h3>
      <a href='https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT' target='_blank'>BTCUSDT Chart</a> |
      <a href='https://www.tradingview.com/chart/?symbol=BINANCE:ETHUSDT' target='_blank'>ETHUSDT Chart</a>
    </div>
    <br>
    <a href='/health'>Health API</a>
    """

# -- BACKTEST endpoint: fetch candles and run SMC-AI logic (sample) --
@app.post("/backtest", response_class=HTMLResponse)
async def backtest(symbol: str = Form(...), res: str = Form(...), days: int = Form(...)):
    # Calculate timestamps
    now = int(time.time())
    start = now - days*86400
    url = f"https://api.delta.exchange/v2/history/candles"
    params = dict(symbol=symbol, resolution=res, start=start, end=now)
    r = requests.get(url, params=params)
    data = r.json()
    candles = data["result"] if "result" in data and data["result"] else []
    # Simple SMC logic sample
    signals = []
    for i in range(1, len(candles)):
        if candles[i]["close"] > candles[i-1]["close"]:
            signals.append(f"Long at {candles[i]['close']} {candles[i]['timestamp']}")
        else:
            signals.append(f"Short at {candles[i]['close']} {candles[i]['timestamp']}")
    sigtxt = "<br>".join(signals[-10:]) if signals else "No signals/candles received."
    return f"""
    <h3>{symbol} [{res}], Last {days} days: {len(candles)} candles</h3>
    <div>Example signals (last 10):<br>{sigtxt}</div>
    <a href='/'>Back</a>
    """

@app.get("/health")
def health():
    return {"status": "up"}

# --- Real-Order/live trading endpoint सिर्फ manually add करें, API KEY/SECRET डालें (for extra security only run as local/admin/test, prod पर dummy रखे):
# @app.post('/order')...
