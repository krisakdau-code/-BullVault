from ui.technical_modal import show_technical_modal
from ui.seasonality_modal import show_seasonality_modal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_right_panel(df: pd.DataFrame, meta: dict, is_thb_mode: bool = False, fx_rate: float = 35.0):
    """
    พาเนลฝั่งขวา: แท็บ 1 ภาพรวมตลาด 8 บล็อก + แท็บ 2 วิเคราะห์ข้อมูลเทคนิคเชิงลึก
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

        # บล็อก 1 & 2: ส่วนหัว, ราคา และ Bid/Ask Depth
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

        # บล็อก 3: แถบหลอดสเกลวัดตำแหน่งราคา (Day Range & 52-Week Range)
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

        # บล็อก 4 & 5: ข่าวสำคัญ + สถิติ Volume
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

        # บล็อก 6: Performance Matrix
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

        # บล็อก 7: กราฟฤดูกาล (Seasonality Trend)
        st.markdown("<div style='font-size:12px; font-weight:bold; color:#d1d4dc; margin:6px 0 2px 0;'>สถิติแนวโน้มฤดูกาล (Seasonality Trend)</div>", unsafe_allow_html=True)
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

        # ปุ่มเปิดหน้าต่างฤดูกาลเพิ่มเติม
        if st.button("ฤดูกาลเพิ่มเติม", key="btn_open_seasonality_modal", use_container_width=True, type="secondary"):
            show_seasonality_modal(sym=st.session_state.get("current_symbol", "BTCUSDT"))

        # บล็อก 8: Technical Gauge สไตล์ TradingView Pro ผ่าน Iframe
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

                    <!-- รางโค้งพื้นหลัง -->
                    <path d="M 45,100 A 95,95 0 0,1 235,100" fill="none" stroke="#1f242c" stroke-width="8" stroke-linecap="round" />

                    <!-- เส้นโค้งสีสัญญาณ -->
                    <path d="M 45,100 A 95,95 0 0,1 235,100" fill="none" stroke="url(#cyberArc)" stroke-width="5" stroke-linecap="round" />

                    <!-- ป้ายข้อความ 5 ช่วง -->
                    <text x="32" y="106" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงขายรุนแรง</text>
                    <text x="65" y="44" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงขาย</text>
                    <text x="140" y="18" font-size="9" font-weight="700" fill="#8b949e" text-anchor="middle">เป็นกลาง</text>
                    <text x="215" y="44" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงซื้อ</text>
                    <text x="248" y="106" font-size="8" fill="#6e7681" text-anchor="middle">มีแรงซื้อรุนแรง</text>

                    <!-- เข็มชี้วัดและหมุดกลาง -->
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

        # ปุ่มเปิดหน้าต่างทางเทคนิคเพิ่มเติม
        if st.button("ทางเทคนิคเพิ่มเติม", use_container_width=True, type="secondary"):
            show_technical_modal(sym=st.session_state.get("current_symbol", "BTCUSDT"))

    # -------------------------------------------------------------
    # แท็บ 2: ยุทธศาสตร์ & ข้อวิเคราะห์เทคนิค
    # -------------------------------------------------------------
    with tab_pro:
        # =========================================================
        # 1. ส่วนบน: วินิจฉัยสินทรัพย์บนกราฟหลัก (Active Asset Diagnostic)
        # =========================================================
        sym_name = meta.get("display_name", meta.get("symbol", "สินทรัพย์ปัจจุบัน"))
        exch_name = str(meta.get("exchange", "BINANCE")).upper()
        cat_name = str(meta.get("category", "Crypto")).upper()

        # คำนวณยอดเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย)
        vol_recent = float(df["volume"].tail(24).sum()) if len(df) >= 24 else float(df["volume"].sum())
        turnover_val = vol_recent * (curr_p / mult)

        # กำหนดเกณฑ์สภาพคล่องขั้นต่ำ (Minimum Liquidity Threshold) แยกตามประเภทตลาด
        if "SET" in exch_name or "STOCK" in cat_name:
            min_turnover = 5_000_000.0  # ตลาดหุ้นไทย เกณฑ์ปลอดภัยขั้นต่ำ 5 ล้านบาท
            turnover_currency = "THB (บาท)"
        elif "BITKUB" in exch_name:
            min_turnover = 1_000_000.0  # Bitkub เกณฑ์ปลอดภัยขั้นต่ำ 1 ล้านบาท
            turnover_currency = "THB (บาท)"
        elif "GOLD" in sym_name.upper() or "XAU" in sym_name.upper():
            min_turnover = 100_000.0
            turnover_currency = "USD (ดอลลาร์สหรัฐ)"
        else:
            min_turnover = 1_000_000.0  # ตลาดโลก / Binance เกณฑ์ปลอดภัย 1 ล้านดอลลาร์สหรัฐ
            turnover_currency = "USD (ดอลลาร์สหรัฐ)"

        # มิติที่ 1: การประเมินสภาพคล่อง (Turnover Liquidity Profile)
        is_liquid = turnover_val >= min_turnover
        if is_liquid:
            liq_badge = '<span style="color:#00e676; background:rgba(0,230,118,0.15); padding:2px 8px; border-radius:4px; font-weight:bold; font-size:11px;">🟢 สภาพคล่องสูง (High Liquidity: มีสภาพคล่องหนาแน่น)</span>'
            liq_desc = "ปริมาณเงินหมุนเวียนหนาแน่นเพียงพอ ปราศจากความเสี่ยงเรื่องการขาดสภาพคล่องหรือราคาคลาดเคลื่อนสูง (Slippage: ส่วนต่างราคาคำสั่งซื้อขาย)"
        else:
            liq_badge = '<span style="color:#ff9800; background:rgba(255,152,0,0.15); padding:2px 8px; border-radius:4px; font-weight:bold; font-size:11px;">⚠️ สภาพคล่องต่ำ (Low Liquidity Trap: กับดักสภาพคล่องแห้ง)</span>'
            liq_desc = "ยอดเงินหมุนเวียนเบาบางกว่าเกณฑ์มาตรฐานความปลอดภัย ระวังคำสั่งซื้อขายจับคู่ไม่สมบูรณ์หรือการเคาะราคาในช่องว่าง (Thin Order Book: กระดานซื้อขายเบาบาง)"

        # มิติที่ 2: ดัชนีแรงซื้อสะสม (Accumulation Score: คะแนนแรงซื้อสะสม 1-10)
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

        # มิติที่ 3: การจำแนกพฤติกรรม (แรงซื้อจริง Organic Demand vs แรงปั่น Wash Trading)
        if chg_pct >= 4.0 and not is_liquid:
            demand_status = '<span style="color:#ff3366; font-weight:bold;">⚠️ ระวังแรงปั่น / กับดักลากราคา (Wash Trading / Bull Trap: การสร้างวอลุ่มเทียม/กับดักล่อซื้อ)</span>'
            demand_article = "ราคาปรับตัวขึ้นสูงแต่ยอดเงินหมุนเวียนต่ำกว่าเกณฑ์ความปลอดภัยอย่างมาก สะท้อนพฤติกรรมการเคาะซื้อลอยตัวในภาวะกระดานบาง เสี่ยงต่อการโดนเทขายทุบราคาฉับพลัน (Dump Risk: ความเสี่ยงถูกเทขาย)"
        elif chg_pct >= 2.0 and accum_score >= 7 and is_liquid:
            demand_status = '<span style="color:#00e676; font-weight:bold;">✅ แรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</span>'
            demand_article = "การปรับขึ้นมีมูลค่าเงินหมุนเวียนและปริมาณซื้อขายสนับสนุนอย่างมีนัยสำคัญ ไม่พบสัญญาณขัดแย้งเชิงลบ (Bearish Divergence: ราคาขึ้นแต่วอลุ่มลดลง) มีโอกาสรันเทรนด์ไปต่อสูง"
        elif accum_score >= 6 and abs(chg_pct) <= 3.0:
            demand_status = '<span style="color:#38bdf8; font-weight:bold;">🌱 ทรงตัวสะสมพลังต้นน้ำ (Accumulation Setup: รูปแบบสะสมพลังก่อนวิ่ง)</span>'
            demand_article = "ราคาทรงตัวในกรอบสะสมพลัง แรงซื้อเริ่มตั้งฐานอย่างเหนียวแน่น มีความเสี่ยงขาลงต่ำ เหมาะแก่การเฝ้าระวังจังหวะทะลุกรอบ"
        else:
            demand_status = '<span style="color:#94a3b8; font-weight:bold;">⚖️ สภาวะสมดุลตามกลไกตลาด (Neutral Market Flow: สภาพตลาดเป็นกลาง)</span>'
            demand_article = "แรงซื้อและแรงขายมีสัดส่วนใกล้เคียงกัน ราคากำลังสร้างฐานรอความชัดเจนจากปัจจัยชี้นำภายนอก"

        # เรนเดอร์การ์ดวิเคราะห์ส่วนบน (ติดชิดซ้าย ไม่มีบรรทัดว่าง ป้องกัน Markdown มองเป็น Code Block)
        st.markdown(f"""<div style="background:#0f172a; padding:12px; border-radius:8px; border:1px solid #3b82f6; margin-bottom:12px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-weight:bold; color:#60a5fa; font-size:14px;">🎯 การวินิจฉัยกระแสเงินทุน: {sym_name}</span>
{liq_badge}
</div>
<div style="font-size:11px; color:#94a3b8; margin-top:2px;">
ตลาด: {exch_name} • หมวด: {cat_name}
</div>
<div style="margin-top:10px; background:#131722; padding:10px; border-radius:6px; border:1px solid #1e222d; font-size:11px;">
<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
<span style="color:#787b86;">1. ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย):</span>
<b style="color:#f8fafc;">{turnover_val:,.0f} {turnover_currency}</b>
</div>
<div style="color:#94a3b8; font-size:10px; line-height:1.4; margin-bottom:8px;">• {liq_desc}</div>
<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
<span style="color:#787b86;">2. ดัชนีแรงซื้อสะสม (Accumulation Score: คะแนนแรงซื้อสะสม):</span>
<b style="color:{score_color}; font-family:monospace; font-size:12px;">{score_bar} ({accum_score}/10)</b>
</div>
<div style="color:#94a3b8; font-size:10px; line-height:1.4; margin-bottom:8px;">• {score_desc}</div>
<div style="margin-top:6px; padding-top:6px; border-top:1px dashed #21262d;">
<span style="color:#787b86;">3. การจำแนกพฤติกรรม:</span> {demand_status}
<div style="color:#e2e8f0; font-size:11px; line-height:1.4; margin-top:4px;">{demand_article}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # โซนราคาสำคัญเดิม (Key Levels) & Spread Analysis (คงไว้ตามเดิม 100%)
        # -------------------------------------------------------------
        high_pivot = float(df["high"].tail(50).max()) * mult
        low_pivot = float(df["low"].tail(50).min()) * mult
        fib_mid = (high_pivot + low_pivot) / 2

        st.markdown(f"""<div style="background:#131722; padding:10px; border-radius:6px; margin-bottom:12px;">
<div style="font-size:12px; font-weight:bold; color:#f8fafc; margin-bottom:6px;">📌 โซนราคาสำคัญ (Key Levels: ระดับราคาสำคัญ)</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:#ef4444; padding:2px 0;">
<span>แนวต้านสำคัญ (Major Resistance)</span><b>{high_pivot:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:#38bdf8; padding:2px 0;">
<span>จุดกึ่งกลางดุลยภาพ (Equilibrium)</span><b>{fib_mid:,.2f}</b>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:#22c55e; padding:2px 0;">
<span>แนวรับสำคัญ (Major Support)</span><b>{low_pivot:,.2f}</b>
</div>
</div>""", unsafe_allow_html=True)

        sym_check = str(meta.get("symbol", ""))
        if "RICE" in sym_check or "FOB" in sym_check:
            st.markdown(f"""<div style="background:#1e1b4b; padding:10px; border-radius:6px; border-left:3px solid #818cf8; margin-bottom:12px;">
<div style="font-size:12px; font-weight:bold; color:#c7d2fe;">🌾 การวิเคราะห์ส่วนต่างข้าว (Spread Analysis: การวิเคราะห์ส่วนต่างราคา)</div>
<div style="font-size:11px; color:#e0e7ff; margin-top:4px;">
• ราคาแปลงเป็นบาท: <b>{curr_p:,.2f} {display_unit}</b><br>
• อัตราแลกเปลี่ยนคำนวณ: <b>{fx_rate:.2f} บาท/USD</b><br>
• สถานะส่วนต่าง: ราคาเวียดนามต่ำกว่าไทย ~<b>30 USD/ตัน</b> ส่งผลให้ผู้ส่งออกชะลอการซื้อข้าวเปลือกหน้าโรงสี
</div>
</div>""", unsafe_allow_html=True)

        # =========================================================
        # 2. ส่วนล่าง: ศูนย์คัดกรองเรดาร์พหุสินทรัพย์ (Multi-Market Screener)
        # =========================================================
        st.markdown("<div style='font-size:13px; font-weight:bold; color:#f8fafc; margin:10px 0 6px 0;'>📡 เรดาร์คัดกรองตลาดพหุสินทรัพย์ (Multi-Market Tactical Screener)</div>", unsafe_allow_html=True)

        # เปลี่ยนเป็นแบบกล่องเลื่อนลง (selectbox) พอดีความกว้างพาเนล ไม่ตกขอบจอ
        market_choice = st.selectbox(
            "เลือกตลาดที่ต้องการสแกน:",
            options=["🇹🇭 Bitkub (THB)", "🌐 Binance (USDT)", "📈 หุ้นไทย (SET)", "🌍 หุ้นต่างประเทศ (US)", "🪙 ตลาดทองคำ (Macro)", "🔄 กระดานอื่นๆ ในแอป"],
            label_visibility="collapsed",
            key="screener_market_selector"
        )

        if market_choice == "🇹🇭 Bitkub (THB)":
            st.markdown("""<div style="background:#131722; padding:10px; border-radius:6px; font-size:11px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; margin-bottom:6px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>THBVIC</b> <span style="color:#00e676;">+4.35%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: ฿0.96 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿275,855</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ราคาบีบอัดตัวในกรอบแคบ 48 ชม. ปริมาณซื้อขาย (Volume) เริ่มยกตัว 1.4 เท่า โครงสร้างอยู่ในระยะสะสมพลัง (Accumulation Phase: ช่วงสะสมพลัง) จ่อทดสอบแนวต้าน ฿1.02
</div>
</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b>THBSOON</b> <span style="color:#00e676;">+4.23%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: ฿7.40 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿191,216</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ดัชนีแรงซื้อสะสม 6/10 เกิดภาวะกรอบราคาบีบอัดตัวแคบ (Volatility Squeeze: การบีบตัวของความผันผวน) สภาพคล่องตั้งฐานรับเหนียวแน่น เหมาะแก่การวางกรอบดักซื้อต้นทุนต่ำ
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; margin:12px 0 6px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>THBSQD</b> <span style="color:#00e676;">+22.87%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: ฿1.54 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿6,002,284</div>
<div style="color:#00e676; font-weight:bold; font-size:10px; margin-top:2px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนทะลุ 6 ล้านบาท ปริมาณซื้อขายพุ่งสูงกว่าค่าเฉลี่ย 3.5 เท่า ยืนยันกระแสเงินทุนไหลเข้าจริง ไม่ใช่การลากราคาลอยตัว
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b>THBWIN</b> <span style="color:#00e676;">+17.41%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: ฿0.00106 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿27,968</div>
<div style="color:#ff3366; font-weight:bold; font-size:10px; margin-top:2px;">⚠️ ระวังกับดักสภาพคล่องต่ำ (Low-Turnover Trap / Bull Trap: กับดักวอลุ่มเงินน้อย/กับดักล่อซื้อ)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> แม้ราคาบวกสูงแต่ยอดเงินซื้อขายทั้งวันมีเพียง 2.7 หมื่นบาท เกิดจากการเคาะซื้อในกระดานที่ไม่มีคนตั้งขาย เสี่ยงโดนเทขายทุบราคาฉับพลัน
</div>
</div>
</div>""", unsafe_allow_html=True)

        elif market_choice == "🌐 Binance (USDT)":
            st.markdown("""<div style="background:#131722; padding:10px; border-radius:6px; font-size:11px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; margin-bottom:6px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>MEUSDT</b> <span style="color:#00e676;">+4.80%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $0.0657 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $3.54M</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> เกิดการสะสมพลังพร้อมปริมาณเงินหมุนเวียนสูงโดดเด่น โครงสร้างราขายกฐานขึ้นอย่างมั่นคง มีโอกาสดันราคาผ่านแนวต้านสูง
</div>
</div>
<div style="margin-bottom:6px;">
<div style="display:flex; justify-content:space-between;">
<b>XMRUSDT</b> <span style="color:#00e676;">+4.77%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $118.70 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.57M</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ราคาทรงตัวในกรอบบีบอัดแคบ แต่ปริมาณการซื้อขายยังไม่ระเบิด แนะนำรอสัญญาณวอลุ่มซัพพอร์ตเพื่อยืนยันการเบรกแนวต้าน
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; margin:12px 0 6px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — เป้าหมาย +15% ใน 2–3 วัน (High Momentum Run Trend: เกาะแนวโน้มตามแรงส่ง)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>PROMUSDT</b> <span style="color:#00e676;">+37.73%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $2.811 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $5.16M</div>
<div style="color:#00e676; font-weight:bold; font-size:10px; margin-top:2px;">✅ ตรวจพบแรงซื้อจริงหนาแน่น (Confirmed Organic Flow: กระแสเงินทุนจริงเข้าหนุน)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> โมเมนตัมแข็งแกร่งมาก เงินหมุนเวียนหนาแน่นทะลุ 5 ล้านดอลลาร์สหรัฐ ยืนยันเทรนด์ขาขึ้นขนาดใหญ่ มีโอกาสรันเทรนด์ไปต่อชัดเจน
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b>CREAMUSDT</b> <span style="color:#00e676;">+65.35%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $2.100 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): $0.28M</div>
<div style="color:#ff3366; font-weight:bold; font-size:10px; margin-top:2px;">⚠️ เกิดสัญญาณขัดแย้งเชิงลบกับวอลุ่ม (Bearish Divergence / Bull Trap: ราคาขึ้นแต่วอลุ่มลด/กับดักล่อซื้อ)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ราคาพุ่งแรงเกินจริงแต่เม็ดเงินหมุนเวียนต่ำมาก เกิดจากสภาพคล่องที่ว่างเปล่า เสี่ยงโดนเทขายทำกำไรฉับพลัน ไม่ควรไล่ราคา
</div>
</div>
</div>""", unsafe_allow_html=True)

        elif market_choice == "📈 หุ้นไทย (SET)":
            st.markdown("""<div style="background:#131722; padding:10px; border-radius:6px; font-size:11px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; margin-bottom:6px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>WHA</b> <span style="color:#00e676;">+2.63%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: ฿5.85 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿215.40M</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานสะสมอย่างเหนียวแน่นเหนือแนวรับเส้นค่าเฉลี่ยเคลื่อนที่ (EMA 15 วัน: Exponential Moving Average) ปริมาณซื้อขายแท่งเขียวเริ่มหนาขึ้นผิดปกติในรอบ 10 วันทำการ จ่อทดสอบจุดสูงสุดเดิม
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; margin:12px 0 6px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำกลุ่มอุตสาหกรรม (Sector Leaders: ผู้นำกลุ่มอุตสาหกรรม)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>HANA</b> <span style="color:#00e676;">+8.97%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: ฿42.50 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1,420M</div>
<div style="color:#00e676; font-weight:bold; font-size:10px; margin-top:2px;">✅ แรงซื้อสถาบันและกองทุนตรวจพบจริง (Institutional Inflow: เม็ดเงินสถาบันไหลเข้า)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนระดับพันล้านบาท ปริมาณซื้อขายเข้ามากกว่าค่าเฉลี่ย 20 วันถึง 4 เท่า ยืนยันการหมุนเวียนกลุ่มลงทุน (Sector Rotation: การโยกย้ายเงินลงทุนข้ามกลุ่ม) เข้าสู่ชิ้นส่วนอิเล็กทรอนิกส์
</div>
</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b>SMALL-CAP (หุ้นขนาดเล็ก)</b> <span style="color:#00e676;">+14.28%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: ฿1.12 • ปริมาณเงินหมุนเวียน 24 ชม. (Turnover: มูลค่าซื้อขาย): ฿1.85M</div>
<div style="color:#ff3366; font-weight:bold; font-size:10px; margin-top:2px;">⚠️ ระวังการลากราคาแบบผิดปกติ (Speculative Pump / Low Turnover: การปั่นราคาเก็งกำไรในวอลุ่มต่ำ)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ยอดเงินหมุนเวียนไม่ถึงเกณฑ์ความปลอดภัยของตลาดหุ้นไทย (ต่ำกว่า 5 ล้านบาท) สภาพคล่องแคบมาก ไม่เอื้อต่อการรันเทรนด์ระยะกลาง
</div>
</div>
</div>""", unsafe_allow_html=True)

        elif market_choice == "🌍 หุ้นต่างประเทศ (US)":
            st.markdown("""<div style="background:#131722; padding:10px; border-radius:6px; font-size:11px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; margin-bottom:6px;">🌱 หมวดตั้งฐานต้นน้ำ — จ่อทะลุกรอบ (Breakout Setup: ทะลุกรอบแนวต้าน)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>PLTR (Palantir)</b> <span style="color:#00e676;">+3.15%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $62.40 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $840M</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> ราคาสร้างฐานรูปถ้วยและหู (Cup and Handle Base: โครงสร้างถ้วยหูพร้อมเบรก) บนแนวรับเส้นค่าเฉลี่ยถ่วงน้ำหนักตามปริมาณซื้อขาย (VWAP: Volume Weighted Average Price) ปริมาณซื้อขายเริ่มฟื้นตัวหนุนโอกาสทำจุดสูงสุดใหม่รอบปี
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; margin:12px 0 6px 0;">🔥 หมวดรันเทรนด์โมเมนตัมสูง — ผู้นำเทคโนโลยีขนาดใหญ่ (Mega-Cap Momentum: หุ้นยักษ์ใหญ่แรงส่งสูง)</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b>NVDA (NVIDIA)</b> <span style="color:#00e676;">+5.82%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $148.90 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $14,200M</div>
<div style="color:#00e676; font-weight:bold; font-size:10px; margin-top:2px;">✅ อภิมหาสภาพคล่องระดับโลก (Mega Liquidity Flow: กระแสเงินทุนมหาศาล)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> เม็ดเงินหมุนเวียนระดับหมื่นล้านดอลลาร์สหรัฐ ขับเคลื่อนด้วยอุปสงค์จริงของกองทุนระดับโลก โมเมนตัมแข็งแกร่งต่อเนื่อง
</div>
</div>
</div>""", unsafe_allow_html=True)

        elif market_choice == "🪙 ตลาดทองคำ (Macro)":
            st.markdown("""<div style="background:#131722; padding:10px; border-radius:6px; font-size:11px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; margin-bottom:6px;">🌱 ภาวะการบีบอัดความผันผวน (Volatility Squeeze Preparation: การสะสมพลังก่อนเลือกทาง)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>XAU/USD (Gold Spot: ทองคำสปอต)</b> <span style="color:#00e676;">+0.42%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $2,645.20 • ตลาดล่วงหน้าสากล (Global Futures: สัญญาซื้อขายล่วงหน้าระดับโลก)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> การเคลื่อนไหวของราคารายวันบีบแคบลงในกรอบไม่เกิน $12 เป็นเวลา 5 วันทำการ ปริมาณการซื้อขายชะลอตัวเพื่อรอตัวเลขเศรษฐกิจมหภาค เป็นพฤติกรรมกักเก็บพลังงานก่อนระเบิดแนวโน้มระลอกใหญ่
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; margin:12px 0 6px 0;">🔥 สัญญาณทะลุจุดสูงสุดรอบสัปดาห์ (Momentum Surge Breakout: ทะลุแนวต้านด้วยแรงส่ง)</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b>PAXG/USDT (Tokenized Gold: เหรียญทองคำดิจิทัล)</b> <span style="color:#00e676;">+1.65%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคา: $2,652.10 • ปริมาณเงินหมุนเวียน (Turnover: มูลค่าซื้อขาย): $48.20M</div>
<div style="color:#00e676; font-weight:bold; font-size:10px; margin-top:2px;">✅ เกิด Breakout เหนือกรอบสะสม 20 วัน (20-Day High Breakout: ทะลุจุดสูงสุด 20 วัน)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> การปรับตัวขึ้นเกิน +1.5% ของทองคำถือเป็นความผิดปกติเชิงโมเมนตัม สะท้อนการเคลื่อนย้ายเงินทุนเข้าสู่สินทรัพย์ปลอดภัย (Safe Haven Flow: เงินไหลเข้าหลบภัย) ชัดเจน
</div>
</div>
</div>""", unsafe_allow_html=True)

        else:  # 🔄 กระดานอื่นๆ ในแอป
            st.markdown("""<div style="background:#131722; padding:10px; border-radius:6px; font-size:11px; border:1px solid #1e222d;">
<div style="color:#38bdf8; font-weight:bold; margin-bottom:6px;">🌱 สินทรัพย์ทางเลือกต้นน้ำ — จ่อทะลุกรอบ (Alternative Assets Setup: รูปแบบสินทรัพย์ทางเลือก)</div>
<div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #1e242c;">
<div style="display:flex; justify-content:space-between;">
<b>THAI-RICE-5% (ข้าวขาว 5%)</b> <span style="color:#00e676;">+1.20%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคาอ้างอิง: $585/ตัน • เกษตรพาณิชย์ (Agri-Commodity: สินค้าเกษตรเพื่อการค้า)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> สถิติส่วนต่างราคา (Spread Analysis: การวิเคราะห์ส่วนต่างราคา) ชะลอการขยายตัว โรงสีเริ่มทยอยเก็บสต็อกผลผลิต เกิดฐานราคารับแน่นหนา
</div>
</div>
<div style="color:#f59e0b; font-weight:bold; margin:12px 0 6px 0;">🔥 สินทรัพย์ทางเลือกรันเทรนด์ (High Momentum Trends: แนวโน้มแรงส่งสูง)</div>
<div style="margin-bottom:4px;">
<div style="display:flex; justify-content:space-between;">
<b>RUBBER-SICOM (ยางพารา)</b> <span style="color:#00e676;">+6.40%</span>
</div>
<div style="color:#787b86; font-size:10px;">ราคาอ้างอิง: 212.5 เซนต์/กก. • สัญญาซื้อขายล่วงหน้าสิงคโปร์ (SICOM Futures: ตลาดซื้อขายล่วงหน้ายางพาราสิงคโปร์)</div>
<div style="color:#00e676; font-weight:bold; font-size:10px; margin-top:2px;">✅ อุปสงค์อุตสาหกรรมรถยนต์หนุนจริง (Physical Demand Flow: ความต้องการใช้สินค้าจริงในอุตสาหกรรม)</div>
<div style="color:#94a3b8; margin-top:2px;">
• <b>บทวิเคราะห์:</b> อุปทานตึงตัวจากสภาพอากาศหนุนราคาทะลุแนวต้าน 200 เซนต์ กระแสเงินทุนเก็งกำไรไหลเข้าต่อเนื่อง
</div>
</div>
</div>""", unsafe_allow_html=True)