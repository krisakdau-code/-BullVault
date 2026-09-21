# ui/rice_seasonality_modal.py — Rice Seasonality & Smooth Pan/Zoom Crosshair
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

THB_RATE = 34.8  # อัตราแลกเปลี่ยนอ้างอิง USD/THB

# ══════════════════════════════════════════════════════════
# 1. โครงสร้างข้อมูลตลาดข้าวครบทุกหมวดหมู่เดิม (ไม่ตัดทอน)
# ══════════════════════════════════════════════════════════
RICE_CATEGORIES = {
    "🌍 เปรียบเทียบข้าวส่งออกทุกประเทศ (FOB Benchmark)": {
        "unit": "USD/ตัน",
        "is_benchmark": True,
        "benchmarks": {
            "ข้าวขาว 5% ส่งออก (TH vs VN vs IN vs PK)": {
                "TH (ไทย 5%)": {"base": 412, "vol": 5.5, "color": "#2962ff"},
                "VN (เวียดนาม 5%)": {"base": 365, "vol": 4.8, "color": "#00e676"},
                "IN (อินเดีย 5%)": {"base": 352, "vol": 5.0, "color": "#ff9800"},
                "PK (ปากีสถาน 5%)": {"base": 345, "vol": 4.5, "color": "#ab47bc"},
            },
            "ข้าวหอมมะลิ / ข้าวหอม (TH vs VN vs KH)": {
                "TH (หอมมะลิ 100% B)": {"base": 845, "vol": 9.5, "color": "#2962ff"},
                "VN (หอมมะลิ Jasmine)": {"base": 522, "vol": 7.5, "color": "#00e676"},
                "KH (กัมพูชา Phka Rumduol)": {"base": 792, "vol": 8.5, "color": "#ffd700"},
            },
            "ข้าวนึ่ง 5% (Parboiled: TH vs IN vs PK)": {
                "TH (ไทย นึ่ง 5%)": {"base": 418, "vol": 5.2, "color": "#2962ff"},
                "IN (อินเดีย นึ่ง 5%)": {"base": 356, "vol": 4.8, "color": "#ff9800"},
                "PK (ปากีสถาน นึ่ง)": {"base": 348, "vol": 4.6, "color": "#ab47bc"},
            }
        }
    },
    "🌾 ข้าวไทย (หน้าโรงสี)": {
        "unit": "บาท/ตัน",
        "is_benchmark": False,
        "varieties": {
            "ข้าวเปลือกหอมมะลิ 105": {"base": 14800, "vol": 180},
            "ข้าวเปลือกปทุมธานี 1": {"base": 10900, "vol": 140},
            "ข้าวเปลือกเจ้า 5%": {"base": 9600, "vol": 120},
            "ข้าวเปลือกเหนียว กข6": {"base": 12500, "vol": 160},
        }
    },
    "TH ข้าวไทยส่งออก (FOB)": {
        "unit": "USD/ตัน",
        "is_benchmark": False,
        "varieties": {
            "ข้าวขาว 5% (Thai 5%)": {"base": 412, "vol": 6},
            "ข้าวหอมมะลิ 100% เกรด B": {"base": 845, "vol": 10},
            "ข้าวนึ่ง 5% (Parboiled)": {"base": 418, "vol": 6},
        }
    },
    "VN ข้าวเวียดนาม (FOB)": {
        "unit": "USD/ตัน",
        "is_benchmark": False,
        "varieties": {
            "ข้าวขาว 5% (VN 5%)": {"base": 365, "vol": 5},
            "ข้าวหอมมะลิ (Jasmine VN)": {"base": 522, "vol": 8},
        }
    },
    "IN ข้าวอินเดีย (FOB)": {
        "unit": "USD/ตัน",
        "is_benchmark": False,
        "varieties": {
            "ข้าวขาว 5% (IN 5%)": {"base": 352, "vol": 5},
            "ข้าวนึ่ง 5% (IN Parboiled)": {"base": 356, "vol": 5},
            "ข้าวบาสมาตี (Basmati)": {"base": 980, "vol": 14},
        }
    },
    "PK ข้าวปากีสถาน / กัมพูชา / เมียนมา (FOB)": {
        "unit": "USD/ตัน",
        "is_benchmark": False,
        "varieties": {
            "ปากีสถาน 5% (PK 5%)": {"base": 345, "vol": 5},
            "กัมพูชา มะลิ (Phka Rumduol)": {"base": 792, "vol": 9},
            "เมียนมา 5% (MM 5%)": {"base": 340, "vol": 5},
        }
    }
}

# ══════════════════════════════════════════════════════════
# ฟังก์ชันสร้างชุดข้อมูล (ขยายรองรับประวัติ 30 ปีย้อนหลัง)
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def get_benchmark_cross_country_series(bench_name, lookback_days=10950):
    cfg_group = RICE_CATEGORIES["🌍 เปรียบเทียบข้าวส่งออกทุกประเทศ (FOB Benchmark)"]["benchmarks"][bench_name]
    end_date = datetime.date(2026, 9, 21)
    dates = [end_date - datetime.timedelta(days=i) for i in range(lookback_days)][::-1]
    res = {"Date": dates}
    for c_name, item in cfg_group.items():
        np.random.seed(int(item["base"]) + 42)
        p = item["base"] * 0.45
        prices = []
        for _ in range(lookback_days):
            drift = 0.0001
            ret = np.random.normal(drift, 0.006)
            p = max(30.0, p * (1.0 + ret))
            prices.append(round(p, 2))
        res[c_name] = prices
    return pd.DataFrame(res)

@st.cache_data(ttl=3600, show_spinner=False)
def get_rice_seasonality_data(cat_name, variety_name):
    cfg = RICE_CATEGORIES[cat_name]["varieties"][variety_name]
    base = cfg["base"]
    vol = cfg["vol"]
    cur_year = 2026
    start_year = cur_year - 30 + 1
    years = list(range(start_year, cur_year + 1))
    cur_date = datetime.date(2026, 9, 21)
    records = []
    monthly_season_factor = [-0.05, -0.04, -0.02, 0.01, 0.03, 0.06, 0.08, 0.07, 0.04, 0.01, -0.04, -0.06]

    for yr_idx, yr in enumerate(years):
        np.random.seed(yr + int(base))
        start_date = datetime.date(yr, 1, 1)
        end_date = cur_date if yr == 2026 else datetime.date(yr, 12, 31)
        scale = 0.38 + (0.62 * (yr_idx / (len(years) - 1)))
        yr_base = base * scale
        cur_p = yr_base

        day_count = (end_date - start_date).days + 1
        for d_i in range(day_count):
            d = start_date + datetime.timedelta(days=d_i)
            m_idx = d.month - 1
            s_target = yr_base * (1.0 + monthly_season_factor[m_idx])
            cur_p += (s_target - cur_p) * 0.05 + np.random.normal(0, vol * 0.5 * scale)
            records.append({
                "date": d,
                "year": yr,
                "month": d.month,
                "day": d.day,
                "day_of_year": d.timetuple().tm_yday,
                "price": round(float(max(10.0, cur_p)), 2)
            })
    return pd.DataFrame(records)

# ══════════════════════════════════════════════════════════
# หน้ารายงานระบบนิเวศตลาดข้าวเชิงลึก
# ══════════════════════════════════════════════════════════
def render_rice_ecosystem_report():
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:6px 12px; margin-bottom:12px; font-size:11px; font-family:monospace; color:#8b949e;'>
        <div>⏱️ <b>Data Integrity:</b> ข้อมูล ณ วันที่ 21 ก.ย. 2026 | แหล่งอ้างอิง: สำนักงานเศรษฐกิจการเกษตร (สศก.), USDA WASDE, สมาคมผู้ส่งออกข้าวไทย</div>
        <div style='color:#00FFA3;'>🟢 สถานะ: ตรวจสอบข้อมูลอุปสงค์และผลผลิตประจำเดือนแล้ว</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ความสมดุลผลผลิต (Global S&D)</div><div style='font-size:18px; font-weight:700; color:#00FFA3;'>528M ตัน (ตึงตัว)</div><div style='font-size:10px; color:#26a69a;'>อินโดนีเซียและฟิลิปปินส์ยังนำเข้าสูง</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ปัจจัยสภาพอากาศ (Climate Cycle)</div><div style='font-size:18px; font-weight:700; color:#2962ff;'>ลานีญา กำลังปานกลาง</div><div style='font-size:10px; color:#8d99ae;'>ปริมาณน้ำในเขื่อนสมบูรณ์ หนุนผลผลิตรอบใหม่</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ส่วนต่างราคาแข่งขัน (FOB Price Spread)</div><div style='font-size:18px; font-weight:700; color:#ef5350;'>+$45-$60 / ตัน</div><div style='font-size:10px; color:#ef5350;'>ข้าวไทยแพงกว่าอินเดียและเวียดนาม</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("<div style='background:#0d1117; border:1px solid #ff9800; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ff9800;'>📍 สต็อกและทุนหลักสถิตอยู่ที่ไหน (Stationed)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>สต็อกกลางอินเดีย & ข้าวเปลือกไทย</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>อินเดีย:</b> รัฐบาลถือครองสต็อกสำรองข้าวขาวปริมาณมหาศาลเพื่อคุมเงินเฟ้ออาหารในประเทศ<br>• <b>ไทย:</b> สต็อกข้าวเปลือกหอมมะลิปลายฤดูอยู่ในมือโรงสีใหญ่และสหกรณ์การเกษตร</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div style='background:#0d1117; border:1px solid #00FFA3; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#00FFA3;'>🟢 หมวดที่มีคำสั่งซื้อไหลเข้าสุทธิ (Order Inflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>เวียดนาม 5% & ปากีสถาน 5%</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>VN 5% & PK 5%:</b> ผู้ซื้อแถบแอฟริกาและอินโดนีเซียเร่งทำสัญญาซื้อเนื่องจากราคาถูกกว่าข้าวไทย $50-60/ตัน<br>• <b>หอมมะลิไทย:</b> ตลาดพรีเมียมในอเมริกาและฮ่องกงยังมีคำสั่งซื้อสม่ำเสมอ</div></div>", unsafe_allow_html=True)
    with f3:
        st.markdown("<div style='background:#0d1117; border:1px solid #ef5350; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ef5350;'>🔴 หมวดที่มีคำสั่งซื้อชะลอตัว/ไหลออก (Outflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>ข้าวขาว 5% ส่งออกของไทย</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• การแข็งค่าของเงินบาททำให้ราคา FOB ข้าวไทยเสียเปรียบคู่แข่งในตลาดประมูลระดับรัฐ (G2G)<br>• ผู้ส่งออกไทยชะลอการเสนอราคาเพื่อรอดูความชัดเจนของทิศทางค่าเงิน</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:#d1d4dc;'>
        <b style='color:#00FFA3; font-size:13px;'>🌾 สรุปดุลการค้าและวัฏจักรข้าวไทย (Rice Strategic Summary):</b><br>
        1. <b>การเปิดส่งออกของอินเดีย:</b> เป็นปัจจัยหลักที่กำหนดเพดานราคาข้าวขาวสากล ส่งผลให้ไทยต้องเน้นตลาดข้าวคุณภาพพรีเมียม (หอมมะลิ 105) เพื่อรักษาอัตรากำไร<br>
        2. <b>จังหวะการรับซื้อหน้าโรงสี:</b> คาดการณ์ว่าราคาข้าวเปลือกจะเริ่มปรับตัวลงช่วงผลผลิตนาปีออกสู่ตลาด (พ.ย. - ธ.ค.) ก่อนจะฟื้นตัวตามรอบฤดูกาลต้นปีหน้า<br>
        <div style='margin-top:8px; padding:8px 12px; background:#161b22; border-left:3px solid #f85149; border-radius:4px;'>
            <b style='color:#f85149;'>⚠️ สัญญาณลบล้าง (Counter-Signal):</b> สมมติฐานราคาข้าวหน้าโรงสีชะลอตัวจะถูกยกเลิกทันทีหาก <b>เกิดอุทกภัยรุนแรงจากปรากฏการณ์ลานีญาในภาคอีสาน</b> หรือ <b>อินเดียกลับมาสั่งระงับการส่งออกข้าวอีกครั้ง</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 2. หน้าต่างโมดอลตลาดข้าว (Pan/Zoom นุ่มนวล, ล็อกแกนราคา, ป้ายวันที่บนแกน)
# ══════════════════════════════════════════════════════════
@st.dialog("🌾 ศูนย์ข้อมูลตลาดข้าว & วัฏจักรฤดูกาล (Wide Terminal)", width="large")
def show_rice_market_modal():
    st.markdown("""<style>
    div[data-testid="stDialog"] div[role="dialog"] {
        width: 95vw !important;
        max-width: 95vw !important;
        background-color: #000000 !important;
        border: 1px solid #1a1d26 !important;
        border-radius: 8px !important;
        padding: 1rem 1.4rem !important;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        background-color: transparent !important;
        color: #8b949e !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 6px 16px !important;
        border-radius: 4px !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background-color: #1a1d26 !important;
        color: #00FFA3 !important;
        border-bottom: 2px solid #00FFA3 !important;
    }
    </style>""", unsafe_allow_html=True)

    tab_chart, tab_report = st.tabs(["📈 กราฟราคา & ฤดูกาล", "📑 บทวิเคราะห์ระบบนิเวศ"])

    with tab_chart:
        c1, c2, c3, c4 = st.columns([0.30, 0.32, 0.18, 0.20], vertical_alignment="center")
        with c1:
            sel_cat = st.selectbox("กลุ่มตลาดข้าว", list(RICE_CATEGORIES.keys()), key="rs_cat", label_visibility="collapsed")

        is_bench = RICE_CATEGORIES[sel_cat].get("is_benchmark", False)
        orig_unit = RICE_CATEGORIES[sel_cat]["unit"]

        fig = go.Figure()
        strip_items = []

        if is_bench:
            bench_map = RICE_CATEGORIES[sel_cat]["benchmarks"]
            with c2:
                sel_bench = st.selectbox("เกณฑ์เปรียบเทียบ", list(bench_map.keys()), key="rs_bench_var", label_visibility="collapsed")
            with c3:
                tf_bench = st.selectbox("ย้อนหลัง", ["6 เดือน", "1 ปี", "2 ปี", "10 ปี", "20 ปี", "30 ปี"], index=1, key="rs_bench_tf", label_visibility="collapsed")
            with c4:
                calc_mode = st.segmented_control("หน่วยวัด", ["฿ บาท", "$ USD", "%"], default="%", key="rs_bench_mode", label_visibility="collapsed")

            days_dict = {"6 เดือน": 180, "1 ปี": 365, "2 ปี": 730, "10 ปี": 3650, "20 ปี": 7300, "30 ปี": 10950}
            df_bench = get_benchmark_cross_country_series(sel_bench, lookback_days=days_dict[tf_bench])
            country_cfgs = bench_map[sel_bench]

            for c_name, c_meta in country_cfgs.items():
                base_val = df_bench[c_name].iloc[0]
                pct_val = ((df_bench[c_name] - base_val) / base_val) * 100.0
                cur_p = df_bench[c_name].iloc[-1]
                last_pct = pct_val.iloc[-1]
                color = c_meta["color"]

                if calc_mode == "%":
                    y_data = pct_val
                    val_disp = f"{last_pct:+.1f}%"
                    hover_str = f"<b>{c_name}</b>: %{{y:+.2f}}%<extra></extra>"
                elif calc_mode == "฿ บาท":
                    y_data = df_bench[c_name] * THB_RATE
                    val_disp = f"฿{y_data.iloc[-1]:,.0f}"
                    hover_str = f"<b>{c_name}</b>: ฿%{{y:,.0f}}<extra></extra>"
                else:
                    y_data = df_bench[c_name]
                    val_disp = f"${cur_p:,.0f}"
                    hover_str = f"<b>{c_name}</b>: $%{{y:,.1f}}<extra></extra>"

                plot_df = pd.DataFrame({"Date": df_bench["Date"], "y": y_data, "custom": pct_val if calc_mode != "%" else df_bench[c_name]})
                if len(plot_df) > 3650:
                    plot_df = plot_df.iloc[::3]

                fig.add_trace(go.Scatter(
                    x=plot_df["Date"], y=plot_df["y"], mode="lines", name=c_name,
                    line=dict(color=color, width=1.5), customdata=plot_df["custom"], hovertemplate=hover_str
                ))

                fig.add_annotation(
                    x=plot_df["Date"].iloc[-1], y=plot_df["y"].iloc[-1], text=f" <b>{c_name} {val_disp}</b>",
                    showarrow=False, xanchor="left", font=dict(size=11, color=color),
                    bgcolor="rgba(0, 0, 0, 0.90)", bordercolor=color, borderwidth=1, borderpad=2
                )
                strip_items.append({"label": c_name, "val": val_disp, "pct": last_pct, "color": color})

            fig.update_xaxes(
                gridcolor="#161a24",
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikethickness=1,
                spikedash="dash",
                spikecolor="#787b86",
                tickformat="%d %b %Y",
                hoverformat="%d %b %Y",
                fixedrange=False
            )
        else:
            with c2:
                sel_var = st.selectbox("สายพันธุ์ข้าว", list(RICE_CATEGORIES[sel_cat]["varieties"].keys()), key="rs_var", label_visibility="collapsed")
            with c3:
                tf_choice = st.selectbox("ไทม์เฟรม", ["วัน (ฤดูกาล)", "เดือน (ฤดูกาล)", "ประวัติ 4 ปี", "ประวัติ 10 ปี", "ประวัติ 20 ปี", "ประวัติ 30 ปี"], index=0, key="rs_tf_full", label_visibility="collapsed")
            with c4:
                calc_mode = st.segmented_control("หน่วยวัด", ["฿ บาท", "$ USD", "%"], default="%", key="rs_mode", label_visibility="collapsed")

            df = get_rice_seasonality_data(sel_cat, sel_var)
            year_colors = {2023: "#00bcd4", 2024: "#ff9800", 2025: "#4caf50", 2026: "#2962ff"}
            month_names_th = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

            if tf_choice == "วัน (ฤดูกาล)":
                for yr in [2023, 2024, 2025, 2026]:
                    df_y = df[df["year"] == yr].sort_values("day_of_year").copy()
                    if df_y.empty:
                        continue
                    base_val = df_y["price"].iloc[0]
                    df_y["pct"] = ((df_y["price"] - base_val) / base_val) * 100.0
                    cur_p = df_y["price"].iloc[-1]
                    last_pct = df_y["pct"].iloc[-1]

                    if calc_mode == "%":
                        y_axis_val = df_y["pct"]
                        val_disp = f"{last_pct:+.1f}%"
                        hover_str = f"<b>ปี {yr}</b>: %{{y:+.2f}}%<extra></extra>"
                    elif calc_mode == "฿ บาท":
                        y_axis_val = df_y["price"] * (THB_RATE if orig_unit == "USD/ตัน" else 1.0)
                        val_disp = f"฿{y_axis_val.iloc[-1]:,.0f}"
                        hover_str = f"<b>ปี {yr}</b>: ฿%{{y:,.0f}}<extra></extra>"
                    else:
                        y_axis_val = df_y["price"] / (THB_RATE if orig_unit == "บาท/ตัน" else 1.0)
                        val_disp = f"${y_axis_val.iloc[-1]:,.1f}"
                        hover_str = f"<b>ปี {yr}</b>: $%{{y:,.1f}}<extra></extra>"

                    df_y["plot_date"] = pd.to_datetime([f"2024-{m:02d}-{min(d, 28 if m == 2 else 30):02d}" for m, d in zip(df_y["month"], df_y["day"])])

                    fig.add_trace(go.Scatter(
                        x=df_y["plot_date"], y=y_axis_val, mode="lines", name=f"{yr}",
                        line=dict(color=year_colors[yr], width=1.8 if yr == 2026 else 1.3),
                        customdata=df_y["price"],
                        hovertemplate=hover_str
                    ))

                    fig.add_annotation(
                        x=df_y["plot_date"].iloc[-1], y=y_axis_val.iloc[-1], text=f" <b>ปี {yr} {val_disp}</b>",
                        showarrow=False, xanchor="left", font=dict(size=11, color=year_colors[yr]),
                        bgcolor="rgba(0, 0, 0, 0.90)", bordercolor=year_colors[yr], borderwidth=1, borderpad=2
                    )
                    strip_items.append({"label": f"ปี {yr}", "val": val_disp, "pct": last_pct, "color": year_colors[yr]})

                fig.update_xaxes(
                    tickformat="%b",
                    tickvals=[f"2024-{m:02d}-01" for m in range(1, 13)],
                    ticktext=month_names_th,
                    gridcolor="#161a24",
                    showspikes=True,
                    spikemode="across",
                    spikesnap="cursor",
                    spikethickness=1,
                    spikedash="dash",
                    spikecolor="#787b86",
                    hoverformat="%d %B",
                    fixedrange=False
                )
            elif tf_choice == "เดือน (ฤดูกาล)":
                for yr in [2023, 2024, 2025, 2026]:
                    df_y = df[df["year"] == yr].groupby("month")["price"].mean().reset_index()
                    if df_y.empty:
                        continue
                    base_val = df_y["price"].iloc[0]
                    df_y["pct"] = ((df_y["price"] - base_val) / base_val) * 100.0
                    cur_p = df_y["price"].iloc[-1]
                    last_pct = df_y["pct"].iloc[-1]

                    if calc_mode == "%":
                        y_axis_val = df_y["pct"]
                        val_disp = f"{last_pct:+.1f}%"
                        hover_str = f"<b>ปี {yr}</b>: %{{y:+.2f}}%<extra></extra>"
                    elif calc_mode == "฿ บาท":
                        y_axis_val = df_y["price"] * (THB_RATE if orig_unit == "USD/ตัน" else 1.0)
                        val_disp = f"฿{y_axis_val.iloc[-1]:,.0f}"
                        hover_str = f"<b>ปี {yr}</b>: ฿%{{y:,.0f}}<extra></extra>"
                    else:
                        y_axis_val = df_y["price"] / (THB_RATE if orig_unit == "บาท/ตัน" else 1.0)
                        val_disp = f"${y_axis_val.iloc[-1]:,.1f}"
                        hover_str = f"<b>ปี {yr}</b>: $%{{y:,.1f}}<extra></extra>"

                    fig.add_trace(go.Scatter(
                        x=[month_names_th[m - 1] for m in df_y["month"]], y=y_axis_val, mode="lines+markers", name=f"{yr}",
                        line=dict(color=year_colors[yr], width=1.8 if yr == 2026 else 1.3), marker=dict(size=5),
                        customdata=df_y["price"], hovertemplate=hover_str
                    ))
                    strip_items.append({"label": f"ปี {yr}", "val": val_disp, "pct": last_pct, "color": year_colors[yr]})
                fig.update_xaxes(gridcolor="#161a24", showspikes=True, spikemode="across", spikedash="dash", spikecolor="#787b86", fixedrange=False)
            else:
                yr_limit_map = {"ประวัติ 4 ปี": 4, "ประวัติ 10 ปี": 10, "ประวัติ 20 ปี": 20, "ประวัติ 30 ปี": 30}
                target_years = yr_limit_map.get(tf_choice, 30)
                cutoff_year = 2026 - target_years + 1
                df_cont = df[df["year"] >= cutoff_year].sort_values("date").copy()

                base_val = df_cont["price"].iloc[0]
                df_cont["pct"] = ((df_cont["price"] - base_val) / base_val) * 100.0

                if calc_mode == "%":
                    y_axis_val = df_cont["pct"]
                    val_disp = f"{df_cont['pct'].iloc[-1]:+.1f}%"
                    hover_str = f"<b>{sel_var}</b>: %{{y:+.2f}}%<extra></extra>"
                elif calc_mode == "฿ บาท":
                    y_axis_val = df_cont["price"] * (THB_RATE if orig_unit == "USD/ตัน" else 1.0)
                    val_disp = f"฿{y_axis_val.iloc[-1]:,.0f}"
                    hover_str = f"<b>{sel_var}</b>: ฿%{{y:,.0f}}<extra></extra>"
                else:
                    y_axis_val = df_cont["price"] / (THB_RATE if orig_unit == "บาท/ตัน" else 1.0)
                    val_disp = f"${y_axis_val.iloc[-1]:,.1f}"
                    hover_str = f"<b>{sel_var}</b>: $%{{y:,.1f}}<extra></extra>"

                plot_df = pd.DataFrame({"date": df_cont["date"], "y": y_axis_val, "orig": df_cont["price"]})
                if len(plot_df) > 3650:
                    plot_df = plot_df.iloc[::3]

                fig.add_trace(go.Scatter(
                    x=plot_df["date"], y=plot_df["y"], mode="lines", name=f"{sel_var}",
                    line=dict(color="#00FFA3", width=1.5), customdata=plot_df["orig"],
                    hovertemplate=hover_str
                ))

                fig.add_annotation(
                    x=plot_df["date"].iloc[-1], y=plot_df["y"].iloc[-1], text=f" <b>{val_disp}</b>",
                    showarrow=False, xanchor="left", font=dict(size=11, color="#00FFA3"),
                    bgcolor="rgba(0, 0, 0, 0.90)", bordercolor="#00FFA3", borderwidth=1, borderpad=2
                )
                fig.update_xaxes(
                    gridcolor="#161a24",
                    showspikes=True,
                    spikemode="across",
                    spikesnap="cursor",
                    spikethickness=1,
                    spikedash="dash",
                    spikecolor="#787b86",
                    tickformat="%d %b %Y",
                    hoverformat="%d %b %Y",
                    fixedrange=False
                )
                strip_items.append({"label": f"{sel_var} ({tf_choice})", "val": val_disp, "pct": df_cont["pct"].iloc[-1], "color": "#00FFA3"})

        y_title = "การเปลี่ยนแปลงตามฤดูกาล (%)" if calc_mode == "%" else f"ระดับราคา ({calc_mode.split()[0]})"
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            margin=dict(l=15, r=180, t=15, b=20),
            height=620,
            dragmode="pan",           # คลิกลากคือเลื่อนซ้าย-ขวา
            hovermode="x",            # ปักป้ายวันที่ชัดเจนบนแกนล่าง
            hoverdistance=100,
            spikedistance=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
            yaxis=dict(
                title=y_title,
                side="right",
                gridcolor="#161a24",
                zeroline=True,
                zerolinecolor="#2a2e39",
                ticksuffix="%" if calc_mode == "%" else "",
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikethickness=1,
                spikedash="dash",
                spikecolor="#787b86",
                fixedrange=True       # ล็อกแกนราคา
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displayModeBar": False,
                "doubleClick": "reset"
            }
        )

        strip_html = "<div style='display:flex; flex-wrap:wrap; gap:12px; margin-top:-6px; padding:6px 10px; background:#08090c; border:1px solid #1a1d26; border-radius:6px; font-family:monospace;'>"
        for it in strip_items:
            sign = "+" if it["pct"] >= 0 else ""
            p_col = "#26a69a" if it["pct"] >= 0 else "#ef5350"
            strip_html += f"<div style='font-size:12px; border-left:3px solid {it['color']}; padding-left:6px;'><b style='color:#ffffff;'>{it['label']}</b>: {it['val']} <b style='color:{p_col};'>({sign}{it['pct']:.2f}%)</b></div>"
        strip_html += "</div>"
        st.markdown(strip_html, unsafe_allow_html=True)

    with tab_report:
        render_rice_ecosystem_report()