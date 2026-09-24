import re
import numpy as np
import pandas as pd

class PineBridgeEngine:
    """
    Pine Script v5 Full Math Engine for Diamond Armor V11.3 - Infinite RSI + Explosion
    ถอดสูตรคณิตศาสตร์ตรงตามโค้ด TradingView ต้นฉบับ 100% พร้อมระบบควบคุมการแสดงผลทุกส่วน
    """
    def __init__(self, script_code: str = ""):
        self.code = script_code
        self.inputs = {
            "f_len": 7,
            "s_len": 13,
            "t_len": 45,
            "min_tp_pct": 3.0,
            "warn_pct": 3.0,
            "danger_pct": 7.0,
            "show_fast": True,
            "show_slow": True,
            "show_trend": True,
            "show_rsi_overlay": False,
            "show_star": True,
            "show_labels": True,
            "show_dots": True,
            "show_hud": True,
        }
        if self.code:
            self.parse_inputs()

    def parse_inputs(self):
        pattern_int = r'(\w+)\s*=\s*input(?:\.int)?\s*\(\s*(\d+)'
        for var_name, val in re.findall(pattern_int, self.code):
            self.inputs[var_name] = int(val)

        pattern_float = r'(\w+)\s*=\s*input(?:\.float)?\s*\(\s*([0-9\.]+)'
        for var_name, val in re.findall(pattern_float, self.code):
            self.inputs[var_name] = float(val)

        pattern_bool = r'(\w+)\s*=\s*input(?:\.bool)?\s*\(\s*(true|false)'
        for var_name, val in re.findall(pattern_bool, self.code, re.IGNORECASE):
            self.inputs[var_name] = (val.lower() == "true")

    def execute(self, df: pd.DataFrame, overrides: dict = None) -> dict:
        if df is None or df.empty or len(df) < 5:
            return {}

        work_df = df.copy()
        for col in ["open", "high", "low", "close", "volume"]:
            if col in work_df.columns:
                work_df[col] = pd.to_numeric(work_df[col], errors="coerce").fillna(0.0)

        close = work_df["close"]
        high = work_df["high"]
        low = work_df["low"]
        time_series = work_df["time"] if "time" in work_df.columns else pd.Series(range(len(work_df)))

        cfg = dict(self.inputs)
        if overrides:
            cfg.update(overrides)

        f_len = int(cfg.get("f_len", cfg.get("fast", 7)))
        s_len = int(cfg.get("s_len", cfg.get("slow", 13)))
        t_len = int(cfg.get("t_len", cfg.get("trend", 45)))
        min_tp_pct = float(cfg.get("min_tp_pct", 3.0))
        warn_pct = float(cfg.get("warn_pct", 3.0))
        danger_pct = float(cfg.get("danger_pct", 7.0))

        show_fast = bool(cfg.get("show_fast", True))
        show_slow = bool(cfg.get("show_slow", True))
        show_trend = bool(cfg.get("show_trend", True))
        show_rsi_overlay = bool(cfg.get("show_rsi_overlay", False))
        show_star = bool(cfg.get("show_star", True))
        show_labels = bool(cfg.get("show_labels", True))
        show_dots = bool(cfg.get("show_dots", True))
        show_hud = bool(cfg.get("show_hud", True))

        # 1. คำนวณเส้น EMA Ribbon
        ema_f = close.ewm(span=f_len, adjust=False).mean()
        ema_s = close.ewm(span=s_len, adjust=False).mean()
        ema_t = close.ewm(span=t_len, adjust=False).mean()

        # 2. คำนวณ RSI (14)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-9)
        rsi_v = (100.0 - (100.0 / (1.0 + rs))).fillna(50.0)

        # 3. จุดตัด Crossovers
        prev_f = ema_f.shift(1)
        prev_s = ema_s.shift(1)
        cross_up = (prev_f <= prev_s) & (ema_f > ema_s)
        cross_dn = (prev_f >= prev_s) & (ema_f < ema_s)

        # 4. Squeeze & Explosion
        hl = high - low
        is_sqz = (hl.rolling(10).mean() < hl.rolling(30).mean()) & ((ema_f - ema_s).abs() < (close * 0.005))
        mom10 = close - close.shift(10)
        is_boom = (rsi_v > 60) & (close > ema_f) & (mom10 > 0)
        explosion_status = "BOOM! 🚀" if bool(is_boom.iloc[-1]) else ("SQUEEZE 💎" if bool(is_sqz.iloc[-1]) else "CHOP / WAIT")

        # 5. Early Warning Detection
        lowest_l5 = low.rolling(5).min()
        lowest_rsi5 = rsi_v.rolling(5).min().shift(1)
        early_warning = (low == lowest_l5) & (rsi_v > lowest_rsi5) & (rsi_v < 40)

        prev_c = close.shift(1)
        prev_ef = ema_f.shift(1)
        c_cross_ef = (prev_c <= prev_ef) & (close > ema_f)
        ema3 = close.ewm(span=3, adjust=False).mean()
        prev_ema3 = ema3.shift(1)
        c_crossunder_ema3 = (prev_c >= prev_ema3) & (close < ema3)

        # RSI Scaled Overlay line
        ema20 = close.ewm(span=20, adjust=False).mean()
        rsi_scaled = ema20 * (1.0 + (rsi_v - 50.0) / 150.0)

        # 6. Bar-by-bar Trade State Machine
        hi_price = 0.0
        entry_p = 0.0
        is_long = False
        just_sold = False
        tp_count = 0

        p_total = 0.0
        l_total = 0.0
        w_count = 0
        l_count = 0

        markers = []
        warning_dots = [np.nan] * len(work_df)

        for i in range(len(work_df)):
            c = float(close.iloc[i])
            h = float(high.iloc[i])
            l = float(low.iloc[i])
            r = float(rsi_v.iloc[i])
            t_val = int(time_series.iloc[i])

            if t_val <= 0:
                continue

            # ดาวเตือนรอบเทรนด์ (⭐)
            if show_star and cross_up.iloc[i]:
                markers.append({"time": t_val, "position": "belowBar", "color": "#FFD700", "shape": "arrowUp", "text": "⭐"})
            if show_star and cross_dn.iloc[i]:
                markers.append({"time": t_val, "position": "aboveBar", "color": "#FFFFFF", "shape": "arrowDown", "text": "⭐"})

            # เงื่อนไขเข้าซื้อ
            b_sig = (cross_up.iloc[i] and c > ema_t.iloc[i]) or (just_sold and c_cross_ef.iloc[i] and c > ema_t.iloc[i])

            if b_sig and not is_long:
                is_long = True
                just_sold = False
                tp_count = 0
                entry_p = c
                hi_price = c
                if show_labels:
                    markers.append({"time": t_val, "position": "belowBar", "color": "#00e676", "shape": "arrowUp", "text": "🚀 BUY"})
            elif is_long:
                hi_price = max(hi_price, h)
                pnl = (c - entry_p) / entry_p * 100.0

                if pnl >= min_tp_pct and r > 65.0 and c_crossunder_ema3.iloc[i]:
                    tp_count += 1
                    if show_labels:
                        markers.append({"time": t_val, "position": "aboveBar", "color": "#00BCD4", "shape": "arrowDown", "text": "💎 TP"})

                if show_dots:
                    if c < hi_price * (1.0 - (danger_pct / 100.0)):
                        warning_dots[i] = h * 1.002
                    elif c < hi_price * (1.0 - (warn_pct / 100.0)):
                        warning_dots[i] = h * 1.001
            else:
                if show_dots and early_warning.iloc[i]:
                    warning_dots[i] = l * 0.998

            # เงื่อนไขขาย
            s_sig = is_long and cross_dn.iloc[i]
            if s_sig:
                is_long = False
                just_sold = True
                m_pnl = (c - entry_p) / entry_p * 100.0
                if m_pnl > 0:
                    p_total += m_pnl
                    w_count += 1
                else:
                    l_total += abs(m_pnl)
                    l_count += 1
                if show_labels:
                    markers.append({"time": t_val, "position": "aboveBar", "color": "#ff3366", "shape": "arrowDown", "text": "⚠️ SELL ALL"})
                hi_price = 0.0

        # สรุปสถิติ HUD Dashboard
        total_trades = w_count + l_count
        win_rate = (w_count * 100.0 / total_trades) if total_trades > 0 else 0.0
        net_pl = p_total - l_total

        hud = {
            "title": "DIAMOND V11.3",
            "subtitle": "DYNAMIC TP",
            "explosion": explosion_status,
            "win_rate": f"{win_rate:.2f}%",
            "net_pl": f"{net_pl:+.2f}%",
            "total_profit": f"+{p_total:.2f}%",
            "total_loss": f"-{l_total:.2f}%",
            "tp_count": f"{tp_count} Times",
            "holding": "YES" if is_long else "NO",
            "early_bird": "READY" if bool(early_warning.iloc[-1]) else "NONE",
            "last_sell_hit": "WATCH" if just_sold else "NO",
            "trailing_high": f"{hi_price:.4f}" if is_long else "0.0000",
            "rsi_current": f"{rsi_v.iloc[-1]:.2f}"
        }

        # รวบรวมเส้น Plot ตามสวิตช์เปิด-ปิด
        plots = []
        if show_fast:
            plots.append({"name": f"Fast EMA ({f_len})", "series": ema_f, "color": cfg.get("fast_color", "#2962ff"), "width": int(cfg.get("fast_width", 2))})
        if show_slow:
            plots.append({"name": f"Slow EMA ({s_len})", "series": ema_s, "color": cfg.get("slow_color", "#ff5252"), "width": int(cfg.get("slow_width", 2))})
        if show_trend:
            plots.append({"name": f"Trend EMA ({t_len})", "series": ema_t, "color": cfg.get("trend_color", "#ffffff"), "width": int(cfg.get("trend_width", 1)), "dash": "dot"})
        if show_rsi_overlay:
            plots.append({"name": "RSI Overlay", "series": rsi_scaled, "color": cfg.get("rsi_overlay_color", "#FFD700"), "width": int(cfg.get("rsi_overlay_width", 1))})

        return {
            "df": work_df,
            "plots": plots,
            "trailing_dots": pd.Series(warning_dots, index=work_df.index) if show_dots else pd.Series(dtype=float),
            "markers": markers,
            "hud": hud if show_hud else {}
        }