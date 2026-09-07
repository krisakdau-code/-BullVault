# fib_tools.py
import pandas as pd

def auto_fib_retracement(df, lookback=5, window=120):
    if df is None or df.empty or len(df) < 5: return None
    cols = {c.lower(): c for c in df.columns}
    h_col, l_col = cols.get("high", "high"), cols.get("low", "low")
    if h_col not in df.columns or l_col not in df.columns: return None
    sub = df.tail(window).reset_index(drop=True)
    sh, sl = float(sub[h_col].max()), float(sub[l_col].min())
    hi, li = sub[h_col].idxmax(), sub[l_col].idxmin()
    uptrend = (li < hi)
    rng = sh - sl
    if rng <= 0: return None
    ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    levels = {lv: (sh - lv * rng if uptrend else sl + lv * rng) for lv in ratios}
    return {"uptrend": uptrend, "swing_high": sh, "swing_low": sl, "range_val": rng, "range_pct": (rng / sl * 100) if sl else 0.0, "levels": levels, "high_idx": hi, "low_idx": li}

def trend_based_fib_extension(df, lookback=5, window=120):
    if df is None or df.empty or len(df) < 5: return None
    cols = {c.lower(): c for c in df.columns}
    h, l = cols.get("high", "high"), cols.get("low", "low")
    if h not in df.columns or l not in df.columns: return None
    sub = df.tail(window).reset_index(drop=True)
    hi, li = sub[h].idxmax(), sub[l].idxmin()
    uptrend = (li < hi)
    try:
        if uptrend:
            b = float(sub[h].iloc[hi])
            p1 = sub.iloc[:hi]
            a = float(p1[l].min()) if not p1.empty else float(sub[l].iloc[li])
            p2 = sub.iloc[hi:]
            c = float(p2[l].min()) if not p2.empty else b * 0.95
        else:
            b = float(sub[l].iloc[li])
            p1 = sub.iloc[:li]
            a = float(p1[h].max()) if not p1.empty else float(sub[h].iloc[hi])
            p2 = sub.iloc[li:]
            c = float(p2[h].max()) if not p2.empty else b * 1.05
    except:
        a, b, c = float(sub[l].min()), float(sub[h].max()), float(sub[l].min())
    r = [0.618, 1.0, 1.272, 1.414, 1.618, 2.0, 2.618, 3.618]
    wl = abs(b - a) or b * 0.1
    targets = {x: (c + x * wl if uptrend else c - x * wl) for x in r}
    return {"uptrend": uptrend, "targets": targets, "point_a": a, "point_b": b, "point_c": c}

def current_fib_zone(last_close, fib):
    if not fib or "levels" not in fib: return None
    lvl = fib["levels"]
    up, sh, sl = fib["uptrend"], fib["swing_high"], fib["swing_low"]
    span = abs(sh - sl)
    pos = max(0.0, min(1.0, (last_close - min(sh, sl)) / span)) if span > 0 else 0.5
    lbls = [
        (0.0, "Bull Run Super Zone (> 0.0)" if up else "Bear Run Crash Zone (< 0.0)"),
        (0.236, "โซนยอดดอย (0.000 - 0.236)" if up else "โซนก้นเหว (0.000 - 0.236)"),
        (0.382, "โซนแนวรับตื้น (0.236 - 0.382)" if up else "โซนแนวต้านตื้น (0.236 - 0.382)"),
        (0.5, "โซนพักฐานกลาง (0.382 - 0.500)" if up else "โซนสะสมกลางทาง (0.382 - 0.500)"),
        (0.618, "Golden Zone 🎯 (0.500 - 0.618)" if up else "Golden Resistance 🎯 (0.500 - 0.618)"),
        (0.786, "โซนรับลึกสะสมพลัง (0.618 - 0.786)" if up else "โซนต้านสำคัญระดับลึก (0.618 - 0.786)"),
        (1.0, "โซนก้นเหวเสี่ยงกลับตัว (0.786 - 1.000)" if up else "โซนทดสอบจุดสูงสุดเดิม (0.786 - 1.000)")
    ]
    p_vals = [lvl.get(x, last_close) for x, _ in lbls]
    # Find match
    if up:
        if last_close >= p_vals[0]: return {"label": lbls[0][1], "ratio": pos}
        for i in range(len(p_vals)-1):
            if p_vals[i] >= last_close >= p_vals[i+1]:
                return {"label": lbls[i+1][1], "ratio": pos}
        return {"label": "Breakdown ต่ำกว่าก้นเหว (< 1.0)", "ratio": pos}
    else:
        if last_close <= p_vals[0]: return {"label": lbls[0][1], "ratio": pos}
        for i in range(len(p_vals)-1):
            if p_vals[i] <= last_close <= p_vals[i+1]:
                return {"label": lbls[i+1][1], "ratio": pos}
        return {"label": "Breakout เหนือยอดสูงสุด (> 1.0)", "ratio": pos}

def near_golden_zone(last_close, fib):
    if not fib or "levels" not in fib: return False
    p5, p6 = fib["levels"].get(0.5), fib["levels"].get(0.618)
    if p5 is None or p6 is None: return False
    p_min, p_max = min(p5, p6), max(p5, p6)
    margin = (p_max - p_min) * 0.015
    return (p_min - margin) <= last_close <= (p_max + margin)

def fib_tp_target(last_close, ext, min_tp_pct=3.0, preferred_level=1.618):
    if not ext or "targets" not in ext or not ext["targets"]: return None
    targets, up = ext["targets"], ext["uptrend"]
    sorted_levels = sorted(targets.keys())
    tp_price = targets.get(preferred_level, last_close * 1.05)
    if up:
        for lvl in sorted_levels:
            price = targets[lvl]
            pct = ((price - last_close) / last_close * 100) if last_close else 0.0
            if price > last_close and pct >= min_tp_pct:
                preferred_level, tp_price = lvl, price
                break
        pct = ((tp_price - last_close) / last_close * 100) if last_close else 0.0
    else:
        for lvl in sorted_levels:
            price = targets[lvl]
            pct = ((last_close - price) / last_close * 100) if last_close else 0.0
            if price < last_close and pct >= min_tp_pct:
                preferred_level, tp_price = lvl, price
                break
        pct = ((last_close - tp_price) / last_close * 100) if last_close else 0.0
    return {"level": preferred_level, "tp_price": tp_price, "tp_pct": pct}

def fib_time_zones(df, lookback=5, window=120, num_zones=8):
    if df is None or df.empty or len(df) < 5: return []
    cols = {c.lower(): c for c in df.columns}
    h = cols.get("high", "high")
    sub = df.tail(window).reset_index(drop=True)
    hi = int(sub[h].idxmax()) if not sub.empty else 0
    fib_seq = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    zones = []
    for count in fib_seq[:num_zones]:
        target = len(df) - window + hi + count
        if target < len(df): zones.append(target)
    return zones
