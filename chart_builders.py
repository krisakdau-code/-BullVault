# chart_builders.py — Full Engine: Synced Crosshair, Dynamic 3-Tab Settings & 4-Color MACD
import pandas as pd
import streamlit as st
import chart_theme as theme


def sanitize_markers(markers: list) -> list:
    if not markers:
        return []
    seen = set()
    cleaned = []
    sorted_markers = sorted(markers, key=lambda x: int(x.get("time", 0)))
    for m in sorted_markers:
        t = int(m.get("time", 0))
        if t <= 0 or t in seen:
            continue
        seen.add(t)
        m["time"] = t
        cleaned.append(m)
    return cleaned


def price_precision(df: pd.DataFrame) -> int:
    if df is None or df.empty or "close" not in df.columns:
        return 2
    p = float(df["close"].iloc[-1])
    if p >= 1000:
        return 2
    if p >= 10:
        return 3
    if p >= 0.1:
        return 5
    return 8


def min_move(df: pd.DataFrame) -> float:
    return 10 ** -price_precision(df)


def is_timeframe_visible(tf: str) -> bool:
    """ตรวจสอบแท็บ Visibility ว่าอนุญาตให้แสดงตัวชี้วัดใน Timeframe ปัจจุบันหรือไม่"""
    tf_str = str(tf).lower()
    if "s" in tf_str:
        return st.session_state.get("vis_sec", True)
    if "m" in tf_str and not "mo" in tf_str:
        return st.session_state.get("vis_min", True)
    if "h" in tf_str:
        return st.session_state.get("vis_hour", True)
    if "d" in tf_str:
        return st.session_state.get("vis_day", True)
    if "w" in tf_str or "mo" in tf_str:
        return st.session_state.get("vis_week_month", True)
    return True


def build_charts(df, symbol, tf, main_h, rsi_h, macd_h):
    if df is None or df.empty:
        return []

    d = df.copy()
    if hasattr(d.columns, "str"):
        d.columns = d.columns.astype(str).str.lower()
    d = d.loc[:, ~d.columns.duplicated()]

    if "time" not in d.columns:
        if isinstance(d.index, pd.DatetimeIndex) or d.index.name is not None:
            d = d.reset_index(drop=False)
            if "time" not in d.columns and len(d.columns) > 0:
                d = d.rename(columns={d.columns[0]: "time"})
        else:
            d["time"] = range(len(d))

    if pd.api.types.is_datetime64_any_dtype(d["time"]):
        d["time"] = (d["time"].astype("int64") // 10**9).astype("int64") + 25200
    else:
        d["time"] = pd.to_numeric(d["time"], errors="coerce").fillna(0).astype("int64") + 25200

    for col in ["open", "high", "low", "close", "volume"]:
        if col not in d.columns:
            d[col] = 100.0 if col == "volume" else 0.0
        else:
            d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0.0)

    # 1. คำนวณ RSI & RSI MA จากแท็บ Inputs
    r_len = int(st.session_state.get("rsi_len", 14))
    r_src = str(st.session_state.get("rsi_source", "close")).lower()
    src_series = d[r_src] if r_src in d.columns else d["close"]

    delta = src_series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / r_len, min_periods=r_len, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / r_len, min_periods=r_len, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    d["calc_rsi"] = 100.0 - (100.0 / (1.0 + rs))

    ma_type = st.session_state.get("rsi_ma_type", "SMA")
    ma_len = int(st.session_state.get("rsi_ma_len", 14))
    if ma_type == "EMA":
        d["calc_rsi_ma"] = d["calc_rsi"].ewm(span=ma_len, adjust=False).mean()
    else:
        d["calc_rsi_ma"] = d["calc_rsi"].rolling(ma_len).mean()

    # 2. คำนวณ MACD จากแท็บ Inputs
    m_fast = int(st.session_state.get("macd_fast_len", 12))
    m_slow = int(st.session_state.get("macd_slow_len", 26))
    m_sig  = int(st.session_state.get("macd_sig_len", 9))
    m_src  = str(st.session_state.get("macd_source", "close")).lower()
    m_series = d[m_src] if m_src in d.columns else d["close"]

    fast_ema = m_series.ewm(span=m_fast, adjust=False).mean()
    slow_ema = m_series.ewm(span=m_slow, adjust=False).mean()
    d["calc_macd"] = fast_ema - slow_ema
    d["calc_macd_sig"] = d["calc_macd"].ewm(span=m_sig, adjust=False).mean()
    d["calc_macd_hist"] = d["calc_macd"] - d["calc_macd_sig"]

    # 3. คำนวณเส้น EMA กราฟหลัก
    ema_f_len = int(st.session_state.get("ema_fast_len", 12))
    ema_s_len = int(st.session_state.get("ema_slow_len", 26))
    ema_t_len = int(st.session_state.get("ema_trend_len", 200))
    d["calc_ema_fast"] = d["close"].ewm(span=ema_f_len, adjust=False).mean()
    d["calc_ema_slow"] = d["close"].ewm(span=ema_s_len, adjust=False).mean()
    d["calc_ema_trend"] = d["close"].ewm(span=ema_t_len, adjust=False).mean()

    records = d.to_dict("records")

    # TimeScale ซิงค์การลากและซูมเวลา
    pane_ts = {
        "visible": True,
        "timeVisible": True,
        "secondsVisible": tf in ("1m", "3m", "5m"),
        "borderColor": theme.BORDER_COLOR,
        "borderVisible": True,
        "fixLeftEdge": False,
        "rightOffset": 6,
    }

    # เส้น Crosshair ไข่ปลาเชื่อมทะลุทั้ง 3 หน้าต่าง
    crosshair_synced = {
        "mode": 1,
        "vertLine": {
            "visible": True,
            "style": 3,
            "width": 1,
            "color": "rgba(255, 255, 255, 0.40)",
            "labelVisible": True,
            "labelBackgroundColor": theme.BORDER_COLOR,
        },
        "horzLine": {
            "visible": True,
            "style": 3,
            "width": 1,
            "color": "rgba(255, 255, 255, 0.40)",
            "labelVisible": True,
            "labelBackgroundColor": theme.BORDER_COLOR,
        },
    }

    base_chart = {
        "layout": {
            "background": {"type": "solid", "color": theme.CHART_BG},
            "textColor": theme.TEXT_COLOR,
            "fontSize": 11,
        },
        "grid": {
            "vertLines": {"color": theme.GRID_COLOR, "style": 1},
            "horzLines": {"color": theme.GRID_COLOR, "style": 1},
        },
        "crosshair": crosshair_synced,
        "rightPriceScale": {
            "autoScale": True,
            "borderColor": theme.BORDER_COLOR,
            "borderVisible": True,
            "scaleMargins": {"top": theme.PRICE_SCALE_TOP, "bottom": theme.PRICE_SCALE_BTM},
            "mode": 0,
        },
        "overlayPriceScales": {
            "scaleMargins": {"top": theme.VOL_TOP_MARGIN, "bottom": 0.0},
        },
        "timeScale": pane_ts,
        # ✅ เปิดให้คลิกลากแกนราคาขวามือเพื่อยืด-หดแนวตั้งได้ทุกกราฟ (ทั้ง Main, RSI, MACD)
        "handleScale": {
            "axisPressedMouseMove": True,
            "mouseWheel": True,
            "pinch": True,
        },
        "handleScroll": {
            "mouseWheel": True,
            "pressedMouseMove": True,
            "horzTouchDrag": True,
            "vertTouchDrag": True,
        },
    }

    # แท่งเทียนหลัก
    candles = [
        {
            "time": int(r["time"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
        }
        for r in records if r["time"] > 0
    ]

    price_series = [{
        "type": "Candlestick",
        "data": candles,
        "options": {
            "upColor": theme.CANDLE_UP,
            "downColor": theme.CANDLE_DOWN,
            "borderVisible": True,
            "borderUpColor": theme.CANDLE_UP,
            "borderDownColor": theme.CANDLE_DOWN,
            "wickUpColor": theme.CANDLE_UP,
            "wickDownColor": theme.CANDLE_DOWN,
            "priceScaleId": "right",
            "priceFormat": {
                "type": "price",
                "precision": price_precision(d),
                "minMove": min_move(d),
            },
        },
    }]

    # เส้น EMA กราฟหลัก
    fast_data = [{"time": int(r["time"]), "value": float(r["calc_ema_fast"])} for r in records if pd.notna(r.get("calc_ema_fast")) and r["time"] > 0]
    price_series.append({
        "type": "Line", "data": fast_data,
        "options": {"color": theme.EMA_FAST_COLOR, "lineWidth": 2, "priceLineVisible": False, "lastValueVisible": False},
    })

    slow_data = [{"time": int(r["time"]), "value": float(r["calc_ema_slow"])} for r in records if pd.notna(r.get("calc_ema_slow")) and r["time"] > 0]
    price_series.append({
        "type": "Line", "data": slow_data,
        "options": {"color": theme.EMA_SLOW_COLOR, "lineWidth": 2, "priceLineVisible": False, "lastValueVisible": False},
    })

    trend_data = [{"time": int(r["time"]), "value": float(r["calc_ema_trend"])} for r in records if pd.notna(r.get("calc_ema_trend")) and r["time"] > 0]
    price_series.append({
        "type": "Line", "data": trend_data,
        "options": {"color": theme.EMA_TREND_COLOR, "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False},
    })

    # Volume Overlay ชิดขอบล่าง
    if theme.SHOW_VOLUME:
        vol = [
            {
                "time": int(r["time"]),
                "value": float(r.get("volume", 0)),
                "color": theme.VOL_UP if float(r.get("close", 0)) >= float(r.get("open", 0)) else theme.VOL_DOWN,
            }
            for r in records if pd.notna(r.get("volume")) and r["time"] > 0
        ]
        price_series.append({
            "type": "Histogram",
            "data": vol,
            "options": {
                "priceFormat": {"type": "volume"},
                "priceScaleId": "",
                "priceLineVisible": False,
                "lastValueVisible": False,
            },
        })

    # กราฟ RSI (14) พร้อม RSI MA และ Bands
    def make_rsi_pane():
        rsi_col = st.session_state.get("rsi_col_line", theme.RSI_LINE_COLOR)
        rsi_lw = int(st.session_state.get("rsi_lw_line", 2))
        u_band = float(st.session_state.get("rsi_band_70", 70.0))
        m_band = float(st.session_state.get("rsi_band_50", 50.0))
        l_band = float(st.session_state.get("rsi_band_30", 30.0))

        rsi_data = [{"time": int(r["time"]), "value": float(r["calc_rsi"])} for r in records if pd.notna(r.get("calc_rsi")) and r["time"] > 0]
        mk = lambda v: [{"time": int(r["time"]), "value": v} for r in records if r["time"] > 0]

        series_list = [
            {"type": "Line", "data": mk(u_band), "options": {"color": "rgba(242,54,69,0.5)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
            {"type": "Line", "data": mk(m_band), "options": {"color": "rgba(120,123,134,0.25)", "lineWidth": 1, "lineStyle": 3, "priceLineVisible": False, "lastValueVisible": False}},
            {"type": "Line", "data": mk(l_band), "options": {"color": "rgba(8,153,129,0.5)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
            {"type": "Line", "data": rsi_data, "options": {"color": rsi_col, "lineWidth": rsi_lw, "priceLineVisible": True}},
        ]

        if st.session_state.get("rsi_show_ma", True):
            ma_col = st.session_state.get("rsi_col_ma", theme.RSI_MA_COLOR)
            ma_data = [{"time": int(r["time"]), "value": float(r["calc_rsi_ma"])} for r in records if pd.notna(r.get("calc_rsi_ma")) and r["time"] > 0]
            series_list.append({"type": "Line", "data": ma_data, "options": {"color": ma_col, "lineWidth": 1, "priceLineVisible": False, "lastValueVisible": False}})

        return {
            "chart": {
                **base_chart,
                "height": rsi_h,
                "timeScale": pane_ts,
                "rightPriceScale": {**base_chart["rightPriceScale"], "scaleMargins": {"top": theme.RSI_TOP_MARGIN, "bottom": theme.RSI_BTM_MARGIN}},
                "watermark": {"visible": True, "text": f"RSI ({r_len})", "fontSize": 18, "color": theme.RSI_TITLE_COLOR, "horzAlign": "left", "vertAlign": "top"},
            },
            "series": series_list,
        }

    # กราฟ MACD (4-Color Histogram & Zero Line)
    def make_macd_pane():
        m_col = st.session_state.get("macd_col_line", theme.MACD_LINE_COLOR)
        m_lw = int(st.session_state.get("macd_lw_line", 2))
        s_col = st.session_state.get("macd_col_sig", theme.MACD_SIG_COLOR)
        s_lw = int(st.session_state.get("macd_lw_sig", 2))

        c0 = st.session_state.get("macd_col_h0", theme.MACD_HIST_H0)
        c1 = st.session_state.get("macd_col_h1", theme.MACD_HIST_H1)
        c2 = st.session_state.get("macd_col_h2", theme.MACD_HIST_H2)
        c3 = st.session_state.get("macd_col_h3", theme.MACD_HIST_H3)

        macd_data = [{"time": int(r["time"]), "value": float(r["calc_macd"])} for r in records if pd.notna(r.get("calc_macd")) and r["time"] > 0]
        sig_data  = [{"time": int(r["time"]), "value": float(r["calc_macd_sig"])} for r in records if pd.notna(r.get("calc_macd_sig")) and r["time"] > 0]

        hist_data = []
        for i, r in enumerate(records):
            if r["time"] <= 0 or pd.isna(r.get("calc_macd_hist")):
                continue
            val = float(r["calc_macd_hist"])
            prev = float(records[i - 1]["calc_macd_hist"]) if i > 0 and pd.notna(records[i - 1].get("calc_macd_hist")) else val
            if val >= 0:
                col = c0 if val >= prev else c1
            else:
                col = c2 if val <= prev else c3
            hist_data.append({"time": int(r["time"]), "value": val, "color": col})

        series_list = []
        # ✅ ผูก Histogram เข้ากับแกนขวา (right) ใช้รูปแบบ price ปกติ เพื่อให้ขยาย-หดพร้อมเส้น MACD ได้
        if st.session_state.get("macd_show_hist", True):
            series_list.append({
                "type": "Histogram",
                "data": hist_data,
                "options": {
                    "priceScaleId": "right",
                    "priceFormat": {"type": "price", "precision": 2, "minMove": 0.01},
                    "priceLineVisible": False,
                    "lastValueVisible": False,
                }
            })

        if st.session_state.get("macd_show_zero", True):
            mk_zero = [{"time": int(r["time"]), "value": 0.0} for r in records if r["time"] > 0]
            series_list.append({
                "type": "Line",
                "data": mk_zero,
                "options": {
                    "color": theme.MACD_ZERO_COLOR,
                    "lineWidth": 1,
                    "lineStyle": 2,
                    "priceScaleId": "right",
                    "priceLineVisible": False,
                    "lastValueVisible": False,
                }
            })

        # ✅ ผูกเส้น MACD และ Signal เข้าแกน right ชัดเจน
        series_list.append({
            "type": "Line",
            "data": macd_data,
            "options": {
                "color": m_col,
                "lineWidth": m_lw,
                "priceScaleId": "right",
                "priceFormat": {"type": "price", "precision": 2, "minMove": 0.01},
                "priceLineVisible": False,
            }
        })
        series_list.append({
            "type": "Line",
            "data": sig_data,
            "options": {
                "color": s_col,
                "lineWidth": s_lw,
                "priceScaleId": "right",
                "priceFormat": {"type": "price", "precision": 2, "minMove": 0.01},
                "priceLineVisible": False,
            }
        })

        return {
            "chart": {
                **base_chart,
                "height": macd_h,
                "timeScale": pane_ts,
                "rightPriceScale": {
                    **base_chart["rightPriceScale"],
                    "autoScale": True,
                    "scaleMargins": {"top": theme.MACD_TOP_MARGIN, "bottom": theme.MACD_BTM_MARGIN},
                },
                "watermark": {
                    "visible": True,
                    "text": f"MACD ({m_fast}, {m_slow}, {m_sig})",
                    "fontSize": 18,
                    "color": theme.MACD_TITLE_COLOR,
                    "horzAlign": "left",
                    "vertAlign": "top",
                },
            },
            "series": series_list,
        }

    charts = [{
        "chart": {
            **base_chart,
            "height": main_h,
            "timeScale": pane_ts,
            "watermark": {
                "visible": True,
                "text": f"{symbol} · {tf}",
                "fontSize": 34,
                "color": "rgba(255,255,255,0.05)",
                "horzAlign": "center",
                "vertAlign": "center",
            },
        },
        "series": price_series,
    }]

    if is_timeframe_visible(tf):
        charts.append(make_rsi_pane())
        charts.append(make_macd_pane())

    return charts