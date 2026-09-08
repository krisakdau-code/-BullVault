GLOBAL_MARKET = "🌐 Global (Yahoo)"

TF = {
    "1m":  {"sec": 60,        "rule": "1min", "base": None, "yf_iv": "1m",  "yf_range": "7d"},
    "3m":  {"sec": 180,       "rule": "3min", "base": "1m", "yf_iv": "5m",  "yf_range": "60d"},
    "5m":  {"sec": 300,       "rule": "5min", "base": None, "yf_iv": "5m",  "yf_range": "60d"},
    "15m": {"sec": 900,       "rule": "15min","base": None, "yf_iv": "15m", "yf_range": "60d"},
    "30m": {"sec": 1800,      "rule": "30min","base": None, "yf_iv": "30m", "yf_range": "60d"},
    "1h":  {"sec": 3600,      "rule": "1h",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "2h":  {"sec": 7200,      "rule": "2h",   "base": "1h", "yf_iv": "60m", "yf_range": "730d"},
    "3h":  {"sec": 10800,     "rule": "3h",   "base": "1h", "yf_iv": "60m", "yf_range": "730d"},
    "4h":  {"sec": 14400,     "rule": "4h",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "6h":  {"sec": 21600,     "rule": "6h",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "8h":  {"sec": 28800,     "rule": "8h",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "12h": {"sec": 43200,     "rule": "12h",  "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "1d":  {"sec": 86400,     "rule": "1D",   "base": None, "yf_iv": "1d",  "yf_range": "10y"},
    "1w":  {"sec": 604800,    "rule": "1W",   "base": None, "yf_iv": "1wk", "yf_range": "10y"},
    "1M":  {"sec": 2592000,   "rule": "1ME",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
    "3M":  {"sec": 7776000,   "rule": "3ME",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
    "6M":  {"sec": 15552000,  "rule": "6ME",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
    "1Y":  {"sec": 31536000,  "rule": "1YE",  "base": "1d", "yf_iv": "1d",  "yf_range": "max"},
}

TF_OPTIONS = list(TF.keys())
UP, DOWN = "#26a69a", "#ef5350"

COMMODITY_NAMES = {
    "GC=F": "ทองคำ (Gold)", "SI=F": "เงิน (Silver)", "HG=F": "ทองแดง (Copper)",
    "PL=F": "แพลทินัม (Platinum)", "PA=F": "แพลเลเดียม (Palladium)",
    "CL=F": "น้ำมันดิบ WTI", "BZ=F": "น้ำมันดิบ Brent", "NG=F": "ก๊าซธรรมชาติ",
    "RB=F": "น้ำมันเบนซิน", "ZC=F": "ข้าวโพด", "ZW=F": "ข้าวสาลี",
    "ZS=F": "ถั่วเหลือง", "RR=F": "ข้าวเปลือก", "KC=F": "กาแฟ",
    "CC=F": "โกโก้", "SB=F": "น้ำตาล", "CT=F": "ฝ้าย"
}

FOREX_NAMES = {
    "USDTHB=X": "ดอลลาร์ / บาท", "EURTHB=X": "ยูโร / บาท", "JPYTHB=X": "เยน / บาท",
    "GBPTHB=X": "ปอนด์ / บาท", "CNYTHB=X": "หยวน / บาท", "SGDTHB=X": "ดอลลาร์สิงคโปร์ / บาท",
    "EURUSD=X": "EUR / USD", "GBPUSD=X": "GBP / USD", "USDJPY=X": "USD / JPY",
    "USDCHF=X": "USD / CHF", "AUDUSD=X": "AUD / USD", "USDCAD=X": "USD / CAD", "NZDUSD=X": "NZD / USD"
}

CHINA_STOCK_NAMES = {
    "002594.SZ": "BYD (บีวายดี EV)", "300750.SZ": "CATL (แบตเตอรี่ EV)",
    "9866.HK":   "NIO (นีโอ)", "9868.HK":   "XPeng (เสี่ยวเผิง)",
    "2015.HK":   "Li Auto (ลี่ออโต้)", "1810.HK":   "Xiaomi (เสียวหมี่)",
    "600104.SS": "SAIC Motor", "601633.SS": "Great Wall Motor",
    "0700.HK":   "Tencent (เทนเซ็นต์)", "9988.HK":   "Alibaba (อาลีบาบา)",
    "3690.HK":   "Meituan (เหม่ยถวน)", "9618.HK":   "JD.com",
    "9999.HK":   "NetEase", "9888.HK":   "Baidu (ไป่ตู้ AI)",
    "688981.SS": "SMIC (ชิปเบอร์ 1)", "601138.SS": "Foxconn Industrial",
    "002415.SZ": "Hikvision (กล้อง AI)", "600519.SS": "Kweichow Moutai (เหมาไถ)",
    "000858.SZ": "Wuliangye (อู่เหลียงเย่)", "000333.SZ": "Midea Group",
    "000651.SZ": "Gree Electric", "601398.SS": "ICBC ธนาคารจีน",
    "601939.SS": "CCB ธนาคารก่อสร้าง", "601288.SS": "ABC ธนาคารเกษตร",
    "601988.SS": "Bank of China", "600036.SS": "China Merchants Bank",
    "601318.SS": "Ping An Insurance", "601857.SS": "PetroChina",
    "600028.SS": "Sinopec", "601088.SS": "China Shenhua",
    "600900.SS": "Yangtze Power", "601899.SS": "Zijin Mining",
    "600276.SS": "Hengrui Medicine", "300760.SZ": "Mindray Bio-Medical"
}

STAR_CATEGORIES = {
    "🔴 ดาวแดง": {"icon": "🔴", "color": "#ef5350"},
    "🟡 ดาวเหลือง": {"icon": "🟡", "color": "#f5c518"},
    "🟢 ดาวเขียว": {"icon": "🟢", "color": "#26a69a"},
    "🔵 ดาวฟ้า": {"icon": "🔵", "color": "#2962ff"},
    "⚪ ขาว": {"icon": "⚪", "color": "#d1d4dc"}
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}
