import streamlit.components.v1 as components

def render_floating_sidebar_toggle(neon: str = "#FF7A1A"):
    components.html(f"""
    <script>
    (function () {{
        const win = window.parent;
        const doc = win.document;
        if (!doc) return;

        // ดึงหน้าจอขึ้นชิดขอบบน
        function forcePullUp() {{
            const block = doc.querySelector('.block-container') || doc.querySelector('[data-testid="stMainBlockContainer"]');
            if (block) {{
                block.style.setProperty('margin-top', '-65px', 'important');
                block.style.setProperty('padding-top', '0px', 'important');
            }}
        }}
        forcePullUp();
        setTimeout(forcePullUp, 100);

        const ID = "cyber-floating-btn-group";
        const existing = doc.getElementById(ID);
        if (existing) existing.remove();

        // 1. CSS Animation
        let styleTag = doc.getElementById("cyber-toggle-animation-style");
        if (!styleTag) {{
            styleTag = doc.createElement("style");
            styleTag.id = "cyber-toggle-animation-style";
            styleTag.innerHTML = `
                .cyber-col-anim {{
                    transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1) !important;
                    transform-origin: left center !important;
                }}
                .cyber-col-collapsed {{
                    width: 0px !important;
                    min-width: 0px !important;
                    max-width: 0px !important;
                    flex: 0 0 0px !important;
                    padding: 0px !important;
                    margin: 0px !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                    transform: translateX(-100%) !important;
                    visibility: hidden !important;
                }}
            `;
            doc.head.appendChild(styleTag);
        }}

        function getLeftCol() {{
            const anchor = doc.getElementById("custom-left-menu-anchor");
            if (anchor) return anchor.closest('div[data-testid="stColumn"]');
            return doc.querySelector('div[data-testid="stColumn"]');
        }}

        // 2. สร้าง Container หุ้มปุ่มคู่ [ ☰ ] [ 🔄 ]
        const group = doc.createElement("div");
        group.id = ID;
        Object.assign(group.style, {{
            position: "fixed",
            display: "flex",
            gap: "4px",
            zIndex: "9999999",
            alignItems: "center"
        }});

        function createBtn(svgHtml, titleText) {{
            const b = doc.createElement("button");
            b.title = titleText;
            b.innerHTML = svgHtml;
            Object.assign(b.style, {{
                width: "30px",
                height: "30px",
                backgroundColor: "#161b22",
                border: "1px solid {neon}",
                borderRadius: "5px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 2px 6px rgba(0,0,0,0.5)",
                transition: "all 0.15s ease",
                padding: "0"
            }});
            b.onmouseenter = () => {{ b.style.backgroundColor = "#21262d"; b.style.boxShadow = "0 0 8px {neon}66"; }};
            b.onmouseleave = () => {{ b.style.backgroundColor = "#161b22"; b.style.boxShadow = "0 2px 6px rgba(0,0,0,0.5)"; }};
            return b;
        }}

        // ปุ่มที่ 1: [ ☰ ] สไลด์เมนูซ้าย
        const btnToggle = createBtn(
            `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{neon}" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`,
            "ย่อ/ขยาย เมนูตลาด (คลิกขวาเพื่อล้างแคช)"
        );

        btnToggle.onclick = (e) => {{
            e.preventDefault();
            const targetCol = getLeftCol();
            if (!targetCol) return;

            win._cyber_sidebar_collapsed = !win._cyber_sidebar_collapsed;
            targetCol.classList.add("cyber-col-anim");
            if (win._cyber_sidebar_collapsed) {{
                targetCol.classList.add("cyber-col-collapsed");
            }} else {{
                targetCol.classList.remove("cyber-col-collapsed");
            }}

            setTimeout(() => {{
                win.dispatchEvent(new Event("resize"));
                snapToPosition();
            }}, 300);
        }};

        // ฟังก์ชันสั่งล้างแคชและรีเซ็ตระบบ
        function doHardReset(e) {{
            e.preventDefault();
            const url = new URL(win.location.href);
            url.searchParams.set("clear_cache", "1");
            win.location.href = url.toString();
        }}

        btnToggle.oncontextmenu = doHardReset;

        // ปุ่มที่ 2: [ 🔄 ] ล้างแคช & รีเซ็ตแอป
        const btnReset = createBtn(
            `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#00FF66" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>`,
            "ล้าง Cache ทั้งหมด & รีสตาร์ตแอปใหม่"
        );
        btnReset.style.borderColor = "#00FF66";
        btnReset.onclick = doHardReset;

        group.appendChild(btnToggle);
        group.appendChild(btnReset);

        // ล็อกตำแหน่งให้อยู่หน้าแถว Timeframe
        function snapToPosition() {{
            const anchor = doc.getElementById("toggle-btn-anchor");
            if (anchor) {{
                const rect = anchor.getBoundingClientRect();
                if (rect.top > 0) {{
                    group.style.top = (rect.top + 1) + "px";
                    group.style.left = (rect.left) + "px";
                }}
            }}
        }}

        doc.body.appendChild(group);
        snapToPosition();
        setTimeout(snapToPosition, 150);
        setTimeout(snapToPosition, 500);
        win.addEventListener("resize", snapToPosition);
    }})();
    </script>
    """, height=0)