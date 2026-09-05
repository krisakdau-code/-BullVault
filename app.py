# app.py — Universal Trading Terminal (Full Verified Version)
import time
import datetime
import requests
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_lightweight_charts_ntf import renderLightweightCharts

try:
    import yfinance as yf
except ImportError:
    yf = None

# ──────────────────────────── CONFIG ────────────────────────────
st.set_page_config(
    page_title="Diamond Armor Universal",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #000000 !important;
    }
    
    /* เปิด Header และเว้นพื้นที่ด้านบนให้ Deploy/Menu ไม่ทับกับเนื้อหา */
    [data-testid="stHeader"] {
        background: #000000 !important;
        height: 2.8rem !important;
        min-height: 2.8rem !important;
        z-index: 100 !important;
    }
    [data-testid="stToolbar"] {
        right: 1.5rem !important;
        top: 0.4rem !important;
        z-index: 999 !important;
        display: flex !important;
        visibility: visible !important;
    }
    .stDeployButton {
        display: inline-block !important;
        visibility: visible !important;
    }
    #MainMenu {
        display: inline-block !important;
        visibility: visible !important;
    }
    footer { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }

    /* ดันพื้นที่หน้าเว็บลงมาใต้ Header ป้องกันไม่ให้ปุ่ม Deploy ทับแถบราคา */
    .block-container,
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMainBlockContainer"],
    [data-testid="block-container"] {
        padding-top: 3.2rem !important;
        padding-bottom: 1rem !important;
        margin-top: 0rem !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
        margin-left: 0px !important;
        margin-right: 0px !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    section.main > div { padding-top: 0rem !important; }

    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        z-index: 1000 !important;
        top: 0.5rem !important;
    }

    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1E1E1E !important;
    }
    [data-testid="stSidebarContent"] {
        background-color: #050505 !important;
        padding-left: 0.5rem !important; padding-right: 0.5rem !important;
        padding-top: 1.2rem !important; max-height: 100vh !important; overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    div[data-testid="stHorizontalBlock"] { gap: 2px !important; }
    div[data-testid="column"] { padding: 0 1px !important; }
    
    .stButton>button {
        background: #101010 !important; color: #D1D4DC !important;
        border: 1px solid #2A2A2A !important; border-radius: 4px !important;
        padding: 2px 4px !important; font-size: 11px !important; font-weight: 500 !important;
        min-height: 24px !important; height: 24px !important; line-height: 1 !important;
        box-shadow: none !important;
    }
    .stButton>button:hover { border-color: #2962FF !important; color: #FFFFFF !important; background: #1A1A1A !important; }
    
    div[data-testid="stExpander"], .stExpander details { border: 1px solid #1E1E1E !important; border-radius: 4px !important; background: #0A0A0A !important; margin-bottom: 4px; }
    div[data-testid="stExpander"] summary { padding: 3px 8px !important; font-size: 11px !important; }
    div[data-testid="stExpander"] summary p { font-size: 11px !important; font-weight: 600 !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { padding: 4px 6px !important; background-color: #0A0A0A !important; }

    [data-testid="stMetric"], div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #0A0A0A !important; border: 1px solid #1A1A1A !important; }
    input, select, textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div { background-color: #0D0D0D !important; color: #D1D4DC !important; border: 1px solid #222222 !important; }
    .stDataFrame, [data-testid="stTable"] { background-color: #000000 !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 2px; background-color: #000000 !important; padding: 2px; border-radius: 6px; border-bottom: 1px solid #1E1E1E !important; }
    .stTabs [data-baseweb="tab"] { padding: 2px 8px !important; font-size: 11px !important; height: 24px !important; }

    .tv-wl-header {
        display: grid; 
        grid-template-columns: 0.6fr 1.8fr 1.4fr 1.2fr 1.2fr 0.4fr;
        padding: 4px 2px; font-size: 10px; font-weight: 600; color: #787b86;
        border-bottom: 1px solid #1E1E1E; margin-bottom: 4px;
    }
    .pane-toolbar {
        background: #0A0A0A; border: 1px solid #1E1E1E; border-bottom: none;
        border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 2px 8px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 11px; font-weight: 600; color: #D1D4DC; margin-top: 2px;
    }
    div[data-testid="column"]:has(div[data-testid="stExpander"]) {
        max-height: 89vh !important; overflow-y: auto !important;
        overflow-x: hidden !important; padding-right: 4px !important;
    }
</style>
""", unsafe_allow_html=True)

try:
    BITKUB_API_KEY = st.secrets.get("BITKUB_API_KEY", "")
except Exception:
    BITKUB_API_KEY = ""

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update(BROWSER_HEADERS)

GLOBAL_MARKET = "🌐 Global (Yahoo)"

TF = {
    "1m":  {"sec": 60,      "rule": "1min", "base": None, "yf_iv": "1m",  "yf_range": "7d"},
    "3m":  {"sec": 180,     "rule": "3min", "base": "1m", "yf_iv": "5m",  "yf_range": "60d"},
    "5m":  {"sec": 300,     "rule": "5min", "base": None, "yf_iv": "5m",  "yf_range": "60d"},
    "15m": {"sec": 900,     "rule": "15min","base": None, "yf_iv": "15m", "yf_range": "60d"},
    "30m": {"sec": 1800,    "rule": "30min","base": None, "yf_iv": "30m", "yf_range": "60d"},
    "1h":  {"sec": 3600,    "rule": "1H",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "2h":  {"sec": 7200,    "rule": "2H",   "base": "1h", "yf_iv": "60m", "yf_range": "730d"},
    "4h":  {"sec": 14400,   "rule": "4H",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "6h":  {"sec": 21600,   "rule": "6H",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "8h":  {"sec": 28800,   "rule": "8H",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "12h": {"sec": 43200,   "rule": "12H",  "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "1d":  {"sec": 86400,   "rule": "1D",   "base": None, "yf_iv": "1d",  "yf_range": "10y"},
    "3d":  {"sec": 259200,  "rule": "3D",   "base": "1d", "yf_iv": "1d",  "yf_range": "10y"},
    "1w":  {"sec": 604800,  "rule": "1W",   "base": None, "yf_iv": "1wk", "yf_range": "10y"},
}

UP, DOWN = "#26a69a", "#ef5350"

# ──────────────────────────── DATASETS ────────────────────────────
VN_HOSE_SYMBOLS = [
    "AAA", "AAM", "AAT", "ABR", "ABS", "ABT", "ACB", "ACC", "ACG", "ACL", "ADG", "ADS", "AGG", "AGM", "AGR",
    "ANV", "APC", "APG", "APH", "ASG", "ASM", "ASP", "AST", "BAF", "BBC", "BCE", "BCG", "BCM", "BFC", "BHN",
    "BIC", "BID", "BKG", "BMC", "BMI", "BMP", "BRC", "BSI", "BTP", "BTT", "BVH", "BWE", "C32", "C47", "CAV",
    "CCI", "CCL", "CDC", "CHP", "CIG", "CII", "CKG", "CLC", "CLL", "CLW", "CMG", "CMV", "CMX", "CNG", "COM",
    "CRC", "CRE", "CSM", "CSV", "CTD", "CTF", "CTG", "CTI", "CTR", "CTS", "CVT", "D2D", "DAG", "DAH", "DAT",
    "DBC", "DBD", "DBT", "DC4", "DCL", "DCM", "DHA", "DHC", "DHG", "DHM", "DIG", "DLG", "DMC", "DPG", "DPM",
    "DPR", "DQC", "DRC", "DRH", "DRL", "DSN", "DTA", "DTL", "DTT", "DVP", "DXG", "DXS", "EIB", "ELC", "EMC",
    "EVE", "EVF", "EVG", "FCM", "FCN", "FDC", "FIR", "FIT", "FLC", "FMC", "FPT", "FRT", "FTS", "GAS", "GDT",
    "GEG", "GEX", "GIL", "GMC", "GMD", "GSP", "GTA", "GVR", "HAG", "HAH", "HAI", "HAP", "HAR", "HAS", "HAX",
    "HBC", "HCD", "HCM", "HDB", "HDC", "HDG", "HHP", "HII", "HMC", "HNG", "HOT", "HPG", "HPX", "HQC", "HRC",
    "HSG", "HSL", "HT1", "HTI", "HTL", "HTN", "HTV", "HU1", "HUB", "HVH", "HVN", "HVX", "IBC", "ICT", "IDI",
    "IJC", "ILB", "IMP", "ITA", "ITC", "ITD", "JVC", "KBC", "KDC", "KDH", "KHG", "KHP", "KMR", "KOS", "KPF",
    "KSB", "L10", "LAF", "LBM", "LCG", "LCM", "LDG", "LEC", "LGC", "LGL", "LHG", "LIX", "LM8", "LPB", "LSS",
    "MBB", "MCG", "MCP", "MDG", "MHC", "MIG", "MSB", "MSN", "MWG", "NAF", "NAV", "NBB", "NCT", "NHA", "NHH",
    "NKG", "NLG", "NNC", "NO1", "NSC", "NT2", "NTL", "NVL", "NVT", "OGC", "OPC", "ORORS", "PAC", "PAN", "PC1",
    "PDN", "PDR", "PET", "PGC", "PGD", "PGI", "PGV", "PHC", "PHR", "PIT", "PJT", "PLX", "PMG", "PNC", "PNJ",
    "POM", "POW", "PPC", "PSH", "PTB", "PTC", "PTL", "PVD", "PVT", "QBS", "QCG", "RAL", "RDP", "REE", "ROS",
    "S4A", "SAB", "SAM", "SAV", "SBA", "SBT", "SBV", "SC5", "SCD", "SCR", "SCS", "SFC", "SFG", "SFI", "SGN",
    "SGR", "SGT", "SHA", "SHB", "SHI", "SHP", "SIP", "SJD", "SJF", "SJS", "SKG", "SMA", "SMB", "SMC", "SPM",
    "SRC", "SRF", "SSB", "SSC", "SSI", "ST8", "STB", "STG", "STK", "SVC", "SVD", "SVI", "SVT", "SZC", "SZL",
    "TAC", "TBC", "TCB", "TCD", "TCH", "TCL", "TCM", "TCO", "TCR", "TCT", "TDC", "TDG", "TDH", "TDM", "TDP",
    "TDW", "TEG", "THG", "THI", "TIP", "TIX", "TLD", "TLG", "TLH", "TMP", "TMS", "TMT", "TN1", "TNA", "TNC",
    "TNH", "TNI", "TNT", "TPB", "TPC", "TRC", "TTB", "TTE", "TTF", "TV2", "TVB", "TVI", "TVT", "TYA", "UIC",
    "VAF", "VCA", "VCB", "VCF", "VCG", "VCI", "VDP", "VDS", "VFG", "VGC", "VGeneric", "VHC", "VHM", "VIB", "VIC",
    "VID", "VIP", "VIS", "VIX", "VJC", "VMD", "VND", "VNE", "VNG", "VNL", "VNM", "VNS", "VOS", "VPB", "VPD",
    "VPG", "VPH", "VPI", "VPS", "VRC", "VRE", "VSC", "VSH", "VSI", "VTB", "VTO", "YBM", "YEG"
]

VN_HNX_SYMBOLS = [
    "AAV", "ACM", "ADC", "ALT", "AMC", "AME", "AMV", "API", "APP", "APS", "ARM", "ART", "BAB", "BAX", "BBS",
    "BCC", "BCF", "BDB", "BII", "BKC", "BLF", "BPC", "BSC", "BST", "BTS", "BVS", "BXH", "C92", "CAG", "CAP",
    "CC4", "CCR", "CDN", "CEO", "CET", "CGC", "CIA", "CJX", "CLH", "CLM", "CMC", "CMS", "CPC", "CSC", "CST",
    "CTA", "CTB", "CTC", "CTN", "CTP", "CTX", "CVN", "D11", "DAD", "DAE", "DAR", "DAS", "DBT", "DC2", "DDG",
    "DHT", "DIH", "DL1", "DNC", "DNM", "DP3", "DPC", "DPS", "DTD", "DTK", "DTC", "DVG", "DXP", "EBS", "ECI",
    "EID", "ELC", "FID", "GIC", "GKM", "GLT", "GMX", "HAD", "HAT", "HBC", "HBE", "HBS", "HCC", "HCT", "HDA",
    "HEV", "HGM", "HHC", "HJS", "HKT", "HLC", "HLD", "HMH", "HOM", "HPD", "HPI", "HPP", "HST", "HTC", "HTP",
    "HUT", "HVT", "ICG", "IDC", "IDJ", "IDV", "INC", "IN4", "ITQ", "IVS", "KDM", "KHL", "KHS", "KMT", "KSD",
    "KSQ", "KST", "KTS", "KTT", "L14", "L18", "L35", "L40", "L43", "L44", "L61", "L62", "LAS", "LBE", "LCD",
    "LCS", "LDP", "LHC", "LIG", "LM7", "LO5", "LTC", "LUT", "MAC", "MAS", "MBG", "MBS", "MCC", "MCF", "MCO",
    "MDC", "MED", "MEL", "MHL", "MKV", "MST", "MTC", "MTG", "NAG", "NAP", "NBC", "NBP", "ND2", "NDN", "NDX",
    "NET", "NFC", "NGC", "NHA", "NHC", "NIT", "NRC", "NST", "NTH", "NTP", "NVB", "OCH", "ONE", "PAN", "PBP",
    "PCE", "PCG", "PCT", "PDB", "PDC", "PEN", "PFL", "PGN", "PGS", "PGT", "PHN", "PHP", "PIA", "PIC", "PJC",
    "PLC", "PMB", "PMC", "PND", "PPY", "PRC", "PSC", "PSD", "PSE", "PSI", "PSW", "PTS", "PV2", "PVB", "PVC",
    "PVG", "PVI", "PVL", "PVR", "PVS", "QHD", "QST", "QTC", "RCL", "S55", "S64", "S74", "S99", "SAF", "SAV",
    "SCG", "SCI", "SD2", "SD4", "SD5", "SD6", "SD9", "SDA", "SDC", "SDG", "SDN", "SDT", "SDU", "SEB", "SED",
    "SFN", "SGC", "SGD", "SGH", "SHN", "SHS", "SIC", "SJ1", "SJE", "SMN", "SMT", "SPC", "SPI", "SQC", "SRB",
    "SSG", "STC", "STP", "SVN", "SZB", "TA9", "TAR", "TBX", "TC6", "TCS", "TDN", "TET", "TFC", "THB", "THS",
    "THT", "TIG", "TJC", "TKC", "TKU", "TMC", "TMX", "TNG", "TPH", "TPP", "TSB", "TTC", "TTD", "TTZ", "TV3",
    "TV4", "TVC", "TXM", "UNI", "V21", "VAT", "VBC", "VC1", "VC2", "VC3", "VC6", "VC7", "VC9", "VCC", "VCG",
    "VCS", "VDL", "VE1", "VE2", "VE3", "VE4", "VE8", "VFR", "VGS", "VHE", "VHL", "VHY", "VIC", "VIE", "VIG",
    "VIT", "VLA", "VMC", "VMS", "VNC", "VND", "VNF", "VNR", "VNT", "VTC", "VTH", "VTJ", "VTL", "VTV", "WCS"
]

VN_UPCOM_150 = [
    "ABB", "ABI", "ACE", "ACV", "AFX", "AGF", "AMP", "AMS", "APF", "APT", "BAB", "BBH", "BCP", "BGF", "BHI",
    "BHT", "BMS", "BOT", "BRG", "BSA", "BSR", "BTH", "BWS", "C4G", "CBI", "CBR", "CC1", "CDO", "CEN", "CFV",
    "CLX", "CMM", "CST", "CTR", "DFF", "DGT", "DRI", "DVN", "FOC", "GDA", "GEE", "GND", "GTH", "GVR", "HAC",
    "HAP", "HBH", "HCI", "HD6", "HEC", "HES", "HHV", "HLG", "HND", "HNG", "HNP", "HPB", "HPP", "HPT", "HSI",
    "HTM", "HUG", "HVN", "ICC", "IFS", "KLB", "KMT", "KSH", "LAB", "LCW", "LDW", "LIC", "LMH", "LPB", "MCH",
    "MCM", "MDF", "MEC", "MFS", "MML", "MSR", "NAB", "NDF", "NDP", "NTC", "OIL", "PGB", "PFL", "PHP", "PLX",
    "PND", "POW", "PPH", "PPP", "PRT", "PTD", "PVP", "PVV", "PVX", "QNS", "QTP", "RBC", "SAB", "SBS", "SCY",
    "SDV", "SEA", "SEP", "SGP", "SHB", "SIV", "SKH", "SKV", "SSN", "TAR", "TCW", "TGP", "TID", "TIS", "TL4",
    "TLP", "TLV", "TNPP", "TPH", "TS4", "TT6", "TVN", "VAB", "VBB", "VCP", "VDB", "VEA", "VET", "VGG", "VGI",
    "VGT", "VIF", "VLG", "VNA", "VNB", "VNP", "VOC", "VPA", "VPK", "VSE", "VTI", "VTR", "VTS", "VWS", "XPH"
]

CHINA_STOCK_NAMES = {
    "002594.SZ": "BYD (บีวายดี - รถยนต์ไฟฟ้าอันดับ 1)",
    "300750.SZ": "CATL (ผู้ผลิตแบตเตอรี่ลิเธียม EV เบอร์ 1 โลก)",
    "9866.HK":   "NIO (นีโอ - รถยนต์ไฟฟ้า)",
    "9868.HK":   "XPeng (เสี่ยวเผิง - รถยนต์ไฟฟ้า AI)",
    "2015.HK":   "Li Auto (ลี่ออโต้ - รถยนต์ SUV EV)",
    "1810.HK":   "Xiaomi (เสียวหมี่ - มือถือและ EV)",
    "600104.SS": "SAIC Motor (เอสเอไอซี ยานยนต์)",
    "601633.SS": "Great Wall Motor (เกรท วอลล์ มอเตอร์)",
    "0700.HK":   "Tencent (เทนเซ็นต์ - WeChat / เกม)",
    "9988.HK":   "Alibaba (อาลีบาบา - อีคอมเมิร์ซ / คลาวด์)",
    "3690.HK":   "Meituan (เหม่ยถวน - เดลิเวอรี)",
    "9618.HK":   "JD.com (เจดีดอทคอม)",
    "9999.HK":   "NetEase (เน็ตอีส)",
    "9888.HK":   "Baidu (ไป่ตู้ AI)",
    "688981.SS": "SMIC (เอสเอ็มไอซี - ชิปเบอร์ 1 จีน)",
    "601138.SS": "Foxconn Industrial (ฟ็อกซ์คอนน์ AI)",
    "002415.SZ": "Hikvision (ฮิควิชั่น - กล้อง AI)",
    "600519.SS": "Kweichow Moutai (เหมาไถ สุราขาวอันดับ 1)",
    "000858.SZ": "Wuliangye (อู่เหลียงเย่ สุราขาว)",
    "000333.SZ": "Midea Group (ไมเดีย เครื่องใช้ไฟฟ้า)",
    "000651.SZ": "Gree Electric (กรี แอร์)",
    "601398.SS": "ICBC (ธนาคารอุตสาหกรรมจีน)",
    "601939.SS": "CCB (ธนาคารก่อสร้างจีน)",
    "601288.SS": "ABC (ธนาคารเกษตรจีน)",
    "601988.SS": "Bank of China (ธนาคารแห่งประเทศจีน)",
    "600036.SS": "China Merchants Bank",
    "601318.SS": "Ping An Insurance (ผิงอัน ประกันภัย)",
    "601857.SS": "PetroChina (ปิโตรไชน่า)",
    "600028.SS": "Sinopec (ซิโนเปค)",
    "601088.SS": "China Shenhua (ถ่านหินและไฟฟ้า)",
    "600900.SS": "Yangtze Power (แยงซี เขื่อนสามผา)",
    "601899.SS": "Zijin Mining (จื่อจิน เหมืองทอง/ทองแดง)",
    "600276.SS": "Hengrui Medicine (เหิงรุ่ย ยาต้านมะเร็ง)",
    "300760.SZ": "Mindray Bio-Medical (มายด์เรย์ การแพทย์)"
}

SP500_SYMBOLS = [
    "A", "AAL", "AAPL", "ABBV", "ABNB", "ABT", "ACGL", "ACN", "ADBE", "ADI",
    "ADM", "ADP", "ADSK", "AEE", "AEP", "AES", "AFL", "AIG", "AIZ", "AJG",
    "AKAM", "ALB", "ALGN", "ALL", "ALLE", "AMAT", "AMCR", "AMD", "AME", "AMGN",
    "AMP", "AMT", "AMZN", "ANET", "ANSS", "AON", "AOS", "APA", "APD", "APH",
    "APTV", "ARE", "ATO", "AVB", "AVGO", "AVY", "AWK", "AXON", "AXP", "AZO",
    "BA", "BAC", "BALL", "BAX", "BBWI", "BBY", "BDX", "BEN", "BF-B", "BG",
    "BIIB", "BK", "BKNG", "BKR", "BLDR", "BLK", "BMY", "BR", "BRK-B", "BRO",
    "BSX", "BWA", "BX", "BXP", "C", "CAG", "CAH", "CARR", "CAT", "CB",
    "CBOE", "CBRE", "CCI", "CCL", "CDNS", "CDW", "CE", "CEG", "CF", "CFG",
    "CHD", "CHRW", "CHTR", "CI", "CINF", "CL", "CLX", "CMA", "CMCSA", "CME",
    "CMG", "CMI", "CMS", "CNC", "CNP", "COF", "COO", "COP", "COR", "COST",
    "CPAY", "CPB", "CPRT", "CPT", "CRL", "CRM", "CSCO", "CSGP", "CSX", "CTAS",
    "CTLT", "CTRA", "CTSH", "CTVA", "CVS", "CVX", "CZR", "D", "DAL", "DAY",
    "DD", "DE", "DECK", "DELL", "DFS", "DG", "DGX", "DHI", "DHR", "DIS",
    "DLR", "DLTR", "DOC", "DOV", "DOW", "DPZ", "DRI", "DTE", "DUK", "DVA",
    "DVN", "DXCM", "EA", "EBAY", "ECL", "ED", "EFX", "EG", "EIX", "EL",
    "ELV", "EMN", "EMR", "ENPH", "EOG", "EPAM", "EQIX", "EQR", "EQT", "ERIE",
    "ES", "ESS", "ETN", "ETR", "ETSY", "EVRG", "EW", "EXC", "EXPD", "EXPE",
    "EXR", "F", "FANG", "FAST", "FCX", "FDS", "FDX", "FE", "FFIV", "FI",
    "FICO", "FIS", "FITB", "FLT", "FMC", "FOX", "FOXA", "FRT", "FSLR", "FTNT",
    "FTV", "GD", "GDDY", "GE", "GEHC", "GEN", "GEV", "GILD", "GIS", "GL",
    "GLW", "GM", "GNRC", "GOOG", "GOOGL", "GPC", "GPN", "GRMN", "GS", "GWW",
    "HAL", "HAS", "HBAN", "HCA", "HD", "HES", "HIG", "HII", "HLT", "HOLX",
    "HON", "HPE", "HPQ", "HRL", "HSIC", "HST", "HSY", "HUBB", "HUM", "HWM",
    "IBM", "ICE", "IDXX", "IEX", "IFF", "INCY", "INTC", "INTU", "INVH", "IP",
    "IPG", "IQV", "IR", "IRM", "ISRG", "IT", "ITW", "IVZ", "J", "JBHT",
    "JBL", "JCI", "JKHY", "JNJ", "JNPR", "JPM", "K", "KDP", "KEY", "KEYS",
    "KHC", "KIM", "KLAC", "KMB", "KMI", "KMX", "KO", "KR", "KVUE", "L",
    "LDOS", "LEN", "LH", "LHX", "LIN", "LKQ", "LLY", "LMT", "LNT", "LOW",
    "LRCX", "LULU", "LUV", "LVS", "LW", "LYB", "LYV", "MA", "MAA", "MAR",
    "MAS", "MCD", "MCHP", "MCK", "MCO", "MDLZ", "MDT", "MET", "META", "MGM",
    "MHK", "MKC", "MKTX", "MLM", "MMC", "MMM", "MNST", "MO", "MOH", "MOS",
    "MPC", "MPWR", "MRK", "MRNA", "MS", "MSCI", "MSFT", "MSI", "MTB", "MTCH",
    "MTD", "MU", "NCLH", "NDAQ", "NDSN", "NEE", "NEM", "NFLX", "NI", "NKE",
    "NOC", "NOW", "NRG", "NSC", "NTAP", "NTRS", "NUE", "NVDA", "NVR", "NWS",
    "NWSA", "NXPI", "O", "ODFL", "OKE", "OMC", "ON", "ORCL", "ORLY", "OTIS",
    "OXY", "PANW", "PARA", "PAYC", "PAYX", "PCAR", "PCG", "PEG", "PEP", "PFE",
    "PFG", "PG", "PGR", "PH", "PHM", "PKG", "PLD", "PLTR", "PM", "PNC",
    "PNR", "PNW", "PODD", "POOL", "PPG", "PPL", "PRU", "PSA", "PSX", "PTC",
    "PWR", "PYPL", "QCOM", "QRVO", "RCL", "REG", "REGN", "RF", "RHI", "RJF",
    "RL", "RMD", "ROK", "ROL", "ROP", "ROST", "RSG", "RTX", "RVTY", "SBAC",
    "SBUX", "SCHW", "SHW", "SJM", "SLB", "SMCI", "SNA", "SNPS", "SO", "SOLV",
    "SPG", "SPGI", "SRE", "STE", "STLD", "STT", "STX", "STZ", "SWK", "SWKS",
    "SWN", "SYF", "SYK", "SYY", "T", "TAP", "TDG", "TDY", "TECH", "TEL",
    "TER", "TFC", "TFX", "TGT", "TJX", "TMO", "TMUS", "TPR", "TRGP", "TRMB",
    "TROW", "TRV", "TSCO", "TSLA", "TSN", "TT", "TTWO", "TXN", "TXT", "TYL",
    "UAL", "UBER", "UDR", "UHS", "ULTA", "UNH", "UNP", "UPS", "URI", "USB",
    "V", "VICI", "VLO", "VLTO", "VMC", "VNO", "VRSK", "VRSN", "VRTX", "VST",
    "VTR", "VTRS", "VZ", "WAB", "WAT", "WBA", "WBD", "WDC", "WEC", "WELL",
    "WFC", "WM", "WMB", "WMT", "WRB", "WRK", "WST", "WTW", "WY", "WYNN",
    "XEL", "XOM", "XYL", "YUM", "ZBH", "ZBRA", "ZTS"
]

COMMODITY_NAMES = {
    "GC=F": "ทองคำ", "SI=F": "เงิน", "CL=F": "น้ำมันWTI",
    "BZ=F": "น้ำมันBrent", "HG=F": "ทองแดง", "RR=F": "ข้าว", "ZC=F": "ข้าวโพด"
}

# ──────────────────────────── FETCHERS ────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_binance_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://api.binance.com/api/v3/ticker/price", timeout=5)
        if r.status_code == 200:
            symbols = [i["symbol"] for i in r.json() if i.get("symbol", "").endswith("USDT")]
            if len(symbols) > 50: return sorted(symbols)
    except Exception: pass
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT", "PEPEUSDT", "NEARUSDT"]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_bitkub_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://api.bitkub.com/api/market/ticker", timeout=5)
        if r.status_code == 200:
            symbols = [f"{k[4:]}_THB" if k.startswith("THB_") else k for k in r.json().keys()]
            if len(symbols) > 20: return sorted(symbols)
    except Exception: pass
    return ["BTC_THB", "ETH_THB", "KUB_THB", "SOL_THB", "DOGE_THB", "XRP_THB", "USDT_THB", "ADA_THB", "NEAR_THB"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_bybit_all_symbols() -> list:
    for cat in ("spot", "linear"):
        try:
            r = HTTP_SESSION.get(f"https://api.bybit.com/v5/market/tickers?category={cat}", timeout=5)
            if r.status_code == 200:
                items = r.json().get("result", {}).get("list", [])
                symbols = [i["symbol"] for i in items if i.get("symbol", "").endswith("USDT")]
                if len(symbols) > 50: return sorted(symbols)
        except Exception: pass
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "MNTUSDT", "XRPUSDT", "DOGEUSDT", "TONUSDT"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_okx_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT", timeout=5)
        if r.status_code == 200:
            items = r.json().get("data", [])
            symbols = [i["instId"] for i in items if i.get("instId", "").endswith("-USDT")]
            if len(symbols) > 50: return sorted(symbols)
    except Exception: pass
    return ["BTC-USDT", "ETH-USDT", "SOL-USDT", "OKB-USDT", "XRP-USDT", "DOGE-USDT"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_mexc_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://api.mexc.com/api/v3/ticker/price", timeout=5)
        if r.status_code == 200:
            symbols = [i["symbol"] for i in r.json() if i.get("symbol", "").endswith("USDT")]
            if len(symbols) > 50: return sorted(symbols)
    except Exception: pass
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "MXUSDT", "DOGEUSDT", "PEPEUSDT", "SHIBUSDT"]

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_set_all_symbols() -> list:
    thai_all_stocks = [
        "2S", "7UP", "A", "A5", "AAI", "AAV", "ABM", "ACE", "ADVANC", "AEONTS", "AGE", "AH", "AIE", "AMATA", "AOT",
        "AP", "ASIAN", "AURA", "AWC", "BA", "BAM", "BANPU", "BAY", "BBIK", "BBL", "BCH", "BCP", "BCPG", "BDMS",
        "BE8", "BEAUTY", "BEM", "BGRIM", "BH", "BJC", "BLA", "BPP", "BTG", "BTS", "CBG", "CCET", "CENTEL", "CHG",
        "CK", "CKP", "COM7", "CPALL", "CPAXT", "CPF", "CPN", "CRC", "DELTA", "DOHOME", "EA", "EGCO", "EPG", "ERW",
        "FORTH", "GLOBAL", "GPSC", "GULF", "GUNKUL", "HANA", "HMPRO", "ICHI", "INTUCH", "ITC", "IVL", "JMART", "JMT",
        "KAMART", "KBANK", "KCE", "KKP", "KTB", "KTC", "LH", "M", "MAJOR", "MBK", "MC", "MEGA", "MGC", "MINT",
        "MOSHI", "MTC", "NER", "NEX", "ONEE", "OR", "ORI", "OSP", "PLANB", "PR9", "PRM", "PSH", "PSL", "PTG",
        "PTT", "PTTEP", "PTTGC", "RATCH", "RBF", "RCL", "SAPPE", "SAWAD", "SCB", "SCC", "SCGP", "SIRI", "SISB",
        "SPALI", "SPRC", "STA", "STARK", "STEC", "STGT", "TASCO", "TCAP", "TFG", "THANI", "THCOM", "THG", "TIDLOR",
        "TIPH", "TISCO", "TKN", "TOP", "TRUE", "TTA", "TTB", "TTW", "TU", "VGI", "WARRIX", "WHA", "WHAUP", "XO"
    ]
    return sorted([f"{s}.BK" for s in set(thai_all_stocks)])

DEFAULT_PRESETS = {
    "🇻🇳 เวียดนาม HOSE (โฮจิมินห์)": sorted([f"{s}.VN" for s in set(VN_HOSE_SYMBOLS)]),
    "🇻🇳 เวียดนาม HNX (ฮานอย)": sorted([f"{s}.VN" for s in set(VN_HNX_SYMBOLS)]),
    "🇻🇳 เวียดนาม UPCoM (ตลาดรอง)": sorted([f"{s}.VN" for s in set(VN_UPCOM_150)]),
    "🇨🇳 หุ้นจีน (China)": sorted(list(CHINA_STOCK_NAMES.keys())),
    "🇺🇸 หุ้นสหรัฐฯ (S&P 500)": sorted(SP500_SYMBOLS),
    "🟡 คริปโต (Crypto)": {
        "Bitkub": fetch_bitkub_all_symbols(),
        "Binance": fetch_binance_all_symbols(),
        "Bybit": fetch_bybit_all_symbols(),
        "OKX": fetch_okx_all_symbols(),
        "MEXC": fetch_mexc_all_symbols(),
    },
    "🇹🇭 หุ้นไทย (SET/mai)": fetch_set_all_symbols(),
    "🟠 สินค้าโภคภัณฑ์ (Commodities)": ["GC=F", "SI=F", "CL=F", "BZ=F", "HG=F", "RR=F", "ZC=F"],
    "🟢 อัตราแลกเปลี่ยน (Forex)": ["USDTHB=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"]
}

STAR_CATEGORIES = {
    "🔴 ดาวแดง": {"icon": "🔴", "symbol": "●", "color": "#ef5350"},
    "🟡 ดาวเหลือง": {"icon": "🟡", "symbol": "●", "color": "#f5c518"},
    "🟢 ดาวเขียว": {"icon": "🟢", "symbol": "●", "color": "#26a69a"},
    "🔵 ดาวฟ้า": {"icon": "🔵", "symbol": "●", "color": "#2962ff"},
    "🟣 ดาวม่วง": {"icon": "🟣", "symbol": "●", "color": "#ab47bc"}
}

# ──────────────────────────── SESSION STATES ────────────────────────────
if "star_watchlists" not in st.session_state:
    st.session_state["star_watchlists"] = {
        "🔴 ดาวแดง": ["VNM.VN", "002594.SZ", "NVDA", "BTC_THB"],
        "🟡 ดาวเหลือง": ["VIC.VN", "0700.HK", "GC=F"],
        "🟢 ดาวเขียว": ["HPG.VN", "600519.SS", "PTT.BK"],
        "🔵 ดาวฟ้า": ["ACV.VN", "TSLA", "BTCUSDT"],
        "🟣 ดาวม่วง": ["USDTHB=X"]
    }
if "custom_symbols" not in st.session_state: st.session_state["custom_symbols"] = []
if "show_rsi" not in st.session_state: st.session_state["show_rsi"] = True
if "show_macd" not in st.session_state: st.session_state["show_macd"] = True
if "pane_order" not in st.session_state: st.session_state["pane_order"] = ["rsi", "macd"]
if "mobile_mode" not in st.session_state: st.session_state["mobile_mode"] = False
if "panel_open" not in st.session_state: st.session_state["panel_open"] = True
if "panel_size" not in st.session_state: st.session_state["panel_size"] = "M"

# ──────────────────────────── ROUTER ────────────────────────────
def resolve_route(symbol: str, ui_market: str, ui_exchange: str):
    s = (symbol or "").upper()
    if s.endswith(".BK"): return "🇹🇭 หุ้นไทย (SET/mai)", "Yahoo"
    if s.endswith(".VN"): return "🇻🇳 เวียดนาม", "Yahoo"
    if s.endswith(".SS") or s.endswith(".SZ") or s.endswith(".HK"): return "🇨🇳 หุ้นจีน (China)", "Yahoo"
    if s.endswith("_THB") or s.startswith("THB_"): return "🟡 คริปโต (Crypto)", "Bitkub"
    if s.endswith("-USDT"): return "🟡 คริปโต (Crypto)", "OKX"
    if s.endswith("USDT"):
        ex = ui_exchange if ui_exchange in ("Binance", "Bybit", "MEXC") else "Binance"
        return "🟡 คริปโต (Crypto)", ex
    if "คริปโต" in ui_market: return GLOBAL_MARKET, "Yahoo"
    return ui_market, ui_exchange

def route_label(r_market: str, r_exchange: str) -> str:
    if "คริปโต" in r_market: return r_exchange
    if r_market == GLOBAL_MARKET: return "Yahoo"
    return r_market.split()[0]

# ──────────────────────────── RESAMPLE & FETCH OHLCV ────────────────────────────
def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if df.empty: return df
    d = df.copy()
    d["datetime"] = pd.to_datetime(d["time"], unit="s")
    d = d.set_index("datetime")
    out = d.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    out["time"] = (out.index.astype("int64") // 10**9).astype("int64")
    return out.reset_index(drop=True)

def fill_empty_bars(df: pd.DataFrame, sec: int, max_fill: int = 20000) -> pd.DataFrame:
    if df.empty or len(df) < 2: return df
    base = df.drop_duplicates(subset=["time"]).sort_values("time").copy()
    base["time"] = (base["time"].astype("int64") // sec) * sec
    base = base.drop_duplicates(subset=["time"]).set_index("time")
    start, end = int(base.index[0]), int(base.index[-1])
    if (end - start) // sec > max_fill: return df

    full_idx = np.arange(start, end + sec, sec, dtype="int64")
    out = base.reindex(full_idx)
    synth = out["close"].isna().values
    out["close"]  = out["close"].ffill()
    out["open"]   = out["open"].fillna(out["close"])
    out["high"]   = out["high"].fillna(out["close"])
    out["low"]    = out["low"].fillna(out["close"])
    out["volume"] = out["volume"].fillna(0.0)
    out["is_synthetic"] = synth
    return out.dropna(subset=["close"]).reset_index()

def fetch_bitkub_raw(symbol: str, tf_code: str, sec: int, bars: int) -> pd.DataFrame:
    all_chunks = []
    curr_to = int(time.time())
    headers = dict(BROWSER_HEADERS)
    if BITKUB_API_KEY and len(BITKUB_API_KEY) > 20: headers["X-BTK-APIKEY"] = BITKUB_API_KEY
    total, max_loops = 0, 400
    window, max_window, min_window = sec * 1000, sec * 300000, sec * 500
    empty_streak, oldest_seen, floor_ts = 0, None, 1451606400

    for _ in range(max_loops):
        if total >= bars: break
        frm = max(curr_to - window, floor_ts)
        if frm >= curr_to: break
        try:
            r = HTTP_SESSION.get(
                "https://api.bitkub.com/tradingview/history", headers=headers,
                params={"symbol": symbol, "resolution": tf_code, "from": frm, "to": curr_to}, timeout=5
            )
            if r.status_code == 429: time.sleep(1.0); continue
            if r.status_code != 200: break
            j = r.json()
        except Exception: break

        status = j.get("s")
        if status == "no_data":
            nxt = j.get("nextTime")
            curr_to = int(nxt) + sec if (nxt and int(nxt) < curr_to) else frm - 1
            window = sec * 1000 if (nxt and int(nxt) < curr_to) else min(window * 4, max_window)
            empty_streak += 1
            if empty_streak >= 10: break
            continue

        if status != "ok" or not j.get("t"): break
        t_list = j["t"]
        if not t_list: break

        all_chunks.append(pd.DataFrame({"time": t_list, "open": j["o"], "high": j["h"], "low": j["l"], "close": j["c"], "volume": j["v"]}))
        total += len(t_list)
        empty_streak = 0
        min_t = int(min(t_list))
        if oldest_seen is not None and min_t >= oldest_seen: break
        oldest_seen = min_t
        curr_to = min_t - 1
        if len(t_list) < 200: break

    if not all_chunks: return pd.DataFrame()
    df = pd.concat(all_chunks, ignore_index=True)
    for c in ["open", "high", "low", "close", "volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")
    return df.dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)

def fetch_binance_raw(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    out, end_ts = [], None
    while len(out) < bars:
        limit = min(1000, bars - len(out))
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if end_ts: params["endTime"] = end_ts
        try:
            r = HTTP_SESSION.get("https://api.binance.com/api/v3/klines", params=params, timeout=5)
            if r.status_code != 200: break
            k = r.json()
            if not k or not isinstance(k, list): break
            out = k + out
            new_end = k[0][0] - 1
            if end_ts and new_end >= end_ts: break
            end_ts = new_end
            if len(k) < limit: break
        except Exception: break
    if not out: return pd.DataFrame()
    df = pd.DataFrame(out, columns=["ot","open","high","low","close","volume","ct","qv","n","tb","tq","ig"])
    df = df[["ot","open","high","low","close","volume"]].astype(float)
    df["time"] = (df["ot"] // 1000).astype("int64")
    return df[["time","open","high","low","close","volume"]].dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)

def parse_yahoo_json(j: dict) -> pd.DataFrame:
    try:
        result = j.get("chart", {}).get("result", [])
        if not result: return pd.DataFrame()
        res = result[0]
        ts = res.get("timestamp", [])
        q = res.get("indicators", {}).get("quote", [{}])[0]
        if not ts or not q: return pd.DataFrame()
        o, h, l, c, v = q.get("open", []), q.get("high", []), q.get("low", []), q.get("close", []), q.get("volume", [])
        rows = []
        for i in range(len(ts)):
            if ts[i] is not None and i < len(c) and c[i] is not None:
                rows.append({"time": ts[i], "open": o[i] if (i < len(o) and o[i] is not None) else c[i],
                             "high": h[i] if (i < len(h) and h[i] is not None) else c[i],
                             "low":  l[i] if (i < len(l) and l[i] is not None) else c[i], "close": c[i],
                             "volume": v[i] if (i < len(v) and v[i] is not None) else 0.0})
        return pd.DataFrame(rows)
    except Exception: return pd.DataFrame()

def fetch_yahoo_rest_api(symbol: str, tf: str, bars: int) -> pd.DataFrame:
    tf_info = TF.get(tf, TF["1d"])
    urls = [f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"]
    df = pd.DataFrame()
    for url in urls:
        try:
            r = HTTP_SESSION.get(url, params={"interval": tf_info["yf_iv"], "range": tf_info.get("yf_range", "60d")}, timeout=3.5)
            if r.status_code == 200:
                df = parse_yahoo_json(r.json())
                if not df.empty and len(df) >= 3: break
        except Exception: pass

    if df.empty or len(df) < 3:
        for fb in [{"interval":"1d","range":"5y"}, {"interval":"60m","range":"730d"}]:
            for url in urls:
                try:
                    r = HTTP_SESSION.get(url, params=fb, timeout=3.5)
                    if r.status_code == 200:
                        df = parse_yahoo_json(r.json())
                        if not df.empty and len(df) >= 3: break
                except Exception: pass
            if not df.empty and len(df) >= 3: break

    if (df.empty or len(df) < 3) and yf is not None:
        try:
            hist = yf.Ticker(symbol).history(period="2y", interval="1d")
            if not hist.empty:
                hist = hist.reset_index()
                tcol = "Datetime" if "Datetime" in hist.columns else "Date"
                hist["time"] = (pd.to_datetime(hist[tcol]).astype("int64") // 10**9).astype("int64")
                hist = hist.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
                df = hist[["time","open","high","low","close","volume"]]
        except Exception: pass

    if df.empty: return pd.DataFrame()
    for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")
    df = df.dropna().drop_duplicates(subset=["time"]).sort_values("time")
    if tf_info["base"] is not None and len(df) > 50: df = resample_ohlcv(df, tf_info["rule"])
    return df.tail(bars).reset_index(drop=True)

def fetch_ohlcv(market_type: str, exchange: str, symbol: str, tf: str, bars: int, fill_gaps: bool = False) -> pd.DataFrame:
    tf_info = TF[tf]
    if "คริปโต" in market_type:
        if exchange == "Bitkub":
            native = {"1m":"1","5m":"5","15m":"15","30m":"30","1h":"60","4h":"240","1d":"1D","1w":"1W"}
            if tf in native: df = fetch_bitkub_raw(symbol, native[tf], tf_info["sec"], bars)
            else:
                base_tf = tf_info["base"] or "1h"
                mult = max(1, tf_info["sec"] // TF[base_tf]["sec"])
                df = fetch_bitkub_raw(symbol, native.get(base_tf, "60"), TF[base_tf]["sec"], min(bars * mult, 25000))
                if not df.empty: df = resample_ohlcv(df, tf_info["rule"])
            if fill_gaps and not df.empty: df = fill_empty_bars(df, tf_info["sec"]).tail(bars).reset_index(drop=True)
        else:
            df = fetch_binance_raw(symbol, tf, bars)
    else:
        df = fetch_yahoo_rest_api(symbol, tf, bars)
    if df is None or df.empty: return pd.DataFrame()
    return df.tail(bars).reset_index(drop=True)

# ──────────────────────────── TICKERS & QUOTES ────────────────────────────
@st.cache_data(ttl=5, show_spinner=False)
def get_bitkub_all_tickers() -> dict:
    out = {}
    for url in ("https://api.bitkub.com/api/v3/market/ticker", "https://api.bitkub.com/api/market/ticker"):
        try:
            r = HTTP_SESSION.get(url, timeout=3)
            if r.status_code != 200: continue
            res = r.json()
            data = res.get("result", res) if isinstance(res, dict) else res
            items = [(d.get("symbol", ""), d) for d in data if isinstance(d, dict)] if isinstance(data, list) else list(data.items())
            for k, v in items:
                if not k or not isinstance(v, dict): continue
                k = str(k).upper()
                base = k[4:] if k.startswith("THB_") else k.replace("_THB", "")
                if not base: continue
                out[f"{base}_THB"] = v
                out[f"THB_{base}"] = v
            if out: return out
        except Exception: pass
    return out

def bitkub_pick(symbol: str) -> dict:
    bk = get_bitkub_all_tickers()
    s = (symbol or "").upper()
    base = s[4:] if s.startswith("THB_") else s.replace("_THB", "")
    return bk.get(f"{base}_THB", {}) or bk.get(f"THB_{base}", {}) or {}

@st.cache_data(ttl=15, show_spinner=False)
def fetch_item_quote(sym: str) -> dict:
    try:
        s = (sym or "").upper()
        if s.endswith("_THB") or s.startswith("THB_"):
            d = bitkub_pick(s)
            if d:
                return {"price": float(d.get("last", 0)), "change": float(d.get("change", 0)),
                        "pct": float(d.get("percentChange", d.get("percent_change", 0))),
                        "vol": float(d.get("baseVolume", d.get("base_volume", 0)))}
            return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

        if s.endswith("USDT") and "-" not in s:
            r = HTTP_SESSION.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}", timeout=3)
            if r.status_code == 200:
                d = r.json()
                return {"price": float(d["lastPrice"]), "change": float(d["priceChange"]),
                        "pct": float(d["priceChangePercent"]), "vol": float(d["volume"])}
            return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

        r = HTTP_SESSION.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d", timeout=3)
        if r.status_code == 200:
            meta = (r.json().get("chart", {}).get("result") or [{}])[0].get("meta", {})
            p = float(meta.get("regularMarketPrice", 0))
            prev = float(meta.get("chartPreviousClose", meta.get("previousClose", p)) or p)
            chg = p - prev; pct = (chg / prev * 100.0) if prev > 0 else 0.0
            if p > 0: return {"price": p, "change": chg, "pct": pct, "vol": float(meta.get("regularMarketVolume", 0))}
    except Exception: pass
    return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

def fmt_price(p: float) -> str:
    if p >= 1000: return f"{p:,.2f}"
    if p >= 1: return f"{p:.4f}"
    return f"{p:.6f}" if p > 0 else "0.00"

def fmt_chg(c: float) -> str:
    s = "+" if c > 0 else ""
    return f"{s}{c:.2f}" if abs(c) >= 1 else f"{s}{c:.4f}"

def fetch_unified_ticker(market_type: str, exchange: str, symbol: str, df_last: pd.DataFrame) -> dict:
    try:
        if "คริปโต" in market_type:
            if exchange == "Bitkub":
                d = bitkub_pick(symbol)
                if d:
                    return {"price": float(d.get("last", 0)), "change": float(d.get("change", 0)),
                            "pct": float(d.get("percentChange", d.get("percent_change", 0))),
                            "bid": float(d.get("highestBid", d.get("highest_bid", 0))),
                            "ask": float(d.get("lowestAsk", d.get("lowest_ask", 0))),
                            "high": float(d.get("high24hr", d.get("high_24_hr", d.get("high", 0)))),
                            "low": float(d.get("low24hr", d.get("low_24_hr", d.get("low", 0)))),
                            "vol": float(d.get("baseVolume", d.get("base_volume", 0)))}
            elif exchange == "Binance":
                r = HTTP_SESSION.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=3)
                if r.status_code == 200:
                    d = r.json()
                    return {"price": float(d["lastPrice"]), "change": float(d["priceChange"]),
                            "pct": float(d["priceChangePercent"]), "bid": float(d["bidPrice"]),
                            "ask": float(d["askPrice"]), "high": float(d["highPrice"]),
                            "low": float(d["lowPrice"]), "vol": float(d["volume"])}
        else:
            q = fetch_item_quote(symbol)
            if q["price"] > 0:
                return {"price": q["price"], "change": q["change"], "pct": q["pct"],
                        "bid": q["price"]*0.9998, "ask": q["price"]*1.0002,
                        "high": q["price"]*1.01, "low": q["price"]*0.99, "vol": q["vol"]}

        if not df_last.empty and len(df_last) >= 2:
            last, prev = df_last.iloc[-1], df_last.iloc[-2]
            chg = last.close - prev.close
            return {"price": float(last.close), "change": float(chg),
                    "pct": float(chg / prev.close * 100.0) if prev.close else 0.0,
                    "bid": float(last.close*0.9998), "ask": float(last.close*1.0002),
                    "high": float(df_last.tail(24)["high"].max()),
                    "low": float(df_last.tail(24)["low"].min()),
                    "vol": float(df_last.tail(24)["volume"].sum())}
    except Exception: pass
    return {}

# ──────────────────────────── INDICATORS ────────────────────────────
def rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)

def calc_bollinger_bands(df: pd.DataFrame, length: int = 20, mult: float = 2.0):
    df = df.copy()
    basis = df["close"].rolling(length).mean()
    dev = df["close"].rolling(length).std() * mult
    df["bb_upper"] = basis + dev
    df["bb_lower"] = basis - dev
    df["bb_basis"] = basis
    return df

def calc_volume_profile(df: pd.DataFrame, bins_count: int = 30, va_pct: float = 0.70):
    if df.empty or len(df) < 5:
        return None, None, None
    p_min = df["low"].min()
    p_max = df["high"].max()
    if p_min == p_max:
        return None, None, None

    bins = np.linspace(p_min, p_max, bins_count + 1)
    bin_vols = np.zeros(bins_count)
    
    for r in df.itertuples():
        c_price = r.close
        v = float(r.volume)
        idx = int(np.digitize(c_price, bins) - 1)
        idx = max(0, min(bins_count - 1, idx))
        bin_vols[idx] += v

    poc_idx = int(np.argmax(bin_vols))
    poc_price = (bins[poc_idx] + bins[poc_idx + 1]) / 2.0

    total_vol = bin_vols.sum()
    target_vol = total_vol * va_pct
    cur_vol = bin_vols[poc_idx]
    up_idx, dn_idx = poc_idx, poc_idx

    while cur_vol < target_vol and (up_idx < bins_count - 1 or dn_idx > 0):
        next_up = bin_vols[up_idx + 1] if up_idx < bins_count - 1 else 0
        next_dn = bin_vols[dn_idx - 1] if dn_idx > 0 else 0
        if next_up >= next_dn and up_idx < bins_count - 1:
            up_idx += 1
            cur_vol += bin_vols[up_idx]
        elif dn_idx > 0:
            dn_idx -= 1
            cur_vol += bin_vols[dn_idx]
        else:
            break

    vah_price = bins[up_idx + 1]
    val_price = bins[dn_idx]
    return float(poc_price), float(vah_price), float(val_price)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_analytics(market_type: str, exchange: str, symbol: str) -> dict:
    try:
        if "คริปโต" in market_type and exchange == "Bitkub":
            df = fetch_bitkub_raw(symbol, "1D", 86400, 380)
        elif "คริปโต" in market_type:
            r = HTTP_SESSION.get("https://api.binance.com/api/v3/klines", params={"symbol": symbol, "interval": "1d", "limit": 375}, timeout=5)
            raw = r.json()
            if not raw: return {}
            cols = ["ot","open","high","low","close","volume","ct","qv","n","tb","tq","ig"][:len(raw[0])]
            df = pd.DataFrame(raw, columns=cols)[["ot","open","high","low","close","volume"]].astype(float)
            df["time"] = (df["ot"] // 1000).astype("int64")
        else:
            df = fetch_yahoo_rest_api(symbol, "1d", 380)

        if df is None or df.empty: return {}
        df = df.dropna().sort_values("time").reset_index(drop=True)
        if len(df) < 15: return {}

        now_p, n = df.iloc[-1]["close"], len(df)
        def ret(b): return (((now_p / df.iloc[-1-b]["close"]) - 1.0) * 100.0) if n > b else 0.0

        r1w, r1m, r3m, r6m, r1y = ret(7), ret(30), ret(90), ret(180), ret(365)
        jan1 = int(datetime.datetime(datetime.datetime.now().year, 1, 1).timestamp())
        ytd_df = df[df["time"] >= jan1]
        rytd = (((now_p / ytd_df.iloc[0]["close"]) - 1.0) * 100.0) if not ytd_df.empty else r1m

        rsi_val = rsi_wilder(df["close"], 14).iloc[-1]
        ema20 = df["close"].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df["close"].ewm(span=50, adjust=False).mean().iloc[-1]
        score = (1 if rsi_val > 55 else (-1 if rsi_val < 45 else 0)) + (1 if now_p > ema20 else -1) + (1 if ema20 > ema50 else -1)

        if score >= 2:    lbl, col, ang = "มีแรงซื้อ", UP, 45
        elif score <= -2: lbl, col, ang = "มีแรงขาย", DOWN, -45
        else:             lbl, col, ang = "เป็นกลาง", "#9aa0a6", 0

        return {"vol_30d_avg": df.tail(30)["volume"].mean(), "1W": r1w, "1M": r1m, "3M": r3m,
                "6M": r6m, "YTD": rytd, "1Y": r1y, "tech_label": lbl, "tech_color": col, "angle": ang}
    except Exception: return {}

def diamond_armor(df: pd.DataFrame, fast=21, slow=55, rsi_len=14):
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["rsi"] = rsi_wilder(df["close"], rsi_len)
    df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_sig"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    up_cross = (df.ema_fast > df.ema_slow) & (df.ema_fast.shift() <= df.ema_slow.shift())
    dn_cross = (df.ema_fast < df.ema_slow) & (df.ema_fast.shift() >= df.ema_slow.shift())
    df["signal"] = np.select([up_cross & (df.rsi > 45), dn_cross & (df.rsi < 55)], ["BUY", "SELL ALL"], default="")

    last, prev = df.iloc[-1], df.iloc[-2]
    stats = {
        "price": last.close, "change_pct": (last.close / prev.close - 1) * 100 if prev.close else 0.0,
        "rsi": last.rsi, "trend": "UP" if last.ema_fast > last.ema_slow else "DOWN",
        "buys": int((df.signal == "BUY").sum()), "sells": int((df.signal == "SELL ALL").sum()), "bars": len(df),
    }
    return df, stats

# ──────────────────────────── AVATAR BUILDER ────────────────────────────
def build_asset_icon_html(sym: str, tag_color: str = "#1E1E1E", size: int = 18) -> str:
    clean_code = sym.split(".")[0].replace("_THB","").replace("-USDT","").replace("USDT","").replace("=F","").replace("=X","")
    clean_lower = clean_code.lower()
    fallback_avatar = f"https://ui-avatars.com/api/?name={clean_code[:3]}&background=0A0A0A&color=D1D4DC&rounded=true&bold=true&size=32"
    icon_url = f"https://assets.coincap.io/assets/icons/{clean_lower}@2x.png"
    return f"""<div style="display:flex;align-items:center;justify-content:center;height:24px;gap:3px;">
        <div style="width:3px;height:16px;border-radius:2px;background:{tag_color};flex-shrink:0;"></div>
        <img src="{icon_url}" onerror="this.onerror=null;this.src='{fallback_avatar}';" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;background:#050505;border:1px solid #1E1E1E;">
    </div>"""

# ──────────────────────────── QUOTE CARD RENDERER ────────────────────────────
def render_tv_quote_card(tk: dict, an: dict, symbol: str, label_name: str):
    if not tk:
        st.caption("กำลังเชื่อมต่อข้อมูลราคา...")
        return

    c_color = UP if tk["change"] >= 0 else DOWN
    bg_pill = "rgba(38, 166, 154, 0.15)" if tk["change"] >= 0 else "rgba(239, 83, 80, 0.15)"
    sign = "+" if tk["change"] >= 0 else ""
    span = tk["high"] - tk["low"]
    ratio = max(0, min(100, ((tk["price"] - tk["low"]) / span * 100) if span > 0 else 50))
    vol_30d = f"{an.get('vol_30d_avg', 0):,.2f}" if an else "-"

    def p_box(lbl, val):
        col = UP if val >= 0 else DOWN
        bg = "rgba(38, 166, 154, 0.12)" if val >= 0 else "rgba(239, 83, 80, 0.12)"
        s = "+" if val >= 0 else ""
        return f"""<div style="background:{bg}; border:1px solid {col}40; border-radius:4px; padding:4px 2px; text-align:center;">
<div style="font-size:11px; font-weight:700; color:{col}; font-family:monospace;">{s}{val:.2f}%</div>
<div style="font-size:9px; color:#787b86;">{lbl}</div></div>"""

    grid_perf = ""
    if an:
        grid_perf = f"""<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:4px; margin-bottom:10px;">
{p_box('1W', an.get('1W',0))}{p_box('1M', an.get('1M',0))}{p_box('3M', an.get('3M',0))}
{p_box('6M', an.get('6M',0))}{p_box('YTD', an.get('YTD',0))}{p_box('1Y', an.get('1Y',0))}</div>"""
    else:
        grid_perf = """<div style="font-size:10px; color:#787b86; padding:6px 0;">ไม่มีข้อมูลย้อนหลังเพียงพอ</div>"""

    t_angle = an.get("angle", 0) if an else 0
    t_label = an.get("tech_label", "เป็นกลาง") if an else "เป็นกลาง"
    t_color = an.get("tech_color", "#9aa0a6") if an else "#9aa0a6"
    desc_display = CHINA_STOCK_NAMES.get(symbol, COMMODITY_NAMES.get(symbol, ""))
    sub_title_html = f"<div style='font-size:10px; color:#00bcd4; margin-bottom:4px;'>{desc_display}</div>" if desc_display else ""

    st.markdown(f"""<div style="background-color:#0A0A0A; border-radius:6px; padding:8px 6px; color:#D1D4DC; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; border:1px solid #1E1E1E;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
<span style="font-size:13px; font-weight:700; color:#fff;">{symbol}</span>
<span style="background:#1A1A1A; color:#9aa0a6; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:600;">{label_name}</span></div>
{sub_title_html}
<div style="font-size:9px; color:#787b86; margin-bottom:6px;">ตลาดเปิดสด</div>
<div style="font-size:20px; font-weight:700; color:#fff; letter-spacing:-0.5px; line-height:1.1;">{tk['price']:,.2f}</div>
<div style="display:inline-block; margin-top:3px; margin-bottom:8px; background:{bg_pill}; color:{c_color}; padding:1px 5px; border-radius:3px; font-size:10px; font-weight:700;">{sign}{tk['change']:,.2f} &nbsp; ({sign}{tk['pct']:.2f}%)</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; margin-bottom:8px; font-family:monospace;">
<div style="background:rgba(41,98,255,0.1); border:1px solid rgba(41,98,255,0.4); border-radius:4px; padding:3px; text-align:center;">
<div style="font-size:8px; color:#2962ff; font-weight:600;">BID (ซื้อ)</div>
<div style="font-size:10px; color:#D1D4DC; font-weight:700;">{tk.get('bid', tk['price']):,.2f}</div></div>
<div style="background:rgba(239,83,80,0.1); border:1px solid rgba(239,83,80,0.4); border-radius:4px; padding:3px; text-align:center;">
<div style="font-size:8px; color:#ef5350; font-weight:600;">ASK (ขาย)</div>
<div style="font-size:10px; color:#D1D4DC; font-weight:700;">{tk.get('ask', tk['price']):,.2f}</div></div></div>
<div style="font-size:9px; color:#787b86; margin-bottom:2px; font-weight:600;">ช่วง 24 ชม.</div>
<div style="display:flex; justify-content:space-between; font-size:9px; font-family:monospace; color:#9aa0a6; margin-bottom:2px;">
<span>{tk.get('low', tk['price']):,.2f}</span><span>{tk.get('high', tk['price']):,.2f}</span></div>
<div style="background:#1A1A1A; height:3px; border-radius:2px; position:relative; margin-bottom:8px;">
<div style="position:absolute; left:{ratio}%; top:-3px; width:9px; height:9px; background:#fff; border:2px solid #2962ff; border-radius:50%; transform:translateX(-50%);"></div></div>
<div style="display:flex; justify-content:space-between; font-size:9px; padding:2px 0;">
<span style="color:#787b86;">ปริมาณ (24h)</span><span style="color:#D1D4DC; font-family:monospace; font-weight:600;">{tk.get('vol', 0):,.2f}</span></div>
<div style="display:flex; justify-content:space-between; font-size:9px; padding:2px 0; margin-bottom:8px;">
<span style="color:#787b86;">เฉลี่ย (30 วัน)</span><span style="color:#D1D4DC; font-family:monospace; font-weight:600;">{vol_30d}</span></div>
<div style="font-size:10px; font-weight:700; color:#fff; margin-bottom:4px; border-top:1px solid #1E1E1E; padding-top:6px;">ประสิทธิภาพ</div>
{grid_perf}
<div style="font-size:10px; font-weight:700; color:#fff; margin-bottom:2px;">ทางเทคนิค</div>
<div style="text-align:center; margin-top:-4px;">
<svg width="130" height="68" viewBox="0 0 140 75">
<path d="M 15 70 A 55 55 0 0 1 125 70" fill="none" stroke="#1E1E1E" stroke-width="8" stroke-linecap="round"/>
<path d="M 15 70 A 55 55 0 0 1 50 25" fill="none" stroke="{DOWN}" stroke-width="8" stroke-linecap="round"/>
<path d="M 90 25 A 55 55 0 0 1 125 70" fill="none" stroke="{UP}" stroke-width="8" stroke-linecap="round"/>
<g transform="translate(70, 70) rotate({t_angle})">
<line x1="0" y1="0" x2="0" y2="-50" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="0" cy="0" r="4" fill="#fff"/></g></svg>
<div style="font-size:12px; font-weight:700; color:{t_color}; margin-top:-6px;">{t_label}</div></div>
</div>""", unsafe_allow_html=True)

# ──────────────────────────── CHART BUILDER ────────────────────────────
def build_charts(df, symbol, tf, show_ema, show_vol, show_sig, label_size,
                 show_rsi, show_macd, pane_order, main_h, rsi_h, macd_h,
                 show_bb=False, show_vp=False, poc=None, vah=None, val=None):
    d = df.copy()
    d["time"] = d["time"] + (7 * 3600)  # GMT+7
    ts_opts = {
        "borderColor": "#1E1E1E", "timeVisible": True, "secondsVisible": tf in ("1m", "3m", "5m"),
        "fixLeftEdge": False, "rightOffset": 5,
        "handleScroll": {"mouseWheel": True, "pressedMouseMove": True, "horzTouchDrag": True, "vertTouchDrag": True},
        "handleScale": {"axisPressedMouseMove": True, "mouseWheel": True, "pinch": True},
    }
    base_chart = {
        "layout": {"background": {"type": "solid", "color": "#000000"}, "textColor": "#D1D4DC"},
        "grid": {"vertLines": {"color": "#141414"}, "horzLines": {"color": "#141414"}},
        "crosshair": {"mode": 0}, "rightPriceScale": {"borderColor": "#1E1E1E"}, "timeScale": ts_opts,
    }
    charts = []
    candles = d[["time","open","high","low","close"]].to_dict("records")
    price_series = [{"type": "Candlestick", "data": candles,
                     "options": {"upColor": UP, "downColor": DOWN, "borderVisible": False, "wickUpColor": UP, "wickDownColor": DOWN}}]

    if show_sig:
        markers = []
        for r in d[d.signal != ""].itertuples():
            is_buy = r.signal == "BUY"
            markers.append({"time": int(r.time), "position": "belowBar" if is_buy else "aboveBar",
                            "color": UP if is_buy else DOWN, "shape": "arrowUp" if is_buy else "arrowDown",
                            "text": r.signal, "size": label_size})
        price_series[0]["markers"] = markers

    if show_ema:
        for col, color in (("ema_fast", "#f5c518"), ("ema_slow", "#8e7bff")):
            price_series.append({"type": "Line", "data": d[["time", col]].rename(columns={col: "value"}).to_dict("records"),
                                 "options": {"color": color, "lineWidth": 2, "priceLineVisible": False}})

    if show_bb and "bb_upper" in d.columns:
        price_series.append({"type": "Line",
                             "data": d[["time", "bb_upper"]].dropna().rename(columns={"bb_upper": "value"}).to_dict("records"),
                             "options": {"color": "rgba(41, 98, 255, 0.6)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}})
        price_series.append({"type": "Line",
                             "data": d[["time", "bb_lower"]].dropna().rename(columns={"bb_lower": "value"}).to_dict("records"),
                             "options": {"color": "rgba(41, 98, 255, 0.6)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}})
        price_series.append({"type": "Line",
                             "data": d[["time", "bb_basis"]].dropna().rename(columns={"bb_basis": "value"}).to_dict("records"),
                             "options": {"color": "rgba(255, 152, 0, 0.7)", "lineWidth": 1, "lineStyle": 0, "priceLineVisible": False}})

    if show_vp and poc is not None:
        def mk_const(val): return [{"time": int(t), "value": float(val)} for t in d["time"]]
        price_series.append({"type": "Line", "data": mk_const(poc),
                             "options": {"color": "#e91e63", "lineWidth": 2, "lineStyle": 0, "priceLineVisible": True, "title": "POC"}})
        if vah is not None:
            price_series.append({"type": "Line", "data": mk_const(vah),
                                 "options": {"color": "#00bcd4", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": True, "title": "VAH"}})
        if val is not None:
            price_series.append({"type": "Line", "data": mk_const(val),
                                 "options": {"color": "#00bcd4", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": True, "title": "VAL"}})

    if show_vol:
        vol = [{"time": int(r.time), "value": float(r.volume),
                "color": UP + "80" if r.close >= r.open else DOWN + "80"} for r in d.itertuples()]
        price_series.append({"type": "Histogram", "data": vol,
                             "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol"},
                             "priceScale": {"scaleMargins": {"top": 0.8, "bottom": 0}}})

    charts.append({"chart": {**base_chart, "height": main_h,
                             "watermark": {"visible": True, "text": f"{symbol} · {tf}", "fontSize": 42, "color": "rgba(255,255,255,0.05)"}},
                   "series": price_series})

    def make_rsi_pane():
        rsi_data = d[["time","rsi"]].rename(columns={"rsi": "value"}).to_dict("records")
        mk = lambda v: [{"time": int(t), "value": v} for t in d["time"]]
        return {"chart": {**base_chart, "height": rsi_h,
                          "watermark": {"visible": True, "text": "RSI (14)", "fontSize": 18, "color": "rgba(0, 188, 212, 0.08)"}},
                "series": [
                    {"type": "Line", "data": mk(70.0), "options": {"color": "rgba(239,83,80,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                    {"type": "Line", "data": mk(50.0), "options": {"color": "rgba(120,123,134,0.3)", "lineWidth": 1, "lineStyle": 3, "priceLineVisible": False}},
                    {"type": "Line", "data": mk(30.0), "options": {"color": "rgba(38,166,154,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                    {"type": "Line", "data": rsi_data, "options": {"color": "#00bcd4", "lineWidth": 2, "priceLineVisible": True}},
                ]}

    def make_macd_pane():
        macd_line = d[["time","macd"]].rename(columns={"macd": "value"}).to_dict("records")
        sig_line  = d[["time","macd_sig"]].rename(columns={"macd_sig": "value"}).to_dict("records")
        hist = [{"time": int(r.time), "value": float(r.macd_hist), "color": UP + "90" if r.macd_hist >= 0 else DOWN + "90"} for r in d.itertuples()]
        return {"chart": {**base_chart, "height": macd_h,
                          "watermark": {"visible": True, "text": "MACD (12, 26, 9)", "fontSize": 18, "color": "rgba(0, 230, 118, 0.08)"}},
                "series": [
                    {"type": "Histogram", "data": hist, "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "macd_hist"}},
                    {"type": "Line", "data": macd_line, "options": {"color": "#00e676", "lineWidth": 2, "priceLineVisible": False}},
                    {"type": "Line", "data": sig_line, "options": {"color": "#ff5252", "lineWidth": 2, "priceLineVisible": False}},
                ]}

    for p in pane_order:
        if p == "rsi" and show_rsi: charts.append(make_rsi_pane())
        elif p == "macd" and show_macd: charts.append(make_macd_pane())
    return charts

# ──────────────────────────── SIDEBAR ────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบ")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("💻 Desktop", use_container_width=True): st.session_state["mobile_mode"] = False; st.rerun()
    with col_m2:
        if st.button("📱 Mobile", use_container_width=True): st.session_state["mobile_mode"] = True; st.rerun()

    # กลุ่มที่ 1: จัดการตลาดและสัญลักษณ์หุ้น
    with st.expander("📌 ตลาดและสินทรัพย์", expanded=True):
        market_type = st.selectbox("หมวดหมู่ตลาด", list(DEFAULT_PRESETS.keys()), index=0)
        exchange = "Binance"
        if "คริปโต" in market_type:
            exchange = st.radio("Exchange", ["Bitkub", "Binance", "Bybit", "OKX", "MEXC"], horizontal=True)
            raw_options = DEFAULT_PRESETS[market_type].get(exchange, [])
        else:
            raw_options = DEFAULT_PRESETS.get(market_type, [])

        available_symbols = sorted(set(raw_options + st.session_state["custom_symbols"]))
        if not available_symbols: available_symbols = ["VNM.VN"]
        if "current_symbol" not in st.session_state or not st.session_state["current_symbol"]:
            st.session_state["current_symbol"] = available_symbols[0]
        if st.session_state["current_symbol"] not in available_symbols:
            available_symbols = sorted(set(available_symbols + [st.session_state["current_symbol"]]))

        cur_idx = available_symbols.index(st.session_state["current_symbol"])
        def format_symbol_label(s: str) -> str:
            if s in CHINA_STOCK_NAMES: return f"{s} — {CHINA_STOCK_NAMES[s]}"
            if s in COMMODITY_NAMES: return f"{s} — {COMMODITY_NAMES[s]}"
            return s

        picked = st.selectbox("🔍 ค้นหา / เลือก:", available_symbols, index=cur_idx, format_func=format_symbol_label)
        if picked != st.session_state["current_symbol"]:
            st.session_state["current_symbol"] = picked
            st.rerun()

        new_ticker = st.text_input("➕ เพิ่ม Ticker:", placeholder="เช่น VNM.VN, PLTR")
        if st.button("บันทึก Ticker", use_container_width=True) and new_ticker:
            sym_clean = new_ticker.strip().upper()
            if sym_clean not in st.session_state["custom_symbols"]:
                st.session_state["custom_symbols"].insert(0, clean)
            st.session_state["current_symbol"] = sym_clean
            st.rerun()

        cur_sym = st.session_state["current_symbol"]
        _rm, _re = resolve_route(cur_sym, market_type, exchange)
        st.caption(f"📡 แหล่งข้อมูล: **{route_label(_rm, _re)}**")

        st.caption(f"⭐ ติดดาว: **{cur_sym}**")
        star_cols = st.columns(5)
        for i, (cat_label, cat_info) in enumerate(STAR_CATEGORIES.items()):
            with star_cols[i]:
                has = cur_sym in st.session_state["star_watchlists"][cat_label]
                btn_text = "★" if has else cat_info["symbol"]
                if st.button(btn_text, key=f"qs_btn_{i}", use_container_width=True, help=f"{cat_label}"):
                    if has: st.session_state["star_watchlists"][cat_label].remove(cur_sym)
                    else: st.session_state["star_watchlists"][cat_label].append(cur_sym)
                    st.rerun()

    # กลุ่มที่ 2: ตั้งค่าแท่งเทียน & ความถี่การดึงข้อมูล
    with st.expander("⏱️ แท่งเทียน & รีเฟรช", expanded=False):
        tf = st.selectbox("Timeframe", list(TF.keys()), index=11)
        bars = st.slider("จำนวนแท่ง", 300, 25000, 3000, step=500)
        fill_gaps = st.checkbox("🧩 เติมแท่งว่าง (Bitkub)", value=False)
        auto = st.checkbox("🟢 Auto-refresh", False)
        every = st.slider("ความถี่ (วิ)", 3, 60, 5, step=1, disabled=not auto)
        reload_btn = st.button("🔄 โหลดใหม่ทั้งหมด", use_container_width=True)

    # กลุ่มที่ 3: อินดิเคเตอร์ & ความสูงชาร์ต
    with st.expander("📊 อินดิเคเตอร์ & ปรับกราฟ", expanded=False):
        show_ema = st.checkbox("EMA 21 / 55", True)
        show_vol = st.checkbox("Volume", True)
        st.session_state["show_rsi"]  = st.checkbox("ช่อง RSI (14)", value=st.session_state["show_rsi"])
        st.session_state["show_macd"] = st.checkbox("ช่อง MACD", value=st.session_state["show_macd"])
        show_sig = st.checkbox("Signals (BUY/SELL)", True)
        label_size = st.slider("ขนาด label", 0, 3, 1)

        st.markdown("---")
        show_bb = st.checkbox("Bollinger Bands (BB)", False)
        if show_bb:
            col_bb1, col_bb2 = st.columns(2)
            with col_bb1: bb_len = st.number_input("BB Length", min_value=5, max_value=100, value=20, step=1)
            with col_bb2: bb_mult = st.number_input("BB Mult", min_value=0.5, max_value=5.0, value=2.0, step=0.1)
        else:
            bb_len, bb_mult = 20, 2.0

        show_vp = st.checkbox("Volume Profile (POC / VAH / VAL)", False)
        if show_vp:
            col_vp1, col_vp2 = st.columns(2)
            with col_vp1: vp_bins = st.slider("Bins (ความละเอียด)", 10, 60, 30, step=5)
            with col_vp2: vp_va = st.slider("Value Area %", 50, 90, 70, step=5) / 100.0
        else:
            vp_bins, vp_va = 30, 0.70

        st.markdown("---")
        if st.button("⇵ สลับตำแหน่ง RSI / MACD", use_container_width=True):
            st.session_state["pane_order"] = list(reversed(st.session_state["pane_order"]))
            st.rerun()

        main_h = st.slider("ความสูงกราฟหลัก", 300, 900, 420 if st.session_state["mobile_mode"] else 520, step=50)
        rsi_h  = st.slider("ความสูง RSI", 80, 400, 120, step=20) if st.session_state["show_rsi"] else 120
        macd_h = st.slider("ความสูง MACD", 80, 400, 120, step=20) if st.session_state["show_macd"] else 120

# ──────────────────────────── DASHBOARD ────────────────────────────
@st.fragment(run_every=every if auto else None)
def dashboard():
    symbol = st.session_state.get("current_symbol", "VNM.VN")
    r_market, r_exchange = resolve_route(symbol, market_type, exchange)
    label_display = route_label(r_market, r_exchange)

    state_key = f"{r_market}_{r_exchange}_{symbol}_{tf}_{bars}_{fill_gaps}"
    if ("df_data" not in st.session_state) or (st.session_state.get("active_key") != state_key) or reload_btn:
        with st.spinner(f"กำลังโหลดข้อมูล {symbol} …"):
            df = fetch_ohlcv(r_market, r_exchange, symbol, tf, bars, fill_gaps)
        st.session_state["df_data"] = df
        st.session_state["active_key"] = state_key
    else:
        df = st.session_state.get("df_data", pd.DataFrame())

    if df.empty or len(df) < 3:
        st.warning(f"ไม่พบข้อมูลสำหรับ {symbol} ({label_display})")
        return

    df, stats = diamond_armor(df)

    if show_bb:
        df = calc_bollinger_bands(df, length=int(bb_len), mult=float(bb_mult))

    poc, vah, val = None, None, None
    if show_vp:
        poc, vah, val = calc_volume_profile(df, bins_count=int(vp_bins), va_pct=float(vp_va))

    trend_color = UP if stats["trend"] == "UP" else DOWN
    chg_color = UP if stats["change_pct"] >= 0 else DOWN
    display_title = f"{symbol} — {CHINA_STOCK_NAMES[symbol]}" if symbol in CHINA_STOCK_NAMES else symbol

    # ── Top Bar พร้อมปุ่มเต็มหน้าจอและหลบ Deploy ──
    fs_script = """
    <script>
        const btn = document.getElementById('tvFsBtn');
        if (btn) {
            btn.addEventListener('click', () => {
                const doc = window.parent.document;
                if (!doc.fullscreenElement) {
                    doc.documentElement.requestFullscreen().catch(e => {});
                    btn.innerText = "🗗 ย่อจอ";
                } else {
                    if (doc.exitFullscreen) { doc.exitFullscreen().catch(e => {}); }
                    btn.innerText = "⛶ เต็มจอ";
                }
            });
        }
    </script>
    """
    top_bar_html = f"""<div style="background-color:#0A0A0A; border:1px solid #1E1E1E; border-radius:4px; padding:6px 12px; font-family:-apple-system,BlinkMacSystemFont,monospace; font-size:11px; color:#D1D4DC; display:flex; justify-content:space-between; align-items:center; width:100%; box-sizing:border-box;">
        <div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
            <span style="color:#00bcd4; font-weight:bold;">📈 {display_title}</span> &nbsp;
            <span style="background:#1A1A1A; padding:1px 5px; border-radius:3px; font-size:10px; color:#9aa0a6;">{label_display}</span> &nbsp;|&nbsp;
            ราคา: <b>{stats['price']:,.2f}</b> &nbsp;|&nbsp;
            เปลี่ยน: <span style="color:{chg_color}; font-weight:bold;">{stats['change_pct']:+.2f}%</span> &nbsp;|&nbsp;
            RSI: <b>{stats['rsi']:.1f}</b> &nbsp;|&nbsp;
            เทรนด์: <span style="color:{trend_color}; font-weight:bold;">{stats['trend']}</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
            <span style="font-size:10px; color:#787b86;">● LIVE</span>
            <button id="tvFsBtn" style="background:#161a21; border:1px solid #2a2e39; color:#d1d4dc; border-radius:4px; font-size:11px; font-weight:bold; padding:2px 8px; cursor:pointer; height:22px; line-height:1; display:flex; align-items:center; justify-content:center;" title="โหมดเต็มหน้าจอ">⛶ เต็มจอ</button>
        </div>
    </div>""" + fs_script
    components.html(top_bar_html, height=40)

    charts = build_charts(df, symbol, tf, show_ema, show_vol, show_sig, label_size,
                          st.session_state["show_rsi"], st.session_state["show_macd"],
                          st.session_state["pane_order"], main_h, rsi_h, macd_h,
                          show_bb=show_bb, show_vp=show_vp, poc=poc, vah=vah, val=val)

    # ── โหมดมือถือ ──
    if st.session_state["mobile_mode"]:
        for p in st.session_state["pane_order"]:
            if p == "rsi" and st.session_state["show_rsi"]:
                st.markdown('<div class="pane-toolbar"><span>📉 RSI (14)</span></div>', unsafe_allow_html=True)
            elif p == "macd" and st.session_state["show_macd"]:
                st.markdown('<div class="pane-toolbar"><span>📊 MACD (12, 26, 9)</span></div>', unsafe_allow_html=True)
        renderLightweightCharts(charts, key="chart_mob_render")

        with st.expander("✨ สินทรัพย์เข้าใหม่ & รายการโปรด", expanded=True):
            new_items = st.session_state.get("custom_symbols", [])
            for s_item in list(new_items):
                q = fetch_item_quote(s_item)
                val_col = UP if q["change"] >= 0 else DOWN
                c1, c2, c3 = st.columns([2, 1.5, 1])
                with c1:
                    if st.button(f"{s_item}", key=f"mob_item_{s_item}", use_container_width=True):
                        st.session_state["current_symbol"] = s_item; st.rerun()
                with c2: st.markdown(f"<div style='text-align:right; font-family:monospace;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div style='text-align:right; color:{val_col};'>{q['pct']:+.2f}%</div>", unsafe_allow_html=True)

        with st.expander("📊 ข้อมูลตลาด 24h & มาตรวัดเทคนิค", expanded=True):
            tk_data = fetch_unified_ticker(r_market, r_exchange, symbol, df)
            an_data = fetch_market_analytics(r_market, r_exchange, symbol)
            render_tv_quote_card(tk_data, an_data, symbol, label_display)
        return

    # ── โหมดเดสก์ท็อป: ปรับแผงขวา 3 ระดับ (S, M, L) และพับเก็บได้ ──
    layout_ratios = {
        "S": [4.1, 0.12, 0.78],
        "M": [3.6, 0.12, 1.28],
        "L": [3.1, 0.12, 1.78]
    }
    cur_size = st.session_state.get("panel_size", "M")

    if st.session_state["panel_open"]:
        col_chart, col_toggle, col_quote = st.columns(layout_ratios[cur_size])
    else:
        col_chart, col_toggle = st.columns([4.88, 0.12])

    with col_chart:
        for p in st.session_state["pane_order"]:
            if p == "rsi" and st.session_state["show_rsi"]:
                st.markdown('<div class="pane-toolbar"><span>📉 RSI (14)</span></div>', unsafe_allow_html=True)
            elif p == "macd" and st.session_state["show_macd"]:
                st.markdown('<div class="pane-toolbar"><span>📊 MACD (12, 26, 9)</span></div>', unsafe_allow_html=True)
        
        st.markdown('<div style="width: 100%; overflow: hidden;">', unsafe_allow_html=True)
        renderLightweightCharts(charts, key=f"chart_desk_{symbol}_{tf}_{main_h}_{cur_size}_{st.session_state['panel_open']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_toggle:
        btn_label = "❯" if st.session_state["panel_open"] else "❮"
        if st.button(btn_label, key="toggle_panel_btn", help="ย่อ/ขยายแผงขวา", use_container_width=True):
            st.session_state["panel_open"] = not st.session_state["panel_open"]
            st.rerun()

    if st.session_state["panel_open"]:
        with col_quote:
            # แถบควบคุมขนาด 3 ระดับ เล็ก (S) / ปกติ (M) / กว้าง (L)
            cs_col1, cs_col2, cs_col3 = st.columns(3)
            with cs_col1:
                if st.button("เล็ก", use_container_width=True, key="sz_s"):
                    st.session_state["panel_size"] = "S"; st.rerun()
            with cs_col2:
                if st.button("ปกติ", use_container_width=True, key="sz_m"):
                    st.session_state["panel_size"] = "M"; st.rerun()
            with cs_col3:
                if st.button("กว้าง", use_container_width=True, key="sz_l"):
                    st.session_state["panel_size"] = "L"; st.rerun()

            # 1. สินทรัพย์เข้าใหม่
            with st.expander("✨ สินทรัพย์เข้าใหม่ (New Listings)", expanded=True):
                col_in, col_add = st.columns([3, 1])
                with col_in:
                    quick_sym = st.text_input("ชื่อย่อ", placeholder="เช่น VNM.VN", label_visibility="collapsed", key="quick_add_sym")
                with col_add:
                    if st.button("➕", use_container_width=True, key="btn_quick_add") and quick_sym:
                        clean = quick_sym.strip().upper()
                        if clean not in st.session_state["custom_symbols"]:
                            st.session_state["custom_symbols"].insert(0, clean)
                            st.session_state["current_symbol"] = clean
                            st.rerun()

                new_items = st.session_state.get("custom_symbols", [])
                for s_item in list(new_items):
                    q = fetch_item_quote(s_item)
                    val_col = UP if q["change"] >= 0 else DOWN
                    s_lbl = CHINA_STOCK_NAMES.get(s_item, COMMODITY_NAMES.get(s_item, s_item.replace("_THB","").replace("-USDT","").replace("USDT","").replace(".BK","").replace(".VN","")))
                    c_dot, a, b, dcol = st.columns([0.4, 2.0, 1.6, 1.4])
                    with c_dot: st.markdown("<div style='text-align:center; color:#00bcd4;'>●</div>", unsafe_allow_html=True)
                    with a:
                        if st.button(f"{s_lbl}", key=f"nwl_{s_item}", use_container_width=True):
                            st.session_state["current_symbol"] = s_item; st.rerun()
                    with b: st.markdown(f"<div style='font-family:monospace; text-align:right; color:#fff;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
                    with dcol: st.markdown(f"<div style='font-family:monospace; text-align:right; color:{val_col};'>{q['pct']:+.2f}%</div>", unsafe_allow_html=True)

            # 2. Watchlist
            with st.expander("⭐ รายการที่น่าสนใจ (Watchlist)", expanded=True):
                star_names = list(STAR_CATEGORIES.keys())
                tabs = st.tabs(star_names)
                for idx, cat_name in enumerate(star_names):
                    with tabs[idx]:
                        items = st.session_state["star_watchlists"][cat_name]
                        if not items:
                            st.caption("ยังไม่มีสินทรัพย์ในหมวดนี้")
                        else:
                            st.markdown("""<div class="tv-wl-header">
                                <span></span><span>สัญลักษณ์</span><span style="text-align:right;">ล่าสุด</span>
                                <span style="text-align:right;">เปลี่ยน</span><span style="text-align:right;">เปลี่ยน%</span><span></span>
                            </div>""", unsafe_allow_html=True)

                            for s_item in list(items):
                                q = fetch_item_quote(s_item)
                                s_lbl = CHINA_STOCK_NAMES.get(s_item, COMMODITY_NAMES.get(s_item, s_item.replace("_THB","").replace("-USDT","").replace("USDT","").replace(".BK","").replace(".VN","")))
                                val_col = UP if q["change"] >= 0 else DOWN
                                sign = "+" if q["change"] >= 0 else ""
                                tag_color = STAR_CATEGORIES[cat_name]["color"]

                                c_ico, a, b, c, dcol, f = st.columns([0.6, 1.8, 1.4, 1.2, 1.2, 0.4])
                                with c_ico:
                                    st.markdown(build_asset_icon_html(s_item, tag_color), unsafe_allow_html=True)
                                with a:
                                    if st.button(f"{s_lbl}", key=f"wl_{cat_name}_{s_item}", use_container_width=True):
                                        st.session_state["current_symbol"] = s_item; st.rerun()
                                with b: st.markdown(f"<div style='font-family:monospace; font-size:11px; text-align:right; padding-top:4px; color:#fff;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
                                with c: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{fmt_chg(q['change'])}</div>", unsafe_allow_html=True)
                                with dcol: st.markdown(f"<div style='font-family:monospace; font-size:10px; text-align:right; padding-top:4px; color:{val_col};'>{sign}{q['pct']:.2f}%</div>", unsafe_allow_html=True)
                                with f:
                                    if st.button("✕", key=f"del_{cat_name}_{s_item}", help="ลบออก"):
                                        st.session_state["star_watchlists"][cat_name].remove(s_item); st.rerun()

            # 3. ข้อมูลตลาด 24h & เทคนิค
            with st.expander("📊 ข้อมูลตลาด 24h & เทคนิค", expanded=True):
                tk_data = fetch_unified_ticker(r_market, r_exchange, symbol, df)
                an_data = fetch_market_analytics(r_market, r_exchange, symbol)
                render_tv_quote_card(tk_data, an_data, symbol, label_display)

dashboard()