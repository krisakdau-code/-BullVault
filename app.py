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
from chart_builders import build_charts
from ui.dock_menu import render_dock_menu
from ui.asset_tabs import asset_tab_bar
from config import *
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

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #000000 !important;
    }
    
  header[data-testid="stHeader"] {
        background: transparent !important;
        height: 32px !important;
        z-index: 99 !important;
    }
    
    /* บังคับแสดงปุ่มลูกศรเปิด/ปิด Sidebar ฝั่งซ้าย */
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        visibility: visible !important;
        color: #FFFFFF !important;
    }
    
    [data-testid="stToolbar"] {
        right: 1.5rem !important;
        top: 0.4rem !important;
        z-index: 999 !important;
        display: flex !important;
        visibility: visible !important;
    }
    .stDeployButton, #MainMenu {
        display: inline-block !important;
        visibility: visible !important;
    }
    footer, [data-testid="stDecoration"] {
        display: none !important;
    }

    .block-container,
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMainBlockContainer"],
    [data-testid="block-container"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
        margin-left: 0px !important;
        margin-right: 0px !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1E1E1E !important;
    }
    [data-testid="stSidebarContent"] {
        background-color: #050505 !important;
        padding-left: 0.5rem !important; padding-right: 0.5rem !important;
        padding-top: 0.2rem !important; max-height: 100vh !important;
        overflow-y: auto !important; overflow-x: hidden !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }
    [data-testid="stSidebar"] h3 {
        margin-top: -10px !important;
        margin-bottom: 8px !important;
        font-size: 15px !important;
    }
    div[data-testid="stHorizontalBlock"] { 
        gap: 2px !important; 
        align-items: flex-start !important; 
    }
    div[data-testid="column"] { padding: 0 1px !important; }

    .stButton>button {
        background: #101010 !important; color: #D1D4DC !important;
        border: 1px solid #2A2A2A !important; border-radius: 4px !important;
        padding: 2px 4px !important; font-size: 11px !important; font-weight: 500 !important;
        min-height: 24px !important; height: 24px !important; line-height: 1 !important;
    }
    .stButton>button:hover { border-color: #2962FF !important; color: #FFFFFF !important; background: #1A1A1A !important; }

    div[data-testid="stExpander"], .stExpander details {
        border: 1px solid #1E1E1E !important; border-radius: 4px !important;
        background: #0A0A0A !important; margin-bottom: 4px;
    }
    div[data-testid="stExpander"] summary { padding: 3px 8px !important; font-size: 11px !important; }
    div[data-testid="stExpander"] summary p { font-size: 11px !important; font-weight: 600 !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { padding: 4px 6px !important; background-color: #0A0A0A !important; }

    input, select, textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput input {
        background-color: #0D0D0D !important; color: #D1D4DC !important; border: 1px solid #222222 !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 2px; background-color: #000000 !important; padding: 2px; border-radius: 4px; border-bottom: 1px solid #1E1E1E !important; }
    .stTabs [data-baseweb="tab"] { padding: 2px 6px !important; font-size: 11px !important; height: 24px !important; }

    div[data-testid="stRadio"] > div {
        display: flex; flex-direction: row; flex-wrap: wrap; gap: 4px;
    }
    div[data-testid="stRadio"] label {
        background: #0A0A0A; border: 1px solid #222222; border-radius: 4px;
        padding: 2px 6px; font-size: 10px; cursor: pointer; color: #9aa0a6;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #2962FF; color: #fff;
    }

    .tv-wl-header {
        display: grid; grid-template-columns: 0.4fr 0.6fr 1.6fr 1.3fr 1.1fr 1.1fr 0.4fr;
        padding: 4px 2px; font-size: 10px; font-weight: 600; color: #787b86;
        border-bottom: 1px solid #1E1E1E; margin-bottom: 4px;
    }
    .pane-toolbar {
        background: #0A0A0A; border: 1px solid #1E1E1E; border-bottom: none;
        border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 2px 8px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 11px; font-weight: 600; color: #D1D4DC; margin-top: 2px;
    }

    .scrollable-market-card {
        max-height: 72vh;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding-right: 3px;
    }
    .scrollable-market-card::-webkit-scrollbar { width: 4px; }
    .scrollable-market-card::-webkit-scrollbar-thumb { background: #262626; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

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
if "panel_open" not in st.session_state: st.session_state["panel_open"] = True
if "panel_size" not in st.session_state: st.session_state["panel_size"] = "M"

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

# ────────────────── SMART CATALOG LOADER ──────────────────
def get_data_dir():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),
        "data",
        os.path.join(os.getcwd(), "data")
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            return c
    return "data"

def extract_symbols_from_json(content):
    if isinstance(content, list):
        res = []
        for item in content:
            if isinstance(item, str):
                res.append(item)
            elif isinstance(item, dict):
                s = item.get("symbol") or item.get("id") or item.get("ticker") or item.get("code")
                if s: res.append(str(s))
        return res
    elif isinstance(content, dict):
        for k in ["symbols", "tickers", "data", "items"]:
            if k in content and isinstance(content[k], list):
                return extract_symbols_from_json(content[k])
        return [str(k) for k in content.keys()]
    return []

@st.cache_data(ttl=600, show_spinner=False)
def load_catalog_smart(keywords: list) -> list:
    data_dir = get_data_dir()
    if not os.path.exists(data_dir):
        return []
    try:
        all_files = os.listdir(data_dir)
    except Exception:
        return []
    
    matched_files = []
    for f in all_files:
        if not f.endswith(".json"):
            continue
        f_lower = f.lower()
        for kw in keywords:
            if kw.lower() in f_lower:
                matched_files.append(f)
                break
    
    all_syms = []
    for mf in matched_files:
        p = os.path.join(data_dir, mf)
        try:
            with open(p, "r", encoding="utf-8") as file:
                content = json.load(file)
                syms = extract_symbols_from_json(content)
                if syms:
                    all_syms.extend(syms)
        except Exception:
            continue
    
    seen = set()
    clean = []
    for s in all_syms:
        if s and s not in seen:
            seen.add(s)
            clean.append(s)
    return clean

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

    # 1. เหรียญ Bitkub ดึงทิคเกอร์ตรงจาก API
    if ("THB" in symbol) or (exchange == "Bitkub"):
        try:
            r = HTTP_SESSION.get("https://api.bitkub.com/api/market/ticker", timeout=3.0)
            if r.status_code == 200:
                data = r.json()
                k = symbol if symbol.startswith("THB_") else f"THB_{symbol.replace('_THB', '')}"
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
        except Exception:
            pass

    # 2. คำนวณจากแท่งเทียน (Fallback)
    try:
        if df is not None and not df.empty and "close" in df.columns:
            last_p = float(df["close"].iloc[-1])
            prev_p = float(df["close"].iloc[-2]) if len(df) >= 2 else last_p
            chg = last_p - prev_p
            pct = (chg / prev_p * 100.0) if prev_p != 0 else 0.0
            h = float(df["high"].max()) if "high" in df.columns else last_p
            l = float(df["low"].min()) if "low" in df.columns else last_p
            v = float(df["volume"].iloc[-1]) if "volume" in df.columns else 0.0
            tk.update({
                "price": last_p, "change": chg, "pct": pct,
                "high": h, "low": l, "vol": v, "bid": last_p, "ask": last_p
            })
    except Exception:
        pass
    return tk

def fetch_item_quote(sym: str) -> dict:
    try:
        t = fetch_unified_ticker(symbol=sym)
        if t and t.get("price", 0) > 0:
            return t
    except Exception:
        pass
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

def get_symbol_badge(sym: str) -> str:
    s = sym.upper()
    if "BTC" in s: return "₿"
    if "ETH" in s: return "Ξ"
    if "SOL" in s: return "◎"
    if "XRP" in s: return "✕"
    if "DOGE" in s: return "Ð"
    if "ADA" in s: return "₳"
    if "BNB" in s: return "🟡"
    if "GC=F" in s or "GOLD" in s: return "🥇"
    if "CL=F" in s or "BZ=F" in s: return "🛢️"
    if ".BK" in s: return "🇹🇭"
    if ".VN" in s: return "🇻🇳"
    if ".SS" in s or ".SZ" in s or ".HK" in s: return "🇨🇳"
    return "📈"

def render_top_toolbar():
    tabs = st.session_state.open_tabs
    n_tabs = len(tabs)

    widths = [0.3] + [0.95, 0.25] * n_tabs + [0.32, 0.08, 0.65, 1.1, 0.45, 0.45, 0.55, 0.65, 3.5]
    cols = st.columns(widths, gap="small", vertical_alignment="center")

    i = 0
    with cols[i]:
        st.markdown(build_asset_icon_html(st.session_state.current_symbol, size=22), unsafe_allow_html=True)
    i += 1

    now = time.time()
    for tab in tabs:
        tab_id = tab["id"]
        is_active = (tab_id == st.session_state.active_tab_id)
        badge = get_symbol_badge(tab["symbol"])
        try:
            _q = fetch_item_quote(tab["symbol"])
            _p = float(_q.get("price", 0.0))
            _c = float(_q.get("percentChange", _q.get("pct", 0.0)))
            _arr = "▲" if _c >= 0 else "▼"
            _p_str = f"{_p:,.4f}" if _p < 10 else f"{_p:,.2f}"
            _chg_str = f"{_c:+.2f}%"
            tab_label = f"{badge} {tab['symbol'].replace('_', '')} {_arr}{_p_str} {_chg_str}"
        except Exception:
            tab_label = f"{badge} {tab['symbol']}"

        with cols[i]:
            if st.button(tab_label, key=f"tab_btn_{tab_id}", type="primary" if is_active else "secondary", use_container_width=True):
                last_time = st.session_state.get(f"last_click_{tab_id}", 0)
                if (now - last_time) < 0.4:
                    st.session_state[f"last_click_{tab_id}"] = 0
                    add_tab(tab["symbol"])
                else:
                    st.session_state[f"last_click_{tab_id}"] = now
                    switch_tab(tab_id)
            i += 1

        with cols[i]:
            if st.button("✕", key=f"tab_close_{tab_id}", disabled=(n_tabs <= 1), use_container_width=True):
                close_tab(tab_id)
        i += 1

    with cols[i]:
        if st.button("➕", key="tab_add_btn", use_container_width=True, help="เปิดแท็บใหม่"):
            add_tab(st.session_state.current_symbol)
    i += 1

    with cols[i]:
        tf = st.selectbox("TF", TF_OPTIONS, index=TF_OPTIONS.index(st.session_state.selected_tf) if st.session_state.selected_tf in TF_OPTIONS else 5, key="tf_select", label_visibility="collapsed")
        if tf != st.session_state.selected_tf:
            st.session_state.selected_tf = tf
            cur = _find_tab(st.session_state.active_tab_id)
            if cur: cur["tf"] = tf
            _clear_chart_state()
            st.rerun()
    i += 1

    with cols[i]:
        bars = st.slider("Bars", 300, 25000, int(st.session_state.get("bars_count", 2500)), 500, label_visibility="collapsed", key="bars_count")
    i += 1

    with cols[i]:
        fill_gaps = st.checkbox("Fill", value=st.session_state.get("fill_gaps", False), key="fill_gaps")
    i += 1

    with cols[i]:
        auto = st.checkbox("Auto", value=st.session_state.get("auto_refresh", False), key="auto_refresh")
    i += 1

    with cols[i]:
        every = st.number_input("Sec", min_value=2, max_value=60, value=int(st.session_state.get("refresh_sec", 5)), step=1, label_visibility="collapsed", key="refresh_sec")
    i += 1

    with cols[i]:
        reload_btn = st.button("🔄 โหลด", key="load_btn", use_container_width=True)
    i += 1

    with cols[i]:
        st.empty()

    return tf, bars, fill_gaps, auto, every, reload_btn

@st.cache_data(ttl=30, show_spinner=False)
def fetch_top_movers(category: str = "all") -> dict:
    empty_result = {"gainers": [], "losers": []}

    # 1. กลุ่ม BITKUB
    if category == "bitkub":
        try:
            r = HTTP_SESSION.get("https://api.bitkub.com/api/market/ticker", timeout=4.0)
            if r.status_code == 200:
                data = r.json()
                items = []
                for sym_code, v in data.items():
                    if not sym_code.startswith("THB_"):
                        continue
                    p = float(v.get("last", 0.0))
                    pct = float(v.get("percentChange", 0.0))
                    vol = float(v.get("baseVolume", 0.0))
                    clean_name = sym_code.replace("THB_", "") + "_THB"
                    items.append({
                        "symbol": clean_name,
                        "label": f"{clean_name} ({pct:+.2f}%)",
                        "price": p,
                        "fmt_price": f"{p:,.4f}" if p < 10 else f"{p:,.2f}",
                        "change": float(v.get("change", 0.0)),
                        "pct": pct,
                        "volume": vol
                    })
                gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
                losers = sorted(items, key=lambda x: x["pct"])[:10]
                return {"gainers": gainers, "losers": losers}
        except Exception:
            return empty_result

    # 2. กลุ่ม BINANCE & คริปโตสากล
    if category in ["all", "crypto", "binance", "okx", "bybit", "gate", "mexc", "kucoin"]:
        try:
            r = HTTP_SESSION.get("https://api.binance.com/api/v3/ticker/24hr", timeout=4.0)
            if r.status_code == 200:
                res = r.json()
                usdt_pairs = []
                for item in res:
                    s = item.get("symbol", "")
                    if s.endswith("USDT"):
                        p = float(item["lastPrice"])
                        chg = float(item["priceChangePercent"])
                        usdt_pairs.append({
                            "symbol": s,
                            "label": f"{s} ({chg:+.2f}%)",
                            "price": p,
                            "fmt_price": f"{p:,.4f}" if p < 1 else f"{p:,.2f}",
                            "change": float(item["priceChange"]),
                            "pct": chg,
                            "volume": float(item["quoteVolume"])
                        })
                gainers = sorted(usdt_pairs, key=lambda x: x["pct"], reverse=True)[:10]
                losers = sorted(usdt_pairs, key=lambda x: x["pct"])[:10]
                return {"gainers": gainers, "losers": losers}
        except Exception:
            return empty_result

    # 3. กลุ่ม หุ้นไทย / สหรัฐฯ / จีน / เวียดนาม / โภคภัณฑ์ & FX
    cat_syms = {
        "thai": ["DELTA.BK", "PTT.BK", "AOT.BK", "ADVANC.BK", "GULF.BK", "PTTEP.BK", "BDMS.BK", "CPALL.BK", "SCB.BK", "KBANK.BK", "TRUE.BK", "SCC.BK", "BBL.BK", "CPAXT.BK", "BH.BK", "TIDLOR.BK", "MINT.BK", "HMPRO.BK", "IVL.BK", "MTC.BK"],
        "us": ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", "NFLX", "INTC", "PLTR", "COIN", "AVGO", "QCOM", "BABA", "ARM", "MU", "PANW", "SNOW", "UBER"],
        "china": ["0700.HK", "9988.HK", "3690.HK", "9618.HK", "9999.HK", "9888.HK", "1810.HK", "2015.HK", "9866.HK", "9868.HK", "002594.SZ", "300750.SZ", "600519.SS", "601398.SS"],
        "vn": ["VIC.VN", "VHM.VN", "HPG.VN", "FPT.VN", "VNM.VN", "MSN.VN", "TCB.VN", "SSI.VN", "MBB.VN", "MWG.VN", "AAA.VN", "DGC.VN"],
        "macro": ["GC=F", "CL=F", "BZ=F", "SI=F", "HG=F", "NG=F", "USDTHB=X", "EURUSD=X", "USDJPY=X", "GBPUSD=X"]
    }

    targets = cat_syms.get(category, [])
    if not targets:
        return empty_result

    items = []
    try:
        sym_str = ",".join(targets)
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={sym_str}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = HTTP_SESSION.get(url, headers=headers, timeout=4.0)
        if r.status_code == 200:
            res = r.json().get("quoteResponse", {}).get("result", [])
            for q in res:
                s = q.get("symbol", "")
                p = float(q.get("regularMarketPrice", 0.0))
                pct = float(q.get("regularMarketChangePercent", 0.0))
                chg = float(q.get("regularMarketChange", 0.0))
                vol = float(q.get("regularMarketVolume", 0.0))
                if p > 0:
                    name_lbl = CHINA_STOCK_NAMES.get(s, COMMODITY_NAMES.get(s, FOREX_NAMES.get(s, s)))
                    items.append({
                        "symbol": s,
                        "label": f"{name_lbl[:10]} ({pct:+.2f}%)",
                        "price": p,
                        "fmt_price": f"{p:,.4f}" if p < 10 else f"{p:,.2f}",
                        "change": chg,
                        "pct": pct,
                        "volume": vol
                    })
    except Exception:
        pass

    if items:
        gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
        losers = sorted(items, key=lambda x: x["pct"])[:10]
        return {"gainers": gainers, "losers": losers}

    return empty_result

def render_watchlist_component(key_prefix: str = "desk"):
    tab_highlight, tab_starred = st.tabs(["🔥 สินทรัพย์โดดเด่น", "⭐ กลุ่มสีโปรด"])

    with tab_highlight:
        market_cats = [
            ("🌐 รวมทุกตลาด", "all"),
            ("🟡 คริปโต (Bitkub)", "bitkub"),
            ("🟡 คริปโต (Binance)", "binance"),
            ("🟡 คริปโต (OKX)", "okx"),
            ("🟡 คริปโต (Bybit)", "bybit"),
            ("🟡 คริปโต (Gate.io)", "gate"),
            ("🟡 คริปโต (MEXC)", "mexc"),
            ("🟡 คริปโต (KuCoin)", "kucoin"),
            ("🇺🇸 หุ้นสหรัฐฯ", "us"),
            ("🇨🇳 หุ้นจีน", "china"),
            ("🇹🇭 หุ้นไทย (SET)", "thai"),
            ("🇻🇳 หุ้นเวียดนาม", "vn"),
            ("🟠 โภคภัณฑ์ & FX", "macro")
        ]
        m_labels = [c[0] for c in market_cats]
        m_dict = {c[0]: c[1] for c in market_cats}

        if hasattr(st, "segmented_control"):
            chosen_label = st.segmented_control("เลือกหมวดหมู่ตลาด", m_labels, default=m_labels[0], label_visibility="collapsed", key=f"seg_{key_prefix}") or m_labels[0]
        else:
            chosen_label = st.radio("เลือกหมวดหมู่ตลาด", m_labels, horizontal=True, label_visibility="collapsed", key=f"rad_{key_prefix}")

        selected_code = m_dict[chosen_label]
        movers = fetch_top_movers(selected_code)
        gainers, losers = movers.get("gainers", []), movers.get("losers", [])

        col_g, col_l = st.columns(2)
        with col_g:
            st.markdown("<div style='color:#26a69a; font-weight:700; font-size:11px; margin-bottom:4px;'>🚀 10 อันดับ ขาขึ้นแรง</div>", unsafe_allow_html=True)
            if not gainers: st.caption("ไม่มีข้อมูล หรืออยู่นอกเวลาทำการ")
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
            st.markdown("<div style='color:#ef5350; font-weight:700; font-size:11px; margin-bottom:4px;'>🔻 10 อันดับ ขาลงแรง</div>", unsafe_allow_html=True)
            if not losers: st.caption("ไม่มีข้อมูล หรืออยู่นอกเวลาทำการ")
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
        for cat in star_names:
            all_starred.update(st.session_state["star_watchlists"].get(cat, []))

        starred_quotes = {}
        if all_starred:
            futures = {THREAD_POOL_EXECUTOR.submit(fetch_item_quote, sym): sym for sym in all_starred}
            for future in concurrent.futures.as_completed(futures):
                s_sym = futures[future]
                try:
                    res = future.result(timeout=1.5)
                    if res: starred_quotes[s_sym] = res
                except Exception:
                    pass

        for idx, cat_name in enumerate(star_names):
            with color_tabs[idx]:
                items = st.session_state["star_watchlists"][cat_name]
                if not items:
                    st.caption("ยังไม่มีสินทรัพย์ในกลุ่มสีนี้ (กดปุ่มสีที่ Sidebar เพื่อติดตาม)")
                else:
                    st.markdown("""<div class="tv-wl-header">
                        <span>สถ.</span><span></span><span>สัญลักษณ์</span><span style="text-align:right;">ล่าสุด</span>
                        <span style="text-align:right;">เปลี่ยน</span><span style="text-align:right;">เปลี่ยน%</span><span></span>
                    </div>""", unsafe_allow_html=True)

                    for s_item in list(items):
                        q = starred_quotes.get(s_item, fetch_item_quote(s_item))
                        s_lbl = CHINA_STOCK_NAMES.get(s_item, COMMODITY_NAMES.get(s_item, FOREX_NAMES.get(s_item, s_item.replace("_THB","").replace("-USDT","").replace("USDT","").replace(".BK","").replace(".VN",""))))
                        val_col = UP if q["change"] >= 0 else DOWN
                        sign = "+" if q["change"] >= 0 else ""
                        tag_color = STAR_CATEGORIES[cat_name]["color"]

                        abs_pct = abs(q["pct"])
                        status_dot = "🔴" if abs_pct >= st.session_state.get("danger_pct", 7.0) else ("🟠" if abs_pct >= st.session_state.get("warn_pct", 3.0) else "🟢")

                        c_stat, c_ico, a, b, c, dcol, f = st.columns([0.4, 0.6, 1.6, 1.3, 1.1, 1.1, 0.4])
                        with c_stat: st.markdown(f"<div style='font-size:10px; padding-top:4px;'>{status_dot}</div>", unsafe_allow_html=True)
                        with c_ico: st.markdown(build_asset_icon_html(s_item, tag_color), unsafe_allow_html=True)
                        with a:
                            if st.button(f"{s_lbl}", key=f"wl_{key_prefix}_{cat_name}_{s_item}", use_container_width=True):
                                cur = _find_tab(st.session_state.active_tab_id)
                                if cur: cur["symbol"] = s_item
                                st.session_state["current_symbol"] = s_item
                                _clear_chart_state()
                                st.rerun()
                        with b: st.markdown(f"<div style='font-family:monospace; font-size:11px; text-align:right; padding-top:4px; color:#fff;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
                        with c: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{fmt_chg(q['change'])}</div>", unsafe_allow_html=True)
                        with dcol: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{sign}{q['pct']:.2f}%</div>", unsafe_allow_html=True)
                        with f:
                            if st.button("✕", key=f"del_{key_prefix}_{cat_name}_{s_item}", help="ลบออก"):
                                st.session_state["star_watchlists"][cat_name].remove(s_item)
                                st.rerun()

# ──────────────────────────── SIDEBAR ────────────────────────────
with st.sidebar:
    render_dock_menu()

# ──────────────────────────── LIVE TOP BAR FRAGMENT ────────────────────────────
@st.fragment(run_every=2)
def render_live_top_bar(r_market: str, r_exchange: str, symbol: str, label_display: str, display_title: str, gz_badge: str, base_price: float, last_vol: float):
    live_tk = fetch_unified_ticker(r_market, r_exchange, symbol)
    cur_price = float(live_tk.get("price", base_price))
    cur_chg = float(live_tk.get("pct", 0.0))
    
    # ─── บันทึกค่ากลางลงใน Session State (SSOT Pattern) ───
    st.session_state[f"live_price_{symbol}"] = cur_price
    st.session_state[f"live_pct_{symbol}"] = cur_chg
    st.session_state[f"live_high_{symbol}"] = float(live_tk.get("high", cur_price))
    st.session_state[f"live_low_{symbol}"] = float(live_tk.get("low", cur_price))
    # ──────────────────────────────────────────────────────

    chg_txt_color = "#26a69a" if cur_chg >= 0 else "#ef5350"
    price_fmt = f"{cur_price:,.4f}" if cur_price < 10 else f"{cur_price:,.2f}"
    bid_p = float(live_tk.get("bid", cur_price))
    bid_fmt = f"{bid_p:,.4f}" if bid_p < 10 else f"{bid_p:,.2f}"
    ask_p = float(live_tk.get("ask", cur_price))
    ask_fmt = f"{ask_p:,.4f}" if ask_p < 10 else f"{ask_p:,.2f}"
    spread_p = abs(ask_p - bid_p)
    spread_fmt = f"{spread_p:,.4f}" if spread_p < 1 else f"{spread_p:,.2f}"

    fs_script = """
    <script>
        const btn = document.getElementById('tvFsBtn');
        if (btn && !btn.hasAttribute('data-bound')) {
            btn.setAttribute('data-bound', 'true');
            btn.addEventListener('click', () => {
                const doc = window.parent.document;
                if (!doc.fullscreenElement) {
                    doc.documentElement.requestFullscreen().catch(e => {});
                    btn.innerText = "🗗 ย่อจอ";
                } else {
                    if (doc.exitFullscreen) { doc.exitFullscreen().catch(e => {}); }
                    btn.innerText = "⛶ เต็มจอ";
                }
            });
        }
    </script>
    """

    top_bar_html = f"""
    <div style="background-color:#0A0A0A; border:1px solid #1E1E1E; border-radius:4px; padding:6px 12px; font-family:-apple-system,BlinkMacSystemFont,monospace; color:#D1D4DC; display:flex; justify-content:space-between; align-items:center; width:100%; box-sizing:border-box;">
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="color:#26a69a; font-size:14px;">●</span>
                <span style="color:#FFFFFF; font-weight:700; font-size:16px;">{price_fmt}</span>
                <span style="color:{chg_txt_color}; font-weight:700; font-size:14px;">({cur_chg:+.2f}%)</span>
                <span style="color:#787b86; font-size:11px; margin-left:4px;">ปริมาณ {last_vol:,.2f}</span>
                <span style="color:#00bcd4; font-weight:600; font-size:12px;">{display_title}</span>
                <span style="background:#1A1A1A; padding:1px 5px; border-radius:3px; font-size:10px; color:#9aa0a6;">{label_display}</span>
                {gz_badge}
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="border:1px solid #ef5350; border-radius:4px; padding:2px 8px; text-align:center; min-width:55px; background:rgba(239,83,80,0.08);">
                    <div style="color:#ef5350; font-weight:bold; font-size:11px;">{bid_fmt}</div>
                    <div style="color:#ef5350; font-size:9px;">ขาย</div>
                </div>
                <div style="font-size:10px; color:#787b86; font-family:monospace;">{spread_fmt}</div>
                <div style="border:1px solid #2962ff; border-radius:4px; padding:2px 8px; text-align:center; min-width:55px; background:rgba(41,98,255,0.08);">
                    <div style="color:#2962ff; font-weight:bold; font-size:11px;">{ask_fmt}</div>
                    <div style="color:#2962ff; font-size:9px;">ซื้อ</div>
                </div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
            <span style="font-size:10px; color:#787b86;">● LIVE TICK</span>
            <button id="tvFsBtn" style="background:#161a21; border:1px solid #2a2e39; color:#d1d4dc; border-radius:4px; font-size:11px; font-weight:bold; padding:2px 8px; cursor:pointer; height:24px;" title="โหมดเต็มหน้าจอ">⛶ เต็มจอ</button>
        </div>
    </div>""" + fs_script
    components.html(top_bar_html, height=52)

# ──────────────────────────── DASHBOARD (STATIC GRAPH) ────────────────────────────
@st.fragment
def dashboard():
    tf, bars, fill_gaps, auto, every, reload_btn = render_top_toolbar()

    symbol = st.session_state.get("current_symbol", "BTC_THB")
    tabs_data = st.session_state.get("open_tabs", st.session_state.get("tabs", []))
    if tabs_data and isinstance(tabs_data[0], dict):
        SYMBOLS = [t.get("symbol") for t in tabs_data if t.get("symbol")]
    elif tabs_data and isinstance(tabs_data[0], str):
        SYMBOLS = tabs_data
    else:
        SYMBOLS = [symbol]

    if symbol not in SYMBOLS:
        SYMBOLS.insert(0, symbol)

    active_symbol = asset_tab_bar(SYMBOLS, state_key="current_symbol")
    symbol = active_symbol or symbol
    st.divider()

    r_market, r_exchange = resolve_route(symbol)
    label_display = route_label(r_market, r_exchange)

    state_key = f"{r_market}_{r_exchange}_{symbol}_{tf}_{bars}_{fill_gaps}"
    
    if ("df_data" not in st.session_state) or (st.session_state.get("active_key") != state_key) or reload_btn:
        with st.spinner(f"กำลังโหลดประวัติ {symbol} ({bars:,} แท่ง) ..."):
            df = fetch_ohlcv(r_market, r_exchange, symbol, tf, bars, fill_gaps)
            st.session_state["df_data"] = df
            st.session_state["active_key"] = state_key
    else:
        df = st.session_state.get("df_data", pd.DataFrame())

    if df.empty or len(df) < 3:
        st.warning(f"ไม่พบข้อมูลสำหรับ {symbol} ({label_display})")
        return

    df, stats = diamond_armor(
        df,
        fast=st.session_state["fast_ema"],
        slow=st.session_state["slow_ema"],
        trend=st.session_state["trend_ema"],
        warn_pct=st.session_state["warn_pct"],
        danger_pct=st.session_state["danger_pct"]
    )

    fib_lookback = st.session_state["fib_lookback"]
    fib_window = st.session_state["fib_window"]
    fib_tp_level = st.session_state["fib_tp_level"]
    fib_confirm = st.session_state["fib_confirm_on"]

    fib = auto_fib_retracement(df, lookback=fib_lookback, window=fib_window) if auto_fib_retracement else None
    ext = trend_based_fib_extension(df, lookback=fib_lookback, window=fib_window) if auto_fib_retracement else None
    
    last_close = float(df["close"].iloc[-1])
    fib_zone = current_fib_zone(last_close, fib) if (auto_fib_retracement and fib) else None
    fib_tp = fib_tp_target(last_close, ext, min_tp_pct=st.session_state["min_tp"], preferred_level=fib_tp_level) if (auto_fib_retracement and ext) else None

    is_in_gz = near_golden_zone(last_close, fib) if fib else False
    if fib_confirm and fib and auto_fib_retracement:
        for b_idx in df.tail(15).index:
            if df.loc[b_idx, "signal"] == "BUY" and not near_golden_zone(float(df.loc[b_idx, "close"]), fib):
                df.loc[b_idx, "signal"] = ""

    df_daily = fetch_daily_history(r_market, r_exchange, symbol)
    if df_daily is None or df_daily.empty or len(df_daily) < 15:
        df_daily = df.copy()

    tech_data = compute_full_technicals(df_daily)
    if not tech_data or "1W" not in tech_data:
        an_fb = fetch_market_analytics(df)
        if tech_data: tech_data.update(an_fb)
        else: tech_data = an_fb

    seasonality_html = fetch_seasonality_svg(df_daily)
    gauges_html_compact = render_3_gauges_html(tech_data, compact=True)
    gauges_html_modal = render_3_gauges_html(tech_data, compact=False)
    tk_data = fetch_unified_ticker(r_market, r_exchange, symbol, df)
    
    # ─── ดึงค่าจาก State กลางมาใช้เพื่อให้ตัวเลขตรงกัน 100% ───
    if f"live_price_{symbol}" in st.session_state:
        tk_data["price"] = st.session_state[f"live_price_{symbol}"]
        tk_data["pct"] = st.session_state[f"live_pct_{symbol}"]
    # ────────────────────────────────────────────────────────

    if st.session_state.get("trigger_fib_modal", False):
        st.session_state["trigger_fib_modal"] = False
        open_fib_dialog(fib, ext, fib_zone, fib_tp, last_close)

    if st.session_state.get("trigger_market_modal", False):
        st.session_state["trigger_market_modal"] = False
        open_market_dialog(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_modal)

    display_title = CHINA_STOCK_NAMES.get(symbol, COMMODITY_NAMES.get(symbol, FOREX_NAMES.get(symbol, symbol)))

    gz_badge = ""
    if fib_confirm and fib:
        if is_in_gz:
            gz_badge = '&nbsp;|&nbsp;<span style="background:rgba(38,166,154,0.18);color:#26a69a;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:bold;">🎯 Golden Zone ยืนยันแล้ว</span>'
        else:
            gz_badge = '&nbsp;|&nbsp;<span style="background:rgba(255,152,0,0.18);color:#ff9800;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:bold;">⏳ รอราคาเข้า Golden Zone</span>'

    vol_val = float(df.iloc[-1].get("volume", 0.0))

    render_live_top_bar(
        r_market, r_exchange, symbol, label_display, display_title,
        gz_badge, stats["price"], vol_val
    )

    cur_main_h = int(st.session_state.get("main_h", 520))
    cur_rsi_h = int(st.session_state.get("rsi_h", 120))
    cur_macd_h = int(st.session_state.get("macd_h", 120))

    charts = build_charts(df, symbol, tf, cur_main_h, cur_rsi_h, cur_macd_h)
    cur_size = st.session_state.get("panel_size", "M")
    chart_dyn_key = f"c_{symbol}_{tf}_{st.session_state.get('active_tab_id', '0')}"
    show_tb = st.session_state.get("show_drawing_toolbar", True)

    # --- ส่วนที่ 1: โหมดมือถือ (Mobile Mode) ---
    if st.session_state.get("mobile_mode", False):
        layout_ratios_mob = {
            "S": [4.88, 0.12],
            "M": [3.5, 0.12, 1.38],
            "L": [2.8, 0.12, 2.08]
        }
        if st.session_state.get("panel_open", True):
            col_chart, col_toggle, col_quote = st.columns(layout_ratios_mob[cur_size])
        else:
            col_chart, col_toggle = st.columns([4.88, 0.12])
            col_quote = None

        with col_chart:
            render_drawing_chart(
                charts,
                height=cur_main_h,
                key=chart_dyn_key,
                show_toolbar=show_tb
            )

        with col_toggle:
            btn_label = ">" if st.session_state.get("panel_open", True) else "<"
            if st.button(btn_label, key="toggle_panel_btn_mob", help="ย่อ/ขยายแผงขวา", use_container_width=True):
                st.session_state["panel_open"] = not st.session_state.get("panel_open", True)
                st.rerun()

        if st.session_state.get("panel_open", True) and col_quote:
            with col_quote:
                with st.expander("⭐ รายการสินทรัพย์ & อันดับขาขึ้น-ลง", expanded=True):
                    render_watchlist_component(key_prefix="mob")
                with st.expander("📊 ข้อมูลตลาด 24h & เทคนิค", expanded=True):
                    if st.button("🔍 ขยายดูตลาด 24h (Pop-up)", key="btn_popup_market_mob", use_container_width=True):
                        st.session_state["trigger_market_modal"] = True
                        st.rerun()
                    render_tv_quote_card(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_compact)
        return

    # --- ส่วนที่ 2: โหมดคอมพิวเตอร์ (Desktop Mode) ---
    layout_ratios = {
        "S": [4.1, 0.12, 0.78],
        "M": [3.6, 0.12, 1.28],
        "L": [3.1, 0.12, 1.78]
    }

    if st.session_state.get("panel_open", True):
        col_chart, col_toggle, col_quote = st.columns(layout_ratios[cur_size])
    else:
        col_chart, col_toggle = st.columns([4.88, 0.12])
        col_quote = None

    with col_chart:
        render_drawing_chart(
            charts,
            height=cur_main_h,
            key=chart_dyn_key,
            show_toolbar=show_tb
        )

    with col_toggle:
        btn_label = ">" if st.session_state.get("panel_open", True) else "<"
        if st.button(btn_label, key="toggle_panel_btn", help="ย่อ/ขยายแผงขวา", use_container_width=True):
            st.session_state["panel_open"] = not st.session_state.get("panel_open", True)
            st.rerun()

    if st.session_state.get("panel_open", True) and col_quote:
        with col_quote:
            cs_col1, cs_col2, cs_col3 = st.columns(3)
            with cs_col1:
                if st.button("เล็ก", use_container_width=True, key="sz_s"):
                    st.session_state["panel_size"] = "S"
                    st.rerun()
            with cs_col2:
                if st.button("ปกติ", use_container_width=True, key="sz_m"):
                    st.session_state["panel_size"] = "M"
                    st.rerun()
            with cs_col3:
                if st.button("กว้าง", use_container_width=True, key="sz_l"):
                    st.session_state["panel_size"] = "L"
                    st.rerun()

            with st.expander("⭐ รายการสินทรัพย์ & อันดับขาขึ้น-ลง", expanded=True):
                render_watchlist_component(key_prefix="desk")

            with st.expander("📊 ข้อมูลตลาด 24h & เทคนิค", expanded=True):
                if st.button("⛶ ขยายดูตลาด 24h (Pop-up)", key="btn_popup_market_desk", use_container_width=True):
                    st.session_state["trigger_market_modal"] = True
                    st.rerun()
                render_tv_quote_card(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_compact)

dashboard()