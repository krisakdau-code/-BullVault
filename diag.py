# diag.py
import time, json, requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
H = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
    "Referer": "https://www.bitkub.com/",
    "Origin": "https://www.bitkub.com",
}

to_ts  = int(time.time())
frm_ts = to_ts - 86400 * 120

TESTS = [
    ("A) history BTC_THB",  "https://api.bitkub.com/tradingview/history",
     {"symbol": "BTC_THB", "resolution": "1D", "from": frm_ts, "to": to_ts}),
    ("B) history THB_BTC",  "https://api.bitkub.com/tradingview/history",
     {"symbol": "THB_BTC", "resolution": "1D", "from": frm_ts, "to": to_ts}),
    ("C) history res=D",    "https://api.bitkub.com/tradingview/history",
     {"symbol": "BTC_THB", "resolution": "D", "from": frm_ts, "to": to_ts}),
    ("D) v3 tradingview",   "https://api.bitkub.com/api/v3/market/tradingview",
     {"symbol": "BTC_THB", "resolution": "1D", "from": frm_ts, "to": to_ts}),
    ("E) v3 ticker",        "https://api.bitkub.com/api/v3/market/ticker", {}),
    ("F) v1 ticker",        "https://api.bitkub.com/api/market/ticker", {}),
]

for name, url, params in TESTS:
    try:
        r = requests.get(url, params=params, headers=H, timeout=20)
        body = r.text[:220].replace("\n", " ")
        print(f"\n{name}\n  status : {r.status_code}")
        print(f"  type   : {r.headers.get('content-type','?')}")
        print(f"  body   : {body}")
    except Exception as e:
        print(f"\n{name}\n  ❌ {type(e).__name__}: {e}")