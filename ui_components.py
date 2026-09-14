import streamlit as st
import streamlit.components.v1 as components

def render_tv_clickable_tabs(open_tabs, active_sym, quotes_dict, key="tv_tabs_bar"):
    """
    open_tabs: list ของ symbols เช่น ['BTC_THB', 'ETH_THB']
    active_sym: symbol ที่กำลังเปิดดูอยู่
    quotes_dict: dict เก็บราคา เช่น {'BTC_THB': {'price': 2590000, 'change': 0.8}}
    """
    tabs_html_items = []
    
    for sym in open_tabs:
        is_active = (sym == active_sym)
        # ตัด underscore ออกตอนแสดงผล และดึงชื่อเหรียญหลักทำโลโก้
        base_asset = sym.split("_")[0].lower().replace("usdt", "")
        logo_url = f"https://assets.coincap.io/assets/icons/{base_asset}@2x.png"
        
        q = quotes_dict.get(sym, {"price": 0.0, "change": 0.0})
        p = q.get("price", 0.0)
        chg = q.get("change", 0.0)
        
        cls = "up" if chg >= 0 else "down"
        arr = "▲" if chg >= 0 else "▼"
        sign = "+" if chg >= 0 else ""
        p_str = f"{p:,.4f}" if p < 10 else f"{p:,.2f}"
        disp_sym = sym.replace("_", "")

        tab_markup = f"""
        <div class="tv-tab {'active' if is_active else ''}" onclick="selectTab('{sym}')">
          <img class="tv-logo" src="{logo_url}">
          <span class="tv-sym">{disp_sym}</span>
          <span class="tv-price {cls}">{arr} {p_str}</span>
          <span class="tv-chg {cls}">{sign}{chg:.2f}%</span>
          <span class="tv-x" onclick="event.stopPropagation(); closeTab('{sym}')">×</span>
        </div>
        """
        tabs_html_items.append(tab_markup)

    full_component = f"""
    <style>
      body {{ margin:0; padding:0; background:transparent; font-family:-apple-system,'Segoe UI',sans-serif; }}
      .tv-tabs {{ display:inline-flex; align-items:center; gap:2px; background:#131722; border-radius:6px; padding:2px; user-select:none; }}
      .tv-tab {{ display:inline-flex; align-items:center; gap:6px; padding:5px 8px; background:#1e222d; border-radius:4px; cursor:pointer; font-size:12px; transition:0.12s; white-space:nowrap; border:1px solid transparent; }}
      .tv-tab:hover {{ background:#2a2e39; }}
      .tv-tab.active {{ background:#2a2e39; border-color:#2962ff; }}
      .tv-logo {{ width:14px; height:14px; border-radius:50%; }}
      .tv-sym {{ color:#d1d4dc; font-weight:600; font-size:12px; }}
      .tv-price {{ font-weight:500; font-size:12px; }}
      .tv-chg {{ font-weight:500; font-size:11px; }}
      .up {{ color:#26a69a; }} .down {{ color:#ef5350; }}
      .tv-x {{ color:#787b86; font-size:14px; margin-left:3px; padding:0 3px; border-radius:3px; }}
      .tv-x:hover {{ background:#363a45; color:#ffffff; }}
      .tv-plus {{ color:#787b86; font-size:16px; padding:2px 8px; cursor:pointer; display:inline-flex; align-items:center; }}
      .tv-plus:hover {{ color:#d1d4dc; }}
    </style>

    <div class="tv-tabs">
      {''.join(tabs_html_items)}
      <span class="tv-plus" onclick="addTab()">+</span>
    </div>

    <script>
      function selectTab(sym) {{
        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: {{action: 'switch', sym: sym}}}}, '*');
      }}
      function closeTab(sym) {{
        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: {{action: 'close', sym: sym}}}}, '*');
      }}
      function addTab() {{
        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: {{action: 'add'}}}}, '*');
      }}
    </script>
    """
    
    # ดักจับค่าการคลิกกลับมายัง Streamlit
    action_data = components.html(full_component, height=36)
    return action_data
# ──────────────────────────── UI CARDS, GAUGES & MODALS ────────────────────────────
import datetime
import pandas as pd
import streamlit as st
from utils import fmt_price, fmt_chg, fmt_vol

UP, DOWN = "#26a69a", "#ef5350"

COMMODITY_NAMES = {
    "GC=F": "ทองคำ (Gold)", "SI=F": "เงิน (Silver)", "HG=F": "ทองแดง (Copper)",
    "PL=F": "แพลทินัม (Platinum)", "PA=F": "แพลเลเดียม (Palladium)",
    "CL=F": "น้ำมันดิบ WTI", "BZ=F": "น้ำมันดิบ Brent", "NG=F": "ก๊าซธรรมชาติ",
    "RB=F": "น้ำมันเบนซิน", "ZC=F": "ข้าวโพด", "ZW=F": "ข้าวสาลี",
    "ZS=F": "ถั่วเหลือง", "RR=F": "ข้าวเปลือก", "KC=F": "กาแฟ",
    "CC=F": "โกโก้", "SB=F": "น้ำตาล", "CT=F": "ฝ้าย"
}

FOREX_NAMES = {
    "USDTHB=X": "ดอลลาร์ / บาท", "EURTHB=X": "ยูโร / บาท", "JPYTHB=X": "เยน / บาท",
    "GBPTHB=X": "ปอนด์ / บาท", "CNYTHB=X": "หยวน / บาท", "SGDTHB=X": "ดอลลาร์สิงคโปร์ / บาท",
    "EURUSD=X": "EUR / USD", "GBPUSD=X": "GBP / USD", "USDJPY=X": "USD / JPY",
    "USDCHF=X": "USD / CHF", "AUDUSD=X": "AUD / USD", "USDCAD=X": "USD / CAD", "NZDUSD=X": "NZD / USD"
}

CHINA_STOCK_NAMES = {
    "002594.SZ": "BYD (บีวายดี EV)", "300750.SZ": "CATL (แบตเตอรี่ EV)",
    "9866.HK":   "NIO (นีโอ)", "9868.HK":   "XPeng (เสี่ยวเผิง)",
    "2015.HK":   "Li Auto (ลี่ออโต้)", "1810.HK":   "Xiaomi (เสียวหมี่)",
    "600104.SS": "SAIC Motor", "601633.SS": "Great Wall Motor",
    "0700.HK":   "Tencent (เทนเซ็นต์)", "9988.HK":   "Alibaba (อาลีบาบา)",
    "3690.HK":   "Meituan (เหม่ยถวน)", "9618.HK":   "JD.com",
    "9999.HK":   "NetEase", "9888.HK":   "Baidu (ไป่ตู้ AI)",
    "688981.SS": "SMIC (ชิปเบอร์ 1)", "601138.SS": "Foxconn Industrial",
    "002415.SZ": "Hikvision (กล้อง AI)", "600519.SS": "Kweichow Moutai (เหมาไถ)",
    "000858.SZ": "Wuliangye (อู่เหลียงเย่)", "000333.SZ": "Midea Group",
    "000651.SZ": "Gree Electric", "601398.SS": "ICBC ธนาคารจีน",
    "601939.SS": "CCB ธนาคารก่อสร้าง", "601288.SS": "ABC ธนาคารเกษตร",
    "601988.SS": "Bank of China", "600036.SS": "China Merchants Bank",
    "601318.SS": "Ping An Insurance", "601857.SS": "PetroChina",
    "600028.SS": "Sinopec", "601088.SS": "China Shenhua",
    "600900.SS": "Yangtze Power", "601899.SS": "Zijin Mining",
    "600276.SS": "Hengrui Medicine", "300760.SZ": "Mindray Bio-Medical"
}

def render_gauge_svg(title: str, label: str, color: str, angle: float, buy: int, neutral: int, sell: int, size: int = 140) -> str:
    w, h = 150, 82
    cx, cy, r = 75, 74, 54
    return f"""<div style="text-align:center; font-family:-apple-system,BlinkMacSystemFont,sans-serif; flex:1; min-width:90px;">
        <div style="font-size:10px; font-weight:700; color:#9aa0a6; margin-bottom:1px;">{title}</div>
        <svg width="100%" height="{h}" viewBox="0 0 {w} {h}" style="max-width:{size}px; margin:0 auto; display:block; overflow:visible;">
            <path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="#1E1E1E" stroke-width="7" stroke-linecap="round"/>
            <path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx - r*0.3} {cy - r*0.9}" fill="none" stroke="{DOWN}" stroke-width="7" stroke-linecap="round"/>
            <path d="M {cx + r*0.3} {cy - r*0.9} A {r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{UP}" stroke-width="7" stroke-linecap="round"/>
            <g transform="translate({cx}, {cy}) rotate({angle})">
                <line x1="0" y1="0" x2="0" y2="{-r + 4}" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round"/>
                <circle cx="0" cy="0" r="3.5" fill="#FFFFFF"/>
            </g>
        </svg>
        <div style="font-size:11px; font-weight:700; color:{color}; margin-top:-2px;">{label}</div>
        <div style="display:flex; justify-content:center; gap:6px; font-size:9px; color:#787b86; margin-top:2px; font-family:monospace;">
            <span>ขาย <b>{sell}</b></span><span>กลาง <b>{neutral}</b></span><span>ซื้อ <b>{buy}</b></span>
        </div>
    </div>"""

def render_3_gauges_html(tech: dict, compact: bool = True) -> str:
    if not tech or "summary" not in tech or "osc" not in tech or "ma" not in tech: return ""
    o, s, m = tech["osc"], tech["summary"], tech["ma"]
    if compact:
        g_sum = render_gauge_svg("ภาพรวม (Summary)", s["label"], s["color"], s["angle"], s["buy"], s["neutral"], s["sell"], size=150)
        g_osc = render_gauge_svg("Oscillators", o["label"], o["color"], o["angle"], o["buy"], o["neutral"], o["sell"], size=120)
        g_ma = render_gauge_svg("ค่าเฉลี่ยเคลื่อนที่", m["label"], m["color"], m["angle"], m["buy"], m["neutral"], m["sell"], size=120)
        return f"""<div style="background:#0D0D0D; border:1px solid #1E1E1E; border-radius:6px; padding:8px 4px; margin:6px 0;">
            <div style="display:flex; justify-content:center; margin-bottom:8px;">{g_sum}</div>
            <div style="display:flex; justify-content:space-between; gap:4px;">{g_osc}{g_ma}</div>
        </div>"""
    else:
        g_osc = render_gauge_svg("Oscillators", o["label"], o["color"], o["angle"], o["buy"], o["neutral"], o["sell"], size=140)
        g_sum = render_gauge_svg("ภาพรวม (Summary)", s["label"], s["color"], s["angle"], s["buy"], s["neutral"], s["sell"], size=165)
        g_ma = render_gauge_svg("ค่าเฉลี่ยเคลื่อนที่", m["label"], m["color"], m["angle"], m["buy"], m["neutral"], m["sell"], size=140)
        return f"""<div style="display:flex; justify-content:space-around; align-items:flex-end; background:#0D0D0D; border:1px solid #1E1E1E; border-radius:6px; padding:12px 6px; margin:8px 0;">
            {g_osc} {g_sum} {g_ma}
        </div>"""

def fetch_seasonality_svg(df: pd.DataFrame) -> str:
    try:
        if df is None or df.empty or len(df) < 60: return ""

        df = df.copy()
        df["dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df["year"] = df["dt"].dt.year
        df["doy"] = df["dt"].dt.dayofyear

        years_target = [2024, 2025, 2026]
        colors = {2024: "#f59e0b", 2025: "#10b981", 2026: "#3b82f6"}
        year_data = {}
        all_pcts = [0.0]

        for yr in years_target:
            ydf = df[df["year"] == yr].sort_values("time")
            if not ydf.empty and len(ydf) >= 5:
                base_close = float(ydf.iloc[0]["close"])
                if base_close > 0:
                    pts = []
                    for _, row in ydf.iterrows():
                        pct = ((float(row["close"]) / base_close) - 1.0) * 100.0
                        pts.append((int(row["doy"]), pct))
                        all_pcts.append(pct)
                    year_data[yr] = {"points": pts, "last_pct": pts[-1][1]}

        if not year_data: return ""

        min_pct = min(all_pcts) - 5.0
        max_pct = max(all_pcts) + 5.0
        if min_pct > -10.0: min_pct = -10.0
        if max_pct < 10.0:  max_pct = 10.0
        span = max_pct - min_pct if max_pct != min_pct else 1.0

        w, h = 540, 160
        pad_l, pad_r, pad_t, pad_b = 15, 20, 15, 20
        gw, gh = w - pad_l - pad_r, h - pad_t - pad_b

        def to_xy(doy, pct):
            x = pad_l + (min(365, max(1, doy)) - 1) / 365.0 * gw
            y = pad_t + (max_pct - pct) / span * gh
            return round(x, 1), round(y, 1)

        zero_y = round(pad_t + (max_pct - 0.0) / span * gh, 1)
        svg_lines = [f'<line x1="{pad_l}" y1="{zero_y}" x2="{w - pad_r}" y2="{zero_y}" stroke="#333333" stroke-width="1.2" stroke-dasharray="4,4"/>']

        for m_doy in [1, 91, 182, 274]:
            gx = round(pad_l + (m_doy - 1) / 365.0 * gw, 1)
            svg_lines.append(f'<line x1="{gx}" y1="{pad_t}" x2="{gx}" y2="{h - pad_b}" stroke="#1E1E1E" stroke-width="1.2" stroke-dasharray="3,3"/>')

        legend_pills = []
        for yr in sorted(year_data.keys()):
            col = colors.get(yr, "#D1D4DC")
            pts = year_data[yr]["points"]
            d_path = [f"{'M' if i == 0 else 'L'} {to_xy(doy, p)[0]} {to_xy(doy, p)[1]}" for i, (doy, p) in enumerate(pts)]
            svg_lines.append(f'<path d="{" ".join(d_path)}" fill="none" stroke="{col}" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/>')
            lx, ly = to_xy(pts[-1][0], pts[-1][1])
            svg_lines.append(f'<circle cx="{lx}" cy="{ly}" r="3.5" fill="{col}"/>')
            legend_pills.append(f'<span style="display:inline-flex; align-items:center; gap:4px; margin:0 5px; font-size:10px; font-family:monospace;"><span style="color:{col};">●</span> {yr}</span>')

        svg_content = "\n".join(svg_lines)
        return f"""<div style="background:#0A0A0A; border:1px solid #1E1E1E; border-radius:6px; padding:6px 8px; margin-bottom:6px; width:100%; box-sizing:border-box;">
            <svg width="100%" height="{h}" viewBox="0 0 {w} {h}" style="overflow:visible; display:block;">
                {svg_content}
                <text x="{pad_l}" y="{h - 4}" fill="#666" font-size="9" font-family="sans-serif">ม.ค.</text>
                <text x="{pad_l + gw*0.33}" y="{h - 4}" fill="#666" font-size="9" font-family="sans-serif">พ.ค.</text>
                <text x="{pad_l + gw*0.66}" y="{h - 4}" fill="#666" font-size="9" font-family="sans-serif">ก.ย.</text>
            </svg>
            <div style="display:flex; justify-content:center; margin-top:4px;">{''.join(legend_pills)}</div>
        </div>"""
    except Exception:
        return ""

def render_tv_quote_card_html(tk: dict, an: dict, symbol: str, label_name: str, seasonality_html: str = "", gauges_html: str = "") -> str:
    if not tk: return "<div style='color:#787b86; padding:10px;'>กำลังเชื่อมต่อข้อมูลราคา...</div>"
    
    p_val = float(tk.get("price", 0))
    day_low = tk.get("low", 0)
    if day_low <= 0:
        day_low = p_val * 0.98
    day_low = float(day_low)

    day_high = tk.get("high", 0)
    if day_high <= 0:
        day_high = p_val * 1.02
    day_high = float(day_high)
    span_day = day_high - day_low
    ratio_day = max(0.0, min(100.0, ((p_val - day_low) / span_day * 100.0))) if span_day > 0 else 50.0

    low_52w = an.get("low_52w", day_low * 0.8) if an else day_low * 0.8
    high_52w = an.get("high_52w", day_high * 1.2) if an else day_high * 1.2
    low_52w = float(low_52w)
    high_52w = float(high_52w)
    span_52w = high_52w - low_52w
    ratio_52w = max(0.0, min(100.0, ((p_val - low_52w) / span_52w * 100.0))) if span_52w > 0 else 50.0

    vol_24h_str = fmt_vol(tk.get("vol", 0))
    vol_30d_str = fmt_vol(an.get("vol_30d_avg", 0)) if an else "-"

    def p_box(lbl, val):
        col = UP if val >= 0 else DOWN
        bg = "rgba(38, 166, 154, 0.12)" if val >= 0 else "rgba(239, 83, 80, 0.12)"
        s = "+" if val >= 0 else ""
        return f"""<div style="background:{bg}; border:1px solid {col}40; border-radius:4px; padding:6px 2px; text-align:center;">
<div style="font-size:11px; font-weight:700; color:{col}; font-family:monospace;">{s}{val:.2f}%</div>
<div style="font-size:9px; color:#787b86; margin-top:2px;">{lbl}</div></div>"""

    grid_perf = ""
    if an:
        grid_perf = f"""<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:4px; margin-bottom:12px;">
{p_box('1W', an.get('1W',0))}{p_box('1M', an.get('1M',0))}{p_box('3M', an.get('3M',0))}
{p_box('6M', an.get('6M',0))}{p_box('YTD', an.get('YTD',0))}{p_box('1Y', an.get('1Y',0))}</div>"""
    else:
        grid_perf = """<div style="font-size:10px; color:#787b86; padding:6px 0;">ไม่มีข้อมูลย้อนหลังเพียงพอ</div>"""

    return f"""<div class="scrollable-market-card">
<div style="background-color:#0A0A0A; border-radius:6px; padding:10px; color:#D1D4DC; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; border:1px solid #1E1E1E;">

<!-- 1. ช่วงราคา 24 ชม. & 52 สัปดาห์ -->
<div style="margin-bottom:12px;">
    <div style="display:flex; justify-content:space-between; font-size:11px; font-family:monospace; color:#D1D4DC; margin-bottom:4px;">
        <span>{fmt_price(day_low)}</span>
        <span style="color:#787b86; font-size:10px; font-family:sans-serif;">ช่วงราคา 24 ชม.</span>
        <span>{fmt_price(day_high)}</span>
    </div>
    <div style="position:relative; width:100%; height:4px; background:#1E1E1E; border-radius:2px;">
        <div style="position:absolute; left:0; width:{ratio_day}%; height:100%; background:#26a69a; border-radius:2px;"></div>
        <div style="position:absolute; left:{ratio_day}%; top:5px; transform:translateX(-50%); font-size:8px; color:#00FFA3; line-height:1;">▲</div>
    </div>
</div>

<div style="margin-bottom:16px;">
    <div style="display:flex; justify-content:space-between; font-size:11px; font-family:monospace; color:#D1D4DC; margin-bottom:4px;">
        <span>{fmt_price(low_52w)}</span>
        <span style="color:#787b86; font-size:10px; font-family:sans-serif;">ช่วงราคา 52 สัปดาห์</span>
        <span>{fmt_price(high_52w)}</span>
    </div>
    <div style="position:relative; width:100%; height:4px; background:#1E1E1E; border-radius:2px;">
        <div style="position:absolute; left:0; width:{ratio_52w}%; height:100%; background:#ffbd2e; border-radius:2px;"></div>
        <div style="position:absolute; left:{ratio_52w}%; top:5px; transform:translateX(-50%); font-size:8px; color:#ffbd2e; line-height:1;">▲</div>
    </div>
</div>

<!-- 2. ปริมาณการซื้อขาย -->
<div style="display:flex; justify-content:space-between; font-size:11px; padding:2px 0;">
    <span style="color:#787b86;">ปริมาณการซื้อขาย 24h</span>
    <span style="color:#fff; font-family:monospace; font-weight:600;">{vol_24h_str}</span>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; padding:2px 0; margin-bottom:12px;">
    <span style="color:#787b86;">ปริมาณเฉลี่ย (30 วัน)</span>
    <span style="color:#fff; font-family:monospace; font-weight:600;">{vol_30d_str}</span>
</div>

<!-- 3. Performance Matrix 6 ช่อง -->
<div style="font-size:11px; font-weight:700; color:#00FFA3; margin-bottom:6px;">ผลการดำเนินงาน (Performance Matrix)</div>
{grid_perf}

<!-- 4. หน้าปัดเลขไมล์สัญญาณเทคนิค (Technical Gauges) -->
<div style="font-size:11px; font-weight:700; color:#00FFA3; margin-bottom:4px; border-top:1px solid #1E1E1E; padding-top:8px;">หน้าปัดสัญญาณเทคนิค (Technical Gauges)</div>
{gauges_html}

<!-- 5. กราฟสถิติฤดูกาล (Seasonality) -->
<div style="font-size:11px; font-weight:700; color:#00FFA3; margin-top:10px; margin-bottom:4px;">สถิติฤดูกาลผลตอบแทน (Seasonality)</div>
{seasonality_html}

</div></div>"""

def render_tv_quote_card(tk: dict, an: dict, symbol: str, label_name: str, seasonality_html: str = "", gauges_html: str = ""):
    card_html = render_tv_quote_card_html(tk, an, symbol, label_name, seasonality_html, gauges_html)
    st.markdown(card_html, unsafe_allow_html=True)

def render_fibonacci_modal_content(fib, ext, fib_zone, fib_tp, last_close):
    if not fib or "levels" not in fib:
        st.info("ข้อมูลประวัติราคายังไม่เพียงพอในการสร้าง Fibonacci Swing")
        return

    is_uptrend = fib.get("uptrend", True)
    trend_title = "แนวโน้ม: ขาขึ้น ▲ (วัดจาก Low ไป High)" if is_uptrend else "แนวโน้ม: ขาลง ▼ (วัดจาก High ไป Low)"
    trend_badge_color = UP if is_uptrend else DOWN

    st.markdown(f"""<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
        <span style="font-size:16px; font-weight:700; color:#fff;">{trend_title}</span>
        <span style="background:{trend_badge_color}20; color:{trend_badge_color}; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold;">
            สวิงกว้าง {fib.get('range_pct', 0.0):.2f}%
        </span>
    </div>""", unsafe_allow_html=True)

    fc1, fc2, fc3, fc4 = st.columns(4)
    fc1.metric("ราคาปัจจุบัน", f"{last_close:,.2f}")
    fc2.metric("โซนปัจจุบัน", fib_zone["label"] if fib_zone else "-", f"ตำแหน่ง {fib_zone['ratio']*100:.1f}%" if fib_zone else "")
    fc3.metric("แนว Golden (0.618)", f"{fib['levels'].get(0.618, 0):,.2f}")
    if fib_tp:
        fc4.metric(f"เป้า TP หลัก ({fib_tp.get('level', 1.618):.3f})", f"{fib_tp.get('tp_price', 0):,.2f}", delta=f"{fib_tp.get('tp_pct', 0):+.2f}%")
    else:
        fc4.metric("เป้า TP หลัก", "-")

    st.markdown("---")
    col_ret, col_ext = st.columns(2)
    with col_ret:
        title_ret = "🟢 แนวรับย่อซื้อ (Retracement Supports)" if is_uptrend else "🔴 แนวต้านเด้งขาย (Retracement Resistances)"
        st.markdown(f"**{title_ret}**")
        ret_rows = []
        for lv, px in sorted(fib.get("levels", {}).items()):
            diff_pct = ((px - last_close) / last_close) * 100.0 if last_close else 0.0
            tag = "⭐ Golden Zone" if lv in (0.5, 0.618) else ("จุดเริ่ม (100%)" if lv == 1.0 else ("จุดยอด (0%)" if lv == 0.0 else ""))
            ret_rows.append({
                "ระดับ (Ratio)": f"{lv:.3f}",
                "ราคา (Price)": f"{px:,.2f}",
                "ระยะห่างจากราคาปัจจุบัน": f"{diff_pct:+.2f}%",
                "หมายเหตุ": tag
            })
        st.dataframe(pd.DataFrame(ret_rows), use_container_width=True, hide_index=True)

    with col_ext:
        st.markdown("**🎯 แผนเป้าหมายทำกำไร (TP) & จุดตัดขาดทุน (SL)**")
        plan_rows = []
        levels = fib.get("levels", {})
        sl_price = levels.get(1.0, min(levels.values()) if levels else last_close * 0.95) if is_uptrend else levels.get(1.0, max(levels.values()) if levels else last_close * 1.05)
        sl_pct = ((sl_price - last_close) / last_close) * 100.0 if last_close else 0.0
        plan_rows.append({
            "ประเภท": "🛑 ตัดขาดทุน (SL)",
            "ระดับเป้าหมาย": "หลุดฐานสวิงเดิม (1.000)",
            "ราคา": f"{sl_price:,.2f}",
            "ความเสี่ยง/ผลตอบแทน": f"{sl_pct:+.2f}%"
        })

        if ext and ext.get("targets"):
            for lv, px in sorted(ext["targets"].items()):
                tp_pct = ((px - last_close) / last_close) * 100.0 if last_close else 0.0
                tag_tp = "🏆 TP หลัก (Golden)" if lv == 1.618 else f"เป้าขยาย {lv:.3f}"
                plan_rows.append({
                    "ประเภท": "🎯 ทำกำไร (TP)",
                    "ระดับเป้าหมาย": tag_tp,
                    "ราคา": f"{px:,.2f}",
                    "ความเสี่ยง/ผลตอบแทน": f"{tp_pct:+.2f}%"
                })
        else:
            plan_rows.append({"ประเภท": "🎯 ทำกำไร (TP)", "ระดับเป้าหมาย": "กำลังรอชุดสวิง A-B-C", "ราคา": "-", "ความเสี่ยง/ผลตอบแทน": "-"})

        st.dataframe(pd.DataFrame(plan_rows), use_container_width=True, hide_index=True)

    def near_golden_zone_local(p, f):
        if not f or "levels" not in f: return False
        p50, p618 = f["levels"].get(0.5), f["levels"].get(0.618)
        if p50 is None or p618 is None: return False
        lo, hi = min(p50, p618), max(p50, p618)
        return (lo * 0.995) <= p <= (hi * 1.005)

    if near_golden_zone_local(last_close, fib):
        st.success("🎯 ราคาปัจจุบันกำลังทดสอบ **Golden Zone (0.5 – 0.618)** ซึ่งเป็นโซนกลับตัวและจุดสะสมที่มีนัยสำคัญสูงสุด")

def color_status(val):
    if val == "มีแรงซื้อ": return 'color: #26a69a'
    elif val == "มีแรงขาย": return 'color: #ef5350'
    else: return 'color: #9aa0a6'

def render_market_modal_content(tk, an, symbol, label_name, seasonality_html, gauges_html):
    st.markdown(f"### 📊 ข้อมูลตลาด 24h & บทวิเคราะห์ทางเทคนิค: {symbol}")
    st.caption(f"กระดาน: {label_name} | ราคาล่าสุด: {tk.get('price', 0):,.2f} ({tk.get('pct', 0):+.2f}%) ")

    tab1, tab2 = st.tabs(["Overview & Gauges", "Indicator & Pivot Tables"])

    with tab1:
        st.markdown("##### 1. รอบผลตอบแทนสะสมรายปี (Seasonality)")
        st.markdown(seasonality_html, unsafe_allow_html=True)

        st.markdown("##### 2. สรุปสัญญาณทางเทคนิค (Technical Indicators)")
        st.markdown(gauges_html, unsafe_allow_html=True)

    with tab2:
        df = st.session_state.get("df_data")
        if df is None or df.empty or len(df) < 30:
            st.info("กำลังโหลดข้อมูล...")
            st.stop()

        if an and "osc" in an and "ma" in an:
            st.markdown("##### 3. ตารางเจาะลึกตัวชี้วัดรายตัว (Indicator Breakdowns)")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown(f"**Oscillators (ตัวแกว่งตัว - {len(an['osc']['rows'])} ดัชนี)**")
                df_osc = pd.DataFrame(an["osc"]["rows"]).rename(columns={"name":"ชื่อดัชนี", "value":"มูลค่า", "action":"สถานะ"})
                if not df_osc.empty:
                    st.dataframe(df_osc.style.map(color_status, subset=['สถานะ']), use_container_width=True, hide_index=True)
                else:
                    st.dataframe(df_osc, use_container_width=True, hide_index=True)

            with t_col2:
                st.markdown(f"**ค่าเฉลี่ยเคลื่อนที่ (Moving Averages - {len(an['ma']['rows'])} เส้น)**")
                df_ma = pd.DataFrame(an["ma"]["rows"]).rename(columns={"name":"ชื่อเส้นค่าเฉลี่ย", "value":"ระดับราคา", "action":"สถานะ"})
                if not df_ma.empty:
                    st.dataframe(df_ma.style.map(color_status, subset=['สถานะ']), use_container_width=True, hide_index=True)
                else:
                    st.dataframe(df_ma, use_container_width=True, hide_index=True)

        if "pivots" in an:
            st.markdown("##### 4. จุดกลับตัวเดย์เทรด (Pivot Points)")
            p_rows = []
            for m_name, vals in an["pivots"].items():
                p_rows.append({
                    "วิธีคำนวณ": m_name,
                    "แนวรับ 2 (S2)": f"{vals['S2']:,.2f}",
                    "แนวรับ 1 (S1)": f"{vals['S1']:,.2f}",
                    "จุดหมุน (Pivot)": f"{vals['P']:,.2f}",
                    "แนวต้าน 1 (R1)": f"{vals['R1']:,.2f}",
                    "แนวต้าน 2 (R2)": f"{vals['R2']:,.2f}"
                })
def build_asset_icon_html(sym: str, tag_color: str = "#1E1E1E", size: int = 18) -> str:
    clean_code = sym.split(".")[0].replace("_THB", "").replace("-USDT", "").replace("USDT", "").replace("=F", "").replace("=X", "")
    clean_lower = clean_code.lower()
    fallback_avatar = f"https://ui-avatars.com/api/?name={clean_code[:3]}&background=0A0A0A&color=D1D4DC&rounded=true&bold=true&size=32"
    icon_url = f"https://assets.coincap.io/assets/icons/{clean_lower}@2x.png"
    return f"""<div style="display:flex;align-items:center;justify-content:center;height:24px;gap:3px;">
        <div style="width:3px;height:16px;border-radius:2px;background:{tag_color};flex-shrink:0;"></div>
        <img src="{icon_url}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;background:#050505;border:1px solid #1E1E1E;">
    </div>"""


def render_panel_controls():
    panel_state = st.session_state.get("panel_state", "normal")

    if panel_state == "hidden":
        handle_html = """
        <style>
            .edge-dock-handle {
                position: fixed;
                top: 50%;
                right: 0px;
                transform: translateY(-50%);
                width: 22px;
                height: 48px;
                background-color: #1e222d;
                border: 1px solid #363a45;
                border-right: none;
                border-radius: 8px 0 0 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 999;
                transition: background-color 0.15s ease;
            }
            .edge-dock-handle:hover {
                background-color: #2a2e39;
            }
            .edge-dock-handle span {
                color: #d1d4dc;
                font-size: 16px;
                font-weight: bold;
            }
        </style>
        <div class="edge-dock-handle" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'restore_panel'}, '*')">
            <span><</span>
        </div>
        """
        return components.html(handle_html, height=0)

    else:
        controls_html = """
        <style>
            .panel-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                height: 32px;
                padding: 0 8px 0 4px;
                user-select: none;
            }
            .traffic-lights {
                display: flex;
                gap: 6px;
            }
            .traffic-btn {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                cursor: pointer;
            }
            .btn-red { background-color: #ff5f57; }
            .btn-yellow { background-color: #ffbd2e; }
            .btn-green { background-color: #28c940; }

            .panel-status {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .live-badge {
                color: #26a69a;
                font-size: 11px;
                font-weight: 700;
            }
            .fullscreen-btn {
                width: 26px;
                height: 26px;
                font-size: 16px;
                color: #787b86;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.15s ease;
            }
            .fullscreen-btn:hover {
                background-color: #2a2e39;
                color: #d1d4dc;
            }
        </style>
        <div class="panel-header">
            <div class="traffic-lights">
                <div class="traffic-btn btn-red" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'red_click'}, '*')"></div>
                <div class="traffic-btn btn-yellow" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'yellow_click'}, '*')"></div>
                <div class="traffic-btn btn-green" onclick="window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'green_click'}, '*')"></div>
            </div>
            <div class="panel-status">
                <span class="live-badge">• LIVE</span>
                <div class="fullscreen-btn">⛶</div>
            </div>
        </div>
        """
        return components.html(controls_html, height=32)
