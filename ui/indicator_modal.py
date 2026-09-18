import streamlit as st

PRICE_SOURCES = ["Close", "Open", "High", "Low", "HL2", "HLC3", "OHLC4"]

# โครงสร้างรายการอินดิเคเตอร์ทั้ง 11 ตัว แบ่งตาม 3 หมวดหมู่หลัก
INDICATOR_GROUPS = {
    "Trend (บนกราฟราคา)": [
        {
            "code": "EMA",
            "name": "Moving Average (EMA/SMA/WMA)",
            "type_opt": ["EMA", "SMA", "WMA"],
            "default_active": True,
            "inputs": {"type": "EMA", "length": 20, "source": "Close"},
            "style": {"color": "#2962ff", "width": 2}
        },
        {
            "code": "BB",
            "name": "Bollinger Bands",
            "type_opt": ["SMA", "EMA"],
            "default_active": False,
            "inputs": {"length": 20, "std_dev": 2.0, "source": "Close"},
            "style": {"color": "#2962ff", "fill_color": "rgba(41, 98, 255, 0.1)", "width": 1}
        },
        {
            "code": "ST",
            "name": "Supertrend",
            "type_opt": None,
            "default_active": False,
            "inputs": {"atr_len": 10, "factor": 3.0},
            "style": {"up_color": "#00e676", "down_color": "#ff5252", "width": 2}
        },
        {
            "code": "ICHI",
            "name": "Ichimoku Cloud",
            "type_opt": None,
            "default_active": False,
            "inputs": {"conversion": 9, "base": 26, "span_b": 52, "displacement": 26},
            "style": {"lead_a_color": "#00e676", "lead_b_color": "#ff5252"}
        },
        {
            "code": "VWAP",
            "name": "VWAP",
            "type_opt": None,
            "default_active": False,
            "inputs": {"anchor": "Session", "source": "HLC3"},
            "style": {"color": "#ff9800", "width": 2}
        }
    ],
    "Momentum (หน้าต่างแยก)": [
        {
            "code": "RSI",
            "name": "Relative Strength Index (RSI)",
            "type_opt": None,
            "default_active": True,
            "inputs": {"length": 14, "source": "Close", "ob": 70, "os": 30},
            "style": {"color": "#7e57c2", "width": 2}
        },
        {
            "code": "MACD",
            "name": "MACD",
            "type_opt": None,
            "default_active": True,
            "inputs": {"fast": 12, "slow": 26, "signal": 9, "source": "Close"},
            "style": {"macd_color": "#2962ff", "sig_color": "#ff6d00", "hist_up": "#26a69a", "hist_dn": "#ef5350"}
        },
        {
            "code": "STOCH",
            "name": "Stochastic Oscillator",
            "type_opt": None,
            "default_active": False,
            "inputs": {"k_len": 14, "k_smooth": 1, "d_smooth": 3, "ob": 80, "os": 20},
            "style": {"k_color": "#2962ff", "d_color": "#ff6d00"}
        }
    ],
    "Volatility & Volume (ความผันผวนและปริมาณ)": [
        {
            "code": "ATR",
            "name": "Average True Range (ATR)",
            "type_opt": ["RMA", "SMA", "EMA", "WMA"],
            "default_active": False,
            "inputs": {"length": 14, "smoothing": "RMA"},
            "style": {"color": "#ab47bc", "width": 2}
        },
        {
            "code": "ADX",
            "name": "ADX / DMI",
            "type_opt": None,
            "default_active": False,
            "inputs": {"adx_len": 14, "di_len": 14, "threshold": 25},
            "style": {"adx_color": "#ff5252", "plus_di": "#00e676", "minus_di": "#ff5252"}
        },
        {
            "code": "VOL",
            "name": "Volume & Volume MA",
            "type_opt": None,
            "default_active": False,
            "inputs": {"ma_len": 20},
            "style": {"ma_color": "#2962ff", "up_vol": "#26a69a", "dn_vol": "#ef5350"}
        }
    ]
}


@st.dialog("📚 คลังอินดิเคเตอร์และการตั้งค่า (Indicators Library)", width="large")
def show_indicators_dialog():
    """หน้าต่างโมดอลสำหรับเปิด-ปิด และปรับแต่ง Inputs/Style ของ 11 อินดิเคเตอร์"""
    for grp_title, ind_list in INDICATOR_GROUPS.items():
        st.markdown(f"##### {grp_title}")

        for ind in ind_list:
            code = ind["code"]
            name = ind["name"]
            active_key = f"ind_active_{code}"

            if active_key not in st.session_state:
                st.session_state[active_key] = ind["default_active"]

            c_star, c_title, c_sw = st.columns([0.08, 0.77, 0.15], vertical_alignment="center")

            with c_star:
                st.write("⭐" if st.session_state[active_key] else "☆")

            with c_title:
                st.markdown(f"**{name}** &nbsp; `<small style='color:#787b86;'>{{{code}}}</small>`", unsafe_allow_html=True)

            with c_sw:
                new_val = st.toggle("", value=st.session_state[active_key], key=f"tgl_{code}", label_visibility="collapsed")
                if new_val != st.session_state[active_key]:
                    st.session_state[active_key] = new_val
                    if code == "EMA": st.session_state["show_ema"] = new_val
                    elif code == "RSI": st.session_state["show_rsi_pane"] = new_val
                    elif code == "MACD": st.session_state["show_macd_pane"] = new_val
                    st.rerun()

            with st.expander(f"⚙️ การตั้งค่า {code} (Inputs & Style)"):
                tab_in, tab_st = st.tabs(["📥 Inputs (การคำนวณ)", "🎨 Style (รูปแบบเส้น/สี)"])

                with tab_in:
                    c_in1, c_in2 = st.columns(2)
                    with c_in1:
                        if "length" in ind["inputs"]:
                            st.session_state[f"{code}_len"] = st.number_input("Length", 1, 500, value=st.session_state.get(f"{code}_len", ind["inputs"]["length"]), key=f"inp_{code}_len")
                        elif "atr_len" in ind["inputs"]:
                            st.session_state[f"{code}_atr_len"] = st.number_input("ATR Length", 1, 100, value=st.session_state.get(f"{code}_atr_len", ind["inputs"]["atr_len"]), key=f"inp_{code}_atr")
                    with c_in2:
                        if "source" in ind["inputs"]:
                            st.session_state[f"{code}_src"] = st.selectbox("Source", PRICE_SOURCES, key=f"inp_{code}_src")
                        elif "factor" in ind["inputs"]:
                            st.session_state[f"{code}_factor"] = st.number_input("Factor", 0.5, 10.0, value=st.session_state.get(f"{code}_factor", ind["inputs"]["factor"]), step=0.1, key=f"inp_{code}_fact")

                with tab_st:
                    c_st1, c_st2 = st.columns(2)
                    with c_st1:
                        st.session_state[f"{code}_color"] = st.color_picker("สีหลัก", value=st.session_state.get(f"{code}_color", ind["style"].get("color", "#2962ff")), key=f"clr_{code}")
                    with c_st2:
                        st.session_state[f"{code}_width"] = st.slider("ความหนาเส้น (px)", 1, 4, value=st.session_state.get(f"{code}_width", ind["style"].get("width", 2)), key=f"wd_{code}")

        st.markdown("<hr style='margin: 8px 0 16px 0; border: 0.5px solid #2a2e39;'>", unsafe_allow_html=True)