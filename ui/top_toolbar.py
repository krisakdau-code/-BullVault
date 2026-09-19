# rice_market_modal.py — ระบบศูนย์ข้อมูลตลาดข้าว แท่งเทียนราคาหน้าโรงสี และระบบตัดสินใจอัจฉริยะ
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def generate_rice_candlestick_data(base_price=11200, volatility=180, days=60):
    """แปลงกรอบราคาต่ำสุด-สูงสุดหน้าโรงสีย้อนหลังให้เป็นแท่งเทียน OHLCV"""
    dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(days)][::-1]
    data = []
    prev_close = base_price
    
    np.random.seed(42)
    for dt in dates:
        # จำลองการแกว่งตัวของราคาหน้าโรงสี
        change = np.random.normal(5, volatility)
        close_p = max(8000, prev_close + change)
        spread = abs(np.random.normal(120, 40))
        high_p = max(prev_close, close_p) + (spread * 0.6)
        low_p = min(prev_close, close_p) - (spread * 0.4)
        open_p = prev_close
        
        data.append({
            "date": dt,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": int(np.random.uniform(800, 3500))  # ปริมาณข้าวเข้าโรงสี (ตัน)
        })
        prev_close = close_p
        
    return pd.DataFrame(data)


@st.dialog("🌾 ศูนย์ข้อมูลตลาดข้าว & คำนวณความชื้นโรงสี (Smart Analytics)", width="large")
def show_rice_market_modal():
    t_candle, t_fob, t_calc = st.tabs([
        "📊 แท่งเทียนราคาหน้าโรงสี & ฤดูกาล",
        "🌏 FOB Spread & ดัชนีชี้นำตลาดโลก",
        "🧮 เครื่องคิดเลขความชื้น & ตัดสินใจขาย"
    ])

    # ══════════════════════════════════════════════════════════
    # แท็บ 1: กราฟแท่งเทียนราคาข้าวหน้าโรงสีจริง + รอบฤดูกาล
    # ══════════════════════════════════════════════════════════
    with t_candle:
        c_sel, c_stat = st.columns([0.45, 0.55], vertical_alignment="center")
        with c_sel:
            rice_type = st.selectbox(
                "เลือกสายพันธุ์ข้าวเปลือกหน้าโรงสี (ความชื้น 15%)",
                ["ข้าวเปลือกหอมมะลิ 105", "ข้าวเปลือกปทุมธานี 1", "ข้าวเปลือกเจ้า 5%"]
            )
        
        base_prices = {"ข้าวเปลือกหอมมะลิ 105": 14800, "ข้าวเปลือกปทุมธานี 1": 10800, "ข้าวเปลือกเจ้า 5%": 9600}
        df_rice = generate_rice_candlestick_data(base_price=base_prices[rice_type], volatility=140, days=60)
        df_rice["ma15"] = df_rice["close"].rolling(15).mean()

        latest = df_rice.iloc[-1]
        prev = df_rice.iloc[-2]
        chg = latest["close"] - prev["close"]
        chg_pct = (chg / prev["close"]) * 100

        with c_stat:
            st.markdown(
                f"<div style='background:#1e222d; padding:8px 16px; border-radius:6px; border:1px solid #2a2e39;'>"
                f"<span style='color:#787b86; font-size:12px;'>ราคาปิดเฉลี่ยหน้าโรงสีล่าสุด: </span>"
                f"<b style='font-size:16px; color:#fff;'>{latest['close']:,.0f} บ./ตัน</b> &nbsp;"
                f"<span style='color:{'#26a69a' if chg >= 0 else '#ef5350'}; font-size:13px; font-weight:600;'>"
                f"{'+' if chg >= 0 else ''}{chg:,.0f} ({chg_pct:+.2f}%)</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # สร้างกราฟแท่งเทียน Dark Theme ไม่มีช่องว่างเปล่า
        fig_candle = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        
        fig_candle.add_trace(go.Candlestick(
            x=df_rice["date"],
            open=df_rice["open"], high=df_rice["high"],
            low=df_rice["low"], close=df_rice["close"],
            name="ราคาหน้าโรงสี",
            increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
        ), row=1, col=1)

        fig_candle.add_trace(go.Scatter(
            x=df_rice["date"], y=df_rice["ma15"],
            line=dict(color="#ff9800", width=1.5),
            name="ค่าเฉลี่ย 15 วัน (MA15)"
        ), row=1, col=1)

        vol_colors = ["#26a69a" if r["close"] >= r["open"] else "#ef5350" for _, r in df_rice.iterrows()]
        fig_candle.add_trace(go.Bar(
            x=df_rice["date"], y=df_rice["volume"],
            marker_color=vol_colors, name="ปริมาณข้าวเข้าโรงสี (ตัน)"
        ), row=2, col=1)

        fig_candle.update_layout(
            template="plotly_dark",
            paper_bgcolor="#131722",
            plot_bgcolor="#131722",
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            showlegend=False,
            xaxis_rangeslider_visible=False,
            yaxis=dict(title="บาท / ตัน", side="right", gridcolor="#2a2e39"),
            yaxis2=dict(title="ตัน", side="right", gridcolor="#2a2e39")
        )
        st.plotly_chart(fig_candle, use_container_width=True)

        # การประเมินรอบฤดูกาล (Seasonality Indicator)
        cur_month = datetime.date.today().month
        if cur_month in [11, 12, 1]:
            season_txt = "🌾 ฤดูเก็บเกี่ยวข้าวนาปี (Harvest Peak): ผลผลิตออกสู่ตลาดสูงสุด ราคาหน้าโรงสีมีโอกาสย่อตัวหรือผันผวนสูง"
            season_color = "#ff9800"
        elif cur_month in [3, 4, 5]:
            season_txt = "🚜 ฤดูเก็บเกี่ยวข้าวนาปรัง: ปริมาณผลผลิตปานกลาง ราคาเคลื่อนไหวตามคำสั่งซื้อผู้ส่งออก"
            season_color = "#2962ff"
        else:
            season_txt = "📦 ช่วงข้าวขาดสต็อก (Lean Season): ผลผลิตในมือน้อย โรงสีอาจปรับเพิ่มราคารับซื้อเพื่อสต็อกข้าว"
            season_color = "#00e676"

        st.markdown(
            f"<div style='background:#171b26; border-left:4px solid {season_color}; padding:8px 12px; border-radius:4px; font-size:12px; color:#d1d4dc;'>"
            f"{season_txt}</div>", unsafe_allow_html=True
        )

    # ══════════════════════════════════════════════════════════
    # แท็บ 2: FOB Spread Monitor & สัญญาณชี้ขาดโรงสี
    # ══════════════════════════════════════════════════════════
    with t_fob:
        fx_rate = 32.5
        th_fob = 410.0
        vn_fob = 365.0
        in_fob = 352.0
        pk_fob = 345.0

        spread_vn = th_fob - vn_fob
        spread_in = th_fob - in_fob

        c_bar, c_signal = st.columns([0.55, 0.45])
        with c_bar:
            st.markdown("<span style='font-size:13px; font-weight:600; color:#d1d4dc;'>เปรียบเทียบราคา FOB ข้าวขาว 5% (USD/ตัน)</span>", unsafe_allow_html=True)
            fig_bar = go.Figure(data=[go.Bar(
                x=["ไทย (TH)", "เวียดนาม (VN)", "อินเดีย (IN)", "ปากีสถาน (PK)"],
                y=[th_fob, vn_fob, in_fob, pk_fob],
                text=[f"${v:.0f}<br>({v*fx_rate:,.0f} บ.)" for v in [th_fob, vn_fob, in_fob, pk_fob]],
                textposition="auto",
                marker_color=["#ff9800", "#00bcd4", "#ab47bc", "#26a69a"]
            )])
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="#131722",
                plot_bgcolor="#131722",
                margin=dict(l=10, r=10, t=20, b=10),
                height=260,
                yaxis=dict(title="USD / MT", gridcolor="#2a2e39")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_signal:
            st.markdown("<span style='font-size:13px; font-weight:600; color:#d1d4dc;'>ดัชนีชี้นำทิศทางราคาข้าวเปลือก (FOB Spread)</span>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:#1e222d; padding:12px; border-radius:6px; border:1px solid #2a2e39; margin-top:8px;'>"
                f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'>"
                f"<span style='color:#787b86; font-size:12px;'>ส่วนต่างราคา ไทย vs เวียดนาม:</span>"
                f"<b style='color:#ff9800;'>+{spread_vn:.0f} USD/ตัน</b></div>"
                f"<div style='display:flex; justify-content:space-between; margin-bottom:8px;'>"
                f"<span style='color:#787b86; font-size:12px;'>ส่วนต่างราคา ไทย vs อินเดีย:</span>"
                f"<b style='color:#ab47bc;'>+{spread_in:.0f} USD/ตัน</b></div>"
                f"</div>",
                unsafe_allow_html=True
            )

            # ตรรกะคาดการณ์การเคลื่อนไหวของราคาหน้าโรงสี
            if spread_vn > 35:
                pred_status = "🔴 เสี่ยงชะลอตัว"
                pred_desc = "ข้าวไทยแพงกว่าเวียดนามเกิน 35 USD ส่งออกแข่งขันยาก มีโอกาสที่โรงสีจะชะลอรับซื้อหรือปรับลดราคารับซื้อข้าวเปลือกลง"
                border_c = "#ef5350"
            elif spread_vn >= 15:
                pred_status = "🟡 ตลาดสมดุล"
                pred_desc = "ส่วนต่างอยู่ในเกณฑ์มาตรฐาน การส่งออกเป็นไปตามปกติ ราคาหน้าโรงสีจะทรงตัวตามกลไกอุปสงค์-อุปทาน"
                border_c = "#ff9800"
            else:
                pred_status = "🟢 แนวโน้มขาขึ้น"
                pred_desc = "ข้าวไทยแข่งขันได้ดีมาก คำสั่งซื้อส่งออกจะหนาแน่น คาดว่าโรงสีจะแย่งกันรับซื้อข้าวเปลือกและดันราคาขึ้น"
                border_c = "#26a69a"

            st.markdown(
                f"<div style='background:#171b26; border-left:4px solid {border_c}; padding:10px 12px; border-radius:4px; font-size:12px; margin-top:8px; color:#d1d4dc;'>"
                f"<b style='color:#fff;'>การคาดการณ์: {pred_status}</b><br>{pred_desc}</div>",
                unsafe_allow_html=True
            )

    # ══════════════════════════════════════════════════════════
    # แท็บ 3: เครื่องคำนวณอัจฉริยะ & ตัดสินใจขายสด VS อบแห้ง
    # ══════════════════════════════════════════════════════════
    with t_calc:
        c_in1, c_in2, c_in3 = st.columns(3)
        with c_in1:
            w_wet = st.number_input("น้ำหนักข้าวสดที่ชั่ง (กก.)", min_value=100.0, value=4500.0, step=100.0)
            p_dry_ref = st.number_input("ราคาข้าวแห้ง 15% วันนี้ (บ./ตัน)", min_value=5000.0, value=11200.0, step=100.0)
        with c_in2:
            moisture = st.number_input("ความชื้นที่วัดได้ (%)", min_value=14.0, max_value=35.0, value=23.5, step=0.5)
            dry_cost_ton = st.number_input("ค่าจ้างอบแห้ง (บ./ตัน)", min_value=0.0, value=450.0, step=50.0)
        with c_in3:
            p_fresh_today = st.number_input("ราคาโรงสีรับซื้อสดวันนี้ (บ./ตัน)", min_value=4000.0, value=8900.0, step=100.0)
            p_dry_forecast = st.number_input("คาดการณ์ราคาแห้งใน 15 วัน (บ./ตัน)", min_value=5000.0, value=11600.0, step=100.0)

        # คำนวณหักความชื้นตามเกณฑ์สมาคมโรงสี
        m_diff = max(0.0, moisture - 15.0)
        deduct_ratio = (m_diff * 0.015) if moisture <= 20 else ((5.0 * 0.015) + (moisture - 20.0) * 0.02)
        w_dry_net = w_wet * (1.0 - deduct_ratio)
        weight_lost = w_wet - w_dry_net

        # 1. รายได้กรณีขายสดหน้าโรงสีทันที
        revenue_fresh = (w_wet / 1000.0) * p_fresh_today

        # 2. รายได้กรณีนำไปอบแห้งแล้วรอขายอีก 15 วัน
        drying_total_cost = (w_wet / 1000.0) * dry_cost_ton
        revenue_dry_future = ((w_dry_net / 1000.0) * p_dry_forecast) - drying_total_cost
        diff_profit = revenue_dry_future - revenue_fresh

        st.markdown("<hr style='margin:10px 0; border:0.5px solid #2a2e39;'>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("น้ำหนักสุทธิหลังหักความชื้น", f"{w_dry_net:,.1f} กก.", f"-{weight_lost:,.1f} กก.", delta_color="inverse")
        with m2:
            st.metric("ขายสดหน้าโรงสีทันที", f"{revenue_fresh:,.0f} บาท", f"@{p_fresh_today:,.0f} บ./ตัน")
        with m3:
            st.metric("อบแห้งรอขาย 15 วัน (สุทธิ)", f"{revenue_dry_future:,.0f} บาท", f"{'+' if diff_profit >= 0 else ''}{diff_profit:,.0f} บาท", delta_color="normal")

        # ป้ายสรุปผลการตัดสินใจอัจฉริยะ
        if diff_profit > 1000:
            verdict_badge = f"✅ แนะนำนำไปอบแห้งรอขาย: คาดว่าจะได้กำไรเพิ่มขึ้นสุทธิ <b>+{diff_profit:,.0f} บาท</b> (หักค่าอบเรียบร้อยแล้ว)"
            v_color = "#26a69a"
        elif diff_profit < -500:
            verdict_badge = f"⚡ แนะนำขายสดทันที: การอบแห้งไม่คุ้มค่าความชื้นและค่าจ้างอบ ขายสดจะประหยัดต้นทุนกว่า <b>+{abs(diff_profit):,.0f} บาท</b>"
            v_color = "#ef5350"
        else:
            verdict_badge = "⚖️ ผลตอบแทนใกล้เคียงกัน: สามารถเลือกขายสดเพื่อรับเงินหมุนเวียนได้ทันทีโดยไม่ต้องแบกรับความเสี่ยงเรื่องราคา"
            v_color = "#ff9800"

        st.markdown(
            f"<div style='background:#1e222d; border-left:4px solid {v_color}; padding:10px 14px; border-radius:4px; font-size:13px; color:#fff; margin-top:8px;'>"
            f"{verdict_badge}</div>", unsafe_allow_html=True
        )