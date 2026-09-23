from ui.technical_modal import show_technical_modal
from ui.seasonality_modal import show_seasonality_modal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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

@modal_dialog("🔍 การวินิจฉัยกระแสเงินทุนเชิงลึก (Deep Flow Diagnosis: การวินิจฉัยเชิงลึก)", width="large")
def show_upper_analysis_modal(data: dict):
    sym_name = data['sym_name']
    st.markdown(f"""<div style="background:#0f172a; padding:22px; border-radius:12px; border:1px solid #3b82f6; margin-bottom:16px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-weight:bold; color:#60a5fa; font-size:21px;">🎯 การวินิจฉัยกระแสเงินทุน: {sym_name}</span>
{data['liq_badge_modal']}
</div>
<div style="font-size:14.5px; color:#94a3b8; margin-top:8px;">
ตลาด: {data['exch_name']} • หมวด: {data['cat_name']} • ⏱️ กรอบเวลา (Analysis Timeframe: กรอบเวลาการวิเคราะห์): <b style="color:#38bdf8;">{data['tf_display']}</b>
</div>
<div style="margin-top:16px; background:#131722; padding:20px; border-radius:10px; border:1px solid #1e222d; font-size:15px;">
<div style="display:flex; justify-content:space-between; margin-bottom:8px;">
<span style="color:#a0aec0; font-size:15.5px;">1. ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย):</span>
<b style="color:#f8fafc; font-size:18px;">{data['turnover_val']:,.0f} {data['turnover_currency']}</b>
</div>
<div style="color:#cbd5e1; font-size:14px; line-height:1.6; margin-bottom:14px;">• {data['liq_desc']}</div>
<div style="display:flex; justify-content:space-between; margin-bottom:8px;">
<span style="color:#a0aec0; font-size:15.5px;">2. ดัชนีแรงซื้อสะสม (Accumulation Score: คะแนนแรงซื้อสะสม):</span>
<b style="color:{data['score_color']}; font-family:monospace; font-size:18px;">{data['score_bar']} ({data['accum_score']}/10)</b>
</div>
<div style="color:#cbd5e1; font-size:14px; line-height:1.6; margin-bottom:14px;">• {data['score_desc']}</div>
<div style="margin-top:12px; padding-top:12px; border-top:1px dashed #2d3748;">
<span style="color:#a0aec0; font-size:15.5px;">3. การจำแนกพฤติกรรม:</span> <span style="font-size:15.5px;">{data['demand_status_modal']}</span>
<div style="color:#f1f5f9; font-size:15px; line-height:1.65; margin-top:8px;">{data['demand_article']}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div style="background:#131722; padding:18px; border-radius:10px; border:1px solid #1e222d; margin-bottom:12px;">
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
</div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""<div style="background:#131722; padding:18px; border-radius:10px; border:1px solid #1e222d; margin-bottom:12px;">
<div style="font-size:16.5px; font-weight:bold; color:#f8fafc; margin-bottom:12px;">💡 คำแนะนำเชิงกลยุทธ์ (Tactical Guidance: คำแนะนำการวางแผน)</div>
<div style="font-size:14.5px; color:#cbd5e1; line-height:1.65;">
• หากคะแนนแรงซื้อสะสมมากกว่า 7/10 และสภาพคล่องสูง: สามารถวางแผนแบ่งไม้เข้าซื้อตามแนวรับเฉลี่ย<br>
• หากพบสัญญาณเตือนกับดักสภาพคล่อง (Bull Trap): หลีกเลี่ยงการไล่ราคา และตั้งจุดตัดขาดทุน (Stop Loss: จุดหยุดขาดทุน) อย่างเคร่งครัด
</div>
</div>""", unsafe_allow_html=True)

# -------------------------------------------------------------
# หน้าต่างป๊อปอัปขยายใหญ่ส่วนล่าง: เรดาร์คัดกรองตลาดฉบับเต็ม (Full Screener Modal)
# -------------------------------------------------------------
@modal_dialog("📊 ศูนย์คัดกรองเรดาร์พหุสินทรัพย์ฉบับเต็ม (Full Multi-Market Screener)", width="large")
def show_bottom_screener_modal(modal_market_htmls: dict, default_market: str):
    options = [
        "🇹🇭 Bitkub (THB)", 
        "🌐 Binance (USDT)", 
        "📈 หุ้นไทย (SET)", 
        "🌍 หุ้นต่างประเทศ (US)", 
        "🪙 ตลาดทองคำ (Macro)", 
        "🔄 คริปโตทางเลือกในแอป (Altcoins: เหรียญคริปโตอื่นๆ)"
    ]
    cur_idx = options.index(default_market) if default_market in options else 0
    selected_mkt = st.selectbox(
        "เลือกตลาดที่ต้องการสแกน (ฉบับเต็ม):",
        options=options,
        index=cur_idx,
        key="screener_modal_mkt_selector"
    )
    st.markdown(modal_market_htmls.get(selected_mkt, ""), unsafe_allow_html=True)


def render_right_panel(df: pd.DataFrame, meta: dict, is_thb_mode: bool = False, fx_rate: float = 35.0):
    """
    พาเนลฝั่งขวา: แท็บ 1 ภาพรวมตลาด 8 บล็อก + แท็บ 2 วิเคราะห์ข้อมูลเทคนิคเชิงลึก
    แบ่งพื้นที่ส่วนบนและส่วนล่างให้อ่านสบายตา และเลื่อนขึ้น-ลงในช่องใครช่องมันอย่างอิสระ
    """
    tab_overview, tab_pro = st.tabs(["📊 ภาพรวมตลาด", "🧠 วิเคราะห์ข้อมูล & เทคนิค"])

    # -------------------------------------------------------------
    # แท็บ 1: โครงสร้าง 8 บล็อก (TradingView Redesign)
    # -------------------------------------------------------------
    with tab_overview:
        if df.empty or len(df) < 2:
            st.warning("ไม่มีข้อมูลแท่งเทียนเพียงพอสำหรับการวิเคราะห์")
            return

        # แปลงราคาตามโหมดที่เลือก
        mult = (fx_rate if (is_thb_mode and not meta.get("is_thb_native", False)) else 1.0)
        curr_p = float(df["close"].iloc[-1]) * mult
        prev_p = float(df["close"].iloc[-2]) * mult
        chg_val = curr_p - prev_p
        chg_pct = (chg_val / prev_p * 100) if prev_p else 0.0
        display_unit = "THB (บาท)" if (is_thb_mode or meta.get("is_thb_native", False)) else meta.get("unit", "USD")

        # =========================================================
        # แท็บ 1 ส่วนบน (รูปที่ 1): กล่องเลื่อนอิสระส่วนบน
        # =========================================================
        with st.container(height=390):
            color_hex = "#00e676" if chg_val >= 0 else "#ff5252"
            sign = "+" if chg_val >= 0 else ""
            st.markdown(f"""<div style="background:#131722; padding:12px; border-radius:8px; border-left:3px solid {color_hex}; margin-bottom:10px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-weight:bold; font-size:16px; color:#fff;">{meta.get('display_name', meta.get('symbol', ''))}</span>
<span style="color:#00e676; font-size:11px; font-weight:bold;">🟢 ตลาดเปิด</span>
</div>
<div style="color:#787b86; font-size:12px;">{meta.get('exchange', 'BINANCE')} • {meta.get('category', 'Crypto')}</div>
<div style="font-size:24px; font-weight:bold; color:#fff; margin-top:4px;">
{curr_p:,.2f} <span style="font-size:13px; color:#787b86;">{display_unit}</span>
</div>
<div style="color:{color_hex}; font-size:13px; font-weight:bold;">
{sign}{chg_val:,.2f} ({sign}{chg_pct:,.2f}%)
</div>
<div style="display:flex; gap:6px; margin-top:8px;">
<div style="flex:1; background:#1e293b; padding:4px; border-radius:4px; text-align:center; color:#38bdf8; font-size:11px;">
Bid (เสนอซื้อ) {curr_p * 0.999:,.2f}
</div>
<div style="flex:1; background:#33141e; padding:4px; border-radius:4px; text-align:center; color:#ff5252; font-size:11px;">
Ask (เสนอขาย) {curr_p * 1.001:,.2f}
</div>
</div>
</div>""", unsafe_allow_html=True)

            d_low = float(df["low"].tail(24).min()) * mult
            d_high = float(df["high"].tail(24).max()) * mult
            w_low = float(df["low"].min()) * mult
            w_high = float(df["high"].max()) * mult

            d_pct = max(0, min(100, int(((curr_p - d_low) / (d_high - d_low) * 100) if d_high > d_low else 50)))
            w_pct = max(0, min(100, int(((curr_p - w_low) / (w_high - w_low) * 100) if w_high > w_low else 50)))

            st.markdown(f"""<div style="background:#131722; padding:10px; border-radius:8px; margin-bottom:10px; font-size:11px;">
<div style="display:flex; justify-content:space-between; color:#787b86;">
<span>{d_low:,.1f}</span><span style="color:#d1d4dc;">ช่วงระหว่างวัน (Day Range)</span><span>{d_high:,.1f}</span>
</div>
<div style="height:4px; background:#2a2e39; border-radius:2px; margin:6px 0; position:relative;">
<div style="height:100%; width:{d_pct}%; background:#2962ff; border-radius:2px;"></div>
</div>
<div style="display:flex; justify-content:space-between; color:#787b86; margin-top:8px;">
<span>{w_low:,.1f}</span><span style="color:#d1d4dc;">รอบ 52 สัปดาห์ (52-Week Range)</span><span>{w_high:,.1f}</span>
</div>
<div style="height:4px; background:#2a2e39; border-radius:2px; margin:6px 0; position:relative;">
<div style="height:100%; width:{w_pct}%; background:#00e676; border-radius:2px;"></div>
</div>
</div>""", unsafe_allow_html=True)

            vol_curr = float(df["volume"].iloc[-1])
            vol_avg = float(df["volume"].tail(30).mean())
            st.markdown(f"""<div style="background:#1a1a2e; padding:8px 10px; border-radius:6px; border-left:3px solid #7c4dff; margin-bottom:10px; font-size:11px;">
<div style="color:#a78bfa; font-weight:bold;">⚡ สรุปปัจจัยข่าวสารล่าสุด (Market News Summary)</div>
<div style="color:#d1d4dc; margin-top:2px;">ติดตามรอบสต็อกผลผลิตและการปรับอัตราดอกเบี้ยส่งผลกระทบต่ออุปสงค์สินค้า</div>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:#787b86; padding:4px 2px;">
<span>ปริมาณการซื้อขาย (Volume)</span><span style="color:#fff; font-weight:bold;">{vol_curr:,.0f}</span>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:#787b86; padding:4px 2px; margin-bottom:10px;">
<span>ปริมาณเฉลี่ย (Average Volume 30 แท่ง)</span><span style="color:#fff; font-weight:bold;">{vol_avg:,.0f}</span>
</div>""", unsafe_allow_html=True)

            def calc_perf(bars):
                if len(df) > bars:
                    p_old = float(df["close"].iloc[-bars])
                    return ((curr_p / mult - p_old) / p_old) * 100
                return 0.0

            perfs = {
                "1W (1 สัปดาห์)": calc_perf(7), "1M (1 เดือน)": calc_perf(30), "3M (3 เดือน)": calc_perf(90),
                "6M (6 เดือน)": calc_perf(180), "YTD (ต้นปีถึงปัจจุบัน)": calc_perf(240), "1Y (1 ปี)": calc_perf(365)
            }

            cols = st.columns(3)
            for idx, (label, val) in enumerate(perfs.items()):
                c_hex = "#00e676" if val >= 0 else "#ff5252"
                s_sign = "+" if val >= 0 else ""
                cols[idx % 3].markdown(f"""<div style="background:#131722; padding:6px; border-radius:4px; text-align:center; margin-bottom:6px; border:1px solid #1e222d;">
<div style="font-size:12px; font-weight:bold; color:{c_hex};">{s_sign}{val:.2f}%</div>
<div style="font-size:10px; color:#787b86;">{label}</div>
</div>""", unsafe_allow_html=True)

        # =========================================================
        # แท็บ 1 ส่วนล่าง (รูปที่ 2): กล่องเลื่อนอิสระส่วนล่าง
        # =========================================================
        with st.container(height=390):
            st.markdown("<div style='font-size:12px; font-weight:bold; color:#d1d4dc; margin:4px 0 2px 0;'>สถิติแนวโน้มฤดูกาล (Seasonality Trend)</div>", unsafe_allow_html=True)
            fig_season = go.Figure()
            x_months = ["ม.ค.", "มี.ค.", "พ.ค.", "ก.ค.", "ก.ย.", "พ.ย."]
            fig_season.add_trace(go.Scatter(x=x_months, y=[0, 4, 8, 12, 10, 16], mode='lines', line=dict(color='#ff9800', width=1.5), name='2024'))
            fig_season.add_trace(go.Scatter(x=x_months, y=[0, -2, -1, 3, 2, 4], mode='lines', line=dict(color='#00e676', width=1.5), name='2025'))
            fig_season.add_trace(go.Scatter(x=x_months[:4], y=[0, -4, -6, 2], mode='lines+markers', line=dict(color='#2962ff', width=2), name='2026'))
            fig_season.update_layout(
                height=120, margin=dict(l=0, r=0, t=5, b=5), showlegend=True,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", y=1.2, x=0.2, font=dict(size=9, color="#787b86")),
                xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#787b86")),
                yaxis=dict(showgrid=True, gridcolor="#1e222d", tickfont=dict(size=9, color="#787b86"))
            )
            st.plotly_chart(fig_season, use_container_width=True, config={"displayModeBar": False})

            if st.button("ฤดูกาลเพิ่มเติม", key="btn_open_seasonality_modal", use_container_width=True, type="secondary"):
                show_seasonality_modal(sym=st.session_state.get("current_symbol", "BTCUSDT"))

            import math
            import streamlit.components.v1 as components

            gauge_score = max(-2.0, min(2.0, chg_pct / 0.8))

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
                        background: linear-gradient(180deg, #131722 0%, #0d1117 100%);
                        border: 1px solid #21262d;
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
                        <text x="32" y="106" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงขายรุนแรง</text>
                        <text x="65" y="44" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงขาย</text>
                        <text x="140" y="18" font-size="9" font-weight="700" fill="#8b949e" text-anchor="middle">เป็นกลาง</text>
                        <text x="215" y="44" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงซื้อ</text>
                        <text x="248" y="106" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงซื้อรุนแรง</text>
                        <line x1="{cx}" y1="{cy}" x2="{tx}" y2="{ty}" stroke="#f0f6fc" stroke-width="2.5" stroke-linecap="round" />
                        <circle cx="{cx}" cy="{cy}" r="5" fill="#161b22" stroke="{status_color}" stroke-width="2" />
                        <circle cx="{cx}" cy="{cy}" r="2" fill="#f0f6fc" />
                    </svg>
                    <div class="summary-txt">{status_text}</div>
                </div>
            </body>
            </html>
            """

            components.html(gauge_html, height=155)

            if st.button("ทางเทคนิคเพิ่มเติม", use_container_width=True, type="secondary"):
                show_technical_modal(sym=st.session_state.get("current_symbol", "BTCUSDT"))

    # -------------------------------------------------------------
    # แท็บ 2: ยุทธศาสตร์ & ข้อวิเคราะห์เทคนิค
    # -------------------------------------------------------------
    with tab_pro:
        # =========================================================
        # ดึงข้อมูลและคำนวณส่วนบน (รูปที่ 3): วินิจฉัยสินทรัพย์บนกราฟหลัก
        # =========================================================
        sym_name = meta.get("display_name", meta.get("symbol", "สินทรัพย์ปัจจุบัน"))
        exch_name = str(meta.get("exchange", "BINANCE")).upper()
        cat_name = str(meta.get("category", "Crypto")).upper()

        detected_tf = None
        if len(df) >= 2:
            try:
                diff_sec = 0
                if isinstance(df.index, pd.DatetimeIndex):
                    diff_sec = abs((df.index[-1] - df.index[-2]).total_seconds())
                else:
                    for col in ["time", "timestamp", "datetime", "date", "Date", "Time", "open_time"]:
                        if col in df.columns:
                            s = df[col]
                            if pd.api.types.is_numeric_dtype(s):
                                val_diff = abs(float(s.iloc[-1] - s.iloc[-2]))
                                diff_sec = val_diff / 1000.0 if s.iloc[-1] > 1e11 else val_diff
                            else:
                                dt_s = pd.to_datetime(s)
                                diff_sec = abs((dt_s.iloc[-1] - dt_s.iloc[-2]).total_seconds())
                            break

                if diff_sec > 0:
                    diff_min = round(diff_sec / 60)
                    if diff_min <= 2: detected_tf = "1m"
                    elif 3 <= diff_min <= 7: detected_tf = "5m"
                    elif 10 <= diff_min <= 20: detected_tf = "15m"
                    elif 25 <= diff_min <= 45: detected_tf = "30m"
                    elif 50 <= diff_min <= 75: detected_tf = "1h"
                    elif 110 <= diff_min <= 135: detected_tf = "2h"
                    elif 165 <= diff_min <= 200: detected_tf = "3h"
                    elif 220 <= diff_min <= 260: detected_tf = "4h"
                    elif 1300 <= diff_min <= 1600: detected_tf = "1D"
                    elif 2700 <= diff_min <= 3100: detected_tf = "2D"
                    elif 4100 <= diff_min <= 4600: detected_tf = "3D"
                    elif 9500 <= diff_min <= 11000: detected_tf = "1W"
                    elif diff_min >= 35000: detected_tf = "1M"
            except Exception:
                pass

        if not detected_tf:
            for k in ["current_interval", "timeframe", "interval", "tf", "selected_interval", "chart_tf", "selected_timeframe", "active_tf"]:
                if k in st.session_state and st.session_state[k]:
                    detected_tf = str(st.session_state[k]).strip()
                    break

        if not detected_tf:
            for k in ["timeframe", "interval", "tf"]:
                if k in meta and meta[k]:
                    detected_tf = str(meta[k]).strip()
                    break

        if not detected_tf:
            detected_tf = "1D"

        tf_map = {
            "1M": "1 นาที (1 Minute)",
            "5M": "5 นาที (5 Minutes)",
            "15M": "15 นาที (15 Minutes)",
            "30M": "30 นาที (30 Minutes)",
            "1H": "1 ชั่วโมง (1 Hour)",
            "2H": "2 ชั่วโมง (2 Hours)",
            "3H": "3 ชั่วโมง (3 Hours)",
            "4H": "4 ชั่วโมง (4 Hours)",
            "D": "1 วัน (1 Day: แท่งเทียนรายวัน)",
            "1D": "1 วัน (1 Day: แท่งเทียนรายวัน)",
            "2D": "2 วัน (2 Days: แท่งเทียน 2 วัน)",
            "3D": "3 วัน (3 Days: แท่งเทียน 3 วัน)",
            "W": "1 สัปดาห์ (1 Week: แท่งเทียนรายสัปดาห์)",
            "1W": "1 สัปดาห์ (1 Week: แท่งเทียนรายสัปดาห์)",
            "M": "1 เดือน (1 Month: แท่งเทียนรายเดือน)",
        }
        tf_display = tf_map.get(detected_tf.upper(), f"{detected_tf} (กรอบเวลาปัจจุบัน)")

        vol_recent = float(df["volume"].tail(24).sum()) if len(df) >= 24 else float(df["volume"].sum())
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
            liq_badge = '<span style="color:#00e676; background:rgba(0,230,118,0.15); padding:3px 10px; border-radius:6px; font-weight:bold; font-size:12.5px;">🟢 สภาพคล่องสูง (High Liquidity: มีสภาพคล่องหนาแน่น)</span>'
            liq_badge_modal = '<span style="color:#00e676; background:rgba(0,230,118,0.15); padding:5px 14px; border-radius:8px; font-weight:bold; font-size:14.5px;">🟢 สภาพคล่องสูง (High Liquidity: มีสภาพคล่องหนาแน่น)</span>'
            liq_desc = "ปริมาณเงินหมุนเวียนหนาแน่นเพียงพอ ปราศจากความเสี่ยงเรื่องการขาดสภาพคล่องหรือราคาคลาดเคลื่อนสูง (Slippage: ส่วนต่างราคาคำสั่งซื้อขาย)"
        else:
            liq_badge = '<span style="color:#ff9800; background:rgba(255,152,0,0.15); padding:3px 10px; border-radius:6px; font-weight:bold; font-size:12.5px;">⚠️ สภาพคล่องต่ำ (Low Liquidity Trap: กับดักสภาพคล่องแห้ง)</span>'
            liq_badge_modal = '<span style="color:#ff9800; background:rgba(255,152,0,0.15); padding:5px 14px; border-radius:8px; font-weight:bold; font-size:14.5px;">⚠️ สภาพคล่องต่ำ (Low Liquidity Trap: กับดักสภาพคล่องแห้ง)</span>'
            liq_desc = "ยอดเงินหมุนเวียนเบาบางกว่าเกณฑ์มาตรฐานความปลอดภัย ระวังคำสั่งซื้อขายจับคู่ไม่สมบูรณ์หรือการเคาะราคาในช่องว่าง (Thin Order Book: กระดานซื้อขายเบาบาง)"

        recent_bars = df.tail(15)
        green_vol = recent_bars[recent_bars["close"] >= recent_bars["open"]]["volume"].sum()
        red_vol = recent_bars[recent_bars["close"] < recent_bars["open"]]["volume"].sum()
        total_vol = green_vol + red_vol
        buy_ratio = (green_vol / total_vol) if total_vol > 0 else 0.5

        sma20 = float(df["close"].tail(20).mean())
        above_sma = (curr_p / mult) >= sma20

        score_raw = int(buy_ratio * 7) + (2 if above_sma else 0) + (1 if chg_pct > 0 else 0)
        accum_score = max(1, min(10, score_raw))
        score_bar = "■" * accum_score + "□" * (10 - accum_score)

        if accum_score >= 8:
            score_color = "#00e676"
            score_desc = "เกิดการดูดซับแรงขายอย่างเป็นระบบ (Absorption: พฤติกรรมทุนใหญ่กวาดซื้อแรงขาย) ปริมาณคำสั่งซื้อหนาแน่น สะท้อนเม็ดเงินทุนใหญ่ทยอยเก็บสะสมสถานะ"
        elif accum_score >= 5:
            score_color = "#38bdf8"
            score_desc = "ภาวะกรอบราคาบีบอัดตัวแคบ (Volatility Squeeze: การบีบตัวของความผันผวน) กำลังสะสมพลังในฐานราคา ไม่พบแรงเทขายกระจายตัว"
        else:
            score_color = "#ff5252"
            score_desc = "ปริมาณคำสั่งขายกดดันต่อเนื่อง โครงสร้างราคาหลุดแนวรับเฉลี่ย อยู่ในระยะระบายของ (Distribution Phase: ช่วงกระจายสินค้า/เทขาย)"

        if chg_pct >= 4.0 and not is_liquid:
            demand_status = '<span style="color:#ff3366; font-weight:bold; font-size:13.5px;">⚠️ ระวังแรงปั่น / กับดักลากราคา (Wash Trading / Bull Trap: การสร้างวอลุ่มเทียม/กับดักล่อซื้อ)</span>'
            demand_status_modal = '<span style="color:#ff3366; font-weight:bold; font-size:16px;">⚠️ ระวังแรงปั่น / กับดักลากราคา (Wash Trading / Bull Trap: การสร้างวอลุ่มเทียม/กับดักล่อซื้อ)</span>'
            demand_article = "ราคาปรับตัวขึ้นสูงแต่ยอดเงินหมุนเวียนต่ำกว่าเกณฑ์ความปลอดภัยอย่างมาก สะท้อนพฤติกรรมการเคาะซื้อลอยตัวในภาวะกระดานบาง เสี่ยงต่อการโดนเทขายทุบราคาฉับพลัน (Dump Risk: ความเสี่ยงถูกเทขาย)"
        elif chg_pct >= 2.0 and accum_score >= 7 and is_liquid:
            demand_status = '<span style="color:#00e676; font-weight:bold; font-size:13.5px;">✅ แรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</span>'
            demand_status_modal = '<span style="color:#00e676; font-weight:bold; font-size:16px;">✅ แรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</span>'
            demand_article = "การปรับขึ้นมีมูลค่าเงินหมุนเวียนและปริมาณซื้อขายสนับสนุนอย่างมีนัยสำคัญ ไม่พบสัญญาณขัดแย้งเชิงลบ (Bearish Divergence: ราคาขึ้นแต่วอลุ่มลดลง) มีโอกาสรันเทรนด์ไปต่อสูง"
        elif accum_score >= 6 and abs(chg_pct) <= 3.0:
            demand_status = '<span style="color:#38bdf8; font-weight:bold; font-size:13.5px;">🌱 ทรงตัวสะสมพลังต้นน้ำ (Accumulation Setup: รูปแบบสะสมพลังก่อนวิ่ง)</span>'
            demand_status_modal = '<span style="color:#38bdf8; font-weight:bold; font-size:16px;">🌱 ทรงตัวสะสมพลังต้นน้ำ (Accumulation Setup: รูปแบบสะสมพลังก่อนวิ่ง)</span>'
            demand_article = "ราคาทรงตัวในกรอบสะสมพลัง แรงซื้อเริ่มตั้งฐานอย่างเหนียวแน่น มีความเสี่ยงขาลงต่ำ เหมาะแก่การเฝ้าระวังจังหวะทะลุกรอบ"
        else:
            demand_status = '<span style="color:#94a3b8; font-weight:bold; font-size:13.5px;">⚖️ สภาวะสมดุลตามกลไกตลาด (Neutral Market Flow: สภาพตลาดเป็นกลาง)</span>'
            demand_status_modal = '<span style="color:#94a3b8; font-weight:bold; font-size:16px;">⚖️ สภาวะสมดุลตามกลไกตลาด (Neutral Market Flow: สภาพตลาดเป็นกลาง)</span>'
            demand_article = "แรงซื้อและแรงขายมีสัดส่วนใกล้เคียงกัน ราคากำลังสร้างฐานรอความชัดเจนจากปัจจัยชี้นำภายนอก"

        high_pivot = float(df["high"].tail(50).max()) * mult
        low_pivot = float(df["low"].tail(50).min()) * mult
        fib_mid = (high_pivot + low_pivot) / 2

        upper_payload = {
            'sym_name': sym_name,
            'exch_name': exch_name,
            'cat_name': cat_name,
            'tf_display': tf_display,
            'turnover_val': turnover_val,
            'turnover_currency': turnover_currency,
            'liq_badge_modal': liq_badge_modal,
            'liq_desc': liq_desc,
            'score_color': score_color,
            'score_bar': score_bar,
            'accum_score': accum_score,
            'score_desc': score_desc,
            'demand_status_modal': demand_status_modal,
            'demand_article': demand_article,
            'high_pivot': high_pivot,
            'low_pivot': low_pivot,
            'fib_mid': fib_mid
        }

        # =========================================================
        # แท็บ 2 ส่วนบน (รูปที่ 3): กล่องเลื่อนอิสระส่วนบน
        # =========================================================
        with st.container(height=390):
            st.markdown(f"""<div style="background:#0f172a; padding:15px; border-radius:10px; border:1px solid #3b82f6; margin-bottom:10px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-weight:bold; color:#60a5fa; font-size:16px;">🎯 การวินิจฉัยกระแสเงินทุน: {sym_name}</span>
{liq_badge}
</div>
<div style="font-size:12.5px; color:#94a3b8; margin-top:4px;">
ตลาด: {exch_name} • หมวด: {cat_name} • กรอบเวลา: <b style="color:#38bdf8;">{tf_display}</b>
</div>
<div style="margin-top:12px; background:#131722; padding:14px; border-radius:8px; border:1px solid #1e222d; font-size:13px;">
<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
<span style="color:#94a3b8; font-size:13px;">1. ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย):</span>
<b style="color:#f8fafc; font-size:14.5px;">{turnover_val:,.0f} {turnover_currency}</b>
</div>
<div style="color:#cbd5e1; font-size:12px; line-height:1.5; margin-bottom:10px;">• {liq_desc}</div>
<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
<span style="color:#94a3b8; font-size:13px;">2. ดัชนีแรงซื้อสะสม (Accumulation Score: คะแนนแรงซื้อสะสม):</span>
<b style="color:{score_color}; font-family:monospace; font-size:15px;">{score_bar} ({accum_score}/10)</b>
</div>
<div style="color:#cbd5e1; font-size:12px; line-height:1.5; margin-bottom:10px;">• {score_desc}</div>
<div style="margin-top:8px; padding-top:8px; border-top:1px dashed #21262d;">
<span style="color:#94a3b8; font-size:13px;">3. การจำแนกพฤติกรรม:</span> {demand_status}
<div style="color:#f1f5f9; font-size:12.5px; line-height:1.55; margin-top:5px;">{demand_article}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

            if st.button("🔍 ขยายผลวิเคราะห์เชิงลึก (Expand Deep Analysis: ขยายผลการวิเคราะห์)", key="btn_open_upper_analysis_modal", use_container_width=True, type="secondary"):
                show_upper_analysis_modal(upper_payload)

            st.markdown(f"""<div style="background:#131722; padding:12px; border-radius:8px; margin:10px 0;">
<div style="font-size:14px; font-weight:bold; color:#f8fafc; margin-bottom:8px;">📌 โซนราคาสำคัญ (Key Levels: ระดับราคาสำคัญ)</div>
<div style="display:flex; justify-content:space-between; font-size:13px; color:#ef4444; padding:3px 0;">
<span>แนวต้านสำคัญ (Major Resistance)</span><b>{high_pivot:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:13px; color:#38bdf8; padding:3px 0;">
<span>จุดกึ่งกลางดุลยภาพ (Equilibrium)</span><b>{fib_mid:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:13px; color:#22c55e; padding:3px 0;">
<span>แนวรับสำคัญ (Major Support)</span><b>{low_pivot:,.2f}</b>
</div>
</div>""", unsafe_allow_html=True)

            sym_check = str(meta.get("symbol", ""))
            if "RICE" in sym_check or "FOB" in sym_check:
                st.markdown(f"""<div style="background:#1e1b4b; padding:12px; border-radius:8px; border-left:3px solid #818cf8; margin-bottom:10px;">
<div style="font-size:14px; font-weight:bold; color:#c7d2fe;">🌾 การวิเคราะห์ส่วนต่างข้าว (Spread Analysis: การวิเคราะห์ส่วนต่างราคา)</div>
<div style="font-size:12.5px; color:#e0e7ff; line-height:1.5; margin-top:4px;">
• ราคาแปลงเป็นบาท: <b>{curr_p:,.2f} {display_unit}</b><br>
• อัตราแลกเปลี่ยนคำนวณ: <b>{fx_rate:.2f} บาท/USD</b><br>
• สถานะส่วนต่าง: ราคาเวียดนามต่ำกว่าไทย ~<b>30 USD/ตัน</b> ส่งผลให้ผู้ส่งออกชะลอการซื้อข้าวเปลือกหน้าโรงสี
</div>
</div>""", unsafe_allow_html=True)

        # =========================================================
        # เตรียมฐานข้อมูล HTML สำหรับสแกนเนอร์ทั้ง 6 ตลาด
        # =========================================================
        market_htmls = {
            "🇹🇭 Bitkub (THB)": """<div style="background:#131722; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBVIC</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.35%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: ฿0.96 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿275,855</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาบีบอัดตัวในกรอบแคบ 48 ชม. ปริมาณซื้อขาย (Volume) เริ่มยกตัว 1.4 เท่า โครงสร้างอยู่ในระยะสะสมพลัง (Accumulation Phase: ช่วงสะสมพลัง) จ่อทดสอบแนวต้าน ฿1.02
</div>
</div>
<div style="margin-bottom:8px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBSOON</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.23%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: ฿7.40 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿191,216</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ดัชนีแรงซื้อสะสม 6/10 เกิดภาวะกรอบราคาบีบอัดตัวแคบ (Volatility Squeeze: การบีบตัวของความผันผวน) สภาพคล่องตั้งฐานรับเหนียวแน่น เหมาะแก่การวางกรอบดักซื้อต้นทุนต่ำ
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBSQD</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+22.87%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: ฿1.54 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿6,002,284</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนทะลุ 6 ล้านบาท ปริมาณซื้อขายพุ่งสูงกว่าค่าเฉลี่ย 3.5 เท่า ยืนยันกระแสเงินทุนไหลเข้าจริง ไม่ใช่การลากราคาลอยตัว
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">THBWIN</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+17.41%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: ฿0.00106 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿27,968</div>
<div style="color:#ff3366; font-weight:bold; font-size:12px; margin-top:3px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> แม้ราคาบวกสูงแต่ยอดเงินซื้อขายทั้งวันมีเพียง 2.7 หมื่นบาท เกิดจากการเคาะซื้อในกระดานที่ไม่มีคนตั้งขาย เสี่ยงโดนเทขายทุบราคาฉับพลัน
</div>
</div>
</div>""",

            "🌐 Binance (USDT)": """<div style="background:#131722; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">MEUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.80%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $0.0657 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $3.54M</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> เกิดการสะสมพลังพร้อมปริมาณเงินหมุนเวียนสูงโดดเด่น โครงสร้างราขายกฐานขึ้นอย่างมั่นคง มีโอกาสดันราคาผ่านแนวต้านสูง
</div>
</div>
<div style="margin-bottom:8px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">XMRUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+4.77%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $118.70 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.57M</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาทรงตัวในกรอบบีบอัดแคบ แต่ปริมาณการซื้อขายยังไม่ระเบิด แนะนำรอสัญญาณวอลุ่มซัพพอร์ตเพื่อยืนยันการเบรกแนวต้าน
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">PROMUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+37.73%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $2.811 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $5.16M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> โมเมนตัมแข็งแกร่งมาก เงินหมุนเวียนหนาแน่นทะลุ 5 ล้านดอลลาร์สหรัฐ ยืนยันเทรนด์ขาขึ้นขนาดใหญ่ มีโอกาสรันเทรนด์ไปต่อชัดเจน
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">CREAMUSDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+65.35%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $2.100 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.28M</div>
<div style="color:#ff3366; font-weight:bold; font-size:12px; margin-top:3px;">⚠️ เกิดสัญญาณขัดแย้งเชิงลบกับวอลุ่ม (Bearish Divergence / Bull Trap: ราคาขึ้นแต่วอลุ่มลด/กับดักล่อซื้อ)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาพุ่งแรงเกินจริงแต่เม็ดเงินหมุนเวียนต่ำมาก เกิดจากสภาพคล่องที่ว่างเปล่า เสี่ยงโดนเทขายทำกำไรฉับพลัน ไม่ควรไล่ราคา
</div>
</div>
</div>""",

            "📈 หุ้นไทย (SET)": """<div style="background:#131722; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">WHA</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+2.63%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: ฿5.85 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿215.40M</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานสะสมอย่างเหนียวแน่นเหนือแนวรับเส้นค่าเฉลี่ยเคลื่อนที่ (EMA 15 วัน: Exponential Moving Average) ปริมาณซื้อขายแท่งเขียวเริ่มหนาขึ้นผิดปกติในรอบ 10 วันทำการ จ่อทดสอบจุดสูงสุดเดิม
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำกลุ่มอุตสาหกรรม (Sector Leaders: ผู้นำกลุ่มอุตสาหกรรม)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">HANA</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+8.97%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: ฿42.50 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1,420M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ แรงซื้อสถาบันและกองทุนตรวจพบจริง (Institutional Inflow: เม็ดเงินสถาบันไหลเข้า)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนระดับพันล้านบาท ปริมาณซื้อขายเข้ามากกว่าค่าเฉลี่ย 20 วันถึง 4 เท่า ยืนยันการหมุนเวียนกลุ่มลงทุน (Sector Rotation: การโยกย้ายเงินลงทุนข้ามกลุ่ม) เข้าสู่ชิ้นส่วนอิเล็กทรอนิกส์
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">SMALL-CAP (หุ้นขนาดเล็ก)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+14.28%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: ฿1.12 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1.85M</div>
<div style="color:#ff3366; font-weight:bold; font-size:12px; margin-top:3px;">⚠️ ระวังการลากราคาแบบผิดปกติ (Speculative Pump / Low Turnover: การปั่นราคาเก็งกำไรในวอลุ่มต่ำ)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนไม่ถึงเกณฑ์ความปลอดภัยของตลาดหุ้นไทย (ต่ำกว่า 5 ล้านบาท) สภาพคล่องแคบมาก ไม่เอื้อต่อการรันเทรนด์ระยะกลาง
</div>
</div>
</div>""",

            "🌍 หุ้นต่างประเทศ (US)": """<div style="background:#131722; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">PLTR (Palantir)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+3.15%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $62.40 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $840M</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานรูปถ้วยและหู (Cup and Handle Base: โครงสร้างถ้วยหูพร้อมเบรก) บนแนวรับเส้นค่าเฉลี่ยถ่วงน้ำหนักตามปริมาณซื้อขาย (VWAP: Volume Weighted Average Price) ปริมาณซื้อขายเริ่มฟื้นตัวหนุนโอกาสทำจุดสูงสุดใหม่รอบปี
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำเทคโนโลยีขนาดใหญ่ (Mega-Cap Momentum: หุ้นยักษ์ใหญ่แรงส่งสูง)</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">NVDA (NVIDIA)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+5.82%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $148.90 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $14,200M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ อภิมหาสภาพคล่องระดับโลก (Mega Liquidity Flow: กระแสเงินทุนมหาศาล)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> เม็ดเงินหมุนเวียนระดับหมื่นล้านดอลลาร์สหรัฐ ขับเคลื่อนด้วยอุปสงค์จริงของกองทุนระดับโลก โมเมนตัมแข็งแกร่งต่อเนื่อง
</div>
</div>
</div>""",

            "🪙 ตลาดทองคำ (Macro)": """<div style="background:#131722; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 ภาวะการบีบอัดความผันผวน (Volatility Squeeze Preparation: การสะสมพลังก่อนเลือกทาง)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">XAU/USD (Gold Spot: ทองคำสปอต)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+0.42%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $2,645.20 • ตลาดล่วงหน้าสากล (Global Futures: สัญญาซื้อขายล่วงหน้าระดับโลก)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> การเคลื่อนไหวของราคารายวันบีบแคบลงในกรอบไม่เกิน $12 เป็นเวลา 5 วันทำการ ปริมาณการซื้อขายชะลอตัวเพื่อรอตัวเลขเศรษฐกิจมหภาค เป็นพฤติกรรมกักเก็บพลังงานก่อนระเบิดแนวโน้มระลอกใหญ่
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 สัญญาณทะลุจุดสูงสุดรอบสัปดาห์ (Momentum Surge Breakout: ทะลุแนวต้านด้วยแรงส่ง)</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">PAXG/USDT (Tokenized Gold: เหรียญทองคำดิจิทัล)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+1.65%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $2,652.10 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $48.20M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ เกิด Breakout เหนือกรอบสะสม 20 วัน (20-Day High Breakout: ทะลุจุดสูงสุด 20 วัน)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> การปรับตัวขึ้นเกิน +1.5% ของทองคำถือเป็นความผิดปกติเชิงโมเมนตัม สะท้อนการเคลื่อนย้ายเงินทุนเข้าสู่สินทรัพย์ปลอดภัย (Safe Haven Flow: เงินไหลเข้าหลบภัย) ชัดเจน
</div>
</div>
</div>""",

            "🔄 คริปโตทางเลือกในแอป (Altcoins: เหรียญคริปโตอื่นๆ)": """<div style="background:#131722; padding:14px; border-radius:8px; font-size:13px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:13.5px; margin-bottom:8px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">SUI/USDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+5.12%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $3.42 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $420M</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาบีบอัดตัวในกรอบสะสมพลังเหนือเส้นค่าเฉลี่ย EMA 20 วัน ปริมาณซื้อขาย (Volume: ปริมาณการซื้อขาย) เริ่มยกตัวขึ้น 1.5 เท่า จ่อทะลุแนวต้านสำคัญ
</div>
</div>
<div style="margin-bottom:8px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">APT/USDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+3.85%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $9.15 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $185M</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ดัชนีแรงซื้อสะสม 7/10 โครงสร้างยกฐานราคา (Higher Low) ต่อเนื่อง สภาพคล่องฝั่งซื้อตั้งรับหนาแน่น มีโอกาสเกิด Breakout (การทะลุกรอบ) ในระยะสั้น
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:13.5px; margin:14px 0 8px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">SOL/USDT</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+11.45%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $214.80 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $3,850M</div>
<div style="color:#00e676; font-weight:bold; font-size:12px; margin-top:3px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ปริมาณเงินหมุนเวียนหลายพันล้านดอลลาร์สหรัฐ ทะลุกรอบสะสม 1 เดือนเต็ม ยืนยันกระแสเงินทุนสถาบันไหลเข้าต่อเนื่อง มีโอกาสรันเทรนด์ไปต่อชัดเจน
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:14.5px;">LOW-CAP MEME (เหรียญมีมขนาดเล็ก)</b> <span style="color:#00e676; font-size:14px; font-weight:bold;">+28.40%</span>
</div>
<div style="color:#94a3b8; font-size:12px; margin-top:2px;">ราคา: $0.00045 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.15M</div>
<div style="color:#ff3366; font-weight:bold; font-size:12px; margin-top:3px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#cbd5e1; font-size:12.5px; line-height:1.5; margin-top:4px;">
• <b>บทวิเคราะห์:</b> ราคาพุ่งขึ้นแรงจากสภาพคล่องที่เบาบางมาก ยอดซื้อขายจริงไม่ถึงเกณฑ์ความปลอดภัย เสี่ยงต่อการโดนทุบราคาฉับพลัน (Dump Risk: ความเสี่ยงถูกเทขาย)
</div>
</div>
</div>"""
        }

        modal_market_htmls = {
            "🇹🇭 Bitkub (THB)": """<div style="background:#131722; padding:22px; border-radius:12px; font-size:15px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">THBVIC</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+4.35%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: ฿0.96 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿275,855</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาบีบอัดตัวในกรอบแคบ 48 ชม. ปริมาณซื้อขาย (Volume) เริ่มยกตัว 1.4 เท่า โครงสร้างอยู่ในระยะสะสมพลัง (Accumulation Phase: ช่วงสะสมพลัง) จ่อทดสอบแนวต้าน ฿1.02
</div>
</div>
<div style="margin-bottom:10px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">THBSOON</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+4.23%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: ฿7.40 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿191,216</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ดัชนีแรงซื้อสะสม 6/10 เกิดภาวะกรอบราคาบีบอัดตัวแคบ (Volatility Squeeze: การบีบตัวของความผันผวน) สภาพคล่องตั้งฐานรับเหนียวแน่น เหมาะแก่การวางกรอบดักซื้อต้นทุนต่ำ
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">THBSQD</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+22.87%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: ฿1.54 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿6,002,284</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนทะลุ 6 ล้านบาท ปริมาณซื้อขายพุ่งสูงกว่าค่าเฉลี่ย 3.5 เท่า ยืนยันกระแสเงินทุนไหลเข้าจริง ไม่ใช่การลากราคาลอยตัว
</div>
</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">THBWIN</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+17.41%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: ฿0.00106 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿27,968</div>
<div style="color:#ff3366; font-weight:bold; font-size:14.5px; margin-top:4px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> แม้ราคาบวกสูงแต่ยอดเงินซื้อขายทั้งวันมีเพียง 2.7 หมื่นบาท เกิดจากการเคาะซื้อในกระดานที่ไม่มีคนตั้งขาย เสี่ยงโดนเทขายทุบราคาฉับพลัน
</div>
</div>
</div>""",

            "🌐 Binance (USDT)": """<div style="background:#131722; padding:22px; border-radius:12px; font-size:15px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">MEUSDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+4.80%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $0.0657 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $3.54M</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> เกิดการสะสมพลังพร้อมปริมาณเงินหมุนเวียนสูงโดดเด่น โครงสร้างราขายกฐานขึ้นอย่างมั่นคง มีโอกาสดันราคาผ่านแนวต้านสูง
</div>
</div>
<div style="margin-bottom:10px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">XMRUSDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+4.77%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $118.70 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.57M</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาทรงตัวในกรอบบีบอัดแคบ แต่ปริมาณการซื้อขายยังไม่ระเบิด แนะนำรอสัญญาณวอลุ่มซัพพอร์ตเพื่อยืนยันการเบรกแนวต้าน
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">PROMUSDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+37.73%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $2.811 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $5.16M</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> โมเมนตัมแข็งแกร่งมาก เงินหมุนเวียนหนาแน่นทะลุ 5 ล้านดอลลาร์สหรัฐ ยืนยันเทรนด์ขาขึ้นขนาดใหญ่ มีโอกาสรันเทรนด์ไปต่อชัดเจน
</div>
</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">CREAMUSDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+65.35%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $2.100 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.28M</div>
<div style="color:#ff3366; font-weight:bold; font-size:14.5px; margin-top:4px;">⚠️ เกิดสัญญาณขัดแย้งเชิงลบกับวอลุ่ม (Bearish Divergence / Bull Trap: ราคาขึ้นแต่วอลุ่มลด/กับดักล่อซื้อ)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาพุ่งแรงเกินจริงแต่เม็ดเงินหมุนเวียนต่ำมาก เกิดจากสภาพคล่องที่ว่างเปล่า เสี่ยงโดนเทขายทำกำไรฉับพลัน ไม่ควรไล่ราคา
</div>
</div>
</div>""",

            "📈 หุ้นไทย (SET)": """<div style="background:#131722; padding:22px; border-radius:12px; font-size:15px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">WHA</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+2.63%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: ฿5.85 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿215.40M</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานสะสมอย่างเหนียวแน่นเหนือแนวรับเส้นค่าเฉลี่ยเคลื่อนที่ (EMA 15 วัน: Exponential Moving Average) ปริมาณซื้อขายแท่งเขียวเริ่มหนาขึ้นผิดปกติในรอบ 10 วันทำการ จ่อทดสอบจุดสูงสุดเดิม
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำกลุ่มอุตสาหกรรม (Sector Leaders: ผู้นำกลุ่มอุตสาหกรรม)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">HANA</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+8.97%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: ฿42.50 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1,420M</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ แรงซื้อสถาบันและกองทุนตรวจพบจริง (Institutional Inflow: เม็ดเงินสถาบันไหลเข้า)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนระดับพันล้านบาท ปริมาณซื้อขายเข้ามากกว่าค่าเฉลี่ย 20 วันถึง 4 เท่า ยืนยันการหมุนเวียนกลุ่มลงทุน (Sector Rotation: การโยกย้ายเงินลงทุนข้ามกลุ่ม) เข้าสู่ชิ้นส่วนอิเล็กทรอนิกส์
</div>
</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">SMALL-CAP (หุ้นขนาดเล็ก)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+14.28%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: ฿1.12 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1.85M</div>
<div style="color:#ff3366; font-weight:bold; font-size:14.5px; margin-top:4px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนไม่ถึงเกณฑ์ความปลอดภัยของตลาดหุ้นไทย (ต่ำกว่า 5 ล้านบาท) สภาพคล่องแคบมาก ไม่เอื้อต่อการรันเทรนด์ระยะกลาง
</div>
</div>
</div>""",

            "🌍 หุ้นต่างประเทศ (US)": """<div style="background:#131722; padding:22px; border-radius:12px; font-size:15px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">PLTR (Palantir)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+3.15%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $62.40 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $840M</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานรูปถ้วยและหู (Cup and Handle Base: โครงสร้างถ้วยหูพร้อมเบรก) บนแนวรับเส้นค่าเฉลี่ยถ่วงน้ำหนักตามปริมาณซื้อขาย (VWAP: Volume Weighted Average Price) ปริมาณซื้อขายเริ่มฟื้นตัวหนุนโอกาสทำจุดสูงสุดใหม่รอบปี
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำเทคโนโลยีขนาดใหญ่ (Mega-Cap Momentum: หุ้นยักษ์ใหญ่แรงส่งสูง)</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">NVDA (NVIDIA)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+5.82%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $148.90 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $14,200M</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ อภิมหาสภาพคล่องระดับโลก (Mega Liquidity Flow: กระแสเงินทุนมหาศาล)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> เม็ดเงินหมุนเวียนระดับหมื่นล้านดอลลาร์สหรัฐ ขับเคลื่อนด้วยอุปสงค์จริงของกองทุนระดับโลก โมเมนตัมแข็งแกร่งต่อเนื่อง
</div>
</div>
</div>""",

            "🪙 ตลาดทองคำ (Macro)": """<div style="background:#131722; padding:22px; border-radius:12px; font-size:15px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 ภาวะการบีบอัดความผันผวน (Volatility Squeeze Preparation: การสะสมพลังก่อนเลือกทาง)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">XAU/USD (Gold Spot: ทองคำสปอต)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+0.42%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $2,645.20 • ตลาดล่วงหน้าสากล (Global Futures: สัญญาซื้อขายล่วงหน้าระดับโลก)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> การเคลื่อนไหวของราคารายวันบีบแคบลงในกรอบไม่เกิน $12 เป็นเวลา 5 วันทำการ ปริมาณการซื้อขายชะลอตัวเพื่อรอตัวเลขเศรษฐกิจมหภาค เป็นพฤติกรรมกักเก็บพลังงานก่อนระเบิดแนวโน้มระลอกใหญ่
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 สัญญาณทะลุจุดสูงสุดรอบสัปดาห์ (Momentum Surge Breakout: ทะลุแนวต้านด้วยแรงส่ง)</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">PAXG/USDT (Tokenized Gold: เหรียญทองคำดิจิทัล)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+1.65%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $2,652.10 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $48.20M</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ เกิด Breakout เหนือกรอบสะสม 20 วัน (20-Day High Breakout: ทะลุจุดสูงสุด 20 วัน)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> การปรับตัวขึ้นเกิน +1.5% ของทองคำถือเป็นความผิดปกติเชิงโมเมนตัม สะท้อนการเคลื่อนย้ายเงินทุนเข้าสู่สินทรัพย์ปลอดภัย (Safe Haven Flow: เงินไหลเข้าหลบภัย) ชัดเจน
</div>
</div>
</div>""",

            "🔄 คริปโตทางเลือกในแอป (Altcoins: เหรียญคริปโตอื่นๆ)": """<div style="background:#131722; padding:22px; border-radius:12px; font-size:15px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; font-size:16.5px; margin-bottom:12px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">SUI/USDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+5.12%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $3.42 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $420M</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาบีบอัดตัวในกรอบสะสมพลังเหนือเส้นค่าเฉลี่ย EMA 20 วัน ปริมาณซื้อขาย (Volume: ปริมาณการซื้อขาย) เริ่มยกตัวขึ้น 1.5 เท่า จ่อทะลุแนวต้านสำคัญ
</div>
</div>
<div style="margin-bottom:10px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">APT/USDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+3.85%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $9.15 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $185M</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ดัชนีแรงซื้อสะสม 7/10 โครงสร้างยกฐานราคา (Higher Low) ต่อเนื่อง สภาพคล่องฝั่งซื้อตั้งรับหนาแน่น มีโอกาสเกิด Breakout (การทะลุกรอบ) ในระยะสั้น
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; font-size:16.5px; margin:20px 0 12px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">SOL/USDT</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+11.45%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $214.80 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $3,850M</div>
<div style="color:#00e676; font-weight:bold; font-size:14.5px; margin-top:4px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ปริมาณเงินหมุนเวียนหลายพันล้านดอลลาร์สหรัฐ ทะลุกรอบสะสม 1 เดือนเต็ม ยืนยันกระแสเงินทุนสถาบันไหลเข้าต่อเนื่อง มีโอกาสรันเทรนด์ไปต่อชัดเจน
</div>
</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b style="font-size:18px;">LOW-CAP MEME (เหรียญมีมขนาดเล็ก)</b> <span style="color:#00e676; font-size:17px; font-weight:bold;">+28.40%</span>
</div>
<div style="color:#94a3b8; font-size:14px; margin-top:3px;">ราคา: $0.00045 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.15M</div>
<div style="color:#ff3366; font-weight:bold; font-size:14.5px; margin-top:4px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#f1f5f9; font-size:15px; line-height:1.6; margin-top:6px;">
• <b>บทวิเคราะห์:</b> ราคาพุ่งแรงเกินจริงแต่เม็ดเงินหมุนเวียนต่ำมาก เกิดจากสภาพคล่องที่ว่างเปล่า เสี่ยงโดนเทขายทำกำไรฉับพลัน ไม่ควรไล่ราคา
</div>
</div>
</div>"""
        }

        # =========================================================
        # แท็บ 2 ส่วนล่าง (รูปที่ 4): กล่องเลื่อนอิสระส่วนล่าง (เรดาร์คัดกรองตลาดพหุสินทรัพย์)
        # =========================================================
        with st.container(height=400):
            st.markdown("<div style='font-size:14.5px; font-weight:bold; color:#f8fafc; margin:4px 0 8px 0;'>📡 เรดาร์คัดกรองตลาดพหุสินทรัพย์ (Multi-Market Tactical Screener)</div>", unsafe_allow_html=True)

            market_choice = st.selectbox(
                "เลือกตลาดที่ต้องการสแกน:",
                options=[
                    "🇹🇭 Bitkub (THB)", 
                    "🌐 Binance (USDT)", 
                    "📈 หุ้นไทย (SET)", 
                    "🌍 หุ้นต่างประเทศ (US)", 
                    "🪙 ตลาดทองคำ (Macro)", 
                    "🔄 คริปโตทางเลือกในแอป (Altcoins: เหรียญคริปโตอื่นๆ)"
                ],
                label_visibility="collapsed",
                key="screener_market_selector"
            )

            st.markdown(market_htmls[market_choice], unsafe_allow_html=True)

            if st.button("📊 ขยายเรดาร์คัดกรองตลาด (Expand Market Screener: ขยายเรดาร์คัดกรอง)", key="btn_open_bottom_screener_modal", use_container_width=True, type="secondary"):
                show_bottom_screener_modal(modal_market_htmls, market_choice)