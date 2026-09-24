# ui/sidebar_refactored.py — Streamlined Terminal Sidebar (Compact Watchlist Rows - TradingView Standard)
import streamlit as st
import datetime
import json
import os
import requests
from ui.symbol_modal import render_symbol_modal
from data.fetchers import resolve_market_info, fetch_ticker_24h, fetch_ohlcv, standardize_symbol
from ui.rice_seasonality_modal import show_rice_market_modal
from color_store import (
    COLOR_TAGS, COLOR_KEYS, norm_sym,
    ensure_color_state, assign_color, get_sym_color_key, get_sym_color_dot
)

WATCHLIST_STORE_FILE = "watchlist_store.json"

PREFERRED_COLOR_ORDER = ["red", "orange", "green", "blue", "gray"]
SORTED_COLOR_KEYS = [k for k in PREFERRED_COLOR_ORDER if k in COLOR_KEYS] + [k for k in COLOR_KEYS if k not in PREFERRED_COLOR_ORDER]


def _format_vol(v: float) -> str:
    """แปลงตัวเลข Volume เป็นหน่วย K, M, B แบบสากล"""
    if v >= 1e9:
        return f"{v / 1e9:.2f} B"
    elif v >= 1e6:
        return f"{v / 1e6:.2f} M"
    elif v >= 1e3:
        return f"{v / 1e3:.2f} K"
    elif v > 0:
        return f"{v:,.0f}"
    return "-"


@st.cache_data(ttl=15, show_spinner=False)
def _get_live_ticker(sym: str):
    """ดึงราคา, % 24h, และ Volume รวม 24h จาก fetch_ticker_24h รองรับทุกกระดาน"""
    try:
        t = fetch_ticker_24h(sym)
        if t and (t.get("last_price", 0) > 0 or t.get("price_change_pct", 0) != 0 or t.get("volume_24h", 0) > 0):
            p = float(t["last_price"])
            c = float(t.get("price_change_pct", 0.0))
            v = float(t.get("volume_24h", 0.0))
            p_str = f"{p:,.2f}" if p >= 1 else f"{p:.4f}"
            c_str = f"{c:+.2f}%"
            v_str = _format_vol(v)
            return p_str, c_str, v_str, (c >= 0), c, v
    except Exception:
        pass
    return None


@st.cache_data(ttl=5, show_spinner=False)
def _get_active_candle(sym: str, tf_str: str = "1h"):
    """ดึงแท่งเทียนล่าสุดตามไทม์เฟรมของกราฟ เพื่อให้ % Change ตรงกับกราฟหลัก 100%"""
    try:
        df = fetch_ohlcv(sym, tf=tf_str, limit=2)
        if df is not None and len(df) >= 2:
            prev_close = float(df["close"].iloc[-2])
            last_close = float(df["close"].iloc[-1])
            vol = float(df["volume"].iloc[-1]) if "volume" in df.columns else 0.0
            diff = last_close - prev_close
            pct = (diff / prev_close) * 100 if prev_close != 0 else 0.0
            p_str = f"{last_close:,.2f}" if last_close >= 1 else f"{last_close:.4f}"
            c_str = f"{pct:+.2f}%"
            v_str = _format_vol(vol)
            return p_str, c_str, v_str, (diff >= 0), pct, vol
    except Exception:
        pass
    return None


def load_saved_data():
    if os.path.exists(WATCHLIST_STORE_FILE):
        try:
            with open(WATCHLIST_STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("watchlist", []), data.get("colors", {})
        except Exception:
            pass
    default_watchlist = [
        ("BTCUSDT", "-", "-", True),
        ("ETHUSDT", "-", "-", True),
        ("SOLUSDT", "-", "-", True),
        ("BNBUSDT", "-", "-", True),
        ("ADAUSDT", "-", "-", True)
    ]
    return default_watchlist, {}


def save_watchlist_data():
    try:
        raw_rows = st.session_state.get("custom_watchlist", [])
        clean_list = [_normalize_row(r) for r in raw_rows]
        color_map = {}
        for r in clean_list:
            s = r[0]
            ckey = get_sym_color_key(s)
            if ckey:
                color_map[s] = ckey
        with open(WATCHLIST_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"watchlist": clean_list, "colors": color_map}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_to_watchlist(sym_code: str):
    """เพิ่มเหรียญเข้า Watchlist โดยตรงแบบ TradingView (ไม่เพิ่มซ้ำ)"""
    if not sym_code:
        return
    clean = standardize_symbol(sym_code)
    raw = norm_sym(sym_code).upper()
    existing = [norm_sym(r[0] if isinstance(r, (list, tuple)) else (r.get("symbol") if isinstance(r, dict) else r)).upper() for r in st.session_state.get("custom_watchlist", [])]
    existing_clean = [standardize_symbol(s) for s in existing]
    if raw not in existing and clean not in existing_clean:
        if "custom_watchlist" not in st.session_state:
            st.session_state["custom_watchlist"] = []
        st.session_state["custom_watchlist"].append((raw, "-", "-", True))
        save_watchlist_data()


def remove_from_watchlist(target_sym: str):
    """ลบเหรียญออกจาก Watchlist ทันทีแบบ 1-Click และสลับเหรียญหากเหรียญที่ลบกำลังเปิดดูอยู่"""
    t_clean = standardize_symbol(target_sym)
    target_norm = norm_sym(target_sym).upper()

    st.session_state["custom_watchlist"] = [
        item for item in st.session_state.get("custom_watchlist", [])
        if norm_sym(item[0] if isinstance(item, (list, tuple)) else item).upper() not in [target_norm, t_clean]
        and standardize_symbol(item[0] if isinstance(item, (list, tuple)) else item) != t_clean
    ]
    assign_color(target_sym, None)
    assign_color(t_clean, None)
    save_watchlist_data()

    cur_sel = st.session_state.get("current_symbol", "BTCUSDT")
    if standardize_symbol(cur_sel) == t_clean or norm_sym(cur_sel).upper() == target_norm:
        rem = st.session_state.get("custom_watchlist", [])
        fallback = rem[0][0] if rem else "BTCUSDT"
        set_active_symbol(fallback)


@st.dialog("⚙️ การตั้งค่าระบบและชาร์ต (Unified Settings)")
def show_chart_settings_dialog():
    tab_chart, tab_ui = st.tabs([
        "🎨 กราฟ & ธีม", 
        "🖥️ พื้นที่ทำงาน"
    ])

    with tab_chart:
        st.caption("🎨 โทนสีแท่งเทียนและพื้นหลัง")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state["candle_up_color"] = st.color_picker(
                "แท่งขึ้น (Bullish)", value=st.session_state.get("candle_up_color", "#089981")
            )
        with c2:
            st.session_state["candle_down_color"] = st.color_picker(
                "แท่งลง (Bearish)", value=st.session_state.get("candle_down_color", "#F23645")
            )
        c3, c4 = st.columns(2)
        with c3:
            st.session_state["chart_bg_color"] = st.color_picker(
                "พื้นหลังกราฟ (Background)", value=st.session_state.get("chart_bg_color", "#131722")
            )
        with c4:
            st.session_state["chart_grid_color"] = st.color_picker(
                "เส้นกริด (Grid)", value=st.session_state.get("chart_grid_color", "#1e222d")
            )

    with tab_ui:
        st.caption("🖥 ควบคุมการแสดงผลแถบ 'กราฟเปรียบเทียบ'")
        st.session_state["show_draw_toolbar"] = st.toggle(
            "✏️ แถบวาดรูป (Draw Toolbar)", value=st.session_state.get("show_draw_toolbar", True)
        )
        st.session_state["show_top_bar"] = st.toggle(
            "💻 แถบควบคุมบน (Top Bar)", value=st.session_state.get("show_top_bar", True)
        )

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🔄 รีเซ็ตเป็นค่าเริ่มต้น", use_container_width=True):
            st.session_state["candle_up_color"] = "#089981"
            st.session_state["candle_down_color"] = "#F23645"
            st.session_state["chart_bg_color"] = "#131722"
            st.session_state["chart_grid_color"] = "#1e222d"
            st.session_state["show_draw_toolbar"] = True
            st.session_state["show_top_bar"] = True
            st.rerun()
    with b2:
        if st.button("💾 บันทึกและปรับใช้", type="primary", use_container_width=True):
            st.rerun()


def set_active_symbol(sym_code: str):
    """สลับเหรียญบนกราฟหลัก (ตัดระบบ Auto-insert เพื่อไม่ให้เหรียญเด้งกลับมาเอง)"""
    clean_sym = standardize_symbol(sym_code)
    st.session_state["current_symbol"] = clean_sym
    st.session_state["selected_symbol"] = clean_sym

    if "chart_tabs" in st.session_state and st.session_state["chart_tabs"]:
        active_id = st.session_state.get("active_tab_id")
        for t in st.session_state["chart_tabs"]:
            if t.get("id") == active_id:
                t["symbol"] = clean_sym
                break

    if "open_tabs" in st.session_state and st.session_state.open_tabs:
        active_id = st.session_state.get("active_tab_id")
        for t in st.session_state.open_tabs:
            if t.get("id") == active_id:
                t["symbol"] = clean_sym
                break

    for k in ("active_key", "df_data", "last_fetch_time"):
        st.session_state.pop(k, None)


def _color_menu(sym: str, prefix: str = "wl") -> None:
    s = norm_sym(sym)
    current = get_sym_color_key(s)
    st.caption(f"กลุ่มสีของ {s}")
    for ckey in SORTED_COLOR_KEYS:
        cinfo = COLOR_TAGS[ckey]
        mark = " ✓" if ckey == current else ""
        if st.button(f"{cinfo['dot']} {cinfo['label']}{mark}", key=f"{prefix}_clr_{s}_{ckey}", use_container_width=True):
            assign_color(s, None if ckey == current else ckey)
            save_watchlist_data()
            st.rerun()

    st.divider()
    if st.button("✖ ปลดกลุ่มสี", key=f"{prefix}_clr_{s}_none", use_container_width=True, disabled=(current is None)):
        assign_color(s, None)
        save_watchlist_data()
        st.rerun()


def _normalize_row(row):
    if isinstance(row, dict):
        return (norm_sym(row.get("symbol") or row.get("sym")), row.get("price", "-"), row.get("change", "-"), bool(row.get("is_up", True)))
    if isinstance(row, (list, tuple)):
        vals = list(row) + ["-", "-", True]
        return (norm_sym(vals[0]), vals[1], vals[2], bool(vals[3]))
    return (norm_sym(row), "-", "-", True)


@st.fragment
def render_sidebar():
    st.markdown('<div id="custom-left-menu-anchor" style="display:none;"></div>', unsafe_allow_html=True)
    ensure_color_state()

    if "custom_watchlist" not in st.session_state:
        saved_wl, saved_colors = load_saved_data()
        st.session_state["custom_watchlist"] = saved_wl
        for s, ckey in saved_colors.items():
            assign_color(s, ckey)

    if "sidebar_active_tab" not in st.session_state:
        st.session_state["sidebar_active_tab"] = "market"
    if "color_filter" not in st.session_state:
        st.session_state["color_filter"] = None
    if "wl_sort_mode" not in st.session_state:
        st.session_state["wl_sort_mode"] = "none"

    st.markdown("""
    <style>
    .tv-sort-wrap div[data-testid="stBaseButton-tertiary"] button,
    .tv-sort-wrap button {
        background: transparent !important;
        border: none !important;
        color: #8b949e !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        padding: 0 2px !important;
        min-height: 22px !important;
        height: 22px !important;
        box-shadow: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    .tv-sort-wrap button:hover {
        color: #ff7d1e !important;
    }
    .tv-sort-right div[data-testid="stBaseButton-tertiary"] button,
    .tv-sort-right button {
        background: transparent !important;
        border: none !important;
        color: #8b949e !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        padding: 0 2px !important;
        min-height: 22px !important;
        height: 22px !important;
        box-shadow: none !important;
        text-align: right !important;
        justify-content: flex-end !important;
    }
    .tv-sort-right button:hover {
        color: #ff7d1e !important;
    }

    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) {
        gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) {
        margin-bottom: -4px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) div[data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) button {
        min-height: 24px !important;
        height: 24px !important;
        padding: 0px 4px !important;
        font-size: 11.5px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) div[data-testid="stPopover"] button {
        min-height: 22px !important;
        height: 22px !important;
        width: 22px !important;
        padding: 0 !important;
    }

    /* ปุ่มจุดสีจัดการกลุ่มสี */
    .tv-neon-wrap div[data-testid="stPopover"] button {
        background: rgba(255, 107, 0, 0.14) !important;
        border: 1px solid rgba(255, 125, 30, 0.4) !important;
        color: #FF7D1E !important;
        padding: 0 !important;
        border-radius: 50% !important;
        font-size: 9px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .tv-neon-wrap div[data-testid="stPopover"] button:hover {
        background: #FF7D1E !important;
        color: #131722 !important;
        box-shadow: 0 0 8px #FF7D1E !important;
    }

    /* ปุ่มลบ ✕ สไตล์ TradingView */
    .tv-del-btn button {
        background: transparent !important;
        border: none !important;
        color: #555e6d !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        padding: 0 !important;
        min-height: 22px !important;
        height: 22px !important;
        width: 22px !important;
        border-radius: 3px !important;
        box-shadow: none !important;
        transition: all 0.15s ease-in-out !important;
    }
    .tv-del-btn button:hover {
        color: #ff3366 !important;
        background: rgba(255, 51, 102, 0.18) !important;
    }

    .tv-val-up {
        color: #00e676 !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace !important;
        white-space: nowrap !important;
    }
    .tv-val-down {
        color: #ff3366 !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace !important;
        white-space: nowrap !important;
    }
    .tv-vol-text {
        color: #ff8c00 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
        white-space: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ปุ่มสลับแท็บหลัก: ตลาด | กราฟเปรียบเทียบ
    t_c1, t_c2 = st.columns(2)
    with t_c1:
        if st.button("ตลาด", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "market" else "secondary"):
            st.session_state["sidebar_active_tab"] = "market"
            st.rerun()
    with t_c2:
        if st.button("กราฟเปรียบเทียบ", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "tools" else "secondary"):
            st.session_state["sidebar_active_tab"] = "tools"
            st.rerun()

    # ──────────────────────────────────────────────────────────
    # TAB 1: ตลาด (Watchlist สไตล์ TradingView)
    # ──────────────────────────────────────────────────────────
    if st.session_state["sidebar_active_tab"] == "market":
        selected_sym = st.session_state.get("current_symbol", "BTCUSDT")

        # 1. ปุ่มค้นหาเหรียญมาตรฐาน (ไม่ล็อกชื่อเหรียญค้างไว้ให้สับสน)
        if st.button("🔍 ค้นหาเหรียญ / สัญลักษณ์สินทรัพย์...", key="btn_open_symbol_modal", use_container_width=True, type="secondary"):
            render_symbol_modal()

        # แถบกรอง 5 สี
        st.markdown("<div style='font-size:11px; color:#8b949e; margin-top:8px; margin-bottom:4px;'>🏷️ กลุ่มสีโปรด (คลิกเพื่อกรอง):</div>", unsafe_allow_html=True)
        f_cols = st.columns([1.1, 1, 1, 1, 1, 1], gap="small")
        active = st.session_state.get("color_filter")

        with f_cols[0]:
            if st.button("ALL" if active else "⭐", key="cf_all", use_container_width=True, type="primary" if active is None else "tertiary"):
                st.session_state["color_filter"] = None
                st.rerun()

        for i, ckey in enumerate(SORTED_COLOR_KEYS):
            with f_cols[i + 1]:
                btn_type = "primary" if active == ckey else "tertiary"
                dot_char = COLOR_TAGS[ckey]["dot"]
                if st.button(dot_char, key=f"cf_{ckey}", use_container_width=True, type=btn_type):
                    st.session_state["color_filter"] = None if active == ckey else ckey
                    st.rerun()

        # 2. ส่วนหัวตาราง Watchlist พร้อมปุ่ม ➕ เพิ่มเหรียญ (ตัดเมนู ..^ เดิมทิ้ง 100%)
        h_title, h_add = st.columns([1.8, 0.4], gap="small", vertical_alignment="center")
        with h_title:
            st.markdown("<div style='font-size:12px; font-weight:700; color:#8b949e;'>📋 รายการสินทรัพย์เฝ้าดู</div>", unsafe_allow_html=True)
        with h_add:
            with st.popover("➕", help="เพิ่มเหรียญ/หุ้น เข้า Watchlist"):
                st.markdown("<b style='font-size:12px; color:#00e676;'>➕ เพิ่มเหรียญเข้า Watchlist</b>", unsafe_allow_html=True)
                new_sym_in = st.text_input("พิมพ์ชื่อเหรียญหรือหุ้น:", placeholder="เช่น BTC, ETH, DELTABK, PERPTHB", key="quick_add_sym_input")
                c_add_btn, c_browse = st.columns([0.6, 0.4])
                with c_add_btn:
                    if st.button("เพิ่ม", key="btn_confirm_quick_add", type="primary", use_container_width=True):
                        if new_sym_in.strip():
                            add_to_watchlist(new_sym_in.strip())
                            st.toast(f"เพิ่ม '{new_sym_in.strip().upper()}' แล้ว!")
                            st.rerun()
                with c_browse:
                    if st.button("ค้นหา...", key="btn_browse_symbols", use_container_width=True):
                        render_symbol_modal()

        # ส่วนหัวคอลัมน์ตาราง 4 ช่อง จัดสัดส่วนตรงกับข้อมูลข้างล่าง
        h_c1, h_c2, h_c3, h_c4 = st.columns([1.44, 0.90, 0.86, 0.28], gap="small", vertical_alignment="center")
        sort_mode = st.session_state.get("wl_sort_mode", "none")

        with h_c1:
            lbl_sym = "สัญลักษณ์"
            if sort_mode == "sym_asc": lbl_sym = "สัญลักษณ์ ▲"
            elif sort_mode == "sym_desc": lbl_sym = "สัญลักษณ์ ▼"
            st.markdown('<div class="tv-sort-wrap">', unsafe_allow_html=True)
            if st.button(lbl_sym, key="btn_sort_sym", type="tertiary", use_container_width=True):
                st.session_state["wl_sort_mode"] = "sym_desc" if sort_mode == "sym_asc" else ("none" if sort_mode == "sym_desc" else "sym_asc")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with h_c2:
            lbl_pct = "เปลี่ยน"
            if sort_mode == "pct_desc": lbl_pct = "เปลี่ยน ▼"
            elif sort_mode == "pct_asc": lbl_pct = "เปลี่ยน ▲"
            st.markdown('<div class="tv-sort-wrap">', unsafe_allow_html=True)
            if st.button(lbl_pct, key="btn_sort_pct", type="tertiary", use_container_width=True):
                st.session_state["wl_sort_mode"] = "pct_asc" if sort_mode == "pct_desc" else ("none" if sort_mode == "pct_asc" else "pct_desc")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with h_c3:
            lbl_vol = "ปริมาณ"
            if sort_mode == "vol_desc": lbl_vol = "ปริมาณ ▼"
            st.markdown('<div class="tv-sort-right">', unsafe_allow_html=True)
            if st.button(lbl_vol, key="btn_sort_vol", type="tertiary", use_container_width=True):
                st.session_state["wl_sort_mode"] = "none" if sort_mode == "vol_desc" else "vol_desc"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with h_c4:
            st.markdown("<span style='font-size:10px; color:#555e6d;'>ลบ</span>", unsafe_allow_html=True)

        raw_rows = [_normalize_row(r) for r in st.session_state.get("custom_watchlist", [])]
        rows = [r for r in raw_rows if get_sym_color_key(r[0]) == active] if active else raw_rows

        if not rows:
            st.caption("ไม่มีเหรียญในกลุ่มนี้ กดปุ่ม ➕ ด้านบนเพื่อเพิ่มเหรียญ")

        active_tf = (
            st.session_state.get("timeframe") or 
            st.session_state.get("selected_timeframe") or 
            st.session_state.get("current_timeframe") or 
            st.session_state.get("selected_tf") or
            st.session_state.get("tf") or 
            "1h"
        )

        display_rows = []
        for sym, p_val, c_val, is_up in rows:
            dot = get_sym_color_dot(sym)
            c_num = 0.0
            v_num = 0.0
            v_val = "-"
            p_val = "-"
            c_val = "+0.00%"
            is_up = True

            s_std = standardize_symbol(sym)
            sel_std = standardize_symbol(selected_sym)
            is_active = (s_std == sel_std) or (norm_sym(sym).upper() == norm_sym(selected_sym).upper())

            # 3.1 ดึง 24h Ticker เพื่อใช้ปริมาณซื้อขาย 24 ชั่วโมง (มาตรฐานเดียวกันตลอดเวลา ไม่สับสนกับแท่ง 1 ชม.)
            ticker_data = _get_live_ticker(sym)
            if ticker_data:
                p_val, c_val, v_val, is_up, c_num, v_num = ticker_data

            # 3.2 ซิงค์ % เปลี่ยนแปลงกับแท่งเทียนกราฟปัจจุบันเฉพาะเหรียญที่กำลังเปิดดู
            if is_active:
                df_act = None
                for k in ("df_data", "df", "chart_df", "data"):
                    v_df = st.session_state.get(k)
                    if v_df is not None and hasattr(v_df, "columns") and len(v_df) >= 2:
                        df_act = v_df
                        break

                if df_act is not None:
                    c_col = next((c for c in df_act.columns if "close" in str(c).lower()), None)
                    if c_col and len(df_act) >= 2:
                        last_close = float(df_act[c_col].iloc[-1])
                        prev_close = float(df_act[c_col].iloc[-2])
                        diff = last_close - prev_close
                        pct = (diff / prev_close) * 100 if prev_close != 0 else 0.0
                        p_val = f"{last_close:,.2f}" if last_close >= 1 else f"{last_close:.4f}"
                        c_val = f"{pct:+.2f}%"
                        is_up = (diff >= 0)
                        c_num = pct
                else:
                    candle_data = _get_active_candle(sym, active_tf)
                    if candle_data:
                        p_val, c_val, _, is_up, c_num, _ = candle_data

            display_rows.append({
                "sym": sym,
                "dot": dot,
                "p_val": p_val,
                "c_val": c_val,
                "v_val": v_val,
                "is_up": is_up,
                "c_num": c_num,
                "v_num": v_num
            })

        if sort_mode == "sym_asc":
            display_rows.sort(key=lambda x: x["sym"])
        elif sort_mode == "sym_desc":
            display_rows.sort(key=lambda x: x["sym"], reverse=True)
        elif sort_mode == "pct_desc":
            display_rows.sort(key=lambda x: x["c_num"], reverse=True)
        elif sort_mode == "pct_asc":
            display_rows.sort(key=lambda x: x["c_num"])
        elif sort_mode == "vol_desc":
            display_rows.sort(key=lambda x: x["v_num"], reverse=True)

        with st.container(height=480):
            for item in display_rows:
                sym = item["sym"]
                dot = item["dot"]
                c_val = item["c_val"]
                v_val = item["v_val"]
                is_up = item["is_up"]

                # 4. แบ่งคอลัมน์อิสระ 5 ช่อง ไม่บีบอัด ไม่ขึ้นตัวอักษรแปลกปลอม
                c_sym, c_tag, c_pct, c_vol, c_del = st.columns([1.18, 0.26, 0.90, 0.86, 0.28], gap="small", vertical_alignment="center")
                with c_sym:
                    btn_title = f"{dot} {sym}".strip()
                    if st.button(btn_title, key=f"wl_btn_{sym}", use_container_width=True):
                        set_active_symbol(sym)
                        st.rerun()
                with c_tag:
                    st.markdown('<div class="tv-neon-wrap">', unsafe_allow_html=True)
                    with st.popover("●", use_container_width=True, help=f"จัดกลุ่มสี {sym}"):
                        _color_menu(sym, prefix="wl")
                    st.markdown('</div>', unsafe_allow_html=True)
                with c_pct:
                    cls = "tv-val-up" if is_up else "tv-val-down"
                    st.markdown(f'<div style="text-align:right;"><span class="{cls}">{c_val}</span></div>', unsafe_allow_html=True)
                with c_vol:
                    st.markdown(f'<div style="text-align:right;"><span class="tv-vol-text">{v_val}</span></div>', unsafe_allow_html=True)
                with c_del:
                    st.markdown('<div class="tv-del-btn">', unsafe_allow_html=True)
                    if st.button("✕", key=f"wl_del_{sym}", help=f"ลบ {sym} ออกจาก Watchlist"):
                        remove_from_watchlist(sym)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────
    # TAB 2: กราฟเปรียบเทียบ
    # ──────────────────────────────────────────────────────────
    else:
        st.markdown("<div style='font-size:11px; color:#00FFA3; margin-bottom:8px;'>⚡ หมวดหมู่เปรียบเทียบ</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🌾 ตลาดข้าว", key="btn_rice_modal", use_container_width=True, type="secondary"):
                from ui import rice_seasonality_modal
                rice_seasonality_modal.show_rice_market_modal()
        with c2:
            if st.button("🪙 คริปโต", key="btn_crypto_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_crypto_modal()

        c3, c4 = st.columns(2)
        with c3:
            if st.button("📈 หุ้น (GICS)", key="btn_stocks_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_stocks_gics_modal()
        with c4:
            if st.button("⛏️ แร่ & เหมือง", key="btn_metals_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_metals_mining_modal()

        c5, c6 = st.columns(2)
        with c5:
            if st.button("💵 สกุลเงิน FX", key="btn_forex_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_forex_modal()
        with c6:
            if st.button("🌐 เทียบข้ามกลุ่ม", key="btn_macro_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_macro_comparison_modal()

        st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
        if st.button("🧭 บทวิเคราะห์เงินทุนไหล (Capital Flow)", key="btn_flow_modal", use_container_width=True, type="primary"):
            from ui import macro_comparison_modal
            macro_comparison_modal.show_flow_analysis_modal()

    # -------------------------------------------------------------
    # แถบล่างสุด: ตั้งค่า + นาฬิกา
    # -------------------------------------------------------------
    st.markdown("<hr style='margin: 14px 0 10px 0; border: 0.5px solid #2a2e39;'>", unsafe_allow_html=True)

    col_set, col_clk = st.columns([0.42, 0.58], vertical_alignment="center")
    with col_set:
        if st.button("⚙️ ตั้งค่า", key="btn_chart_settings", use_container_width=True, type="secondary", help="ตั้งค่ากราฟ"):
            show_chart_settings_dialog()

    with col_clk:
        now_bkk = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
        st.markdown(f"""
        <div style="padding:6px 8px; background:#131722; border:1px solid #2a2e39; border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:10px; color:#787b86; display:flex; align-items:center; gap:3px;">
                    <span>🕒</span> BKK
                </div>
                <div style="font-size:11px; font-weight:600; color:#d1d4dc; font-family:monospace;">
                    {now_bkk.strftime('%H:%M:%S')}
                </div>
            </div>
            <span style="background:rgba(38,166,154,0.15); color:#26a69a; border:1px solid #26a69a; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:bold;">LIVE</span>
        </div>
        """, unsafe_allow_html=True)

    return {
        "show_top_bar": st.session_state.get("show_top_bar", True),
        "show_draw_toolbar": st.session_state.get("show_draw_toolbar", True)
    }