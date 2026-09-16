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

        /* 2. ดึงขอบหน้าจอชิดบน -65px */
        .stMainBlockContainer,
        div[data-testid="stMainBlockContainer"],
        section[data-testid="stMain"] .block-container,
        .block-container {
            padding-top: 0px !important;
            margin-top: -65px !important;
            padding-bottom: 0.2rem !important;
            padding-left: 0.4rem !important;
            padding-right: 0.4rem !important;
            max-width: 100% !important;
            width: 100% !important;
        }

        /* 3. ซ่อน Header ดั้งเดิม */
        header[data-testid="stHeader"],
        [data-testid="stDecoration"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"] {
            display: none !important;
            height: 0 !important;
        }

        /* 4. สีพื้นหลัง Dark Terminal */
        .stApp {
            background-color: #0b0e14 !important;
            color: #e6edf3 !important;
        }

        /* 5. ล็อกแถวแนวนอนห้ามตกบรรทัดเด็ดขาด */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            width: 100% !important;
        }

        /* 6. เมนูซ้าย: ล็อกความกว้างอิสระ (ห้ามยืด/หดตามเพื่อนบ้าน) + Scroll แยกเดี่ยว */
        div[data-testid="stColumn"]:has(#custom-left-menu-anchor) {
            flex: 0 0 auto !important;
            margin-top: -20px !important;
            padding-top: 0px !important;
            max-height: calc(100vh - 60px) !important;
            height: calc(100vh - 60px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            padding-right: 0px !important;
        }

        /* 7. ชาร์ตกราฟตรงกลาง: ทำหน้าที่เป็นตัวยืด-หดรับขนาดเพียงตัวเดียว */
        div[data-testid="stColumn"]:has(#custom-center-chart-anchor) {
            flex: 1 1 0% !important;
            min-width: 300px !important;
            width: auto !important;
            overflow: hidden !important;
        }

        /* 8. เมนูขวา: ล็อกความกว้างอิสระ (ห้ามยืด/หดตามเพื่อนบ้าน) + Scroll แยกเดี่ยว */
        div[data-testid="stColumn"]:has(#custom-right-menu-anchor) {
            flex: 0 0 auto !important;
            margin-top: -20px !important;
            padding-top: 0px !important;
            max-height: calc(100vh - 60px) !important;
            height: calc(100vh - 60px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            padding-left: 6px !important;
            padding-right: 2px !important;
        }

        /* ซ่อน Anchor ทั้ง 3 จุด */
        #custom-left-menu-anchor,
        #custom-center-chart-anchor,
        #custom-right-menu-anchor {
            display: block !important;
            height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
            overflow: hidden !important;
        }
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

        /* 9. Scrollbar ขนาด 4px สำหรับซ้ายและขวา */
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