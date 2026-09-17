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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from chart_builders import build_charts
from config import *
from data.fetchers import (
    TF_TARGET_BARS,
    fetch_ohlcv as fetch_market_ohlcv,
    fetch_ticker_24h,
    get_usd_thb_rate,
    resolve_market_info,
)
from data.rice_ohlcv import generate_rice_ohlcv
from data.symbols import (
    get_full_binance_symbols,
    get_full_bitkub_symbols,
    get_full_commodities,
    get_full_forex,
    get_full_sp500_symbols,
)
from drawing_chart import render_drawing_chart
from streamlit_lightweight_charts_ntf import renderLightweightCharts
from technicals import compute_full_technicals, diamond_armor, fetch_market_analytics
from ui.chart_settings_modal import init_settings_state, show_chart_settings_dialog
from ui.floating_toggle import render_floating_sidebar_toggle
from ui.rice_tab import render_rice_tab, show_rice_dialog_modal
from ui.right_panel import render_right_panel
from ui.sidebar_refactored import render_sidebar
from ui.theme import apply_theme
from ui_components import (
    build_asset_icon_html,
    fetch_seasonality_svg,
    render_3_gauges_html,
    render_fibonacci_modal_content,
    render_market_modal_content,
    render_panel_controls,
    render_tv_quote_card,
)
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
    /* 1. ยุบ Header ดั้งเดิมของ Streamlit ทั้งหมด */
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

    /* 2. ดึงเนื้อหาขึ้นชิดบนสุด */
    .block-container,
    .stMainBlockContainer,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"],
    section[data-testid="stMain"] .block-container {
        padding-top: 2px !important;
        padding-bottom: 0rem !important;
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
        max-width: 100% !important;
    }

    /* 3. แถบแท็บด้านบนสุด (Top Tabs Bar) */
    .top-tab-active button {
        background: linear-gradient(135deg, #ff5722 0%, #e64a19 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 4px 4px 0 0 !important;
        height: 32px !important;
        box-shadow: 0 -2px 8px rgba(255, 87, 34, 0.4) !important;
    }

    .top-tab-inactive button {
        background: #181b22 !important;
        color: #8f96a3 !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 4px 4px 0 0 !important;
        height: 32px !important;
    }
    .top-tab-inactive button:hover {
        background: #222631 !important;
        color: #ffffff !important;
    }

    /* 4. สไตล์ปุ่ม Timeframe Pills */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 2px !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label {
        padding: 2px 7px !important;
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
        background-color: #ff5722 !important;
    }

    /* 5. ปุ่ม Indicators Popover */
    div[data-testid="stPopover"] {
        position: relative !important;
        z-index: 10010 !important;
    }
    div[data-testid="stPopover"] > button {
        background-color: #1e222d !important;
        border: 1px solid #363c4e !important;
        color: #d1d4dc !important;
        height: 30px !important;
        border-radius: 4px !important;
    }
    div[data-testid="stPopover"] > button:hover {
        background-color: #2a2e39 !important;
        border-color: #2962ff !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ระบบฉีด JavaScript เพื่อสร้างแท่งจับลากปรับขนาดซ้าย-ขวา (Draggable Resizers)
def inject_workspace_resizers():
    components.html("""
    <script>
    (function attachSplitters() {
        const doc = window.parent.document;
        function run() {
            const sideAnchor = doc.getElementById('custom-left-menu-anchor');
            const chartAnchor = doc.getElementById('custom-center-chart-anchor');
            const rightAnchor = doc.getElementById('custom-right-menu-anchor');

            if (!sideAnchor || !chartAnchor || !rightAnchor) return;

            const sideCol = sideAnchor.closest('[data-testid="column"]');
            const chartCol = chartAnchor.closest('[data-testid="column"]');
            const rightCol = rightAnchor.closest('[data-testid="column"]');

            if (!sideCol || !chartCol || !rightCol) return;
            if (sideCol.nextElementSibling && sideCol.nextElementSibling.id === 'resizer-left-bar') return;

            // ลบ Resizer เก่าถ้ามีตกค้าง
            const oldL = doc.getElementById('resizer-left-bar');
            if (oldL) oldL.remove();
            const oldR = doc.getElementById('resizer-right-bar');
            if (oldR) oldR.remove();

            // 1. สร้างแถบเลื่อนฝั่งซ้าย (ระหว่างเมนูซ้ายกับกราฟ)
            const resizerL = doc.createElement('div');
            resizerL.id = 'resizer-left-bar';
            resizerL.title = 'คลิกค้างแล้วลากเพื่อปรับขนาดเมนูซ้าย';
            resizerL.innerHTML = '<div style="width:2px; height:40px; background:#4a5061; border-radius:1px; margin:auto;"></div>';
            resizerL.style.cssText = `
                width: 8px; cursor: col-resize; display: flex; align-items: center; justify-content: center;
                background: transparent; z-index: 9999; flex-shrink: 0; user-select: none; transition: background 0.15s;
            `;
            resizerL.onmouseenter = () => resizerL.style.background = 'rgba(255, 87, 34, 0.4)';
            resizerL.onmouseleave = () => resizerL.style.background = 'transparent';

            // 2. สร้างแถบเลื่อนฝั่งขวา (ระหว่างกราฟกับเมนูขวา)
            const resizerR = doc.createElement('div');
            resizerR.id = 'resizer-right-bar';
            resizerR.title = 'คลิกค้างแล้วลากเพื่อปรับขนาดเมนูขวา';
            resizerR.innerHTML = '<div style="width:2px; height:40px; background:#4a5061; border-radius:1px; margin:auto;"></div>';
            resizerR.style.cssText = `
                width: 8px; cursor: col-resize; display: flex; align-items: center; justify-content: center;
                background: transparent; z-index: 9999; flex-shrink: 0; user-select: none; transition: background 0.15s;
            `;
            resizerR.onmouseenter = () => resizerR.style.background = 'rgba(255, 87, 34, 0.4)';
            resizerR.onmouseleave = () => resizerR.style.background = 'transparent';

            sideCol.after(resizerL);
            chartCol.after(resizerR);

            // Drag Handler สำหรับฝั่งซ้าย
            resizerL.onmousedown = (e) => {
                e.preventDefault();
                const startX = e.clientX;
                const startW = sideCol.getBoundingClientRect().width;
                const onMouseMove = (ev) => {
                    const nw = Math.max(160, Math.min(480, startW + (ev.clientX - startX)));
                    sideCol.style.width = nw + 'px';
                    sideCol.style.flex = '0 0 ' + nw + 'px';
                };
                const onMouseUp = () => {
                    doc.removeEventListener('mousemove', onMouseMove);
                    doc.removeEventListener('mouseup', onMouseUp);
                };
                doc.addEventListener('mousemove', onMouseMove);
                doc.addEventListener('mouseup', onMouseUp);
            };

            // Drag Handler สำหรับฝั่งขวา
            resizerR.onmousedown = (e) => {
                e.preventDefault();
                const startX = e.clientX;
                const startW = rightCol.getBoundingClientRect().width;
                const onMouseMove = (ev) => {
                    const nw = Math.max(200, Math.min(520, startW - (ev.clientX - startX)));
                    rightCol.style.width = nw + 'px';
                    rightCol.style.flex = '0 0 ' + nw + 'px';
                };
                const onMouseUp = () => {
                    doc.removeEventListener('mousemove', onMouseMove);
                    doc.removeEventListener('mouseup', onMouseUp);
                };
                doc.addEventListener('mousemove', onMouseMove);
                doc.addEventListener('mouseup', onMouseUp);
            };

            // เชื่อมต่อปุ่มพับขวาและขยายเต็มจอ
            const btnRight = doc.getElementById('btn-collapse-right');
            if (btnRight) {
                btnRight.onclick = function() {
                    const isHidden = (rightCol.style.display === 'none');
                    rightCol.style.display = isHidden ? 'block' : 'none';
                    resizerR.style.display = isHidden ? 'flex' : 'none';
                };
            }
            const btnFull = doc.getElementById('btn-fullscreen-app');
            if (btnFull) {
                btnFull.onclick = function() {
                    if (!doc.fullscreenElement) doc.documentElement.requestFullscreen();
                    else doc.exitFullscreen();
                };
            }
        }
        setTimeout(run, 300);
        setTimeout(run, 1000);
    })();
    </script>
    """, height=0, width=0)

# กำหนดสถานะ Multi-Tabs ใน Session
if "chart_tabs" not in st.session_state:
    st.session_state["chart_tabs"] = [
        {"id": "tab_1", "symbol": "BTCUSDT", "tf": "1h"}
    ]
if "active_tab_id" not in st.session_state:
    st.session_state["active_tab_id"] = "tab_1"

if "current_symbol" not in st.session_state: st.session_state["current_symbol"] = "BTCUSDT"
if "selected_tf" not in st.session_state: st.session_state["selected_tf"] = "1h"
if "fast_ema" not in st.session_state: st.session_state["fast_ema"] = 7
if "slow_ema" not in st.session_state: st.session_state["slow_ema"] = 13
if "trend_ema" not in st.session_state: st.session_state["trend_ema"] = 45

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update(BROWSER_HEADERS)
retry_strategy = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
HTTP_SESSION.mount("https://", HTTPAdapter(max_retries=retry_strategy))

def fetch_ohlcv(symbol: str, tf: str, bars: int) -> pd.DataFrame:
    if symbol.startswith("RICE:") or symbol.startswith("FOB:") or "ZR=F" in symbol:
        return generate_rice_ohlcv(symbol, bars=bars)

    df = fetch_market_ohlcv(symbol=symbol, tf=tf, limit=bars)

    if not df.empty and "time" in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df["time"]):
            df["time"] = (df["time"].astype("int64") // 10**9)
        return df.dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)

    return df

def dashboard():
    if "clear_cache" in st.query_params:
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    apply_theme()
    render_floating_sidebar_toggle()
    init_settings_state()
    inject_workspace_resizers()

    # ซิงค์ข้อมูลแท็บที่เปิดอยู่
    tabs = st.session_state["chart_tabs"]
    active_id = st.session_state["active_tab_id"]
    active_tab = next((t for t in tabs if t["id"] == active_id), tabs[0])

    symbol = active_tab["symbol"]
    tf = active_tab.get("tf", st.session_state.get("selected_tf", "1h"))
    st.session_state["current_symbol"] = symbol
    st.session_state["selected_tf"] = tf

    # ปรับจำนวนแท่งตามโควตา Ultra-Deep
    bars = TF_TARGET_BARS.get(tf, 25000)

    # คำนวณข้อมูลราคาและอินดิเคเตอร์
    meta = resolve_market_info(symbol)
    fx_rate = get_usd_thb_rate()
    is_thb_mode = st.session_state.get("currency_mode_thb", False)

    df = fetch_ohlcv(symbol, tf, bars)
    if not df.empty:
        df, stats = diamond_armor(df, fast=st.session_state["fast_ema"], slow=st.session_state["slow_ema"], trend=st.session_state["trend_ema"])
        mult = (fx_rate if (is_thb_mode and not meta["is_thb_native"]) else 1.0)
        last_close = float(df["close"].iloc[-1]) * mult
        prev_close = float(df["close"].iloc[-2]) * mult if len(df) >= 2 else last_close
        chg_val = last_close - prev_close
        live_pct = (chg_val / prev_close * 100.0) if prev_close != 0 else 0.0
    else:
        last_close = 0.0
        live_pct = 0.0

    pct_sign = "+" if live_pct >= 0 else ""
    pct_str = f"{pct_sign}{live_pct:.2f}%"

    # =========================================================================
    # แถวที่ 1 (บนสุด): แถบแท็บสินทรัพย์ (Multi-Tab Bar) แยกอิสระตามกรอบสีเขียว
    # =========================================================================
    tab_cols_widths = [0.35]
    for _ in tabs:
        tab_cols_widths.extend([1.6, 0.25])  # ช่องชื่อแท็บ + ช่องปุ่มปิด (x)
    tab_cols_widths.extend([0.35, 8.0])      # ช่องปุ่มบวก (+) + พื้นที่ว่าง

    t_cols = st.columns(tab_cols_widths, gap="small")
    with t_cols[0]:
        st.markdown('<div id="toggle-btn-anchor" style="height:30px; display:flex; align-items:center; font-size:16px; color:#9aa0a6;">☰</div>', unsafe_allow_html=True)

    col_idx = 1
    for t in tabs:
        is_active = (t["id"] == active_id)
        t_meta = resolve_market_info(t["symbol"])
        t_label = f"💎 {t_meta['display_name']} {pct_str if is_active else ''}".strip()
        css_class = "top-tab-active" if is_active else "top-tab-inactive"

        with t_cols[col_idx]:
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(t_label, key=f"t_btn_{t['id']}", use_container_width=True):
                st.session_state["active_tab_id"] = t["id"]
                st.session_state["current_symbol"] = t["symbol"]
                st.session_state["selected_tf"] = t["tf"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with t_cols[col_idx + 1]:
            if len(tabs) > 1:
                if st.button("✕", key=f"t_close_{t['id']}", help="ปิดแท็บนี้"):
                    st.session_state["chart_tabs"] = [x for x in tabs if x["id"] != t["id"]]
                    if t["id"] == active_id:
                        st.session_state["active_tab_id"] = st.session_state["chart_tabs"][0]["id"]
                        st.session_state["current_symbol"] = st.session_state["chart_tabs"][0]["symbol"]
                    st.rerun()
        col_idx += 2

    # ปุ่มเครื่องหมายบวก (+) เพื่อเพิ่มแท็บใหม่
    with t_cols[col_idx]:
        if st.button("＋", key="btn_add_tab_global", help="เพิ่มแท็บกราฟใหม่"):
            new_tab_id = f"tab_{int(time.time() * 1000)}"
            new_sym = "ETHUSDT" if symbol == "BTCUSDT" else "BTCUSDT"
            st.session_state["chart_tabs"].append({"id": new_tab_id, "symbol": new_sym, "tf": tf})
            st.session_state["active_tab_id"] = new_tab_id
            st.session_state["current_symbol"] = new_sym
            st.rerun()

    # =========================================================================
    # แถวที่ 2: แถบเลือก Timeframe และ Indicators Popover
    # =========================================================================
    c_space, c_tf, c_ind = st.columns([0.35, 7.8, 1.6], gap="small")
    with c_tf:
        st.markdown('<div class="notranslate" translate="no">', unsafe_allow_html=True)
        primary_tfs = ["5m", "15m", "30m", "1h", "2h", "3h", "4h", "D", "2D", "3D", "W", "M"]
        cur_tf = tf
        def_idx = primary_tfs.index(cur_tf) if cur_tf in primary_tfs else 3
        new_tf = st.radio("TF", primary_tfs, index=def_idx, horizontal=True, label_visibility="collapsed", key="toolbar_tf_horizontal")
        if new_tf != cur_tf:
            active_tab["tf"] = new_tf
            st.session_state["selected_tf"] = new_tf
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_ind:
        with st.popover("📊 Indicators ▾", use_container_width=True):
            st.markdown("##### ⚙️ ตัวชี้วัดเทคนิค")
            st.toggle("RSI (14)", value=True, key="show_rsi_pane")
            st.toggle("MACD (12, 26, 9)", value=True, key="show_macd_pane")
            st.toggle("EMA Ribbon", value=True, key="show_ema")

    # =========================================================================
    # แถวที่ 3: พื้นที่ทำงาน 3 คอลัมน์หลัก (มี Draggable Splitters คั่นกลาง)
    # =========================================================================
    tech_data = compute_full_technicals(df)
    charts = build_charts(df, symbol, tf, 520, 120, 120)

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
        render_right_panel(df=df, meta=meta, is_thb_mode=is_thb_mode, fx_rate=fx_rate)

dashboard()