import streamlit as st
from data.symbols import _load_json

# ══════════════════════════════════════════════════════════
# พจนานุกรมชื่อบริษัทมาตรฐาน (อังกฤษ : ไทย)
# ══════════════════════════════════════════════════════════
COMPANY_EN_TH = {
    # คริปโต & โภคภัณฑ์
    "BTCUSDT": ("Bitcoin", "บิตคอยน์"),
    "ETHUSDT": ("Ethereum", "อีเธอเรียม"),
    "SOLUSDT": ("Solana", "โซลานา"),
    "BNBUSDT": ("BNB Chain", "เหรียญไบแนนซ์"),
    "DOGEUSDT": ("Dogecoin", "โดจคอยน์"),
    "GC=F": ("Gold", "ทองคำโลก"),
    "SI=F": ("Silver", "โลหะเงิน"),
    "CL=F": ("WTI Crude", "น้ำมันดิบสหรัฐฯ"),
    "BZ=F": ("Brent Crude", "น้ำมันดิบเบรนท์"),
    
    # หุ้นจีนและฮ่องกงยอดนิยม
    "0700.HK": ("Tencent", "เทนเซ็นต์ ยักษ์ใหญ่ไอที"),
    "9988.HK": ("Alibaba", "อาลีบาบา อีคอมเมิร์ซ"),
    "3690.HK": ("Meituan", "เหม่ยถวน แพลตฟอร์มส่งอาหาร"),
    "9618.HK": ("JD.com", "เจดี ดอทคอม ค้าปลีกออนไลน์"),
    "9888.HK": ("Baidu", "ไป่ตู้ เสิร์ชเอนจินและ AI"),
    "9999.HK": ("NetEase", "เน็ตอีส ค่ายเกมยักษ์ใหญ่"),
    "1810.HK": ("Xiaomi", "เสียวหมี่ สมาร์ทโฟน/อุปกรณ์ไอที"),
    "002594.SZ": ("BYD", "บีวายดี ยานยนต์ไฟฟ้า"),
    "1211.HK": ("BYD Company", "บีวายดี ฮ่องกง"),
    "300750.SZ": ("CATL", "หนิงเต๋อ แบตเตอรี่ EV เบอร์ 1 โลก"),
    "2015.HK": ("Li Auto", "หลี่ ออโต้ รถยนต์ไฟฟ้าไฮบริด"),
    "9866.HK": ("NIO", "นีโอ รถยนต์ไฟฟ้าระดับพรีเมียม"),
    "9868.HK": ("XPeng", "เสี่ยวเผิง รถยนต์ไฟฟ้าอัจฉริยะ"),
    "0981.HK": ("SMIC", "ผู้ผลิตชิปเซมิคอนดักเตอร์จีน"),
    "0992.HK": ("Lenovo", "เลอโนโว คอมพิวเตอร์"),
    "600519.SS": ("Kweichow Moutai", "สุราเหมาไถ สุราประจำชาติจีน"),
    "000858.SZ": ("Wuliangye", "อู่เหลียงเย่ สุราชั้นนำ"),
    "601398.SS": ("ICBC", "ธนาคารไอซีบีซี จีน"),
    "1398.HK": ("ICBC HK", "ธนาคารไอซีบีซี ฮ่องกง"),
    "601939.SS": ("China Const Bank", "ธนาคารก่อสร้างจีน CCB"),
    "601288.SS": ("Agri Bank China", "ธนาคารเพื่อการเกษตรจีน ABC"),
    "601988.SS": ("Bank of China", "แบงก์ ออฟ ไชน่า"),
    "600036.SS": ("China Merchants", "ธนาคารเจาซาง"),
    "600000.SS": ("SPD Bank", "ธนาคารผู่ตงเซี่ยงไฮ้"),
    "601318.SS": ("Ping An Ins", "ผิงอัน ประกันภัยและการเงิน"),
    "0941.HK": ("China Mobile", "ไชน่า โมบายล์ สื่อสารเบอร์ 1"),
    "601857.SS": ("PetroChina", "เปโตรไชน่า น้ำมันและก๊าซ"),
    "600028.SS": ("Sinopec", "ซิโนเปก ปิโตรเคมีและโรงกลั่น"),
    "000333.SZ": ("Midea Group", "ไมเดีย เครื่องใช้ไฟฟ้าภายในบ้าน"),
    "000001.SZ": ("Ping An Bank", "ธนาคารผิงอัน เซินเจิ้น"),
    "000002.SZ": ("Vanke", "ว่านเคอ พัฒนาอสังหาริมทรัพย์"),
    "600009.SS": ("Shanghai Airport", "ท่าอากาศยานนานาชาติเซี่ยงไฮ้"),
    "600004.SS": ("Baiyun Airport", "ท่าอากาศยานไป่หยุน กวางโจว"),
    "600019.SS": ("Baosteel", "เป่าสตีล โรงงานเหล็กกล้าแห่งชาติ"),
    "600029.SS": ("China Southern", "สายการบินไชน่า เซาเทิร์น"),
    "600031.SS": ("Sany Heavy", "ซานี่ เครื่องจักรกลหนัก"),
    "600050.SS": ("China Unicom", "ไชน่า ยูนิคอม เครือข่ายโทรคมนาคม"),
    "600276.SS": ("Hengrui Medicine", "เหิงรุ่ย นวัตกรรมยาและเวชภัณฑ์"),
    "600309.SS": ("Wanhua Chemical", "ว่านหัว อุตสาหกรรมเคมีคอล"),
    "600585.SS": ("Conch Cement", "คอนช์ ซีเมนต์ ปูนซีเมนต์")
}

# แปลงชื่อภาษาจีนจากฐานข้อมูลเป็น อังกฤษ และ ไทย
CHINESE_NAME_MAP = {
    "邯郸钢铁": ("Handan Steel", "หานตาน สตีล"), "齐鲁石化": ("Qilu Petrochem", "ฉีหลู่ ปิโตรเคม"),
    "ST东北高": ("Dongbei Express", "ตงเป่ย ไฮเวย์"), "武钢股份": ("Wuhan Steel", "อู่ฮั่น สตีล"),
    "东风股份": ("Dongfeng Auto", "ตงฟง มอเตอร์"), "中国国贸": ("China World Trade", "ไชน่า เวิลด์เทรด"),
    "首创环保": ("Capital Eco", "โส่วชวง สิ่งแวดล้อม"), "包钢股份": ("Baotou Steel", "เปาโถว สตีล"),
    "华能国际": ("Huaneng Power", "หวาเหนิง พาวเวอร์"), "皖通高速": ("Wantong Express", "หว่านทง ไฮเวย์"),
    "华夏银行": ("Huaxia Bank", "ธนาคารหวาเซี่ย"), "民生银行": ("Minsheng Bank", "ธนาคารหมินเซิง"),
    "日照港": ("Rizhao Port", "ท่าเรือรื่อจ้าว"), "上港集团": ("Shanghai Port", "ท่าเรือเซี่ยงไฮ้ SIPG"),
    "中原高速": ("Zhongyuan Express", "จงหยวน ไฮเวย์"), "上海电力": ("Shanghai Electric", "การไฟฟ้าเซี่ยงไฮ้"),
    "山东钢铁": ("Shandong Steel", "ชานตง สตีล"), "浙能电力": ("Zheneng Electric", "เจ้อเหนิง พาวเวอร์"),
    "华能水电": ("Huaneng Hydro", "หวาเหนิง พลังน้ำ"), "中远海能": ("COSCO Energy", "คอสโค ขนส่งพลังงาน"),
    "华电国际": ("Huadian Power", "หวาเตี้ยน อินเตอร์"), "福建高速": ("Fujian Express", "ทางด่วนฝูเจี้ยน"),
    "楚天高速": ("Chutian Express", "ฉู่เทียน ทางด่วน"), "歌华有线": ("Gehua CATV", "เกอหวา เคเบิลทีวี"),
    "中直股份": ("AVICopter", "เอวิคอปเตอร์ อากาศยาน"), "四川路桥": ("Sichuan Bridge", "เสฉวน ถนนและสะพาน"),
    "保利发展": ("Poly Real Estate", "โพลี่ อสังหาริมทรัพย์"), "宁波联合": ("Ningbo United", "หนิงโป ยูไนเต็ด"),
    "黄山旅游": ("Huangshan Tour", "ท่องเที่ยวเขาหวงซาน"), "万东医疗": ("Wandong Medical", "ว่านตง การแพทย์"),
    "中国医药": ("China Meheco", "ไชน่า เมเฮโค เภสัชกรรม"), "厦门象屿": ("Xiamen Xiangyu", "เซี่ยเหมิน เซียงอวี่"),
    "五矿发展": ("Minmetals Dev", "มินเมทัลส์ ดีเวลลอป"), "古越龙山": ("Guyuelongshan", "กู่เย่ว์หลงซาน สุราจีน"),
    "海信视像": ("Hisense Visual", "ไฮเซ่นส์ ทีวีและจอภาพ"), "国投资本": ("SDIC Capital", "เอสดีไอซี การเงิน"),
    "华润双鹤": ("CR Double-Crane", "หัวรุ่น ยาและเวชภัณฑ์"), "皖维高新": ("Wanwei Hi-Tech", "หว่านเหวย ไฮเทค"),
    "南京高科": ("Nanjing Hi-Tech", "หนานจิง ไฮเทค"), "宇通客车": ("Yutong Bus", "ยวี่ทง รถบัสไฟฟ้า"),
    "中船科技": ("CSSC Science", "ต่อเรือแห่งชาติจีน"), "光明肉业": ("Bright Meat", "กวางหมิง ผลิตภัณฑ์เนื้อ"),
    "新疆天业": ("Xinjiang Tianye", "ซินเจียง เทียนเย่ เคมี"), "同仁堂": ("Tongrentang", "ถงเหรินถัง ยาสมุนไพรจีน"),
    "特变电工": ("TBEA Electric", "ทีบีอีเอ ส่งไฟฟ้าแรงสูง"), "云天化": ("Yuntianhua", "หยุนเทียนหัว ปุ๋ยและเคมี"),
    "中国东航": ("China Eastern", "ไชน่า อีสเทิร์น แอร์ไลน์"), "中国卫星": ("China Satellite", "ไชน่า แซตเทิลไลท์"),
    "中国船舶": ("China Ship", "ไชน่า สเตท ชิปบิลดิ้ง"), "航天机电": ("HT-SAAE Solar", "แอโรสเปซ โซลาร์เซลล์"),
    "福田汽车": ("Foton Motor", "โฟตอน ยานยนต์พาณิชย์"), "上海建工": ("Shanghai Const", "เซี่ยงไฮ้ คอนสตรัคชั่น"),
    "生益科技": ("Shengyi Tech", "เซิงอี้ แผงวงจรไอที"), "兖矿能源": ("Yankuang Energy", "เหยียนข矿 ถ่านหิน"),
    "复星医药": ("Fosun Pharma", "ฟู่ซิง ชีวเวชภัณฑ์"), "海航控股": ("Hainan Air", "สายการบินไห่หนาน แอร์ไลน์"),
    "圆通速递": ("YTO Express", "วายทีโอ โลจิสติกส์พัสดุ"), "广汇能源": ("Guanghui Energy", "กว่างฮุ่ย ก๊าซธรรมชาติ"),
    "安琪酵母": ("Angel Yeast", "แองเจิล ยีสต์ อาหาร"), "江西铜业": ("Jiangxi Copper", "เจียงซี เหมืองทองแดง"),
    "片仔癀": ("Pien Tze Huang", "เพียนจื่อหวง ยาจีนโบราณ"), "通威股份": ("Tongwei Solar", "ทงเว่ย โซลาร์เซลล์"),
    "士兰微": ("Silan Micro", "ซีหลาน ชิปเซมิคอนดักเตอร์"), "中金黄金": ("China Gold", "ไชน่า โกลด์ เหมืองทอง"),
    "海螺水泥": ("Conch Cement", "คอนช์ ปูนซีเมนต์")
}

CRYPTO_EXCHANGE_FILES = {
    "Binance Spot": "binance_crypto.json", "Binance TH": "binance_th_crypto.json", "Bitkub": "bitkub_crypto.json",
    "OKX": "okx_crypto.json", "Bybit": "bybit_crypto.json", "MEXC": "mexc_crypto.json", "KuCoin": "kucoin_crypto.json",
    "Gate.io": "gateio_crypto.json", "Coinbase": "coinbase_crypto.json", "Kraken": "kraken_crypto.json",
}

# รายชื่อไฟล์หุ้นรายประเทศทั้งหมดในโฟลเดอร์ data/
STOCK_MARKET_FILES = {
    "หุ้นไทย (SET)": "thai_stocks.json", 
    "หุ้นสหรัฐฯ (US)": "us_stocks.json",
    "หุ้นจีน (China)": "china_stocks.json", 
    "หุ้นเวียดนาม (VN)": "vietnam_stocks.json",
    "🇯🇵 หุ้นญี่ปุ่น (TSE)": "japan_stocks.json",
    "🇰🇷 หุ้นเกาหลีใต้ (KRX)": "korea_stocks.json",
    "🇮🇳 หุ้นอินเดีย (NSE)": "india_stocks.json",
    "🇩🇪 หุ้นเยอรมนี (XETRA)": "germany_stocks.json",
    "🇬🇧 หุ้นสหราชอาณาจักร (LSE)": "uk_stocks.json",
    "🇫🇷 หุ้นฝรั่งเศส (Euronext)": "france_stocks.json",
    "🇮🇹 หุ้นอิตาลี (Borsa Italiana)": "italy_stocks.json",
    "🇪🇸 หุ้นสเปน (BME Madrid)": "spain_stocks.json"
}

DEFAULT_FOREX = ["USDTHB=X", "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", "USDCHF=X", "USDCAD=X", "EURGBP=X"]
DEFAULT_COMMODITIES = ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F"]

@st.dialog("ค้นหาและเลือกสินทรัพย์ (Symbol Search)", width="large")
def render_symbol_modal():
    st.markdown("""
    <style>
        div[data-testid="stDialog"] div[role="radiogroup"],
        div[data-testid="stModal"] div[role="radiogroup"] {
            display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
            overflow-x: auto !important; -webkit-overflow-scrolling: touch !important;
            gap: 10px !important; padding-bottom: 6px !important; margin-bottom: 4px !important;
        }
        div[data-testid="stDialog"] div[role="radiogroup"] > label,
        div[data-testid="stModal"] div[role="radiogroup"] > label {
            flex: 0 0 auto !important; white-space: nowrap !important;
            background: rgba(255, 255, 255, 0.05) !important; padding: 4px 10px !important;
            border-radius: 16px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        div[data-testid="stDialog"] button,
        div[data-testid="stModal"] button {
            white-space: normal !important;
            word-break: break-word !important;
            height: auto !important;
            min-height: 52px !important;
            padding: 6px 8px !important;
            text-align: left !important;
            line-height: 1.25 !important;
            display: flex !important;
            align-items: center !important;
        }
        div[data-testid="stDialog"] button p,
        div[data-testid="stModal"] button p {
            white-space: normal !important;
            text-align: left !important;
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)

    market_category = st.radio(
        "เลือกหมวดหมู่ตลาด",
        ["🪙 คริปโต (10 กระดาน)", "📈 ตลาดหุ้น", "💱 ฟอเร็กซ์", "🛢️ โภคภัณฑ์ / สินค้าเกษตร"],
        horizontal=True, label_visibility="collapsed", key="modal_main_market_category"
    )

    symbol_raw_data = []
    current_market_tag = "CRYPTO"

    if "คริปโต" in market_category:
        ex_names = list(CRYPTO_EXCHANGE_FILES.keys())
        chosen_ex = st.selectbox("เลือกกระดานเทรด (Exchange)", ex_names, index=0, key="modal_crypto_ex_select")
        current_market_tag = chosen_ex
        symbol_raw_data = _load_json(CRYPTO_EXCHANGE_FILES[chosen_ex]) or []
        if chosen_ex == "Gate.io" and not symbol_raw_data:
            symbol_raw_data = _load_json("gate_crypto.json") or []

    elif "ตลาดหุ้น" in market_category:
        st_names = list(STOCK_MARKET_FILES.keys())
        chosen_st = st.selectbox("เลือกตลาดหุ้น (Market)", st_names, index=0, key="modal_stock_market_select")
        current_market_tag = chosen_st
        symbol_raw_data = _load_json(STOCK_MARKET_FILES[chosen_st]) or []

    elif "ฟอเร็กซ์" in market_category:
        current_market_tag = "FOREX"
        symbol_raw_data = _load_json("forex.json") or DEFAULT_FOREX

    elif "โภคภัณฑ์" in market_category:
        sub_other = st.selectbox(
            "เลือกกลุ่มสินค้า / ประเทศคู่แข่ง",
            ["🌾 ข้าวไทย (หน้าโรงสี)", "🇹🇭 ข้าวไทยส่งออก (FOB)", "🇻🇳 ข้าวเวียดนาม (FOB)", "🇮🇳 ข้าวอินเดีย (FOB)", "🇵🇰 ข้าวปากีสถาน / กัมพูชา / เมียนมา (FOB)", "🌐 ตลาดอนุพันธ์โลก (CBOT)", "🛢️ โภคภัณฑ์สากล (ทองคำ/น้ำมัน)"],
            index=0, key="modal_sub_other_select"
        )
        if "ข้าวไทย (หน้าโรงสี)" in sub_other:
            current_market_tag = "RICE_TH"
            symbol_raw_data = ["RICE:ข้าวเปลือกหอมมะลิ", "RICE:ข้าวเปลือกเจ้า5%", "RICE:ข้าวเปลือกปทุมธานี1", "RICE:ข้าวเปลือกเหนียว"]
        elif "ข้าวไทยส่งออก" in sub_other:
            current_market_tag = "FOB_TH"
            symbol_raw_data = ["FOB:TH_HOM_MALI", "FOB:TH_WHITE_5%", "FOB:TH_WHITE_25%", "FOB:TH_PARBOILED", "FOB:TH_BROKEN_A1"]
        elif "ข้าวเวียดนาม" in sub_other:
            current_market_tag = "FOB_VN"
            symbol_raw_data = ["FOB:VN_ST25", "FOB:VN_JASMINE85", "FOB:VN_DT8", "FOB:VN_WHITE_5%", "FOB:VN_WHITE_25%", "FOB:VN_BROKEN_100%"]
        elif "ข้าวอินเดีย" in sub_other:
            current_market_tag = "FOB_IN"
            symbol_raw_data = ["FOB:IN_BASMATI_1121", "FOB:IN_WHITE_5%", "FOB:IN_WHITE_25%", "FOB:IN_PARBOILED_5%", "FOB:IN_BROKEN_100%"]
        elif "ข้าวปากีสถาน" in sub_other:
            current_market_tag = "FOB_OTHER"
            symbol_raw_data = ["FOB:PK_BASMATI_SUPER", "FOB:PK_WHITE_5%", "FOB:PK_WHITE_25%", "FOB:KH_PHKA_RUMDUOL", "FOB:MM_EMATA_5%"]
        elif "ตลาดอนุพันธ์โลก" in sub_other:
            current_market_tag = "CBOT"
            symbol_raw_data = ["ZR=F"]
        else:
            current_market_tag = "COMMODITY"
            symbol_raw_data = _load_json("commodities.json") or DEFAULT_COMMODITIES

    clean_symbols = []
    symbol_name_map = {}

    if isinstance(symbol_raw_data, dict):
        clean_symbols = list(symbol_raw_data.keys())
        symbol_name_map = {k: str(v) for k, v in symbol_raw_data.items() if v}
    elif isinstance(symbol_raw_data, list):
        clean_symbols = [str(s) for s in symbol_raw_data if s]

    def _get_display_names(s_code):
        if s_code in COMPANY_EN_TH:
            return COMPANY_EN_TH[s_code]
        
        raw_val = symbol_name_map.get(s_code, "").strip()
        if raw_val in CHINESE_NAME_MAP:
            return CHINESE_NAME_MAP[raw_val]
        
        if "(" in raw_val and ")" in raw_val:
            en_part = raw_val.split("(")[0].strip()
            th_part = raw_val.split("(")[1].replace(")", "").strip()
            return en_part, th_part
        
        num = s_code.split('.')[0]
        if s_code.endswith('.SS'):
            return f"SSE {num}", f"บมจ. เซี่ยงไฮ้ ({raw_val or num})"
        elif s_code.endswith('.SZ'):
            return f"SZSE {num}", f"บมจ. เซินเจิ้น ({raw_val or num})"
        elif s_code.endswith('.HK'):
            return f"HKEX {num}", f"บมจ. ฮ่องกง ({raw_val or num})"
        return s_code, raw_val

    st.write("---")
    col_search, col_count = st.columns([3, 1])
    with col_search:
        search_kw = st.text_input("พิมพ์ชื่อบริษัทหรือรหัสเพื่อค้นหา...", placeholder="เช่น ICBC, Tencent, BYD, Toyota, SAP, 7203", key="modal_filter_input")
    with col_count:
        st.write("")
        st.caption(f"ทั้งหมด: **{len(clean_symbols):,}** รายการ")

    if search_kw:
        kw = search_kw.strip().upper()
        display_symbols = [
            s for s in clean_symbols 
            if kw in s.upper() or kw in _get_display_names(s)[0].upper() or kw in _get_display_names(s)[1].upper()
        ]
    else:
        display_symbols = clean_symbols

    with st.container(height=380):
        if not display_symbols:
            st.warning(f"ไม่พบรายการสินทรัพย์ในหมวด {current_market_tag}")
        else:
            wl_syms = set(item[0] for item in st.session_state.get("custom_watchlist", []))
            cols_count = 2
            for i in range(0, min(len(display_symbols), 1000), cols_count):
                row_cols = st.columns(cols_count)
                for j in range(cols_count):
                    if i + j < len(display_symbols):
                        sym = display_symbols[i + j]
                        in_wl = sym in wl_syms
                        en_name, th_name = _get_display_names(sym)
                        icon = "✓ " if in_wl else "➕ "

                        btn_label = f"{icon}**{en_name}**\n:gray[{th_name}]"

                        with row_cols[j]:
                            if st.button(btn_label, key=f"btn_m_{current_market_tag}_{sym}", use_container_width=True):
                                # ย้ายการ Import เข้ามาในปุ่มเพื่อป้องกัน Circular Import
                                from ui.sidebar_refactored import add_to_watchlist
                                add_to_watchlist(sym)
                                
                                st.session_state["current_symbol"] = sym
                                st.session_state["selected_symbol"] = sym
                                for t in st.session_state.get("chart_tabs", []):
                                    if t.get("id") == st.session_state.get("active_tab_id"):
                                        t["symbol"] = sym
                                st.rerun()