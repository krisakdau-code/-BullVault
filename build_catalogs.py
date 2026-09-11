import json
import os
import requests

os.makedirs("data", exist_ok=True)

# 1. หุ้นไทย SET + mai (ชื่อหุ้นจริง)
print("1. กำลังสร้างฐานข้อมูลหุ้นไทย (SET/mai)...")
THAI_BASE = [
    "24CS", "2S", "3K-BAT", "7UP", "A", "A5", "AAI", "AAV", "ABICO", "ABM", "ACAP", "ACC", "ACE", 
    "ACG", "ADB", "ADD", "ADVANC", "AEC", "AEONTS", "AF", "AFC", "AGE", "AH", "AHC", "AI", "AIE", 
    "AIRA", "AIT", "AJ", "AJA", "AKP", "AKR", "ALL", "ALLA", "ALPHAX", "ALT", "ALUCON", "AMA", 
    "AMARIN", "AMATA", "AMATAV", "AMC", "AMR", "ANAN", "AOT", "AP", "APCO", "APCS", "APEX", "APP", 
    "APURE", "AQ", "AQUA", "ARIN", "ARROW", "AS", "ASAP", "ASEFA", "ASIA", "ASIAN", "ASIMAR", "ASK", 
    "ASN", "ASP", "ASW", "ATP30", "AU", "AUCT", "AURA", "AWC", "AYUD", "B", "B52", "BA", "BAFS", 
    "BAM", "BANPU", "BAY", "BBGI", "BBIK", "BBL", "BC", "BCH", "BCP", "BCPG", "BCT", "BDMS", "BE8", 
    "BEAUTY", "BEM", "BEYOND", "BFIT", "BGC", "BGRIM", "BGT", "BH", "BIG", "BIOTEC", "BIS", "BIZ", 
    "BJC", "BJCHI", "BKD", "BKI", "BKWK", "BLA", "BLAND", "BLISS", "BM", "BOL", "BPP", "BR", "BRI", 
    "BRR", "BRRGIF", "BSBM", "BTNC", "BTG", "BTS", "BTSGIF", "BTW", "BUI", "BWG", "BYD", "CAZ", 
    "CBG", "CCET", "CCP", "CEN", "CENTEL", "CFRESH", "CGD", "CGH", "CH", "CHAO", "CHARAN", "CHAYO", 
    "CHG", "CHIC", "CHOTI", "CHOW", "CI", "CIG", "CIMBT", "CITY", "CIVIL", "CK", "CKP", "CM", "CMAN", 
    "CMC", "CMO", "CMR", "CNT", "COLOR", "COMAN", "COCOCO", "CPALL", "CPAXT", "CPF", "CPG", "CPI", 
    "CPL", "CPN", "CPNCG", "CPNREIT", "CPR", "CPT", "CPW", "CRANE", "CRC", "CRD", "CSC", "CSP", 
    "CSR", "CSS", "CTW", "CV", "CWT", "D", "DCC", "DCON", "DDD", "DELTA", "DEMCO", "DEXON", "DHOUSE", 
    "DIF", "DIMET", "DITTO", "DMT", "DOD", "DOHOME", "DPAINT", "DRT", "DTCENT", "DTCI", "DV8", 
    "EA", "EAC", "EASTW", "ECF", "ECL", "EE", "EFORL", "EGATIF", "EGCO", "EKH", "EMC", "EP", "EPG", 
    "ERW", "ESSO", "ESTAR", "ETC", "ETE", "EURO", "EVER", "F&D", "FANCY", "FE", "FLOYD", "FMT", 
    "FN", "FNS", "FORTH", "FPI", "FPT", "FSMART", "FSX", "FTE", "FTI", "FTREIT", "FUTUREPF", "FVC", 
    "GBX", "GC", "GCAP", "GEL", "GENCO", "GENI", "GFPT", "GGC", "GIFT", "GL", "GLAND", "GLOBAL", 
    "GLOCON", "GLOW", "GPSC", "GRAMMY", "GRAND", "GREEN", "GSC", "GTB", "GTV", "GULF", "GUNKUL", 
    "GYT", "HANA", "HARN", "HENG", "HFT", "HIGH", "HMPRO", "HPT", "HTC", "HTECH", "HUMAN", "HYDRO", 
    "ICHI", "ICN", "IFEC", "IFS", "IHL", "IIG", "III", "ILINK", "ILM", "IMH", "INDRS", "INET", 
    "INETREIT", "INGRS", "INOX", "INSURE", "INTUCH", "IP", "IRC", "IRPC", "IT", "ITD", "ITEL", "ITNS", 
    "IVL", "J", "JAS", "JASIF", "JCK", "JCKH", "JCT", "JDF", "JMART", "JMT", "JR", "JSP", "JTS", 
    "JUBILE", "JUTHA", "K", "KASET", "KBANK", "KBS", "KBSPIF", "KC", "KCAR", "KCE", "KCM", "KDH", 
    "KEX", "KGI", "KIAT", "KISS", "KK", "KKC", "KKP", "KLEAN", "KLINIQ", "KMC", "KMP", "KNEW", 
    "KOP", "KP", "KPN", "KPO", "KPP", "KPR", "KPT", "KPX", "KSL", "KTB", "KTC", "KTIS", "KTMS", 
    "KTP", "KUMWEL", "KUN", "KWC", "KWG", "KYE", "L&E", "LALIN", "LANNA", "LDC", "LEE", "LEO", 
    "LH", "LHHOTEL", "LHPF", "LHSC", "LIT", "LOXLEY", "LPH", "LPN", "LRH", "LST", "LTX", "M", 
    "MACO", "MAJOR", "MALEE", "MANRIN", "MATCH", "MATI", "MAX", "MBAX", "MBK", "MC", "M-CHAI", 
    "MCOT", "MCS", "MDX", "MEB", "MEGA", "METCO", "MFC", "MFEC", "M-II", "MICRO", "MIDA", "MILL", 
    "MINT", "MIPF", "MIT", "MJD", "MK", "ML", "Modern", "MONO", "MOONG", "MORE", "MOSHI", "MPIC", 
    "MSC", "MTC", "MTI", "MTW", "MUD", "MVP", "NC", "NCH", "NCL", "NDR", "NER", "NETBAY", "NEW", 
    "NEX", "NFC", "NINE", "NKI", "NKT", "NL", "NMG", "NNCL", "NOBLE", "NOK", "NOVA", "NPK", "NPPG", 
    "NSI", "NTV", "NUSA", "NV", "NVD", "NYT", "OCC", "OGC", "OHTL", "OISHI", "ONE", "OR", "ORI", 
    "OSP", "OTO", "PACO", "PATO", "PB", "PCSGH", "PDG", "PDJ", "PEACE", "PERM", "PF", "PFS", 
    "PG", "PHOL", "PICO", "PIMO", "PJW", "PL", "PLANB", "PLANET", "PLAT", "PLE", "PLUS", "PM", 
    "PMTA", "PNC", "POLAR", "POLY", "POPF", "PORT", "POST", "PPF", "PPM", "PPPM", "PR9", "PRAKIT", 
    "PRAPAT", "PREB", "PRECHA", "PRG", "PRIME", "PRIN", "PRINC", "PRM", "PROEN", "PROS", "PROUD", 
    "PSG", "PSH", "PSL", "PSP", "PSTC", "PT", "PTC", "PTG", "PTL", "PTT", "PTTEP", "PTTGC", 
    "PVD", "PVR", "PYLON", "Q-CON", "QH", "QHHR", "QHOP", "QHPF", "QLT", "QTC", "RABBIT", "RATCH", 
    "RBF", "RCL", "RJH", "RML", "RS", "RSP", "S", "S&J", "S11", "SA", "SABINA", "SABUY", "SAF", 
    "SAFE", "SAFARI", "SALEE", "SAM", "SAMART", "SAMCO", "SAMTEL", "SANKO", "SAPPE", "SAT", "SAUCE", 
    "SAWAD", "SAWANG", "SC", "SCB", "SCC", "SCCC", "SCG", "SCGD", "SCGP", "SCI", "SCM", "SCN", 
    "SCP", "SDC", "SE", "SEAOIL", "SEAFCO", "SECURE", "SE-ED", "SELIC", "SENA", "SENAJ", "SENX", 
    "SFLEX", "SFP", "SFT", "SGC", "SGF", "SHR", "SIAM", "SICT", "SIMAT", "SINGER", "SIRI", "SIS", 
    "SISB", "SITHAI", "SJWD", "SK", "SKE", "SKN", "SKR", "SKY", "SLM", "SLP", "SM", "SMART", 
    "SMD", "SMIT", "SMK", "SMM", "SMT", "SNC", "SNP", "SO", "SOLAR", "SONIC", "SORKON", "SPA", 
    "SPALI", "SPC", "SPCG", "SPG", "SPI", "SPRC", "SPVI", "SQ", "SR", "SRICHA", "SRIPANWA", "SSC", 
    "SSF", "SSP", "SSSC", "SST", "STA", "STANLY", "STAR", "STARK", "STC", "STEC", "STECH", "STGT", 
    "STHAI", "STI", "STP", "STPI", "SUC", "SUTHA", "SVH", "SVI", "SVOA", "SWC", "SYNEX", "SYNTEC", 
    "TACC", "TAE", "TAKUNI", "TAPAC", "TASCO", "TC", "TCAP", "TCC", "TCMC", "TCOAT", "TEAM", "TEAMG", 
    "TEGH", "TEKA", "TFG", "TFI", "TFM", "TFMAMA", "TGE", "TGPRO", "TH", "THAI", "THANA", "THANI", 
    "THCOM", "THG", "THIP", "THL", "THMUI", "THRE", "THREL", "TIDLOR", "TIF1", "TIGER", "TITLE", 
    "TK", "TKC", "TKN", "TKS", "TKT", "TLI", "TM", "TMC", "TMD", "TMI", "TMILL", "TMT", "TNDT", 
    "TNH", "TNITY", "TNL", "TNP", "TNPC", "TNR", "TOA", "TOG", "TOP", "TOPP", "TPA", "TPAC", 
    "TPBI", "TPCH", "TPCS", "TPE", "TPIPL", "TPIPP", "TPLAS", "TPOLY", "TPS", "TQR", "TR", "TRC", 
    "TRITN", "TRP", "TRT", "TRU", "TRUBB", "TRV", "TSE", "TSF", "TSI", "TSR", "TSTE", "TSTH", 
    "TTA", "TTB", "TTCL", "TTI", "TTT", "TTW", "TU", "TURI", "TVDH", "TVH", "TVO", "TVT", "TWP", 
    "TWPC", "TWZ", "TYCN", "U", "UAC", "UBE", "UBIS", "UEC", "UKEM", "UMI", "UMS", "UNIK", "UNIQ", 
    "UOBKH", "UP", "UPF", "UPOIC", "URBNPF", "UREKA", "UT", "UTP", "UV", "UVAN", "VARO", "VCOM", 
    "VI", "VIBHA", "VIH", "VL", "VNG", "VPO", "VRANDA", "WARRIX", "WAVE", "WGE", "WHA", "WHAIR", 
    "WHABT", "WHAUP", "WICE", "WIIK", "WIN", "WINMED", "WINNER", "WORK", "WORLD", "WP", "WPH", 
    "XPG", "YGG", "YONG", "YUASA", "ZAA", "ZIGA"
]
thai_tickers = sorted(list(set([f"{s.strip().upper()}.BK" for s in THAI_BASE])))
with open(os.path.join("data", "thai_stocks.json"), "w", encoding="utf-8") as f:
    json.dump(thai_tickers, f, indent=2)
print(f"✅ บันทึกหุ้นไทย {len(thai_tickers)} ตัว สำเร็จ")

# 2. หุ้นสหรัฐฯ (ดึงผ่าน SEC)
print("\n2. กำลังดึงฐานข้อมูลหุ้นสหรัฐฯ...")
PRIORITY_GROWTH = [
    "ARM", "TSM", "ASML", "MRVL", "ALAB", "VRT", "CRDO", "AMAT", "LRCX", "KLAC", 
    "POET", "ACLS", "CAMT", "ONTO", "COHR", "AAOI", "CIEN", "CLS", "SMCI", "WDC",
    "CEG", "VST", "TLN", "CCJ", "SMR", "OKLO", "NNE", "LEU", "BWXT", "UEC", 
    "NXE", "DNN", "UUUU", "FLR", "GEV", "RKLB", "LUNR", "ASTS", "PL", "KTOS", 
    "AVAV", "ACHR", "JOBY", "RDW", "BKSY", "SPIR", "IONQ", "RGTI", "QBTS", "QUBT", 
    "SYM", "ALB", "LAC", "MP", "FCX", "SCCO", "SQM", "ERO", "HL", "CDE", 
    "CRSP", "VKTX", "HIMS", "BEAM", "NTLA", "RXRX", "IOVA", "MDGL", "KRTX", "TMDX",
    "MSTR", "COIN", "MARA", "CLSK", "RIOT", "SOFI", "HOOD", "AFRM", "UPST", "HUT",
    "BITF", "IREN", "CORZ", "WULF", "CIFR", "PLTR", "CRWD", "NET", "SNOW", "DDOG", 
    "ZS", "MDB", "PATH", "ESTC", "CFLT", "GTLB", "IOT", "MNDY", "S", "DOCN"
]
us_tickers = set(PRIORITY_GROWTH)
try:
    headers_sec = {"User-Agent": "TradingTerminal admin@terminal.local"}
    res_sec = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers_sec, timeout=10)
    for item in res_sec.json().values():
        tk = item.get("ticker", "").replace(".", "-").strip().upper()
        if tk and len(tk) <= 5 and tk.isalpha():
            us_tickers.add(tk)
        if len(us_tickers) >= 1000:
            break
except Exception:
    pass

final_us = sorted(list(us_tickers))[:1000]
with open(os.path.join("data", "us_stocks.json"), "w", encoding="utf-8") as f:
    json.dump(final_us, f, indent=2)
print(f"✅ บันทึกหุ้นสหรัฐฯ {len(final_us)} ตัว สำเร็จ")

# 3. หุ้นจีนและฮ่องกง
print("\n3. กำลังสร้างฐานข้อมูลหุ้นจีน...")
cn_set = set([
    "002594.SZ", "300750.SZ", "9866.HK", "9868.HK", "2015.HK", "1810.HK", "600104.SS", "601633.SS",
    "0700.HK", "9988.HK", "3690.HK", "9618.HK", "9999.HK", "9888.HK", "688981.SS", "601138.SS",
    "002415.SZ", "600519.SS", "000858.SZ", "000333.SZ", "000651.SZ", "601398.SS", "601939.SS",
    "601288.SS", "601988.SS", "600036.SS", "601318.SS", "601857.SS", "600028.SS", "601088.SS",
    "600900.SS", "601899.SS", "600276.SS", "300760.SZ", "1211.HK", "2269.HK", "2318.HK", "0388.HK"
])
for code in range(600000, 600500):
    cn_set.add(f"{code:06d}.SS")
for code in range(1, 300):
    cn_set.add(f"{code:06d}.SZ")

final_cn = sorted(list(cn_set))[:800]
with open(os.path.join("data", "china_stocks.json"), "w", encoding="utf-8") as f:
    json.dump(final_cn, f, indent=2)
print(f"✅ บันทึกหุ้นจีน {len(final_cn)} ตัว สำเร็จ")

# 4. คริปโต Bitkub & Binance
print("\n4. กำลังดึงรายชื่อเหรียญ Bitkub & Binance...")
def fetch_bitkub_symbols():
    try:
        r = requests.get("https://api.bitkub.com/api/market/ticker", timeout=8)
        return sorted([k.replace("THB_", "") + "_THB" for k in r.json().keys() if k.startswith("THB_")])
    except Exception:
        return ["BTC_THB", "ETH_THB", "SOL_THB", "KUB_THB", "ADA_THB", "DOGE_THB", "XRP_THB"]

def fetch_binance_symbols():
    try:
        r = requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=8)
        return sorted([s["symbol"] for s in r.json()["symbols"] if s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"])
    except Exception:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]

with open(os.path.join("data", "bitkub_crypto.json"), "w", encoding="utf-8") as f:
    json.dump(fetch_bitkub_symbols(), f, indent=2)
print("✅ บันทึกกระดาน Bitkub สำเร็จ")

with open(os.path.join("data", "binance_crypto.json"), "w", encoding="utf-8") as f:
    json.dump(fetch_binance_symbols(), f, indent=2)
print("✅ บันทึกกระดาน Binance สำเร็จ")