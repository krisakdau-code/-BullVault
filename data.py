# data.py
import time
import requests
import pandas as pd
import streamlit as st

BASE = "https://api.bitkub.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bitkub.com/",
    "Origin": "https://www.bitkub.com",
    "Connection": "keep-alive",
}

# ความยาววินาทีต่อ 1 แท่งของ Native Resolution
RES_SEC = {
    "1": 60,
    "5": 300,
    "15": 900,
    "60": 3600,
    "240": 14400,
    "1D": 86400,
}

# ไทม์เฟรมพื้นฐานที่ดึงตรงได้จาก Bitkub
NATIVE_TF = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "1h": "60",
    "4h": "240",
    "1d": "1D",
}

# ไทม์เฟรมที่ต้องสร้างขึ้นมาเอง: (ไทม์เฟรมฐาน, pandas resample rule)
DERIVED_TF = {
    "3m":  ("1m",  "3min"),
    "30m": ("15m", "30min"),
    "2h":  ("1h",  "2h"),
    "6h":  ("1h",  "6h"),
    "12h": ("4h",  "12h"),
    "1w":  ("1d",  "1W-MON"),
}


@st.cache_resource
def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def to_tv_sym(sym: str) -> str:
    s = sym.upper().strip()
    return f"{s[4:]}_THB" if s.startswith("THB_") else s


def _fetch_bitkub_chunk(sym: str, res: str, frm: int, to: int) -> list:
    """ดึงข้อมูล 1 ช่วงเวลา รองรับทั้ง endpoint tradingview และ v3"""
    session = _session()
    
    # 1. ลองดึงผ่าน endpoint tradingview/history มาตรฐาน
    try:
        url = f"{BASE}/tradingview/history"
        params = {"symbol": to_tv_sym(sym), "resolution": res, "from": frm, "to": to}
        r = session.get(url, params=params, timeout=15)
        if r.status_code == 200:
            j = r.json()
            if j.get("s") == "ok" and j.get("t"):
                n = min(len(j["t"]), len(j["c"]))
                return list(zip(j["t"][:n], j["o"][:n], j["h"][:n], j["l"][:n], j["c"][:n], j.get("v", [0] * n)[:n]))
    except Exception:
        pass

    # 2. กรณี endpoint แรกไม่ตอบสนอง ให้ลองสำรองผ่าน /api/v3/market/tradingview
    try:
        url = f"{BASE}/api/v3/market/tradingview"
        params = {"sym": to_tv_sym(sym), "int": res, "frm": frm, "to": to}
        r = session.get(url, params=params, timeout=15)
        if r.status_code == 200:
            j = r.json()
            if j.get("s") == "ok" and j.get("t"):
                n = min(len(j["t"]), len(j["c"]))
                return list(zip(j["t"][:n], j["o"][:n], j["h"][:n], j["l"][:n], j["c"][:n], j.get("v", [0] * n)[:n]))
    except Exception:
        pass

    return []


@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlcv(symbol: str, tf: str = "1h", bars: int = 5000) -> pd.DataFrame:
    """เดินถอยหลังทีละช่วงเพื่อดึงข้อมูลย้อนหลังให้ยาวที่สุดตามที่ต้องการ"""
    base_tf, rule = DERIVED_TF.get(tf, (tf, None))
    res = NATIVE_TF.get(base_tf, "60")
    sec_per_bar = RES_SEC.get(res, 3600)
    
    bars_per_call = 1000
    step = sec_per_bar * bars_per_call

    to_ts = int(time.time())
    rows, seen = [], set()
    empty_streak = 0

    # ปรับโควต้าแท่งฐานที่ต้องดึง (หากเป็น Timeframe แปลง ต้องคูณเผื่อเพื่อนำมา Resample)
    target_fetch_bars = bars * 2 if rule else bars

    while len(rows) < target_fetch_bars:
        chunk = _fetch_bitkub_chunk(symbol, res, to_ts - step, to_ts)
        if not chunk:
            empty_streak += 1
            if empty_streak >= 3:  # ว่าง 3 รอบติด แปลว่าสุดข้อมูลย้อนหลังตั้งแต่เข้ากระดานเทรดแล้ว
                break
            to_ts -= step
            continue

        empty_streak = 0
        new_candles = [c for c in chunk if c[0] not in seen]
        if not new_candles:
            break

        seen.update(c[0] for c in new_candles)
        rows.extend(new_candles)
        to_ts = min(c[0] for c in chunk) - 1
        time.sleep(0.08)  # ป้องกัน Rate limit

    if not rows:
        return pd.DataFrame()

    rows.sort(key=lambda x: x[0])
    df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # แปลงเวลาเป็น Datetime ใน Timezone ไทย
    df["dt"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert("Asia/Bangkok")
    df = df.set_index("dt").drop_duplicates()

    # ทำ Resample สำหรับ Timeframe พิเศษ เช่น 30m, 2h, 1w
    if rule:
        kw = {"label": "left", "closed": "left"}
        if str(rule).endswith(("min", "h", "m")):
            kw["origin"] = "epoch"

        df = df.resample(rule, **kw).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna(subset=["close"]).reset_index()
        df["time"] = df["dt"]
    else:
        df = df.reset_index()
        df["time"] = df["dt"]

    return df[["time", "open", "high", "low", "close", "volume"]].tail(bars).reset_index(drop=True)


# ==================== BINANCE API (ขุดย้อนหลังยาวเทียบเท่ากัน) ====================
BINANCE_ENDPOINTS = [
    "https://data-api.binance.vision/api/v3/klines",
    "https://api1.binance.com/api/v3/klines",
    "https://api.binance.com/api/v3/klines"
]

BINANCE_NATIVE_TF = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
    "1d": "1d", "3d": "3d", "1w": "1w"
}


@st.cache_data(ttl=45, show_spinner=False)
def fetch_binance_ohlcv(symbol: str, tf: str = "1h", bars: int = 5000) -> pd.DataFrame:
    """ดึงข้อมูล Binance ย้อนหลังแบบถอยหลังทีละช่วง ยาวสูงสุดตามที่ระบุ"""
    clean_sym = symbol.replace("_", "").upper()
    interval = BINANCE_NATIVE_TF.get(tf, "1h")

    all_dfs = []
    end_time = None
    session = _session()

    # วนดึงรอบละ 1,000 แท่ง
    loops = max(1, bars // 1000 + 1)
    for _ in range(loops):
        params = {"symbol": clean_sym, "interval": interval, "limit": 1000}
        if end_time:
            params["endTime"] = end_time

        chunk_data = None
        for base_url in BINANCE_ENDPOINTS:
            try:
                r = session.get(base_url, params=params, timeout=10).json()
                if isinstance(r, list) and len(r) > 0:
                    chunk_data = r
                    break
            except Exception:
                continue

        if not chunk_data:
            break

        df_chunk = pd.DataFrame(chunk_data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "q_vol", "trades", "tb_base", "tb_quote", "ignore"
        ])
        df_chunk["time"] = pd.to_datetime(df_chunk["open_time"], unit="ms", utc=True).dt.tz_convert("Asia/Bangkok")
        for col in ["open", "high", "low", "close", "volume"]:
            df_chunk[col] = pd.to_numeric(df_chunk[col], errors="coerce")

        df_chunk = df_chunk[["time", "open", "high", "low", "close", "volume"]].dropna()
        if df_chunk.empty:
            break

        all_dfs.append(df_chunk)
        oldest_open_time = int(chunk_data[0][0])
        if end_time and oldest_open_time >= end_time:
            break
        end_time = oldest_open_time - 1

        if len(df_chunk) < 500:
            break
        time.sleep(0.08)

    if not all_dfs:
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    df = df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df.tail(bars).reset_index(drop=True)