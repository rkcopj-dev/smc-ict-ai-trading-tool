from fastapi import FastAPI, Request
from smc_fusion import get_trade_signal

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "SMC/ICT AI Tool running!"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    config = {"ailength":10, "aimultiplier":3.0}  # Optional advanced config
    signal = get_trade_signal(data, config)
    return signal
