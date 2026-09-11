# asset_tabs.py
from __future__ import annotations
import html
from collections import deque
import streamlit as st

_UP, _DOWN, _FLAT = "▲", "▼", "■"
_GREEN, _RED, _GREY = "#26a69a", "#ef5350", "#8b949e"
_SPARK_LEN = 40          
_SPARK_W, _SPARK_H = 62, 20

def _f(key: str):
    try:
        return float(st.session_state.get(key))
    except (TypeError, ValueError):
        return None

def push_tick(sym: str) -> None:
    px = _f(f"live_price_{sym}")
    if px is None:
        return
    buf_key = f"spark_buf_{sym}"
    if buf_key not in st.session_state:
        st.session_state[buf_key] = deque(maxlen=_SPARK_LEN)
    buf = st.session_state[buf_key]
    if not buf or buf[-1] != px:
        buf.append(px)

def read_quote(sym: str) -> dict:
    price, pct = _f(f"live_price_{sym}"), _f(f"live_pct_{sym}")
    bid, ask = _f(f"live_bid_{sym}"), _f(f"live_ask_{sym}")

    if pct is None:
        arrow, color = _FLAT, _GREY
    elif pct > 0:
        arrow, color = _UP, _GREEN
    elif pct < 0:
        arrow, color = _DOWN, _RED
    else:
        arrow, color = _FLAT, _GREY

    if bid is not None and ask is not None and ask > 0:
        spread_abs = ask - bid
        spread_bps = spread_abs / ((ask + bid) / 2) * 10_000
        spread_txt = f"{spread_abs:,.2f} ({spread_bps:.1f}bp)"
    else:
        spread_txt = "—"

    return {
        "price_txt": "—" if price is None else f"{price:,.2f}",
        "pct_txt": "—" if pct is None else f"{pct:+.2f}%",
        "bid_txt": "—" if bid is None else f"{bid:,.2f}",
        "ask_txt": "—" if ask is None else f"{ask:,.2f}",
        "spread_txt": spread_txt,
        "arrow": arrow,
        "color": color,
    }

def _sparkline_svg(sym: str, color: str) -> str:
    buf = list(st.session_state.get(f"spark_buf_{sym}", []))
    if len(buf) < 2:
        return (f'<svg class="tspark" width="{_SPARK_W}" height="{_SPARK_H}">'
                f'<line x1="0" y1="{_SPARK_H/2}" x2="{_SPARK_W}" y2="{_SPARK_H/2}" '
                f'stroke="{_GREY}" stroke-width="1" stroke-dasharray="2 2"/></svg>')

    lo, hi = min(buf), max(buf)
    rng = (hi - lo) or 1e-9
    pad = 2
    step = _SPARK_W / (len(buf) - 1)
    pts = " ".join(
        f"{i*step:.1f},{pad + (1 - (v - lo) / rng) * (_SPARK_H - 2*pad):.1f}"
        for i, v in enumerate(buf)
    )
    lx, ly = pts.split(" ")[-1].split(",")
    area = f"0,{_SPARK_H} {pts} {_SPARK_W},{_SPARK_H}"
    uid = abs(hash(sym)) % 100000
    return (
        f'<svg class="tspark" width="{_SPARK_W}" height="{_SPARK_H}" '
        f'viewBox="0 0 {_SPARK_W} {_SPARK_H}" preserveAspectRatio="none">'
        f'<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity=".35"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{area}" fill="url(#g{uid})"/>'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{lx}" cy="{ly}" r="1.8" fill="{color}"/></svg>'
    )

_CSS = """
<style>
.tbar{display:flex;gap:8px;overflow-x:auto;padding:6px 2px 10px;
     border-bottom:1px solid rgba(255,255,255,.08);scrollbar-width:thin}
.tbar::-webkit-scrollbar{height:4px}
.tbar::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15);border-radius:2px}
.tcell{flex:0 0 auto;display:flex;align-items:center;gap:10px;
       padding:6px 14px;border-radius:8px;white-space:nowrap;
       font-family:"SF Mono",Consolas,monospace;line-height:1.15;
       background:rgba(255,255,255,.02);transition:background .15s}
.tcell.on{background:rgba(38,166,154,.10);box-shadow:inset 0 -2px 0 0 #26a69a}
.tmain{display:flex;flex-direction:column;gap:2px}
.trow1{display:flex;align-items:baseline;gap:8px}
.tsym{font-size:.82rem;font-weight:700;letter-spacing:.4px;color:#e6edf3}
.tpx{font-size:.86rem;font-weight:600}
.tpct{font-size:.72rem;opacity:.9}
.trow2{display:flex;gap:8px;font-size:.63rem;color:#7d8590}
.tbid{color:#26a69a}.task{color:#ef5350}
.tspread{opacity:.75}
.tspark{display:block;flex:0 0 auto}
div[data-testid="stHorizontalBlock"].tabclicks div.stButton>button{
    border:none;background:transparent;color:#7d8590;
    padding:0;min-height:0;height:22px;font-size:.70rem;width:100%}
div[data-testid="stHorizontalBlock"].tabclicks div.stButton>button:hover{
    color:#e6edf3;background:rgba(255,255,255,.05);border:none}
</style>
"""

def _strip_html(symbols: list[str], active: str) -> str:
    cells = []
    for s in symbols:
        push_tick(s)
        q = read_quote(s)
        cls = "tcell on" if s == active else "tcell"
        cells.append(
            f'<div class="{cls}">'
            f'<div class="tmain">'
            f'<div class="trow1">'
            f'<span class="tsym">{html.escape(s)}</span>'
            f'<span class="tpx" style="color:{q["color"]}">{q["arrow"]} {q["price_txt"]}</span>'
            f'<span class="tpct" style="color:{q["color"]}">{q["pct_txt"]}</span>'
            f'</div>'
            f'<div class="trow2">'
            f'<span class="tbid">B {q["bid_txt"]}</span>'
            f'<span class="task">A {q["ask_txt"]}</span>'
            f'<span class="tspread">S {q["spread_txt"]}</span>'
            f'</div></div>'
            f'{_sparkline_svg(s, q["color"])}'
            f'</div>'
        )
    return f'<div class="tbar">{"".join(cells)}</div>'

def render_asset_tabs(symbols: list[str], state_key: str = "active_symbol") -> str:
    if not symbols:
        return ""
    st.session_state.setdefault(state_key, symbols[0])
    if st.session_state[state_key] not in symbols:
        st.session_state[state_key] = symbols[0]

    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(_strip_html(symbols, st.session_state[state_key]), unsafe_allow_html=True)

    cols = st.columns(len(symbols), gap="small")
    for col, sym in zip(cols, symbols):
        with col:
            st.markdown('<div class="tabclicks">', unsafe_allow_html=True)
            if st.button(sym, key=f"tabbtn_{sym}", use_container_width=True):
                st.session_state[state_key] = sym
                st.rerun(scope="fragment")
            st.markdown('</div>', unsafe_allow_html=True)
    return st.session_state[state_key]

@st.fragment(run_every="1s")
def asset_tab_bar(symbols: list[str], state_key: str = "active_symbol") -> None:
    render_asset_tabs(symbols, state_key)