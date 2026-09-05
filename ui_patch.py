# ui_patch.py — รวมทุกแพตช์ UI ไว้ไฟล์เดียว
import html as _html
import streamlit as st
import streamlit.components.v1 as components

_Q_SUFFIX = ("USDT", "USDC", "FDUSD", "BUSD", "TUSD", "DAI",
             "THB", "USD", "BTC", "ETH", "BNB")

# ──────────────────────────── [1] CSS มินิมอล ────────────────────────────
def inject_minimal_css():
    st.markdown("""
    <style>
    :root{ --ln:#2a2e39; --pn:#161a21; --tx:#d1d4dc; --dm:#787b86; --ac:#2962ff; }

    .stButton>button, .stDownloadButton>button{
      background:var(--pn)!important; color:var(--tx)!important;
      border:1px solid var(--ln)!important; border-radius:4px!important;
      padding:2px 6px!important; font-size:11px!important; font-weight:500!important;
      min-height:26px!important; height:26px!important; line-height:1!important;
      box-shadow:none!important; transition:.12s;
    }
    .stButton>button:hover{ border-color:var(--ac)!important; color:#fff!important;
                            background:#1c2230!important; }
    .stButton>button:focus{ box-shadow:none!important; outline:none!important; }
    .stButton>button p{ font-size:11px!important; margin:0!important; }

    div[data-testid="stHorizontalBlock"]{ gap:2px!important; }
    div[data-testid="column"]{ padding:0 1px!important; }

    div[data-testid="stExpander"]{ border:1px solid var(--ln)!important;
      border-radius:4px!important; background:#0D0F14!important; }
    div[data-testid="stExpander"] summary{ padding:3px 8px!important; font-size:11px!important; }
    div[data-testid="stExpander"] summary p{ font-size:11px!important; font-weight:600!important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"]{ padding:4px 6px!important; }

    section[data-testid="stSidebar"] .stButton>button{ text-align:left!important; }
    section[data-testid="stSidebar"] label{ font-size:11px!important; color:var(--dm)!important; }
    section[data-testid="stSidebar"] .block-container{ padding-top:.6rem!important; }

    div[data-baseweb="select"]>div, .stTextInput input, .stNumberInput input{
      background:var(--pn)!important; border:1px solid var(--ln)!important;
      border-radius:4px!important; font-size:11px!important; min-height:28px!important;
    }
    .stTabs [data-baseweb="tab"]{ padding:2px 8px!important; font-size:11px!important;
                                  height:28px!important; }
    .stTabs [data-baseweb="tab-list"]{ gap:1px!important; }
    hr{ margin:4px 0!important; border-color:var(--ln)!important; }
    </style>
    """, unsafe_allow_html=True)

# ──────────────────────────── [2] โลโก้ FALLBACK 4 ชั้น ────────────────────────────
def clean_asset_code(sym: str) -> str:
    s = (sym or "").upper().strip().lstrip("^")
    s = s.split(".")[0].split(":")[0]
    s = s.replace("=F", "").replace("=X", "").replace("_THB", "")
    for sep in ("-", "/", "_"):
        if sep in s:
            s = s.split(sep)[0]
    for q in _Q_SUFFIX:
        if s.endswith(q) and len(s) > len(q):
            s = s[:-len(q)]
            break
    return s or "NA"

def build_asset_icon(sym: str, tag_color: str = "#2a2e39", size: int = 20) -> str:
    code = clean_asset_code(sym)
    low = code.lower()
    chain = [
        f"https://cdn.jsdelivr.net/npm/cryptocurrency-icons@0.18.1/svg/color/{low}.svg",
        f"https://assets.coincap.io/assets/icons/{low}@2x.png",
        f"https://images.financialmodelingprep.com/symbol/{code}.png",
        f"https://ui-avatars.com/api/?name={code[:3]}&background=1e222d&color=d1d4dc&rounded=true&bold=true&size=64",
    ]
    data = _html.escape("|".join(chain), quote=True)
    onerr = ("var l=this.dataset.c.split('|');var i=+this.dataset.i+1;"
             "if(i<l.length){this.dataset.i=i;this.src=l[i];}"
             "else{this.onerror=null;}")
    return (
        '<div style="display:flex;align-items:center;justify-content:center;height:28px;gap:4px;">'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{tag_color};flex-shrink:0;"></div>'
        f'<img src="{_html.escape(chain[0], quote=True)}" data-c="{data}" data-i="0" '
        f'loading="lazy" onerror="{onerr}" alt="{code}" '
        f'style="width:{size}px;height:{size}px;border-radius:50%;object-fit:contain;'
        'background:#1c2030;border:1px solid #2a2e39;"></div>'
    )

# ──────────────────────────── [3] ปุ่มเต็มจอ (NATIVE + CSS + SHIFT+F) ────────────────────────────
def render_fullscreen_button(height: int = 34):
    components.html("""
<style>
 html,body{margin:0;padding:0;background:transparent;overflow:hidden}
 #fsb{width:100%;height:26px;background:#161a21;color:#d1d4dc;
      border:1px solid #2a2e39;border-radius:4px;font-size:11px;font-weight:500;
      cursor:pointer;font-family:inherit;transition:.12s;white-space:nowrap}
 #fsb:hover{border-color:#2962ff;color:#fff;background:#1c2230}
</style>
<button id="fsb">⛶ เต็มหน้าจอ</button>
<script>
const D=window.parent.document, E=D.documentElement, B=document.getElementById('fsb');

if(!D.getElementById('pfs-style')){
  const s=D.createElement('style'); s.id='pfs-style';
  s.textContent=`body.pfs header[data-testid="stHeader"],
                 body.pfs section[data-testid="stSidebar"],
                 body.pfs footer,
                 body.pfs div[data-testid="stToolbar"]{display:none!important}
                 body.pfs .block-container,
                 body.pfs div[data-testid="stMainBlockContainer"]{
                   max-width:100vw!important;padding:.3rem .6rem!important}`;
  D.head.appendChild(s);
}
const inFS=()=>D.fullscreenElement||D.webkitFullscreenElement;
const isOn=()=>!!inFS()||D.body.classList.contains('pfs');
const paint=()=>{B.textContent=isOn()?'🗗 ออกจากเต็มจอ':'⛶ เต็มหน้าจอ';};

B.addEventListener('click',async()=>{
  try{
    if(!inFS()){
      const rq=E.requestFullscreen||E.webkitRequestFullscreen||E.msRequestFullscreen;
      await rq.call(E); D.body.classList.add('pfs');
    }else{
      const ex=D.exitFullscreen||D.webkitExitFullscreen;
      await ex.call(D); D.body.classList.remove('pfs');
    }
  }catch(e){ D.body.classList.toggle('pfs'); }
  setTimeout(paint,80);
});
D.addEventListener('fullscreenchange',()=>{
  if(!inFS())D.body.classList.remove('pfs'); paint();
});
D.addEventListener('keydown',e=>{
  if(e.shiftKey&&(e.key==='F'||e.key==='f')) B.click();
});
paint();
</script>
""", height=height)

# ──────────────────────────── [4] แผงขวาและปุ่ม TOGGLE ────────────────────────────
def init_right_panel_state():
    if "right_open" not in st.session_state:
        st.session_state["right_open"] = True

def split_columns_with_toggle(base=(3.7, 1.1), tg=0.16):
    init_right_panel_state()
    if st.session_state["right_open"]:
        return st.columns([base[0], tg, base[1]])
    return st.columns([base[0] + base[1], tg, 0.001])

def render_right_toggle():
    init_right_panel_state()
    on = st.session_state["right_open"]
    if st.button("❯" if on else "❮", key="btn_right_toggle",
                 help="ย่อแผงขวา" if on else "ขยายแผงขวา",
                 use_container_width=True):
        st.session_state["right_open"] = not on
        st.rerun()

def right_open() -> bool:
    init_right_panel_state()
    return st.session_state["right_open"]

# ──────────────────────────── [5] WATCHLIST ROW มินิมอล ────────────────────────────
_NUM = ("font-family:ui-monospace,monospace;font-size:10.5px;text-align:right;"
        "padding-top:6px;font-variant-numeric:tabular-nums;letter-spacing:-.2px;")

def watchlist_row(s_item, s_lbl, q, tag_color, val_col, sign, fmt_price, fmt_chg, cat_name):
    action = None
    c0, c1, c2, c3, c4, c5 = st.columns([0.55, 1.6, 1.5, 1.25, 1.1, 0.35])
    with c0:
        st.markdown(build_asset_icon(s_item, tag_color), unsafe_allow_html=True)
    with c1:
        if st.button(s_lbl, key=f"wl_{cat_name}_{s_item}", use_container_width=True, help=s_item):
            action = "pick"
    with c2:
        st.markdown(f"<div style='{_NUM}color:#fff;font-weight:600;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='{_NUM}color:{val_col};'>{fmt_chg(q['change'])}</div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div style='{_NUM}color:{val_col};font-weight:600;'>{sign}{q['pct']:.2f}%</div>", unsafe_allow_html=True)
    with c5:
        if st.button("✕", key=f"del_{cat_name}_{s_item}", help="ลบออก"):
            action = "del"
    return action