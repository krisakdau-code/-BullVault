# ui/right_panel.py — Complete Precision Market Analytics & Multi-Market Screener
from datetime import datetime, timedelta, timezone
import math
from data.candles import fetch_daily_bars
from data.fetchers import fetch_ohlcv, get_52w_range, get_ticker_24h
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from ui.seasonality_modal import show_seasonality_modal
from ui.technical_modal import show_technical_modal

TH_TZ = timezone(timedelta(hours=7))

# -------------------------------------------------------------
# หน้าต่างป๊อปอัปขยายใหญ่ส่วนบน: วินิจฉัยเชิงลึก (Deep Flow Diagnosis Modal)
# -------------------------------------------------------------
if hasattr(st, "dialog"):
  modal_dialog = st.dialog
elif hasattr(st, "experimental_dialog"):
  modal_dialog = st.experimental_dialog
else:

  def modal_dialog(title, width="large"):
    def decorator(func):
      def wrapper(*args, **kwargs):
        st.subheader(title)
        return func(*args, **kwargs)

      return wrapper

    return decorator


@modal_dialog(
    "🔍 การวินิจฉัยกระแสเงินทุนเชิงลึก (Deep Flow Diagnosis: การวินิจฉัยเชิงลึก)",
    width="large",
)
def show_upper_analysis_modal(data: dict):
  sym_name = data["sym_name"]
  tf_details = data.get("tf_details", {})

  tf_breakdown_html = f"""<div style="margin-top:12px; background:#0b0f19; padding:14px; border-radius:8px; border:1px solid #1e293b;">
<div style="font-weight:700; color:#38bdf8; font-size:14px; margin-bottom:10px;">
⏱️ เจาะลึกพฤติกรรมกราฟและวอลุ่มแยกรายกรอบเวลา (Multi-Timeframe Price Action & Volume Breakdown)
</div>
<div style="display:flex; flex-direction:column; gap:8px; font-size:13px; line-height:1.55;">
<div style="border-left:3px solid #38bdf8; padding-left:10px;">
<b style="color:#f8fafc;">• กรอบ 15m (จังหวะเข้าทำระยะสั้น):</b> <span style="color:#d1d5db;">{tf_details.get('15m', '-')}</span>
</div>
<div style="border-left:3px solid #00e676; padding-left:10px; background:rgba(0,230,118,0.05); padding-top:4px; padding-bottom:4px; border-radius:0 6px 6px 0;">
<b style="color:#00e676;">• กรอบ 1h (จังหวะผู้เล่นหลัก & รายชั่วโมง):</b> <span style="color:#f1f5f9;">{tf_details.get('1h', '-')}</span>
</div>
<div style="border-left:3px solid #ffb300; padding-left:10px;">
<b style="color:#f8fafc;">• กรอบ 4h (รอบสวิงและสภาพคล่องกลาง):</b> <span style="color:#d1d5db;">{tf_details.get('4h', '-')}</span>
</div>
<div style="border-left:3px solid #ff7d1e; padding-left:10px;">
<b style="color:#f8fafc;">• กรอบ 1D (แนวโน้มหลักภาพใหญ่):</b> <span style="color:#d1d5db;">{tf_details.get('1D', '-')}</span>
</div>
</div>
</div>"""

  st.markdown(
      f"""<div style="background:#0f172a; padding:22px; border-radius:12px; border:1px solid #F63B3B; margin-bottom:16px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-weight:bold; color:#FA6060; font-size:21px;">🎯 การวินิจฉัยกระแสเงินทุน: {sym_name}</span>
{data['liq_badge_modal']}
</div>
<div style="font-size:14.5px; color:#B89494; margin-top:8px;">
ตลาด: {data['exch_name']} • หมวด: {data['cat_name']} • ⏱️ กรอบเวลา (Analysis Timeframe: กรอบเวลาการวิเคราะห์): <b style="color:#38bdf8;">{data['tf_display']}</b>
</div>
<div style="margin-top:16px; background:#131722; padding:20px; border-radius:10px; border:1px solid #1e222d; font-size:15px;">
<div style="display:flex; justify-content:space-between; margin-bottom:6px;">
<span style="color:#C0A0A0; font-size:15.5px;">1. ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย):</span>
<b style="color:#FCF8F8; font-size:18px;">{data['turnover_val']:,.0f} {data['turnover_currency']}</b>
</div>
<div style="color:#38bdf8; font-size:13.5px; margin-bottom:8px;">
⏱️ กรอบเวลาการวิเคราะห์: <b>Multi-Timeframe (15m, 1h, 4h, 1D)</b>
</div>
<div style="color:#E1CBCB; font-size:14px; line-height:1.6; margin-bottom:14px;">• {data['liq_desc']}</div>
<div style="display:flex; justify-content:space-between; margin-bottom:8px;">
<span style="color:#C0A0A0; font-size:15.5px;">2. ดัชนีแรงซื้อสะสม (Accumulation Score: คะแนนแรงซื้อสะสม):</span>
<b style="color:{data['score_color']}; font-family:monospace; font-size:18px;">{data['score_bar']} ({data['accum_score']}/10)</b>
</div>
<div style="color:#E1CBCB; font-size:14px; line-height:1.6; margin-bottom:14px;">• {data['score_desc']}</div>
<div style="margin-top:12px; padding-top:12px; border-top:1px dashed #482D2D;">
<span style="color:#C0A0A0; font-size:15.5px;">3. การจำแนกพฤติกรรม:</span> <span style="font-size:15.5px;">{data['demand_status_modal']}</span>
<div style="color:#F9F1F1; font-size:15px; line-height:1.65; margin-top:8px;">{data['demand_article']}</div>
{tf_breakdown_html}
</div>
</div>
</div>""",
      unsafe_allow_html=True,
  )

  col1, col2 = st.columns(2)
  with col1:
    st.markdown(
        f"""<div style="background:#221313; padding:18px; border-radius:10px; border:1px solid #1e222d; margin-bottom:12px;">
<div style="font-size:16.5px; font-weight:bold; color:#f8fafc; margin-bottom:12px;">📌 โซนราคาสำคัญ (Key Levels: ระดับราคาสำคัญ)</div>
<div style="display:flex; justify-content:space-between; font-size:15px; color:#ef4444; padding:6px 0;">
<span>แนวต้านสำคัญ (Major Resistance)</span><b>{data['high_pivot']:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:15px; color:#38bdf8; padding:6px 0;">
<span>จุดกึ่งกลางดุลยภาพ (Equilibrium)</span><b>{data['fib_mid']:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:15px; color:#22c55e; padding:6px 0;">
<span>แนวรับสำคัญ (Major Support)</span><b>{data['low_pivot']:,.2f}</b>
</div>
</div>""",
        unsafe_allow_html=True,
    )

  with col2:
    st.markdown(
        """<div style="background:#131722; padding:18px; border-radius:10px; border:1px solid #1e222d; margin-bottom:12px;">
<div style="font-size:16.5px; font-weight:bold; color:#FCF8F8; margin-bottom:12px;">💡 คำแนะนำเชิงกลยุทธ์ (Tactical Guidance: คำแนะนำการวางแผน)</div>
<div style="font-size:14.5px; color:#E1CBCB; line-height:1.65;">
• หากคะแนนแรงซื้อสะสมมากกว่า 7/10 และสภาพคล่องสูง: สามารถวางแผนแบ่งไม้เข้าซื้อตามแนวรับเฉลี่ย<br>
• หากพบสัญญาณเตือนกับดักสภาพคล่อง (Bull Trap): หลีกเลี่ยงการไล่ราคา และตั้งจุดตัดขาดทุน (Stop Loss: จุดหยุดขาดทุน) อย่างเคร่งครัด
</div>
</div>""",
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------
# หน้าต่างป๊อปอัปขยายใหญ่ส่วนล่าง: เรดาร์คัดกรองตลาดฉบับเต็ม (Full Screener Modal)
# -------------------------------------------------------------
@modal_dialog(
    "📊 ศูนย์คัดกรองเรดาร์พหุสินทรัพย์ฉบับเต็ม (Full Multi-Market Screener)",
    width="large",
)
def show_bottom_screener_modal(modal_market_htmls: dict, default_market: str):
  options = [
      "🇹🇭 Bitkub (THB)",
      "🌐 Binance (USDT)",
      "📈 หุ้นไทย (SET)",
      "🌍 หุ้นต่างประเทศ (US)",
      "🪙 ตลาดทองคำ (Macro)",
      "🔄 คริปโตทางเลือกในแอป (Altcoins: เหรียญคริปโตอื่นๆ)",
  ]
  cur_idx = options.index(default_market) if default_market in options else 0
  selected_mkt = st.selectbox(
      "เลือกตลาดที่ต้องการสแกน (ฉบับเต็ม):",
      options=options,
      index=cur_idx,
      key="screener_modal_mkt_selector",
  )
  st.markdown(modal_market_htmls.get(selected_mkt, ""), unsafe_allow_html=True)


def fmt_price(v: float) -> str:
  if v is None:
    return "-"
  a = abs(v)
  if a >= 1000:
    return f"{v:,.2f}"
  if a >= 100:
    return f"{v:,.2f}"
  if a >= 1:
    return f"{v:,.3f}"
  if a >= 0.01:
    return f"{v:,.4f}"
  if a >= 0.0001:
    return f"{v:,.6f}"
  return f"{v:,.8f}"


def fmt_volume(v: float) -> str:
  if v >= 1_000_000:
    return f"{v/1_000_000:.2f}M"
  if v >= 1_000:
    return f"{v/1_000:.2f}K"
  return f"{v:,.0f}"


def fmt_pct(p: float) -> str:
  return f"{p:+.2f}%"


def calc_calendar_perf(daily_bars: list) -> dict:
  if not daily_bars:
    return {}

  def to_dt(t):
    return t if isinstance(t, datetime) else datetime.fromtimestamp(t, TH_TZ)

  bars = sorted(
      (
          {"dt": to_dt(b["time"]), "close": float(b["close"])}
          for b in daily_bars
          if b.get("close")
      ),
      key=lambda x: x["dt"],
  )
  if not bars:
    return {}

  last_close = bars[-1]["close"]
  now = bars[-1]["dt"]

  def close_on_or_before(target: datetime):
    cand = [b for b in bars if b["dt"] <= target]
    return cand[-1]["close"] if cand else bars[0]["close"]

  anchors = {
      "1W (1 สัปดาห์)": now - timedelta(days=7),
      "1M (1 เดือน)": now - timedelta(days=30),
      "3M (3 เดือน)": now - timedelta(days=90),
      "6M (6 เดือน)": now - timedelta(days=180),
      "YTD (ต้นปีถึงปัจจุบัน)": datetime(now.year, 1, 1, tzinfo=TH_TZ),
      "1Y (1 ปี)": now - timedelta(days=365),
  }

  out = {}
  for label, target in anchors.items():
    base = close_on_or_before(target)
    out[label] = ((last_close - base) / base * 100.0) if base else 0.0
  return out


# =========================================================================
# TACTICAL CONFLUENCE (TAB 1 กล่องย่อด่วน)
# =========================================================================
@st.cache_data(ttl=15, show_spinner=False)
def get_quick_mtf_confluence(sym_code: str):
  tfs = ["15m", "1h", "4h", "1D"]
  mtf_results = {}
  bullish_count = 0

  for tf in tfs:
    try:
      df_tf = fetch_ohlcv(sym_code, tf=tf, limit=20)
      if df_tf is not None and len(df_tf) >= 5:
        c = float(df_tf["close"].iloc[-1])
        ema_fast = float(df_tf["close"].ewm(span=7).mean().iloc[-1])
        ema_slow = float(df_tf["close"].ewm(span=13).mean().iloc[-1])

        if c > ema_fast and ema_fast > ema_slow:
          status = "bull"
          bullish_count += 1
        elif c < ema_fast and ema_fast < ema_slow:
          status = "bear"
        else:
          status = "neutral"
      else:
        status = "neutral"
    except Exception:
      status = "neutral"

    mtf_results[tf] = status

  return mtf_results, bullish_count


def render_tactical_box(df: pd.DataFrame, symbol: str):
  buy_pct = 50
  sell_pct = 50
  vol_multiplier = 1.0

  if df is not None and not df.empty and "volume" in df.columns:
    lookback = df.tail(15)
    up_vol = float(
        lookback[lookback["close"] >= lookback["open"]]["volume"].sum()
    )
    down_vol = float(
        lookback[lookback["close"] < lookback["open"]]["volume"].sum()
    )
    tot = up_vol + down_vol
    if tot > 0:
      buy_pct = int((up_vol / tot) * 100)
      sell_pct = 100 - buy_pct

    avg_vol = float(df["volume"].tail(30).mean())
    last_vol = float(df["volume"].iloc[-1])
    if avg_vol > 0:
      vol_multiplier = last_vol / avg_vol

  mtf_status, bull_score = get_quick_mtf_confluence(symbol)

  tf_badges = []
  for tf in ["15m", "1h", "4h", "1D"]:
    st_val = mtf_status.get(tf, "neutral")
    if st_val == "bull":
      badge = (
          f"<span style='color:#00e676; background:rgba(0,230,118,0.12);"
          f" padding:1px 5px; border-radius:3px; font-weight:700;'>{tf} ▲</span>"
      )
    elif st_val == "bear":
      badge = (
          f"<span style='color:#ff3366; background:rgba(255,51,102,0.12);"
          f" padding:1px 5px; border-radius:3px; font-weight:700;'>{tf} ▼</span>"
      )
    else:
      badge = (
          f"<span style='color:#ffb300; background:rgba(255,179,0,0.12);"
          f" padding:1px 5px; border-radius:3px; font-weight:600;'>{tf} ■</span>"
      )
    tf_badges.append(badge)

  if bull_score >= 3:
    conf_label = (
        f"<span style='color:#00e676;'>แรงซื้อหนุน {bull_score}/4 กรอบเวลา"
        " (Bullish Confluence)</span>"
    )
  elif bull_score <= 1:
    conf_label = (
        f"<span style='color:#ff3366;'>แรงขายกดดัน {4 - bull_score}/4 กรอบเวลา"
        " (Bearish Confluence)</span>"
    )
  else:
    conf_label = (
        "<span style='color:#ffb300;'>สัญญาณผสมผสาน ทรงตัวในกรอบ"
        " (Sideways)</span>"
    )

  vol_spike_text = (
      f"<span style='color:#ff9d42; font-weight:bold;'>🔥 วอลุ่มสูงผิดปกติ"
      f" {vol_multiplier:.1f}x (Spike)</span>"
      if vol_multiplier >= 1.5
      else f"<span style='color:#8b949e;'>วอลุ่มปกติ ({vol_multiplier:.1f}x"
      " เฉลี่ย)</span>"
  )

  tactical_html = f"""<div style="background:#0e1118; border:1px solid rgba(255,125,30,0.3); border-radius:8px; padding:10px 12px; margin-bottom:10px; box-shadow:0 0 10px rgba(255,125,30,0.08);">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
<span style="font-size:11px; font-weight:700; color:#ff9d42;">⚡ สัญญาณหลากกรอบเวลา (MTF Confluence)</span>
<div style="display:flex; gap:4px; font-size:10px; font-family:'JetBrains Mono', monospace;">{" ".join(tf_badges)}</div>
</div>
<div style="font-size:11px; margin-bottom:8px; font-weight:500;">{conf_label}</div>
<div style="height:1px; background:#1e2433; margin:8px 0;"></div>
<div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; font-weight:600; margin-bottom:4px; font-family:'JetBrains Mono', monospace;">
<span style="color:#00e676;">แรงซื้อ {buy_pct}%</span>
<span style="font-size:10.5px;">{vol_spike_text}</span>
<span style="color:#ff3366;">แรงขาย {sell_pct}%</span>
</div>
<div style="width:100%; height:6px; background:#ff3366; border-radius:3px; overflow:hidden; display:flex;">
<div style="width:{buy_pct}%; height:100%; background:#00e676; transition:width 0.3s ease;"></div>
</div>
</div>"""

  st.markdown(tactical_html, unsafe_allow_html=True)


# =========================================================================
# FULL MULTI-TIMEFRAME MATRIX GRID & DEEP ENGINE
# =========================================================================
@st.cache_data(ttl=15, show_spinner=False)
def get_detailed_mtf_matrix(symbol: str, is_liquid_asset: bool = True):
  """คำนวณตารางกริด MTF Matrix ภาษาไทย + Confluence Meter + คำอธิบายพฤติกรรมคนเล่นรายชั่วโมง"""
  tfs = ["15m", "1h", "4h", "1D"]
  matrix_rows = []
  tf_details = {}
  bull_count = 0
  bear_count = 0

  for tf in tfs:
    try:
      df_tf = fetch_ohlcv(symbol, tf=tf, limit=35)
      if df_tf is not None and len(df_tf) >= 15:
        c = df_tf["close"]
        c_last = float(c.iloc[-1])
        o_last = float(df_tf["open"].iloc[-1])

        # 1. แนวโน้ม (Trend)
        ema_fast = float(c.ewm(span=7).mean().iloc[-1])
        ema_slow = float(c.ewm(span=14).mean().iloc[-1])
        if c_last > ema_fast > ema_slow:
          trend_badge = '<span style="color:#00e676; font-weight:700;">🟢 ขาขึ้น</span>'
          t_state = 1
          bull_count += 1
        elif c_last < ema_fast < ema_slow:
          trend_badge = '<span style="color:#ff3366; font-weight:700;">🔴 ขาลง</span>'
          t_state = -1
          bear_count += 1
        else:
          trend_badge = '<span style="color:#ffb300; font-weight:600;">🟡 ไซด์เวย์</span>'
          t_state = 0

        # 2. โมเมนตัม RSI (14) ภาษาไทย
        delta = c.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean().iloc[-1]
        avg_loss = loss.rolling(window=14, min_periods=14).mean().iloc[-1]
        if avg_loss == 0 or np.isnan(avg_loss):
          rsi_val = 100.0 if avg_gain > 0 else 50.0
        else:
          rs = avg_gain / avg_loss
          rsi_val = 100.0 - (100.0 / (1.0 + rs))

        if rsi_val >= 58:
          mom_badge = (
              f'<span style="color:#00e676;">แรงส่งขึ้น ({rsi_val:.0f})</span>'
          )
          m_state = 1
        elif rsi_val <= 42:
          mom_badge = (
              f'<span style="color:#ff3366;">แรงกดลง ({rsi_val:.0f})</span>'
          )
          m_state = -1
        else:
          mom_badge = (
              f'<span style="color:#8b949e;">เป็นกลาง ({rsi_val:.0f})</span>'
          )
          m_state = 0

        # 3. สภาพคล่องวอลุ่ม (Volume Flow)
        vols = df_tf["volume"]
        v_avg = float(vols.tail(20).mean())
        v_last = float(vols.iloc[-1])
        v_mult = (v_last / v_avg) if v_avg > 0 else 1.0

        if v_mult >= 1.3 and c_last >= o_last:
          vol_badge = '<span style="color:#00e676;">🟢 ซื้อหนุน</span>'
          v_state = "buy_heavy"
        elif v_mult >= 1.3 and c_last < o_last:
          vol_badge = '<span style="color:#ff3366;">🔴 เทขาย</span>'
          v_state = "sell_heavy"
        elif v_mult < 0.7:
          vol_badge = '<span style="color:#6b7280;">⚪ วอลุ่มบาง</span>'
          v_state = "thin"
        else:
          vol_badge = '<span style="color:#d1d5db;">ปกติ</span>'
          v_state = "normal"

        # 4. หน้าเทรด (Action Bias) ภาษาไทยมืออาชีพ
        if t_state == 1 and m_state >= 0:
          action_txt = "ดักย่อซื้อ (Long)"
          act_col = "#00e676"
        elif t_state == -1 and m_state <= 0:
          action_txt = "ดักเด้งขาย (Short)"
          act_col = "#ff3366"
        elif t_state == 1 and m_state == -1:
          action_txt = "ระวังพักตัว"
          act_col = "#ffb300"
        elif t_state == -1 and m_state == 1:
          action_txt = "ลุ้นรีบาวด์"
          act_col = "#38bdf8"
        else:
          action_txt = "รอทะลุกรอบ"
          act_col = "#8b949e"

        # 5. วิเคราะห์เจาะลึกพฤติกรรมผู้เล่น & การปั่นกระแส
        if tf == "15m":
          if t_state == 1 and v_state == "buy_heavy":
            desc = (
                "เกิดการดูดซับแรงขาย (Absorption) เหนือแนวรับสั้น มีแรงเคาะขวา"
                f" หนุนวอลุ่มเข้า {v_mult:.1f}x แรงส่งขาขึ้นเปิดทางเล่นรอบเร็ว"
            )
          elif t_state == 1:
            desc = (
                "ราคายกฐานสูงขึ้นต่อเนื่องเหนือ EMA7 โมเมนตัมทรงตัวรอแรงกระตุ้น"
                " ปริมาณขายกดดันไม่หนาแน่น"
            )
          elif t_state == -1:
            desc = (
                "โครงสร้างราคาทำ Lower Low ระยะสั้น แรงขายกดดันหลุดเส้นเฉลี่ย"
                " ระวังการย่อตัวทดสอบโซนรับล่าง"
            )
          else:
            desc = (
                "บีบตัวพักในกรอบแคบ สเปรดแท่งเทียนสั้น วอลุ่มชะลอตัว"
                " เป็นพฤติกรรมรอเลือกทิศทางเบรกเอาต์"
            )

        elif tf == "1h":
          # กรอบ 1 ชั่วโมง: เจาะจงจังหวะของคนที่เล่นกับตัวนี้ (Organic vs Manipulated/Pump)
          if t_state == 1 and not is_liquid_asset:
            desc = (
                "<b>คาดการณ์: จังหวะคนเล่นเป็นแรงซื้อขายปั่นกระแส</b> —"
                " แท่งเทียน 1 ชม. ยกตัวขึ้นในภาวะสภาพคล่องกระดานเบาบาง"
                " เป็นจังหวะเคาะกระตุ้นความโลภ (Speculative Pump / Bull Trap)"
                " ระวังคนคุมราคาเทขายทุบทำกำไรฉับพลัน"
            )
          elif t_state == 1 and v_state == "buy_heavy" and is_liquid_asset:
            desc = (
                "<b>คาดการณ์: จังหวะคนเล่นเป็นโมเมนตัมแรงซื้อจริงไม่ปั่น</b> —"
                " ตรวจพบเม็ดเงินคนเล่นก้อนใหญ่เคาะซื้อจริงจังในรอบชั่วโมง"
                f" วอลุ่มหนุนสูง {v_mult:.1f}x ยก High/Low ชัดเจน"
                " สะท้อนผู้เล่นหลักกำลังดันราคาตามรอบ (Mark-up Phase)"
            )
          elif t_state == 1 and is_liquid_asset:
            desc = (
                "<b>คาดการณ์: คนเล่นหลักคุมเกมประคองเทรนด์ (ไม่ปั่น)</b> —"
                " ราคายืนแกร่งเหนือ EMA14 โมเมนตัมรายชั่วโมงเสถียร"
                " มีการวาง Bid ดักรับของอย่างเป็นระบบ การพักตัวเป็นการย่อสะสมพลัง"
            )
          elif t_state == -1 and v_state == "sell_heavy":
            desc = (
                "<b>คาดการณ์: จังหวะคนเล่นหลักเทขายระบายของจริง</b> —"
                f" ปริมาณคำสั่งขายในรอบ 1 ชม. ไหลออกหนาแน่น {v_mult:.1f}x"
                " หลุดแนวรับสั้น ทุนใหญ่ยังไม่เข้ารับของ หลีกเลี่ยงการสวนทาง"
            )
          elif t_state == -1:
            desc = (
                "<b>คาดการณ์: โมเมนตัมซึมลงตามกลไกตลาด</b> —"
                " ขาดแรงซื้อจากผู้เล่นหลัก ราคาอ่อนตัวลงตามธรรมชาติ"
                " ยังไม่พบสัญญาณกระตุกทำรอบของกลุ่มเก็งกำไร"
            )
          else:
            desc = (
                "<b>คาดการณ์: จังหวะคนเล่นยังกบดานดูเชิง</b> —"
                " สภาพคล่องรายชั่วโมงทรงตัวในกรอบสมดุล ปริมาณซื้อขายแห้งลง"
                " เป็นพฤติกรรมสะสมของเงียบๆ รอจังหวะจุดพลุทำราคาใหม่"
            )

        elif tf == "4h":
          if t_state == 1:
            desc = (
                "รอบสวิงระยะกลางยังคงสถานะขาขึ้นแข็งแกร่ง"
                " การพักตัวในกรอบสั้นไม่กระทบแนวโน้มหลัก"
                " เป็นโซนดักสะสมสถานะรอบใหญ่"
            )
          elif t_state == -1:
            desc = (
                "แนวโน้มระยะกลางอยู่ในช่วงปรับฐาน (Correction Phase)"
                " โซนแนวต้านกดต่ำลงต่อเนื่อง ยังไม่พบสัญญาณ Divergence กลับตัว"
            )
          else:
            desc = (
                "เกิดภาวะกรอบราคาบีบอัดตัว (Volatility Squeeze)"
                " ความผันผวนลดลงต่ำสุด เป็นพฤติกรรมกักเก็บพลังงานก่อนระเบิดเทรนด์"
            )

        else:  # 1D
          if t_state == 1:
            desc = (
                "เทรนด์ภาพใหญ่ระดับวันยืนยันขาขึ้นสมบูรณ์แบบ"
                " กระแสเงินทุนหลักยังถือครองสถานะ โครงสร้างแข็งแกร่งสูงสุด"
            )
          elif t_state == -1:
            desc = (
                "ภาพใหญ่ยังอยู่ใต้แนวโน้มขาลง การปรับขึ้นระยะสั้นเป็นเพียง Technical"
                " Rebound ยังต้องระมัดระวังแรงขายตามรอบ"
            )
          else:
            desc = (
                "ภาพรวมระดับวันแกว่งตัวในกรอบกว้าง (Trading Range)"
                " รอการคอนเฟิร์มทะลุแนวต้านหรือหลุดแนวรับใหญ่"
            )

        tf_details[tf] = desc

        matrix_rows.append({
            "tf": tf,
            "trend": trend_badge,
            "mom": mom_badge,
            "vol": vol_badge,
            "action": (
                f'<span style="color:{act_col}; font-weight:bold;">{action_txt}</span>'
            ),
        })
      else:
        matrix_rows.append({
            "tf": tf,
            "trend": "⚪ N/A",
            "mom": "⚪ N/A",
            "vol": "⚪ N/A",
            "action": '<span style="color:#6b7280;">รอข้อมูล</span>',
        })
        tf_details[tf] = "ข้อมูลแท่งเทียนไม่เพียงพอสำหรับการวิเคราะห์พฤติกรรม"
    except Exception:
      matrix_rows.append({
          "tf": tf,
          "trend": "⚪ N/A",
          "mom": "⚪ N/A",
          "vol": "⚪ N/A",
          "action": '<span style="color:#6b7280;">รอข้อมูล</span>',
      })
      tf_details[tf] = "เกิดข้อผิดพลาดในการดึงข้อมูลกรอบเวลานี้"

  # สรุป Confluence Meter
  if bull_count >= 3:
    summary_label = (
        f"🟢 สอดคล้องฝั่งซื้อ {bull_count}/4 TF (Bullish Alignment)"
    )
    meter_pct = int((bull_count / 4.0) * 100)
    meter_color = "#00e676"
  elif bear_count >= 3:
    summary_label = f"🔴 สอดคล้องฝั่งขาย {bear_count}/4 TF (Bearish Alignment)"
    meter_pct = int((bear_count / 4.0) * 100)
    meter_color = "#ff3366"
  else:
    summary_label = "🟡 สัญญาณผสมผสานในกรอบ (Mixed Alignment)"
    meter_pct = 50
    meter_color = "#ffb300"

  return (
      matrix_rows,
      summary_label,
      meter_pct,
      meter_color,
      tf_details,
      bull_count,
  )


# =========================================================================
# 1. Fragment กล่องราคาด้านบน: อัปเดตเฉพาะตัวเลขราคาและค่า Bid/Ask ทุก 5 วินาที
# =========================================================================
@st.fragment(run_every=5)
def render_price_quote_fragment(
    df: pd.DataFrame, meta: dict, is_thb_mode: bool, fx_rate: float
):
  mult = (
      fx_rate if (is_thb_mode and not meta.get("is_thb_native", False)) else 1.0
  )
  symbol = meta.get("symbol", "")
  ticker = get_ticker_24h(symbol)

  if ticker:
    curr_p = (
        float(df["close"].iloc[-1]) * mult
        if (df is not None and not df.empty)
        else (ticker["last"] * mult)
    )
    chg_pct = ticker["change_pct"]
    chg_val = ticker["change_abs"] * mult
    bid_val = ticker["bid"] * mult
    ask_val = ticker["ask"] * mult
  else:
    curr_p = float(df["close"].iloc[-1]) * mult
    prev_p = float(df["close"].iloc[-2]) * mult
    chg_val = curr_p - prev_p
    chg_pct = (chg_val / prev_p * 100) if prev_p else 0.0
    bid_val = curr_p * 0.999
    ask_val = curr_p * 1.001

  display_unit = (
      "THB (บาท)"
      if (is_thb_mode or meta.get("is_thb_native", False))
      else meta.get("unit", "USD")
  )
  color_hex = "#00e676" if chg_val >= 0 else "#ff5252"
  sign = "+" if chg_val >= 0 else ""

  st.markdown(
      f"""<div style="background:#131722; padding:12px; border-radius:8px; border-left:3px solid {color_hex}; margin-bottom:10px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:bold; font-size:16px; color:#fff;">{meta.get('display_name', meta.get('symbol', ''))}</span>
    <span style="color:#00e676; font-size:11px; font-weight:bold;">● ตลาดเปิด</span>
    </div>
    <div style="color:#867878; font-size:12px;">{meta.get('exchange', 'BINANCE')} • {meta.get('category', 'Crypto')}</div>
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:4px; margin-bottom:8px;">
      <div>
         <span style="font-size:24px; font-weight:800; color:#ffffff; font-family:'JetBrains Mono', monospace; letter-spacing:-0.5px;">
            {fmt_price(curr_p)}
         </span>
         <span style="font-size:12px; color:#867878; font-weight:600; margin-left:3px;">
            {display_unit}
         </span>
      </div>
      <div style="text-align:right;">
          <span style="color:{color_hex}; font-size:17px; font-weight:800; font-family:'JetBrains Mono', monospace;">
            {sign}{fmt_price(chg_val)} ({sign}{chg_pct:.2f}%)
          </span>
      </div>
    </div>
    <div style="display:flex; gap:6px; margin-top:8px;">
    <div style="flex:1; background:#1e293b; padding:4px; border-radius:4px; text-align:center; color:#38bdf8; font-size:11px;">
    Bid (เสนอซื้อ) {fmt_price(bid_val)}
    </div>
    <div style="flex:1; background:#33141e; padding:4px; border-radius:4px; text-align:center; color:#ff5252; font-size:11px;">
    Ask (เสนอขาย) {fmt_price(ask_val)}
    </div>
    </div>
    </div>""",
      unsafe_allow_html=True,
  )


# =========================================================================
# 2. Fragment เข็มเลขไมล์: อัปเดตเฉพาะเข็มชี้วัดและสถานะเทคนิคทุก 5 วินาที
# =========================================================================
@st.fragment(run_every=5)
def render_gauge_fragment(symbol: str, df: pd.DataFrame):
  ticker = get_ticker_24h(symbol)
  if ticker and "change_pct" in ticker:
    live_chg_pct = float(ticker["change_pct"])
  elif df is not None and len(df) >= 2:
    last_c = float(df["close"].iloc[-1])
    prev_c = float(df["close"].iloc[-2])
    live_chg_pct = (
        ((last_c - prev_c) / prev_c * 100.0) if prev_c > 0 else 0.0
    )
  else:
    live_chg_pct = 0.0

  gauge_score = max(-2.0, min(2.0, live_chg_pct / 0.8))

  if gauge_score <= -1.2:
    status_text = "มีแรงขายรุนแรง"
    status_color = "#ff3366"
    glow_color = "rgba(255, 51, 102, 0.3)"
  elif gauge_score <= -0.4:
    status_text = "มีแรงขาย"
    status_color = "#ff7b72"
    glow_color = "rgba(255, 123, 114, 0.25)"
  elif gauge_score < 0.4:
    status_text = "เป็นกลาง"
    status_color = "#8b949e"
    glow_color = "rgba(139, 148, 158, 0.2)"
  elif gauge_score < 1.2:
    status_text = "มีแรงซื้อ"
    status_color = "#3fb950"
    glow_color = "rgba(63, 185, 80, 0.25)"
  else:
    status_text = "มีแรงซื้อรุนแรง"
    status_color = "#00f59b"
    glow_color = "rgba(0, 245, 155, 0.35)"

  deg = 180.0 - ((gauge_score + 2.0) / 4.0) * 180.0
  rad = math.radians(deg)
  cx, cy, r_needle = 140, 100, 60
  tx = cx + r_needle * math.cos(rad)
  ty = cy - r_needle * math.sin(rad)

  gauge_html = f"""
    <!DOCTYPE html>
    <html translate="no" class="notranslate">
    <head>
        <meta charset="utf-8">
        <meta name="google" content="notranslate">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            body {{ background: transparent; overflow: hidden; }}
            .gauge-card {{
                background: linear-gradient(180deg, #221313 0%, #170D0D 100%);
                border: 1px solid #2D2121;
                border-radius: 8px;
                padding: 10px 12px;
                text-align: center;
            }}
            .header-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2px;
            }}
            .title-lbl {{
                font-size: 12px;
                font-weight: 700;
                color: #c9d1d9;
            }}
            .status-badge {{
                font-size: 11px;
                font-weight: 700;
                color: {status_color};
                background: {glow_color};
                padding: 2px 8px;
                border-radius: 12px;
                border: 1px solid {status_color}55;
            }}
            .summary-txt {{
                font-size: 14px;
                font-weight: 800;
                color: {status_color};
                margin-top: -6px;
            }}
        </style>
    </head>
    <body>
        <div class="gauge-card notranslate" translate="no">
            <div class="header-row">
                <span class="title-lbl">ทางเทคนิค (Technical Summary)</span>
                <span class="status-badge">● {status_text}</span>
            </div>

            <svg width="280" height="110" viewBox="0 0 280 110" style="display: block; margin: 0 auto; overflow: visible;">
                <defs>
                    <linearGradient id="cyberArc" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#ff1744" />
                        <stop offset="25%" stop-color="#ff5252" />
                        <stop offset="50%" stop-color="#484f58" />
                        <stop offset="75%" stop-color="#2ea043" />
                        <stop offset="100%" stop-color="#00f59b" />
                    </linearGradient>
                </defs>
                <path d="M 45,100 A 95,95 0 0,1 235,100" fill="none" stroke="#1f242c" stroke-width="8" stroke-linecap="round" />
                <path d="M 45,100 A 95,95 0 0,1 235,100" fill="none" stroke="url(#cyberArc)" stroke-width="5" stroke-linecap="round" />
                <text x="32" y="106" font-size="8" fill="#816E6E" text-anchor="middle">มีแรงขายรุนแรง</text>
                <text x="65" y="44" font-size="8" fill="#816E6E" text-anchor="middle">มีแรงขาย</text>
                <text x="140" y="18" font-size="9" font-weight="700" fill="#9E8B8B" text-anchor="middle">เป็นกลาง</text>
                <text x="215" y="44" font-size="8" fill="#816E6E" text-anchor="middle">มีแรงซื้อ</text>
                <text x="248" y="106" font-size="8" fill="#816E6E" text-anchor="middle">มีแรงซื้อรุนแรง</text>
                <line x1="{cx}" y1="{cy}" x2="{tx}" y2="{ty}" stroke="#FCF0F0" stroke-width="2.5" stroke-linecap="round" />
                <circle cx="{cx}" cy="{cy}" r="5" fill="#221616" stroke="{status_color}" stroke-width="2" />
                <circle cx="{cx}" cy="{cy}" r="2" fill="#FCF0F0" />
            </svg>
            <div class="summary-txt">{status_text}</div>
        </div>
    </body>
    </html>
    """
  components.html(gauge_html, height=155)


# =========================================================================
# 3. ฟังก์ชันหลักของแผงขวา
# =========================================================================
def render_right_panel(
    df: pd.DataFrame,
    meta: dict,
    is_thb_mode: bool = False,
    fx_rate: float = 35.0,
):
  if df.empty or len(df) < 2:
    st.warning("ไม่มีข้อมูลแท่งเทียนเพียงพอสำหรับการวิเคราะห์")
    return

  mult = (
      fx_rate if (is_thb_mode and not meta.get("is_thb_native", False)) else 1.0
  )
  symbol = meta.get("symbol", "")
  ticker = get_ticker_24h(symbol)

  if ticker:
    curr_p = (
        float(df["close"].iloc[-1]) * mult
        if (df is not None and not df.empty)
        else (ticker["last"] * mult)
    )
    chg_pct = ticker.get("change_pct", 0.0)
    d_low = ticker["low_24h"] * mult
    d_high = ticker["high_24h"] * mult
    vol_curr = ticker["base_volume"]
  elif len(df) >= 2:
    curr_p = float(df["close"].iloc[-1]) * mult
    prev_p = float(df["close"].iloc[-2]) * mult
    chg_pct = ((curr_p - prev_p) / prev_p * 100.0) if prev_p > 0 else 0.0
    d_low = float(df["low"].tail(24).min()) * mult
    d_high = float(df["high"].tail(24).max()) * mult
    vol_curr = float(df["volume"].iloc[-1])
  else:
    curr_p = (
        float(df["close"].iloc[-1]) * mult
        if (df is not None and not df.empty)
        else 0.0
    )
    chg_pct = 0.0
    d_low = curr_p
    d_high = curr_p
    vol_curr = 0.0

  daily_bars = fetch_daily_bars(symbol, 400) or []
  rng_52 = get_52w_range(symbol, fetch_daily_bars)
  w_low = (
      rng_52["low"] * mult
      if rng_52["low"] > 0
      else (float(df["low"].min()) * mult if not df.empty else 0.0)
  )
  w_high = (
      rng_52["high"] * mult
      if rng_52["high"] > 0
      else (float(df["high"].max()) * mult if not df.empty else 0.0)
  )

  vol_avg = (
      float(np.mean([b["volume"] for b in daily_bars[-30:]]))
      if len(daily_bars) >= 10
      else (float(df["volume"].tail(30).mean()) if not df.empty else 0.0)
  )
  perfs = calc_calendar_perf(daily_bars)

  display_unit = (
      "THB (บาท)"
      if (is_thb_mode or meta.get("is_thb_native", False))
      else meta.get("unit", "USD")
  )

  tab_overview, tab_pro = st.tabs(
      ["📊 ภาพรวมตลาด", "🧠 วิเคราะห์ข้อมูล & เทคนิค"]
  )

  with tab_overview:
    # =========================================================
    # แท็บ 1 ส่วนบน: กล่องเลื่อนอิสระส่วนบน
    # =========================================================
    with st.container(height=390):
      render_price_quote_fragment(
          df=df, meta=meta, is_thb_mode=is_thb_mode, fx_rate=fx_rate
      )

      d_pct = max(
          0,
          min(
              100,
              int(
                  ((curr_p - d_low) / (d_high - d_low) * 100)
                  if d_high > d_low
                  else 50
              ),
          ),
      )
      w_pct = max(
          0,
          min(
              100,
              int(
                  ((curr_p - w_low) / (w_high - w_low) * 100)
                  if w_high > w_low
                  else 50
              ),
          ),
      )

      st.markdown(
          f"""<div style="background:#131722; padding:10px; border-radius:8px; margin-bottom:10px; font-size:11px;">
<div style="display:flex; justify-content:space-between; color:#867878;">
<span>{fmt_price(d_low)}</span><span style="color:#DCD1D1;">ช่วงระหว่างวัน (Day Range)</span><span>{fmt_price(d_high)}</span>
</div>
<div style="height:4px; background:#392A2A; border-radius:2px; margin:6px 0; position:relative;">
<div style="height:100%; width:{d_pct}%; background:#FF8629; border-radius:2px;"></div>
</div>
<div style="display:flex; justify-content:space-between; color:#867878; margin-top:8px;">
<span>{fmt_price(w_low)}</span><span style="color:#DCD1D1;">รอบ 52 สัปดาห์ (52-Week Range)</span><span>{fmt_price(w_high)}</span>
</div>
<div style="height:4px; background:#392A2A; border-radius:2px; margin:6px 0; position:relative;">
<div style="height:100%; width:{w_pct}%; background:#00e676; border-radius:2px;"></div>
</div>
</div>""",
          unsafe_allow_html=True,
      )

      # กล่องสัญญาณด่วน: MTF Confluence & สัดส่วนแรงซื้อขาย
      render_tactical_box(df, symbol)

      st.markdown(
          f"""<div style="display:flex; justify-content:space-between; font-size:11px; color:#867878; padding:4px 2px;">
<span>ปริมาณการซื้อขาย (Volume)</span><span style="color:#fff; font-weight:bold;">{fmt_volume(vol_curr)}</span>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:#867878; padding:4px 2px; margin-bottom:10px;">
<span>ปริมาณเฉลี่ย (Average Volume 30 แท่ง)</span><span style="color:#fff; font-weight:bold;">{fmt_volume(vol_avg)}</span>
</div>""",
          unsafe_allow_html=True,
      )

      cols = st.columns(3)
      for idx, (label, val) in enumerate(perfs.items()):
        c_hex = "#00e676" if val >= 0 else "#ff5252"
        s_sign = "+" if val >= 0 else ""
        cols[idx % 3].markdown(
            f"""<div style="background:#131722; padding:6px; border-radius:4px; text-align:center; margin-bottom:6px;">
<div style="font-size:12px; font-weight:bold; color:{c_hex};">{s_sign}{val:.2f}%</div>
<div style="font-size:10px; color:#867878;">{label}</div>
</div>""",
            unsafe_allow_html=True,
        )

    # =========================================================
    # แท็บ 1 ส่วนล่าง: กล่องเลื่อนอิสระส่วนล่าง
    # =========================================================
    with st.container(height=390):
      st.markdown(
          "<div style='font-size:12px; font-weight:bold; color:#d1d4dc;"
          " margin:4px 0 2px 0;'>สถิติแนวโน้มฤดูกาล (Seasonality Trend)</div>",
          unsafe_allow_html=True,
      )
      fig_season = go.Figure()
      x_months = ["ม.ค.", "มี.ค.", "พ.ค.", "ก.ค.", "ก.ย.", "พ.ย."]
      fig_season.add_trace(
          go.Scatter(
              x=x_months,
              y=[0, 4, 8, 12, 10, 16],
              mode="lines",
              line=dict(color="#ff9800", width=1.5),
              name="2024",
          )
      )
      fig_season.add_trace(
          go.Scatter(
              x=x_months,
              y=[0, -2, -1, 3, 2, 4],
              mode="lines",
              line=dict(color="#00e676", width=1.5),
              name="2025",
          )
      )
      fig_season.add_trace(
          go.Scatter(
              x=x_months[:4],
              y=[0, -4, -6, 2],
              mode="lines+markers",
              line=dict(color="#2962ff", width=2),
              name="2026",
          )
      )
      fig_season.update_layout(
          height=120,
          margin=dict(l=0, r=0, t=5, b=5),
          showlegend=True,
          plot_bgcolor="rgba(0,0,0,0)",
          paper_bgcolor="rgba(0,0,0,0)",
          legend=dict(
              orientation="h", y=1.2, x=0.2, font=dict(size=9, color="#867878")
          ),
          xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#867878")),
          yaxis=dict(
              showgrid=True,
              gridcolor="#1e222d",
              tickfont=dict(size=9, color="#867878"),
          ),
      )
      st.plotly_chart(
          fig_season,
          use_container_width=True,
          config={"displayModeBar": False},
      )

      if st.button(
          "ฤดูกาลเพิ่มเติม",
          key="btn_open_seasonality_modal",
          use_container_width=True,
          type="secondary",
      ):
        show_seasonality_modal(
            sym=st.session_state.get("current_symbol", "BTCUSDT")
        )

      render_gauge_fragment(symbol=symbol, df=df)

      if st.button(
          "ทางเทคนิคเพิ่มเติม", use_container_width=True, type="secondary"
      ):
        show_technical_modal(
            sym=st.session_state.get("current_symbol", "BTCUSDT")
        )

  # -------------------------------------------------------------
  # แท็บ 2: ยุทธศาสตร์ & MULTI-TIMEFRAME MATRIX GRID
  # -------------------------------------------------------------
  with tab_pro:
    sym_name = meta.get(
        "display_name", meta.get("symbol", "สินทรัพย์ปัจจุบัน")
    )
    exch_name = str(meta.get("exchange", "BINANCE")).upper()
    cat_name = str(meta.get("category", "Crypto")).upper()

    vol_recent = (
        float(df["volume"].tail(24).sum())
        if len(df) >= 24
        else float(df["volume"].sum())
    )
    turnover_val = vol_recent * (curr_p / mult)

    if "SET" in exch_name or "STOCK" in cat_name:
      min_turnover = 5_000_000.0
      turnover_currency = "THB (บาท)"
    elif "BITKUB" in exch_name:
      min_turnover = 1_000_000.0
      turnover_currency = "THB (บาท)"
    elif "GOLD" in sym_name.upper() or "XAU" in sym_name.upper():
      min_turnover = 100_000.0
      turnover_currency = "USD (ดอลลาร์สหรัฐ)"
    else:
      min_turnover = 1_000_000.0
      turnover_currency = "USD (ดอลลาร์สหรัฐ)"

    is_liquid = turnover_val >= min_turnover
    if is_liquid:
      liq_badge = (
          '<span style="color:#00e676; background:rgba(0,230,118,0.15);'
          " padding:3px 8px; border-radius:6px; font-weight:bold;"
          ' font-size:11.5px;">🟢 สภาพคล่องสูง</span>'
      )
      liq_badge_modal = (
          '<span style="color:#00e676; background:rgba(0,230,118,0.15);'
          " padding:5px 14px; border-radius:8px; font-weight:bold;"
          ' font-size:14.5px;">🟢 สภาพคล่องสูง (High Liquidity:'
          " มีสภาพคล่องหนาแน่น)</span>"
      )
      liq_desc = (
          "ปริมาณเงินหมุนเวียนหนาแน่นเพียงพอ"
          " ปราศจากความเสี่ยงเรื่องการขาดสภาพคล่องหรือราคาคลาดเคลื่อนสูง"
          " (Slippage: ส่วนต่างราคาคำสั่งซื้อขาย)"
      )
    else:
      liq_badge = (
          '<span style="color:#ff9800; background:rgba(255,152,0,0.15);'
          " padding:3px 8px; border-radius:6px; font-weight:bold;"
          ' font-size:11.5px;">⚠️ สภาพคล่องต่ำ</span>'
      )
      liq_badge_modal = (
          '<span style="color:#ff9800; background:rgba(255,152,0,0.15);'
          " padding:5px 14px; border-radius:8px; font-weight:bold;"
          ' font-size:14.5px;">⚠️ สภาพคล่องต่ำ (Low Liquidity Trap:'
          " กับดักสภาพคล่องแห้ง)</span>"
      )
      liq_desc = (
          "ยอดเงินหมุนเวียนเบาบางกว่าเกณฑ์มาตรฐานความปลอดภัย"
          " ระวังคำสั่งซื้อขายจับคู่ไม่สมบูรณ์หรือการเคาะราคาในช่องว่าง (Thin"
          " Order Book: กระดานซื้อขายเบาบาง)"
      )

    recent_bars = df.tail(15)
    green_vol = recent_bars[recent_bars["close"] >= recent_bars["open"]][
        "volume"
    ].sum()
    red_vol = recent_bars[recent_bars["close"] < recent_bars["open"]][
        "volume"
    ].sum()
    total_vol = green_vol + red_vol
    buy_ratio = (green_vol / total_vol) if total_vol > 0 else 0.5

    sma20 = float(df["close"].tail(20).mean())
    above_sma = (curr_p / mult) >= sma20

    score_raw = (
        int(buy_ratio * 7) + (2 if above_sma else 0) + (1 if chg_pct > 0 else 0)
    )
    accum_score = max(1, min(10, score_raw))
    score_bar = "■" * accum_score + "□" * (10 - accum_score)

    if accum_score >= 8:
      score_color = "#00e676"
      score_desc = (
          "เกิดการดูดซับแรงขายอย่างเป็นระบบ (Absorption:"
          " พฤติกรรมทุนใหญ่กวาดซื้อแรงขาย) ปริมาณคำสั่งซื้อหนาแน่น"
          " สะท้อนเม็ดเงินทุนใหญ่ทยอยเก็บสะสมสถานะ"
      )
    elif accum_score >= 5:
      score_color = "#38bdf8"
      score_desc = (
          "ภาวะกรอบราคาบีบอัดตัวแคบ (Volatility Squeeze:"
          " การบีบตัวของความผันผวน) กำลังสะสมพลังในฐานราคา ไม่พบแรงเทขายกระจายตัว"
      )
    else:
      score_color = "#ff5252"
      score_desc = (
          "ปริมาณคำสั่งขายกดดันต่อเนื่อง โครงสร้างราคาหลุดแนวรับเฉลี่ย"
          " อยู่ในระยะระบายของ (Distribution Phase: ช่วงกระจายสินค้า/เทขาย)"
      )

    # วงสีแดง: จำแนกโมเมนตัมแรงซื้อขายจริงไม่ปั่น vs โมเมนตัมแรงซื้อขายปั่นกระแส
    if chg_pct >= 3.5 and not is_liquid:
      demand_status_modal = (
          '<span style="color:#ff3366; font-weight:bold; font-size:16px;">🔴'
          " คาดการณ์: โมเมนตัมแรงซื้อขายปั่นกระแส (Speculative Pump / Wash"
          " Trading)</span>"
      )
      demand_article = (
          "ราคาปรับตัวขึ้นสูงแต่ยอดเงินหมุนเวียนต่ำกว่าเกณฑ์ความปลอดภัยอย่างมาก"
          " ตรวจพบพฤติกรรมการเคาะซื้อลอยตัวในภาวะกระดานบาง (Thin Order Book)"
          " เป็นการปั่นกระแสกระตุ้นความโลภระยะสั้น"
          " เสี่ยงต่อการโดนคนคุมราคาเทขายทุบราคาฉับพลัน (Dump Risk) ไม่ควรไล่ราคา"
      )
    elif is_liquid and accum_score >= 7 and (chg_pct >= 1.5 or above_sma):
      demand_status_modal = (
          '<span style="color:#00e676; font-weight:bold; font-size:16px;">🟢'
          " คาดการณ์: โมเมนตัมแรงซื้อขายจริงไม่ปั่น (Confirmed Organic"
          " Flow)</span>"
      )
      demand_article = (
          "การเคลื่อนไหวของราคามีมูลค่าเงินหมุนเวียนและปริมาณซื้อขายสนับสนุนอย่างมีนัยสำคัญ"
          " สอดคล้องในหลายกรอบเวลา เป็นการเข้าทำของกระแสเงินทุนจริง (Real"
          " Capital Inflow) ไม่พบความผิดปกติของการสร้างสภาพคล่องเทียม"
          " มีโอกาสรันเทรนด์ไปต่อสูง"
      )
    elif accum_score >= 5 and abs(chg_pct) <= 3.0:
      demand_status_modal = (
          '<span style="color:#38bdf8; font-weight:bold; font-size:16px;">🌱'
          " คาดการณ์: ทรงตัวสะสมพลังตามธรรมชาติ (Organic Accumulation)</span>"
      )
      demand_article = (
          "ราคาสร้างฐานในกรอบสะสมพลัง แรงซื้อเริ่มตั้งรับอย่างเหนียวแน่น"
          " ปราศจากพฤติกรรมกระชากปั่นราคา มีความเสี่ยงขาลงต่ำ"
          " เหมาะแก่การเฝ้าระวังจังหวะเบรกเอาต์"
      )
    else:
      demand_status_modal = (
          '<span style="color:#B89494; font-weight:bold; font-size:16px;">⚖️'
          " คาดการณ์: โมเมนตัมสมดุลตามกลไกตลาด (Neutral Market Flow)</span>"
      )
      demand_article = (
          "แรงซื้อและแรงขายมีสัดส่วนใกล้เคียงกัน"
          " ไม่ปรากฏเม็ดเงินปั่นกระแสหรือการควบคุมราคาผิดปกติ"
          " ราคากำลังสร้างฐานรอความชัดเจนจากปัจจัยชี้นำภายนอก"
      )

    high_pivot = float(df["high"].tail(50).max()) * mult
    low_pivot = float(df["low"].tail(50).min()) * mult
    fib_mid = (high_pivot + low_pivot) / 2

    # =========================================================
    # แท็บ 2 ส่วนบน: FULL MULTI-TIMEFRAME MATRIX GRID
    # =========================================================
    with st.container(height=390):
      (
          mtf_matrix,
          summary_label,
          meter_pct,
          meter_color,
          tf_details,
          bull_count,
      ) = get_detailed_mtf_matrix(symbol, is_liquid_asset=is_liquid)

      upper_payload = {
          "sym_name": sym_name,
          "exch_name": exch_name,
          "cat_name": cat_name,
          "tf_display": "Multi-Timeframe (15m, 1h, 4h, 1D)",
          "turnover_val": turnover_val,
          "turnover_currency": turnover_currency,
          "liq_badge_modal": liq_badge_modal,
          "liq_desc": liq_desc,
          "score_color": score_color,
          "score_bar": score_bar,
          "accum_score": accum_score,
          "score_desc": score_desc,
          "demand_status_modal": demand_status_modal,
          "demand_article": demand_article,
          "high_pivot": high_pivot,
          "low_pivot": low_pivot,
          "fib_mid": fib_mid,
          "tf_details": tf_details,
      }

      matrix_tr_html = "".join([
          f'<tr style="border-bottom:1px solid #1a202c; height:28px;">'
          f'<td style="text-align:left; font-weight:bold; color:#f8fafc; padding:3px 4px;">{row["tf"]}</td>'
          f'<td style="padding:3px 2px;">{row["trend"]}</td>'
          f'<td style="padding:3px 2px; font-size:10.5px;">{row["mom"]}</td>'
          f'<td style="padding:3px 2px; font-size:10.5px;">{row["vol"]}</td>'
          f'<td style="text-align:right; padding:3px 4px; font-size:11px;">{row["action"]}</td>'
          f'</tr>'
          for row in mtf_matrix
      ])

      matrix_box_html = f"""<div style="background:#0f172a; padding:12px; border-radius:10px; border:1px solid #1e2433; margin-bottom:10px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
<span style="font-weight:bold; color:#ff9d42; font-size:13.5px;">📊 Multi-Timeframe Matrix (MTF Grid)</span>
{liq_badge}
</div>
<div style="display:flex; justify-content:space-between; align-items:center; background:#131722; padding:6px 10px; border-radius:6px; margin-bottom:8px; font-size:11px;">
<span style="color:#B89494;">สะสมทุน: <b style="color:{score_color}; font-family:monospace;">{score_bar} ({accum_score}/10)</b></span>
<span style="color:#d1d4dc;">ยอด 24h: <b>{turnover_val:,.0f} {turnover_currency}</b></span>
</div>
<div style="background:#131722; padding:6px 8px; border-radius:6px; margin-bottom:8px;">
<div style="display:flex; justify-content:space-between; align-items:center; font-size:10.5px; font-weight:700; margin-bottom:4px;">
<span style="color:{meter_color};">{summary_label}</span>
<span style="color:#8b949e; font-family:monospace;">{meter_pct}%</span>
</div>
<div style="width:100%; height:5px; background:#1e293b; border-radius:3px; overflow:hidden;">
<div style="width:{meter_pct}%; height:100%; background:{meter_color}; border-radius:3px; transition:width 0.3s ease;"></div>
</div>
</div>
<table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-family:'JetBrains Mono', monospace;">
<thead>
<tr style="border-bottom:1px solid #2a2e39; color:#8b949e; font-size:10px;">
<th style="padding:3px 4px; text-align:left;">TF</th>
<th style="padding:3px 2px;">แนวโน้ม</th>
<th style="padding:3px 2px;">โมเมนตัม</th>
<th style="padding:3px 2px;">วอลุ่ม</th>
<th style="padding:3px 4px; text-align:right;">หน้าเทรด</th>
</tr>
</thead>
<tbody>
{matrix_tr_html}
</tbody>
</table>
</div>"""

      st.markdown(matrix_box_html, unsafe_allow_html=True)

      if st.button(
          "🔍 ขยายผลวิเคราะห์เชิงลึก (Deep Analysis Modal)",
          key="btn_open_upper_analysis_modal",
          use_container_width=True,
          type="secondary",
      ):
        show_upper_analysis_modal(upper_payload)

      st.markdown(
          f"""<div style="background:#131722; padding:12px; border-radius:8px; margin:10px 0;">
<div style="font-size:14px; font-weight:bold; color:#FCF8F8; margin-bottom:8px;">📌 โซนราคาสำคัญ (Key Levels: ระดับราคาสำคัญ)</div>
<div style="display:flex; justify-content:space-between; font-size:13px; color:#ef4444; padding:3px 0;">
<span>แนวต้านสำคัญ (Major Resistance)</span><b>{high_pivot:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:13px; color:#38bdf8; padding:3px 0;">
<span>จุดกึ่งกลางดุลยภาพ (Equilibrium)</span><b>{fib_mid:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:13px; color:#22c55e; padding:3px 0;">
<span>แนวรับสำคัญ (Major Support)</span><b>{low_pivot:,.2f}</b>
</div>
</div>""",
          unsafe_allow_html=True,
      )

      sym_check = str(meta.get("symbol", ""))
      if "RICE" in sym_check or "FOB" in sym_check:
        st.markdown(
            f"""<div style="background:#1e1b4b; padding:12px; border-radius:8px; border-left:3px solid #F8B981; margin-bottom:10px;">
<div style="font-size:14px; font-weight:bold; color:#FEC7C7;">🌾 การวิเคราะห์ส่วนต่างข้าว (Spread Analysis: การวิเคราะห์ส่วนต่างราคา)</div>
<div style="font-size:12.5px; color:#FFE0E0; line-height:1.5; margin-top:4px;">
• ราคาแปลงเป็นบาท: <b>{curr_p:,.2f} {display_unit}</b><br>
• อัตราแลกเปลี่ยนคำนวณ: <b>{fx_rate:.2f} บาท/USD</b><br>
• สถานะส่วนต่าง: ราคาเวียดนามต่ำกว่าไทย ~<b>30 USD/ตัน</b> ส่งผลให้ผู้ส่งออกชะลอการซื้อข้าวเปลือกหน้าโรงสี
</div>
</div>""",
            unsafe_allow_html=True,
        )

    # =========================================================
    # ฐานข้อมูล HTML สำหรับสแกนเนอร์ทั้ง 6 ตลาด (คงเดิม 100%)
    # =========================================================
    market_htmls = {
        "🇹🇭 Bitkub (THB)": """<div style="background:#221313; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBVIC</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.35%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: ฿0.96 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿275,855</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาบีบอัดตัวในกรอบแคบ 48 ชม. ปริมาณซื้อขาย (Volume) เริ่มยกตัว 1.4 เท่า โครงสร้างอยู่ในระยะสะสมพลัง (Accumulation Phase: ช่วงสะสมพลัง) จ่อทดสอบแนวต้าน ฿1.02
</div>
</div>
<div style="margin-bottom:8px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBSOON</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.23%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: ฿7.40 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿191,216</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ดัชนีแรงซื้อสะสม 6/10 เกิดภาวะกรอบราคาบีบอัดตัวแคบ (Volatility Squeeze: การบีบตัวของความผันผวน) สภาพคล่องตั้งฐานรับเหนียวแน่น เหมาะแก่การวางกรอบดักซื้อต้นทุนต่ำ
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBSQD</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+22.87%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: ฿1.54 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿6,002,284</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนทะลุ 6 ล้านบาท ปริมาณซื้อขายพุ่งสูงกว่าค่าเฉลี่ย 3.5 เท่า ยืนยันกระแสเงินทุนไหลเข้าจริง ไม่ใช่การลากราคาลอยตัว
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBWIN</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+17.41%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: ฿0.00106 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿27,968</div>
<div style="color:#ff3366; font-weight:bold; font-size:12px; margin-top:3px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> แม้ราคาบวกสูงแต่ยอดเงินซื้อขายทั้งวันมีเพียง 2.7 หมื่นบาท เกิดจากการเคาะซื้อในกระดานที่ไม่มีคนตั้งขาย เสี่ยงโดนเทขายทุบราคาฉับพลัน
</div>
</div>
</div>""",
        "🌐 Binance (USDT)": """<div style="background:#221313; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">MEUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.80%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: $0.0657 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $3.54M</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> เกิดการสะสมพลังพร้อมปริมาณเงินหมุนเวียนสูงโดดเด่น โครงสร้างราขายกฐานขึ้นอย่างมั่นคง มีโอกาสดันราคาผ่านแนวต้านสูง
</div>
</div>
<div style="margin-bottom:8px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">XMRUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.77%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: $118.70 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.57M</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาทรงตัวในกรอบบีบอัดแคบ แต่ปริมาณการซื้อขายยังไม่ระเบิด แนะนำรอสัญญาณวอลุ่มซัพพอร์ตเพื่อยืนยันการเบรกแนวต้าน
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">PROMUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+37.73%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: $2.811 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $5.16M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> โมเมนตัมแข็งแกร่งมาก เงินหมุนเวียนหนาแน่นทะลุ 5 ล้านดอลลาร์สหรัฐ ยืนยันเทรนด์ขาขึ้นขนาดใหญ่ มีโอกาสรันเทรนด์ไปต่อชัดเจน
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">CREAMUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+65.35%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: $2.100 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.28M</div>
<div style="color:#ff3366; font-weight:bold; font-size:12px; margin-top:3px;">⚠️ เกิดสัญญาณขัดแย้งเชิงลบกับวอลุ่ม (Bearish Divergence / Bull Trap: ราคาขึ้นแต่วอลุ่มลด/กับดักล่อซื้อ)</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาพุ่งแรงเกินจริงแต่เม็ดเงินหมุนเวียนต่ำมาก เกิดจากสภาพคล่องที่ว่างเปล่า เสี่ยงโดนเทขายทำกำไรฉับพลัน ไม่ควรไล่ราคา
</div>
</div>
</div>""",
        "📈 หุ้นไทย (SET)": """<div style="background:#221313; padding:14px; border-radius:8px; font-size:13px; border:1px solid #2D1E1E;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">WHA</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+2.63%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: ฿5.85 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿215.40M</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานสะสมอย่างเหนียวแน่นเหนือแนวรับเส้นค่าเฉลี่ยเคลื่อนที่ (EMA 15 วัน: Exponential Moving Average) ปริมาณซื้อขายแท่งเขียวเริ่มหนาขึ้นผิดปกติในรอบ 10 วันทำการ จ่อทดสอบจุดสูงสุดเดิม
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำกลุ่มอุตสาหกรรม (Sector Leaders: ผู้นำกลุ่มอุตสาหกรรม)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">HANA</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+8.97%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: ฿42.50 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1,420M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ แรงซื้อสถาบันและกองทุนตรวจพบจริง (Institutional Inflow: เม็ดเงินสถาบันไหลเข้า)</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนระดับพันล้านบาท ปริมาณซื้อขายเข้ามากกว่าค่าเฉลี่ย 20 วันถึง 4 เท่า ยืนยันการหมุนเวียนกลุ่มลงทุน (Sector Rotation: การโยกย้ายเงินลงทุนข้ามกลุ่ม) เข้าสู่ชิ้นส่วนอิเล็กทรอนิกส์
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">SMALL-CAP (หุ้นขนาดเล็ก)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+14.28%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: ฿1.12 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1.85M</div>
<div style="color:#ff3366; font-weight:bold; font-size:12px; margin-top:3px;">⚠️ ระวังการลากราคาแบบผิดปกติ (Speculative Pump / Low Turnover: การปั่นราคาเก็งกำไรในวอลุ่มต่ำ)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนไม่ถึงเกณฑ์ความปลอดภัยของตลาดหุ้นไทย (ต่ำกว่า 5 ล้านบาท) สภาพคล่องแคบมาก ไม่เอื้อต่อการรันเทรนด์ระยะกลาง
</div>
</div>
</div>""",
        "🌍 หุ้นต่างประเทศ (US)": """<div style="background:#221313; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">PLTR (Palantir)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+3.15%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: $62.40 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $840M</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานรูปถ้วยและหู (Cup and Handle Base: โครงสร้างถ้วยหูพร้อมเบรก) บนแนวรับเส้นค่าเฉลี่ยถ่วงน้ำหนักตามปริมาณซื้อขาย (VWAP: Volume Weighted Average Price) ปริมาณซื้อขายเริ่มฟื้นตัวหนุนโอกาสทำจุดสูงสุดใหม่รอบปี
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำเทคโนโลยีขนาดใหญ่ (Mega-Cap Momentum: หุ้นยักษ์ใหญ่แรงส่งสูง)</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">NVDA (NVIDIA)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+5.82%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: $148.90 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $14,200M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ อภิมหาสภาพคล่องระดับโลก (Mega Liquidity Flow: กระแสเงินทุนมหาศาล)</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> เม็ดเงินหมุนเวียนระดับหมื่นล้านดอลลาร์สหรัฐ ขับเคลื่อนด้วยอุปสงค์จริงของกองทุนระดับโลก โมเมนตัมแข็งแกร่งต่อเนื่อง
</div>
</div>
</div>""",
        "🪙 ตลาดทองคำ (Macro)": """<div style="background:#221313; padding:22px; border-radius:12px; font-size:15px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 ภาวะการบีบอัดความผันผวน (Volatility Squeeze Preparation: การสะสมพลังก่อนเลือกทาง)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">XAU/USD (Gold Spot: ทองคำสปอต)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+0.42%</span>
</div>
<div style="color:#B89494; font-size:14px; margin-top:3px;">ราคา: $2,645.20 • ตลาดล่วงหน้าสากล (Global Futures: สัญญาซื้อขายล่วงหน้าระดับโลก)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> การเคลื่อนไหวของราคารายวันบีบแคบลงในกรอบไม่เกิน $12 เป็นเวลา 5 วันทำการ ปริมาณการซื้อขายชะลอตัวเพื่อรอตัวเลขเศรษฐกิจมหภาค เป็นพฤติกรรมกักเก็บพลังงานก่อนระเบิดแนวโน้มระลอกใหญ่
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 สัญญาณทะลุจุดสูงสุดรอบสัปดาห์ (Momentum Surge Breakout: ทะลุแนวต้านด้วยแรงส่ง)</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">PAXG/USDT (Tokenized Gold: เหรียญทองคำดิจิทัล)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+1.65%</span>
</div>
<div style="color:#B89494; font-size:14px; margin-top:3px;">ราคา: $2,652.10 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $48.20M</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ เกิด Breakout เหนือกรอบสะสม 20 วัน (20-Day High Breakout: ทะลุจุดสูงสุด 20 วัน)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> การปรับตัวขึ้นเกิน +1.5% ของทองคำถือเป็นความผิดปกติเชิงโมเมนตัม สะท้อนการเคลื่อนย้ายเงินทุนเข้าสู่สินทรัพย์ปลอดภัย (Safe Haven Flow: เงินไหลเข้าหลบภัย) ชัดเจน
</div>
</div>
</div>""",
        "🔄 คริปโตทางเลือกในแอป (Altcoins: เหรียญคริปโตอื่นๆ)": """<div style="background:#221313; padding:22px; border-radius:12px; font-size:15px; border:1px solid #2D1E1E;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">SUI/USDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+5.12%</span>
</div>
<div style="color:#B89494; font-size:14px; margin-top:3px;">ราคา: $3.42 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $420M</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาบีบอัดตัวในกรอบสะสมพลังเหนือเส้นค่าเฉลี่ย EMA 20 วัน ปริมาณซื้อขาย (Volume: ปริมาณการซื้อขาย) เริ่มยกตัวขึ้น 1.5 เท่า จ่อทะลุแนวต้านสำคัญ
</div>
</div>
<div style="margin-bottom:8px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">APT/USDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+3.85%</span>
</div>
<div style="color:#B89494; font-size:12px; margin-top:2px;">ราคา: $9.15 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $185M</div>
<div style="color:#E1CBCB; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ดัชนีแรงซื้อสะสม 7/10 โครงสร้างยกฐานราคา (Higher Low) ต่อเนื่อง สภาพคล่องฝั่งซื้อตั้งรับหนาแน่น มีโอกาสเกิด Breakout (การทะลุกรอบ) ในระยะสั้น
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #2C1E1E;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">SOL/USDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+11.45%</span>
</div>
<div style="color:#B89494; font-size:14px; margin-top:3px;">ราคา: $214.80 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $3,850M</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ปริมาณเงินหมุนเวียนหลายพันล้านดอลลาร์สหรัฐ ทะลุกรอบสะสม 1 เดือนเต็ม ยืนยันกระแสเงินทุนสถาบันไหลเข้าต่อเนื่อง มีโอกาสรันเทรนด์ไปต่อชัดเจน
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">LOW-CAP MEME (เหรียญมีมขนาดเล็ก)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+28.40%</span>
</div>
<div style="color:#B89494; font-size:14px; margin-top:3px;">ราคา: $0.00045 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.15M</div>
<div style="color:#ff3366; font-weight:bold; font-size:14.5px; margin-top:4px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาพุ่งขึ้นแรงจากสภาพคล่องที่เบาบางมาก ยอดซื้อขายจริงไม่ถึงเกณฑ์ความปลอดภัย เสี่ยงต่อการโดนทุบราคาฉับพลัน (Dump Risk: ความเสี่ยงถูกเทขาย)
</div>
</div>
</div>""",
    }

    # =========================================================
    # แท็บ 2 ส่วนล่าง: กล่องเลื่อนอิสระส่วนล่าง (เรดาร์คัดกรองตลาดพหุสินทรัพย์)
    # =========================================================
    with st.container(height=400):
      st.markdown(
          "<div style='font-size:14.5px; font-weight:bold; color:#f8fafc;"
          " margin:4px 0 8px 0;'>📡 เรดาร์คัดกรองตลาดพหุสินทรัพย์"
          " (Multi-Market Tactical Screener)</div>",
          unsafe_allow_html=True,
      )

      market_choice = st.selectbox(
          "เลือกตลาดที่ต้องการสแกน:",
          options=[
              "🇹🇭 Bitkub (THB)",
              "🌐 Binance (USDT)",
              "📈 หุ้นไทย (SET)",
              "🌍 หุ้นต่างประเทศ (US)",
              "🪙 ตลาดทองคำ (Macro)",
              "🔄 คริปโตทางเลือกในแอป (Altcoins: เหรียญคริปโตอื่นๆ)",
          ],
          label_visibility="collapsed",
          key="screener_market_selector",
      )

      st.markdown(market_htmls[market_choice], unsafe_allow_html=True)

      if st.button(
          "📊 ขยายเรดาร์คัดกรองตลาด (Expand Market Screener:"
          " ขยายเรดาร์คัดกรอง)",
          key="btn_open_bottom_screener_modal",
          use_container_width=True,
          type="secondary",
      ):
        show_bottom_screener_modal(modal_market_htmls, market_choice)