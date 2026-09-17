import streamlit as st
import datetime
from ui.symbol_modal import render_symbol_modal
from data.symbols import (
    get_full_binance_symbols,
    get_full_binance_th_symbols,
    get_full_bitkub_symbols,
    get_full_okx_symbols,
    get_full_bybit_symbols,
    get_full_gate_symbols,
    get_full_mexc_symbols,
    get_full_kucoin_symbols,
    get_full_commodities,
    get_full_forex,
    get_full_sp500_symbols,
    get_full_china_stocks,
    get_full_vietnam_symbols,
    _load_json
)
from data.fetchers import resolve_market_info

# นิยาม 5 กลุ่มสีหลัก
COLOR_TAGS = {
    "red": {"name": "แดง", "dot": "🔴", "hex": "#FF3366"},
    "green": {"name": "เขียว", "dot": "🟢", "hex": "#00FF66"},
    "orange": {"name": "ส้ม", "dot": "🟠", "hex": "#FF7A1A"},
    "blue": {"name": "ฟ้า", "dot": "🔵", "hex": "#00E5FF"},
    "white": {"name": "ขาว", "dot": "⚪", "hex": "#FFFFFF"},
}

def set_active_symbol(sym_code: str):
    st.session_state["current_symbol"] = sym_code
    st.session_state["selected_symbol"] = sym_code
    
    # ซิงค์กับ chart_tabs ของหน้าจอหลัก
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

    for k in ("active_key", "df_data", "last_fetch_ts"):
        st.session_state.pop(k, None)

def render_sidebar():
    # Anchor สำหรับ Workspace Resizers
    st.markdown('<div id="custom-left-menu-anchor" style="display:none;"></div>', unsafe_allow_html=True)

    if "sidebar_active_tab" not in st.session_state:
        st.session_state["sidebar_active_tab"] = "market"
        
    # ค่าเริ่มต้นสำหรับ 5 กลุ่มสี
    if "color_watchlists" not in st.session_state:
        st.session_state["color_watchlists"] = {
            "red": ["BTCUSDT"],
            "green": ["DELTA.BK"],
            "orange": ["ETHUSDT"],
            "blue": ["SOLUSDT"],
            "white": ["GC=F"]
        }
        
    if "active_color_filter" not in st.session_state:
        st.session_state["active_color_filter"] = "all"

    # CSS ตกแต่ง Cyberpunk UI
    st.markdown("""
    <style>
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

    # 1. แท็บคู่บน: ตลาด (ส้ม) | เครื่องมือ (เขียว)
    t_c1, t_c2 = st.columns(2)
    with t_c1:
        if st.button("ตลาด (ส้ม)", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "market" else "secondary"):
            st.session_state["sidebar_active_tab"] = "market"
            st.rerun()
    with t_c2:
        if st.button("เครื่องมือ (เขียว)", use_container_width=True, type="primary" if st.session_state["sidebar_active_tab"] == "tools" else "secondary"):
            st.session_state["sidebar_active_tab"] = "tools"
            st.rerun()

    # ══════════════════════════════════════════════════════
    # แท็บ 1: ตลาด (ส้ม)
    # ══════════════════════════════════════════════════════
    if st.session_state["sidebar_active_tab"] == "market":
        # เลือกระดับกลุ่มสินทรัพย์
        st.selectbox(
            "1. กลุ่มสินทรัพย์",
            ["1. คริปโต (Crypto)", "2. หุ้น (Stock)", "3. ฟอเร็กซ์ (Forex)", "4. สินทรัพย์/โภคภัณฑ์", "5. ข้าว (Rice)"],
            label_visibility="collapsed",
            key="sb_asset_cat"
        )

        selected_sym = st.session_state.get("current_symbol", "BTCUSDT")
        meta = resolve_market_info(selected_sym)
        tag = meta.get("exchange", "BINANCE")

        # 1. แถบค้นหาเหรียญแบบ Compact แถวเดียว (ตัดความซ้ำซ้อนออกทั้งหมด)
        if st.button(f"🔍 {selected_sym}   [{tag}]", key="btn_open_symbol_modal", use_container_width=True, type="secondary", help="คลิกเพื่อค้นหาและเปลี่ยนสินทรัพย์"):
            render_symbol_modal()

        # 2. แถบกรอง 5 กลุ่มสี (แดง, เขียว, ส้ม, ฟ้า, ขาว)
        st.markdown("<div style='font-size:11px; color:#8b949e; margin-top:8px; margin-bottom:4px;'>🏷️ กลุ่มสีโปรด (คลิกเพื่อกรอง):</div>", unsafe_allow_html=True)
        f_cols = st.columns([1.4, 1, 1, 1, 1, 1])
        cur_filter = st.session_state.get("active_color_filter", "all")
        
        with f_cols[0]:
            if st.button("ทั้งหมด", key="filter_all", use_container_width=True, type="primary" if cur_filter == "all" else "secondary"):
                st.session_state["active_color_filter"] = "all"
                st.rerun()
        with f_cols[1]:
            if st.button("🔴", key="filter_red", use_container_width=True, type="primary" if cur_filter == "red" else "secondary", help="กลุ่มสีแดง"):
                st.session_state["active_color_filter"] = "red"
                st.rerun()
        with f_cols[2]:
            if st.button("🟢", key="filter_green", use_container_width=True, type="primary" if cur_filter == "green" else "secondary", help="กลุ่มสีเขียว"):
                st.session_state["active_color_filter"] = "green"
                st.rerun()
        with f_cols[3]:
            if st.button("🟠", key="filter_orange", use_container_width=True, type="primary" if cur_filter == "orange" else "secondary", help="กลุ่มสีส้ม"):
                st.session_state["active_color_filter"] = "orange"
                st.rerun()
        with f_cols[4]:
            if st.button("🔵", key="filter_blue", use_container_width=True, type="primary" if cur_filter == "blue" else "secondary", help="กลุ่มสีฟ้า"):
                st.session_state["active_color_filter"] = "blue"
                st.rerun()
        with f_cols[5]:
            if st.button("⚪", key="filter_white", use_container_width=True, type="primary" if cur_filter == "white" else "secondary", help="กลุ่มสีขาว"):
                st.session_state["active_color_filter"] = "white"
                st.rerun()

        # 3. รายการสินทรัพย์เฝ้าดู (Watchlist)
        st.markdown("<div style='font-size:12px; color:#8b949e; margin:10px 0 4px 0;'>📋 รายการสินทรัพย์เฝ้าดู</div>", unsafe_allow_html=True)
        
        def get_sym_color_dot(sym):
            for c_key, c_info in COLOR_TAGS.items():
                if sym in st.session_state.get("color_watchlists", {}).get(c_key, []):
                    return c_info["dot"]
            return ""

        base_watchlist = [
            ("BTCUSDT", "79,036.15", "+2.27%", True),
            ("ETHUSDT", "2,645.80", "+3.14%", True),
            ("SOLUSDT", "184.25", "+5.42%", True),
            ("BNBUSDT", "588.50", "-0.85%", False),
            ("GC=F", "2,684.50", "+0.45%", True),
            ("NVDA", "142.30", "-1.12%", False),
            ("PTT.BK", "33.50", "+0.75%", True)
        ]

        # กรองรายการตามกลุ่มสีที่เลือก
        if cur_filter == "all":
            display_list = base_watchlist
        else:
            allowed_syms = set(st.session_state.get("color_watchlists", {}).get(cur_filter, []))
            display_list = [item for item in base_watchlist if item[0] in allowed_syms]
            # หากมีเหรียญอื่นถูกย้ายเข้ามา ให้ดึงมาแสดงด้วย
            for sym in allowed_syms:
                if not any(item[0] == sym for item in display_list):
                    display_list.append((sym, "--", "0.00%", True))

        if not display_list:
            st.caption(f"ไม่มีเหรียญในกลุ่ม {COLOR_TAGS.get(cur_filter, {}).get('name', '')}")

        for sym, p_val, c_val, is_up in display_list:
            p_class = "tv-pill-green" if is_up else "tv-pill-red"
            c_dot = get_sym_color_dot(sym)
            btn_title = f"{c_dot} {sym}".strip()

            c1, c2 = st.columns([2.2, 1.8])
            with c1:
                if st.button(btn_title, key=f"wl_btn_{sym}_{cur_filter}", use_container_width=True):
                    set_active_symbol(sym)
                    st.rerun()
            with c2:
                st.markdown(f"""
                <div style="text-align:right; margin-top:6px;">
                    <span style="color:#ffffff; font-size:12px; font-weight:bold; margin-right:4px;">{p_val}</span>
                    <span class="{p_class}">{c_val}</span>
                </div>
                """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # แท็บ 2: เครื่องมือ & อินดี้ (เขียว)
    # ══════════════════════════════════════════════════════
    else:
        st.markdown("<b style='font-size:12px; color:#00FF66;'>⚙️ พารามิเตอร์อินดิเคเตอร์</b>", unsafe_allow_html=True)
        with st.expander("📈 EMA Ribbon", expanded=True):
            st.slider("Fast", 5, 20, int(st.session_state.get("fast_ema", 7)), key="fast_ema_sb")
            st.slider("Slow", 10, 50, int(st.session_state.get("slow_ema", 13)), key="slow_ema_sb")
            st.slider("Trend", 30, 200, int(st.session_state.get("trend_ema", 45)), key="trend_ema_sb")

    # ฟังก์ชันด่วน 4 ปุ่ม (📐, 📊, 🌾, 🟣)
    st.markdown("<hr style='margin: 10px 0 6px 0; border: 0.5px solid #2a2e39;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px; color:#00FFA3; margin-bottom:4px;'>⚡ ฟังก์ชันด่วน (Hover Tooltips)</div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("📐", help="Fibonacci", use_container_width=True):
            st.session_state["trigger_fib_modal"] = True
            st.rerun()
    with q2:
        if st.button("📊", help="สถิติตลาด 24 ชม.", use_container_width=True):
            st.session_state["trigger_market_modal"] = True
            st.rerun()
    with q3:
        if st.button("🌾", help="รายงานราคาข้าว", use_container_width=True):
            from ui.rice_tab import show_rice_dialog_modal
            show_rice_dialog_modal()
    with q4:
        if st.button("🟣", help="การตั้งค่าสีกราฟ", use_container_width=True):
            st.session_state["trigger_settings_modal"] = True
            st.rerun()

    # สวิตช์ ON แถบวาดรูป & แถบควบคุมบน
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        draw_on = st.checkbox("✏️ แถบวาดรูป (Draw)", value=st.session_state.get("show_draw_toolbar", True), key="sb_chk_draw")
        st.session_state["show_draw_toolbar"] = draw_on
    with s_col2:
        top_on = st.checkbox("💻 แถบควบคุมบน (Top)", value=st.session_state.get("show_top_bar", True), key="sb_chk_top")
        st.session_state["show_top_bar"] = top_on

    # นาฬิกา BKK LIVE
    now_bkk = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    st.markdown(f"""
    <div style="margin-top:10px; padding:6px 10px; background:#131722; border:1px solid #2a2e39; border-radius:6px; font-size:11px; color:#00FF66; display:flex; justify-content:space-between; align-items:center;">
        <span>🕒 BKK {now_bkk.strftime('%H:%M:%S')}</span>
        <span class="tv-quick-badge-on">LIVE</span>
    </div>
    """, unsafe_allow_html=True)

    return {"show_top_bar": top_on, "show_draw_toolbar": draw_on}