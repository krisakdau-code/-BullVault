# technicals.py — Technical Indicators & Calculation Engine
import datetime
import numpy as np
import pandas as pd
import streamlit as st

UP, DOWN = "#26a69a", "#ef5350"

def rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)

def diamond_armor(df: pd.DataFrame, fast=7, slow=13, trend=45, rsi_len=14, macd_f=12, macd_s=26, macd_sig=9, warn_pct=3.0, danger_pct=7.0):
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["ema_trend"] = df["close"].ewm(span=trend, adjust=False).mean()
    df["rsi"] = rsi_wilder(df["close"], rsi_len)
    df["ema12"] = df["close"].ewm(span=macd_f, adjust=False).mean()
    df["ema26"] = df["close"].ewm(span=macd_s, adjust=False).mean()
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_sig"] = df["macd"].ewm(span=macd_sig, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    up_cross = (df.ema_fast > df.ema_slow) & (df.ema_fast.shift() <= df.ema_slow.shift())
    dn_cross = (df.ema_fast < df.ema_slow) & (df.ema_fast.shift() >= df.ema_slow.shift())
    df["signal"] = np.select([up_cross & (df.rsi > 45), dn_cross & (df.rsi < 55)], ["BUY", "SELL ALL"], default="")

    df["dist_trend_pct"] = ((df["close"] - df["ema_trend"]) / df["ema_trend"]) * 100.0
    df["dot_warn"] = np.where(df["dist_trend_pct"] >= danger_pct, "RED",
                     np.where(df["dist_trend_pct"] >= warn_pct, "ORANGE", ""))

    avg_vol = df["volume"].rolling(20).mean().fillna(df["volume"])
    df["star"] = (df["signal"] == "BUY") & (df["volume"] > avg_vol * 1.15) & (df["close"] > df["ema_trend"])

    last, prev = df.iloc[-1], df.iloc[-2]
    stats = {
        "price": float(last.close), "change_pct": float((last.close / prev.close - 1) * 100) if prev.close else 0.0,
        "rsi": float(last.rsi), "trend": "UP" if last.ema_fast > last.ema_slow else "DOWN",
        "buys": int((df.signal == "BUY").sum()), "sells": int((df.signal == "SELL ALL").sum()), "bars": len(df),
        "dist_trend": float(last.dist_trend_pct) if "dist_trend_pct" in last else 0.0
    }
    return df, stats

def safe_ret(df: pd.DataFrame, days: int) -> float:
    try:
        if df is None or df.empty or len(df) < 2: return 0.0
        now_p = float(df["close"].iloc[-1])
        past_p = float(df["close"].iloc[-1 - days]) if len(df) > days else float(df["close"].iloc[0])
        return float(((now_p - past_p) / past_p) * 100.0) if past_p > 0 else 0.0
    except Exception:
        return 0.0

def fetch_market_analytics(df: pd.DataFrame) -> dict:
    try:
        if df is None or df.empty or len(df) < 2: return {}
        now_p = float(df["close"].iloc[-1])
        vol_30d = float(df.tail(30)["volume"].mean()) if "volume" in df.columns else 0.0
        jan1 = int(datetime.datetime(datetime.datetime.now().year, 1, 1).timestamp())
        ytd_df = df[df["time"] >= jan1] if "time" in df.columns else pd.DataFrame()
        rytd = float(((now_p / float(ytd_df.iloc[0]["close"])) - 1.0) * 100.0) if not ytd_df.empty and float(ytd_df.iloc[0]["close"]) > 0 else safe_ret(df, 30)
        
        tail_52w = df.tail(365)
        low_52w = float(tail_52w["low"].min()) if "low" in tail_52w.columns else now_p * 0.9
        high_52w = float(tail_52w["high"].max()) if "high" in tail_52w.columns else now_p * 1.1

        return {
            "vol_30d_avg": vol_30d, "1W": safe_ret(df, 7), "1M": safe_ret(df, 30),
            "3M": safe_ret(df, 90), "6M": safe_ret(df, 180), "YTD": rytd, "1Y": safe_ret(df, 365),
            "low_52w": low_52w, "high_52w": high_52w
        }
    except Exception:
        return {}

default_tech_data = {
    "vol_30d_avg": 0.0, "1W": 0.0, "1M": 0.0, "3M": 0.0, "6M": 0.0, "YTD": 0.0, "1Y": 0.0,
    "low_52w": 0.0, "high_52w": 0.0,
    "summary": {"label": "N/A", "color": "#9aa0a6", "angle": 0, "buy": 0, "neutral": 0, "sell": 0},
    "osc": {"label": "N/A", "color": "#9aa0a6", "angle": 0, "buy": 0, "neutral": 0, "sell": 0, "rows": []},
    "ma": {"label": "N/A", "color": "#9aa0a6", "angle": 0, "buy": 0, "neutral": 0, "sell": 0, "rows": []},
    "pivots": {
        "Classic": {"P": 0.0, "S1": 0.0, "R1": 0.0, "S2": 0.0, "R2": 0.0},
        "Fibonacci": {"P": 0.0, "S1": 0.0, "R1": 0.0, "S2": 0.0, "R2": 0.0},
        "Camarilla": {"P": 0.0, "S1": 0.0, "R1": 0.0, "S2": 0.0, "R2": 0.0},
    }
}

def compute_full_technicals(df: pd.DataFrame) -> dict:
    try:
        if df is None or df.empty: return default_tech_data

        if "time" not in df.columns:
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index().rename(columns={"index": "time"})
            else:
                return default_tech_data

        required_cols = ["close", "high", "low", "volume"]
        for col in required_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                return default_tech_data
        
        df = df.dropna(subset=required_cols).sort_values("time").reset_index(drop=True)
        if df.empty: return default_tech_data

        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        last_p = float(close.iloc[-1])

        ma_rows = []
        ma_buy, ma_sell, ma_neutral = 0, 0, 0
        periods = [10, 20, 30, 50, 100, 200]
        for p in periods:
            if len(df) >= p:
                ema_v = float(close.ewm(span=p, adjust=False, min_periods=1).mean().iloc[-1])
                act_e = "มีแรงซื้อ" if last_p > ema_v else ("มีแรงขาย" if last_p < ema_v else "เป็นกลาง")
                if act_e == "มีแรงซื้อ": ma_buy += 1
                elif act_e == "มีแรงขาย": ma_sell += 1
                else: ma_neutral += 1
                ma_rows.append({"name": f"ค่าเฉลี่ยเคลื่อนที่เอ็กซ์โปเนนเชียล ({p})", "value": f"{ema_v:,.4f}" if last_p < 10 else f"{ema_v:,.2f}", "action": act_e})

                sma_v = float(close.rolling(p, min_periods=1).mean().iloc[-1])
                act_s = "มีแรงซื้อ" if last_p > sma_v else ("มีแรงขาย" if last_p < sma_v else "เป็นกลาง")
                if act_s == "มีแรงซื้อ": ma_buy += 1
                elif act_s == "มีแรงขาย": ma_sell += 1
                else: ma_neutral += 1
                ma_rows.append({"name": f"ค่าเฉลี่ยเคลื่อนที่แบบง่าย ({p})", "value": f"{sma_v:,.4f}" if last_p < 10 else f"{sma_v:,.2f}", "action": act_s})

        h26, l26 = high.rolling(26, min_periods=1).max(), low.rolling(26, min_periods=1).min()
        ichimoku = float(((h26 + l26) / 2).iloc[-1])
        act_ichi = "มีแรงซื้อ" if last_p > ichimoku else ("มีแรงขาย" if last_p < ichimoku else "เป็นกลาง")
        if act_ichi == "มีแรงซื้อ": ma_buy += 1
        elif act_ichi == "มีแรงขาย": ma_sell += 1
        else: ma_neutral += 1
        ma_rows.append({"name": "เส้น Ichimoku Base Line (9, 26, 52, 26)", "value": f"{ichimoku:,.4f}" if last_p < 10 else f"{ichimoku:,.2f}", "action": act_ichi})

        vwma = float(((close * vol).rolling(20, min_periods=1).sum() / vol.rolling(20, min_periods=1).sum().replace(0, np.nan)).iloc[-1])
        act_vwma = "มีแรงซื้อ" if last_p > vwma else ("มีแรงขาย" if last_p < vwma else "เป็นกลาง")
        if act_vwma == "มีแรงซื้อ": ma_buy += 1
        elif act_vwma == "มีแรงขาย": ma_sell += 1
        else: ma_neutral += 1
        ma_rows.append({"name": "เส้นค่าเฉลี่ยเคลื่อนที่วัดจากปริมาณ (20)", "value": f"{vwma:,.4f}" if last_p < 10 else f"{vwma:,.2f}", "action": act_vwma})

        wma_half = close.rolling(4, min_periods=1).mean() * 2
        wma_full = close.rolling(9, min_periods=1).mean()
        hma = float((wma_half - wma_full).rolling(3, min_periods=1).mean().iloc[-1])
        act_hma = "มีแรงซื้อ" if last_p > hma else ("มีแรงขาย" if last_p < hma else "เป็นกลาง")
        if act_hma == "มีแรงซื้อ": ma_buy += 1
        elif act_hma == "มีแรงขาย": ma_sell += 1
        else: ma_neutral += 1
        ma_rows.append({"name": "ค่าเฉลี่ยเคลื่อนที่ฮัล (9)", "value": f"{hma:,.4f}" if last_p < 10 else f"{hma:,.2f}", "action": act_hma})

        osc_rows = []
        osc_buy, osc_sell, osc_neutral = 0, 0, 0

        rsi_val = float(rsi_wilder(close, 14).iloc[-1])
        act_rsi = "มีแรงขาย" if rsi_val > 70 else ("มีแรงซื้อ" if rsi_val < 30 else "เป็นกลาง")
        if act_rsi == "มีแรงซื้อ": osc_buy += 1
        elif act_rsi == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Relative Strength Index (14)", "value": f"{rsi_val:.4f}", "action": act_rsi})

        l14, h14 = low.rolling(14, min_periods=1).min(), high.rolling(14, min_periods=1).max()
        denom = (h14 - l14).replace(0, np.nan)
        stoch_k = float((((close - l14) / denom) * 100).rolling(3, min_periods=1).mean().iloc[-1])
        act_stoch = "มีแรงขาย" if stoch_k > 80 else ("มีแรงซื้อ" if stoch_k < 20 else "เป็นกลาง")
        if act_stoch == "มีแรงซื้อ": osc_buy += 1
        elif act_stoch == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Stochastic %K (14, 3, 3)", "value": f"{stoch_k:.4f}", "action": act_stoch})

        tp = (high + low + close) / 3
        sma_tp = tp.rolling(20, min_periods=1).mean()
        mad = (tp - sma_tp).abs().rolling(20, min_periods=1).mean().replace(0, np.nan)
        cci_v = float(((tp - sma_tp) / (0.015 * mad)).iloc[-1])
        act_cci = "มีแรงขาย" if cci_v > 100 else ("มีแรงซื้อ" if cci_v < -100 else "เป็นกลาง")
        if act_cci == "มีแรงซื้อ": osc_buy += 1
        elif act_cci == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "ดัชนีแชนแนลสินค้าโภคภัณฑ์(20)", "value": f"{cci_v:.4f}", "action": act_cci})

        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14, min_periods=1).mean().replace(0, np.nan)
        up_m, dn_m = high.diff(), -low.diff()
        p_dm = up_m.where((up_m > dn_m) & (up_m > 0), 0.0).rolling(14, min_periods=1).mean()
        m_dm = dn_m.where((dn_m > up_m) & (dn_m > 0), 0.0).rolling(14, min_periods=1).mean()
        p_di = 100 * (p_dm / atr)
        m_di = 100 * (m_dm / atr)
        dx = (100 * (p_di - m_di).abs() / (p_di + m_di).replace(0, np.nan)).fillna(0)
        adx_v = float(dx.rolling(14, min_periods=1).mean().iloc[-1])
        act_adx = "มีแรงซื้อ" if (adx_v > 25 and p_di.iloc[-1] > m_di.iloc[-1]) else ("มีแรงขาย" if (adx_v > 25 and m_di.iloc[-1] > p_di.iloc[-1]) else "เป็นกลาง")
        if act_adx == "มีแรงซื้อ": osc_buy += 1
        elif act_adx == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Average Directional Index (14)", "value": f"{adx_v:.4f}", "action": act_adx})

        med_p = (high + low) / 2
        ao_v = float((med_p.rolling(5, min_periods=1).mean() - med_p.rolling(34, min_periods=1).mean()).iloc[-1])
        act_ao = "มีแรงซื้อ" if ao_v > 0 else "มีแรงขาย"
        if act_ao == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "ตัววัดการแกว่งที่ยอดเยี่ยม", "value": f"{ao_v:.4f}", "action": act_ao})

        mom_v = float(close.diff(10).iloc[-1])
        act_mom = "มีแรงซื้อ" if mom_v > 0 else "มีแรงขาย"
        if act_mom == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "โมเมนตัม (10)", "value": f"{mom_v:.4f}", "action": act_mom})

        macd_l = float((close.ewm(span=12, adjust=False, min_periods=1).mean() - close.ewm(span=26, adjust=False, min_periods=1).mean()).iloc[-1])
        macd_s = float(pd.Series(close.ewm(span=12, adjust=False, min_periods=1).mean() - close.ewm(span=26, adjust=False, min_periods=1).mean()).ewm(span=9, adjust=False, min_periods=1).mean().iloc[-1])
        act_macd = "มีแรงซื้อ" if macd_l > macd_s else "มีแรงขาย"
        if act_macd == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "ระดับ MACD (12, 26)", "value": f"{macd_l:.4f}", "action": act_macd})

        rsi_series = rsi_wilder(close, 14)
        rsi_l14, rsi_h14 = rsi_series.rolling(14, min_periods=1).min(), rsi_series.rolling(14, min_periods=1).max()
        stoch_rsi = float((((rsi_series - rsi_l14) / (rsi_h14 - rsi_l14).replace(0, np.nan)) * 100).rolling(3, min_periods=1).mean().iloc[-1])
        act_srsi = "มีแรงขาย" if stoch_rsi > 80 else ("มีแรงซื้อ" if stoch_rsi < 20 else "เป็นกลาง")
        if act_srsi == "มีแรงซื้อ": osc_buy += 1
        elif act_srsi == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Stochastic RSI Fast (3, 3, 14, 14)", "value": f"{stoch_rsi:.4f}", "action": act_srsi})

        wr_v = float((((h14 - close) / denom) * -100).iloc[-1])
        act_wr = "มีแรงขาย" if wr_v > -20 else ("มีแรงซื้อ" if wr_v < -80 else "เป็นกลาง")
        if act_wr == "มีแรงซื้อ": osc_buy += 1
        elif act_wr == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Williams Percent Range (14)", "value": f"{wr_v:.4f}", "action": act_wr})

        ema13 = close.ewm(span=13, adjust=False, min_periods=1).mean()
        bbp = float((high.iloc[-1] - ema13.iloc[-1]) + (low.iloc[-1] - ema13.iloc[-1]))
        act_bbp = "มีแรงซื้อ" if bbp > 0 else "มีแรงขาย"
        if act_bbp == "มีแรงซื้อ": osc_buy += 1
        else: osc_sell += 1
        osc_rows.append({"name": "พลังของตลาดขาขึ้นขาลง", "value": f"{bbp:.4f}", "action": act_bbp})

        bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
        tr_uo = pd.concat([high, close.shift()], axis=1).max(axis=1) - pd.concat([low, close.shift()], axis=1).min(axis=1)
        avg7 = (bp.rolling(7, min_periods=1).sum() / tr_uo.rolling(7, min_periods=1).sum().replace(0, np.nan))
        avg14 = (bp.rolling(14, min_periods=1).sum() / tr_uo.rolling(14, min_periods=1).sum().replace(0, np.nan))
        avg28 = (bp.rolling(28, min_periods=1).sum() / tr_uo.rolling(28, min_periods=1).sum().replace(0, np.nan))
        uo = float((100 * (4 * avg7 + 2 * avg14 + avg28) / 7).iloc[-1])
        act_uo = "มีแรงขาย" if uo > 70 else ("มีแรงซื้อ" if uo < 30 else "เป็นกลาง")
        if act_uo == "มีแรงซื้อ": osc_buy += 1
        elif act_uo == "มีแรงขาย": osc_sell += 1
        else: osc_neutral += 1
        osc_rows.append({"name": "Ultimate Oscillator (7, 14, 28)", "value": f"{uo:.4f}", "action": act_uo})

        tot_buy = osc_buy + ma_buy
        tot_sell = osc_sell + ma_sell
        tot_neu = osc_neutral + ma_neutral
        net_score = tot_buy - tot_sell

        if net_score >= 6:    sum_lbl, sum_col, sum_ang = "มีแรงซื้อรุนแรง", "#00e676", 55
        elif net_score >= 2:  sum_lbl, sum_col, sum_ang = "มีแรงซื้อ", "#26a69a", 30
        elif net_score <= -6: sum_lbl, sum_col, sum_ang = "มีแรงขายรุนแรง", "#d32f2f", -55
        elif net_score <= -2: sum_lbl, sum_col, sum_ang = "มีแรงขาย", "#ef5350", -30
        else:                 sum_lbl, sum_col, sum_ang = "เป็นกลาง", "#9aa0a6", 0

        osc_score = osc_buy - osc_sell
        osc_lbl, osc_col, osc_ang = ("มีแรงซื้อ", "#26a69a", 35) if osc_score > 1 else (("มีแรงขาย", "#ef5350", -35) if osc_score < -1 else ("เป็นกลาง", "#9aa0a6", 0))

        ma_score = ma_buy - ma_sell
        ma_lbl, ma_col, ma_ang = ("มีแรงซื้อ", "#26a69a", 35) if ma_score > 1 else (("มีแรงขาย", "#ef5350", -35) if ma_score < -1 else ("เป็นกลาง", "#9aa0a6", 0))

        prev_h, prev_l, prev_c = float(high.iloc[-2]), float(low.iloc[-2]), float(close.iloc[-2])
        pp = (prev_h + prev_l + prev_c) / 3
        pivots = {
            "Classic": {"P": pp, "S1": 2*pp - prev_h, "R1": 2*pp - prev_l, "S2": pp - (prev_h - prev_l), "R2": pp + (prev_h - prev_l)},
            "Fibonacci": {"P": pp, "S1": pp - 0.382*(prev_h - prev_l), "R1": pp + 0.382*(prev_h - prev_l), "S2": pp - 0.618*(prev_h - prev_l), "R2": pp + 0.618*(prev_h - prev_l)},
            "Camarilla": {"P": pp, "S1": prev_c - (prev_h - prev_l)*1.0833/12, "R1": prev_c + (prev_h - prev_l)*1.0833/12, "S2": prev_c - (prev_h - prev_l)*1.1666/12, "R2": prev_c + (prev_h - prev_l)*1.1666/12}
        }

        perf = fetch_market_analytics(df)

        return {
            **perf,
            "summary": {"label": sum_lbl, "color": sum_col, "angle": sum_ang, "buy": tot_buy, "neutral": tot_neu, "sell": tot_sell},
            "osc": {"label": osc_lbl, "color": osc_col, "angle": osc_ang, "buy": osc_buy, "neutral": osc_neutral, "sell": osc_sell, "rows": osc_rows},
            "ma": {"label": ma_lbl, "color": ma_col, "angle": ma_ang, "buy": ma_buy, "neutral": ma_neutral, "sell": ma_sell, "rows": ma_rows},
            "pivots": pivots
        }
    except Exception as e:
        st.error(f"🐞 เกิดข้อผิดพลาดในการคำนวณ Technicals: {e}")
        return default_tech_data