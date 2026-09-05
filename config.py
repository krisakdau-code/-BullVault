# config.py

# res  = resolution ที่ขอจาก Bitkub  (1, 5, 15, 60, 240, 1D)
# rule = pandas resample rule        (None = ใช้ตรง ๆ ไม่ต้องรวมแท่ง)
# sec  = วินาทีต่อ 1 แท่ง "ปลายทาง"  (ใช้คำนวณว่าต้องขอข้อมูลย้อนไปกี่วินาที)

TF_MAP = {
    # --- Minutes ---
    "1m":  {"res": "1",   "rule": None,     "sec": 60},
    "2m":  {"res": "1",   "rule": "2min",   "sec": 120},
    "3m":  {"res": "1",   "rule": "3min",   "sec": 180},
    "5m":  {"res": "5",   "rule": None,     "sec": 300},
    "10m": {"res": "5",   "rule": "10min",  "sec": 600},
    "15m": {"res": "15",  "rule": None,     "sec": 900},
    "30m": {"res": "15",  "rule": "30min",  "sec": 1800},
    "45m": {"res": "15",  "rule": "45min",  "sec": 2700},

    # --- Hours ---
    "1h":  {"res": "60",  "rule": None,     "sec": 3600},
    "2h":  {"res": "60",  "rule": "2h",     "sec": 7200},
    "3h":  {"res": "60",  "rule": "3h",     "sec": 10800},
    "4h":  {"res": "240", "rule": None,     "sec": 14400},

    # --- Days / Weeks ---
    "1d":  {"res": "240", "rule": "1D",     "sec": 86400},
    "3d":  {"res": "1D",  "rule": "3D",     "sec": 259200},
    "1w":  {"res": "1D",  "rule": "W-MON",  "sec": 604800},

    # --- Months / Years ---
    "1M":  {"res": "1D",  "rule": "MS",     "sec": 2629800},
    "3M":  {"res": "1D",  "rule": "QS",     "sec": 7889400},
    "6M":  {"res": "1D",  "rule": "2QS",    "sec": 15778800},
    "12M": {"res": "1D",  "rule": "YS",     "sec": 31557600},
}

# วินาทีต่อ 1 แท่งของ resolution "ต้นทาง" — ใช้กันขอข้อมูลก้อนใหญ่เกิน
RES_SEC = {"1": 60, "5": 300, "15": 900, "60": 3600, "240": 14400, "1D": 86400}

MAX_SRC_BARS    = 20000            # เพดานแท่งดิบต่อ 1 request
MAX_HISTORY_SEC = 86400 * 365 * 9  # Bitkub มีข้อมูลย้อนถึง ~ปี 2017

DEFAULT_TF   = "1h"
DEFAULT_BARS = 400
TF_LIST      = list(TF_MAP.keys())