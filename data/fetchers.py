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

YF_TF_MAP = {
    "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "60m", "2h": "60m", "3h": "60m", "4h": "60m",
    "D": "1d", "2D": "1d", "3D": "1d", "W": "1wk", "M": "1mo"
}
def is_yahoo_symbol(symbol: str) -> bool:
    return any(suffix in symbol for suffix in [".BK", ".HK", ".SS", ".SZ", ".VN", "=F", "=_"])

@st.cache_data(ttl=15, show_spinner=False)
def fetch_ohlcv(symbol: str = "BTCUSDT", tf: str = "1h", limit: int = 500) -> pd.DataFrame:
    clean_sym = symbol.strip().upper()
    limit = min(max(int(limit), 50), 1000)

    # 1. สินทรัพย์กลุ่มหุ้น โภคภัณฑ์ Forex (Yahoo Finance)
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
                # แปลงเวลาเป็น Unix Timestamp (วินาที)
                df["time"] = (pd.to_datetime(df[time_col]).astype("int64") // 10**9)
                df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
                df = df[["time", "open", "high", "low", "close", "volume"]].dropna()
                return df.drop_duplicates(subset=["time"]).sort_values("time").tail(limit).reset_index(drop=True)
        except Exception:
            pass

    # 2. สินทรัพย์คริปโต (Binance REST API + Headers)
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
            # แปลง open_time (ms) เป็น seconds int64 โดยตรง
            df["time"] = (df["open_time"].astype("int64") // 1000)
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            return df[["time", "open", "high", "low", "close", "volume"]].drop_duplicates(subset=["time"]).sort_values("time").tail(limit).reset_index(drop=True)
    except Exception:
        pass

    # 3. Fallback ฉุกเฉิน
    return _generate_fallback_data(clean_sym, limit)

@st.cache_data(ttl=10, show_spinner=False)
def fetch_ticker_24h(symbol: str = "BTCUSDT") -> dict:
    clean_sym = symbol.strip().upper()
    default_stats = {"last_price": 78000.0, "price_change_pct": 0.0, "high_24h": 79000.0, "low_24h": 76000.0, "volume_24h": 1500.0}

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
    base = 78000.0 if "BTC" in symbol else 150.0
    noise = np.random.normal(0, base * 0.002, limit).cumsum()
    close_p = base + noise
    return pd.DataFrame({
        "time": times, "open": close_p - 10, "high": close_p + 25,
        "low": close_p - 25, "close": close_p, "volume": np.random.uniform(100, 1000, limit)
    })