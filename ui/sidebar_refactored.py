import streamlit as st
import datetime
import json
import os
import requests
from ui.symbol_modal import render_symbol_modal
from data.fetchers import resolve_market_info
from ui.rice_seasonality_modal import show_rice_market_modal
from color_store import (
    COLOR_TAGS, COLOR_KEYS, norm_sym,
    ensure_color_state, assign_color, get_sym_color_key, get_sym_color_dot
)

WATCHLIST_STORE_FILE = "watchlist_store.json"

# ลำดับสี: แดง 🔴 -> ส้ม 🟠 -> เขียว 🟢 -> ฟ้า 🔵 -> เทา/ขาว ⚪
PREFERRED_COLOR_ORDER = ["red", "orange", "green", "blue", "gray"]
SORTED_COLOR_KEYS = [k for k in PREFERRED_COLOR_ORDER if k in COLOR_KEYS] + [k for k in COLOR_KEYS if k not in PREFERRED_COLOR_ORDER]


# ══════════════════════════════════════════════════════════════
# ระบบแปลงหน่วย Volume ให้อ่านง่ายแบบ TradingView
# ══════════════════════════════════════════════════════════════
def _format_vol(v: float) -> str:
    """แปลงตัวเลข Volume เป็นหน่วย K, M, B"""
    if v >= 1e9:
        return f"{v / 1e9:.2f} B"
    elif v >= 1e6:
        return f"{v / 1e6:.2f} M"
    elif v >= 1e3:
        return f"{v / 1e3:.2f} K"
    elif v > 0:
        return f"{v:,.0f}"
    return "-"


# ══════════════════════════════════════════════════════════════
# ระบบดึงราคา % และ Volume (Fast Cache Ticker)
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=15, show_spinner=False)
def _get_live_ticker(sym: str):
    """ดึงราคา, % 24h, และ Volume จาก Binance API แบบแคช 15 วินาที"""
    try:
        s = norm_sym(sym).upper()
        if not any(s.endswith(x) for x in ["USDT", "BUSD", "USDC", "BTC"]):
            s += "USDT"
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}"
        resp = requests.get(url, timeout=1.2).json()
        if "lastPrice" in resp:
            p = float(resp["lastPrice"])
            c = float(resp["priceChangePercent"])
            v = float(resp.get("volume", 0.0))
            p_str = f"{p:,.2f}" if p >= 1 else f"{p:.4f}"
            c_str = f"{c:+.2f}%"
            v_str = _format_vol(v)
            return p_str, c_str, v_str, (c >= 0), c, v
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════
# ระบบบันทึกข้อมูล Watchlist และกลุ่มสีลงไฟล์ถาวร
# ══════════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════
# 1. กล่องโมดอลศูนย์ตั้งค่ารวม (Unified Settings Dialog)
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# 2. ฟังก์ชันจัดการข้อมูลเหรียญและสี
# ══════════════════════════════════════════════════════════════
def set_active_symbol(sym_code: str):
    sym_code = norm_sym(sym_code)
    st.session_state["current_symbol"] = sym_code
    st.session_state["selected_symbol"] = sym_code
    
    if "custom_watchlist" not in st.session_state:
        st.session_state["custom_watchlist"] = []
    
    existing = [norm_sym(r[0] if isinstance(r, (list, tuple)) else (r.get("symbol") if isinstance(r, dict) else r)) for r in st.session_state["custom_watchlist"]]
    if sym_code not in existing:
        st.session_state["custom_watchlist"].insert(0, (sym_code, "-", "-", True))
        save_watchlist_data()

    if "chart_tabs" in st.session_state and st.session_state["chart_tabs"]:
        active_id = st.session_state.get("active_tab_id")
        for t in st.session_state["chart_tabs"]:
            if t.get("id") == active_id:
                t["symbol"] = sym_code
                break

    if "open_tabs" in st.session_state and st.session_state.open_tabs:
        active_id = st.session_state.get("active_tab_id")
        for t in st.session_state.open_tabs:
            if t.get("id") == active_id:
                t["symbol"] = sym_code
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
    if st.button("🗑️ ลบจาก Watchlist", key=f"{prefix}_clr_{s}_del", use_container_width=True):
        assign_color(s, None)
        if "custom_watchlist" in st.session_state:
            st.session_state["custom_watchlist"] = [
                item for item in st.session_state["custom_watchlist"]
                if norm_sym(item[0] if isinstance(item, (list, tuple)) else item) != s
            ]
        save_watchlist_data()
        st.rerun()

def _normalize_row(row):
    if isinstance(row, dict):
        return (norm_sym(row.get("symbol") or row.get("sym")), row.get("price", "-"), row.get("change", "-"), bool(row.get("is_up", True)))
    if isinstance(row, (list, tuple)):
        vals = list(row) + ["-", "-", True]
        return (norm_sym(vals[0]), vals[1], vals[2], bool(vals[3]))
    return (norm_sym(row), "-", "-", True)


# ══════════════════════════════════════════════════════════════
# 3. เมนูหลักแถบข้าง SIDEBAR (Fragmented UI)
# ══════════════════════════════════════════════════════════════
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

    # สไตล์ UI TradingView + ปุ่มหัวตารางสำหรับคลิกจัดเรียง
    st.markdown("""
    <style>
    /* สไตล์ปุ่มหัวตารางสำหรับจัดเรียง */
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

    /* ปุ่มจุดส้มนีออนหลังชื่อเหรียญ */
    .tv-neon-wrap div[data-testid="stPopover"] button {
        background: rgba(255, 107, 0, 0.18) !important;
        border: 1px solid #FF7D1E !important;
        color: #FF7D1E !important;
        box-shadow: 0 0 7px rgba(255, 125, 30, 0.55) !important;
        padding: 0 !important;
        min-height: 22px !important;
        height: 22px !important;
        width: 22px !important;
        border-radius: 50% !important;
        font-size: 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .tv-neon-wrap div[data-testid="stPopover"] button:hover {
        background: #FF7D1E !important;
        color: #131722 !important;
        box-shadow: 0 0 12px #FF7D1E !important;
    }
    .tv-val-up {
        color: #089981;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
    }
    .tv-val-down {
        color: #F23645;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
    }
    .tv-vol-text {
        color: #8b949e;
        font-size: 11px;
        font-weight: 600;
        text-align: right;
        white-space: nowrap;
    }
    .tv-quick-badge-on {
        background: rgba(0, 255, 102, 0.15);
        color: #00FF66;
        border: 1px solid #00FF66;
        padding: 1px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # ปุ่มสลับแท็บหลัก: ตลาด  | กราฟเปรียบเทียบ (เขียว)
    t_c1, t_c2 = st.columns(2)
    with t_c1:
        if st.button("ตลาด", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "market" else "secondary"):
            st.session_state["sidebar_active_tab"] = "market"
            st.rerun()
    with t_c2:
        if st.button("กราฟเปรียบเทียบ (เขียว)", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "tools" else "secondary"):
            st.session_state["sidebar_active_tab"] = "tools"
            st.rerun()

    # ──────────────────────────────────────────────────────────
    # TAB 1: ตลาด
    # ──────────────────────────────────────────────────────────
    if st.session_state["sidebar_active_tab"] == "market":
        st.selectbox(
            "1. กลุ่มสินทรัพย์",
            ["1. คริปโต (Crypto)", "2. หุ้น (Stock)", "3. ฟอเร็กซ์ (Forex)", "4. สินทรัพย์/โภคภัณฑ์", "5. ข้าว (Rice)"],
            label_visibility="collapsed",
            key="sb_asset_cat"
        )

        selected_sym = st.session_state.get("current_symbol", "BTCUSDT")
        meta = resolve_market_info(selected_sym)
        tag = meta.get("exchange", "BINANCE")

        # บันทึกเหรียญปัจจุบันเข้า Watchlist อัตโนมัติถ้ายังไม่มี
        existing_syms = [norm_sym(r[0] if isinstance(r, (list, tuple)) else (r.get("symbol") if isinstance(r, dict) else r)) for r in st.session_state["custom_watchlist"]]
        if norm_sym(selected_sym) not in existing_syms:
            st.session_state["custom_watchlist"].insert(0, (norm_sym(selected_sym), "-", "-", True))
            save_watchlist_data()

        # ปุ่มค้นหาเหรียญเต็มความกว้าง
        if st.button(f"🔍 {selected_sym}  [{tag}]", key="btn_open_symbol_modal", use_container_width=True, type="secondary"):
            render_symbol_modal()

        # แถบกรอง 5 สี เรียงลำดับ: ALL -> แดง -> ส้ม -> เขียว -> ฟ้า -> เทา
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

        # ส่วนหัวตาราง Watchlist พร้อมปุ่มคลิกจัดเรียง (สัญลักษณ์ | เปลี่ยน | ปริมาณ)
        st.markdown("<div style='font-size:12px; color:#8b949e; margin:10px 0 2px 0;'>📋 รายการสินทรัพย์เฝ้าดู</div>", unsafe_allow_html=True)
        h_c1, h_c2, h_c3 = st.columns([1.47, 0.77, 0.76], gap="small", vertical_alignment="center")

        sort_mode = st.session_state.get("wl_sort_mode", "none")

        with h_c1:
            lbl_sym = "สัญลักษณ์"
            if sort_mode == "sym_asc": lbl_sym = "สัญลักษณ์ ▲"
            elif sort_mode == "sym_desc": lbl_sym = "สัญลักษณ์ ▼"
            st.markdown('<div class="tv-sort-wrap">', unsafe_allow_html=True)
            if st.button(lbl_sym, key="btn_sort_sym", type="tertiary", use_container_width=True, help="คลิกเพื่อเรียงชื่อตัวอักษร"):
                if sort_mode == "sym_asc":
                    st.session_state["wl_sort_mode"] = "sym_desc"
                elif sort_mode == "sym_desc":
                    st.session_state["wl_sort_mode"] = "none"
                else:
                    st.session_state["wl_sort_mode"] = "sym_asc"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with h_c2:
            lbl_pct = "เปลี่ยน"
            if sort_mode == "pct_desc": lbl_pct = "เปลี่ยน ▼"
            elif sort_mode == "pct_asc": lbl_pct = "เปลี่ยน ▲"
            st.markdown('<div class="tv-sort-wrap">', unsafe_allow_html=True)
            if st.button(lbl_pct, key="btn_sort_pct", type="tertiary", use_container_width=True, help="คลิกเพื่อเรียงตาม % บวกลบ"):
                if sort_mode == "pct_desc":
                    st.session_state["wl_sort_mode"] = "pct_asc"
                elif sort_mode == "pct_asc":
                    st.session_state["wl_sort_mode"] = "none"
                else:
                    st.session_state["wl_sort_mode"] = "pct_desc"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with h_c3:
            lbl_vol = "ปริมาณ"
            if sort_mode == "vol_desc": lbl_vol = "ปริมาณ ▼"
            st.markdown('<div class="tv-sort-right">', unsafe_allow_html=True)
            if st.button(lbl_vol, key="btn_sort_vol", type="tertiary", use_container_width=True, help="คลิกเพื่อเรียงตาม Volume มากสุด"):
                if sort_mode == "vol_desc":
                    st.session_state["wl_sort_mode"] = "none"
                else:
                    st.session_state["wl_sort_mode"] = "vol_desc"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        raw_rows = [_normalize_row(r) for r in st.session_state.get("custom_watchlist", [])]
        rows = [r for r in raw_rows if get_sym_color_key(r[0]) == active] if active else raw_rows

        if not rows:
            st.caption("ไม่มีเหรียญในกลุ่มนี้")

        # เตรียมข้อมูลสำหรับแสดงผลและจัดเรียง
        display_rows = []
        for sym, p_val, c_val, is_up in rows:
            dot = get_sym_color_dot(sym)
            v_val = "-"
            c_num = 0.0
            v_num = 0.0

            live_data = _get_live_ticker(sym)
            if live_data:
                p_val, c_val, v_val, is_up, c_num, v_num = live_data
            elif norm_sym(sym) == norm_sym(selected_sym) and "df_data" in st.session_state:
                df_act = st.session_state.get("df_data")
                if df_act is not None and len(df_act) >= 2:
                    l_close = float(df_act["close"].iloc[-1])
                    l_open = float(df_act["open"].iloc[-1])
                    l_vol = float(df_act["volume"].iloc[-1]) if "volume" in df_act.columns else 0.0
                    pct = ((l_close - l_open) / l_open) * 100 if l_open != 0 else 0.0
                    p_val = f"{l_close:,.2f}" if l_close >= 1 else f"{l_close:.4f}"
                    c_val = f"{pct:+.2f}%"
                    v_val = _format_vol(l_vol)
                    is_up = (pct >= 0)
                    c_num = pct
                    v_num = l_vol

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

        # ดำเนินการจัดเรียงลำดับตามที่ผู้ใช้เลือก
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

        # กรอบคอนเทนเนอร์พร้อมเลื่อนด้วยเมาส์
        with st.container(height=480):
            for item in display_rows:
                sym = item["sym"]
                dot = item["dot"]
                c_val = item["c_val"]
                v_val = item["v_val"]
                is_up = item["is_up"]

                c1, c2, c3 = st.columns([1.15, 0.32, 1.53], gap="small", vertical_alignment="center")
                with c1:
                    btn_title = f"{dot} {sym}".strip()
                    if st.button(btn_title, key=f"wl_btn_{sym}", use_container_width=True):
                        set_active_symbol(sym)
                        st.rerun()
                with c2:
                    st.markdown('<div class="tv-neon-wrap">', unsafe_allow_html=True)
                    with st.popover("●", use_container_width=True, help=f"จัดการกลุ่มสี / ลบ {sym}"):
                        _color_menu(sym, prefix="wl")
                    st.markdown('</div>', unsafe_allow_html=True)
                with c3:
                    cls = "tv-val-up" if is_up else "tv-val-down"
                    st.markdown(
                        f'<div style="display:flex; justify-content:space-between; align-items:center; height:28px; width:100%; padding-left:4px;">'
                        f'<span class="{cls}">{c_val}</span>'
                        f'<span class="tv-vol-text">{v_val}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    # ──────────────────────────────────────────────────────────
    # -------------------------------------------------------------
    # แท็บที่ 2: กราฟเปรียบเทียบ (มีปุ่มตลาดข้าวเฉพาะแท็บนี้)
    # -------------------------------------------------------------
    # TAB 2: กราฟเปรียบเทียบ
    # -------------------------------------------------------------
    # แท็บที่ 2: กราฟเปรียบเทียบ (6 ปุ่มหมวด + 1 ปุ่มบทวิเคราะห์)
    # -------------------------------------------------------------
    else:
        st.markdown("<div style='font-size:11px; color:#00FFA3; margin-bottom:8px;'>⚡ หมวดหมู่เปรียบเทียบ</div>", unsafe_allow_html=True)
        
        # แถวที่ 1
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🌾 ตลาดข้าว", key="btn_rice_modal", use_container_width=True, type="secondary"):
                from ui import rice_seasonality_modal
                rice_seasonality_modal.show_rice_market_modal()
        with c2:
            if st.button("🪙 คริปโต", key="btn_crypto_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_crypto_modal()

        # แถวที่ 2
        c3, c4 = st.columns(2)
        with c3:
            if st.button("📈 หุ้น (GICS)", key="btn_stocks_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_stocks_gics_modal()
        with c4:
            if st.button("⛏️ แร่ & เหมือง", key="btn_metals_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_metals_mining_modal()

        # แถวที่ 3
        c5, c6 = st.columns(2)
        with c5:
            if st.button("💵 สกุลเงิน FX", key="btn_forex_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_forex_modal()
        with c6:
            if st.button("🌐 เทียบข้ามกลุ่ม", key="btn_macro_modal", use_container_width=True, type="secondary"):
                from ui import macro_comparison_modal
                macro_comparison_modal.show_macro_comparison_modal()

        # แถวที่ 4: ปุ่มบทวิเคราะห์กระแสเงินทุน
        st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
        if st.button("🧭 บทวิเคราะห์เงินทุนไหล (Capital Flow)", key="btn_flow_modal", use_container_width=True, type="primary"):
            from ui import macro_comparison_modal
            macro_comparison_modal.show_flow_analysis_modal()

    # -------------------------------------------------------------
    # แถบล่างสุด: ตั้งค่า + นาฬิกา (เคาะ 4 ช่อง อยู่นอก else เพื่อให้แสดงทั้ง 2 แท็บ)
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