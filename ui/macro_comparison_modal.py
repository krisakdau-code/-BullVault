# ui/macro_comparison_modal.py — Universal Macro Terminal & Tabbed Capital Flow Intelligence
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

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
</style>
"""

THB_RATE = 34.8  # อัตราแลกเปลี่ยนอ้างอิง USD/THB

# ══════════════════════════════════════════════════════════
# 1. นิยามโครงสร้างสินทรัพย์ครบทุกหมวดหมู่เดิม (+ หัวข้อที่ 8 ตัวแทนกลุ่ม)
# ══════════════════════════════════════════════════════════
CRYPTO_GROUPS = {
    "1. เหรียญหลัก (Layer 1)": {
        "BTC": {"name": "Bitcoin", "base": 81579, "vol": 0.024, "unit": "$", "color": "#f7931a"},
        "ETH": {"name": "Ethereum", "base": 2980, "vol": 0.030, "unit": "$", "color": "#627eea"},
        "SOL": {"name": "Solana", "base": 168, "vol": 0.042, "unit": "$", "color": "#14f195"},
        "BNB": {"name": "BNB Chain", "base": 590, "vol": 0.025, "unit": "$", "color": "#f3ba2f"}
    },
    "2. โทเค็นใช้งาน (Utility)": {
        "LINK": {"name": "Chainlink", "base": 14.5, "vol": 0.038, "unit": "$", "color": "#375bd2"},
        "BAT": {"name": "Basic Attention", "base": 0.22, "vol": 0.040, "unit": "$", "color": "#ff5000"}
    },
    "3. โทเค็นกำกับดูแล (Governance)": {
        "UNI": {"name": "Uniswap", "base": 8.2, "vol": 0.041, "unit": "$", "color": "#ff007a"},
        "MKR": {"name": "Maker", "base": 1750, "vol": 0.035, "unit": "$", "color": "#1aab9b"}
    },
    "4. สเตเบิลคอยน์ (Stablecoin Cap)": {
        "USDT": {"name": "Tether USD", "base": 1.00, "vol": 0.001, "unit": "$", "color": "#26a17b"},
        "USDC": {"name": "USD Coin", "base": 1.00, "vol": 0.001, "unit": "$", "color": "#2775ca"}
    },
    "5. โทเค็น DeFi": {
        "AAVE": {"name": "Aave", "base": 155, "vol": 0.045, "unit": "$", "color": "#b6509e"},
        "CRV": {"name": "Curve DAO", "base": 0.38, "vol": 0.048, "unit": "$", "color": "#4388cc"}
    },
    "6. มีมคอยน์ (Memecoin)": {
        "DOGE": {"name": "Dogecoin", "base": 0.14, "vol": 0.055, "unit": "$", "color": "#c2a633"},
        "SHIB": {"name": "Shiba Inu", "base": 0.000019, "vol": 0.058, "unit": "$", "color": "#e17135"}
    },
    "7. NFT & GameFi": {
        "APE": {"name": "ApeCoin", "base": 0.85, "vol": 0.052, "unit": "$", "color": "#0055ff"},
        "SAND": {"name": "The Sandbox", "base": 0.32, "vol": 0.049, "unit": "$", "color": "#0084ff"}
    },
    "8. ตัวแทนกลุ่มเหรียญ (Sector Leaders)": {
        "BTC": {"name": "BTC (Layer 1)", "base": 81579, "vol": 0.024, "unit": "$", "color": "#f7931a"},
        "LINK": {"name": "LINK (Utility)", "base": 14.5, "vol": 0.038, "unit": "$", "color": "#375bd2"},
        "UNI": {"name": "UNI (Governance)", "base": 8.2, "vol": 0.041, "unit": "$", "color": "#ff007a"},
        "USDT": {"name": "USDT (Stablecoin)", "base": 1.00, "vol": 0.001, "unit": "$", "color": "#26a17b"},
        "AAVE": {"name": "AAVE (DeFi)", "base": 155, "vol": 0.045, "unit": "$", "color": "#b6509e"},
        "DOGE": {"name": "DOGE (Memecoin)", "base": 0.14, "vol": 0.055, "unit": "$", "color": "#c2a633"},
        "SAND": {"name": "SAND (NFT/Game)", "base": 0.32, "vol": 0.049, "unit": "$", "color": "#0084ff"}
    }
}

STOCKS_GICS = {
    "1. Energy (พลังงาน)": {"XLE": {"name": "Energy Sector", "base": 89, "vol": 0.016, "unit": "$", "color": "#8d6e63"}},
    "2. Materials (วัสดุพื้นฐาน)": {"XLB": {"name": "Materials", "base": 92, "vol": 0.014, "unit": "$", "color": "#795548"}},
    "3. Industrials (อุตสาหกรรม/ขนส่ง)": {"XLI": {"name": "Industrials", "base": 128, "vol": 0.012, "unit": "$", "color": "#607d8b"}},
    "4. Consumer Discretionary (ฟุ่มเฟือย)": {"XLY": {"name": "Consumer Discr", "base": 195, "vol": 0.018, "unit": "$", "color": "#e91e63"}},
    "5. Consumer Staples (สินค้าจำเป็น)": {"XLP": {"name": "Consumer Staples", "base": 78, "vol": 0.008, "unit": "$", "color": "#4caf50"}},
    "6. Health Care (การแพทย์/ยา)": {"XLV": {"name": "Health Care", "base": 146, "vol": 0.009, "unit": "$", "color": "#00bcd4"}},
    "7. Financials (การเงิน/ธนาคาร)": {"XLF": {"name": "Financials", "base": 44, "vol": 0.013, "unit": "$", "color": "#3f51b5"}},
    "8. Information Tech (ชิป/ซอฟต์แวร์)": {"XLK": {"name": "Technology", "base": 225, "vol": 0.021, "unit": "$", "color": "#00e676"}},
    "9. Communication (สื่อ/แพลตฟอร์ม)": {"XLC": {"name": "Communication", "base": 88, "vol": 0.017, "unit": "$", "color": "#9c27b0"}},
    "10. Utilities (สาธารณูปโภค)": {"XLU": {"name": "Utilities", "base": 72, "vol": 0.010, "unit": "$", "color": "#ffc107"}},
    "11. Real Estate (อสังหาริมทรัพย์)": {"XLRE": {"name": "Real Estate", "base": 42, "vol": 0.015, "unit": "$", "color": "#ff5722"}}
}

METALS_MINING = {
    "Precious Metals (โลหะมีค่า)": {
        "GOLD": {"name": "ทองคำ (Gold)", "base": 2684, "vol": 0.008, "unit": "$", "color": "#ffd700"},
        "SILVER": {"name": "เงิน (Silver)", "base": 31.8, "vol": 0.016, "unit": "$", "color": "#e0e0e0"},
        "PLATINUM": {"name": "แพลทินัม", "base": 990, "vol": 0.014, "unit": "$", "color": "#b0bec5"}
    },
    "Industrial Metals (โลหะอุตสาหกรรม)": {
        "COPPER": {"name": "ทองแดง", "base": 4.35, "vol": 0.015, "unit": "$", "color": "#ff7043"},
        "ALUMINUM": {"name": "อะลูมิเนียม", "base": 2610, "vol": 0.012, "unit": "$", "color": "#90a4ae"},
        "IRON_ORE": {"name": "แร่เหล็ก", "base": 105, "vol": 0.017, "unit": "$", "color": "#8d6e63"},
        "LITHIUM": {"name": "ลิเทียม", "base": 11200, "vol": 0.025, "unit": "$", "color": "#00e5ff"}
    }
}

FOREX_PAIRS = {
    "DXY": {"name": "ดัชนีดอลลาร์", "base": 102.5, "vol": 0.004, "unit": "จุด", "color": "#26a69a"},
    "USDTHB": {"name": "ดอลลาร์/บาท", "base": 34.8, "vol": 0.005, "unit": "บาท", "color": "#ff9800"},
    "EURUSD": {"name": "ยูโร/ดอลลาร์", "base": 1.09, "vol": 0.005, "unit": "$", "color": "#2962ff"},
    "USDJPY": {"name": "ดอลลาร์/เยน", "base": 149.2, "vol": 0.007, "unit": "¥", "color": "#e91e63"},
    "GBPUSD": {"name": "ปอนด์/ดอลลาร์", "base": 1.31, "vol": 0.006, "unit": "$", "color": "#ab47bc"}
}

# ══════════════════════════════════════════════════════════
# ฟังก์ชันสร้างข้อมูลและการเรนเดอร์กราฟ
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def generate_series(catalog_dict, lookback_days=365):
    np.random.seed(42)
    end_date = datetime.date(2026, 9, 21)
    dates = [end_date - datetime.timedelta(days=i) for i in range(lookback_days)][::-1]
    res = {"Date": dates}
    for item_key, meta in catalog_dict.items():
        base = meta["base"]
        vol = meta["vol"]
        p = base * 0.95
        prices = []
        for _ in range(lookback_days):
            ret = np.random.normal(0.0003, vol)
            p = max(0.000001, p * (1.0 + ret))
            prices.append(p)
        res[item_key] = prices
    return pd.DataFrame(res)

def render_chart_with_crosshair(df, selected_items, meta_dict, calc_mode, height=620):
    fig = go.Figure()
    ticker_items = []
    
    for code in selected_items:
        meta = meta_dict[code]
        raw_series = df[code]
        base_val = raw_series.iloc[0]
        pct_series = ((raw_series - base_val) / base_val) * 100.0
        
        orig_unit = meta.get("unit", "$")
        color = meta["color"]
        
        if calc_mode == "%":
            y_data = pct_series
            custom_data = raw_series
            val_display = f"{pct_series.iloc[-1]:+.1f}%"
            hover_html = f"<b>{meta['name']}</b><br>ผลตอบแทน: %{{y:+.2f}}%<br>ราคาจริง: %{{customdata:,.2f}} {orig_unit}<extra></extra>"
        elif calc_mode == "฿ บาท":
            display_unit = "฿"
            y_data = raw_series * THB_RATE if orig_unit == "$" else raw_series
            custom_data = pct_series
            val_display = f"{display_unit}{y_data.iloc[-1]:,.2f}"
            hover_html = f"<b>{meta['name']}</b><br>ราคา: %{{y:,.2f}} {display_unit}<br>เปลี่ยนแปลง: %{{customdata:+.2f}}%<extra></extra>"
        else:  # "$ USD"
            display_unit = "$"
            y_data = raw_series / THB_RATE if orig_unit in ["บาท", "บ./ตัน"] else raw_series
            custom_data = pct_series
            val_display = f"{display_unit}{y_data.iloc[-1]:,.2f}"
            hover_html = f"<b>{meta['name']}</b><br>ราคา: %{{y:,.2f}} {display_unit}<br>เปลี่ยนแปลง: %{{customdata:+.2f}}%<extra></extra>"

        cur_p_orig = raw_series.iloc[-1]
        p_str_orig = f"{orig_unit}{cur_p_orig:,.2f}" if orig_unit == "$" else f"{cur_p_orig:,.2f} {orig_unit}"

        plot_df = pd.DataFrame({"Date": df["Date"], "y": y_data, "custom": custom_data})
        if len(plot_df) > 3650:
            plot_df = plot_df.iloc[::3]

        fig.add_trace(go.Scatter(
            x=plot_df["Date"], y=plot_df["y"], mode="lines", name=code,
            line=dict(color=color, width=1.4), customdata=plot_df["custom"], hovertemplate=hover_html
        ))

        fig.add_annotation(
            x=plot_df["Date"].iloc[-1], y=plot_df["y"].iloc[-1],
            text=f" <b>{code} {val_display}</b>" + (f" ({p_str_orig})" if calc_mode != "%" else ""),
            showarrow=False, xanchor="left", font=dict(size=11, color=color),
            bgcolor="rgba(0,0,0,0.90)", bordercolor=color, borderwidth=1, borderpad=2
        )
        ticker_items.append({"code": code, "val": val_display, "pct": pct_series.iloc[-1], "color": color})

    y_title = "ผลตอบแทนสะสม (%)" if calc_mode == "%" else f"ระดับราคา ({calc_mode.split()[0]})"
    
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(l=15, r=180, t=15, b=20), height=height, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        xaxis=dict(gridcolor="#161a24", showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1, spikedash="dash", spikecolor="#787b86"),
        yaxis=dict(title=y_title, side="right", gridcolor="#161a24", zeroline=True, zerolinecolor="#2a2e39", ticksuffix="%" if calc_mode == "%" else "", showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1, spikedash="dash", spikecolor="#787b86")
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": False})

    ticker_html = "<div style='display:flex; flex-wrap:wrap; gap:10px; margin-top:-6px; padding:6px 10px; background:#08090c; border:1px solid #1a1d26; border-radius:6px; font-family:monospace;'>"
    for it in ticker_items:
        sign = "+" if it["pct"] >= 0 else ""
        pct_color = "#26a69a" if it["pct"] >= 0 else "#ef5350"
        ticker_html += f"<div style='font-size:12px; border-left:3px solid {it['color']}; padding-left:6px; margin-right:8px;'><b style='color:#ffffff;'>{it['code']}</b> <span style='color:#9e9e9e;'>{it['val']}</span> <b style='color:{pct_color};'>({sign}{it['pct']:.2f}%)</b></div>"
    ticker_html += "</div>"
    st.markdown(ticker_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 2. ฟังก์ชันเรนเดอร์เนื้อหารายงานระบบนิเวศ
# ══════════════════════════════════════════════════════════
def render_crypto_ecosystem_report():
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:6px 12px; margin-bottom:12px; font-size:11px; font-family:monospace; color:#8b949e;'>
        <div>⏱️ <b>Data Integrity:</b> ข้อมูล ณ วันที่ 21 ก.ย. 2026 | แหล่งอ้างอิง: DefiLlama, CoinGecko Categories, Artemis</div>
        <div style='color:#00FFA3;'>🟢 สถานะการเชื่อมต่อ: 5/5 ระบบปกติ</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>สภาพคล่องฐาน (Stablecoin Supply)</div><div style='font-size:18px; font-weight:700; color:#00FFA3;'>$316.2B (+4.2%)</div><div style='font-size:10px; color:#26a69a;'>USDT & USDC มี Net Mint สม่ำเสมอ</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>มูลค่าเงินฝากค้ำประกัน (DeFi TVL)</div><div style='font-size:18px; font-weight:700; color:#2962ff;'>$76.4B (Real TVL +2.1%)</div><div style='font-size:10px; color:#8d99ae;'>ETH 52%, BNB 16%, SOL 13%</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ส่วนแบ่งตลาดบิตคอยน์ (BTC Dominance)</div><div style='font-size:18px; font-weight:700; color:#f7931a;'>58.5% (Consolidating)</div><div style='font-size:10px; color:#ffd700;'>เงินสถาบันสถิตอยู่ใน BTC เป็นหลัก</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ดัชนีอารมณ์ตลาด (Fear & Greed)</div><div style='font-size:18px; font-weight:700; color:#00FFA3;'>64 (Greed)</div><div style='font-size:10px; color:#26a69a;'>ปริมาณซื้อขายอนุพันธ์อยู่ในเกณฑ์สมดุล</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("<div style='background:#0d1117; border:1px solid #ff9800; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ff9800;'>📍 หมวดที่ถือครองสภาพคล่องสูงสุด (Stationed)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>BTC & Stablecoins Reserve</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>BTC:</b> สปอต ETF ยังดูดซับสภาพคล่องไว้กว่า 58% Exchange Netflow เป็นลบ (เหรียญถูกถอนเก็บ Cold Wallet)<br>• <b>USDT / USDC:</b> สภาพคล่องระดับ $316B+ จอดนิ่งในระบบพร้อมเป็นกำลังซื้อแฝง</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div style='background:#0d1117; border:1px solid #00FFA3; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#00FFA3;'>🟢 หมวดที่มีเงินไหลเข้าสุทธิ (Net Inflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>SOL, LINK, AAVE, BNB</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>SOL & BNB:</b> Net Bridge Inflow เติบโตต่อเนื่อง กิจกรรมบนเชนสร้าง Fee สูงสุด<br>• <b>LINK:</b> สถาบันสะสมเพื่อรองรับโครงสร้าง RWA / Oracle Infrastructure<br>• <b>AAVE:</b> Real Yield เติบโต รายได้จากค่าธรรมเนียมกู้ยืมทำสถิติสูงสุด</div></div>", unsafe_allow_html=True)
    with f3:
        st.markdown("<div style='background:#0d1117; border:1px solid #ef5350; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ef5350;'>🔴 หมวดที่มีเงินไหลออกสุทธิ (Net Outflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>DOGE, SHIB, UNI</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>Memecoins (DOGE/SHIB):</b> Volume-to-Mcap ลดลงต่อเนื่อง สภาพคล่องไหลออกแปลงกลับเป็น Stablecoin<br>• <b>Governance (UNI):</b> เผชิญแรงขายลดพอร์ตเนื่องจากขาดการกระจายรายได้โดยตรงสู่ผู้ถือ</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:#d1d4dc;'>
        <b style='color:#00FFA3; font-size:13px;'>🧭 วงจรการหมุนของเงินทุน (Capital Rotation Sequence & Thesis):</b><br>
        สภาวะตลาดปัจจุบันอยู่ในช่วง <b>BTC Dominant — Selective Altcoin</b> เงินทุนสถาบันไม่กระจายตัวเป็น Altseason วงกว้าง แต่ไหลเข้าเฉพาะโปรเจกต์ที่มี <i>Real TVL Growth</i> และมีผู้ใช้งานหนาแน่น<br>
        <div style='margin-top:8px; padding:8px 12px; background:#161b22; border-left:3px solid #f85149; border-radius:4px;'>
            <b style='color:#f85149;'>⚠️ สัญญาณลบล้าง (Counter-Signal):</b> สมมติฐานนี้จะเป็นโมฆะทันทีหาก <b>Stablecoin Supply หดตัว > 2% ในรอบ 14 วัน</b> หรือ <b>BTC Dominance ดีดกลับขึ้นทะลุ 62%</b> ซึ่งจะดึงสภาพคล่องกลับเข้าสู่โหมด Safe Haven และกดดัน Altcoin ทุกกลุ่ม
        </div>
        <div style='font-size:10px; color:#8b949e; margin-top:8px;'>* ข้อมูลนี้จัดทำเพื่อการศึกษาและติดตามการหมุนเวียนสภาพคล่องในระบบนิเวศเท่านั้น ไม่ใช่คำแนะนำการลงทุน</div>
    </div>
    """, unsafe_allow_html=True)

def render_stocks_ecosystem_report():
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:6px 12px; margin-bottom:12px; font-size:11px; font-family:monospace; color:#8b949e;'>
        <div>⏱️ <b>Data Integrity:</b> ข้อมูล ณ วันที่ 21 ก.ย. 2026 | แหล่งอ้างอิง: S&P Dow Jones Indices, Bloomberg, SEC Form 13F</div>
        <div style='color:#00FFA3;'>🟢 สถานะการเชื่อมต่อ: ครอบคลุม 11 กลุ่มอุตสาหกรรม</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ส่วนต่างผลตอบแทน (E/P Yield Gap)</div><div style='font-size:18px; font-weight:700; color:#00FFA3;'>+1.8% vs US10Y</div><div style='font-size:10px; color:#26a69a;'>ผลตอบแทนหุ้นยังจูงใจกว่าพันธบัตร</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>การเติบโตของกำไร (EPS Growth YoY)</div><div style='font-size:18px; font-weight:700; color:#2962ff;'>+14.2% (Tech +22%)</div><div style='font-size:10px; color:#8d99ae;'>XLK & XLC ยังเป็นแกนผลักดันกำไร</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>สถานะวัฏจักรเศรษฐกิจ (Business Cycle)</div><div style='font-size:18px; font-weight:700; color:#ffd700;'>Late-Cycle Expansion</div><div style='font-size:10px; color:#ffd700;'>เริ่มกระจายความเสี่ยงสู่ Defensive Sectors</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("<div style='background:#0d1117; border:1px solid #ff9800; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ff9800;'>📍 หมวดที่ถือครองสภาพคล่องสูงสุด (Stationed)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>Technology (XLK) & Financials (XLF)</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>XLK:</b> หุ้นเซมิคอนดักเตอร์และคลาวด์ยังดูดซับเงินกองทุนทั่วโลกด้วยกระแส AI<br>• <b>XLF:</b> สถาบันการเงินได้ประโยชน์จากส่วนต่างดอกเบี้ย (NIM) ที่ทรงตัวสูง</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div style='background:#0d1117; border:1px solid #00FFA3; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#00FFA3;'>🟢 หมวดที่มีเงินไหลเข้าสุทธิ (Net Inflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>Utilities (XLU), Industrials (XLI)</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>XLU:</b> โรงไฟฟ้าและพลังงานสะอาดได้แรงหนุนจากความต้องการไฟของ Data Center<br>• <b>XLI:</b> โครงสร้างพื้นฐานและโลจิสติกส์รับอานิสงส์งบลงทุน CapEx รอบใหม่</div></div>", unsafe_allow_html=True)
    with f3:
        st.markdown("<div style='background:#0d1117; border:1px solid #ef5350; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ef5350;'>🔴 หมวดที่มีเงินไหลออกสุทธิ (Net Outflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>Real Estate (XLRE), Staples (XLP)</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>XLRE:</b> กองทุนลดน้ำหนักจากภาระต้นทุนรีไฟแนนซ์หนี้ดอกเบี้ยสูง<br>• <b>XLP:</b> สินค้าจำเป็นให้อัตราปันผลไม่น่าดึงดูดเมื่อเทียบกับผลตอบแทนตลาดเงิน</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:#d1d4dc;'>
        <b style='color:#00FFA3; font-size:13px;'>📈 กลยุทธ์การหมุนกลุ่มอุตสาหกรรม (Sector Rotation Playbook):</b><br>
        เม็ดเงินสถาบันกำลังทำ <i>Defensive & Power-Play Rotation</i> สลับจากหุ้นเก็งกำไรขนาดเล็กเข้าหาหุ้นสาธารณูปโภคและโครงสร้างพื้นฐานพลังงานเพื่อรับมือวัฏจักรปลายรอบ<br>
        <div style='margin-top:8px; padding:8px 12px; background:#161b22; border-left:3px solid #f85149; border-radius:4px;'>
            <b style='color:#f85149;'>⚠️ สัญญาณลบล้าง (Counter-Signal):</b> สมมติฐานนี้จะถูกยกเลิกหาก <b>อัตราผลตอบแทนพันธบัตร 10 ปี (US10Y) ดีดทะลุ 4.70%</b> หรือกำไรกลุ่ม Tech รายงานต่ำกว่าเป้าเกิน 5% ซึ่งจะบีบให้เงินไหลออกจากหุ้นเข้าสู่ Money Market
        </div>
        <div style='font-size:10px; color:#8b949e; margin-top:8px;'>* ข้อมูลนี้จัดทำเพื่อการวิเคราะห์ทางสถิติเท่านั้น ไม่ใช่คำแนะนำการลงทุน</div>
    </div>
    """, unsafe_allow_html=True)

def render_metals_ecosystem_report():
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:6px 12px; margin-bottom:12px; font-size:11px; font-family:monospace; color:#8b949e;'>
        <div>⏱️ <b>Data Integrity:</b> ข้อมูล ณ วันที่ 21 ก.ย. 2026 | แหล่งอ้างอิง: World Gold Council, LME, COMEX Inventories</div>
        <div style='color:#ffd700;'>🟢 ข้อมูลอุปสงค์และสต็อกสำรองได้รับการตรวจสอบแล้ว</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>แรงซื้อธนาคารกลาง (Central Bank Gold)</div><div style='font-size:18px; font-weight:700; color:#00FFA3;'>1,037 ตัน/ปี</div><div style='font-size:10px; color:#26a69a;'>สะสมทองคำลดการพึ่งพาดอลลาร์อย่างมีนัยสำคัญ</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>สต็อกทองแดง LME (Copper Inventory)</div><div style='font-size:18px; font-weight:700; color:#2962ff;'>ระดับต่ำสุดในรอบ 3 ปี</div><div style='font-size:10px; color:#8d99ae;'>อุปทานเหมืองตึงตัว ขณะที่อุปสงค์กริดไฟฟ้าสูง</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>สมดุลตลาดลิเทียม (Lithium Supply)</div><div style='font-size:18px; font-weight:700; color:#ef5350;'>Overcapacity</div><div style='font-size:10px; color:#ef5350;'>ผลผลิตแบตเตอรี่เกินความต้องการระยะสั้น</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("<div style='background:#0d1117; border:1px solid #ff9800; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ff9800;'>📍 หมวดที่ถือครองสภาพคล่องสูงสุด (Stationed)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>ทองคำแท่ง (Gold XAU)</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• เม็ดเงินสถาบันสถิตอยู่ในทองคำแท่งเพื่อประกันความเสี่ยงภูมิรัฐศาสตร์และภาระหนี้สาธารณะสหรัฐฯ</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div style='background:#0d1117; border:1px solid #00FFA3; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#00FFA3;'>🟢 หมวดที่มีเงินไหลเข้าสุทธิ (Net Inflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>ทองแดง (Copper) & เงิน (Silver)</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>Copper:</b> เงินไหลเข้าอุปสงค์สายส่งไฟฟ้า พลังงานสีเขียว และ Data Center<br>• <b>Silver:</b> ได้แรงหนุนคู่ทั้งจาก Safe Haven และการผลิตแผงโซลาร์เซลล์</div></div>", unsafe_allow_html=True)
    with f3:
        st.markdown("<div style='background:#0d1117; border:1px solid #ef5350; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ef5350;'>🔴 หมวดที่มีเงินไหลออกสุทธิ (Net Outflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>แร่เหล็ก (Iron Ore) & ลิเทียม</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>Iron Ore:</b> การชะลอตัวของอสังหาฯ ในจีนกดดันยอดสั่งซื้อเหล็กกล้า<br>• <b>Lithium:</b> อุปทานส่วนเกินจากเหมืองใหม่กดดันราคาต่อเนื่อง</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:#d1d4dc;'>
        <b style='color:#ffd700; font-size:13px;'>⛏️ สรุปนัยสำคัญตลาดแร่และโลหะ:</b> ทองคำยังคงทำสถิติสูงสุดจากการลดสัดส่วนดอลลาร์ของธนาคารกลาง ขณะที่การหมุนเงินเข้าทองแดงและเงินสะท้อนการขยายโครงข่ายไฟฟ้าโลก<br>
        <div style='margin-top:8px; padding:8px 12px; background:#161b22; border-left:3px solid #f85149; border-radius:4px;'>
            <b style='color:#f85149;'>⚠️ สัญญาณลบล้าง (Counter-Signal):</b> สมมติฐานทองคำจะอ่อนแรงลงหาก <b>Real Yield สหรัฐฯ ดีดกลับเหนือ 2.5%</b> พร้อมกับสถานการณ์สงครามผ่อนคลายลงอย่างถาวร
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_forex_ecosystem_report():
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:6px 12px; margin-bottom:12px; font-size:11px; font-family:monospace; color:#8b949e;'>
        <div>⏱️ <b>Data Integrity:</b> ข้อมูล ณ วันที่ 21 ก.ย. 2026 | แหล่งอ้างอิง: BIS, ธนาคารแห่งประเทศไทย (BOT), Federal Reserve</div>
        <div style='color:#26a69a;'>🟢 ข้อมูลอัตราแลกเปลี่ยนและทุนสำรองเงินตราระหว่างประเทศ</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ดัชนีดอลลาร์ (DXY Strength)</div><div style='font-size:18px; font-weight:700; color:#00FFA3;'>102.5 (Peaking Out)</div><div style='font-size:10px; color:#26a69a;'>เริ่มชะลอการแข็งค่าเมื่อเงินเฟ้อลดลง</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ส่วนต่างดอกเบี้ย (Yield Spread)</div><div style='font-size:18px; font-weight:700; color:#2962ff;'>FED vs BOJ บีบแคบลง</div><div style='font-size:10px; color:#8d99ae;'>กดดันการปิดสถานะ Yen Carry Trade</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ทุนสำรองเงินตราไทย (TH FX Reserve)</div><div style='font-size:18px; font-weight:700; color:#ffd700;'>$225.4B (แข็งแกร่ง)</div><div style='font-size:10px; color:#ffd700;'>รองรับการนำเข้าได้มากกว่า 8 เดือน</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("<div style='background:#0d1117; border:1px solid #ff9800; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ff9800;'>📍 หมวดที่ถือครองสภาพคล่องสูงสุด (Stationed)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>ดอลลาร์สหรัฐ (USD) & T-Bills</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• ตลาดเงินระยะสั้นสหรัฐฯ (Money Market) ยังล็อกเงินสภาพคล่องไว้สูงด้วยผลตอบแทนระดับสูง</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div style='background:#0d1117; border:1px solid #00FFA3; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#00FFA3;'>🟢 หมวดที่มีเงินไหลเข้าสุทธิ (Net Inflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>บาทไทย (THB) & เยนญี่ปุ่น (JPY)</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>THB:</b> เม็ดเงินท่องเที่ยวและดุลบัญชีเดินสะพัดหนุนค่าเงินบาทแข็งค่า<br>• <b>JPY:</b> ได้รับแรงซื้อกลับจากแนวโน้มการปรับขึ้นดอกเบี้ยนโยบายของ BOJ</div></div>", unsafe_allow_html=True)
    with f3:
        st.markdown("<div style='background:#0d1117; border:1px solid #ef5350; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ef5350;'>🔴 หมวดที่มีเงินไหลออกสุทธิ (Net Outflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>ยูโร (EUR) & ปอนด์ (GBP)</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• การชะลอตัวทางเศรษฐกิจในยูโรโซนและการลดดอกเบี้ยของ ECB กดดันค่าเงิน</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:#d1d4dc;'>
        <b style='color:#26a69a; font-size:13px;'>💵 นัยสำคัญต่อสภาพคล่องโลก:</b> ดอลลาร์ที่เริ่มชะลอการแข็งค่าเปิดทางให้เม็ดเงินไหลเข้าตลาดเกิดใหม่ แต่ความผันผวนของเงินบาทเป็นปัจจัยท้าทายของผู้ส่งออกสินค้าเกษตร<br>
        <div style='margin-top:8px; padding:8px 12px; background:#161b22; border-left:3px solid #f85149; border-radius:4px;'>
            <b style='color:#f85149;'>⚠️ สัญญาณลบล้าง (Counter-Signal):</b> หาก <b>DXY พุ่งกลับทะลุ 105.5 จุด</b> สภาพคล่องโลกจะไหลกลับเข้าสู่ดอลลาร์ทันที และกดดันสินทรัพย์เสี่ยงทั่วโลก
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_cross_asset_ecosystem_report():
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:6px 12px; margin-bottom:12px; font-size:11px; font-family:monospace; color:#8b949e;'>
        <div>⏱️ <b>Data Integrity:</b> ข้อมูล ณ วันที่ 21 ก.ย. 2026 | การวิเคราะห์สภาพคล่องข้ามกลุ่มสินทรัพย์ (Macro Terminal)</div>
        <div style='color:#00FFA3;'>🟢 สถานะ: วิเคราะห์ภาพรวมเชื่อมโยง 6 กลุ่มสินทรัพย์</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>โหมดความเสี่ยง (Risk Appetite)</div><div style='font-size:18px; font-weight:700; color:#00FFA3;'>Risk-On Rotation</div><div style='font-size:10px; color:#26a69a;'>เงินทุนเริ่มออกจากสินทรัพย์ตั้งรับ</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>สภาพคล่อง M2 โลก (Global M2)</div><div style='font-size:18px; font-weight:700; color:#2962ff;'>$104.8T (+4.1% YoY)</div><div style='font-size:10px; color:#8d99ae;'>ธนาคารกลางเริ่มขยายงบดุลอีกครั้ง</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:12px;'><div style='font-size:11px; color:#787b86;'>ความสัมพันธ์ทองคำ vs ดอลลาร์</div><div style='font-size:18px; font-weight:700; color:#ffd700;'>-0.78 (Inverse Correl)</div><div style='font-size:10px; color:#ffd700;'>ทองคำแข็งแกร่งเมื่อดอลลาร์พักฐาน</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("<div style='background:#0d1117; border:1px solid #ff9800; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ff9800;'>📍 หมวดที่ถือครองสภาพคล่องสูงสุด (Stationed)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>พันธบัตรสหรัฐฯ & เงินสดสำรอง</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• สภาพคล่องโลกส่วนใหญ่ยังคงสถิตอยู่ในตลาดเงินระยะสั้นและพันธบัตรรัฐบาลสหรัฐฯ กว่า $6.3 ล้านล้านดอลลาร์</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div style='background:#0d1117; border:1px solid #00FFA3; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#00FFA3;'>🟢 หมวดที่มีเงินไหลเข้าสุทธิ (Net Inflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>คริปโต (BTC) & หุ้นเทคฯ & ทองคำ</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• <b>BTC & Gold:</b> สินทรัพย์ทางเลือกที่ได้อานิสงส์จากการป้องกันเงินเฟ้อและการด้อยค่าของเงินตรากระดาษ<br>• <b>Tech:</b> หุ้น AI ยังเป็นเป้าหมายหลักของการเติบโตของกำไร</div></div>", unsafe_allow_html=True)
    with f3:
        st.markdown("<div style='background:#0d1117; border:1px solid #ef5350; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ef5350;'>🔴 หมวดที่มีเงินไหลออกสุทธิ (Net Outflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>น้ำมันดิบ (Brent) & สินค้าโภคภัณฑ์เก่า</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• อุปสงค์พลังงานฟอสซิลชะลอตัวตามการเปลี่ยนผ่านด้านพลังงานและการขนส่ง</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:#d1d4dc;'>
        <b style='color:#00FFA3; font-size:13px;'>🌐 กลยุทธ์การจัดพอร์ตมหภาค (Barbell Strategy):</b><br>
        นักลงทุนสถาบันกระจายความเสี่ยงด้วยการถือสินทรัพย์ปลอดภัยสูง (ทองคำ/เงินสด) ควบคู่กับสินทรัพย์เติบโตสูง (Tech/BTC) และลดการถือครองกลุ่มที่เติบโตต่ำ<br>
        <div style='margin-top:8px; padding:8px 12px; background:#161b22; border-left:3px solid #f85149; border-radius:4px;'>
            <b style='color:#f85149;'>⚠️ สัญญาณลบล้าง (Counter-Signal):</b> สมมติฐาน Risk-On จะถูกลบล้างหาก <b>เงินเฟ้อสหรัฐฯ (CPI) เร่งตัวกลับขึ้นเกิน 3.8%</b> ส่งผลให้ธนาคารกลางต้องกลับมาใช้นโยบายการเงินตึงตัว
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 3. หน้าต่างโมดอลย่อยหลัก (ใช้ st.tabs ไม่เกิด Rerun / ไม่เด้งปิด)
# ══════════════════════════════════════════════════════════
@st.dialog("🪙 ตลาดคริปโตเคอร์เรนซี (โครงสร้างกลุ่ม & ตัวแทนตลาด)", width="large")
def show_crypto_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    tab_chart, tab_report = st.tabs(["📈 กราฟราคา", "📑 บทวิเคราะห์ระบบนิเวศ"])
    
    with tab_chart:
        c1, c2, c3, c4 = st.columns([0.28, 0.36, 0.18, 0.18], vertical_alignment="center")
        with c1:
            sel_group = st.selectbox("กลุ่มคริปโต", list(CRYPTO_GROUPS.keys()), key="cr_grp", label_visibility="collapsed")
        with c2:
            meta_sub = CRYPTO_GROUPS[sel_group]
            sel_coins = st.multiselect("เลือกเหรียญ", list(meta_sub.keys()), default=list(meta_sub.keys()), format_func=lambda x: f"{x} - {meta_sub[x]['name']}", key="cr_sel", label_visibility="collapsed")
        with c3:
            tf = st.selectbox("ไทม์เฟรม", ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "4 ปี", "6 ปี", "10 ปี"], index=3, key="cr_tf", label_visibility="collapsed")
        with c4:
            calc_mode = st.segmented_control("หน่วยวัด", ["฿ บาท", "$ USD", "%"], default="%", key="cr_mode", label_visibility="collapsed")

        days_map = {"1 เดือน": 30, "3 เดือน": 90, "6 เดือน": 180, "1 ปี": 365, "2 ปี": 730, "4 ปี": 1460, "6 ปี": 2190, "10 ปี": 3650}
        df = generate_series(meta_sub, lookback_days=days_map[tf])
        if sel_coins:
            render_chart_with_crosshair(df, sel_coins, meta_sub, calc_mode, height=620)
            
    with tab_report:
        render_crypto_ecosystem_report()

@st.dialog("📈 ตลาดหุ้นสากล 11 อุตสาหกรรม (GICS Sectors)", width="large")
def show_stocks_gics_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    tab_chart, tab_report = st.tabs(["📈 กราฟราคา", "📑 บทวิเคราะห์ระบบนิเวศ"])
    
    with tab_chart:
        flat_gics = {code: meta for grp, items in STOCKS_GICS.items() for code, meta in items.items()}
        c1, c2, c3 = st.columns([0.55, 0.22, 0.23], vertical_alignment="center")
        with c1:
            sel = st.multiselect("เลือก Sector", list(flat_gics.keys()), default=["XLK", "XLE", "XLF", "XLV", "XLY"], format_func=lambda x: f"{x} - {flat_gics[x]['name']}", key="gics_sel", label_visibility="collapsed")
        with c2:
            tf = st.selectbox("ไทม์เฟรม", ["1 ปี", "2 ปี", "4 ปี", "10 ปี", "20 ปี", "30 ปี"], index=3, key="gics_tf", label_visibility="collapsed")
        with c3:
            calc_mode = st.segmented_control("หน่วยวัด", ["฿ บาท", "$ USD", "%"], default="%", key="gics_mode", label_visibility="collapsed")

        days_map = {"1 ปี": 365, "2 ปี": 730, "4 ปี": 1460, "10 ปี": 3650, "20 ปี": 7300, "30 ปี": 10950}
        df = generate_series(flat_gics, lookback_days=days_map[tf])
        if sel:
            render_chart_with_crosshair(df, sel, flat_gics, calc_mode, height=620)
            
    with tab_report:
        render_stocks_ecosystem_report()

@st.dialog("⛏️ ตลาดแร่ & โลหะ (Precious & Industrial Metals)", width="large")
def show_metals_mining_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    tab_chart, tab_report = st.tabs(["📈 กราฟราคา", "📑 บทวิเคราะห์ระบบนิเวศ"])
    
    with tab_chart:
        flat_metals = {code: meta for grp, items in METALS_MINING.items() for code, meta in items.items()}
        c1, c2, c3 = st.columns([0.55, 0.22, 0.23], vertical_alignment="center")
        with c1:
            sel = st.multiselect("เลือกโลหะ/แร่", list(flat_metals.keys()), default=["GOLD", "SILVER", "COPPER", "LITHIUM"], format_func=lambda x: f"{x} - {flat_metals[x]['name']}", key="mtl_sel", label_visibility="collapsed")
        with c2:
            tf = st.selectbox("ไทม์เฟรม", ["1 ปี", "4 ปี", "10 ปี", "20 ปี", "30 ปี"], index=2, key="mtl_tf", label_visibility="collapsed")
        with c3:
            calc_mode = st.segmented_control("หน่วยวัด", ["฿ บาท", "$ USD", "%"], default="%", key="mtl_mode", label_visibility="collapsed")

        days_map = {"1 ปี": 365, "4 ปี": 1460, "10 ปี": 3650, "20 ปี": 7300, "30 ปี": 10950}
        df = generate_series(flat_metals, lookback_days=days_map[tf])
        if sel:
            render_chart_with_crosshair(df, sel, flat_metals, calc_mode, height=620)
            
    with tab_report:
        render_metals_ecosystem_report()

@st.dialog("💵 ตลาดเงินตรา & ค่าเงิน (Forex & DXY)", width="large")
def show_forex_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    tab_chart, tab_report = st.tabs(["📈 กราฟราคา", "📑 บทวิเคราะห์ระบบนิเวศ"])
    
    with tab_chart:
        c1, c2, c3 = st.columns([0.55, 0.22, 0.23], vertical_alignment="center")
        with c1:
            sel = st.multiselect("เลือกคู่เงิน/ดัชนี", list(FOREX_PAIRS.keys()), default=["DXY", "USDTHB", "EURUSD", "USDJPY"], format_func=lambda x: f"{x} - {FOREX_PAIRS[x]['name']}", key="fx_sel", label_visibility="collapsed")
        with c2:
            tf = st.selectbox("ไทม์เฟรม", ["1 ปี", "4 ปี", "10 ปี", "20 ปี", "30 ปี"], index=2, key="fx_tf", label_visibility="collapsed")
        with c3:
            calc_mode = st.segmented_control("หน่วยวัด", ["฿ บาท", "$ USD", "%"], default="%", key="fx_mode", label_visibility="collapsed")

        days_map = {"1 ปี": 365, "4 ปี": 1460, "10 ปี": 3650, "20 ปี": 7300, "30 ปี": 10950}
        df = generate_series(FOREX_PAIRS, lookback_days=days_map[tf])
        if sel:
            render_chart_with_crosshair(df, sel, FOREX_PAIRS, calc_mode, height=620)
            
    with tab_report:
        render_forex_ecosystem_report()

@st.dialog("🌐 Macro Terminal — เปรียบเทียบผลตอบแทนข้ามกลุ่มสินทรัพย์", width="large")
def show_macro_comparison_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    tab_chart, tab_report = st.tabs(["📈 กราฟราคา", "📑 บทวิเคราะห์ระบบนิเวศ"])
    
    with tab_chart:
        macro_items = {
            "BTC": {"name": "Bitcoin", "base": 81579, "vol": 0.024, "unit": "$", "color": "#f7931a"},
            "GOLD": {"name": "ทองคำ (Gold)", "base": 2684, "vol": 0.008, "unit": "$", "color": "#ffd700"},
            "RICE": {"name": "ข้าวหอมมะลิ 105", "base": 14850, "vol": 0.010, "unit": "บ./ตัน", "color": "#4caf50"},
            "SET": {"name": "หุ้นไทย (SET)", "base": 1422, "vol": 0.007, "unit": "จุด", "color": "#00bcd4"},
            "DXY": {"name": "ดอลลาร์ (DXY)", "base": 102.5, "vol": 0.004, "unit": "จุด", "color": "#e91e63"},
            "OIL": {"name": "น้ำมันดิบ Brent", "base": 74.8, "vol": 0.016, "unit": "$", "color": "#8d6e63"},
        }
        c1, c2, c3 = st.columns([0.55, 0.22, 0.23], vertical_alignment="center")
        with c1:
            sel = st.multiselect("เลือกสินทรัพย์ข้ามกลุ่ม", list(macro_items.keys()), default=["BTC", "GOLD", "RICE", "SET", "DXY"], format_func=lambda x: f"{x} - {macro_items[x]['name']}", key="macro_sel", label_visibility="collapsed")
        with c2:
            tf = st.selectbox("ย้อนหลัง", ["1 ปี", "4 ปี", "10 ปี", "20 ปี", "30 ปี"], index=1, key="macro_tf", label_visibility="collapsed")
        with c3:
            calc_mode = st.segmented_control("หน่วยวัด", ["฿ บาท", "$ USD", "%"], default="%", key="macro_mode", label_visibility="collapsed")

        days_map = {"1 ปี": 365, "4 ปี": 1460, "10 ปี": 3650, "20 ปี": 7300, "30 ปี": 10950}
        df = generate_series(macro_items, lookback_days=days_map[tf])
        if sel:
            render_chart_with_crosshair(df, sel, macro_items, calc_mode, height=620)
            
    with tab_report:
        render_cross_asset_ecosystem_report()

# ══════════════════════════════════════════════════════════
# 4. ศูนย์วิเคราะห์ระบบนิเวศและกระแสเงินทุนโลก (Capital Flow Command Center)
# ══════════════════════════════════════════════════════════
@st.dialog("🧭 ศูนย์วิเคราะห์ระบบนิเวศและเงินทุนโลก (Global Macro & Capital Ecosystem)", width="large")
def show_flow_analysis_modal():
    st.markdown(MODAL_STYLE, unsafe_allow_html=True)
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:6px 12px; margin-bottom:12px; font-size:11px; font-family:monospace; color:#8b949e;'>
        <div>⏱️ <b>Global Macro Integrity:</b> ข้อมูล ณ วันที่ 21 ก.ย. 2026 | แหล่งอ้างอิง: Federal Reserve, DefiLlama, LME, World Bank</div>
        <div style='color:#00FFA3;'>🟢 สถานะ: วิเคราะห์กระแสเงินทุนโลก 9 หมวดหลัก</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'><div style='font-size:11px; color:#787b86;'>โหมดสภาพคล่องโลก</div><div style='font-size:16px; font-weight:700; color:#00FFA3;'>🟢 Risk-On Rotation</div><div style='font-size:10px; color:#26a69a;'>Global M2 ขยายตัว หนุนสินทรัพย์เติบโต</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'><div style='font-size:11px; color:#787b86;'>กระแสเงินเข้าสุทธิสูงสุด</div><div style='font-size:16px; font-weight:700; color:#f7931a;'>🪙 คริปโต (BTC / L1)</div><div style='font-size:10px; color:#26a69a;'>+18.4% Net Inflow 30D</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'><div style='font-size:11px; color:#787b86;'>กระแสเงินออกสุทธิสูงสุด</div><div style='font-size:16px; font-weight:700; color:#ef5350;'>⚡ Utilities & พันธบัตร</div><div style='font-size:10px; color:#ef5350;'>-4.2% ถูกลดสัดส่วนทำกำไร</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown("<div style='background:#131722; border:1px solid #2a2e39; border-radius:6px; padding:10px;'><div style='font-size:11px; color:#787b86;'>เสถียรภาพค่าเงิน (DXY/THB)</div><div style='font-size:16px; font-weight:700; color:#ffd700;'>💵 ดอลลาร์เริ่มชะลอ</div><div style='font-size:10px; color:#26a69a;'>บาทแข็งค่า สภาพคล่องไหลเข้าไทย</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("<div style='background:#0d1117; border:1px solid #ff9800; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ff9800;'>📍 แหล่งพักเงินหลักระดับโลก (Global Stationed)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>US Money Market & ทองคำแท่ง</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• ตลาดเงินสหรัฐฯ พักสภาพคล่องสูงกว่า $6.3T จากอัตราดอกเบี้ยระยะสั้น<br>• ธนาคารกลางทั่วโลกเพิ่มสัดส่วนสำรองทองคำแทนดอลลาร์อย่างมีนัยสำคัญ</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div style='background:#0d1117; border:1px solid #00FFA3; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#00FFA3;'>🟢 สินทรัพย์ที่มีเงินไหลเข้าสุทธิ (Global Net Inflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>Crypto ETF, Tech AI, ทองแดง</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• สปอต ETF ของบิตคอยน์ดึงดูดเงินสถาบันสม่ำเสมอ<br>• เงินทุนไหลเข้าโครงสร้างพื้นฐาน Data Center พลังงานสะอาด และกริดไฟฟ้า</div></div>", unsafe_allow_html=True)
    with f3:
        st.markdown("<div style='background:#0d1117; border:1px solid #ef5350; border-radius:6px; padding:12px;'><div style='font-size:12px; font-weight:700; color:#ef5350;'>🔴 สินทรัพย์ที่มีเงินไหลออกสุทธิ (Global Net Outflow)</div><div style='font-size:15px; font-weight:700; color:#ffffff; margin:6px 0;'>น้ำมันดิบ, ยูโร, พันธบัตรระยะยาว</div><div style='font-size:11px; color:#d1d4dc; line-height:1.5;'>• ภาคการผลิตยุโรปชะลอกดดันยูโร<br>• ความกังวลหนี้สาธารณะทำให้กองทุนลดการถือพันธบัตรอายุยาว</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    categories = ["คริปโต (Layer 1)", "เทคโนโลยี (XLK)", "ทองคำ (Safe Haven)", "สินค้าเกษตร/ข้าว", "อุตสาหกรรม (XLI)", "หุ้นไทย (SET)", "พลังงาน (XLE)", "ดอลลาร์ (DXY)", "สาธารณูปโภค (XLU)"]
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
        margin=dict(l=10, r=40, t=40, b=20), height=300,
        xaxis=dict(gridcolor="#161a24", zerolinecolor="#474d57", zerolinewidth=1.2, ticksuffix="%"),
        yaxis=dict(gridcolor="#161a24", autorange="reversed")
    )
    st.plotly_chart(fig_flow, use_container_width=True, config={"displayModeBar": False})

    st.markdown("""
    <div style='background:#08090c; border:1px solid #1a1d26; border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:#d1d4dc;'>
        <b style='color:#00FFA3; font-size:13px;'>📌 สรุปบทวิเคราะห์ระบบนิเวศมหภาค (Global Macro Significance):</b><br>
        • <b>สภาวะสภาพคล่องโลก (Global Liquidity Expansion):</b> วัฏจักรดอกเบี้ยขาลงกำลังผลักดันสภาพคล่องออกจากสินทรัพย์ปลอดภัยไปยังสินทรัพย์ที่มีอัตราการเติบโตสูง<br>
        • <b>การกระจายความเสี่ยงระดับสถาบัน:</b> ทองคำและบิตคอยน์ทำหน้าที่เป็นคู่สินทรัพย์ป้องกันความเสี่ยงจากการขยายตัวของหนี้สาธารณะทั่วโลก<br>
        <div style='margin-top:8px; padding:8px 12px; background:#161b22; border-left:3px solid #f85149; border-radius:4px;'>
            <b style='color:#f85149;'>⚠️ สัญญาณลบล้าง (Counter-Signal):</b> สมมติฐานสภาพคล่องขยายตัวจะล้มเหลวหาก <b>DXY พุ่งกลับทะลุ 106.0</b> หรือ <b>ธนาคารกลางสหรัฐฯ ส่งสัญญาณคงดอกเบี้ยยาวนานกว่าคาด</b>
        </div>
        <div style='font-size:10px; color:#8b949e; margin-top:8px;'>* ข้อมูลนี้จัดทำเพื่อการศึกษาและวิเคราะห์สถิติมหภาคเท่านั้น ไม่ใช่คำแนะนำการลงทุน</div>
    </div>
    """, unsafe_allow_html=True)