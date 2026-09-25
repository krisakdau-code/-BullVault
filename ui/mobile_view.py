# ui/mobile_view.py — Dedicated Mobile View (TradingView Mobile Style)
import streamlit as st
from ui.right_panel import render_right_panel
from ui.indicator_modal import show_indicators_modal

def render_mobile_view(df, meta, is_thb_mode: bool, fx_rate: float, chart_renderer=None, watchlist_renderer=None):
    """
    หน้าจอโหมดมือถือสไตล์ TradingView Mobile:
    1. เมนูล่างสุด (Bottom Navigation Bar) บรรทัดเดียว 6 ปุ่ม: [📋ลิสต์] [📈กราฟ] [📊สรุป] [✏️วาด] [⚙️อินดิ] [💻คอม]
    2. ปุ่มสลับเหรียญด่วน (Quick Symbol Switcher) ป๊อปอัปสลับเหรียญในคลิกเดียว
    3. ซ่อนส่วนหัวเดิมด้านบน 100% คืนพื้นที่ให้กราฟชิดขอบจอ
    4. แก้ปัญหาส่วนหัวชาร์ตและปุ่มคำสั่งทับซ้อนกัน (วงสีเหลือง)
    """
    if "mobile_nav_view" not in st.session_state:
        st.session_state["mobile_nav_view"] = "chart"
    if "show_draw_toolbar" not in st.session_state:
        st.session_state["show_draw_toolbar"] = False

    active_view = st.session_state["mobile_nav_view"]

    # -------------------------------------------------------------------------
    # CSS จัดหน้าจอมือถือ: ล็อกแถบล่าง ตรึงกราฟ ซ่อนหัวเดิม และแก้จุดทับซ้อน
    # -------------------------------------------------------------------------
    st.markdown("""
    <style>
        /* 1. ซ่อนส่วนหัวเดิมของ Desktop ด้านบนทั้งหมด */
        div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) { display: none !important; height: 0px !important; margin: 0 !important; }
        #toggle-btn-anchor { display: none !important; }
        div[data-testid="stColumn"]:has(div[role="radiogroup"]) { display: none !important; }
        div[data-testid="stColumn"]:has(#btn_open_ind_modal),
        div[data-testid="stColumn"]:has(button[key="btn_open_ind_modal"]) { display: none !important; }
        div[data-testid="stColumn"]:has(button[key="btn_toggle_draw_desktop"]) { display: none !important; }
        div[data-testid="stColumn"]:has(div[data-testid="stToggle"]) { display: none !important; }

        /* 2. ดันพื้นที่ทำงานขึ้นชิดขอบบน และเว้นขอบล่าง 60px สำหรับแถบเมนูล่าง */
        .block-container {
            padding-top: 6px !important;
            padding-bottom: 65px !important;
            margin-top: 0px !important;
            max-width: 100% !important;
        }

        /* 3. แถบควบคุมชาร์ตด้านบน (ปุ่มสลับเหรียญด่วน + Timeframe) */
        .mobile-quick-bar {
            margin-bottom: 4px !important;
        }
        .mobile-quick-bar div[data-testid="stPopover"] > button {
            height: 32px !important;
            background: #11141c !important;
            border: 1px solid #2a2e39 !important;
            color: #00e676 !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            border-radius: 6px !important;
        }
        .mobile-quick-bar div[data-baseweb="select"] > div {
            min-height: 32px !important;
            height: 32px !important;
            border-radius: 6px !important;
            background-color: #11141c !important;
            border-color: #2a2e39 !important;
            font-size: 12px !important;
        }

        /* 4. แก้ปัญหาข้อความและปุ่มทับซ้อนบนหัวชาร์ต (วงสีเหลือง) */
        div[data-testid="stCustomComponentV1"], iframe {
            width: 100% !important;
            max-width: 100% !important;
        }

        /* 5. ตรึงแถบเมนู 6 ปุ่มไว้ล่างสุดของหน้าจอมือถือ (Fixed Bottom Bar บรรทัดเดียวจบ) */
        div[data-testid="stHorizontalBlock"]:has(#mobile-bottom-nav-marker) {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100vw !important;
            background: #090b10 !important;
            border-top: 1px solid #1e2433 !important;
            z-index: 9999999 !important;
            padding: 5px 4px 8px 4px !important;
            margin: 0 !important;
            box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.85) !important;
            display: flex !important;
            flex-direction: row !important;
            gap: 3px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(#mobile-bottom-nav-marker) > div[data-testid="column"] {
            flex: 1 1 0px !important;
            min-width: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(#mobile-bottom-nav-marker) button {
            height: 36px !important;
            min-height: 36px !important;
            padding: 0 1px !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            border: 1px solid #1e2433 !important;
            background: #11141c !important;
            color: #8b949e !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            white-space: nowrap !important;
        }
        div[data-testid="stHorizontalBlock"]:has(#mobile-bottom-nav-marker) button[kind="primary"],
        div[data-testid="stHorizontalBlock"]:has(#mobile-bottom-nav-marker) button[data-testid="baseButton-primary"] {
            background: rgba(0, 230, 118, 0.15) !important;
            color: #00e676 !important;
            border: 1.5px solid #00e676 !important;
            box-shadow: 0 0 8px rgba(0, 230, 118, 0.35) !important;
        }

        /* 6. แนวนอน (Landscape): กราฟเต็มจอ 100% อัตโนมัติ ซ่อนแถบล่าง */
        @media (orientation: landscape) and (max-height: 580px) {
            div[data-testid="stHorizontalBlock"]:has(#mobile-bottom-nav-marker),
            .mobile-quick-bar {
                display: none !important;
            }
            .block-container {
                padding: 0 !important;
                margin: 0 !important;
            }
            div[data-testid="stCustomComponentV1"], iframe {
                height: 98vh !important;
                max-height: 98vh !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # การแสดงผลเนื้อหาหลักตามปุ่มที่เลือก (ชาร์ตกราฟ / รายชื่อเฝ้าดู / วิเคราะห์)
    # -------------------------------------------------------------------------
    if active_view == "chart":
        symbol = meta.get("symbol", st.session_state.get("current_symbol", "BTCUSDT"))
        disp_name = meta.get("display_name", symbol)
        cur_tf = st.session_state.get("selected_tf", "1h")

        # แถบด้านบนของชาร์ต: [ปุ่มสลับเหรียญด่วนแบบ Popover] คู่กับ [ช่องเลือก TF]
        st.markdown('<div class="mobile-quick-bar">', unsafe_allow_html=True)
        c_q_sym, c_q_tf = st.columns([2.0, 1.1], gap="small")

        with c_q_sym:
            with st.popover(f"💎 {disp_name} ▾", use_container_width=True):
                st.caption("🔍 ค้นหา / แตะเปลี่ยนเหรียญด่วน")
                q_search = st.text_input("ค้นหาชื่อเหรียญ...", key="m_quick_sym_search").strip().upper()
                quick_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT", "PEPEUSDT", "SUIUSDT"]
                if q_search:
                    quick_symbols = [s for s in quick_symbols if q_search in s] or [q_search]

                for s in quick_symbols[:8]:
                    if st.button(f"🔸 {s}", key=f"btn_quick_{s}", use_container_width=True):
                        st.session_state["current_symbol"] = s
                        st.session_state["selected_symbol"] = s
                        tabs = st.session_state.get("chart_tabs", [])
                        active_id = st.session_state.get("active_tab_id")
                        for t in tabs:
                            if t["id"] == active_id:
                                t["symbol"] = s
                        try:
                            st.rerun(scope="app")
                        except TypeError:
                            st.rerun()

        with c_q_tf:
            tf_options = ["5m", "15m", "30m", "1h", "2h", "4h", "D", "W"]
            selected_m_tf = st.selectbox(
                "TF",
                options=tf_options,
                index=tf_options.index(cur_tf) if cur_tf in tf_options else 3,
                key="m_quick_tf_selector",
                label_visibility="collapsed"
            )
            if selected_m_tf != cur_tf:
                st.session_state["selected_tf"] = selected_m_tf
                tabs = st.session_state.get("chart_tabs", [])
                active_id = st.session_state.get("active_tab_id")
                for t in tabs:
                    if t["id"] == active_id:
                        t["tf"] = selected_m_tf
                try:
                    st.rerun(scope="app")
                except TypeError:
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        if chart_renderer:
            chart_renderer()
        else:
            st.info("กำลังโหลดกราฟ...")

    elif active_view == "watchlist":
        if watchlist_renderer:
            watchlist_renderer()
        else:
            st.info("กำลังโหลดรายการเหรียญ...")

    elif active_view == "overview":
        render_right_panel(df=df, meta=meta, is_thb_mode=is_thb_mode, fx_rate=fx_rate)

    # เปิด Modal Indicators หากมีการกดเรียก
    if st.session_state.get("modal_indicators_open", False):
        show_indicators_modal()

    # -------------------------------------------------------------------------
    # แถบเมนูล่างสุด (Bottom Navigation Bar) บรรทัดเดียวจบ 6 ปุ่ม
    # -------------------------------------------------------------------------
    st.markdown('<div id="mobile-bottom-nav-marker"></div>', unsafe_allow_html=True)
    nb1, nb2, nb3, nb4, nb5, nb6 = st.columns(6, gap="small")

    with nb1:
        if st.button("📋ลิสต์", type="primary" if active_view == "watchlist" else "secondary", key="nav_btn_watch", use_container_width=True):
            st.session_state["mobile_nav_view"] = "watchlist"
            st.rerun()

    with nb2:
        if st.button("📈กราฟ", type="primary" if active_view == "chart" else "secondary", key="nav_btn_chart", use_container_width=True):
            st.session_state["mobile_nav_view"] = "chart"
            st.rerun()

    with nb3:
        if st.button("📊สรุป", type="primary" if active_view == "overview" else "secondary", key="nav_btn_overview", use_container_width=True):
            st.session_state["mobile_nav_view"] = "overview"
            st.rerun()

    with nb4:
        is_draw = st.session_state.get("show_draw_toolbar", False)
        if st.button("✏️วาด", type="primary" if is_draw else "secondary", key="nav_btn_draw", use_container_width=True):
            st.session_state["show_draw_toolbar"] = not is_draw
            st.rerun()

    with nb5:
        if st.button("⚙️อินดิ", type="secondary", key="nav_btn_ind", use_container_width=True):
            st.session_state["modal_indicators_open"] = True
            st.rerun()

    with nb6:
        if st.button("💻คอม", type="secondary", key="nav_btn_desktop", use_container_width=True):
            st.session_state["mobile_mode"] = False
            st.rerun()