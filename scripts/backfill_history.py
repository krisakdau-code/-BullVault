import os
import time
import requests
import pandas as pd
import yfinance as yf

CACHE_DIR = os.path.join("data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# 1. Binance
def backfill_binance(symbol: str, tf: str, target_bars: int = 15000):
    interval_map = {"1h": "1h", "4h": "4h", "D": "1d", "W": "1w"}
    interval = interval_map.get(tf, "1h")
    url = "https://api.binance.com/api/v3/klines"
    
    clean_sym = symbol.replace("/", "").replace(" ", "").upper()
    file_path = os.path.join(CACHE_DIR, f"{clean_sym}_{tf}.parquet")
    print(f"[*] Downloading Binance: {clean_sym} ({tf})...")

    records = []
    earliest_time = int(time.time())

    while len(records) < target_bars:
        params = {
            "symbol": clean_sym,
            "interval": interval,
            "endTime": (earliest_time - 1) * 1000,
            "limit": 1000
        }
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                break
            data = res.json()
            if not data or len(data) == 0:
                print(f"    -> ถึงแท่งแรกสุดของตลาดแล้ว ({len(records):,} bars)")
                break

            batch = []
            for k in data:
                batch.append({
                    "time": int(k[0]) // 1000,
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                })
            records = batch + records
            earliest_time = records[0]["time"]
            time.sleep(0.1)
        except Exception as e:
            print(f"    Error: {e}")
            break

    if records:
        df = pd.DataFrame(records).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        df.to_parquet(file_path, index=False)
        print(f"    [+] บันทึกสำเร็จ: {file_path} ({len(df):,} แท่ง)")

# 2. Bitkub (แก้ URL และสลับ Format เป็น COIN_THB)
def backfill_bitkub(symbol: str, tf: str, target_bars: int = 10000):
    res_map = {"1h": "60", "4h": "240", "D": "1D"}
    sec_map = {"1h": 3600, "4h": 14400, "D": 86400}
    resolution = res_map.get(tf, "60")
    tf_sec = sec_map.get(tf, 3600)

    clean_sym = symbol.strip().upper()
    coin = clean_sym.replace("_THB", "").replace("THB_", "")
    # Bitkub TradingView History ต้องใช้ COIN_THB เท่านั้น
    bk_symbol = f"{coin}_THB"
    file_path = os.path.join(CACHE_DIR, f"{clean_sym}_{tf}.parquet")
    print(f"[*] Downloading Bitkub: {bk_symbol} ({tf})...")

    records = []
    to_ts = int(time.time())

    while len(records) < target_bars:
        # ดึงทีละก้อน 1,000 แท่งถอยหลัง
        from_ts = to_ts - (1000 * tf_sec)
        # URL ที่ถูกต้อง: api.bitkub.com/tradingview/history
        url = f"https://api.bitkub.com/tradingview/history?symbol={bk_symbol}&resolution={resolution}&from={from_ts}&to={to_ts}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                break
            d = res.json()
            if d.get("s") != "ok" or not d.get("t") or len(d["t"]) == 0:
                print(f"    -> ถึงแท่งแรกสุดของ Bitkub แล้ว ({len(records):,} bars)")
                break

            batch = []
            for i in range(len(d["t"])):
                batch.append({
                    "time": int(d["t"][i]),
                    "open": float(d["o"][i]),
                    "high": float(d["h"][i]),
                    "low": float(d["l"][i]),
                    "close": float(d["c"][i]),
                    "volume": float(d["v"][i])
                })
            records = batch + records
            to_ts = int(d["t"][0]) - 1
            time.sleep(0.15)
        except Exception as e:
            print(f"    Error: {e}")
            break

    if records:
        df = pd.DataFrame(records).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        df.to_parquet(file_path, index=False)
        print(f"    [+] บันทึกสำเร็จ: {file_path} ({len(df):,} แท่ง)")

# 3. หุ้นไทย SET และทองคำ (ปลดล็อก yf.download ย้อนหลัง 15 ปี)
def backfill_yahoo(symbol: str, tf: str):
    clean_sym = symbol.strip().upper()
    file_path = os.path.join(CACHE_DIR, f"{clean_sym}_{tf}.parquet")
    print(f"[*] Downloading Yahoo Finance: {clean_sym} ({tf})...")

    try:
        if tf in ["D", "W"]:
            df = yf.download(clean_sym, start="2010-01-01", interval="1d", progress=False)
        else:
            df = yf.download(clean_sym, period="2y", interval="60m", progress=False)

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
            df = df[["time", "open", "high", "low", "close", "volume"]].dropna()
            df = df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
            df.to_parquet(file_path, index=False)
            print(f"    [+] บันทึกสำเร็จ: {file_path} ({len(df):,} แท่ง)")
    except Exception as e:
        print(f"    Error: {e}")

if __name__ == "__main__":
    print("=== เริ่มการดึงประวัติศาสตร์ตลาด (Tier 1 Assets) ===")

    # คริปโต Bitkub
    bitkub_coins = ["BTC_THB", "ETH_THB", "KUB_THB", "DOGE_THB"]
    for sym in bitkub_coins:
        backfill_bitkub(sym, "D", target_bars=3500)
        backfill_bitkub(sym, "1h", target_bars=15000)

    # หุ้นไทย SET และทองคำโลก
    set_stocks = ["PTT.BK", "DELTA.BK", "AOT.BK", "CPALL.BK", "GC=F"]
    for sym in set_stocks:
        backfill_yahoo(sym, "D")
        backfill_yahoo(sym, "1h")

    print("\n=== ดึงข้อมูลประวัติศาสตร์ครบถ้วนเรียบร้อย! ===")