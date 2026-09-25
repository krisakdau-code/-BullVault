# drawing_chart.py — Multi-Pane Anchored Drawing Terminal (Modular Clean Edition)
import json
import os
import streamlit.components.v1 as components
import streamlit as st
from data.fetchers import resolve_market_info

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "drawing_assets")

def _load_asset(filename: str) -> str:
    path = os.path.join(ASSETS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def render_drawing_chart(
    charts_config: list,
    height: int = None,
    key: str = "draw_chart",
    show_toolbar: bool = True,
    change_pct=None
):
    if not charts_config:
        return

    curr_sym = st.session_state.get("current_symbol", "BTCUSDT")
    meta = resolve_market_info(curr_sym)
    display_title = meta.get("display_name", curr_sym)
    exchange_name = meta.get("exchange", "MARKET")
    # ดึง % ตัดรอบวัน (00:00 UTC) ให้ตรงกับ TradingView, แท็บบน และเมนูขวา 100%
    if change_pct is not None:
      live_pct = float(change_pct)
    else:
      from data.fetchers import fetch_ticker_24h

      tk_24h = fetch_ticker_24h(curr_sym)
      live_pct = (
          float(tk_24h["price_change_pct"])
          if tk_24h and "price_change_pct" in tk_24h
          else 0.0
      )

    pct_sign = "+" if live_pct >= 0 else ""
    pct_str = f"{pct_sign}{live_pct:.2f}%"
    pct_color = "#00e676" if live_pct >= 0 else "#ff3366"

    # คำนวณความสูงหน้าต่าง
    if len(charts_config) == 1:
        charts_config[0]["chart"]["height"] = 650
        real_total_h = 660
    elif len(charts_config) == 2:
        charts_config[0]["chart"]["height"] = 540
        real_total_h = 540 + int(charts_config[1].get("chart", {}).get("height", 140)) + 10
    else:
        real_total_h = 0
        for c in charts_config:
            real_total_h += int(c.get("chart", {}).get("height", 130))
        _n_sub = max(0, len(charts_config) - 1)
        real_total_h += (_n_sub * 6) + 20 + 250

    chart_json = json.dumps(charts_config)
    toolbar_display = "flex" if show_toolbar else "none"

    # โหลดไฟล์แยกส่วนแล้วนำมาประกอบกัน
    html_template = _load_asset("drawing_template.html")
    css_content = _load_asset("drawing_style.css")
    js_fib = _load_asset("fibonacci_tool.js")
    js_pat = _load_asset("pattern_tool.js")
    js_engine = _load_asset("drawing_engine.js")
    js_content = js_fib + "\n" + js_pat + "\n" + js_engine

    rendered_html = (
        html_template
        .replace("/* INJECT_CSS_HERE */", css_content)
        .replace("/* INJECT_JS_HERE */", js_content)
        .replace("{{TOOLBAR_DISPLAY}}", toolbar_display)
        .replace("{{DISPLAY_TITLE}}", str(display_title))
        .replace("{{EXCHANGE_NAME}}", str(exchange_name))
        .replace("{{CHART_JSON}}", chart_json)
        .replace("{{CHANGE_PCT}}", pct_str)
        .replace("{{CHANGE_COLOR}}", pct_color)
    )

    components.html(rendered_html, height=real_total_h)