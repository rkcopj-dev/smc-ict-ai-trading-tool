from fastapi import FastAPI, Request
from smc_fusion import get_trade_signal
from telegram_alert import send_telegram_alert   # <-- ये लाइन जोड़ें

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "SMC/ICT AI Tool running!"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    config = {"ailength": 10, "aimultiplier": 3.0}
    signal = get_trade_signal(data, config)
    # --- Telegram Alert Integration ---
    msg = (
        f"🪙 <b>Trade Signal:</b> {signal['side'].upper()}"
        f"\nEntry: {signal['entry']}"
        f"\nStop: {signal['stop']}"
        f"\nTarget: {signal['target']}"
        f"\n\nDetails: {signal['details']}"
    )
    send_telegram_alert(msg)
    return signal
