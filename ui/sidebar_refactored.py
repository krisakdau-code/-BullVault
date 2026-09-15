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
    # 1. State Management & Favorite Colors
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
    # 2. Catalogs
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
    # 3. Sidebar Body (ไม่ฝัง CSS ทับซ้อน ปล่อยให้ theme.py คุมทั้งหมด)
    # -------------------------------------------------------------
    with st.container():
        tab_market, tab_tools = st.tabs(["🔍 ตลาด & ค้นหา", "🟢 เครื่องมือ & อินดี้ (3)"])

        # =============================================================
        # แท็บ 1: ระบบ 3 ชั้น + Watchlist
        # =============================================================
        with tab_market:
            # 1. Category 2x2
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
                if st.button("🇹🇭 หุ้นไทย", key="cat_btn_1", use_container_width=True):
                    st.session_state["active_cat"] = cat_keys[1]
                    st.session_state["active_exch"] = "SET Index"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            r2c1, r2c2 = st.columns(2)
            with r2c1:
                is_active = (cur_cat == cat_keys[2])
                st.markdown(f'<div class="{"cat-active" if is_active else ""}">', unsafe_allow_html=True)
                if st.button("🌐 หุ้นนอก/FX", key="cat_btn_2", use_container_width=True):
                    st.session_state["active_cat"] = cat_keys[2]
                    st.session_state["active_exch"] = "สหรัฐฯ (US)"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with r2c2:
                is_active = (cur_cat == cat_keys[3])
                st.markdown(f'<div class="{"cat-active" if is_active else ""}">', unsafe_allow_html=True)
                if st.button("🌾 เกษตร/ทอง", key="cat_btn_3", use_container_width=True):
                    st.session_state["active_cat"] = cat_keys[3]
                    st.session_state["active_exch"] = "สมาคมโรงสีข้าว"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # 2. กระดานเทรด (Exchange Selector)
            st.markdown('<div class="cyber-header-orange" style="font-size:9.5px; color:#8F9CAE;"><span>EXCHANGE SELECTOR</span></div>', unsafe_allow_html=True)
            exchs = list(all_markets[cur_cat].keys())
            with st.container(height=100):
                for i, ex in enumerate(exchs):
                    is_active = (ex == cur_exch)
                    st.markdown(f'<div class="{"exch-active" if is_active else "exch-inactive"}">', unsafe_allow_html=True)
                    btn_txt = f"🟢 {ex}" if is_active else f"▫️ {ex}"
                    if st.button(btn_txt, key=f"v_exch_btn_{i}_{ex}", use_container_width=True):
                        st.session_state["active_exch"] = ex
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # 3. Dropdown สินทรัพย์
            st.markdown(f'<div class="cyber-header-orange"><span>🔍 สินทรัพย์</span><span class="cyber-badge-orange">{exch_badge}</span></div>', unsafe_allow_html=True)
            search_opts = list(available_symbols)
            if cur_sym not in search_opts:
                search_opts.insert(0, cur_sym)

            idx_cur = search_opts.index(cur_sym) if cur_sym in search_opts else 0
            chosen = st.selectbox(
                label="เลือกสินทรัพย์",
                options=search_opts,
                index=idx_cur,
                key="native_symbol_selector",
                label_visibility="collapsed"
            )
            if chosen != cur_sym:
                set_active_symbol(chosen)
                st.rerun()

            # 4. รายการติดตาม Watchlist (Two-Way Auto Sync)
            st.markdown("""
            <div class="cyber-header-green">
                <span>📌 รายการติดตาม (SELECTED)</span>
                <span class="cyber-badge-green">AUTO-SYNC</span>
            </div>
            """, unsafe_allow_html=True)

            watchlist = []
            if "open_tabs" in st.session_state and st.session_state.open_tabs:
                for t in st.session_state.open_tabs:
                    if t.get("symbol") and t["symbol"] not in watchlist:
                        watchlist.append(t["symbol"])

            default_tracked = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "GC=F", "NVDA", "DELTA.BK", "ข้าวหอม 100%"]
            for s in default_tracked:
                if s not in watchlist:
                    watchlist.append(s)

            quotes = st.session_state.get("quotes_dict", {})
            color_emojis = {"red": "🔴", "orange": "🟠", "yellow": "🟡", "green": "🟢", "blue": "🔵", "purple": "🟣"}

            with st.container(height=250):
                for idx, sym in enumerate(watchlist):
                    is_active = (sym == cur_sym)
                    q = quotes.get(sym, {})
                    price = q.get("price", 0.0)
                    chg = q.get("change", 0.0)

                    if price == 0.0:
                        mock_p = {"BTCUSDT": 79036.15, "ETHUSDT": 2645.80, "SOLUSDT": 184.25, "BNBUSDT": 588.50, "GC=F": 2684.50, "NVDA": 142.30, "DELTA.BK": 82.50, "ข้าวหอม 100%": 545.00}
                        mock_c = {"BTCUSDT": 2.27, "ETHUSDT": 3.14, "SOLUSDT": 5.42, "BNBUSDT": -0.85, "GC=F": 0.45, "NVDA": -1.12, "DELTA.BK": 1.25, "ข้าวหอม 100%": 0.00}
                        price = mock_p.get(sym, 100.0)
                        chg = mock_c.get(sym, 0.0)

                    sign = "+" if chg >= 0 else ""
                    chg_str = f"{sign}{chg:.2f}%"

                    assigned_color = None
                    for c_name, sym_list in st.session_state["favorite_colors"].items():
                        if sym in sym_list:
                            assigned_color = c_name
                            break
                    color_dot = color_emojis.get(assigned_color, "⚪")

                    c_card, c_tag = st.columns([8.6, 1.4])
                    with c_card:
                        st.markdown(f'<div class="{"card-active" if is_active else ""}">', unsafe_allow_html=True)
                        btn_label = f"{sym}  {price:,.2f}  {chg_str}"
                        if st.button(btn_label, key=f"wl_sym_{idx}_{sym}", use_container_width=True):
                            set_active_symbol(sym)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    with c_tag:
                        with st.popover(color_dot):
                            st.markdown(f"**🏷️ กลุ่มสี: {sym}**")
                            cols_picker = st.columns(3)
                            for c_i, (c_k, c_emo) in enumerate(color_emojis.items()):
                                with cols_picker[c_i % 3]:
                                    if st.button(c_emo, key=f"set_col_{sym}_{c_k}"):
                                        for group in st.session_state["favorite_colors"].values():
                                            if sym in group:
                                                group.remove(sym)
                                        st.session_state["favorite_colors"][c_k].append(sym)
                                        st.rerun()
                            if assigned_color:
                                st.divider()
                                if st.button("🗑️ เอาออกจากกลุ่มสี", key=f"del_col_{sym}", use_container_width=True):
                                    for group in st.session_state["favorite_colors"].values():
                                        if sym in group:
                                            group.remove(sym)
                                    st.rerun()

            # 5. สวิตช์เปิด/ปิด ล่างสุด
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
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
            st.markdown('<div class="cyber-header-green"><span>⚡ เครื่องมือระบบ (QUICK TOOLS)</span></div>', unsafe_allow_html=True)

            i1, i2, i3, i4 = st.columns(4)
            with i1:
                if st.button("📐", key="tb_fib", use_container_width=True):
                    st.session_state["trigger_fib_modal"] = True
                    st.rerun()
            with i2:
                if st.button("📊", key="tb_mkt", use_container_width=True):
                    st.session_state["trigger_market_modal"] = True
                    st.rerun()
            with i3:
                if st.button("🌾", key="tb_rice", use_container_width=True):
                    st.session_state["app_mode"] = "rice"
                    st.rerun()
            with i4:
                if st.button("🟣", key="tb_thm", use_container_width=True):
                    st.session_state["trigger_settings_modal"] = True
                    st.rerun()

            st.markdown("""
            <div style="background:#0B0E14; border:1px solid #1F2633; border-radius:5px; padding:4px 6px; margin:6px 0 12px 0; font-size:9px; color:#8F9CAE; display:flex; justify-content:space-around;">
                <span>📐 ฟิโบ</span><span>|</span><span>📊 ตลาด 24h</span><span>|</span><span>🌾 ราคาข้าว</span><span>|</span><span>🟣 ธีม/กราฟ</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="cyber-header-green"><span>⚙️ อินดิเคเตอร์ที่เปิดใช้งาน</span></div>', unsafe_allow_html=True)

            with st.expander("📈 เส้นค่าเฉลี่ย EMA Ribbon", expanded=True):
                st.caption("Fast EMA: 7 | Slow EMA: 15 | Trend EMA: 45")
            with st.expander("📈 พารามิเตอร์ RSI (14)", expanded=False):
                st.caption("Upper Band: 70 | Lower Band: 30 | สี: #00FFA3")
            with st.expander("📊 พารามิเตอร์ MACD (12, 26, 9)", expanded=False):
                st.caption("Fast: 12 | Slow: 26 | Signal: 9")

            now_bkk2 = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S")
            st.markdown(f"""
            <div class="clock-container" style="margin-top:16px;">
                <span>🕒 BKK (UTC+7) {now_bkk2}</span>
                <span class="cyber-badge-green">LIVE</span>
            </div>
            """, unsafe_allow_html=True)

    return {
        "show_top_bar": st.session_state.get("show_top_bar", True),
        "show_draw_toolbar": st.session_state.get("show_draw_toolbar", True)
    }