import streamlit as st
from data.symbols import _load_json

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

DEFAULT_FOREX = ["USDTHB=X", "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", "USDCHF=X", "USDCAD=X", "EURGBP=X"]
DEFAULT_COMMODITIES = ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F"]
DEFAULT_RICE = ["RICE:ข้าวเปลือกหอมมะลิ", "RICE:ข้าวสาร 5%", "ZR=F (CBOT Rough Rice)"]

@st.dialog("ค้นหาและเลือกสินทรัพย์ (Symbol Search)", width="large")
def render_symbol_modal():
    # 1. ตัวเลือกหมวดหมู่หลัก 4 ตลาด (ส่งค่าเข้า Python ได้ทันที)
    market_category = st.radio(
        "เลือกหมวดหมู่ตลาด",
        ["🪙 คริปโต (10 กระดาน)", "📈 ตลาดหุ้น", "💱 ฟอเร็กซ์", "🛢️ โภคภัณฑ์ / สินค้าเกษตร"],
        horizontal=True,
        label_visibility="collapsed",
        key="modal_main_market_category"
    )

    symbol_list = []
    current_market_tag = "CRYPTO"

    # 2. แยกโหลดข้อมูลตามตลาดที่เลือกอย่างแท้จริง
    if "คริปโต" in market_category:
        ex_names = list(CRYPTO_EXCHANGE_FILES.keys())
        chosen_ex = st.selectbox("เลือกกระดานเทรด (Exchange)", ex_names, index=0, key="modal_crypto_ex_select")
        current_market_tag = chosen_ex
        json_file = CRYPTO_EXCHANGE_FILES[chosen_ex]
        symbol_list = _load_json(json_file) or []
        if chosen_ex == "Gate.io" and not symbol_list:
            symbol_list = _load_json("gate_crypto.json") or []

    elif "ตลาดหุ้น" in market_category:
        st_names = list(STOCK_MARKET_FILES.keys())
        chosen_st = st.selectbox("เลือกตลาดหุ้น (Market)", st_names, index=0, key="modal_stock_market_select")
        current_market_tag = chosen_st
        symbol_list = _load_json(STOCK_MARKET_FILES[chosen_st]) or []

    elif "ฟอเร็กซ์" in market_category:
        current_market_tag = "FOREX"
        symbol_list = _load_json("forex.json") or DEFAULT_FOREX

    elif "โภคภัณฑ์" in market_category:
        sub_other = st.radio("กลุ่มสินค้า", ["สินค้าโภคภัณฑ์ (ทองคำ/น้ำมัน)", "ตลาดข้าวไทยและโลก"], horizontal=True, key="modal_sub_other_choice")
        if "ข้าว" in sub_other:
            current_market_tag = "RICE"
            symbol_list = _load_json("rice_catalog.json") or DEFAULT_RICE
        else:
            current_market_tag = "COMMODITY"
            symbol_list = _load_json("commodities.json") or DEFAULT_COMMODITIES

    # 3. จัดการโครงสร้างข้อมูลกรณีเป็น Dict หรือ List
    if isinstance(symbol_list, dict):
        clean_symbols = list(symbol_list.keys())
    elif isinstance(symbol_list, list):
        clean_symbols = [str(s) for s in symbol_list if s]
    else:
        clean_symbols = []

    # 4. กล่องค้นหา
    st.write("---")
    col_search, col_count = st.columns([3, 1])
    with col_search:
        search_kw = st.text_input("พิมพ์ชื่อย่อเพื่อค้นหา...", placeholder="เช่น USD, GC=F, DELTA, BTC", key="modal_filter_input")
    with col_count:
        st.write("")
        st.caption(f"ทั้งหมด: **{len(clean_symbols):,}** รายการ")

    # กรองตามคำค้น
    if search_kw:
        kw = search_kw.strip().upper()
        display_symbols = [s for s in clean_symbols if kw in s.upper()]
    else:
        display_symbols = clean_symbols

    # 5. แสดงผลปุ่มกดเลือกสินทรัพย์
    with st.container(height=380):
        if not display_symbols:
            st.warning(f"ไม่พบรายการสินทรัพย์ในหมวด {current_market_tag}")
        else:
            cols_count = 4
            for i in range(0, min(len(display_symbols), 400), cols_count):
                row_cols = st.columns(cols_count)
                for j in range(cols_count):
                    if i + j < len(display_symbols):
                        sym = display_symbols[i + j]
                        if row_cols[j].button(sym, key=f"btn_m_{current_market_tag}_{sym}", use_container_width=True):
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