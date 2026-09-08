# app.py — Universal Trading Terminal (Hybrid Ultra Edition)
import os
import time
import datetime
import requests
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import json
import uuid
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from streamlit_lightweight_charts_ntf import renderLightweightCharts
from ui_components import render_tv_clickable_tabs

try:
    import symbols
except ImportError:
    symbols = None


def _has_data(series_list) -> bool:
    for s in series_list or []:
        data = s.get("data") or []
        for p in data:
            v = p.get("value", p.get("close"))
            if v is not None and v == v:   # กรอง None และ NaN
                return True
    return False

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from fib_tools import (
        auto_fib_retracement, trend_based_fib_extension, fib_time_zones,
        fib_tp_target, current_fib_zone, near_golden_zone
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
    
    header[data-testid="stHeader"], [data-testid="stHeader"] {
        display: none !important;
        height: 0px !important;
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



def _fetch_url_with_timeout(url: str, timeout: float = 1.5) -> requests.Response | None:
    try:
        return HTTP_SESSION.get(url, timeout=timeout)
    except Exception:
        return None

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

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_set_all_symbols() -> list[str]:
    paths = [os.path.join("data", "thai_stocks.json"), "c:\\Users\\admin\\Desktop\\แอปทำเอง\\data\\thai_stocks.json"]
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return sorted(data)
        except Exception:
            continue
    return sorted([
        "ADVANC.BK", "AOT.BK", "AWC.BK", "BAM.BK", "BBL.BK", "BDMS.BK", "BEM.BK", "BGRIM.BK",
        "BH.BK", "BJC.BK", "BTS.BK", "CBG.BK", "CENTEL.BK", "CPALL.BK", "CPAXT.BK", "CPF.BK",
        "CPN.BK", "CRC.BK", "DELTA.BK", "EA.BK", "EGCO.BK", "GLOBAL.BK", "GPSC.BK", "GULF.BK",
        "HANA.BK", "HMPRO.BK", "INTUCH.BK", "IVL.BK", "KBANK.BK", "KCE.BK", "KKP.BK", "KTB.BK",
        "KTC.BK", "LH.BK", "MINT.BK", "MTC.BK", "OR.BK", "OSP.BK", "PTT.BK", "PTTEP.BK", "PTTGC.BK",
        "RATCH.BK", "SAWAD.BK", "SCB.BK", "SCC.BK", "SCGP.BK", "TCAP.BK", "TIDLOR.BK", "TISCO.BK",
        "TOP.BK", "TRUE.BK", "TTB.BK", "TU.BK", "WHA.BK"
    ])

def get_full_bitkub_symbols() -> list[str]:
    if symbols and hasattr(symbols, "bitkub_symbols"):
        res = symbols.bitkub_symbols()
        if isinstance(res, list) and len(res) > 0: return res
    return ["BTC_THB", "ETH_THB", "SOL_THB", "XRP_THB", "DOGE_THB", "ADA_THB"]

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_binance_symbols() -> list[str]:
    if symbols and hasattr(symbols, "binance_symbols"):
        res = symbols.binance_symbols()
        if isinstance(res, list) and len(res) > 0: return res
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"]

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_sp500_symbols() -> list[str]:
    paths = [os.path.join("data", "us_stocks.json"), "c:\\Users\\admin\\Desktop\\แอปทำเอง\\data\\us_stocks.json"]
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return sorted(data)
        except Exception:
            continue
    return sorted([
        "AAPL", "ABBV", "ABNB", "ADBE", "ADI", "AMD", "AMZN", "ARM", "ASML", "AVGO", "BA", "BAC",
        "BRK-B", "C", "CAT", "CCJ", "CEG", "COIN", "CRM", "CRWD", "CSCO", "CVX", "DIS", "GOOG", "GOOGL", "GS",
        "HD", "IBM", "INTC", "IONQ", "JNJ", "JPM", "KO", "LLY", "LUNR", "MA", "MCD", "META",
        "MSFT", "MSTR", "NFLX", "NKE", "NVDA", "OKLO", "ORCL", "PEP", "PFE", "PG", "PLTR", "QCOM",
        "RKLB", "SBUX", "SMCI", "SMR", "TSLA", "TSM", "TXN", "UNH", "V", "VRT", "WFC", "WMT", "XOM"
    ])

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_china_stocks() -> list[str]:
    paths = [os.path.join("data", "china_stocks.json"), "c:\\Users\\admin\\Desktop\\แอปทำเอง\\data\\china_stocks.json"]
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return sorted(data)
        except Exception:
            continue
    return sorted(list(CHINA_STOCK_NAMES.keys()))

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_vietnam_symbols() -> list[str]:
    paths = [os.path.join("data", "vietnam_stocks.json"), "c:\\Users\\admin\\Desktop\\แอปทำเอง\\data\\vietnam_stocks.json"]
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return sorted(data)
        except Exception:
            continue
    return sorted(["AAA.VN", "HPG.VN", "VIC.VN", "VHM.VN", "FPT.VN", "VNM.VN", "SSI.VN", "TCB.VN", "MWG.VN"])

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_commodities() -> list[str]:
    return sorted(list(COMMODITY_NAMES.keys()))

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_forex() -> list[str]:
    return sorted(list(FOREX_NAMES.keys()))

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_okx_symbols() -> list[str]:
    with open(os.path.join("data", "okx_crypto.json"), "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_bybit_symbols() -> list[str]:
    with open(os.path.join("data", "bybit_crypto.json"), "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_gate_symbols() -> list[str]:
    with open(os.path.join("data", "gate_crypto.json"), "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_mexc_symbols() -> list[str]:
    with open(os.path.join("data", "mexc_crypto.json"), "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=86400, show_spinner=False)
def get_full_kucoin_symbols() -> list[str]:
    with open(os.path.join("data", "kucoin_crypto.json"), "r", encoding="utf-8") as f:
        return json.load(f)


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
    st.session_state["selected_symbol_picker"] = tab["symbol"]
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
if "auto_refresh" not in st.session_state: st.session_state["auto_refresh"] = False
if "refresh_sec" not in st.session_state: st.session_state["refresh_sec"] = 5

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

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

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

def _fetch_url_with_timeout(url: str, timeout: float = 1.5) -> requests.Response | None:
    try:
        return HTTP_SESSION.get(url, timeout=timeout)
    except Exception:
        return None
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

def rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)

def diamond_armor(df: pd.DataFrame, fast=7, slow=13, trend=45, rsi_len=14, macd_f=12, macd_s=26, macd_sig=9, warn_pct=3.0, danger_pct=7.0):
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["ema_trend"] = df["close"].ewm(span=trend, adjust=False).mean()
    df["rsi"] = rsi_wilder(df["close"], rsi_len)
    df["ema12"] = df["close"].ewm(span=macd_f, adjust=False).mean()
    df["ema26"] = df["close"].ewm(span=macd_s, adjust=False).mean()
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_sig"] = df["macd"].ewm(span=macd_sig, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    up_cross = (df.ema_fast > df.ema_slow) & (df.ema_fast.shift() <= df.ema_slow.shift())
    dn_cross = (df.ema_fast < df.ema_slow) & (df.ema_fast.shift() >= df.ema_slow.shift())
    df["signal"] = np.select([up_cross & (df.rsi > 45), dn_cross & (df.rsi < 55)], ["BUY", "SELL ALL"], default="")

    df["dist_trend_pct"] = ((df["close"] - df["ema_trend"]) / df["ema_trend"]) * 100.0
    df["dot_warn"] = np.where(df["dist_trend_pct"] >= danger_pct, "RED",
                     np.where(df["dist_trend_pct"] >= warn_pct, "ORANGE", ""))

    avg_vol = df["volume"].rolling(20).mean().fillna(df["volume"])
    df["star"] = (df["signal"] == "BUY") & (df["volume"] > avg_vol * 1.15) & (df["close"] > df["ema_trend"])

    last, prev = df.iloc[-1], df.iloc[-2]
    stats = {
        "price": float(last.close), "change_pct": float((last.close / prev.close - 1) * 100) if prev.close else 0.0,
        "rsi": float(last.rsi), "trend": "UP" if last.ema_fast > last.ema_slow else "DOWN",
        "buys": int((df.signal == "BUY").sum()), "sells": int((df.signal == "SELL ALL").sum()), "bars": len(df),
        "dist_trend": float(last.dist_trend_pct) if "dist_trend_pct" in last else 0.0
    }
    return df, stats

def safe_ret(df: pd.DataFrame, days: int) -> float:
    try:
        if df is None or df.empty or len(df) < 2: return 0.0
        now_p = float(df["close"].iloc[-1])
        past_p = float(df["close"].iloc[-1 - days]) if len(df) > days else float(df["close"].iloc[0])
        return float(((now_p - past_p) / past_p) * 100.0) if past_p > 0 else 0.0
    except Exception:
        return 0.0

def fetch_market_analytics(df: pd.DataFrame) -> dict:
    try:
        if df is None or df.empty or len(df) < 2: return {}
        now_p = float(df["close"].iloc[-1])
        vol_30d = float(df.tail(30)["volume"].mean()) if "volume" in df.columns else 0.0
        jan1 = int(datetime.datetime(datetime.datetime.now().year, 1, 1).timestamp())
        ytd_df = df[df["time"] >= jan1] if "time" in df.columns else pd.DataFrame()
        rytd = float(((now_p / float(ytd_df.iloc[0]["close"])) - 1.0) * 100.0) if not ytd_df.empty and float(ytd_df.iloc[0]["close"]) > 0 else safe_ret(df, 30)
        
        tail_52w = df.tail(365)
        low_52w = float(tail_52w["low"].min()) if "low" in tail_52w.columns else now_p * 0.9
        high_52w = float(tail_52w["high"].max()) if "high" in tail_52w.columns else now_p * 1.1

        return {
            "vol_30d_avg": vol_30d, "1W": safe_ret(df, 7), "1M": safe_ret(df, 30),
            "3M": safe_ret(df, 90), "6M": safe_ret(df, 180), "YTD": rytd, "1Y": safe_ret(df, 365),
            "low_52w": low_52w, "high_52w": high_52w
        }
    except Exception:
        return {}

default_tech_data = {
    "vol_30d_avg": 0.0, "1W": 0.0, "1M": 0.0, "3M": 0.0, "6M": 0.0, "YTD": 0.0, "1Y": 0.0,
    "low_52w": 0.0, "high_52w": 0.0,
    "summary": {"label": "N/A", "color": "#9aa0a6", "angle": 0, "buy": 0, "neutral": 0, "sell": 0},
    "osc": {"label": "N/A", "color": "#9aa0a6", "angle": 0, "buy": 0, "neutral": 0, "sell": 0, "rows": []},
    "ma": {"label": "N/A", "color": "#9aa0a6", "angle": 0, "buy": 0, "neutral": 0, "sell": 0, "rows": []},
    "pivots": {
        "Classic": {"P": 0.0, "S1": 0.0, "R1": 0.0, "S2": 0.0, "R2": 0.0},
        "Fibonacci": {"P": 0.0, "S1": 0.0, "R1": 0.0, "S2": 0.0, "R2": 0.0},
        "Camarilla": {"P": 0.0, "S1": 0.0, "R1": 0.0, "S2": 0.0, "R2": 0.0},
    }
}

def compute_full_technicals(df: pd.DataFrame) -> dict:
    try:
        if df is None or df.empty: return default_tech_data

        if "time" not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index().rename(columns={"index": "time"})
            else:
                return default_tech_data

        required_cols = ["close", "high", "low", "volume"]
        for col in required_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                return default_tech_data
        
        df = df.dropna(subset=required_cols).sort_values("time").reset_index(drop=True)
        if df.empty: return default_tech_data

        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        last_p = float(close.iloc[-1])

        ma_rows = []
        ma_buy, ma_sell, ma_neutral = 0, 0, 0
        periods = [10, 20, 30, 50, 100, 200]
        for p in periods:
            if len(df) >= p:
                ema_v = float(close.ewm(span=p, adjust=False, min_periods=1).mean().iloc[-1])
                act_e = "มีแรงซื้อ" if last_p > ema_v else ("มีแรงขาย" if last_p < ema_v else "เป็นกลาง")
                if act_e == "มีแรงซื้อ": ma_buy += 1
                elif act_e == "มีแรงขาย": ma_sell += 1
                else: ma_neutral += 1
                ma_rows.append({"name": f"ค่าเฉลี่ยเคลื่อนที่เอ็กซ์โปเนนเชียล ({p})", "value": f"{ema_v:,.4f}" if last_p < 10 else f"{ema_v:,.2f}", "action": act_e})

                sma_v = float(close.rolling(p, min_periods=1).mean().iloc[-1])
                act_s = "มีแรงซื้อ" if last_p > sma_v else ("มีแรงขาย" if last_p < sma_v else "เป็นกลาง")
                if act_s == "มีแรงซื้อ": ma_buy += 1
                elif act_s == "มีแรงขาย": ma_sell += 1
                else: ma_neutral += 1
                ma_rows.append({"name": f"ค่าเฉลี่ยเคลื่อนที่แบบง่าย ({p})", "value": f"{sma_v:,.4f}" if last_p < 10 else f"{sma_v:,.2f}", "action": act_s})

        h26, l26 = high.rolling(26, min_periods=1).max(), low.rolling(26, min_periods=1).min()
        ichimoku = float(((h26 + l26) / 2).iloc[-1])
        act_ichi = "มีแรงซื้อ" if last_p > ichimoku else ("มีแรงขาย" if last_p < ichimoku else "เป็นกลาง")
        if act_ichi == "มีแรงซื้อ": ma_buy += 1
        elif act_ichi == "มีแรงขาย": ma_sell += 1
        else: ma_neutral += 1
        ma_rows.append({"name": "เส้น Ichimoku Base Line (9, 26, 52, 26)", "value": f"{ichimoku:,.4f}" if last_p < 10 else f"{ichimoku:,.2f}", "action": act_ichi})

        vwma = float(((close * vol).rolling(20, min_periods=1).sum() / vol.rolling(20, min_periods=1).sum().replace(0, np.nan)).iloc[-1])
        act_vwma = "มีแรงซื้อ" if last_p > vwma else ("มีแรงขาย" if last_p < vwma else "เป็นกลาง")
        if act_vwma == "มีแรงซื้อ": ma_buy += 1
        elif act_vwma == "มีแรงขาย": ma_sell += 1
        else: ma_neutral += 1
        ma_rows.append({"name": "เส้นค่าเฉลี่ยเคลื่อนที่วัดจากปริมาณ (20)", "value": f"{vwma:,.4f}" if last_p < 10 else f"{vwma:,.2f}", "action": act_vwma})

        wma_half = close.rolling(4, min_periods=1).mean() * 2
        wma_full = close.rolling(9, min_periods=1).mean()
        hma = float((wma_half - wma_full).rolling(3, min_periods=1).mean().iloc[-1])
        act_hma = "มีแรงซื้อ" if last_p > hma else ("มีแรงขาย" if last_p < hma else "เป็นกลาง")
        if act_hma == "มีแรงซื้อ": ma_buy += 1
        elif act_hma == "มีแรงขาย": ma_sell += 1
        else: ma_neutral += 1
        ma_rows.append({"name": "ค่าเฉลี่ยเคลื่อนที่ฮัล (9)", "value": f"{hma:,.4f}" if last_p < 10 else f"{hma:,.2f}", "action": act_hma})

        osc_rows = []
        osc_buy, osc_sell, osc_neutral = 0, 0, 0

        rsi_val = float(rsi_wilder(close, 14).iloc[-1])
        act_rsi = "มีแรงขาย" if rsi_val > 70 else ("มีแรงซื้อ" if rsi_val < 30 else "เป็นกลาง")
        if act_rsi == "มีแรงซื้อ": osc_buy += 1
        elif act_rsi == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Relative Strength Index (14)", "value": f"{rsi_val:.4f}", "action": act_rsi})

        l14, h14 = low.rolling(14, min_periods=1).min(), high.rolling(14, min_periods=1).max()
        denom = (h14 - l14).replace(0, np.nan)
        stoch_k = float((((close - l14) / denom) * 100).rolling(3, min_periods=1).mean().iloc[-1])
        act_stoch = "มีแรงขาย" if stoch_k > 80 else ("มีแรงซื้อ" if stoch_k < 20 else "เป็นกลาง")
        if act_stoch == "มีแรงซื้อ": osc_buy += 1
        elif act_stoch == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Stochastic %K (14, 3, 3)", "value": f"{stoch_k:.4f}", "action": act_stoch})

        tp = (high + low + close) / 3
        sma_tp = tp.rolling(20, min_periods=1).mean()
        mad = (tp - sma_tp).abs().rolling(20, min_periods=1).mean().replace(0, np.nan)
        cci_v = float(((tp - sma_tp) / (0.015 * mad)).iloc[-1])
        act_cci = "มีแรงขาย" if cci_v > 100 else ("มีแรงซื้อ" if cci_v < -100 else "เป็นกลาง")
        if act_cci == "มีแรงซื้อ": osc_buy += 1
        elif act_cci == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "ดัชนีแชนแนลสินค้าโภคภัณฑ์(20)", "value": f"{cci_v:.4f}", "action": act_cci})

        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14, min_periods=1).mean().replace(0, np.nan)
        up_m, dn_m = high.diff(), -low.diff()
        p_dm = up_m.where((up_m > dn_m) & (up_m > 0), 0.0).rolling(14, min_periods=1).mean()
        m_dm = dn_m.where((dn_m > up_m) & (dn_m > 0), 0.0).rolling(14, min_periods=1).mean()
        p_di = 100 * (p_dm / atr)
        m_di = 100 * (m_dm / atr)
        dx = (100 * (p_di - m_di).abs() / (p_di + m_di).replace(0, np.nan)).fillna(0)
        adx_v = float(dx.rolling(14, min_periods=1).mean().iloc[-1])
        act_adx = "มีแรงซื้อ" if (adx_v > 25 and p_di.iloc[-1] > m_di.iloc[-1]) else ("มีแรงขาย" if (adx_v > 25 and m_di.iloc[-1] > p_di.iloc[-1]) else "เป็นกลาง")
        if act_adx == "มีแรงซื้อ": osc_buy += 1
        elif act_adx == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Average Directional Index (14)", "value": f"{adx_v:.4f}", "action": act_adx})

        med_p = (high + low) / 2
        ao_v = float((med_p.rolling(5, min_periods=1).mean() - med_p.rolling(34, min_periods=1).mean()).iloc[-1])
        act_ao = "มีแรงซื้อ" if ao_v > 0 else "มีแรงขาย"
        if act_ao == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "ตัววัดการแกว่งที่ยอดเยี่ยม", "value": f"{ao_v:.4f}", "action": act_ao})

        mom_v = float(close.diff(10).iloc[-1])
        act_mom = "มีแรงซื้อ" if mom_v > 0 else "มีแรงขาย"
        if act_mom == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "โมเมนตัม (10)", "value": f"{mom_v:.4f}", "action": act_mom})

        macd_l = float((close.ewm(span=12, adjust=False, min_periods=1).mean() - close.ewm(span=26, adjust=False, min_periods=1).mean()).iloc[-1])
        macd_s = float(pd.Series(close.ewm(span=12, adjust=False, min_periods=1).mean() - close.ewm(span=26, adjust=False, min_periods=1).mean()).ewm(span=9, adjust=False, min_periods=1).mean().iloc[-1])
        act_macd = "มีแรงซื้อ" if macd_l > macd_s else "มีแรงขาย"
        if act_macd == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "ระดับ MACD (12, 26)", "value": f"{macd_l:.4f}", "action": act_macd})

        rsi_series = rsi_wilder(close, 14)
        rsi_l14, rsi_h14 = rsi_series.rolling(14, min_periods=1).min(), rsi_series.rolling(14, min_periods=1).max()
        stoch_rsi = float((((rsi_series - rsi_l14) / (rsi_h14 - rsi_l14).replace(0, np.nan)) * 100).rolling(3, min_periods=1).mean().iloc[-1])
        act_srsi = "มีแรงขาย" if stoch_rsi > 80 else ("มีแรงซื้อ" if stoch_rsi < 20 else "เป็นกลาง")
        if act_srsi == "มีแรงซื้อ": osc_buy += 1
        elif act_srsi == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Stochastic RSI Fast (3, 3, 14, 14)", "value": f"{stoch_rsi:.4f}", "action": act_srsi})

        wr_v = float((((h14 - close) / denom) * -100).iloc[-1])
        act_wr = "มีแรงขาย" if wr_v > -20 else ("มีแรงซื้อ" if wr_v < -80 else "เป็นกลาง")
        if act_wr == "มีแรงซื้อ": osc_buy += 1
        elif act_wr == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Williams Percent Range (14)", "value": f"{wr_v:.4f}", "action": act_wr})

        ema13 = close.ewm(span=13, adjust=False, min_periods=1).mean()
        bbp = float((high.iloc[-1] - ema13.iloc[-1]) + (low.iloc[-1] - ema13.iloc[-1]))
        act_bbp = "มีแรงซื้อ" if bbp > 0 else "มีแรงขาย"
        if act_bbp == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "พลังของตลาดขาขึ้นขาลง", "value": f"{bbp:.4f}", "action": act_bbp})

        bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
        tr_uo = pd.concat([high, close.shift()], axis=1).max(axis=1) - pd.concat([low, close.shift()], axis=1).min(axis=1)
        avg7 = (bp.rolling(7, min_periods=1).sum() / tr_uo.rolling(7, min_periods=1).sum().replace(0, np.nan))
        avg14 = (bp.rolling(14, min_periods=1).sum() / tr_uo.rolling(14, min_periods=1).sum().replace(0, np.nan))
        avg28 = (bp.rolling(28, min_periods=1).sum() / tr_uo.rolling(28, min_periods=1).sum().replace(0, np.nan))
        uo = float((100 * (4 * avg7 + 2 * avg14 + avg28) / 7).iloc[-1])
        act_uo = "มีแรงขาย" if uo > 70 else ("มีแรงซื้อ" if uo < 30 else "เป็นกลาง")
        if act_uo == "มีแรงซื้อ": osc_buy += 1
        elif act_uo == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Ultimate Oscillator (7, 14, 28)", "value": f"{uo:.4f}", "action": act_uo})

        tot_buy = osc_buy + ma_buy
        tot_sell = osc_sell + ma_sell
        tot_neu = osc_neutral + ma_neutral
        net_score = tot_buy - tot_sell

        if net_score >= 6:    sum_lbl, sum_col, sum_ang = "มีแรงซื้อรุนแรง", "#00e676", 55
        elif net_score >= 2:  sum_lbl, sum_col, sum_ang = "มีแรงซื้อ", "#26a69a", 30
        elif net_score <= -6: sum_lbl, sum_col, sum_ang = "มีแรงขายรุนแรง", "#d32f2f", -55
        elif net_score <= -2: sum_lbl, sum_col, sum_ang = "มีแรงขาย", "#ef5350", -30
        else:                 sum_lbl, sum_col, sum_ang = "เป็นกลาง", "#9aa0a6", 0

        osc_score = osc_buy - osc_sell
        osc_lbl, osc_col, osc_ang = ("มีแรงซื้อ", "#26a69a", 35) if osc_score > 1 else (("มีแรงขาย", "#ef5350", -35) if osc_score < -1 else ("เป็นกลาง", "#9aa0a6", 0))

        ma_score = ma_buy - ma_sell
        ma_lbl, ma_col, ma_ang = ("มีแรงซื้อ", "#26a69a", 35) if ma_score > 1 else (("มีแรงขาย", "#ef5350", -35) if ma_score < -1 else ("เป็นกลาง", "#9aa0a6", 0))

        prev_h, prev_l, prev_c = float(high.iloc[-2]), float(low.iloc[-2]), float(close.iloc[-2])
        pp = (prev_h + prev_l + prev_c) / 3
        pivots = {
            "Classic": {"P": pp, "S1": 2*pp - prev_h, "R1": 2*pp - prev_l, "S2": pp - (prev_h - prev_l), "R2": pp + (prev_h - prev_l)},
            "Fibonacci": {"P": pp, "S1": pp - 0.382*(prev_h - prev_l), "R1": pp + 0.382*(prev_h - prev_l), "S2": pp - 0.618*(prev_h - prev_l), "R2": pp + 0.618*(prev_h - prev_l)},
            "Camarilla": {"P": pp, "S1": prev_c - (prev_h - prev_l)*1.0833/12, "R1": prev_c + (prev_h - prev_l)*1.0833/12, "S2": prev_c - (prev_h - prev_l)*1.1666/12, "R2": prev_c + (prev_h - prev_l)*1.1666/12}
        }

        perf = fetch_market_analytics(df)

        return {
            **perf,
            "summary": {"label": sum_lbl, "color": sum_col, "angle": sum_ang, "buy": tot_buy, "neutral": tot_neu, "sell": tot_sell},
            "osc": {"label": osc_lbl, "color": osc_col, "angle": osc_ang, "buy": osc_buy, "neutral": osc_neutral, "sell": osc_sell, "rows": osc_rows},
            "ma": {"label": ma_lbl, "color": ma_col, "angle": ma_ang, "buy": ma_buy, "neutral": ma_neutral, "sell": ma_sell, "rows": ma_rows},
            "pivots": pivots
        }
    except Exception as e:
        st.error(f"🐞 เกิดข้อผิดพลาดในการคำนวณ Technicals: {e}")
        return default_tech_data

def render_gauge_svg(title: str, label: str, color: str, angle: float, buy: int, neutral: int, sell: int, size: int = 140) -> str:
    w, h = 150, 82
    cx, cy, r = 75, 74, 54
    return f"""<div style="text-align:center; font-family:-apple-system,BlinkMacSystemFont,sans-serif; flex:1; min-width:90px;">
        <div style="font-size:10px; font-weight:700; color:#9aa0a6; margin-bottom:1px;">{title}</div>
        <svg width="100%" height="{h}" viewBox="0 0 {w} {h}" style="max-width:{size}px; margin:0 auto; display:block; overflow:visible;">
            <path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="#1E1E1E" stroke-width="7" stroke-linecap="round"/>
            <path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx - r*0.3} {cy - r*0.9}" fill="none" stroke="{DOWN}" stroke-width="7" stroke-linecap="round"/>
            <path d="M {cx + r*0.3} {cy - r*0.9} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{UP}" stroke-width="7" stroke-linecap="round"/>
            <g transform="translate({cx}, {cy}) rotate({angle})">
                <line x1="0" y1="0" x2="0" y2="{-r + 4}" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round"/>
                <circle cx="0" cy="0" r="3.5" fill="#FFFFFF"/>
            </g>
        </svg>
        <div style="font-size:11px; font-weight:700; color:{color}; margin-top:-2px;">{label}</div>
        <div style="display:flex; justify-content:center; gap:6px; font-size:9px; color:#787b86; margin-top:2px; font-family:monospace;">
            <span>ขาย <b>{sell}</b></span><span>กลาง <b>{neutral}</b></span><span>ซื้อ <b>{buy}</b></span>
        </div>
    </div>"""

def render_3_gauges_html(tech: dict, compact: bool = True) -> str:
    if not tech or "summary" not in tech or "osc" not in tech or "ma" not in tech: return ""
    o, s, m = tech["osc"], tech["summary"], tech["ma"]
    if compact:
        g_sum = render_gauge_svg("ภาพรวม (Summary)", s["label"], s["color"], s["angle"], s["buy"], s["neutral"], s["sell"], size=150)
        g_osc = render_gauge_svg("Oscillators", o["label"], o["color"], o["angle"], o["buy"], o["neutral"], o["sell"], size=120)
        g_ma = render_gauge_svg("ค่าเฉลี่ยเคลื่อนที่", m["label"], m["color"], m["angle"], m["buy"], m["neutral"], m["sell"], size=120)
        return f"""<div style="background:#0D0D0D; border:1px solid #1E1E1E; border-radius:6px; padding:8px 4px; margin:6px 0;">
            <div style="display:flex; justify-content:center; margin-bottom:8px;">{g_sum}</div>
            <div style="display:flex; justify-content:space-between; gap:4px;">{g_osc}{g_ma}</div>
        </div>"""
    else:
        g_osc = render_gauge_svg("Oscillators", o["label"], o["color"], o["angle"], o["buy"], o["neutral"], o["sell"], size=140)
        g_sum = render_gauge_svg("ภาพรวม (Summary)", s["label"], s["color"], s["angle"], s["buy"], s["neutral"], s["sell"], size=165)
        g_ma = render_gauge_svg("ค่าเฉลี่ยเคลื่อนที่", m["label"], m["color"], m["angle"], m["buy"], m["neutral"], m["sell"], size=140)
        return f"""<div style="display:flex; justify-content:space-around; align-items:flex-end; background:#0D0D0D; border:1px solid #1E1E1E; border-radius:6px; padding:12px 6px; margin:8px 0;">
            {g_osc} {g_sum} {g_ma}
        </div>"""

def fetch_seasonality_svg(df: pd.DataFrame) -> str:
    try:
        if df is None or df.empty or len(df) < 60: return ""

        df = df.copy()
        df["dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df["year"] = df["dt"].dt.year
        df["doy"] = df["dt"].dt.dayofyear

        years_target = [2024, 2025, 2026]
        colors = {2024: "#f59e0b", 2025: "#10b981", 2026: "#3b82f6"}
        year_data = {}
        all_pcts = [0.0]

        for yr in years_target:
            ydf = df[df["year"] == yr].sort_values("time")
            if not ydf.empty and len(ydf) >= 5:
                base_close = float(ydf.iloc[0]["close"])
                if base_close > 0:
                    pts = []
                    for _, row in ydf.iterrows():
                        pct = ((float(row["close"]) / base_close) - 1.0) * 100.0
                        pts.append((int(row["doy"]), pct))
                        all_pcts.append(pct)
                    year_data[yr] = {"points": pts, "last_pct": pts[-1][1]}

        if not year_data: return ""

        min_pct = min(all_pcts) - 5.0
        max_pct = max(all_pcts) + 5.0
        if min_pct > -10.0: min_pct = -10.0
        if max_pct < 10.0:  max_pct = 10.0
        span = max_pct - min_pct if max_pct != min_pct else 1.0

        w, h = 540, 160
        pad_l, pad_r, pad_t, pad_b = 15, 20, 15, 20
        gw, gh = w - pad_l - pad_r, h - pad_t - pad_b

        def to_xy(doy, pct):
            x = pad_l + (min(365, max(1, doy)) - 1) / 365.0 * gw
            y = pad_t + (max_pct - pct) / span * gh
            return round(x, 1), round(y, 1)

        zero_y = round(pad_t + (max_pct - 0.0) / span * gh, 1)
        svg_lines = [f'<line x1="{pad_l}" y1="{zero_y}" x2="{w - pad_r}" y2="{zero_y}" stroke="#333333" stroke-width="1.2" stroke-dasharray="4,4"/>']

        for m_doy in [1, 91, 182, 274]:
            gx = round(pad_l + (m_doy - 1) / 365.0 * gw, 1)
            svg_lines.append(f'<line x1="{gx}" y1="{pad_t}" x2="{gx}" y2="{h - pad_b}" stroke="#1E1E1E" stroke-width="1.2" stroke-dasharray="3,3"/>')

        legend_pills = []
        for yr in sorted(year_data.keys()):
            col = colors.get(yr, "#D1D4DC")
            pts = year_data[yr]["points"]
            d_path = [f"{'M' if i == 0 else 'L'} {to_xy(doy, p)[0]} {to_xy(doy, p)[1]}" for i, (doy, p) in enumerate(pts)]
            svg_lines.append(f'<path d="{" ".join(d_path)}" fill="none" stroke="{col}" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/>')
            lx, ly = to_xy(pts[-1][0], pts[-1][1])
            svg_lines.append(f'<circle cx="{lx}" cy="{ly}" r="3.5" fill="{col}"/>')
            legend_pills.append(f'<span style="display:inline-flex; align-items:center; gap:4px; margin:0 5px; font-size:10px; font-family:monospace;"><span style="color:{col};">●</span> {yr}</span>')

        svg_content = "\n".join(svg_lines)
        return f"""<div style="background:#0A0A0A; border:1px solid #1E1E1E; border-radius:6px; padding:6px 8px; margin-bottom:6px; width:100%; box-sizing:border-box;">
            <svg width="100%" height="{h}" viewBox="0 0 {w} {h}" style="overflow:visible; display:block;">
                {svg_content}
                <text x="{pad_l}" y="{h - 4}" fill="#666" font-size="9" font-family="sans-serif">ม.ค.</text>
                <text x="{pad_l + gw*0.33}" y="{h - 4}" fill="#666" font-size="9" font-family="sans-serif">พ.ค.</text>
                <text x="{pad_l + gw*0.66}" y="{h - 4}" fill="#666" font-size="9" font-family="sans-serif">ก.ย.</text>
            </svg>
            <div style="display:flex; justify-content:center; margin-top:4px;">{''.join(legend_pills)}</div>
        </div>"""
    except Exception:
        return ""

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yahoo_batch_quotes(symbols_list: tuple[str, ...]) -> dict[str, dict]:
    if not symbols_list: return {}
    results = {}
    chunk_size = 40
    syms = list(symbols_list)

    for i in range(0, len(syms), chunk_size):
        chunk = syms[i:i + chunk_size]
        sym_str = ",".join(chunk)
        urls = [
            f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={sym_str}",
            f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={sym_str}"
        ]
        success = False
        for u in urls:
            try:
                r = _fetch_url_with_timeout(u, timeout=1.5)
                if r and r.status_code == 200:
                    data = r.json().get("quoteResponse", {}).get("result", [])
                    for q in data:
                        s = q.get("symbol", "")
                        p = float(q.get("regularMarketPrice", 0) or 0)
                        chg = float(q.get("regularMarketChange", 0) or 0)
                        pct = float(q.get("regularMarketChangePercent", 0) or 0)
                        vol = float(q.get("regularMarketVolume", 0) or 0)
                        results[s] = {"price": p, "change": chg, "pct": pct, "vol": vol}
                    success = True
                    break
            except Exception:
                pass

        if not success:
            futures = {THREAD_POOL_EXECUTOR.submit(fetch_item_quote, s): s for s in chunk}
            for future in concurrent.futures.as_completed(futures):
                sym = futures[future]
                try:
                    q = future.result(timeout=1.5)
                    if q.get("price", 0) > 0:
                        results[sym] = q
                except Exception:
                    pass

    return results

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_top_movers(category: str) -> dict:
    gainers, losers = [], []
    try:
        if category == "bitkub":
            r = HTTP_SESSION.get("https://api.bitkub.com/api/market/ticker", timeout=4)
            if r.status_code == 200:
                raw = r.json()
                items = []
                for k, v in raw.items():
                    sym = f"{k[4:]}_THB" if k.startswith("THB_") else k
                    pct = float(v.get("percentChange", v.get("percent_change", 0)))
                    px = float(v.get("last", 0))
                    items.append({"symbol": sym, "label": sym.replace("_THB",""), "price": px, "pct": pct})
                gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
                losers = sorted(items, key=lambda x: x["pct"])[:10]

        elif category == "binance":
            r = HTTP_SESSION.get("https://api.binance.com/api/v3/ticker/24hr", timeout=4)
            if r.status_code == 200:
                raw = r.json()
                items = []
                for d in raw:
                    s = d.get("symbol", "")
                    if s.endswith("USDT") and not s.endswith("UPUSDT") and not s.endswith("DOWNUSDT"):
                        pct = float(d.get("priceChangePercent", 0))
                        px = float(d.get("lastPrice", 0))
                        items.append({"symbol": s, "label": s.replace("USDT",""), "price": px, "pct": pct})
                gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
                losers = sorted(items, key=lambda x: x["pct"])[:10]

        elif category == "bybit":
            r = HTTP_SESSION.get("https://api.bybit.com/v5/market/tickers?category=spot", timeout=4)
            if r.status_code == 200:
                raw = r.json().get("result", {}).get("list", [])
                items = []
                for d in raw:
                    s = d.get("symbol", "")
                    if s.endswith("USDT"):
                        pct = float(d.get("price24hPcnt", 0)) * 100
                        px = float(d.get("lastPrice", 0))
                        items.append({"symbol": s, "label": s.replace("USDT",""), "price": px, "pct": pct})
                gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
                losers = sorted(items, key=lambda x: x["pct"])[:10]
        elif category == "gate":
            r = HTTP_SESSION.get("https://api.gateio.ws/api/v4/spot/tickers", timeout=4)
            if r.status_code == 200:
                raw = r.json()
                items = []
                for d in raw:
                    s = d.get("currency_pair", "")
                    if s.endswith("_USDT"):
                        pct = float(d.get("change_percentage", 0))
                        px = float(d.get("last", 0))
                        items.append({"symbol": s, "label": s.replace("_USDT",""), "price": px, "pct": pct})
                gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
                losers = sorted(items, key=lambda x: x["pct"])[:10]
        elif category == "kucoin":
            r = HTTP_SESSION.get("https://api.kucoin.com/api/v1/market/allTickers", timeout=4)
            if r.status_code == 200:
                raw = r.json().get("data", {}).get("ticker", [])
                items = []
                for d in raw:
                    s = d.get("symbol", "")
                    if s.endswith("-USDT"):
                        pct = float(d.get("changeRate", 0)) * 100
                        px = float(d.get("last", 0))
                        items.append({"symbol": s.replace("-", "_"), "label": s.replace("-USDT",""), "price": px, "pct": pct})
                gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
                losers = sorted(items, key=lambda x: x["pct"])[:10]
        elif category == "us":
            us_pool = (
                "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "AMD",
                "PLTR", "MSTR", "COIN", "NFLX", "AVGO", "INTC", "ARM", "RKLB",
                "SMCI", "SMR", "CCJ", "LLY", "JPM", "VRT", "IONQ", "CRWD", "QCOM"
            )
            quotes = fetch_yahoo_batch_quotes(us_pool)
            items = []
            for sym in us_pool:
                q = quotes.get(sym, {"price": 0.0, "pct": 0.0})
                if q["price"] > 0:
                    items.append({"symbol": sym, "label": sym, "price": q["price"], "pct": q["pct"]})
            gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
            losers = sorted(items, key=lambda x: x["pct"])[:10]

        elif category == "china":
            cn_pool = (
                "002594.SZ", "300750.SZ", "9866.HK", "9868.HK", "2015.HK", "1810.HK",
                "0700.HK", "9988.HK", "3690.HK", "9618.HK", "9888.HK", "688981.SS",
                "600519.SS", "601398.SS", "601857.SS"
            )
            quotes = fetch_yahoo_batch_quotes(cn_pool)
            items = []
            for sym in cn_pool:
                q = quotes.get(sym, {"price": 0.0, "pct": 0.0})
                if q["price"] > 0:
                    lbl = CHINA_STOCK_NAMES.get(sym, sym.split(".")[0])
                    items.append({"symbol": sym, "label": lbl, "price": q["price"], "pct": q["pct"]})
            gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
            losers = sorted(items, key=lambda x: x["pct"])[:10]

        else:
            pool = []
            if category == "thai":
                pool = [
                    "DELTA.BK", "PTT.BK", "AOT.BK", "ADVANC.BK", "GULF.BK", "PTTEP.BK",
                    "CPALL.BK", "BDMS.BK", "KBANK.BK", "SCB.BK", "BBL.BK", "TRUE.BK",
                    "KTB.BK", "SCC.BK", "CPN.BK", "CRC.BK", "MINT.BK", "IVL.BK",
                    "BH.BK", "TOP.BK", "HMPRO.BK", "EA.BK", "WHA.BK", "AMATA.BK", "GPSC.BK"
                ]
            elif category == "vn":
                pool = ["AAA.VN", "HPG.VN", "VIC.VN", "VHM.VN", "FPT.VN", "VNM.VN", "SSI.VN", "TCB.VN", "MWG.VN"]
            elif category == "macro":
                pool = list(COMMODITY_NAMES.keys()) + list(FOREX_NAMES.keys())
            elif category == "all":
                pool = ["NVDA", "TSLA", "PLTR", "DELTA.BK", "PTT.BK", "GC=F", "CL=F", "USDTHB=X", "0700.HK", "HPG.VN"]

            quotes = fetch_yahoo_batch_quotes(tuple(pool))
            items = []
            for sym in pool:
                q = quotes.get(sym, {"price": 0.0, "pct": 0.0})
                if q["price"] > 0:
                    lbl = CHINA_STOCK_NAMES.get(sym, COMMODITY_NAMES.get(sym, FOREX_NAMES.get(sym, sym.split(".")[0])))
                    items.append({"symbol": sym, "label": lbl, "price": q["price"], "pct": q["pct"]})

            if category == "all":
                for c_sym in ["BTC_THB", "ETH_THB"]:
                    cq = fetch_item_quote(c_sym)
                    if cq["price"] > 0:
                        items.append({"symbol": c_sym, "label": c_sym.replace("_THB",""), "price": cq["price"], "pct": cq["pct"]})

            gainers = sorted(items, key=lambda x: x["pct"], reverse=True)[:10]
            losers = sorted(items, key=lambda x: x["pct"])[:10]

    except Exception:
        pass
    return {"gainers": gainers, "losers": losers}

@st.cache_data(ttl=5, show_spinner=False)
def get_bitkub_all_tickers() -> dict:
    out = {}
    for url in ("https://api.bitkub.com/api/v3/market/ticker", "https://api.bitkub.com/api/market/ticker"):
        try:
            r = HTTP_SESSION.get(url, timeout=3)
            if r.status_code != 200: continue
            res = r.json()
            data = res.get("result", res) if isinstance(res, dict) else res
            items = [(d.get("symbol", ""), d) for d in data if isinstance(d, dict)] if isinstance(data, list) else list(data.items())
            for k, v in items:
                if not k or not isinstance(v, dict): continue
                k = str(k).upper()
                base = k[4:] if k.startswith("THB_") else k.replace("_THB", "")
                if not base: continue
                out[f"{base}_THB"] = v
                out[f"THB_{base}"] = v
            if out: return out
        except Exception: pass
    return out

def bitkub_pick(symbol: str) -> dict:
    bk = get_bitkub_all_tickers()
    s = (symbol or "").upper()
    base = s[4:] if s.startswith("THB_") else s.replace("_THB", "")
    return bk.get(f"{base}_THB", {}) or bk.get(f"THB_{base}", {}) or {}

@st.cache_data(ttl=10, show_spinner=False)
def fetch_item_quote(sym: str) -> dict:
    try:
        s = (sym or "").upper()
        if s.endswith("_THB") or s.startswith("THB_"):
            d = bitkub_pick(s)
            if d:
                return {"price": float(d.get("last", 0)), "change": float(d.get("change", 0)),
                        "pct": float(d.get("percentChange", d.get("percent_change", 0))),
                        "vol": float(d.get("baseVolume", d.get("base_volume", 0)))}
            return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

        if s.endswith("USDT") and "-" not in s:
            r = _fetch_url_with_timeout(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}", timeout=1.5)
            if r and r.status_code == 200:
                d = r.json()
                return {"price": float(d["lastPrice"]), "change": float(d["priceChange"]),
                        "pct": float(d["priceChangePercent"]), "vol": float(d["volume"])}
            return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

        r = _fetch_url_with_timeout(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d", timeout=1.5)
        if r and r.status_code == 200:
            meta = (r.json().get("chart", {}).get("result") or [{}])[0].get("meta", {})
            p = float(meta.get("regularMarketPrice", 0))
            prev = float(meta.get("chartPreviousClose", meta.get("previousClose", p)) or p)
            chg = p - prev; pct = (chg / prev * 100.0) if prev > 0 else 0.0
            if p > 0: return {"price": p, "change": chg, "pct": pct, "vol": float(meta.get("regularMarketVolume", 0))}
    except Exception: pass
    return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

def fmt_price(p: float) -> str:
    if p >= 1000: return f"{p:,.2f}"
    if p >= 1: return f"{p:.4f}"
    return f"{p:.6f}" if p > 0 else "0.00"

def fmt_chg(c: float) -> str:
    s = "+" if c > 0 else ""
    return f"{s}{c:.2f}" if abs(c) >= 1 else f"{s}{c:.4f}"

def fmt_vol(v: float) -> str:
    if v >= 1_000_000_000: return f"{v/1_000_000_000:,.2f}B"
    if v >= 1_000_000: return f"{v/1_000_000:,.2f}M"
    if v >= 1_000: return f"{v/1_000:,.2f}K"
    return f"{v:,.2f}"

def fetch_unified_ticker(market_type: str, exchange: str, symbol: str, df_last: pd.DataFrame) -> dict:
    try:
        if "คริปโต" in market_type:
            if exchange == "Bitkub":
                d = bitkub_pick(symbol)
                if d:
                    bid_vol = float(d.get("highestBidVolume", d.get("bid_volume", 0)))
                    ask_vol = float(d.get("lowestAskVolume", d.get("ask_volume", 0)))
                    
                    low_24hr = float(d.get("low24hr", d.get("low_24_hr", d.get("low", 0))))
                    if low_24hr <= 0 and not df_last.empty:
                        low_24hr = float(df_last.tail(24)['low'].min()) if not df_last.tail(24)['low'].empty else low_24hr
                        if low_24hr <= 0:
                            low_24hr = float(d.get("last", 0)) * 0.98 
                    elif low_24hr <= 0:
                        low_24hr = float(d.get("last", 0)) * 0.98

                    return {"price": float(d.get("last", 0)),
                            "change": float(d.get("change", 0)),
                            "pct": float(d.get("percentChange", d.get("percent_change", 0))),
                            "bid": float(d.get("highestBid", d.get("highest_bid", 0))),
                            "ask": float(d.get("lowestAsk", d.get("lowest_ask", 0))),
                            "bid_vol": bid_vol,
                            "ask_vol": ask_vol,
                            "high": float(d.get("high24hr", d.get("high_24_hr", d.get("high", 0)))),
                            "low": low_24hr,
                            "vol": float(d.get("baseVolume", d.get("base_volume", 0)))}
            elif exchange == "Binance":
                r = HTTP_SESSION.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=3)
                if r.status_code == 200:
                    d = r.json()
                    bid_vol = float(d.get("bidQty", 0))
                    ask_vol = float(d.get("askQty", 0))
                    
                    low_24hr = float(d.get("lowPrice", 0))
                    if low_24hr <= 0 and not df_last.empty:
                        low_24hr = float(df_last.tail(24)['low'].min()) if not df_last.tail(24)['low'].empty else low_24hr
                        if low_24hr <= 0:
                            low_24hr = float(d.get("lastPrice", 0)) * 0.98
                    elif low_24hr <= 0:
                        low_24hr = float(d.get("lastPrice", 0)) * 0.98

                    return {"price": float(d["lastPrice"]), "change": float(d["priceChange"]),
                            "pct": float(d["priceChangePercent"]), "bid": float(d["bidPrice"]),
                            "ask": float(d["askPrice"]), "bid_vol": bid_vol, "ask_vol": ask_vol,
                            "high": float(d["highPrice"]),
                            "low": low_24hr,
                            "vol": float(d["volume"])}
            elif exchange == "Bybit":
                r = HTTP_SESSION.get(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}", timeout=3)
                if r.status_code == 200:
                    d = r.json().get("result", {}).get("list", [{}])[0]
                    if d:
                        return {"price": float(d.get("lastPrice", 0)), "change": 0, # Bybit doesn't provide priceChange directly, pct is provided
                                "pct": float(d.get("price24hPcnt", 0)) * 100,
                                "bid": float(d.get("bid1Price", 0)), "ask": float(d.get("ask1Price", 0)),
                                "bid_vol": float(d.get("bid1Size", 0)), "ask_vol": float(d.get("ask1Size", 0)),
                                "high": float(d.get("highPrice24h", 0)), "low": float(d.get("lowPrice24h", 0)),
                                "vol": float(d.get("volume24h", 0))}
            elif exchange == "Gate.io":
                r = HTTP_SESSION.get(f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}", timeout=3)
                if r.status_code == 200:
                    d = r.json()[0]
                    if d:
                        return {"price": float(d.get("last", 0)), "change": 0, # Gate.io doesn't provide priceChange directly
                                "pct": float(d.get("change_percentage", 0)),
                                "bid": float(d.get("highest_bid", 0)), "ask": float(d.get("lowest_ask", 0)),
                                "bid_vol": 0, "ask_vol": 0, # Not provided in tickers endpoint
                                "high": float(d.get("high_24h", 0)), "low": float(d.get("low_24h", 0)),
                                "vol": float(d.get("base_volume", 0))}
            elif exchange == "KuCoin":
                symbol_kucoin = symbol.replace("_", "-")
                r = HTTP_SESSION.get(f"https://api.kucoin.com/api/v1/market/allTickers", timeout=3) # Get all tickers and find the one
                if r.status_code == 200:
                    tickers = r.json().get("data", {}).get("ticker", [])
                    d = next((t for t in tickers if t.get("symbol") == symbol_kucoin), None)
                    if d:
                        return {"price": float(d.get("last", 0)), "change": 0, # Kucoin doesn't provide priceChange directly
                                "pct": float(d.get("changeRate", 0)) * 100,
                                "bid": float(d.get("buy", 0)), "ask": float(d.get("sell", 0)),
                                "bid_vol": 0, "ask_vol": 0, # Not provided
                                "high": float(d.get("high", 0)), "low": float(d.get("low", 0)),
                                "vol": float(d.get("vol", 0))}
        else:
            q = fetch_item_quote(symbol)
            if q["price"] > 0:
                bid_vol = q.get("bid_vol", 1.0)
                ask_vol = q.get("ask_vol", 1.0)
                
                low_val = q.get("low", q["price"] * 0.99)
                if low_val <= 0 and not df_last.empty:
                    low_val = float(df_last.tail(24)['low'].min()) if not df_last.tail(24)['low'].empty else low_val
                    if low_val <= 0:
                        low_val = q["price"] * 0.98
                elif low_val <= 0:
                    low_val = q["price"] * 0.98

                return {"price": q["price"], "change": q["change"], "pct": q["pct"],
                        "bid": q["price"]*0.9998, "ask": q["price"]*1.0002,
                        "bid_vol": bid_vol, "ask_vol": ask_vol,
                        "high": q["price"]*1.01,
                        "low": low_val,
                        "vol": q["vol"]}

        if not df_last.empty and len(df_last) >= 2:
            last, prev = df_last.iloc[-1], df_last.iloc[-2]
            chg = last.close - prev.close
            
            bid_vol = 1.0
            ask_vol = 1.0
            
            low_val = float(df_last.tail(24)["low"].min())
            if low_val <= 0:
                low_val = float(last.close) * 0.98

            return {"price": float(last.close), "change": float(chg),
                    "pct": float(chg / prev.close * 100.0) if prev.close else 0.0,
                    "bid": float(last.close*0.9998), "ask": float(last.close*1.0002),
                    "bid_vol": bid_vol, "ask_vol": ask_vol,
                    "high": float(df_last.tail(24)["high"].max()),
                    "low": low_val,
                    "vol": float(df_last.tail(24)["volume"].sum())}
    except Exception: pass
    return {}

def build_asset_icon_html(sym: str, tag_color: str = "#1E1E1E", size: int = 18) -> str:
    clean_code = sym.split(".")[0].replace("_THB","").replace("-USDT","").replace("USDT","").replace("=F","").replace("=X","")
    clean_lower = clean_code.lower()
    fallback_avatar = f"https://ui-avatars.com/api/?name={clean_code[:3]}&background=0A0A0A&color=D1D4DC&rounded=true&bold=true&size=32"
    icon_url = f"https://assets.coincap.io/assets/icons/{clean_lower}@2x.png"
    return f"""<div style="display:flex;align-items:center;justify-content:center;height:24px;gap:3px;">
        <div style="width:3px;height:16px;border-radius:2px;background:{tag_color};flex-shrink:0;"></div>
        <img src="{icon_url}" onerror="this.onerror=null;this.src='{fallback_avatar}';" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;background:#050505;border:1px solid #1E1E1E;">
    </div>"""

def render_tv_quote_card_html(tk: dict, an: dict, symbol: str, label_name: str, seasonality_html: str = "", gauges_html: str = "") -> str:
    if not tk: return "<div style='color:#787b86; padding:10px;'>กำลังเชื่อมต่อข้อมูลราคา...</div>"
    c_color = UP if tk.get("change", 0) >= 0 else DOWN
    sign = "+" if tk.get("change", 0) >= 0 else ""
    
    p_val = float(tk.get("price", 0))
    p_str = f"{p_val:,.4f}" if p_val < 10 else f"{p_val:,.2f}"
    
    c_val = float(tk.get("change", 0))
    c_str = f"{c_val:,.4f}" if abs(c_val) < 1 else f"{c_val:,.2f}"
    
    bid_val = float(tk.get("bid", p_val))
    bid_str = f"{bid_val:,.4f}" if bid_val < 10 else f"{bid_val:,.2f}"
    
    ask_val = float(tk.get("ask", p_val))
    ask_str = f"{ask_val:,.4f}" if ask_val < 10 else f"{ask_val:,.2f}"
    bid_vol_raw = tk.get('bid_vol', 0)
    ask_vol_raw = tk.get('ask_vol', 0)
    bid_vol_str = f"{bid_vol_raw:,.0f}" if bid_vol_raw > 0 else "-"
    ask_vol_str = f"{ask_vol_raw:,.0f}" if ask_vol_raw > 0 else "-"

    day_low = tk.get("low", 0)
    if day_low <= 0:
        day_low = p_val * 0.98
    day_low = float(day_low)

    day_high = tk.get("high", 0)
    if day_high <= 0:
        day_high = p_val * 1.02
    day_high = float(day_high)
    span_day = day_high - day_low
    ratio_day = max(0.0, min(100.0, ((p_val - day_low) / span_day * 100.0))) if span_day > 0 else 50.0

    low_52w = an.get("low_52w", day_low * 0.8) if an else day_low * 0.8
    high_52w = an.get("high_52w", day_high * 1.2) if an else day_high * 1.2
    low_52w = float(low_52w)
    high_52w = float(high_52w)
    span_52w = high_52w - low_52w
    ratio_52w = max(0.0, min(100.0, ((p_val - low_52w) / span_52w * 100.0))) if span_52w > 0 else 50.0

    vol_24h_str = fmt_vol(tk.get("vol", 0))
    vol_30d_str = fmt_vol(an.get("vol_30d_avg", 0)) if an else "-"

    def p_box(lbl, val):
        col = UP if val >= 0 else DOWN
        bg = "rgba(38, 166, 154, 0.12)" if val >= 0 else "rgba(239, 83, 80, 0.12)"
        s = "+" if val >= 0 else ""
        return f"""<div style="background:{bg}; border:1px solid {col}40; border-radius:4px; padding:6px 2px; text-align:center;">
<div style="font-size:11px; font-weight:700; color:{col}; font-family:monospace;">{s}{val:.2f}%</div>
<div style="font-size:9px; color:#787b86; margin-top:2px;">{lbl}</div></div>"""

    grid_perf = ""
    if an:
        grid_perf = f"""<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:4px; margin-bottom:12px;">
{p_box('1W', an.get('1W',0))}{p_box('1M', an.get('1M',0))}{p_box('3M', an.get('3M',0))}
{p_box('6M', an.get('6M',0))}{p_box('YTD', an.get('YTD',0))}{p_box('1Y', an.get('1Y',0))}</div>"""
    else:
        grid_perf = """<div style="font-size:10px; color:#787b86; padding:6px 0;">ไม่มีข้อมูลย้อนหลังเพียงพอ</div>"""

    desc_display = CHINA_STOCK_NAMES.get(symbol, COMMODITY_NAMES.get(symbol, FOREX_NAMES.get(symbol, "")))
    sub_title_html = f"<div style='font-size:10px; color:#888; margin-bottom:2px;'>{desc_display}</div>" if desc_display else ""
    currency_label = "THB" if ("_THB" in symbol or ".BK" in symbol) else "USD"

    return f"""<div class="scrollable-market-card">
<div style="background-color:#0A0A0A; border-radius:6px; padding:12px 10px; color:#D1D4DC; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; border:1px solid #1E1E1E;">

<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
    <div style="display:flex; align-items:center; gap:6px;">
        <span style="font-size:15px; font-weight:800; color:#fff;">{symbol}</span>
    </div>
    <span style="background:#1A1A1A; color:#9aa0a6; padding:1px 6px; border-radius:3px; font-size:9px; font-weight:600;">{label_name}</span>
</div>
{sub_title_html}
<div style="font-size:10px; color:#787b86; margin-bottom:8px;">ตำแหน่ง • คริปโต</div>

<div style="display:flex; align-items:baseline; gap:6px; margin-bottom:2px;">
    <span style="font-size:24px; font-weight:800; color:#fff; letter-spacing:-0.5px;">{p_str}</span>
    <span style="font-size:10px; color:#787b86; font-weight:bold;">{currency_label}</span>
    <span style="font-size:12px; font-weight:700; color:{c_color}; font-family:monospace;">{sign}{c_str}</span>
    <span style="font-size:12px; font-weight:700; color:{c_color}; font-family:monospace;">{sign}{tk.get('pct', 0):.2f}%</span>
</div>
<div style="font-size:10px; color:#26a69a; margin-bottom:12px; font-weight:600;">● ตลาดเปิด</div>

<div style="display:flex; gap:6px; margin-bottom:14px;">
    <div style="background:rgba(41,98,255,0.15); border:1px solid rgba(41,98,255,0.4); border-radius:12px; padding:2px 10px; font-size:10px; color:#2962ff; font-family:monospace;">
        {bid_str} × {bid_vol_str}
    </div>
    <div style="background:rgba(239,83,80,0.15); border:1px solid rgba(239,83,80,0.4); border-radius:12px; padding:2px 10px; font-size:10px; color:#ef5350; font-family:monospace;">
        {ask_str} × {ask_vol_str}
    </div>
</div>

<div style="margin-bottom:14px;">
    <div style="display:flex; justify-content:space-between; font-size:11px; font-family:monospace; color:#D1D4DC; margin-bottom:4px;">
        <span>{fmt_price(day_low)}</span>
        <span style="color:#787b86; font-size:10px; font-family:sans-serif;">ระหว่างวัน</span>
        <span>{fmt_price(day_high)}</span>
    </div>
    <div style="position:relative; width:100%; height:4px; background:#1E1E1E; border-radius:2px;">
        <div style="position:absolute; left:0; width:{ratio_day}%; height:100%; background:#26a69a; border-radius:2px;"></div>
        <div style="position:absolute; left:{ratio_day}%; top:5px; transform:translateX(-50%); font-size:8px; color:#D1D4DC; line-height:1;">▲</div>
    </div>
</div>

<div style="margin-bottom:18px;">
    <div style="display:flex; justify-content:space-between; font-size:11px; font-family:monospace; color:#D1D4DC; margin-bottom:4px;">
        <span>{fmt_price(low_52w)}</span>
        <span style="color:#787b86; font-size:10px; font-family:sans-serif;">ระยะในรอบ 52 สัปดาห์</span>
        <span>{fmt_price(high_52w)}</span>
    </div>
    <div style="position:relative; width:100%; height:4px; background:#1E1E1E; border-radius:2px;">
        <div style="position:absolute; left:0; width:{ratio_52w}%; height:100%; background:#26a69a; border-radius:2px;"></div>
        <div style="position:absolute; left:{ratio_52w}%; top:5px; transform:translateX(-50%); font-size:8px; color:#D1D4DC; line-height:1;">▲</div>
    </div>
</div>

<div style="font-size:12px; font-weight:700; color:#fff; margin-bottom:6px;">สถิติสำคัญ</div>
<div style="display:flex; justify-content:space-between; font-size:11px; padding:3px 0;">
    <span style="color:#787b86;">ปริมาณการซื้อขาย</span>
    <span style="color:#fff; font-family:monospace; font-weight:600;">{vol_24h_str}</span>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; padding:3px 0; margin-bottom:14px;">
    <span style="color:#787b86;">ปริมาณเฉลี่ย (30 วัน)</span>
    <span style="color:#fff; font-family:monospace; font-weight:600;">{vol_30d_str}</span>
</div>

<div style="font-size:12px; font-weight:700; color:#fff; margin-bottom:6px;">ประสิทธิภาพ</div>
{grid_perf}

<div style="font-size:12px; font-weight:700; color:#fff; margin-bottom:4px;">ฤดูกาล</div>
{seasonality_html}
<div style="text-align:center; margin-top:6px; margin-bottom:16px;">
    <span style="background:#161616; color:#9aa0a6; padding:3px 12px; border-radius:12px; font-size:10px; font-weight:600; border:1px solid #262626;">ฤดูกาลเพิ่มเติม</span>
</div>

<div style="font-size:12px; font-weight:700; color:#fff; margin-bottom:6px; border-top:1px solid #1E1E1E; padding-top:10px;">ทางเทคนิค</div>
{gauges_html}

</div></div>"""

def render_tv_quote_card(tk: dict, an: dict, symbol: str, label_name: str, seasonality_html: str = "", gauges_html: str = ""):
    card_html = render_tv_quote_card_html(tk, an, symbol, label_name, seasonality_html, gauges_html)
    st.markdown(card_html, unsafe_allow_html=True)

def render_fibonacci_modal_content(fib, ext, fib_zone, fib_tp, last_close):
    if not fib or "levels" not in fib:
        st.info("ข้อมูลประวัติราคายังไม่เพียงพอในการสร้าง Fibonacci Swing")
        return

    is_uptrend = fib.get("uptrend", True)
    trend_title = "แนวโน้ม: ขาขึ้น ▲ (วัดจาก Low ไป High)" if is_uptrend else "แนวโน้ม: ขาลง ▼ (วัดจาก High ไป Low)"
    trend_badge_color = UP if is_uptrend else DOWN

    st.markdown(f"""<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
        <span style="font-size:16px; font-weight:700; color:#fff;">{trend_title}</span>
        <span style="background:{trend_badge_color}20; color:{trend_badge_color}; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;">
            สวิงกว้าง {fib.get('range_pct', 0.0):.2f}%
        </span>
    </div>""", unsafe_allow_html=True)

    fc1, fc2, fc3, fc4 = st.columns(4)
    fc1.metric("ราคาปัจจุบัน", f"{last_close:,.2f}")
    fc2.metric("โซนปัจจุบัน", fib_zone["label"] if fib_zone else "-", f"ตำแหน่ง {fib_zone['ratio']*100:.1f}%" if fib_zone else "")
    fc3.metric("แนว Golden (0.618)", f"{fib['levels'].get(0.618, 0):,.2f}")
    if fib_tp:
        fc4.metric(f"เป้า TP หลัก ({fib_tp.get('level', 1.618):.3f})", f"{fib_tp.get('tp_price', 0):,.2f}", delta=f"{fib_tp.get('tp_pct', 0):+.2f}%")
    else:
        fc4.metric("เป้า TP หลัก", "-")

    st.markdown("---")
    col_ret, col_ext = st.columns(2)
    with col_ret:
        title_ret = "🟢 แนวรับย่อซื้อ (Retracement Supports)" if is_uptrend else "🔴 แนวต้านเด้งขาย (Retracement Resistances)"
        st.markdown(f"**{title_ret}**")
        ret_rows = []
        for lv, px in sorted(fib.get("levels", {}).items()):
            diff_pct = ((px - last_close) / last_close) * 100.0 if last_close else 0.0
            tag = "⭐ Golden Zone" if lv in (0.5, 0.618) else ("จุดเริ่ม (100%)" if lv == 1.0 else ("จุดยอด (0%)" if lv == 0.0 else ""))
            ret_rows.append({
                "ระดับ (Ratio)": f"{lv:.3f}",
                "ราคา (Price)": f"{px:,.2f}",
                "ระยะห่างจากราคาปัจจุบัน": f"{diff_pct:+.2f}%",
                "หมายเหตุ": tag
            })
        st.dataframe(pd.DataFrame(ret_rows), use_container_width=True, hide_index=True)

    with col_ext:
        st.markdown("**🎯 แผนเป้าหมายทำกำไร (TP) & จุดตัดขาดทุน (SL)**")
        plan_rows = []
        levels = fib.get("levels", {})
        sl_price = levels.get(1.0, min(levels.values()) if levels else last_close * 0.95) if is_uptrend else levels.get(1.0, max(levels.values()) if levels else last_close * 1.05)
        sl_pct = ((sl_price - last_close) / last_close) * 100.0 if last_close else 0.0
        plan_rows.append({
            "ประเภท": "🛑 ตัดขาดทุน (SL)",
            "ระดับเป้าหมาย": "หลุดฐานสวิงเดิม (1.000)",
            "ราคา": f"{sl_price:,.2f}",
            "ความเสี่ยง/ผลตอบแทน": f"{sl_pct:+.2f}%"
        })

        if ext and ext.get("targets"):
            for lv, px in sorted(ext["targets"].items()):
                tp_pct = ((px - last_close) / last_close) * 100.0 if last_close else 0.0
                tag_tp = "🏆 TP หลัก (Golden)" if lv == 1.618 else f"เป้าขยาย {lv:.3f}"
                plan_rows.append({
                    "ประเภท": "🎯 ทำกำไร (TP)",
                    "ระดับเป้าหมาย": tag_tp,
                    "ราคา": f"{px:,.2f}",
                    "ความเสี่ยง/ผลตอบแทน": f"{tp_pct:+.2f}%"
                })
        else:
            plan_rows.append({"ประเภท": "🎯 ทำกำไร (TP)", "ระดับเป้าหมาย": "กำลังรอชุดสวิง A-B-C", "ราคา": "-", "ความเสี่ยง/ผลตอบแทน": "-"})

        st.dataframe(pd.DataFrame(plan_rows), use_container_width=True, hide_index=True)

    if near_golden_zone(last_close, fib):
        st.success("🎯 ราคาปัจจุบันกำลังทดสอบ **Golden Zone (0.5 – 0.618)** ซึ่งเป็นโซนกลับตัวและจุดสะสมที่มีนัยสำคัญสูงสุด")

def color_status(val):
    if val == "มีแรงซื้อ": return 'color: #26a69a'
    elif val == "มีแรงขาย": return 'color: #ef5350'
    else: return 'color: #9aa0a6'

def render_market_modal_content(tk, an, symbol, label_name, seasonality_html, gauges_html):
    st.markdown(f"### 📊 ข้อมูลตลาด 24h & บทวิเคราะห์ทางเทคนิค: {symbol}")
    st.caption(f"กระดาน: {label_name} | ราคาล่าสุด: {tk.get('price', 0):,.2f} ({tk.get('pct', 0):+.2f}%) ")

    tab1, tab2 = st.tabs(["Overview & Gauges", "Indicator & Pivot Tables"])

    with tab1:
        st.markdown("##### 1. รอบผลตอบแทนสะสมรายปี (Seasonality)")
        st.markdown(seasonality_html, unsafe_allow_html=True)

        st.markdown("##### 2. สรุปสัญญาณทางเทคนิค (Technical Indicators)")
        st.markdown(gauges_html, unsafe_allow_html=True)

    with tab2:
        df = st.session_state.get("df_data")
        if df is None or df.empty or len(df) < 30:
            st.info("กำลังโหลดข้อมูล...")
            st.stop()

        if an and "osc" in an and "ma" in an:
            st.markdown("##### 3. ตารางเจาะลึกตัวชี้วัดรายตัว (Indicator Breakdowns)")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown(f"**Oscillators (ตัวแกว่งตัว - {len(an['osc']['rows'])} ดัชนี)**")
                df_osc = pd.DataFrame(an["osc"]["rows"]).rename(columns={"name":"ชื่อดัชนี", "value":"มูลค่า", "action":"สถานะ"})
                if not df_osc.empty:
                    st.dataframe(df_osc.style.map(color_status, subset=['สถานะ']), use_container_width=True, hide_index=True)
                else:
                    st.dataframe(df_osc, use_container_width=True, hide_index=True)

            with t_col2:
                st.markdown(f"**ค่าเฉลี่ยเคลื่อนที่ (Moving Averages - {len(an['ma']['rows'])} เส้น)**")
                df_ma = pd.DataFrame(an["ma"]["rows"]).rename(columns={"name":"ชื่อเส้นค่าเฉลี่ย", "value":"ระดับราคา", "action":"สถานะ"})
                if not df_ma.empty:
                    st.dataframe(df_ma.style.map(color_status, subset=['สถานะ']), use_container_width=True, hide_index=True)
                else:
                    st.dataframe(df_ma, use_container_width=True, hide_index=True)

        if "pivots" in an:
            st.markdown("##### 4. จุดกลับตัวเดย์เทรด (Pivot Points)")
            p_rows = []
            for m_name, vals in an["pivots"].items():
                p_rows.append({
                    "วิธีคำนวณ": m_name,
                    "แนวรับ 2 (S2)": f"{vals['S2']:,.2f}",
                    "แนวรับ 1 (S1)": f"{vals['S1']:,.2f}",
                    "จุดหมุน (Pivot)": f"{vals['P']:,.2f}",
                    "แนวต้าน 1 (R1)": f"{vals['R1']:,.2f}",
                    "แนวต้าน 2 (R2)": f"{vals['R2']:,.2f}"
                })
            st.dataframe(pd.DataFrame(p_rows), use_container_width=True, hide_index=True)

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

def sanitize_markers(markers: list) -> list:
    if not markers: return []
    seen = set()
    cleaned = []
    sorted_markers = sorted(markers, key=lambda x: int(x.get("time", 0)))
    for m in sorted_markers:
        t = int(m.get("time", 0))
        if t <= 0 or t in seen: continue
        seen.add(t)
        m["time"] = t
        cleaned.append(m)
    return cleaned

def price_precision(df: pd.DataFrame) -> int:
    if df is None or df.empty or "close" not in df.columns: return 2
    p = float(df["close"].iloc[-1])
    if p >= 1000: return 2
    if p >= 10: return 3
    if p >= 0.1: return 5
    return 8

def min_move(df: pd.DataFrame) -> float:
    return 10 ** -price_precision(df)

def build_charts(df, symbol, tf, main_h, rsi_h, macd_h):
    if df is None or df.empty:
        return []

    show_r = st.session_state.get('show_rsi', True)
    show_m = st.session_state.get('show_macd', True)
    d = df.copy()

    if hasattr(d.columns, 'str'):
        d.columns = d.columns.astype(str).str.lower()
    d = d.loc[:, ~d.columns.duplicated()]

    if 'time' not in d.columns:
        if isinstance(d.index, pd.DatetimeIndex) or d.index.name is not None:
            d = d.reset_index(drop=False)
            if 'time' not in d.columns and len(d.columns) > 0:
                d = d.rename(columns={d.columns[0]: 'time'})
        else:
            d['time'] = range(len(d))

    if 'time' not in d.columns:
        d['time'] = range(len(d))

    d.columns = [str(c).lower() for c in d.columns]

    if pd.api.types.is_datetime64_any_dtype(d['time']):
        d['time'] = (d['time'].astype('int64') // 10**9).astype('int64')
    else:
        d['time'] = pd.to_numeric(d['time'], errors='coerce').fillna(0).astype('int64')

    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col not in d.columns:
            d[col] = 100.0 if col == 'volume' else 0.0
        else:
            d[col] = pd.to_numeric(d[col], errors='coerce').fillna(0.0)

    records = d.to_dict('records')

    ts_opts = {
        "borderColor": "#1E1E1E", "timeVisible": True, "secondsVisible": tf in ("1m", "3m", "5m"),
        "fixLeftEdge": False, "rightOffset": 5,
        "handleScroll": {"mouseWheel": True, "pressedMouseMove": True, "horzTouchDrag": True, "vertTouchDrag": True},
        "handleScale": {"axisPressedMouseMove": True, "mouseWheel": True, "pinch": True},
    }

    base_chart = {
        "layout": {"background": {"type": "solid", "color": "#000000"}, "textColor": "#D1D4DC"},
        "grid": {"vertLines": {"color": "#141414"}, "horzLines": {"color": "#141414"}},
        "crosshair": {"mode": 0},
        "rightPriceScale": {
            "autoScale": True,
            "borderColor": "#1E1E1E",
            "scaleMargins": {"top": 0.1, "bottom": 0.1},
            "mode": 0
        },
        "timeScale": ts_opts,
    }

    candles = [
        {
            "time": int(r["time"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"])
        }
        for r in records if r["time"] > 0
    ]

    price_series = [{
        "type": "Candlestick", 
        "data": candles,
        "options": {
            "upColor": UP, "downColor": DOWN, "borderVisible": False, 
            "wickUpColor": UP, "wickDownColor": DOWN,
            "priceScaleId": "right",
            "priceFormat": {
                "type": "price",
                "precision": price_precision(d),
                "minMove": min_move(d)
            }
        }
    }]

    show_sig = st.session_state.get("show_sig", False)
    show_stars = st.session_state.get("show_stars", True)
    show_dots = st.session_state.get("show_dots", False)

    if show_sig or show_stars or show_dots:
        marker_map = {}
        for r in records:
            t = int(r["time"])
            labels = []
            sig = str(r.get("signal", ""))
            is_buy = sig == "BUY"
            is_sell = sig == "SELL ALL"

            if show_sig and (is_buy or is_sell): labels.append(sig)
            if show_stars and r.get("star", False): labels.append("⭐")
            dot = str(r.get("dot_warn", ""))
            if show_dots and dot: labels.append("🔴" if dot == "RED" else "🟠")

            if labels:
                marker_map[t] = {
                    "time": t, "position": "belowBar" if is_buy else "aboveBar",
                    "color": UP if is_buy else (DOWN if is_sell else "#ffd700"),
                    "shape": "arrowUp" if is_buy else ("arrowDown" if is_sell else "circle"),
                    "text": " ".join(labels), "size": 1
                }

        raw_markers = list(marker_map.values())
        clean_markers = sanitize_markers(raw_markers)
        if clean_markers:
            price_series[0]["markers"] = clean_markers

    ema_alpha = (100 - st.session_state.get("ema_opacity", 0)) / 100.0
    trend_alpha = (100 - st.session_state.get("trend_opacity", 60)) / 100.0
    lw = int(st.session_state.get("line_width", 2))

    if st.session_state.get("show_fast", True) and "ema_fast" in d:
        fast_data = [{"time": int(r["time"]), "value": float(r["ema_fast"])} for r in records if pd.notna(r.get("ema_fast")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": fast_data,
            "options": {"color": f"rgba(41, 98, 255, {ema_alpha:.2f})", "lineWidth": lw, "priceLineVisible": False}
        })

    if st.session_state.get("show_slow", True) and "ema_slow" in d:
        slow_data = [{"time": int(r["time"]), "value": float(r["ema_slow"])} for r in records if pd.notna(r.get("ema_slow")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": slow_data,
            "options": {"color": f"rgba(239, 83, 80, {ema_alpha:.2f})", "lineWidth": lw, "priceLineVisible": False}
        })

    if st.session_state.get("show_trend", True) and "ema_trend" in d:
        trend_data = [{"time": int(r["time"]), "value": float(r["ema_trend"])} for r in records if pd.notna(r.get("ema_trend")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": trend_data,
            "options": {"color": f"rgba(255, 255, 255, {trend_alpha:.2f})", "lineWidth": max(1, lw - 1), "lineStyle": 2, "priceLineVisible": False}
        })

    vol = [
        {
            "time": int(r["time"]),
            "value": float(r.get("volume", 0)),
            "color": UP + "80" if float(r.get("close", 0)) >= float(r.get("open", 0)) else DOWN + "80"
        }
        for r in records if pd.notna(r.get("volume")) and r["time"] > 0
    ]
    price_series.append({
        "type": "Histogram", "data": vol,
        "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol"},
        "priceScale": {"scaleMargins": {"top": 0.8, "bottom": 0}}
    })

    charts = [{
        "chart": {
            **base_chart,
            "height": main_h,
            "watermark": {"visible": True, "text": f"{symbol} · {tf}", "fontSize": 40, "color": "rgba(255,255,255,0.05)"}
        },
        "series": price_series
    }]

    def make_rsi_pane():
        rsi_data = [{"time": int(r["time"]), "value": float(r["rsi"])} for r in records if pd.notna(r.get("rsi")) and r["time"] > 0]
        mk = lambda v: [{"time": int(r["time"]), "value": v} for r in records if r["time"] > 0]
        return {
            "chart": {
                **base_chart, "height": rsi_h,
                "watermark": {"visible": True, "text": "RSI (14)", "fontSize": 18, "color": "rgba(0, 188, 212, 0.08)"}
            },
            "series": [
                {"type": "Line", "data": mk(70.0), "options": {"color": "rgba(239,83,80,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                {"type": "Line", "data": mk(50.0), "options": {"color": "rgba(120,123,134,0.3)", "lineWidth": 1, "lineStyle": 3, "priceLineVisible": False}},
                {"type": "Line", "data": mk(30.0), "options": {"color": "rgba(38,166,154,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                {"type": "Line", "data": rsi_data, "options": {"color": "#00bcd4", "lineWidth": 2, "priceLineVisible": True}},
            ]
        }

    def make_macd_pane():
        macd_line = [{"time": int(r["time"]), "value": float(r["macd"])} for r in records if pd.notna(r.get("macd")) and r["time"] > 0]
        sig_line  = [{"time": int(r["time"]), "value": float(r["macd_sig"])} for r in records if pd.notna(r.get("macd_sig")) and r["time"] > 0]
        hist = [
            {"time": int(r["time"]), "value": float(r["macd_hist"]), "color": UP + "90" if float(r.get("macd_hist", 0)) >= 0 else DOWN + "90"}
            for r in records if pd.notna(r.get("macd_hist")) and r["time"] > 0
        ]
        return {
            "chart": {
                **base_chart, "height": macd_h,
                "watermark": {"visible": True, "text": "MACD (12, 26, 9)", "fontSize": 18, "color": "rgba(0, 230, 118, 0.08)"}
            },
            "series": [
                {"type": "Histogram", "data": hist, "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "macd_hist"}},
                {"type": "Line", "data": macd_line, "options": {"color": "#00e676", "lineWidth": 2, "priceLineVisible": False}},
                {"type": "Line", "data": sig_line, "options": {"color": "#ff5252", "lineWidth": 2, "priceLineVisible": False}},
            ]
        }

    for p in st.session_state.get("pane_order", ["rsi", "macd"]):
        if p == "rsi" and show_r:
            charts.append(make_rsi_pane())
        elif p == "macd" and show_m:
            charts.append(make_macd_pane())

    return charts

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
            _c = float(_q.get("percentChange", _q.get("change_pct", 0.0)))
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
        st.markdown("<div style='height:18px;border-left:1px solid #222;margin:0 auto;'></div>", unsafe_allow_html=True)
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
                        st.session_state["selected_symbol_picker"] = r["symbol"]
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
                        st.session_state["selected_symbol_picker"] = r["symbol"]
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
                                st.session_state["selected_symbol_picker"] = s_item
                                _clear_chart_state()
                                st.rerun()
                        with b: st.markdown(f"<div style='font-family:monospace; font-size:11px; text-align:right; padding-top:4px; color:#fff;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
                        with c: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{fmt_chg(q['change'])}</div>", unsafe_allow_html=True)
                        with dcol: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{sign}{q['pct']:.2f}%</div>", unsafe_allow_html=True)
                        with f:
                            if st.button("✕", key=f"del_{key_prefix}_{cat_name}_{s_item}", help="ลบออก"):
                                st.session_state["star_watchlists"][cat_name].remove(s_item)
                                st.rerun()

with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบ")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("💻 Desktop", use_container_width=True): st.session_state["mobile_mode"] = False; st.rerun()
    with col_m2:
        if st.button("📱 Mobile", use_container_width=True): st.session_state["mobile_mode"] = True; st.rerun()

    if st.button("🧹 เคลียร์แคชระบบ", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        _clear_chart_state()
        st.rerun()
    st.divider()

    with st.expander("📌 ตลาดและสินทรัพย์", expanded=True):
        market_categories = [
            "🟡 คริปโต (Crypto)", "🇺🇸 หุ้นสหรัฐฯ (US Stocks)", "🇨🇳 หุ้นจีน (China)",
            "🇹🇭 หุ้นไทย (SET/mai)", "🇻🇳 หุ้นเวียดนาม (Vietnam)",
            "🟠 สินค้าโภคภัณฑ์ (Commodities)", "🟢 อัตราแลกเปลี่ยน (Forex)"
        ]
        selected_category = st.selectbox("หมวดหมู่ตลาด", market_categories, key="selected_market_category")

        current_available_symbols = []
        selected_exchange = None

        if selected_category == "🟡 คริปโต (Crypto)":
            exchanges = ["Bitkub", "Binance", "OKX", "Bybit", "Gate.io", "MEXC", "KuCoin"]
            selected_exchange = st.selectbox("กระดานเทรด", exchanges, key="selected_crypto_exchange")
            if selected_exchange == "Bitkub":
                current_available_symbols = get_full_bitkub_symbols()
            elif selected_exchange == "Binance":
                current_available_symbols = get_full_binance_symbols()
            elif selected_exchange == "OKX":
                current_available_symbols = get_full_okx_symbols()
            elif selected_exchange == "Bybit":
                current_available_symbols = get_full_bybit_symbols()
            elif selected_exchange == "Gate.io":
                current_available_symbols = get_full_gate_symbols()
            elif selected_exchange == "MEXC":
                current_available_symbols = get_full_mexc_symbols()
            elif selected_exchange == "KuCoin":
                current_available_symbols = get_full_kucoin_symbols()
        elif selected_category == "🇺🇸 หุ้นสหรัฐฯ (US Stocks)":
            current_available_symbols = get_full_sp500_symbols()
        elif selected_category == "🇨🇳 หุ้นจีน (China)":
            current_available_symbols = get_full_china_stocks()
        elif selected_category == "🇹🇭 หุ้นไทย (SET/mai)":
            current_available_symbols = fetch_set_all_symbols()
        elif selected_category == "🇻🇳 หุ้นเวียดนาม (Vietnam)":
            current_available_symbols = get_full_vietnam_symbols()
        elif selected_category == "🟠 สินค้าโภคภัณฑ์ (Commodities)":
            current_available_symbols = get_full_commodities()
        elif selected_category == "🟢 อัตราแลกเปลี่ยน (Forex)":
            current_available_symbols = get_full_forex()

        safe_current_symbols = current_available_symbols or []
        custom_syms_clean = [s for s in st.session_state.get("custom_symbols", []) if s not in safe_current_symbols]
        display_symbols = (custom_syms_clean or []) + safe_current_symbols

        if "current_symbol" in st.session_state and st.session_state["current_symbol"] not in display_symbols:
            display_symbols.insert(0, st.session_state["current_symbol"])

        if not display_symbols: display_symbols = ["- Select -"]

        cur_idx = 0
        if "current_symbol" in st.session_state and st.session_state["current_symbol"] in display_symbols:
            cur_idx = display_symbols.index(st.session_state["current_symbol"])
        elif "- Select -" in display_symbols:
            cur_idx = display_symbols.index("- Select -")
            
        def format_symbol_label(s: str) -> str:
            if s in CHINA_STOCK_NAMES: return f"{s} — {CHINA_STOCK_NAMES[s]}"
            if s in COMMODITY_NAMES: return f"{s} — {COMMODITY_NAMES[s]}"
            if s in FOREX_NAMES: return f"{s} — {FOREX_NAMES[s]}"
            return s

        picked = st.selectbox("🔍 เลือกสินทรัพย์:", display_symbols, index=cur_idx, format_func=format_symbol_label, key="selected_symbol_picker")
        
        if picked != st.session_state.get("current_symbol") and picked != "- Select -":
            cur = _find_tab(st.session_state.active_tab_id)
            if cur: cur["symbol"] = picked
            st.session_state["current_symbol"] = picked
            _clear_chart_state()
            st.rerun()

        new_ticker = st.text_input("➕ เพิ่ม Ticker (เฉพาะกิจ):", placeholder="เช่น AAA.VN, PLTR", key="add_new_ticker")
        if st.button("บันทึก Ticker", use_container_width=True, key="save_new_ticker") and new_ticker:
            sym_clean = new_ticker.strip().upper()
            if sym_clean and sym_clean not in st.session_state["custom_symbols"]:
                st.session_state["custom_symbols"].insert(0, sym_clean)
            cur = _find_tab(st.session_state.active_tab_id)
            if cur: cur["symbol"] = sym_clean
            st.session_state["current_symbol"] = sym_clean
            _clear_chart_state()
            st.rerun()

        cur_sym = st.session_state.get("current_symbol", "BTC_THB")
        _rm, _re = resolve_route(cur_sym)
        st.caption(f"📡 แหล่งข้อมูล: **{route_label(_rm, _re)}**")

        st.caption(f"⭐ ติดดาวกลุ่มสี: **{cur_sym}**")
        star_cols = st.columns(5)
        for i, (cat_label, cat_info) in enumerate(STAR_CATEGORIES.items()):
            with star_cols[i]:
                has = cur_sym in st.session_state["star_watchlists"][cat_label]
                btn_display = f"★{cat_info['icon']}" if has else cat_info["icon"]
                if st.button(btn_display, key=f"qs_btn_{i}", use_container_width=True):
                    if has: st.session_state["star_watchlists"][cat_label].remove(cur_sym)
                    else: st.session_state["star_watchlists"][cat_label].append(cur_sym)
                    st.rerun()

    with st.expander("⚙️ ตั้งค่าอินดิเคเตอร์ (Diamond Armor)", expanded=False):
        tab_info, tab_style = st.tabs(["ข้อมูล", "รูปแบบ"])

        with tab_info:
            st.session_state["fast_ema"] = st.number_input("Fast EMA (น้ำเงิน)", 1, 200, int(st.session_state["fast_ema"]))
            st.session_state["slow_ema"] = st.number_input("Slow EMA (แดง)", 1, 200, int(st.session_state["slow_ema"]))
            st.session_state["trend_ema"] = st.number_input("Trend Filter (ขาว)", 1, 400, int(st.session_state["trend_ema"]))
            st.divider()
            st.session_state["min_tp"] = st.number_input("Minimum TP Threshold (%)", 0.0, 100.0, float(st.session_state["min_tp"]), 0.5)
            st.session_state["warn_pct"] = st.number_input("Orange Dot Warning (%)", 0.0, 100.0, float(st.session_state["warn_pct"]), 0.5)
            st.session_state["danger_pct"] = st.number_input("Red Dot Danger (%)", 0.0, 100.0, float(st.session_state["danger_pct"]), 0.5)
            st.session_state["show_stars"] = st.checkbox("Show Stars (⭐)", value=st.session_state["show_stars"])

        with tab_style:
            st.session_state["show_fast"]  = st.checkbox("Fast EMA", value=st.session_state["show_fast"])
            st.session_state["show_slow"]  = st.checkbox("Slow EMA", value=st.session_state["show_slow"])
            st.session_state["show_trend"] = st.checkbox("Trend Filter", value=st.session_state["show_trend"])
            st.session_state["show_rsi"]   = st.checkbox("ช่อง RSI (14)", value=st.session_state["show_rsi"])
            st.session_state["show_macd"]  = st.checkbox("ช่อง MACD", value=st.session_state["show_macd"])
            st.session_state["show_sig"]   = st.checkbox("ป้ายสัญญาณ BUY/SELL", value=st.session_state["show_sig"])
            st.session_state["show_dots"]  = st.checkbox("จุดเตือน Orange/Red Dots", value=st.session_state["show_dots"])
            st.divider()
            st.session_state["ema_opacity"]   = st.slider("EMA Transparency", 0, 100, int(st.session_state["ema_opacity"]))
            st.session_state["trend_opacity"] = st.slider("Trend Filter Transparency", 0, 100, int(st.session_state["trend_opacity"]))
            st.session_state["line_width"]    = st.slider("ความหนาเส้น EMA", 1, 3, int(st.session_state["line_width"]))

            st.divider()
            if st.button("⇅ สลับตำแหน่ง RSI / MACD", use_container_width=True):
                st.session_state["pane_order"] = list(reversed(st.session_state["pane_order"]))
                st.rerun()

            st.session_state["main_h"] = st.slider("ความสูงกราฟหลัก", 300, 900, value=int(st.session_state.get("main_h", 520)), step=20)
            if st.session_state.get("show_rsi", True):
                st.session_state["rsi_h"] = st.slider("ความสูง RSI", 80, 400, value=int(st.session_state.get("rsi_h", 120)), step=10)
            if st.session_state.get("show_macd", True):
                st.session_state["macd_h"] = st.slider("ความสูง MACD", 80, 400, value=int(st.session_state.get("macd_h", 120)), step=10)

        st.divider()
        if st.button("🔄 คืนค่าเริ่มต้น (Reset)", use_container_width=True):
            st.session_state["fast_ema"] = 7
            st.session_state["slow_ema"] = 13
            st.session_state["trend_ema"] = 45
            st.session_state["min_tp"] = 3.0
            st.session_state["warn_pct"] = 3.0
            st.session_state["danger_pct"] = 7.0
            st.session_state["show_stars"] = True
            st.session_state["show_fast"] = True
            st.session_state["show_slow"] = True
            st.session_state["show_trend"] = True
            st.session_state["show_rsi"] = True
            st.session_state["show_macd"] = True
            st.session_state["show_sig"] = False
            st.session_state["show_dots"] = False
            st.session_state["ema_opacity"] = 0
            st.session_state["trend_opacity"] = 60
            st.session_state["line_width"] = 2
            st.session_state["main_h"] = 520
            st.session_state["rsi_h"] = 120
            st.session_state["macd_h"] = 120
            st.rerun()

    with st.expander("📐 ระบบ Fibonacci Suite", expanded=True):
        if st.button("🔍 เปิดแผงวิเคราะห์ Fibonacci (Pop-up)", use_container_width=True):
            st.session_state["trigger_fib_modal"] = True

        st.divider()
        st.session_state["fib_lookback"] = st.slider("ความไวการหา Swing", 2, 15, int(st.session_state["fib_lookback"]))
        st.session_state["fib_window"] = st.slider("จำนวนแท่งวิเคราะห์", 30, 400, int(st.session_state["fib_window"]), step=10)
        st.session_state["fib_tp_level"] = st.selectbox("ระดับ Fib เป้าหมายหลัก", [1.272, 1.414, 1.618, 2.0, 2.618], index=2)
        st.session_state["fib_confirm_on"] = st.checkbox("ใช้ Golden Zone ยืนยันสัญญาณ BUY", value=st.session_state["fib_confirm_on"])

# ──────────────────────────── DASHBOARD ────────────────────────────
auto = st.session_state.get("auto_refresh", False)
every = int(st.session_state.get("refresh_sec", 5))
frag_interval = every if auto else None

@st.fragment(run_every=frag_interval)
def dashboard():
    tf, bars, fill_gaps, auto, every, reload_btn = render_top_toolbar()

    symbol = st.session_state.get("current_symbol", "BTC_THB")
    r_market, r_exchange = resolve_route(symbol)
    label_display = route_label(r_market, r_exchange)

    state_key = f"{r_market}_{r_exchange}_{symbol}_{tf}_{bars}_{fill_gaps}"
    
    if ("df_data" not in st.session_state) or (st.session_state.get("active_key") != state_key) or reload_btn:
        with st.spinner(f"กำลังโหลดประวัติ {symbol} ({bars:,} แท่ง) …"):
            df = fetch_ohlcv(r_market, r_exchange, symbol, tf, bars, fill_gaps)
        st.session_state["df_data"] = df
        st.session_state["active_key"] = state_key
    else:
        df = st.session_state.get("df_data", pd.DataFrame())
        if auto and not df.empty:
            q = fetch_item_quote(symbol)
            if q.get("price", 0) > 0:
                cur_p = q["price"]
                df.iloc[-1, df.columns.get_loc("close")] = cur_p
                if cur_p > df.iloc[-1]["high"]: df.iloc[-1, df.columns.get_loc("high")] = cur_p
                if cur_p < df.iloc[-1]["low"]:  df.iloc[-1, df.columns.get_loc("low")]  = cur_p
                st.session_state["df_data"] = df

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

    if st.session_state.get("trigger_fib_modal", False):
        st.session_state["trigger_fib_modal"] = False
        open_fib_dialog(fib, ext, fib_zone, fib_tp, last_close)

    if st.session_state.get("trigger_market_modal", False):
        st.session_state["trigger_market_modal"] = False
        open_market_dialog(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_modal)

    trend_color = UP if stats["trend"] == "UP" else DOWN
    chg_color = UP if stats["change_pct"] >= 0 else DOWN
    display_title = CHINA_STOCK_NAMES.get(symbol, COMMODITY_NAMES.get(symbol, FOREX_NAMES.get(symbol, symbol)))

    gz_badge = ""
    if fib_confirm and fib:
        if is_in_gz:
            gz_badge = '&nbsp;|&nbsp;<span style="background:rgba(38,166,154,0.18);color:#26a69a;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:bold;">🎯 Golden Zone ยืนยันแล้ว</span>'
        else:
            gz_badge = '&nbsp;|&nbsp;<span style="background:rgba(255,152,0,0.18);color:#ff9800;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:bold;">⏳ รอราคาเข้า Golden Zone</span>'

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
    # ใช้ราคาและ % Change ล่าสุดจาก Ticker ตรงๆ เพื่อให้เท่ากับการ์ดขวา
    cur_price = float(tk_data.get("price", stats["price"]))
    cur_chg = float(tk_data.get("percentChange", tk_data.get("change_pct", 0.0)))
    chg_txt_color = "#26a69a" if cur_chg >= 0 else "#ef5350"

    price_fmt = f"{cur_price:,.4f}" if cur_price < 10 else f"{cur_price:,.2f}"
    bid_p = float(tk_data.get("bid", cur_price))
    bid_fmt = f"{bid_p:,.4f}" if bid_p < 10 else f"{bid_p:,.2f}"
    ask_p = float(tk_data.get("ask", cur_price))
    ask_fmt = f"{ask_p:,.4f}" if ask_p < 10 else f"{ask_p:,.2f}"
    spread_p = abs(ask_p - bid_p)
    spread_fmt = f"{spread_p:,.4f}" if spread_p < 1 else f"{spread_p:,.2f}"
    vol_val = float(df.iloc[-1].get("volume", 0.0))

    top_bar_html = f"""
    <div style="background-color:#0A0A0A; border:1px solid #1E1E1E; border-radius:4px; padding:6px 12px; font-family:-apple-system,BlinkMacSystemFont,monospace; color:#D1D4DC; display:flex; justify-content:space-between; align-items:center; width:100%; box-sizing:border-box;">
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="color:#26a69a; font-size:14px;">●</span>
                <span style="color:#FFFFFF; font-weight:700; font-size:16px;">{price_fmt}</span>
                <span style="color:{chg_txt_color}; font-weight:700; font-size:14px;">({cur_chg:+.2f}%)</span>
                <span style="color:#787b86; font-size:11px; margin-left:4px;">ปริมาณ {vol_val:,.2f}</span>
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
    cur_main_h = int(st.session_state.get("main_h", 520))
    cur_rsi_h = int(st.session_state.get("rsi_h", 120))
    cur_macd_h = int(st.session_state.get("macd_h", 120))

    charts = build_charts(df, symbol, tf, cur_main_h, cur_rsi_h, cur_macd_h)

    clock_html = """
    <div style="display:flex; justify-content:space-between; align-items:center; background:#0A0A0A; border:1px solid #1E1E1E; border-top:none; border-bottom-left-radius:4px; border-bottom-right-radius:4px; padding:3px 10px; font-family:monospace; font-size:11px; color:#787b86; margin-top:-2px;">
        <div><span>⏱️ เวลาตลาด: </span><b id="liveClock" style="color:#26a69a;">--:--:--</b> <span style="color:#555;">(UTC+7 Bangkok)</span></div>
        <div><span>สถานะเซิร์ฟเวอร์: </span><span style="color:#00bcd4;">เชื่อมต่อปกติ</span></div>
    </div>
    <script>
        function updateClock() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('th-TH', { hour12: false });
            const el = document.getElementById('liveClock');
            if (el) el.innerText = timeStr;
        }
        setInterval(updateClock, 1000);
        updateClock();
    </script>
    """

    show_r = st.session_state.get('show_rsi', True)
    show_m = st.session_state.get('show_macd', True)
    p_ord = "_".join(st.session_state.get("pane_order", ["rsi", "macd"]))
    cur_size = st.session_state.get("panel_size", "M")
    
    chart_dyn_key = (
        f"c_{symbol}_{tf}_{st.session_state.get('active_tab_id', '0')}_"
        f"{show_r}_{show_m}_{p_ord}_{cur_main_h}_{cur_rsi_h}_{cur_macd_h}_"
        f"{cur_size}"
    )

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
            renderLightweightCharts(charts, key=chart_dyn_key)
            components.html(clock_html, height=28)

        with col_toggle:
            btn_label = "❯" if st.session_state.get("panel_open", True) else "❮"
            if st.button(btn_label, key="toggle_panel_btn_mob", help="ย่อ/ขยายแผงขวา", use_container_width=True):
                st.session_state["panel_open"] = not st.session_state.get("panel_open", True)
                st.rerun()

        if st.session_state.get("panel_open", True) and col_quote:
            with col_quote:
                with st.expander("⭐ รายการสินทรัพย์ & อันดับขาขึ้น-ลง", expanded=True):
                    render_watchlist_component(key_prefix="mob")
                with st.expander("📊 ข้อมูลตลาด 24h & เทคนิค", expanded=True):
                    if st.button("⛶ ขยายดูตลาด 24h (Pop-up)", key="btn_popup_market_mob", use_container_width=True):
                        st.session_state["trigger_market_modal"] = True
                        st.rerun()
                    render_tv_quote_card(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_compact)
        return

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
        st.markdown('<div style="width: 100%; overflow: hidden;">', unsafe_allow_html=True)
        renderLightweightCharts(charts, key=chart_dyn_key)
        st.markdown('</div>', unsafe_allow_html=True)
        components.html(clock_html, height=28)

    with col_toggle:
        btn_label = "❯" if st.session_state.get("panel_open", True) else "❮"
        if st.button(btn_label, key="toggle_panel_btn", help="ย่อ/ขยายแผงขวา", use_container_width=True):
            st.session_state["panel_open"] = not st.session_state.get("panel_open", True)
            st.rerun()

    if st.session_state.get("panel_open", True) and col_quote:
        with col_quote:
            cs_col1, cs_col2, cs_col3 = st.columns(3)
            with cs_col1:
                if st.button("เล็ก", use_container_width=True, key="sz_s"):
                    st.session_state["panel_size"] = "S"; st.rerun()
            with cs_col2:
                if st.button("ปกติ", use_container_width=True, key="sz_m"):
                    st.session_state["panel_size"] = "M"; st.rerun()
            with cs_col3:
                if st.button("กว้าง", use_container_width=True, key="sz_l"):
                    st.session_state["panel_size"] = "L"; st.rerun()

            with st.expander("⭐ รายการสินทรัพย์ & อันดับขาขึ้น-ลง", expanded=True):
                render_watchlist_component(key_prefix="desk")

            with st.expander("📊 ข้อมูลตลาด 24h & เทคนิค", expanded=True):
                if st.button("⛶ ขยายดูตลาด 24h (Pop-up)", key="btn_popup_market_desk", use_container_width=True):
                    st.session_state["trigger_market_modal"] = True
                    st.rerun()
                render_tv_quote_card(tk_data, tech_data, symbol, label_display, seasonality_html, gauges_html_compact)

dashboard()