# chart.py
import pandas as pd


def y_digits(price: float) -> int:
    """คำนวณจำนวนทศนิยมให้อัตโนมัติตามระดับราคาเหรียญ"""
    try:
        p = float(price)
        if p >= 1000:
            return 2
        elif p >= 1:
            return 4
        elif p >= 0.001:
            return 6
        return 8
    except Exception:
        return 2


def build_tv_chart(
    df: pd.DataFrame,
    symbol: str,
    tf: str = "1h",
    show_ema=True,
    show_vol=True,
    show_signals=True,
):
    df = df.sort_values("time").drop_duplicates(subset=["time"]).reset_index(drop=True).copy()

    last_close = df["close"].iloc[-1] if not df.empty else 1.0
    dig = y_digits(last_close)
    min_move = 1 / (10 ** dig)
    df["time_sec"] = df["time"].apply(lambda x: int(x.timestamp()))

    # 1. แท่งเทียน Candlestick
    candle_data = [
        {
            "time": int(row["time_sec"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
        }
        for _, row in df.iterrows()
    ]

    series = [{
        "type": "Candlestick",
        "data": candle_data,
        "options": {
            "upColor": "#089981",
            "downColor": "#f23645",
            "borderUpColor": "#089981",
            "borderDownColor": "#f23645",
            "wickUpColor": "#089981",
            "wickDownColor": "#f23645",
            "priceFormat": {"type": "price", "precision": dig, "minMove": min_move},
        }
    }]

    # 2. เส้น EMA 7/13/45 สไตล์ TradingView
    if show_ema:
        ema_configs = [
            ("ema_f", "#2962ff", 2),
            ("ema_s", "#ff9800", 2),
            ("ema_t", "#9c27b0", 2),
        ]
        for col, color, width in ema_configs:
            if col in df.columns:
                line_data = [
                    {"time": int(row["time_sec"]), "value": float(row[col])}
                    for _, row in df.iterrows() if pd.notnull(row[col])
                ]
                series.append({
                    "type": "Line",
                    "data": line_data,
                    "options": {
                        "color": color,
                        "lineWidth": width,
                        "priceFormat": {"type": "price", "precision": dig, "minMove": min_move},
                    }
                })

    # 3. ป้ายสัญญาณคลีนแบบ TradingView (BUY, SELL ALL, TP)
    if show_signals:
        markers = []
        for _, row in df.iterrows():
            t = int(row["time_sec"])
            if row.get("buy"):
                markers.append({
                    "time": t, "position": "belowBar", "color": "#089981",
                    "shape": "arrowUp", "text": "BUY"
                })
            elif row.get("sell"):
                markers.append({
                    "time": t, "position": "aboveBar", "color": "#f23645",
                    "shape": "arrowDown", "text": "SELL ALL"
                })
            elif row.get("tp"):
                markers.append({
                    "time": t, "position": "aboveBar", "color": "#ffb74d",
                    "shape": "circle", "text": ""
                })
            elif row.get("early"):
                markers.append({
                    "time": t, "position": "belowBar", "color": "#00b0ff",
                    "shape": "arrowUp", "text": ""
                })

        if markers:
            series[0]["markers"] = sorted(markers, key=lambda x: x["time"])

    # 4. Volume (แยกสเกลแกนซ้าย ป้องกันดึงราคาจนแกนขวาติดลบ)
    if show_vol:
        vol_data = [
            {
                "time": int(row["time_sec"]),
                "value": float(row["volume"]),
                "color": "rgba(8, 153, 129, 0.45)" if row["close"] >= row["open"] else "rgba(242, 54, 69, 0.45)"
            }
            for _, row in df.iterrows()
        ]
        series.append({
            "type": "Histogram",
            "data": vol_data,
            "options": {
                "priceFormat": {"type": "volume"},
                "priceScaleId": "left",
            }
        })

    chart_options = {
        "height": 660,
        "layout": {"background": {"type": "solid", "color": "#0d1017"}, "textColor": "#787b86"},
        "grid": {"vertLines": {"color": "#1e222d"}, "horzLines": {"color": "#1e222d"}},
        "crosshair": {"mode": 1},
        "rightPriceScale": {
            "borderColor": "#2a2e39",
            "autoScale": True,
            "scaleMargins": {"top": 0.08, "bottom": 0.08},
        },
        "leftPriceScale": {
            "visible": False,
            "scaleMargins": {"top": 0.82, "bottom": 0.0},
        },
        "timeScale": {"borderColor": "#2a2e39", "timeVisible": True, "secondsVisible": False},
    }

    return chart_options, series