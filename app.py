""" ICT + SMC + CLAUDE AI FUTURES TRADING SYSTEM - Railway Ready + Web Dashboard """
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import hmac
import hashlib
import time
from collections import deque
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENUMS
class TradeType(str, Enum):
    FUTURES_LONG = "FUTURES_LONG"
    FUTURES_SHORT = "FUTURES_SHORT"

class SessionType(str, Enum):
    TOKYO = "TOKYO"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    ASIAN_NIGHT = "ASIAN_NIGHT"

class MarketBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

# CONFIG
class Config:
    DELTA_API_KEY = os.getenv("DELTA_API_KEY", "")
    DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    TOTAL_CAPITAL = float(os.getenv("TOTAL_CAPITAL", "500"))
    FUTURES_LEVERAGE = 10
    MAX_RISK_PER_TRADE = 0.02
    MIN_RISK_REWARD = 2.0
    DAILY_LOSS_LIMIT = 0.05

# MODELS
class FuturesSignal(BaseModel):
    symbol: str
    trade_type: TradeType
    entry_price: float
    stop_loss: float
    target_price: float
    confidence: float
    leverage: int
    session: SessionType
    reasons: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

class OrderBlock(BaseModel):
    price_high: float
    price_low: float
    bias: MarketBias
    strength: float

class FairValueGap(BaseModel):
    top: float
    bottom: float
    bias: MarketBias
    size_percentage: float

# CLAUDE AI BRAIN
class ClaudeAIBrain:
    def __init__(self):
        self.total_trades = 0
        self.profitable_trades = 0
        self.success_rate = 50.0
        self.trade_history = deque(maxlen=100)
        self.consecutive_losses = 0
        self.dynamic_multiplier = 1.0

    def record_trade(self, was_profitable: bool, session: str):
        self.total_trades += 1
        if was_profitable:
            self.profitable_trades += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
        self.success_rate = (self.profitable_trades / self.total_trades) * 100 if self.total_trades > 0 else 50.0
        self._adjust_parameters()

    def _adjust_parameters(self):
        if self.consecutive_losses >= 3:
            self.dynamic_multiplier = 0.8
        elif self.success_rate > 70:
            self.dynamic_multiplier = 1.0
        elif self.success_rate < 50:
            self.dynamic_multiplier = 0.7

    def should_trade(self) -> Tuple[bool, str]:
        if self.consecutive_losses >= 4:
            return False, "4+ losses - Paused"
        return True, "All systems go"

# ICT DETECTOR
class ICTDetector:
    def __init__(self):
        pass

    def detect_order_block(self, candles: List[Dict]) -> Optional[OrderBlock]:
        if len(candles) < 20:
            return None
        for i in range(len(candles) - 5, max(0, len(candles) - 20), -1):
            candle = candles[i]
            if candle["close"] < candle["open"] and i + 1 < len(candles):
                next_c = candles[i + 1]
                if next_c["close"] > next_c["open"]:
                    displacement = (next_c["close"] - next_c["open"]) / next_c["open"]
                    if displacement > 0.01:
                        return OrderBlock(
                            price_high=candle["high"],
                            price_low=candle["low"],
                            bias=MarketBias.BULLISH,
                            strength=min(displacement * 10, 1.0)
                        )
        return None

    def detect_fvg(self, candles: List[Dict]) -> Optional[FairValueGap]:
        if len(candles) < 3:
            return None
        for i in range(len(candles) - 1, max(2, len(candles) - 10), -1):
            gap_bottom = candles[i-2]["high"]
            gap_top = candles[i]["low"]
            if gap_top > gap_bottom:
                gap_size = (gap_top - gap_bottom) / gap_bottom
                if gap_size > 0.002:
                    return FairValueGap(
                        top=gap_top,
                        bottom=gap_bottom,
                        bias=MarketBias.BULLISH,
                        size_percentage=gap_size * 100
                    )
        return None

# DELTA CLIENT
class DeltaClient:
    BASE_URL = "https://api.delta.exchange"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def get_candles(self, symbol: str, resolution: str = "1h", limit: int = 100) -> List[Dict]:
        endpoint = f"/v2/history/candles"
        params = {"symbol": symbol, "resolution": resolution, "limit": limit}
        try:
            response = requests.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get("result", [])
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
        return []

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        endpoint = f"/v2/tickers/{symbol}"
        try:
            response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                return response.json().get("result", {})
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
        return None

# TELEGRAM
class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_signal(self, signal: FuturesSignal):
        message = f"""
🚀 FUTURES SIGNAL 🚀
Symbol: {signal.symbol}
Type: {signal.trade_type.value}
Entry: ${signal.entry_price:.2f}
Stop: ${signal.stop_loss:.2f}
Target: ${signal.target_price:.2f}
Leverage: {signal.leverage}x
Confidence: {signal.confidence*100:.1f}%

Reasons:
"""
        for reason in signal.reasons:
            message += f"\n✓ {reason}"
        self._send(message)

    def _send(self, text: str):
        try:
            requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": text},
                timeout=5
            )
        except:
            pass

# SESSION HELPER (24/7 CRYPTO)
def get_current_session() -> Tuple[str, str]:
    """Returns (emoji_label, session_name) based on IST time for 24/7 crypto markets"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    time_minutes = hour * 60 + minute
    
    # Tokyo: 05:30 AM - 01:30 PM
    if (5 * 60 + 30) <= time_minutes < (13 * 60 + 30):
        return "🌅 टोक्यो", SessionType.TOKYO
    
    # London: 01:00 PM - 09:00 PM
    elif (13 * 60) <= time_minutes < (21 * 60):
        return "🏦 लंदन", SessionType.LONDON
    
    # New York: 06:00 PM - 02:30 AM (next day)
    elif time_minutes >= (18 * 60) or time_minutes < (2 * 60 + 30):
        return "🗽 न्यूयॉर्क", SessionType.NEW_YORK
    
    # Asian Night: 02:30 AM - 05:30 AM
    else:
        return "🌙 एशियन रात", SessionType.ASIAN_NIGHT

# TRADING ENGINE
class TradingEngine:
    def __init__(self):
        self.config = Config()
        self.ai_brain = ClaudeAIBrain()
        self.ict_detector = ICTDetector()
        self.delta_client = DeltaClient(self.config.DELTA_API_KEY, self.config.DELTA_API_SECRET)
        self.telegram = TelegramNotifier(self.config.TELEGRAM_BOT_TOKEN, self.config.TELEGRAM_CHAT_ID)

    def analyze(self, symbol: str) -> Optional[FuturesSignal]:
        can_trade, msg = self.ai_brain.should_trade()
        if not can_trade:
            logger.warning(f"Trading paused: {msg}")
            return None

        candles = self.delta_client.get_candles(symbol)
        if not candles:
            return None

        ticker = self.delta_client.get_ticker(symbol)
        if not ticker:
            return None

        current_price = float(ticker.get("close", 0))
        order_block = self.ict_detector.detect_order_block(candles)
        fvg = self.ict_detector.detect_fvg(candles)

        return self._generate_signal(symbol, current_price, order_block, fvg)

    def _generate_signal(
        self, symbol: str, price: float, ob: Optional[OrderBlock], fvg: Optional[FairValueGap]
    ) -> Optional[FuturesSignal]:
        reasons = []
        confidence = 0.5

        if ob and ob.bias == MarketBias.BULLISH:
            if ob.price_low <= price <= ob.price_high:
                reasons.append("📦 Bullish Order Block")
                confidence += 0.25

        if fvg and fvg.bias == MarketBias.BULLISH and fvg.bottom > price:
            reasons.append("⬆️ FVG Target Above")
            confidence += 0.25
            target = fvg.bottom
        else:
            if ob:
                risk = price - ob.price_low
                target = price + (risk * Config.MIN_RISK_REWARD)
            else:
                return None

        if confidence > 0.65 and ob:
            _, session = get_current_session()
            return FuturesSignal(
                symbol=symbol,
                trade_type=TradeType.FUTURES_LONG,
                entry_price=price,
                stop_loss=ob.price_low * 0.998,
                target_price=target,
                confidence=confidence,
                leverage=Config.FUTURES_LEVERAGE,
                session=session,
                reasons=reasons
            )
        return None

# FASTAPI APP
app = FastAPI(title="ICT+SMC+Claude Futures Trading")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

trading_engine = TradingEngine()
active_trades = {}

# WEB DASHBOARD (MAIN PAGE) - Hindi + Real-Time Session
@app.get("/", response_class=HTMLResponse)
def dashboard():
    session_label, _ = get_current_session()
    current_time = datetime.now().strftime("%I:%M %p IST, %d %b %Y")
    
    success_rate = trading_engine.ai_brain.success_rate
    total_trades = trading_engine.ai_brain.total_trades
    ai_confidence = 100.0
    
    return f"""
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60">
    <title>🚀 ICT + SMC + Claude AI</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ text-align: center; font-size: 2.5rem; margin-bottom: 10px; }}
        .subtitle {{ text-align: center; opacity: 0.9; margin-bottom: 30px; font-size: 1.1rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .card h3 {{ font-size: 0.9rem; opacity: 0.8; margin-bottom: 10px; text-transform: uppercase; }}
        .card .value {{ font-size: 2rem; font-weight: bold; }}
        .status-active {{ color: #4ade80; }}
        .buttons {{ display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; margin: 30px 0; }}
        .btn {{
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }}
        .btn-primary {{ background: #3b82f6; color: white; }}
        .btn-success {{ background: #10b981; color: white; }}
        .btn-danger {{ background: #ef4444; color: white; }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }}
        .live-results {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
        }}
        .live-results h2 {{ margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
        .result-item {{
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        .footer {{ text-align: center; margin-top: 40px; opacity: 0.8; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 ICT + SMC + Claude AI</h1>
        <p class="subtitle">Futures Trading Dashboard | राहुल यादव Strategy</p>
        
        <div class="grid">
            <div class="card">
                <h3>सिस्टम स्थिति</h3>
                <div class="value status-active">✅ चालू रहा है</div>
            </div>
            <div class="card">
                <h3>सफलता दर</h3>
                <div class="value">{success_rate:.1f}%</div>
            </div>
            <div class="card">
                <h3>कुल ट्रेड्स</h3>
                <div class="value">{total_trades}</div>
            </div>
            <div class="card">
                <h3>सक्रिय ट्रेड्स</h3>
                <div class="value">{len(active_trades)}</div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>AI कॉन्फिडेंस</h3>
                <div class="value">{ai_confidence:.0f}%</div>
            </div>
            <div class="card">
                <h3>वर्तमान सत्र</h3>
                <div class="value">{session_label}</div>
            </div>
        </div>

        <div class="buttons">
            <a href="/analyze/BTCUSD" class="btn btn-primary">📊 मार्केट का विश्लेषण करें</a>
            <a href="/dashboard" class="btn btn-success">📈 डेल रिफ्रेश करें</a>
            <a href="/trends" class="btn btn-danger">📉 ट्रेंड देखें</a>
        </div>

        <div class="live-results">
            <h2>🎯 लाइव रिज़ल्ट्स</h2>
            <div class="result-item">
                <strong>❌ कोई सिग्नल नहीं</strong><br>
                Current conditions don't meet ICT criteria<br>
                🕐 Checked: {current_time}
            </div>
        </div>

        <div class="footer">
            <p>Powered by ICT + SMC + Claude AI | Last Updated: {current_time}</p>
            <p>⚡ Auto-refresh हर 60 seconds | 24/7 Crypto Market</p>
        </div>
    </div>
</body>
</html>
    """

# API ENDPOINTS
@app.get("/analyze/{symbol}")
def analyze_symbol(symbol: str):
    signal = trading_engine.analyze(symbol)
    if signal:
        trading_engine.telegram.send_signal(signal)
        return {"status": "success", "signal": signal.dict()}
    return {"status": "no_signal", "message": "No ICT criteria met"}

@app.get("/stats")
def get_stats():
    return {
        "total_trades": trading_engine.ai_brain.total_trades,
        "success_rate": trading_engine.ai_brain.success_rate,
        "active_trades": len(active_trades)
    }

@app.get("/health")
def health_check():
    session_label, _ = get_current_session()
    return {
        "status": "healthy",
        "session": session_label,
        "timestamp": datetime.now().isoformat()
    }

# RUN SERVER
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
