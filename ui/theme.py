import streamlit as st

CYBER_COLORS = {
    "bg": "#0d1117",
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
        /* 1. ปิดตาย Native Sidebar เดิมของ Streamlit */
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
            width: 0px !important;
            min-width: 0px !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        /* 2. ดึงขอบหน้าจอชิด 0px ไม่ให้มีช่องว่างด้านบน */
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

        /* 3. ซ่อน Header Streamlit ดั้งเดิม */
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

        /* 5. Scrollbar */
        ::-webkit-scrollbar {
            width: 5px;
            height: 5px;
        }
        ::-webkit-scrollbar-track {
            background: #0d1117;
        }
        ::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #FF7A1A;
        }
        </style>
        """,
        unsafe_allow_html=True
    )