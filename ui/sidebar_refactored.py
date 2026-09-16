import streamlit as st
import datetime

def set_active_symbol(sym_code: str):
    st.session_state["current_symbol"] = sym_code
    st.session_state["selected_symbol"] = sym_code
    if "open_tabs" in st.session_state and st.session_state.open_tabs:
        active_id = st.session_state.get("active_tab_id")
        for t in st.session_state.open_tabs:
            if t.get("id") == active_id:
                t["symbol"] = sym_code
                break
    for k in ("active_key", "df_data", "last_fetch_ts"):
        st.session_state.pop(k, None)

def render_sidebar():
    # Anchor สำหรับปุ่มสไลด์ซ้าย
    st.markdown('<div id="custom-left-menu-anchor" style="display:none;"></div>', unsafe_allow_html=True)

    if "sidebar_active_tab" not in st.session_state:
        st.session_state["sidebar_active_tab"] = "market"
    if "star_watchlists" not in st.session_state:
        st.session_state["star_watchlists"] = {
            "🔴 ดาวแดง": ["BTCUSDT"],
            "🟡 ดาวเหลือง": ["ETHUSDT"],
            "🟢 ดาวเขียว": ["DELTA.BK"],
            "🔵 ดาวฟ้า": ["SOLUSDT"],
            "🟣 ดาวม่วง": ["GC=F"]
        }

    # CSS แต่งการ์ดมืดและปุ่มสไตล์ TradingView ให้ตรงกับรูป
    st.markdown("""
    <style>
    .tv-tab-header {
        display: flex;
        border-bottom: 1px solid #2a2e39;
        margin-bottom: 10px;
    }
    .tv-tab-btn {
        flex: 1;
        text-align: center;
        padding: 6px 0;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
    }
    .tv-tab-orange {
        color: #FF7A1A;
        border-bottom: 2px solid #FF7A1A;
    }
    .tv-tab-green {
        color: #787b86;
    }
    .tv-card-deck {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-top: 6px;
    }
    .tv-card-row {
        background: #131722;
        border: 1px solid #2a2e39;
        border-radius: 6px;
        padding: 8px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .tv-card-row:hover {
        border-color: #FF7A1A;
    }
    .tv-card-sym {
        font-size: 13px;
        font-weight: 700;
        color: #ffffff;
    }
    .tv-card-price {
        font-size: 12px;
        color: #8b949e;
        font-family: monospace;
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
        # ขั้นที่ 1: เลือกระดับกลุ่มสินทรัพย์ (5 กลุ่ม)
        cat = st.selectbox(
            "1. กลุ่มสินทรัพย์",
            ["1. คริปโต (Crypto)", "2. หุ้น (Stock)", "3. ฟอเร็กซ์ (Forex)", "4. สินทรัพย์/โภคภัณฑ์", "5. ข้าว (Rice)"],
            label_visibility="collapsed",
            key="sb_asset_cat"
        )

        # ขั้นที่ 2: เลือกระดับกระดาน / ประเทศ
        symbol_map = {}
        if "คริปโต" in cat:
            sub = st.radio("กระดาน", ["Binance Spot", "Binance TH", "Bitkub"], horizontal=True, label_visibility="collapsed", key="sb_sub_cr")
            symbol_map = {
                "BTCUSDT": {"price": "79,036.15", "chg": "+2.27%", "up": True, "tag": "BINANCE"},
                "ETHUSDT": {"price": "2,645.80", "chg": "+3.14%", "up": True, "tag": "BINANCE"},
                "SOLUSDT": {"price": "184.25", "chg": "+5.42%", "up": True, "tag": "BINANCE"},
                "BNBUSDT": {"price": "588.50", "chg": "-0.85%", "up": False, "tag": "BINANCE"}
            }
        elif "หุ้น" in cat:
            sub = st.radio("ตลาด", ["หุ้นไทย (SET)", "หุ้นนอก (US)"], horizontal=True, label_visibility="collapsed", key="sb_sub_st")
            if "SET" in sub:
                symbol_map = {
                    "PTT.BK": {"price": "33.50", "chg": "+0.75%", "up": True, "tag": "SET"},
                    "DELTA.BK": {"price": "88.50", "chg": "+1.14%", "up": True, "tag": "SET"},
                    "AOT.BK": {"price": "61.25", "chg": "-0.40%", "up": False, "tag": "SET"}
                }
            else:
                symbol_map = {
                    "NVDA": {"price": "142.30", "chg": "-1.12%", "up": False, "tag": "NASDAQ"},
                    "AAPL": {"price": "228.10", "chg": "+0.45%", "up": True, "tag": "NASDAQ"}
                }
        elif "ฟอเร็กซ์" in cat:
            sub = st.radio("ประเภท", ["คู่เงินหลัก", "ดัชนีเงินบาท"], horizontal=True, label_visibility="collapsed", key="sb_sub_fx")
            symbol_map = {
                "EURUSD=X": {"price": "1.0845", "chg": "+0.15%", "up": True, "tag": "FX"},
                "USDTHB=X": {"price": "34.50", "chg": "+0.05%", "up": True, "tag": "FX"}
            }
        elif "โภคภัณฑ์" in cat:
            sub = st.radio("กลุ่ม", ["โลหะมีค่า (ทองคำ)", "พลังงาน (น้ำมัน)"], horizontal=True, label_visibility="collapsed", key="sb_sub_cm")
            symbol_map = {
                "GC=F": {"price": "2,684.50", "chg": "+0.45%", "up": True, "tag": "GOLD"},
                "CL=F": {"price": "71.30", "chg": "-1.05%", "up": False, "tag": "OIL"}
            }
        else:
            sub = st.radio("หมวดข้าว", ["ข้าวไทย", "ตลาดโลก (CBOT)"], horizontal=True, label_visibility="collapsed", key="sb_sub_rc")
            symbol_map = {
                "RICE:ข้าวเปลือกหอมมะลิ": {"price": "15,200", "chg": "+0.50%", "up": True, "tag": "RICE"},
                "ZR=F (CBOT Rough Rice)": {"price": "14.85", "chg": "+1.20%", "up": True, "tag": "CBOT"}
            }

        # ขั้นที่ 3: ช่องค้นหา + Badge สีส้ม
        sym_list = list(symbol_map.keys())
        active_sym = st.session_state.get("current_symbol", sym_list[0])
        def_idx = sym_list.index(active_sym) if active_sym in sym_list else 0

        c_s1, c_s2 = st.columns([3, 1])
        with c_s1:
            selected_sym = st.selectbox("เลือก", sym_list, index=def_idx, label_visibility="collapsed", key="sb_sym_box")
        with c_s2:
            if st.button("เลือก", use_container_width=True, key="btn_choose_sym"):
                set_active_symbol(selected_sym)
                st.rerun()

        # ขั้นที่ 4: กล่องแสดงเหรียญที่เลือก (Selected Asset Card) สไตล์ในรูป
        cur_info = symbol_map.get(selected_sym, {"price": "---", "chg": "+0.00%", "up": True, "tag": "MARKET"})
        p_badge = "tv-pill-green" if cur_info["up"] else "tv-pill-red"
        st.markdown(f"""
        <div style="background:#131722; border:1px solid #FF7A1A; border-radius:6px; padding:8px 12px; margin:6px 0; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="color:#ffffff; font-weight:700; font-size:14px;">🔍 {selected_sym}</span>
                    <span style="background:rgba(255,122,26,0.15); color:#FF7A1A; border:1px solid #FF7A1A; border-radius:4px; font-size:10px; padding:1px 5px; font-weight:bold;">{cur_info['tag']}</span>
                </div>
                <div style="color:#ffffff; font-size:15px; font-weight:800; margin-top:2px;">{cur_info['price']}</div>
            </div>
            <div>
                <span class="{p_badge}">{cur_info['chg']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ขั้นที่ 5: ติ๊กเลือกส่งไปที่กลุ่มสีโปรด
        st.caption("⭐ ส่งเข้ากลุ่มสีโปรด:")
        c_cols = st.columns(5)
        color_keys = ["🔴 ดาวแดง", "🟡 ดาวเหลือง", "🟢 ดาวเขียว", "🔵 ดาวฟ้า", "🟣 ดาวม่วง"]
        for idx, k_col in enumerate(color_keys):
            with c_cols[idx]:
                has_it = selected_sym in st.session_state["star_watchlists"].get(k_col, [])
                if st.button(f"✓" if has_it else k_col[0], key=f"fav_btn_{k_col}_{selected_sym}", use_container_width=True):
                    if has_it:
                        st.session_state["star_watchlists"][k_col].remove(selected_sym)
                    else:
                        st.session_state["star_watchlists"][k_col].append(selected_sym)
                    st.rerun()

        # รายการสินทรัพย์เฝ้าดู 7 ตัวเป๊ะตามรูปตัวอย่าง
        st.markdown("<div style='font-size:12px; color:#8b949e; margin:10px 0 4px 0;'>📋 รายการสินทรัพย์เฝ้าดู</div>", unsafe_allow_html=True)
        watchlist_presets = [
            ("BTCUSDT", "79,036.15", "+2.27%", True),
            ("ETHUSDT", "2,645.80", "+3.14%", True),
            ("SOLUSDT", "184.25", "+5.42%", True),
            ("BNBUSDT", "588.50", "-0.85%", False),
            ("GC=F", "2,684.50", "+0.45%", True),
            ("NVDA", "142.30", "-1.12%", False),
            ("PTT.BK", "33.50", "+0.75%", True)
        ]

        for sym, p_val, c_val, is_up in watchlist_presets:
            p_class = "tv-pill-green" if is_up else "tv-pill-red"
            c1, c2 = st.columns([2.2, 1.8])
            with c1:
                if st.button(sym, key=f"wl_btn_{sym}", use_container_width=True):
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