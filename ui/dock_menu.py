import datetime
import streamlit as st
import symbols


def _safe_fetch(func_name: str, fallback: list[str]) -> list[str]:
    """เรียกฟังก์ชันจาก symbols.py อย่างปลอดภัย หากติด error หรือได้ลิสต์ว่างจะใช้ fallback ทันที"""
    try:
        if hasattr(symbols, func_name):
            res = getattr(symbols, func_name)()
            if res and isinstance(res, list) and len(res) > 0:
                return res
    except Exception:
        pass
    return fallback


def get_exchange_symbols(market: str, exchange: str) -> list[str]:
    """ดึงรายชื่อเหรียญ/หุ้นแบบสมบูรณ์ แยกตามตลาดและกระดานเทรดจริง"""
    m = (market or "").lower()
    ex = (exchange or "").lower()

    # 1. คริปโต
    if "คริปโต" in m or "crypto" in m:
        if "binance" in ex:
            return _safe_fetch("get_full_binance_symbols", [
                "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", 
                "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT", 
                "PEPEUSDT", "SHIBUSDT", "DOTUSDT", "LTCUSDT", "UNIUSDT"
            ])
        elif "bitkub" in ex:
            return _safe_fetch("get_full_bitkub_symbols", [
                "BTC_THB", "ETH_THB", "SOL_THB", "ADA_THB", "XRP_THB", "DOGE_THB", 
                "KUB_THB", "USDT_THB", "BNB_THB", "OP_THB", "ARB_THB", "NEAR_THB"
            ])
        elif "bybit" in ex:
            return _safe_fetch("get_full_bybit_symbols", [
                "BTCUSDT", "ETHUSDT", "SOLUSDT", "MNTUSDT", "XRPUSDT"
            ])
        elif "okx" in ex:
            return _safe_fetch("get_full_okx_symbols", [
                "BTC-USDT", "ETH-USDT", "SOL-USDT", "OKB-USDT", "XRP-USDT"
            ])
        else:
            return _safe_fetch("get_full_binance_symbols", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])

    # 2. หุ้นไทย
    elif "หุ้นไทย" in m or "thai" in m or "set" in m:
        return _safe_fetch("fetch_set_all_symbols", [
            "DELTA.BK", "PTT.BK", "AOT.BK", "ADVANC.BK", "GULF.BK", "PTTEP.BK", 
            "BDMS.BK", "CPALL.BK", "SCB.BK", "KBANK.BK", "TRUE.BK", "SCC.BK", 
            "BBL.BK", "CPAXT.BK", "BH.BK", "TIDLOR.BK", "MINT.BK", "HMPRO.BK", "IVL.BK", "MTC.BK"
        ])

    # 3. หุ้นสหรัฐฯ
    elif "สหรัฐ" in m or "us" in m or "sp500" in m:
        return _safe_fetch("get_full_sp500_symbols", [
            "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", 
            "NFLX", "INTC", "PLTR", "COIN", "AVGO", "QCOM", "BABA", "ARM", "MU"
        ])

    # 4. หุ้นจีน
    elif "จีน" in m or "china" in m:
        return _safe_fetch("get_full_china_stocks", [
            "0700.HK", "9988.HK", "3690.HK", "9618.HK", "9999.HK", "9888.HK", 
            "1810.HK", "2015.HK", "9866.HK", "9868.HK", "002594.SZ", "300750.SZ", "600519.SS", "601398.SS"
        ])

    # 5. หุ้นเวียดนาม
    elif "เวียดนาม" in m or "vietnam" in m or "vn" in m:
        return _safe_fetch("get_full_vietnam_symbols", [
            "VIC.VN", "VHM.VN", "HPG.VN", "FPT.VN", "VNM.VN", "MSN.VN", 
            "TCB.VN", "SSI.VN", "MBB.VN", "MWG.VN", "AAA.VN", "DGC.VN"
        ])

    # 6. สินค้าโภคภัณฑ์
    elif "โภคภัณฑ์" in m or "commodity" in m:
        return _safe_fetch("get_full_commodities", [
            "GC=F", "SI=F", "HG=F", "CL=F", "BZ=F", "NG=F", "PL=F", "PA=F"
        ])

    # 7. Forex
    elif "forex" in m or "fx" in m:
        return _safe_fetch("get_full_forex", [
            "USDTHB=X", "EURUSD=X", "USDJPY=X", "GBPUSD=X", "EURTHB=X", "JPYTHB=X"
        ])

    return ["BTCUSDT", "ETHUSDT"]


def inject_dock_css():
    st.markdown(
        """
        <style>
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            position: fixed !important;
            top: 14px !important;
            left: 12px !important;
            z-index: 9999999 !important;
            background-color: #131722 !important;
            border: 2px solid #089981 !important;
            border-radius: 50% !important;
            width: 42px !important;
            height: 42px !important;
            box-shadow: 0 0 12px rgba(8, 153, 129, 0.6) !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease-in-out !important;
        }
        [data-testid="stSidebarCollapsedControl"]:hover {
            transform: scale(1.08) !important;
            box-shadow: 0 0 18px rgba(8, 153, 129, 0.9) !important;
            background-color: #1e222d !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg {
            fill: #089981 !important;
            stroke: #089981 !important;
            width: 22px !important;
            height: 22px !important;
        }

        [data-testid="stSidebar"] {
            background-color: #0b0e14 !important;
            border-right: 1px solid #1f2430 !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding: 0.6rem 0.6rem 2rem 0.6rem !important;
        }

        div[data-testid="stPopoverBody"] {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            width: 440px !important;
            max-width: 90vw !important;
            max-height: 75vh !important;
            background-color: #131722 !important;
            border: 1px solid #2a2e39 !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.95) !important;
            overflow-y: auto !important;
            z-index: 999999 !important;
        }

        .main-dock div[data-testid="stPopover"] > button {
            border-radius: 50% !important;
            width: 50px !important;
            height: 50px !important;
            min-height: 50px !important;
            padding: 0 !important;
            margin: 6px auto !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background-color: #131722 !important;
            border: 1px solid #2a2e39 !important;
            color: #d1d4dc !important;
            font-size: 1.25rem !important;
            transition: all 0.2s ease-in-out !important;
        }
        .main-dock div[data-testid="stPopover"] > button:hover {
            border-color: #089981 !important;
            background-color: #1e222d !important;
            box-shadow: 0 0 12px rgba(8, 153, 129, 0.4) !important;
        }

        .status-badge {
            background: #131722;
            border: 1px solid #2a2e39;
            border-radius: 12px;
            padding: 8px 12px;
            margin-bottom: 12px;
        }
        .live-dot {
            height: 7px;
            width: 7px;
            background-color: #089981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 6px #089981;
        }
        .section-label {
            font-size: 11px;
            font-weight: 600;
            color: #787b86;
            margin: 10px 0 6px 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_drawing_toolbar():
    st.markdown('<div class="section-label">🎨 เครื่องมือวาดกราฟ</div>', unsafe_allow_html=True)
    st.toggle(
        "แสดงแถบเครื่องมือบนกราฟ",
        value=st.session_state.get("show_drawing_toolbar", True),
        key="show_drawing_toolbar",
    )


def render_dock_menu():
    inject_dock_css()

    now = datetime.datetime.now()
    st.markdown(
        f"""
        <div class="status-badge">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span style="font-size: 11px; color: #787b86;">🕒 UTC+7</span>
                <span style="font-size: 11px; color: #089981;"><span class="live-dot"></span> ออนไลน์</span>
            </div>
            <div style="font-size: 17px; font-weight: 700; color: #2962ff; font-family: monospace;">
                {now.strftime('%H:%M:%S')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_drawing_toolbar()

    st.divider()

    st.markdown('<div class="section-label">⚡ แผงควบคุมระบบ</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-dock">', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    # --- 🪙 หมวด 1: ตลาดและสินทรัพย์ ---
    with c1:
        with st.popover("🪙", help="ตลาด, กระดาน และสินทรัพย์"):
            st.markdown("### 🪙 ตลาดและสินทรัพย์")
            market = st.selectbox(
                "หมวดหมู่ตลาด",
                ["คริปโต (Crypto)", "หุ้นไทย", "หุ้นสหรัฐ", "หุ้นจีน", "หุ้นเวียดนาม", "Forex", "โภคภัณฑ์"],
                key="market_category"
            )

            # กรองกระดานเทรดตามหมวดหมู่
            if "คริปโต" in market:
                ex_options = ["Binance", "Bitkub", "Bybit", "OKX"]
            else:
                ex_options = ["Yahoo", "TradeStation"]

            exchange = st.selectbox(
                "กระดานเทรด", 
                ex_options, 
                key=f"dock_ex_{market}"
            )

            # ดึงรายชื่อเหรียญแบบไดนามิกตามตลาดและกระดานที่เลือกจริง
            asset_options = get_exchange_symbols(market, exchange)
            if not asset_options:
                asset_options = ["BTCUSDT", "ETHUSDT"]

            cur_selected = st.session_state.get("current_symbol")
            default_idx = asset_options.index(cur_selected) if cur_selected in asset_options else 0

            picked_symbol = st.selectbox(
                "เลือกสินทรัพย์:",
                asset_options,
                index=default_idx,
                key=f"dock_sym_{market}_{exchange}"
            )

            if picked_symbol != st.session_state.get("current_symbol"):
                st.session_state["current_symbol"] = picked_symbol
                st.session_state["selected_symbol"] = picked_symbol
                st.rerun()

            st.text_input("➕ เพิ่ม Ticker (เฉพาะกิจ):", placeholder="เช่น AAA.VN, PLTR", key="custom_ticker")
            if st.button("บันทึก Ticker", use_container_width=True, key="btn_save_custom_ticker"):
                st.toast("บันทึก Ticker สำเร็จ!")

            st.caption(f"⭐ ติดดาวกลุ่มสี: {st.session_state.get('selected_symbol', picked_symbol)}")
            w1, w2, w3, w4, w5 = st.columns(5)
            if w1.button("🔴", key="btn_tag_red"): st.session_state["tag_color"] = "red"
            if w2.button("🟡", key="btn_tag_yellow"): st.session_state["tag_color"] = "yellow"
            if w3.button("🟢", key="btn_tag_green"): st.session_state["tag_color"] = "green"
            if w4.button("🔵", key="btn_tag_blue"): st.session_state["tag_color"] = "blue"
            if w5.button("🟣", key="btn_tag_purple"): st.session_state["tag_color"] = "purple"

    # --- 📊 หมวด 2: การตั้งค่าตัวชี้วัด 3 แท็บ ---
    with c2:
        with st.popover("📊", help="การตั้งค่าตัวชี้วัด: ข้อมูล, รูปแบบ, การแสดงผล"):
            st.markdown("### ⚙️ การตั้งค่าตัวชี้วัด")
            tab_input, tab_style, tab_vis = st.tabs(["ข้อมูล", "รูปแบบ", "การแสดงผล"])

            with tab_input:
                st.markdown("**🔵 เครื่องมือ MACD**")
                st.number_input("Fast Length", value=12, min_value=1, key="macd_fast_len")
                st.number_input("Slow Length", value=26, min_value=1, key="macd_slow_len")
                st.number_input("ความยาวสัญญาณ (Signal)", value=9, min_value=1, key="macd_sig_len")
                st.selectbox("แหล่งที่มา (Source)", ["close", "open", "high", "low"], key="macd_source")

                st.divider()
                st.markdown("**🟢 เครื่องมือ RSI**")
                st.number_input("RSI Length", value=14, min_value=1, key="rsi_len")
                st.selectbox("RSI แหล่งที่มา (Source)", ["close", "open", "high", "low"], key="rsi_source")
                st.selectbox("ประเภทเส้นเฉลี่ย (RSI MA Type)", ["SMA", "EMA", "WMA"], key="rsi_ma_type")
                st.number_input("ความยาว RSI MA", value=14, min_value=1, key="rsi_ma_len")

                st.divider()
                st.markdown("**📈 เส้น EMA กราฟหลัก**")
                st.number_input("EMA Fast", value=12, min_value=1, key="ema_fast_len")
                st.number_input("EMA Slow", value=26, min_value=1, key="ema_slow_len")
                st.number_input("EMA Trend", value=200, min_value=1, key="ema_trend_len")

            with tab_style:
                st.markdown("**ฮิสโทแกรม MACD (4 สี)**")
                st.session_state["macd_show_hist"] = st.checkbox("เปิดแสดง ฮิสโทแกรม", value=True, key="cb_show_hist")
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    st.color_picker("สี 0 (บวกเพิ่ม)", "#00E676", key="macd_col_h0")
                    st.color_picker("สี 2 (ลบเพิ่ม)", "#FF5252", key="macd_col_h2")
                with col_h2:
                    st.color_picker("สี 1 (บวกลด)", "#00897B", key="macd_col_h1")
                    st.color_picker("สี 3 (ลบลด)", "#B71C1C", key="macd_col_h3")

                st.divider()
                st.markdown("**เส้น MACD & Signal**")
                st.color_picker("สี MACD Line", "#00E676", key="macd_col_line")
                st.slider("ความหนา MACD Line", 1, 4, 2, key="macd_lw_line")
                st.color_picker("สี Signal Line", "#FFD700", key="macd_col_sig")
                st.slider("ความหนา Signal Line", 1, 4, 2, key="macd_lw_sig")
                st.session_state["macd_show_zero"] = st.checkbox("แสดงเส้น 0 (Zero Line)", value=True, key="cb_show_zero")

                st.divider()
                st.markdown("**สไตล์ RSI**")
                st.color_picker("สีเส้น RSI", "#2962FF", key="rsi_col_line")
                st.slider("ความหนาเส้น RSI", 1, 4, 2, key="rsi_lw_line")
                st.session_state["rsi_show_ma"] = st.checkbox("แสดงเส้น RSI MA", value=True, key="cb_show_rsi_ma")
                st.color_picker("สีเส้น RSI MA", "#FF6D00", key="rsi_col_ma")
                st.number_input("ระดับบน (Upper Band)", value=70, key="rsi_band_70")
                st.number_input("ระดับกลาง (Middle Band)", value=50, key="rsi_band_50")
                st.number_input("ระดับล่าง (Lower Band)", value=30, key="rsi_band_30")

            with tab_vis:
                st.markdown("#### 👁️ เลือกระดับ Timeframe ที่ต้องการให้แสดง")
                st.checkbox("วินาที (Seconds)", value=True, key="vis_sec")
                st.checkbox("นาที (Minutes: 1m - 59m)", value=True, key="vis_min")
                st.checkbox("ชั่วโมง (Hours: 1h - 4h)", value=True, key="vis_hour")
                st.checkbox("วัน (Days: 1D)", value=True, key="vis_day")
                st.checkbox("สัปดาห์ / เดือน (Weeks & Months)", value=True, key="vis_week_month")

    # --- 📐 หมวด 3: Fibonacci Suite ---
    with c3:
        with st.popover("📐", help="ระบบคำนวณ Fibonacci Suite"):
            st.markdown("### 📐 Fibonacci Suite")
            if st.button("🔍 เปิดแผงวิเคราะห์ Fib (Pop-up)", use_container_width=True, key="btn_open_fib"):
                st.session_state["open_fib_popup"] = True
            st.slider("ความไวการหา Swing", 2, 20, value=5, key="fib_swing")
            st.slider("จำนวนแท่งวิเคราะห์", 50, 300, value=120, key="fib_bars")
            st.selectbox("ระดับ Fib เป้าหมายหลัก", ["1.618", "2.618", "0.618", "0.786"], key="fib_target")
            st.checkbox("ใช้ Golden Zone ยืนยันสัญญาณ BUY", key="fib_golden_zone")

    # --- ⚙️ หมวด 4: ระบบและหน้าจอ ---
    with c4:
        with st.popover("⚙️", help="แผงควบคุมระบบ และอุปกรณ์"):
            st.markdown("### ⚙️ แผงควบคุมระบบ")
            mode = st.radio("Display Mode", ["🖥️ Desktop", "📱 Mobile"], horizontal=True, label_visibility="collapsed", key="radio_dock_mode")
            st.session_state["device_mode"] = mode
            st.divider()
            if st.button("🧹 ล้างแคชระบบ", use_container_width=True, key="btn_dock_clear_cache"):
                st.cache_data.clear()
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)