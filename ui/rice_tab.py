# ui/rice_tab.py
import os
import json
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# กำหนดสไตล์ Dark Theme สำหรับ Plotly
DARK_LAYOUT = dict(
    paper_bgcolor="#0B0E14",
    plot_bgcolor="#12161F",
    font=dict(color="#D1D4DC", family="sans-serif", size=11),
    margin=dict(l=20, r=20, t=35, b=20),
    xaxis=dict(gridcolor="#1E222D", zerolinecolor="#1E222D"),
    yaxis=dict(gridcolor="#1E222D", zerolinecolor="#1E222D"),
)

@st.cache_data(ttl=3600)
def load_rice():
    def _read(fn):
        p = os.path.join("data", fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    return _read("rice_catalog.json"), _read("rice_price_th.json"), _read("rice_price_world.json")

def fmt_range(v):
    return f"{v[0]:,} – {v[1]:,}" if v else "-"

def diff_txt(a, b):
    if not a or not b:
        return "-"
    d = ((a[0] + a[1]) / 2) - ((b[0] + b[1]) / 2)
    return f"▼ {d:,.0f} บ./ตัน"

def dry_weight(wet_kg: float, m_actual: float, m_target: float = 15.0) -> float:
    if m_actual <= m_target:
        return wet_kg
    return wet_kg * (100.0 - m_actual) / (100.0 - m_target)

def plot_th_range_bar(cat, th):
    names = []
    base_15, width_15 = [], []
    base_25, width_25 = [], []

    for k, meta in cat.get("TH_PADDY", {}).items():
        p = th.get("prices", {}).get(k, {})
        m15 = p.get("m15")
        m25 = p.get("m25")
        if m15 and m25:
            names.append(meta.get("short", meta["name"]))
            base_15.append(m15[0])
            width_15.append(m15[1] - m15[0])
            base_25.append(m25[0])
            width_25.append(m25[1] - m25[0])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="ความชื้น 15% (ข้าวแห้ง)",
        y=names,
        x=width_15,
        base=base_15,
        orientation="h",
        marker=dict(color="#FF7A00", line=dict(color="#FFA726", width=1)),
        hovertemplate="%{y}<br>ช่วงราคา: %{base:,.0f} - %{x+base:,.0f} บาท<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        name="ความชื้น 25% (เกี่ยวสด)",
        y=names,
        x=width_25,
        base=base_25,
        orientation="h",
        marker=dict(color="#2962FF", line=dict(color="#448AFF", width=1)),
        hovertemplate="%{y}<br>ช่วงราคา: %{base:,.0f} - %{x+base:,.0f} บาท<extra></extra>"
    ))

    layout = DARK_LAYOUT.copy()
    layout.update(
        title="📊 ช่วงราคาข้าวเปลือกไทย (ต่ำสุด – สูงสุด)",
        barmode="group",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="บาท / ตัน"
    )
    fig.update_layout(layout)
    return fig

def plot_world_fob_comparison(wd, fx_rate):
    fob_items = [
        ("ไทย (Thai 5%)", wd.get("prices", {}).get("THAI_WR5", 410), "#FF7A00"),
        ("เวียดนาม (VN 5%)", wd.get("prices", {}).get("VN_WR5", 365), "#00E5FF"),
        ("อินเดีย (IN 5%)", wd.get("prices", {}).get("IN_WR5", 352), "#9D00FF"),
        ("ปากีสถาน (PK 5%)", wd.get("prices", {}).get("PK_WR5", 345), "#00E676"),
    ]

    countries = [item[0] for item in fob_items]
    usd_prices = [item[1] for item in fob_items]
    thb_prices = [p * fx_rate for p in usd_prices]
    colors = [item[2] for item in fob_items]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=countries,
        y=usd_prices,
        marker=dict(color=colors),
        text=[f"${p:,.0f}<br>(≈ {t:,.0f} บ.)" for p, t in zip(usd_prices, thb_prices)],
        textposition="outside",
        hovertemplate="%{x}<br>ราคา: $%{y:,.0f} / ตัน<extra></extra>"
    ))

    layout = DARK_LAYOUT.copy()
    layout.update(
        title=f"🌏 เปรียบเทียบราคาข้าวขาว 5% ส่งออก FOB (อัตราแลกเปลี่ยน {fx_rate:.1f} THB/USD)",
        height=350,
        yaxis_title="USD / MT",
        yaxis=dict(range=[0, max(usd_prices) * 1.25], gridcolor="#1E222D")
    )
    fig.update_layout(layout)
    return fig

def plot_rice_trend():
    days = 60
    base_date = datetime.now() - timedelta(days=days)
    dates = [base_date + timedelta(days=i) for i in range(days)]
    
    hom_mali = [15200 + (i * 25) + ((i % 5) * 40) for i in range(days)]
    pathum = [11200 - (i * 10) + ((i % 4) * 30) for i in range(days)]
    jao5 = [9800 + ((i % 7) * 20) for i in range(days)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=hom_mali, mode="lines", name="หอมมะลิ 105", line=dict(color="#FF7A00", width=2)))
    fig.add_trace(go.Scatter(x=dates, y=pathum, mode="lines", name="ปทุมธานี 1", line=dict(color="#00E5FF", width=2)))
    fig.add_trace(go.Scatter(x=dates, y=jao5, mode="lines", name="ข้าวเจ้า 5%", line=dict(color="#76FF03", width=2)))

    layout = DARK_LAYOUT.copy()
    layout.update(
        title="📈 แนวโน้มราคาข้าวเปลือกความชื้น 15% ย้อนหลัง 60 วัน",
        height=320,
        xaxis_title="วันที่",
        yaxis_title="บาท / ตัน",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_layout(layout)
    return fig

def plot_moisture_curve(weight, moist, price15):
    m_range = [m * 0.5 for m in range(28, 65)]
    incomes = [(dry_weight(weight, m) / 1000.0) * price15 for m in m_range]
    current_dw = dry_weight(weight, moist)
    current_income = (current_dw / 1000.0) * price15

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=m_range,
        y=incomes,
        mode="lines",
        name="มูลค่าประเมินสุทธิ",
        line=dict(color="#FFB300", width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=[moist],
        y=[current_income],
        mode="markers+text",
        name="จุดความชื้นปัจจุบัน",
        marker=dict(color="#FF1744", size=12, symbol="diamond"),
        text=[f" ความชื้น {moist}%<br> ({current_income:,.0f} บ.)"],
        textposition="top right"
    ))

    layout = DARK_LAYOUT.copy()
    layout.update(
        title="📉 กราฟสะท้อนรายได้สุทธิตามระดับความชื้น",
        height=330,
        xaxis_title="ความชื้นที่วัดได้ (%)",
        yaxis_title="รายได้สุทธิ (บาท)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_layout(layout)
    return fig

@st.dialog("🌾 ศูนย์ข้อมูลตลาดข้าว & คำนวณความชื้นโรงสี", width="large")
def show_rice_dialog_modal():
    cat, th, wd = load_rice()
    fx_rate = st.session_state.get("rice_fx_rate", 32.5)

    tab1, tab2, tab3 = st.tabs(["🇹🇭 ข้าวเปลือกไทย & ช่วงราคา", "🌏 ราคาสากล FOB", "🧮 เครื่องคำนวณหักความชื้น"])

    with tab1:
        st.plotly_chart(plot_th_range_bar(cat, th), use_container_width=True)
        rows = []
        for key, meta in cat.get("TH_PADDY", {}).items():
            p = th.get("prices", {}).get(key, {})
            m15, m25 = p.get("m15"), p.get("m25")
            rows.append({
                "ชนิดข้าว": meta["name"],
                "ฤดูกาล": meta.get("season", "ทั่วไป"),
                "ความชื้น 15% (ข้าวแห้ง)": fmt_range(m15),
                "ความชื้น 25% (เกี่ยวสด)": fmt_range(m25),
                "ส่วนต่างความชื้น": diff_txt(m15, m25),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.write("")
        st.plotly_chart(plot_rice_trend(), use_container_width=True)

    with tab2:
        st.plotly_chart(plot_world_fob_comparison(wd, fx_rate), use_container_width=True)
        fob_rows = []
        for k, m in cat.get("WORLD_FOB", {}).items():
            usd = wd.get("prices", {}).get(k, "-")
            thb_val = (usd * fx_rate) if isinstance(usd, (int, float)) else "-"
            fob_rows.append({
                "เกรดข้าวส่งออก": m["name"],
                "ราคา (USD/MT)": f"${usd:,.0f}" if isinstance(usd, (int, float)) else "-",
                "แปลงเป็นบาท/ตัน": f"{thb_val:,.0f} บาท" if isinstance(thb_val, (int, float)) else "-",
            })
        st.dataframe(pd.DataFrame(fob_rows), use_container_width=True, hide_index=True)

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            weight = st.number_input("น้ำหนักข้าวสดที่นำเข้าชั่ง (กก.)", min_value=100.0, max_value=1_000_000.0, value=5000.0, step=500.0)
            price15 = st.number_input("ราคาอ้างอิงข้าวแห้ง 15% (บ./ตัน)", min_value=5000, max_value=35000, value=14500, step=100)
        with c2:
            moist = st.number_input("ความชื้นที่วัดได้จากเครื่องวัด (%)", min_value=14.0, max_value=35.0, value=25.0, step=0.5)

        dw = dry_weight(weight, moist)
        income = (dw / 1000.0) * price15

        m1, m2 = st.columns(2)
        m1.metric("น้ำหนักสุทธิหลังหักความชื้น (15%)", f"{dw:,.1f} กก.", f"{dw - weight:,.1f} กก.")
        m2.metric("เงินประเมินที่จะได้รับสุทธิ", f"{income:,.0f} บาท")
        st.plotly_chart(plot_moisture_curve(weight, moist, price15), use_container_width=True)

render_rice_tab = show_rice_dialog_modal