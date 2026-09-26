# app.py — Universal Trading Terminal (Hybrid Ultra Edition)
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
import streamlit.components.v1 as components

from color_store import ensure_color_state
ensure_color_state()

from config import BROWSER_HEADERS
from chart_builders import build_charts
from data.fetchers import (
    TF_TARGET_BARS,
    fetch_ohlcv as fetch_market_ohlcv,
    fetch_ticker_24h,
    get_usd_thb_rate,
    resolve_market_info,
)
from data.rice_ohlcv import generate_rice_ohlcv
from drawing_chart import render_drawing_chart
from technicals import diamond_armor
from ui.chart_settings_modal import init_settings_state
from ui.indicator_modal import show_indicators_modal
from ui.mobile_view import render_mobile_view
from ui.right_panel import render_right_panel
from ui.sidebar_refactored import render_sidebar
from ui.theme import apply_theme

st.set_page_config(
    page_title="Diamond Armor Universal",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    /* ==========================================================================
       DESIGN SYSTEM: DEEP DARK + NEON ACCENTS + UNIFIED TYPOGRAPHY
       ========================================================================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* 1. ยุบ Header ดั้งเดิมของ Streamlit ทั้งหมด และเซ็ตพื้นหลัง Deep Dark */
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

    .stApp, body, [data-testid="stAppViewContainer"] {
        background-color: #07080a !important;
        color: #d1d5db !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ซ่อนกล่องพื้นที่ว่างของ Iframe ด้านบน */
    div[data-testid="stElementContainer"]:has(iframe[height="0"]) {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
        height: 0px !important;
    }

    /* 2. สั่งย้ายตัว ☰ (#toggle-btn-anchor) ลงมาอยู่หน้าแถวไทม์เฟรม */
    #toggle-btn-anchor {
        position: fixed !important;
        top: 66px !important;
        left: 14px !important;
        z-index: 9999999 !important;
        background: #0e1118 !important;
        border: 1px solid #1e2433 !important;
        border-radius: 4px !important;
        width: 32px !important;
        height: 26px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        color: #8b949e !important;
        transition: all 0.15s ease-in-out !important;
    }
    #toggle-btn-anchor:hover {
        color: #00e676 !important;
        border-color: #00e676 !important;
        box-shadow: 0 0 8px rgba(0, 230, 118, 0.4) !important;
    }

    [data-testid="stSidebar"] { top: 0 !important; background-color: #090b10 !important; }
    section[data-testid="stMain"] { padding-top: 0 !important; top: 0 !important; }
    [data-testid="stAppViewContainer"] { padding-top: 0 !important; top: 0 !important; }

    /* 3. ดึงเนื้อหาขึ้นในระยะที่พอดีสายตา ไม่ชนขอบจอด้านบน */
    .stApp [data-testid="stMain"],
    .stApp [data-testid="stMainBlockContainer"],
    section[data-testid="stMain"] .block-container,
    .block-container {
        padding-top: 0px !important;
        margin-top: -12px !important;
        padding-bottom: 0rem !important;
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
        max-width: 100% !important;
    }

    /* 4. สไตล์ปุ่มแท็บด้านบนสุด: เขียวสะท้อนแสง Neon Glow */
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[kind="primary"],
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #00E67752, #00FF8857) !important;
        color: #F0E9E9 !important;
        font-weight: 700 !important;
        font-size: 12.5px !important;
        border: 1px solid #00ff88 !important;
        border-radius: 4px !important;
        height: 28px !important;
        min-height: 28px !important;
        box-shadow: 0 0 12px rgba(0, 230, 118, 0.6) !important;
        backdrop-filter: blur(8px) !important;
    }

    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[data-testid="baseButton-secondary"] {
        background: #0e1118 !important;
        color: #9E8B8B !important;
        border: 1px solid #1e2433 !important;
        border-radius: 4px !important;
        height: 28px !important;
        min-height: 28px !important;
        font-size: 12.5px !important;
        transition: all 0.15s ease-in-out !important;
    }
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[kind="secondary"]:hover,
    div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) button[data-testid="baseButton-secondary"]:hover {
        background: #17130e !important;
        color: #00E6775B !important;
        border-color: #00E67755 !important;
        box-shadow: 0 0 8px rgba(0, 230, 118, 0.3) !important;
    }

    /* 5. สไตล์ปุ่ม Timeframe Pills */
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
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #9E8B8B !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        transition: all 0.15s ease !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label:hover {
        color: #00E67784 !important;
        background-color: #111e16 !important;
        border-color: rgba(0, 230, 118, 0.3) !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) {
        color: #000000 !important;
        background: linear-gradient(135deg, #00E67753, #00FF8852) !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(0 230 119 / 0.27) !important;
    }

    /* 6. ปุ่ม Indicators */
    button#btn_open_ind_modal, button[key="btn_open_ind_modal"],
    div[data-testid="stPopover"] > button {
        background-color: #0e1118 !important;
        border: 1px solid #1e2433 !important;
        color: #d1d5db !important;
        height: 28px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        border-radius: 4px !important;
        transition: all 0.15s ease-in-out !important;
    }
    button#btn_open_ind_modal:hover,
    div[data-testid="stPopover"] > button:hover {
        background-color: #17130e !important;
        border-color: #ff8c00 !important;
        color: #ff8c00 !important;
        box-shadow: 0 0 8px rgba(255, 140, 0, 0.3) !important;
    }
   /* ปุ่มเครื่องมือวาดรูปบนเดสท็อป (ต่อท้าย Timeframe) */
    button[key="btn_toggle_draw_desktop"] {
        background-color: #0e1118 !important;
        border: 1px solid #1e2433 !important;
        color: #d1d5db !important;
        height: 28px !important;
        min-height: 28px !important;
        font-size: 13px !important;
        border-radius: 4px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease-in-out !important;
    }
    button[key="btn_toggle_draw_desktop"][kind="primary"],
    button[key="btn_toggle_draw_desktop"][data-testid="baseButton-primary"] {
        background: rgba(255, 125, 30, 0.22) !important;
        border: 1.5px solid #ff7d1e !important;
        box-shadow: 0 0 8px rgba(255, 125, 30, 0.5) !important;
    }
    button[key="btn_toggle_draw_desktop"]:hover {
        border-color: #ff7d1e !important;
    }
    /* สถานะเปิดใช้งาน: เรืองแสงสีส้มสไตล์ TradingView */
    button[key="btn_toggle_draw"][kind="primary"],
    button[key="btn_toggle_draw"][data-testid="baseButton-primary"] {
        background: rgba(255, 125, 30, 0.18) !important;
        border: 1.5px solid #ff7d1e !important;
        box-shadow: 0 0 10px rgba(255, 125, 30, 0.45) !important;
    }
    /* สถานะปิดใช้งาน: สีเทาเข้มกลืนกับแถบควบคุม */
    button[key="btn_toggle_draw"][kind="secondary"],
    button[key="btn_toggle_draw"][data-testid="baseButton-secondary"] {
        background: #0e1118 !important;
        border: 1px solid #1e2433 !important;
        opacity: 0.6 !important;
    }
    button[key="btn_toggle_draw"]:hover {
        border-color: #ff7d1e !important;
        opacity: 1 !important;
    }

    /* 7. ปลดล็อกกราฟและการปรับขนาดพาเนลด้วย CSS Variables */
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
        background-color: #090b10 !important;
        border-right: 1px solid #161a23 !important;
    }
    div[data-testid="column"]:has(#custom-center-chart-anchor) {
        flex: 1 1 0% !important;
        min-width: 300px !important;
        width: 100% !important;
    }
    div[data-testid="column"]:has(#custom-center-chart-anchor),
    div[data-testid="column"]:has(#custom-center-chart-anchor) iframe,
    div[data-testid="column"]:has(#custom-center-chart-anchor) div[data-testid="stCustomComponentV1"] {
        width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 auto !important;
    }
    div[data-testid="column"]:has(#custom-right-menu-anchor) {
        flex: 0 0 var(--right-panel-width) !important;
        width: var(--right-panel-width) !important;
        min-width: 200px !important;
        max-width: 520px !important;
        background-color: #090b10 !important;
        border-left: 1px solid #161a23 !important;
    }

    /* ปุ่มตลาด และปุ่มดาวฝั่งซ้าย */
    div[data-testid="column"]:has(#custom-left-menu-anchor) button:has(span:contains("ตลาด")),
    div[data-testid="column"]:has(#custom-left-menu-anchor) button:has(div:contains("ตลาด")) {
        background: linear-gradient(135deg, #00e676, #00ff88) !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: 1px solid #00ff88 !important;
        box-shadow: 0 0 12px rgba(0, 230, 118, 0.5) !important;
    }
    div[data-testid="column"]:has(#custom-left-menu-anchor) button:has(span:contains("⭐")),
    div[data-testid="column"]:has(#custom-left-menu-anchor) .stButton:has(button:contains("⭐")) button {
        background: rgba(0, 230, 118, 0.15) !important;
        border: 1.5px solid #00e676 !important;
        box-shadow: 0 0 8px rgba(0, 230, 118, 0.5) !important;
    }

    /* Watchlist Active Highlight (กรอบไฟสีส้มเรืองแสงแบบ TradingView แท้) */
    div[data-testid="column"]:has(#custom-left-menu-anchor) div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) button[kind="primary"],
    div[data-testid="column"]:has(#custom-left-menu-anchor) div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) button[data-testid="baseButton-primary"] {
        background: rgba(255, 125, 30, 0.22) !important;
        border: 1.5px solid #ff7d1e !important;
        box-shadow: 0 0 12px rgba(255, 125, 30, 0.6) !important;
        color: #ff9d42 !important;
        font-weight: 700 !important;
    }

    /* 8. สไตล์ตัวเลข % และราคา */
    .text-green, span:contains("+"), [data-change^="+"] {
        color: #00e676 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
    }
    .text-red, span:contains("-"), [data-change^="-"] {
        color: #ff3366 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
    }

    /* 9. Scrollbar Minimal Dark */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: #07080a; }
    ::-webkit-scrollbar-thumb { background: #1a202e; border-radius: 2px; }
    ::-webkit-scrollbar-thumb:hover { background: #ff8c00; }
</style>
""",
    unsafe_allow_html=True,
)

def inject_workspace_resizers():
  components.html(
      """
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
            color: #9E8B8B;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-bottom: 1px solid #392A2A;
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

                if (sideCol && !doc.getElementById('resizer-left-bar')) {
                    const resizerL = doc.createElement('div');
                    resizerL.id = 'resizer-left-bar';
                    resizerL.title = 'คลิกลากเพื่อปรับขนาด หรือคลิกปุ่มเพื่อพับเก็บ';
                    resizerL.style.cssText = 'position: relative; width: 10px; cursor: col-resize; display: flex; align-items: center; justify-content: center; z-index: 99999; flex-shrink: 0; user-select: none; margin: 0 -5px; touch-action: none;';
                    
                    resizerL.innerHTML = `
                        <div style="width:3px; height:60px; background:#ff7d1e; border-radius:2px; box-shadow:0 0 8px rgba(255,125,30,0.9);"></div>
                        <div id="btn-collapse-left" title="พับ/กาง เมนูซ้าย" style="position: absolute; left: -3px; width: 16px; height: 32px; background: #181b22; border: 1px solid #ff7d1e; border-radius: 4px; color: #ff7d1e; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 10px; font-weight: bold; box-shadow: 0 0 8px rgba(0,0,0,0.7); transition: all 0.15s ease;">◀</div>
                    `;
                    sideCol.after(resizerL);

                    const btnLeft = resizerL.querySelector('#btn-collapse-left');
                    let isCollapsed = false;
                    let lastWidth = '240px';

                    btnLeft.onclick = function(e) {
                        e.stopPropagation();
                        isCollapsed = !isCollapsed;
                        if (isCollapsed) {
                            lastWidth = sideCol.style.width || '240px';
                            sideCol.style.setProperty('display', 'none', 'important');
                            btnLeft.innerHTML = '▶';
                            btnLeft.style.left = '0px';
                        } else {
                            sideCol.style.setProperty('display', 'block', 'important');
                            sideCol.style.setProperty('width', lastWidth, 'important');
                            sideCol.style.setProperty('flex', '0 0 ' + lastWidth, 'important');
                            btnLeft.innerHTML = '◀';
                            btnLeft.style.left = '-3px';
                        }
                        notifyResize();
                    };

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
                    resizerL.onmousedown = (e) => {
                        if (e.target.id === 'btn-collapse-left') return;
                        e.preventDefault();
                        startDragL(e.clientX);
                    };
                    resizerL.ontouchstart = (e) => {
                        if (e.target.id === 'btn-collapse-left') return;
                        if (e.touches[0]) startDragL(e.touches[0].clientX);
                    };
                }

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
    """,
      height=0,
      width=0,
  )

if "chart_tabs" not in st.session_state:
  st.session_state["chart_tabs"] = [
      {"id": "tab_1", "symbol": "BTCUSDT", "tf": "1h"}
  ]
if "active_tab_id" not in st.session_state:
  st.session_state["active_tab_id"] = "tab_1"

if "current_symbol" not in st.session_state:
  st.session_state["current_symbol"] = "BTCUSDT"
if "selected_tf" not in st.session_state:
  st.session_state["selected_tf"] = "1h"
if "fast_ema" not in st.session_state:
  st.session_state["fast_ema"] = 7
if "slow_ema" not in st.session_state:
  st.session_state["slow_ema"] = 13
if "trend_ema" not in st.session_state:
  st.session_state["trend_ema"] = 45

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update(BROWSER_HEADERS)
retry_strategy = Retry(
    total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504]
)
HTTP_SESSION.mount("https://", HTTPAdapter(max_retries=retry_strategy))

def fetch_ohlcv(symbol: str, tf: str, bars: int) -> pd.DataFrame:
  if (
      symbol.startswith("RICE:")
      or symbol.startswith("FOB:")
      or "ZR=F" in symbol
  ):
    df = generate_rice_ohlcv(symbol, bars=bars)
  else:
    df = fetch_market_ohlcv(symbol=symbol, tf=tf, limit=bars)

  if not df.empty and "time" in df.columns:
    if pd.api.types.is_datetime64_any_dtype(df["time"]):
      df["time"] = df["time"].astype("int64") // 10**9
    df = (
        df.dropna()
        .drop_duplicates(subset=["time"])
        .sort_values("time")
        .tail(bars)
        .reset_index(drop=True)
    )

  if df is not None and not df.empty:
    st.session_state["df_data"] = df

  return df

# 1. Fragment แท็บด้านบน (อัปเดต % ทุก 5 วินาที)
@st.fragment(run_every=5)
def render_top_tabs_fragment():
  tabs = st.session_state["chart_tabs"]
  active_id = st.session_state["active_tab_id"]
  active_tab = next((t for t in tabs if t["id"] == active_id), tabs[0])
  symbol = active_tab["symbol"]

  ticker_24h = fetch_ticker_24h(symbol)
  live_pct = (
      float(ticker_24h["price_change_pct"])
      if ticker_24h and "price_change_pct" in ticker_24h
      else 0.0
  )
  pct_sign = "+" if live_pct >= 0 else ""
  pct_str = f"{pct_sign}{live_pct:.2f}%"

  has_close = len(tabs) > 1
  col_widths = [0.01]
  for _ in tabs:
    col_widths.append(1.0)
    if has_close:
      col_widths.append(0.18)
  col_widths.append(0.22)
  col_widths.append(8.0)

  t_cols = st.columns(col_widths, gap="small")
  col_iter = iter(t_cols)

  with next(col_iter):
    st.markdown('<div id="top-tabs-marker"></div>', unsafe_allow_html=True)

  for t in tabs:
    is_active = t["id"] == active_id
    t_meta = resolve_market_info(t["symbol"])
    t_label = (
        f"💎 {t_meta['display_name']} {pct_str if is_active else ''}".strip()
    )
    btn_type = "primary" if is_active else "secondary"

    with next(col_iter):
      if st.button(
          t_label,
          key=f"t_btn_{t['id']}",
          type=btn_type,
          use_container_width=True,
      ):
        st.session_state["active_tab_id"] = t["id"]
        st.session_state["current_symbol"] = t["symbol"]
        st.session_state["selected_tf"] = t["tf"]
        st.session_state.pop("selected_symbol", None)
        try:
          st.rerun(scope="app")
        except TypeError:
          st.rerun()

    if has_close:
      with next(col_iter):
        if st.button(
            "✕",
            key=f"t_close_{t['id']}",
            help="ปิดแท็บนี้",
            use_container_width=True,
        ):
          st.session_state["chart_tabs"] = [
              x for x in tabs if x["id"] != t["id"]
          ]
          if t["id"] == active_id:
            st.session_state["active_tab_id"] = st.session_state["chart_tabs"][
                0
            ]["id"]
            st.session_state["current_symbol"] = st.session_state["chart_tabs"][
                0
            ]["symbol"]
          try:
            st.rerun(scope="app")
          except TypeError:
            st.rerun()

  with next(col_iter):
    if st.button(
        "＋",
        key="btn_add_tab_global",
        help="เพิ่มแท็บกราฟใหม่",
        use_container_width=True,
    ):
      new_tab_id = f"tab_{int(time.time() * 1000)}"
      new_sym = "ETHUSDT" if symbol == "BTCUSDT" else "BTCUSDT"
      st.session_state["chart_tabs"].append(
          {"id": new_tab_id, "symbol": new_sym, "tf": active_tab.get("tf", "1h")}
      )
      st.session_state["active_tab_id"] = new_tab_id
      st.session_state["current_symbol"] = new_sym
      try:
        st.rerun(scope="app")
      except TypeError:
        st.rerun()

def render_sidebar_fragment():
  render_sidebar()

def render_right_panel_fragment(df, meta, is_thb_mode, fx_rate):
  render_right_panel(
      df=df, meta=meta, is_thb_mode=is_thb_mode, fx_rate=fx_rate
  )

def dashboard():
  if "clear_cache" in st.query_params:
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

  apply_theme()
  init_settings_state()
  inject_workspace_resizers()

  tabs = st.session_state["chart_tabs"]
  active_id = st.session_state["active_tab_id"]
  active_tab = next((t for t in tabs if t["id"] == active_id), tabs[0])

  incoming_sym = st.session_state.pop("selected_symbol", None)
  if incoming_sym:
    active_tab["symbol"] = incoming_sym

  symbol = active_tab["symbol"]
  st.session_state["current_symbol"] = symbol

  tf = active_tab.get("tf", st.session_state.get("selected_tf", "1h"))
  st.session_state["selected_tf"] = tf

  bars = TF_TARGET_BARS.get(tf, 25000)

  meta = resolve_market_info(symbol)
  fx_rate = get_usd_thb_rate()
  is_thb_mode = st.session_state.get("currency_mode_thb", False)

  df = fetch_ohlcv(symbol, tf, bars)
  if not df.empty:
    df, stats = diamond_armor(
        df,
        fast=st.session_state["fast_ema"],
        slow=st.session_state["slow_ema"],
        trend=st.session_state["trend_ema"],
    )

  raw_charts = build_charts(df, symbol, tf, 520, 120, 120)
  filtered_charts = raw_charts

  is_mobile = st.session_state.get("mobile_mode", False)

  if is_mobile:
    render_mobile_view(
        df=df,
        meta=meta,
        is_thb_mode=is_thb_mode,
        fx_rate=fx_rate,
        chart_renderer=lambda: render_drawing_chart(
            filtered_charts,
            height=480,
            key=f"c_{symbol}_{tf}_mobile",
            show_toolbar=st.session_state.get("show_draw_toolbar", True),
        ),
        watchlist_renderer=lambda: render_sidebar_fragment(),
    )
  else:
    render_top_tabs_fragment()

    c_tf, c_draw, c_ind, c_right_blank = st.columns(
        [5.15, 0.45, 2.0, 1.8], gap="small"
    )
    with c_right_blank:
      is_m = st.toggle("📱 มือถือ", value=False, key="toggle_mobile_mode")
      if is_m:
        st.session_state["mobile_mode"] = True
        st.rerun()
   
    with c_tf:
      st.markdown('<div class="notranslate" translate="no">', unsafe_allow_html=True)
      primary_tfs = [
          "5m", "15m", "30m", "1h", "2h", "3h", "4h",
          "D", "2D", "3D", "W", "M",
      ]
      cur_tf = tf
      def_idx = primary_tfs.index(cur_tf) if cur_tf in primary_tfs else 3
      new_tf = st.radio(
          "TF",
          primary_tfs,
          index=def_idx,
          horizontal=True,
          label_visibility="collapsed",
          key="toolbar_tf_horizontal",
      )
      if new_tf != cur_tf:
        active_tab["tf"] = new_tf
        st.session_state["selected_tf"] = new_tf
        st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

    with c_draw:
      draw_active = st.session_state.get("show_draw_toolbar", True)
      btn_type = "primary" if draw_active else "secondary"
      if st.button(
          "✏️",
          key="btn_toggle_draw_desktop",
          help="เปิด/ปิด แถบเครื่องมือวาดรูป (Draw Toolbar)",
          type=btn_type,
          use_container_width=True,
      ):
        st.session_state["show_draw_toolbar"] = not draw_active
        st.rerun()

    with c_ind:
      if st.button(
          "📊 Indicators",
          key="btn_open_ind_modal",
          type="secondary",
          use_container_width=True,
      ):
        st.session_state["modal_indicators_open"] = True

      if st.session_state.get("modal_indicators_open", False):
        show_indicators_modal()

    col_side, col_chart, col_quote = st.columns(
        [0.88, 3.87, 1.25], gap="small"
    )

    with col_side:
      st.markdown(
          '<div id="custom-left-menu-anchor"></div>', unsafe_allow_html=True
      )
      render_sidebar_fragment()

    with col_chart:
      st.markdown(
          '<div id="custom-center-chart-anchor"></div>', unsafe_allow_html=True
      )
      render_drawing_chart(
          filtered_charts,
          height=530,
          key=f"c_{symbol}_{tf}",
          show_toolbar=st.session_state.get("show_draw_toolbar", True),
      )

    with col_quote:
      st.markdown(
          '<div id="custom-right-menu-anchor"></div>', unsafe_allow_html=True
      )
      st.markdown(
          """
              <div style="display:flex; align-items:center; margin-bottom:6px;">
                  <span id="btn-collapse-right" title="คลิกเพื่อพับเก็บเมนูขวา" style="cursor:pointer; display:inline-block; width:11px; height:11px; background:#FF3366; border-radius:50%; margin-right:6px; box-shadow:0 0 6px #FF3366; transition:transform 0.15s;" onmouseover="this.style.transform='scale(1.25)'" onmouseout="this.style.transform='scale(1)'"></span>
                  <span id="btn-fullscreen-app" title="คลิกเพื่อขยายเต็มจอ / ออกจากเต็มจอ" style="cursor:pointer; display:inline-block; width:11px; height:11px; background:#00FF66; border-radius:50%; margin-right:8px; box-shadow:0 0 6px #00FF66; transition:transform 0.15s;" onmouseover="this.style.transform='scale(1.25)'" onmouseout="this.style.transform='scale(1)'"></span>
                  <b style='font-size:13px; color:#ffffff;'>บทวิเคราะห์เทคนิค 24h <span style='background:#FF7A1A; color:#000; font-size:9px; padding:2px 4px; border-radius:3px; font-weight:bold;'>PRO</span></b>
              </div>
          """,
          unsafe_allow_html=True,
      )
      render_right_panel_fragment(
          df=df, meta=meta, is_thb_mode=is_thb_mode, fx_rate=fx_rate
      )

dashboard()