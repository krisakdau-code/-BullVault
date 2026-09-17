import os
import re
import time
import threading
import requests
import pandas as pd

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

CACHE_DIR = os.path.join("data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _get_cache_path(symbol: str, tf: str) -> str:
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', symbol)
    return os.path.join(CACHE_DIR, f"{safe_name}_{tf}.parquet")

def _load_cached_df(cache_path: str) -> pd.DataFrame:
    if os.path.exists(cache_path):
        try:
            return pd.read_parquet(cache_path)
        except Exception:
            pkl_path = cache_path.replace(".parquet", ".pkl")
            if os.path.exists(pkl_path):
                try:
                    return pd.read_pickle(pkl_path)
                except Exception:
                    pass
    return pd.DataFrame()

def _save_cached_df(df: pd.DataFrame, cache_path: str):
    if df.empty:
        return
    try:
        df.to_parquet(cache_path, index=False)
    except Exception:
        pkl_path = cache_path.replace(".parquet", ".pkl")
        df.to_pickle(pkl_path)

_SYNC_LOCKS = set()

def sync_deep_history_background(symbol: str, tf: str = "1h", target_bars: int = 5000):
    """รันการดึงข้อมูลประวัติศาสตร์ลึกในโหมดเบื้องหลัง (Background Thread)"""
    lock_key = f"{symbol}_{tf}"
    if lock_key in _SYNC_LOCKS:
        return
    
    t = threading.Thread(target=_sync_worker, args=(symbol, tf, target_bars), daemon=True)
    t.start()

def _sync_worker(symbol: str, tf: str, target_bars: int):
    lock_key = f"{symbol}_{tf}"
    _SYNC_LOCKS.add(lock_key)
    try:
        clean_sym = symbol.strip().upper()
        cache_path = _get_cache_path(clean_sym, tf)
        df = _load_cached_df(cache_path)

        if "_THB" in clean_sym or clean_sym.startswith("THB_"):
            _sync_bitkub_deep(clean_sym, tf, target_bars, df, cache_path)
        elif not any(x in clean_sym for x in [".BK", "RICE:", "FOB:", "=F", "=X"]):
            _sync_binance_deep(clean_sym, tf, target_bars, df, cache_path)
    finally:
        _SYNC_LOCKS.discard(lock_key)

def _sync_binance_deep(symbol: str, tf: str, target_bars: int, df: pd.DataFrame, cache_path: str):
    clean_crypto = symbol.replace("/", "").replace(" ", "")
    interval = BINANCE_TF_MAP.get(tf, "1h")
    url = "https://api.binance.com/api/v3/klines"
    
    records = df.to_dict("records") if not df.empty else []
    
    while len(records) < target_bars:
        earliest_time = records[0]["time"] if len(records) > 0 else int(time.time())
        params = {
            "symbol": clean_crypto,
            "interval": interval,
            "endTime": (earliest_time - 1) * 1000,
            "limit": 1000
        }
        
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=8)
            if res.status_code != 200:
                break
            data = res.json()
            if not data or len(data) == 0:
                break

            new_bars = []
            for k in data:
                new_bars.append({
                    "time": int(k[0]) // 1000,
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                })
            
            records = new_bars + records
            time.sleep(0.15)
        except Exception:
            break

    if records:
        merged_df = pd.DataFrame(records).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        _save_cached_df(merged_df, cache_path)

def _sync_bitkub_deep(symbol: str, tf: str, target_bars: int, df: pd.DataFrame, cache_path: str):
    coin = symbol.replace("_THB", "").replace("THB_", "")
    bk_symbol = f"THB_{coin}"
    resolution = BITKUB_TF_MAP.get(tf, "60")
    tf_seconds = {"5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400, "D": 86400}.get(tf, 3600)

    records = df.to_dict("records") if not df.empty else []
    
    while len(records) < target_bars:
        earliest_time = records[0]["time"] if len(records) > 0 else int(time.time())
        to_ts = earliest_time - 1
        from_ts = to_ts - (1000 * tf_seconds)
        
        url = f"https://api.bitkub.com/api/market/tradingview/history?symbol={bk_symbol}&resolution={resolution}&from={from_ts}&to={to_ts}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code != 200:
                break
            d = res.json()
            if d.get("s") != "ok" or not d.get("t"):
                break

            new_bars = []
            for i in range(len(d["t"])):
                new_bars.append({
                    "time": int(d["t"][i]),
                    "open": float(d["o"][i]),
                    "high": float(d["h"][i]),
                    "low": float(d["l"][i]),
                    "close": float(d["c"][i]),
                    "volume": float(d["v"][i])
                })
            
            records = new_bars + records
            time.sleep(0.15)
        except Exception:
            break

    if records:
        merged_df = pd.DataFrame(records).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        _save_cached_df(merged_df, cache_path)