# ui/chart_settings_modal.py
import streamlit as st

def init_settings_state():
    defaults = {
        # สวิตช์เปิด/ปิด 3 บานหน้าต่าง
        "show_main_chart": True,
        "show_rsi_pane": True,
        "show_macd_pane": True,

        # กราฟหลักและสเกล
        "candle_up": "#089981",
        "candle_down": "#F23645",
        "candle_border_up": "#089981",
        "candle_border_down": "#F23645",
        "candle_wick_up": "#089981",
        "candle_wick_down": "#F23645",
        "chart_prev_close_bar": True,
        "chart_precision": "ค่าเริ่มต้น",
        "chart_timezone": "(UTC+7) กรุงเทพ",

        # บรรทัดสถานะ
        "status_logo": True,
        "status_symbol_name": True,
        "status_market_status": True,
        "status_ohlc": True,
        "status_volume": True,
        "status_change": True,

        # สเกลและเส้น
        "scale_last_price": True,
        "scale_countdown": False,
        "scale_high_low": False,
        "scale_bid_ask": False,

        # ผ้าใบ
        "canvas_bg_color": "#000000",
        "canvas_grid_v": True,
        "canvas_grid_h": True,
        "canvas_crosshair": True,

        # ---------------- RSI TradingView มาตรฐานเต็ม ----------------
        # แท็บข้อมูล
        "rsi_length": 14,
        "rsi_source": "ปิด",
        "rsi_calc_divergence": False,
        "rsi_ma_type": "SMA",
        "rsi_ma_length": 14,
        "rsi_bb_stddev": 2.0,
        "rsi_tf": "ชาร์ต",
        "rsi_wait_close": True,

        # แท็บรูปแบบ (Style)
        "rsi_show_line": True,
        "rsi_line_color": "#7E57C2",
        "rsi_show_ma": True,
        "rsi_ma_color": "#FFEB3B",
        "rsi_show_upper": True,
        "rsi_upper_band": 70,
        "rsi_upper_color": "#787B86",
        "rsi_show_middle": True,
        "rsi_middle_band": 50,
        "rsi_middle_color": "#434651",
        "rsi_show_lower": True,
        "rsi_lower_band": 30,
        "rsi_lower_color": "#787B86",
        "rsi_fill_bg": True,
        "rsi_fill_color": "#2A2E39",
        "rsi_ob_gradient": True,
        "rsi_ob_c1": "#089981",
        "rsi_ob_c2": "#1E222D",
        "rsi_os_gradient": True,
        "rsi_os_c1": "#1E222D",
        "rsi_os_c2": "#F23645",
        "rsi_precision": "ค่าเริ่มต้น",
        "rsi_show_price_label": True,
        "rsi_show_status_val": True,
        "rsi_show_status_in": True,

        # แท็บการแสดงผล RSI
        "rsi_vis_ticks": True,
        "rsi_vis_sec": True,
        "rsi_vis_min": True,
        "rsi_vis_hour": True,
        "rsi_vis_day": True,
        "rsi_vis_week": True,
        "rsi_vis_month": True,
        "rsi_vis_ranges": True,

        # ---------------- MACD ----------------
        "macd_tf": "ชาร์ต",
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "macd_source": "ปิด",
        "macd_wait_close": True,
        "macd_hist_c0": "#00FFA3",
        "macd_hist_c1": "#005A36",
        "macd_hist_c2": "#FF3B69",
        "macd_hist_c3": "#66001B",
        "macd_line_color": "#00FFA3",
        "macd_signal_color": "#FFEB3B",
        "macd_cross_bull": True,
        "macd_cross_bear": True,
        "macd_zero_line": True,

        "settings_current_tab": "🕯️ สัญลักษณ์",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


@st.dialog("การตั้งค่า", width="large")
def show_chart_settings_dialog():
    init_settings_state()

    # ล้างสีฟ้าออกเด็ดขาด: เปลี่ยนเป็นเขียวนีออน #00FFA3 ทั้งหมด
    st.markdown("""
    <style>
    div[data-testid="stDialog"] div[role="dialog"] {
        background-color: #131722 !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 10px !important;
        color: #d1d4dc !important;
    }
    div[data-testid="stDialog"] div[data-testid="column"]:first-child button[kind="primary"] {
        background-color: rgba(0, 255, 163, 0.15) !important;
        border: 1px solid #00FFA3 !important;
        color: #00FFA3 !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(0, 255, 163, 0.25) !important;
    }
    div[data-testid="stDialog"] div[data-testid="column"]:first-child button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #8f9cae !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stDialog"] div[data-testid="column"]:first-child button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
    }
    div[data-testid="stDialog"] div[data-baseweb="tab-highlight"] {
        background-color: #00FFA3 !important;
    }
    div[data-testid="stDialog"] button[role="tab"][aria-selected="true"] {
        color: #00FFA3 !important;
        font-weight: bold !important;
    }
    div[data-testid="stDialog"] div[data-baseweb="checkbox"] span[aria-checked="true"] {
        background-color: #00FFA3 !important;
        border-color: #00FFA3 !important;
    }
    div[data-testid="stDialog"] div[class*="st-key-btn_dlg_ok"] button {
        background-color: #00FFA3 !important;
        border: 1px solid #00FFA3 !important;
        color: #000000 !important;
        font-weight: 800 !important;
        box-shadow: 0 0 12px rgba(0, 255, 163, 0.4) !important;
    }
    div[data-testid="stDialog"] div[class*="st-key-btn_dlg_ok"] button:hover {
        background-color: #00e08f !important;
        box-shadow: 0 0 18px rgba(0, 255, 163, 0.6) !important;
    }
    div[data-testid="stColorPicker"] label {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    c_nav, c_divider, c_content = st.columns([2.8, 0.1, 7.1])

    with c_nav:
        st.markdown('<div style="font-size:11px; color:#787b86; font-weight:700; margin-bottom:6px;">กราฟและผ้าใบ</div>', unsafe_allow_html=True)
        for sec in ["🕯️ สัญลักษณ์", "📜 บรรทัดสถานะ", "📐 สเกลและเส้น", "🎨 ผ้าใบ"]:
            is_active = (st.session_state["settings_current_tab"] == sec)
            btn_type = "primary" if is_active else "secondary"
            if st.button(sec, key=f"nav_{sec}", type=btn_type, use_container_width=True):
                st.session_state["settings_current_tab"] = sec

        st.markdown('<div style="font-size:11px; color:#787b86; font-weight:700; margin:16px 0 6px 0;">อินดิเคเตอร์</div>', unsafe_allow_html=True)
        for sec in ["📈 RSI", "📊 MACD"]:
            is_active = (st.session_state["settings_current_tab"] == sec)
            btn_type = "primary" if is_active else "secondary"
            if st.button(sec, key=f"nav_{sec}", type=btn_type, use_container_width=True):
                st.session_state["settings_current_tab"] = sec

    with c_divider:
        st.markdown("""<div style="border-left: 1px solid #2a2e39; height: 500px;"></div>""", unsafe_allow_html=True)

    with c_content:
        active = st.session_state["settings_current_tab"]

        # ---------------- 1. สัญลักษณ์ ----------------
        if active == "🕯️ สัญลักษณ์":
            st.session_state["show_main_chart"] = st.checkbox("เปิดแสดงบานกราฟแท่งเทียนหลัก (Main Chart)", value=st.session_state["show_main_chart"])
            st.session_state["chart_prev_close_bar"] = st.checkbox("สีของ Bars อ้างอิงจากราคาปิดก่อนหน้า", value=st.session_state["chart_prev_close_bar"])

            st.write("### แท่งเทียน")
            r1_c1, r1_c2, r1_c3 = st.columns([4, 3, 3])
            with r1_c1: st.write("บอดี้")
            with r1_c2: st.session_state["candle_up"] = st.color_picker("บอดี้ขึ้น", st.session_state["candle_up"], key="cp_c_up")
            with r1_c3: st.session_state["candle_down"] = st.color_picker("บอดี้ลง", st.session_state["candle_down"], key="cp_c_dn")

            r2_c1, r2_c2, r2_c3 = st.columns([4, 3, 3])
            with r2_c1: st.write("เส้นขอบ")
            with r2_c2: st.session_state["candle_border_up"] = st.color_picker("ขอบขึ้น", st.session_state["candle_border_up"], key="cp_b_up")
            with r2_c3: st.session_state["candle_border_down"] = st.color_picker("ขอบลง", st.session_state["candle_border_down"], key="cp_b_dn")

            r3_c1, r3_c2, r3_c3 = st.columns([4, 3, 3])
            with r3_c1: st.write("ไส้เทียน")
            with r3_c2: st.session_state["candle_wick_up"] = st.color_picker("ไส้ขึ้น", st.session_state["candle_wick_up"], key="cp_w_up")
            with r3_c3: st.session_state["candle_wick_down"] = st.color_picker("ไส้ลง", st.session_state["candle_wick_down"], key="cp_w_dn")

        # ---------------- 2. บรรทัดสถานะ ----------------
        elif active == "📜 บรรทัดสถานะ":
            st.write("### ตราสาร")
            st.session_state["status_logo"] = st.checkbox("โลโก้สินทรัพย์", value=st.session_state["status_logo"])
            st.session_state["status_symbol_name"] = st.checkbox("ชื่อสัญลักษณ์", value=st.session_state["status_symbol_name"])
            st.session_state["status_market_status"] = st.checkbox("สถานะตลาดเปิด/ปิด", value=st.session_state["status_market_status"])
            st.session_state["status_ohlc"] = st.checkbox("ค่าของชาร์ต (OHLC)", value=st.session_state["status_ohlc"])
            st.session_state["status_change"] = st.checkbox("ค่าการเปลี่ยนแปลงวันล่าสุด (%)", value=st.session_state["status_change"])
            st.session_state["status_volume"] = st.checkbox("ปริมาณการซื้อขาย (Volume)", value=st.session_state["status_volume"])

        # ---------------- 3. สเกลและเส้น ----------------
        elif active == "📐 สเกลและเส้น":
            st.write("### ป้ายราคา & เส้น")
            st.session_state["scale_last_price"] = st.checkbox("เส้นราคาปิดล่าสุด (Last Price Line)", value=st.session_state["scale_last_price"])
            st.session_state["scale_countdown"] = st.checkbox("นับถอยหลังไปยังราคาปิดของแท่ง (Countdown)", value=st.session_state["scale_countdown"])
            st.session_state["scale_high_low"] = st.checkbox("ป้ายราคาสูงและต่ำของวัน", value=st.session_state["scale_high_low"])
            st.session_state["scale_bid_ask"] = st.checkbox("เส้น Bid และ Ask", value=st.session_state["scale_bid_ask"])

        # ---------------- 4. ผ้าใบ ----------------
        elif active == "🎨 ผ้าใบ":
            st.write("### พื้นผิวชาร์ต")
            bg_col1, bg_col2 = st.columns([5, 5])
            with bg_col1: st.write("สีพื้นหลังชาร์ต")
            with bg_col2: st.session_state["canvas_bg_color"] = st.color_picker("สีพื้นหลัง", st.session_state["canvas_bg_color"], key="cp_canvas_bg")
            st.session_state["canvas_grid_v"] = st.checkbox("เส้นตารางแนวตั้ง (Vertical Grid)", value=st.session_state["canvas_grid_v"])
            st.session_state["canvas_grid_h"] = st.checkbox("เส้นตารางแนวนอน (Horizontal Grid)", value=st.session_state["canvas_grid_h"])
            st.session_state["canvas_crosshair"] = st.checkbox("เส้นเล็งกากบาท (Crosshair)", value=st.session_state["canvas_crosshair"])

        # ---------------- 5. RSI (ถอดแบบ TradingView 100%) ----------------
        elif active == "📈 RSI":
            st.session_state["show_rsi_pane"] = st.checkbox("เปิดแสดงหน้าต่าง RSI (Sub-pane)", value=st.session_state["show_rsi_pane"])
            rsi_tabs = st.tabs(["ข้อมูล", "รูปแบบ", "การแสดงผล"])

            # 1. แท็บข้อมูล (Inputs)
            with rsi_tabs[0]:
                st.markdown('<div style="font-size:11px; color:#787b86; font-weight:700; margin-bottom:4px;">ตั้งค่า RSI</div>', unsafe_allow_html=True)
                st.session_state["rsi_length"] = st.number_input("ความยาว RSI", min_value=1, max_value=200, value=st.session_state["rsi_length"])
                st.session_state["rsi_source"] = st.selectbox("แหล่งที่มา", ["ปิด", "เปิด", "สูงสุด", "ต่ำสุด", "hl2", "hlc3", "ohlc4"], index=0)
                st.session_state["rsi_calc_divergence"] = st.checkbox("คำนวณ Divergence", value=st.session_state["rsi_calc_divergence"])

                st.markdown('<div style="font-size:11px; color:#787b86; font-weight:700; margin:16px 0 4px 0;">ความราบเรียบ</div>', unsafe_allow_html=True)
                st.session_state["rsi_ma_type"] = st.selectbox("ประเภท", ["SMA", "EMA", "WMA", "Bollinger Bands"], index=0)
                st.session_state["rsi_ma_length"] = st.number_input("ความยาว", min_value=1, max_value=100, value=st.session_state["rsi_ma_length"])
                if st.session_state["rsi_ma_type"] == "Bollinger Bands":
                    st.session_state["rsi_bb_stddev"] = st.number_input("BB StdDev", min_value=0.1, max_value=5.0, value=float(st.session_state["rsi_bb_stddev"]))

                st.markdown('<div style="font-size:11px; color:#787b86; font-weight:700; margin:16px 0 4px 0;">การคำนวณ</div>', unsafe_allow_html=True)
                st.session_state["rsi_tf"] = st.selectbox("ไทม์เฟรม", ["ชาร์ต", "1 นาที", "5 นาที", "15 นาที", "1 ชั่วโมง", "1 วัน"], index=0)
                st.session_state["rsi_wait_close"] = st.checkbox("รอให้จบไทม์เฟรม", value=st.session_state["rsi_wait_close"])

            # 2. แท็บรูปแบบ (Style)
            with rsi_tabs[1]:
                # เส้น RSI
                c_rsi1, c_rsi2 = st.columns([6, 4])
                with c_rsi1: st.session_state["rsi_show_line"] = st.checkbox("RSI", value=st.session_state["rsi_show_line"])
                with c_rsi2: st.session_state["rsi_line_color"] = st.color_picker("สี RSI", st.session_state["rsi_line_color"], key="cp_r_line")

                # เส้น RSI-based MA
                c_ma1, c_ma2 = st.columns([6, 4])
                with c_ma1: st.session_state["rsi_show_ma"] = st.checkbox("RSI-based MA", value=st.session_state["rsi_show_ma"])
                with c_ma2: st.session_state["rsi_ma_color"] = st.color_picker("สี RSI MA", st.session_state["rsi_ma_color"], key="cp_r_ma")

                # Upper Band
                u_col1, u_col2, u_col3 = st.columns([4.5, 2.5, 3])
                with u_col1: st.session_state["rsi_show_upper"] = st.checkbox("RSI Upper Band", value=st.session_state["rsi_show_upper"])
                with u_col2: st.session_state["rsi_upper_color"] = st.color_picker("สี Upper", st.session_state["rsi_upper_color"], key="cp_r_up")
                with u_col3: st.session_state["rsi_upper_band"] = st.number_input("UB", value=st.session_state["rsi_upper_band"], label_visibility="collapsed")

                # Middle Band
                m_col1, m_col2, m_col3 = st.columns([4.5, 2.5, 3])
                with m_col1: st.session_state["rsi_show_middle"] = st.checkbox("RSI Middle Band", value=st.session_state["rsi_show_middle"])
                with m_col2: st.session_state["rsi_middle_color"] = st.color_picker("สี Middle", st.session_state["rsi_middle_color"], key="cp_r_mid")
                with m_col3: st.session_state["rsi_middle_band"] = st.number_input("MB", value=st.session_state["rsi_middle_band"], label_visibility="collapsed")

                # Lower Band
                l_col1, l_col2, l_col3 = st.columns([4.5, 2.5, 3])
                with l_col1: st.session_state["rsi_show_lower"] = st.checkbox("RSI Lower Band", value=st.session_state["rsi_show_lower"])
                with l_col2: st.session_state["rsi_lower_color"] = st.color_picker("สี Lower", st.session_state["rsi_lower_color"], key="cp_r_low")
                with l_col3: st.session_state["rsi_lower_band"] = st.number_input("LB", value=st.session_state["rsi_lower_band"], label_visibility="collapsed")

                # Background Fills
                bf_c1, bf_c2 = st.columns([6, 4])
                with bf_c1: st.session_state["rsi_fill_bg"] = st.checkbox("RSI Background Fill", value=st.session_state["rsi_fill_bg"])
                with bf_c2: st.session_state["rsi_fill_color"] = st.color_picker("สี Fill", st.session_state["rsi_fill_color"], key="cp_r_bgfill")

                # Overbought Gradient Fill
                ob_c1, ob_c2, ob_c3 = st.columns([5, 2.5, 2.5])
                with ob_c1: st.session_state["rsi_ob_gradient"] = st.checkbox("Overbought Gradient Fill", value=st.session_state["rsi_ob_gradient"])
                with ob_c2: st.session_state["rsi_ob_c1"] = st.color_picker("OB C1", st.session_state["rsi_ob_c1"], key="cp_ob_1")
                with ob_c3: st.session_state["rsi_ob_c2"] = st.color_picker("OB C2", st.session_state["rsi_ob_c2"], key="cp_ob_2")

                # Oversold Gradient Fill
                os_c1, os_c2, os_c3 = st.columns([5, 2.5, 2.5])
                with os_c1: st.session_state["rsi_os_gradient"] = st.checkbox("Oversold Gradient Fill", value=st.session_state["rsi_os_gradient"])
                with os_c2: st.session_state["rsi_os_c1"] = st.color_picker("OS C1", st.session_state["rsi_os_c1"], key="cp_os_1")
                with os_c3: st.session_state["rsi_os_c2"] = st.color_picker("OS C2", st.session_state["rsi_os_c2"], key="cp_os_2")

                st.markdown('<div style="font-size:11px; color:#787b86; font-weight:700; margin:16px 0 4px 0;">ค่า OUTPUT</div>', unsafe_allow_html=True)
                st.session_state["rsi_precision"] = st.selectbox("ความแม่นยำ", ["ค่าเริ่มต้น", "2 ตำแหน่ง", "4 ตำแหน่ง"], index=0)
                st.session_state["rsi_show_price_label"] = st.checkbox("ป้ายกำกับระดับราคา", value=st.session_state["rsi_show_price_label"])
                st.session_state["rsi_show_status_val"] = st.checkbox("ค่าในบรรทัดสถานะ", value=st.session_state["rsi_show_status_val"])

                st.markdown('<div style="font-size:11px; color:#787b86; font-weight:700; margin:12px 0 4px 0;">ค่า INPUT</div>', unsafe_allow_html=True)
                st.session_state["rsi_show_status_in"] = st.checkbox("Input ในบรรทัดสถานะ", value=st.session_state["rsi_show_status_in"])

            # 3. แท็บการแสดงผล (Visibility)
            with rsi_tabs[2]:
                st.session_state["rsi_vis_ticks"] = st.checkbox("Ticks", value=st.session_state["rsi_vis_ticks"])
                st.session_state["rsi_vis_sec"] = st.checkbox("วินาที (1-59)", value=st.session_state["rsi_vis_sec"])
                st.session_state["rsi_vis_min"] = st.checkbox("นาที (1-59)", value=st.session_state["rsi_vis_min"])
                st.session_state["rsi_vis_hour"] = st.checkbox("ชั่วโมง (1-24)", value=st.session_state["rsi_vis_hour"])
                st.session_state["rsi_vis_day"] = st.checkbox("วัน (1-366)", value=st.session_state["rsi_vis_day"])
                st.session_state["rsi_vis_week"] = st.checkbox("สัปดาห์ (1-52)", value=st.session_state["rsi_vis_week"])
                st.session_state["rsi_vis_month"] = st.checkbox("เดือน (1-12)", value=st.session_state["rsi_vis_month"])
                st.session_state["rsi_vis_ranges"] = st.checkbox("Ranges", value=st.session_state["rsi_vis_ranges"])

        # ---------------- 6. MACD ----------------
        elif active == "📊 MACD":
            st.session_state["show_macd_pane"] = st.checkbox("เปิดแสดงหน้าต่าง MACD (Sub-pane)", value=st.session_state["show_macd_pane"])
            macd_tabs = st.tabs(["ข้อมูล", "รูปแบบ", "การแสดงผล"])

            with macd_tabs[0]:
                st.session_state["macd_tf"] = st.selectbox("Timeframe", ["ชาร์ต", "1 นาที", "5 นาที", "15 นาที", "1 ชั่วโมง", "1 วัน"], index=0)
                st.session_state["macd_fast"] = st.number_input("Fast Length", min_value=1, max_value=100, value=st.session_state["macd_fast"])
                st.session_state["macd_slow"] = st.number_input("Slow Length", min_value=1, max_value=200, value=st.session_state["macd_slow"])
                st.session_state["macd_signal"] = st.number_input("ความยาวของสัญญาณ (Signal)", min_value=1, max_value=100, value=st.session_state["macd_signal"])
                st.session_state["macd_source"] = st.selectbox("แหล่งที่มา", ["ปิด (Close)", "เปิด (Open)", "สูงสุด (High)", "ต่ำสุด (Low)"], index=0)
                st.session_state["macd_wait_close"] = st.checkbox("รอให้จบไทม์เฟรม (Wait for bar close)", value=st.session_state["macd_wait_close"])

            with macd_tabs[1]:
                st.write("### ฮิสโตแกรม 4 เฉดสี")
                h_c1, h_c2 = st.columns(2)
                with h_c1:
                    st.session_state["macd_hist_c0"] = st.color_picker("สี 0 (บวกเพิ่มขึ้น)", st.session_state["macd_hist_c0"], key="cp_m_c0")
                    st.session_state["macd_hist_c1"] = st.color_picker("สี 1 (บวกอ่อนแรง)", st.session_state["macd_hist_c1"], key="cp_m_c1")
                with h_c2:
                    st.session_state["macd_hist_c2"] = st.color_picker("สี 2 (ลบทวีความแรง)", st.session_state["macd_hist_c2"], key="cp_m_c2")
                    st.session_state["macd_hist_c3"] = st.color_picker("สี 3 (ลบชะลอตัว)", st.session_state["macd_hist_c3"], key="cp_m_c3")

                st.write("### เส้นสัญญาณ")
                l_c1, l_c2 = st.columns(2)
                with l_c1:
                    st.session_state["macd_line_color"] = st.color_picker("MACD Line", st.session_state["macd_line_color"], key="cp_m_line")
                with l_c2:
                    st.session_state["macd_signal_color"] = st.color_picker("Signal Line", st.session_state["macd_signal_color"], key="cp_m_sig")

                st.session_state["macd_cross_bull"] = st.checkbox("Bullish Cross (จุดตัดขึ้น)", value=st.session_state["macd_cross_bull"])
                st.session_state["macd_cross_bear"] = st.checkbox("Bearish Cross (จุดตัดลง)", value=st.session_state["macd_cross_bear"])
                st.session_state["macd_zero_line"] = st.checkbox("เส้น 0 (Zero Line)", value=st.session_state["macd_zero_line"])

            with macd_tabs[2]:
                st.checkbox("Ticks", value=True)
                st.checkbox("นาที (1-59)", value=True)
                st.checkbox("ชั่วโมง (1-24)", value=True)
                st.checkbox("วัน (1-366)", value=True)

    st.markdown("""<div style="margin-top: 24px; border-top: 1px solid #2a2e39; padding-top: 12px;"></div>""", unsafe_allow_html=True)
    f_left, f_right = st.columns([4, 6])

    with f_left:
        if st.button("ค่าเริ่มต้น ▾", key="btn_reset_defaults", help="คืนค่าการตั้งค่ามาตรฐานทั้งหมด"):
            st.session_state.clear()
            init_settings_state()
            st.rerun()

    with f_right:
        b_canc, b_ok = st.columns(2)
        with b_canc:
            if st.button("ยกเลิก", use_container_width=True, key="btn_dlg_cancel"):
                st.rerun()
        with b_ok:
            if st.button("ตกลง", type="primary", use_container_width=True, key="btn_dlg_ok"):
                st.session_state["chart_force_refresh"] = st.session_state.get("chart_force_refresh", 0) + 1
                st.rerun()