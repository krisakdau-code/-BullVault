# ui/sidebar.py
import streamlit as st
from ui.dock_menu import render_dock_menu
from symbols import (
    get_full_binance_symbols,
    get_full_bitkub_symbols,
    get_full_okx_symbols,
    get_full_bybit_symbols,
    get_full_gate_symbols,
    get_full_mexc_symbols,
    get_full_kucoin_symbols,
    get_full_china_stocks,
    get_full_commodities,
    get_full_forex,
    get_full_sp500_symbols,
    get_full_vietnam_symbols,
)

def render_sidebar():
    with st.sidebar:
        # 1. นาฬิกาเรียลไทม์
        st.markdown("""
        <div style="background: #0B0E14; border: 1px solid #FF7A00; border-radius: 8px; padding: 6px; margin-bottom: 8px;">
            <div style="font-size: 8px; color: #8F9CAE;">📍 BKK (UTC+7)</div>
            <div id="sb-clock" style="font-family: monospace; font-size: 1.2rem; font-weight: 800; color: #FF7A1A; text-align: center;">--:--:--</div>
        </div>
        <script>
        function updateClock() {
            const el = document.getElementById('sb-clock');
            if (el) el.textContent = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Bangkok', hour12: false });
        }
        if (window.clockInterval) clearInterval(window.clockInterval);
        window.clockInterval = setInterval(updateClock, 1000);
        updateClock();
        </script>
        """, unsafe_allow_html=True)

        st.divider()

        # 2. ค้นหาและเลือกสินทรัพย์ (ครอบคลุมทุกกระดานและตลาด)
        st.markdown("### 🔍 ค้นหาสินทรัพย์")
        market_type = st.selectbox("ตลาด", [
            "🟡 คริปโต (Binance)", "🟡 คริปโต (Bitkub)", "🟡 คริปโต (OKX)",
            "🟡 คริปโต (Bybit)", "🟡 คริปโต (Gate.io)", "🟡 คริปโต (MEXC)", "🟡 คริปโต (KuCoin)",
            "🇹🇭 หุ้นไทย (SET)", "🇻🇳 หุ้นเวียดนาม", "🇨🇳 หุ้นจีน", 
            "🇺🇸 หุ้นสหรัฐฯ (S&P500)", "🟠 โภคภัณฑ์ & FX"
        ], key="sb_market_type")

        sym_list = []
        try:
            if "Binance" in market_type:
                sym_list = get_full_binance_symbols() if get_full_binance_symbols else []
            elif "Bitkub" in market_type:
                sym_list = get_full_bitkub_symbols() if get_full_bitkub_symbols else []
            elif "OKX" in market_type:
                sym_list = get_full_okx_symbols() if get_full_okx_symbols else []
            elif "Bybit" in market_type:
                sym_list = get_full_bybit_symbols() if get_full_bybit_symbols else []
            elif "Gate.io" in market_type:
                sym_list = get_full_gate_symbols() if get_full_gate_symbols else []
            elif "MEXC" in market_type:
                sym_list = get_full_mexc_symbols() if get_full_mexc_symbols else []
            elif "KuCoin" in market_type:
                sym_list = get_full_kucoin_symbols() if get_full_kucoin_symbols else []
            elif "หุ้นไทย" in market_type:
                sym_list = ["DELTA.BK", "PTT.BK", "AOT.BK", "ADVANC.BK", "GULF.BK", "PTTEP.BK", "SCB.BK", "KBANK.BK"]
            elif "เวียดนาม" in market_type:
                sym_list = get_full_vietnam_symbols() if get_full_vietnam_symbols else ["VIC.VN", "VHM.VN", "HPG.VN", "FPT.VN"]
            elif "หุ้นจีน" in market_type:
                sym_list = get_full_china_stocks() if get_full_china_stocks else ["0700.HK", "9988.HK", "3690.HK"]
            elif "สหรัฐฯ" in market_type:
                sym_list = get_full_sp500_symbols() if get_full_sp500_symbols else ["NVDA", "AAPL", "MSFT", "AMZN", "TSLA"]
            elif "โภคภัณฑ์" in market_type:
                comms = get_full_commodities() if get_full_commodities else []
                fx = get_full_forex() if get_full_forex else []
                sym_list = list(comms) + list(fx)
        except Exception:
            sym_list = []

        # Fallback ป้องกันการเกิดอาการ No options to select
        if not sym_list:
            sym_list = ["BTCUSDT", "ETHUSDT", "BTC_THB", "GC=F", "USDTHB=X", "NVDA"]

        selected_sym = st.selectbox("เลือกหรือพิมพ์สัญลักษณ์", sym_list, key="sb_symbol_select")
        if st.button("📈 เปิดกราฟสินทรัพย์นี้", use_container_width=True, key="sb_open_sym_btn"):
            st.session_state["current_symbol"] = selected_sym
            existing_ids = [t["symbol"] for t in st.session_state.get("open_tabs", [])]
            if selected_sym not in existing_ids:
                import uuid
                new_id = uuid.uuid4().hex[:8]
                st.session_state.open_tabs.append({"id": new_id, "symbol": selected_sym, "tf": st.session_state.get("selected_tf", "1h")})
                st.session_state.active_tab_id = new_id
            st.rerun()

        st.divider()

        # 3. ตัวควบคุมการตั้งค่า Indicator
        st.markdown("### ⚙️ ตั้งค่าอินดิเคเตอร์")
        st.session_state["fast_ema"] = st.number_input("Fast EMA", min_value=1, max_value=200, value=st.session_state.get("fast_ema", 7))
        st.session_state["slow_ema"] = st.number_input("Slow EMA", min_value=1, max_value=200, value=st.session_state.get("slow_ema", 13))
        st.session_state["trend_ema"] = st.number_input("Trend EMA", min_value=1, max_value=500, value=st.session_state.get("trend_ema", 45))

        st.divider()

        # 4. ตัวควบคุมเปิด/ปิด UI ส่วนหลัก
        show_top = st.toggle("แสดงแถบควบคุมด้านบน (TF/บาร์)", key="show_top_bar", value=True)
        show_tool = st.toggle("แสดงแถบเครื่องมือวาดกราฟ", key="show_draw_toolbar", value=True)

        st.divider()

        # 5. แผงควบคุมระบบล่างสุด
        render_dock_menu()

    return {
        "show_top_bar": show_top,
        "show_draw_toolbar": show_tool
    }