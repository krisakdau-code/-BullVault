# ui/sidebar_refactored.py
import os
import json
import streamlit as st
import streamlit.components.v1 as components

try:
    from data.rice_ohlcv import get_rice_symbols_list
except ImportError:
    def get_rice_symbols_list():
        return ["RICE:ข้าวเปลือกเจ้า", "RICE:ข้าวเปลือกหอมมะลิ", "FOB:ข้าวสารขาว 100%", "ZR=F (CBOT Rough Rice)"]

try:
    from symbols import get_full_binance_symbols
except ImportError:
    try:
        from data.symbols import get_full_binance_symbols
    except ImportError:
        get_full_binance_symbols = None


def render_sidebar():
    # -------------------------------------------------------------
    # 1. ดักรับ Event จากการคลิกเลือกเหรียญ/หุ้น (Query Params)
    # -------------------------------------------------------------
    chosen_sym = None
    if "select_sym" in st.query_params:
        chosen_sym = st.query_params.get("select_sym")
        del st.query_params["select_sym"]

    if chosen_sym and chosen_sym != st.session_state.get("current_symbol"):
        st.session_state["current_symbol"] = chosen_sym
        st.session_state["app_mode"] = "chart"
        is_r = chosen_sym.startswith("RICE:") or chosen_sym.startswith("FOB:") or chosen_sym == "ZR=F (CBOT Rough Rice)"
        tf_val = "1D" if is_r else st.session_state.get("selected_tf", "1h")
        if is_r:
            st.session_state["selected_tf"] = "1D"

        if "open_tabs" not in st.session_state or not st.session_state.open_tabs:
            import uuid
            new_id = uuid.uuid4().hex[:8]
            st.session_state.open_tabs = [{"id": new_id, "symbol": chosen_sym, "tf": tf_val}]
            st.session_state.active_tab_id = new_id
        else:
            active_id = st.session_state.get("active_tab_id")
            updated = False
            for t in st.session_state.open_tabs:
                if t.get("id") == active_id:
                    t["symbol"] = chosen_sym
                    if is_r:
                        t["tf"] = "1D"
                    updated = True
                    break
            if not updated:
                st.session_state.open_tabs[0]["symbol"] = chosen_sym
                if is_r:
                    st.session_state.open_tabs[0]["tf"] = "1D"
                st.session_state.active_tab_id = st.session_state.open_tabs[0]["id"]
        st.rerun()

    if "toggle_tool" in st.query_params:
        t_name = st.query_params.get("toggle_tool")
        del st.query_params["toggle_tool"]
        if t_name == "draw":
            st.session_state["show_draw_toolbar"] = not st.session_state.get("show_draw_toolbar", True)
        elif t_name == "top":
            st.session_state["show_top_bar"] = not st.session_state.get("show_top_bar", True)
        st.rerun()

    if "trigger_action" in st.query_params:
        act = st.query_params.get("trigger_action")
        del st.query_params["trigger_action"]
        if act == "fibo":
            st.session_state["trigger_fib_modal"] = True
        elif act == "market":
            st.session_state["trigger_market_modal"] = True
        elif act == "rice":
            st.session_state["app_mode"] = "rice"
        elif act == "theme":
            st.session_state["trigger_settings_modal"] = True
        st.rerun()

    show_top = st.session_state.get("show_top_bar", True)
    show_tool = st.session_state.get("show_draw_toolbar", True)

   # -------------------------------------------------------------
    # 2. ฐานข้อมูลสินทรัพย์จริงทุกกระดาน (โหลดจาก data/*.json)
    # -------------------------------------------------------------
    def load_json_symbols(filename, fallback):
        path = os.path.join("data", filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return list(json.load(f).keys())
            except Exception:
                pass
        return fallback

    all_markets_data = {
        "Crypto": {
            "Binance Spot": {
                "badge": "BINANCE", 
                "symbols": load_json_symbols("binance_crypto.json", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
            },
            "Binance TH": {
                "badge": "BINANCE TH", 
                "symbols": load_json_symbols("binance_th_crypto.json", ["BTC_THB", "ETH_THB", "USDT_THB"])
            },
            "OKX": {
                "badge": "OKX", 
                "symbols": load_json_symbols("okx_crypto.json", ["BTC-USDT", "ETH-USDT", "SOL-USDT"])
            },
            "KuCoin": {
                "badge": "KUCOIN", 
                "symbols": load_json_symbols("kucoin_crypto.json", ["BTC-USDT", "ETH-USDT", "KCS-USDT"])
            },
            "Bitkub (THB)": {
                "badge": "BITKUB", 
                "symbols": load_json_symbols("bitkub_crypto.json", ["BTC_THB", "ETH_THB", "KUB_THB"])
            },
            "Bybit": {
                "badge": "BYBIT", 
                "symbols": load_json_symbols("bybit_crypto.json", ["BTCUSDT", "ETHUSDT"])
            }
        },
        "หุ้นต่างประเทศ": {
            "สหรัฐฯ (US)": {
                "badge": "US", 
                "symbols": load_json_symbols("us_stocks.json", ["NVDA", "AAPL", "MSFT", "TSLA"])
            },
            "จีน/ฮ่องกง (China/HK)": {
                "badge": "CHINA", 
                "symbols": load_json_symbols("china_stocks.json", ["0700.HK", "9988.HK", "BABA"])
            },
            "เวียดนาม (VN)": {
                "badge": "VIETNAM", 
                "symbols": load_json_symbols("vietnam_stocks.json", ["VNM.VN", "VIC.VN", "HPG.VN"])
            },
            "Forex": {
                "badge": "FOREX", 
                "symbols": load_json_symbols("forex.json", ["USDTHB=X", "EURUSD=X", "USDJPY=X"])
            }
        },
        "หุ้นไทย": {
            "SET Index": {
                "badge": "SET", 
                "symbols": load_json_symbols("thai_stocks.json", ["DELTA.BK", "PTT.BK", "AOT.BK"])
            },
            "mai": {
                "badge": "MAI", 
                "symbols": ["AU.BK", "DEXON.BK", "KLINIQ.BK", "SPA.BK", "MASTER.BK"]
            },
            "TFEX": {
                "badge": "TFEX", 
                "symbols": ["S50=F", "GO=F"]
            }
        },
        "สินค้าเกษตร": {
            "สมาคมโรงสีข้าว": {
                "badge": "RICE", 
                "symbols": get_rice_symbols_list()
            },
            "ส่งออก (FOB)": {
                "badge": "FOB", 
                "symbols": ["FOB:ข้าวสารขาว 100%", "FOB:ข้าวนึ่ง 100%", "FOB:ข้าวหอมมะลิไทย"]
            },
            "CBOT ข้าว": {
                "badge": "CBOT", 
                "symbols": ["ZR=F (CBOT Rough Rice)", "ZC=F (Corn)", "ZS=F (Soybean)", "ZW=F (Wheat)"]
            }
        },
        "โภคภัณฑ์": {
            "โลหะมีค่า (Gold)": {
                "badge": "METALS", 
                "symbols": ["GC=F", "SI=F", "PL=F"]
            },
            "พลังงาน (Energy)": {
                "badge": "ENERGY", 
                "symbols": ["CL=F", "BZ=F", "NG=F"]
            }
        }
    }

    cur_sym = st.session_state.get("current_symbol", "BTCUSDT")

    # Watchlist Feed
    tracked = []
    if "open_tabs" in st.session_state and st.session_state.open_tabs:
        for t in st.session_state.open_tabs:
            if t.get("symbol") and t["symbol"] not in tracked:
                tracked.append(t["symbol"])

    default_feed = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "GC=F", "NVDA", "PTT.BK", "ข้าวหอม 100%"]
    for s_feed in default_feed:
        if s_feed not in tracked:
            tracked.append(s_feed)

    quotes = st.session_state.get("quotes_dict", {})
    rows_html = []
    for sym_code in tracked:
        is_active = (sym_code == cur_sym)
        lbl = sym_code.replace("_THB", "").replace(".BK", "")
        q = quotes.get(sym_code, {})
        price_val = q.get("price", 0.0)
        chg_val = q.get("change", 0.0)

        if price_val == 0.0:
            mock_p = {"BTCUSDT": 79036.15, "ETHUSDT": 2645.80, "SOLUSDT": 184.25, "BNBUSDT": 588.50, "GC=F": 2684.50, "NVDA": 142.30, "PTT.BK": 33.50, "ข้าวหอม 100%": 545.00}
            mock_c = {"BTCUSDT": 2.27, "ETHUSDT": 3.14, "SOLUSDT": 5.42, "BNBUSDT": -0.85, "GC=F": 0.45, "NVDA": -1.12, "PTT.BK": 0.75, "ข้าวหอม 100%": 0.00}
            price_val = mock_p.get(sym_code, 100.0)
            chg_val = mock_c.get(sym_code, 0.0)

        p_str = f"{price_val:,.2f}"
        is_up = (chg_val >= 0)
        c_sign = "+" if is_up else ""
        badge_color = "#00FFA3" if is_up else "#EF5350"
        badge_bg = "rgba(0, 255, 163, 0.12)" if is_up else "rgba(239, 83, 80, 0.12)"
        row_border = "1px solid #00FFA3; box-shadow: 0 0 8px rgba(0, 255, 163, 0.35);" if is_active else "1px solid #1A202C;"
        row_bg = "#111724" if is_active else "#0B0E14"
        market_sub = "Binance Spot" if "USDT" in sym_code else ("SET Index" if ".BK" in sym_code else ("Futures" if "=F" in sym_code else "Market"))

        rows_html.append(f"""
        <a href="/?select_sym={sym_code}" target="_top" class="coin-card" style="background:{row_bg}; border:{row_border}; text-decoration:none;">
            <div>
                <div class="coin-sym">{lbl}</div>
                <div class="coin-sub">{market_sub}</div>
            </div>
            <div class="coin-right">
                <span class="coin-price">{p_str}</span>
                <span class="coin-badge" style="color:{badge_color}; background:{badge_bg}; border:1px solid {badge_color};">
                    {c_sign}{chg_val:.2f}%
                </span>
            </div>
        </a>
        """)

    draw_status = "ON" if show_tool else "OFF"
    draw_cls = "btn-on" if show_tool else "btn-off"
    top_status = "ON" if show_top else "OFF"
    top_cls = "btn-on" if show_top else "btn-off"

    with st.sidebar:
        st.markdown("""
        <style>
        div[data-testid="stSidebarContent"] { padding-top: 6px !important; }
        div[data-testid="stSidebar"] div[data-baseweb="tab-list"] {
            gap: 6px !important;
            background: #0B0E14 !important;
            padding: 4px !important;
            border-radius: 8px !important;
            border: 1px solid #1A202C !important;
            margin-bottom: 6px !important;
        }
        div[data-testid="stSidebar"] button[data-baseweb="tab"] {
            border-radius: 6px !important;
            padding: 6px 10px !important;
            font-size: 11.5px !important;
            font-weight: 700 !important;
            color: #8F9CAE !important;
            background: transparent !important;
            border: 1px solid transparent !important;
        }
        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
            background: rgba(255, 122, 0, 0.15) !important;
            border: 1px solid #FF7A00 !important;
            color: #FF9433 !important;
            box-shadow: 0 0 10px rgba(255, 122, 0, 0.4) !important;
        }
        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
            background: rgba(0, 255, 163, 0.12) !important;
            border: 1px solid #00FFA3 !important;
            color: #00FFA3 !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.4) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        tab_market, tab_tools = st.tabs(["🔍 ตลาด & ค้นหา", "🟢 เครื่องมือ & อินดี้ (3)"])

        # =============================================================
        # แท็บ 1: ระบบ 3 ชั้น Cascading + Modal คลังสินทรัพย์
        # =============================================================
        with tab_market:
            tab1_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                body {{ background: transparent; color: #D1D4DC; user-select: none; overflow: hidden; }}

                .sec-title-orange {{ color: #FF9400; font-size: 11px; font-weight: 700; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }}
                .sec-title-green {{ color: #00FFA3; font-size: 11px; font-weight: 700; margin: 8px 0 5px 0; }}

                .btn-open-modal {{
                    background: rgba(255, 122, 0, 0.12); border: 1px solid #FF7A00; color: #FF9433;
                    font-size: 9.5px; font-weight: 700; padding: 2px 6px; border-radius: 4px; cursor: pointer;
                }}
                .btn-open-modal:hover {{ background: rgba(255, 122, 0, 0.25); }}

                .pills-scroll {{
                    display: flex; gap: 4px; overflow-x: auto; padding-bottom: 3px; margin-bottom: 4px;
                }}
                .pills-scroll::-webkit-scrollbar {{ height: 3px; }}
                .pills-scroll::-webkit-scrollbar-thumb {{ background: #23293A; border-radius: 2px; }}

                .pill-btn {{
                    white-space: nowrap; background: #0B0E14; border: 1px solid #1F2633; color: #8F9CAE;
                    font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 4px; cursor: pointer;
                }}
                .pill-btn.active-cat {{
                    background: rgba(255, 122, 0, 0.15); border: 1px solid #FF7A00; color: #FF9400; font-weight: 700;
                    box-shadow: 0 0 6px rgba(255, 122, 0, 0.3);
                }}
                .pill-btn-sub {{
                    white-space: nowrap; background: #0B0E14; border: 1px solid #1F2633; color: #8F9CAE;
                    font-size: 9.5px; font-weight: 600; padding: 2px 7px; border-radius: 4px; cursor: pointer;
                }}
                .pill-btn-sub.active-sub {{
                    background: rgba(0, 255, 163, 0.15); border: 1px solid #00FFA3; color: #00FFA3; font-weight: 700;
                    box-shadow: 0 0 6px rgba(0, 255, 163, 0.3);
                }}

                .search-box {{
                    display: flex; align-items: center; background: #0B0E14; border: 1px solid #FF7A00;
                    border-radius: 6px; padding: 4px 8px; margin-bottom: 6px; box-shadow: 0 0 8px rgba(255, 122, 0, 0.2);
                }}
                .search-icon {{ color: #FF7A00; font-size: 13px; margin-right: 6px; }}
                .search-select {{
                    background: transparent; border: none; color: #FFFFFF; font-size: 12px; font-weight: 700;
                    width: 100%; outline: none; cursor: pointer;
                }}
                .search-select option {{ background: #0B0E14; color: #FFFFFF; }}
                .badge-binance {{
                    color: #FF7A00; border: 1px solid #FF7A00; border-radius: 4px; font-size: 9px;
                    font-weight: 700; padding: 1px 5px; white-space: nowrap;
                }}

                .watchlist-box {{
                    background: #06080E; border: 1px solid #00FFA3; border-radius: 8px; padding: 5px;
                    height: 275px; overflow-y: auto; display: flex; flex-direction: column; gap: 5px;
                    box-shadow: 0 0 10px rgba(0, 255, 163, 0.2);
                }}
                .watchlist-box::-webkit-scrollbar {{ width: 5px; }}
                .watchlist-box::-webkit-scrollbar-thumb {{ background: #00FFA3; border-radius: 3px; }}

                .coin-card {{
                    display: flex; justify-content: space-between; align-items: center; padding: 5px 8px;
                    border-radius: 6px; cursor: pointer; transition: all 0.15s ease;
                }}
                .coin-card:hover {{ border-color: #00FFA3 !important; background: #111724 !important; }}
                .coin-sym {{ font-size: 11.5px; font-weight: 700; color: #FFFFFF; }}
                .coin-sub {{ font-size: 9px; color: #787B86; }}
                .coin-right {{ display: flex; align-items: center; gap: 6px; }}
                .coin-price {{ font-size: 11px; font-weight: 600; font-family: monospace; color: #FFFFFF; }}
                .coin-badge {{ font-size: 9px; font-weight: 700; border-radius: 4px; padding: 1px 5px; }}

                .bottom-ctrls {{ margin-top: 8px; display: flex; flex-direction: column; gap: 5px; }}
                .ctrl-row {{ display: flex; justify-content: space-between; align-items: center; font-size: 10.5px; color: #8F9CAE; }}
                .status-btn {{ font-size: 9.5px; font-weight: 700; padding: 2px 7px; border-radius: 4px; cursor: pointer; }}
                .btn-on {{ color: #00FFA3; border: 1px solid #00FFA3; background: rgba(0, 255, 163, 0.12); }}
                .btn-off {{ color: #787B86; border: 1px solid #2A303C; background: #0B0E14; }}

                .clock-bar {{
                    margin-top: 6px; background: #0B0E14; border: 1px solid #1A202C; border-radius: 6px;
                    padding: 4px 8px; display: flex; justify-content: space-between; align-items: center;
                    font-size: 10px; color: #8F9CAE; font-family: monospace;
                }}
                .badge-live {{
                    color: #00FFA3; border: 1px solid #00FFA3; background: rgba(0, 255, 163, 0.12);
                    padding: 1px 5px; border-radius: 3px; font-weight: 700;
                }}

                /* Modal Overlay */
                .modal-overlay {{
                    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(5, 7, 12, 0.95); z-index: 9999; padding: 10px; flex-direction: column;
                }}
                .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
                .modal-title {{ color: #00FFA3; font-size: 12px; font-weight: 700; }}
                .modal-close {{ color: #EF5350; font-size: 16px; font-weight: 700; cursor: pointer; padding: 0 4px; }}
                .modal-input {{
                    background: #0B0E14; border: 1px solid #00FFA3; border-radius: 5px; padding: 6px 10px;
                    color: #FFFFFF; font-size: 11px; width: 100%; outline: none; margin-bottom: 8px;
                }}
                .modal-results {{
                    flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px;
                }}
                .modal-item {{
                    display: flex; justify-content: space-between; align-items: center; padding: 5px 8px;
                    background: #0E131E; border: 1px solid #1A202C; border-radius: 4px; cursor: pointer;
                }}
                .modal-item:hover {{ border-color: #00FFA3; background: #162030; }}
            </style>
            </head>
            <body>
                <div class="sec-title-orange">
                    <span>🔍 ค้นหาด่วน (Quick Search)</span>
                    <span class="btn-open-modal" onclick="openModal()">⛶ คลังสินทรัพย์</span>
                </div>

                <!-- 1. แถบหมวดหมู่หลัก (ชั้น 1) -->
                <div class="pills-scroll" id="cat-pills-container"></div>

                <!-- 2. แถบกระดานย่อย (ชั้น 2) -->
                <div class="pills-scroll" id="exch-pills-container"></div>

                <!-- 3. ช่องค้นหา + ป้ายกระดาน (ชั้น 3) -->
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <select class="search-select" id="symbol-select" onchange="navTop(this.value)"></select>
                    <span class="badge-binance" id="exch-badge">BINANCE</span>
                </div>

                <div class="sec-title-green">📌 เหรียญที่เลือกมาแล้ว (Selected)</div>

                <!-- 4. Watchlist เลื่อนได้ -->
                <div class="watchlist-box">
                    {''.join(rows_html)}
                </div>

                <div class="bottom-ctrls">
                    <div class="ctrl-row">
                        <span>✏️ แถบวาดรูป (Draw)</span>
                        <span class="status-btn {draw_cls}" onclick="navToggle('draw')">{draw_status}</span>
                    </div>
                    <div class="ctrl-row">
                        <span>⏱️ แถบควบคุมบน (Top)</span>
                        <span class="status-btn {top_cls}" onclick="navToggle('top')">{top_status}</span>
                    </div>
                </div>

                <div class="clock-bar">
                    <span>🕒 BKK (UTC+7) <span id="clock-t1">--:--:--</span></span>
                    <span class="badge-live">LIVE</span>
                </div>

                <!-- หน้าต่าง Modal คลังสินทรัพย์ทั้งหมด -->
                <div class="modal-overlay" id="asset-modal">
                    <div class="modal-header">
                        <span class="modal-title">📂 คลังสินทรัพย์และกระดานทั้งหมด</span>
                        <span class="modal-close" onclick="closeModal()">✕</span>
                    </div>
                    <input type="text" class="modal-input" id="modal-search-box" placeholder="พิมพ์ชื่อค้นหา เช่น BTC, OKX, PTT, ข้าว, VNM..." oninput="filterModalItems(this.value)">
                    <div class="modal-results" id="modal-results-container"></div>
                </div>

                <script>
                    const marketData = {json.dumps(all_markets_data)};
                    let curCat = "Crypto";
                    let curExch = "Binance Spot";
                    let curSym = "{cur_sym}";

                    function navTop(sym) {{
                        const a = document.createElement('a');
                        a.href = '/?select_sym=' + encodeURIComponent(sym);
                        a.target = '_top';
                        document.body.appendChild(a);
                        a.click();
                    }}

                    function navToggle(t) {{
                        const a = document.createElement('a');
                        a.href = '/?toggle_tool=' + encodeURIComponent(t);
                        a.target = '_top';
                        document.body.appendChild(a);
                        a.click();
                    }}

                    function renderCats() {{
                        const container = document.getElementById('cat-pills-container');
                        container.innerHTML = Object.keys(marketData).map(c => `
                            <div class="pill-btn ${{c === curCat ? 'active-cat' : ''}}" onclick="changeCat('${{c}}')">${{c}}</div>
                        `).join('');
                    }}

                    function renderExchs() {{
                        const container = document.getElementById('exch-pills-container');
                        const exchs = Object.keys(marketData[curCat] || {{}});
                        if (!exchs.includes(curExch)) curExch = exchs[0];
                        container.innerHTML = exchs.map(e => `
                            <div class="pill-btn-sub ${{e === curExch ? 'active-sub' : ''}}" onclick="changeExch('${{e}}')">${{e}}</div>
                        `).join('');
                    }}

                    function renderSymbols() {{
                        const sel = document.getElementById('symbol-select');
                        const badge = document.getElementById('exch-badge');
                        const data = marketData[curCat][curExch] || {{ badge: 'MARKET', symbols: [] }};
                        badge.textContent = data.badge;

                        let symList = [...data.symbols];
                        if (!symList.includes(curSym)) symList.unshift(curSym);

                        sel.innerHTML = symList.map(s => `
                            <option value="${{s}}" ${{s === curSym ? 'selected' : ''}}>${{s}}</option>
                        `).join('');
                    }}

                    function changeCat(cat) {{
                        curCat = cat;
                        renderCats();
                        renderExchs();
                        renderSymbols();
                    }}

                    function changeExch(exch) {{
                        curExch = exch;
                        renderExchs();
                        renderSymbols();
                    }}

                    function openModal() {{
                        document.getElementById('asset-modal').style.display = 'flex';
                        filterModalItems('');
                    }}

                    function closeModal() {{
                        document.getElementById('asset-modal').style.display = 'none';
                    }}

                    function filterModalItems(query) {{
                        const container = document.getElementById('modal-results-container');
                        const q = query.trim().toUpperCase();
                        let html = '';

                        for (const [cName, exchs] of Object.entries(marketData)) {{
                            for (const [eName, eData] of Object.entries(exchs)) {{
                                for (const sym of eData.symbols) {{
                                    if (!q || sym.toUpperCase().includes(q) || eName.toUpperCase().includes(q) || cName.toUpperCase().includes(q)) {{
                                        html += `
                                            <div class="modal-item" onclick="navTop('${{sym}}')">
                                                <div>
                                                    <span style="color:#FFF; font-size:11px; font-weight:700;">${{sym}}</span>
                                                    <span style="color:#787B86; font-size:9.5px; margin-left:6px;">${{eName}}</span>
                                                </div>
                                                <span style="color:#00FFA3; border:1px solid #00FFA3; font-size:8.5px; padding:1px 5px; border-radius:3px;">${{eData.badge}}</span>
                                            </div>
                                        `;
                                    }}
                                }}
                            }}
                        }}
                        container.innerHTML = html || '<div style="color:#787B86; font-size:11px; text-align:center; padding:10px;">ไม่พบสินทรัพย์ที่ค้นหา</div>';
                    }}

                    function updateClock() {{
                        const el = document.getElementById('clock-t1');
                        if (el) el.textContent = new Date().toLocaleTimeString('en-GB', {{ timeZone: 'Asia/Bangkok', hour12: false }});
                    }}

                    renderCats();
                    renderExchs();
                    renderSymbols();
                    updateClock();
                    setInterval(updateClock, 1000);
                </script>
            </body>
            </html>
            """
            components.html(tab1_html, height=585)

        # =============================================================
        # แท็บ 2: เครื่องมือ & อินดี้ (ตรงตามรูปภาพ 100%)
        # =============================================================
        with tab_tools:
            tab2_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                body {{ background: transparent; color: #D1D4DC; user-select: none; overflow: hidden; }}

                .sec-title {{ color: #00FFA3; font-size: 11.5px; font-weight: 700; display: flex; align-items: center; gap: 4px; }}
                .sec-sub {{ color: #787B86; font-size: 9.5px; margin-top: 1px; margin-bottom: 6px; }}

                .icons-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 6px; }}
                .icon-btn {{
                    background: #0B0E14; border: 1px solid #1F2633; border-radius: 6px; height: 38px;
                    display: flex; align-items: center; justify-content: center; cursor: pointer;
                    font-size: 15px; color: #00FFA3; transition: all 0.15s ease;
                }}
                .icon-btn:hover {{
                    border-color: #00FFA3; box-shadow: 0 0 8px rgba(0, 255, 163, 0.3); background: #111724;
                }}

                .tooltip-banner {{
                    background: #0B0E14; border: 1px solid #00FFA3; border-radius: 6px; padding: 6px 8px;
                    margin-bottom: 10px; box-shadow: 0 0 8px rgba(0, 255, 163, 0.2);
                }}
                .tt-title {{ color: #00FFA3; font-size: 10.5px; font-weight: 700; }}
                .tt-desc {{ color: #8F9CAE; font-size: 9px; margin-top: 1px; }}

                .acc-card {{
                    background: #0B0E14; border: 1px solid #00FFA3; border-radius: 8px; padding: 7px 9px;
                    margin-bottom: 7px; box-shadow: 0 0 8px rgba(0, 255, 163, 0.15);
                }}
                .acc-card-dim {{
                    background: #0B0E14; border: 1px solid #1A202C; border-radius: 8px; padding: 7px 9px;
                    margin-bottom: 7px;
                }}
                .acc-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
                .acc-name {{ font-size: 11px; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 5px; }}
                .badge-active {{
                    font-size: 8.5px; font-weight: 700; color: #00FFA3; border: 1px solid #00FFA3;
                    background: rgba(0, 255, 163, 0.12); padding: 1px 5px; border-radius: 4px;
                }}

                .field-row {{
                    display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;
                    font-size: 10px; color: #8F9CAE;
                }}
                .field-val {{
                    background: #06080E; border: 1px solid #1F2633; border-radius: 4px; color: #FFFFFF;
                    font-family: monospace; font-size: 10.5px; font-weight: 600; padding: 2px 10px; min-width: 50px; text-align: right;
                }}
                .field-val-color {{
                    background: #06080E; border: 1px solid #00FFA3; border-radius: 4px; color: #00FFA3;
                    font-family: monospace; font-size: 10px; font-weight: 700; padding: 2px 8px;
                }}

                .info-box {{
                    background: #080B10; border: 1px solid #1F2633; border-radius: 6px; padding: 6px 8px;
                    margin-top: 6px; font-size: 9.5px; color: #8F9CAE;
                }}
                .info-title {{ color: #00FFA3; font-weight: 700; margin-bottom: 2px; }}

                .bottom-ctrls {{ margin-top: 8px; display: flex; flex-direction: column; gap: 5px; }}
                .ctrl-row {{ display: flex; justify-content: space-between; align-items: center; font-size: 10.5px; color: #8F9CAE; }}
                .status-btn {{ font-size: 9.5px; font-weight: 700; padding: 2px 7px; border-radius: 4px; cursor: pointer; }}
                .btn-on {{ color: #00FFA3; border: 1px solid #00FFA3; background: rgba(0, 255, 163, 0.12); }}
                .btn-off {{ color: #787B86; border: 1px solid #2A303C; background: #0B0E14; }}

                .clock-bar {{
                    margin-top: 6px; background: #0B0E14; border: 1px solid #1A202C; border-radius: 6px;
                    padding: 4px 8px; display: flex; justify-content: space-between; align-items: center;
                    font-size: 10px; color: #8F9CAE; font-family: monospace;
                }}
                .badge-live {{
                    color: #00FFA3; border: 1px solid #00FFA3; background: rgba(0, 255, 163, 0.12);
                    padding: 1px 5px; border-radius: 3px; font-weight: 700;
                }}
            </style>
            </head>
            <body>
                <div class="sec-title">⚡ เครื่องมือระบบ (Icon Launchers + Hover Tooltip)</div>
                <div class="sec-sub">ปุ่มไอคอนเรียบหรู ลดตัวหนังสือรกตา ชี้เมาส์เพื่อดูคำอธิบาย</div>

                <div class="icons-grid">
                    <div class="icon-btn" onmouseover="setTT('📐 Fibonacci Suite & Golden Zone', 'คำนวณเป้าหมายราคาและแนวรับต้านอัตโนมัติ')" onclick="navAction('fibo')">📐</div>
                    <div class="icon-btn" onmouseover="setTT('📊 ตลาด 24h (Market Analysis)', 'ภาพรวมสถิติวอลุ่ม การซื้อขาย และโมเมนตัมตลาด')" onclick="navAction('market')">📊</div>
                    <div class="icon-btn" onmouseover="setTT('🌾 กราฟราคาข้าวไทย', 'สลับสู่โหมดวิเคราะห์ข้อมูลราคาสินค้าเกษตรไทย')" onclick="navAction('rice')">🌾</div>
                    <div class="icon-btn" onmouseover="setTT('⚙️ สไตล์กราฟ & การแสดงผล', 'ปรับแต่งธีม สีแท่งเทียน และอินเทอร์เฟซผู้ใช้')" onclick="navAction('theme')">🟣</div>
                </div>

                <div class="tooltip-banner">
                    <div class="tt-title" id="tt-title-el">📐 Fibonacci Suite & Golden Zone</div>
                    <div class="tt-desc" id="tt-desc-el">คำนวณเป้าหมายราคาและแนวรับต้านอัตโนมัติ</div>
                </div>

                <div class="sec-title">⚙️ อินดิเคเตอร์ที่เปิดใช้งาน (Dynamic Accordion)</div>
                <div class="sec-sub">กางเฉพาะตัวที่เปิด ปิดตัวไหนซ่อนตัวนั้น</div>

                <div class="acc-card">
                    <div class="acc-header">
                        <span class="acc-name">📈 เส้นค่าเฉลี่ย EMA Ribbon</span>
                        <span class="badge-active">ACTIVE</span>
                    </div>
                    <div class="field-row">
                        <span>Fast EMA:</span>
                        <span class="field-val">7</span>
                    </div>
                    <div class="field-row">
                        <span>Slow EMA:</span>
                        <span class="field-val">15</span>
                    </div>
                    <div class="field-row">
                        <span>Trend EMA:</span>
                        <span class="field-val">45</span>
                    </div>
                </div>

                <div class="acc-card-dim">
                    <div class="acc-header">
                        <span class="acc-name">📈 พารามิเตอร์ RSI (14)</span>
                        <span class="badge-active">ACTIVE</span>
                    </div>
                    <div class="field-row">
                        <span>Upper Band (UB):</span>
                        <span class="field-val">70.0</span>
                    </div>
                    <div class="field-row">
                        <span>Lower Band (LB):</span>
                        <span class="field-val">30.0</span>
                    </div>
                    <div class="field-row">
                        <span>สีเส้นสัญญาณ:</span>
                        <span class="field-val-color">#00FFA3</span>
                    </div>
                </div>

                <div class="acc-card-dim">
                    <div class="acc-header">
                        <span class="acc-name">📊 พารามิเตอร์ MACD (12, 26, 9)</span>
                        <span class="badge-active">ACTIVE</span>
                    </div>
                </div>

                <div class="info-box">
                    <div class="info-title">💡 จัดการอินดิเคเตอร์:</div>
                    <div>เปิด/ปิด หรือปักหมุดอินดี้ได้ที่ปุ่ม 'Indicators' บนแถบบาร์</div>
                </div>

                <div class="bottom-ctrls">
                    <div class="ctrl-row">
                        <span>✏️ แถบวาดรูป (Drawing Bar)</span>
                        <span class="status-btn {draw_cls}" onclick="navToggle('draw')">{draw_status}</span>
                    </div>
                    <div class="ctrl-row">
                        <span>⏱️ แถบเครื่องมือบน (Toolbar)</span>
                        <span class="status-btn {top_cls}" onclick="navToggle('top')">{top_status}</span>
                    </div>
                </div>

                <div class="clock-bar">
                    <span>🕒 BKK (UTC+7) <span id="clock-t2">--:--:--</span></span>
                    <span class="badge-live">LIVE</span>
                </div>

                <script>
                    function setTT(t, d) {{
                        document.getElementById('tt-title-el').textContent = t;
                        document.getElementById('tt-desc-el').textContent = d;
                    }}

                    function navAction(a) {{
                        const el = document.createElement('a');
                        el.href = '/?trigger_action=' + encodeURIComponent(a);
                        el.target = '_top';
                        document.body.appendChild(el);
                        el.click();
                    }}

                    function navToggle(t) {{
                        const el = document.createElement('a');
                        el.href = '/?toggle_tool=' + encodeURIComponent(t);
                        el.target = '_top';
                        document.body.appendChild(el);
                        el.click();
                    }}

                    function updateClock() {{
                        const el = document.getElementById('clock-t2');
                        if (el) el.textContent = new Date().toLocaleTimeString('en-GB', {{ timeZone: 'Asia/Bangkok', hour12: false }});
                    }}
                    updateClock();
                    setInterval(updateClock, 1000);
                </script>
            </body>
            </html>
            """
            components.html(tab2_html, height=585)

    return {"show_top_bar": show_top, "show_draw_toolbar": show_tool}