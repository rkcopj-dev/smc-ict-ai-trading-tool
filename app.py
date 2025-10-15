import os
import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from smc_fusion import run_smc_backtest
from telegram_alert import send_telegram_alert

app = FastAPI()

# Railway variables (API Key, Secret, Telegram setup)
DELTA_API_KEY = os.environ.get("DELTA_API_KEY")
DELTA_API_SECRET = os.environ.get("DELTA_API_SECRET")
DELTA_API_URL = os.environ.get("DELTA_API_URL", "https://api.delta.exchange/v2")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)

@app.post("/backtest", response_class=HTMLResponse)
async def backtest(symbol: str = Form(...), res: str = Form(...), days: int = Form(...)):
    import time
    now = int(time.time())
    start = now - days*86400
    url = f"{DELTA_API_URL}/history/candles"
    params = dict(symbol=symbol, resolution=res, start=start, end=now)
    headers = {"api-key": DELTA_API_KEY} if DELTA_API_KEY else {}
    candles = requests.get(url, params=params, headers=headers).json().get("result", [])
    # SMC logic!
    signals = run_smc_backtest(candles)
    res_html = f"<h3>Backtest Results for {symbol} ({res})</h3>"
    res_html += "<ul>"
    for sig in signals[-12:]:
        res_html += f"<li>{sig}</li>"
    res_html += "</ul>"
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, f"SMC {symbol} Signals: {', '.join(str(x) for x in signals[-3:])}")
    return HTMLResponse(content=res_html + "<a href='/'>Back</a>")

@app.get("/health")
def health():
    return {"status": "up"}
