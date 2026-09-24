# data/candles.py — Precision Historical Bars Fetcher
import time
import math
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

TV_HISTORY_URL = "https://api.bitkub.com/tradingview/history"
TH_TZ = timezone(timedelta(hours=7))

RESOLUTION_MAP = {
    "1m": "1", "5m": "5", "15m": "15", "30m": "15",
    "1h": "60", "2h": "60", "4h": "240",
    "1d": "1D", "1D": "1D", "D": "1D",
    "1w": "1D", "W": "1D",
}
RES_SECONDS = {"1": 60, "5": 300, "15": 900, "60": 3600, "240": 14400, "1D": 86400}
_BAR_CACHE: Dict[str, Dict] = {}
_CACHE_TTL = {"1D": 300, "240": 120, "60": 45, "15": 20, "5": 10, "1": 5}
_MAX_BARS_PER_CALL = 1000


def to_tv_symbol(symbol: str) -> str:
    """
    สำหรับ Bitkub /tradingview/history ต้องใช้ BASE_QUOTE เช่น PERP_THB
    """
    s = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
    if s.startswith("THB") and len(s) > 3:
        base = s[3:]
    elif s.endswith("THB"):
        base = s[:-3]
    else:
        base = s
    if not base:
        raise ValueError(f"แปลง symbol ไม่ได้: {symbol}")
    return f"{base}_THB"


def _request_bitkub(symbol_tv: str, resolution: str, frm: int, to: int) -> Optional[dict]:
    params = {"symbol": symbol_tv, "resolution": resolution, "from": frm, "to": to}
    for attempt in range(3):
        try:
            r = requests.get(TV_HISTORY_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            status = data.get("s")
            if status == "ok":
                return data
            if status == "no_data":
                nxt = data.get("nextTime")
                if nxt and attempt == 0:
                    span = to - frm
                    params["to"] = int(nxt)
                    params["from"] = int(nxt) - span
                    continue
                return None
        except Exception:
            pass
        time.sleep(0.4 * (attempt + 1))
    return None


def _to_bars(data: dict) -> List[Dict]:
    t = data.get("t") or []
    o, h, l, c = data.get("o") or [], data.get("h") or [], data.get("l") or [], data.get("c") or []
    v = data.get("v") or [0] * len(t)
    n = min(len(t), len(o), len(h), len(l), len(c))
    bars = []
    for i in range(n):
        try:
            hi, lo, cl = float(h[i]), float(l[i]), float(c[i])
        except (TypeError, ValueError):
            continue
        if not all(map(math.isfinite, (hi, lo, cl))) or cl <= 0 or hi <= 0 or lo <= 0:
            continue
        if hi < lo:
            hi, lo = lo, hi
        bars.append({
            "time": int(t[i]),
            "datetime": datetime.fromtimestamp(int(t[i]), TH_TZ),
            "open": float(o[i]),
            "high": hi,
            "low": lo,
            "close": cl,
            "volume": float(v[i]) if i < len(v) and v[i] is not None else 0.0,
        })
    bars.sort(key=lambda b: b["time"])
    dedup = {b["time"]: b for b in bars}
    return [dedup[k] for k in sorted(dedup)]


def fetch_bars(symbol: str, timeframe: str = "1D", limit: int = 385, use_cache: bool = True) -> List[Dict]:
    """ดึงแท่งเทียนระดับวันย้อนหลัง รองรับทั้ง Bitkub และ Binance"""
    res = RESOLUTION_MAP.get(timeframe, "1D")
    sym_upper = symbol.upper().replace("_", "")

    # กรณีเป็นคู่ Binance (USDT, BUSD, USDC)
    if any(sym_upper.endswith(x) for x in ["USDT", "BUSD", "USDC"]):
        try:
            r = requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym_upper}&interval=1d&limit={limit}", timeout=8)
            if r.status_code == 200:
                bars = []
                for b in r.json():
                    t_sec = int(b[0]) // 1000
                    bars.append({
                        "time": t_sec,
                        "datetime": datetime.fromtimestamp(t_sec, TH_TZ),
                        "open": float(b[1]),
                        "high": float(b[2]),
                        "low": float(b[3]),
                        "close": float(b[4]),
                        "volume": float(b[5]),
                    })
                return bars
        except Exception:
            pass

    # กรณีเป็นคู่ Bitkub
    sym_tv = to_tv_symbol(symbol)
    key = f"{sym_tv}|{res}|{limit}"
    ttl = _CACHE_TTL.get(res, 60)

    if use_cache:
        hit = _BAR_CACHE.get(key)
        if hit and (time.time() - hit["ts"] < ttl):
            return hit["bars"]

    sec = RES_SECONDS[res]
    to_ts = int(time.time())
    need = limit + 5
    collected: List[Dict] = []
    cursor_to = to_ts

    while need > 0:
        chunk = min(need, _MAX_BARS_PER_CALL)
        frm = cursor_to - chunk * sec
        data = _request_bitkub(sym_tv, res, frm, cursor_to)
        if not data:
            break
        bars = _to_bars(data)
        if not bars:
            break
        collected = bars + collected
        need -= len(bars)
        cursor_to = bars[0]["time"] - sec
        if len(bars) < chunk * 0.5:
            break
        time.sleep(0.15)

    dedup = {b["time"]: b for b in collected}
    out = [dedup[k] for k in sorted(dedup)][-limit:]
    if out:
        _BAR_CACHE[key] = {"ts": time.time(), "bars": out}
    return out


def fetch_daily_bars(symbol: str, limit: int = 385) -> List[Dict]:
    return fetch_bars(symbol, "1D", limit)