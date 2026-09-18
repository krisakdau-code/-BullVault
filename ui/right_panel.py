import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_right_panel(df: pd.DataFrame, meta: dict, is_thb_mode: bool = False, fx_rate: float = 35.0):
    """
    พาเนลฝั่งขวา: แท็บ 1 ภาพรวมตลาด 8 บล็อก + แท็บ 2 วิเคราะห์ข้อมูลเทคนิคเชิงลึก (ไม้ตาย)
    """
    tab_overview, tab_pro = st.tabs(["📊 ภาพรวมตลาด", "🧠 วิเคราะห์ข้อมูล & เทคนิค (ไม้ตาย)"])

    # -------------------------------------------------------------
    # แท็บ 1: โครงสร้าง 8 บล็อก (TradingView Redesign)
    # -------------------------------------------------------------
    with tab_overview:
        if df.empty or len(df) < 2:
            st.warning("ไม่มีข้อมูลแท่งเทียนเพียงพอสำหรับการวิเคราะห์")
            return

        # แปลงราคาตามโหมดที่เลือก
        mult = (fx_rate if (is_thb_mode and not meta["is_thb_native"]) else 1.0)
        curr_p = float(df["close"].iloc[-1]) * mult
        prev_p = float(df["close"].iloc[-2]) * mult
        chg_val = curr_p - prev_p
        chg_pct = (chg_val / prev_p * 100) if prev_p else 0.0
       #  เปลี่ยนเป็นบรรทัดนี้
        display_unit = "THB (บาท)" if (is_thb_mode or meta.get("is_thb_native", False)) else meta.get("unit", "USD")

        # บล็อก 1 & 2: ส่วนหัว, ราคา และ Bid/Ask Depth
        color_hex = "#00e676" if chg_val >= 0 else "#ff5252"
        sign = "+" if chg_val >= 0 else ""
        st.markdown(f"""
        <div style="background:#131722; padding:12px; border-radius:8px; border-left:3px solid {color_hex}; margin-bottom:10px;">
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
                    Bid {curr_p * 0.999:,.2f}
                </div>
                <div style="flex:1; background:#33141e; padding:4px; border-radius:4px; text-align:center; color:#ff5252; font-size:11px;">
                    Ask {curr_p * 1.001:,.2f}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # บล็อก 3: แถบหลอดสเกลวัดตำแหน่งราคา (Day Range & 52-Week Range)
        d_low = float(df["low"].tail(24).min()) * mult
        d_high = float(df["high"].tail(24).max()) * mult
        w_low = float(df["low"].min()) * mult
        w_high = float(df["high"].max()) * mult

        d_pct = max(0, min(100, int(((curr_p - d_low) / (d_high - d_low) * 100) if d_high > d_low else 50)))
        w_pct = max(0, min(100, int(((curr_p - w_low) / (w_high - w_low) * 100) if w_high > w_low else 50)))

        st.markdown(f"""
        <div style="background:#131722; padding:10px; border-radius:8px; margin-bottom:10px; font-size:11px;">
            <div style="display:flex; justify-content:space-between; color:#787b86;">
                <span>{d_low:,.1f}</span><span style="color:#d1d4dc;">ช่วงระหว่างวัน</span><span>{d_high:,.1f}</span>
            </div>
            <div style="height:4px; background:#2a2e39; border-radius:2px; margin:6px 0; position:relative;">
                <div style="height:100%; width:{d_pct}%; background:#2962ff; border-radius:2px;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; color:#787b86; margin-top:8px;">
                <span>{w_low:,.1f}</span><span style="color:#d1d4dc;">รอบ 52 สัปดาห์</span><span>{w_high:,.1f}</span>
            </div>
            <div style="height:4px; background:#2a2e39; border-radius:2px; margin:6px 0; position:relative;">
                <div style="height:100%; width:{w_pct}%; background:#00e676; border-radius:2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # บล็อก 4 & 5: ข่าวสำคัญ + สถิติ Volume
        vol_curr = float(df["volume"].iloc[-1])
        vol_avg = float(df["volume"].tail(30).mean())
        st.markdown(f"""
        <div style="background:#1a1a2e; padding:8px 10px; border-radius:6px; border-left:3px solid #7c4dff; margin-bottom:10px; font-size:11px;">
            <div style="color:#a78bfa; font-weight:bold;">⚡ สรุปปัจจัยข่าวสารล่าสุด</div>
            <div style="color:#d1d4dc; margin-top:2px;">ติดตามรอบสต็อกผลผลิตและการปรับอัตราดอกเบี้ยส่งผลกระทบต่ออุปสงค์สินค้า</div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11px; color:#787b86; padding:4px 2px;">
            <span>ปริมาณการซื้อขาย</span><span style="color:#fff; font-weight:bold;">{vol_curr:,.0f}</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11px; color:#787b86; padding:4px 2px; margin-bottom:10px;">
            <span>ปริมาณเฉลี่ย (30 แท่ง)</span><span style="color:#fff; font-weight:bold;">{vol_avg:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        # บล็อก 6: Performance Matrix
        def calc_perf(bars):
            if len(df) > bars:
                p_old = float(df["close"].iloc[-bars])
                return ((curr_p / mult - p_old) / p_old) * 100
            return 0.0

        perfs = {
            "1W": calc_perf(7), "1M": calc_perf(30), "3M": calc_perf(90),
            "6M": calc_perf(180), "YTD": calc_perf(240), "1Y": calc_perf(365)
        }

        cols = st.columns(3)
        for idx, (label, val) in enumerate(perfs.items()):
            c_hex = "#00e676" if val >= 0 else "#ff5252"
            s_sign = "+" if val >= 0 else ""
            cols[idx % 3].markdown(f"""
            <div style="background:#131722; padding:6px; border-radius:4px; text-align:center; margin-bottom:6px; border:1px solid #1e222d;">
                <div style="font-size:12px; font-weight:bold; color:{c_hex};">{s_sign}{val:.2f}%</div>
                <div style="font-size:10px; color:#787b86;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

        # บล็อก 7: กราฟฤดูกาล (Seasonality Trend)
        st.markdown("<div style='font-size:12px; font-weight:bold; color:#d1d4dc; margin:6px 0 2px 0;'>สถิติแนวโน้มฤดูกาล (Seasonality)</div>", unsafe_allow_html=True)
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

      # บล็อก 8: Technical Gauge สไตล์ TradingView Pro ผ่าน Iframe (เรนเดอร์ตรง ไม่โดนตัด SVG)
        import math
        import streamlit.components.v1 as components

        # ประเมินระดับสัญญาณจาก % การเปลี่ยนแปลง (-2 ถึง +2)
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

        # คำนวณมุมองศาเข็มชี้ (180 องศาฝั่งซ้าย -> 0 องศาฝั่งขวา)
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
                .more-btn {{
                    background: #21262d;
                    color: #8b949e;
                    border: 1px solid #30363d;
                    padding: 4px 14px;
                    border-radius: 16px;
                    font-size: 10px;
                    font-weight: 600;
                    cursor: pointer;
                    margin-top: 6px;
                }}
            </style>
        </head>
        <body>
            <div class="gauge-card notranslate" translate="no">
                <div class="header-row">
                    <span class="title-lbl">ทางเทคนิค</span>
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
                <button class="more-btn">ทางเทคนิคเพิ่มเติม</button>
            </div>
        </body>
        </html>
        """

        components.html(gauge_html, height=185)

    # -------------------------------------------------------------
    # แท็บ 2: ยุทธศาสตร์ & ข้อวิเคราะห์เทคนิค (พื้นที่ไม้ตาย)
    # -------------------------------------------------------------
    with tab_pro:
        st.markdown("""
        <div style="background:#0f172a; padding:12px; border-radius:8px; border:1px solid #3b82f6; margin-bottom:12px;">
            <div style="font-weight:bold; color:#60a5fa; font-size:14px;">🎯 โมเดลการวิเคราะห์ยุทธศาสตร์ & เทคนิค</div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">ระบบสังเคราะห์สัญญาณทางเทคนิคและสถิติส่วนต่างราคา (Crack Spread)</div>
        </div>
        """, unsafe_allow_html=True)

        # 1. แผงประเมินแนวรับ-แนวต้านอัตโนมัติ
        high_pivot = float(df["high"].tail(50).max()) * mult
        low_pivot = float(df["low"].tail(50).min()) * mult
        fib_mid = (high_pivot + low_pivot) / 2

        st.markdown(f"""
        <div style="background:#131722; padding:10px; border-radius:6px; margin-bottom:10px;">
            <div style="font-size:12px; font-weight:bold; color:#f8fafc; margin-bottom:6px;">📌 โซนราคาสำคัญ (Key Levels)</div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#ef4444; padding:2px 0;">
                <span>แนวต้านสำคัญ (Major Res)</span><b>{high_pivot:,.2f}</b>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#38bdf8; padding:2px 0;">
                <span>จุดกึ่งกลาง (Equilibrium)</span><b>{fib_mid:,.2f}</b>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#22c55e; padding:2px 0;">
                <span>แนวรับสำคัญ (Major Sup)</span><b>{low_pivot:,.2f}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. กรณีเป็นสินค้าข้าว/เกษตร: ส่วนต่างราคาเทียบตลาดโลก (Price Spread Matrix)
        #  แก้ไขเป็นบรรทัดนี้
        sym_check = str(meta.get("symbol", ""))
        if "RICE" in sym_check or "FOB" in sym_check:
            st.markdown(f"""
            <div style="background:#1e1b4b; padding:10px; border-radius:6px; border-left:3px solid #818cf8; margin-bottom:10px;">
                <div style="font-size:12px; font-weight:bold; color:#c7d2fe;">🌾 การวิเคราะห์ส่วนต่างข้าว (Spread Analysis)</div>
                <div style="font-size:11px; color:#e0e7ff; margin-top:4px;">
                    • ราคาแปลงเป็นบาท: <b>{curr_p:,.2f} {display_unit}</b><br>
                    • อัตราแลกเปลี่ยนคำนวณ: <b>{fx_rate:.2f} บาท/USD</b><br>
                    • สถานะส่วนต่าง: ราคาเวียดนามต่ำกว่าไทย ~<b>30 USD/ตัน</b> ส่งผลให้ผู้ส่งออกชะลอการซื้อข้าวเปลือกหน้าโรงสี
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 3. โซนบรรจุสูตรอินดิเคเตอร์หรืออัลกอริทึมไม้ตายของผู้ใช้ในอนาคต
        st.info("💡 **พื้นที่พร้อมต่อยอด:** สามารถผูกสูตรสัญญาณ Pine Script, ตรรกะตรวจจับ Smart Money Concept (SMC), หรือตารางดุลการค้าได้ทันที")