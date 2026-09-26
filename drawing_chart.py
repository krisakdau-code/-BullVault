# drawing_chart.py — Multi-Pane Anchored Drawing Terminal (Modular Clean Edition)
import json
import os
import streamlit as st
import streamlit.components.v1 as components
from data.fetchers import resolve_market_info

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "drawing_assets")

def _load_asset(filename: str) -> str:
    path = os.path.join(ASSETS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# =========================================================================
# 1. CSS รองรับ Touch Dragging, Fullscreen และปรับขนาดตัวเลขหัวชาร์ต
# =========================================================================
EXTRA_TOUCH_CSS = """
/* ป้องกัน Safari Double-Tap Zoom และล็อกไม่ให้การเลื่อนนิ้วหลุดไปเลื่อนหน้าจอหลัก */
#chart-container, .chart-container, .pane-container, canvas {
    touch-action: none !important;
    -webkit-touch-callout: none !important;
    -webkit-user-select: none !important;
    user-select: none !important;
}

/* ขยาย Hitbox และปลดล็อก Touch Action สำหรับเส้นเขียวแบ่งชาร์ต (Subchart Divider) */
.pane-resizer, .resizer, .chart-divider, .separator, [class*="resizer"], [class*="divider"], [class*="separator"], div[style*="cursor: row-resize"], div[style*="cursor: ns-resize"] {
    touch-action: none !important;
    -webkit-user-select: none !important;
    user-select: none !important;
    position: relative !important;
    cursor: row-resize !important;
}
.pane-resizer::after, .resizer::after, .chart-divider::after, [class*="resizer"]::after, [class*="divider"]::after {
    content: '' !important;
    position: absolute !important;
    top: -14px !important;
    bottom: -14px !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 9999 !important;
    background: transparent !important;
}

/* 1. ย่อเปอร์เซ็นต์ติดราคาหลัก (วงแดง) ให้เล็กลง */
.price-change, .change-pct, .legend-change, .header-change, #header-change, #price-change, [class*="change-pct"], [class*="price-change"] {
    font-size: 11.5px !important;
    font-weight: 600 !important;
    opacity: 0.85 !important;
}

/* 2. ขยายกล่อง 24h (วงเขียว) ให้ใหญ่เด่นชัด */
.badge-24h, .stat-24h, .change-24h, #badge-24h, [class*="24h"] {
    font-size: 14.5px !important;
    font-weight: 800 !important;
    padding: 3px 9px !important;
    letter-spacing: 0.3px !important;
}

/* สไตล์เมื่ออยู่ในโหมดเต็มหน้าจอ (Fullscreen Overlay) */
body.chart-fullscreen-active {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 99999999 !important;
    background: #07080a !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
body.chart-fullscreen-active #main-container,
body.chart-fullscreen-active #chart-container,
body.chart-fullscreen-active .chart-container {
    width: 100vw !important;
    height: 100vh !important;
}

/* ปุ่มลอยสำหรับออกจากโหมดเต็มหน้าจอ */
#btn-exit-fullscreen-float {
    position: fixed !important;
    top: 10px !important;
    right: 14px !important;
    z-index: 100000000 !important;
    background: rgba(22, 27, 34, 0.9) !important;
    border: 1px solid #ff7d1e !important;
    color: #ff9d42 !important;
    font-size: 11.5px !important;
    font-weight: 700 !important;
    padding: 5px 12px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    display: none;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;
    backdrop-filter: blur(8px) !important;
}
"""

# =========================================================================
# 2. JavaScript จัดการ Touch Dragging, Double-Tap Fullscreen และ Badge Styling
# =========================================================================
EXTRA_TOUCH_JS = """
(function() {
    // ---------------------------------------------------------------------
    // A. ควบคุมการลากเส้นเขียวแบ่งชาร์ตบนมือถือ (Touch Drag Divider)
    // ---------------------------------------------------------------------
    function initTouchResizers() {
        const selector = '.pane-resizer, .resizer, .chart-divider, [class*="resizer"], [class*="divider"], [class*="separator"], div[style*="cursor: row-resize"], div[style*="cursor: ns-resize"]';
        const resizers = document.querySelectorAll(selector);

        resizers.forEach(resizer => {
            if (resizer._touchBound) return;
            resizer._touchBound = true;
            resizer.style.touchAction = 'none';

            resizer.addEventListener('touchstart', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const t = e.touches[0];
                if (!t) return;

                const mdEv = new MouseEvent('mousedown', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: t.clientX,
                    clientY: t.clientY,
                    screenX: t.screenX,
                    screenY: t.screenY,
                    button: 0,
                    buttons: 1
                });
                resizer.dispatchEvent(mdEv);

                function onTouchMove(ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    const touch = ev.touches[0];
                    if (!touch) return;

                    const mmEv = new MouseEvent('mousemove', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: touch.clientX,
                        clientY: touch.clientY,
                        screenX: touch.screenX,
                        screenY: touch.screenY,
                        button: 0,
                        buttons: 1
                    });
                    window.dispatchEvent(mmEv);
                    document.dispatchEvent(mmEv);
                }

                function onTouchEnd(ev) {
                    const muEv = new MouseEvent('mouseup', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        button: 0,
                        buttons: 0
                    });
                    window.dispatchEvent(muEv);
                    document.dispatchEvent(muEv);

                    window.removeEventListener('touchmove', onTouchMove);
                    window.removeEventListener('touchend', onTouchEnd);
                    window.removeEventListener('touchcancel', onTouchEnd);
                    window.dispatchEvent(new Event('resize'));
                }

                window.addEventListener('touchmove', onTouchMove, { passive: false });
                window.addEventListener('touchend', onTouchEnd, { passive: false });
                window.addEventListener('touchcancel', onTouchEnd, { passive: false });
            }, { passive: false });
        });
    }

    // ---------------------------------------------------------------------
    // B. ระบบดับเบิลคลิก / ดับเบิลแท็บ สลับโหมดเต็มหน้าจอ (Fullscreen)
    // ---------------------------------------------------------------------
    let isFsActive = false;
    let originalFrameStyle = {};

    let exitBtn = document.getElementById('btn-exit-fullscreen-float');
    if (!exitBtn) {
        exitBtn = document.createElement('button');
        exitBtn.id = 'btn-exit-fullscreen-float';
        exitBtn.innerHTML = '✕ ออกจากเต็มจอ';
        document.body.appendChild(exitBtn);
        exitBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleFullscreen(false);
        };
    }

    function toggleFullscreen(forceState) {
        isFsActive = (typeof forceState === 'boolean') ? forceState : !isFsActive;
        const frame = window.frameElement;

        if (isFsActive) {
            if (frame) {
                originalFrameStyle = {
                    position: frame.style.position || '',
                    top: frame.style.top || '',
                    left: frame.style.left || '',
                    width: frame.style.width || '',
                    height: frame.style.height || '',
                    zIndex: frame.style.zIndex || '',
                    background: frame.style.background || ''
                };
                frame.style.setProperty('position', 'fixed', 'important');
                frame.style.setProperty('top', '0', 'important');
                frame.style.setProperty('left', '0', 'important');
                frame.style.setProperty('width', '100vw', 'important');
                frame.style.setProperty('height', '100vh', 'important');
                frame.style.setProperty('z-index', '99999999', 'important');
                frame.style.setProperty('background', '#07080a', 'important');
            }

            try {
                if (document.documentElement.requestFullscreen) {
                    document.documentElement.requestFullscreen().catch(() => {});
                } else if (window.parent && window.parent.document.documentElement.requestFullscreen) {
                    window.parent.document.documentElement.requestFullscreen().catch(() => {});
                }
            } catch(e) {}

            document.body.classList.add('chart-fullscreen-active');
            exitBtn.style.display = 'block';
        } else {
            if (frame && originalFrameStyle) {
                frame.style.position = originalFrameStyle.position;
                frame.style.top = originalFrameStyle.top;
                frame.style.left = originalFrameStyle.left;
                frame.style.width = originalFrameStyle.width;
                frame.style.height = originalFrameStyle.height;
                frame.style.zIndex = originalFrameStyle.zIndex;
                frame.style.background = originalFrameStyle.background;
            }

            try {
                if (document.exitFullscreen && document.fullscreenElement) {
                    document.exitFullscreen().catch(() => {});
                } else if (window.parent && window.parent.document.exitFullscreen && window.parent.document.fullscreenElement) {
                    window.parent.document.exitFullscreen().catch(() => {});
                }
            } catch(e) {}

            document.body.classList.remove('chart-fullscreen-active');
            exitBtn.style.display = 'none';
        }

        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
            if (window.parent) window.parent.dispatchEvent(new Event('resize'));
        }, 150);
    }

    function bindChartEvents() {
        const chartArea = document.body;
        let lastTap = 0;

        chartArea.addEventListener('dblclick', function(e) {
            if (e.target.closest('button, select, input, [role="button"], .pane-resizer, #btn-exit-fullscreen-float')) return;
            e.preventDefault();
            toggleFullscreen();
        });

        chartArea.addEventListener('touchend', function(e) {
            if (e.target.closest('button, select, input, [role="button"], .pane-resizer, #btn-exit-fullscreen-float')) return;
            const now = Date.now();
            const diff = now - lastTap;
            if (diff > 40 && diff < 320) {
                e.preventDefault();
                toggleFullscreen();
            }
            lastTap = now;
        }, { passive: false });
    }

    // ---------------------------------------------------------------------
    // C. ปรับแต่งขนาดตัวเลขเปอร์เซ็นต์ (วงแดงย่อลง / วงเขียว 24h ขยายใหญ่เด่นขึ้น)
    // ---------------------------------------------------------------------
    function adjustHeaderBadges() {
        // 1. วงเขียว (24h) -> ขยายใหญ่เด่นชัด
        const allEls = document.querySelectorAll('*');
        for (let el of allEls) {
            if (el.children.length === 0 && el.textContent && el.textContent.trim().startsWith('24h')) {
                el.style.setProperty('font-size', '14.5px', 'important');
                el.style.setProperty('font-weight', '800', 'important');
                el.style.setProperty('letter-spacing', '0.3px', 'important');
                const parent = el.parentElement;
                if (parent) {
                    parent.style.setProperty('padding', '2px 8px', 'important');
                    parent.style.setProperty('border-radius', '5px', 'important');
                }
                break;
            }
        }

        // 2. วงแดง (% ติดราคาหลักในแถวแรก) -> ย่อให้เล็กลงเป็นตัวรอง
        const headerEl = document.querySelector('#chart-header, .chart-header, .header-container, #header, .legend, [class*="header"], div[style*="position: absolute"]');
        if (headerEl) {
            const spans = headerEl.querySelectorAll('span, div, p, b');
            for (let s of spans) {
                if (s.children.length === 0 && s.textContent) {
                    const txt = s.textContent.trim();
                    if (txt.includes('%') && !txt.includes('24h') && (txt.startsWith('+') || txt.startsWith('-') || txt.startsWith('0') || txt.endsWith('%'))) {
                        s.style.setProperty('font-size', '11.5px', 'important');
                        s.style.setProperty('font-weight', '600', 'important');
                        s.style.setProperty('opacity', '0.85', 'important');
                        s.style.setProperty('margin-left', '4px', 'important');
                    }
                }
            }
        }
    }

    initTouchResizers();
    bindChartEvents();
    adjustHeaderBadges();
    setInterval(() => {
        initTouchResizers();
        adjustHeaderBadges();
    }, 600);
})();
"""

def render_drawing_chart(
    charts_config: list,
    height: int = None,
    key: str = "draw_chart",
    show_toolbar: bool = True,
    change_pct=None
):
    if not charts_config:
        return

    curr_sym = st.session_state.get("current_symbol", "BTCUSDT")
    meta = resolve_market_info(curr_sym)
    display_title = meta.get("display_name", curr_sym)
    exchange_name = meta.get("exchange", "MARKET")
    if change_pct is not None:
      live_pct = float(change_pct)
    else:
      from data.fetchers import fetch_ticker_24h

      tk_24h = fetch_ticker_24h(curr_sym)
      live_pct = (
          float(tk_24h["price_change_pct"])
          if tk_24h and "price_change_pct" in tk_24h
          else 0.0
      )

    pct_sign = "+" if live_pct >= 0 else ""
    pct_str = f"{pct_sign}{live_pct:.2f}%"
    pct_color = "#00e676" if live_pct >= 0 else "#ff3366"

    if len(charts_config) == 1:
        charts_config[0]["chart"]["height"] = 650
        real_total_h = 660
    elif len(charts_config) == 2:
        charts_config[0]["chart"]["height"] = 540
        real_total_h = 540 + int(charts_config[1].get("chart", {}).get("height", 140)) + 10
    else:
        real_total_h = 0
        for c in charts_config:
            real_total_h += int(c.get("chart", {}).get("height", 130))
        _n_sub = max(0, len(charts_config) - 1)
        real_total_h += (_n_sub * 6) + 20 + 250

    chart_json = json.dumps(charts_config)
    toolbar_display = "flex" if show_toolbar else "none"

    html_template = _load_asset("drawing_template.html")
    css_content = _load_asset("drawing_style.css") + "\n" + EXTRA_TOUCH_CSS
    js_fib = _load_asset("fibonacci_tool.js")
    js_pat = _load_asset("pattern_tool.js")
    js_engine = _load_asset("drawing_engine.js")
    js_content = js_fib + "\n" + js_pat + "\n" + js_engine + "\n" + EXTRA_TOUCH_JS

    rendered_html = (
        html_template
        .replace("/* INJECT_CSS_HERE */", css_content)
        .replace("/* INJECT_JS_HERE */", js_content)
        .replace("{{TOOLBAR_DISPLAY}}", toolbar_display)
        .replace("{{DISPLAY_TITLE}}", str(display_title))
        .replace("{{EXCHANGE_NAME}}", str(exchange_name))
        .replace("{{CHART_JSON}}", chart_json)
        .replace("{{CHANGE_PCT}}", pct_str)
        .replace("{{CHANGE_COLOR}}", pct_color)
    )

    components.html(rendered_html, height=real_total_h)