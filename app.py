from fastapi import FastAPI, Request
from smc_indicator import get_trade_signal
from delta_api import place_order
from telegram_alert import send_telegram_alert

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "SMC/ICT AI Tool running!"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    signal_data = get_trade_signal(data)
    result = place_order(signal_data)
    msg = (
        f"⏰ <b>SMC/ICT Trade Alert</b>\n"
        f"Signal: {signal_data['side']}\n"
        f"Entry: {signal_data['entry']}\n"
        f"SL: {signal_data['stop']}\n"
        f"TP: {signal_data['target']}\n"
        f"Exchange Status: {result}"
    )
    send_telegram_alert(msg)
    return result
