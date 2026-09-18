import streamlit as st
# 1. กำหนดโครงสร้างพารามิเตอร์เริ่มต้นของอินดิเคเตอร์ทั้ง 11 ตัว
INDICATOR_CATALOG = {
    "Trend (บนกราฟราคา)": {
        "EMA": {
            "name": "Moving Average (EMA/SMA/WMA)",
            "overlay": True,
            "inputs": {"type": "EMA", "length": 20, "source": "Close"},
            "style": {"color": "#2962ff", "width": 2, "line_type": "Solid"}
        },
        "BB": {
            "name": "Bollinger Bands",
            "overlay": True,
            "inputs": {"length": 20, "std_dev": 2.0, "ma_type": "SMA", "source": "Close"},
            "style": {"color": "#2962ff", "fill_color": "rgba(41, 98, 255, 0.1)", "width": 1}
        },
        "ST": {
            "name": "Supertrend",
            "overlay": True,
            "inputs": {"atr_len": 10, "factor": 3.0},
            "style": {"up_color": "#00e676", "down_color": "#ff5252", "width": 2}
        },
        "ICHI": {
            "name": "Ichimoku Cloud",
            "overlay": True,
            "inputs": {"conversion": 9, "base": 26, "span_b": 52, "displacement": 26},
            "style": {"lead_a_color": "#00e676", "lead_b_color": "#ff5252"}
        },
        "VWAP": {
            "name": "VWAP",
            "overlay": True,
            "inputs": {"source": "HLC3", "anchor": "Session"},
            "style": {"color": "#ff9800", "width": 2}
        }
    },
    "Momentum (หน้าต่างแยก)": {
        "RSI": {
            "name": "Relative Strength Index (RSI)",
            "overlay": False,
            "inputs": {"length": 14, "source": "Close", "ob": 70, "os": 30},
            "style": {"color": "#7e57c2", "width": 2}
        },
        "MACD": {
            "name": "MACD",
            "overlay": False,
            "inputs": {"fast": 12, "slow": 26, "signal": 9, "source": "Close"},
            "style": {"fast_color": "#2962ff", "slow_color": "#ff6d00", "hist_up": "#26a69a", "hist_dn": "#ef5350"}
        },
        "STOCH": {
            "name": "Stochastic Oscillator",
            "overlay": False,
            "inputs": {"k_len": 14, "d_smooth": 3, "k_smooth": 3, "ob": 80, "os": 20},
            "style": {"k_color": "#2196f3", "d_color": "#ff5252", "width": 1}
        }
    },
    "Volatility & Volume (ความผันผวนและปริมาณ)": {
        "ATR": {
            "name": "Average True Range (ATR)",
            "overlay": False,
            "inputs": {"length": 14, "smoothing": "RMA"},
            "style": {"color": "#ff5252", "width": 2}
        },
        "ADX": {
            "name": "ADX / DMI",
            "overlay": False,
            "inputs": {"di_len": 14, "adx_smooth": 14, "threshold": 25},
            "style": {"adx_color": "#ff9800", "plus_di": "#00e676", "minus_di": "#ff5252", "width": 2}
        },
        "VOL": {
            "name": "Volume & Volume MA",
            "overlay": False,
            "inputs": {"ma_len": 20},
            "style": {"up_color": "#089981", "down_color": "#f23645", "ma_color": "#ff9800"}
        }
    }
}

PRICE_SOURCES = ["Close", "Open", "High", "Low", "HL2", "HLC3", "OHLC4"]

# 2. ฟังก์ชันโมดอลขนาดใหญ่พิเศษ width="large"
@st.dialog("⚙️ การตั้งค่าระบบและชาร์ต (Unified Settings)", width="large")
def show_chart_settings_dialog():
    tab_chart, tab_ind, tab_ui = st.tabs([
        "🎨 กราฟ & ธีม",
        "📈 คลังอินดิเคเตอร์",
        "🖥️ พื้นที่ทำงาน"
    ])

    with tab_chart:
        st.caption("โทนสีแท่งเทียนและพื้นหลัง")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state["candle_up_color"] = st.color_picker("แท่งขึ้น (Bullish)", value=st.session_state.get("candle_up_color", "#089981"))
        with c2:
            st.session_state["candle_dn_color"] = st.color_picker("แท่งลง (Bearish)", value=st.session_state.get("candle_dn_color", "#f23645"))

    with tab_ind:
        st.markdown("#### 📚 คลังอินดิเคเตอร์และการตั้งค่า (Indicators Library)")
        favs = st.session_state.get("favorite_indicators", ["EMA", "RSI", "MACD"])

        for group_name, indicators in INDICATOR_CATALOG.items():
            st.markdown(f"##### {group_name}")
            for code, meta in indicators.items():
                is_fav = code in favs
                star_icon = "⭐" if is_fav else "☆"
                active_key = f"ind_active_{code}"

                # แถวควบคุมหลัก: [ ⭐ ดาว ] | [ ชื่อตัวบ่งชี้ ] | [ สวิตช์ เปิด/ปิด ]
                c_star, c_title, c_tog = st.columns([0.6, 6.0, 1.4])
                with c_star:
                    if st.button(star_icon, key=f"star_btn_{code}", help="ปักหมุดไปที่ Top Bar"):
                        if is_fav:
                            favs.remove(code)
                        else:
                            favs.append(code)
                        st.session_state["favorite_indicators"] = favs
                        st.rerun()

                with c_title:
                    st.markdown(f"**{meta['name']}** (`{code}`)")

                with c_tog:
                    cur_active = st.session_state.get(active_key, False if code not in ["EMA", "RSI", "MACD"] else True)
                    new_active = st.toggle("แสดง", value=cur_active, key=f"tog_{code}", label_visibility="collapsed")
                    if new_active != cur_active:
                        st.session_state[active_key] = new_active
                        st.rerun()

                # บล็อกตั้งค่าละเอียด ⚙️ (เจาะลึก Inputs และ Style ตาม TradingView)
                with st.expander(f"⚙️ การตั้งค่า {code} (Inputs & Style)", expanded=False):
                    tab_inp, tab_sty = st.tabs(["📥 Inputs (การคำนวณ)", "🎨 Style (รูปแบบเส้น/สี)"])

                    # --- แท็บ Inputs ---
                    with tab_inp:
                        if code in ["EMA", "SMA"]:
                            c_t, c_l, c_s = st.columns(3)
                            with c_t:
                                st.session_state[f"{code}_type"] = st.selectbox("Type", ["EMA", "SMA", "WMA"], key=f"cfg_type_{code}")
                            with c_l:
                                st.session_state[f"{code}_len"] = st.number_input("Length", 1, 500, value=st.session_state.get(f"{code}_len", 20), key=f"cfg_len_{code}")
                            with c_s:
                                st.session_state[f"{code}_src"] = st.selectbox("Source", PRICE_SOURCES, key=f"cfg_src_{code}")

                        elif code == "RSI":
                            c_l, c_s, c_ob, c_os = st.columns(4)
                            with c_l:
                                st.session_state["rsi_len"] = st.number_input("Length", 1, 100, value=st.session_state.get("rsi_len", 14), key="cfg_rsi_len")
                            with c_s:
                                st.session_state["rsi_src"] = st.selectbox("Source", PRICE_SOURCES, key="cfg_rsi_src")
                            with c_ob:
                                st.session_state["rsi_ob"] = st.number_input("Overbought", 50, 95, value=st.session_state.get("rsi_ob", 70), key="cfg_rsi_ob")
                            with c_os:
                                st.session_state["rsi_os"] = st.number_input("Oversold", 5, 50, value=st.session_state.get("rsi_os", 30), key="cfg_rsi_os")

                        elif code == "MACD":
                            c_f, c_s, c_sig, c_src = st.columns(4)
                            with c_f:
                                st.session_state["macd_fast"] = st.number_input("Fast Length", 1, 100, value=st.session_state.get("macd_fast", 12), key="cfg_macd_f")
                            with c_s:
                                st.session_state["macd_slow"] = st.number_input("Slow Length", 1, 100, value=st.session_state.get("macd_slow", 26), key="cfg_macd_s")
                            with c_sig:
                                st.session_state["macd_sig"] = st.number_input("Signal Smoothing", 1, 50, value=st.session_state.get("macd_sig", 9), key="cfg_macd_sig")
                            with c_src:
                                st.session_state["macd_src"] = st.selectbox("Source", PRICE_SOURCES, key="cfg_macd_src")

                        elif code == "BB":
                            c_l, c_std, c_ma = st.columns(3)
                            with c_l:
                                st.session_state["bb_len"] = st.number_input("Length", 1, 100, value=st.session_state.get("bb_len", 20), key="cfg_bb_l")
                            with c_std:
                                st.session_state["bb_std"] = st.number_input("StdDev", 0.5, 5.0, value=st.session_state.get("bb_std", 2.0), step=0.1, key="cfg_bb_std")
                            with c_ma:
                                st.session_state["bb_matype"] = st.selectbox("Basis MA Type", ["SMA", "EMA"], key="cfg_bb_ma")

                        elif code == "ST":
                            c_l, c_fac = st.columns(2)
                            with c_l:
                                st.session_state["st_atr_len"] = st.number_input("ATR Length", 1, 100, value=st.session_state.get("st_atr_len", 10), key="cfg_st_len")
                            with c_fac:
                                st.session_state["st_factor"] = st.number_input("Factor (Multiplier)", 0.5, 10.0, value=st.session_state.get("st_factor", 3.0), step=0.5, key="cfg_st_fac")

                        elif code == "STOCH":
                            c_k, c_d, c_s, c_ob, c_os = st.columns(5)
                            with c_k:
                                st.session_state["stoch_k"] = st.number_input("%K", 1, 50, value=14, key="cfg_stoch_k")
                            with c_d:
                                st.session_state["stoch_d"] = st.number_input("%D", 1, 50, value=3, key="cfg_stoch_d")
                            with c_s:
                                st.session_state["stoch_smooth"] = st.number_input("Smooth", 1, 20, value=3, key="cfg_stoch_sm")
                            with c_ob:
                                st.session_state["stoch_ob"] = st.number_input("OB", 50, 95, value=80, key="cfg_stoch_ob")
                            with c_os:
                                st.session_state["stoch_os"] = st.number_input("OS", 5, 50, value=20, key="cfg_stoch_os")

                        elif code == "ATR":
                            c_l, c_sm = st.columns(2)
                            with c_l:
                                st.session_state["atr_len"] = st.number_input("Length", 1, 100, value=14, key="cfg_atr_len")
                            with c_sm:
                                st.session_state["atr_smooth"] = st.selectbox("Smoothing", ["RMA", "SMA", "EMA"], key="cfg_atr_sm")

                        elif code == "ADX":
                            c_di, c_adx, c_th = st.columns(3)
                            with c_di:
                                st.session_state["adx_di_len"] = st.number_input("DI Length", 1, 50, value=14, key="cfg_adx_di")
                            with c_adx:
                                st.session_state["adx_len"] = st.number_input("ADX Smoothing", 1, 50, value=14, key="cfg_adx_sm")
                            with c_th:
                                st.session_state["adx_th"] = st.number_input("Threshold", 10, 50, value=25, key="cfg_adx_th")

                        elif code == "ICHI":
                            c_conv, c_base, c_span, c_disp = st.columns(4)
                            with c_conv:
                                st.session_state["ichi_conv"] = st.number_input("Conversion (Tenkan)", 1, 50, value=9, key="cfg_ichi_c")
                            with c_base:
                                st.session_state["ichi_base"] = st.number_input("Base (Kijun)", 1, 100, value=26, key="cfg_ichi_b")
                            with c_span:
                                st.session_state["ichi_span_b"] = st.number_input("Span B", 1, 200, value=52, key="cfg_ichi_sb")
                            with c_disp:
                                st.session_state["ichi_disp"] = st.number_input("Displacement", 1, 50, value=26, key="cfg_ichi_d")

                        elif code == "VWAP":
                            c_s, c_a = st.columns(2)
                            with c_s:
                                st.session_state["vwap_src"] = st.selectbox("Source", PRICE_SOURCES, index=5, key="cfg_vwap_src") # HLC3
                            with c_a:
                                st.session_state["vwap_anchor"] = st.selectbox("Anchor Period", ["Session", "Week", "Month"], key="cfg_vwap_anc")

                        elif code == "VOL":
                            st.session_state["vol_ma_len"] = st.number_input("Volume MA Length", 1, 100, value=20, key="cfg_vol_ma")

                    # --- แท็บ Style ---
                    with tab_sty:
                        c_col, c_w, c_dash = st.columns(3)
                        with c_col:
                            st.session_state[f"{code}_color"] = st.color_picker("สีของเส้น", value=meta["style"].get("color", "#2962ff"), key=f"sty_col_{code}")
                        with c_w:
                            st.session_state[f"{code}_width"] = st.slider("ความหนา (px)", 1, 4, value=meta["style"].get("width", 2), key=f"sty_w_{code}")
                        with c_dash:
                            st.session_state[f"{code}_dash"] = st.selectbox("รูปแบบเส้น", ["Solid (ทึบ)", "Dashed (ประ)", "Dotted (จุด)"], key=f"sty_dash_{code}")

                st.markdown("<hr style='margin: 4px 0 10px 0; border: 0.5px solid #2a2e39;'>", unsafe_allow_html=True)

    with tab_ui:
        st.caption("ปรับแต่งแถบควบคุม Workspace")
        st.toggle("แสดงพาเนลขวา", value=True, key="show_right_panel")
def render_sidebar():
    """แสดงแถบเมนูควบคุมฝั่งซ้ายของหน้าจอ"""
    st.markdown('<div class="notranslate" translate="no">', unsafe_allow_html=True)

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
            st.button("ตลาด (ส้ม)", key="side_btn_market", use_container_width=True)
    with c_btn2:
            st.button("เครื่องมือ (เขียว)", key="side_btn_tools", use_container_width=True)

    st.caption("⚡ เมนูควบคุมหลัก")
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.button("🌿 ตลาดข่าว", key="side_btn_news", use_container_width=True)
    with c_m2:
        if st.button("⚙️ ตั้งค่ากราฟ", key="side_btn_settings", use_container_width=True):
            show_chart_settings_dialog()

    st.markdown('</div>', unsafe_allow_html=True)