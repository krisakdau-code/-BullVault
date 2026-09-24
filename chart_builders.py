# chart_builders.py — Full Engine: 11 Professional Indicators, Dynamic Sub-panes & Bottom-only TimeScale
from core.pine_bridge import PineBridgeEngine
import pandas as pd
import numpy as np
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


def render_pine_hud_overlay():
    """สร้างกล่อง HUD Dashboard สีดำ-เหลืองลอยตัวที่มุมซ้ายล่างของกราฟเหมือนใน TradingView"""
    hud = st.session_state.get("pine_hud_stats")
    if not hud or not st.session_state.get("custom_pine_active", False):
        return

    net_color = "#00e676" if str(hud.get("net_pl", "")).startswith("+") else "#ff5252"
    hold_color = "#00e676" if hud.get("holding") == "YES" else "#ffb74d"

    st.markdown(f"""
        <div style="position: fixed; bottom: 35px; left: 75px; z-index: 999; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; font-size: 11px; background: rgba(13, 17, 23, 0.95); border: 1px solid #30363d; border-radius: 6px; box-shadow: 0 8px 24px rgba(0,0,0,0.7); pointer-events: none; min-width: 175px;">
            <div style="display: flex; background: #ffd600; color: #000; font-weight: 800; padding: 4px 8px; justify-content: space-between; border-top-left-radius: 5px; border-top-right-radius: 5px; font-size: 11px;">
                <span>{hud.get('title', 'DIAMOND V11.3')}</span>
                <span style="font-size: 10px; opacity: 0.85;">{hud.get('subtitle', 'DYNAMIC TP')}</span>
            </div>
            <table style="width: 100%; border-collapse: collapse; color: #c9d1d9; margin: 0; padding: 2px;">
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">EXPLOSION</td><td style="padding: 2.5px 8px; text-align: right; color: #58a6ff; font-weight: 600;">{hud.get('explosion', 'CHOP / WAIT')}</td></tr>
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">Win Rate</td><td style="padding: 2.5px 8px; text-align: right; color: #58a6ff; font-weight: bold;">{hud.get('win_rate', '12.62%')}</td></tr>
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">Net P/L</td><td style="padding: 2.5px 8px; text-align: right; color: {net_color}; font-weight: bold;">{hud.get('net_pl', '-705.06%')}</td></tr>
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">Total Profit</td><td style="padding: 2.5px 8px; text-align: right; color: #00e676;">{hud.get('total_profit', '+242.69%')}</td></tr>
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">Total Loss</td><td style="padding: 2.5px 8px; text-align: right; color: #ff5252;">{hud.get('total_loss', '-947.75%')}</td></tr>
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">TP Count</td><td style="padding: 2.5px 8px; text-align: right; color: #00e5ff; font-weight: bold;">{hud.get('tp_count', '0 Times')}</td></tr>
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">Holding</td><td style="padding: 2.5px 8px; text-align: right; color: {hold_color}; font-weight: bold;">{hud.get('holding', 'YES')}</td></tr>
                <tr style="border-bottom: 1px solid #21262d;"><td style="padding: 2.5px 8px; color: #8b949e;">Trailing High</td><td style="padding: 2.5px 8px; text-align: right; color: #ffd600; font-weight: 600;">{hud.get('trailing_high', '0.7499')}</td></tr>
                <tr><td style="padding: 2.5px 8px; color: #8b949e;">RSI Current</td><td style="padding: 2.5px 8px; text-align: right; color: #f8fafc; font-weight: bold;">{hud.get('rsi_current', '49.86')}</td></tr>
            </table>
        </div>
    """, unsafe_allow_html=True)


def build_charts(df, symbol, tf, main_h=520, rsi_h=120, macd_h=120):
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

    tr = pd.concat([d["high"] - d["low"], (d["high"] - d["close"].shift(1)).abs(), (d["low"] - d["close"].shift(1)).abs()], axis=1).max(axis=1)

    # ══════════════════════════════════════════════════════════
    # 1. RSI & RSI MA (คงของเดิม 100% สลับ SMA/EMA ได้)
    # ══════════════════════════════════════════════════════════
    r_len = int(st.session_state.get("RSI_in_length", st.session_state.get("rsi_len", 14)))
    r_src = str(st.session_state.get("RSI_in_source", st.session_state.get("rsi_source", "close"))).lower()
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

    # ══════════════════════════════════════════════════════════
    # 2. MACD (คงของเดิม 100%)
    # ══════════════════════════════════════════════════════════
    m_fast = int(st.session_state.get("MACD_in_fast", st.session_state.get("macd_fast_len", 12)))
    m_slow = int(st.session_state.get("MACD_in_slow", st.session_state.get("macd_slow_len", 26)))
    m_sig  = int(st.session_state.get("MACD_in_signal", st.session_state.get("macd_sig_len", 9)))
    m_src  = str(st.session_state.get("MACD_in_source", st.session_state.get("macd_source", "close"))).lower()
    m_series = d[m_src] if m_src in d.columns else d["close"]

    fast_ema = m_series.ewm(span=m_fast, adjust=False).mean()
    slow_ema = m_series.ewm(span=m_slow, adjust=False).mean()
    d["calc_macd"] = fast_ema - slow_ema
    d["calc_macd_sig"] = d["calc_macd"].ewm(span=m_sig, adjust=False).mean()
    d["calc_macd_hist"] = d["calc_macd"] - d["calc_macd_sig"]

    # ══════════════════════════════════════════════════════════
    # 3. EMA Ribbon กราฟหลัก (คงของเดิม 100%)
    # ══════════════════════════════════════════════════════════
    ema_f_len = int(st.session_state.get("EMA_in_fast", st.session_state.get("ema_fast_len", 12)))
    ema_s_len = int(st.session_state.get("EMA_in_slow", st.session_state.get("ema_slow_len", 26)))
    ema_t_len = int(st.session_state.get("EMA_in_trend", st.session_state.get("ema_trend_len", 200)))
    d["calc_ema_fast"] = d["close"].ewm(span=ema_f_len, adjust=False).mean()
    d["calc_ema_slow"] = d["close"].ewm(span=ema_s_len, adjust=False).mean()
    d["calc_ema_trend"] = d["close"].ewm(span=ema_t_len, adjust=False).mean()

    # ══════════════════════════════════════════════════════════
    # 4. คำนวณอินดิเคเตอร์เพิ่มเติม
    # ══════════════════════════════════════════════════════════
    # Bollinger Bands
    bb_len = int(st.session_state.get("BB_in_length", 20))
    bb_dev = float(st.session_state.get("BB_in_std_dev", 2.0))
    d["calc_bb_mid"] = d["close"].rolling(bb_len).mean()
    bb_std = d["close"].rolling(bb_len).std()
    d["calc_bb_upper"] = d["calc_bb_mid"] + (bb_std * bb_dev)
    d["calc_bb_lower"] = d["calc_bb_mid"] - (bb_std * bb_dev)

    # Supertrend
    st_len = int(st.session_state.get("ST_in_atr_period", 10))
    st_fac = float(st.session_state.get("ST_in_factor", 3.0))
    hl2 = (d["high"] + d["low"]) / 2.0
    st_atr = tr.ewm(alpha=1 / st_len, adjust=False).mean()
    d["calc_st_upper"] = hl2 + (st_fac * st_atr)
    d["calc_st_lower"] = hl2 - (st_fac * st_atr)

    # Ichimoku Cloud
    ichi_conv = int(st.session_state.get("ICHI_in_conversion", 9))
    ichi_base = int(st.session_state.get("ICHI_in_base", 26))
    ichi_span_b = int(st.session_state.get("ICHI_in_span_b", 52))
    d["calc_ichi_tenkan"] = (d["high"].rolling(ichi_conv).max() + d["low"].rolling(ichi_conv).min()) / 2.0
    d["calc_ichi_kijun"] = (d["high"].rolling(ichi_base).max() + d["low"].rolling(ichi_base).min()) / 2.0
    d["calc_ichi_span_a"] = ((d["calc_ichi_tenkan"] + d["calc_ichi_kijun"]) / 2.0).shift(ichi_base)
    d["calc_ichi_span_b"] = ((d["high"].rolling(ichi_span_b).max() + d["low"].rolling(ichi_span_b).min()) / 2.0).shift(ichi_base)

    # VWAP
    hlc3 = (d["high"] + d["low"] + d["close"]) / 3.0
    cum_vol = d["volume"].cumsum()
    d["calc_vwap"] = (hlc3 * d["volume"]).cumsum() / cum_vol.replace(0, np.nan)

    # Stochastic Oscillator
    stoch_k_len = int(st.session_state.get("STOCH_in_k_len", 14))
    stoch_k_smooth = int(st.session_state.get("STOCH_in_k_smooth", 1))
    stoch_d_smooth = int(st.session_state.get("STOCH_in_d_smooth", 3))
    ll = d["low"].rolling(stoch_k_len).min()
    hh = d["high"].rolling(stoch_k_len).max()
    raw_k = 100.0 * (d["close"] - ll) / (hh - ll).replace(0, np.nan)
    d["calc_stoch_k"] = raw_k.rolling(stoch_k_smooth).mean()
    d["calc_stoch_d"] = d["calc_stoch_k"].rolling(stoch_d_smooth).mean()

    # ATR
    atr_len = int(st.session_state.get("ATR_in_length", 14))
    d["calc_atr"] = tr.ewm(alpha=1 / atr_len, adjust=False).mean()

    # ADX / DMI
    adx_len = int(st.session_state.get("ADX_in_adx_len", 14))
    up_m = d["high"] - d["high"].shift(1)
    dn_m = d["low"].shift(1) - d["low"]
    pdm = np.where((up_m > dn_m) & (up_m > 0), up_m, 0.0)
    mdm = np.where((dn_m > up_m) & (dn_m > 0), dn_m, 0.0)
    tr_smooth = tr.ewm(alpha=1 / adx_len, adjust=False).mean().replace(0, 1e-9)
    pdi_s = 100.0 * (pd.Series(pdm, index=d.index).ewm(alpha=1 / adx_len, adjust=False).mean() / tr_smooth)
    mdi_s = 100.0 * (pd.Series(mdm, index=d.index).ewm(alpha=1 / adx_len, adjust=False).mean() / tr_smooth)
    dx = (100.0 * (pdi_s - mdi_s).abs() / (pdi_s + mdi_s).replace(0, 1e-9)).fillna(0)
    d["calc_adx"] = dx.ewm(alpha=1 / adx_len, adjust=False).mean()
    d["calc_pdi"] = pdi_s
    d["calc_mdi"] = mdi_s

    # Volume MA
    vol_ma_len = int(st.session_state.get("VOL_in_ma_len", 20))
    d["calc_vol_ma"] = d["volume"].rolling(vol_ma_len).mean()

    records = d.to_dict("records")

    pane_ts = {
        "visible": False,  # ซ่อนแกนเวลาไว้เป็นค่าเริ่มต้น (จะเปิดเฉพาะหน้าต่างล่างสุดตัวเดียว)
        "timeVisible": True,
        "secondsVisible": tf in ("1m", "3m", "5m"),
        "borderColor": theme.BORDER_COLOR,
        "borderVisible": True,
        "fixLeftEdge": False,
        "rightOffset": 6,
    }

    crosshair_synced = {
        "mode": 1,
        "vertLine": {
            "visible": True, "style": 3, "width": 1,
            "color": "rgba(255, 255, 255, 0.40)", "labelVisible": True, "labelBackgroundColor": theme.BORDER_COLOR,
        },
        "horzLine": {
            "visible": True, "style": 3, "width": 1,
            "color": "rgba(255, 255, 255, 0.40)", "labelVisible": True, "labelBackgroundColor": theme.BORDER_COLOR,
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

    # 1. EMA Ribbon Overlay
    if st.session_state.get("ind_active_EMA", st.session_state.get("show_ema", True)):
        fast_col = st.session_state.get("EMA_st_fast_color", theme.EMA_FAST_COLOR)
        fast_lw = int(st.session_state.get("EMA_st_fast_width", 2))
        slow_col = st.session_state.get("EMA_st_slow_color", theme.EMA_SLOW_COLOR)
        slow_lw = int(st.session_state.get("EMA_st_slow_width", 2))
        trend_col = st.session_state.get("EMA_st_trend_color", theme.EMA_TREND_COLOR)
        trend_lw = int(st.session_state.get("EMA_st_trend_width", 1))

        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_ema_fast"])} for r in records if pd.notna(r.get("calc_ema_fast")) and r["time"] > 0],
                             "options": {"color": fast_col, "lineWidth": fast_lw, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_ema_slow"])} for r in records if pd.notna(r.get("calc_ema_slow")) and r["time"] > 0],
                             "options": {"color": slow_col, "lineWidth": slow_lw, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_ema_trend"])} for r in records if pd.notna(r.get("calc_ema_trend")) and r["time"] > 0],
                             "options": {"color": trend_col, "lineWidth": trend_lw, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}})

    # 2. Bollinger Bands Overlay
    if st.session_state.get("ind_active_BB", False):
        bb_u_col = st.session_state.get("BB_st_upper_color", "#2962ff")
        bb_u_lw = int(st.session_state.get("BB_st_upper_width", 1))
        bb_l_col = st.session_state.get("BB_st_lower_color", "#2962ff")
        bb_l_lw = int(st.session_state.get("BB_st_lower_width", 1))
        bb_m_col = st.session_state.get("BB_st_mid_color", "#ff9800")
        bb_m_lw = int(st.session_state.get("BB_st_mid_width", 2))

        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_bb_upper"])} for r in records if pd.notna(r.get("calc_bb_upper")) and r["time"] > 0],
                             "options": {"color": bb_u_col, "lineWidth": bb_u_lw, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_bb_lower"])} for r in records if pd.notna(r.get("calc_bb_lower")) and r["time"] > 0],
                             "options": {"color": bb_l_col, "lineWidth": bb_l_lw, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_bb_mid"])} for r in records if pd.notna(r.get("calc_bb_mid")) and r["time"] > 0],
                             "options": {"color": bb_m_col, "lineWidth": bb_m_lw, "priceLineVisible": False, "lastValueVisible": False}})

    # 3. Supertrend Overlay
    if st.session_state.get("ind_active_ST", False):
        st_up_col = st.session_state.get("ST_st_up_color", "#00e676")
        st_up_lw = int(st.session_state.get("ST_st_up_width", 2))
        st_dn_col = st.session_state.get("ST_st_down_color", "#ff5252")
        st_dn_lw = int(st.session_state.get("ST_st_down_width", 2))

        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_st_lower"])} for r in records if pd.notna(r.get("calc_st_lower")) and r["time"] > 0],
                             "options": {"color": st_up_col, "lineWidth": st_up_lw, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_st_upper"])} for r in records if pd.notna(r.get("calc_st_upper")) and r["time"] > 0],
                             "options": {"color": st_dn_col, "lineWidth": st_dn_lw, "priceLineVisible": False, "lastValueVisible": False}})

    # 4. Ichimoku Cloud Overlay (ผูกค่าสี Lead A, Lead B ตามหน้าต่าง Style 100%)
    if st.session_state.get("ind_active_ICHI", False):
        ichi_t_col = st.session_state.get("ICHI_st_tenkan_color", "#00bcd4")
        ichi_k_col = st.session_state.get("ICHI_st_kijun_color", "#ff4081")
        ichi_a_col = st.session_state.get("ICHI_st_lead_a_color", st.session_state.get("ICHI_st_span_a_color", "rgba(0, 230, 118, 0.6)"))
        ichi_b_col = st.session_state.get("ICHI_st_lead_b_color", st.session_state.get("ICHI_st_span_b_color", "rgba(255, 82, 82, 0.6)"))

        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_ichi_tenkan"])} for r in records if pd.notna(r.get("calc_ichi_tenkan")) and r["time"] > 0],
                             "options": {"color": ichi_t_col, "lineWidth": 1, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_ichi_kijun"])} for r in records if pd.notna(r.get("calc_ichi_kijun")) and r["time"] > 0],
                             "options": {"color": ichi_k_col, "lineWidth": 1, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_ichi_span_a"])} for r in records if pd.notna(r.get("calc_ichi_span_a")) and r["time"] > 0],
                             "options": {"color": ichi_a_col, "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}})
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_ichi_span_b"])} for r in records if pd.notna(r.get("calc_ichi_span_b")) and r["time"] > 0],
                             "options": {"color": ichi_b_col, "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}})

    # 5. VWAP Overlay
    if st.session_state.get("ind_active_VWAP", False):
        price_series.append({"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_vwap"])} for r in records if pd.notna(r.get("calc_vwap")) and r["time"] > 0],
                             "options": {"color": st.session_state.get("VWAP_st_color", "#ff9800"), "lineWidth": int(st.session_state.get("VWAP_st_width", 2)), "priceLineVisible": False, "lastValueVisible": False}})

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

    # ══════════════════════════════════════════════════════════
    # 6. Pine Script Interpreter Bridge Overlay (Diamond Armor / สคริปต์ของฉัน)
    # ══════════════════════════════════════════════════════════
    markers = []
    if st.session_state.get("custom_pine_active", False):
        pine_code = st.session_state.get("custom_pine_code", "")
        if pine_code:
            try:
                engine = PineBridgeEngine(pine_code)
                pine_res = engine.execute(d)
                if pine_res:
                    # 1. วาดเส้นอินดิเคเตอร์จาก Pine Script (Fast, Slow, Trend)
                    for p in pine_res.get("plots", []):
                        line_data = [
                            {"time": int(records[i]["time"]), "value": float(val)}
                            for i, val in enumerate(p["series"])
                            if i < len(records) and pd.notna(val) and records[i]["time"] > 0
                        ]
                        line_style = 2 if p.get("dash") == "dot" else 0
                        price_series.append({
                            "type": "Line",
                            "data": line_data,
                            "options": {
                                "color": p["color"],
                                "lineWidth": p.get("width", 2),
                                "lineStyle": line_style,
                                "priceLineVisible": False,
                                "lastValueVisible": False
                            }
                        })

                    # 2. วาดจุด Trailing Stop Dots (จุดกลมใต้แท่งเทียนสีส้ม/แดงเหมือนรูปที่ 2)
                    trail_series = pine_res.get("trailing_dots", pd.Series(dtype=float))
                    if not trail_series.empty:
                        dot_data = [
                            {"time": int(records[i]["time"]), "value": float(val)}
                            for i, val in enumerate(trail_series)
                            if i < len(records) and pd.notna(val) and records[i]["time"] > 0
                        ]
                        price_series.append({
                            "type": "Line",
                            "data": dot_data,
                            "options": {
                                "color": "#ff9800",
                                "lineWidth": 2,
                                "lineStyle": 3,
                                "priceLineVisible": False,
                                "lastValueVisible": False
                            }
                        })

                    # 3. ป้ายสัญญาณ BUY / SELL (Markers แคปซูลไอคอนบนแท่งเทียนเหมือนรูปที่ 2)
                    res_df = pine_res.get("df", pd.DataFrame())
                    if not res_df.empty and "buy_signal" in res_df.columns:
                        for i in range(len(records)):
                            if records[i]["time"] <= 0:
                                continue
                            if res_df["buy_signal"].iloc[i]:
                                markers.append({
                                    "time": int(records[i]["time"]),
                                    "position": "belowBar",
                                    "color": "#00e676",
                                    "shape": "arrowUp",
                                    "text": "🏷️ BUY"
                                })
                            elif res_df["sell_signal"].iloc[i]:
                                markers.append({
                                    "time": int(records[i]["time"]),
                                    "position": "aboveBar",
                                    "color": "#ff3366",
                                    "shape": "arrowDown",
                                    "text": "⚠️ SELL ALL"
                                })

                    if "hud" in pine_res:
                        st.session_state["pine_hud_stats"] = pine_res["hud"]
            except Exception:
                pass

    if markers:
        price_series[0]["markers"] = sanitize_markers(markers)

    # ══════════════════════════════════════════════════════════
    # Sub-panes (RSI, MACD, Stochastic, ATR, ADX, Volume)
    # ══════════════════════════════════════════════════════════
    def make_rsi_pane():
        rsi_col = st.session_state.get("RSI_st_line_color", st.session_state.get("rsi_col_line", theme.RSI_LINE_COLOR))
        rsi_lw = int(st.session_state.get("RSI_st_line_width", st.session_state.get("rsi_lw_line", 2)))
        u_band = float(st.session_state.get("RSI_in_ob", st.session_state.get("rsi_band_70", 70.0)))
        m_band = float(st.session_state.get("rsi_band_50", 50.0))
        l_band = float(st.session_state.get("RSI_in_os", st.session_state.get("rsi_band_30", 30.0)))

        rsi_data = [{"time": int(r["time"]), "value": float(r["calc_rsi"])} for r in records if pd.notna(r.get("calc_rsi")) and r["time"] > 0]
        mk = lambda v: [{"time": int(r["time"]), "value": v} for r in records if r["time"] > 0]

        series_list = [
            {"type": "Line", "data": mk(u_band), "options": {"color": st.session_state.get("RSI_st_ob_color", "rgba(242,54,69,0.5)"), "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
            {"type": "Line", "data": mk(m_band), "options": {"color": "rgba(120,123,134,0.25)", "lineWidth": 1, "lineStyle": 3, "priceLineVisible": False, "lastValueVisible": False}},
            {"type": "Line", "data": mk(l_band), "options": {"color": st.session_state.get("RSI_st_os_color", "rgba(8,153,129,0.5)"), "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
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

    def make_macd_pane():
        m_col = st.session_state.get("MACD_st_macd_color", st.session_state.get("macd_col_line", theme.MACD_LINE_COLOR))
        m_lw = int(st.session_state.get("MACD_st_macd_width", st.session_state.get("macd_lw_line", 2)))
        s_col = st.session_state.get("MACD_st_sig_color", st.session_state.get("macd_col_sig", theme.MACD_SIG_COLOR))
        s_lw = int(st.session_state.get("MACD_st_sig_width", st.session_state.get("macd_lw_sig", 2)))

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

    def make_stoch_pane():
        mk = lambda v: [{"time": int(r["time"]), "value": v} for r in records if r["time"] > 0]
        return {
            "chart": {**base_chart, "height": 120, "timeScale": pane_ts, "rightPriceScale": {**base_chart["rightPriceScale"], "scaleMargins": {"top": 0.1, "bottom": 0.1}},
                      "watermark": {"visible": True, "text": f"Stochastic ({stoch_k_len}, {stoch_d_smooth})", "fontSize": 16, "color": "#787b86", "horzAlign": "left", "vertAlign": "top"}},
            "series": [
                {"type": "Line", "data": mk(float(st.session_state.get("STOCH_in_ob", 80.0))), "options": {"color": "rgba(242,54,69,0.5)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": mk(float(st.session_state.get("STOCH_in_os", 20.0))), "options": {"color": "rgba(8,153,129,0.5)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_stoch_k"])} for r in records if pd.notna(r.get("calc_stoch_k")) and r["time"] > 0],
                 "options": {"color": st.session_state.get("STOCH_st_k_color", "#2962ff"), "lineWidth": int(st.session_state.get("STOCH_st_k_width", 2)), "priceLineVisible": False}},
                {"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_stoch_d"])} for r in records if pd.notna(r.get("calc_stoch_d")) and r["time"] > 0],
                 "options": {"color": st.session_state.get("STOCH_st_d_color", "#ff6d00"), "lineWidth": int(st.session_state.get("STOCH_st_d_width", 2)), "priceLineVisible": False}}
            ]
        }

    def make_atr_pane():
        return {
            "chart": {**base_chart, "height": 120, "timeScale": pane_ts, "rightPriceScale": {**base_chart["rightPriceScale"], "scaleMargins": {"top": 0.1, "bottom": 0.1}},
                      "watermark": {"visible": True, "text": f"ATR ({atr_len})", "fontSize": 16, "color": "#787b86", "horzAlign": "left", "vertAlign": "top"}},
            "series": [
                {"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_atr"])} for r in records if pd.notna(r.get("calc_atr")) and r["time"] > 0],
                 "options": {"color": st.session_state.get("ATR_st_color", "#ab47bc"), "lineWidth": int(st.session_state.get("ATR_st_width", 2)), "priceLineVisible": False}}
            ]
        }

    def make_adx_pane():
        mk = lambda v: [{"time": int(r["time"]), "value": v} for r in records if r["time"] > 0]
        return {
            "chart": {**base_chart, "height": 120, "timeScale": pane_ts, "rightPriceScale": {**base_chart["rightPriceScale"], "scaleMargins": {"top": 0.1, "bottom": 0.1}},
                      "watermark": {"visible": True, "text": f"ADX / DMI ({adx_len})", "fontSize": 16, "color": "#787b86", "horzAlign": "left", "vertAlign": "top"}},
            "series": [
                {"type": "Line", "data": mk(float(st.session_state.get("ADX_in_threshold", 25.0))), "options": {"color": "rgba(120,123,134,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_adx"])} for r in records if pd.notna(r.get("calc_adx")) and r["time"] > 0],
                 "options": {"color": st.session_state.get("ADX_st_adx_color", "#e040fb"), "lineWidth": int(st.session_state.get("ADX_st_adx_width", 2)), "priceLineVisible": False}},
                {"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_pdi"])} for r in records if pd.notna(r.get("calc_pdi")) and r["time"] > 0],
                 "options": {"color": st.session_state.get("ADX_st_pdi_color", "#00e676"), "lineWidth": 1, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_mdi"])} for r in records if pd.notna(r.get("calc_mdi")) and r["time"] > 0],
                 "options": {"color": st.session_state.get("ADX_st_mdi_color", "#ff5252"), "lineWidth": 1, "priceLineVisible": False, "lastValueVisible": False}}
            ]
        }

    def make_vol_pane():
        vol_bars = [{"time": int(r["time"]), "value": float(r.get("volume", 0)), "color": st.session_state.get("VOL_st_up_color", "#26a69a") if float(r.get("close", 0)) >= float(r.get("open", 0)) else st.session_state.get("VOL_st_down_color", "#ef5350")} for r in records if pd.notna(r.get("volume")) and r["time"] > 0]
        return {
            "chart": {**base_chart, "height": 120, "timeScale": pane_ts, "rightPriceScale": {**base_chart["rightPriceScale"], "scaleMargins": {"top": 0.1, "bottom": 0.0}},
                      "watermark": {"visible": True, "text": f"Volume ({vol_ma_len})", "fontSize": 16, "color": "#787b86", "horzAlign": "left", "vertAlign": "top"}},
            "series": [
                {"type": "Histogram", "data": vol_bars, "options": {"priceFormat": {"type": "volume"}, "priceLineVisible": False, "lastValueVisible": False}},
                {"type": "Line", "data": [{"time": int(r["time"]), "value": float(r["calc_vol_ma"])} for r in records if pd.notna(r.get("calc_vol_ma")) and r["time"] > 0],
                 "options": {"color": st.session_state.get("VOL_st_ma_color", "#ff9800"), "lineWidth": int(st.session_state.get("VOL_st_ma_width", 2)), "priceLineVisible": False, "lastValueVisible": False}}
            ]
        }

    # ประกอบชุดชาร์ตหลัก
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
        if st.session_state.get("ind_active_RSI", st.session_state.get("show_rsi_pane", True)):
            charts.append(make_rsi_pane())
        if st.session_state.get("ind_active_MACD", st.session_state.get("show_macd_pane", True)):
            charts.append(make_macd_pane())
        if st.session_state.get("ind_active_STOCH", False):
            charts.append(make_stoch_pane())
        if st.session_state.get("ind_active_ATR", False):
            charts.append(make_atr_pane())
        if st.session_state.get("ind_active_ADX", False):
            charts.append(make_adx_pane())
        if st.session_state.get("ind_active_VOL", False):
            charts.append(make_vol_pane())

    # ══════════════════════════════════════════════════════════
    # ตั้งค่าให้แถบวันที่/เวลาแสดงผล "เฉพาะหน้าต่างล่างสุดตัวเดียวเสมอ"
    # ══════════════════════════════════════════════════════════
    if charts:
     for i, c in enumerate(charts):
        c["chart"]["timeScale"] = dict(c["chart"].get("timeScale", pane_ts)).copy()
        c["chart"]["timeScale"]["visible"] = (i == len(charts) - 1)

    # ══════════════════════════════════════════════════════════
    # แสดงกล่อง HUD Dashboard สถิติกลยุทธ์มุมซ้ายล่างเหมือน TradingView (รูปที่ 2)
    # ══════════════════════════════════════════════════════════
    render_pine_hud_overlay()

    return charts
