# chart_builders.py — Chart Assembly & Multi-pane Layout Engine
import pandas as pd
import streamlit as st

UP, DOWN = "#26a69a", "#ef5350"

def sanitize_markers(markers: list) -> list:
    if not markers: return []
    seen = set()
    cleaned = []
    sorted_markers = sorted(markers, key=lambda x: int(x.get("time", 0)))
    for m in sorted_markers:
        t = int(m.get("time", 0))
        if t <= 0 or t in seen: continue
        seen.add(t)
        m["time"] = t
        cleaned.append(m)
    return cleaned

def price_precision(df: pd.DataFrame) -> int:
    if df is None or df.empty or "close" not in df.columns: return 2
    p = float(df["close"].iloc[-1])
    if p >= 1000: return 2
    if p >= 10: return 3
    if p >= 0.1: return 5
    return 8

def min_move(df: pd.DataFrame) -> float:
    return 10 ** -price_precision(df)

def build_charts(df, symbol, tf, main_h, rsi_h, macd_h):
    if df is None or df.empty:
        return []

    show_r = st.session_state.get('show_rsi', True)
    show_m = st.session_state.get('show_macd', True)
    d = df.copy()

    if hasattr(d.columns, 'str'):
        d.columns = d.columns.astype(str).str.lower()
    d = d.loc[:, ~d.columns.duplicated()]

    if 'time' not in d.columns:
        if isinstance(d.index, pd.DatetimeIndex) or d.index.name is not None:
            d = d.reset_index(drop=False)
            if 'time' not in d.columns and len(d.columns) > 0:
                d = d.rename(columns={d.columns[0]: 'time'})
        else:
            d['time'] = range(len(d))

    if 'time' not in d.columns:
        d['time'] = range(len(d))

    d.columns = [str(c).lower() for c in d.columns]

    if pd.api.types.is_datetime64_any_dtype(d['time']):
        d['time'] = (d['time'].astype('int64') // 10**9).astype('int64') + 25200
    else:
        d['time'] = pd.to_numeric(d['time'], errors='coerce').fillna(0).astype('int64') + 25200

    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col not in d.columns:
            d[col] = 100.0 if col == 'volume' else 0.0
        else:
            d[col] = pd.to_numeric(d[col], errors='coerce').fillna(0.0)

    records = d.to_dict('records')

    ts_opts = {
        "borderColor": "#1E1E1E", "timeVisible": True, "secondsVisible": tf in ("1m", "3m", "5m"),
        "fixLeftEdge": False, "rightOffset": 5,
        "handleScroll": {"mouseWheel": True, "pressedMouseMove": True, "horzTouchDrag": True, "vertTouchDrag": True},
        "handleScale": {"axisPressedMouseMove": True, "mouseWheel": True, "pinch": True},
    }

    base_chart = {
        "layout": {"background": {"type": "solid", "color": "#000000"}, "textColor": "#D1D4DC"},
        "grid": {"vertLines": {"color": "#141414"}, "horzLines": {"color": "#141414"}},
        "crosshair": {"mode": 0},
        "rightPriceScale": {
            "autoScale": True,
            "borderColor": "#1E1E1E",
            "scaleMargins": {"top": 0.1, "bottom": 0.1},
            "mode": 0
        },
        "timeScale": ts_opts,
    }

    candles = [
        {
            "time": int(r["time"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"])
        }
        for r in records if r["time"] > 0
    ]

    price_series = [{
        "type": "Candlestick", 
        "data": candles,
        "options": {
            "upColor": UP, "downColor": DOWN, "borderVisible": False, 
            "wickUpColor": UP, "wickDownColor": DOWN,
            "priceScaleId": "right",
            "priceFormat": {
                "type": "price",
                "precision": price_precision(d),
                "minMove": min_move(d)
            }
        }
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

            if show_sig and (is_buy or is_sell): labels.append(sig)
            if show_stars and r.get("star", False): labels.append("⭐")
            dot = str(r.get("dot_warn", ""))
            if show_dots and dot: labels.append("🔴" if dot == "RED" else "🟠")

            if labels:
                marker_map[t] = {
                    "time": t, "position": "belowBar" if is_buy else "aboveBar",
                    "color": UP if is_buy else (DOWN if is_sell else "#ffd700"),
                    "shape": "arrowUp" if is_buy else ("arrowDown" if is_sell else "circle"),
                    "text": " ".join(labels), "size": 1
                }

        raw_markers = list(marker_map.values())
        clean_markers = sanitize_markers(raw_markers)
        if clean_markers:
            price_series[0]["markers"] = clean_markers

    ema_alpha = (100 - st.session_state.get("ema_opacity", 0)) / 100.0
    trend_alpha = (100 - st.session_state.get("trend_opacity", 60)) / 100.0
    lw = int(st.session_state.get("line_width", 2))

    if st.session_state.get("show_fast", True) and "ema_fast" in d:
        fast_data = [{"time": int(r["time"]), "value": float(r["ema_fast"])} for r in records if pd.notna(r.get("ema_fast")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": fast_data,
            "options": {"color": f"rgba(41, 98, 255, {ema_alpha:.2f})", "lineWidth": lw, "priceLineVisible": False}
        })

    if st.session_state.get("show_slow", True) and "ema_slow" in d:
        slow_data = [{"time": int(r["time"]), "value": float(r["ema_slow"])} for r in records if pd.notna(r.get("ema_slow")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": slow_data,
            "options": {"color": f"rgba(239, 83, 80, {ema_alpha:.2f})", "lineWidth": lw, "priceLineVisible": False}
        })

    if st.session_state.get("show_trend", True) and "ema_trend" in d:
        trend_data = [{"time": int(r["time"]), "value": float(r["ema_trend"])} for r in records if pd.notna(r.get("ema_trend")) and r["time"] > 0]
        price_series.append({
            "type": "Line", "data": trend_data,
            "options": {"color": f"rgba(255, 255, 255, {trend_alpha:.2f})", "lineWidth": max(1, lw - 1), "lineStyle": 2, "priceLineVisible": False}
        })

    vol = [
        {
            "time": int(r["time"]),
            "value": float(r.get("volume", 0)),
            "color": UP + "80" if float(r.get("close", 0)) >= float(r.get("open", 0)) else DOWN + "80"
        }
        for r in records if pd.notna(r.get("volume")) and r["time"] > 0
    ]
    price_series.append({
        "type": "Histogram", "data": vol,
        "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol"},
        "priceScale": {"scaleMargins": {"top": 0.8, "bottom": 0}}
    })

    charts = [{
        "chart": {
            **base_chart,
            "height": main_h,
            "watermark": {"visible": True, "text": f"{symbol} · {tf}", "fontSize": 40, "color": "rgba(255,255,255,0.05)"}
        },
        "series": price_series
    }]

    def make_rsi_pane():
        rsi_data = [{"time": int(r["time"]), "value": float(r["rsi"])} for r in records if pd.notna(r.get("rsi")) and r["time"] > 0]
        mk = lambda v: [{"time": int(r["time"]), "value": v} for r in records if r["time"] > 0]
        return {
            "chart": {
                **base_chart, "height": rsi_h,
                "watermark": {"visible": True, "text": "RSI (14)", "fontSize": 18, "color": "rgba(0, 188, 212, 0.08)"}
            },
            "series": [
                {"type": "Line", "data": mk(70.0), "options": {"color": "rgba(239,83,80,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                {"type": "Line", "data": mk(50.0), "options": {"color": "rgba(120,123,134,0.3)", "lineWidth": 1, "lineStyle": 3, "priceLineVisible": False}},
                {"type": "Line", "data": mk(30.0), "options": {"color": "rgba(38,166,154,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                {"type": "Line", "data": rsi_data, "options": {"color": "#00bcd4", "lineWidth": 2, "priceLineVisible": True}},
            ]
        }

    def make_macd_pane():
        macd_line = [{"time": int(r["time"]), "value": float(r["macd"])} for r in records if pd.notna(r.get("macd")) and r["time"] > 0]
        sig_line  = [{"time": int(r["time"]), "value": float(r["macd_sig"])} for r in records if pd.notna(r.get("macd_sig")) and r["time"] > 0]
        hist = [
            {"time": int(r["time"]), "value": float(r["macd_hist"]), "color": UP + "90" if float(r.get("macd_hist", 0)) >= 0 else DOWN + "90"}
            for r in records if pd.notna(r.get("macd_hist")) and r["time"] > 0
        ]
        return {
            "chart": {
                **base_chart, "height": macd_h,
                "watermark": {"visible": True, "text": "MACD (12, 26, 9)", "fontSize": 18, "color": "rgba(0, 230, 118, 0.08)"}
            },
            "series": [
                {"type": "Histogram", "data": hist, "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "macd_hist"}},
                {"type": "Line", "data": macd_line, "options": {"color": "#00e676", "lineWidth": 2, "priceLineVisible": False}},
                {"type": "Line", "data": sig_line, "options": {"color": "#ff5252", "lineWidth": 2, "priceLineVisible": False}},
            ]
        }

    for p in st.session_state.get("pane_order", ["rsi", "macd"]):
        if p == "rsi" and show_r:
            charts.append(make_rsi_pane())
        elif p == "macd" and show_m:
            charts.append(make_macd_pane())

    return charts