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

def is_yahoo_symbol(symbol: str) -> bool:
    return any(suffix in symbol for suffix in [".BK", ".HK", ".SS", ".SZ", ".VN", "=F", "=X"])

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

@st.cache_data(ttl=15, show_spinner=False)
def fetch_ohlcv(symbol: str = "BTCUSDT", tf: str = "1h", limit: int = 2000) -> pd.DataFrame:
    clean_sym = symbol.strip().upper()
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
    url = "https://api.binance.com/api/v3/klines"
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

@st.cache_data(ttl=10, show_spinner=False)
def fetch_ticker_24h(symbol: str = "BTCUSDT") -> dict:
    clean_sym = symbol.strip().upper()
    default_stats = {"last_price": 0.0, "price_change_pct": 0.0, "high_24h": 0.0, "low_24h": 0.0, "volume_24h": 0.0}

    if is_yahoo_symbol(clean_sym):
        try:
            import yfinance as yf
            info = yf.Ticker(clean_sym).fast_info
            last_p = float(info.last_price or 0)
            prev_p = float(info.previous_close or last_p)
            pct = round(((last_p - prev_p) / prev_p) * 100, 2) if prev_p else 0.0
            return {
                "last_price": last_p, "price_change_pct": pct,
                "high_24h": float(info.day_high or last_p), "low_24h": float(info.day_low or last_p),
                "volume_24h": float(info.last_volume or 0)
            }
        except Exception:
            return default_stats

    if "_THB" in clean_sym or clean_sym.startswith("THB_"):
        coin = clean_sym.replace("_THB", "").replace("THB_", "")
        bk_symbol = f"THB_{coin}"
        url = f"https://api.bitkub.com/api/market/ticker?sym={bk_symbol}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=4)
            if res.status_code == 200:
                d = res.json().get(bk_symbol, {})
                if d:
                    return {
                        "last_price": float(d.get("last", 0)),
                        "price_change_pct": float(d.get("percentChange", 0)),
                        "high_24h": float(d.get("high24hr", 0)),
                        "low_24h": float(d.get("low24hr", 0)),
                        "volume_24h": float(d.get("baseVolume", 0))
                    }
        except Exception:
            pass

    clean_crypto = clean_sym.replace("/", "").replace(" ", "")
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={clean_crypto}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=4)
        if res.status_code == 200:
            d = res.json()
            return {
                "last_price": float(d.get("lastPrice", 0)),
                "price_change_pct": float(d.get("priceChangePercent", 0)),
                "high_24h": float(d.get("highPrice", 0)),
                "low_24h": float(d.get("lowPrice", 0)),
                "volume_24h": float(d.get("volume", 0))
            }
    except Exception:
        pass

    return default_stats

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
    sym = symbol.strip()
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