# app.py — Universal Trading Terminal (Hybrid Ultra Edition)
import concurrent.futures
import datetime
import json
import os
import time
import uuid

import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from ui.theme import apply_theme
from ui.sidebar import render_sidebar
from chart_builders import build_charts
from config import *
from data.rice_ohlcv import generate_rice_ohlcv
from ui.rice_tab import show_rice_dialog_modal
from ui.rice_tab import render_rice_tab
from ui.chart_settings_modal import show_chart_settings_dialog, init_settings_state
from drawing_chart import render_drawing_chart
from requests.adapters import HTTPAdapter
from streamlit_lightweight_charts_ntf import renderLightweightCharts
from technicals import compute_full_technicals, diamond_armor, fetch_market_analytics
from ui_components import (
    build_asset_icon_html,
    fetch_seasonality_svg,
    render_3_gauges_html,
    render_fibonacci_modal_content,
    render_market_modal_content,
    render_tv_clickable_tabs,
    render_tv_quote_card,
    render_panel_controls,
)
from urllib3.util.retry import Retry
from utils import _has_data, fmt_chg, fmt_price, fmt_vol

from symbols import (
    fetch_set_all_symbols,
    get_full_binance_symbols,
    get_full_bitkub_symbols,
    get_full_bybit_symbols,
    get_full_china_stocks,
    get_full_commodities,
    get_full_forex,
    get_full_gate_symbols,
    get_full_kucoin_symbols,
    get_full_mexc_symbols,
    get_full_okx_symbols,
    get_full_sp500_symbols,
    get_full_vietnam_symbols,
)

try:
    import symbols
except ImportError:
    symbols = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from fib_tools import (
        auto_fib_retracement,
        current_fib_zone,
        fib_time_zones,
        fib_tp_target,
        near_golden_zone,
        trend_based_fib_extension,
    )
except ImportError:
    auto_fib_retracement = None

# ──────────────────────────── CONFIG & THEME ────────────────────────────
st.set_page_config(
    page_title="Diamond Armor Universal",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_theme()

# ────────────────────────── PANEL STATE MANAGEMENT ──────────────────────────
if "panel_open" not in st.session_state:
    st.session_state["panel_open"] = True
if "panel_size" not in st.session_state:
    st.session_state["panel_size"] = "M"

GLOBAL_MARKET = "🌐 Global (Yahoo)"

TF = {
    "1m":  {"sec": 60,        "rule": "1min", "base": None, "yf_iv": "1m",  "yf_range": "7d"},
    "3m":  {"sec": 180,       "rule": "3min", "base": "1m", "yf_iv": "5m",  "yf_range": "60d"},
    "5m":  {"sec": 300,       "rule": "5min", "base": None, "yf_iv": "5m",  "yf_range": "60d"},
    "15m": {"sec": 900,       "rule": "15min","base": None, "yf_iv": "15m", "yf_range": "60d"},
    "30m": {"sec": 1800,      "rule": "30min","base": None, "yf_iv": "30m", "yf_range": "60d"},
    "1h":  {"sec": 3600,      "rule": "1h",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "2h":  {"sec": 7200,      "rule": "2h",   "base": "1h", "yf_iv": "60m", "yf_range": "730d"},
    "3h":  {"sec": 10800,     "rule": "3h",   "base": "1h", "yf_iv": "60m", "yf_range": "730d"},
    "4h":  {"sec": 14400,     "rule": "4h",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "6h":  {"sec": 21600,     "rule": "6h",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "8h":  {"sec": 28800,     "rule": "8h",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "12h": {"sec": 43200,     "rule": "12h",  "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "1d":  {"sec": 86400,     "rule": "1D",   "base": None, "yf_iv": "1d",  "yf_range": "10y"},
    "1w":  {"sec": 604800,    "rule": "1W",   "base": None, "yf_iv": "1wk", "yf_range": "10y"},
    "1M":  {"sec": 2592000,   "rule": "1ME",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
    "3M":  {"sec": 7776000,   "rule": "3ME",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
    "6M":  {"sec": 15552000,  "rule": "6ME",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
    "1Y":  {"sec": 31536000,  "rule": "1YE",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
}

TF_OPTIONS = list(TF.keys())
UP, DOWN = "#26a69a", "#ef5350"

COMMODITY_NAMES = {
    "GC=F": "ทองคำ (Gold)", "SI=F": "เงิน (Silver)", "HG=F": "ทองแดง (Copper)",
    "PL=F": "แพลทินัม (Platinum)", "PA=F": "แพลเลเดียม (Palladium)",
    "CL=F": "น้ำมันดิบ WTI", "BZ=F": "น้ำมันดิบ Brent", "NG=F": "ก๊าซธรรมชาติ",
    "RB=F": "น้ำมันเบนซิน", "ZC=F": "ข้าวโพด", "ZW=F": "ข้าวสาลี",
    "ZS=F": "ถั่วเหลือง", "RR=F": "ข้าวเปลือก", "KC=F": "กาแฟ",
    "CC=F": "โกโก้", "SB=F": "น้ำตาล", "CT=F": "ฝ้าย"
}

FOREX_NAMES = {
    "USDTHB=X": "ดอลลาร์ / บาท", "EURTHB=X": "ยูโร / บาท", "JPYTHB=X": "เยน / บาท",
    "GBPTHB=X": "ปอนด์ / บาท", "CNYTHB=X": "หยวน / บาท", "SGDTHB=X": "ดอลลาร์สิงคโปร์ / บาท",
    "EURUSD=X": "EUR / USD", "GBPUSD=X": "GBP / USD", "USDJPY=X": "USD / JPY",
    "USDCHF=X": "USD / CHF", "AUDUSD=X": "AUD / USD", "USDCAD=X": "USD / CAD", "NZDUSD=X": "NZD / USD"
}

CHINA_STOCK_NAMES = {
    "002594.SZ": "BYD (บีวายดี EV)", "300750.SZ": "CATL (แบตเตอรี่ EV)",
    "9866.HK":   "NIO (นีโอ)", "9868.HK":   "XPeng (เสี่ยวเผิง)",
    "2015.HK":   "Li Auto (ลี่ออโต้)", "1810.HK":   "Xiaomi (เสียวหมี่)",
    "600104.SS": "SAIC Motor", "601633.SS": "Great Wall Motor",
    "0700.HK":   "Tencent (เทนเซ็นต์)", "9988.HK":   "Alibaba (อาลีบาบา)",
    "3690.HK":   "Meituan (เหม่ยถวน)", "9618.HK":   "JD.com",
    "9999.HK":   "NetEase", "9888.HK":   "Baidu (ไป่ตู้ AI)",
    "688981.SS": "SMIC (ชิปเบอร์ 1)", "601138.SS": "Foxconn Industrial",
    "002415.SZ": "Hikvision (กล้อง AI)", "600519.SS": "Kweichow Moutai (เหมาไถ)",
    "000858.SZ": "Wuliangye (อู่เหลียงเย่)", "000333.SZ": "Midea Group",
    "000651.SZ": "Gree Electric", "601398.SS": "ICBC ธนาคารจีน",
    "601939.SS": "CCB ธนาคารก่อสร้าง", "601288.SS": "ABC ธนาคารเกษตร",
    "601988.SS": "Bank of China", "600036.SS": "China Merchants Bank",
    "601318.SS": "Ping An Insurance", "601857.SS": "PetroChina",
    "600028.SS": "Sinopec", "601088.SS": "China Shenhua",
    "600900.SS": "Yangtze Power", "601899.SS": "Zijin Mining",
    "600276.SS": "Hengrui Medicine", "300760.SZ": "Mindray Bio-Medical"
}

STAR_CATEGORIES = {
    "🔴 ดาวแดง": {"icon": "🔴", "color": "#ef5350"},
    "🟡 ดาวเหลือง": {"icon": "🟡", "color": "#f5c518"},
    "🟢 ดาวเขียว": {"icon": "🟢", "color": "#26a69a"},
    "🔵 ดาวฟ้า": {"icon": "🔵", "color": "#2962ff"},
    "🟣 ดาวม่วง": {"icon": "🟣", "color": "#ab47bc"}
}

if "star_watchlists" not in st.session_state:
    st.session_state["star_watchlists"] = {
        "🔴 ดาวแดง": ["AAA.VN", "GC=F", "NVDA", "BTC_THB"],
        "🟡 ดาวเหลือง": ["VIC.VN", "0700.HK", "USDTHB=X"],
        "🟢 ดาวเขียว": ["HPG.VN", "CL=F", "PTT.BK"],
        "🔵 ดาวฟ้า": ["FPT.VN", "TSLA", "BTCUSDT"],
        "🟣 ดาวม่วง": ["EURUSD=X"]
    }
if "custom_symbols" not in st.session_state: st.session_state["custom_symbols"] = []
if "current_symbol" not in st.session_state: st.session_state["current_symbol"] = "BTC_THB"
if "selected_tf" not in st.session_state: st.session_state["selected_tf"] = "1h"

def init_tabs():
    if "open_tabs" not in st.session_state or not st.session_state.open_tabs:
        first_id = uuid.uuid4().hex[:8]
        st.session_state.open_tabs = [{
            "id": first_id,
            "symbol": st.session_state.current_symbol,
            "tf": st.session_state.selected_tf
        }]
        st.session_state.active_tab_id = first_id

def _find_tab(tab_id):
    return next((t for t in st.session_state.open_tabs if t["id"] == tab_id), None)

def _clear_chart_state():
    for k in ("active_key", "df_data", "last_fetch_ts"):
        st.session_state.pop(k, None)

def add_tab(symbol):
    new_id = uuid.uuid4().hex[:8]
    tab = {"id": new_id, "symbol": symbol, "tf": st.session_state.selected_tf}
    st.session_state.open_tabs.append(tab)
    switch_tab(new_id)

def switch_tab(tab_id):
    tab = _find_tab(tab_id)
    if not tab: return
    current = _find_tab(st.session_state.get("active_tab_id"))
    if current:
        current["tf"] = st.session_state.selected_tf
    st.session_state.active_tab_id = tab_id
    st.session_state.current_symbol = tab["symbol"]
    st.session_state.selected_tf = tab["tf"]
    _clear_chart_state()
    st.rerun()

def close_tab(tab_id):
    if len(st.session_state.open_tabs) <= 1: return
    idx = next((i for i, t in enumerate(st.session_state.open_tabs) if t["id"] == tab_id), 0)
    st.session_state.open_tabs.pop(idx)
    if st.session_state.active_tab_id == tab_id:
        fallback = st.session_state.open_tabs[max(0, idx - 1)]
        switch_tab(fallback["id"])
    else:
        st.rerun()

init_tabs()

if "pane_order" not in st.session_state: st.session_state["pane_order"] = ["rsi", "macd"]
if "mobile_mode" not in st.session_state: st.session_state["mobile_mode"] = False
if "main_h" not in st.session_state: st.session_state["main_h"] = 520
if "rsi_h" not in st.session_state: st.session_state["rsi_h"] = 120
if "macd_h" not in st.session_state: st.session_state["macd_h"] = 120

if "fast_ema" not in st.session_state: st.session_state["fast_ema"] = 7
if "slow_ema" not in st.session_state: st.session_state["slow_ema"] = 13
if "trend_ema" not in st.session_state: st.session_state["trend_ema"] = 45
if "min_tp" not in st.session_state: st.session_state["min_tp"] = 3.0
if "warn_pct" not in st.session_state: st.session_state["warn_pct"] = 3.0
if "danger_pct" not in st.session_state: st.session_state["danger_pct"] = 7.0
if "show_stars" not in st.session_state: st.session_state["show_stars"] = True

if "show_fast" not in st.session_state: st.session_state["show_fast"] = True
if "show_slow" not in st.session_state: st.session_state["show_slow"] = True
if "show_trend" not in st.session_state: st.session_state["show_trend"] = True
if "show_rsi" not in st.session_state: st.session_state["show_rsi"] = True
if "show_macd" not in st.session_state: st.session_state["show_macd"] = True
if "show_sig" not in st.session_state: st.session_state["show_sig"] = False
if "show_dots" not in st.session_state: st.session_state["show_dots"] = False
if "ema_opacity" not in st.session_state: st.session_state["ema_opacity"] = 0
if "trend_opacity" not in st.session_state: st.session_state["trend_opacity"] = 60
if "line_width" not in st.session_state: st.session_state["line_width"] = 2

if "bars_count" not in st.session_state: st.session_state["bars_count"] = 2500
if "fill_gaps" not in st.session_state: st.session_state["fill_gaps"] = False
if "auto_refresh" not in st.session_state: st.session_state["auto_refresh"] = True
if "refresh_sec" not in st.session_state: st.session_state["refresh_sec"] = 2

if "fib_lookback" not in st.session_state: st.session_state["fib_lookback"] = 5
if "fib_window" not in st.session_state: st.session_state["fib_window"] = 120
if "fib_tp_level" not in st.session_state: st.session_state["fib_tp_level"] = 1.618
if "fib_confirm_on" not in st.session_state: st.session_state["fib_confirm_on"] = False
if "chart_slot" not in st.session_state: st.session_state["chart_slot"] = None

def resolve_route(symbol: str, ui_market: str = "", ui_exchange: str = "Binance"):
    s = (symbol or "").upper()
    if s.endswith(".BK"): return "🇹🇭 หุ้นไทย (SET/mai)", "Yahoo"
    if s.endswith(".VN"): return "🇻🇳 หุ้นเวียดนาม (Vietnam)", "Yahoo"
    if s.endswith(".SS") or s.endswith(".SZ") or s.endswith(".HK"): return "🇨🇳 หุ้นจีน (China)", "Yahoo"
    if s.endswith("_THB") or s.startswith("THB_"): return "🟡 คริปโต (Crypto)", "Bitkub"
    if s.endswith("-USDT"): return "🟡 คริปโต (Crypto)", "OKX"
    if s.endswith("USDT"): return "🟡 คริปโต (Crypto)", "Binance"
    return GLOBAL_MARKET, "Yahoo"

def route_label(r_market: str, r_exchange: str) -> str:
    if "คริปโต" in r_market: return r_exchange
    if r_market == GLOBAL_MARKET: return "Yahoo"
    return r_market.split()[0]

def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if df is None or df.empty or len(df) < 2 or not rule: return df
    d = df.copy()
    d["datetime"] = pd.to_datetime(d["time"], unit="s", utc=True)
    d = d.set_index("datetime")
    out = d.resample(rule, origin="epoch", closed="left", label="left").agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
    }).dropna(subset=["open", "close"])
    out["time"] = (out.index.astype("int64") // 10**9).astype("int64")
    return out.reset_index(drop=True)

def fill_empty_bars(df: pd.DataFrame, sec: int, max_fill: int = 20000) -> pd.DataFrame:
    if df.empty or len(df) < 2: return df
    base = df.drop_duplicates(subset=["time"]).sort_values("time").copy()
    base["time"] = (base["time"].astype("int64") // sec) * sec
    base = base.drop_duplicates(subset=["time"]).set_index("time")
    start, end = int(base.index[0]), int(base.index[-1])
    if (end - start) // sec > max_fill: return df

    full_idx = np.arange(start, end + sec, sec, dtype="int64")
    out = base.reindex(full_idx)
    synth = out["close"].isna().values
    out["close"]  = out["close"].ffill()
    out["open"]   = out["open"].fillna(out["close"])
    out["high"]   = out["high"].fillna(out["close"])
    out["low"]    = out["low"].fillna(out["close"])
    out["volume"] = out["volume"].fillna(0.0)
    out["is_synthetic"] = synth
    return out.dropna(subset=["close"]).reset_index()

try:
    BITKUB_API_KEY = st.secrets.get("BITKUB_API_KEY", "")
except Exception:
    BITKUB_API_KEY = ""

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update(BROWSER_HEADERS)
retry_strategy = Retry(
    total=3,
    backoff_factor=0.8,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
http_adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=25, pool_maxsize=25)
HTTP_SESSION.mount("https://", http_adapter)
HTTP_SESSION.mount("http://", http_adapter)
THREAD_POOL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def fetch_bitkub_raw(symbol: str, tf_code: str, sec: int, bars: int) -> pd.DataFrame:
    all_chunks = []
    curr_to = int(time.time())
    headers = dict(BROWSER_HEADERS)
    if BITKUB_API_KEY and len(BITKUB_API_KEY) > 20: headers["X-BTK-APIKEY"] = BITKUB_API_KEY
    total, max_loops = 0, 400
    window, max_window = sec * 1000, sec * 300000
    empty_streak, oldest_seen, floor_ts = 0, None, 1451606400

    for _ in range(max_loops):
        if total >= bars: break
        frm = max(curr_to - window, floor_ts)
        if frm >= curr_to: break
        try:
            r = HTTP_SESSION.get(
                "https://api.bitkub.com/tradingview/history", headers=headers,
                params={"symbol": symbol, "resolution": tf_code, "from": frm, "to": curr_to}, timeout=5
            )
            if r.status_code == 429: time.sleep(1.0); continue
            if r.status_code != 200: break
            j = r.json()
        except Exception: break

        status = j.get("s")
        if status == "no_data":
            nxt = j.get("nextTime")
            curr_to = int(nxt) + sec if (nxt and int(nxt) < curr_to) else frm - 1
            window = sec * 1000 if (nxt and int(nxt) < curr_to) else min(window * 4, max_window)
            empty_streak += 1
            if empty_streak >= 10: break
            continue

        if status != "ok" or not j.get("t"): break
        t_list = j["t"]
        if not t_list: break

        all_chunks.append(pd.DataFrame({"time": t_list, "open": j["o"], "high": j["h"], "low": j["l"], "close": j["c"], "volume": j["v"]}))
        total += len(t_list)
        empty_streak = 0
        min_t = int(min(t_list))
        if oldest_seen is not None and min_t >= oldest_seen: break
        oldest_seen = min_t
        curr_to = min_t - 1
        if len(t_list) < 200: break

    if not all_chunks: return pd.DataFrame()
    df = pd.concat(all_chunks, ignore_index=True)
    for c in ["open", "high", "low", "close", "volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")
    return df.dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)

def fetch_binance_raw(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    out = []
    end_ts = None
    while len(out) < bars:
        limit = min(1000, bars - len(out))
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if end_ts: params["endTime"] = end_ts
        try:
            r = HTTP_SESSION.get("https://api.binance.com/api/v3/klines", params=params, timeout=5)
            if r.status_code != 200: break
            k = r.json()
            if not k or not isinstance(k, list): break
            out = k + out
            new_end = k[0][0] - 1
            if end_ts and new_end >= end_ts: break
            end_ts = new_end
            if len(k) < limit: break
        except Exception: break
            
    if not out: return pd.DataFrame()
    df = pd.DataFrame(out, columns=["ot","open","high","low","close","volume","ct","qv","n","tb","tq","ig"])
    df = df[["ot","open","high","low","close","volume"]].astype(float)
    df["time"] = (df["ot"] // 1000).astype("int64")
    return df.dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)

def parse_yahoo_json(j: dict) -> pd.DataFrame:
    try:
        result = j.get("chart", {}).get("result", [])
        if not result: return pd.DataFrame()
        res = result[0]
        ts = res.get("timestamp", [])
        q = res.get("indicators", {}).get("quote", [{}])[0]
        if not ts or not q: return pd.DataFrame()
        o, h, l, c, v = q.get("open", []), q.get("high", []), q.get("low", []), q.get("close", []), q.get("volume", [])
        rows = []
        for i in range(len(ts)):
            if ts[i] is not None and i < len(c) and c[i] is not None:
                rows.append({
                    "time": int(ts[i]),
                    "open": float(o[i] if (i < len(o) and o[i] is not None) else c[i]),
                    "high": float(h[i] if (i < len(h) and h[i] is not None) else c[i]),
                    "low":  float(l[i] if (i < len(l) and l[i] is not None) else c[i]),
                    "close": float(c[i]),
                    "volume": float(v[i] if (i < len(v) and v[i] is not None) else 0.0)
                })
        return pd.DataFrame(rows)
    except Exception: return pd.DataFrame()

def fetch_yahoo_rest_api(symbol: str, tf: str, bars: int) -> pd.DataFrame:
    tf_info = TF.get(tf, TF["1d"])
    urls = [f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"]
    df = pd.DataFrame()
    for url in urls:
        try:
            r = HTTP_SESSION.get(url, params={"interval": tf_info["yf_iv"], "range": tf_info.get("yf_range", "60d")}, timeout=4.0)
            if r.status_code == 200:
                df = parse_yahoo_json(r.json())
                if not df.empty and len(df) >= 3: break
        except Exception: pass

    if df.empty or len(df) < 3:
        for fb in [{"interval":"1d","range":"5y"}, {"interval":"60m","range":"730d"}]:
            for url in urls:
                try:
                    r = HTTP_SESSION.get(url, params=fb, timeout=4.0)
                    if r.status_code == 200:
                        df = parse_yahoo_json(r.json())
                        if not df.empty and len(df) >= 3: break
                except Exception: pass
            if not df.empty and len(df) >= 3: break

    if (df.empty or len(df) < 3) and yf is not None:
        try:
            hist = yf.Ticker(symbol).history(period="5y", interval="1d")
            if not hist.empty:
                hist = hist.reset_index()
                tcol = "Datetime" if "Datetime" in hist.columns else "Date"
                hist["time"] = (pd.to_datetime(hist[tcol]).astype("int64") // 10**9).astype("int64")
                hist = hist.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
                df = hist[["time","open","high","low","close","volume"]]
        except Exception: pass

    if df.empty: return pd.DataFrame()
    for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")
    df = df.dropna().drop_duplicates(subset=["time"]).sort_values("time")
    if tf_info["base"] is not None and len(df) > 50: df = resample_ohlcv(df, tf_info["rule"])
    return df.tail(bars).reset_index(drop=True)

def fetch_ohlcv(market_type: str, exchange: str, symbol: str, tf: str, bars: int, fill_gaps: bool = False) -> pd.DataFrame:
    tf_info = TF[tf]
    if "คริปโต" in market_type:
        if exchange == "Bitkub":
            native = {"1m":"1","5m":"5","15m":"15","30m":"30","1h":"60","4h":"240","1d":"1D","1w":"1W"}
            if tf in native: df = fetch_bitkub_raw(symbol, native[tf], tf_info["sec"], bars)
            else:
                base_tf = tf_info["base"] or "1h"
                mult = max(1, tf_info["sec"] // TF[base_tf]["sec"])
                df = fetch_bitkub_raw(symbol, native.get(base_tf, "60"), TF[base_tf]["sec"], min(bars * mult, 25000))
                if not df.empty: df = resample_ohlcv(df, tf_info["rule"])
            if fill_gaps and not df.empty: df = fill_empty_bars(df, tf_info["sec"]).tail(bars).reset_index(drop=True)
        else:
            df = fetch_binance_raw(symbol, tf, bars)
    else:
        df = fetch_yahoo_rest_api(symbol, tf, bars)
    if df is None or df.empty: return pd.DataFrame()
    return df.tail(bars).reset_index(drop=True)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_daily_history(market_type: str, exchange: str, symbol: str) -> pd.DataFrame:
    try:
        if "คริปโต" in market_type and exchange == "Bitkub":
            return fetch_bitkub_raw(symbol, "1D", 86400, 1100)
        elif "คริปโต" in market_type:
            return fetch_binance_raw(symbol, "1d", 1100)
        else:
            return fetch_yahoo_rest_api(symbol, "1d", 1100)
    except Exception:
        return pd.DataFrame()

def fetch_unified_ticker(market: str = "", exchange: str = "", symbol: str = "", df: pd.DataFrame = None) -> dict:
    tk = {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0, "high": 0.0, "low": 0.0, "bid": 0.0, "ask": 0.0}
    sym = (symbol or "").upper()

    # 1. สินค้าเกษตร / ราคาข้าว
    if sym.startswith("RICE:") or sym.startswith("FOB:") or sym == "ZR=F (CBOT Rough Rice)":
        try:
            r_df = generate_rice_ohlcv(sym)
            if r_df is not None and not r_df.empty:
                last_p = float(r_df["close"].iloc[-1])
                prev_p = float(r_df["close"].iloc[-2]) if len(r_df) >= 2 else last_p
                chg = last_p - prev_p
                pct = (chg / prev_p * 100.0) if prev_p != 0 else 0.0
                return {
                    "price": last_p, "change": chg, "pct": pct,
                    "high": float(r_df["high"].max()), "low": float(r_df["low"].min()),
                    "vol": float(r_df["volume"].iloc[-1]) if "volume" in r_df.columns else 0.0,
                    "bid": last_p, "ask": last_p
                }
        except Exception: pass

    # 2. คริปโตไทย (Bitkub: _THB หรือ THB_)
    elif ("THB" in sym) or (exchange == "Bitkub"):
        try:
            r = HTTP_SESSION.get("https://api.bitkub.com/api/market/ticker", timeout=3.0)
            if r.status_code == 200:
                data = r.json()
                k = sym if sym.startswith("THB_") else f"THB_{sym.replace('_THB', '')}"
                if k in data:
                    item = data[k]
                    last_p = float(item.get("last", 0.0))
                    pct = float(item.get("percentChange", 0.0))
                    chg = float(item.get("change", 0.0))
                    return {
                        "price": last_p, "change": chg, "pct": pct,
                        "high": float(item.get("high24hr", last_p)),
                        "low": float(item.get("low24hr", last_p)),
                        "vol": float(item.get("baseVolume", 0.0)),
                        "bid": float(item.get("highestBid", last_p)),
                        "ask": float(item.get("lowestAsk", last_p))
                    }
        except Exception: pass

    # 3. คริปโต Binance (คู่เหรียญ USDT เช่น BNBUSDT, BTCUSDT)
    elif sym.endswith("USDT"):
        try:
            r = HTTP_SESSION.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}", timeout=3.0)
            if r.status_code == 200:
                data = r.json()
                last_p = float(data.get("lastPrice", 0.0))
                pct = float(data.get("priceChangePercent", 0.0))
                chg = float(data.get("priceChange", 0.0))
                return {
                    "price": last_p, "change": chg, "pct": pct,
                    "high": float(data.get("highPrice", last_p)),
                    "low": float(data.get("lowPrice", last_p)),
                    "vol": float(data.get("volume", 0.0)),
                    "bid": last_p, "ask": last_p
                }
        except Exception: pass

    # 4. สินทรัพย์ต่างประเทศ / ทองคำ / Forex / หุ้น (Yahoo Finance)
    else:
        try:
            r = HTTP_SESSION.get(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={sym}", timeout=3.0)
            if r.status_code == 200:
                q_list = r.json().get("quoteResponse", {}).get("result", [])
                if q_list:
                    item = q_list[0]
                    last_p = float(item.get("regularMarketPrice", 0.0))
                    pct = float(item.get("regularMarketChangePercent", 0.0))
                    chg = float(item.get("regularMarketChange", 0.0))
                    return {
                        "price": last_p, "change": chg, "pct": pct,
                        "high": float(item.get("regularMarketDayHigh", last_p)),
                        "low": float(item.get("regularMarketDayLow", last_p)),
                        "vol": float(item.get("regularMarketVolume", 0.0)),
                        "bid": last_p, "ask": last_p
                    }
        except Exception: pass

    # 5. กรณีดึงออนไลน์ไม่ผ่าน ให้ใช้ข้อมูลจากแท่งเทียน (Fallback)
    try:
        if df is not None and not df.empty and "close" in df.columns:
            last_p = float(df["close"].iloc[-1])
            prev_p = float(df["close"].iloc[-2]) if len(df) >= 2 else last_p
            chg = last_p - prev_p
            pct = (chg / prev_p * 100.0) if prev_p != 0 else 0.0
            tk.update({
                "price": last_p, "change": chg, "pct": pct,
                "high": float(df["high"].max()), "low": float(df["low"].min()),
                "vol": float(df["volume"].iloc[-1]) if "volume" in df.columns else 0.0,
                "bid": last_p, "ask": last_p
            })
    except Exception: pass

    return tk

@st.cache_data(ttl=5, show_spinner=False)
def fetch_cached_tab_quote(sym: str) -> dict:
    try:
        t = fetch_unified_ticker(symbol=sym)
        if t and t.get("price", 0) > 0: return t
    except Exception: pass
    return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0, "high": 0.0, "low": 0.0, "bid": 0.0, "ask": 0.0}

def format_clean_tab_label(sym: str, q: dict) -> str:
    if sym.startswith("RICE:"):
        name = sym.replace("RICE:", "").replace("ข้าวเปลือก", "").replace("ข้าวสาร", "").strip()[:10]
        ico = "🌾"
    elif sym.startswith("FOB:"):
        name = sym.replace("FOB:", "").strip()[:10]
        ico = "🚢"
    elif sym.endswith("_THB"):
        name = f"{sym.replace('_THB', '')}/THB"
        ico = "₿"
    elif sym.endswith("USDT"):
        name = f"{sym.replace('USDT', '')}/USDT"
        ico = "₿"
    elif sym.endswith(".BK"):
        name = sym.replace(".BK", "")
        ico = "🇹🇭"
    elif sym == "GC=F":
        name = "Gold"
        ico = "🪙"
    elif sym == "CL=F":
        name = "Oil"
        ico = "🛢️"
    else:
        name = sym[:10]
        ico = "📈"

    p = q.get("price", 0.0)
    pct = q.get("pct", 0.0)
    if p > 0:
        p_str = f"{p:,.0f}" if p >= 1000 else (f"{p:,.2f}" if p >= 1 else f"{p:,.4f}")
        return f"{ico} {name}  {p_str} ({pct:+.2f}%)"
    return f"{ico} {name}  --"

# ────────────────── TRADINGVIEW PRO UNIFORM TABS (CYBER GLOW) ──────────────────
def render_tradingview_clean_tabs():
    st.markdown("""
    <style>
    /* 1. ล้างระยะห่างระหว่างแท็บกับปุ่มปิด X ให้ติดกันสนิท */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-tv_tab_"]) {
        gap: 0px !important;
        align-items: center !important;
        margin-bottom: 4px !important;
    }

    /* 2. สไตล์ปุ่มแท็บหลัก (ขอบขวาตัดตรง) */
    div[class*="st-key-tv_tab_"] button,
    div[class*="st-key-tv_tab_"] button[data-testid*="BaseButton"] {
        height: 32px !important;
        min-height: 32px !important;
        border-top-right-radius: 0px !important;
        border-bottom-right-radius: 0px !important;
        border-right: none !important;
        padding: 0 8px 0 10px !important;
        font-size: 11.5px !important;
        font-weight: 600 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        white-space: nowrap !important;
        overflow: visible !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* 3. สไตล์ปุ่มปิด X (ขอบซ้ายตัดตรง เชื่อมกับแท็บหลัก) */
    div[class*="st-key-tv_close_"] button,
    div[class*="st-key-tv_close_"] button[data-testid*="BaseButton"] {
        height: 32px !important;
        min-height: 32px !important;
        border-top-left-radius: 0px !important;
        border-bottom-left-radius: 0px !important;
        border-left: none !important;
        padding: 0 8px 0 2px !important;
        font-size: 11px !important;
        color: #787b86 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* 4. สถานะแท็บ Active (กำลังดู) - พื้นหลังดำเทา #1c202d + ขอบเรืองแสงเขียวนีออน */
    div[class*="st-key-tv_tab_"] button[kind="primary"],
    div[class*="st-key-tv_tab_"] button[data-testid="stBaseButton-primary"] {
        background: #1c202d !important;
        background-color: #1c202d !important;
        border: 1px solid #00FFA3 !important;
        border-right: none !important;
        color: #ffffff !important;
        box-shadow: -2px 0 8px rgba(0, 255, 163, 0.3), 0 -2px 8px rgba(0, 255, 163, 0.3), 0 2px 8px rgba(0, 255, 163, 0.3) !important;
    }
    div[class*="st-key-tv_close_"] button[kind="primary"],
    div[class*="st-key-tv_close_"] button[data-testid="stBaseButton-primary"] {
        background: #1c202d !important;
        background-color: #1c202d !important;
        border: 1px solid #00FFA3 !important;
        border-left: none !important;
        color: #8f9cae !important;
        box-shadow: 2px 0 8px rgba(0, 255, 163, 0.3), 0 -2px 8px rgba(0, 255, 163, 0.3), 0 2px 8px rgba(0, 255, 163, 0.3) !important;
    }

    /* 5. สถานะแท็บ Inactive (แท็บรอง) - พื้นหลังมืดสนิท #11141c + ขอบเขียวโปร่งแสง */
    div[class*="st-key-tv_tab_"] button[kind="secondary"],
    div[class*="st-key-tv_tab_"] button[data-testid="stBaseButton-secondary"] {
        background: #11141c !important;
        background-color: #11141c !important;
        border: 1px solid rgba(0, 255, 163, 0.2) !important;
        border-right: none !important;
        color: #8f9cae !important;
    }
    div[class*="st-key-tv_close_"] button[kind="secondary"],
    div[class*="st-key-tv_close_"] button[data-testid="stBaseButton-secondary"] {
        background: #11141c !important;
        background-color: #11141c !important;
        border: 1px solid rgba(0, 255, 163, 0.2) !important;
        border-left: none !important;
        color: #787b86 !important;
    }

    /* 6. เอฟเฟกต์เมาส์ชี้ (Hover) - สีเขียวเรืองแสงโปร่งแสงทั้งก้อน */
    div[class*="st-key-tv_tab_"] button:hover {
        background: rgba(0, 255, 163, 0.16) !important;
        background-color: rgba(0, 255, 163, 0.16) !important;
        border-color: #00FFA3 !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px rgba(0, 255, 163, 0.45) !important;
    }
    div[class*="st-key-tv_close_"] button:hover {
        background: rgba(239, 83, 80, 0.2) !important;
        background-color: rgba(239, 83, 80, 0.2) !important;
        border-color: #ef5350 !important;
        color: #ef5350 !important;
        box-shadow: 0 0 10px rgba(239, 83, 80, 0.4) !important;
    }

    /* 7. ปุ่มเพิ่มแท็บใหม่ (+) */
    div[class*="st-key-tv_add_btn"] button,
    div[class*="st-key-tv_add_btn"] button[data-testid*="BaseButton"] {
        height: 32px !important;
        min-height: 32px !important;
        width: 32px !important;
        background: #11141c !important;
        background-color: #11141c !important;
        border: 1px solid rgba(0, 255, 163, 0.25) !important;
        border-radius: 4px !important;
        color: #787b86 !important;
        font-size: 15px !important;
        padding: 0 !important;
        margin-left: 6px !important;
        transition: all 0.2s ease !important;
    }
    div[class*="st-key-tv_add_btn"] button:hover {
        background: rgba(0, 255, 163, 0.16) !important;
        background-color: rgba(0, 255, 163, 0.16) !important;
        border-color: #00FFA3 !important;
        color: #00FFA3 !important;
        box-shadow: 0 0 10px rgba(0, 255, 163, 0.4) !important;
    }
    div[class*="st-key-chip_"] button {

    border-radius: 6px !important;

    font-size: 13px !important;

    font-weight: 700 !important;

    height: 38px !important;

    padding: 0 6px !important;

    transition: all .2s ease !important;

}

div[class*="st-key-chip_"] button[kind="primary"],

div[class*="st-key-chip_"] button[data-testid="stBaseButton-primary"] {

    background: rgba(0, 255, 163, 0.12) !important;

    background-color: rgba(0, 255, 163, 0.12) !important;

    border: 1px solid #00FFA3 !important;

    color: #00FFA3 !important;

    box-shadow: 0 0 8px rgba(0, 255, 163, 0.25) !important;

}

div[class*="st-key-chip_"] button[kind="secondary"],

div[class*="st-key-chip_"] button[data-testid="stBaseButton-secondary"] {

    background: #11141c !important;

    background-color: #11141c !important;

    border: 1px solid rgba(0, 255, 163, 0.2) !important;

    color: #8f9cae !important;

    box-shadow: none !important;

}

div[class*="st-key-chip_"] button:hover {

    border-color: #00FFA3 !important;

    color: #ffffff !important;

    box-shadow: 0 0 12px rgba(0, 255, 163, 0.45) !important;

}
    </style>
    """, unsafe_allow_html=True)

    tabs = st.session_state.get("open_tabs", [])
    if not tabs:
        init_tabs()
        tabs = st.session_state.get("open_tabs", [])

    active_id = st.session_state.get("active_tab_id")

    TAB_WIDTH = 2.4
    CLOSE_WIDTH = 0.38
    ADD_WIDTH = 0.32

    col_specs = []
    for _ in tabs:
        col_specs.extend([TAB_WIDTH, CLOSE_WIDTH])
    col_specs.append(ADD_WIDTH)
    col_specs.append(max(0.5, 18.0 - (len(tabs) * (TAB_WIDTH + CLOSE_WIDTH) + ADD_WIDTH)))

    cols = st.columns(col_specs)
    col_idx = 0

    for t in tabs:
        t_id = t["id"]
        sym = t["symbol"]
        is_active = (t_id == active_id)

        if sym == "GC=F":
            badge, name = "🟡", "GOLD"
        elif sym == "CL=F":
            badge, name = "🛢️", "OIL"
        elif sym.startswith("RICE:"):
            badge = "🌾"
            name = sym.replace("RICE:", "").replace("ข้าวเปลือก", "").replace("ข้าวสาร", "").strip()[:8]
        elif sym.startswith("FOB:"):
            badge, name = "🚢", sym.replace("FOB:", "").strip()[:8]
        elif sym.endswith("_THB"):
            badge, name = "💠", sym.replace("_THB", "THB")
        elif sym.endswith("USDT"):
            badge, name = "🟡", sym
        elif sym.endswith(".BK"):
            badge, name = "🇹🇭", sym.replace(".BK", "")
        else:
            badge, name = "📈", sym[:8]

        q = fetch_cached_tab_quote(sym)
        p = q.get("price", 0.0)
        pct = q.get("pct", 0.0)

        if p > 0:
            p_str = f"{p:.4f}" if p < 1 else (f"{p:,.2f}" if p < 10000 else f"{p:,.0f}")
            if pct < 0:
                label = f"{badge} {name}  :red[▼ {p_str} {pct:.2f}%]"
            elif pct > 0:
                label = f"{badge} {name}  :green[▲ {p_str} +{pct:.2f}%]"
            else:
                label = f"{badge} {name}  {p_str} 0.00%"
        else:
            label = f"{badge} {name}  --"

        b_type = "primary" if is_active else "secondary"

        with cols[col_idx]:
            if st.button(label, key=f"tv_tab_{t_id}", type=b_type, use_container_width=True):
                switch_tab(t_id)
        col_idx += 1

        with cols[col_idx]:
            if st.button("✕", key=f"tv_close_{t_id}", type=b_type, help=f"ปิด {sym}", use_container_width=True):
                close_tab(t_id)
        col_idx += 1

    with cols[col_idx]:
        if st.button("＋", key="tv_add_btn", help="เพิ่มแท็บใหม่"):
            add_tab("BTCUSDT")

    active_tab = _find_tab(active_id)
    return active_tab["symbol"] if active_tab else st.session_state.get("current_symbol", "BTC_THB")

def fetch_item_quote(sym: str) -> dict:
    try:
        t = fetch_unified_ticker(symbol=sym)
        if t and t.get("price", 0) > 0: return t
    except Exception: pass
    return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0, "high": 0.0, "low": 0.0, "bid": 0.0, "ask": 0.0}

if hasattr(st, "dialog"):
    @st.dialog("📐 บทวิเคราะห์ Fibonacci Suite & เป้าหมายราคา", width="large")
    def open_fib_dialog(fib, ext, fib_zone, fib_tp, last_close):
        render_fibonacci_modal_content(fib, ext, fib_zone, fib_tp, last_close)

    @st.dialog("📊 ข้อมูลตลาด 24h & บทวิเคราะห์เทคนิคขั้นสูง", width="large")
    def open_market_dialog(tk, an, symbol, label_name, seasonality_html, gauges_html):
        render_market_modal_content(tk, an, symbol, label_name, seasonality_html, gauges_html)
else:
    def open_fib_dialog(fib, ext, fib_zone, fib_tp, last_close):
        with st.expander("📐 บทวิเคราะห์ Fibonacci Suite & เป้าหมายราคา", expanded=True):
            render_fibonacci_modal_content(fib, ext, fib_zone, fib_tp, last_close)

    def open_market_dialog(tk, an, symbol, label_name, seasonality_html, gauges_html):
        with st.expander("📊 ข้อมูลตลาด 24h & บทวิเคราะห์เทคนิคขั้นสูง", expanded=True):
            render_market_modal_content(tk, an, symbol, label_name, seasonality_html, gauges_html)

# ──────────────────────────── TOP TOOLBAR ────────────────────────────
def _render_chip(col, state_key, on_label, off_label, key, default=True):
    with col:
        active = bool(st.session_state.get(state_key, default))
        if st.button(on_label if active else off_label,
                     key=key, use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state[state_key] = not active
            st.rerun()
    return active


def render_top_toolbar():
    (col_tf, col_slider, col_fill, col_auto,
     col_rsi, col_macd, col_sec, col_load) = st.columns(
        [1.5, 5, 1.2, 1.2, 1.3, 1.4, 1.5, 1.8])

    with col_tf:
        tf = st.selectbox(
            "TF", TF_OPTIONS,
            index=TF_OPTIONS.index(st.session_state.get("selected_tf", "1h"))
                  if st.session_state.get("selected_tf", "1h") in TF_OPTIONS else 0,
            label_visibility="collapsed", key="toolbar_tf")
    with col_slider:
        bars = st.slider("Bars", 300, 25000,
                         int(st.session_state.get("bars_count", 2500)), 500,
                         label_visibility="collapsed", key="toolbar_bars")
    with col_fill:
        fill_gaps = st.checkbox("Fill",
                                value=st.session_state.get("fill_gaps", False),
                                key="toolbar_fill")
    with col_auto:
        auto = st.checkbox("Auto",
                           value=st.session_state.get("auto_refresh", False),
                           key="toolbar_auto")

    _render_chip(col_rsi,  "show_rsi_pane",  "📈 RSI",  "+ RSI",  "chip_rsi")
    _render_chip(col_macd, "show_macd_pane", "📊 MACD", "+ MACD", "chip_macd")

    with col_sec:
        every = st.number_input("Sec", 2, 60,
                                int(st.session_state.get("refresh_sec", 5)), 1,
                                label_visibility="collapsed", key="toolbar_sec")
    with col_load:
        reload_btn = st.button("🔄 โหลด", use_container_width=True,
                               key="toolbar_reload_btn")

    if tf != st.session_state.get("selected_tf"):
        st.session_state.selected_tf = tf
        cur = _find_tab(st.session_state.active_tab_id)
        if cur:
            cur["tf"] = tf
        _clear_chart_state()
        st.rerun()

    st.session_state.bars_count   = bars
    st.session_state.fill_gaps    = fill_gaps
    st.session_state.auto_refresh = auto
    st.session_state.refresh_sec  = every

    if reload_btn:
        _clear_chart_state()
        st.rerun()

    return tf, bars, fill_gaps, auto, every, reload_btn

@st.cache_data(ttl=30, show_spinner=False)
def fetch_top_movers(category: str = "all") -> dict:
    empty_result = {"gainers": [], "losers": []}
    if category == "bitkub":
        try:
            r = HTTP_SESSION.get("https://api.bitkub.com/api/market/ticker", timeout=4.0)
            if r.status_code == 200:
                items = []
                for sym_code, v in r.json().items():
                    if not sym_code.startswith("THB_"): continue
                    p = float(v.get("last", 0.0))
                    pct = float(v.get("percentChange", 0.0))
                    clean_name = sym_code.replace("THB_", "") + "_THB"
                    items.append({
                        "symbol": clean_name, "label": f"{clean_name} ({pct:+.2f}%)",
                        "price": p, "fmt_price": f"{p:,.4f}" if p < 10 else f"{p:,.2f}",
                        "change": float(v.get("change", 0.0)), "pct": pct, "volume": float(v.get("baseVolume", 0.0))
                    })
                return {"gainers": sorted(items, key=lambda x: x["pct"], reverse=True)[:10], "losers": sorted(items, key=lambda x: x["pct"])[:10]}
        except Exception: return empty_result

    if category in ["all", "crypto", "binance", "okx", "bybit", "gate", "mexc", "kucoin"]:
        try:
            r = HTTP_SESSION.get("https://api.binance.com/api/v3/ticker/24hr", timeout=4.0)
            if r.status_code == 200:
                usdt_pairs = []
                for item in r.json():
                    s = item.get("symbol", "")
                    if s.endswith("USDT"):
                        p = float(item["lastPrice"])
                        chg = float(item["priceChangePercent"])
                        usdt_pairs.append({
                            "symbol": s, "label": f"{s} ({chg:+.2f}%)",
                            "price": p, "fmt_price": f"{p:,.4f}" if p < 1 else f"{p:,.2f}",
                            "change": float(item["priceChange"]), "pct": chg, "volume": float(item["quoteVolume"])
                        })
                return {"gainers": sorted(usdt_pairs, key=lambda x: x["pct"], reverse=True)[:10], "losers": sorted(usdt_pairs, key=lambda x: x["pct"])[:10]}
        except Exception: return empty_result

    cat_syms = {
        "thai": ["DELTA.BK", "PTT.BK", "AOT.BK", "ADVANC.BK", "GULF.BK", "PTTEP.BK", "BDMS.BK", "CPALL.BK", "SCB.BK", "KBANK.BK"],
        "us": ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", "NFLX", "INTC"],
        "china": ["0700.HK", "9988.HK", "3690.HK", "9618.HK", "9999.HK", "9888.HK", "1810.HK", "2015.HK"],
        "vn": ["VIC.VN", "VHM.VN", "HPG.VN", "FPT.VN", "VNM.VN", "MSN.VN", "TCB.VN", "SSI.VN"],
        "macro": ["GC=F", "CL=F", "BZ=F", "SI=F", "HG=F", "NG=F", "USDTHB=X", "EURUSD=X"]
    }
    targets = cat_syms.get(category, [])
    if not targets: return empty_result

    items = []
    try:
        r = HTTP_SESSION.get(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={','.join(targets)}", timeout=4.0)
        if r.status_code == 200:
            for q in r.json().get("quoteResponse", {}).get("result", []):
                s = q.get("symbol", "")
                p = float(q.get("regularMarketPrice", 0.0))
                pct = float(q.get("regularMarketChangePercent", 0.0))
                if p > 0:
                    name_lbl = CHINA_STOCK_NAMES.get(s, COMMODITY_NAMES.get(s, FOREX_NAMES.get(s, s)))
                    items.append({
                        "symbol": s, "label": f"{name_lbl[:10]} ({pct:+.2f}%)",
                        "price": p, "fmt_price": f"{p:,.4f}" if p < 10 else f"{p:,.2f}",
                        "change": float(q.get("regularMarketChange", 0.0)), "pct": pct, "volume": float(q.get("regularMarketVolume", 0.0))
                    })
    except Exception: pass

    if items:
        return {"gainers": sorted(items, key=lambda x: x["pct"], reverse=True)[:10], "losers": sorted(items, key=lambda x: x["pct"])[:10]}
    return empty_result

def render_watchlist_component(key_prefix: str = "desk"):
    tab_highlight, tab_starred = st.tabs(["🔥 สินทรัพย์โดดเด่น", "⭐ กลุ่มสีโปรด"])
    with tab_highlight:
        market_cats = [
            ("🌐 รวม", "all"), ("🟡 Bitkub", "bitkub"), ("🟡 Binance", "binance"),
            ("🇺🇸 US", "us"), ("🇨🇳 China", "china"), ("🇹🇭 SET", "thai"), ("🇻🇳 VN", "vn"), ("🟠 Macro", "macro")
        ]
        m_labels = [c[0] for c in market_cats]
        m_dict = {c[0]: c[1] for c in market_cats}

        if hasattr(st, "segmented_control"):
            chosen_label = st.segmented_control("เลือกหมวด", m_labels, default=m_labels[0], label_visibility="collapsed", key=f"seg_{key_prefix}") or m_labels[0]
        else:
            chosen_label = st.radio("เลือกหมวด", m_labels, horizontal=True, label_visibility="collapsed", key=f"rad_{key_prefix}")

        selected_code = m_dict[chosen_label]
        movers = fetch_top_movers(selected_code)
        gainers, losers = movers.get("gainers", []), movers.get("losers", [])

        col_g, col_l = st.columns(2)
        with col_g:
            st.markdown("<div style='color:#26a69a; font-weight:700; font-size:11px; margin-bottom:4px;'>🚀 ขาขึ้นแรง</div>", unsafe_allow_html=True)
            for r in gainers:
                c_a, c_b = st.columns([1.6, 1.4])
                with c_a:
                    if st.button(f"{r['label']}", key=f"btn_g_{key_prefix}_{selected_code}_{r['symbol']}", use_container_width=True):
                        cur = _find_tab(st.session_state.active_tab_id)
                        if cur: cur["symbol"] = r["symbol"]
                        st.session_state["current_symbol"] = r["symbol"]
                        _clear_chart_state()
                        st.rerun()
                with c_b:
                    st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px;'><b style='color:#fff;'>{fmt_price(r['price'])}</b> <span style='color:{UP}; font-weight:bold;'>+{r['pct']:.2f}%</span></div>", unsafe_allow_html=True)

        with col_l:
            st.markdown("<div style='color:#ef5350; font-weight:700; font-size:11px; margin-bottom:4px;'>🔻 ขาลงแรง</div>", unsafe_allow_html=True)
            for r in losers:
                c_a, c_b = st.columns([1.6, 1.4])
                with c_a:
                    if st.button(f"{r['label']}", key=f"btn_l_{key_prefix}_{selected_code}_{r['symbol']}", use_container_width=True):
                        cur = _find_tab(st.session_state.active_tab_id)
                        if cur: cur["symbol"] = r["symbol"]
                        st.session_state["current_symbol"] = r["symbol"]
                        _clear_chart_state()
                        st.rerun()
                with c_b:
                    st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px;'><b style='color:#fff;'>{fmt_price(r['price'])}</b> <span style='color:{DOWN}; font-weight:bold;'>{r['pct']:.2f}%</span></div>", unsafe_allow_html=True)

    with tab_starred:
        star_names = list(STAR_CATEGORIES.keys())
        color_tabs = st.tabs(star_names)
        all_starred = set()
        for cat in star_names: all_starred.update(st.session_state["star_watchlists"].get(cat, []))

        starred_quotes = {}
        if all_starred:
            for sym in all_starred: starred_quotes[sym] = fetch_item_quote(sym)

        for idx, cat_name in enumerate(star_names):
            with color_tabs[idx]:
                items = st.session_state["star_watchlists"][cat_name]
                if not items: st.caption("ยังไม่มีสินทรัพย์ในกลุ่มนี้")
                else:
                    for s_item in list(items):
                        q = starred_quotes.get(s_item, fetch_item_quote(s_item))
                        s_lbl = s_item.replace("_THB", "")
                        val_col = UP if q["change"] >= 0 else DOWN
                        c_ico, a, b, c, dcol, f = st.columns([0.6, 1.6, 1.3, 1.1, 1.1, 0.4])
                        with c_ico: st.markdown(build_asset_icon_html(s_item, STAR_CATEGORIES[cat_name]["color"]), unsafe_allow_html=True)
                        with a:
                            if st.button(f"{s_lbl}", key=f"wl_{key_prefix}_{cat_name}_{s_item}", use_container_width=True):
                                cur = _find_tab(st.session_state.active_tab_id)
                                if cur: cur["symbol"] = s_item
                                st.session_state["current_symbol"] = s_item
                                _clear_chart_state()
                                st.rerun()
                        with b: st.markdown(f"<div style='font-family:monospace; font-size:11px; text-align:right; padding-top:4px; color:#fff;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
                        with c: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{fmt_chg(q['change'])}</div>", unsafe_allow_html=True)
                        with dcol: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{q['pct']:+.2f}%</div>", unsafe_allow_html=True)
                        with f:
                            if st.button("✕", key=f"del_{key_prefix}_{cat_name}_{s_item}"):
                                st.session_state["star_watchlists"][cat_name].remove(s_item)
                                st.rerun()

# ──────────────────────────── LOAD SIDEBAR ────────────────────────────
app_config = render_sidebar()

# ──────────────────────────── LIVE TOP BAR ────────────────────────────
@st.fragment(run_every=2)
def render_live_top_bar(r_market: str, r_exchange: str, symbol: str, label_display: str, display_title: str, gz_badge: str, base_price: float, last_vol: float):
    live_tk = fetch_unified_ticker(r_market, r_exchange, symbol)
    cur_price = float(live_tk.get("price", base_price))
    cur_chg = float(live_tk.get("pct", 0.0))
    st.session_state[f"live_price_{symbol}"] = cur_price
    st.session_state[f"live_pct_{symbol}"] = cur_chg

    chg_txt_color = "#26a69a" if cur_chg >= 0 else "#ef5350"
    price_fmt = f"{cur_price:,.4f}" if cur_price < 10 else f"{cur_price:,.2f}"

    ch_left, ch_mid, ch_right = st.columns([6, 3, 3])
    with ch_left:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:16px; height:38px;">'
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<span style="color:#26a69a; font-size:14px;">●</span>'
            f'<span style="color:#FFFFFF; font-weight:700; font-size:16px;">{price_fmt}</span>'
            f'<span style="color:{chg_txt_color}; font-weight:700; font-size:14px;">({cur_chg:+.2f}%)</span>'
            f'<span style="color:#787b86; font-size:11px; margin-left:4px;">Vol {last_vol:,.2f}</span>'
            f'<span style="color:#00bcd4; font-weight:600; font-size:12px;">{display_title}</span>'
            f'<span style="background:#1A1A1A; padding:1px 5px; border-radius:3px; font-size:10px; color:#9aa0a6;">{label_display}</span>'
            f'{gz_badge}'
            f'</div></div>',
            unsafe_allow_html=True
        )
    with ch_right:
        st.markdown('<div style="padding-top:8px; font-size:10px; color:#787b86; text-align:right; padding-right:12px;">● LIVE</div>', unsafe_allow_html=True)

# ──────────────────────────── DASHBOARD (MAIN) ────────────────────────────
def dashboard():
    init_settings_state()
    if st.session_state.get("trigger_settings_modal"):
        st.session_state["trigger_settings_modal"] = False
        show_chart_settings_dialog()
    # กำหนดค่าเริ่มต้นเสมอ ป้องกัน UnboundLocalError เมื่อแถบควบคุมด้านบนถูกปิด
    tf = st.session_state.get("selected_tf", "1h")
    bars = int(st.session_state.get("bars_count", 2500))
    fill_gaps = bool(st.session_state.get("fill_gaps", False))

    # 1. เรนเดอร์แท็บ TradingView Pro (อยู่บนสุด)
    symbol = render_tradingview_clean_tabs()

    # 2. บังคับ Timeframe 1D สำหรับสินค้าเกษตร/ข้าว
    if symbol.startswith("RICE:") or symbol.startswith("FOB:") or symbol == "ZR=F (CBOT Rough Rice)":
        tf = "1D"

    # 3. แถบควบคุม Timeframe / Bars (แสดงใต้แท็บ เมื่อเปิดสวิตช์)
    if app_config.get("show_top_bar", True):
        tb_tf, tb_bars, tb_fill, auto, every, reload_btn = render_top_toolbar()
        bars = tb_bars
        fill_gaps = tb_fill
        if not (symbol.startswith("RICE:") or symbol.startswith("FOB:") or symbol == "ZR=F (CBOT Rough Rice)"):
            tf = tb_tf

    r_market, r_exchange = resolve_route(symbol)
    label_display = route_label(r_market, r_exchange)
    state_key = f"{r_market}_{r_exchange}_{symbol}_{tf}_{bars}_{fill_gaps}"

    if ("df_data" not in st.session_state) or (st.session_state.get("active_key") != state_key):
        with st.spinner(f"กำลังโหลดประวัติ {symbol} ..."):
            if symbol.startswith("RICE:") or symbol.startswith("FOB:") or symbol == "ZR=F (CBOT Rough Rice)":
                df = generate_rice_ohlcv(symbol)
            else:
                df = fetch_ohlcv(r_market, r_exchange, symbol, tf, bars, fill_gaps)
            st.session_state["df_data"] = df
            st.session_state["active_key"] = state_key
    else:
        df = st.session_state.get("df_data", pd.DataFrame())

    if df.empty or len(df) < 3:
        st.warning(f"ไม่พบข้อมูลสำหรับ {symbol}")
        return

    df, stats = diamond_armor(
        df, fast=st.session_state["fast_ema"], slow=st.session_state["slow_ema"],
        trend=st.session_state["trend_ema"], warn_pct=st.session_state["warn_pct"], danger_pct=st.session_state["danger_pct"]
    )

    fib = auto_fib_retracement(df, lookback=st.session_state["fib_lookback"], window=st.session_state["fib_window"]) if auto_fib_retracement else None
    ext = trend_based_fib_extension(df, lookback=st.session_state["fib_lookback"], window=st.session_state["fib_window"]) if auto_fib_retracement else None
    last_close = float(df["close"].iloc[-1])
    fib_zone = current_fib_zone(last_close, fib) if (auto_fib_retracement and fib) else None
    fib_tp = fib_tp_target(last_close, ext, min_tp_pct=st.session_state["min_tp"], preferred_level=st.session_state["fib_tp_level"]) if (auto_fib_retracement and ext) else None

    df_daily = fetch_daily_history(r_market, r_exchange, symbol)
    if df_daily is None or df_daily.empty: df_daily = df.copy()

    tech_data = compute_full_technicals(df_daily)
    seasonality_html = fetch_seasonality_svg(df_daily)
    gauges_html_compact = render_3_gauges_html(tech_data, compact=True)
    gauges_html_modal = render_3_gauges_html(tech_data, compact=False)
    tk_data = fetch_unified_ticker(r_market, r_exchange, symbol, df)

    if st.session_state.get("trigger_fib_modal", False):
        st.session_state["trigger_fib_modal"] = False
        open_fib_dialog(fib, ext, fib_zone, fib_tp, last_close)

    if st.session_state.get("trigger_market_modal", False):
        st.session_state["trigger_market_modal"] = False
        open_market_dialog(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_modal)

    display_title = CHINA_STOCK_NAMES.get(symbol, COMMODITY_NAMES.get(symbol, FOREX_NAMES.get(symbol, symbol)))
    vol_val = float(df.iloc[-1].get("volume", 0.0))

    if app_config.get("show_top_bar", True):
        render_live_top_bar(r_market, r_exchange, symbol, label_display, display_title, "", stats["price"], vol_val)

    cur_main_h = int(st.session_state.get("main_h", 520))
    cur_rsi_h = int(st.session_state.get("rsi_h", 120))
    cur_macd_h = int(st.session_state.get("macd_h", 120))

    charts = build_charts(df, symbol, tf, cur_main_h, cur_rsi_h, cur_macd_h)
    cur_size = st.session_state.get("panel_size", "M")
    chart_dyn_key = f"c_{symbol}_{tf}_{st.session_state.get('active_tab_id', '0')}"
    show_tb = app_config.get("show_draw_toolbar", True)

    # 3. การจัดวางหน้าจอ (Chart vs Quote Panel)
    panel_ratios = {"S": [4.25, 0.75], "M": [3.85, 1.15], "L": [3.40, 1.60]}
    p_open = st.session_state.get("panel_open", True)
    p_size = st.session_state.get("panel_size", "M")

    if p_open:
        col_chart, col_quote = st.columns(panel_ratios.get(p_size, [3.85, 1.15]))
        col_toggle = None
    else:
        col_chart, col_toggle = st.columns([4.92, 0.08])
        col_quote = None

    with col_chart:
        filtered_charts = []
        if charts:
            # 1. กราฟแท่งเทียนหลัก (Main Chart)
            if st.session_state.get("show_main_chart", True):
                c0 = charts[0]
                for s in c0.get("series", []):
                    if s.get("type") == "Candlestick":
                        s.setdefault("options", {})
                        s["options"]["upColor"] = st.session_state.get("candle_up", "#089981")
                        s["options"]["downColor"] = st.session_state.get("candle_down", "#F23645")
                        s["options"]["borderUpColor"] = st.session_state.get("candle_border_up", "#089981")
                        s["options"]["borderDownColor"] = st.session_state.get("candle_border_down", "#F23645")
                        s["options"]["wickUpColor"] = st.session_state.get("candle_wick_up", "#089981")
                        s["options"]["wickDownColor"] = st.session_state.get("candle_wick_down", "#F23645")
                filtered_charts.append(c0)

                      # 2. กรองบานหน้าต่างย่อย พร้อมอัปเดตสี RSI & MACD แบบ Real-time
            for sub in charts[1:]:
                txt = str(sub.get("chart", {}).get("watermark", {}).get("text", "")).upper()
                series_titles = " ".join([str(s.get("title", "")).upper() for s in sub.get("series", [])])
                full_info = txt + " " + series_titles

                # ส่วนของ RSI
                if "RSI" in full_info:
                    if not st.session_state.get("show_rsi_pane", True):
                        continue

                    active_rsi_series = []
                    for s in sub.get("series", []):
                        s.setdefault("options", {})
                        title = str(s.get("title", "")).upper()

                        # 1. เส้นหลัก RSI
                        if "RSI" in title and "MA" not in title:
                            if not st.session_state.get("rsi_show_line", True):
                                continue
                            s["options"]["color"] = st.session_state.get("rsi_line_color", "#B388FF")

                        # 2. เส้น RSI-based MA
                        elif "MA" in title:
                            if not st.session_state.get("rsi_show_ma", True):
                                continue
                            s["options"]["color"] = st.session_state.get("rsi_ma_color", "#FFB74D")

                        active_rsi_series.append(s)

                    sub["series"] = active_rsi_series
                    filtered_charts.append(sub)

                # ส่วนของ MACD
                elif "MACD" in full_info:
                    if not st.session_state.get("show_macd_pane", True):
                        continue
                    for s in sub.get("series", []):
                        s.setdefault("options", {})
                        if s.get("type") == "Line":
                            title = str(s.get("title", "")).upper()
                            if "SIGNAL" in title:
                                s["options"]["color"] = st.session_state.get("macd_signal_color", "#FFEB3B")
                            else:
                                s["options"]["color"] = st.session_state.get("macd_line_color", "#00FFA3")
                    filtered_charts.append(sub)

                else:
                    filtered_charts.append(sub)

        # ผูก key เข้ากับตัวนับ chart_force_refresh เพื่อไม่ให้กราฟค้างหรือสะดุด
        refresh_tick = st.session_state.get("chart_force_refresh", 0)
        render_drawing_chart(
            filtered_charts, 
            height=cur_main_h, 
            key=f"{chart_dyn_key}_v{refresh_tick}", 
            show_toolbar=show_tb
        )

    if col_toggle is not None:
        with col_toggle:
            if st.button("<", key="toggle_panel_btn", help="เปิดแผงขวา", use_container_width=True):
                st.session_state["panel_open"] = True
                st.rerun()

    # 4. แผงควบคุมฝั่งขวา + ปุ่ม Mac 3 สี
    if p_open and col_quote:
        with col_quote:
            st.markdown("""
            <style>
            div[data-baseweb="tooltip"] { display: none !important; }
            .st-key-sz_s button, .st-key-sz_m button, .st-key-sz_l button {
                border: none !important; background: transparent !important;
                box-shadow: none !important; min-height: 24px !important;
                height: 24px !important; padding: 0 !important;
                display: flex !important; align-items: center !important; justify-content: center !important;
            }
            .st-key-sz_s button p, .st-key-sz_m button p, .st-key-sz_l button p { display: none !important; }
            .st-key-sz_s button::before { content: ""; display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #ff5f56 !important; }
            .st-key-sz_m button::before { content: ""; display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #ffbd2e !important; }
            .st-key-sz_l button::before { content: ""; display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #27c93f !important; }
            .st-key-sz_full button { border: none !important; background: transparent !important; box-shadow: none !important; color: #787b86 !important; font-size: 15px !important; height: 24px !important; min-height: 24px !important; }
            .st-key-sz_full button:hover { color: #ffffff !important; }
            </style>
            """, unsafe_allow_html=True)

            c_red, c_yel, c_grn, c_space, c_full = st.columns([0.08, 0.08, 0.08, 0.64, 0.12])
            with c_red:
                if st.button(" ", key="sz_s"):
                    st.session_state["panel_open"] = False if st.session_state.get("panel_size") == "S" else True
                    st.session_state["panel_size"] = "S"
                    st.rerun()
            with c_yel:
                if st.button(" ", key="sz_m"):
                    st.session_state["panel_open"] = True
                    st.session_state["panel_size"] = "M"
                    st.rerun()
            with c_grn:
                if st.button(" ", key="sz_l"):
                    st.session_state["panel_open"] = True
                    st.session_state["panel_size"] = "L"
                    st.rerun()
            with c_full:
                st.button("⛶", key="sz_full")
                components.html("""
                <script>
                const pDoc = window.parent.document;
                function bindFs() {
                    const btn = pDoc.querySelector('.st-key-sz_full button');
                    if (btn && !btn.dataset.bound) {
                        btn.dataset.bound = "true";
                        btn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            if (!pDoc.fullscreenElement) pDoc.documentElement.requestFullscreen().catch(()=>{});
                            else if (pDoc.exitFullscreen) pDoc.exitFullscreen().catch(()=>{});
                        }, true);
                    }
                }
                bindFs();
                setInterval(bindFs, 250);
                </script>
                """, height=0, width=0)

            with st.expander("⭐ รายการสินทรัพย์ & อันดับขาขึ้น-ลง", expanded=True):
                render_watchlist_component(key_prefix="desk")

            with st.expander("📊 ข้อมูลตลาด 24h & เทคนิค", expanded=True):
                if st.button("🔍 ขยายดูตลาด 24h (Pop-up)", key="btn_popup_market_desk", use_container_width=True):
                    st.session_state["trigger_market_modal"] = True
                    st.rerun()
                render_tv_quote_card(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_compact)

if st.session_state.get("app_mode") == "rice":
    render_rice_tab()
else:
    dashboard()