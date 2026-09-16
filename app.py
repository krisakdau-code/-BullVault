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
from ui.sidebar_refactored import render_sidebar
from ui.floating_toggle import render_floating_sidebar_toggle
from chart_builders import build_charts
from config import *
from data.rice_ohlcv import generate_rice_ohlcv
from ui.rice_tab import show_rice_dialog_modal, render_rice_tab
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
    render_tv_quote_card,
    render_panel_controls,
)
from data.fetchers import fetch_ohlcv, fetch_ticker_24h
from data.symbols import (
    get_full_binance_symbols,
    get_full_bitkub_symbols,
    get_full_commodities,
    get_full_forex,
    get_full_sp500_symbols,
)
from urllib3.util.retry import Retry
from utils import _has_data, fmt_chg, fmt_price, fmt_vol

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from fib_tools import (
        auto_fib_retracement,
        current_fib_zone,
        fib_tp_target,
        trend_based_fib_extension,
    )
except ImportError:
    auto_fib_retracement = None

st.set_page_config(page_title="Diamond Armor Universal", page_icon="💎", layout="wide")

st.markdown("""
<style>
    /* 1. ยุบ Header และแถบเครื่องมือของ Streamlit ทั้งหมด */
    header, .stAppHeader,
    [data-testid="stHeader"], [data-testid="stAppHeader"],
    [data-testid="stDecoration"], [data-testid="stToolbar"],
    [data-testid="stStatusWidget"], [data-testid="stMainMenu"] {
        display: none !important;
        height: 0px !important;
        min-height: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
    }

    [data-testid="stSidebar"] { top: 0 !important; }
    section[data-testid="stMain"] { padding-top: 0 !important; top: 0 !important; }
    [data-testid="stAppViewContainer"] { padding-top: 0 !important; top: 0 !important; }

    /* 2. ตัดกล่องว่างและ Wrapper ซ่อนทั้งหมด (ลบพื้นที่สีเขียวทิ้ง 100%) */
    div[data-testid="stElementContainer"]:has(iframe[height="0"]),
    div[data-testid="stElementContainer"]:has(iframe[width="0"]),
    div[data-testid="stElementContainer"]:has(.stCustomComponentV1 > iframe[height="0"]),
    div[data-testid="stElementContainer"]:has(> div.stMarkdown > style),
    div[data-testid="stElementContainer"]:has(> div.stMarkdown:empty) {
        display: none !important;
        height: 0px !important;
        min-height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
    }

    /* 3. ดึงเนื้อหาหลักทั้งหมดขยับขึ้นแนบชิดขอบบน 0px ทันที */
    .block-container,
    .stMainBlockContainer,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"],
    section[data-testid="stMain"] .block-container {
        padding-top: 0rem !important;
        margin-top: -24px !important; /* ปรับดึงทุกอย่างขึ้นชิดขอบบน */
        padding-bottom: 0rem !important;
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
        max-width: 100% !important;
    }

    /* 4. ซ่อน Native Sidebar ดั้งเดิม */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"],
    button[kind="header"],
    button[kind="headerNoPadding"] {
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
        height: 0px !important;
    }

    /* 5. ปุ่ม Timeframe แนวนอนสไตล์ Pill มน */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 3px !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label {
        padding: 3px 6px !important;
        margin: 0 !important;
        border-radius: 4px !important;
        cursor: pointer !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #9aa0a6 !important;
        background: transparent !important;
        border: none !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label:hover {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) {
        color: #ffffff !important;
        background-color: #2a2e39 !important;
    }
</style>
""", unsafe_allow_html=True)

if "current_symbol" not in st.session_state: st.session_state["current_symbol"] = "BTCUSDT"
if "selected_tf" not in st.session_state: st.session_state["selected_tf"] = "1h"
if "fast_ema" not in st.session_state: st.session_state["fast_ema"] = 7
if "slow_ema" not in st.session_state: st.session_state["slow_ema"] = 13
if "trend_ema" not in st.session_state: st.session_state["trend_ema"] = 45
if "warn_pct" not in st.session_state: st.session_state["warn_pct"] = 3.0
if "danger_pct" not in st.session_state: st.session_state["danger_pct"] = 7.0
if "fib_lookback" not in st.session_state: st.session_state["fib_lookback"] = 5
if "fib_window" not in st.session_state: st.session_state["fib_window"] = 120
if "fib_tp_level" not in st.session_state: st.session_state["fib_tp_level"] = 1.618
if "min_tp" not in st.session_state: st.session_state["min_tp"] = 3.0

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update(BROWSER_HEADERS)
retry_strategy = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
HTTP_SESSION.mount("https://", HTTPAdapter(max_retries=retry_strategy))

def fetch_binance_raw(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    iv_map = {"D": "1d", "2D": "1d", "3D": "1d", "W": "1w", "M": "1M"}
    interval = iv_map.get(interval, interval)
    try:
        r = HTTP_SESSION.get("https://api.binance.com/api/v3/klines", params={"symbol": symbol, "interval": interval, "limit": min(bars, 1000)}, timeout=5)
        if r.status_code == 200:
            k = r.json()
            df = pd.DataFrame(k, columns=["ot","open","high","low","close","volume","ct","qv","n","tb","tq","ig"])
            df = df[["ot","open","high","low","close","volume"]].astype(float)
            df["time"] = (df["ot"] // 1000).astype("int64")
            return df.dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)
    except Exception: pass
    return pd.DataFrame()

def fetch_ohlcv(symbol: str, tf: str, bars: int) -> pd.DataFrame:
    # 1. สินค้ากลุ่มข้าว ให้ดึงผ่านโมดูลข้าว
    if symbol.startswith("RICE:") or symbol.startswith("FOB:") or symbol == "ZR=F (CBOT Rough Rice)":
        return generate_rice_ohlcv(symbol)
    
    # 2. สินทรัพย์จริงทุกตลาด (คริปโต, หุ้นไทย, ทองคำ, Forex) ดึงสดผ่าน data/fetchers.py
    from data.fetchers import fetch_ohlcv as fetch_market_ohlcv
    df = fetch_market_ohlcv(symbol=symbol, tf=tf, limit=bars)
    
    # 3. แปลง Timestamp ให้อยู่ในฟอร์แมต Unix Seconds สำหรับ Lightweight Charts
    if not df.empty and "time" in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df["time"]):
            df["time"] = (df["time"].astype("int64") // 10**9)
        return df.dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)
        
    return df
def render_top_toolbar():
    # ขยายสัดส่วน col_tf เป็น 5.5 ให้ปุ่ม Timeframe เรียงแนวนอนแบบไม่อึดอัด
    col_spacer, col_tf, col_slider, col_ind_menu, col_fill, col_auto, col_sec, col_load = st.columns(
        [0.35, 5.5, 1.5, 1.2, 0.45, 0.45, 0.55, 0.75], gap="small"
    )
    with col_spacer:
        st.markdown('<div id="toggle-btn-anchor" style="height:24px; width:34px;"></div>', unsafe_allow_html=True)

    with col_tf:
        # กำกับ translate="no" และ notranslate บล็อก Chrome Translate 100%
        st.markdown('<div class="notranslate" translate="no">', unsafe_allow_html=True)
        primary_tfs = ["5m", "15m", "30m", "1h", "2h", "3h", "4h", "D", "2D", "3D", "W", "M"]
        cur_tf = st.session_state.get("selected_tf", "1h")
        def_idx = primary_tfs.index(cur_tf) if cur_tf in primary_tfs else 3
        tf = st.radio("TF", primary_tfs, index=def_idx, horizontal=True, label_visibility="collapsed", key="toolbar_tf_horizontal")
        if tf != st.session_state.get("selected_tf"):
            st.session_state["selected_tf"] = tf
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_slider: bars = st.slider("Bars", 300, 25000, 2500, 500, label_visibility="collapsed", key="toolbar_bars")
    with col_ind_menu:
        with st.popover("📊 Indicators ▾", use_container_width=True):
            st.toggle("RSI (14)", value=True, key="show_rsi_pane")
            st.toggle("MACD (12, 26, 9)", value=True, key="show_macd_pane")
            st.toggle("EMA Ribbon", value=True, key="show_ema")
    with col_fill: fill_gaps = st.checkbox("Fill", value=False, key="toolbar_fill")
    with col_auto: auto = st.checkbox("Auto", value=False, key="toolbar_auto")
    with col_sec: every = st.number_input("Sec", 2, 60, 2, 1, label_visibility="collapsed", key="toolbar_sec")
    with col_load: reload_btn = st.button("🔄 โหลด", use_container_width=True, key="toolbar_reload_btn")
    return tf, bars, fill_gaps, auto, every, reload_btn
def dashboard():
    # ตรวจจับคำสั่งล้างแคช & รีสตาร์ตจากเบราว์เซอร์
    if "clear_cache" in st.query_params:
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    apply_theme()
    render_floating_sidebar_toggle()
    init_settings_state()
    apply_theme()
    render_floating_sidebar_toggle()
    init_settings_state()

    symbol = st.session_state.get("current_symbol", "BTCUSDT")

   # แถบแท็บด้านบน
    c_tab, c_add, c_empty = st.columns([2.0, 0.4, 12.0])
    with c_tab:
        st.markdown('<div id="custom-tabs-anchor"></div>', unsafe_allow_html=True)
        st.button(f"💎 {symbol} +2.27%", type="primary", use_container_width=True)
    with c_add:
        st.button("+", key="add_t_btn")

    # แถบเครื่องมือ Top Toolbar
    if st.session_state.get("show_top_bar", True):
        tb_tf, tb_bars, tb_fill, auto, every, reload_btn = render_top_toolbar()
        tf = tb_tf
        bars = tb_bars
    else:
        tf = st.session_state.get("selected_tf", "1h")
        bars = 2500

    df = fetch_ohlcv(symbol, tf, bars)
    df, stats = diamond_armor(df, fast=st.session_state["fast_ema"], slow=st.session_state["slow_ema"], trend=st.session_state["trend_ema"])

    last_close = float(df["close"].iloc[-1])
    prev_close = float(df["close"].iloc[-2]) if len(df) >= 2 else last_close
    chg_val = last_close - prev_close
    live_pct = (chg_val / prev_close * 100.0) if prev_close != 0 else 0.0

    tech_data = compute_full_technicals(df)
    seasonality_html = fetch_seasonality_svg(df)
    gauges_html_compact = render_3_gauges_html(tech_data, compact=True)

    tk_data = {
        "price": last_close, "change": chg_val, "pct": live_pct,
        "high": float(df["high"].max()), "low": float(df["low"].min()),
        "vol": float(df["volume"].iloc[-1]), "bid": last_close, "ask": last_close
    }
    charts = build_charts(df, symbol, tf, 520, 120, 120)

    try:
        tech_data = compute_full_technicals(df)
    except Exception:
        tech_data = {}

    try:
        gauges_html_compact = render_3_gauges_html(tech_data)
    except Exception:
        gauges_html_compact = ""

    try:
        seasonality_html = fetch_seasonality_svg(symbol)
    except Exception:
        seasonality_html = ""

    # แบ่ง Layout 3 ส่วน: เมนูซ้าย | ชาร์ตกลาง | บทวิเคราะห์เทคนิค 24h ขวา
   # แบ่ง Layout 3 ส่วน
    col_side, col_chart, col_quote = st.columns([0.88, 3.87, 1.25], gap="small")

    with col_side:
        st.markdown('<div id="custom-left-menu-anchor"></div>', unsafe_allow_html=True)
        render_sidebar()

    with col_chart:
        st.markdown('<div id="custom-center-chart-anchor"></div>', unsafe_allow_html=True)
        render_drawing_chart(charts, height=530, key=f"c_{symbol}_{tf}", show_toolbar=st.session_state.get("show_draw_toolbar", True))

    with col_quote:
        st.markdown('<div id="custom-right-menu-anchor"></div>', unsafe_allow_html=True)
        st.markdown("""
            <div style="display:flex; align-items:center; margin-bottom:6px;">
                <span id="btn-collapse-right" title="คลิกเพื่อพับเก็บเมนูขวา" style="cursor:pointer; display:inline-block; width:11px; height:11px; background:#FF3366; border-radius:50%; margin-right:6px; box-shadow:0 0 6px #FF3366; transition:transform 0.15s;" onmouseover="this.style.transform='scale(1.25)'" onmouseout="this.style.transform='scale(1)'"></span>
                <span id="btn-fullscreen-app" title="คลิกเพื่อขยายเต็มจอ / ออกจากเต็มจอ" style="cursor:pointer; display:inline-block; width:11px; height:11px; background:#00FF66; border-radius:50%; margin-right:8px; box-shadow:0 0 6px #00FF66; transition:transform 0.15s;" onmouseover="this.style.transform='scale(1.25)'" onmouseout="this.style.transform='scale(1)'"></span>
                <b style='font-size:13px; color:#ffffff;'>บทวิเคราะห์เทคนิค 24h <span style='background:#FF7A1A; color:#000; font-size:9px; padding:2px 4px; border-radius:3px; font-weight:bold;'>PRO</span></b>
            </div>
        """, unsafe_allow_html=True)
        render_tv_quote_card(tk_data, tech_data, symbol, "Binance", seasonality_html, gauges_html_compact)


dashboard()