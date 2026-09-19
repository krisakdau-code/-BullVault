# ui/rice_seasonality_modal.py — Rice Seasonality & Global FOB Benchmark Dashboard
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════
# 1. โครงสร้างข้อมูลตลาดข้าว (เพิ่มหมวดเปรียบเทียบส่งออกทุกประเทศ)
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

@st.cache_data(ttl=3600, show_spinner=False)
def get_benchmark_cross_country_series(bench_name, lookback_days=365):
    cfg_group = RICE_CATEGORIES["🌍 เปรียบเทียบข้าวส่งออกทุกประเทศ (FOB Benchmark)"]["benchmarks"][bench_name]
    end_date = datetime.date(2026, 9, 19)
    dates = [end_date - datetime.timedelta(days=i) for i in range(lookback_days)][::-1]
    res = {"Date": dates}
    for c_name, item in cfg_group.items():
        np.random.seed(int(item["base"]) + 42)
        p = item["base"] * 0.90
        prices = []
        for _ in range(lookback_days):
            drift = 0.0002
            ret = np.random.normal(drift, 0.007)
            p = max(50.0, p * (1.0 + ret))
            prices.append(round(p, 2))
        res[c_name] = prices
    return pd.DataFrame(res)

@st.cache_data(ttl=3600, show_spinner=False)
def get_rice_seasonality_data(cat_name, variety_name):
    cfg = RICE_CATEGORIES[cat_name]["varieties"][variety_name]
    base = cfg["base"]
    vol = cfg["vol"]
    years = [2023, 2024, 2025, 2026]
    cur_date = datetime.date(2026, 9, 19)
    records = []
    monthly_season_factor = [-0.05, -0.04, -0.02, 0.01, 0.03, 0.06, 0.08, 0.07, 0.04, 0.01, -0.04, -0.06]

    for yr_idx, yr in enumerate(years):
        np.random.seed(yr + int(base))
        start_date = datetime.date(yr, 1, 1)
        end_date = cur_date if yr == 2026 else datetime.date(yr, 12, 31)
        yr_drift = (yr_idx - 1.5) * (base * 0.04)
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
# 2. หน้าต่างแสดงผล (พร้อม Crosshair เส้นประ & ป้ายวันที่)
# ══════════════════════════════════════════════════════════
@st.dialog("🌾 ศูนย์ข้อมูลตลาดข้าว & วัฏจักรฤดูกาล (Wide Terminal)", width="large")
def show_rice_market_modal():
    st.markdown("""
    <style>
    div[data-testid="stDialog"] div[role="dialog"] {
        width: 95vw !important;
        max-width: 95vw !important;
        background-color: #000000 !important;
        border: 1px solid #1a1d26 !important;
        border-radius: 8px !important;
        padding: 1rem 1.4rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([0.32, 0.32, 0.20, 0.16], vertical_alignment="center")
    with c1:
        sel_cat = st.selectbox("กลุ่มตลาดข้าว", list(RICE_CATEGORIES.keys()), key="rs_cat", label_visibility="collapsed")

    is_bench = RICE_CATEGORIES[sel_cat].get("is_benchmark", False)
    unit_name = RICE_CATEGORIES[sel_cat]["unit"]

    fig = go.Figure()
    strip_items = []

    # โหมดเปรียบเทียบข้าวส่งออกทุกประเทศ
    if is_bench:
        bench_map = RICE_CATEGORIES[sel_cat]["benchmarks"]
        with c2:
            sel_bench = st.selectbox("เกณฑ์เปรียบเทียบ", list(bench_map.keys()), key="rs_bench_var", label_visibility="collapsed")
        with c3:
            tf_bench = st.segmented_control("ย้อนหลัง", ["6 เดือน", "1 ปี", "2 ปี"], default="1 ปี", key="rs_bench_tf", label_visibility="collapsed")
        with c4:
            calc_mode = st.segmented_control("โหมด", ["ราคา", "%"], default="ราคา", key="rs_bench_mode", label_visibility="collapsed")

        days_dict = {"6 เดือน": 180, "1 ปี": 365, "2 ปี": 730}
        df_bench = get_benchmark_cross_country_series(sel_bench, lookback_days=days_dict[tf_bench])
        country_cfgs = bench_map[sel_bench]

        for c_name, c_meta in country_cfgs.items():
            base_val = df_bench[c_name].iloc[0]
            pct_val = ((df_bench[c_name] - base_val) / base_val) * 100.0
            y_data = pct_val if calc_mode == "%" else df_bench[c_name]
            cur_p = df_bench[c_name].iloc[-1]
            last_pct = pct_val.iloc[-1]
            color = c_meta["color"]

            badge_text = f" <b>{c_name}</b> {cur_p:,.1f} {unit_name} ({last_pct:+.1f}%)" if calc_mode != "%" else f" <b>{c_name}</b> {last_pct:+.1f}% ({cur_p:,.1f} {unit_name})"

            fig.add_trace(go.Scatter(
                x=df_bench["Date"],
                y=y_data,
                mode="lines",
                name=c_name,
                line=dict(color=color, width=1.6),
                customdata=df_bench[c_name],
                hovertemplate=f"<b>{c_name}</b><br>ราคา: %{{customdata:,.2f}} {unit_name}<br>เปลี่ยนแปลง: %{{y:+.2f}}%<extra></extra>" if calc_mode == "%" else f"<b>{c_name}</b><br>ราคา: %{{y:,.2f}} {unit_name}<extra></extra>"
            ))

            fig.add_annotation(
                x=df_bench["Date"].iloc[-1],
                y=y_data.iloc[-1],
                text=badge_text,
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color=color),
                bgcolor="rgba(0, 0, 0, 0.90)",
                bordercolor=color,
                borderwidth=1,
                borderpad=2
            )
            strip_items.append({"label": c_name, "price": cur_p, "pct": last_pct, "color": color})

        fig.update_xaxes(
            gridcolor="#161a24",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikedash="dash",
            spikecolor="#787b86",
            tickformat="%d %b %Y",
            hoverformat="%d %b %Y"
        )
    else:
        # โหมดรายประเทศเทียบ 4 ปีตามฤดูกาลเดิม
        with c2:
            sel_var = st.selectbox("สายพันธุ์ข้าว", list(RICE_CATEGORIES[sel_cat]["varieties"].keys()), key="rs_var", label_visibility="collapsed")
        with c3:
            timeframe = st.segmented_control("ไทม์เฟรม", ["วัน", "เดือน", "ปี"], default="วัน", key="rs_tf", label_visibility="collapsed")
        with c4:
            calc_mode = st.segmented_control("โหมด", ["%", "ราคา"], default="%", key="rs_mode", label_visibility="collapsed")

        df = get_rice_seasonality_data(sel_cat, sel_var)
        year_colors = {2023: "#00bcd4", 2024: "#ff9800", 2025: "#4caf50", 2026: "#2962ff"}
        month_names_th = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

        if timeframe == "วัน":
            for yr in [2023, 2024, 2025, 2026]:
                df_y = df[df["year"] == yr].sort_values("day_of_year").copy()
                if df_y.empty:
                    continue
                base_val = df_y["price"].iloc[0]
                df_y["pct"] = ((df_y["price"] - base_val) / base_val) * 100.0
                y_axis_val = df_y["pct"] if calc_mode == "%" else df_y["price"]
                df_y["plot_date"] = pd.to_datetime([f"2024-{m:02d}-{min(d, 28 if m == 2 else 30):02d}" for m, d in zip(df_y["month"], df_y["day"])])
                
                cur_p = df_y["price"].iloc[-1]
                last_pct = df_y["pct"].iloc[-1]
                p_badge = f"{yr}: {last_pct:+.1f}% ({cur_p:,.0f} {unit_name})" if calc_mode == "%" else f"{yr}: {cur_p:,.0f} {unit_name} ({last_pct:+.1f}%)"

                fig.add_trace(go.Scatter(
                    x=df_y["plot_date"],
                    y=y_axis_val,
                    mode="lines",
                    name=f"{yr}",
                    line=dict(color=year_colors[yr], width=1.8 if yr == 2026 else 1.3),
                    customdata=df_y["price"],
                    hovertemplate=f"<b>ปี {yr}</b><br>ราคา: %{{customdata:,.1f}} {unit_name}<br>เปลี่ยนแปลง: %{{y:+.2f}}%<extra></extra>" if calc_mode == "%" else f"<b>ปี {yr}</b><br>ราคา: %{{y:,.0f}} {unit_name}<extra></extra>"
                ))

                fig.add_annotation(
                    x=df_y["plot_date"].iloc[-1],
                    y=y_axis_val.iloc[-1],
                    text=f" <b>{p_badge}</b>",
                    showarrow=False,
                    xanchor="left",
                    font=dict(size=11, color=year_colors[yr]),
                    bgcolor="rgba(0, 0, 0, 0.90)",
                    bordercolor=year_colors[yr],
                    borderwidth=1,
                    borderpad=2
                )
                strip_items.append({"label": f"ปี {yr}", "price": cur_p, "pct": last_pct, "color": year_colors[yr]})

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
                hoverformat="%d %B"
            )
        elif timeframe == "เดือน":
            for yr in [2023, 2024, 2025, 2026]:
                df_y = df[df["year"] == yr].groupby("month")["price"].mean().reset_index()
                if df_y.empty:
                    continue
                base_val = df_y["price"].iloc[0]
                df_y["pct"] = ((df_y["price"] - base_val) / base_val) * 100.0
                y_axis_val = df_y["pct"] if calc_mode == "%" else df_y["price"]

                fig.add_trace(go.Scatter(
                    x=[month_names_th[m - 1] for m in df_y["month"]],
                    y=y_axis_val,
                    mode="lines+markers",
                    name=f"{yr}",
                    line=dict(color=year_colors[yr], width=1.8 if yr == 2026 else 1.3),
                    marker=dict(size=5),
                    customdata=df_y["price"],
                    hovertemplate=f"<b>ปี {yr}</b>: %{{customdata:,.0f}} {unit_name} (%{{y:+.2f}}%)<extra></extra>"
                ))
                strip_items.append({"label": f"ปี {yr}", "price": df_y["price"].iloc[-1], "pct": df_y["pct"].iloc[-1], "color": year_colors[yr]})
            fig.update_xaxes(gridcolor="#161a24", showspikes=True, spikemode="across", spikedash="dash", spikecolor="#787b86")
        else:
            df_cont = df.sort_values("date").copy()
            base_val = df_cont["price"].iloc[0]
            df_cont["pct"] = ((df_cont["price"] - base_val) / base_val) * 100.0
            y_axis_val = df_cont["pct"] if calc_mode == "%" else df_cont["price"]

            fig.add_trace(go.Scatter(
                x=df_cont["date"],
                y=y_axis_val,
                mode="lines",
                name="ราคาต่อเนื่อง",
                line=dict(color="#00bcd4", width=1.5),
                customdata=df_cont["price"],
                hovertemplate=f"<b>ราคา:</b> %{{customdata:,.0f}} {unit_name}<extra></extra>"
            ))
            fig.update_xaxes(
                gridcolor="#161a24",
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikethickness=1,
                spikedash="dash",
                spikecolor="#787b86",
                tickformat="%d %b %Y",
                hoverformat="%d %b %Y"
            )

    y_label = "การเปลี่ยนแปลงตามฤดูกาล (%)" if calc_mode == "%" else f"ระดับราคา ({unit_name})"
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=15, r=180, t=15, b=20),
        height=620,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        yaxis=dict(
            title=y_label,
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
            spikecolor="#787b86"
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": False})

    strip_html = "<div style='display:flex; flex-wrap:wrap; gap:12px; margin-top:-6px; padding:6px 10px; background:#08090c; border:1px solid #1a1d26; border-radius:6px; font-family:monospace;'>"
    for it in strip_items:
        sign = "+" if it["pct"] >= 0 else ""
        p_col = "#26a69a" if it["pct"] >= 0 else "#ef5350"
        strip_html += (
            f"<div style='font-size:12px; border-left:3px solid {it['color']}; padding-left:6px;'>"
            f"<b style='color:#ffffff;'>{it['label']}</b>: {it['price']:,.0f} {unit_name} "
            f"<b style='color:{p_col};'>({sign}{it['pct']:.2f}%)</b>"
            f"</div>"
        )
    strip_html += "</div>"
    st.markdown(strip_html, unsafe_allow_html=True)