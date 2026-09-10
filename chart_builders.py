# chart_builders.py — Chart Assembly & Multi-pane Engine
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


def build_charts(df, symbol, tf, main_h, rsi_h, macd_h):
    if df is None or df.empty:
        return []

    show_r = st.session_state.get("show_rsi", True)
    show_m = st.session_state.get("show_macd", True)
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

    if "time" not in d.columns:
        d["time"] = range(len(d))

    d.columns = [str(c).lower() for c in d.columns]

    if pd.api.types.is_datetime64_any_dtype(d["time"]):
        d["time"] = (d["time"].astype("int64") // 10**9).astype("int64") + 25200
    else:
        d["time"] = pd.to_numeric(d["time"], errors="coerce").fillna(0).astype("int64") + 25200

    for col in ["open", "high", "low", "close", "volume"]:
        if col not in d.columns:
            d[col] = 100.0 if col == "volume" else 0.0
        else:
            d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0.0)

    records = d.to_dict("records")

    pane_ts = {
        "visible": True,
        "timeVisible": True,
        "secondsVisible": tf in ("1m", "3m", "5m"),
        "borderColor": theme.BORDER_COLOR,
        "borderVisible": True,
        "fixLeftEdge": False,
        "rightOffset": 6,
        "handleScroll": {"mouseWheel": True, "pressedMouseMove": True, "horzTouchDrag": True, "vertTouchDrag": True},
        "handleScale": {"axisPressedMouseMove": True, "mouseWheel": True, "pinch": True},
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
        "crosshair": {
            "mode": 1,
            "vertLine": {"color": theme.CROSSHAIR_COLOR, "style": 3, "labelBackgroundColor": theme.BORDER_COLOR},
            "horzLine": {"color": theme.CROSSHAIR_COLOR, "style": 3, "labelBackgroundColor": theme.BORDER_COLOR},
        },
        "rightPriceScale": {
            "autoScale": True,
            "borderColor": theme.BORDER_COLOR,
            "borderVisible": True,
            "scaleMargins": {"top": theme.PRICE_SCALE_TOP, "bottom": theme.PRICE_SCALE_BTM},
            "mode": 0,
        },
        # ควบคุมสเกล Overlay (Volume) ให้ยืนติดขอบล่างสุด และไม่ให้สูงเกิน 20%
        "overlayPriceScales": {
            "scaleMargins": {"top": theme.VOL_TOP_MARGIN, "bottom": 0.0},
        },
        "timeScale": pane_ts,
    }

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

    show_sig = st.session_state.get("show_sig", False)
    show_stars = st.session_state.get("show_stars", True)
    show_dots = st.session_state.get("show_dots", False)

    if show_sig or show_stars or show_dots:
        marker_map = {}
        for r in records:
            t = int(r["time"])
            labels = []
            sig = str(r.get("signal", ""))
            is_buy = sig == "BUY"
            is_sell = sig == "SELL ALL"

            if show_sig and (is_buy or is_sell):
                labels.append(sig)
            if show_stars and r.get("star", False):
                labels.append("⭐")
            dot = str(r.get("dot_warn", ""))
            if show_dots and dot:
                labels.append("🔴" if dot == "RED" else "🟠")

            if labels:
                marker_map[t] = {
                    "time": t,
                    "position": "belowBar" if is_buy else "aboveBar",
                    "color": theme.CANDLE_UP if is_buy else (theme.CANDLE_DOWN if is_sell else "#FFD700"),
                    "shape": "arrowUp" if is_buy else ("arrowDown" if is_sell else "circle"),
                    "text": " ".join(labels),
                    "size": 1,
                }

        clean_markers = sanitize_markers(list(marker_map.values()))
        if clean_markers:
            price_series[0]["markers"] = clean_markers

    ema_alpha = (100 - st.session_state.get("ema_opacity", 0)) / 100.0
    trend_alpha = (100 - st.session_state.get("trend_opacity", 60)) / 100.0
    lw = int(st.session_state.get("line_width", 2))

    if st.session_state.get("show_fast", True) and "ema_fast" in d:
        fast_data = [{"time": int(r["time"]), "value": float(r["ema_fast"])} for r in records if pd.notna(r.get("ema_fast")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": fast_data,
            "options": {"color": theme.EMA_FAST_COLOR, "lineWidth": lw, "priceLineVisible": False, "lastValueVisible": False},
        })

    if st.session_state.get("show_slow", True) and "ema_slow" in d:
        slow_data = [{"time": int(r["time"]), "value": float(r["ema_slow"])} for r in records if pd.notna(r.get("ema_slow")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": slow_data,
            "options": {"color": theme.EMA_SLOW_COLOR, "lineWidth": lw, "priceLineVisible": False, "lastValueVisible": False},
        })

    if st.session_state.get("show_trend", True) and "ema_trend" in d:
        trend_data = [{"time": int(r["time"]), "value": float(r["ema_trend"])} for r in records if pd.notna(r.get("ema_trend")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": trend_data,
            "options": {"color": theme.EMA_TREND_COLOR, "lineWidth": max(1, lw - 1), "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False},
        })

    # Volume: priceScaleId เป็น "" (Overlay) แยกเด็ดขาดจากแกนราคา และตั้งติดพื้นล่างสุด 0px
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
                "priceScaleId": "",            # กำหนดเป็น Overlay อิสระ ไม่ดึงสเกลแท่งเทียน
                "priceLineVisible": False,    # ปิดเส้นประแนวนอนยาว
                "lastValueVisible": False,    # ปิดป้ายตัวเลขราคา
            },
        })

    def make_rsi_pane():
        rsi_data = [{"time": int(r["time"]), "value": float(r["rsi"])} for r in records if pd.notna(r.get("rsi")) and r["time"] > 0]
        mk = lambda v: [{"time": int(r["time"]), "value": v} for r in records if r["time"] > 0]
        return {
            "chart": {
                **base_chart,
                "height": rsi_h,
                "timeScale": pane_ts,
                "rightPriceScale": {
                    **base_chart["rightPriceScale"],
                    "scaleMargins": {"top": theme.RSI_TOP_MARGIN, "bottom": theme.RSI_BTM_MARGIN},
                },
                "watermark": {
                    "visible": True,
                    "text": "RSI (14)",
                    "fontSize": 18,
                    "color": theme.RSI_TITLE_COLOR,
                    "horzAlign": "left",
                    "vertAlign": "top",
                },
            },
            "series": [
                {"type": "Line", "data": mk(70.0), "options": {"color": theme.RSI_LEVEL_70, "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": mk(50.0), "options": {"color": theme.RSI_LEVEL_50, "lineWidth": 1, "lineStyle": 3, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": mk(30.0), "options": {"color": theme.RSI_LEVEL_30, "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": rsi_data, "options": {"color": theme.RSI_LINE_COLOR, "lineWidth": theme.RSI_LINE_WIDTH, "priceLineVisible": True}},
            ],
        }

    def make_macd_pane():
        macd_line = [{"time": int(r["time"]), "value": float(r["macd"])} for r in records if pd.notna(r.get("macd")) and r["time"] > 0]
        sig_line  = [{"time": int(r["time"]), "value": float(r["macd_sig"])} for r in records if pd.notna(r.get("macd_sig")) and r["time"] > 0]
        hist = [
            {
                "time": int(r["time"]),
                "value": float(r["macd_hist"]),
                "color": theme.MACD_HIST_UP if float(r.get("macd_hist", 0)) >= 0 else theme.MACD_HIST_DOWN,
            }
            for r in records if pd.notna(r.get("macd_hist")) and r["time"] > 0
        ]
        return {
            "chart": {
                **base_chart,
                "height": macd_h,
                "timeScale": pane_ts,
                "rightPriceScale": {
                    **base_chart["rightPriceScale"],
                    "scaleMargins": {"top": theme.MACD_TOP_MARGIN, "bottom": theme.MACD_BTM_MARGIN},
                },
                "watermark": {
                    "visible": True,
                    "text": "MACD (12, 26, 9)",
                    "fontSize": 18,
                    "color": theme.MACD_TITLE_COLOR,
                    "horzAlign": "left",
                    "vertAlign": "top",
                },
            },
            "series": [
                {"type": "Histogram", "data": hist, "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "macd_hist", "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": macd_line, "options": {"color": theme.MACD_LINE_COLOR, "lineWidth": theme.MACD_LINE_WIDTH, "priceLineVisible": False}},
                {"type": "Line", "data": sig_line, "options": {"color": theme.MACD_SIG_COLOR, "lineWidth": theme.MACD_SIG_WIDTH, "priceLineVisible": False}},
            ],
        }

    charts = [{
        "chart": {
            **base_chart,
            "height": main_h,
            "timeScale": pane_ts,
            "watermark": {"visible": True, "text": f"{symbol} · {tf}", "fontSize": 34, "color": "rgba(255,255,255,0.05)", "horzAlign": "center", "vertAlign": "center"},
        },
        "series": price_series,
    }]

    for p in st.session_state.get("pane_order", ["rsi", "macd"]):
        if p == "rsi" and show_r:
            charts.append(make_rsi_pane())
        elif p == "macd" and show_m:
            charts.append(make_macd_pane())

    return charts