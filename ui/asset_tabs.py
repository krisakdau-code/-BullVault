import streamlit as st
import requests


# ──────────────────────────────────────────────────────────
# 0. ฟังก์ชันทำความสะอาดรหัส Symbol
# ──────────────────────────────────────────────────────────
def to_clean_str(val) -> str:
    """แปลงค่าให้เป็น String Ticker เสมอ"""
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
            first_key = list(val.keys())[0]
            if isinstance(first_key, str):
                return first_key.strip()
    return str(val).strip() if val is not None else ""


# ──────────────────────────────────────────────────────────
# 1. ระบบดึงราคาแบบด่วน (Cache 10 วินาที)
# ──────────────────────────────────────────────────────────
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

    # 3. หุ้นไทย / สหรัฐฯ / Forex / โภคภัณฑ์ (Yahoo Finance)
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
            "bid": "-",
            "ask": "-",
            "spread": "-"
        }
    except Exception:
        pass

    return {"price": "--", "change": 0.0, "bid": "-", "ask": "-", "spread": "-"}


# ──────────────────────────────────────────────────────────
# 2. สไตล์ CSS รวมการ์ดและปุ่มเป็นหนึ่งเดียว
# ──────────────────────────────────────────────────────────
def inject_tab_card_css():
    st.markdown(
        """
        <style>
        .tab-box {
            background-color: #0d1117;
            border: 1px solid #1f2636;
            border-radius: 8px;
            padding: 8px 10px 6px 10px;
            margin-bottom: 4px;
            transition: all 0.2s ease-in-out;
        }
        .tab-box:hover {
            border-color: #2962ff;
        }
        .tab-box.active {
            background-color: #0b1726;
            border: 1.5px solid #00f0ff !important;
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.25);
        }
        .tab-top-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
            font-family: monospace;
        }
        .dot-icon { color: #787b86; margin: 0 4px; font-size: 10px; }
        .tab-price { color: #e0e3eb; }
        .tab-chg-up { color: #00E676; font-size: 11px; margin-left: 6px; }
        .tab-chg-down { color: #FF5252; font-size: 11px; margin-left: 6px; }
        .tab-sub-row {
            display: flex;
            gap: 8px;
            font-size: 10px;
            margin-top: 2px;
            margin-bottom: 6px;
            font-family: monospace;
        }
        .sub-b { color: #00f0ff; }
        .sub-a { color: #ff5252; }
        .sub-s { color: #787b86; }

        /* ปรับปุ่มใต้การ์ดให้แนบสนิท */
        div[data-testid="column"] div.stButton > button {
            width: 100% !important;
            padding: 1px 4px !important;
            min-height: 22px !important;
            height: 22px !important;
            font-size: 11px !important;
            border-radius: 4px !important;
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            color: #c9d1d9 !important;
        }
        div[data-testid="column"] div.stButton > button:hover {
            border-color: #00f0ff !important;
            color: #00f0ff !important;
            background-color: #1f242c !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────
# 3. ฟังก์ชันเรนเดอร์แท็บสินทรัพย์ (Unified Tab System)
# ──────────────────────────────────────────────────────────
def render_asset_tabs(symbols=None, state_key="current_symbol", *args, **kwargs) -> str:
    inject_tab_card_css()

    current = to_clean_str(st.session_state.get(state_key, "BTC_THB")) or "BTC_THB"
    st.session_state[state_key] = current
    st.session_state["selected_symbol"] = current
# ค่าเริ่มต้นสำหรับแท็บ (แปลงเป็น Dict รองรับ app.py line 781)
    if "open_tabs" not in st.session_state or not st.session_state["open_tabs"]:
        st.session_state["open_tabs"] = [
            {"id": current, "symbol": current},
            {"id": "BTCUSDT", "symbol": "BTCUSDT"}
        ]
    else:
        clean_tabs = []
        seen_ids = set()
        for item in st.session_state["open_tabs"]:
            sym_str = to_clean_str(item)
            if sym_str and sym_str not in seen_ids:
                seen_ids.add(sym_str)
                clean_tabs.append({"id": sym_str, "symbol": sym_str})
        st.session_state["open_tabs"] = clean_tabs if clean_tabs else [{"id": current, "symbol": current}]

    existing_ids = [t["id"] for t in st.session_state["open_tabs"]]
    if current not in existing_ids:
        st.session_state["open_tabs"].append({"id": current, "symbol": current})

    tabs = st.session_state["open_tabs"]
    cols = st.columns(len(tabs) + 1)

   # 1. แสดงแท็บแต่ละตัว
    for idx, tab_item in enumerate(tabs):
        sym = tab_item.get("symbol", tab_item.get("id", str(tab_item))) if isinstance(tab_item, dict) else str(tab_item)
        with cols[idx]:
            is_active = (sym == current)
            data = fetch_mini_ticker_data(sym)

            chg = data["change"]
            chg_class = "tab-chg-up" if chg >= 0 else "tab-chg-down"
            chg_sign = "+" if chg >= 0 else ""
            active_class = "active" if is_active else ""

            # กล่องการ์ดราคา
            st.markdown(
                f"""
                <div class="tab-box {active_class}">
                    <div class="tab-top-row">
                        <span>{sym}</span>
                        <span class="dot-icon">■</span>
                        <span class="tab-price">{data['price']}</span>
                        <span class="{chg_class}">{chg_sign}{chg:.2f}%</span>
                    </div>
                    <div class="tab-sub-row">
                        <span class="sub-b">B {data['bid']}</span>
                        <span class="sub-a">A {data['ask']}</span>
                        <span class="sub-s">S {data['spread']}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ปุ่มสลับดูกราฟ และปุ่มปิดแท็บ
            c_sel, c_close = st.columns([4, 1])
            with c_sel:
                if is_active:
                    st.button("🟢 กำลังดู", key=f"active_badge_{sym}", disabled=True, use_container_width=True)
                else:
                    if st.button("🔘 ดูกราฟ", key=f"btn_switch_{sym}", use_container_width=True):
                        st.session_state[state_key] = sym
                        st.session_state["selected_symbol"] = sym
                        st.session_state["current_symbol"] = sym
                        st.rerun()

            with c_close:
                if len(tabs) > 1:
                    if st.button("✕", key=f"btn_del_{sym}", use_container_width=True):
                        st.session_state["open_tabs"] = [
                            t for t in st.session_state["open_tabs"]
                            if (t.get("id") if isinstance(t, dict) else str(t)) != sym
                        ]
                        if current == sym:
                            first_tab = st.session_state["open_tabs"][0]
                            new_sym = first_tab.get("id") if isinstance(first_tab, dict) else str(first_tab)
                            st.session_state[state_key] = new_sym
                            st.session_state["selected_symbol"] = new_sym
                            st.session_state["current_symbol"] = new_sym
                        st.rerun()

    # 2. ปุ่มเพิ่มแท็บใหม่แบบ Popover
    with cols[-1]:
        st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)
        with st.popover("➕ เพิ่มแท็บ", use_container_width=True):
            st.markdown("**เลือกสินทรัพย์ที่ต้องการเปิดแท็บเพิ่ม:**")

            quick_pool = [
                "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT",
                "ETH_THB", "KUB_THB", "DELTA.BK", "PTT.BK", "NVDA", "AAPL", "GC=F", "USDTHB=X"
            ]
            current_ids = [t.get("id") if isinstance(t, dict) else str(t) for t in tabs]
            available_pool = [c for c in quick_pool if c not in current_ids]

            selected_add = st.selectbox("สินทรัพย์ยอดนิยม:", options=available_pool if available_pool else ["ETHUSDT"])
            custom_input = st.text_input("หรือพิมพ์รหัส Ticker เอง:", placeholder="เช่น SOLUSDT, AOT.BK")

            if st.button("ยืนยันเพิ่มแท็บ", use_container_width=True, key="btn_confirm_add_tab"):
                target_sym = to_clean_str(custom_input).upper() if custom_input else selected_add
                if target_sym and target_sym not in current_ids:
                    st.session_state["open_tabs"].append({"id": target_sym, "symbol": target_sym})
                    st.session_state[state_key] = target_sym
                    st.session_state["selected_symbol"] = target_sym
                    st.session_state["current_symbol"] = target_sym
                    st.rerun()

    return st.session_state.get(state_key, current)


# เชื่อมฟังก์ชันให้ app.py ใช้งานได้ทันที
asset_tab_bar = render_asset_tabs