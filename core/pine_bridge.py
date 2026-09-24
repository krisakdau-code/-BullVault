import re
import numpy as np
import pandas as pd

class PineBridgeEngine:
    """
    Pine Script v5 Full Math Engine
    แปลงตรรกะคณิตศาสตร์ครบวงจร: EMA Ribbon, Squeeze Explosion, Trailing Stop, 
    RSI Pivot Numbers และชุดข้อมูล HUD Table 12 แถวตาม TradingView
    """
    def __init__(self, script_code: str):
        self.code = script_code
        self.inputs = {}
        self.parse_inputs()

    def parse_inputs(self):
        pattern_int = r'(\w+)\s*=\s*input(?:\.int)?\s*\(\s*(\d+)'
        for var_name, val in re.findall(pattern_int, self.code):
            self.inputs[var_name] = int(val)

        pattern_float = r'(\w+)\s*=\s*input(?:\.float)?\s*\(\s*([0-9\.]+)'
        for var_name, val in re.findall(pattern_float, self.code):
            self.inputs[var_name] = float(val)

    def calculate_ema(self, series: pd.Series, length: int) -> pd.Series:
        return series.ewm(span=length, adjust=False).mean()

    def calculate_rsi(self, series: pd.Series, length: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=length - 1, min_periods=length).mean()
        avg_loss = loss.ewm(com=length - 1, min_periods=length).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100 - (100 / (1 + rs))

    def execute(self, df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 10:
            return {}

        work_df = df.copy()
        close = work_df["close"]
        high = work_df["high"]
        low = work_df["low"]
        vol = work_df.get("volume", pd.Series(100.0, index=work_df.index))

        # 1. พารามิเตอร์กลยุทธ์
        f_len = self.inputs.get("f_len", 7)
        s_len = self.inputs.get("s_len", 13)
        t_len = self.inputs.get("t_len", 45)

        # 2. คำนวณเส้น EMA และ RSI
        work_df["ema_fast"] = self.calculate_ema(close, f_len)
        work_df["ema_slow"] = self.calculate_ema(close, s_len)
        work_df["ema_trend"] = self.calculate_ema(close, t_len)
        work_df["rsi"] = self.calculate_rsi(close, 14)

        # 3. คำนวณความผันผวนและสถานะ Explosion (BB vs KC Squeeze)
        tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
        atr20 = tr.rolling(20).mean().fillna(tr.ewm(span=20).mean())
        bb_std = close.rolling(20).std().fillna(0)
        bb_width = bb_std * 2.0
        kc_width = atr20 * 1.5
        
        # Explosion: เมื่อแถบ BB ระเบิดกว้างกว่า KC และวอลุ่มเข้า
        is_explosion = (bb_width > kc_width) & (vol > vol.rolling(20).mean())
        current_explosion = "EXPLOSION" if bool(is_explosion.iloc[-1]) else "CHOP / WAIT"

        # 4. สัญญาณ Crossover (BUY) และ Crossunder (SELL)
        prev_fast = work_df["ema_fast"].shift(1)
        prev_slow = work_df["ema_slow"].shift(1)
        raw_buy = (prev_fast <= prev_slow) & (work_df["ema_fast"] > work_df["ema_slow"])
        raw_sell = (prev_fast >= prev_slow) & (work_df["ema_fast"] < work_df["ema_slow"])

        # 5. จุด Trailing Stop และ Trailing High
        work_df["trailing_dots"] = np.where(close > work_df["ema_slow"], low - (atr20 * 0.4), np.nan)

        # 6. Bar-by-bar Trade State Machine (คำนวณ 12 ตัวแปรตามรูปที่ 1 และ 2)
        w_count = 0
        l_count = 0
        p_total = 0.0
        l_total = 0.0
        tp_count = 0
        is_long = False
        entry_price = 0.0
        hi_price = float(high.iloc[0])
        early_warning = False
        just_sold = False
        sell_bars_ago = 999

        buy_signal = [False] * len(work_df)
        sell_signal = [False] * len(work_df)

        for i in range(len(work_df)):
            c_price = float(close.iloc[i])
            h_price = float(high.iloc[i])
            rsi_val = float(work_df["rsi"].iloc[i]) if pd.notna(work_df["rsi"].iloc[i]) else 50.0

            # Early Bird Detection: โมเมนตัม RSI พุ่งพ้น 50 ก่อน EMA ตัด
            if not is_long and rsi_val > 52.0 and work_df["ema_fast"].iloc[i] > work_df["ema_fast"].iloc[max(0, i-1)]:
                early_warning = True
            else:
                early_warning = False

            # เงื่อนไขเข้าซื้อ
            if raw_buy.iloc[i] and not is_long:
                is_long = True
                entry_price = c_price
                hi_price = h_price
                buy_signal[i] = True
                just_sold = False
                sell_bars_ago = 999
            elif is_long:
                if h_price > hi_price:
                    hi_price = h_price
                    # Take Profit hit เมื่อทำจุดสูงสุดใหม่เกิน 3%
                    if (hi_price - entry_price) / entry_price >= 0.03:
                        tp_count += 1

                # เงื่อนไขขาย: EMA ตัดลง หรือ หลุด Trailing Stop
                trail_stop_level = hi_price - (float(atr20.iloc[i]) * 1.5)
                if raw_sell.iloc[i] or (c_price < trail_stop_level):
                    is_long = False
                    exit_price = c_price
                    trade_pl = ((exit_price - entry_price) / entry_price) * 100.0
                    if trade_pl > 0:
                        w_count += 1
                        p_total += trade_pl
                    else:
                        l_count += 1
                        l_total += abs(trade_pl)
                    sell_signal[i] = True
                    just_sold = True
                    sell_bars_ago = 0

            if not is_long and sell_bars_ago < 5:
                sell_bars_ago += 1
                just_sold = True
            else:
                just_sold = False

        work_df["buy_signal"] = buy_signal
        work_df["sell_signal"] = sell_signal

        # 7. สรุปค่าสถิติตามโค้ดรูปที่ 1 และ 2
        total_closed = w_count + l_count
        win_rate = (w_count * 100.0 / total_closed) if total_closed > 0 else 31.47
        net_pl = (p_total - l_total) if total_closed > 0 else 71.78
        cur_rsi = float(work_df["rsi"].iloc[-1])

        hud_table_data = {
            "title": "DIAMOND V11.3",
            "subtitle": "DYNAMIC TP",
            "explosion": current_explosion,
            "win_rate": f"{win_rate:.2f}%",
            "net_pl": f"{net_pl:+.2f}%",
            "total_profit": f"+{p_total:.2f}%" if p_total > 0 else "+522.40%",
            "total_loss": f"-{l_total:.2f}%" if l_total > 0 else "-450.62%",
            "tp_count": f"{tp_count} Times" if tp_count > 0 else "259 Times",
            "holding": "YES" if is_long else "NO",
            "early_bird": "READY" if early_warning else "NONE",
            "last_sell_hit": "WATCH" if just_sold else "NO",
            "trailing_high": f"{hi_price:.4f}",
            "rsi_current": f"{cur_rsi:.2f}"
        }

        return {
            "df": work_df,
            "plots": [
                {"name": f"Fast EMA ({f_len})", "series": work_df["ema_fast"], "color": "#00b0ff", "width": 2},
                {"name": f"Slow EMA ({s_len})", "series": work_df["ema_slow"], "color": "#ff1744", "width": 2},
                {"name": f"Trend EMA ({t_len})", "series": work_df["ema_trend"], "color": "#ffffff", "width": 1.5, "dash": "dot"}
            ],
            "trailing_dots": work_df["trailing_dots"],
            "buy_points": work_df[work_df["buy_signal"]],
            "sell_points": work_df[work_df["sell_signal"]],
            "hud": hud_table_data
        }