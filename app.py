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
from ui.indicator_modal import show_indicators_modal, INDICATOR_REGISTRY, init_indicator_state
from color_store import ensure_color_state
ensure_color_state()
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
   /* 1. ซ่อนกล่องพื้นที่ว่างของ Iframe ด้านบน */
    div[data-testid="stElementContainer"]:has(iframe[height="0"]) {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 0px !important;
    }

    /* 2. สั่งย้ายตัว ☰ (#toggle-btn-anchor) ลงมาอยู่หน้าเลข 5m โดยตรง */
    #toggle-btn-anchor {
        position: fixed !important;
        top: 52px !important;          /* <--- ปรับระดับ ขึ้น-ลง ให้ตรงแถวเลข 5m (ปรับได้ระหว่าง 48px - 56px) */
        left: 14px !important;         /* <--- ปรับ ซ้าย-ขวา ให้อยู่หน้า 5m */
        z-index: 9999999 !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 4px !important;
        width: 32px !important;
        height: 26px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
    }

    [data-testid="stSidebar"] { top: 0 !important; }
    section[data-testid="stMain"] { padding-top: 0 !important; top: 0 !important; }
    [data-testid="stAppViewContainer"] { padding-top: 0 !important; top: 0 !important; }

    /* 3. ดึงเนื้อหาทั้งหมดชิดขอบบนสุด (แก้จุดขีดส้ม) */
    .stApp [data-testid="stMain"],
    .stApp [data-testid="stMainBlockContainer"],
    section[data-testid="stMain"] .block-container,
    .block-container {
        padding-top: 0px !important;
        margin-top: -38px !important;  /* <--- ปรับช่องว่างขอบบน (ยิ่งติดลบมาก ยิ่งชิดขอบบน เช่น -40px) */
        padding-bottom: 0rem !important;
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
        max-width: 100% !important;
    }
    /* 3. สไตล์ปุ่มแท็บด้านบนสุด: ส้มเรืองแสงโปร่งแสง 50% */
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[kind="primary"],
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[data-testid="baseButton-primary"] {
        background: rgba(255, 102, 0, 0.25) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        border: 1px solid rgba(255, 125, 30, 0.95) !important;
        border-radius: 4px !important;
        height: 28px !important;
        min-height: 28px !important;
        box-shadow: 0 0 14px rgba(255, 110, 20, 0.50), inset 0 0 6px rgba(255, 110, 20, 0.25) !important;
        backdrop-filter: blur(8px) !important;
    }

    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[data-testid="baseButton-secondary"] {
        background: rgba(24, 27, 34, 0.6) !important;
        color: #8f96a3 !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 4px !important;
        height: 28px !important;
        min-height: 28px !important;
        font-size: 13px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[kind="secondary"]:hover,
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[data-testid="baseButton-secondary"]:hover {
        background: rgba(38, 43, 54, 0.9) !important;
        color: #ffffff !important;
        border-color: #ff7d1e !important;
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
    /* ปลดล็อกคอนเทนเนอร์และ Iframe ของกราฟให้ยืดหดตามความกว้างคอลัมน์อัตโนมัติ */
    div[data-testid="column"]:has(#custom-center-chart-anchor),
    div[data-testid="column"]:has(#custom-center-chart-anchor) iframe,
    div[data-testid="column"]:has(#custom-center-chart-anchor) div[data-testid="stCustomComponentV1"] {
        width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 auto !important;
    }
    /* 6. ปลดล็อกระบบปรับขนาดพาเนลซ้าย-ขวาด้วย CSS Variables */
    :root {
        --left-panel-width: 240px;
        --right-panel-width: 320px;
    }
    div[data-testid="stHorizontalBlock"]:has(#custom-center-chart-anchor) {
        display: flex !important;
        flex-direction: row !important;
        width: 100% !important;
        align-items: stretch !important;
    }
    div[data-testid="column"]:has(#custom-left-menu-anchor) {
        flex: 0 0 var(--left-panel-width) !important;
        width: var(--left-panel-width) !important;
        min-width: 160px !important;
        max-width: 480px !important;
    }
    div[data-testid="column"]:has(#custom-center-chart-anchor) {
        flex: 1 1 0% !important;
        min-width: 300px !important;
        width: 100% !important;
    }
    div[data-testid="column"]:has(#custom-right-menu-anchor) {
        flex: 0 0 var(--right-panel-width) !important;
        width: var(--right-panel-width) !important;
        min-width: 200px !important;
        max-width: 520px !important;
    }
</style>
""", unsafe_allow_html=True)

def inject_workspace_resizers():
    components.html("""
    <style>
        @media (max-width: 768px) {
            #resizer-left-bar,
            #resizer-right-bar,
            #drag-shield-overlay,
            #custom-color-context-menu {
                display: none !important;
            }
        }
        #custom-color-context-menu {
            position: fixed;
            z-index: 1000000;
            background: #181b22;
            border: 1px solid #2a2e39;
            box-shadow: 0 4px 16px rgba(0,0,0,0.7), 0 0 10px rgba(255,122,26,0.3);
            border-radius: 6px;
            padding: 6px;
            min-width: 160px;
            display: none;
            flex-direction: column;
            gap: 3px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 12px;
            user-select: none;
        }
        .ctx-header {
            color: #8b949e;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-bottom: 1px solid #2a2e39;
            margin-bottom: 3px;
        }
        .ctx-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 8px;
            border-radius: 4px;
            color: #d1d4dc;
            cursor: pointer;
            transition: background 0.15s;
        }
        .ctx-item:hover {
            background: rgba(255, 122, 26, 0.2);
            color: #ffffff;
        }
        .ctx-divider {
            height: 1px;
            background: #2a2e39;
            margin: 3px 0;
        }
        .ctx-danger {
            color: #f23645;
        }
        .ctx-danger:hover {
            background: rgba(242, 54, 69, 0.2);
            color: #ff4d5a;
        }
    </style>
    <script>
    (function() {
        try {
            const doc = window.parent.document;

            function notifyResize() {
                window.parent.dispatchEvent(new Event('resize'));
                doc.querySelectorAll('iframe').forEach(f => {
                    try { f.contentWindow.dispatchEvent(new Event('resize')); } catch(e) {}
                });
            }

            function createShield() {
                let shield = doc.getElementById('drag-shield-overlay');
                if (!shield) {
                    shield = doc.createElement('div');
                    shield.id = 'drag-shield-overlay';
                    shield.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;cursor:col-resize;background:transparent;display:none;touch-action:none;';
                    doc.body.appendChild(shield);
                }
                return shield;
            }

            function getCol(anchorId) {
                const el = doc.getElementById(anchorId);
                return el ? el.closest('[data-testid="stColumn"], [data-testid="column"], .stColumn') : null;
            }

            function attachResizers() {
                if (window.parent.innerWidth < 768) return;

                const sideCol = getCol('custom-left-menu-anchor');
                const chartCol = getCol('custom-center-chart-anchor');
                const rightCol = getCol('custom-right-menu-anchor');

                if (chartCol) {
                    chartCol.style.flex = '1 1 0%';
                    chartCol.style.minWidth = '260px';
                }

                const shield = createShield();

                // 1. ซ้าย
                if (sideCol && !doc.getElementById('resizer-left-bar')) {
                    const resizerL = doc.createElement('div');
                    resizerL.id = 'resizer-left-bar';
                    resizerL.title = 'คลิกลากเพื่อปรับขนาดเมนูซ้าย';
                    resizerL.innerHTML = '<div style="width:3px; height:50px; background:#ff7d1e; border-radius:2px; margin:auto; box-shadow:0 0 6px rgba(255,125,30,0.9);"></div>';
                    resizerL.style.cssText = 'width: 10px; cursor: col-resize; display: flex; align-items: center; justify-content: center; z-index: 99999; flex-shrink: 0; user-select: none; margin: 0 -5px; touch-action: none;';
                    sideCol.after(resizerL);

                    const startDragL = (clientX) => {
                        shield.style.display = 'block';
                        const startX = clientX;
                        const startW = sideCol.getBoundingClientRect().width;
                        const onMove = (x) => {
                            const nw = Math.max(160, Math.min(480, startW + (x - startX)));
                            sideCol.style.width = nw + 'px';
                            sideCol.style.flex = '0 0 ' + nw + 'px';
                            notifyResize();
                        };
                        const onEnd = () => {
                            shield.style.display = 'none';
                            doc.removeEventListener('mousemove', onMouseMove);
                            doc.removeEventListener('mouseup', onMouseUp);
                            doc.removeEventListener('touchmove', onTouchMove);
                            doc.removeEventListener('touchend', onTouchEnd);
                            notifyResize();
                        };
                        const onMouseMove = (ev) => onMove(ev.clientX);
                        const onMouseUp = () => onEnd();
                        const onTouchMove = (ev) => { if (ev.touches[0]) onMove(ev.touches[0].clientX); };
                        const onTouchEnd = () => onEnd();

                        doc.addEventListener('mousemove', onMouseMove);
                        doc.addEventListener('mouseup', onMouseUp);
                        doc.addEventListener('touchmove', onTouchMove, { passive: false });
                        doc.addEventListener('touchend', onTouchEnd);
                    };
                    resizerL.onmousedown = (e) => { e.preventDefault(); startDragL(e.clientX); };
                    resizerL.ontouchstart = (e) => { if (e.touches[0]) startDragL(e.touches[0].clientX); };
                }

                // 2. ขวา
                if (rightCol) {
                    rightCol.style.position = 'relative';
                    let resizerR = doc.getElementById('resizer-right-bar');
                    if (!resizerR || resizerR.parentElement !== rightCol) {
                        if (resizerR) resizerR.remove();
                        resizerR = doc.createElement('div');
                        resizerR.id = 'resizer-right-bar';
                        resizerR.title = 'คลิกลากเพื่อปรับขนาดเมนูขวา';
                        resizerR.innerHTML = '<div style="width:3px; height:50px; background:#ff7d1e; border-radius:2px; margin:auto; box-shadow:0 0 10px rgba(255,125,30,0.9);"></div>';
                        resizerR.style.cssText = 'position: absolute; left: -6px; top: 0; bottom: 0; width: 14px; cursor: col-resize; display: flex; align-items: center; justify-content: center; z-index: 999999; user-select: none; transition: background 0.15s; touch-action: none;';
                        resizerR.onmouseenter = () => { resizerR.style.background = 'rgba(255,125,30,0.2)'; };
                        resizerR.onmouseleave = () => { resizerR.style.background = 'transparent'; };
                        rightCol.prepend(resizerR);

                        const startDragR = (clientX) => {
                            shield.style.display = 'block';
                            const startX = clientX;
                            const startW = rightCol.getBoundingClientRect().width;
                            const onMove = (x) => {
                                const nw = Math.max(200, Math.min(540, startW + (startX - x)));
                                rightCol.style.setProperty('width', nw + 'px', 'important');
                                rightCol.style.setProperty('min-width', nw + 'px', 'important');
                                rightCol.style.setProperty('max-width', nw + 'px', 'important');
                                rightCol.style.setProperty('flex', '0 0 ' + nw + 'px', 'important');
                                notifyResize();
                            };
                            const onEnd = () => {
                                shield.style.display = 'none';
                                doc.removeEventListener('mousemove', onMouseMove);
                                doc.removeEventListener('mouseup', onMouseUp);
                                doc.removeEventListener('touchmove', onTouchMove);
                                doc.removeEventListener('touchend', onTouchEnd);
                                notifyResize();
                            };
                            const onMouseMove = (ev) => onMove(ev.clientX);
                            const onMouseUp = () => onEnd();
                            const onTouchMove = (ev) => { if (ev.touches[0]) onMove(ev.touches[0].clientX); };
                            const onTouchEnd = () => onEnd();

                            doc.addEventListener('mousemove', onMouseMove);
                            doc.addEventListener('mouseup', onMouseUp);
                            doc.addEventListener('touchmove', onTouchMove, { passive: false });
                            doc.addEventListener('touchend', onTouchEnd);
                        };
                        resizerR.onmousedown = (e) => { e.preventDefault(); startDragR(e.clientX); };
                        resizerR.ontouchstart = (e) => { if (e.touches[0]) startDragR(e.touches[0].clientX); };
                    }
                }

                // 3. พับขวา
                const btnRight = doc.getElementById('btn-collapse-right');
                if (btnRight && !btnRight.dataset.bound) {
                    btnRight.dataset.bound = 'true';
                    btnRight.onclick = function() {
                        if (rightCol) {
                            const isHidden = (rightCol.style.display === 'none');
                            rightCol.style.display = isHidden ? 'block' : 'none';
                            const barR = doc.getElementById('resizer-right-bar');
                            if (barR) barR.style.display = isHidden ? 'none' : 'flex';
                            notifyResize();
                        }
                    };
                }
            }

            const interval = setInterval(attachResizers, 200);
            setTimeout(() => clearInterval(interval), 10000);

            if (!window.parent._resizerObserver) {
                const observer = new MutationObserver(attachResizers);
                observer.observe(doc.body, { childList: true, subtree: true });
                window.parent._resizerObserver = observer;
            }
            attachResizers();
        } catch (err) {
            console.error("Resizer script error:", err);
        }
    })();
    </script>
    """, height=0, width=0)
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

    tabs = st.session_state["chart_tabs"]
    active_id = st.session_state["active_tab_id"]
    active_tab = next((t for t in tabs if t["id"] == active_id), tabs[0])

    # ซิงค์ค่าเหรียญ: ตรวจสอบว่ามีการกดเลือกเหรียญใหม่จาก Sidebar หรือ Modal หรือไม่
    incoming_sym = st.session_state.get("selected_symbol") or st.session_state.get("current_symbol")
    if incoming_sym and incoming_sym != active_tab.get("symbol"):
        active_tab["symbol"] = incoming_sym  # อัปเดตแท็บด้านบนให้เป็นเหรียญใหม่

    symbol = active_tab["symbol"]
    st.session_state["current_symbol"] = symbol
    st.session_state["selected_symbol"] = symbol

    tf = active_tab.get("tf", st.session_state.get("selected_tf", "1h"))
    st.session_state["selected_tf"] = tf

    bars = TF_TARGET_BARS.get(tf, 25000)

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
    # แถวที่ 1 (บนสุด): แถบแท็บสินทรัพย์ (Dynamic Column Iterator - ปลอดภัย 100%)
    has_close = len(tabs) > 1
    col_widths = [0.01]  # ลดความกว้างช่องแรกเพื่อให้แท็บ BTC ชิดซ้ายสวยงาม
    for _ in tabs:
        col_widths.append(1.0)
        if has_close:
            col_widths.append(0.18)
    col_widths.append(0.22)
    col_widths.append(8.0)

    t_cols = st.columns(col_widths, gap="small")
    col_iter = iter(t_cols)

    # 1. ตัวระบุ Marker สำหรับ CSS แท็บด้านบน
    with next(col_iter):
        st.markdown('<div id="top-tabs-marker"></div>', unsafe_allow_html=True)
    # 2. วาดแท็บและปุ่มปิด
    for t in tabs:
        is_active = (t["id"] == active_id)
        t_meta = resolve_market_info(t["symbol"])
        t_label = f"💎 {t_meta['display_name']} {pct_str if is_active else ''}".strip()
        btn_type = "primary" if is_active else "secondary"

        with next(col_iter):
            if st.button(t_label, key=f"t_btn_{t['id']}", type=btn_type, use_container_width=True):
                st.session_state["active_tab_id"] = t["id"]
                st.session_state["current_symbol"] = t["symbol"]
                st.session_state["selected_tf"] = t["tf"]
                st.rerun()

        if has_close:
            with next(col_iter):
                if st.button("✕", key=f"t_close_{t['id']}", help="ปิดแท็บนี้", use_container_width=True):
                    st.session_state["chart_tabs"] = [x for x in tabs if x["id"] != t["id"]]
                    if t["id"] == active_id:
                        st.session_state["active_tab_id"] = st.session_state["chart_tabs"][0]["id"]
                        st.session_state["current_symbol"] = st.session_state["chart_tabs"][0]["symbol"]
                    st.rerun()

    # 3. ปุ่มเพิ่มแท็บใหม่ (＋)
    with next(col_iter):
        if st.button("＋", key="btn_add_tab_global", help="เพิ่มแท็บกราฟใหม่", use_container_width=True):
            new_tab_id = f"tab_{int(time.time() * 1000)}"
            new_sym = "ETHUSDT" if symbol == "BTCUSDT" else "BTCUSDT"
            st.session_state["chart_tabs"].append({"id": new_tab_id, "symbol": new_sym, "tf": tf})
            st.session_state["active_tab_id"] = new_tab_id
            st.session_state["current_symbol"] = new_sym
            st.rerun()

   # แถวที่ 2: Timeframe และ Indicators (ใส่ปุ่ม ☰ ไว้หน้าแถว 5m)
    c_space, c_tf, c_ind, c_right_blank = st.columns([0.35, 5.2, 2.5, 2.0], gap="small")

    with c_space:
        st.markdown('<div id="toggle-btn-anchor" style="height:28px; width:34px; display:flex; align-items:center; justify-content:center; font-size:16px; color:#9aa0a6; cursor:pointer; background:rgba(255,255,255,0.06); border:1px solid #2a2e39; border-radius:4px; margin-top:2px;">☰</div>', unsafe_allow_html=True)

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

   # จุดวงเขียว 2: ปุ่ม Indicators
    with c_ind:
        if st.button("📊 Indicators", key="btn_open_ind_modal", type="secondary", use_container_width=True):
            show_indicators_modal()

    # =========================================================================
    # แถวที่ 3: พื้นที่ทำงาน 3 คอลัมน์หลัก (มี Draggable Splitters คั่นกลาง)
    # =========================================================================
    tech_data = compute_full_technicals(df)
    raw_charts = build_charts(df, symbol, tf, 520, 120, 120)
    filtered_charts = raw_charts

    col_side, col_chart, col_quote = st.columns([0.88, 3.87, 1.25], gap="small")

    with col_side:
        st.markdown('<div id="custom-left-menu-anchor"></div>', unsafe_allow_html=True)
        render_sidebar()

    with col_chart:
        st.markdown('<div id="custom-center-chart-anchor"></div>', unsafe_allow_html=True)
        render_drawing_chart(filtered_charts, height=530, key=f"c_{symbol}_{tf}", show_toolbar=st.session_state.get("show_draw_toolbar", True))

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