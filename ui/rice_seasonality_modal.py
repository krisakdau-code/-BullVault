# ui/rice_seasonality_modal.py — Rice Seasonality Dashboard (TradingView Style)
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════
# 1. ฐานข้อมูลกลุ่มข้าวตามรูปที่ 2
# ══════════════════════════════════════════════════════════
RICE_CATEGORIES = {
    "🌾 ข้าวไทย (หน้าโรงสี)": {
        "unit": "บาท/ตัน",
        "varieties": {
            "ข้าวเปลือกหอมมะลิ 105": {"base": 14800, "vol": 180},
            "ข้าวเปลือกปทุมธานี 1": {"base": 10900, "vol": 140},
            "ข้าวเปลือกเจ้า 5%": {"base": 9600, "vol": 120},
            "ข้าวเปลือกเหนียว กข6": {"base": 12500, "vol": 160},
        }
    },
    "TH ข้าวไทยส่งออก (FOB)": {
        "unit": "USD/ตัน",
        "varieties": {
            "ข้าวขาว 5% (Thai 5%)": {"base": 410, "vol": 6},
            "ข้าวหอมมะลิ 100% เกรด B": {"base": 840, "vol": 10},
            "ข้าวนึ่ง 5% (Parboiled)": {"base": 415, "vol": 6},
        }
    },
    "VN ข้าวเวียดนาม (FOB)": {
        "unit": "USD/ตัน",
        "varieties": {
            "ข้าวขาว 5% (VN 5%)": {"base": 365, "vol": 5},
            "ข้าวหอมมะลิ (Jasmine VN)": {"base": 520, "vol": 8},
        }
    },
    "IN ข้าวอินเดีย (FOB)": {
        "unit": "USD/ตัน",
        "varieties": {
            "ข้าวขาว 5% (IN 5%)": {"base": 352, "vol": 5},
            "ข้าวนึ่ง 5% (IN Parboiled)": {"base": 355, "vol": 5},
            "ข้าวบาสมาตี (Basmati)": {"base": 980, "vol": 14},
        }
    },
    "PK ข้าวปากีสถาน / กัมพูชา / เมียนมา (FOB)": {
        "unit": "USD/ตัน",
        "varieties": {
            "ปากีสถาน 5% (PK 5%)": {"base": 345, "vol": 5},
            "กัมพูชา มะลิ (Phka Rumduol)": {"base": 790, "vol": 9},
            "เมียนมา 5% (MM 5%)": {"base": 340, "vol": 5},
        }
    }
}

# ══════════════════════════════════════════════════════════
# 2. ฟังก์ชันจำลองประวัติราคาย้อนหลังตามรอบฤดูกาลจริง
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def get_rice_seasonality_data(cat_name, variety_name):
    cfg = RICE_CATEGORIES[cat_name]["varieties"][variety_name]
    base = cfg["base"]
    vol = cfg["vol"]

    years = [2023, 2024, 2025, 2026]
    cur_date = datetime.date(2026, 9, 19)
    records = []

    # โมเดลฤดูกาล: ราคาตกช่วงเก็บเกี่ยว (พ.ย.-ม.ค.) และพุ่งขึ้นช่วงของขาด (มิ.ย.-ก.ย.)
    monthly_season_factor = [
        -0.05, -0.04, -0.02, 0.01, 0.03, 0.06, 0.08, 0.07, 0.04, 0.01, -0.04, -0.06
    ]

    for yr_idx, yr in enumerate(years):
        np.random.seed(yr + int(base))
        start_date = datetime.date(yr, 1, 1)
        end_date = cur_date if yr == 2026 else datetime.date(yr, 12, 31)

        yr_drift = (yr_idx - 1.5) * (base * 0.04)  # แนวโน้มเงินเฟ้อ/ปัจจัยรายปี
        cur_p = base + yr_drift
        day_count = (end_date - start_date).days + 1

        for d_i in range(day_count):
            d = start_date + datetime.timedelta(days=d_i)
            m_idx = d.month - 1
            s_target = (base + yr_drift) * (1.0 + monthly_season_factor[m_idx])
            cur_p += (s_target - cur_p) * 0.05 + np.random.normal(0, vol * 0.5)

            records.append({
                "date": d,
                "year": yr,
                "month": d.month,
                "day": d.day,
                "day_of_year": d.timetuple().tm_yday,
                "price": round(float(cur_p), 2)
            })

    return pd.DataFrame(records)

# ══════════════════════════════════════════════════════════
# 3. หน้าต่างแดชบอร์ดฤดูกาล (Seasonality Modal)
# ══════════════════════════════════════════════════════════
@st.dialog("🌾 ศูนย์ข้อมูลตลาดข้าว & วิเคราะห์รอบฤดูกาล (Seasonality)", width="large")
def show_rice_market_modal():
    # แถบควบคุมบนสุด
    col_grp, col_var = st.columns([0.48, 0.52])
    with col_grp:
        sel_cat = st.selectbox("เลือกกลุ่มตลาดข้าว (รูปที่ 2)", list(RICE_CATEGORIES.keys()), key="rs_cat")
    with col_var:
        sel_var = st.selectbox("เลือกสายพันธุ์ข้าว", list(RICE_CATEGORIES[sel_cat]["varieties"].keys()), key="rs_var")

    unit_name = RICE_CATEGORIES[sel_cat]["unit"]
    df = get_rice_seasonality_data(sel_cat, sel_var)

    # แถบสลับมุมมอง (Timeframe & Mode)
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([0.34, 0.33, 0.33])
    with c_ctrl1:
        timeframe = st.segmented_control("ไทม์เฟรม", ["วัน", "เดือน", "ปี"], default="วัน", key="rs_tf")
    with c_ctrl2:
        calc_mode = st.segmented_control("แสดงผลลัพธ์", ["เปอร์เซ็นต์ (%)", "ราคาจริง"], default="เปอร์เซ็นต์ (%)", key="rs_mode")
    with c_ctrl3:
        show_avg = st.checkbox("📈 แสดงเส้นค่าเฉลี่ยสถิติ", value=True, key="rs_avg")

    # ══════════════════════════════════════════════════════════
    # 4. วาดกราฟเปรียบเทียบสไตล์ TradingView Seasonality (รูปที่ 1)
    # ══════════════════════════════════════════════════════════
    year_colors = {
        2023: "#00bcd4",   # สีฟ้า Cyan
        2024: "#ff9800",   # สีส้ม Orange
        2025: "#4caf50",   # สีเขียว Green
        2026: "#2962ff"    # สีกรม/น้ำเงินสด (ปีปัจจุบัน หนาพิเศษ)
    }

    fig = go.Figure()
    month_names_th = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

    if timeframe == "วัน":
        # คำนวณแกน 365 วัน (วันที่ 1 ม.ค. เทียบ 31 ธ.ค.)
        ref_year = 2024  # ปีอธิกสุรทินสำหรับแกนวันที่
        all_doy = pd.date_range("2024-01-01", "2024-12-31")
        avg_accumulator = []

        for yr in [2023, 2024, 2025, 2026]:
            df_y = df[df["year"] == yr].sort_values("day_of_year").copy()
            if df_y.empty:
                continue

            base_val = df_y["price"].iloc[0]
            if calc_mode == "เปอร์เซ็นต์ (%)":
                df_y["y_val"] = ((df_y["price"] - base_val) / base_val) * 100.0
            else:
                df_y["y_val"] = df_y["price"]

            # จัดแกน X ให้อยู่บนปีเดียวกันเพื่อซ้อนทับกัน
            df_y["plot_date"] = pd.to_datetime([f"2024-{m:02d}-{min(d, 28 if m == 2 else 30):02d}" for m, d in zip(df_y["month"], df_y["day"])])
            avg_accumulator.append(df_y[["plot_date", "y_val"]].set_index("plot_date"))

            last_val = df_y["y_val"].iloc[-1]
            last_date = df_y["plot_date"].iloc[-1]
            txt_label = f"{yr} ({last_val:+.2f}%)" if calc_mode == "เปอร์เซ็นต์ (%)" else f"{yr} ({last_val:,.0f})"

            fig.add_trace(go.Scatter(
                x=df_y["plot_date"],
                y=df_y["y_val"],
                mode="lines",
                name=f"{yr}",
                line=dict(color=year_colors[yr], width=3 if yr == 2026 else 1.8),
                hovertemplate=f"<b>{yr}:</b> %{{y:.2f}}{'%' if calc_mode == 'เปอร์เซ็นต์ (%)' else ' ' + unit_name}<extra></extra>"
            ))

            # ป้ายตัวเลขกำกับท้ายเส้น (Year Badge)
            fig.add_annotation(
                x=last_date, y=last_val,
                text=f"<b>{txt_label}</b>",
                showarrow=False,
                xanchor="left",
                font=dict(size=10, color=year_colors[yr]),
                bgcolor="rgba(19, 23, 34, 0.85)",
                bordercolor=year_colors[yr],
                borderwidth=1,
                borderpad=2
            )

        if show_avg and avg_accumulator:
            df_avg = pd.concat(avg_accumulator, axis=1).mean(axis=1)
            fig.add_trace(go.Scatter(
                x=df_avg.index, y=df_avg.values,
                mode="lines", name="ค่าเฉลี่ยสถิติ",
                line=dict(color="rgba(255, 255, 255, 0.4)", width=1.5, dash="dash"),
                hovertemplate="<b>เฉลี่ย:</b> %{y:.2f}<extra></extra>"
            ))

        fig.update_xaxes(
            tickformat="%b",
            tickvals=[f"2024-{m:02d}-01" for m in range(1, 13)],
            ticktext=month_names_th,
            gridcolor="#2a2e39"
        )

    elif timeframe == "เดือน":
        # รวมค่าเฉลี่ยรายเดือน
        for yr in [2023, 2024, 2025, 2026]:
            df_y = df[df["year"] == yr].groupby("month")["price"].mean().reset_index()
            if df_y.empty:
                continue

            base_val = df_y["price"].iloc[0]
            if calc_mode == "เปอร์เซ็นต์ (%)":
                df_y["y_val"] = ((df_y["price"] - base_val) / base_val) * 100.0
            else:
                df_y["y_val"] = df_y["price"]

            fig.add_trace(go.Scatter(
                x=[month_names_th[m - 1] for m in df_y["month"]],
                y=df_y["y_val"],
                mode="lines+markers",
                name=f"{yr}",
                line=dict(color=year_colors[yr], width=3 if yr == 2026 else 1.8),
                marker=dict(size=6),
                hovertemplate=f"<b>{yr}:</b> %{{y:.2f}}<extra></extra>"
            ))

    else:  # โหมด "ปี" (ต่อเนื่อง Multi-Year)
        df_cont = df.sort_values("date").copy()
        if calc_mode == "เปอร์เซ็นต์ (%)":
            base_val = df_cont["price"].iloc[0]
            df_cont["y_val"] = ((df_cont["price"] - base_val) / base_val) * 100.0
        else:
            df_cont["y_val"] = df_cont["price"]

        fig.add_trace(go.Scatter(
            x=df_cont["date"],
            y=df_cont["y_val"],
            mode="lines",
            name="แนวโน้มราคาต่อเนื่อง",
            line=dict(color="#00bcd4", width=2),
            hovertemplate="<b>ราคา:</b> %{y:.2f}<extra></extra>"
        ))

    # ปรับสไตล์ Dark Theme สวยงามตามรูปที่ 1
    y_title = "เปอร์เซ็นต์การเปลี่ยนแปลง (%)" if calc_mode == "เปอร์เซ็นต์ (%)" else f"ราคา ({unit_name})"
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=20, r=90, t=20, b=30),
        height=440,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(title=y_title, side="right", gridcolor="#1e222d", zeroline=True, zerolinecolor="#363a45")
    )

    st.plotly_chart(fig, use_container_width=True)

    # คำอธิบายบริบทตลาดข้าว
    st.markdown(
        f"<div style='background:#161922; border-left:4px solid #00bcd4; padding:8px 14px; border-radius:4px; font-size:12px; color:#d1d4dc;'>"
        f"💡 <b>การอ่านวงจรฤดูกาล:</b> เส้นกราฟช่วยคาดการณ์ว่าในช่วงเดือนปัจจุบัน (ก.ย.) ราคามักปรับตัวขึ้นจากสต็อกเก่าที่ลดลง ก่อนจะเริ่มย่อตัวลงเมื่อผลผลิตข้าวนาปีชุดใหม่ทยอยออกสู่ตลาดตั้งแต่เดือน พ.ย. เป็นต้นไป</div>",
        unsafe_allow_html=True
    )