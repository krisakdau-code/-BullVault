import streamlit as st

PRICE_SOURCES = ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"]

INDICATOR_CONFIGS = {
    # ── Trend (Overlay บนกราฟหลัก) ──────────────────────────
    "EMA": {
        "name": "Moving Average Ribbon (EMA)", "type": "trend", "default": True,
        "inputs": {"fast": 7, "slow": 13, "trend": 45, "source": "close"},
        "style": {
            "fast_color": "#2962ff", "fast_width": 2,
            "slow_color": "#ff6d00", "slow_width": 2,
            "trend_color": "#e040fb", "trend_width": 2
        }
    },
    "BB": {
        "name": "Bollinger Bands", "type": "trend", "default": False,
        "inputs": {"length": 20, "std_dev": 2.0, "source": "close"},
        "style": {
            "mid_color": "#ff9800", "mid_width": 2,
            "upper_color": "#2962ff", "upper_width": 1,
            "lower_color": "#2962ff", "lower_width": 1,
            "fill_color": "rgba(41, 98, 255, 0.1)"
        }
    },
    "ST": {
        "name": "Supertrend", "type": "trend", "default": False,
        "inputs": {"atr_period": 10, "factor": 3.0},
        "style": {
            "up_color": "#00e676", "up_width": 2,
            "down_color": "#ff5252", "down_width": 2
        }
    },
    "ICHI": {
        "name": "Ichimoku Cloud", "type": "trend", "default": False,
        "inputs": {"conversion": 9, "base": 26, "span_b": 52},
        "style": {
            "tenkan_color": "#00bcd4", "kijun_color": "#ff4081",
            "lead_a_color": "rgba(0, 230, 118, 0.2)", "lead_b_color": "rgba(255, 82, 82, 0.2)"
        }
    },
    "VWAP": {
        "name": "VWAP (Volume Weighted Average)", "type": "trend", "default": False,
        "inputs": {"source": "hlc3"},
        "style": {"color": "#ff9800", "width": 2}
    },
    # ── Momentum (Sub-pane ล่าง) ──────────────────────────
    "RSI": {
        "name": "Relative Strength Index (RSI)", "type": "momentum", "default": True,
        "inputs": {"length": 14, "source": "close", "ob": 70, "os": 30},
        "style": {
            "line_color": "#7e57c2", "line_width": 2,
            "ob_color": "#ef5350", "os_color": "#26a69a"
        }
    },
    "MACD": {
        "name": "MACD", "type": "momentum", "default": True,
        "inputs": {"fast": 12, "slow": 26, "signal": 9, "source": "close"},
        "style": {
            "macd_color": "#2962ff", "macd_width": 2,
            "sig_color": "#ff6d00", "sig_width": 2,
            "hist_up_color": "#26a69a", "hist_dn_color": "#ef5350"
        }
    },
    "STOCH": {
        "name": "Stochastic Oscillator", "type": "momentum", "default": False,
        "inputs": {"k_len": 14, "k_smooth": 1, "d_smooth": 3, "ob": 80, "os": 20},
        "style": {
            "k_color": "#2962ff", "k_width": 2,
            "d_color": "#ff6d00", "d_width": 2
        }
    },
    # ── Volatility & Volume ──────────────────────────────
    "ATR": {
        "name": "Average True Range (ATR)", "type": "volatility", "default": False,
        "inputs": {"length": 14},
        "style": {"color": "#ab47bc", "width": 2}
    },
    "ADX": {
        "name": "ADX / DMI", "type": "volatility", "default": False,
        "inputs": {"adx_len": 14, "threshold": 25},
        "style": {
            "adx_color": "#e040fb", "adx_width": 2,
            "pdi_color": "#00e676", "mdi_color": "#ff5252"
        }
    },
    "VOL": {
        "name": "Volume & Volume MA", "type": "volatility", "default": True,
        "inputs": {"ma_len": 20},
        "style": {
            "up_color": "#26a69a", "down_color": "#ef5350",
            "ma_color": "#ff9800", "ma_width": 2
        }
    }
}

INDICATOR_REGISTRY = INDICATOR_CONFIGS

def init_indicator_state():
    for code, cfg in INDICATOR_CONFIGS.items():
        if f"ind_active_{code}" not in st.session_state:
            st.session_state[f"ind_active_{code}"] = cfg["default"]
        for k, v in cfg["inputs"].items():
            if f"{code}_in_{k}" not in st.session_state:
                st.session_state[f"{code}_in_{k}"] = v
        for k, v in cfg["style"].items():
            if f"{code}_st_{k}" not in st.session_state:
                st.session_state[f"{code}_st_{k}"] = v

@st.dialog("📚 คลังอินดิเคเตอร์และการตั้งค่า (Indicators Library)", width="large")
def show_indicators_modal():
    init_indicator_state()
    categories = {
        "📈 Trend (บนกราฟราคา)": [k for k, v in INDICATOR_CONFIGS.items() if v["type"] == "trend"],
        "📊 Momentum (หน้าต่างแยก)": [k for k, v in INDICATOR_CONFIGS.items() if v["type"] == "momentum"],
        "🌊 Volatility & Volume (ความผันผวนและปริมาณ)": [k for k, v in INDICATOR_CONFIGS.items() if v["type"] == "volatility"]
    }

    for grp_title, codes in categories.items():
        st.markdown(f"##### {grp_title}")
        for code in codes:
            cfg = INDICATOR_CONFIGS[code]
            act_k = f"ind_active_{code}"
            
            c_star, c_title, c_sw = st.columns([0.08, 0.77, 0.15], vertical_alignment="center")
            with c_star:
                st.write("⭐" if st.session_state.get(act_k, False) else "☆")
            with c_title:
                st.markdown(f"**{cfg['name']}** &nbsp; `<small style='color:#787b86;'>{{{code}}}</small>`", unsafe_allow_html=True)
            with c_sw:
                new_act = st.toggle("", value=st.session_state.get(act_k, cfg["default"]), key=f"tgl_{code}", label_visibility="collapsed")
                if new_act != st.session_state.get(act_k):
                    st.session_state[act_k] = new_act
                    if code == "EMA": st.session_state["show_ema"] = new_act
                    elif code == "RSI": st.session_state["show_rsi_pane"] = new_act
                    elif code == "MACD": st.session_state["show_macd_pane"] = new_act
                    st.rerun()

            with st.expander(f"⚙️ ตั้งค่า {cfg['name']} (Inputs & Style)"):
                t_in, t_st = st.tabs(["📥 Inputs (การคำนวณ)", "🎨 Style (รูปแบบและสี)"])
                
                # ── แท็บ Inputs ──────────────────────────────────
                with t_in:
                    cols = st.columns(2)
                    for i, (k, default_val) in enumerate(cfg["inputs"].items()):
                        target_col = cols[i % 2]
                        inp_k = f"{code}_in_{k}"
                        with target_col:
                            if k == "source":
                                st.session_state[inp_k] = st.selectbox("Source", PRICE_SOURCES, index=PRICE_SOURCES.index(st.session_state.get(inp_k, default_val)), key=f"ui_{inp_k}")
                            elif isinstance(default_val, float):
                                st.session_state[inp_k] = st.number_input(k.replace('_', ' ').title(), value=float(st.session_state.get(inp_k, default_val)), step=0.1, key=f"ui_{inp_k}")
                            elif isinstance(default_val, int):
                                st.session_state[inp_k] = st.number_input(k.replace('_', ' ').title(), min_value=1, value=int(st.session_state.get(inp_k, default_val)), step=1, key=f"ui_{inp_k}")

                # ── แท็บ Style ──────────────────────────────────
                with t_st:
                    s_cols = st.columns(2)
                    idx = 0
                    for k, default_val in cfg["style"].items():
                        st_k = f"{code}_st_{k}"
                        if "color" in k:
                            with s_cols[idx % 2]:
                                cur_color = st.session_state.get(st_k, default_val)
                                base_color = cur_color if cur_color.startswith("#") else "#2962ff"
                                st.session_state[st_k] = st.color_picker(k.replace('_', ' ').title(), value=base_color, key=f"ui_{st_k}")
                            idx += 1
                        elif "width" in k:
                            with s_cols[idx % 2]:
                                st.session_state[st_k] = st.slider(f"ความหนา {k.replace('_width', '').title()}", 1, 4, value=int(st.session_state.get(st_k, default_val)), key=f"ui_{st_k}")
                            idx += 1

        st.markdown("<hr style='margin: 8px 0 16px 0; border: 0.5px solid #2a2e39;'>", unsafe_allow_html=True)