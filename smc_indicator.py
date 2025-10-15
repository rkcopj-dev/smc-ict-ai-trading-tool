def get_smc_structure(data):
    closes = [row["close"] for row in data]
    highs = [row["high"] for row in data]
    lows = [row["low"] for row in data]
    bos_up = closes[-2] < closes[-3] and closes[-1] > closes[-2] if len(closes)>=3 else False
    bos_down = closes[-2] > closes[-3] and closes[-1] < closes[-2] if len(closes)>=3 else False
    fvg_up = (lows[-1] > highs[-3]) if len(highs)>=3 else False
    fvg_down = (highs[-1] < lows[-3]) if len(lows)>=3 else False
    side = "buy" if bos_up or fvg_up else ("sell" if bos_down or fvg_down else "hold")
    return {
        "side": side,
        "bos_up": bos_up,
        "bos_down": bos_down,
        "fvg_up": fvg_up,
        "fvg_down": fvg_down,
        "entry": closes[-1] if closes else 0,
        "stop": min(lows) if lows else 0,
        "target": max(highs) if highs else 0
    }

def get_rahulyadav_ai(data, config):
    closes = [row["close"] for row in data]
    highs = [row["high"] for row in data]
    lows = [row["low"] for row in data]
    volumes = [row.get("volume", 0) for row in data]
    # AI adaptive SuperTrend
    length = config.get("ailength", 10)
    multiplier = config.get("aimultiplier", 3.0)
    atr = max([highs[i]-lows[i] for i in range(-length, 0)]) if len(highs) >= length else 0
    hl2 = (highs[-1]+lows[-1])/2 if highs and lows else 0
    upper = hl2 + multiplier*atr
    lower = hl2 - multiplier*atr
    supertrend = -1 if closes[-1] < lower else (1 if closes[-1] > upper else 0)
    # Session filter (active, prime hours)
    is_prime = config.get('session_active', True)
    # Volume Profile approx (big move if volume surge vs avg)
    avg_vol = sum(volumes[-20:-1])/19 if len(volumes)>=21 else 0
    vp_signal = volumes[-1] > 1.5*avg_vol if avg_vol else False
    # FVG confirmation merged
    ai_signal = (supertrend==1 and vp_signal and is_prime)
    return {
        "aitrend": supertrend,
        "vp_signal": vp_signal,
        "ai_signal": ai_signal,
        "entry": closes[-1] if closes else 0,
        "stop": lower if supertrend==1 else upper,
        "target": highs[-1] if supertrend==1 and highs else lows[-1] if supertrend==-1 and lows else closes[-1]
    }

# ----- FINAL FUSION CALL -----
def get_zero_to_millionaire_signal(data, config):
    smc_struct = get_smc_structure(data)
    ry_ai = get_rahulyadav_ai(data, config)
    if smc_struct["side"]=="buy" and ry_ai["ai_signal"]:
        final = "buy"
    elif smc_struct["side"]=="sell" and ry_ai["ai_signal"]:
        final = "sell"
    else:
        final = "hold"
    return {
        "side": final,
        "entry": ry_ai["entry"],
        "stop": ry_ai["stop"],
        "target": ry_ai["target"],
        "details": {"smc": smc_struct, "ry_ai": ry_ai}
    }
