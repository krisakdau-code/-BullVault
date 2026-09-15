# ui/sidebar_refactored.py
import os
import json
from datetime import datetime, timezone, timedelta
import streamlit as st

try:
    from data.rice_ohlcv import get_rice_symbols_list
except ImportError:
    def get_rice_symbols_list():
        return ["RICE:ข้าวเปลือกเจ้า", "RICE:ข้าวเปลือกหอมมะลิ", "FOB:ข้าวสารขาว 100%", "ZR=F (CBOT Rough Rice)"]


def load_json_symbols(filename, fallback):
    path = os.path.join("data", filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return list(data.keys()) if isinstance(data, dict) else data
        except Exception:
            pass
    return fallback


def set_active_symbol(sym_code):
    st.session_state["current_symbol"] = sym_code
    st.session_state["app_mode"] = "chart"
    is_r = sym_code.startswith("RICE:") or sym_code.startswith("FOB:") or sym_code == "ZR=F (CBOT Rough Rice)"
    tf_val = "1D" if is_r else st.session_state.get("selected_tf", "1h")
    if is_r:
        st.session_state["selected_tf"] = "1D"

    if "open_tabs" not in st.session_state or not st.session_state.open_tabs:
        import uuid
        new_id = uuid.uuid4().hex[:8]
        st.session_state.open_tabs = [{"id": new_id, "symbol": sym_code, "tf": tf_val}]
        st.session_state.active_tab_id = new_id
    else:
        active_id = st.session_state.get("active_tab_id")
        updated = False
        for t in st.session_state.open_tabs:
            if t.get("id") == active_id:
                t["symbol"] = sym_code
                if is_r:
                    t["tf"] = "1D"
                updated = True
                break
        if not updated:
            st.session_state.open_tabs[0]["symbol"] = sym_code
            if is_r:
                st.session_state.open_tabs[0]["tf"] = "1D"
            st.session_state.active_tab_id = st.session_state.open_tabs[0]["id"]


def render_sidebar():
    # -------------------------------------------------------------
    # 1. จัดการ State และกลุ่มสีโปรด (Favorite Color Groups)
    # -------------------------------------------------------------
    if "favorite_colors" not in st.session_state:
        st.session_state["favorite_colors"] = {
            "red": ["BTCUSDT"],
            "orange": ["ETHUSDT"],
            "yellow": [],
            "green": ["DELTA.BK", "ข้าวหอม 100%"],
            "blue": ["SOLUSDT"],
            "purple": ["GC=F"]
        }
    if "active_cat" not in st.session_state:
        st.session_state["active_cat"] = "Crypto"
    if "active_exch" not in st.session_state:
        st.session_state["active_exch"] = "Binance Spot"

    cur_sym = st.session_state.get("current_symbol", "BTCUSDT")

    # -------------------------------------------------------------
    # 2. คลังข้อมูลสินทรัพย์จริงทุกกระดาน
    # -------------------------------------------------------------
    all_markets = {
        "Crypto": {
            "Binance Spot": {"badge": "BINANCE", "symbols": load_json_symbols("binance_crypto.json", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"])},
            "Binance TH": {"badge": "BINANCE TH", "symbols": load_json_symbols("binance_th_crypto.json", ["BTC_THB", "ETH_THB", "USDT_THB", "SOL_THB", "BNB_THB"])},
            "OKX": {"badge": "OKX", "symbols": load_json_symbols("okx_crypto.json", ["BTC-USDT", "ETH-USDT", "SOL-USDT", "OKB-USDT", "PEPE-USDT"])},
            "KuCoin": {"badge": "KUCOIN", "symbols": load_json_symbols("kucoin_crypto.json", ["BTC-USDT", "ETH-USDT", "KCS-USDT", "SOL-USDT"])},
            "Bitkub (THB)": {"badge": "BITKUB", "symbols": load_json_symbols("bitkub_crypto.json", ["BTC_THB", "ETH_THB", "KUB_THB", "SOL_THB", "USDT_THB"])},
            "Bybit": {"badge": "BYBIT", "symbols": load_json_symbols("bybit_crypto.json", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "MNTUSDT"])}
        },
        "หุ้นไทย (SET)": {
            "SET Index": {"badge": "SET", "symbols": load_json_symbols("thai_stocks.json", ["DELTA.BK", "PTT.BK", "AOT.BK", "KBANK.BK", "SCB.BK", "ADVANC.BK"])},
            "mai": {"badge": "MAI", "symbols": ["AU.BK", "DEXON.BK", "KLINIQ.BK", "SPA.BK", "MASTER.BK"]},
            "TFEX": {"badge": "TFEX", "symbols": ["S50=F", "GO=F"]}
        },
        "หุ้นนอก / Forex": {
            "สหรัฐฯ (US)": {"badge": "US", "symbols": load_json_symbols("us_stocks.json", ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD", "COIN", "PLTR"])},
            "จีน/ฮ่องกง": {"badge": "CHINA", "symbols": load_json_symbols("china_stocks.json", ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "BABA", "BIDU"])},
            "เวียดนาม (VN)": {"badge": "VIETNAM", "symbols": load_json_symbols("vietnam_stocks.json", ["VNM.VN", "VIC.VN", "HPG.VN", "VCB.VN", "FPT.VN", "MSN.VN"])},
            "Forex": {"badge": "FOREX", "symbols": load_json_symbols("forex.json", ["USDTHB=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"])}
        },
        "สินค้าเกษตร/โภคภัณฑ์": {
            "สมาคมโรงสีข้าว": {"badge": "RICE", "symbols": get_rice_symbols_list()},
            "ส่งออก (FOB)": {"badge": "FOB", "symbols": ["FOB:ข้าวสารขาว 100%", "FOB:ข้าวนึ่ง 100%", "FOB:ข้าวหอมมะลิไทย"]},
            "CBOT ข้าว": {"badge": "CBOT", "symbols": ["ZR=F (CBOT Rough Rice)", "ZC=F (Corn)", "ZS=F (Soybean)"]},
            "โลหะมีค่า (Gold)": {"badge": "METALS", "symbols": ["GC=F", "SI=F", "PL=F"]},
            "พลังงาน (Energy)": {"badge": "ENERGY", "symbols": ["CL=F", "BZ=F", "NG=F"]}
        }
    }

    # ตรวจสอบความถูกต้องของหมวดหมู่และกระดานที่เปิดอยู่
    cur_cat = st.session_state["active_cat"]
    if cur_cat not in all_markets:
        cur_cat = "Crypto"
        st.session_state["active_cat"] = cur_cat

    cur_exch = st.session_state["active_exch"]
    if cur_exch not in all_markets[cur_cat]:
        cur_exch = list(all_markets[cur_cat].keys())[0]
        st.session_state["active_exch"] = cur_exch

    available_symbols = all_markets[cur_cat][cur_exch]["symbols"]
    exch_badge = all_markets[cur_cat][cur_exch]["badge"]

    # -------------------------------------------------------------
    # 3. ตกแต่ง Native Streamlit ด้วย Cyber Theme CSS
    # -------------------------------------------------------------
    with st.sidebar:
        st.markdown("""
        <style>
        div[data-testid="stSidebarContent"] {
            background-color: #06080E !important;
            padding: 10px 12px 15px 12px !important;
        }
        /* Tab Header */
        div[data-testid="stSidebar"] div[data-baseweb="tab-list"] {
            gap: 6px !important;
            background: #0B0E14 !important;
            padding: 4px !important;
            border-radius: 8px !important;
            border: 1px solid #1A202C !important;
            margin-bottom: 12px !important;
        }
        div[data-testid="stSidebar"] button[data-baseweb="tab"] {
            border-radius: 6px !important;
            padding: 6px 12px !important;
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
            box-shadow: 0 0 10px rgba(255, 122, 0, 0.35) !important;
        }
        div[data-testid="stSidebar"] button[data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
            background: rgba(0, 255, 163, 0.12) !important;
            border: 1px solid #00FFA3 !important;
            color: #00FFA3 !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.35) !important;
        }
        /* Buttons styling */
        div[data-testid="stSidebar"] div.stButton > button {
            background: #0B0E14 !important;
            border: 1px solid #1F2633 !important;
            color: #8F9CAE !important;
            border-radius: 6px !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            padding: 4px 6px !important;
            height: auto !important;
            transition: all 0.15s ease !important;
        }
        div[data-testid="stSidebar"] div.stButton > button:hover {
            border-color: #00FFA3 !important;
            color: #FFFFFF !important;
            background: #111724 !important;
        }
        /* Active Category Cyber Buttons */
        div[data-testid="stSidebar"] div.cat-active > div.stButton > button {
            background: rgba(255, 122, 0, 0.15) !important;
            border: 1.5px solid #FF7A00 !important;
            color: #FF9400 !important;
            box-shadow: 0 0 8px rgba(255, 122, 0, 0.3) !important;
        }
        /* Active Exchange Pill */
        div[data-testid="stSidebar"] div.exch-active > div.stButton > button {
            background: rgba(0, 255, 163, 0.15) !important;
            border: 1.5px solid #00FFA3 !important;
            color: #00FFA3 !important;
            box-shadow: 0 0 8px rgba(0, 255, 163, 0.3) !important;
        }
        /* Selectbox styling */
        div[data-testid="stSidebar"] div[data-baseweb="select"] {
            background-color: #0B0E14 !important;
            border: 1.5px solid #FF7A00 !important;
            border-radius: 6px !important;
            box-shadow: 0 0 8px rgba(255, 122, 0, 0.2) !important;
        }
        div[data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #FFFFFF !important;
            font-size: 12px !important;
            font-weight: 700 !important;
        }
        /* Watchlist active card glow */
        div[data-testid="stSidebar"] div.card-active > div.stButton > button {
            background: #111724 !important;
            border: 1.5px solid #00FFA3 !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 10px rgba(0, 255, 163, 0.35) !important;
        }
        /* Cyber Labels */
        .cyber-header-orange {
            color: #FF9400; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; margin: 10px 0 5px 0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .cyber-header-green {
            color: #00FFA3; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; margin: 12px 0 6px 0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .cyber-badge-orange {
            background: rgba(255, 122, 0, 0.15); border: 1px solid #FF7A00; color: #FF9400;
            font-size: 8.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px;
        }
        .cyber-badge-green {
            background: rgba(0, 255, 163, 0.15); border: 1px solid #00FFA3; color: #00FFA3;
            font-size: 8.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px;
        }
        .clock-container {
            margin-top: 14px; background: #0B0E14; border: 1px solid #1A202C; border-radius: 6px;
            padding: 6px 10px; display: flex; justify-content: space-between; align-items: center;
            font-family: monospace; font-size: 10.5px; color: #8F9CAE;
        }
        </style>
        """, unsafe_allow_html=True)

        tab_market, tab_tools = st.tabs(["🔍 ตลาด & ค้นหา", "🟢 เครื่องมือ & อินดี้ (3)"])

        # =============================================================
        # แท็บ 1: ระบบเลือก 3 ชั้น (Native) + Watchlist + กลุ่มสีโปรด
        # =============================================================
        with tab_market:
            # ----------------- ชั้นที่ 1: Category Grid 2x2 -----------------
            st.markdown('<div class="cyber-header-orange"><span>⚡ ค้นหาด่วน (CATEGORIES 2x2)</span></div>', unsafe_allow_html=True)

            cat_keys = ["Crypto", "หุ้นไทย (SET)", "หุ้นนอก / Forex", "สินค้าเกษตร/โภคภัณฑ์"]
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                is_active = (cur_cat == cat_keys[0])
                st.markdown(f'<div class="{"cat-active" if is_active else ""}">', unsafe_allow_html=True)
                if st.button("🪙 Crypto", key="cat_btn_0", use_container_width=True):
                    st.session_state["active_cat"] = cat_keys[0]
                    st.session_state["active_exch"] = "Binance Spot"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with r1c2:
                is_active = (cur_cat == cat_keys[1])
                st.markdown(f'<div class="{"cat-active" if is_active else ""}">', unsafe_allow_html=True)
                if st.button("🇹🇭 หุ้นไทย (SET)", key="cat_btn_1", use_container_width=True):
                    st.session_state["active_cat"] = cat_keys[1]
                    st.session_state["active_exch"] = "SET Index"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            r2c1, r2c2 = st.columns(2)
            with r2c1:
                is_active = (cur_cat == cat_keys[2])
                st.markdown(f'<div class="{"cat-active" if is_active else ""}">', unsafe_allow_html=True)
                if st.button("🌐 หุ้นนอก/Forex", key="cat_btn_2", use_container_width=True):
                    st.session_state["active_cat"] = cat_keys[2]
                    st.session_state["active_exch"] = "สหรัฐฯ (US)"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with r2c2:
                is_active = (cur_cat == cat_keys[3])
                st.markdown(f'<div class="{"cat-active" if is_active else ""}">', unsafe_allow_html=True)
                if st.button("🌾 เกษตร/โภคภัณฑ์", key="cat_btn_3", use_container_width=True):
                    st.session_state["active_cat"] = cat_keys[3]
                    st.session_state["active_exch"] = "สมาคมโรงสีข้าว"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # ----------------- ชั้นที่ 2: Exchange Cascading Pills -----------------
            st.markdown('<div class="cyber-header-orange" style="font-size:10px; color:#8F9CAE;">EXCHANGE SELECTOR</div>', unsafe_allow_html=True)
            exchs = list(all_markets[cur_cat].keys())
            exch_cols = st.columns(len(exchs))
            for i, ex in enumerate(exchs):
                with exch_cols[i]:
                    is_active = (ex == cur_exch)
                    st.markdown(f'<div class="{"exch-active" if is_active else ""}">', unsafe_allow_html=True)
                    # แสดงชื่อสั้นบนปุ่ม
                    short_name = ex.replace("Index", "").replace("Spot", "").strip()
                    if st.button(short_name, key=f"exch_btn_{i}", use_container_width=True):
                        st.session_state["active_exch"] = ex
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # ----------------- ชั้นที่ 3: ช่องค้นหาสินทรัพย์ + ป้าย Badge -----------------
            st.markdown(f'<div class="cyber-header-orange"><span>🔍 สินทรัพย์</span><span class="cyber-badge-orange">{exch_badge}</span></div>', unsafe_allow_html=True)

            search_opts = list(available_symbols)
            if cur_sym not in search_opts:
                search_opts.insert(0, cur_sym)

            chosen = st.selectbox(
                label="เลือกสินทรัพย์",
                options=search_opts,
                index=search_opts.index(cur_sym),
                key="native_symbol_selector",
                label_visibility="collapsed"
            )
            if chosen != cur_sym:
                set_active_symbol(chosen)
                st.rerun()

            # ----------------- ส่วนที่ 2: Selected Watchlist + Two-Way Sync -----------------
            st.markdown("""
            <div class="cyber-header-green">
                <span>📌 รายการติดตาม (WATCHLIST & SYNC)</span>
                <span class="cyber-badge-green">AUTO-SYNC</span>
            </div>
            """, unsafe_allow_html=True)

            # รวบรวมสินทรัพย์ใน Watchlist
            watchlist = []
            if "open_tabs" in st.session_state and st.session_state.open_tabs:
                for t in st.session_state.open_tabs:
                    if t.get("symbol") and t["symbol"] not in watchlist:
                        watchlist.append(t["symbol"])

            default_tracked = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "GC=F", "NVDA", "DELTA.BK", "ข้าวหอม 100%"]
            for s in default_tracked:
                if s not in watchlist:
                    watchlist.append(s)

            # เรนเดอร์การ์ดสินทรัพย์ (Native Buttons + Color Picker)
            quotes = st.session_state.get("quotes_dict", {})
            color_emojis = {"red": "🔴", "orange": "🟠", "yellow": "🟡", "green": "🟢", "blue": "🔵", "purple": "🟣"}

            for idx, sym in enumerate(watchlist):
                is_active = (sym == cur_sym)
                q = quotes.get(sym, {})
                price = q.get("price", 0.0)
                chg = q.get("change", 0.0)

                # ข้อมูลจำลองหากยังไม่มี Feed
                if price == 0.0:
                    mock_p = {"BTCUSDT": 79036.15, "ETHUSDT": 2645.80, "SOLUSDT": 184.25, "BNBUSDT": 588.50, "GC=F": 2684.50, "NVDA": 142.30, "DELTA.BK": 82.50, "ข้าวหอม 100%": 545.00}
                    mock_c = {"BTCUSDT": 2.27, "ETHUSDT": 3.14, "SOLUSDT": 5.42, "BNBUSDT": -0.85, "GC=F": 0.45, "NVDA": -1.12, "DELTA.BK": 1.25, "ข้าวหอม 100%": 0.00}
                    price = mock_p.get(sym, 100.0)
                    chg = mock_c.get(sym, 0.0)

                sign = "+" if chg >= 0 else ""
                chg_str = f"{sign}{chg:.2f}%"

                # ค้นหาว่าเหรียญนี้อยู่กลุ่มสีไหน
                assigned_color = None
                for c_name, sym_list in st.session_state["favorite_colors"].items():
                    if sym in sym_list:
                        assigned_color = c_name
                        break
                color_dot = color_emojis.get(assigned_color, "⚪")

                c_card, c_tag = st.columns([8.2, 1.8])
                with c_card:
                    st.markdown(f'<div class="{"card-active" if is_active else ""}">', unsafe_allow_html=True)
                    btn_label = f"{sym:<11} | {price:,.2f} ({chg_str})"
                    if st.button(btn_label, key=f"wl_sym_{idx}_{sym}", use_container_width=True):
                        set_active_symbol(sym)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                with c_tag:
                    # ป๊อปอัพจัดการกลุ่มสีโปรดและการถอดสี
                    with st.popover(color_dot):
                        st.markdown(f"**🏷️ กลุ่มสี: {sym}**")
                        cols_picker = st.columns(3)
                        for c_i, (c_k, c_emo) in enumerate(color_emojis.items()):
                            with cols_picker[c_i % 3]:
                                if st.button(c_emo, key=f"set_col_{sym}_{c_k}"):
                                    # ลบออกจากกลุ่มสีเดิมทั้งหมดก่อน
                                    for group in st.session_state["favorite_colors"].values():
                                        if sym in group:
                                            group.remove(sym)
                                    # เพิ่มเข้ากลุ่มสีใหม่
                                    st.session_state["favorite_colors"][c_k].append(sym)
                                    st.rerun()
                        if assigned_color:
                            st.divider()
                            if st.button("🗑️ ถอดออกจากกลุ่มสี", key=f"del_col_{sym}", use_container_width=True):
                                for group in st.session_state["favorite_colors"].values():
                                    if sym in group:
                                        group.remove(sym)
                                st.rerun()

            # ----------------- สวิตช์ควบคุมส่วนล่าง (Native Toggles) -----------------
            st.divider()
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                cur_draw = st.session_state.get("show_draw_toolbar", True)
                new_draw = st.toggle("แถบวาดรูป", value=cur_draw, key="native_draw_toggle")
                if new_draw != cur_draw:
                    st.session_state["show_draw_toolbar"] = new_draw
                    st.rerun()

            with t_col2:
                cur_top = st.session_state.get("show_top_bar", True)
                new_top = st.toggle("แถบบน (Top)", value=cur_top, key="native_top_toggle")
                if new_top != cur_top:
                    st.session_state["show_top_bar"] = new_top
                    st.rerun()

            # นาฬิกา BKK UTC+7
            now_bkk = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S")
            st.markdown(f"""
            <div class="clock-container">
                <span>🕒 BKK (UTC+7) {now_bkk}</span>
                <span class="cyber-badge-green">LIVE</span>
            </div>
            """, unsafe_allow_html=True)

        # =============================================================
        # แท็บ 2: เครื่องมือ & อินดี้ (3)
        # =============================================================
        with tab_tools:
            st.markdown("""
            <div class="cyber-header-green">
                <span>⚡ เครื่องมือระบบ (ICON LAUNCHERS)</span>
            </div>
            """, unsafe_allow_html=True)

            i1, i2, i3, i4 = st.columns(4)
            with i1:
                if st.button("📐", help="Fibonacci Suite & Golden Zone", use_container_width=True):
                    st.session_state["trigger_fib_modal"] = True
                    st.rerun()
            with i2:
                if st.button("📊", help="วิเคราะห์ตลาด 24h", use_container_width=True):
                    st.session_state["trigger_market_modal"] = True
                    st.rerun()
            with i3:
                if st.button("🌾", help="กราฟราคาข้าวไทย", use_container_width=True):
                    st.session_state["app_mode"] = "rice"
                    st.rerun()
            with i4:
                if st.button("🟣", help="ปรับแต่งสไตล์กราฟและธีม", use_container_width=True):
                    st.session_state["trigger_settings_modal"] = True
                    st.rerun()

            st.markdown("""
            <div class="cyber-header-green" style="margin-top:14px;">
                <span>⚙️ อินดิเคเตอร์ที่เปิดใช้งาน</span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📈 เส้นค่าเฉลี่ย EMA Ribbon", expanded=True):
                st.caption("Fast EMA: 7 | Slow EMA: 15 | Trend EMA: 45")
            with st.expander("📈 พารามิเตอร์ RSI (14)", expanded=False):
                st.caption("Upper Band: 70 | Lower Band: 30 | สี: #00FFA3")
            with st.expander("📊 พารามิเตอร์ MACD (12, 26, 9)", expanded=False):
                st.caption("Fast: 12 | Slow: 26 | Signal: 9")

            now_bkk2 = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S")
            st.markdown(f"""
            <div class="clock-container" style="margin-top:20px;">
                <span>🕒 BKK (UTC+7) {now_bkk2}</span>
                <span class="cyber-badge-green">LIVE</span>
            </div>
            """, unsafe_allow_html=True)

    return {
        "show_top_bar": st.session_state.get("show_top_bar", True),
        "show_draw_toolbar": st.session_state.get("show_draw_toolbar", True)
    }