import streamlit.components.v1 as components

def render_floating_sidebar_toggle(neon: str = "#FF7A1A"):
    components.html(f"""
    <script>
    (function () {{
        const win = window.parent;
        const doc = win.document;
        if (!doc) return;

        // ดึงเฉพาะคอลัมน์ซ้ายที่มี ID ระบุไว้เท่านั้น (ห้ามเดาสุ่มเด็ดขาด)
        function getLeftCol() {{
            const anchor = doc.getElementById("custom-left-menu-anchor");
            if (anchor) return anchor.closest('div[data-testid="stColumn"]');
            return null;
        }}

        // ติดตั้งแถบลากยืด-หดซ้ายขวา
        function attachResizer() {{
            const leftCol = getLeftCol();
            if (!leftCol) return;

            leftCol.style.setProperty('position', 'relative', 'important');

            const RESIZER_ID = "cyber-left-resizer";
            if (!doc.getElementById(RESIZER_ID)) {{
                const resizer = doc.createElement("div");
                resizer.id = RESIZER_ID;
                resizer.title = "คลิกค้างแล้วลากเมาส์ซ้าย-ขวาเพื่อปรับขนาดเมนู";
                Object.assign(resizer.style, {{
                    position: "absolute",
                    top: "0",
                    right: "-2px",
                    width: "6px",
                    height: "100%",
                    cursor: "col-resize",
                    zIndex: "9999",
                    backgroundColor: "transparent"
                }});

                resizer.onmouseenter = () => {{
                    resizer.style.backgroundColor = "{neon}";
                    resizer.style.boxShadow = "0 0 6px {neon}";
                }};
                resizer.onmouseleave = () => {{
                    if (!win._is_dragging_resizer) {{
                        resizer.style.backgroundColor = "transparent";
                        resizer.style.boxShadow = "none";
                    }}
                }};

                resizer.addEventListener("mousedown", (e) => {{
                    win._is_dragging_resizer = true;
                    const startX = e.clientX;
                    const startWidth = leftCol.getBoundingClientRect().width;
                    doc.body.style.cursor = "col-resize";
                    doc.body.style.userSelect = "none";

                    function onMouseMove(ev) {{
                        if (!win._is_dragging_resizer) return;
                        const dx = ev.clientX - startX;
                        let newW = startWidth + dx;
                        if (newW < 200) newW = 200;
                        if (newW > 480) newW = 480;

                        leftCol.style.setProperty("flex", `0 0 ${{newW}}px`, "important");
                        leftCol.style.setProperty("width", `${{newW}}px`, "important");
                        leftCol.style.setProperty("min-width", `${{newW}}px`, "important");
                        leftCol.style.setProperty("max-width", `${{newW}}px`, "important");

                        win.dispatchEvent(new Event("resize"));
                    }}

                    function onMouseUp() {{
                        win._is_dragging_resizer = false;
                        doc.body.style.cursor = "";
                        doc.body.style.userSelect = "";
                        resizer.style.backgroundColor = "transparent";
                        resizer.style.boxShadow = "none";
                        doc.removeEventListener("mousemove", onMouseMove);
                        doc.removeEventListener("mouseup", onMouseUp);
                        win.dispatchEvent(new Event("resize"));
                    }}

                    doc.addEventListener("mousemove", onMouseMove);
                    doc.addEventListener("mouseup", onMouseUp);
                    e.preventDefault();
                    e.stopPropagation();
                }});

                leftCol.appendChild(resizer);
            }}
        }}

        // ปุ่มส้ม [ ☰ ] สลับพับ/เปิดเมนูซ้าย
        const BTN_ID = "cyber-floating-toggle-btn";
        let btn = doc.getElementById(BTN_ID);
        if (!btn) {{
            btn = doc.createElement("button");
            btn.id = BTN_ID;
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
                const lCol = getLeftCol();
                if (!lCol) return;
                win._cyber_sidebar_collapsed = !win._cyber_sidebar_collapsed;
                lCol.style.display = win._cyber_sidebar_collapsed ? "none" : "";
                setTimeout(() => {{ win.dispatchEvent(new Event("resize")); }}, 200);
            }};

            function snapLeft() {{
                const anchor = doc.getElementById("toggle-btn-anchor");
                if (anchor) {{
                    const rect = anchor.getBoundingClientRect();
                    if (rect.top > 0) {{
                        btn.style.top = (rect.top + 1) + "px";
                        btn.style.left = rect.left + "px";
                    }}
                }}
            }}
            doc.body.appendChild(btn);
            snapLeft();
            win.addEventListener("resize", snapLeft);
        }}

        setTimeout(attachResizer, 400);
        setTimeout(attachResizer, 1200);
    }})();
    </script>
    """, height=0)