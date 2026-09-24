import os
import re
import time
import zipfile
import urllib.request
import requests
import pandas as pd
import numpy as np
import streamlit as st

from data.history_sync import (
    HEADERS, BINANCE_TF_MAP, BITKUB_TF_MAP, CACHE_DIR,
    _get_cache_path, _load_cached_df, _save_cached_df,
    sync_deep_history_background
)

# ลิงก์ดาวน์โหลดตรงจาก GitHub Release
GITHUB_RELEASE_ZIP_URL = "https://github.com/krisakdau-code/Kating-diamond/releases/download/v1.0-data/market_history.zip.zip"

def ensure_cache_hydrated():
    """ดาวน์โหลดและแตกไฟล์ประวัติศาสตร์ย้อนหลังลง CACHE_DIR อัตโนมัติเมื่อรันบน Cloud"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        parquet_files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".parquet")]
        if not parquet_files and GITHUB_RELEASE_ZIP_URL:
            zip_dest = os.path.join("data", "market_history.zip")
            urllib.request.urlretrieve(GITHUB_RELEASE_ZIP_URL, zip_dest)
            if os.path.exists(zip_dest):
                with zipfile.ZipFile(zip_dest, "r") as zip_ref:
                    zip_ref.extractall(CACHE_DIR)
                os.remove(zip_dest)
    except Exception:
        pass

ensure_cache_hydrated()

# ตารางความลึกระดับ Ultra-Deep History
TF_TARGET_BARS = {
    "1m": 15000, "3m": 15000, "5m": 20000, "15m": 20000, "30m": 20000, "45m": 15000,
    "1h": 25000, "2h": 15000, "3h": 12000, "4h": 15000,
    "D": 6000, "2D": 3500, "3D": 2500, "W": 1500,
    "M": 500, "3M": 200, "6M": 100, "12M": 50
}

YF_TF_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "60m", "2h": "60m", "4h": "60m",
    "D": "1d", "2D": "1d", "3D": "1d", "W": "1wk", "M": "1mo"
}

def standardize_symbol(symbol: str) -> str:
    """แปลงและปรับมาตรฐานชื่อสัญลักษณ์ข้ามกระดาน ป้องกันข้อผิดพลาด API และชื่อสับสน"""
    if not symbol:
        return ""
    s = str(symbol).strip().upper()
    
    # 1. สินค้าเกษตรข้าว
    if s.startswith("RICE") and not s.startswith("RICE:"):
        return "RICE:" + s[4:].lstrip(":")
    if s.startswith("FOB") and not s.startswith("FOB:"):
        return "FOB:" + s[3:].lstrip(":")
    if s.startswith("RICE:") or s.startswith("FOB:") or "ZR=F" in s:
        return s
        
    # 2. สินค้าโภคภัณฑ์และค่าเงิน
    if any(s.endswith(x) for x in ["=F", "=X"]):
        return s
        
    # 3. หุ้นไทย SET (Yahoo Finance format: .BK)
    if s.endswith(".BK"):
        return s
    if s.endswith("BK") and not (s.startswith("THB_") or "_THB" in s or s.endswith("USDT")):
        ticker = s[:-2]
        if ticker:
            return f"{ticker}.BK"
            
    # 4. คริปโต Bitkub (format: THB_xxx)
    if s.endswith("_THB"):
        coin = s[:-4]
        return f"THB_{coin}"
    if s.endswith("THB") and not s.startswith("THB_"):
        coin = s[:-3]
        if coin:
            return f"THB_{coin}"

    # 5. คริปโตทั่วไป
    if s == "BTC":
        return "BTCUSDT"
    if not any(s.endswith(x) for x in ["USDT", "BUSD", "USDC"]) and not s.startswith("THB_") and not s.endswith(".BK"):
        return f"{s}USDT"
        
    return s

def is_yahoo_symbol(symbol: str) -> bool:
    s = standardize_symbol(symbol)
    return any(suffix in s for suffix in [".BK", ".HK", ".SS", ".SZ", ".VN", "=F", "=X"])

def resample_ohlcv(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """รวมแท่งเทียนอัตโนมัติสำหรับ Timeframe ที่ไม่มีใน API ตรงๆ"""
    if df.empty or len(df) < 2:
        return df
    
    rule_map = {
        "45m": "45min", "2h": "2h", "3h": "3h",
        "2D": "2D", "3D": "3D", "3M": "3ME", "6M": "6ME", "12M": "12ME"
    }
    rule = rule_map.get(target_tf)
    if not rule:
        return df

    try:
        temp = df.copy()
        temp["datetime"] = pd.to_datetime(temp["time"], unit="s")
        temp = temp.set_index("datetime")
        resampled = temp.resample(rule).agg({
            "time": "first",
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna().reset_index(drop=True)
        return resampled
    except Exception:
        return df

@st.cache_data(ttl=300, show_spinner=False)
def get_usd_thb_rate() -> float:
    try:
        import yfinance as yf
        fx = yf.Ticker("USDTHB=X").fast_info.last_price
        if fx and fx > 20:
            return float(fx)
    except Exception:
        pass
    return 35.0

@st.cache_data(ttl=5, show_spinner=False)
def fetch_ohlcv(symbol: str = "BTCUSDT", tf: str = "1h", limit: int = 2000) -> pd.DataFrame:
    clean_sym = standardize_symbol(symbol)
    cache_path = _get_cache_path(clean_sym, tf)
    cached_df = _load_cached_df(cache_path)
    
    # ดึงข้อมูลประวัติศาสตร์ลึกในพื้นหลังตามโควตาของแต่ละ Timeframe
    target = TF_TARGET_BARS.get(tf, 3000)
    sync_deep_history_background(clean_sym, tf, target_bars=target)
    
    last_timestamp = int(cached_df["time"].max()) if not cached_df.empty and "time" in cached_df.columns else 0

    # 1. สินค้าเกษตรข้าว
    if clean_sym.startswith("RICE:") or clean_sym.startswith("FOB:"):
        try:
            from data.rice_ohlcv import get_rice_ohlcv
            df_rice = get_rice_ohlcv(clean_sym, tf, limit=limit)
            if not df_rice.empty:
                _save_cached_df(df_rice, cache_path)
                return df_rice
        except Exception:
            pass

    # 2. หุ้น SET, ทองคำ, Forex (Yahoo Finance)
    if is_yahoo_symbol(clean_sym):
        try:
            import yfinance as yf
            base_tf = "60m" if tf in ["2h", "3h", "4h"] else ("1d" if tf in ["2D", "3D"] else YF_TF_MAP.get(tf, "60m"))
            period = "max" if tf in ["D", "2D", "3D", "W", "M", "3M", "6M", "12M"] else "730d"
            ticker = yf.Ticker(clean_sym)
            df = ticker.history(period=period, interval=base_tf)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0].lower() for col in df.columns]
                else:
                    df.columns = [c.lower() for c in df.columns]

                df = df.reset_index()
                time_col = "Datetime" if "Datetime" in df.columns else "Date"
                if time_col not in df.columns:
                    time_col = df.columns[0]

                df["time"] = (pd.to_datetime(df[time_col]).astype("int64") // 10**9)
                df = df.rename(columns={"open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
                df = df[["time", "open", "high", "low", "close", "volume"]].dropna()
                merged = pd.concat([cached_df, df]).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
                
                if tf in ["45m", "2h", "3h", "2D", "3D", "3M", "6M", "12M"]:
                    merged = resample_ohlcv(merged, tf)
                
                _save_cached_df(merged, cache_path)
                return merged
        except Exception:
            pass

    # 3. Bitkub (_THB)
    if "_THB" in clean_sym or clean_sym.startswith("THB_"):
        coin = clean_sym.replace("_THB", "").replace("THB_", "")
        bk_symbol = f"{coin}_THB"
        resolution = BITKUB_TF_MAP.get(tf, "60")
        tf_seconds = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400, "D": 86400}.get(tf, 3600)
        
        to_ts = int(time.time())
        from_ts = last_timestamp if last_timestamp > 0 else (to_ts - (limit * tf_seconds))
        url = f"https://api.bitkub.com/tradingview/history?symbol={bk_symbol}&resolution={resolution}&from={from_ts}&to={to_ts}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                data = res.json()
                if data.get("s") == "ok" and "t" in data and len(data["t"]) > 0:
                    df_new = pd.DataFrame({
                        "time": data["t"], "open": data["o"], "high": data["h"],
                        "low": data["l"], "close": data["c"], "volume": data["v"]
                    })
                    for col in ["open", "high", "low", "close", "volume"]:
                        df_new[col] = df_new[col].astype(float)
                    merged = pd.concat([cached_df, df_new]).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
                    
                    if tf in ["45m", "2h", "3h", "2D", "3D", "3M", "6M", "12M"]:
                        merged = resample_ohlcv(merged, tf)
                        
                    _save_cached_df(merged, cache_path)
                    return merged
        except Exception:
            pass

        # Failover Binance -> THB
        try:
            binance_equiv = f"{coin}USDT"
            df_equiv = fetch_ohlcv(binance_equiv, tf=tf, limit=limit)
            if not df_equiv.empty and "close" in df_equiv.columns and df_equiv["close"].iloc[-1] > 0:
                rate = get_usd_thb_rate()
                for c in ["open", "high", "low", "close"]:
                    df_equiv[c] = df_equiv[c] * rate
                return df_equiv
        except Exception:
            pass

    # 4. Binance REST API
    clean_crypto = clean_sym.replace("/", "").replace(" ", "")
    interval = BINANCE_TF_MAP.get(tf, "1h")
    url = "https://data-api.binance.vision/api/v3/klines"
    params = {"symbol": clean_crypto, "interval": interval, "limit": 1000}
    if last_timestamp > 0:
        params["startTime"] = (last_timestamp + 1) * 1000

    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            k = res.json()
            if len(k) > 0:
                df_new = pd.DataFrame(k, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "count", "taker_buy_volume",
                    "taker_buy_quote_volume", "ignore"
                ])
                df_new["time"] = (df_new["open_time"].astype("int64") // 1000)
                for col in ["open", "high", "low", "close", "volume"]:
                    df_new[col] = df_new[col].astype(float)
                df_new = df_new[["time", "open", "high", "low", "close", "volume"]]
                merged = pd.concat([cached_df, df_new]).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
                
                if tf in ["45m", "2h", "3h", "2D", "3D", "3M", "6M", "12M"]:
                    merged = resample_ohlcv(merged, tf)
                    
                _save_cached_df(merged, cache_path)
                return merged
    except Exception:
        pass

    if not cached_df.empty:
        return cached_df

    return _generate_fallback_data(clean_sym, limit=1000)

@st.cache_data(ttl=3, show_spinner=False)
def fetch_ticker_24h(symbol: str) -> dict:
    """ดึงข้อมูลราคาล่าสุด, Bid/Ask, % เปลี่ยนแปลงรอบ 24h และ Volume รวม 24h ตรงตามกระดานจริง"""
    if not symbol:
        return None
    sym = standardize_symbol(symbol)

    # 1. กระดาน Bitkub (เหรียญที่จับคู่กับ THB)
    is_bitkub = sym.startswith("THB_") or sym.endswith("THB") or "_THB" in sym
    if is_bitkub:
        coin_part = sym.replace("THB_", "").replace("_THB", "").replace("THB", "")
        bk_key = f"THB_{coin_part}".upper()
        try:
            r = requests.get("https://api.bitkub.com/api/market/ticker", timeout=4)
            if r.status_code == 200:
                data = r.json()
                item = data.get(bk_key)
                if not item:
                    item = next((v for k, v in data.items() if coin_part in k), None)
                if item:
                    last_p = float(item.get("last", 0.0))
                    base_v = float(item.get("baseVolume", 0.0))
                    quote_v = float(item.get("quoteVolume", 0.0))
                    high_24 = float(item.get("high24hr", 0.0))
                    low_24 = float(item.get("low24hr", 0.0))
                    bid_p = float(item.get("highestBid", 0.0))
                    ask_p = float(item.get("lowestAsk", 0.0))

                    # ดึงราคาปิดแท่งวันเมื่อวานเพื่อให้ได้ % เปลี่ยนแปลงตรงกับ TradingView (-2.68%)
                    prev_c = 0.0
                    try:
                        from data.candles import fetch_daily_bars

                        d_bars = fetch_daily_bars(sym, 2)
                        if d_bars and len(d_bars) >= 2:
                            prev_c = float(d_bars[-2]["close"])
                        elif d_bars and len(d_bars) == 1:
                            prev_c = float(d_bars[0]["open"])
                    except Exception:
                        pass

                    if prev_c > 0:
                        chg_abs = last_p - prev_c
                        pct_val = (chg_abs / prev_c) * 100.0
                    else:
                        pct_val = float(item.get("percentChange", 0.0))
                        prev_c = (
                            (last_p / (1.0 + pct_val / 100.0))
                            if pct_val != -100
                            else last_p
                        )
                        chg_abs = last_p - prev_c

                    return {
                        "symbol": bk_key,
                        "display": f"{coin_part}THB",
                        "last": last_p,
                        "last_price": last_p,
                        "prev_close": prev_c,
                        "bid": bid_p,
                        "ask": ask_p,
                        "high_24h": high_24,
                        "low_24h": low_24,
                        "change_abs": chg_abs,
                        "change_pct": pct_val,
                        "price_change_pct": pct_val,
                        "base_volume": base_v,
                        "volume_24h": base_v,
                        "quote_volume": quote_v,
                        "ts": time.time(),
                    }
        except Exception:
            pass

            if prev_c > 0:
                    chg_abs = last_p - prev_c
                    pct_val = (chg_abs / prev_c) * 100.0
            else:
                        pct_val = float(item.get("percentChange", 0.0))
                        prev_c = (
                            (last_p / (1.0 + pct_val / 100.0))
                            if pct_val != -100
                            else last_p
                        )
                        chg_abs = last_p - prev_c
            return {
                        "symbol": bk_key,
                        "display": f"{coin_part}THB",
                        "last": last_p,
                        "last_price": last_p,
                        "prev_close": prev_c,
                        "bid": bid_p,
                        "ask": ask_p,
                        "high_24h": high_24,
                        "low_24h": low_24,
                        "change_abs": chg_abs,
                        "change_pct": pct_val,
                        "price_change_pct": pct_val,
                        "base_volume": base_v,
                        "volume_24h": base_v,
                        "quote_volume": quote_v,
                        "ts": time.time(),
                    }
        except Exception:
            pass

   # 2. กระดาน Binance (เหรียญที่จับคู่กับ USDT, BUSD, USDC)
    b_sym = sym.replace("_", "").upper()
    if any(b_sym.endswith(x) for x in ["USDT", "BUSD", "USDC", "BTC", "ETH"]):
      try:
        # ดึง Ticker ข้อมูล Bid / Ask / Volume
        r = requests.get(
            f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={b_sym}",
            timeout=4,
        )
        item = r.json() if r.status_code == 200 else {}

        last_p = float(item.get("lastPrice", 0.0))
        prev_c = float(item.get("prevClosePrice", last_p))
        bid_p = float(item.get("bidPrice", 0.0))
        ask_p = float(item.get("askPrice", 0.0))
        high_24 = float(item.get("highPrice", 0.0))
        low_24 = float(item.get("lowPrice", 0.0))
        base_v = float(item.get("volume", 0.0))
        quote_v = float(item.get("quoteVolume", 0.0))

        # ดึงแท่งเทียน 1D (Daily 00:00 UTC) เพื่อคำนวณ % และราคาล่าสุดให้ตรงกับ TradingView เป๊ะๆ
        try:
          rk = requests.get(
              f"https://data-api.binance.vision/api/v3/klines?symbol={b_sym}&interval=1d&limit=2",
              timeout=3,
          )
          if rk.status_code == 200:
            kl = rk.json()
            if len(kl) >= 2:
              prev_c = float(
                  kl[0][4]
              )  # ราคาปิดแท่งเมื่อวาน (ตัดรอบ 00:00 UTC ตามแบบ TradingView)
              last_p = float(kl[1][4])  # ราคาปิดแท่งล่าสุดแบบเรียลไทม์
              high_24 = max(high_24, float(kl[1][2]))
              low_24 = (
                  min(low_24, float(kl[1][3]))
                  if low_24 > 0
                  else float(kl[1][3])
              )
        except Exception:
          pass

        chg_abs = last_p - prev_c
        pct_val = (chg_abs / prev_c * 100.0) if prev_c > 0 else 0.0

        return {
            "symbol": b_sym,
            "display": b_sym,
            "last": last_p,
            "last_price": last_p,
            "prev_close": prev_c,
            "bid": bid_p,
            "ask": ask_p,
            "high_24h": high_24,
            "low_24h": low_24,
            "change_abs": chg_abs,
            "change_pct": pct_val,
            "price_change_pct": pct_val,
            "base_volume": base_v,
            "volume_24h": base_v,
            "quote_volume": quote_v,
            "ts": time.time(),
        }
      except Exception:
        pass

    # 3. สินทรัพย์อื่น ๆ (Forex / Stocks) ดึงผ่าน yfinance
    try:
        import yfinance as yf
        t = yf.Ticker(sym)
        hist = t.history(period="2d")
        if len(hist) >= 2:
            p_prev = float(hist["Close"].iloc[-2])
            p_now = float(hist["Close"].iloc[-1])
            pct_val = ((p_now - p_prev) / p_prev) * 100.0 if p_prev > 0 else 0.0
            vol_val = float(hist["Volume"].iloc[-1])
            hi_val = float(hist["High"].iloc[-1])
            lo_val = float(hist["Low"].iloc[-1])
            return {
                "symbol": sym,
                "display": sym,
                "last": p_now,
                "last_price": p_now,
                "prev_close": p_prev,
                "bid": p_now * 0.9995,
                "ask": p_now * 1.0005,
                "high_24h": hi_val,
                "low_24h": lo_val,
                "change_abs": p_now - p_prev,
                "change_pct": pct_val,
                "price_change_pct": pct_val,
                "base_volume": vol_val,
                "volume_24h": vol_val,
                "quote_volume": vol_val * p_now,
                "ts": time.time(),
            }
    except Exception:
        pass

    return None

# สร้าง alias ให้รองรับการเรียกทั้งสองชื่อ
get_ticker_24h = fetch_ticker_24h


def get_52w_range(symbol: str, fetch_daily_bars=None) -> dict:
    """คำนวณช่วง 52 สัปดาห์ (1 ปี) พร้อม Sanity Check กำจัดแท่ง Outlier ป้องกัน 52W High ระเบิดเป็น 75.4"""
    bars = []
    if fetch_daily_bars:
        bars = fetch_daily_bars(symbol, 365) or []
    else:
        try:
            from data.candles import fetch_daily_bars as _f
            bars = _f(symbol, 365) or []
        except Exception:
            df_d = fetch_ohlcv(symbol, tf="D", limit=365)
            if df_d is not None and not df_d.empty:
                bars = df_d.to_dict("records")

    if not bars:
        return {"low": 0.0, "high": 0.0, "bars": 0}

    highs = [float(b["high"]) for b in bars if b.get("high") and float(b["high"]) > 0]
    lows = [float(b["low"]) for b in bars if b.get("low") and float(b["low"]) > 0]
    if not highs or not lows:
        return {"low": 0.0, "high": 0.0, "bars": 0}

    hi, lo = max(highs), min(lows)
    t = fetch_ticker_24h(symbol)
    if t and t.get("last", 0) > 0 and hi > t["last"] * 50:
        med = sorted(highs)[len(highs) // 2]
        highs = [h for h in highs if h <= med * 20]
        hi = max(highs) if highs else t["last"]

    return {"low": lo, "high": hi, "bars": len(bars)}

def _generate_fallback_data(symbol: str, limit: int) -> pd.DataFrame:
    now = int(time.time())
    times = [now - (i * 3600) for i in range(limit)][::-1]
    
    if "BTC" in symbol: base = 2600000.0 if "_THB" in symbol else 78000.0
    elif "ETH" in symbol: base = 90000.0 if "_THB" in symbol else 2600.0
    elif "DOGE" in symbol: base = 4.2 if "_THB" in symbol else 0.12
    elif "PERP" in symbol: base = 25.0 if "_THB" in symbol else 0.75
    else: base = 100.0

    noise = np.random.normal(0, base * 0.003, limit).cumsum()
    close_p = np.maximum(base + noise, base * 0.5)
    spread = close_p * 0.004
    open_p = close_p + np.random.uniform(-spread, spread, limit)
    high_p = np.maximum(open_p, close_p) + np.abs(np.random.normal(0, spread * 0.5, limit))
    low_p = np.minimum(open_p, close_p) - np.abs(np.random.normal(0, spread * 0.5, limit))

    return pd.DataFrame({
        "time": times, "open": open_p, "high": high_p,
        "low": low_p, "close": close_p, "volume": np.random.uniform(500, 5000, limit)
    })

def resolve_market_info(symbol: str) -> dict:
    sym = standardize_symbol(symbol).strip()
    if sym.startswith("RICE:"):
        name_th = sym.replace("RICE:", "")
        return {"symbol": sym, "display_name": name_th, "exchange": "ไทย (หน้าโรงสี)", "category": "สินค้าเกษตร", "currency": "THB", "unit": "บาท/ตัน", "is_thb_native": True}
    elif sym.startswith("FOB:"):
        name_th = sym.replace("FOB:", "")
        return {"symbol": sym, "display_name": f"{name_th} (ส่งออก)", "exchange": "ตลาดส่งออกโลก", "category": "ข้าวส่งออก (FOB)", "currency": "USD", "unit": "USD/ตัน", "is_thb_native": False}
    elif "ZR=F" in sym:
        return {"symbol": "ZR=F", "display_name": "ข้าวเปลือกชิคาโก (CBOT)", "exchange": "CBOT", "category": "สัญญาอนุพันธ์ล่วงหน้า", "currency": "USD", "unit": "USd/bu", "is_thb_native": False}
    elif sym.endswith(".BK"):
        return {"symbol": sym, "display_name": sym.replace(".BK", ""), "exchange": "SET", "category": "ตลาดหลักทรัพย์ไทย", "currency": "THB", "unit": "บาท/หุ้น", "is_thb_native": True}
    elif sym in ["GC=F", "CL=F", "SI=F", "BZ=F", "NG=F"]:
        names = {"GC=F": "ทองคำโลก (Gold)", "CL=F": "น้ำมันดิบ WTI", "SI=F": "โลหะเงิน"}
        return {"symbol": sym, "display_name": names.get(sym, sym), "exchange": "COMEX / NYMEX", "category": "สินค้าโภคภัณฑ์", "currency": "USD", "unit": "USD", "is_thb_native": False}
    elif "=X" in sym:
        return {"symbol": sym, "display_name": sym.replace("=X", ""), "exchange": "FOREX", "category": "อัตราแลกเปลี่ยนเงินตรา", "currency": "USD", "unit": "", "is_thb_native": False}
    elif "_THB" in sym or sym.startswith("THB_"):
        clean_name = sym.replace("_THB", "").replace("THB_", "")
        return {"symbol": sym, "display_name": clean_name, "exchange": "BITKUB", "category": "คริปโตเคอร์เรนซี", "currency": "THB", "unit": "บาท", "is_thb_native": True}
    else:
        return {"symbol": sym, "display_name": sym.replace("USDT", ""), "exchange": "BINANCE", "category": "คริปโตเคอร์เรนซี", "currency": "USDT", "unit": "USDT", "is_thb_native": False}