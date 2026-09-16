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
        /* 1. ปิด Native Sidebar ดั้งเดิม */
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
            width: 0px !important;
            min-width: 0px !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        /* 2. ดึงขอบหน้าจอชิดบนพอดี */
        .stMainBlockContainer,
        div[data-testid="stMainBlockContainer"],
        section[data-testid="stMain"] .block-container,
        .block-container {
            padding-top: 4px !important;
            margin-top: 0px !important;
            padding-bottom: 0px !important;
            padding-left: 0.3rem !important;
            padding-right: 0.3rem !important;
            max-width: 100% !important;
            width: 100% !important;
        }

        /* 3. ซ่อน Header Streamlit */
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

        /* ================= 4. แถบแท็บสลับเหรียญ (Row 1) ================= */
        div[data-testid="stHorizontalBlock"]:has(#custom-tabs-anchor) {
            margin-top: 0px !important;
            margin-bottom: 2px !important;
            padding-bottom: 0px !important;
            align-items: center !important;
        }
        div[data-testid="stHorizontalBlock"]:has(#custom-tabs-anchor) button {
            height: 27px !important;
            min-height: 27px !important;
            padding: 0px 10px !important;
            font-size: 11px !important;
            line-height: 1.2 !important;
            border-radius: 4px 4px 0 0 !important;
        }

        /* ================= 5. แถบเครื่องมือ Toolbar (Row 2) ================= */
        div[data-testid="stHorizontalBlock"]:has(#toggle-btn-anchor) {
            margin-top: 0px !important;
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

        /* Timeframe: บรรทัดเดียว ล็อกภาษาอังกฤษ ไม่ซ้อนทับ */
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

        /* ================= 6. พื้นที่ 3 ส่วนหลัก ================= */
        div[data-testid="stHorizontalBlock"]:has(#custom-left-menu-anchor) {
            display: flex !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            width: 100% !important;
            margin-top: 2px !important;
        }

        /* --- จุดแก้ที่ 1: เมนูซ้าย (คืนระยะห่างธรรมชาติ ไม่ให้ตัวหนังสือซ้อนทับ) --- */
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor) {
            flex: 0 0 auto !important;
            margin-top: 0px !important;
            padding-top: 0px !important;
            max-height: calc(100vh - 78px) !important;
            height: calc(100vh - 78px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            padding-right: 0px !important;
        }
        /* คืนช่องไฟแนวตั้งเฉพาะภายในเมนูซ้าย ไม่ให้ปุ่มทับข้อความหัวข้อ */
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor) div[data-testid="stVerticalBlock"] {
            gap: 8px !important;
        }
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor) div[data-testid="element-container"] {
            margin-bottom: 3px !important;
        }

        /* --- กราฟชาร์ตกลาง (คงเดิม: แนบชิดติดขอบ Toolbar) --- */
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

        /* --- จุดแก้ที่ 2: เมนูขวา (ดันลงมา 10px หลบปุ่มเครื่องมือด้านบน) --- */
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor) {
            flex: 0 0 auto !important;
            margin-top: 0px !important;
            padding-top: 10px !important; /* เว้นระยะห่างด้านบน ไม่ให้หัวข้อชนปุ่มโหลด */
            max-height: calc(100vh - 78px) !important;
            height: calc(100vh - 78px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            padding-left: 6px !important;
            padding-right: 2px !important;
        }
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor) div[data-testid="stVerticalBlock"] {
            gap: 6px !important;
        }

        /* ซ่อน Anchor ทั้งหมด */
        #custom-tabs-anchor,
        #custom-left-menu-anchor,
        #custom-center-chart-anchor,
        #custom-right-menu-anchor {
            display: block !important;
            height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
            overflow: hidden !important;
        }
        .element-container:has(#custom-tabs-anchor),
        div[data-testid="element-container"]:has(#custom-tabs-anchor),
        .element-container:has(#custom-left-menu-anchor),
        div[data-testid="element-container"]:has(#custom-left-menu-anchor),
        .element-container:has(#custom-center-chart-anchor),
        div[data-testid="element-container"]:has(#custom-center-chart-anchor),
        .element-container:has(#custom-right-menu-anchor),
        div[data-testid="element-container"]:has(#custom-right-menu-anchor) {
            margin: 0px !important;
            padding: 0px !important;
            height: 0px !important;
        }

        /* Scrollbar 4px */
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