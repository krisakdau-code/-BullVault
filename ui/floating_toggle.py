import streamlit.components.v1 as components

NEON = "#FF7A1A"

def render_floating_sidebar_toggle(neon: str = NEON, top: int = 12, left: int = 12):
    """ปุ่มลอยควบคุม Sidebar แบบเสถียร — ป้องกัน Infinite Loop ด้วย RequestAnimationFrame"""
    components.html(f"""
<script>
(function () {{
  const NEON = "{neon}";
  const TOP  = {top};
  const LEFT = {left};
  const ID   = "cyber-sb-toggle";

  let doc, win;
  try {{ win = window.parent; doc = win.document; }}
  catch (e) {{ return; }}

  const sidebar = () => doc.querySelector('[data-testid="stSidebar"]');

  function isOpen() {{
    const sb = sidebar();
    if (!sb) return false;
    const aria = sb.getAttribute("aria-expanded");
    if (aria !== null) return aria === "true";
    return sb.getBoundingClientRect().width > 60;
  }}

  const expandBtn = () => doc.querySelector(
    '[data-testid="stSidebarCollapsedControl"] button,' +
    '[data-testid="collapsedControl"] button,' +
    '[data-testid="stExpandSidebarButton"] button,' +
    '[data-testid="stSidebarCollapsedControl"],' +
    '[data-testid="stExpandSidebarButton"]');

  const collapseBtn = () => doc.querySelector(
    '[data-testid="stSidebarCollapseButton"] button,' +
    '[data-testid="stSidebarCollapseButton"]');

  function toggle(e) {{
    e && e.stopPropagation();
    const open = isOpen();
    const native = open ? collapseBtn() : expandBtn();
    if (native) {{
      native.click();
    }} else {{
      const sb = sidebar();
      if (sb) {{
        sb.style.transform = open ? "translateX(-105%)" : "translateX(0)";
        sb.setAttribute("aria-expanded", open ? "false" : "true");
      }}
    }}
    setTimeout(sync, 250);
  }}

  function ensureButton() {{
    let b = doc.getElementById(ID);
    if (b && doc.body.contains(b)) return b;

    b = doc.createElement("button");
    b.id = ID; b.type = "button";
    b.setAttribute("aria-label", "Toggle sidebar");
    b.innerHTML = '<span style="font-size:16px;line-height:1;font-weight:700">&raquo;</span>';
    Object.assign(b.style, {{
      position: "fixed", top: TOP + "px", left: LEFT + "px",
      width: "36px", height: "36px",
      display: "flex", alignItems: "center", justifyContent: "center",
      background: "rgba(11,11,15,0.95)",
      color: NEON,
      border: "1px solid " + NEON + "88",
      borderRadius: "8px",
      boxShadow: "0 0 10px " + NEON + "44",
      cursor: "pointer",
      zIndex: "2147483647",
      pointerEvents: "auto",
      transition: "all 0.2s ease"
    }});
    b.onmouseenter = () => {{ b.style.boxShadow = "0 0 16px " + NEON; b.style.transform = "scale(1.05)"; }};
    b.onmouseleave = () => {{ b.style.boxShadow = "0 0 10px " + NEON + "44"; b.style.transform = "scale(1)"; }};
    b.addEventListener("click", toggle, true);

    doc.body.appendChild(b);
    return b;
  }}

  function sync() {{
    const b = ensureButton();
    const open = isOpen();
    b.querySelector("span").innerHTML = open ? "&laquo;" : "&raquo;";
    if (open) {{
      const w = sidebar() ? sidebar().getBoundingClientRect().width : 0;
      b.style.left = (w > 60 ? w + 8 : LEFT) + "px";
    }} else {{
      b.style.left = LEFT + "px";
    }}
  }}

  // ใช้ Event Listener และ Throttle แทนการรัว setInterval ถี่ยิบ
  ensureButton();
  sync();
  
  if (!win.__cyberInit) {{
    win.__cyberInit = true;
    win.addEventListener("resize", sync);
    doc.addEventListener("click", () => setTimeout(sync, 300), true);
  }}
}})();
</script>
""", height=0, width=0)