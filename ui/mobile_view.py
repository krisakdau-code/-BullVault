# ui/mobile_view.py — TradingView Mobile Standard
import os, json
import streamlit as st
import streamlit.components.v1 as components
from ui.symbol_modal import render_symbol_modal
from ui.indicator_modal import show_indicators_modal

PRIMARY_TFS = ["5m", "15m", "30m", "1h", "2h", "3h", "4h", "D", "2D", "3D", "W", "M"]
COLOR_TABS = [
    ("⭐", "star", ["star", "yellow", "fav"]),
    ("🔴", "red", ["red"]),
    ("🟠", "orange", ["orange"]),
    ("🟢", "green", ["green"]),
    ("🔵", "blue", ["blue"]),
    ("⚪", "white", ["white", "gray"])
]

def render_mobile_view(df, meta, is_thb_mode, fx_rate, chart_renderer, watchlist_renderer):
    if "mobile_tab" not in st.session_state:
        st.session_state["mobile_tab"] = "chart"

    cur_tab = st.session_state["mobile_tab"]
    cur_sym = st.session_state.get("current_symbol", "BTCUSDT")
    cur_tf = st.session_state.get("selected_tf", "1h")

    # =========================================================================
    # 1. CSS จัดระเบียบโครงสร้าง Mobile ตามรูปที่ 2
    # =========================================================================
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2px !important;
            padding-bottom: 94px !important;
            padding-left: 4px !important;
            padding-right: 4px !important;
        }

        /* ซ่อนปุ่ม ☰ มุมซ้ายบน */
        #toggle-btn-anchor, #floating-toggle-btn, .floating-toggle,
        div:has(> #toggle-btn-anchor), div:has(> #floating-toggle-btn),
        div[data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }

        /* ล็อกแถวปุ่ม 6 สี ให้เรียงแนวนอน 1 แถวเสมอ */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 4px !important;
            width: 100% !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            min-width: 0 !important;
            flex: 1 1 0px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(6)) button {
            height: 34px !important;
            min-height: 34px !important;
            padding: 0 !important;
            font-size: 15px !important;
            width: 100% !important;
        }

        /* กรอบแสดงรายการเหรียญ */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            height: auto !important;
            min-height: 48px !important;
            max-height: 56vh !important;
            overflow-y: auto !important;
            background: #090b10 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            padding: 4px !important;
        }

        /* ตรึงแถบควบคุม 4 ปุ่ม ไว้เหนือแถบล่าง 6 ปุ่ม พอดีเป๊ะ */
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) {
            position: fixed !important;
            bottom: 52px !important;
            left: 0px !important;
            right: 0px !important;
            width: 100vw !important;
            height: 38px !important;
            background: #090b10 !important;
            border-top: 1px solid #1e2433 !important;
            z-index: 9999998 !important;
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: space-between !important;
            padding: 0 4px !important;
            margin: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) > div[data-testid="stColumn"] {
            min-width: 0 !important;
            width: auto !important;
            flex: 1 1 auto !important;
            padding: 0 2px !important;
            margin: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) > div:last-child {
            flex: 0 0 38px !important;
            width: 38px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) button,
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) div[data-testid="stPopover"] > button {
            height: 30px !important;
            min-height: 30px !important;
            font-size: 11.5px !important;
            font-weight: 600 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #d1d4dc !important;
            padding: 0 4px !important;
            border-radius: 4px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) button:hover,
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) div[data-testid="stPopover"] > button:hover {
            background: rgba(255, 255, 255, 0.06) !important;
            color: #ff9d42 !important;
        }

        /* แถบนำทางด้านล่าง 6 ปุ่ม */
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) {
            position: fixed !important;
            bottom: 0px !important;
            left: 0px !important;
            right: 0px !important;
            width: 100vw !important;
            height: 52px !important;
            background: #090b10 !important;
            border-top: 1px solid #1e2433 !important;
            z-index: 9999999 !important;
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            justify-content: space-around !important;
            align-items: center !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) > div {
            flex: 1 1 16.666% !important;
            width: 16.666% !important;
            min-width: 0 !important;
            max-width: 16.666% !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) div[data-testid="stElementContainer"] {
            width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            height: 50px !important;
            min-height: 50px !important;
            padding: 2px 0 !important;
            margin: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button p {
            font-size: 10px !important;
            line-height: 1.2 !important;
            color: #8b949e !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: center !important;
            white-space: pre-wrap !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button:hover p {
            color: #ff9d42 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button[kind="primary"] p,
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button[data-testid="baseButton-primary"] p {
            color: #ff7d1e !important;
            font-weight: 700 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # สคริปต์ JavaScript จัดการปุ่มตั้งค่า (วงสีเขียว) และนาฬิกา BKK (วงสีแดง) ให้สมส่วน
    components.html("""
    <script>
    (function() {
        const d = window.parent.document;
        setInterval(() => {
            d.querySelectorAll('#toggle-btn-anchor, #floating-toggle-btn').forEach(e => e.style.setProperty('display', 'none', 'important'));

            // จัดการวงสีเขียว (ปุ่มตั้งค่า) และวงสีแดง (นาฬิกา BKK LIVE)
            d.querySelectorAll('button').forEach(btn => {
                if (btn.innerText && btn.innerText.includes('ตั้งค่า')) {
                    // วงสีเขียว: ขนาดเล็กลง และโปร่งแสง
                    btn.style.setProperty('background', 'rgba(255, 255, 255, 0.08)', 'important');
                    btn.style.setProperty('border', '1px solid rgba(255, 255, 255, 0.16)', 'important');
                    btn.style.setProperty('color', '#a0aec0', 'important');
                    btn.style.setProperty('height', '30px', 'important');
                    btn.style.setProperty('min-height', '30px', 'important');
                    btn.style.setProperty('padding', '0 10px', 'important');
                    btn.style.setProperty('font-size', '11.5px', 'important');
                    btn.style.setProperty('border-radius', '6px', 'important');
                    btn.style.setProperty('width', 'auto', 'important');
                    btn.style.setProperty('box-shadow', 'none', 'important');

                    // วงสีแดง: นาฬิกา BKK LIVE ดึงเข้าแถวเดียวกันชิดขวา ไม่ตกขอบ
                    const row = btn.closest('[data-testid="stHorizontalBlock"]');
                    if (row) {
                        row.style.setProperty('display', 'flex', 'important');
                        row.style.setProperty('flex-direction', 'row', 'important');
                        row.style.setProperty('flex-wrap', 'nowrap', 'important');
                        row.style.setProperty('align-items', 'center', 'important');
                        row.style.setProperty('justify-content', 'space-between', 'important');
                        row.style.setProperty('width', '100%', 'important');
                        row.style.setProperty('box-sizing', 'border-box', 'important');
                        row.style.setProperty('padding', '2px 4px', 'important');
                        row.style.setProperty('margin-top', '4px', 'important');

                        const cols = row.querySelectorAll(':scope > div[data-testid="column"], :scope > div[data-testid="stColumn"]');
                        if (cols.length >= 2) {
                            cols[0].style.setProperty('flex', '0 0 auto', 'important');
                            cols[0].style.setProperty('width', 'auto', 'important');

                            cols[1].style.setProperty('flex', '0 0 auto', 'important');
                            cols[1].style.setProperty('width', 'auto', 'important');
                            cols[1].style.setProperty('margin-left', 'auto', 'important');
                            cols[1].style.setProperty('display', 'flex', 'important');
                            cols[1].style.setProperty('justify-content', 'flex-end', 'important');
                        }
                    }
                }
            });
        }, 150);
    })();
    </script>
    """, height=0, width=0)

    # =========================================================================
    # 2. พื้นที่แสดงผลหลัก
    # =========================================================================
    if cur_tab == "list":
        watchlist_renderer()

    elif cur_tab == "summary":
        from ui.right_panel import render_right_panel
        render_right_panel(df=df, meta=meta, is_thb_mode=is_thb_mode, fx_rate=fx_rate)

    else:
        chart_renderer()

        # แถบควบคุม 4 ปุ่ม ใต้กราฟ
        c_sym, c_tf, c_clr, c_fs = st.columns([1.3, 1.1, 0.9, 0.5], gap="small")

        with c_sym:
            st.markdown('<div class="subchart-marker" style="display:none;"></div>', unsafe_allow_html=True)
            with st.popover(f"🔍 {cur_sym} ▾", use_container_width=True):
                st.markdown("<div style='font-size:12px; font-weight:700; color:#ff7d1e; margin-bottom:6px;'>⚡ เลือกกลุ่มดาว / สี</div>", unsafe_allow_html=True)

                cur_col = st.session_state.get("mobile_quick_col", "star")
                c_cols = st.columns(6)
                for idx, (emoji, key, _) in enumerate(COLOR_TABS):
                    with c_cols[idx]:
                        if st.button(emoji, key=f"mq_col_{key}"):
                            st.session_state["mobile_quick_col"] = key
                            st.rerun()

                def _load_wlists():
                    for p in [".color_watchlists.json", "data/.color_watchlists.json"]:
                        if os.path.exists(p):
                            try:
                                with open(p, "r", encoding="utf-8") as f:
                                    return json.load(f)
                            except Exception:
                                pass
                    return {}

                matched_symbols = []
                if cur_col == "star":
                    cw = st.session_state.get("custom_watchlist", [])
                    for item in cw:
                        if isinstance(item, (list, tuple)) and len(item) > 0:
                            matched_symbols.append(str(item[0]))
                        elif isinstance(item, dict) and "symbol" in item:
                            matched_symbols.append(str(item["symbol"]))
                        elif isinstance(item, str) and item.strip():
                            matched_symbols.append(item.strip())
                    
                    if not matched_symbols:
                        wlists = _load_wlists()
                        for k in ["star", "yellow", "fav"]:
                            if k in wlists and wlists[k]:
                                matched_symbols = wlists[k]
                                break
                else:
                    wlists = _load_wlists()
                    active_aliases = next((a for _, k, a in COLOR_TABS if k == cur_col), [cur_col])
                    for k, v in wlists.items():
                        if k.lower() in active_aliases:
                            matched_symbols = v
                            break

                if matched_symbols:
                    st.markdown("<div style='max-height: 220px; overflow-y: auto; margin: 6px 0; display: flex; flex-direction: column; gap: 4px;'>", unsafe_allow_html=True)
                    for idx_s, item in enumerate(matched_symbols):
                        s_code = item.get("symbol", item) if isinstance(item, dict) else str(item)
                        if st.button(f"🪙 {s_code}", key=f"qpick_{s_code}_{idx_s}", use_container_width=True):
                            st.session_state["current_symbol"] = s_code
                            st.session_state.pop("selected_symbol", None)
                            for t in st.session_state.get("chart_tabs", []):
                                if t.get("id") == st.session_state.get("active_tab_id"):
                                    t["symbol"] = s_code
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.caption("ไม่มีเหรียญในกลุ่มนี้")

                st.divider()

                if st.button("🔎 ค้นหาสินทรัพย์ทั้งหมด...", key="mob_open_sym_search", use_container_width=True):
                    render_symbol_modal()

        with c_tf:
            with st.popover(f"⏱️ {cur_tf} ▾", use_container_width=True):
                st.caption("เลือกไทม์เฟรม")
                for tf_item in PRIMARY_TFS:
                    t_type = "primary" if tf_item == cur_tf else "secondary"
                    if st.button(tf_item, key=f"mob_qtf_{tf_item}", type=t_type, use_container_width=True):
                        st.session_state["selected_tf"] = tf_item
                        for t in st.session_state.get("chart_tabs", []):
                            if t.get("id") == st.session_state.get("active_tab_id"):
                                t["tf"] = tf_item
                        st.rerun()

        with c_clr:
            if st.button("🧹 ล้าง", key="mob_btn_clear_ind", help="ล้างอินดิเคเตอร์ทั้งหมด", use_container_width=True):
                st.session_state["active_indicators"] = []
                st.session_state["rsi_enabled"] = False
                st.session_state["macd_enabled"] = False
                st.session_state["bb_enabled"] = False
                st.toast("ล้างอินดิเคเตอร์เรียบร้อย")
                st.rerun()

        with c_fs:
            if st.button("⛶", key="mob_btn_fullscreen", help="เปิดเต็มจอ", use_container_width=True):
                components.html("""
                <script>
                    const doc = window.parent.document;
                    if (!doc.fullscreenElement) {
                        doc.documentElement.requestFullscreen().catch(err => {});
                    } else {
                        doc.exitFullscreen().catch(err => {});
                    }
                </script>
                """, height=0, width=0)

    if st.session_state.get("modal_indicators_open", False):
        show_indicators_modal()

    # =========================================================================
    # 3. แถบนำทางด้านล่าง 6 ปุ่ม
    # =========================================================================
    NAV_ITEMS = [
        ("📋\nรายการ", "list", "mob_nav_list"),
        ("📈\nชาร์ต", "chart", "mob_nav_chart"),
        ("📊\nสรุป", "summary", "mob_nav_summary"),
        ("✏️\nวาด", "draw", "mob_nav_draw"),
        ("⚙️\nอินดิ", "ind", "mob_nav_ind"),
        ("💻\nคอม", "desktop", "mob_nav_desktop")
    ]

    b_cols = st.columns(6, gap="small")
    with b_cols[0]:
        st.markdown('<div class="bottom-nav-marker" style="display:none;"></div>', unsafe_allow_html=True)
    
    for col, (label, act, k) in zip(b_cols, NAV_ITEMS):
        with col:
            is_act = (act == cur_tab) or (act == "draw" and st.session_state.get("show_draw_toolbar", True))
            if st.button(label, key=k, type="primary" if is_act else "secondary", use_container_width=True):
                if act in ["list", "chart", "summary"]:
                    st.session_state["mobile_tab"] = act
                elif act == "draw":
                    st.session_state["show_draw_toolbar"] = not st.session_state.get("show_draw_toolbar", True)
                    st.session_state["mobile_tab"] = "chart"
                elif act == "ind":
                    st.session_state["modal_indicators_open"] = True
                elif act == "desktop":
                    st.session_state["mobile_mode"] = False
                st.rerun()