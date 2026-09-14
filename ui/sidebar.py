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
    show_top = True
    show_tool = True

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
        # เว้นระยะบนสุด 36px เพื่อหลบไอคอนแฮมเบอร์เกอร์ ☰ และสคริปต์นาฬิกาอัตโนมัติ
        st.markdown("""
        <div style="margin-top: 36px; background: #0B0E14; border: 1px solid #FF7A00; border-radius: 8px; padding: 6px; margin-bottom: 12px;">
            <div style="font-size: 9px; color: #8F9CAE; font-weight: 600;">📍 BKK (UTC+7)</div>
            <div id="sb-clock" style="font-family: monospace; font-size: 1.25rem; font-weight: 800; color: #FF7A1A; text-align: center;">--:--:--</div>
        </div>
        <script>
        (function() {
            function updateClock() {
                const el = document.getElementById('sb-clock');
                if (el) {
                    el.textContent = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Bangkok', hour12: false });
                }
            }
            updateClock();
            if (window.sbClockInterval) clearInterval(window.sbClockInterval);
            window.sbClockInterval = setInterval(updateClock, 1000);
        })();
        </script>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("### 🔍 ค้นหาสินทรัพย์")

        market_categories = [
            "₿ คริปโตเคอร์เรนซี",
            "📈 หุ้น",
            "🟠 โภคภัณฑ์ (Commodities)",
            "💱 อัตราแลกเปลี่ยน (Forex)",
            "🌾 สินค้าเกษตร (ราคาข้าว)",
        ]

        main_category = st.selectbox("กลุ่มตลาด", market_categories, key="sb_main_category")

        if "prev_main_cat" not in st.session_state:
            st.session_state["prev_main_cat"] = main_category
        if st.session_state["prev_main_cat"] != main_category:
            st.session_state["prev_main_cat"] = main_category
            for k in ["sb_crypto_exchange", "sb_stock_country", "sb_symbol_select", "sb_rice_select_v2"]:
                if k in st.session_state:
                    del st.session_state[k]

        sym_list = []

        # ==========================================
        # 1. กลุ่มราคาข้าว (เชื่อมเข้ากราฟแท่งเทียน)
        # ==========================================
        if "สินค้าเกษตร" in main_category:
            sym_list = get_rice_symbols_list()
            selected_sym = st.selectbox("เลือกชนิดข้าว / ตลาดส่งออก", sym_list, key="sb_rice_choice")

            if st.button("📈 ดูกราฟแท่งเทียนสายพันธุ์นี้", use_container_width=True, key="btn_open_rice_chart"):
                update_active_tab_symbol(selected_sym, default_tf="1D")

        # ==========================================
        # 2. สินทรัพย์คริปโต / หุ้น / โภคภัณฑ์ / Forex
        # ==========================================
        else:
            if main_category == "₿ คริปโตเคอร์เรนซี":
                sub_selection = st.selectbox("เลือกกระดานเทรด", ["🟡 Binance", "🟢 Bitkub", "🔵 OKX", "🟣 Bybit", "🟤 MEXC"], key="sb_crypto_exchange")
                try:
                    if "Bitkub" in sub_selection and get_full_bitkub_symbols:
                        sym_list = get_full_bitkub_symbols()
                    elif get_full_binance_symbols:
                        sym_list = get_full_binance_symbols()
                except Exception:
                    sym_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

            elif main_category == "📈 หุ้น":
                sub_selection = st.selectbox("เลือกประเทศ / ตลาดหุ้น", ["🇹🇭 หุ้นไทย (SET/mai)", "🇺🇸 หุ้นสหรัฐฯ (S&P500)"], key="sb_stock_country")
                sym_list = ["DELTA.BK", "PTT.BK", "AOT.BK", "KBANK.BK"] if "หุ้นไทย" in sub_selection else ["AAPL", "NVDA", "TSLA", "MSFT"]

            elif main_category == "🟠 โภคภัณฑ์ (Commodities)":
                sym_list = ["GC=F", "CL=F", "SI=F", "NG=F"]

            elif main_category == "💱 อัตราแลกเปลี่ยน (Forex)":
                sym_list = ["USDTHB=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X"]

            if not sym_list:
                sym_list = ["BTCUSDT"]

            selected_sym = st.selectbox("เลือกหรือพิมพ์สัญลักษณ์", sym_list, key="sb_symbol_select")

            btn_clicked = st.button("📈 เปิดกราฟสินทรัพย์นี้", use_container_width=True, key="sb_open_sym_btn")

            # เช็คเฉพาะเมื่อผู้ใช้อยู่ในโหมดกราฟ และมีการเปลี่ยนค่าเหรียญจริง
            sym_changed = (
                selected_sym
                and selected_sym != st.session_state.get("current_symbol")
                and st.session_state.get("last_sb_choice") != selected_sym
                and st.session_state.get("app_mode", "chart") == "chart"
            )

            if btn_clicked or sym_changed:
                st.session_state["last_sb_choice"] = selected_sym
                update_active_tab_symbol(selected_sym)

        st.divider()
        st.markdown("### ⚙ ตั้งค่าอินดิเคเตอร์")
        st.session_state["fast_ema"] = st.number_input("Fast EMA", min_value=1, max_value=200, value=st.session_state.get("fast_ema", 7))
        st.session_state["slow_ema"] = st.number_input("Slow EMA", min_value=1, max_value=200, value=st.session_state.get("slow_ema", 13))
        st.session_state["trend_ema"] = st.number_input("Trend EMA", min_value=1, max_value=500, value=st.session_state.get("trend_ema", 45))

        st.divider()
        show_top = st.toggle("แสดงแถบควบคุมด้านบน (TF/บาร์)", key="show_top_bar", value=True)
        show_tool = st.toggle("แสดงแถบเครื่องมือวาดกราฟ", key="show_draw_toolbar", value=True)

        st.divider()
        # พื้นที่ Dock Menu
        st.markdown("""
        <style>
        /* จัดระยะเว้นระหว่างหัวข้อแผงควบคุมกับปุ่ม Dock ไม่ให้ทับกัน */
        div[data-testid="stSidebar"] div:has(> #dock-anchor) {
            margin-top: 6px;
        }
        </style>
        <span id="dock-anchor"></span>
        """, unsafe_allow_html=True)
        render_dock_menu()

    return {"show_top_bar": show_top, "show_draw_toolbar": show_tool}