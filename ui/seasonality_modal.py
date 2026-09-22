# ui/seasonality_modal.py — TradingView-style Seasonality Analysis Modal
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

@st.dialog("ฤดูกาล", width="large")
def show_seasonality_modal(sym: str = "BTCUSDT"):
    # 1. แถบควบคุมบนสุด (โหมดมุมมอง, เส้นค่าเฉลี่ย, สเกลราคา)
    c1, c2, c3, c4 = st.columns([0.45, 0.25, 0.15, 0.15], vertical_alignment="center")
    
    with c1:
        st.markdown(f"<h3 style='margin:0; color:#fff;'>💠 {sym} • ฤดูกาล</h3>", unsafe_allow_html=True)
    with c2:
        v_mode = st.radio("มุมมอง", ["📈 กราฟเส้น", "▦ ตารางผลตอบแทน"], horizontal=True, label_visibility="collapsed")
    with c3:
        show_avg = st.toggle("ค่าเฉลี่ย", value=True)
    with c4:
        if st.button("⌂ กลับไปชาร์ต", use_container_width=True, type="secondary"):
            st.rerun()

    # 2. ข้อมูลผลตอบแทนรายเดือนจริงตามรูปต้นแบบ (2023 - 2026)
    month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    short_months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    
    data = {
        2026: [-70.57, -31.33, 68.42, -14.58, -14.63, -15.71, 6.85, 3.14, 7.66, None, None, None],
        2025: [-19.29, -33.30, -18.27, -7.08, -25.53, -11.22, 18.89, -2.10, 13.13, -37.87, -50.08, -4.08],
        2024: [-16.83, 24.99, 4.77, -31.84, 20.53, -34.23, -28.44, -1.96, 3.32, 7.85, 58.41, -20.53],
        2023: [None, None, None, None, -34.17, -3.70, -11.20, -14.33, 65.31, -12.75, 8.10, 103.90]
    }
    year_totals = {2026: -75.18, 2025: -89.41, 2024: -42.09, 2023: 53.33}

    # 3. แสดงผลตามโหมดที่เลือก
    if "กราฟเส้น" in v_mode:
        # มุมมองกราฟเส้น (Line Chart Overlay)
        fig = go.Figure()
        colors = {2026: "#2962FF", 2025: "#089981", 2024: "#FF9800", 2023: "#00BCD4"}

        # คำนวณเส้นค่าเฉลี่ย
        avg_pts = []
        for m_idx in range(12):
            vals = [data[y][m_idx] for y in data if data[y][m_idx] is not None]
            avg_pts.append(np.mean(vals) if vals else None)

        if show_avg:
            fig.add_trace(go.Scatter(
                x=short_months, y=avg_pts,
                mode="lines", name="Avg",
                line=dict(color="#ffffff", width=2, dash="dot"),
                hoverinfo="y+name"
            ))

        for yr in sorted(data.keys()):
            y_vals = data[yr]
            fig.add_trace(go.Scatter(
                x=short_months, y=y_vals,
                mode="lines+markers" if yr == 2026 else "lines",
                name=str(yr),
                line=dict(color=colors.get(yr, "#fff"), width=2.2),
                marker=dict(size=5 if yr == 2026 else 0)
            ))

        fig.update_layout(
            plot_bgcolor="#0b0e14",
            paper_bgcolor="#0b0e14",
            margin=dict(l=15, r=70, t=15, b=25),
            height=420,
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor="#1e222d", gridwidth=1, griddash="dash", color="#8b949e"),
            yaxis=dict(showgrid=True, gridcolor="#1e222d", zeroline=True, zerolinecolor="#434651", color="#8b949e", side="right", ticksuffix="%")
        )
        st.plotly_chart(fig, use_container_width=True)

        # Legend สรุปเปอร์เซ็นต์ท้ายเส้น
        st.markdown(f"""
        <div style="display:flex; justify-content:center; gap:20px; font-size:12px; margin-top:-10px;">
            <span style="color:#2962FF; font-weight:700;">● 2026 ({year_totals[2026]:+.2f}%)</span>
            <span style="color:#089981; font-weight:700;">● 2025 ({year_totals[2025]:+.2f}%)</span>
            <span style="color:#FF9800; font-weight:700;">● 2024 ({year_totals[2024]:+.2f}%)</span>
            <span style="color:#00BCD4; font-weight:700;">● 2023 ({year_totals[2023]:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

    else:
        # มุมมองตาราง Heatmap รายเดือน (รูปที่ 4)
        tbl_html = """
        <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; font-size:12px; text-align:center; min-width:850px;">
            <tr style="color:#787b86; border-bottom:1px solid #2a2e39;">
                <th style="padding:10px 6px; text-align:left;">วันที่</th>
        """
        for m in month_names:
            tbl_html += f"<th>{m}</th>"
        tbl_html += "<th>ปี</th></tr>"

        # วนลูปแถวแต่ละปี
        for yr in sorted(data.keys(), reverse=True):
            tbl_html += f'<tr style="border-bottom:1px solid #1a1e29;"><td style="padding:9px 6px; text-align:left; font-weight:700; color:#d1d4dc;">{yr}</td>'
            for val in data[yr]:
                if val is None:
                    tbl_html += '<td style="color:#434651;">—</td>'
                else:
                    bg = "rgba(41, 98, 255, 0.18)" if val >= 0 else "rgba(242, 54, 69, 0.18)"
                    tc = "#2962FF" if val >= 0 else "#F23645"
                    tbl_html += f'<td style="background:{bg}; color:{tc}; font-weight:600; padding:6px 2px;">{val:+.2f}%</td>'
            
            # ช่องผลรวมทั้งปี
            tot = year_totals[yr]
            tot_bg = "rgba(41, 98, 255, 0.28)" if tot >= 0 else "rgba(242, 54, 69, 0.28)"
            tot_tc = "#2962FF" if tot >= 0 else "#F23645"
            tbl_html += f'<td style="background:{tot_bg}; color:{tot_tc}; font-weight:700;">{tot:+.2f}%</td></tr>'

        # แถวสรุป "ขึ้น และ ลง" ด้านล่างสุด
        tbl_html += '<tr style="border-top:1px solid #2a2e39; color:#d1d4dc; font-weight:700;"><td style="padding:10px 6px; text-align:left;">ขึ้น และ ลง</td>'
        for m_idx in range(12):
            ups = sum(1 for yr in data if data[yr][m_idx] is not None and data[yr][m_idx] > 0)
            downs = sum(1 for yr in data if data[yr][m_idx] is not None and data[yr][m_idx] < 0)
            txt = []
            if ups > 0: txt.append(f'<span style="color:#089981;">▲{ups}</span>')
            if downs > 0: txt.append(f'<span style="color:#F23645;">▼{downs}</span>')
            tbl_html += f'<td>{" ".join(txt) if txt else "—"}</td>'
        tbl_html += '<td></td></tr></table></div>'
        st.markdown(tbl_html, unsafe_allow_html=True)