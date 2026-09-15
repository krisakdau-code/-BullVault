# ui/sidebar.py
import os
import json
import streamlit as st
import streamlit.components.v1 as components

try:
    from data.rice_ohlcv import get_rice_symbols_list
except ImportError:
    def get_rice_symbols_list():
        return ["RICE:ข้าวเปลือกเจ้า", "RICE:ข้าวเปลือกหอมมะลิ", "FOB:ข้าวสารขาว 100%", "ZR=F (CBOT Rough Rice)"]

try:
    from symbols import get_full_binance_symbols
except ImportError:
    try:
        from data.symbols import get_full_binance_symbols
    except ImportError:
        get_full_binance_symbols = None


def render_sidebar():
    show_top = st.session_state.get("show_top_bar", True)
    show_tool = st.session_state.get("show_draw_toolbar", True)

    def update_active_tab_symbol(sym, default_tf=None):
        st.session_state["current_symbol"] = sym
        st.session_state["app_mode"] = "chart"
        tf_val = default_tf if default_tf else st.session_state.get("selected_tf", "1h")
        if default_tf:
            st.session_state["selected_tf"] = default_tf

        if "open_tabs" not in st.session_state or not st.session_state.open_tabs:
            import uuid
            new_id = uuid.uuid4().hex[:8]
            st.session_state.open_tabs = [{"id": new_id, "symbol": sym, "tf": tf_val}]
            st.session_state.active_tab_id = new_id
        else:
            active_id = st.session_state.get("active_tab_id")
            updated = False
            for t in st.session_state.open_tabs:
                if t.get("id") == active_id:
                    t["symbol"] = sym
                    if default_tf:
                        t["tf"] = default_tf
                    updated = True
                    break
            if not updated:
                st.session_state.open_tabs[0]["symbol"] = sym
                if default_tf:
                    st.session_state.open_tabs[0]["tf"] = default_tf
                st.session_state.active_tab_id = st.session_state.open_tabs[0]["id"]
        st.rerun()

    with st.sidebar:
        # สไตล์ CSS กำกับกรอบส้ม Cyber Orange และกรอบเขียว Cyber Green
        st.markdown("""
        <style>
        div[data-testid="stSidebarContent"] {
            padding-top: 10px !important;
        }
        /* แถบแท็บ 2 ตัวด้านบน */
        div[data-testid="stSidebar"] div[data-baseweb="tab-list"] {
            gap: 6px !important;
            background: #0E121B !important;
            padding: 4px !important;
            border-radius: 8px !important;
            border: 1px solid #1F2433 !important;
            margin-bottom: 10px !important;
        }
        div[data-testid="stSidebar"] button[data-baseweb="tab"] {
            border-radius: 6px !important;
            padding: 6px 12px !important;
            font-size: 11.5px !important;
            font-weight: 700 !important;
            color: #8F9CAE !important;
            background: transparent !important;
            border: 1px solid transparent !important;
        }
        /* แท็บ 1 ส้มสะท้อนแสง */
        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
            background: rgba(255, 122, 0, 0.15) !important;
            border: 1px solid #FF7A00 !important;
            color: #FF9433 !important;
            box-shadow: 0 0 10px rgba(255, 122, 0, 0.35) !important;
        }
        /* แท็บ 2 เขียวนีออน */
        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
            background: rgba(0, 255, 163, 0.15) !important;
            border: 1px solid #00FFA3 !important;
            color: #00FFA3 !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.35) !important;
        }
        /* ช่องเลือกเหรียญ: บังคับกรอบส้มสะท้อนแสง */
        div[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #141824 !important;
            border: 1px solid #FF7A00 !important;
            border-radius: 6px !important;
            color: #ffffff !important;
        }
        /* ปุ่มชิป 4 ช่อง */
        div[data-testid="stSidebar"] button[kind="secondary"] {
            background: #141824 !important;
            border: 1px solid #23293A !important;
            color: #D1D4DC !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            border-radius: 5px !important;
        }
        div[data-testid="stSidebar"] button[kind="primary"] {
            background: rgba(255, 122, 0, 0.15) !important;
            border: 1px solid #FF7A00 !important;
            color: #FF9433 !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            border-radius: 5px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        tab_market, tab_tools = st.tabs(["🔍 ตลาด & ค้นหา", "⚙️ เครื่องมือ (3)"])

        # =============================================================
        # แท็บ 1: ตลาด & ค้นหา
        # =============================================================
        with tab_market:
            st.markdown("<div style='color:#FF9433; font-size:11px; font-weight:700; margin-bottom:4px;'>🔍 ค้นหาด่วน (Quick Search)</div>", unsafe_allow_html=True)

            current_pill = st.session_state.get("sb_pill_choice", "Crypto")

            sym_list = []
            if current_pill == "สินค้าเกษตร":
                sym_list = get_rice_symbols_list()
            elif current_pill == "หุ้นไทย (SET)":
                sym_list = ["DELTA.BK", "PTT.BK", "AOT.BK", "KBANK.BK", "SCB.BK", "ADVANC.BK", "CPALL.BK", "GULF.BK"]
            elif current_pill == "Crypto":
                try:
                    if get_full_binance_symbols:
                        sym_list = get_full_binance_symbols()
                except Exception:
                    pass
                if not sym_list:
                    sym_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT"]
            else:
                sym_list = ["BTCUSDT", "ETHUSDT", "GC=F", "CL=F", "DELTA.BK", "PTT.BK", "NVDA", "AAPL", "USDTHB=X"]

            cur_sym = st.session_state.get("current_symbol", "BTCUSDT")
            sel_idx = sym_list.index(cur_sym) if cur_sym in sym_list else 0

            selected_sym = st.selectbox(
                "ค้นหา",
                sym_list,
                index=sel_idx,
                label_visibility="collapsed",
                key="sb_select_sym_box"
            )

            if selected_sym and selected_sym != st.session_state.get("current_symbol"):
                is_rice = selected_sym.startswith("RICE:") or selected_sym.startswith("FOB:") or selected_sym == "ZR=F (CBOT Rough Rice)"
                update_active_tab_symbol(selected_sym, default_tf="1D" if is_rice else None)

            # ชิปเลือกหมวดหมู่ 4 ช่อง
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🟡 Crypto", key="chip_crypto", use_container_width=True, type="primary" if current_pill == "Crypto" else "secondary"):
                    st.session_state["sb_pill_choice"] = "Crypto"
                    st.rerun()
                if st.button("🇹🇭 หุ้นไทย (SET)", key="chip_thai", use_container_width=True, type="primary" if current_pill == "หุ้นไทย (SET)" else "secondary"):
                    st.session_state["sb_pill_choice"] = "หุ้นไทย (SET)"
                    st.rerun()
            with c2:
                if st.button("🌾 สินค้าเกษตร", key="chip_rice", use_container_width=True, type="primary" if current_pill == "สินค้าเกษตร" else "secondary"):
                    st.session_state["sb_pill_choice"] = "สินค้าเกษตร"
                    st.rerun()
                if st.button("🌐 ทั้งหมด", key="chip_all", use_container_width=True, type="primary" if current_pill == "ทั้งหมด" else "secondary"):
                    st.session_state["sb_pill_choice"] = "ทั้งหมด"
                    st.rerun()

            st.markdown("<div style='color:#00FFA3; font-size:11px; font-weight:700; margin-top:10px; margin-bottom:2px;'>📌 เหรียญที่เลือกมาแล้ว (Selected)</div>", unsafe_allow_html=True)

            # ---------------------------------------------------------
            # กล่องเลื่อนดูเหรียญ (Scrollable Watchlist HTML Component)
            # ---------------------------------------------------------
            tracked = []
            if "open_tabs" in st.session_state and st.session_state.open_tabs:
                for t in st.session_state.open_tabs:
                    if t.get("symbol") and t["symbol"] not in tracked:
                        tracked.append(t["symbol"])

            default_feed = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "GC=F", "NVDA", "PTT.BK", "ข้าวหอม 100%"]
            for s_feed in default_feed:
                if s_feed not in tracked:
                    tracked.append(s_feed)

            quotes = st.session_state.get("quotes_dict", {})
            rows_html = []
            active_current = st.session_state.get("current_symbol", "BTCUSDT")

            for sym_code in tracked:
                is_active = (sym_code == active_current)
                lbl = sym_code.replace("_THB", "").replace(".BK", "")
                
                # ข้อมูลราคาและ % เปลี่ยนแปลง
                q = quotes.get(sym_code, {})
                price_val = q.get("price", 0.0)
                chg_val = q.get("change", 0.0)
                
                # ราคา Mockup สำรองถ้าไม่มีข้อมูลสด
                if price_val == 0.0:
                    mock_p = {"BTCUSDT": 79036.15, "ETHUSDT": 2645.80, "SOLUSDT": 184.25, "BNBUSDT": 588.50, "GC=F": 2684.50, "NVDA": 142.30, "PTT.BK": 33.50, "ข้าวหอม 100%": 545.00}
                    mock_c = {"BTCUSDT": 2.27, "ETHUSDT": 3.14, "SOLUSDT": 5.42, "BNBUSDT": -0.85, "GC=F": 0.45, "NVDA": -1.12, "PTT.BK": 0.75, "ข้าวหอม 100%": 0.00}
                    price_val = mock_p.get(sym_code, 100.0)
                    chg_val = mock_c.get(sym_code, 1.25)

                p_str = f"{price_val:,.2f}"
                is_up = (chg_val >= 0)
                c_sign = "+" if is_up else ""
                badge_color = "#00FFA3" if is_up else "#ef5350"
                badge_bg = "rgba(0, 255, 163, 0.12)" if is_up else "rgba(239, 83, 80, 0.12)"
                row_border = "1px solid #00FFA3; box-shadow: 0 0 8px rgba(0, 255, 163, 0.25);" if is_active else "1px solid #23293A;"
                row_bg = "#182030" if is_active else "#141824"

                market_sub = "Binance Spot" if "USDT" in sym_code else ("SET Index" if ".BK" in sym_code else ("Futures" if "=F" in sym_code else "Market"))

                row_markup = f"""
                <div class="coin-row" style="background:{row_bg}; border:{row_border};" onclick="selectCoin('{sym_code}')">
                    <div style="display:flex; flex-direction:column;">
                        <span style="font-size:12px; font-weight:700; color:#ffffff;">{lbl}</span>
                        <span style="font-size:9px; color:#787B86;">{market_sub}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:11px; font-weight:600; font-family:monospace; color:#ffffff;">{p_str}</span>
                        <span style="font-size:10px; font-weight:700; color:{badge_color}; background:{badge_bg}; border:1px solid {badge_color}; border-radius:4px; padding:1px 5px;">
                            {c_sign}{chg_val:.2f}%
                        </span>
                    </div>
                </div>
                """
                rows_html.append(row_markup)

            watchlist_html = f"""
            <style>
                body {{ margin:0; padding:0; background:transparent; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .scroll-box {{
                    height: 330px;
                    overflow-y: auto;
                    background: #0E121B;
                    border: 1px solid rgba(0, 255, 163, 0.4);
                    border-radius: 8px;
                    padding: 6px;
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                    box-sizing: border-box;
                }}
                .scroll-box::-webkit-scrollbar {{
                    width: 5px;
                }}
                .scroll-box::-webkit-scrollbar-track {{
                    background: #0E121B;
                }}
                .scroll-box::-webkit-scrollbar-thumb {{
                    background: #00FFA3;
                    border-radius: 3px;
                }}
                .coin-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 5px 8px;
                    border-radius: 6px;
                    cursor: pointer;
                    user-select: none;
                    transition: all 0.15s ease;
                }}
                .coin-row:hover {{
                    border-color: #00FFA3 !important;
                    background: #182030 !important;
                }}
            </style>
            <div class="scroll-box">
                {''.join(rows_html)}
            </div>
            <script>
                function selectCoin(sym) {{
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: sym
                    }}, '*');
                }}
            </script>
            """

            clicked_sym = components.html(watchlist_html, height=340)
            if clicked_sym and clicked_sym != st.session_state.get("current_symbol"):
                is_r = clicked_sym.startswith("RICE:") or clicked_sym.startswith("FOB:") or clicked_sym == "ZR=F (CBOT Rough Rice)"
                update_active_tab_symbol(clicked_sym, default_tf="1D" if is_r else None)

        # =============================================================
        # แท็บ 2: เครื่องมือ (3)
        # =============================================================
        with tab_tools:
            st.markdown("<div style='color:#00FFA3; font-size:11px; font-weight:700; margin-bottom:6px;'>⚡ เครื่องมือระบบ (Launchers)</div>", unsafe_allow_html=True)
            
            c_fibo, c_mkt = st.columns(2)
            with c_fibo:
                if st.button("📐 Fibonacci", key="btn_fibo_side", use_container_width=True):
                    st.session_state["trigger_fib_modal"] = True
                    st.rerun()
            with c_mkt:
                if st.button("📊 ตลาด 24h", key="btn_mkt_side", use_container_width=True):
                    st.session_state["trigger_market_modal"] = True
                    st.rerun()

            c_rice, c_theme = st.columns(2)
            with c_rice:
                if st.button("🌾 ราคาข้าว", key="btn_rice_side", use_container_width=True):
                    st.session_state["app_mode"] = "rice"
                    st.rerun()
            with c_theme:
                if st.button("⚙️ สไตล์กราฟ", key="btn_theme_side", use_container_width=True):
                    st.session_state["trigger_settings_modal"] = True
                    st.rerun()

            st.markdown("<div style='color:#00FFA3; font-size:11px; font-weight:700; margin-top:12px; margin-bottom:4px;'>⚙️ ตั้งค่าอินดิเคเตอร์ที่เปิดอยู่</div>", unsafe_allow_html=True)

            if st.session_state.get("show_ema", True):
                with st.expander("📈 เส้นค่าเฉลี่ย EMA Ribbon", expanded=True):
                    st.session_state["fast_ema"] = st.number_input("Fast EMA", min_value=1, max_value=200, value=int(st.session_state.get("fast_ema", 7)), key="in_f_ema")
                    st.session_state["slow_ema"] = st.number_input("Slow EMA", min_value=1, max_value=200, value=int(st.session_state.get("slow_ema", 13)), key="in_s_ema")
                    st.session_state["trend_ema"] = st.number_input("Trend EMA", min_value=1, max_value=500, value=int(st.session_state.get("trend_ema", 45)), key="in_t_ema")

            if st.session_state.get("show_rsi_pane", True):
                with st.expander("📉 พารามิเตอร์ RSI (14)", expanded=False):
                    st.session_state["rsi_upper_band"] = st.number_input("Upper Band (UB)", value=float(st.session_state.get("rsi_upper_band", 70.0)), key="in_ub")
                    st.session_state["rsi_lower_band"] = st.number_input("Lower Band (LB)", value=float(st.session_state.get("rsi_lower_band", 30.0)), key="in_lb")
                    st.session_state["rsi_line_color"] = st.color_picker("สีเส้น RSI", st.session_state.get("rsi_line_color", "#00FFA3"), key="in_r_col")

            if st.session_state.get("show_macd_pane", True):
                with st.expander("📊 พารามิเตอร์ MACD", expanded=False):
                    st.session_state["macd_line_color"] = st.color_picker("สีเส้น MACD", st.session_state.get("macd_line_color", "#00FFA3"), key="in_m_col")
                    st.session_state["macd_signal_color"] = st.color_picker("สีเส้น Signal", st.session_state.get("macd_signal_color", "#FFEB3B"), key="in_sg_col")

        # =============================================================
        # ด้านล่างสุด: สวิตช์เปิด-ปิดแถบควบคุม + นาฬิกา BKK LIVE
        # =============================================================
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        show_tool = st.toggle("✏️ แถบวาดรูป (Draw)", key="show_draw_toolbar", value=show_tool)
        show_top = st.toggle("⏱️ แถบควบคุมบน (Top)", key="show_top_bar", value=show_top)

        st.markdown("""
        <div style="margin-top:6px; background:#0E121B; border:1px solid #1E2433; border-radius:6px; padding:4px 8px; display:flex; align-items:center; justify-content:space-between;">
            <div style="font-size:10px; color:#8F9CAE; font-family:monospace;">🕒 BKK (UTC+7) <span id="clock-live-txt">--:--:--</span></div>
            <div style="font-size:9px; color:#00FFA3; font-weight:700; background:rgba(0,255,163,0.15); padding:1px 5px; border-radius:3px;">LIVE</div>
        </div>
        <script>
        (function() {
            function updateClock() {
                const el = document.getElementById('clock-live-txt');
                if (el) el.textContent = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Bangkok', hour12: false });
            }
            updateClock();
            if (window.timerLive) clearInterval(window.timerLive);
            window.timerLive = setInterval(updateClock, 1000);
        })();
        </script>
        """, unsafe_allow_html=True)

    return {"show_top_bar": show_top, "show_draw_toolbar": show_tool}