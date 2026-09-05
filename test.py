from data import fetch_ohlcv

for tf in ["1m", "1h", "1d", "1เดือน"]:
    d = fetch_ohlcv("PEPE_THB", tf)
    print(tf, len(d), d.close.iloc[-1] if len(d) else "ว่าง")