# ui/sidebar_refactored.py — Streamlined Terminal Sidebar (Slot Replacement & TradingView Standard)
import datetime
import json
import os
import requests
import streamlit as st
import streamlit.components.v1 as components

from color_store import (
    COLOR_KEYS,
    COLOR_TAGS,
    assign_color,
    ensure_color_state,
    get_sym_color_dot,
    get_sym_color_key,
    norm_sym,
)
from data.fetchers import (
    fetch_ohlcv,
    fetch_ticker_24h,
    resolve_market_info,
    standardize_symbol,
)
from data.rice_ohlcv import generate_rice_ohlcv
from ui.rice_seasonality_modal import show_rice_market_modal
from ui.symbol_modal import render_symbol_modal

WATCHLIST_STORE_FILE = "watchlist_store.json"

PREFERRED_COLOR_ORDER = ["red", "orange", "green", "blue", "gray"]
SORTED_COLOR_KEYS = [
    k for k in PREFERRED_COLOR_ORDER if k in COLOR_KEYS
] + [k for k in COLOR_KEYS if k not in PREFERRED_COLOR_ORDER]

# ==============================================================================
# HIERARCHICAL MARKET DEFINITIONS (COMPLETE 10 EXCHANGES & 12 STOCK MARKETS)
# ==============================================================================
MARKET_TYPES = {
    "crypto": "🪙 คริปโต (10 กระดาน)",
    "stock": "📈 ตลาดหุ้น (12 ประเทศ)",
    "forex": "💵 ฟอเร็กซ์ & ดอลลาร์ (Forex / DXY)",
    "commodity": "🛢️ โภคภัณฑ์ / สินค้าเกษตร & ข้าว",
}

SUB_CATEGORIES = {
    "crypto": {
        "binance": "Binance Spot",
        "binance_th": "Binance TH",
        "bitkub": "Bitkub",
        "okx": "OKX",
        "bybit": "Bybit",
        "mexc": "MEXC",
        "kucoin": "KuCoin",
        "gateio": "Gate.io",
        "coinbase": "Coinbase",
        "kraken": "Kraken",
    },
    "stock": {
        "th": "🇹🇭 หุ้นไทย (SET)",
        "us": "🇺🇸 หุ้นสหรัฐฯ (US)",
        "cn": "🇨🇳 หุ้นจีน (China)",
        "vn": "🇻🇳 หุ้นเวียดนาม (VN)",
        "jp": "🇯🇵 JP หุ้นญี่ปุ่น (TSE)",
        "kr": "🇰🇷 KR หุ้นเกาหลีใต้ (KRX)",
        "in": "🇮🇳 IN หุ้นอินเดีย (NSE)",
        "de": "🇩🇪 DE หุ้นเยอรมนี (XETRA)",
        "gb": "🇬🇧 GB หุ้นสหราชอาณาจักร (LSE)",
        "fr": "🇫🇷 FR หุ้นฝรั่งเศส (Euronext)",
        "it": "🇮🇹 IT หุ้นอิตาลี (Borsa Italiana)",
        "es": "🇪🇸 ES หุ้นสเปน (BME Madrid)",
    },
    "forex": {
        "majors": "คู่เงินหลักสากล (Major Pairs)",
        "dxy_cross": "ดัชนีดอลลาร์ & Cross Currency",
        "thb_cross": "คู่เงินบาทไทย (THB Crosses)",
    },
    "commodity": {
        "metals_energy": "ทองคำ / โลหะ / พลังงาน",
        "rice_world": "ตลาดข้าวสากล (CBOT & FOB)",
    },
}

# ฐานข้อมูลหุ้นรายประเทศ โภคภัณฑ์ และฟอเร็กซ์
STATIC_MARKET_DATA = {
    ("stock", "th"): [
        ("DELTA.BK", "DELTA", 108.50, 1.40),
        ("PTT.BK", "PTT", 33.50, 0.00),
        ("CPALL.BK", "CPALL", 65.25, 0.77),
        ("ADVANC.BK", "ADVANC", 264.00, -0.75),
        ("KBANK.BK", "KBANK", 152.00, 1.33),
        ("AOT.BK", "AOT", 62.50, -0.40),
        ("GULF.BK", "GULF", 56.50, 2.26),
        ("BDMS.BK", "BDMS", 28.50, 0.00),
        ("SCB.BK", "SCB", 111.00, 0.91),
        ("TRUE.BK", "TRUE", 11.80, -1.67),
    ],
    ("stock", "us"): [
        ("NVDA", "Nvidia", 125.50, 2.45),
        ("TSLA", "Tesla", 248.20, -1.80),
        ("AAPL", "Apple", 228.10, 0.65),
        ("MSFT", "Microsoft", 428.90, 0.40),
        ("GOOGL", "Alphabet", 165.30, -0.30),
        ("AMZN", "Amazon", 188.50, 1.20),
        ("META", "Meta", 580.40, 1.85),
        ("SPY", "S&P 500 ETF", 570.20, 0.35),
        ("QQQ", "Nasdaq ETF", 485.40, 0.55),
    ],
    ("stock", "cn"): [
        ("BABA", "Alibaba", 102.50, 4.20),
        ("TCEHY", "Tencent", 54.80, 2.80),
        ("JD", "JD.com", 38.60, 3.10),
        ("BIDU", "Baidu", 94.20, -0.65),
        ("NIO", "NIO", 5.85, -2.50),
        ("BYDDF", "BYD Company", 36.40, 1.95),
    ],
    ("stock", "vn"): [
        ("VNM", "Vinamilk", 72.80, 0.69),
        ("VIC", "Vingroup", 41.50, -1.19),
        ("HPG", "Hoa Phat Group", 26.30, 1.54),
        ("VCB", "Vietcombank", 90.20, 0.45),
        ("FPT", "FPT Corp", 135.50, 2.65),
    ],
    ("stock", "jp"): [
        ("7203.T", "Toyota Motor", 2740.0, 1.10),
        ("6758.T", "Sony Group", 2850.0, -0.55),
        ("9984.T", "SoftBank Group", 8940.0, 2.40),
        ("6861.T", "Keyence", 68500.0, 0.85),
    ],
    ("stock", "kr"): [
        ("005930.KS", "Samsung Electronics", 61500.0, -1.44),
        ("000660.KS", "SK Hynix", 184500.0, 3.10),
        ("035420.KS", "NAVER", 168000.0, 0.60),
        ("005380.KS", "Hyundai Motor", 232000.0, -0.85),
    ],
    ("stock", "in"): [
        ("RELIANCE.NS", "Reliance Ind.", 2980.0, 0.85),
        ("TCS.NS", "Tata Consultancy", 4250.0, -0.40),
        ("HDFCBANK.NS", "HDFC Bank", 1680.0, 1.20),
        ("INFY.NS", "Infosys", 1920.0, 0.50),
    ],
    ("stock", "de"): [
        ("SAP.DE", "SAP SE", 204.50, 1.45),
        ("SIE.DE", "Siemens", 178.20, 0.80),
        ("ALV.DE", "Allianz", 288.60, -0.30),
        ("BMW.DE", "BMW Group", 78.40, -1.25),
    ],
    ("stock", "gb"): [
        ("SHEL.L", "Shell plc", 2620.0, 0.65),
        ("AZN.L", "AstraZeneca", 11840.0, -0.45),
        ("HSBA.L", "HSBC Holdings", 670.0, 0.90),
        ("ULVR.L", "Unilever", 4820.0, 0.20),
    ],
    ("stock", "fr"): [
        ("MC.PA", "LVMH Moët Hennessy", 685.0, 1.85),
        ("TTE.PA", "TotalEnergies", 61.20, -0.80),
        ("OR.PA", "L'Oréal", 392.50, 0.40),
        ("SAN.PA", "Sanofi", 102.40, -0.15),
    ],
    ("stock", "it"): [
        ("ENEL.MI", "Enel SpA", 7.15, 0.55),
        ("ENI.MI", "Eni SpA", 14.30, -0.90),
        ("ISP.MI", "Intesa Sanpaolo", 3.85, 1.10),
        ("RACE.MI", "Ferrari N.V.", 432.0, 1.40),
    ],
    ("stock", "es"): [
        ("SAN.MC", "Banco Santander", 4.55, 1.25),
        ("ITX.MC", "Inditex (Zara)", 50.20, 0.80),
        ("IBE.MC", "Iberdrola", 13.60, -0.30),
        ("BBVA.MC", "BBVA", 9.45, 1.50),
    ],
    ("forex", "majors"): [
        ("EURUSD", "EUR / USD", 1.1160, 0.30),
        ("USDJPY", "USD / JPY", 143.20, -0.55),
        ("GBPUSD", "GBP / USD", 1.3380, 0.45),
        ("AUDUSD", "AUD / USD", 0.6890, 0.20),
        ("USDCAD", "USD / CAD", 1.3520, -0.15),
        ("USDCHF", "USD / CHF", 0.8480, -0.22),
    ],
    ("forex", "dxy_cross"): [
        ("DXY", "ดัชนีดอลลาร์สหรัฐ", 100.85, -0.25),
        ("EURGBP", "EUR / GBP", 0.8340, -0.12),
        ("EURJPY", "EUR / JPY", 159.80, -0.25),
        ("GBPJPY", "GBP / JPY", 191.60, -0.10),
    ],
    ("forex", "thb_cross"): [
        ("USDTHB", "USD / THB", 32.45, -0.35),
        ("EURTHB", "EUR / THB", 36.20, -0.05),
        ("JPYTHB", "JPY / THB (100)", 22.65, 0.20),
        ("SGDTHB", "SGD / THB", 25.10, -0.18),
    ],
    ("commodity", "metals_energy"): [
        ("XAUUSD", "ทองคำ (Gold)", 2658.40, 0.85),
        ("XAGUSD", "แร่เงิน (Silver)", 31.85, 1.42),
        ("BRENT", "น้ำมันดิบ Brent", 74.20, -1.15),
        ("WTI", "น้ำมันดิบ WTI", 70.80, -0.95),
        ("COPPER", "ทองแดง (Copper)", 4.35, 0.50),
        ("NATGAS", "ก๊าซธรรมชาติ", 2.85, -2.10),
    ],
    ("commodity", "rice_world"): [
        ("ZR=F", "ข้าวฟิวเจอร์ส CBOT", 15.20, 0.66),
        ("RICE:TH_JASMINE", "ข้าวหอมมะลิไทย (ส่งออก)", 890.00, 0.25),
        ("RICE:TH_WHITE5", "ข้าวขาว 5% ไทย (หน้าโรงสี)", 565.00, -0.50),
        ("FOB:TH_5PCT", "FOB ข้าวขาว 5% กรุงเทพฯ", 575.00, -0.35),
        ("RICE:VN_5PCT", "ข้าวขาวเวียดนาม 5% FOB", 535.00, -0.80),
        ("RICE:IN_5PCT", "ข้าวขาวอินเดีย 5% FOB", 490.00, 0.00),
    ],
}


# ==============================================================================
# LOCALSTORAGE WATCHLIST ENGINE (BROWSER PERSISTENCE)
# ==============================================================================
def _sync_localstorage_to_watchlist():
  url_intl = st.query_params.get("intl_wl", "")
  if url_intl:
    saved_list = [s.strip().upper() for s in url_intl.split(",") if s.strip()]
    if "custom_watchlist" in st.session_state:
      existing = set(
          norm_sym(
              r[0] if isinstance(r, (list, tuple)) else r
          ).upper()
          for r in st.session_state["custom_watchlist"]
      )
      for sym in saved_list:
        sym_norm = norm_sym(sym).upper()
        if sym_norm not in existing:
          st.session_state["custom_watchlist"].append((sym, "-", "-", True))
          existing.add(sym_norm)


def _sync_watchlist_to_url():
  if "custom_watchlist" in st.session_state:
    syms = [
        norm_sym(r[0] if isinstance(r, (list, tuple)) else r).upper()
        for r in st.session_state["custom_watchlist"]
    ]
    st.query_params["intl_wl"] = ",".join(syms)


def inject_localstorage_sync_bridge():
  components.html(
      """
        <script>
        (function() {
            try {
                const win = window.parent;
                const STORAGE_KEY = 'bullvault_intl_watchlist';
                
                const saved = localStorage.getItem(STORAGE_KEY) || '';
                const urlParams = new URLSearchParams(win.location.search);
                const currentUrlVal = urlParams.get('intl_wl') || '';
                
                if (saved && !currentUrlVal) {
                    urlParams.set('intl_wl', saved);
                    win.location.search = urlParams.toString();
                } else if (currentUrlVal && currentUrlVal !== saved) {
                    localStorage.setItem(STORAGE_KEY, currentUrlVal);
                }
            } catch(e) {
                console.error("LocalStorage Bridge Error:", e);
            }
        })();
        </script>
        """,
      height=0,
      width=0,
  )


def _format_vol(v: float) -> str:
  if v >= 1e9:
    return f"{v / 1e9:.2f} B"
  elif v >= 1e6:
    return f"{v / 1e6:.2f} M"
  elif v >= 1e3:
    return f"{v / 1e3:.2f} K"
  elif v > 0:
    return f"{v:,.0f}"
  return "-"


def _format_price(p: float) -> str:
  if p >= 100:
    return f"{p:,.2f}"
  elif p >= 1:
    return f"{p:,.4f}"
  elif p > 0:
    s = f"{p:.6f}".rstrip("0").rstrip(".")
    return s if s else f"{p:.6f}"
  return "-"


@st.cache_data(ttl=5, show_spinner=False)
def _get_live_ticker(sym: str):
  try:
    t = fetch_ticker_24h(sym)
    if t and (
        t.get("last_price", 0) > 0
        or t.get("price_change_pct", 0) != 0
        or t.get("volume_24h", 0) > 0
    ):
      p = float(t["last_price"])
      c = float(t.get("price_change_pct", 0.0))
      v = float(t.get("volume_24h", 0.0))
      p_str = _format_price(p)
      c_str = (
          f"{c:+.2f}%"
          if abs(c) >= 0.01
          else (f"{c:+.4f}%" if c != 0 else "+0.00%")
      )
      v_str = _format_vol(v)
      return p_str, c_str, v_str, (c >= 0), c, v
  except Exception:
    pass
  return None


# ==============================================================================
# SMART MARKET FETCHER (10 CRYPTO EXCHANGES + 12 STOCK MARKETS + MACRO)
# ==============================================================================
@st.cache_data(ttl=15, show_spinner=False)
def fetch_ranked_market_data(m_type: str, sub_id: str):
  items = []

  # 1. กลุ่มคริปโต (10 กระดาน)
  if m_type == "crypto":
    if sub_id in ["binance", "binance_th"]:
      try:
        res = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr", timeout=3.5
        ).json()
        for t in res:
          sym = t.get("symbol", "")
          if sym.endswith("USDT"):
            items.append({
                "symbol": sym,
                "display_name": sym.replace("USDT", ""),
                "last_price": float(t.get("lastPrice", 0)),
                "change_pct": float(t.get("priceChangePercent", 0)),
                "volume_quote": float(t.get("quoteVolume", 0)),
            })
      except Exception:
        pass

    elif sub_id == "bitkub":
      try:
        res_bk = requests.get(
            "https://api.bitkub.com/api/market/ticker", timeout=3.5
        ).json()
        for k, v in res_bk.items():
          if k.startswith("THB_"):
            sym_clean = k.replace("THB_", "")
            items.append({
                "symbol": f"{sym_clean}THB",
                "display_name": sym_clean,
                "last_price": float(v.get("last", 0)),
                "change_pct": float(v.get("percentChange", 0)),
                "volume_quote": float(v.get("baseVolume", 0))
                * float(v.get("last", 0)),
            })
      except Exception:
        pass

    elif sub_id == "bybit":
      try:
        res_by = requests.get(
            "https://api.bybit.com/v5/market/tickers?category=spot", timeout=3.5
        ).json()
        for t in res_by.get("result", {}).get("list", []):
          sym = t.get("symbol", "")
          if sym.endswith("USDT"):
            items.append({
                "symbol": sym,
                "display_name": sym.replace("USDT", ""),
                "last_price": float(t.get("lastPrice", 0)),
                "change_pct": float(t.get("price24hPcnt", 0)) * 100,
                "volume_quote": float(t.get("turnover24h", 0)),
            })
      except Exception:
        pass

    elif sub_id == "okx":
      try:
        res_ok = requests.get(
            "https://www.okx.com/api/v5/market/tickers?instType=SPOT",
            timeout=3.5,
        ).json()
        for t in res_ok.get("data", []):
          inst = t.get("instId", "")
          if inst.endswith("-USDT"):
            clean_s = inst.replace("-", "")
            items.append({
                "symbol": clean_s,
                "display_name": inst.replace("-USDT", ""),
                "last_price": float(t.get("last", 0)),
                "change_pct": (
                    (float(t.get("last", 0)) - float(t.get("open24h", 1)))
                    / float(t.get("open24h", 1))
                )
                * 100,
                "volume_quote": float(t.get("volCcy24h", 0)),
            })
      except Exception:
        pass

    elif sub_id == "coinbase":
      try:
        res_cb = requests.get(
            "https://api.exchange.coinbase.com/products", timeout=3.5
        ).json()
        usd_pairs = [
            p["id"]
            for p in res_cb
            if p.get("quote_currency") == "USD" and p.get("status") == "online"
        ][:40]
        for pid in usd_pairs:
          sym_clean = pid.replace("-USD", "USDT")
          t_live = fetch_ticker_24h(sym_clean)
          if t_live and t_live.get("last_price", 0) > 0:
            items.append({
                "symbol": sym_clean,
                "display_name": pid.replace("-USD", ""),
                "last_price": float(t_live["last_price"]),
                "change_pct": float(t_live.get("price_change_pct", 0.0)),
                "volume_quote": float(t_live.get("volume_24h", 50000000.0)),
            })
      except Exception:
        pass

    elif sub_id == "kraken":
      try:
        res_kr = requests.get(
            "https://api.kraken.com/0/public/Ticker", timeout=3.5
        ).json()
        for k, v in list(res_kr.get("result", {}).items())[:50]:
          if k.endswith("USD") or k.endswith("USDT"):
            disp = k.replace("X", "").replace("Z", "").replace("USD", "")
            sym_clean = f"{disp}USDT"
            p = float(v.get("c", [0])[0])
            open_p = float(v.get("o", 1))
            chg = ((p - open_p) / open_p) * 100 if open_p > 0 else 0.0
            vol = float(v.get("v", [0])[1]) * p
            items.append({
                "symbol": sym_clean,
                "display_name": disp,
                "last_price": p,
                "change_pct": chg,
                "volume_quote": vol,
            })
      except Exception:
        pass

    else:
      # สำหรับ MEXC, KuCoin, Gate.io
      try:
        res = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr", timeout=3.5
        ).json()
        for t in res[:60]:
          sym = t.get("symbol", "")
          if sym.endswith("USDT"):
            items.append({
                "symbol": sym,
                "display_name": sym.replace("USDT", ""),
                "last_price": float(t.get("lastPrice", 0)),
                "change_pct": float(t.get("priceChangePercent", 0)),
                "volume_quote": float(t.get("quoteVolume", 0)),
            })
      except Exception:
        pass

  # 2. กลุ่มหุ้นรายประเทศ (12 ประเทศ), ฟอเร็กซ์, โภคภัณฑ์ & ข้าว
  else:
    lookup_key = (m_type, sub_id)
    raw_list = STATIC_MARKET_DATA.get(lookup_key, [])
    for sym_code, disp_name, def_p, def_chg in raw_list:
      p = def_p
      chg = def_chg
      vol = 50000000.0

      try:
        t_live = fetch_ticker_24h(sym_code)
        if t_live and t_live.get("last_price", 0) > 0:
          p = float(t_live["last_price"])
          chg = float(t_live.get("price_change_pct", def_chg))
          vol = float(t_live.get("volume_24h", vol))
      except Exception:
        pass

      items.append({
          "symbol": sym_code,
          "display_name": disp_name,
          "last_price": p,
          "change_pct": chg,
          "volume_quote": vol,
      })

  return items


def load_saved_data():
  if os.path.exists(WATCHLIST_STORE_FILE):
    try:
      with open(WATCHLIST_STORE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("watchlist", []), data.get("colors", {})
    except Exception:
      pass
  default_watchlist = [
      ("BTCUSDT", "-", "-", True),
      ("ETHUSDT", "-", "-", True),
      ("SOLUSDT", "-", "-", True),
      ("BNBUSDT", "-", "-", True),
      ("ADAUSDT", "-", "-", True),
  ]
  return default_watchlist, {}


def save_watchlist_data():
  try:
    raw_rows = st.session_state.get("custom_watchlist", [])
    clean_list = [_normalize_row(r) for r in raw_rows]
    color_map = {}
    for r in clean_list:
      s = r[0]
      ckey = get_sym_color_key(s)
      if ckey:
        color_map[s] = ckey
    with open(WATCHLIST_STORE_FILE, "w", encoding="utf-8") as f:
      json.dump(
          {"watchlist": clean_list, "colors": color_map},
          f,
          ensure_ascii=False,
          indent=2,
      )
  except Exception:
    pass


def add_to_watchlist(sym_code: str):
  if not sym_code:
    return
  clean = standardize_symbol(sym_code)
  raw = norm_sym(sym_code).upper()
  existing = [
      norm_sym(
          r[0]
          if isinstance(r, (list, tuple))
          else (r.get("symbol") if isinstance(r, dict) else r)
      ).upper()
      for r in st.session_state.get("custom_watchlist", [])
  ]
  existing_clean = [standardize_symbol(s) for s in existing]
  if raw not in existing and clean not in existing_clean:
    if "custom_watchlist" not in st.session_state:
      st.session_state["custom_watchlist"] = []
    st.session_state["custom_watchlist"].insert(0, (raw, "-", "-", True))
    save_watchlist_data()
    _sync_watchlist_to_url()


def remove_from_watchlist(target_sym: str):
  t_clean = standardize_symbol(target_sym)
  target_norm = norm_sym(target_sym).upper()

  st.session_state["custom_watchlist"] = [
      item
      for item in st.session_state.get("custom_watchlist", [])
      if norm_sym(
          item[0] if isinstance(item, (list, tuple)) else item
      ).upper()
      not in [target_norm, t_clean]
      and standardize_symbol(
          item[0] if isinstance(item, (list, tuple)) else item
      )
      != t_clean
  ]
  assign_color(target_sym, None)
  assign_color(t_clean, None)
  save_watchlist_data()
  _sync_watchlist_to_url()

  cur_sel = st.session_state.get("current_symbol", "BTCUSDT")
  if (
      standardize_symbol(cur_sel) == t_clean
      or norm_sym(cur_sel).upper() == target_norm
  ):
    rem = st.session_state.get("custom_watchlist", [])
    fallback = rem[0][0] if rem else "BTCUSDT"
    set_active_symbol(fallback)


@st.dialog("⚙️ การตั้งค่าระบบและชาร์ต (Unified Settings)")
def show_chart_settings_dialog():
  tab_chart, tab_ui = st.tabs(["🎨 กราฟ & ธีม", "🖥️ พื้นที่ทำงาน"])

  with tab_chart:
    st.caption("🎨 โทนสีแท่งเทียนและพื้นหลัง")
    c1, c2 = st.columns(2)
    with c1:
      st.session_state["candle_up_color"] = st.color_picker(
          "แท่งขึ้น (Bullish)",
          value=st.session_state.get("candle_up_color", "#089981"),
      )
    with c2:
      st.session_state["candle_down_color"] = st.color_picker(
          "แท่งลง (Bearish)",
          value=st.session_state.get("candle_down_color", "#F23645"),
      )
    c3, c4 = st.columns(2)
    with c3:
      st.session_state["chart_bg_color"] = st.color_picker(
          "พื้นหลังกราฟ (Background)",
          value=st.session_state.get("chart_bg_color", "#131722"),
      )
    with c4:
      st.session_state["chart_grid_color"] = st.color_picker(
          "เส้นกริด (Grid)",
          value=st.session_state.get("chart_grid_color", "#1e222d"),
      )

  with tab_ui:
    st.caption("🖥 ควบคุมการแสดงผลแถบ 'กราฟเปรียบเทียบ'")
    st.session_state["show_draw_toolbar"] = st.toggle(
        "✏️ แถบวาดรูป (Draw Toolbar)",
        value=st.session_state.get("show_draw_toolbar", True),
    )
    st.session_state["show_top_bar"] = st.toggle(
        "💻 แถบควบคุมบน (Top Bar)",
        value=st.session_state.get("show_top_bar", True),
    )

  st.divider()
  b1, b2 = st.columns(2)
  with b1:
    if st.button("🔄 รีเซ็ตเป็นค่าเริ่มต้น", use_container_width=True):
      st.session_state["candle_up_color"] = "#089981"
      st.session_state["candle_down_color"] = "#F23645"
      st.session_state["chart_bg_color"] = "#131722"
      st.session_state["chart_grid_color"] = "#1e222d"
      st.session_state["show_draw_toolbar"] = True
      st.session_state["show_top_bar"] = True
      st.rerun()
  with b2:
    if st.button(
        "💾 บันทึกและปรับใช้", type="primary", use_container_width=True
    ):
      st.rerun()


def set_active_symbol(sym_code: str):
  clean_sym = standardize_symbol(sym_code)
  st.session_state["current_symbol"] = clean_sym
  st.session_state["selected_symbol"] = clean_sym

  if "chart_tabs" in st.session_state and st.session_state["chart_tabs"]:
    active_id = st.session_state.get("active_tab_id")
    for t in st.session_state["chart_tabs"]:
      if t.get("id") == active_id:
        t["symbol"] = clean_sym
        break

  for k in ("active_key", "df_data", "last_fetch_time"):
    st.session_state.pop(k, None)


def _color_menu(sym: str, prefix: str = "wl") -> None:
  s = norm_sym(sym)
  current = get_sym_color_key(s)
  st.caption(f"กลุ่มสีของ {s}")
  for ckey in SORTED_COLOR_KEYS:
    cinfo = COLOR_TAGS[ckey]
    mark = " ✓" if ckey == current else ""
    if st.button(
        f"{cinfo['dot']} {cinfo['label']}{mark}",
        key=f"{prefix}_clr_{s}_{ckey}",
        use_container_width=True,
    ):
      assign_color(s, None if ckey == current else ckey)
      save_watchlist_data()
      st.rerun()

  st.divider()
  if st.button(
      "✖ ปลดกลุ่มสี",
      key=f"{prefix}_clr_{s}_none",
      use_container_width=True,
      disabled=(current is None),
  ):
    assign_color(s, None)
    save_watchlist_data()
    st.rerun()


def _normalize_row(row):
  if isinstance(row, dict):
    return (
        norm_sym(row.get("symbol") or row.get("sym")),
        row.get("price", "-"),
        row.get("change", "-"),
        bool(row.get("is_up", True)),
    )
  if isinstance(row, (list, tuple)):
    vals = list(row) + ["-", "-", True]
    return (norm_sym(vals[0]), vals[1], vals[2], bool(vals[3]))
  return (norm_sym(row), "-", "-", True)


def render_sidebar():
  st.markdown(
      '<div id="custom-left-menu-anchor" style="display:none;"></div>',
      unsafe_allow_html=True,
  )
  ensure_color_state()
  inject_localstorage_sync_bridge()

  if "custom_watchlist" not in st.session_state:
    saved_wl, saved_colors = load_saved_data()
    st.session_state["custom_watchlist"] = saved_wl
    for s, ckey in saved_colors.items():
      assign_color(s, ckey)

  _sync_localstorage_to_watchlist()

  seen_syms = set()
  deduped_wl = []
  for r in st.session_state.get("custom_watchlist", []):
    sym_name = (
        r[0]
        if isinstance(r, (list, tuple))
        else (r.get("symbol") if isinstance(r, dict) else r)
    )
    s_norm = norm_sym(sym_name).upper()
    if s_norm not in seen_syms:
      seen_syms.add(s_norm)
      deduped_wl.append(r)
  st.session_state["custom_watchlist"] = deduped_wl

  if "sidebar_active_tab" not in st.session_state:
    st.session_state["sidebar_active_tab"] = "market"
  if "color_filter" not in st.session_state:
    st.session_state["color_filter"] = None
  if "wl_sort_mode" not in st.session_state:
    st.session_state["wl_sort_mode"] = "none"

  st.markdown(
      """
    <style>
    .tv-sort-wrap div[data-testid="stBaseButton-tertiary"] button,
    .tv-sort-wrap button {
        background: transparent !important;
        border: none !important;
        color: #8b949e !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        padding: 0 2px !important;
        min-height: 22px !important;
        height: 22px !important;
        box-shadow: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    .tv-sort-wrap button:hover {
        color: #ff7d1e !important;
    }
    .tv-sort-right div[data-testid="stBaseButton-tertiary"] button,
    .tv-sort-right button {
        background: transparent !important;
        border: none !important;
        color: #8b949e !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        padding: 0 2px !important;
        min-height: 22px !important;
        height: 22px !important;
        box-shadow: none !important;
        text-align: right !important;
        justify-content: flex-end !important;
    }
    .tv-sort-right button:hover {
        color: #ff7d1e !important;
    }

    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) {
        gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) {
        margin-bottom: -4px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) div[data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) button {
        min-height: 24px !important;
        height: 24px !important;
        padding: 0px 4px !important;
        font-size: 11.5px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    div[data-testid="stVerticalBlock"]:has(.tv-neon-wrap) div[data-testid="stPopover"] button {
        min-height: 22px !important;
        height: 22px !important;
        width: 22px !important;
        padding: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) div[data-testid="column"]:first-child button[kind="primary"],
    div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) div[data-testid="column"]:first-child button[data-testid="baseButton-primary"] {
        border: 1.5px solid rgba(255, 125, 30, 0.55) !important;
        background: rgba(255, 125, 30, 0.16) !important;
        box-shadow: 0 0 10px rgba(255, 125, 30, 0.25) !important;
        backdrop-filter: blur(8px) !important;
        color: #ff9d42 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) div[data-testid="column"]:first-child button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) div[data-testid="column"]:first-child button[data-testid="baseButton-secondary"] {
        border: 1px solid #1e222d !important;
        background: #11141c !important;
        color: #d1d4dc !important;
        box-shadow: none !important;
        font-weight: 500 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.tv-neon-wrap) div[data-testid="column"]:first-child button:hover {
        border-color: #ff7d1e !important;
        color: #ff7d1e !important;
    }

    .tv-neon-wrap div[data-testid="stPopover"] button {
        background: rgba(255, 107, 0, 0.14) !important;
        border: 1px solid rgba(255, 125, 30, 0.4) !important;
        color: #FF7D1E !important;
        padding: 0 !important;
        border-radius: 50% !important;
        font-size: 9px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .tv-neon-wrap div[data-testid="stPopover"] button:hover {
        background: #FF7D1E !important;
        color: #131722 !important;
        box-shadow: 0 0 8px #FF7D1E !important;
    }

    .tv-del-btn button {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #787b86 !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        padding: 0 !important;
        min-height: 22px !important;
        height: 22px !important;
        width: 22px !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        transition: all 0.15s ease-in-out !important;
    }
    .tv-del-btn button:hover {
        color: #ffffff !important;
        background: #f23645 !important;
        border-color: #f23645 !important;
    }

    .tv-val-up {
        color: #00e676 !important;
        font-size: 13.5px !important;
        font-weight: 800 !important;
        font-family: 'JetBrains Mono', monospace !important;
        white-space: nowrap !important;
    }
    .tv-val-down {
        color: #ff3366 !important;
        font-size: 13.5px !important;
        font-weight: 800 !important;
        font-family: 'JetBrains Mono', monospace !important;
        white-space: nowrap !important;
    }
    .tv-vol-text {
        color: #ff8c00 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
        text-align: right !important;
        white-space: nowrap !important;
    }

    /* ป้องกันข้อความบนปุ่มตัดคำเป็นจุดไข่ปลา (...) */
    div[data-testid="stHorizontalBlock"]:has(.main-tabs-marker) button,
    div[data-testid="stHorizontalBlock"]:has(.rk-sort-marker) button {
        padding: 0 1px !important;
        font-size: 11px !important;
        white-space: nowrap !important;
        letter-spacing: -0.4px !important;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )

  # --- แถบปุ่มแท็บ 3 แท็บหลัก ---
  st.markdown(
      '<div class="main-tabs-marker" style="display:none;"></div>',
      unsafe_allow_html=True,
  )
  t_c1, t_c2, t_c3 = st.columns([1.0, 1.25, 1.05], gap="small")
  with t_c1:
    if st.button(
        "ตลาด",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["sidebar_active_tab"] == "market"
            else "secondary"
        ),
    ):
      st.session_state["sidebar_active_tab"] = "market"
      st.rerun()
  with t_c2:
    if st.button(
        "กราฟเปรียบ",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["sidebar_active_tab"] == "tools"
            else "secondary"
        ),
    ):
      st.session_state["sidebar_active_tab"] = "tools"
      st.rerun()
  with t_c3:
    if st.button(
        "อันดับ 24h",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["sidebar_active_tab"] == "ranking"
            else "secondary"
        ),
    ):
      st.session_state["sidebar_active_tab"] = "ranking"
      st.rerun()

  # ──────────────────────────────────────────────────────────
  # TAB 1: ตลาด (Watchlist สไตล์ TradingView)
  # ──────────────────────────────────────────────────────────
  if st.session_state["sidebar_active_tab"] == "market":
    active_tab_sym = "BTCUSDT"
    if "chart_tabs" in st.session_state and st.session_state["chart_tabs"]:
      active_id = st.session_state.get("active_tab_id")
      for t in st.session_state["chart_tabs"]:
        if t.get("id") == active_id:
          active_tab_sym = t.get("symbol", "BTCUSDT")
          break
    else:
      active_tab_sym = st.session_state.get("current_symbol", "BTCUSDT")

    selected_sym = active_tab_sym
    clean_selected = standardize_symbol(selected_sym)

    raw_rows = [
        _normalize_row(r)
        for r in st.session_state.get("custom_watchlist", [])
    ]
    wl_syms_clean = [standardize_symbol(r[0]) for r in raw_rows]

    if clean_selected not in wl_syms_clean:
      st.session_state["custom_watchlist"].append(
          (clean_selected, "-", "-", True)
      )
      save_watchlist_data()
      _sync_watchlist_to_url()
      raw_rows = [
          _normalize_row(r)
          for r in st.session_state.get("custom_watchlist", [])
      ]
    st.session_state["last_active_wl_sym"] = clean_selected

    if st.button(
        "🔍 ค้นหาเหรียญ / สัญลักษณ์สินทรัพย์...",
        key="btn_open_symbol_modal",
        use_container_width=True,
        type="secondary",
    ):
      render_symbol_modal()
    f_cols = st.columns([1.1, 1, 1, 1, 1, 1], gap="small")
    active = st.session_state.get("color_filter")

    with f_cols[0]:
      if st.button(
          "ALL" if active else "⭐",
          key="cf_all",
          use_container_width=True,
          type="primary" if active is None else "tertiary",
      ):
        st.session_state["color_filter"] = None
        st.rerun()

    for i, ckey in enumerate(SORTED_COLOR_KEYS):
      with f_cols[i + 1]:
        btn_type = "primary" if active == ckey else "tertiary"
        dot_char = COLOR_TAGS[ckey]["dot"]
        if st.button(
            dot_char,
            key=f"cf_{ckey}",
            use_container_width=True,
            type=btn_type,
        ):
          st.session_state["color_filter"] = (
              None if active == ckey else ckey
          )
          st.rerun()

    h_title, h_add = st.columns(
        [1.8, 0.4], gap="small", vertical_alignment="center"
    )
    with h_title:
      st.markdown(
          "<div style='font-size:12px; font-weight:700; color:#8b949e;'>📋"
          " รายการสินทรัพย์เฝ้าดู</div>",
          unsafe_allow_html=True,
      )
    with h_add:
      with st.popover("➕", help="เพิ่มเหรียญ/หุ้น เข้า Watchlist"):
        st.markdown(
            "<b style='font-size:12px; color:#00e676;'>➕ เพิ่มเหรียญเข้า"
            " Watchlist</b>",
            unsafe_allow_html=True,
        )
        new_sym_in = st.text_input(
            "พิมพ์ชื่อเหรียญหรือหุ้น:",
            placeholder="เช่น BTC, ETH, DELTABK, PERPTHB",
            key="quick_add_sym_input",
        )
        c_add_btn, c_browse = st.columns([0.6, 0.4])
        with c_add_btn:
          if st.button(
              "เพิ่ม",
              key="btn_confirm_quick_add",
              type="primary",
              use_container_width=True,
          ):
            if new_sym_in.strip():
              add_to_watchlist(new_sym_in.strip())
              st.toast(f"เพิ่ม '{new_sym_in.strip().upper()}' แล้ว!")
              st.rerun()
        with c_browse:
          if st.button(
              "ค้นหา...", key="btn_browse_symbols", use_container_width=True
          ):
            render_symbol_modal()

    h_c1, h_c2, h_c3, h_c4 = st.columns(
        [1.44, 0.90, 0.86, 0.28], gap="small", vertical_alignment="center"
    )
    sort_mode = st.session_state.get("wl_sort_mode", "none")

    with h_c1:
      lbl_sym = "สัญลักษณ์"
      if sort_mode == "sym_asc":
        lbl_sym = "สัญลักษณ์ ▲"
      elif sort_mode == "sym_desc":
        lbl_sym = "สัญลักษณ์ ▼"
      st.markdown('<div class="tv-sort-wrap">', unsafe_allow_html=True)
      if st.button(
          lbl_sym, key="btn_sort_sym", type="tertiary", use_container_width=True
      ):
        st.session_state["wl_sort_mode"] = (
            "sym_desc"
            if sort_mode == "sym_asc"
            else ("none" if sort_mode == "sym_desc" else "sym_asc")
        )
        st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

    with h_c2:
      lbl_pct = "เปลี่ยน"
      if sort_mode == "pct_desc":
        lbl_pct = "เปลี่ยน ▼"
      elif sort_mode == "pct_asc":
        lbl_pct = "เปลี่ยน ▲"
      st.markdown('<div class="tv-sort-wrap">', unsafe_allow_html=True)
      if st.button(
          lbl_pct, key="btn_sort_pct", type="tertiary", use_container_width=True
      ):
        st.session_state["wl_sort_mode"] = (
            "pct_asc"
            if sort_mode == "pct_desc"
            else ("none" if sort_mode == "pct_asc" else "pct_desc")
        )
        st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

    with h_c3:
      lbl_vol = "ปริมาณ"
      if sort_mode == "vol_desc":
        lbl_vol = "ปริมาณ ▼"
      st.markdown('<div class="tv-sort-right">', unsafe_allow_html=True)
      if st.button(
          lbl_vol, key="btn_sort_vol", type="tertiary", use_container_width=True
      ):
        st.session_state["wl_sort_mode"] = (
            "none" if sort_mode == "vol_desc" else "vol_desc"
        )
        st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

    with h_c4:
      st.markdown(
          "<span style='font-size:10px; color:#555e6d;'>ลบ</span>",
          unsafe_allow_html=True,
      )

    rows = (
        [r for r in raw_rows if get_sym_color_key(r[0]) == active]
        if active
        else raw_rows
    )

    if not rows:
      st.caption("ไม่มีเหรียญในกลุ่มนี้ กดปุ่ม ➕ ด้านบนเพื่อเพิ่มเหรียญ")

    display_rows = []
    for sym, p_val, c_val, is_up in rows:
      dot = get_sym_color_dot(sym)
      c_num = 0.0
      v_num = 0.0
      v_val = "-"
      p_val = "-"
      c_val = "+0.00%"
      is_up = True

      s_std = standardize_symbol(sym)
      row_active = (s_std == clean_selected) or (
          norm_sym(sym).upper() == norm_sym(selected_sym).upper()
      )

      ticker_data = _get_live_ticker(sym)
      if ticker_data:
        p_val, c_val, v_val, is_up, c_num, v_num = ticker_data

      display_rows.append({
          "sym": sym,
          "dot": dot,
          "p_val": p_val,
          "c_val": c_val,
          "v_val": v_val,
          "is_up": is_up,
          "c_num": c_num,
          "v_num": v_num,
          "is_active": row_active,
      })

    if sort_mode == "sym_asc":
      display_rows.sort(key=lambda x: x["sym"])
    elif sort_mode == "sym_desc":
      display_rows.sort(key=lambda x: x["sym"], reverse=True)
    elif sort_mode == "pct_desc":
      display_rows.sort(key=lambda x: x["c_num"], reverse=True)
    elif sort_mode == "pct_asc":
      display_rows.sort(key=lambda x: x["c_num"])
    elif sort_mode == "vol_desc":
      display_rows.sort(key=lambda x: x["v_num"], reverse=True)

    with st.container(height=480):
      for idx, item in enumerate(display_rows):
        sym = item["sym"]
        dot = item["dot"]
        c_val = item["c_val"]
        v_val = item["v_val"]
        is_up = item["is_up"]
        row_active = item["is_active"]

        c_sym, c_tag, c_pct, c_vol, c_del = st.columns(
            [1.18, 0.26, 0.90, 0.86, 0.28],
            gap="small",
            vertical_alignment="center",
        )
        with c_sym:
          active_badge = "🔶 " if row_active else ""
          btn_title = f"{active_badge}{dot} {sym}".strip()
          btn_type = "primary" if row_active else "secondary"
          if st.button(
              btn_title,
              key=f"wl_btn_{sym}_{idx}",
              type=btn_type,
              use_container_width=True,
          ):
            set_active_symbol(sym)
            st.session_state["last_active_wl_sym"] = standardize_symbol(sym)
            st.rerun()

        with c_tag:
          st.markdown('<div class="tv-neon-wrap">', unsafe_allow_html=True)
          with st.popover(
              "●", use_container_width=True, help=f"จัดกลุ่มสี {sym}"
          ):
            _color_menu(sym, prefix=f"wl_{idx}")
          st.markdown("</div>", unsafe_allow_html=True)

        with c_pct:
          cls = "tv-val-up" if is_up else "tv-val-down"
          st.markdown(
              '<div style="text-align:right;"><span'
              f' class="{cls}">{c_val}</span></div>',
              unsafe_allow_html=True,
          )

        with c_vol:
          st.markdown(
              '<div style="text-align:right;"><span'
              f' class="tv-vol-text">{v_val}</span></div>',
              unsafe_allow_html=True,
          )

        with c_del:
          st.markdown('<div class="tv-del-btn">', unsafe_allow_html=True)
          if st.button(
              "✕",
              key=f"wl_del_{sym}_{idx}",
              help=f"ลบ {sym} ออกจาก Watchlist",
          ):
            remove_from_watchlist(sym)
            st.rerun()
          st.markdown("</div>", unsafe_allow_html=True)

  # ──────────────────────────────────────────────────────────
  # TAB 2: กราฟเปรียบเทียบ
  # ──────────────────────────────────────────────────────────
  elif st.session_state["sidebar_active_tab"] == "tools":
    st.markdown(
        "<div style='font-size:11px; color:#00FFA3;"
        " margin-bottom:8px;'>⚡ หมวดหมู่เปรียบเทียบ</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
      if st.button(
          "🌾 ตลาดข้าว",
          key="btn_rice_modal",
          use_container_width=True,
          type="secondary",
      ):
        from ui import rice_seasonality_modal

        rice_seasonality_modal.show_rice_market_modal()
    with c2:
      if st.button(
          "🪙 คริปโต",
          key="btn_crypto_modal",
          use_container_width=True,
          type="secondary",
      ):
        from ui import macro_comparison_modal

        macro_comparison_modal.show_crypto_modal()

    c3, c4 = st.columns(2)
    with c3:
      if st.button(
          "📈 หุ้น (GICS)",
          key="btn_stocks_modal",
          use_container_width=True,
          type="secondary",
      ):
        from ui import macro_comparison_modal

        macro_comparison_modal.show_stocks_gics_modal()
    with c4:
      if st.button(
          "⛏️ แร่ & เหมือง",
          key="btn_metals_modal",
          use_container_width=True,
          type="secondary",
      ):
        from ui import macro_comparison_modal

        macro_comparison_modal.show_metals_mining_modal()

    c5, c6 = st.columns(2)
    with c5:
      if st.button(
          "💵 สกุลเงิน FX",
          key="btn_forex_modal",
          use_container_width=True,
          type="secondary",
      ):
        from ui import macro_comparison_modal

        macro_comparison_modal.show_forex_modal()
    with c6:
      if st.button(
          "🌐 เทียบข้ามกลุ่ม",
          key="btn_macro_modal",
          use_container_width=True,
          type="secondary",
      ):
        from ui import macro_comparison_modal

        macro_comparison_modal.show_macro_comparison_modal()

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    if st.button(
        "🧭 บทวิเคราะห์เงินทุนไหล (Capital Flow)",
        key="btn_flow_modal",
        use_container_width=True,
        type="primary",
    ):
      from ui import macro_comparison_modal

      macro_comparison_modal.show_flow_analysis_modal()

  # ──────────────────────────────────────────────────────────
  # TAB 3: อันดับ 24h (2-Tier Cascading Filter Scanner)
  # ──────────────────────────────────────────────────────────
  elif st.session_state["sidebar_active_tab"] == "ranking":
    if "rank_sort_mode" not in st.session_state:
      st.session_state["rank_sort_mode"] = "gain"
    if "rank_primary_type" not in st.session_state:
      st.session_state["rank_primary_type"] = "crypto"
    if "rank_sub_cat" not in st.session_state:
      st.session_state["rank_sub_cat"] = "binance"

    # 1. แถบปุ่มโหมดจัดอันดับ 3 หัวข้อหลัก
    st.markdown(
        '<div class="rk-sort-marker" style="display:none;"></div>',
        unsafe_allow_html=True,
    )
    col_s1, col_s2, col_s3 = st.columns(3, gap="small")
    with col_s1:
      if st.button(
          "ปริมาณ 24h",
          key="rk_sort_vol",
          type=(
              "primary"
              if st.session_state["rank_sort_mode"] == "vol"
              else "secondary"
          ),
          use_container_width=True,
      ):
        st.session_state["rank_sort_mode"] = "vol"
        st.rerun()
    with col_s2:
      if st.button(
          "% เพิ่มสูงสุด",
          key="rk_sort_gain",
          type=(
              "primary"
              if st.session_state["rank_sort_mode"] == "gain"
              else "secondary"
          ),
          use_container_width=True,
      ):
        st.session_state["rank_sort_mode"] = "gain"
        st.rerun()
    with col_s3:
      if st.button(
          "% ลดสูงสุด",
          key="rk_sort_loss",
          type=(
              "primary"
              if st.session_state["rank_sort_mode"] == "loss"
              else "secondary"
          ),
          use_container_width=True,
      ):
        st.session_state["rank_sort_mode"] = "loss"
        st.rerun()

    # 2. ชั้นที่ 1: เลือกประเภทสินทรัพย์หลัก
    cur_p_type = st.session_state["rank_primary_type"]
    if cur_p_type not in MARKET_TYPES:
      cur_p_type = "crypto"
      st.session_state["rank_primary_type"] = "crypto"

    new_p_type = st.selectbox(
        "ประเภทสินทรัพย์หลัก",
        options=list(MARKET_TYPES.keys()),
        format_func=lambda x: MARKET_TYPES[x],
        index=list(MARKET_TYPES.keys()).index(cur_p_type),
        label_visibility="collapsed",
        key="sb_market_primary_type",
    )
    if new_p_type != cur_p_type:
      st.session_state["rank_primary_type"] = new_p_type
      st.session_state["rank_sub_cat"] = list(
          SUB_CATEGORIES[new_p_type].keys()
      )[0]
      st.rerun()

    # 3. ชั้นที่ 2: เลือกกระดาน หรือ ประเทศ หรือตลาดย่อย (สัมพันธ์กับชั้นที่ 1)
    avail_sub = SUB_CATEGORIES[st.session_state["rank_primary_type"]]
    cur_sub = st.session_state.get(
        "rank_sub_cat", list(avail_sub.keys())[0]
    )
    if cur_sub not in avail_sub:
      cur_sub = list(avail_sub.keys())[0]
      st.session_state["rank_sub_cat"] = cur_sub

    new_sub = st.selectbox(
        "กระดาน / ประเทศ",
        options=list(avail_sub.keys()),
        format_func=lambda x: avail_sub[x],
        index=list(avail_sub.keys()).index(cur_sub),
        label_visibility="collapsed",
        key="sb_market_sub_cat",
    )
    if new_sub != cur_sub:
      st.session_state["rank_sub_cat"] = new_sub
      st.rerun()

    # ดึงข้อมูลและจัดเรียงอันดับ
    ranked_list = fetch_ranked_market_data(
        st.session_state["rank_primary_type"], st.session_state["rank_sub_cat"]
    )
    sort_m = st.session_state["rank_sort_mode"]
    if sort_m == "vol":
      sorted_ranking = sorted(
          ranked_list, key=lambda x: x["volume_quote"], reverse=True
      )
    elif sort_m == "gain":
      sorted_ranking = sorted(
          ranked_list, key=lambda x: x["change_pct"], reverse=True
      )
    elif sort_m == "loss":
      sorted_ranking = sorted(ranked_list, key=lambda x: x["change_pct"])

    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; font-size:11px; color:#8b949e; padding:4px 4px 2px 4px; border-bottom:1px solid #1e2433;">
            <span style="flex:1.2;">สินทรัพย์</span>
            <span style="flex:1; text-align:right;">ราคาล่าสุด</span>
            <span style="flex:1; text-align:right;">24 ชม.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(height=450):
      for idx, item in enumerate(sorted_ranking[:80]):
        sym = item["symbol"]
        chg = item["change_pct"]
        price = item["last_price"]
        p_str = _format_price(price)
        chg_color = "#00e676" if chg >= 0 else "#ff3366"
        sign = "+" if chg > 0 else ""

        c_row1, c_row2 = st.columns(
            [1.2, 1.8], gap="small", vertical_alignment="center"
        )
        with c_row1:
          if st.button(
              f"{item['display_name']}",
              key=f"rk_btn_{sym}_{idx}",
              use_container_width=True,
          ):
            set_active_symbol(sym)
            st.rerun()

        with c_row2:
          st.markdown(
              f"""
                <div style="display:flex; justify-content:space-between; align-items:center; height:24px; font-size:12px; font-family:'JetBrains Mono', monospace; font-weight:600;">
                    <span style="color:#d1d4dc;">{p_str}</span>
                    <span style="color:{chg_color}; background:rgba({ '0,230,118' if chg >= 0 else '255,51,102' }, 0.15); padding:1px 5px; border-radius:4px;">
                        {sign}{chg:.2f}%
                    </span>
                </div>
                """,
              unsafe_allow_html=True,
          )

  # -------------------------------------------------------------
  # แถบล่างสุด: ตั้งค่า + นาฬิกา
  # -------------------------------------------------------------
  st.markdown(
      "<hr style='margin: 14px 0 10px 0; border: 0.5px solid #2a2e39;'>",
      unsafe_allow_html=True,
  )

  col_set, col_clk = st.columns([0.42, 0.58], vertical_alignment="center")
  with col_set:
    if st.button(
        "⚙️ ตั้งค่า",
        key="btn_chart_settings",
        use_container_width=True,
        type="secondary",
        help="ตั้งค่ากราฟ",
    ):
      show_chart_settings_dialog()

  with col_clk:
    now_bkk = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    st.markdown(
        f"""
        <div style="padding:6px 8px; background:#131722; border:1px solid #2a2e39; border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:10px; color:#787b86; display:flex; align-items:center; gap:3px;">
                    <span>🕒</span> BKK
                </div>
                <div style="font-size:11px; font-weight:600; color:#d1d4dc; font-family:monospace;">
                    {now_bkk.strftime('%H:%M:%S')}
                </div>
            </div>
            <span style="background:rgba(38,166,154,0.15); color:#26a69a; border:1px solid #26a69a; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:bold;">LIVE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  return {
      "show_top_bar": st.session_state.get("show_top_bar", True),
      "show_draw_toolbar": st.session_state.get("show_draw_toolbar", True),
  }