import streamlit as st

CYBER_COLORS = {
    "bg": "#0b0e14",
    "surface": "#161b22",
    "panel": "#1f242d",
    "border": "#30363d",
    "neon_orange": "#FF7A1A",
    "neon_green": "#00FF66",
    "neon_red": "#FF3366",
    "text": "#c9d1d9",
    "text_dim": "#8b949e",
}

def apply_theme():
    st.markdown(
        """
        <style>
        /* 1. ปิด Native Sidebar ดั้งเดิมของ Streamlit */
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
            width: 0px !important;
            min-width: 0px !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        /* 2. ซ่อน Header Streamlit */
        header[data-testid="stHeader"],
        [data-testid="stDecoration"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"] {
            display: none !important;
            height: 0 !important;
        }

        .stApp {
            background-color: #0b0e14 !important;
            color: #e6edf3 !important;
        }

        /* ================= จุดที่ 1: กำจัดช่องว่างบนสุด (ดึงแท็บเหรียญขึ้นชิดขอบจอ) ================= */
        .stMainBlockContainer,
        div[data-testid="stMainBlockContainer"],
        section[data-testid="stMain"] .block-container,
        .block-container {
           padding-top: 3px !important;
            margin-top: 0px !important; /* ดึงเนื้อหาขึ้นแตะขอบบนสุดพอดี ไม่ขาด ไม่แหว่ง */
            padding-bottom: 0px !important;
            padding-left: 0.3rem !important;
            padding-right: 0.3rem !important;
            max-width: 100% !important;
            width: 100% !important;
        }

        /* ตัดระยะห่างระหว่างบล็อกแนวตั้งหลัก */
        div[data-testid="stVerticalBlock"] {
            gap: 0px !important;
        }

        /* ซ่อน Anchor ทุกตัว ไม่ให้กลายเป็นบรรทัดว่างคั่น */
        #custom-tabs-anchor,
        #toggle-btn-anchor,
        #custom-left-menu-anchor,
        #custom-center-chart-anchor,
        #custom-right-menu-anchor {
            display: none !important;
        }
        div[data-testid="element-container"]:has(#custom-tabs-anchor),
        div[data-testid="element-container"]:has(#toggle-btn-anchor),
        div[data-testid="element-container"]:has(#custom-left-menu-anchor),
        div[data-testid="element-container"]:has(#custom-center-chart-anchor),
        div[data-testid="element-container"]:has(#custom-right-menu-anchor) {
            display: none !important;
            margin: 0px !important;
            padding: 0px !important;
            height: 0px !important;
        }

        /* แถวที่ 1: แถบแท็บเหรียญ */
        div[data-testid="stHorizontalBlock"]:has(#custom-tabs-anchor) {
            margin-top: 0px !important;
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
            align-items: center !important;
        }
        div[data-testid="stHorizontalBlock"]:has(#custom-tabs-anchor) button {
            height: 25px !important;
            min-height: 25px !important;
            padding: 0px 8px !important;
            font-size: 11px !important;
            line-height: 1.1 !important;
            border-radius: 4px 4px 0 0 !important;
        }

        /* ================= จุดที่ 2: ดึงแถบ Timeframe ขึ้นประกบชิดใต้แท็บเหรียญ ================= */
        div[data-testid="stHorizontalBlock"]:has(#toggle-btn-anchor) {
            margin-top: -6px !important;  /* ดึงขึ้นประกบติดตูดแถบแท็บ */
            margin-bottom: 0px !important;
            padding: 0px !important;
            align-items: center !important;
            min-height: 28px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(#toggle-btn-anchor) button,
        div[data-testid="stHorizontalBlock"]:has(#toggle-btn-anchor) div[data-testid="stPopover"] button {
            height: 25px !important;
            min-height: 25px !important;
            padding: 0px 6px !important;
            font-size: 11px !important;
            line-height: 1.1 !important;
        }
        div[data-testid="stHorizontalBlock"]:has(#toggle-btn-anchor) input {
            height: 25px !important;
            min-height: 25px !important;
            padding: 0px 4px !important;
            font-size: 11px !important;
        }

        /* Timeframe: แถวเดียว, ล็อกอังกฤษ, ไม่ทับซ้อน */
        div[data-testid="stRadio"] {
            translate: no !important;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 6px !important;
            align-items: center !important;
            white-space: nowrap !important;
            margin: 0px !important;
            padding: 0px !important;
            translate: no !important;
        }
        div[data-testid="stRadio"] label {
            padding: 1px 2px !important;
            margin: 0px !important;
            font-size: 11px !important;
            white-space: nowrap !important;
            translate: no !important;
            cursor: pointer !important;
        }
        div[data-testid="stRadio"] label p {
            font-size: 11px !important;
            line-height: 1.2 !important;
            margin: 0px 0px 0px 3px !important;
            font-weight: 500 !important;
            display: inline-block !important;
            translate: no !important;
        }

        div[data-testid="stSlider"] {
            padding: 0px !important;
            margin-top: -12px !important;
            margin-bottom: -10px !important;
        }
        div[data-testid="stSlider"] label {
            display: none !important;
        }
        div[data-testid="stCheckbox"] {
            margin: 0px !important;
            padding: 0px !important;
        }
        div[data-testid="stCheckbox"] label p {
            font-size: 11px !important;
            line-height: 1.1 !important;
        }

        /* ================= จุดที่ 3: ดึงกราฟและเมนูข้างขึ้นมาชนขอบล่างของ Toolbar ================= */
        div[data-testid="stHorizontalBlock"]:has(#custom-left-menu-anchor) {
            display: flex !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            width: 100% !important;
            margin-top: -4px !important; /* ดึงขึ้นชนใต้ Toolbar ทันที */
        }

        /* เมนูซ้าย (เว้นระยะภายใน ป้องกันตัวหนังสือทับกัน) */
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor) {
            flex: 0 0 auto !important;
            margin-top: 0px !important;
            padding-top: 0px !important;
            max-height: calc(100vh - 60px) !important;
            height: calc(100vh - 60px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            padding-right: 2px !important;
        }
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor) div[data-testid="stVerticalBlock"] {
            gap: 10px !important;
        }
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor) div[data-testid="element-container"] {
            margin-bottom: 4px !important;
        }

        /* ชาร์ตกราฟกลาง (แนบชิด Toolbar) */
        div[data-testid="stColumn"]:has(#custom-center-chart-anchor) {
            flex: 1 1 0% !important;
            min-width: 300px !important;
            width: auto !important;
            overflow: hidden !important;
            margin-top: 0px !important;
            padding-top: 0px !important;
        }
        div[data-testid="stColumn"]:has(#custom-center-chart-anchor) iframe {
            margin-top: 0px !important;
            padding-top: 0px !important;
        }

        /* เมนูขวา */
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor) {
            flex: 0 0 auto !important;
            margin-top: 0px !important;
            padding-top: 4px !important;
            max-height: calc(100vh - 60px) !important;
            height: calc(100vh - 60px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            padding-left: 6px !important;
            padding-right: 2px !important;
        }
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor) div[data-testid="stVerticalBlock"] {
            gap: 8px !important;
        }

        /* Scrollbars 4px */
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor)::-webkit-scrollbar,
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor)::-webkit-scrollbar {
            width: 4px !important;
        }
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor)::-webkit-scrollbar-track,
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor)::-webkit-scrollbar-track {
            background: transparent !important;
        }
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor)::-webkit-scrollbar-thumb,
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor)::-webkit-scrollbar-thumb {
            background: #21262d !important;
            border-radius: 4px !important;
        }
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor)::-webkit-scrollbar-thumb:hover,
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor)::-webkit-scrollbar-thumb:hover {
            background: #FF7A1A !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )