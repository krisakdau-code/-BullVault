# ui/sidebar.py
import streamlit as st
from ui.dock_menu import render_dock_menu

try:
    from data.symbols import (
        get_full_binance_symbols,
        get_full_binance_th_symbols,
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
except ImportError:
    try:
        from symbols import (
            get_full_binance_symbols,
            get_full_binance_th_symbols,
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
    except ImportError:
        get_full_binance_symbols = get_full_binance_th_symbols = get_full_bitkub_symbols = get_full_okx_symbols = None
        get_full_bybit_symbols = get_full_gate_symbols = get_full_mexc_symbols = None
        get_full_kucoin_symbols = get_full_china_stocks = get_full_commodities = None
        get_full_forex = get_full_sp500_symbols = get_full_vietnam_symbols = None

def render_sidebar():
    with st.sidebar:
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

        st.markdown("### 🔍 ค้นหาสินทรัพย์")
        
        # ขั้นที่ 1: เลือกกลุ่มตลาดหลัก
        main_category = st.selectbox(
            "กลุ่มตลาด", 
            ["🪙 คริปโตเคอร์เรนซี", "📈 หุ้น", "🟠 โภคภัณฑ์ (Commodities)", "💱 อัตราแลกเปลี่ยน (Forex)"], 
            key="sb_main_category"
        )

        # รีเซ็ตค่าเมื่อเปลี่ยนกลุ่มตลาดหลัก
        if "prev_main_cat" not in st.session_state:
            st.session_state["prev_main_cat"] = main_category
        if st.session_state["prev_main_cat"] != main_category:
            st.session_state["prev_main_cat"] = main_category
            for k in ["sb_crypto_exchange", "sb_stock_country", "sb_symbol_select"]:
                if k in st.session_state:
                    del st.session_state[k]

        sym_list = []

        # ขั้นที่ 2: เลือกระบบย่อยตามกลุ่มตลาดหลัก พร้อมกำหนดสีไอคอนกระดานไม่ซ้ำกัน
        if main_category == "🪙 คริปโตเคอร์เรนซี":
            exchange_options = [
                "🟡 Binance", 
                "🟡 Binance TH", 
                "🟢 Bitkub", 
                "🔵 OKX", 
                "🟣 Bybit", 
                "🟠 Gate.io", 
                "🟤 MEXC", 
                "🔴 KuCoin"
            ]
            sub_selection = st.selectbox("เลือกกระดานเทรด", exchange_options, key="sb_crypto_exchange")
            
            try:
                if "Binance TH" in sub_selection and get_full_binance_th_symbols:
                    sym_list = get_full_binance_th_symbols()
                elif sub_selection == "🟡 Binance" and get_full_binance_symbols:
                    sym_list = get_full_binance_symbols()
                elif "Bitkub" in sub_selection and get_full_bitkub_symbols:
                    sym_list = get_full_bitkub_symbols()
                elif "OKX" in sub_selection and get_full_okx_symbols:
                    sym_list = get_full_okx_symbols()
                elif "Bybit" in sub_selection and get_full_bybit_symbols:
                    sym_list = get_full_bybit_symbols()
                elif "Gate.io" in sub_selection and get_full_gate_symbols:
                    sym_list = get_full_gate_symbols()
                elif "MEXC" in sub_selection and get_full_mexc_symbols:
                    sym_list = get_full_mexc_symbols()
                elif "KuCoin" in sub_selection and get_full_kucoin_symbols:
                    sym_list = get_full_kucoin_symbols()
            except Exception:
                sym_list = []

        elif main_category == "📈 หุ้น":
            country_options = [
                "🇹🇭 หุ้นไทย (SET/mai)", 
                "🇺🇸 หุ้นสหรัฐฯ (S&P500)", 
                "🇨🇳 หุ้นจีนและฮ่องกง", 
                "🇻🇳 หุ้นเวียดนาม"
            ]
            sub_selection = st.selectbox("เลือกประเทศ / ตลาดหุ้น", country_options, key="sb_stock_country")
            
            try:
                if "หุ้นไทย" in sub_selection:
                    sym_list = ["DELTA.BK", "PTT.BK", "AOT.BK", "ADVANC.BK", "GULF.BK", "PTTEP.BK", "SCB.BK", "KBANK.BK", "CPALL.BK", "BDMS.BK"]
                elif "หุ้นสหรัฐฯ" in sub_selection and get_full_sp500_symbols:
                    sym_list = get_full_sp500_symbols()
                elif "หุ้นจีน" in sub_selection and get_full_china_stocks:
                    sym_list = get_full_china_stocks()
                elif "เวียดนาม" in sub_selection and get_full_vietnam_symbols:
                    sym_list = get_full_vietnam_symbols()
            except Exception:
                sym_list = []

        elif main_category == "🟠 โภคภัณฑ์ (Commodities)":
            try:
                sym_list = get_full_commodities() if get_full_commodities else ["GC=F", "CL=F", "BZ=F", "SI=F"]
            except Exception:
                sym_list = ["GC=F", "CL=F"]

        elif main_category == "💱 อัตราแลกเปลี่ยน (Forex)":
            try:
                sym_list = get_full_forex() if get_full_forex else ["USDTHB=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X"]
            except Exception:
                sym_list = ["USDTHB=X", "EURUSD=X"]

        if not sym_list:
            sym_list = ["BTCUSDT", "BTC_THB", "GC=F", "USDTHB=X"]

        # ขั้นที่ 3: เลือกรายชื่อสินทรัพย์
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

        st.markdown("### ⚙️ ตั้งค่าอินดิเคเตอร์")
        st.session_state["fast_ema"] = st.number_input("Fast EMA", min_value=1, max_value=200, value=st.session_state.get("fast_ema", 7))
        st.session_state["slow_ema"] = st.number_input("Slow EMA", min_value=1, max_value=200, value=st.session_state.get("slow_ema", 13))
        st.session_state["trend_ema"] = st.number_input("Trend EMA", min_value=1, max_value=500, value=st.session_state.get("trend_ema", 45))

        st.divider()

        show_top = st.toggle("แสดงแถบควบคุมด้านบน (TF/บาร์)", key="show_top_bar", value=True)
        show_tool = st.toggle("แสดงแถบเครื่องมือวาดกราฟ", key="show_draw_toolbar", value=True)

        st.divider()

        render_dock_menu()

    return {
        "show_top_bar": show_top,
        "show_draw_toolbar": show_tool
    }