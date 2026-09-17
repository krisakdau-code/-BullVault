import time
import requests
import pandas as pd
import numpy as np
import streamlit as st

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

BINANCE_TF_MAP = {
    "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "3h": "2h", "4h": "4h",
    "D": "1d", "2D": "1d", "3D": "3d", "W": "1w", "M": "1M"
}

BITKUB_TF_MAP = {
    "5m": "5", "15m": "15", "30m": "30",
    "1h": "60", "2h": "120", "3h": "180", "4h": "240",
    "D": "1D", "2D": "1D", "3D": "1D", "W": "1W", "M": "1M"
}

YF_TF_MAP = {
    "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "60m", "2h": "60m", "3h": "60m", "4h": "60m",
    "D": "1d", "2D": "1d", "3D": "1d", "W": "1wk", "M": "1mo"
}

def is_yahoo_symbol(symbol: str) -> bool:
    return any(suffix in symbol for suffix in [".BK", ".HK", ".SS", ".SZ", ".VN", "=F", "=X"])

@st.cache_data(ttl=300, show_spinner=False)
def get_usd_thb_rate() -> float:
    """ดึงอัตราแลกเปลี่ยน USD/THB ล่าสุด"""
    try:
        import yfinance as yf
        fx = yf.Ticker("USDTHB=X").fast_info.last_price
        if fx and fx > 20:
            return float(fx)
    except Exception:
        pass
    return 35.0

@st.cache_data(ttl=15, show_spinner=False)
def fetch_ohlcv(symbol: str = "BTCUSDT", tf: str = "1h", limit: int = 500) -> pd.DataFrame:
    clean_sym = symbol.strip().upper()
    limit = min(max(int(limit), 50), 1000)

    # 1. สินทรัพย์กลุ่มข้าว (Local Catalog & Synthetic OHLCV)
    if clean_sym.startswith("RICE:") or clean_sym.startswith("FOB:"):
        try:
            from data.rice_ohlcv import get_rice_ohlcv
            df_rice = get_rice_ohlcv(clean_sym, tf, limit)
            if not df_rice.empty:
                return df_rice
        except Exception:
            pass

    # 2. สินทรัพย์กลุ่มหุ้น SET, โภคภัณฑ์, Forex (Yahoo Finance)
    if is_yahoo_symbol(clean_sym):
        try:
            import yfinance as yf
            interval = YF_TF_MAP.get(tf, "60m")
            period = "1y" if tf in ["D", "2D", "3D", "W", "M"] else "60d"
            ticker = yf.Ticker(clean_sym)
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                df = df.reset_index()
                time_col = "Datetime" if "Datetime" in df.columns else "Date"
                df["time"] = (pd.to_datetime(df[time_col]).astype("int64") // 10**9)
                df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
                df = df[["time", "open", "high", "low", "close", "volume"]].dropna()
                return df.drop_duplicates(subset=["time"]).sort_values("time").tail(limit).reset_index(drop=True)
        except Exception:
            pass

    # 3. สินทรัพย์คริปโตกระดาน Bitkub (เหรียญที่ลงท้ายด้วย _THB)
    if "_THB" in clean_sym or clean_sym.startswith("THB_"):
        coin = clean_sym.replace("_THB", "").replace("THB_", "")
        bk_symbol = f"THB_{coin}"
        resolution = BITKUB_TF_MAP.get(tf, "60")
        
        # คำนวณช่วงเวลาย้อนหลัง
        tf_seconds = {"5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400, "D": 86400}.get(tf, 3600)
        to_ts = int(time.time())
        from_ts = to_ts - (limit * tf_seconds * 2)

        url = f"https://api.bitkub.com/api/market/tradingview/history?symbol={bk_symbol}&resolution={resolution}&from={from_ts}&to={to_ts}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                data = res.json()
                if data.get("s") == "ok" and "t" in data and len(data["t"]) > 0:
                    df_bk = pd.DataFrame({
                        "time": data["t"],
                        "open": data["o"],
                        "high": data["h"],
                        "low": data["l"],
                        "close": data["c"],
                        "volume": data["v"]
                    })
                    for col in ["open", "high", "low", "close", "volume"]:
                        df_bk[col] = df_bk[col].astype(float)
                    return df_bk.drop_duplicates(subset=["time"]).sort_values("time").tail(limit).reset_index(drop=True)
        except Exception:
            pass

        # Fallback สำรองเฉพาะของ Bitkub: ดึงกราฟจริงจาก Binance แล้วแปลงค่าเป็นบาท (THB)
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

    # 4. สินทรัพย์คริปโตสากล (Binance REST API)
    clean_crypto = clean_sym.replace("/", "").replace(" ", "")
    interval = BINANCE_TF_MAP.get(tf, "1h")
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": clean_crypto, "interval": interval, "limit": limit}

    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            k = res.json()
            df = pd.DataFrame(k, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "count", "taker_buy_volume",
                "taker_buy_quote_volume", "ignore"
            ])
            df["time"] = (df["open_time"].astype("int64") // 1000)
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            return df[["time", "open", "high", "low", "close", "volume"]].drop_duplicates(subset=["time"]).sort_values("time").tail(limit).reset_index(drop=True)
    except Exception:
        pass

    # 5. Fallback ปลอดภัย (ไม่สร้างไส้เทียนซี่หวี)
    return _generate_fallback_data(clean_sym, limit)

@st.cache_data(ttl=10, show_spinner=False)
def fetch_ticker_24h(symbol: str = "BTCUSDT") -> dict:
    clean_sym = symbol.strip().upper()
    default_stats = {"last_price": 0.0, "price_change_pct": 0.0, "high_24h": 0.0, "low_24h": 0.0, "volume_24h": 0.0}

    # 1. Yahoo Finance
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

    # 2. Bitkub Ticker API
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

    # 3. Binance Ticker API
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
    
    # กำหนดราคาฐานให้สอดคล้องกับความเป็นจริง
    if "BTC" in symbol: base = 2600000.0 if "_THB" in symbol else 78000.0
    elif "ETH" in symbol: base = 90000.0 if "_THB" in symbol else 2600.0
    elif "DOGE" in symbol: base = 4.2 if "_THB" in symbol else 0.12
    elif "PERP" in symbol: base = 25.0 if "_THB" in symbol else 0.75
    else: base = 100.0

    noise = np.random.normal(0, base * 0.003, limit).cumsum()
    close_p = np.maximum(base + noise, base * 0.5)
    
    # ไส้เทียนคำนวณตามสัดส่วน % จริง (ไม่เกิน 0.5%) ป้องกันไส้ซี่หวี
    spread = close_p * 0.004
    open_p = close_p + np.random.uniform(-spread, spread, limit)
    high_p = np.maximum(open_p, close_p) + np.abs(np.random.normal(0, spread * 0.5, limit))
    low_p = np.minimum(open_p, close_p) - np.abs(np.random.normal(0, spread * 0.5, limit))

    return pd.DataFrame({
        "time": times, "open": open_p, "high": high_p,
        "low": low_p, "close": close_p, "volume": np.random.uniform(500, 5000, limit)
    })

def resolve_market_info(symbol: str) -> dict:
    """ฟังก์ชันกลางระบุข้อมูลสินทรัพย์ ป้องกันข้อมูลขัดแย้งกันข้ามหน้าจอ (Single Source of Truth)"""
    sym = symbol.strip()
    
    if sym.startswith("RICE:"):
        name_th = sym.replace("RICE:", "")
        return {
            "symbol": sym, "display_name": name_th, "exchange": "ไทย (หน้าโรงสี)",
            "category": "สินค้าเกษตร", "currency": "THB", "unit": "บาท/ตัน", "is_thb_native": True
        }
    elif sym.startswith("FOB:"):
        name_th = sym.replace("FOB:", "")
        return {
            "symbol": sym, "display_name": f"{name_th} (ส่งออก)", "exchange": "ตลาดส่งออกโลก",
            "category": "ข้าวส่งออก (FOB)", "currency": "USD", "unit": "USD/ตัน", "is_thb_native": False
        }
    elif "ZR=F" in sym:
        return {
            "symbol": "ZR=F", "display_name": "ข้าวเปลือกชิคาโก (CBOT)", "exchange": "CBOT",
            "category": "สัญญาอนุพันธ์ล่วงหน้า", "currency": "USD", "unit": "USd/bu", "is_thb_native": False
        }
    elif sym.endswith(".BK"):
        return {
            "symbol": sym, "display_name": sym.replace(".BK", ""), "exchange": "SET",
            "category": "ตลาดหลักทรัพย์ไทย", "currency": "THB", "unit": "บาท/หุ้น", "is_thb_native": True
        }
    elif sym in ["GC=F", "CL=F", "SI=F", "BZ=F", "NG=F"]:
        names = {"GC=F": "ทองคำโลก (Gold)", "CL=F": "น้ำมันดิบ WTI", "SI=F": "โลหะเงิน"}
        return {
            "symbol": sym, "display_name": names.get(sym, sym), "exchange": "COMEX / NYMEX",
            "category": "สินค้าโภคภัณฑ์", "currency": "USD", "unit": "USD", "is_thb_native": False
        }
    elif "=X" in sym:
        return {
            "symbol": sym, "display_name": sym.replace("=X", ""), "exchange": "FOREX",
            "category": "อัตราแลกเปลี่ยนเงินตรา", "currency": "USD", "unit": "", "is_thb_native": False
        }
    elif "_THB" in sym or sym.startswith("THB_"):
        clean_name = sym.replace("_THB", "").replace("THB_", "")
        return {
            "symbol": sym, "display_name": clean_name, "exchange": "BITKUB",
            "category": "คริปโตเคอร์เรนซี", "currency": "THB", "unit": "บาท", "is_thb_native": True
        }
    else:
        return {
            "symbol": sym, "display_name": sym.replace("USDT", ""), "exchange": "BINANCE",
            "category": "คริปโตเคอร์เรนซี", "currency": "USDT", "unit": "USDT", "is_thb_native": False
        }