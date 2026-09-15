# ui/theme.py
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 🎨 แผงควบคุมสีหลักของทั้งระบบ (แก้สีทุกจุดได้จากตรงนี้จุดเดียว)
# ==============================================================================
CYBER_COLORS = {
    "neon_green": "#22D090",       # สีเขียวนีออน (สวิตช์ ON, เส้นไฮไลต์, ป้าย LIVE, ขอบ Active)
    "cyber_orange": "#FF7A00",     # สีส้มไซเบอร์ (ปุ่มลอย ☰, ปุ่มหมวดหมู่, กรอบค้นหา)
    "bg_main": "#0E0606",          # สีพื้นหลังจอหลัก (Dark Obsidian)
    "bg_sidebar": "#100808",       # สีพื้นหลังแถบข้าง (Sidebar)
    "bg_card": "#140B0B",          # สีพื้นหลังการ์ด / กล่องข้อความ
    "bg_card_active": "#241111",   # สีพื้นหลังการ์ดที่กำลังเลือกดูอยู่
    "border_dim": "#331F1F",       # สีกรอบเส้นบางทั่วไป
    "text_main": "#FFFFFF",        # สีตัวอักษรหลัก
    "text_muted": "#B19393",       # สีตัวอักษรรอง / คำอธิบาย
}


def apply_theme():
    """โหลดสไตล์ CSS Cyberpunk และฝังปุ่มเปิด-ปิด Sidebar แบบถาวร"""
    c = CYBER_COLORS

    # 1. CSS ปรับแต่งสี เลย์เอาต์ และแก้ปัญหาการทับกัน
    st.markdown(
        f"""
    <style>
        /* พื้นหลังหน้าจอหลัก */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: {c['bg_main']} !important;
            color: {c['text_main']} !important;
        }}

        /* ซ่อน Header มาตรฐานของ Streamlit */
        header[data-testid="stHeader"], .stAppHeader {{
            background: transparent !important;
            height: 0px !important;
            min-height: 0px !important;
            overflow: visible !important;
            pointer-events: none !important;
        }}

        [data-testid="stDecoration"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],
        [data-testid="stMainMenu"],
        .stDeployButton, #MainMenu, footer {{
            display: none !important;
        }}

        /* คืนพื้นที่ให้กราฟเต็มจอ */
        .block-container,
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stMainBlockContainer"],
        [data-testid="block-container"] {{
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
            padding-left: 0px !important;
            padding-right: 0px !important;
            max-width: 100% !important;
            width: 100% !important;
        }}

        /* ปลดล็อกระยะห่างใน Sidebar (แก้ปัญหาตัวหนังสือทับกันถาวร) */
        [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
            gap: 8px !important;
        }}

        /* สีพื้นหลังแถบข้าง */
        [data-testid="stSidebar"] {{
            background-color: {c['bg_sidebar']} !important;
            border-right: 1px solid rgba(255, 122, 0, 0.25) !important;
        }}
        [data-testid="stSidebarContent"] {{
            background-color: {c['bg_sidebar']} !important;
            padding: 8px 10px 16px 10px !important;
        }}

        /* ซ่อนปุ่ม << ใน Sidebar (วงสีเขียว) */
        button[data-testid="stSidebarCollapseButton"],
        div[data-testid="stSidebarCollapseButton"],
        button[aria-label="Close sidebar"],
        [data-testid="stSidebarCollapseButton"] {{
            display: none !important;
            visibility: hidden !important;
        }}

        /* กำจัดสีฟ้าใต้แท็บ ให้เป็นสีเขียวนีออน Cyber */
        div[data-testid="stSidebar"] [data-baseweb="tab-highlight"] {{
            background-color: {c['neon_green']} !important;
            height: 2px !important;
        }}
        div[data-testid="stSidebar"] button[data-baseweb="tab"][aria-selected="true"] {{
            color: {c['neon_green']} !important;
        }}
        div[data-testid="stSidebar"] button[data-baseweb="tab"][aria-selected="true"] p {{
            color: {c['neon_green']} !important;
        }}

        /* สวิตช์ Toggle ตอนเปิด: เปลี่ยนจากสีฟ้าเป็นสีเขียวนีออน Cyber */
        div[data-testid="stSidebar"] div[data-testid="stToggle"] input:checked ~ div,
        div[data-testid="stSidebar"] div[data-testid="stToggle"] [data-checked="true"] {{
            background-color: {c['neon_green']} !important;
            border-color: {c['neon_green']} !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.45) !important;
        }}
        div[data-testid="stSidebar"] div[data-testid="stToggle"] input:checked ~ div > div,
        div[data-testid="stSidebar"] div[data-testid="stToggle"] [data-checked="true"] > div {{
            background-color: {c['bg_main']} !important;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # 2. ฝังปุ่มลอย ☰ สีส้ม Cyberpunk (เปิด-ปิด Sidebar ได้ตลอดเวลา)
    components.html(
        f"""
    <script>
    (function initToggle() {{
        const doc = window.parent.document;
        
        function setupButton() {{
            if (doc.getElementById('cyber-floating-toggle')) return;

            const btn = doc.createElement('button');
            btn.id = 'cyber-floating-toggle';
            btn.innerHTML = '&#9776;'; // สัญลักษณ์เมนู 3 ขีด (☰)
            btn.title = "เปิด/ปิด เมนูข้าง";
            
            btn.style.position = 'fixed';
            btn.style.top = '48px';
            btn.style.left = '8px';
            btn.style.zIndex = '99999999';
            btn.style.width = '32px';
            btn.style.height = '32px';
            btn.style.background = '#0E121A';
            btn.style.color = '{c["cyber_orange"]}';
            btn.style.border = '1.5px solid {c["cyber_orange"]}';
            btn.style.borderRadius = '6px';
            btn.style.fontSize = '16px';
            btn.style.fontWeight = 'bold';
            btn.style.cursor = 'pointer';
            btn.style.display = 'flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.boxShadow = '0 0 10px rgba(255, 122, 0, 0.5)';
            btn.style.transition = 'all 0.2s ease';

            btn.onmouseenter = () => {{
                btn.style.borderColor = '{c["neon_green"]}';
                btn.style.color = '{c["neon_green"]}';
                btn.style.boxShadow = '0 0 14px rgba(0, 255, 163, 0.7)';
            }};
            btn.onmouseleave = () => {{
                btn.style.borderColor = '{c["cyber_orange"]}';
                btn.style.color = '{c["cyber_orange"]}';
                btn.style.boxShadow = '0 0 10px rgba(255, 122, 0, 0.5)';
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