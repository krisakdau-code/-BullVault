# diamond.py — Diamond Armor V11.3 (Infinite RSI + Explosion)
import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def _cross_up(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a > b) & (a.shift(1) <= b.shift(1))


def _cross_dn(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a < b) & (a.shift(1) >= b.shift(1))


def diamond_armor(
    df: pd.DataFrame,
    f_len: int = 7,
    s_len: int = 13,
    t_len: int = 45,
    min_tp_pct: float = 3.0,
    warn_pct: float = 3.0,
    danger_pct: float = 7.0,
):
    """คืน (df ที่เติมคอลัมน์สัญญาณ, dict สรุปสำหรับ Dashboard)"""
    d = df.copy().reset_index(drop=True)

    # กันกรณีข้อมูลน้อยเกินไป
    if len(d) < max(t_len, 30) + 5:
        for col in ["buy", "sell", "tp", "warn", "danger", "early", "is_long"]:
            d[col] = False
        d["ema_f"] = d["ema_s"] = d["ema_t"] = d["close"]
        d["rsi"] = 50.0
        d["rsi_scaled"] = d["close"]
        d["hi_price"] = 0.0
        d["explosion"] = "CHOP / WAIT"
        empty = dict(explosion="CHOP / WAIT", win_rate=0.0, net=0.0, profit=0.0,
                     loss=0.0, tp_count=0, holding=False, early=False,
                     just_sold=False, trailing_high=0.0, rsi=50.0, trades=0)
        return d, empty

    c, h, l = d["close"], d["high"], d["low"]

    d["ema_f"] = ema(c, f_len)
    d["ema_s"] = ema(c, s_len)
    d["ema_t"] = ema(c, t_len)
    d["rsi"] = rsi(c, 14)
    ema3 = ema(c, 3)

    cu = _cross_up(d["ema_f"], d["ema_s"])
    cd = _cross_dn(d["ema_f"], d["ema_s"])
    c_up_f = _cross_up(c, d["ema_f"])
    c_dn_3 = _cross_dn(c, ema3)

    d["rsi_scaled"] = ema(c, 20) * (1 + (d["rsi"] - 50) / 150)

    d["early"] = (
        (l == l.rolling(5).min())
        & (d["rsi"] > d["rsi"].rolling(5).min().shift(1))
        & (d["rsi"] < 40)
    ).fillna(False)

    rng = h - l
    is_sqz = (rng.rolling(10).mean() < rng.rolling(30).mean()) & (
        (d["ema_f"] - d["ema_s"]).abs() < c * 0.005
    )
    is_boom = (d["rsi"] > 60) & (c > d["ema_f"]) & ((c - c.shift(10)) > 0)
    d["explosion"] = np.where(is_boom, "BOOM! 🚀",
                     np.where(is_sqz, "SQUEEZE 💎", "CHOP / WAIT"))

    n = len(d)
    buy = np.zeros(n, bool); sell = np.zeros(n, bool); tp = np.zeros(n, bool)
    warn = np.zeros(n, bool); danger = np.zeros(n, bool)
    hi_arr = np.zeros(n); long_arr = np.zeros(n, bool)

    is_long = just_sold = False
    hi_price = entry_p = 0.0
    tp_count = 0
    p_total = l_total = 0.0
    w_count = ls_count = 0
    trades = []

    for i in range(n):
        px, hh = c.iat[i], h.iat[i]

        b = (cu.iat[i] and px > d["ema_t"].iat[i]) or (
            just_sold and c_up_f.iat[i] and px > d["ema_t"].iat[i]
        )
        if b:
            is_long, just_sold = True, False
            tp_count = 0
            entry_p = hi_price = px
            buy[i] = True

        if is_long:
            hi_price = max(hi_price, hh)

        pnl = (px - entry_p) / entry_p * 100 if is_long and entry_p else 0.0

        if is_long and pnl >= min_tp_pct and d["rsi"].iat[i] > 65 and c_dn_3.iat[i]:
            tp_count += 1
            tp[i] = True

        if is_long and cd.iat[i]:
            m = (px - entry_p) / entry_p * 100
            if m > 0:
                p_total += m; w_count += 1
            else:
                l_total += abs(m); ls_count += 1
            trades.append(m)
            is_long, just_sold = False, True
            hi_price = 0.0
            sell[i] = True

        if is_long and hi_price:
            if px < hi_price * (1 - danger_pct / 100):
                danger[i] = True
            elif px < hi_price * (1 - warn_pct / 100):
                warn[i] = True

        hi_arr[i], long_arr[i] = hi_price, is_long

    d["buy"], d["sell"], d["tp"] = buy, sell, tp
    d["warn"], d["danger"] = warn, danger
    d["hi_price"], d["is_long"] = hi_arr, long_arr

    total = w_count + ls_count
    stats = {
        "explosion": d["explosion"].iat[-1],
        "win_rate": (w_count * 100 / total) if total else 0.0,
        "net": p_total - l_total,
        "profit": p_total,
        "loss": l_total,
        "tp_count": tp_count,
        "holding": is_long,
        "early": bool(d["early"].iat[-1]),
        "just_sold": just_sold,
        "trailing_high": hi_price,
        "rsi": float(d["rsi"].iat[-1]),
        "trades": len(trades),
    }
    return d, stats