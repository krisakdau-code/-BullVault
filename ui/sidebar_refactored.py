import streamlit as st
import datetime
from ui.symbol_modal import render_symbol_modal
from data.fetchers import resolve_market_info
from color_store import (
    COLOR_TAGS, COLOR_KEYS, norm_sym,
    ensure_color_state, assign_color, get_sym_color_key, get_sym_color_dot
)

# ══════════════════════════════════════════════════════════════
# 1. กล่องโมดอลศูนย์ตั้งค่ารวม 4 แท็บ (Unified Settings Dialog)
# ══════════════════════════════════════════════════════════════
@st.dialog("⚙️ การตั้งค่าระบบและชาร์ต (Unified Settings)")
def show_chart_settings_dialog():
    tab_chart, tab_main_ind, tab_sub_ind, tab_ui = st.tabs([
        "🎨 กราฟ & ธีม", 
        "📈 อินดิเคเตอร์หลัก", 
        "📉 RSI & MACD", 
        "🖥️ พื้นที่ทำงาน"
    ])

    # ──────────────────────────────────────────────────────────
    # แท็บ 1: สีกราฟและแท่งเทียน
    # ──────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────
    # แท็บ 2: อินดิเคเตอร์หลักบนกราฟ (EMA & Volume)
    # ──────────────────────────────────────────────────────────
    with tab_main_ind:
        st.caption("📈 EMA Ribbon")
        st.session_state["show_ema"] = st.toggle("เปิดใช้งาน EMA Ribbon", value=st.session_state.get("show_ema", True))
        
        e1, e2, e3 = st.columns(3)
        with e1:
            st.session_state["fast_ema"] = st.number_input(
                "Fast EMA", min_value=1, max_value=50, value=int(st.session_state.get("fast_ema", 7))
            )
        with e2:
            st.session_state["slow_ema"] = st.number_input(
                "Slow EMA", min_value=5, max_value=100, value=int(st.session_state.get("slow_ema", 13))
            )
        with e3:
            st.session_state["trend_ema"] = st.number_input(
                "Trend EMA", min_value=20, max_value=300, value=int(st.session_state.get("trend_ema", 45))
            )

        st.divider()
        st.caption("📊 ปริมาณการซื้อขาย (Volume)")
        st.session_state["show_volume"] = st.toggle("แสดง Volume แท่งล่าง", value=st.session_state.get("show_volume", True))

    # ──────────────────────────────────────────────────────────
    # แท็บ 3: อินดิเคเตอร์ย่อยด้านล่าง (RSI & MACD)
    # ──────────────────────────────────────────────────────────
    with tab_sub_ind:
        st.caption("📉 RSI Settings")
        st.session_state["show_rsi"] = st.toggle("แสดง RSI Pane", value=st.session_state.get("show_rsi", True))
        r1, r2, r3 = st.columns(3)
        with r1:
            st.session_state["rsi_length"] = st.number_input("RSI Length", min_value=2, max_value=50, value=int(st.session_state.get("rsi_length", 14)))
        with r2:
            st.session_state["rsi_ob"] = st.number_input("Overbought", min_value=50, max_value=95, value=int(st.session_state.get("rsi_ob", 70)))
        with r3:
            st.session_state["rsi_os"] = st.number_input("Oversold", min_value=5, max_value=50, value=int(st.session_state.get("rsi_os", 30)))

        st.divider()
        st.caption("📊 MACD Settings")
        st.session_state["show_macd"] = st.toggle("แสดง MACD Pane", value=st.session_state.get("show_macd", True))
        m1, m2, m3 = st.columns(3)
        with m1:
            st.session_state["macd_fast"] = st.number_input("Fast Period", min_value=2, max_value=50, value=int(st.session_state.get("macd_fast", 12)))
        with m2:
            st.session_state["macd_slow"] = st.number_input("Slow Period", min_value=5, max_value=100, value=int(st.session_state.get("macd_slow", 26)))
        with m3:
            st.session_state["macd_signal"] = st.number_input("Signal Period", min_value=1, max_value=50, value=int(st.session_state.get("macd_signal", 9)))

    # ──────────────────────────────────────────────────────────
    # แท็บ 4: สวิตช์เปิด-ปิดแถบควบคุม (Workspace UI)
    # ──────────────────────────────────────────────────────────
    with tab_ui:
        st.caption("🖥️ ควบคุมการแสดงผลแถบเครื่องมือ")
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
            # รีเซ็ตค่าทั้งหมด
            st.session_state["candle_up_color"] = "#089981"
            st.session_state["candle_down_color"] = "#F23645"
            st.session_state["chart_bg_color"] = "#131722"
            st.session_state["chart_grid_color"] = "#1e222d"
            st.session_state["show_ema"] = True
            st.session_state["fast_ema"] = 7
            st.session_state["slow_ema"] = 13
            st.session_state["trend_ema"] = 45
            st.session_state["show_volume"] = True
            st.session_state["show_rsi"] = True
            st.session_state["rsi_length"] = 14
            st.session_state["rsi_ob"] = 70
            st.session_state["rsi_os"] = 30
            st.session_state["show_macd"] = True
            st.session_state["macd_fast"] = 12
            st.session_state["macd_slow"] = 26
            st.session_state["macd_signal"] = 9
            st.session_state["show_draw_toolbar"] = True
            st.session_state["show_top_bar"] = True
            try:
                st.rerun(scope="app")
            except TypeError:
                st.rerun()
    with b2:
        if st.button("💾 บันทึกและปรับใช้", type="primary", use_container_width=True):
            try:
                st.rerun(scope="app")
            except TypeError:
                st.rerun()


# ══════════════════════════════════════════════════════════════
# 2. ฟังก์ชันเสริมการจัดการข้อมูล
# ══════════════════════════════════════════════════════════════
def set_active_symbol(sym_code: str):
    sym_code = norm_sym(sym_code)
    st.session_state["current_symbol"] = sym_code
    st.session_state["selected_symbol"] = sym_code
    
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

def _color_menu(sym: str) -> None:
    s = norm_sym(sym)
    current = get_sym_color_key(s)
    st.caption(f"กลุ่มสีของ {s}")
    for ckey, cinfo in COLOR_TAGS.items():
        mark = " ✓" if ckey == current else ""
        if st.button(f"{cinfo['dot']} {cinfo['label']}{mark}", key=f"clr_{s}_{ckey}", use_container_width=True):
            assign_color(s, None if ckey == current else ckey)
            st.rerun()

    st.divider()
    if st.button("✖ ปลดกลุ่มสี", key=f"clr_{s}_none", use_container_width=True, disabled=(current is None)):
        assign_color(s, None)
        st.rerun()
    if st.button("🗑️ ลบจาก Watchlist", key=f"clr_{s}_del", use_container_width=True):
        assign_color(s, None)
        if "custom_watchlist" in st.session_state:
            st.session_state["custom_watchlist"] = [
                item for item in st.session_state["custom_watchlist"]
                if norm_sym(item[0] if isinstance(item, (list, tuple)) else item) != s
            ]
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

    if "sidebar_active_tab" not in st.session_state:
        st.session_state["sidebar_active_tab"] = "market"
    if "color_filter" not in st.session_state:
        st.session_state["color_filter"] = None
    if "custom_watchlist" not in st.session_state:
        st.session_state["custom_watchlist"] = []

    st.markdown("""
    <style>
    section[data-testid="stSidebar"] div[data-testid="stPopover"] button {
        padding: 0.15rem 0.2rem !important;
        min-height: 26px !important;
        height: 26px !important;
        border: 1px solid #2a2e39 !important;
        background: transparent !important;
        color: #787b86 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stPopover"] button:hover {
        color: #ff7d1e !important;
        border-color: #ff7d1e !important;
    }
    .tv-pill-green {
        background: rgba(8, 153, 129, 0.2);
        color: #089981;
        border: 1px solid #089981;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .tv-pill-red {
        background: rgba(242, 54, 69, 0.2);
        color: #F23645;
        border: 1px solid #F23645;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
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

    # ปุ่มสลับแท็บหลัก: ตลาด (ส้ม) | เครื่องมือ (เขียว)
    t_c1, t_c2 = st.columns(2)
    with t_c1:
        if st.button("ตลาด (ส้ม)", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "market" else "secondary"):
            st.session_state["sidebar_active_tab"] = "market"
            st.rerun()
    with t_c2:
        if st.button("เครื่องมือ (เขียว)", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "tools" else "secondary"):
            st.session_state["sidebar_active_tab"] = "tools"
            st.rerun()

    # ──────────────────────────────────────────────────────────
    # TAB 1: ตลาด (แสดง Watchlist เต็มพื้นที่)
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

        if st.button(f"🔍 {selected_sym}   [{tag}]", key="btn_open_symbol_modal", use_container_width=True, type="secondary"):
            render_symbol_modal()

        # แถบกรอง 5 สีแบบ Ghost Buttons
        st.markdown("<div style='font-size:11px; color:#8b949e; margin-top:8px; margin-bottom:4px;'>🏷️ กลุ่มสีโปรด (คลิกเพื่อกรอง):</div>", unsafe_allow_html=True)
        f_cols = st.columns([1.2, 1, 1, 1, 1, 1])
        active = st.session_state.get("color_filter")

        with f_cols[0]:
            if st.button("ALL" if active else "⭐", key="cf_all", use_container_width=True, type="primary" if active is None else "tertiary"):
                st.session_state["color_filter"] = None
                st.rerun()

        for i, ckey in enumerate(COLOR_KEYS):
            with f_cols[i + 1]:
                btn_type = "primary" if active == ckey else "tertiary"
                if st.button(COLOR_TAGS[ckey]["dot"], key=f"cf_{ckey}", use_container_width=True, type=btn_type):
                    st.session_state["color_filter"] = None if active == ckey else ckey
                    st.rerun()

        st.markdown("<div style='font-size:12px; color:#8b949e; margin:10px 0 4px 0;'>📋 รายการสินทรัพย์เฝ้าดู</div>", unsafe_allow_html=True)
        raw_rows = [_normalize_row(r) for r in st.session_state.get("custom_watchlist", [])]
        rows = [r for r in raw_rows if get_sym_color_key(r[0]) == active] if active else raw_rows

        if not rows:
            st.caption("ไม่มีเหรียญในกลุ่มนี้")

        for sym, p_val, c_val, is_up in rows:
            dot = get_sym_color_dot(sym)
            c1, c2, c3 = st.columns([1.9, 1.7, 0.4], vertical_alignment="center")
            with c1:
                if st.button(f"{dot} {sym}".strip(), key=f"wl_btn_{sym}", use_container_width=True):
                    set_active_symbol(sym)
                    try:
                        st.rerun(scope="app")
                    except TypeError:
                        st.rerun()
            with c2:
                cls = "tv-pill-green" if is_up else "tv-pill-red"
                st.markdown(f'<div style="text-align:right;"><span style="color:#eaecef;font-size:12px;font-weight:700;margin-right:4px;">{p_val}</span><span class="{cls}">{c_val}</span></div>', unsafe_allow_html=True)
            with c3:
                with st.popover("⋮", use_container_width=True):
                    _color_menu(sym)

    # ──────────────────────────────────────────────────────────
    # TAB 2: เครื่องมือ (Control Center สะอาดตา)
    # ──────────────────────────────────────────────────────────
    else:
        st.markdown("<div style='font-size:11px; color:#00FFA3; margin-bottom:8px;'>⚡ เมนูควบคุมหลัก</div>", unsafe_allow_html=True)
        act1, act2 = st.columns(2)
        with act1:
            if st.button("🌾 ตลาดข้าว", key="btn_rice_modal", use_container_width=True, type="secondary"):
                from ui.rice_tab import show_rice_dialog_modal
                show_rice_dialog_modal()
        with act2:
            if st.button("⚙️ ตั้งค่ากราฟ", key="btn_chart_settings", use_container_width=True, type="secondary"):
                show_chart_settings_dialog()

        st.markdown("<hr style='margin: 16px 0 12px 0; border: 0.5px solid #2a2e39;'>", unsafe_allow_html=True)

        # นาฬิกา BKK LIVE
        now_bkk = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
        st.markdown(f"""
        <div style="padding:8px 12px; background:#131722; border:1px solid #2a2e39; border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#eaecef; font-size:12px; font-weight:600;">🕒 BKK {now_bkk.strftime('%H:%M:%S')}</span>
            <span class="tv-quick-badge-on">LIVE</span>
        </div>
        """, unsafe_allow_html=True)

    return {
        "show_top_bar": st.session_state.get("show_top_bar", True),
        "show_draw_toolbar": st.session_state.get("show_draw_toolbar", True)
    }