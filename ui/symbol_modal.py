import streamlit as st
from data.symbols import _load_json

# ══════════════════════════════════════════════════════════
# พจนานุกรมชื่อภาษาไทยสำหรับแสดงผล 2 บรรทัดและค้นหาภาษาไทย
# ══════════════════════════════════════════════════════════
SYMBOL_NAMES_TH = {
    # โภคภัณฑ์
    "GC=F": "ทองคำโลก (Gold)",
    "SI=F": "โลหะเงิน (Silver)",
    "PL=F": "แพลทินัม (Platinum)",
    "HG=F": "ทองแดง (Copper)",
    "CL=F": "น้ำมันดิบ WTI Crude",
    "BZ=F": "น้ำมันดิบ Brent Crude",
    "NG=F": "ก๊าซธรรมชาติ (Natural Gas)",
    "ZC=F": "ข้าวโพด (Corn)",
    "ZS=F": "ถั่วเหลือง (Soybeans)",
    "ZW=F": "ข้าวสาลี (Wheat)",
    # ข้าว
    "RICE:ข้าวเปลือกหอมมะลิ": "ข้าวเปลือกหอมมะลิ 105",
    "RICE:ข้าวเปลือกเจ้า5%": "ข้าวเปลือกเจ้า 5%",
    "RICE:ข้าวเปลือกปทุมธานี1": "ข้าวเปลือกหอมปทุมธานี 1",
    "RICE:ข้าวเปลือกเหนียว": "ข้าวเปลือกเหนียว กข6",
    "FOB:TH_HOM_MALI": "ข้าวหอมมะลิไทย 100% เกรด B",
    "FOB:TH_WHITE_5%": "ข้าวขาวไทย 5%",
    "FOB:TH_WHITE_25%": "ข้าวขาวไทย 25%",
    "FOB:TH_PARBOILED": "ข้าวนึ่งไทย 5%",
    "FOB:TH_BROKEN_A1": "ข้าวหักไทย A1 เลิศ",
    "FOB:VN_WHITE_5%": "ข้าวขาวเวียดนาม 5%",
    "FOB:VN_JASMINE85": "ข้าวหอมจัสมิน เวียดนาม",
    "FOB:IN_WHITE_5%": "ข้าวขาวอินเดีย 5%",
    "FOB:IN_BASMATI_1121": "ข้าวบาสมาตี อินเดีย",
    "FOB:PK_WHITE_5%": "ข้าวขาวปากีสถาน 5%",
    "FOB:KH_PHKA_RUMDUOL": "ข้าวหอมผการำดวน กัมพูชา",
    # ฟอเร็กซ์
    "USDTHB=X": "ดอลลาร์สหรัฐ / บาทไทย",
    "EURUSD=X": "ยูโร / ดอลลาร์สหรัฐ",
    "USDJPY=X": "ดอลลาร์สหรัฐ / เยนญี่ปุ่น",
    "GBPUSD=X": "ปอนด์สเตอร์ลิง / ดอลลาร์",
    "AUDUSD=X": "ดอลลาร์ออสเตรเลีย / ดอลลาร์",
    "USDCHF=X": "ดอลลาร์สหรัฐ / ฟรังก์สวิส",
    "USDCAD=X": "ดอลลาร์สหรัฐ / ดอลลาร์แคนาดา",
    "EURGBP=X": "ยูโร / ปอนด์สเตอร์ลิง",
    # หุ้นไทยยอดนิยม
    "ADVANC.BK": "บมจ.แอดวานซ์ อินโฟร์ เซอร์วิส",
    "AOT.BK": "บมจ.ท่าอากาศยานไทย",
    "CPALL.BK": "บมจ.ซีพี ออลล์",
    "DELTA.BK": "บมจ.เดลต้า อีเลคโทรนิคส์",
    "KBANK.BK": "ธนาคารกสิกรไทย",
    "PTT.BK": "บมจ.ปตท.",
    "SCB.BK": "บมจ.เอสซีบี เอกซ์",
    # คริปโตหลัก
    "BTCUSDT": "Bitcoin (บิตคอยน์)",
    "ETHUSDT": "Ethereum (อีเธอเรียม)",
    "SOLUSDT": "Solana (โซลานา)",
    "BNBUSDT": "BNB Chain",
    "DOGEUSDT": "Dogecoin (โดจคอยน์)",
}

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
    # 1. ตัวเลือกหมวดหมู่หลัก 4 ตลาด
    market_category = st.radio(
        "เลือกหมวดหมู่ตลาด",
        ["🪙 คริปโต (10 กระดาน)", "📈 ตลาดหุ้น", "💱 ฟอเร็กซ์", "🛢️ โภคภัณฑ์ / สินค้าเกษตร"],
        horizontal=True,
        label_visibility="collapsed",
        key="modal_main_market_category"
    )

    symbol_list = []
    current_market_tag = "CRYPTO"

    # 2. แยกโหลดข้อมูลตามตลาดที่เลือก
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
        sub_other = st.selectbox(
            "เลือกกลุ่มสินค้า / ประเทศคู่แข่ง",
            [
                "🌾 ข้าวไทย (หน้าโรงสี)",
                "🇹🇭 ข้าวไทยส่งออก (FOB)",
                "🇻🇳 ข้าวเวียดนาม (FOB)",
                "🇮🇳 ข้าวอินเดีย (FOB)",
                "🇵🇰 ข้าวปากีสถาน / กัมพูชา / เมียนมา (FOB)",
                "🌐 ตลาดอนุพันธ์โลก (CBOT)",
                "🛢️ โภคภัณฑ์สากล (ทองคำ/น้ำมัน)"
            ],
            index=0,
            key="modal_sub_other_select"
        )
        
        if "ข้าวไทย (หน้าโรงสี)" in sub_other:
            current_market_tag = "RICE_TH"
            symbol_list = [
                "RICE:ข้าวเปลือกหอมมะลิ",
                "RICE:ข้าวเปลือกเจ้า5%",
                "RICE:ข้าวเปลือกปทุมธานี1",
                "RICE:ข้าวเปลือกเหนียว"
            ]
        elif "ข้าวไทยส่งออก" in sub_other:
            current_market_tag = "FOB_TH"
            symbol_list = [
                "FOB:TH_HOM_MALI",
                "FOB:TH_WHITE_5%",
                "FOB:TH_WHITE_25%",
                "FOB:TH_PARBOILED",
                "FOB:TH_BROKEN_A1"
            ]
        elif "ข้าวเวียดนาม" in sub_other:
            current_market_tag = "FOB_VN"
            symbol_list = [
                "FOB:VN_ST25",
                "FOB:VN_JASMINE85",
                "FOB:VN_DT8",
                "FOB:VN_WHITE_5%",
                "FOB:VN_WHITE_25%",
                "FOB:VN_BROKEN_100%"
            ]
        elif "ข้าวอินเดีย" in sub_other:
            current_market_tag = "FOB_IN"
            symbol_list = [
                "FOB:IN_BASMATI_1121",
                "FOB:IN_WHITE_5%",
                "FOB:IN_WHITE_25%",
                "FOB:IN_PARBOILED_5%",
                "FOB:IN_BROKEN_100%"
            ]
        elif "ข้าวปากีสถาน" in sub_other:
            current_market_tag = "FOB_OTHER"
            symbol_list = [
                "FOB:PK_BASMATI_SUPER",
                "FOB:PK_WHITE_5%",
                "FOB:PK_WHITE_25%",
                "FOB:KH_PHKA_RUMDUOL",
                "FOB:MM_EMATA_5%"
            ]
        elif "ตลาดอนุพันธ์โลก" in sub_other:
            current_market_tag = "CBOT"
            symbol_list = ["ZR=F"]
        else:
            current_market_tag = "COMMODITY"
            symbol_list = _load_json("commodities.json") or DEFAULT_COMMODITIES

    # 3. จัดการโครงสร้างข้อมูล
    if isinstance(symbol_list, dict):
        clean_symbols = list(symbol_list.keys())
    elif isinstance(symbol_list, list):
        clean_symbols = [str(s) for s in symbol_list if s]
    else:
        clean_symbols = []

    # 4. กล่องค้นหา (รองรับค้นหาทั้งรหัสและชื่อภาษาไทย)
    st.write("---")
    col_search, col_count = st.columns([3, 1])
    with col_search:
        search_kw = st.text_input("พิมพ์ชื่อย่อเพื่อค้นหา...", placeholder="เช่น USD, GC=F, DELTA, BTC, ทองคำ, ข้าว", key="modal_filter_input")
    with col_count:
        st.write("")
        st.caption(f"ทั้งหมด: **{len(clean_symbols):,}** รายการ")

    # กรองตามคำค้น (เช็กทั้งรหัสสัญลักษณ์และคำอธิบายภาษาไทย)
    if search_kw:
        kw = search_kw.strip().upper()
        display_symbols = [
            s for s in clean_symbols 
            if kw in s.upper() or (s in SYMBOL_NAMES_TH and kw in SYMBOL_NAMES_TH[s].upper())
        ]
    else:
        display_symbols = clean_symbols

    # 5. แสดงผลปุ่มกดเลือกสินทรัพย์ (แถบการ์ดปุ่มเดียว Single Action Card รวมชื่อและปุ่มบวก)
    with st.container(height=380):
        if not display_symbols:
            st.warning(f"ไม่พบรายการสินทรัพย์ในหมวด {current_market_tag}")
        else:
            wl_syms = set(item[0] for item in st.session_state.get("custom_watchlist", []))

            cols_count = 2
            for i in range(0, min(len(display_symbols), 400), cols_count):
                row_cols = st.columns(cols_count)
                for j in range(cols_count):
                    if i + j < len(display_symbols):
                        sym = display_symbols[i + j]
                        in_wl = sym in wl_syms
                        
                        # รวมไอคอนสถานะ + ชื่อเหรียญ + คำอธิบาย เป็นการ์ดปุ่มเดียว
                        th_name = SYMBOL_NAMES_TH.get(sym)
                        icon = "✓ " if in_wl else "➕ "
                        btn_label = f"{icon}**{sym}**  \n:gray[{th_name}]" if th_name else f"{icon}**{sym}**"

                        with row_cols[j]:
                            if st.button(btn_label, key=f"btn_m_{current_market_tag}_{sym}", use_container_width=True):
                                if "custom_watchlist" not in st.session_state:
                                    st.session_state["custom_watchlist"] = []
                                if not in_wl:
                                    st.session_state["custom_watchlist"].append((sym, "--", "0.00%", True))
                                
                                st.session_state["current_symbol"] = sym
                                st.session_state["selected_symbol"] = sym
                                for t in st.session_state.get("chart_tabs", []):
                                    if t.get("id") == st.session_state.get("active_tab_id"):
                                        t["symbol"] = sym
                                st.rerun()