import streamlit as st
from data.symbols import _load_json

# แผนผังเชื่อมไฟล์ JSON ในโฟลเดอร์ data/ ให้ครบทุกกระดาน
CRYPTO_EXCHANGE_FILES = {
    "Binance Spot": "binance_crypto.json",
    "Binance TH": "binance_th_crypto.json",
    "Bitkub": "bitkub_crypto.json",
    "OKX": "okx_crypto.json",
    "Bybit": "bybit_crypto.json",
    "MEXC": "mexc_crypto.json",
    "KuCoin": "kucoin_crypto.json",
    "Gate.io": "gateio_crypto.json",
    "Coinbase": "coinbase_crypto.json",
    "Kraken": "kraken_crypto.json",
}

STOCK_MARKET_FILES = {
    "หุ้นไทย (SET)": "thai_stocks.json",
    "หุ้นสหรัฐฯ (US)": "us_stocks.json",
    "หุ้นจีน (China)": "china_stocks.json",
    "หุ้นเวียดนาม (VN)": "vietnam_stocks.json",
}

@st.dialog("ค้นหาและเลือกสินทรัพย์ (Symbol Search)", width="large")
def render_symbol_modal():
    # 1. แท็บหมวดหมู่หลัก 4 ตลาด
    tab_crypto, tab_stocks, tab_forex, tab_commodities = st.tabs([
        "🪙 คริปโต (10 กระดาน)",
        "📈 ตลาดหุ้น",
        "💱 ฟอเร็กซ์",
        "🛢️ โภคภัณฑ์ / สินค้าเกษตร"
    ])

    symbol_list = []
    current_exchange_name = ""

    # --- แท็บ 1: คริปโต ---
    with tab_crypto:
        ex_names = list(CRYPTO_EXCHANGE_FILES.keys())
        chosen_ex = st.selectbox("เลือกกระดานเทรด (Exchange)", ex_names, index=0, key="modal_crypto_ex_select")
        current_exchange_name = chosen_ex
        json_file = CRYPTO_EXCHANGE_FILES[chosen_ex]
        symbol_list = _load_json(json_file) or []
        if chosen_ex == "Gate.io" and not symbol_list:
            symbol_list = _load_json("gate_crypto.json") or []

    # --- แท็บ 2: หุ้น ---
    with tab_stocks:
        st_names = list(STOCK_MARKET_FILES.keys())
        chosen_st = st.selectbox("เลือกตลาดหุ้น (Market)", st_names, index=0, key="modal_stock_market_select")
        if not symbol_list:
            current_exchange_name = chosen_st
            symbol_list = _load_json(STOCK_MARKET_FILES[chosen_st]) or []

    # --- แท็บ 3: ฟอเร็กซ์ ---
    with tab_forex:
        if not symbol_list:
            current_exchange_name = "Forex"
            symbol_list = _load_json("forex.json") or ["USDTHB=X", "EURUSD=X", "USDJPY=X"]

    # --- แท็บ 4: โภคภัณฑ์ & ข้าว ---
    with tab_commodities:
        sub_other = st.radio("กลุ่มสินค้า", ["สินค้าโภคภัณฑ์ (ทองคำ/น้ำมัน)", "ตลาดข้าวไทยและโลก"], horizontal=True, key="modal_sub_other")
        if not symbol_list:
            if "ข้าว" in sub_other:
                current_exchange_name = "Rice"
                symbol_list = _load_json("rice_catalog.json") or ["RICE:ข้าวเปลือกหอมมะลิ", "ZR=F (CBOT Rough Rice)"]
            else:
                current_exchange_name = "Commodities"
                symbol_list = _load_json("commodities.json") or ["GC=F", "CL=F", "SI=F"]

    # 2. ป้องกันข้อผิดพลาดกรณีโครงสร้าง JSON เป็น Dict
    if isinstance(symbol_list, dict):
        clean_symbols = list(symbol_list.keys())
    else:
        clean_symbols = [str(s) for s in symbol_list if s]

    # 3. ช่องค้นหาชื่อย่อสินทรัพย์แบบ Real-time
    st.write("---")
    col_search, col_count = st.columns([3, 1])
    with col_search:
        search_kw = st.text_input("พิมพ์ชื่อย่อเพื่อค้นหา...", placeholder="เช่น BTC, ETH, DELTA, GC=F", key="modal_quick_search")
    with col_count:
        st.write("")
        st.caption(f"ทั้งหมด: **{len(clean_symbols):,}** รายการ")

    # กรองรายการตามคำค้น
    if search_kw:
        kw = search_kw.strip().upper()
        display_symbols = [s for s in clean_symbols if kw in s.upper()]
    else:
        display_symbols = clean_symbols

    # 4. กล่องแสดงผลรายการแบบสลักความเร็วสูง (เลือกแล้วรีเฟรชกราฟทันที)
    with st.container(height=380):
        if not display_symbols:
            st.warning("ไม่พบสัญลักษณ์ที่ตรงกับคำค้นหา")
        else:
            # แบ่งเป็น Grid 4 คอลัมน์ เพื่อความสะดวกในการคลิกเลือก
            cols_count = 4
            for i in range(0, min(len(display_symbols), 400), cols_count):
                row_cols = st.columns(cols_count)
                for j in range(cols_count):
                    if i + j < len(display_symbols):
                        sym = display_symbols[i + j]
                        if row_cols[j].button(sym, key=f"btn_pick_{current_exchange_name}_{sym}", use_container_width=True):
                            st.session_state["current_symbol"] = sym
                            st.session_state["selected_symbol"] = sym
                            st.rerun()

def get_current_trigger_label():
    sym = st.session_state.get("current_symbol", "BTCUSDT")
    tag = "BINANCE"
    if ".BK" in sym: tag = "SET"
    elif "=" in sym: tag = "FX" if "X" in sym else "COMMODITY"
    elif "_THB" in sym: tag = "BITKUB"
    return f"🔍 {tag} | {sym}"