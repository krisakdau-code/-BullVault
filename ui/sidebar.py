# ui/sidebar.py
import os
import json
import streamlit as st
from ui.dock_menu import render_dock_menu
from data.rice_ohlcv import get_rice_symbols_list

try:
    from data.symbols import (
        get_full_binance_symbols, get_full_binance_th_symbols, get_full_bitkub_symbols,
        get_full_okx_symbols, get_full_bybit_symbols, get_full_gate_symbols,
        get_full_mexc_symbols, get_full_kucoin_symbols, get_full_china_stocks,
        get_full_commodities, get_full_forex, get_full_sp500_symbols, get_full_vietnam_symbols
    )
except ImportError:
    get_full_binance_symbols = get_full_binance_th_symbols = get_full_bitkub_symbols = None
    get_full_okx_symbols = get_full_bybit_symbols = get_full_gate_symbols = None
    get_full_mexc_symbols = get_full_kucoin_symbols = get_full_china_stocks = None
    get_full_commodities = get_full_forex = get_full_sp500_symbols = get_full_vietnam_symbols = None


def render_sidebar():
    show_top = st.session_state.get("show_top_bar", True)
    show_tool = st.session_state.get("show_draw_toolbar", True)

    # ฟังก์ชันสลับเหรียญ: แทนที่ลงในแท็บปัจจุบันเสมอ (ไม่สร้างแท็บใหม่)
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
        # สไตล์ CSS เสริมสำหรับแถบแท็บสีส้มสะท้อนแสง + สีเขียวนีออน และ Scrollbar เรียบหรู
        st.markdown("""
        <style>
        /* สไตล์แท็บด้านบนของ Sidebar */
        div[data-testid="stSidebar"] div[data-baseweb="tab-list"] {
            gap: 4px !important;
            background: #0E121B !important;
            padding: 4px !important;
            border-radius: 8px !important;
            border: 1px solid #1F2433 !important;
        }
        div[data-testid="stSidebar"] button[data-baseweb="tab"] {
            border-radius: 6px !important;
            padding: 6px 12px !important;
            font-size: 11.5px !important;
            font-weight: 700 !important;
            color: #8F9CAE !important;
            background: transparent !important;
            transition: all 0.2s ease !important;
        }
        /* แท็บที่ 1: ตลาด & ค้นหา (สีส้มสะท้อนแสง) */
        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
            background: rgba(255, 122, 0, 0.15) !important;
            border: 1px solid #FF7A00 !important;
            color: #FF9433 !important;
            box-shadow: 0 0 10px rgba(255, 122, 0, 0.35) !important;
        }
        /* แท็บที่ 2: เครื่องมือ & อินดี้ (สีเขียวนีออน) */
        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
            background: rgba(0, 255, 163, 0.15) !important;
            border: 1px solid #00FFA3 !important;
            color: #00FFA3 !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.35) !important;
        }

        /* ตกแต่ง Scrollbar ของกล่องเหรียญ */
        div[data-testid="stVerticalBlock"]:has(> div.coin-scroll-box) {
            scrollbar-width: thin !important;
            scrollbar-color: #00FFA3 #131722 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # -------------------------------------------------------------
        # ระบบ 2 แท็บหลักของ Sidebar
        # -------------------------------------------------------------
        tab_market, tab_tools = st.tabs(["🔍 ตลาด & ค้นหา", "⚙️ เครื่องมือ & อินดี้"])

        # =============================================================
        # แท็บที่ 1: ตลาด & ค้นหา (Cyber Orange Theme)
        # =============================================================
        with tab_market:
            st.markdown("<div style='color: #FF9433; font-size: 11px; font-weight: 700; margin: 4px 0 2px 2px;'>🔍 ค้นหาด่วน (Quick Search)</div>", unsafe_allow_html=True)

            # 4 ชิปหมวดหมู่ตลาด (2x2 Grid ตามรูปที่ 2)
            market_map = {
                "Crypto": "₿ คริปโตเคอร์เรนซี",
                "หุ้นไทย (SET)": "📈 หุ้น",
                "สินค้าเกษตร": "🌾 สินค้าเกษตร (ราคาข้าว)",
                "ทั้งหมด": "🌐 ทั้งหมด"
            }
            pills = ["Crypto", "หุ้นไทย (SET)", "สินค้าเกษตร", "ทั้งหมด"]
            current_pill = st.session_state.get("sb_pill_choice", "Crypto")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                if st.button("🟡 Crypto", key="pill_crypto", use_container_width=True, type="primary" if current_pill == "Crypto" else "secondary"):
                    st.session_state["sb_pill_choice"] = "Crypto"
                    st.rerun()
                if st.button("🇹🇭 หุ้นไทย (SET)", key="pill_thai", use_container_width=True, type="primary" if current_pill == "หุ้นไทย (SET)" else "secondary"):
                    st.session_state["sb_pill_choice"] = "หุ้นไทย (SET)"
                    st.rerun()
            with col_p2:
                if st.button("🌾 สินค้าเกษตร", key="pill_rice", use_container_width=True, type="primary" if current_pill == "สินค้าเกษตร" else "secondary"):
                    st.session_state["sb_pill_choice"] = "สินค้าเกษตร"
                    st.rerun()
                if st.button("🌐 ทั้งหมด", key="pill_all", use_container_width=True, type="primary" if current_pill == "ทั้งหมด" else "secondary"):
                    st.session_state["sb_pill_choice"] = "ทั้งหมด"
                    st.rerun()

            # โหลดรายการสัญลักษณ์ตามหมวดหมู่ที่เลือก
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

            # ช่องค้นหาด่วนแบบบรรทัดเดียว (ขอบส้มเรืองแสง)
            cur_sym = st.session_state.get("current_symbol", "BTCUSDT")
            sel_idx = sym_list.index(cur_sym) if cur_sym in sym_list else 0

            selected_sym = st.selectbox(
                "ค้นหาสินทรัพย์",
                sym_list,
                index=sel_idx,
                label_visibility="collapsed",
                key="sb_quick_search_box"
            )

            # ตรวจสอบการเลือกเหรียญเพื่อเปลี่ยนชาร์ตทันที
            if selected_sym and selected_sym != st.session_state.get("current_symbol"):
                st.session_state["last_sb_choice"] = selected_sym
                is_rice = selected_sym.startswith("RICE:") or selected_sym.startswith("FOB:") or selected_sym == "ZR=F (CBOT Rough Rice)"
                update_active_tab_symbol(selected_sym, default_tf="1D" if is_rice else None)

            st.markdown("<hr style='border:none; border-top:1px solid #242A3A; margin: 10px 0 6px 0;'/>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # จุดที่ 1: กล่องเลื่อนดูเหรียญที่เลือกมาแล้ว (Scrollable Watchlist)
            # -------------------------------------------------------------
            st.markdown("<div style='color: #00FFA3; font-size: 11px; font-weight: 700; margin-bottom: 2px;'>📌 สินทรัพย์ที่เลือกแล้ว (Selected Watchlist)</div>", unsafe_allow_html=True)
            st.caption("คลิกที่แถวเหรียญเพื่อสลับกราฟมาดูทันที")

            # รวบรวมเหรียญที่เปิดแท็บอยู่ + รายการโปรดมาใส่ในกล่องเลื่อนดู
            tracked_symbols = []
            if "open_tabs" in st.session_state and st.session_state.open_tabs:
                for t in st.session_state.open_tabs:
                    if t.get("symbol") and t["symbol"] not in tracked_symbols:
                        tracked_symbols.append(t["symbol"])

            # เพิ่มเหรียญยอดนิยมเข้ามาสำรองหากยังมีน้อย
            default_feed = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "GC=F", "NVDA", "PTT.BK"]
            for df_sym in default_feed:
                if df_sym not in tracked_symbols:
                    tracked_symbols.append(df_sym)

            # คอนเทนเนอร์แบบเลื่อนแนวตั้ง (Scrollable Container ความสูง 350px)
            with st.container(height=350):
                st.markdown('<div class="coin-scroll-box"></div>', unsafe_allow_html=True)
                for sym_item in tracked_symbols:
                    is_active = (sym_item == st.session_state.get("current_symbol"))
                    
                    # ป้ายชื่อเหรียญย่อ
                    lbl = sym_item.replace("_THB", "").replace(".BK", "")
                    border_style = "border: 1px solid #00FFA3; background: rgba(0, 255, 163, 0.12);" if is_active else "border: 1px solid #242A3A; background: #131722;"
                    
                    c_btn, c_del = st.columns([4, 1])
                    with c_btn:
                        btn_label = f"● {lbl}" if is_active else lbl
                        if st.button(btn_label, key=f"sb_wl_btn_{sym_item}", use_container_width=True, type="primary" if is_active else "secondary"):
                            is_r = sym_item.startswith("RICE:") or sym_item.startswith("FOB:") or sym_item == "ZR=F (CBOT Rough Rice)"
                            update_active_tab_symbol(sym_item, default_tf="1D" if is_r else None)
                    with c_del:
                        if st.button("✕", key=f"sb_wl_del_{sym_item}", help=f"ลบ {sym_item}"):
                            # ลบออกจากแท็บหากมีมากกว่า 1 แท็บ
                            if "open_tabs" in st.session_state and len(st.session_state.open_tabs) > 1:
                                st.session_state.open_tabs = [t for t in st.session_state.open_tabs if t.get("symbol") != sym_item]
                            st.rerun()

        # =============================================================
        # แท็บที่ 2: เครื่องมือ & อินดี้ (Cyber Green Theme)
        # =============================================================
        with tab_tools:
            st.markdown("<div style='color: #00FFA3; font-size: 11px; font-weight: 700; margin-bottom: 6px;'>⚡ เครื่องมือระบบ (Launchers)</div>", unsafe_allow_html=True)
            
            # ปุ่มไอคอนระบบ 4 ช่อง (2x2 Grid)
            c_fibo, c_market = st.columns(2)
            with c_fibo:
                if st.button("📐 Fibonacci", key="sb_btn_fibo", use_container_width=True, help="วิเคราะห์เป้าหมายราคา Fibonacci Suite"):
                    st.session_state["trigger_fib_modal"] = True
                    st.rerun()
            with c_market:
                if st.button("📊 ตลาด 24h", key="sb_btn_mkt", use_container_width=True, help="ภาพรวมตลาด 24 ชม. & เครื่องวัดสัญญาณ"):
                    st.session_state["trigger_market_modal"] = True
                    st.rerun()

            c_rice, c_theme = st.columns(2)
            with c_rice:
                if st.button("🌾 ราคาข้าว", key="sb_btn_rice", use_container_width=True, help="ดูดัชนีราคาข้าวและสถิติการส่งออก"):
                    st.session_state["app_mode"] = "rice"
                    st.rerun()
            with c_theme:
                if st.button("⚙️ สไตล์กราฟ", key="sb_btn_theme", use_container_width=True, help="ปรับแต่งสีแท่งเทียนและสไตล์กราฟ"):
                    st.session_state["trigger_settings_modal"] = True
                    st.rerun()

            st.markdown("<hr style='border:none; border-top:1px solid #242A3A; margin: 10px 0 6px 0;'/>", unsafe_allow_html=True)

            # การตั้งค่าอินดิเคเตอร์แบบไดนามิก (เปิดเฉพาะตัวที่ใช้งาน)
            st.markdown("<div style='color: #00FFA3; font-size: 11px; font-weight: 700; margin-bottom: 4px;'>⚙️ ตั้งค่าอินดิเคเตอร์ที่เปิดอยู่</div>", unsafe_allow_html=True)

            # 1. กล่อง EMA Ribbon
            if st.session_state.get("show_ema", True):
                with st.expander("📈 เส้นค่าเฉลี่ย EMA Ribbon", expanded=True):
                    st.session_state["fast_ema"] = st.number_input("Fast EMA", min_value=1, max_value=200, value=int(st.session_state.get("fast_ema", 7)), key="sb_in_fast_ema")
                    st.session_state["slow_ema"] = st.number_input("Slow EMA", min_value=1, max_value=200, value=int(st.session_state.get("slow_ema", 13)), key="sb_in_slow_ema")
                    st.session_state["trend_ema"] = st.number_input("Trend EMA", min_value=1, max_value=500, value=int(st.session_state.get("trend_ema", 45)), key="sb_in_trend_ema")

            # 2. กล่อง RSI
            if st.session_state.get("show_rsi_pane", True):
                with st.expander("📉 พารามิเตอร์ RSI (14)", expanded=False):
                    st.session_state["rsi_upper_band"] = st.number_input("Upper Band (UB)", value=float(st.session_state.get("rsi_upper_band", 70.0)), key="sb_in_rsi_ub")
                    st.session_state["rsi_lower_band"] = st.number_input("Lower Band (LB)", value=float(st.session_state.get("rsi_lower_band", 30.0)), key="sb_in_rsi_lb")
                    st.session_state["rsi_line_color"] = st.color_picker("สีเส้นสัญญาณ RSI", st.session_state.get("rsi_line_color", "#00FFA3"), key="sb_in_rsi_col")

            # 3. กล่อง MACD
            if st.session_state.get("show_macd_pane", True):
                with st.expander("📊 พารามิเตอร์ MACD", expanded=False):
                    st.session_state["macd_line_color"] = st.color_picker("สีเส้น MACD", st.session_state.get("macd_line_color", "#00FFA3"), key="sb_in_macd_col")
                    st.session_state["macd_signal_color"] = st.color_picker("สีเส้น Signal", st.session_state.get("macd_signal_color", "#FFEB3B"), key="sb_in_sig_col")

        # -------------------------------------------------------------
        # ด้านล่างสุด: สวิตช์เปิด-ปิดแถบควบคุม + นาฬิกา BKK LIVE
        # -------------------------------------------------------------
        st.markdown("<hr style='border:none; border-top:1px solid #242A3A; margin: 12px 0 6px 0;'/>", unsafe_allow_html=True)
        show_tool = st.toggle("✏️ แถบวาดรูป (Draw)", key="show_draw_toolbar", value=show_tool)
        show_top = st.toggle("⏱️ แถบควบคุมบน (Top)", key="show_top_bar", value=show_top)

        # แถบนาฬิกา BKK LIVE แบบมินิมอล
        st.markdown("""
        <div style="margin-top: 8px; background: #0E121B; border: 1px solid #1E2433; border-radius: 6px; padding: 4px 8px; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 10px; color: #8F9CAE; font-family: monospace;">🕒 BKK (UTC+7) <span id="sb-clock-live">--:--:--</span></div>
            <div style="font-size: 9px; color: #00FFA3; font-weight: 700; background: rgba(0, 255, 163, 0.15); padding: 1px 5px; border-radius: 3px;">LIVE</div>
        </div>
        <script>
        (function() {
            function updateLiveClock() {
                const el = document.getElementById('sb-clock-live');
                if (el) {
                    el.textContent = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Bangkok', hour12: false });
                }
            }
            updateLiveClock();
            if (window.sbLiveClockInterval) clearInterval(window.sbLiveClockInterval);
            window.sbLiveClockInterval = setInterval(updateLiveClock, 1000);
        })();
        </script>
        """, unsafe_allow_html=True)

    return {"show_top_bar": show_top, "show_draw_toolbar": show_tool}