import streamlit as st
import re

PRICE_SOURCES = ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"]

INDICATOR_CONFIGS = {
    "EMA": {
        "name": "Moving Average Ribbon (EMA)", "type": "trend", "author": "drsweets", "default": True,
        "inputs": {"fast": 7, "slow": 13, "trend": 45, "source": "close"},
        "style": {"fast_color": "#2962ff", "fast_width": 2, "slow_color": "#ff6d00", "slow_width": 2, "trend_color": "#e040fb", "trend_width": 2}
    },
    "BB": {
        "name": "Bollinger Bands", "type": "trend", "author": "John Bollinger", "default": False,
        "inputs": {"length": 20, "std_dev": 2.0, "source": "close"},
        "style": {"mid_color": "#ff9800", "mid_width": 2, "upper_color": "#2962ff", "upper_width": 1, "lower_color": "#2962ff", "lower_width": 1, "fill_color": "rgba(41, 98, 255, 0.1)"}
    },
    "ST": {
        "name": "Supertrend", "type": "trend", "author": "KivancOzbilgic", "default": False,
        "inputs": {"atr_period": 10, "factor": 3.0},
        "style": {"up_color": "#00e676", "up_width": 2, "down_color": "#ff5252", "down_width": 2}
    },
    "ICHI": {
        "name": "Ichimoku Cloud", "type": "trend", "author": "Goichi Hosoda", "default": False,
        "inputs": {"conversion": 9, "base": 26, "span_b": 52},
        "style": {"tenkan_color": "#00bcd4", "kijun_color": "#ff4081", "lead_a_color": "#00e676", "lead_b_color": "#ff5252"}
    },
    "VWAP": {
        "name": "VWAP (Volume Weighted Average)", "type": "trend", "author": "Institutional Flow", "default": False,
        "inputs": {"source": "hlc3"},
        "style": {"color": "#ff9800", "width": 2}
    },
    "RSI": {
        "name": "Relative Strength Index (RSI)", "type": "momentum", "author": "J. Welles Wilder", "default": True,
        "inputs": {"length": 14, "source": "close", "ob": 70, "os": 30},
        "style": {"line_color": "#7e57c2", "line_width": 2, "ob_color": "#ef5350", "os_color": "#26a69a"}
    },
    "MACD": {
        "name": "MACD", "type": "momentum", "author": "Gerald Appel", "default": True,
        "inputs": {"fast": 12, "slow": 26, "signal": 9, "source": "close"},
        "style": {"macd_color": "#2962ff", "macd_width": 2, "sig_color": "#ff6d00", "sig_width": 2, "hist_up_color": "#26a69a", "hist_dn_color": "#ef5350"}
    },
    "STOCH": {
        "name": "Stochastic Oscillator", "type": "momentum", "author": "George Lane", "default": False,
        "inputs": {"k_len": 14, "k_smooth": 1, "d_smooth": 3, "ob": 80, "os": 20},
        "style": {"k_color": "#2962ff", "k_width": 2, "d_color": "#ff6d00", "d_width": 2}
    },
    "ATR": {
        "name": "Average True Range (ATR)", "type": "volatility", "author": "J. Welles Wilder", "default": False,
        "inputs": {"length": 14},
        "style": {"color": "#ab47bc", "width": 2}
    },
    "ADX": {
        "name": "ADX / DMI", "type": "volatility", "author": "J. Welles Wilder", "default": False,
        "inputs": {"adx_len": 14, "threshold": 25},
        "style": {"adx_color": "#e040fb", "adx_width": 2, "pdi_color": "#00e676", "mdi_color": "#ff5252"}
    },
    "VOL": {
        "name": "Volume & Volume MA", "type": "volatility", "author": "Trading System", "default": True,
        "inputs": {"ma_len": 20},
        "style": {"up_color": "#26a69a", "down_color": "#ef5350", "ma_color": "#ff9800", "ma_width": 2}
    }
}

INDICATOR_REGISTRY = INDICATOR_CONFIGS

def init_indicator_state():
    for code, cfg in INDICATOR_CONFIGS.items():
        if f"ind_active_{code}" not in st.session_state:
            st.session_state[f"ind_active_{code}"] = cfg["default"]
        if f"ind_fav_{code}" not in st.session_state:
            st.session_state[f"ind_fav_{code}"] = (code in ["EMA", "RSI", "MACD"])
        for k, v in cfg["inputs"].items():
            if f"{code}_in_{k}" not in st.session_state:
                st.session_state[f"{code}_in_{k}"] = v
        for k, v in cfg["style"].items():
            if f"{code}_st_{k}" not in st.session_state:
                st.session_state[f"{code}_st_{k}"] = v

    if "my_scripts" not in st.session_state:
        st.session_state["my_scripts"] = {
            "Takaya kating (Diamond Armor V11.3)": {
                "author": "Takayakating9...",
                "code": '''// @version=5
indicator("Diamond Armor V11.3 - Infinite RSI + Explosion", overlay=true, max_labels_count=500)
f_len = input.int(7, "Fast EMA (น้ำเงิน)", group="Strategy Settings")
s_len = input.int(13, "Slow EMA (แดง)", group="Strategy Settings")
t_len = input.int(45, "Trend Filter (ขาว)", group="Strategy Settings")
ema_f = ta.ema(close, f_len)
ema_s = ta.ema(close, s_len)
ema_t = ta.ema(close, t_len)
plot(ema_f, color=color.blue, title="Fast EMA")
plot(ema_s, color=color.red, title="Slow EMA")
plot(ema_t, color=color.white, title="Trend EMA")
''',
                "active": True,
                "fav": True
            },
            "16/4/69 (Smart Money Strategy)": {
                "author": "Takayakating9...",
                "code": '''// @version=5
strategy("16/4/69 Smart Money Strategy", overlay=true)
f_len = input.int(9, "Fast EMA")
s_len = input.int(21, "Slow EMA")
buy_signal = ta.crossover(ta.ema(close, f_len), ta.ema(close, s_len))
plotshape(buy_signal, title="BUY", style=shape.labelup, location=location.belowbar, color=color.green, text="BUY")
''',
                "active": False,
                "fav": False
            }
        }

    if "current_editor_script_name" not in st.session_state:
        st.session_state["current_editor_script_name"] = "Takaya kating (Diamond Armor V11.3)"
    if "sidebar_active_nav" not in st.session_state:
        st.session_state["sidebar_active_nav"] = "👤 สคริปต์ของฉัน (เครื่องมือที่ฉันออกแบบ)"

def apply_pine_script_to_chart(script_title, script_code, is_active):
    st.session_state["custom_pine_active"] = is_active
    st.session_state["custom_pine_title"] = script_title
    st.session_state["custom_pine_code"] = script_code

    if is_active:
        f_val, s_val, t_val = 7, 13, 45
        m_f = re.search(r'f_len\s*=\s*input(?:\.int)?\s*\(\s*(\d+)', script_code)
        m_s = re.search(r's_len\s*=\s*input(?:\.int)?\s*\(\s*(\d+)', script_code)
        m_t = re.search(r't_len\s*=\s*input(?:\.int)?\s*\(\s*(\d+)', script_code)
        if m_f: f_val = int(m_f.group(1))
        if m_s: s_val = int(m_s.group(1))
        if m_t: t_val = int(m_t.group(1))

        st.session_state["show_ema"] = True
        st.session_state["ind_active_EMA"] = True
        st.session_state["EMA_in_fast"] = f_val
        st.session_state["EMA_in_slow"] = s_val
        st.session_state["EMA_in_trend"] = t_val
        st.session_state["EMA_st_fast_color"] = "#2962ff"
        st.session_state["EMA_st_slow_color"] = "#ff1744"
        st.session_state["EMA_st_trend_color"] = "#ffffff"
    else:
        st.session_state["custom_pine_active"] = False

@st.dialog("อินดิเคเตอร์ ตัวชี้วัด และกลยุทธ์ (Indicators Library & Pine Script)", width="large")
def show_indicators_modal():
    init_indicator_state()

    st.markdown("""
        <style>
        .stTextArea textarea {
            border: 1.5px solid #ff9800 !important;
            box-shadow: 0 0 12px rgba(255, 152, 0, 0.45) !important;
            background-color: #0d1117 !important;
            color: #f8fafc !important;
            font-family: monospace !important;
            font-size: 13.5px !important;
            border-radius: 8px !important;
        }
        .stTextArea textarea:focus {
            border: 2px solid #ffb74d !important;
            box-shadow: 0 0 18px rgba(255, 152, 0, 0.75) !important;
        }
        .tv-nav-header {
            font-size: 11.5px;
            font-weight: 700;
            color: #787b86;
            margin: 10px 0 4px 4px;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

    search_kw = st.text_input(
        "ค้นหา:", 
        placeholder="🔍 ค้นหา (พิมพ์ชื่อตัวชี้วัดหรือกลยุทธ์...)", 
        key="tv_search_input", 
        label_visibility="collapsed"
    ).strip().lower()

    col_nav, col_content = st.columns([0.30, 0.70], gap="medium")

    # ── เมนูนำทางฝั่งซ้าย (คลิกแล้วไม่สั่ง rerun ทั้งหน้า จึงไม่เด้งปิด) ──
    with col_nav:
        st.markdown("<div class='tv-nav-header'>ส่วนตัว</div>", unsafe_allow_html=True)
        nav_items_personal = [
            ("⭐ รายการโปรด", "⭐ รายการโปรด"),
            ("👤 สคริปต์ของฉัน", "👤 สคริปต์ของฉัน (เครื่องมือที่ฉันออกแบบ)")
        ]
        for label, val in nav_items_personal:
            is_active = (st.session_state["sidebar_active_nav"] == val)
            if st.button(label, key=f"nav_p_{val}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state["sidebar_active_nav"] = val

        st.markdown("<div class='tv-nav-header'>ที่มีอยู่แล้ว</div>", unsafe_allow_html=True)
        is_active_tech = (st.session_state["sidebar_active_nav"] == "📈 ทางเทคนิค")
        if st.button("📈 ทางเทคนิค", key="nav_tech", use_container_width=True, type="primary" if is_active_tech else "secondary"):
            st.session_state["sidebar_active_nav"] = "📈 ทางเทคนิค"

        st.markdown("<div class='tv-nav-header'>เครื่องมือพัฒนา</div>", unsafe_allow_html=True)
        is_active_pine = (st.session_state["sidebar_active_nav"] == "⚡ ตัวแก้ไข Pine Script (Pine Editor)")
        if st.button("⚡ ตัวแก้ไข Pine Script", key="nav_pine", use_container_width=True, type="primary" if is_active_pine else "secondary"):
            st.session_state["sidebar_active_nav"] = "⚡ ตัวแก้ไข Pine Script (Pine Editor)"

    # ── พื้นที่แสดงผลฝั่งขวา ──
    with col_content:
        if st.session_state["sidebar_active_nav"] == "⚡ ตัวแก้ไข Pine Script (Pine Editor)":
            st.markdown("<div style='font-size: 15px; font-weight: bold; color: #ff9800; margin-bottom: 8px;'>⚡ ตัวแก้ไข Pine Script (Pine Editor) — เครื่องมือออกแบบกลยุทธ์</div>", unsafe_allow_html=True)
            
            db = st.session_state["my_scripts"]
            script_list = list(db.keys()) + ["+ สร้างสคริปต์ใหม่"]

            ed_c1, ed_c2 = st.columns([0.65, 0.35])
            with ed_c1:
                cur_sel = st.selectbox("เลือกสคริปต์:", options=script_list, index=script_list.index(st.session_state["current_editor_script_name"]) if st.session_state["current_editor_script_name"] in script_list else 0, key="editor_select_box")
                if cur_sel == "+ สร้างสคริปต์ใหม่":
                    active_title = "กลยุทธ์ใหม่ของฉัน"
                    active_code = '''//@version=5\nstrategy("New Strategy", overlay=true)\n'''
                else:
                    active_title = cur_sel
                    active_code = db[cur_sel]["code"]
                st.session_state["current_editor_script_name"] = cur_sel

            with ed_c2:
                script_title_input = st.text_input("ชื่อสคริปต์:", value=active_title, key="editor_title_input")

            pine_code_input = st.text_area("Pine Editor Code:", value=active_code, height=270, key="editor_code_textarea")

            btn_col1, btn_col2, btn_col3 = st.columns([0.45, 0.25, 0.30])
            with btn_col1:
                if st.button("💾 บันทึกสคริปต์ลงคลัง", use_container_width=True, type="primary"):
                    if script_title_input and script_title_input != "+ สร้างสคริปต์ใหม่":
                        is_active_prev = db.get(script_title_input, {}).get("active", True)
                        is_fav_prev = db.get(script_title_input, {}).get("fav", False)
                        db[script_title_input] = {
                            "author": "Takayakating9...",
                            "code": pine_code_input,
                            "active": is_active_prev,
                            "fav": is_fav_prev
                        }
                        if is_active_prev:
                            apply_pine_script_to_chart(script_title_input, pine_code_input, True)
                            
                        st.session_state["current_editor_script_name"] = script_title_input
                        st.session_state["sidebar_active_nav"] = "👤 สคริปต์ของฉัน (เครื่องมือที่ฉันออกแบบ)"
                        st.success(f"บันทึก '{script_title_input}' สำเร็จ!")

            with btn_col2:
                if cur_sel in db:
                    cur_act = db[cur_sel].get("active", False)
                    tgl_act = st.toggle("ติกลงกราฟ", value=cur_act, key=f"tgl_ed_{cur_sel}")
                    if tgl_act != cur_act:
                        db[cur_sel]["active"] = tgl_act
                        apply_pine_script_to_chart(cur_sel, db[cur_sel]["code"], tgl_act)

            with btn_col3:
                if st.button("🔍 ตรวจสอบโค้ด", use_container_width=True, type="secondary"):
                    if "//@version=5" in pine_code_input or "strategy" in pine_code_input or "indicator" in pine_code_input:
                        st.info("✅ ไวยากรณ์ถูกต้อง: พร้อมทำงานบนกราฟ")
                    else:
                        st.error("❌ จำเป็นต้องมี //@version=5 หรือ indicator/strategy")

        else:
            h_star, h_name, h_author, h_toggle = st.columns([0.08, 0.48, 0.28, 0.16])
            with h_name: st.markdown("<b style='color:#787b86; font-size:12px;'>ชื่อ</b>", unsafe_allow_html=True)
            with h_author: st.markdown("<b style='color:#787b86; font-size:12px;'>ผู้เขียน</b>", unsafe_allow_html=True)
            with h_toggle: st.markdown("<b style='color:#787b86; font-size:12px;'>เปิดใช้</b>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0 10px 0; border:0.5px solid #21262d;'>", unsafe_allow_html=True)

            current_nav = st.session_state["sidebar_active_nav"]

            if current_nav == "👤 สคริปต์ของฉัน (เครื่องมือที่ฉันออกแบบ)" or (search_kw and any(search_kw in k.lower() for k in st.session_state["my_scripts"])):
                db = st.session_state["my_scripts"]
                for s_name, s_data in list(db.items()):
                    if search_kw and (search_kw not in s_name.lower()):
                        continue
                    
                    row_star, row_title, row_author, row_sw = st.columns([0.08, 0.48, 0.28, 0.16], vertical_alignment="center")
                    with row_star:
                        is_fav = s_data.get("fav", False)
                        if st.button("⭐" if is_fav else "☆", key=f"fav_btn_script_{s_name}", help="ติดดาวรายการโปรด"):
                            s_data["fav"] = not is_fav
                    with row_title:
                        st.markdown(f"<span style='color:#f8fafc; font-size:13.5px; font-weight:500;'>{s_name}</span>", unsafe_allow_html=True)
                    with row_author:
                        st.markdown(f"<span style='color:#38bdf8; font-size:12px;'>{s_data.get('author', 'ฉันเอง')}</span>", unsafe_allow_html=True)
                    with row_sw:
                        is_act = s_data.get("active", False)
                        tgl_val = st.toggle("", value=is_act, key=f"tgl_myscript_{s_name}", label_visibility="collapsed")
                        if tgl_val != is_act:
                            s_data["active"] = tgl_val
                            apply_pine_script_to_chart(s_name, s_data["code"], tgl_val)

                    with st.expander(f"📝 ดูและแก้ไขสคริปต์ {s_name}"):
                        st.code(s_data["code"], language="pine")
                        if st.button(f"✏️ เปิดในตัวแก้ไข Pine Editor", key=f"load_ed_{s_name}", use_container_width=True):
                            st.session_state["current_editor_script_name"] = s_name
                            st.session_state["sidebar_active_nav"] = "⚡ ตัวแก้ไข Pine Script (Pine Editor)"

            if current_nav in ["⭐ รายการโปรด", "📈 ทางเทคนิค"] or search_kw:
                if current_nav == "⭐ รายการโปรด":
                    db = st.session_state["my_scripts"]
                    for s_name, s_data in db.items():
                        if s_data.get("fav", False):
                            if search_kw and (search_kw not in s_name.lower()):
                                continue
                            row_star, row_title, row_author, row_sw = st.columns([0.08, 0.48, 0.28, 0.16], vertical_alignment="center")
                            with row_star:
                                if st.button("⭐", key=f"fav_star_my_{s_name}"):
                                    s_data["fav"] = False
                            with row_title:
                                st.markdown(f"<span style='color:#f8fafc; font-size:13.5px;'>{s_name}</span>", unsafe_allow_html=True)
                            with row_author:
                                st.markdown(f"<span style='color:#38bdf8; font-size:12px;'>{s_data.get('author', 'Takayakating9...')}</span>", unsafe_allow_html=True)
                            with row_sw:
                                is_act = s_data.get("active", False)
                                tgl_val = st.toggle("", value=is_act, key=f"tgl_fav_my_{s_name}", label_visibility="collapsed")
                                if tgl_val != is_act:
                                    s_data["active"] = tgl_val
                                    apply_pine_script_to_chart(s_name, s_data["code"], tgl_val)

                for code, cfg in INDICATOR_CONFIGS.items():
                    act_k = f"ind_active_{code}"
                    fav_k = f"ind_fav_{code}"
                    
                    is_fav = st.session_state.get(fav_k, False)
                    if current_nav == "⭐ รายการโปรด" and not is_fav:
                        continue
                    if search_kw and (search_kw not in cfg["name"].lower() and search_kw not in code.lower()):
                        continue

                    row_star, row_title, row_author, row_sw = st.columns([0.08, 0.48, 0.28, 0.16], vertical_alignment="center")
                    with row_star:
                        star_icon = "⭐" if is_fav else "☆"
                        if st.button(star_icon, key=f"star_btn_{code}", help="ติดดาวรายการโปรด"):
                            st.session_state[fav_k] = not is_fav
                    with row_title:
                        st.markdown(f"<span style='color:#f8fafc; font-size:13.5px;'>{cfg['name']}</span>", unsafe_allow_html=True)
                    with row_author:
                        st.markdown(f"<span style='color:#787b86; font-size:12px;'>{cfg.get('author', 'Trading System')}</span>", unsafe_allow_html=True)
                    with row_sw:
                        cur_state = st.session_state.get(act_k, cfg["default"])
                        new_act = st.toggle("", value=cur_state, key=f"tgl_std_{code}", label_visibility="collapsed")
                        if new_act != cur_state:
                            st.session_state[act_k] = new_act
                            if code == "EMA": st.session_state["show_ema"] = new_act
                            elif code == "RSI": st.session_state["show_rsi_pane"] = new_act
                            elif code == "MACD": st.session_state["show_macd_pane"] = new_act

                    with st.expander(f"⚙️ ตั้งค่า {cfg['name']} (Inputs & Style)"):
                        t_in, t_st = st.tabs(["📥 Inputs (การคำนวณ)", "🎨 Style (รูปแบบและสี)"])
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

def show_indicators_library_modal():
    show_indicators_modal()