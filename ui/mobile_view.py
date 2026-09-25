# ui/mobile_view.py — TradingView Mobile Standard
import streamlit as st
import streamlit.components.v1 as components
from ui.symbol_modal import render_symbol_modal
from ui.indicator_modal import show_indicators_modal

PRIMARY_TFS = ["5m", "15m", "30m", "1h", "2h", "3h", "4h", "D", "2D", "3D", "W", "M"]

def render_mobile_view(df, meta, is_thb_mode, fx_rate, chart_renderer, watchlist_renderer):
    if "mobile_tab" not in st.session_state:
        st.session_state["mobile_tab"] = "chart"

    cur_tab = st.session_state["mobile_tab"]
    cur_sym = st.session_state.get("current_symbol", "BTCUSDT")
    cur_tf = st.session_state.get("selected_tf", "1h")

    # =========================================================================
    # 1. CSS จัดระเบียบโครงสร้าง Mobile
    # =========================================================================
    st.markdown("""
    <style>
        /* เว้นระยะล่าง 94px เพื่อไม่ให้กราฟโดนแถบ 4 ปุ่ม และแถบนำทาง 6 ปุ่ม บดบัง */
        .block-container {
            padding-top: 2px !important;
            padding-bottom: 94px !important;
            padding-left: 2px !important;
            padding-right: 2px !important;
        }

        /* 1. ซ่อนปุ่ม ☰ สีส้มมุมซ้ายบนเฉพาะโหมดมือถือ */
        #toggle-btn-anchor,
        #floating-toggle-btn,
        .floating-toggle,
        div:has(> #toggle-btn-anchor),
        div:has(> #floating-toggle-btn),
        div[data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }

        /* 2. ล็อกขนาด 16.666% เฉพาะแถวปุ่ม 6 สีเท่านั้น (ไม่กระทบรายชื่อเหรียญหรือหน้าค้นหา) */
        div[data-testid="stHorizontalBlock"]:has(button[key*="mq_col_"]),
        div[data-testid="stHorizontalBlock"]:has(button[key*="cf_"]) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 3px !important;
            width: 100% !important;
            margin: 4px 0 8px 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(button[key*="mq_col_"]) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(button[key*="cf_"]) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(button[key*="mq_col_"]) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(button[key*="cf_"]) > div[data-testid="stColumn"] {
            min-width: 0 !important;
            max-width: 16.666% !important;
            flex: 1 1 16.666% !important;
            width: 16.666% !important;
            padding: 0 1px !important;
            margin: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(button[key*="mq_col_"]) button,
        div[data-testid="stHorizontalBlock"]:has(button[key*="cf_"]) button {
            padding: 2px 0px !important;
            height: 34px !important;
            min-height: 34px !important;
            font-size: 15px !important;
            width: 100% !important;
        }

        /* 3. กรอบแสดงเหรียญ (วงสีเขียว): หดตัวแนบพอดีเมื่อมีเหรียญน้อย ยืดได้สูงสุด 60vh พร้อมเลื่อน Scroll */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            height: auto !important;
            min-height: 60px !important;
            max-height: 60vh !important;
            overflow-y: auto !important;
            background: #0d1117 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
            padding: 4px !important;
        }

        /* จัดแถวข้อมูลเหรียญในแนวนอนให้สมส่วน ไม่บีบอักษร */
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: 4px !important;
            padding: 3px 4px !important;
            margin: 1px 0 !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
        }

        /* 4. จัดแถบล่างสุด (⚙️ ตั้งค่า และ นาฬิกา BKK) แยกซ้าย-ขวา ไม่ทับกัน */
        div[data-testid="stHorizontalBlock"]:has(button[key*="settings"]),
        div[data-testid="stHorizontalBlock"]:has(div[class*="bkk"]),
        div[data-testid="stHorizontalBlock"]:has(*:contains("BKK")) {
            display: flex !important;
            flex-direction: row !important;
            justify-content: space-between !important;
            align-items: center !important;
            width: 100% !important;
            padding: 6px 4px !important;
            margin-top: 6px !important;
        }

        /* 5. ตรึงแถบควบคุม 4 ปุ่ม ไว้เหนือแถบล่าง 6 ปุ่ม พอดีเป๊ะ */
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
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) > div[data-testid="column"]:last-child,
        div[data-testid="stHorizontalBlock"]:has(.subchart-marker) > div[data-testid="stColumn"]:last-child {
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

        /* 6. แถบนำทางด้านล่าง 6 ปุ่ม (Fixed ขอบล่างสุด 0px) */
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
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) > div[data-testid="stColumn"] {
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
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button p,
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button span {
            font-size: 10px !important;
            line-height: 1.2 !important;
            color: #8b949e !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: center !important;
            white-space: pre-wrap !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button:hover p,
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button:hover span {
            color: #ff9d42 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button[kind="primary"] p,
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button[kind="primary"] span,
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button[data-testid="baseButton-primary"] p,
        div[data-testid="stHorizontalBlock"]:has(.bottom-nav-marker) button[data-testid="baseButton-primary"] span {
            color: #ff7d1e !important;
            font-weight: 700 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # สคริปต์ล็อกตำแหน่งและซ่อนปุ่ม ☰ อัตโนมัติ
    components.html("""
    <script>
    (function() {
        const doc = window.parent.document;
        function enforceLayout() {
            // 1. ซ่อนปุ่ม ☰
            const tb = doc.querySelectorAll('#toggle-btn-anchor, #floating-toggle-btn');
            tb.forEach(el => el.style.setProperty('display', 'none', 'important'));

            // 2. ล็อกแถบควบคุม 4 ปุ่ม (บริเวณวงสีแดง)
            const sMarker = doc.querySelector('.subchart-marker');
            if (sMarker) {
                const sBlock = sMarker.closest('[data-testid="stHorizontalBlock"]');
                if (sBlock) {
                    sBlock.style.cssText = 'position:fixed !important; bottom:52px !important; left:0 !important; right:0 !important; width:100vw !important; height:38px !important; background:#090b10 !important; border-top:1px solid #1e2433 !important; z-index:9999998 !important; display:flex !important; flex-direction:row !important; flex-wrap:nowrap !important; align-items:center !important; justify-content:space-between !important; margin:0 !important; padding:0 4px !important;';
                }
            }

            // 3. ล็อกแถบล่าง 6 ปุ่ม (ขอบล่างสุด)
            const bMarker = doc.querySelector('.bottom-nav-marker');
            if (bMarker) {
                const bBlock = bMarker.closest('[data-testid="stHorizontalBlock"]');
                if (bBlock) {
                    bBlock.style.cssText = 'position:fixed !important; bottom:0 !important; left:0 !important; right:0 !important; width:100vw !important; height:52px !important; background:#090b10 !important; border-top:1px solid #1e2433 !important; z-index:9999999 !important; display:flex !important; flex-direction:row !important; flex-wrap:nowrap !important; justify-content:space-around !important; align-items:center !important; margin:0 !important; padding:0 !important;';
                    const cols = bBlock.querySelectorAll(':scope > div[data-testid="column"], :scope > div[data-testid="stColumn"]');
                    cols.forEach(col => {
                        col.style.cssText = 'width:16.666% !important; min-width:0 !important; max-width:16.666% !important; flex:1 1 16.666% !important; margin:0 !important; padding:0 !important; display:flex !important; align-items:center !important; justify-content:center !important;';
                    });
                }
            }
        }
        setInterval(enforceLayout, 150);
        setTimeout(enforceLayout, 20);
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
        # กราฟชาร์ตหลัก ชิดขอบบนทันที
        chart_renderer()

        # ---------------------------------------------------------------------
        # แถบควบคุม 4 ปุ่ม (บริเวณวงสีแดงเหนือแถบล่าง 6 ปุ่ม)
        # ---------------------------------------------------------------------
        c_sym, c_tf, c_clr, c_fs = st.columns([1.3, 1.1, 0.9, 0.5], gap="small")

        with c_sym:
            st.markdown('<div class="subchart-marker" style="display:none;"></div>', unsafe_allow_html=True)
            with st.popover(f"🔍 {cur_sym} ▾", use_container_width=True):
                st.markdown(
                    "<div style='font-size:12px; font-weight:700; color:#ff7d1e; margin-bottom:6px;'>⚡ เลือกกลุ่มดาว / สี</div>",
                    unsafe_allow_html=True
                )

                # 1. แถวปุ่มเลือกกลุ่มสี 6 ปุ่ม
                COLOR_TABS = [
                    ("⭐", "star", ["star", "yellow", "fav"]),
                    ("🔴", "red", ["red"]),
                    ("🟠", "orange", ["orange"]),
                    ("🟢", "green", ["green"]),
                    ("🔵", "blue", ["blue"]),
                    ("⚪", "white", ["white", "gray"])
                ]

                cur_col = st.session_state.get("mobile_quick_col", "star")
                c_cols = st.columns(6)
                for idx, (emoji, key, _) in enumerate(COLOR_TABS):
                    with c_cols[idx]:
                        if st.button(emoji, key=f"mq_col_{key}"):
                            st.session_state["mobile_quick_col"] = key
                            st.rerun()

                # 2. ดึงรายชื่อเหรียญตามกลุ่มสีที่เลือก
                def _load_wlists():
                    import os, json
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
                    # กรณีเลือกดาว ⭐ ให้ดึงตรงจากรายการเฝ้าดูหลัก (custom_watchlist)
                    cw = st.session_state.get("custom_watchlist", [])
                    for item in cw:
                        s_name = item[0] if isinstance(item, (list, tuple)) else (item.get("symbol") if isinstance(item, dict) else str(item))
                        if s_name:
                            matched_symbols.append(s_name)
                else:
                    wlists = _load_wlists()
                    active_aliases = next((a for _, k, a in COLOR_TABS if k == cur_col), [cur_col])
                    for k, v in wlists.items():
                        if k.lower() in active_aliases:
                            matched_symbols = v
                            break

                # 3. แสดงเหรียญในกลุ่ม กดปุ๊บ กราฟเปลี่ยนปั๊บ
                if matched_symbols:
                    st.markdown("<div style='max-height: 220px; overflow-y: auto; margin: 6px 0; display: flex; flex-direction: column; gap: 4px;'>", unsafe_allow_html=True)
                    for item in matched_symbols:
                        s_code = item.get("symbol", item) if isinstance(item, dict) else str(item)
                        if st.button(f"🪙 {s_code}", key=f"qpick_{s_code}", use_container_width=True):
                            st.session_state["current_symbol"] = s_code
                            st.session_state.pop("selected_symbol", None)
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.caption("ไม่มีเหรียญในกลุ่มนี้")

                st.divider()

                # 4. ปุ่มค้นหาสินทรัพย์ทั้งหมดเดิม
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
    # 3. แถบนำทางด้านล่าง 6 ปุ่ม (Fixed ขอบล่างสุด)
    # =========================================================================
    b_cols = st.columns(6, gap="small")

    with b_cols[0]:
        st.markdown('<div class="bottom-nav-marker" style="display:none;"></div>', unsafe_allow_html=True)
        t_type = "primary" if cur_tab == "list" else "secondary"
        if st.button("📋\nรายการ", key="mob_nav_list", type=t_type, use_container_width=True):
            st.session_state["mobile_tab"] = "list"
            st.rerun()

    with b_cols[1]:
        t_type = "primary" if cur_tab == "chart" else "secondary"
        if st.button("📈\nชาร์ต", key="mob_nav_chart", type=t_type, use_container_width=True):
            st.session_state["mobile_tab"] = "chart"
            st.rerun()

    with b_cols[2]:
        t_type = "primary" if cur_tab == "summary" else "secondary"
        if st.button("📊\nสรุป", key="mob_nav_summary", type=t_type, use_container_width=True):
            st.session_state["mobile_tab"] = "summary"
            st.rerun()

    with b_cols[3]:
        draw_on = st.session_state.get("show_draw_toolbar", True)
        t_type = "primary" if draw_on else "secondary"
        if st.button("✏️\nวาด", key="mob_nav_draw", type=t_type, use_container_width=True):
            st.session_state["show_draw_toolbar"] = not draw_on
            st.session_state["mobile_tab"] = "chart"
            st.rerun()

    with b_cols[4]:
        if st.button("⚙️\nอินดิ", key="mob_nav_ind", use_container_width=True):
            st.session_state["modal_indicators_open"] = True
            st.rerun()

    with b_cols[5]:
        if st.button("💻\nคอม", key="mob_nav_desktop", use_container_width=True):
            st.session_state["mobile_mode"] = False
            st.rerun()