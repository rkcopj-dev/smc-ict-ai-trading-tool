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
    NEW_YORK = "NEW_YORK"
    CRYPTO_PRIME = "CRYPTO_PRIME"

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
        self.success_rate = (self.profitable_trades / self.total_trades) * 100
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

    def get_candles(self, symbol: str, resolution: str = "60", limit: int = 100) -> List[Dict]:
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
        if not self._is_valid_session():
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

    def _is_valid_session(self) -> bool:
        now = datetime.now()
        hour = now.hour
        # Tokyo: 5:30-13:30, NY: 19:00-01:00, Crypto Prime: 15:30-18:30
        if (5 <= hour < 13) or (15 <= hour < 18) or (hour >= 19) or (hour <= 1):
            return True
        return False

    def _generate_signal(
        self,
        symbol: str,
        price: float,
        ob: Optional[OrderBlock],
        fvg: Optional[FairValueGap]
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
                    risk = price - ob.price_low
                    target = price + (risk * Config.MIN_RISK_REWARD)
                if confidence > 0.65:
                    return FuturesSignal(
                        symbol=symbol,
                        trade_type=TradeType.FUTURES_LONG,
                        entry_price=price,
                        stop_loss=ob.price_low * 0.998,
                        target_price=target,
                        confidence=confidence,
                        leverage=Config.FUTURES_LEVERAGE,
                        session=SessionType.CRYPTO_PRIME,
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

# -------------------
#   WEB DASHBOARD (MAIN PAGE) - Hindi + English
# -------------------
@app.get("/", response_class=HTMLResponse)
def dashboard():
    current_hour = datetime.now().hour
    session_label = (
        '🌅 टोक्यो' if 5 <= current_hour < 13
        else '🏮 क्रिप्टो प्राइम' if 15 <= current_hour < 18
        else '🌃 न्यूयॉर्क' if current_hour >= 19 or current_hour <= 1
        else '😴 बंद'
    )
    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICT + SMC + Claude AI Futures Trading Dashboard</title>
    <style>
        body {{ font-family:'Arial',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;color:white;margin:0 }}
        .container{{ max-width:1200px;margin:0 auto;padding:20px; }}
        .header{{ text-align:center;margin-bottom:30px; }}
        .header h1{{ font-size:2.5em;margin-bottom:10px;text-shadow:2px 2px 4px rgba(0,0,0,0.3); }}
        .header p{{ font-size:1.2em;opacity:0.9; }}
        .stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px;}}
        .stat-card{{background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);border-radius:15px;padding:20px;text-align:center; border:1px solid rgba(255,255,255,0.2);}}
        .stat-card h3{{font-size:1.1em;margin-bottom:10px;opacity:0.8;}}
        .stat-card .value{{font-size:2em;font-weight:bold;}}
        .status-running{{color:#4CAF50}}
        .action-buttons{{display:flex;gap:15px;justify-content:center;margin:30px 0;}}
        .btn{{padding:12px 30px;background:rgba(255,255,255,0.2);border:none;border-radius:25px;color:white;cursor:pointer;transition:all 0.3s;}}
        .btn:hover{{background:rgba(255,255,255,0.3);transform:translateY(-2px);}}
        .trade-log{{background:rgba(0,0,0,0.2);border-radius:15px;padding:20px;margin-top:30px}}
        .trade-log h3{{margin-bottom:15px}}
        .log-entry{{background:rgba(255,255,255,0.1);padding:10px;margin:10px 0;border-radius:8px;}}
        .refresh{{animation:spin 1s linear infinite;}}
        @keyframes spin{{from{{transform:rotate(0deg);}}to{{transform:rotate(360deg);}}}}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ICT + SMC + Claude AI</h1>
            <p>Futures Trading Dashboard | राहुल यादव Strategy</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>सिस्टम स्थिति</h3>
                <div class="value status-running" id="system-status">●️ चल रहा है</div>
            </div>
            <div class="stat-card">
                <h3>सफलता दर</h3>
                <div class="value" id="success-rate">{trading_engine.ai_brain.success_rate:.1f}%</div>
            </div>
            <div class="stat-card">
                <h3>कुल ट्रेड्स</h3>
                <div class="value" id="total-trades">{trading_engine.ai_brain.total_trades}</div>
            </div>
            <div class="stat-card">
                <h3>सक्रिय ट्रेड्स</h3>
                <div class="value" id="active-trades">{len(active_trades)}</div>
            </div>
            <div class="stat-card">
                <h3>AI कॉन्फिडेंस</h3>
                <div class="value" id="ai-confidence">{trading_engine.ai_brain.dynamic_multiplier*100:.0f}%</div>
            </div>
            <div class="stat-card">
                <h3>वर्तमान सत्र</h3>
                <div class="value" id="current-session">{session_label}</div>
            </div>
        </div>
        <div class="action-buttons">
            <button class="btn" onclick="analyzeMarket()">📊 मार्केट का विश्लेषण करें</button>
            <button class="btn" onclick="refreshStats()">🔄 डेटा रिफ्रेश करें</button>
            <button class="btn" onclick="viewTrades()">📋 ट्रेड्स देखें</button>
        </div>
        <div class="trade-log">
            <h3>🎯 लाइव सिग्नल्स</h3>
            <div id="signal-log"><div class="log-entry">💡 सिस्टम तैयार है - BTC/USDT का विश्लेषण करने के लिए ऊपर का बटन दबाएं</div></div>
        </div>
    </div>
    <script>
        async function analyzeMarket() {{
            const btn = event.target;
            btn.innerHTML = '🔄 विश्लेषण कर रहे हैं...';
            btn.classList.add('refresh');
            try {{
                const response = await fetch('/analyze/BTCUSD');
                const data = await response.json();
                const logDiv = document.getElementById('signal-log');
                const now = new Date().toLocaleString('hi-IN');
                if (data.status === 'signal') {{
                    logDiv.innerHTML = `
                        <div class="log-entry" style="border-left: 4px solid #4CAF50;">
                            <strong>🎯 NEW SIGNAL - ${{data.data.symbol}}</strong><br>
                            📈 Type: ${{data.data.trade_type}}<br>
                            💰 Entry: $${{data.data.entry_price}}<br>
                            🛑 Stop: $${{data.data.stop_loss}}<br>
                            🎯 Target: $${{data.data.target_price}}<br>
                            🔥 Confidence: ${{(data.data.confidence*100).toFixed(1)}}%<br>
                            ⏰ Time: ${{now}}
                        </div>
                    `;
                }} else {{
                    logDiv.innerHTML = `
                        <div class="log-entry" style="border-left: 4px solid #FF9800;">
                            <strong>⏳ कोई सिग्नल नहीं</strong><br>
                            Current conditions don't meet ICT criteria<br>
                            ⏰ Checked: ${{now}}
                        </div>
                    `;
                }}
            }} catch (error) {{
                document.getElementById('signal-log').innerHTML = `
                    <div class="log-entry" style="border-left: 4px solid #F44336;">
                        <strong>❌ Error</strong><br>
                        ${{error.message}}<br>
                        Check API connection
                    </div>
                `;
            }}
            btn.innerHTML = '📊 मार्केट का विश्लेषण करें';
            btn.classList.remove('refresh');
        }}
        async function refreshStats() {{
            try {{
                const response = await fetch('/stats');
                const stats = await response.json();
                document.getElementById('total-trades').textContent = stats.total_trades;
                document.getElementById('success-rate').textContent = stats.success_rate.toFixed(1) + '%';
                document.getElementById('active-trades').textContent = stats.active_trades;
            }} catch (error) {{
                console.error('Failed to refresh stats:', error);
            }}
        }}
        function viewTrades() {{
            window.open('/stats', '_blank');
        }}
        setInterval(refreshStats, 30000);
    </script>
</body>
</html>
    """

@app.get("/api/status")
def api_status():
    return {
        "status": "running",
        "system": "ICT+SMC+Claude Futures AI",
        "success_rate": f"{trading_engine.ai_brain.success_rate:.1f}%",
        "trades": trading_engine.ai_brain.total_trades
    }

@app.get("/analyze/{symbol}")
def analyze(symbol: str):
    try:
        signal = trading_engine.analyze(symbol)
        if signal:
            trading_engine.telegram.send_signal(signal)
            active_trades[symbol] = signal.dict()
            return {"status": "signal", "data": signal.dict()}
        return {"status": "no_signal", "message": "No setup found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/close/{symbol}")
def close_trade(symbol: str, exit_price: float, profitable: bool):
    if symbol in active_trades:
        trading_engine.ai_brain.record_trade(profitable, "CRYPTO_PRIME")
        del active_trades[symbol]
        return {"status": "closed", "success_rate": trading_engine.ai_brain.success_rate}
    raise HTTPException(404, "Trade not found")

@app.get("/stats")
def stats():
    return {
        "total_trades": trading_engine.ai_brain.total_trades,
        "success_rate": trading_engine.ai_brain.success_rate,
        "active_trades": len(active_trades)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
