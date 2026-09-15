# ui/theme.py
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 🎨 แผงควบคุมสีทุกจุดของระบบ (แก้ไขสีหน้าจอทั้งหมดได้จากตรงนี้ที่เดียว)
# ==============================================================================
CYBER_COLORS = {
    # 1. สีพื้นหลัง & โครงสร้างหลัก
    "bg_main": "#06080E",          # พื้นหลังจอแสดงกราฟตรงกลาง
    "bg_sidebar": "#080B10",       # พื้นหลังแถบเมนูซ้าย (Sidebar)
    "bg_card": "#0B0E14",          # พื้นหลังการ์ด / กล่องทั่วไป
    "bg_card_active": "#111724",   # พื้นหลังการ์ดเหรียญที่เลือกดูอยู่
    "border_dim": "#1F2633",       # สีกรอบเส้นบางทั่วไป
    "text_main": "#FFFFFF",        # สีข้อความหลัก
    "text_muted": "#8F9CAE",       # สีข้อความรอง / สถิติตัวเลข

    # 2. สีแท็บบนสุดของ Sidebar (ตลาด & เครื่องมือ)
    "tab_market_border": "#FF7A00",  # สีกรอบแท็บ 1 ตอนเลือก
    "tab_market_text": "#FF9433",    # สีตัวหนังสือแท็บ 1 ตอนเลือก
    "tab_market_bg": "rgba(255, 122, 0, 0.16)",
    "tab_tools_border": "#00FFA3",   # สีกรอบแท็บ 2 ตอนเลือก
    "tab_tools_text": "#00FFA3",     # สีตัวหนังสือแท็บ 2 ตอนเลือก
    "tab_tools_bg": "rgba(0, 255, 163, 0.14)",

    # 3. สีหัวข้อ (Headers) & ป้ายกำกับ (Badges)
    "header_orange": "#FF9400",      # สีหัวข้อค้นหาด่วน & สินทรัพย์
    "badge_orange_border": "#FF7A00",
    "badge_orange_text": "#FF9400",
    "badge_orange_bg": "rgba(255, 122, 0, 0.15)",
    "header_green": "#00FFA3",       # สีหัวข้อรายการติดตาม & เครื่องมือ
    "badge_green_border": "#00FFA3",
    "badge_green_text": "#00FFA3",
    "badge_green_bg": "rgba(0, 255, 163, 0.15)",

    # 4. ปุ่มหมวดหมู่ 2x2 & กระดานเทรด (Active States)
    "cat_active_border": "#FF7A00",
    "cat_active_text": "#FF9400",
    "cat_active_bg": "rgba(255, 122, 0, 0.18)",
    "exch_active_border": "#00FFA3",
    "exch_active_text": "#00FFA3",
    "exch_active_bg": "rgba(0, 255, 163, 0.15)",

    # 5. ช่องเลือกสินทรัพย์ & การ์ดรายการติดตาม
    "select_border": "#FF7A00",
    "card_active_border": "#00FFA3",
    "card_active_glow": "rgba(0, 255, 163, 0.35)",

    # 6. สวิตช์เปิด/ปิด (Toggles) ด้านล่าง
    "toggle_active": "#00FFA3",
    "toggle_inactive": "#1A202C",

    # 7. แถบเลื่อน (Scrollbar) & ปุ่มลอย ☰
    "scrollbar_thumb": "#00FFA3",
    "menu_btn_color": "#FF7A00",
    "menu_btn_hover": "#00FFA3",
}


def apply_theme():
    """โหลดสไตล์ CSS Cyberpunk ตัดช่องว่างด้านบนทิ้งทั้งหมด และฝังปุ่มลอย ☰"""
    c = CYBER_COLORS

    st.markdown(
        f"""
    <style>
        /* ---------------- 1. ตัดพื้นที่ว่างด้านบนสุดแบบ 100% ---------------- */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        .stAppHeader,
        header {{
            display: none !important;
            height: 0px !important;
            min-height: 0px !important;
            max-height: 0px !important;
            padding: 0px !important;
            margin: 0px !important;
            visibility: hidden !important;
        }}

        [data-testid="stAppViewContainer"],
        section[data-testid="stMain"],
        .main {{
            padding-top: 0px !important;
            margin-top: 0px !important;
        }}

        section[data-testid="stMain"] .block-container,
        div[data-testid="stMainBlockContainer"],
        [data-testid="stAppViewBlockContainer"],
        .block-container {{
            padding-top: 0px !important;
            margin-top: 0px !important;
            padding-bottom: 0.2rem !important;
            padding-left: 0px !important;
            padding-right: 0px !important;
            max-width: 100% !important;
            width: 100% !important;
        }}

        /* ซ่อนไอเทมส่วนเกินของ Streamlit */
        [data-testid="stDecoration"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],
        [data-testid="stMainMenu"],
        .stDeployButton, #MainMenu, footer {{
            display: none !important;
        }}

        /* พื้นหลังหน้าจอหลัก */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: {c['bg_main']} !important;
            color: {c['text_main']} !important;
        }}

        /* ---------------- 2. Sidebar Core & Layout Fix ---------------- */
        [data-testid="stSidebar"] {{
            background-color: {c['bg_sidebar']} !important;
            border-right: 1px solid {c['border_dim']} !important;
        }}

        [data-testid="stSidebarContent"] {{
            background-color: {c['bg_sidebar']} !important;
            padding: 8px 10px 16px 10px !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
            gap: 8px !important;
        }}

        /* ซ่อนปุ่มพับ Streamlit (<<) ถาวร */
        button[data-testid="stSidebarCollapseButton"],
        div[data-testid="stSidebarCollapseButton"],
        button[aria-label="Close sidebar"],
        [data-testid="stSidebarCollapseButton"] {{
            display: none !important;
            visibility: hidden !important;
        }}

        /* ---------------- 3. Sidebar Tabs ---------------- */
        div[data-testid="stSidebar"] div[data-baseweb="tab-highlight"],
        div[data-testid="stSidebar"] div[data-baseweb="tab-border"] {{
            display: none !important;
            background-color: transparent !important;
        }}

        div[data-testid="stSidebar"] div[data-baseweb="tab-list"] {{
            gap: 6px !important;
            background: {c['bg_card']} !important;
            padding: 3px !important;
            border-radius: 8px !important;
            border: 1px solid {c['border_dim']} !important;
            margin-bottom: 8px !important;
        }}

        div[data-testid="stSidebar"] button[data-baseweb="tab"] {{
            border-radius: 6px !important;
            padding: 5px 8px !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            color: {c['text_muted']} !important;
            background: transparent !important;
            border: 1.2px solid transparent !important;
            outline: none !important;
        }}

        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {{
            background: {c['tab_market_bg']} !important;
            border-color: {c['tab_market_border']} !important;
            color: {c['tab_market_text']} !important;
            box-shadow: 0 0 10px rgba(255, 122, 0, 0.35) !important;
        }}

        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {{
            background: {c['tab_tools_bg']} !important;
            border-color: {c['tab_tools_border']} !important;
            color: {c['tab_tools_text']} !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.35) !important;
        }}

        div[data-testid="stSidebar"] button[data-baseweb="tab"][aria-selected="true"] p {{
            color: inherit !important;
        }}

        /* ---------------- 4. Headers & Badges ---------------- */
        .cyber-header-orange {{
            color: {c['header_orange']} !important;
            font-size: 10.5px !important;
            font-weight: 800 !important;
            letter-spacing: 0.5px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            width: 100% !important;
            min-height: 26px !important;
            line-height: 1.6 !important;
            margin-top: 12px !important;
            margin-bottom: 6px !important;
            clear: both !important;
        }}

        .cyber-header-green {{
            color: {c['header_green']} !important;
            font-size: 10.5px !important;
            font-weight: 800 !important;
            letter-spacing: 0.5px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            width: 100% !important;
            min-height: 26px !important;
            line-height: 1.6 !important;
            margin-top: 12px !important;
            margin-bottom: 6px !important;
            clear: both !important;
        }}

        .cyber-badge-orange {{
            background: {c['badge_orange_bg']} !important;
            border: 1px solid {c['badge_orange_border']} !important;
            color: {c['badge_orange_text']} !important;
            font-size: 8px !important;
            font-weight: 800 !important;
            padding: 1px 5px !important;
            border-radius: 4px !important;
        }}

        .cyber-badge-green {{
            background: {c['badge_green_bg']} !important;
            border: 1px solid {c['badge_green_border']} !important;
            color: {c['badge_green_text']} !important;
            font-size: 8px !important;
            font-weight: 800 !important;
            padding: 1px 5px !important;
            border-radius: 4px !important;
        }}

        /* ---------------- 5. Controls & Widgets ---------------- */
        div[data-testid="stSidebar"] div.stButton > button {{
            background: {c['bg_card']} !important;
            border: 1px solid {c['border_dim']} !important;
            color: {c['text_muted']} !important;
            border-radius: 5px !important;
            font-size: 10px !important;
            font-weight: 700 !important;
            padding: 3px 5px !important;
            white-space: nowrap !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
        }}

        div[data-testid="stSidebar"] div.stButton > button:hover {{
            border-color: {c['header_green']} !important;
            color: {c['text_main']} !important;
            background: {c['bg_card_active']} !important;
        }}

        div[data-testid="stSidebar"] div.cat-active > div.stButton > button {{
            background: {c['cat_active_bg']} !important;
            border: 1.2px solid {c['cat_active_border']} !important;
            color: {c['cat_active_text']} !important;
            box-shadow: 0 0 8px rgba(255, 122, 0, 0.3) !important;
        }}

        div[data-testid="stSidebar"] div.exch-active > div.stButton > button {{
            background: {c['exch_active_bg']} !important;
            border: 1.2px solid {c['exch_active_border']} !important;
            color: {c['exch_active_text']} !important;
            box-shadow: 0 0 8px rgba(0, 255, 163, 0.25) !important;
            text-align: left !important;
            padding-left: 8px !important;
        }}
        div[data-testid="stSidebar"] div.exch-inactive > div.stButton > button {{
            text-align: left !important;
            padding-left: 8px !important;
        }}

        div[data-testid="stSidebar"] div[data-baseweb="select"] {{
            background-color: {c['bg_card']} !important;
            border: 1.2px solid {c['select_border']} !important;
            border-radius: 5px !important;
            box-shadow: 0 0 6px rgba(255, 122, 0, 0.2) !important;
            margin-top: 6px !important;
        }}
        div[data-testid="stSidebar"] div[data-baseweb="select"] * {{
            color: {c['text_main']} !important;
            font-size: 11px !important;
            font-weight: 700 !important;
        }}

        div[data-testid="stSidebar"] div.card-active > div.stButton > button {{
            background: {c['bg_card_active']} !important;
            border: 1.2px solid {c['card_active_border']} !important;
            color: {c['text_main']} !important;
            box-shadow: 0 0 8px {c['card_active_glow']} !important;
        }}

        div[data-testid="stSidebar"] div[data-testid="stPopover"] button svg {{
            display: none !important;
        }}
        div[data-testid="stSidebar"] div[data-testid="stPopover"] button {{
            background: transparent !important;
            border: 1px solid {c['border_dim']} !important;
            border-radius: 5px !important;
            padding: 2px 0px !important;
            min-width: 24px !important;
            width: 24px !important;
            height: 28px !important;
            justify-content: center !important;
        }}

        div[data-testid="stSidebar"] div[role="switch"][aria-checked="true"],
        div[data-testid="stSidebar"] [data-baseweb="checkbox"] div[role="switch"][aria-checked="true"] {{
            background-color: {c['toggle_active']} !important;
            border-color: {c['toggle_active']} !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.45) !important;
        }}
        div[data-testid="stSidebar"] div[role="switch"][aria-checked="true"] div,
        div[data-testid="stSidebar"] [data-baseweb="checkbox"] div[role="switch"][aria-checked="true"] div {{
            background-color: {c['bg_main']} !important;
        }}
        div[data-testid="stSidebar"] div[role="switch"][aria-checked="false"] {{
            background-color: {c['toggle_inactive']} !important;
            border: 1px solid {c['border_dim']} !important;
        }}

        div[data-testid="stSidebar"] ::-webkit-scrollbar {{
            width: 4px !important;
        }}
        div[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
            background: {c['scrollbar_thumb']} !important;
            border-radius: 2px !important;
        }}

        .clock-container {{
            margin-top: 10px; background: {c['bg_card']}; border: 1px solid {c['border_dim']}; border-radius: 6px;
            padding: 5px 8px; display: flex; justify-content: space-between; align-items: center;
            font-family: monospace; font-size: 9.5px; color: {c['text_muted']};
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ฝังปุ่มลอย ☰ ไว้ใน st.sidebar (ไม่ทิ้งกล่อง Iframe กวนพื้นที่หน้าหลัก)
    with st.sidebar:
        components.html(
            f"""
        <script>
        (function initToggle() {{
            const doc = window.parent.document;
            function setupButton() {{
                if (doc.getElementById('cyber-floating-toggle')) return;
                const btn = doc.createElement('button');
                btn.id = 'cyber-floating-toggle';
                btn.innerHTML = '&#9776;';
                btn.title = "เปิด/ปิด เมนูข้าง";
                btn.style.position = 'fixed';
                btn.style.top = '48px';
                btn.style.left = '8px';
                btn.style.zIndex = '99999999';
                btn.style.width = '32px';
                btn.style.height = '32px';
                btn.style.background = '{c["bg_card"]}';
                btn.style.color = '{c["menu_btn_color"]}';
                btn.style.border = '1.5px solid {c["menu_btn_color"]}';
                btn.style.borderRadius = '6px';
                btn.style.fontSize = '16px';
                btn.style.fontWeight = 'bold';
                btn.style.cursor = 'pointer';
                btn.style.display = 'flex';
                btn.style.alignItems = 'center';
                btn.style.justifyContent = 'center';
                btn.style.boxShadow = '0 0 10px rgba(255, 122, 0, 0.4)';
                btn.style.transition = 'all 0.2s ease';

                btn.onmouseenter = () => {{
                    btn.style.borderColor = '{c["menu_btn_hover"]}';
                    btn.style.color = '{c["menu_btn_hover"]}';
                }};
                btn.onmouseleave = () => {{
                    btn.style.borderColor = '{c["menu_btn_color"]}';
                    btn.style.color = '{c["menu_btn_color"]}';
                }};

                btn.onclick = () => {{
                    const nativeBtn = doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                      doc.querySelector('[data-testid="stSidebarCollapsedControl"] button') ||
                                      doc.querySelector('button[aria-label*="sidebar" i]');
                    if (nativeBtn) {{
                        nativeBtn.click();
                    }} else {{
                        const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                        if (sidebar) {{
                            const isClosed = sidebar.getAttribute('aria-expanded') === 'false';
                            sidebar.setAttribute('aria-expanded', isClosed ? 'true' : 'false');
                        }}
                    }}
                }};
                doc.body.appendChild(btn);
            }}
            setupButton();
            setInterval(setupButton, 1000);
        }})();
        </script>
        """,
            height=0,
            width=0,
        )