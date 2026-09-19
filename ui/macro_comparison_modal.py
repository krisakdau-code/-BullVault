# ui/macro_comparison_modal.py — Universal Macro Terminal & Capital Flow Analytics
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════
# สไตล์พื้นหลังสีดำมืด 95% ของจอภาพ
# ══════════════════════════════════════════════════════════
MODAL_STYLE = """
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
"""

# ══════════════════════════════════════════════════════════
# 1. นิยามสินทรัพย์แยกตามโครงสร้าง 4 หมวด
# ══════════════════════════════════════════════════════════
CRYPTO_GROUPS = {
    "1. เหรียญหลัก (Layer 1)": {
        "BTC": {"name": "Bitcoin", "base": 81579, "vol": 0.024, "color": "#f7931a"},
        "ETH": {"name": "Ethereum", "base": 2980, "vol": 0.030, "color": "#627eea"},
        "SOL": {"name": "Solana", "base": 168, "vol": 0.042, "color": "#14f195"},
        "BNB": {"name": "BNB Chain", "base": 590, "vol": 0.025, "color": "#f3ba2f"},
    },
    "2. โทเค็นใช้งาน (Utility)": {
        "LINK": {"name": "Chainlink", "base": 14.5, "vol": 0.038, "color": "#375bd2"},
        "BAT": {"name": "Basic Attention", "base": 0.22, "vol": 0.040, "color": "#ff5000"},
    },
    "3. โทเค็นกำกับดูแล (Governance)": {
        "UNI": {"name": "Uniswap", "base": 8.2, "vol": 0.041, "color": "#ff007a"},
        "MKR": {"name": "Maker", "base": 1750, "vol": 0.035, "color": "#1aab9b"},
    },
    "4. สเตเบิลคอยน์ (Stablecoin Cap)": {
        "USDT": {"name": "Tether USD", "base": 1.00, "vol": 0.001, "color": "#26a17b"},
        "USDC": {"name": "USD Coin", "base": 1.00, "vol": 0.001, "color": "#2775ca"},
    },
    "5. โทเค็น DeFi": {
        "AAVE": {"name": "Aave", "base": 155, "vol": 0.045, "color": "#b6509e"},
        "CRV": {"name": "Curve DAO", "base": 0.38, "vol": 0.048, "color": "#4388cc"},
    },
    "6. มีมคอยน์ (Memecoin)": {
        "DOGE": {"name": "Dogecoin", "base": 0.14, "vol": 0.055, "color": "#c2a633"},
        "SHIB": {"name": "Shiba Inu", "base": 0.000019, "vol": 0.058, "color": "#e17135"},
    },
    "7. NFT & GameFi": {
        "APE": {"name": "ApeCoin", "base": 0.85, "vol": 0.052, "color": "#0055ff"},
        "SAND": {"name": "The Sandbox", "base": 0.32, "vol": 0.049, "color": "#0084ff"},
    }
}

STOCKS_GICS = {
    "1. Energy (พลังงาน)": {"XLE": {"name": "Energy Sector (XLE)", "base": 89, "vol": 0.016, "color": "#8d6e63"}},
    "2. Materials (วัสดุพื้นฐาน)": {"XLB": {"name": "Materials Sector (XLB)", "base": 92, "vol": 0.014, "color": "#795548"}},
    "3. Industrials (อุตสาหกรรม/ขนส่ง)": {"XLI": {"name": "Industrials (XLI)", "base": 128, "vol": 0.012, "color": "#607d8b"}},
    "4. Consumer Discretionary (ฟุ่มเฟือย)": {"XLY": {"name": "Consumer Discretionary (XLY)", "base": 195, "vol": 0.018, "color": "#e91e63"}},
    "5. Consumer Staples (สินค้าจำเป็น)": {"XLP": {"name": "Consumer Staples (XLP)", "base": 78, "vol": 0.008, "color": "#4caf50"}},
    "6. Health Care (การแพทย์/ยา)": {"XLV": {"name": "Health Care (XLV)", "base": 146, "vol": 0.009, "color": "#00bcd4"}},
    "7. Financials (การเงิน/ธนาคาร)": {"XLF": {"name": "Financials (XLF)", "base": 44, "vol": 0.013, "color": "#3f51b5"}},
    "8. Information Tech (เทคโนโลยี/ชิป)": {"XLK": {"name": "Technology (XLK)", "base": 225, "vol": 0.021, "color": "#00e676"}},
    "9. Communication (สื่อ/แพลตฟอร์ม)": {"XLC": {"name": "Communication (XLC)", "base": 88, "vol": 0.017, "color": "#9c27b0"}},
    "10. Utilities (สาธารณูปโภค)": {"XLU": {"name": "Utilities (XLU)", "base": 72, "vol": 0.010, "color": "#ffc107"}},
    "11. Real Estate (อสังหาริมทรัพย์)": {"XLRE": {"name": "Real Estate (XLRE)", "base": 42, "vol": 0.015, "color": "#ff5722"}}
}

METALS_MINING = {
    "Precious Metals (โลหะมีค่า)": {
        "GOLD": {"name": "ทองคำ (Gold XAU/USD)", "base": 2684, "vol": 0.008, "unit": "$", "color": "#ffd700"},
        "SILVER": {"name": "โลหะเงิน (Silver XAG/USD)", "base": 31.8, "vol": 0.016, "unit": "$", "color": "#e0e0e0"},
        "PLATINUM": {"name": "แพลทินัม (Platinum)", "base": 990, "vol": 0.014, "unit": "$", "color": "#b0bec5"},
    },
    "Industrial Metals (โลหะอุตสาหกรรม)": {
        "COPPER": {"name": "ทองแดง (Copper)", "base": 4.35, "vol": 0.015, "unit": "$", "color": "#ff7043"},
        "ALUMINUM": {"name": "อะลูมิเนียม (Aluminum)", "base": 2610, "vol": 0.012, "unit": "$", "color": "#90a4ae"},
        "IRON_ORE": {"name": "แร่เหล็ก (Iron Ore)", "base": 105, "vol": 0.017, "unit": "$", "color": "#8d6e63"},
        "LITHIUM": {"name": "ลิเทียม (Lithium Carb)", "base": 11200, "vol": 0.025, "unit": "$", "color": "#00e5ff"},
    }
}

FOREX_PAIRS = {
    "DXY": {"name": "ดัชนีดอลลาร์สหรัฐ (US Dollar Index)", "base": 102.5, "vol": 0.004, "unit": "จุด", "color": "#26a69a"},
    "USDTHB": {"name": "ดอลลาร์/บาท (USD/THB)", "base": 34.8, "vol": 0.005, "unit": "บาท", "color": "#ff9800"},
    "EURUSD": {"name": "ยูโร/ดอลลาร์ (EUR/USD)", "base": 1.09, "vol": 0.005, "unit": "$", "color": "#2962ff"},
    "USDJPY": {"name": "ดอลลาร์/เยน (USD/JPY)", "base": 149.2, "vol": 0.007, "unit": "¥", "color": "#e91e63"},
    "GBPUSD": {"name": "ปอนด์/ดอลลาร์ (GBP/USD)", "base": 1.31, "vol": 0.006, "unit": "$", "color": "#ab47bc"},
}

# ══════════════════════════════════════════════════════════
# ฟังก์ชันสร้างชุดข้อมูลจำลอง
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def generate_series(catalog_dict, lookback_days=365):
    np.random.seed(42)
    end_date = datetime.date(2026, 9, 19)
    dates = [end_date - datetime.timedelta(days=i) for i in range(lookback_days)][::-1]
    res = {"Date": dates}
    for item_key, meta in catalog_dict.items():
        base = meta["base"]
        vol = meta["vol"]
        p = base * 0.95
        prices = []
        for _ in range(lookback_days):
            drift = 0.0003
            ret = np.random.normal(drift, vol)
            p = max(0.000001, p * (1.0 + ret))
            prices.append(round(p, 4 if p < 1 else 2))
        res[item_key] = prices
    return pd.DataFrame(res)

def render_chart_with_crosshair(df, selected_items, meta_dict, height=620, unit_default=""):
    fig = go.Figure()
    ticker_items = []
    for code in selected_items:
        meta = meta_dict[code]
        base_val = df[code].iloc[0]
        pct = ((df[code] - base_val) / base_val) * 100.0
        cur_p = df[code].iloc[-1]
        last_pct = pct.iloc[-1]
        color = meta["color"]
        unit = meta.get("unit", unit_default)
        p_str = f"{unit}{cur_p:,.2f}" if unit == "$" else f"{cur_p:,.2f} {unit}"

        fig.add_trace(go.Scatter(
            x=df["Date"], y=pct, mode="lines", name=code,
            line=dict(color=color, width=1.4),
            customdata=df[code],
            hovertemplate=f"<b>{meta['name']}</b><br>ผลตอบแทน: %{{y:+.2f}}%<br>ราคา: %{{customdata:,.2f}} {unit}<extra></extra>"
        ))

        fig.add_annotation(
            x=df["Date"].iloc[-1], y=last_pct,
            text=f" <b>{code} {last_pct:+.1f}%</b> ({p_str})",
            showarrow=False, xanchor="left",
            font=dict(size=11, color=color),
            bgcolor="rgba(0,0,0,0.90)", bordercolor=color, borderwidth=1, borderpad=2
        )
        ticker_items.append({"code": code, "price": p_str, "pct": last_pct, "color": color})

    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(l=15, r=180, t=15, b=20), height=height, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        xaxis=dict(gridcolor="#161a24", showspikes=True, spikemode="across", spikesnap="cursor",
                   spikethickness=1, spikedash="dash", spikecolor="#787b86", tickformat="%d %b %Y", hoverformat="%d %b %Y"),
        yaxis=dict(title="ผลตอบแทนสะสม (%)", side="right", gridcolor="#161a24", zeroline=True,
                   zerolinecolor="#2a2e39", ticksuffix="%", showspikes=True, spikemode="across",
                   spikesnap="cursor", spikethickness=1, spikedash="dash", spikecolor="#787b86")
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": False})

    ticker_html = "<div style='display:flex; flex-wrap:wrap; gap:10px; margin-top:-6px; padding:6px 10px; background:#08090c; border:1px solid #1a1d26; border-radius:6px; font-family:monospace;'>"
    for it in ticker_items:
        sign = "+" if it["pct"] >= 0 else ""
        pct_color = "#26a69a" if it["pct"] >= 0 else "#ef5350"
        ticker_html += f"<div style='font-size:12px; border-left:3px solid {it['color']}; padding-left:6px; margin-right:8px;'><b style='color:#ffffff;'>{it['code']}</b> <span style='color:#9e9e9e;'>{it['price']}</span> <b style='color:{pct_color};'>({sign}{it['pct']:.2f}%)</b></div>"
    ticker_html += "</div>"
    st.markdown(ticker_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 2. หน้าต่างโมดอลย่อย 4 หมวด + 1 ทั่วไป
# ══════════════════════════════════════════════════════════
@st.dialog("🪙 ตลาดคริปโตเคอร์เรนซี (7 กลุ่มโครงสร้าง)", width="large")
def show_crypto_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([0.30, 0.45, 0.25], vertical_alignment="center")
    with c1:
        sel_group = st.selectbox("กลุ่มคริปโต", list(CRYPTO_GROUPS.keys()), key="cr_grp", label_visibility="collapsed")
    with c2:
        meta_sub = CRYPTO_GROUPS[sel_group]
        sel_coins = st.multiselect("เลือกเหรียญ", list(meta_sub.keys()), default=list(meta_sub.keys()), format_func=lambda x: f"{x} - {meta_sub[x]['name']}", key="cr_sel", label_visibility="collapsed")
    with c3:
        tf = st.selectbox("ไทม์เฟรม", ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "4 ปี"], index=3, key="cr_tf", label_visibility="collapsed")

    days_map = {"1 เดือน": 30, "3 เดือน": 90, "6 เดือน": 180, "1 ปี": 365, "2 ปี": 730, "4 ปี": 1460}
    df = generate_series(meta_sub, lookback_days=days_map[tf])
    if sel_coins:
        render_chart_with_crosshair(df, sel_coins, meta_sub, unit_default="$")

@st.dialog("📈 ตลาดหุ้นสากล 11 อุตสาหกรรม (GICS Sectors)", width="large")
def show_stocks_gics_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    flat_gics = {}
    for grp, items in STOCKS_GICS.items():
        for code, meta in items.items():
            flat_gics[code] = meta

    c1, c2 = st.columns([0.70, 0.30], vertical_alignment="center")
    with c1:
        sel_sectors = st.multiselect("เลือก Sector GICS", list(flat_gics.keys()), default=["XLK", "XLE", "XLF", "XLV", "XLY"], format_func=lambda x: f"{x} — {flat_gics[x]['name']}", key="gics_sel", label_visibility="collapsed")
    with c2:
        tf = st.selectbox("ไทม์เฟรม", ["3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "4 ปี", "10 ปี"], index=2, key="gics_tf", label_visibility="collapsed")

    days_map = {"3 เดือน": 90, "6 เดือน": 180, "1 ปี": 365, "2 ปี": 730, "4 ปี": 1460, "10 ปี": 3650}
    df = generate_series(flat_gics, lookback_days=days_map[tf])
    if sel_sectors:
        render_chart_with_crosshair(df, sel_sectors, flat_gics, unit_default="$")

@st.dialog("⛏️ ตลาดแร่ & โลหะ (Precious & Industrial Metals)", width="large")
def show_metals_mining_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    flat_metals = {}
    for grp, items in METALS_MINING.items():
        for code, meta in items.items():
            flat_metals[code] = meta

    c1, c2 = st.columns([0.70, 0.30], vertical_alignment="center")
    with c1:
        sel_metals = st.multiselect("เลือกโลหะ/แร่", list(flat_metals.keys()), default=["GOLD", "SILVER", "COPPER", "LITHIUM"], format_func=lambda x: f"{x} — {flat_metals[x]['name']}", key="metal_sel", label_visibility="collapsed")
    with c2:
        tf = st.selectbox("ไทม์เฟรม", ["3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี", "10 ปี"], index=2, key="metal_tf", label_visibility="collapsed")

    days_map = {"3 เดือน": 90, "6 เดือน": 180, "1 ปี": 365, "2 ปี": 730, "5 ปี": 1825, "10 ปี": 3650}
    df = generate_series(flat_metals, lookback_days=days_map[tf])
    if sel_metals:
        render_chart_with_crosshair(df, sel_metals, flat_metals)

@st.dialog("💵 ตลาดเงินตรา & ค่าเงิน (Forex & DXY)", width="large")
def show_forex_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    c1, c2 = st.columns([0.70, 0.30], vertical_alignment="center")
    with c1:
        sel_fx = st.multiselect("เลือกคู่เงิน/ดัชนี", list(FOREX_PAIRS.keys()), default=["DXY", "USDTHB", "EURUSD", "USDJPY"], format_func=lambda x: f"{x} — {FOREX_PAIRS[x]['name']}", key="fx_sel", label_visibility="collapsed")
    with c2:
        tf = st.selectbox("ไทม์เฟรม", ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี"], index=3, key="fx_tf", label_visibility="collapsed")

    days_map = {"1 เดือน": 30, "3 เดือน": 90, "6 เดือน": 180, "1 ปี": 365, "2 ปี": 730, "5 ปี": 1825}
    df = generate_series(FOREX_PAIRS, lookback_days=days_map[tf])
    if sel_fx:
        render_chart_with_crosshair(df, sel_fx, FOREX_PAIRS)

@st.dialog("🌐 Macro Terminal — เปรียบเทียบผลตอบแทนข้ามกลุ่มสินทรัพย์", width="large")
def show_macro_comparison_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    macro_items = {
        "BTC": {"name": "Bitcoin", "base": 81579, "vol": 0.024, "unit": "$", "color": "#f7931a"},
        "GOLD": {"name": "ทองคำ (Gold)", "base": 2684, "vol": 0.008, "unit": "$", "color": "#ffd700"},
        "RICE": {"name": "ข้าวหอมมะลิ 105", "base": 14850, "vol": 0.010, "unit": "บ./ตัน", "color": "#4caf50"},
        "SET": {"name": "หุ้นไทย (SET)", "base": 1422, "vol": 0.007, "unit": "จุด", "color": "#00bcd4"},
        "DXY": {"name": "ดอลลาร์ (DXY)", "base": 102.5, "vol": 0.004, "unit": "จุด", "color": "#e91e63"},
        "OIL": {"name": "น้ำมันดิบ Brent", "base": 74.8, "vol": 0.016, "unit": "$", "color": "#8d6e63"},
    }
    c1, c2 = st.columns([0.65, 0.35], vertical_alignment="center")
    with c1:
        sel = st.multiselect("เลือกสินทรัพย์ข้ามกลุ่ม", list(macro_items.keys()), default=["BTC", "GOLD", "RICE", "SET", "DXY"], format_func=lambda x: f"{x} - {macro_items[x]['name']}", key="macro_sel_cross", label_visibility="collapsed")
    with c2:
        tf = st.selectbox("ย้อนหลัง", ["3 เดือน", "6 เดือน", "1 ปี (1Y)", "2 ปี (2Y)", "4 ปี (4Y)", "10 ปี (10Y)"], index=2, key="macro_cross_tf", label_visibility="collapsed")

    days_map = {"3 เดือน": 90, "6 เดือน": 180, "1 ปี (1Y)": 365, "2 ปี (2Y)": 730, "4 ปี (4Y)": 1460, "10 ปี (10Y)": 3650}
    df = generate_series(macro_items, lookback_days=days_map[tf])
    if sel:
        render_chart_with_crosshair(df, sel, macro_items)

# ══════════════════════════════════════════════════════════
# 3. บทวิเคราะห์ทิศทางเงินทุนไหลเข้า-ออก (Capital Flow Analytics)
# ══════════════════════════════════════════════════════════
@st.dialog("🧭 บทวิเคราะห์ทิศทางเงินทุนไหลเข้า-ออก (Capital Flow & Rotation)", width="large")
def show_flow_analysis_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    st.markdown("<div style='font-size:18px; font-weight:700; color:#00FFA3; margin-bottom:12px;'>📊 แดชบอร์ดสรุปกระแสเงินทุนโลก & สถานะสินทรัพย์ (Macro Pulse)</div>", unsafe_allow_html=True)

    # 4 การ์ดสรุปสถานะหลัก
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'>
            <div style='font-size:11px; color:#787b86;'>โหมดตลาดปัจจุบัน</div>
            <div style='font-size:16px; font-weight:700; color:#00FFA3;'>🟢 Risk-On (สินทรัพย์เสี่ยง)</div>
            <div style='font-size:10px; color:#26a69a;'>เงินทุนไหลเข้า Crypto & Tech</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'>
            <div style='font-size:11px; color:#787b86;'>กลุ่มเงินเข้าสูงสุด (Top Inflow)</div>
            <div style='font-size:16px; font-weight:700; color:#f7931a;'>🪙 คริปโต (BTC / L1)</div>
            <div style='font-size:10px; color:#26a69a;'>+18.4% Net Inflow 30D</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'>
            <div style='font-size:11px; color:#787b86;'>กลุ่มเงินออกสูงสุด (Outflow)</div>
            <div style='font-size:16px; font-weight:700; color:#ef5350;'>⚡ Utilities & พันธบัตร</div>
            <div style='font-size:10px; color:#ef5350;'>-4.2% ถูกเทขายทำกำไร</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'>
            <div style='font-size:11px; color:#787b86;'>ทิศทางค่าเงิน (DXY / THB)</div>
            <div style='font-size:16px; font-weight:700; color:#ffd700;'>💵 ดอลลาร์เริ่มชะลอ</div>
            <div style='font-size:10px; color:#26a69a;'>บาทแข็งค่า หนุนสินค้าเกษตร</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # กราฟแท่งแสดง Relative Strength Flow ของแต่ละกลุ่ม
    categories = [
        "คริปโต (Layer 1)", "เทคโนโลยี (XLK)", "ทองคำ (Safe Haven)",
        "สินค้าเกษตร/ข้าว", "อุตสาหกรรม (XLI)", "หุ้นไทย (SET)",
        "พลังงาน (XLE)", "ดอลลาร์ (DXY)", "สาธารณูปโภค (XLU)"
    ]
    flow_scores = [18.4, 12.1, 8.5, 3.8, 1.2, -0.8, -2.4, -3.1, -4.2]
    colors = ["#00e676" if x > 0 else "#ef5350" for x in flow_scores]

    fig_flow = go.Figure(go.Bar(
        x=flow_scores, y=categories, orientation='h',
        marker=dict(color=colors, line=dict(color="#1a1d26", width=1)),
        hovertemplate="<b>%{y}</b>: %{x:+.1f}%<extra></extra>"
    ))
    fig_flow.update_layout(
        title="ดัชนีวัดความแรงของเงินทุนไหลเข้า/ออก 30 วันล่าสุด (Capital Flow Score %)",
        template="plotly_dark", paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(l=10, r=40, t=40, b=20), height=340,
        xaxis=dict(gridcolor="#161a24", zerolinecolor="#474d57", zerolinewidth=1.2, ticksuffix="%"),
        yaxis=dict(gridcolor="#161a24", autorange="reversed")
    )
    st.plotly_chart(fig_flow, use_container_width=True, config={"displayModeBar": False})

    # สรุปมุมมองเชิงกลยุทธ์แบบตรงไปตรงมา
    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:6px; padding:12px; font-size:12px; line-height:1.7; color:#d1d4dc;'>
        <b style='color:#00FFA3;'>📌 วิเคราะห์เจาะลึกสถานะแต่ละกลุ่ม:</b><br>
        • <b>คริปโตเคอร์เรนซี:</b> เงินทุนหลักยังคงกระจุกตัวใน BTC และเหรียญ Layer 1 ขนาดใหญ่ ยังไม่หมุนเข้าสู่ Altcoins หรือ DeFi ขนาดเล็กเต็มตัว<br>
        • <b>ตลาดหุ้น:</b> กลุ่มเทคโนโลยี (Tech) และการเงิน (Financials) มีเม็ดเงินไหลเข้าแข็งแกร่ง ขณะที่กลุ่มปลอดภัย (Defensive) ถูกลดสัดส่วนลง<br>
        • <b>แร่และโลหะ:</b> ทองคำทรงตัวในระดับสูงจากการกระจายความเสี่ยงของธนาคารกลาง ส่วนทองแดงเริ่มมีแรงซื้อกลับจากภาคอุตสาหกรรม<br>
        • <b>สินค้าเกษตรและข้าว:</b> ราคาข้าวไทยได้รับแรงหนุนจากความต้องการส่งออกช่วงปลายปี แต่ต้องจับตาการแข่งขันด้านราคาจากอินเดียและเวียดนาม
    </div>
    """, unsafe_allow_html=True)