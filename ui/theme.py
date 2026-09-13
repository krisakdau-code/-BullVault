# ui/theme.py
import streamlit as st
import streamlit.components.v1 as components

NEON = "#FF7A1A"  # Neon Orange
OBSIDIAN = "#07090E"  # Dark Obsidian


def apply_theme():
    """โหลดสไตล์ CSS Cyberpunk และฝังปุ่มเปิด-ปิด Sidebar แบบถาวร"""

    # 1. CSS ปรับแต่งสีและเลย์เอาต์หน้าจอ
    st.markdown(
        f"""
    <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: {OBSIDIAN} !important;
        }}

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

        div[data-testid="stVerticalBlock"],
        div.st-emotion-cache-q25c81,
        div.st-emotion-cache-1ndxyp5 {{ gap: 0px !important; }}
        div[data-testid="stHorizontalBlock"] {{ gap: 0px !important; }}
        div[data-testid="column"] {{ padding: 0px !important; }}

        [data-testid="stSidebar"] {{
            background-color: #0A0D14 !important;
            border-right: 1px solid rgba(255, 122, 26, 0.25) !important;
        }}
        [data-testid="stSidebarContent"] {{
            background-color: #0A0D14 !important;
            padding: 6px 8px !important;
        }}
        [data-testid="stSidebarCollapseButton"] button {{
            color: {NEON} !important;
        }}
        [data-testid="stSidebarCollapseButton"] svg {{
            fill: {NEON} !important;
            stroke: {NEON} !important;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # 2. ฝังปุ่มลอยผ่าน JavaScript อยู่นอกระบบ React ของ Streamlit ไม่มีวันหาย 100%
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
            
            // ตำแหน่งลอย: อยู่ใต้ช่อง 1h เหนือแถบเครื่องมือสีน้ำเงิน
            btn.style.position = 'fixed';
            btn.style.top = '48px';
            btn.style.left = '8px';
            btn.style.zIndex = '99999999';
            btn.style.width = '32px';
            btn.style.height = '32px';
            btn.style.background = '#0E121A';
            btn.style.color = '{NEON}';
            btn.style.border = '1.5px solid {NEON}';
            btn.style.borderRadius = '6px';
            btn.style.fontSize = '16px';
            btn.style.fontWeight = 'bold';
            btn.style.cursor = 'pointer';
            btn.style.display = 'flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.boxShadow = '0 0 10px rgba(255, 122, 26, 0.5)';
            btn.style.transition = 'all 0.2s ease';

            btn.onmouseenter = () => {{
                btn.style.borderColor = '#00FF66';
                btn.style.color = '#00FF66';
                btn.style.boxShadow = '0 0 14px rgba(0, 255, 102, 0.7)';
            }};
            btn.onmouseleave = () => {{
                btn.style.borderColor = '{NEON}';
                btn.style.color = '{NEON}';
                btn.style.boxShadow = '0 0 10px rgba(255, 122, 26, 0.5)';
            }};

            // สั่งเปิด-ปิด Sidebar เมื่อกดคลิก
            btn.onclick = () => {{
                const nativeBtn = doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                  doc.querySelector('[data-testid="stSidebarCollapsedControl"] button') ||
                                  doc.querySelector('button[aria-label*="sidebar" i]');
                if (nativeBtn) {{
                    nativeBtn.click();
                }} else {{
                    // Fallback: ถ้าหาปุ่ม Streamlit ไม่เจอ ให้สั่งกางเองตรงๆ
                    const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                    if (sidebar) {{
                        const isClosed = sidebar.getAttribute('aria-expanded') === 'false';
                        sidebar.setAttribute('aria-expanded', isClosed ? 'true' : 'false');
                    }}
                }}
            }};

            doc.body.appendChild(btn);
        }}

        // รันตั้งค่าทันทีและคอยเช็คทุก 1 วินาทีกันหลุด
        setupButton();
        setInterval(setupButton, 1000);
    }})();
    </script>
    """,
        height=0,
        width=0,
    )