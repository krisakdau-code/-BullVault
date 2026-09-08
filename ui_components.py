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
          <img class="tv-logo" src="{logo_url}" onerror="this.src='https://assets.coincap.io/assets/icons/btc@2x.png'">
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