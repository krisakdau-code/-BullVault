import streamlit as st
import requests

def to_clean_str(val) -> str:
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        for k in ["symbol", "ticker", "code", "name", "id"]:
            if k in val and isinstance(val[k], str):
                return val[k].strip()
        if len(val) > 0:
            first_val = list(val.values())[0]
            if isinstance(first_val, str):
                return first_val.strip()
    return str(val).strip() if val is not None else ""

@st.cache_data(ttl=10)
def fetch_mini_ticker_data(symbol_input) -> dict:
    sym = to_clean_str(symbol_input).upper()
    if not sym:
        return {"price": "--", "change": 0.0, "bid": "-", "ask": "-", "spread": "-"}

    headers = {"User-Agent": "Mozilla/5.0"}
    # 1. Bitkub
    if "_THB" in sym or sym.endswith("THB"):
        try:
            r = requests.get("https://api.bitkub.com/api/market/ticker", headers=headers, timeout=3).json()
            coin = sym.replace("_THB", "").replace("THB", "")
            key = f"THB_{coin}"
            if key in r:
                d = r[key]
                last = float(d.get("last", 0))
                change = float(d.get("percentChange", 0))
                bid = float(d.get("highestBid", 0))
                ask = float(d.get("lowestAsk", 0))
                spread = ask - bid if ask > bid else 0
                return {
                    "price": f"{last:,.2f}" if last < 1000 else f"{last:,.0f}",
                    "change": change,
                    "bid": f"{bid:,.0f}" if bid >= 100 else f"{bid:.2f}",
                    "ask": f"{ask:,.0f}" if ask >= 100 else f"{ask:.2f}",
                    "spread": f"{spread:.2f}"
                }
        except Exception:
            pass
    # 2. Binance
    elif "USDT" in sym:
        try:
            r = requests.get(f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={sym}", headers=headers, timeout=3).json()
            last = float(r.get("lastPrice", 0))
            change = float(r.get("priceChangePercent", 0))
            bid = float(r.get("bidPrice", 0))
            ask = float(r.get("askPrice", 0))
            spread = ask - bid if ask > bid else 0
            return {
                "price": f"{last:,.4f}" if last < 1 else f"{last:,.2f}",
                "change": change,
                "bid": f"{bid:.2f}",
                "ask": f"{ask:.2f}",
                "spread": f"{spread:.2f}"
            }
        except Exception:
            pass

    # 3. Yahoo Finance (หุ้นไทย / US / Forex)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d"
        r = requests.get(url, headers=headers, timeout=3).json()
        meta = r["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev = meta.get("chartPreviousClose", price)
        change = ((price - prev) / prev * 100) if prev else 0
        return {
            "price": f"{price:,.2f}",
            "change": change,
            "bid": "-", "ask": "-", "spread": "-"
        }
    except Exception:
        pass

    return {"price": "--", "change": 0.0, "bid": "-", "ask": "-", "spread": "-"}

def inject_tab_css():
    st.markdown(
        """
        <style>
        .tab-card {
            background-color: #0b0f19;
            border: 1px solid #1e2638;
            border-radius: 6px;
            padding: 8px 12px 6px 12px;
            margin-bottom: 4px;
            font-family: monospace;
        }
        .tab-card.active {
            border: 1.5px solid #00f0ff !important;
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
        }
        .tab-card-row1 {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
        }
        .tab-dot { color: #8b949e; font-size: 10px; margin: 0 4px; }
        .tab-price { color: #ffffff; }
        .chg-green { color: #00E676; font-size: 12px; }
        .chg-red { color: #FF5252; font-size: 12px; }
        .tab-card-row2 {
            display: flex;
            gap: 8px;
            font-size: 10px;
            margin-top: 3px;
        }
        .sub-bid { color: #00f0ff; }
        .sub-ask { color: #ff5252; }
        .sub-spread { color: #8b949e; }

        /* ปรับปุ่มใต้การ์ดให้อยู่ในระนาบเดียวกับรูปที่ 1 */
        div[data-testid="column"] div.stButton > button {
            width: 100% !important;
            min-height: 24px !important;
            height: 24px !important;
            padding: 1px 4px !important;
            font-size: 11px !important;
            border-radius: 4px !important;
            background-color: #121721 !important;
            border: 1px solid #252d3d !important;
            color: #c9d1d9 !important;
        }
        div[data-testid="column"] div.stButton > button:hover {
            border-color: #00f0ff !important;
            color: #00f0ff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_asset_tabs(symbols=None, state_key="current_symbol", *args, **kwargs) -> str:
    inject_tab_css()

    current = to_clean_str(st.session_state.get(state_key, "BTC_THB")) or "BTC_THB"
    st.session_state[state_key] = current
    st.session_state["selected_symbol"] = current

    if "open_tabs" not in st.session_state or not st.session_state["open_tabs"]:
        st.session_state["open_tabs"] = [
            {"id": "BTCUSDT", "symbol": "BTCUSDT"},
            {"id": current, "symbol": current}
        ]

    tabs = st.session_state["open_tabs"]
    cols = st.columns(len(tabs) + 1)

    for idx, tab_item in enumerate(tabs):
        sym = tab_item.get("symbol", tab_item.get("id", str(tab_item))) if isinstance(tab_item, dict) else str(tab_item)
        with cols[idx]:
            is_active = (sym == current)
            data = fetch_mini_ticker_data(sym)
            chg = data["change"]
            chg_cls = "chg-green" if chg >= 0 else "chg-red"
            chg_sign = "+" if chg >= 0 else ""
            active_cls = "active" if is_active else ""

            # 1. กล่องการ์ดด้านบน (เหมือนรูปที่ 1)
            st.markdown(
                f"""
                <div class="tab-card {active_cls}">
                    <div class="tab-card-row1">
                        <span>{sym}</span>
                        <span class="tab-dot">▪</span>
                        <span class="tab-price">{data['price']}</span>
                        <span class="{chg_cls}">{chg_sign}{chg:.2f}%</span>
                    </div>
                    <div class="tab-card-row2">
                        <span class="sub-bid">B {data['bid']}</span>
                        <span class="sub-ask">A {data['ask']}</span>
                        <span class="sub-spread">S {data['spread']}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 2. แถวปุ่มใต้การ์ด (ปุ่มสลับดูกราฟ + ปุ่มปิด X)
            c_view, c_del = st.columns([4, 1])
            with c_view:
                if is_active:
                    st.button("🟢 กำลังดู", key=f"act_tab_{idx}_{sym}", disabled=True, use_container_width=True)
                else:
                    if st.button("⚪ ดูกราฟ", key=f"sw_tab_{idx}_{sym}", use_container_width=True):
                        st.session_state["current_symbol"] = sym
                        st.rerun()

            with c_del:
                if len(tabs) > 1:
                    if st.button("✕", key=f"del_tab_{idx}_{sym}", use_container_width=True):
                        st.session_state["open_tabs"] = [
                            t for t in st.session_state["open_tabs"]
                            if (t.get("id") if isinstance(t, dict) else str(t)) != sym
                        ]
                        if current == sym:
                            first = st.session_state["open_tabs"][0]
                            new_sym = first.get("id") if isinstance(first, dict) else str(first)
                            st.session_state[state_key] = new_sym
                            st.session_state["selected_symbol"] = new_sym
                            st.session_state["current_symbol"] = new_sym
                        st.rerun()

    # 3. เมนูเพิ่มแท็บ (เชื่อมโยง ตลาด -> สินทรัพย์)
    with cols[-1]:
        st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)
        with st.popover("+ เพิ่มแท็บ ˅", use_container_width=True):
            st.markdown("**เลือกตลาดและสินทรัพย์:**")

            market_data = {
                "🇹🇭 Bitkub (THB)": ["BTC_THB", "ETH_THB", "KUB_THB", "USDT_THB", "DOGE_THB", "XRP_THB", "ADA_THB"],
                "🌐 Binance (USDT)": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT", "PEPEUSDT"],
                "📈 หุ้นไทย (SET)": ["DELTA.BK", "PTT.BK", "AOT.BK", "KBANK.BK", "CPALL.BK", "ADVANC.BK", "GULF.BK"],
                "🇺🇸 หุ้นสหรัฐฯ (US)": ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "META"],
                "💱 Forex & สินค้าโภคภัณฑ์": ["GC=F", "CL=F", "USDTHB=X", "EURUSD=X"]
            }

            selected_market = st.selectbox("เลือกตลาด:", list(market_data.keys()), key="pop_mkt_select")
            available_symbols = market_data[selected_market]
            selected_asset = st.selectbox("เลือกสินทรัพย์:", available_symbols, key="pop_sym_select")
            custom_sym = st.text_input("หรือระบุ Ticker เอง:", placeholder="เช่น BTCUSDT, AOT.BK", key="pop_custom_input")

            if st.button("ยืนยันเพิ่มแท็บ", use_container_width=True, key="pop_add_confirm_btn"):
                final_sym = to_clean_str(custom_sym).upper() if custom_sym else selected_asset
                current_ids = [t.get("id") if isinstance(t, dict) else str(t) for t in tabs]
                if final_sym and final_sym not in current_ids:
                    st.session_state["open_tabs"].append({"id": final_sym, "symbol": final_sym})
                    st.session_state[state_key] = final_sym
                    st.session_state["selected_symbol"] = final_sym
                    st.session_state["current_symbol"] = final_sym
                    st.rerun()

    return st.session_state.get(state_key, current)

asset_tab_bar = render_asset_tabs