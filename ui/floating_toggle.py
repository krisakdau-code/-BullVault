import streamlit.components.v1 as components

def render_floating_sidebar_toggle(neon: str = "#FF7A1A"):
    components.html(f"""
    <script>
    (function () {{
        const win = window.parent;
        const doc = win.document;
        if (!doc) return;

        const ID = "cyber-floating-toggle-btn";
        const existing = doc.getElementById(ID);
        if (existing) existing.remove();

        function getLeftCol() {{
            const anchor = doc.getElementById("custom-left-menu-anchor");
            if (anchor) return anchor.closest('div[data-testid="stColumn"]');
            return doc.querySelector('div[data-testid="stColumn"]');
        }}

        const btn = doc.createElement("button");
        btn.id = ID;
        btn.title = "ย่อ/ขยาย เมนูตลาด";
        btn.innerHTML = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="{neon}" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`;
        
        Object.assign(btn.style, {{
            position: "fixed",
            width: "30px",
            height: "30px",
            backgroundColor: "#161b22",
            border: "1px solid {neon}",
            borderRadius: "5px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: "9999999",
            boxShadow: "0 2px 6px rgba(0,0,0,0.5)"
        }});

        btn.onclick = (e) => {{
            e.preventDefault();
            const targetCol = getLeftCol();
            if (!targetCol) return;
            win._cyber_sidebar_collapsed = !win._cyber_sidebar_collapsed;
            targetCol.style.display = win._cyber_sidebar_collapsed ? "none" : "";
            setTimeout(() => {{ win.dispatchEvent(new Event("resize")); }}, 250);
        }};

        function snapToPosition() {{
            const anchor = doc.getElementById("toggle-btn-anchor");
            if (anchor) {{
                const rect = anchor.getBoundingClientRect();
                if (rect.top > 0) {{
                    btn.style.top = (rect.top + 1) + "px";
                    btn.style.left = (rect.left) + "px";
                }}
            }}
        }}

        doc.body.appendChild(btn);
        snapToPosition();
        setTimeout(snapToPosition, 150);
        win.addEventListener("resize", snapToPosition);
    }})();
    </script>
    """, height=0)