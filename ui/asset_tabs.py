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
    elif "USDT" in sym:
        try:
            r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}", headers=headers, timeout=3).json()
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
    
    # รองรับหุ้น/Forex ผ่าน Yahoo Finance
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

def inject_tab_card_css():
    st.markdown(
        """
        <style>
        .terminal-tab-card {
            background-color: #0d1117;
            border: 1px solid #21262d;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 2px;
            font-family: monospace;
            position: relative;
        }
        .terminal-tab-card.active {
            background-color: #111a24;
            border: 1.5px solid #00f0ff !important;
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.25);
        }
        .tab-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
        }
        .tab-price-txt { color: #e0e3eb; font-family: monospace; }
        .chg-up { color: #00E676; font-size: 11px; }
        .chg-down { color: #FF5252; font-size: 11px; }
        .tab-bot {
            display: flex;
            gap: 8px;
            font-size: 10px;
            margin-top: 2px;
            color: #8b949e;
        }
        /* ซ่อนปุ่มสลับเดิมให้กลืนไปกับการคลิกการ์ด */
        div[data-testid="column"] div.stButton > button {
            width: 100% !important;
            padding: 2px 4px !important;
            min-height: 24px !important;
            font-size: 11px !important;
            border-radius: 4px !important;
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
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
    inject_tab_card_css()

    current = to_clean_str(st.session_state.get(state_key, "BTC_THB")) or "BTC_THB"
    st.session_state[state_key] = current
    st.session_state["selected_symbol"] = current

    if "open_tabs" not in st.session_state or not st.session_state["open_tabs"]:
        st.session_state["open_tabs"] = [{"id": current, "symbol": current}]
    
    tabs = st.session_state["open_tabs"]
    cols = st.columns(len(tabs) + 1)

    for idx, tab_item in enumerate(tabs):
        sym = tab_item.get("symbol", tab_item.get("id", str(tab_item))) if isinstance(tab_item, dict) else str(tab_item)
        with cols[idx]:
            is_active = (sym == current)
            data = fetch_mini_ticker_data(sym)
            chg = data["change"]
            chg_class = "chg-up" if chg >= 0 else "chg-down"
            chg_sign = "+" if chg >= 0 else ""
            active_class = "active" if is_active else ""

            # แสดงผลการ์ดแท็บดีไซน์นีออน
            st.markdown(
                f"""
                <div class="terminal-tab-card {active_class}">
                    <div class="tab-top">
                        <span>{"🟢 " if is_active else ""}{sym}</span>
                        <span class="tab-price-txt">{data['price']} <span class="{chg_class}">({chg_sign}{chg:.2f}%)</span></span>
                    </div>
                    <div class="tab-bot">
                        <span>B: {data['bid']}</span>
                        <span>A: {data['ask']}</span>
                        <span>Spread: {data['spread']}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ควบคุมการสลับและปุ่มปิดแบบ Inline ในแถวเดียวกัน
            c_switch, c_close = st.columns([5, 1])
            with c_switch:
                if not is_active:
                    if st.button("คลิกเพื่อดูกราฟ", key=f"switch_card_{idx}_{sym}", use_container_width=True):
                        st.session_state[state_key] = sym
                        st.session_state["selected_symbol"] = sym
                        st.session_state["current_symbol"] = sym
                        st.rerun()
                else:
                    st.button("กำลังแสดงผล", key=f"active_badge_{idx}_{sym}", disabled=True, use_container_width=True)

            with c_close:
                if len(tabs) > 1:
                    if st.button("✕", key=f"close_card_{idx}_{sym}", use_container_width=True):
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

    # ช่องขวาสุด: ปุ่มเพิ่มแท็บ (Popover)
    with cols[-1]:
        st.markdown('<div style="height: 2px;"></div>', unsafe_allow_html=True)
        with st.popover("➕ เพิ่มแท็บสินทรัพย์", use_container_width=True):
            st.markdown("**เลือกหรือพิมพ์รหัสสินทรัพย์ที่ต้องการเปิดเพิ่ม:**")
            pool = ["ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ETH_THB", "KUB_THB", "PTT.BK", "NVDA", "AAPL"]
            current_ids = [t.get("id") if isinstance(t, dict) else str(t) for t in tabs]
            available = [c for c in pool if c not in current_ids]

            chosen = st.selectbox("รายการยอดนิยม:", options=available if available else ["ETHUSDT"])
            custom = st.text_input("ระบุ Ticker เอง:", placeholder="เช่น SOLUSDT")

            if st.button("ยืนยันเปิดแท็บใหม่", use_container_width=True, key="confirm_add_tab_btn"):
                target = to_clean_str(custom).upper() if custom else chosen
                if target and target not in current_ids:
                    st.session_state["open_tabs"].append({"id": target, "symbol": target})
                    st.session_state[state_key] = target
                    st.session_state["selected_symbol"] = target
                    st.session_state["current_symbol"] = target
                    st.rerun()

    return st.session_state.get(state_key, current)

asset_tab_bar = render_asset_tabs