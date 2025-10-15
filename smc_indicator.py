# ---- BASE SMC/ICT/Structure Logic ----
def get_smc_signal(data):
    # data: [{'close':..., 'low':..., 'high':..., ...}]
    closes = [row["close"] for row in data if "close" in row]
    highs = [row["high"] for row in data if "high" in row]
    lows = [row["low"] for row in data if "low" in row]
    latest = data[-1] if data else {}
    # TODO: True ICT/SMC structure logic (BOS/CHoCH/FVG etc)
    return {
        "smc_side": "buy",  # placeholder (replace with BOS/CHoCH calc)
        "smc_high": max(highs) if highs else None,
        "smc_low": min(lows) if lows else None,
        "entry": latest.get("close", 0)
    }

# ---- Breakout/Volume/Custom Logic plugins (from PineScripts) ----
def get_breakout_signal(data):
    # Example: basic breakout (replace logic with true breakout rules from pine)
    closes = [row["close"] for row in data]
    return {"breakout": closes[-1] > max(closes[-10:-1]) if len(closes) > 11 else False}

def get_money_flow_signal(data):
    # Example: placeholder logic (replace with custom oscillator/MFI etc)
    volumes = [row.get("volume", 0) for row in data]
    avg_vol = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else 0
    return {"money_flow": volumes[-1] > avg_vol if volumes else False}

def get_volume_signal(data):
    # Example: placeholder logic (replace with VOLUME.txt based logic)
    volumes = [row.get("volume", 0) for row in data]
    return {"volume_spike": volumes[-1] > (sum(volumes[-10:]) / 10) if len(volumes) >= 10 else False}

# ---- Main Signal Fusion ----
def get_trade_signal(data):
    smc = get_smc_signal(data)
    breakout = get_breakout_signal(data)
    money_flow = get_money_flow_signal(data)
    volume = get_volume_signal(data)

    # Master-trade-signal: combines all (customize as per fusion model/risk rules)
    final_signal = {
        "side": "buy" if smc["smc_side"] == "buy" and breakout["breakout"] and money_flow["money_flow"] else "sell",
        "product_id": 101,  # TODO: Make dynamic, use mapping/config
        "size": 1,          # TODO: Make dynamic
        "entry": smc["entry"],
        "stop": smc["smc_low"] if smc["smc_side"] == "buy" else smc["smc_high"],
        "target": smc["smc_high"] if smc["smc_side"] == "buy" else smc["smc_low"],
        "details": {"smc": smc, "breakout": breakout, "money_flow": money_flow, "volume": volume}
    }
    return final_signal
