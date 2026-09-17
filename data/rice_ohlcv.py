import os
import json
import time
import numpy as np
import pandas as pd

RICE_SPECS = {
    # ข้าวไทยหน้าโรงสี (บาท/ตัน)
    "RICE:ข้าวเปลือกหอมมะลิ": {"base": 15200.0, "vol": 180.0},
    "RICE:ข้าวเปลือกเจ้า5%": {"base": 11400.0, "vol": 140.0},
    "RICE:ข้าวเปลือกปทุมธานี1": {"base": 12600.0, "vol": 150.0},
    "RICE:ข้าวเปลือกเหนียว": {"base": 13300.0, "vol": 160.0},

    # ข้าวไทยส่งออก FOB (USD/ตัน)
    "FOB:TH_HOM_MALI": {"base": 885.0, "vol": 12.0},
    "FOB:TH_WHITE_5%": {"base": 575.0, "vol": 8.0},
    "FOB:TH_WHITE_25%": {"base": 535.0, "vol": 7.0},
    "FOB:TH_PARBOILED": {"base": 570.0, "vol": 8.0},
    "FOB:TH_BROKEN_A1": {"base": 450.0, "vol": 6.0},

    # ข้าวเวียดนามส่งออก FOB (USD/ตัน)
    "FOB:VN_ST25": {"base": 795.0, "vol": 11.0},
    "FOB:VN_JASMINE85": {"base": 640.0, "vol": 9.0},
    "FOB:VN_DT8": {"base": 615.0, "vol": 8.0},
    "FOB:VN_WHITE_5%": {"base": 545.0, "vol": 8.0},
    "FOB:VN_WHITE_25%": {"base": 518.0, "vol": 7.0},
    "FOB:VN_BROKEN_100%": {"base": 435.0, "vol": 6.0},

    # ข้าวอินเดียส่งออก FOB (USD/ตัน)
    "FOB:IN_BASMATI_1121": {"base": 1050.0, "vol": 15.0},
    "FOB:IN_WHITE_5%": {"base": 490.0, "vol": 10.0},
    "FOB:IN_WHITE_25%": {"base": 465.0, "vol": 9.0},
    "FOB:IN_PARBOILED_5%": {"base": 525.0, "vol": 8.0},
    "FOB:IN_BROKEN_100%": {"base": 410.0, "vol": 6.0},

    # ปากีสถาน / กัมพูชา / เมียนมา (USD/ตัน)
    "FOB:PK_BASMATI_SUPER": {"base": 920.0, "vol": 14.0},
    "FOB:PK_WHITE_5%": {"base": 510.0, "vol": 8.0},
    "FOB:PK_WHITE_25%": {"base": 475.0, "vol": 7.0},
    "FOB:KH_PHKA_RUMDUOL": {"base": 820.0, "vol": 11.0},
    "FOB:MM_EMATA_5%": {"base": 495.0, "vol": 8.0},
}

def generate_rice_ohlcv(symbol: str, bars: int = 600) -> pd.DataFrame:
    clean_sym = symbol.strip()

    # 1. ตลาดล่วงหน้าชิคาโก CBOT (ดึงสดผ่าน Yahoo Finance)
    if "ZR=F" in clean_sym:
        try:
            import yfinance as yf
            df = yf.Ticker("ZR=F").history(period="2y", interval="1d")
            if not df.empty:
                df = df.reset_index()
                time_col = "Datetime" if "Datetime" in df.columns else "Date"
                df["time"] = (pd.to_datetime(df[time_col]).astype("int64") // 10**9)
                df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
                return df[["time", "open", "high", "low", "close", "volume"]].dropna().tail(bars).reset_index(drop=True)
        except Exception:
            pass

    # 2. กรณีมีไฟล์บันทึกราคาจริงในเครื่อง
    json_path = os.path.join(os.path.dirname(__file__), "rice_price_th.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if clean_sym in data and len(data[clean_sym]) > 10:
                    df = pd.DataFrame(data[clean_sym])
                    df["time"] = (pd.to_datetime(df["date"]).astype("int64") // 10**9)
                    return df[["time", "open", "high", "low", "close", "volume"]].sort_values("time").tail(bars).reset_index(drop=True)
        except Exception:
            pass

    # 3. คำนวณแท่งเทียนจำลองอิงตามราคาฐานสถิติจริง (Daily OHLCV)
    spec = RICE_SPECS.get(clean_sym, {"base": 550.0, "vol": 8.0})
    base_price = spec["base"]
    vol = spec["vol"]

    now_ts = int(time.time())
    day_seconds = 86400
    times = []
    curr = now_ts
    while len(times) < bars:
        weekday = pd.to_datetime(curr, unit='s').weekday()
        if weekday < 5:
            times.append(curr)
        curr -= day_seconds
    times = sorted(times)

    np.random.seed(abs(hash(clean_sym)) % (10**8))
    trend = np.sin(np.linspace(0, 4 * np.pi, bars)) * (base_price * 0.07)
    daily_noise = np.cumsum(np.random.normal(0, vol * 0.4, bars))
    close_prices = np.round(base_price + trend + daily_noise, 2)

    opens = np.roll(close_prices, 1)
    opens[0] = close_prices[0]
    highs = np.round(np.maximum(opens, close_prices) + np.abs(np.random.normal(vol * 0.45, vol * 0.25, bars)), 2)
    lows = np.round(np.minimum(opens, close_prices) - np.abs(np.random.normal(vol * 0.45, vol * 0.25, bars)), 2)
    volumes = np.random.randint(400, 3500, size=bars)

    return pd.DataFrame({
        "time": times,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": close_prices,
        "volume": volumes.astype(float)
    })