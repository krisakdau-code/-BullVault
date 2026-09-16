import streamlit.components.v1 as components

def render_floating_sidebar_toggle(neon: str = "#FF7A1A"):
    components.html(f"""
    <script>
    (function () {{
        const win = window.parent;
        const doc = win.document;
        if (!doc) return;

        function getLeftCol() {{
            const anchor = doc.getElementById("custom-left-menu-anchor");
            return anchor ? anchor.closest('div[data-testid="stColumn"]') : null;
        }}

        function getCenterCol() {{
            const anchor = doc.getElementById("custom-center-chart-anchor");
            return anchor ? anchor.closest('div[data-testid="stColumn"]') : null;
        }}

        function getRightCol() {{
            const anchor = doc.getElementById("custom-right-menu-anchor");
            return anchor ? anchor.closest('div[data-testid="stColumn"]') : null;
        }}

        // แผ่นใสกันกราฟขโมยเมาส์ขณะลาก
        function setDragShield(active) {{
            let shield = doc.getElementById("cyber-drag-shield");
            if (active) {{
                if (!shield) {{
                    shield = doc.createElement("div");
                    shield.id = "cyber-drag-shield";
                    Object.assign(shield.style, {{
                        position: "fixed",
                        top: "0",
                        left: "0",
                        width: "100vw",
                        height: "100vh",
                        zIndex: "9999999",
                        cursor: "col-resize",
                        backgroundColor: "transparent"
                    }});
                    doc.body.appendChild(shield);
                }}
            }} else {{
                if (shield) shield.remove();
            }}
        }}

        // ล็อกคอลัมน์เริ่มต้นให้แยกอิสระทันทีที่โหลดหน้า
        function lockLayoutPivots() {{
            const leftCol = getLeftCol();
            const centerCol = getCenterCol();
            const rightCol = getRightCol();

            if (leftCol && !leftCol.style.width) {{
                const w = Math.round(leftCol.getBoundingClientRect().width);
                if (w > 50) {{
                    leftCol.style.setProperty("flex", `0 0 ${{w}}px`, "important");
                    leftCol.style.setProperty("width", `${{w}}px`, "important");
                }}
            }}

            if (rightCol && !rightCol.style.width) {{
                const w = Math.round(rightCol.getBoundingClientRect().width);
                if (w > 50) {{
                    rightCol.style.setProperty("flex", `0 0 ${{w}}px`, "important");
                    rightCol.style.setProperty("width", `${{w}}px`, "important");
                }}
            }}

            if (centerCol) {{
                centerCol.style.setProperty("flex", "1 1 0%", "important");
                centerCol.style.setProperty("width", "auto", "important");
            }}
        }}

        // 1. แถบลากยืด-หด เมนูซ้าย
        function initLeftResizer() {{
            const leftCol = getLeftCol();
            if (!leftCol) return;
            leftCol.style.position = "relative";

            const RESIZER_ID = "cyber-left-resizer";
            let resizer = doc.getElementById(RESIZER_ID);
            if (!resizer) {{
                resizer = doc.createElement("div");
                resizer.id = RESIZER_ID;
                resizer.title = "คลิกค้างแล้วลากเมาส์เพื่อปรับขนาดเมนูซ้าย";
                Object.assign(resizer.style, {{
                    position: "absolute",
                    top: "0",
                    right: "-3px",
                    width: "7px",
                    height: "100%",
                    cursor: "col-resize",
                    zIndex: "9999",
                    backgroundColor: "transparent",
                    transition: "background 0.15s"
                }});

                resizer.onmouseenter = () => {{ resizer.style.backgroundColor = "{neon}"; }};
                resizer.onmouseleave = () => {{ if (!win._is_dragging_left) resizer.style.backgroundColor = "transparent"; }};

                resizer.addEventListener("mousedown", (e) => {{
                    win._is_dragging_left = true;
                    setDragShield(true);
                    const startX = e.clientX;
                    const startWidth = leftCol.getBoundingClientRect().width;

                    function onMouseMove(ev) {{
                        if (!win._is_dragging_left) return;
                        const dx = ev.clientX - startX;
                        let newW = startWidth + dx;
                        if (newW < 180) newW = 180;
                        if (newW > 450) newW = 450;

                        leftCol.style.setProperty("flex", `0 0 ${{newW}}px`, "important");
                        leftCol.style.setProperty("width", `${{newW}}px`, "important");
                        leftCol.style.setProperty("min-width", `${{newW}}px`, "important");
                        leftCol.style.setProperty("max-width", `${{newW}}px`, "important");

                        // ให้กราฟกลางปรับตาม โดยไม่แตะต้องเมนูขวา
                        win.dispatchEvent(new Event("resize"));
                    }}

                    function onMouseUp() {{
                        win._is_dragging_left = false;
                        setDragShield(false);
                        resizer.style.backgroundColor = "transparent";
                        win.removeEventListener("mousemove", onMouseMove);
                        win.removeEventListener("mouseup", onMouseUp);
                        win.dispatchEvent(new Event("resize"));
                    }}

                    win.addEventListener("mousemove", onMouseMove);
                    win.addEventListener("mouseup", onMouseUp);
                    e.preventDefault();
                }});

                leftCol.appendChild(resizer);
            }}
        }}

        // 2. แถบลากยืด-หด เมนูขวา
        function initRightResizer() {{
            const rightCol = getRightCol();
            if (!rightCol) return;
            rightCol.style.position = "relative";

            const RESIZER_ID = "cyber-right-resizer";
            let resizer = doc.getElementById(RESIZER_ID);
            if (!resizer) {{
                resizer = doc.createElement("div");
                resizer.id = RESIZER_ID;
                resizer.title = "คลิกค้างแล้วลากเมาส์เพื่อปรับขนาดเมนูขวา";
                Object.assign(resizer.style, {{
                    position: "absolute",
                    top: "0",
                    left: "-4px",
                    width: "8px",
                    height: "100%",
                    cursor: "col-resize",
                    zIndex: "9999",
                    backgroundColor: "transparent",
                    transition: "background 0.15s"
                }});

                resizer.onmouseenter = () => {{ resizer.style.backgroundColor = "{neon}"; }};
                resizer.onmouseleave = () => {{ if (!win._is_dragging_right) resizer.style.backgroundColor = "transparent"; }};

                resizer.addEventListener("mousedown", (e) => {{
                    win._is_dragging_right = true;
                    setDragShield(true);
                    const startX = e.clientX;
                    const startWidth = rightCol.getBoundingClientRect().width;

                    function onMouseMove(ev) {{
                        if (!win._is_dragging_right) return;
                        const dx = ev.clientX - startX;
                        let newW = startWidth - dx; // ลากซ้าย = เพิ่มขนาดขวา
                        if (newW < 220) newW = 220;
                        if (newW > 550) newW = 550;

                        rightCol.style.setProperty("flex", `0 0 ${{newW}}px`, "important");
                        rightCol.style.setProperty("width", `${{newW}}px`, "important");
                        rightCol.style.setProperty("min-width", `${{newW}}px`, "important");
                        rightCol.style.setProperty("max-width", `${{newW}}px`, "important");

                        // ให้กราฟกลางปรับตาม โดยไม่แตะต้องเมนูซ้าย
                        win.dispatchEvent(new Event("resize"));
                    }}

                    function onMouseUp() {{
                        win._is_dragging_right = false;
                        setDragShield(false);
                        resizer.style.backgroundColor = "transparent";
                        win.removeEventListener("mousemove", onMouseMove);
                        win.removeEventListener("mouseup", onMouseUp);
                        win.dispatchEvent(new Event("resize"));
                    }}

                    win.addEventListener("mousemove", onMouseMove);
                    win.addEventListener("mouseup", onMouseUp);
                    e.preventDefault();
                }});

                rightCol.appendChild(resizer);
            }}
        }}

        // 3. ปุ่มส้ม [ ☰ ] สลับพับ/เปิดเมนูซ้าย
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

        function setup() {{
            lockLayoutPivots();
            initLeftResizer();
            initRightResizer();
        }}

        setup();
        setTimeout(setup, 400);
        setTimeout(setup, 1200);
    }})();
    </script>
    """, height=0)