from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
import requests, time

app = FastAPI()

TELEGRAM_CHAT_ID = "your_chat_id"
TELEGRAM_TOKEN = "your_bot_token"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def get_wallet_balance(api_key="", api_secret=""):
    # DEMO: Actual Delta API authentication/headers needed; sample below.
    # You must fill your keys; below is the public endpoint sample.
    r = requests.get("https://api.delta.exchange/v2/wallet/balances", headers={"api-key":api_key})
    return r.json()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return f"""
    <h1>SMC-AI PRO Dashboard</h1>
    <form action='/backtest' method='post'>
        <label>Market: </label>
        <select name="symbol">
            <option value="BTCUSD">BTCUSD</option>
            <option value="ETHUSD">ETHUSD</option>
        </select>
        <label>Resolution:</label>
        <select name="res">
            <option>1h</option><option>5m</option><option>1d</option>
        </select>
        <label>Period (days):</label>
        <input name="days" type="number" value="7"/>
        <button>Run SMC Backtest & Alert</button>
    </form>
    <form action='/balance' method='post'>
        <label>Check Delta Wallet Balance:</label>
        <input name="api_key" type="text" placeholder="API Key"/>
        <input name="api_secret" type="text" placeholder="API Secret"/>
        <button>Show Balance</button>
    </form>
    <div>
      <a href='/health'>Health API</a>
    </div>
    <div>
      <h3>Chart Links</h3>
      <a href='https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT'>BTCUSDT Chart</a> |
      <a href='https://www.tradingview.com/chart/?symbol=BINANCE:ETHUSDT'>ETHUSDT Chart</a>
    </div>
    """

@app.post("/backtest", response_class=HTMLResponse)
async def backtest(symbol: str = Form(...), res: str = Form(...), days: int = Form(...)):
    now = int(time.time())
    start = now - days*86400
    url = f"https://api.delta.exchange/v2/history/candles"
    params = dict(symbol=symbol, resolution=res, start=start, end=now)
    candles = requests.get(url, params=params).json().get("result", [])
    signals = []
    for i in range(1, len(candles)):
        c = candles[i]
        prev = candles[i-1]
        # यहाँ अपनी SMC-strategy apply करें
        if c["close"] > prev["close"]:
            signals.append(f"Long at {c['close']} {c['timestamp']}")
        else:
            signals.append(f"Short at {c['close']} {c['timestamp']}")
    sigtxt = "<br>".join(signals[-10:]) if signals else "No signals/candles received."
    send_telegram(f"SMC Backtest result for {symbol}: {sigtxt}")
    return f"<h3>{symbol} [{res}] Backtest:</h3><div>{sigtxt}</div><a href='/'>Back</a>"

@app.post("/balance", response_class=HTMLResponse)
async def balance(api_key: str = Form(...), api_secret: str = Form(...)):
    # Real credentials needed for actual request
    balance = get_wallet_balance(api_key, api_secret)
    return f"<h3>Wallet Balance:</h3><pre>{balance}</pre><a href='/'>Back</a>"

@app.get("/health")
def health():
    return {"status": "up"}
