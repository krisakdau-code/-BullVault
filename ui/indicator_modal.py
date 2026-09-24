import streamlit as st
import re

try:
    from streamlit_monaco import st_monaco
    HAS_MONACO = True
except ImportError:
    HAS_MONACO = False

PRICE_SOURCES = ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"]

INDICATOR_CONFIGS = {
    "DIAMOND": {
        "name": "Diamond Armor V11.3 (Infinite RSI + Explosion)", "type": "strategy", "author": "Takayakating9...", "default": False,
        "inputs": {"fast": 7, "slow": 13, "trend": 45, "min_tp_pct": 3.0, "warn_pct": 3.0, "danger_pct": 7.0},
        "style": {
            "show_fast": True, "fast_color": "#2962ff", "fast_width": 2,
            "show_slow": True, "slow_color": "#ff5252", "slow_width": 2,
            "show_trend": True, "trend_color": "#ffffff", "trend_width": 1,
            "show_rsi_overlay": False, "rsi_overlay_color": "#FFD700", "rsi_overlay_width": 1,
            "show_star": True, "show_labels": True, "show_dots": True, "show_hud": True
        }
    },
    "EMA": {
        "name": "Moving Average Ribbon (EMA)", "type": "trend", "author": "drsweets", "default": True,
        "inputs": {"fast": 7, "slow": 13, "trend": 45, "source": "close"},
        "style": {
            "show_fast": True, "fast_color": "#2962ff", "fast_width": 2,
            "show_slow": True, "slow_color": "#ff6d00", "slow_width": 2,
            "show_trend": True, "trend_color": "#e040fb", "trend_width": 2
        }
    },
    "BB": {
        "name": "Bollinger Bands", "type": "trend", "author": "John Bollinger", "default": False,
        "inputs": {"length": 20, "std_dev": 2.0, "source": "close"},
        "style": {
            "show_mid": True, "mid_color": "#ff9800", "mid_width": 2,
            "show_upper": True, "upper_color": "#2962ff", "upper_width": 1,
            "show_lower": True, "lower_color": "#2962ff", "lower_width": 1
        }
    },
    "ST": {
        "name": "Supertrend", "type": "trend", "author": "KivancOzbilgic", "default": False,
        "inputs": {"atr_period": 10, "factor": 3.0},
        "style": {
            "show_up": True, "up_color": "#00e676", "up_width": 2,
            "show_down": True, "down_color": "#ff5252", "down_width": 2
        }
    },
    "ICHI": {
        "name": "Ichimoku Cloud", "type": "trend", "author": "Goichi Hosoda", "default": False,
        "inputs": {"conversion": 9, "base": 26, "span_b": 52},
        "style": {
            "show_tenkan": True, "tenkan_color": "#00bcd4", "tenkan_width": 1,
            "show_kijun": True, "kijun_color": "#ff4081", "kijun_width": 1,
            "show_span_a": True, "lead_a_color": "#00e676", "span_a_width": 1,
            "show_span_b": True, "lead_b_color": "#ff5252", "span_b_width": 1
        }
    },
    "VWAP": {
        "name": "VWAP (Volume Weighted Average)", "type": "trend", "author": "Institutional Flow", "default": False,
        "inputs": {"source": "hlc3"},
        "style": {"show_vwap": True, "color": "#ff9800", "width": 2}
    },
    "RSI": {
        "name": "Relative Strength Index (RSI)", "type": "momentum", "author": "J. Welles Wilder", "default": True,
        "inputs": {"length": 14, "source": "close", "ob": 70, "os": 30},
        "style": {
            "show_line": True, "line_color": "#7e57c2", "line_width": 2,
            "show_ma": True, "ma_color": "#ffeb3b",
            "show_bands": True, "ob_color": "#ef5350", "os_color": "#26a69a"
        }
    },
    "MACD": {
        "name": "MACD", "type": "momentum", "author": "Gerald Appel", "default": True,
        "inputs": {"fast": 12, "slow": 26, "signal": 9, "source": "close"},
        "style": {
            "show_macd": True, "macd_color": "#2962ff", "macd_width": 2,
            "show_sig": True, "sig_color": "#ff6d00", "sig_width": 2,
            "show_hist": True, "show_zero": True
        }
    },
    "STOCH": {
        "name": "Stochastic Oscillator", "type": "momentum", "author": "George Lane", "default": False,
        "inputs": {"k_len": 14, "k_smooth": 1, "d_smooth": 3, "ob": 80, "os": 20},
        "style": {
            "show_k": True, "k_color": "#2962ff", "k_width": 2,
            "show_d": True, "d_color": "#ff6d00", "d_width": 2,
            "show_bands": True
        }
    },
    "ATR": {
        "name": "Average True Range (ATR)", "type": "volatility", "author": "J. Welles Wilder", "default": False,
        "inputs": {"length": 14},
        "style": {"show_line": True, "color": "#ab47bc", "width": 2}
    },
    "ADX": {
        "name": "ADX / DMI", "type": "volatility", "author": "J. Welles Wilder", "default": False,
        "inputs": {"adx_len": 14, "threshold": 25},
        "style": {
            "show_adx": True, "adx_color": "#e040fb", "adx_width": 2,
            "show_pdi": True, "pdi_color": "#00e676", "pdi_width": 1,
            "show_mdi": True, "mdi_color": "#ff5252", "mdi_width": 1,
            "show_threshold": True
        }
    },
    "VOL": {
        "name": "Volume & Volume MA", "type": "volatility", "author": "Trading System", "default": True,
        "inputs": {"ma_len": 20},
        "style": {
            "show_bars": True, "up_color": "#26a69a", "down_color": "#ef5350",
            "show_ma": True, "ma_color": "#ff9800", "ma_width": 2
        }
    }
}

# เชื่อมโยงตัวแปรสำหรับ app.py
INDICATOR_REGISTRY = INDICATOR_CONFIGS

STYLE_LABELS = {
    "show_fast": "เปิดเส้น Fast EMA", "show_slow": "เปิดเส้น Slow EMA", "show_trend": "เปิดเส้น Trend EMA",
    "show_rsi_overlay": "เปิดเส้น RSI Overlay (เหลือง)", "show_star": "เปิดดวงดาว (⭐)",
    "show_labels": "เปิดป้ายสัญญาณ BUY / TP / SELL", "show_dots": "เปิดจุดเตือนภัย Warning Dots",
    "show_hud": "เปิดตารางสถิติ HUD Dashboard", "show_upper": "เปิดเส้นกรอบบน (Upper)",
    "show_mid": "เปิดเส้นกึ่งกลาง (Basis)", "show_lower": "เปิดเส้นกรอบล่าง (Lower)",
    "show_up": "เปิดเส้น Uptrend (เขียว)", "show_down": "เปิดเส้น Downtrend (แดง)",
    "show_tenkan": "เปิดเส้น Tenkan-sen", "show_kijun": "เปิดเส้น Kijun-sen",
    "show_span_a": "เปิดเส้น Senkou Span A", "show_span_b": "เปิดเส้น Senkou Span B",
    "show_vwap": "เปิดเส้น VWAP", "show_line": "เปิดเส้นตัวชี้วัดหลัก",
    "show_ma": "เปิดเส้นค่าเฉลี่ย MA", "show_bands": "เปิดเส้นระดับ OB / OS",
    "show_macd": "เปิดเส้น MACD Line", "show_sig": "เปิดเส้น Signal Line",
    "show_hist": "เปิดแท่ง Histogram", "show_zero": "เปิดเส้นระดับ 0",
    "show_k": "เปิดเส้น Stochastic %K", "show_d": "เปิดเส้น Stochastic %D",
    "show_adx": "เปิดเส้นหลัก ADX", "show_pdi": "เปิดเส้นแรงซื้อ +DI",
    "show_mdi": "เปิดเส้นแรงขาย -DI", "show_threshold": "เปิดเส้นระดับ Threshold",
    "show_bars": "เปิดแท่ง Volume ซื้อขาย",
    "fast_color": "สี Fast EMA", "slow_color": "สี Slow EMA", "trend_color": "สี Trend Filter",
    "rsi_overlay_color": "สี RSI Overlay", "mid_color": "สีเส้นกลาง", "upper_color": "สีเส้นบน",
    "lower_color": "สีเส้นล่าง", "up_color": "สีเทรนด์ขาขึ้น", "down_color": "สีเทรนด์ขาลง",
    "tenkan_color": "สี Tenkan", "kijun_color": "สี Kijun", "lead_a_color": "สี Span A",
    "lead_b_color": "สี Span B", "color": "สีเส้นหลัก", "line_color": "สีเส้นหลัก",
    "ma_color": "สีเส้นค่าเฉลี่ย MA", "ob_color": "สี Overbought", "os_color": "สี Oversold",
    "macd_color": "สีเส้น MACD", "sig_color": "สีเส้น Signal", "k_color": "สี %K",
    "d_color": "สี %D", "adx_color": "สี ADX", "pdi_color": "สี +DI", "mdi_color": "สี -DI"
}

INPUT_LABELS = {
    "fast": "Fast EMA Length", "slow": "Slow EMA Length", "trend": "Trend Filter Length",
    "min_tp_pct": "Take Profit ขั้นต่ำ (%)", "warn_pct": "จุดเตือนสีส้ม Warning (%)",
    "danger_pct": "จุดอันตรายสีแดง Danger (%)", "length": "Length (ความยาวรอบ)",
    "std_dev": "StdDev (ความกว้างเบี่ยงเบน)", "source": "ราคาอ้างอิง (Source)",
    "atr_period": "ATR Period", "factor": "Factor Multiplier", "conversion": "Conversion (Tenkan)",
    "base": "Base (Kijun)", "span_b": "Leading Span B", "ob": "Overbought Level",
    "os": "Oversold Level", "signal": "Signal Length", "k_len": "%K Length",
    "k_smooth": "%K Smoothing", "d_smooth": "%D Smoothing", "adx_len": "ADX Length",
    "threshold": "Threshold Level", "ma_len": "Volume MA Length"
}

def init_indicator_state():
    for code, cfg in INDICATOR_CONFIGS.items():
        if f"ind_active_{code}" not in st.session_state:
            st.session_state[f"ind_active_{code}"] = cfg["default"]
        if f"ind_fav_{code}" not in st.session_state:
            st.session_state[f"ind_fav_{code}"] = (code in ["DIAMOND", "EMA", "RSI", "MACD"])
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
                "active": False,
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
        st.session_state["sidebar_active_nav"] = "📈 ทางเทคนิค"

def apply_pine_script_to_chart(script_title, script_code, is_active):
    st.session_state["custom_pine_active"] = is_active
    st.session_state["custom_pine_title"] = script_title
    st.session_state["custom_pine_code"] = script_code

def _trigger_app_rerun():
    try:
        st.rerun(scope="app")
    except TypeError:
        st.rerun()

def _on_modal_dismiss():
    st.session_state["modal_indicators_open"] = False

def _render_modal_body():
    init_indicator_state()

    st.markdown("""
        <style>
        .stTextArea textarea {
            border: 1.5px solid #ff9800 !important;
            box-shadow: 0 0 12px rgba(255, 152, 0, 0.45) !important;
            background-color: #0d1117 !important;
            color: #f8fafc !important;
            font-family: 'Consolas', 'Monaco', monospace !important;
            font-size: 13px !important;
            border-radius: 8px !important;
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

    # ── เมนูนำทางฝั่งซ้าย ──
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

    # ── พื้นที่แสดงผลฝั่งขวา ──
    with col_content:
        current_nav = st.session_state["sidebar_active_nav"]

        # 1. หน้าสคริปต์ของฉัน (3 แท็บ: รายการสคริปต์ | ตัวแก้ไขโค้ด | สร้างโค้ดใหม่)
        if current_nav == "👤 สคริปต์ของฉัน (เครื่องมือที่ฉันออกแบบ)" and not search_kw:
            tab_list, tab_editor, tab_create = st.tabs(["📋 รายการสคริปต์ของฉัน", "⚡ ตัวแก้ไขโค้ด (Pine Editor)", "➕ สร้างโค้ดใหม่"])

            with tab_list:
                h_star, h_name, h_author, h_toggle, h_del = st.columns([0.08, 0.44, 0.24, 0.14, 0.10])
                with h_name: st.markdown("<b style='color:#787b86; font-size:12px;'>ชื่อ</b>", unsafe_allow_html=True)
                with h_author: st.markdown("<b style='color:#787b86; font-size:12px;'>ผู้เขียน</b>", unsafe_allow_html=True)
                with h_toggle: st.markdown("<b style='color:#787b86; font-size:12px;'>เปิดใช้</b>", unsafe_allow_html=True)
                with h_del: st.markdown("<b style='color:#787b86; font-size:12px;'>จัดการ</b>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:4px 0 10px 0; border:0.5px solid #21262d;'>", unsafe_allow_html=True)

                db = st.session_state["my_scripts"]
                for s_name, s_data in list(db.items()):
                    row_star, row_title, row_author, row_sw, row_del = st.columns([0.08, 0.44, 0.24, 0.14, 0.10], vertical_alignment="center")
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
                            _trigger_app_rerun()
                    with row_del:
                        if st.button("🗑️", key=f"del_script_btn_{s_name}", help=f"ลบสคริปต์ {s_name}"):
                            if s_data.get("active", False):
                                apply_pine_script_to_chart(s_name, "", False)
                            del db[s_name]
                            remaining = list(db.keys())
                            st.session_state["current_editor_script_name"] = remaining[0] if remaining else "กลยุทธ์ใหม่ของฉัน"
                            st.toast(f"ลบ '{s_name}' เรียบร้อยแล้ว")
                            _trigger_app_rerun()

                    with st.expander(f"📝 ดูโค้ดสคริปต์ {s_name}"):
                        st.code(s_data["code"], language="pine")

            with tab_editor:
                st.markdown("<div style='font-size: 14px; font-weight: bold; color: #ff9800; margin-bottom: 8px;'>⚡ Pine Editor — แก้ไขโค้ดกลยุทธ์ (Monaco Engine)</div>", unsafe_allow_html=True)
                db = st.session_state["my_scripts"]
                script_list = list(db.keys())

                if not script_list:
                    st.info("💡 ยังไม่มีสคริปต์ในคลัง กดที่แท็บ '➕ สร้างโค้ดใหม่' เพื่อสร้างสคริปต์แรกของคุณ")
                else:
                    ed_c1, ed_c2 = st.columns([0.65, 0.35])
                    with ed_c1:
                        cur_sel = st.selectbox(
                            "เลือกสคริปต์ที่จะแก้ไข:", 
                            options=script_list, 
                            index=script_list.index(st.session_state["current_editor_script_name"]) if st.session_state["current_editor_script_name"] in script_list else 0, 
                            key="editor_select_box"
                        )
                        active_title = cur_sel
                        active_code = db[cur_sel]["code"]
                        st.session_state["current_editor_script_name"] = cur_sel

                    with ed_c2:
                        script_title_input = st.text_input("ชื่อสคริปต์:", value=active_title, key="editor_title_input")

                    if HAS_MONACO:
                        pine_code_input = st_monaco(value=active_code, height="300px", language="python", theme="vs-dark", key=f"monaco_{cur_sel}")
                        if pine_code_input is None:
                            pine_code_input = active_code
                    else:
                        pine_code_input = st.text_area("Pine Script Code:", value=active_code, height=270, key="editor_code_textarea")

                    btn_col1, btn_del, btn_col2, btn_col3 = st.columns([0.35, 0.20, 0.20, 0.25])
                    with btn_col1:
                        if st.button("💾 บันทึกสคริปต์ลงคลัง", use_container_width=True, type="primary"):
                            if script_title_input:
                                is_active_prev = db.get(cur_sel, {}).get("active", False)
                                is_fav_prev = db.get(cur_sel, {}).get("fav", False)
                                if script_title_input != cur_sel and cur_sel in db:
                                    del db[cur_sel]
                                db[script_title_input] = {
                                    "author": "Takayakating9...",
                                    "code": pine_code_input,
                                    "active": is_active_prev,
                                    "fav": is_fav_prev
                                }
                                if is_active_prev:
                                    apply_pine_script_to_chart(script_title_input, pine_code_input, True)

                                st.session_state["current_editor_script_name"] = script_title_input
                                st.success(f"บันทึก '{script_title_input}' สำเร็จ!")
                                _trigger_app_rerun()

                    with btn_del:
                        if cur_sel in db:
                            if st.button("🗑️ ลบสคริปต์นี้", use_container_width=True, type="secondary"):
                                if db[cur_sel].get("active", False):
                                    apply_pine_script_to_chart(cur_sel, "", False)
                            del db[cur_sel]
                            remaining = list(db.keys())
                            st.session_state["current_editor_script_name"] = remaining[0] if remaining else "กลยุทธ์ใหม่ของฉัน"
                            st.toast(f"ลบ '{cur_sel}' เรียบร้อยแล้ว")
                            _trigger_app_rerun()

                    with btn_col2:
                        if cur_sel in db:
                            cur_act = db[cur_sel].get("active", False)
                            tgl_act = st.toggle("ติกลงกราฟ", value=cur_act, key=f"tgl_ed_{cur_sel}")
                            if tgl_act != cur_act:
                                db[cur_sel]["active"] = tgl_act
                                apply_pine_script_to_chart(cur_sel, db[cur_sel]["code"], tgl_act)
                                _trigger_app_rerun()

                    with btn_col3:
                        if st.button("🔍 ตรวจสอบโค้ด", use_container_width=True, type="secondary"):
                            if "//@version=5" in pine_code_input or "strategy" in pine_code_input or "indicator" in pine_code_input:
                                st.info("✅ ไวยากรณ์ถูกต้อง: พร้อมประมวลผลบนกราฟ")
                            else:
                                st.error("❌ จำเป็นต้องมี //@version=5 หรือ indicator/strategy")

            with tab_create:
                st.markdown("<div style='font-size: 14px; font-weight: bold; color: #00e676; margin-bottom: 8px;'>➕ สร้างสคริปต์ Pine Script ใหม่</div>", unsafe_allow_html=True)
                
                cr_c1, cr_c2 = st.columns([0.65, 0.35])
                with cr_c1:
                    new_script_title = st.text_input("ชื่อสคริปต์ใหม่:", value="กลยุทธ์ใหม่ของฉัน", key="create_title_input")
                with cr_c2:
                    template_sel = st.selectbox("เทมเพลตเริ่มต้น:", ["Indicator (ตัวชี้วัด)", "Strategy (ระบบเทรด)"], key="template_select")

                if template_sel == "Indicator (ตัวชี้วัด)":
                    default_new_code = '''//@version=5
indicator("My Custom Indicator", overlay=true)
ema_fast = ta.ema(close, 9)
ema_slow = ta.ema(close, 21)
plot(ema_fast, color=color.blue, title="Fast EMA")
plot(ema_slow, color=color.orange, title="Slow EMA")
'''
                else:
                    default_new_code = '''//@version=5
strategy("My Custom Strategy", overlay=true)
longCondition = ta.crossover(ta.ema(close, 14), ta.ema(close, 28))
if (longCondition)
    strategy.entry("Long", strategy.long)
plotshape(longCondition, style=shape.triangleup, location=location.belowbar, color=color.green, text="BUY")
'''

                if HAS_MONACO:
                    created_code_input = st_monaco(value=default_new_code, height="300px", language="python", theme="vs-dark", key="monaco_create_code")
                    if created_code_input is None:
                        created_code_input = default_new_code
                else:
                    created_code_input = st.text_area("เขียนโค้ดใหม่ที่นี่:", value=default_new_code, height=270, key="create_code_textarea")

                cr_btn1, cr_btn2 = st.columns([0.40, 0.30])
                with cr_btn1:
                    if st.button("🚀 บันทึกและเพิ่มเข้าคลัง", use_container_width=True, type="primary", key="btn_save_new_script"):
                        clean_title = new_script_title.strip()
                        if not clean_title:
                            st.error("กรุณาระบุชื่อสคริปต์")
                        else:
                            db = st.session_state["my_scripts"]
                            db[clean_title] = {
                                "author": "Takayakating9...",
                                "code": created_code_input,
                                "active": False,
                                "fav": False
                            }
                            st.session_state["current_editor_script_name"] = clean_title
                            st.success(f"สร้างและบันทึกสคริปต์ '{clean_title}' สำเร็จแล้ว!")
                            _trigger_app_rerun()
                with cr_btn2:
                    if st.button("🔍 ตรวจสอบไวยากรณ์", use_container_width=True, type="secondary", key="btn_check_new_script"):
                        if "//@version=5" in created_code_input or "strategy" in created_code_input or "indicator" in created_code_input:
                            st.info("✅ ไวยากรณ์ถูกต้อง: พร้อมบันทึก")
                        else:
                            st.error("❌ จำเป็นต้องมี //@version=5 หรือ indicator/strategy")

        # 2. หน้าแสดงรายการโปรด / ทางเทคนิค / ผลการค้นหา
        else:
            h_star, h_name, h_author, h_toggle = st.columns([0.08, 0.48, 0.28, 0.16])
            with h_name: st.markdown("<b style='color:#787b86; font-size:12px;'>ชื่อ</b>", unsafe_allow_html=True)
            with h_author: st.markdown("<b style='color:#787b86; font-size:12px;'>ผู้เขียน</b>", unsafe_allow_html=True)
            with h_toggle: st.markdown("<b style='color:#787b86; font-size:12px;'>เปิดใช้</b>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0 10px 0; border:0.5px solid #21262d;'>", unsafe_allow_html=True)

            if current_nav == "⭐ รายการโปรด" or (search_kw and any(search_kw in k.lower() for k in st.session_state["my_scripts"])):
                db = st.session_state["my_scripts"]
                for s_name, s_data in db.items():
                    if current_nav == "⭐ รายการโปรด" and not s_data.get("fav", False):
                        continue
                    if search_kw and (search_kw not in s_name.lower()):
                        continue
                    row_star, row_title, row_author, row_sw = st.columns([0.08, 0.48, 0.28, 0.16], vertical_alignment="center")
                    with row_star:
                        is_fav = s_data.get("fav", False)
                        if st.button("⭐" if is_fav else "☆", key=f"fav_star_my_{s_name}"):
                            s_data["fav"] = not is_fav
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
                            _trigger_app_rerun()

            if current_nav in ["⭐ รายการโปรด", "📈 ทางเทคนิค"] or search_kw:
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
                            _trigger_app_rerun()

                    # หน้าต่างตั้งค่าแบบครอบคลุมทุกส่วน (Inputs & Style)
                    with st.expander(f"⚙️ ตั้งค่า {cfg['name']} (Inputs & Style)"):
                        t_in, t_st = st.tabs(["📥 Inputs (การคำนวณ)", "🎨 Style (รูปแบบและสี)"])
                        
                        with t_in:
                            cols = st.columns(2)
                            for i, (k, default_val) in enumerate(cfg["inputs"].items()):
                                target_col = cols[i % 2]
                                inp_k = f"{code}_in_{k}"
                                label_in = INPUT_LABELS.get(k, k.replace('_', ' ').title())
                                with target_col:
                                    if k == "source":
                                        st.session_state[inp_k] = st.selectbox(label_in, PRICE_SOURCES, index=PRICE_SOURCES.index(st.session_state.get(inp_k, default_val)), key=f"ui_{inp_k}")
                                    elif isinstance(default_val, float):
                                        st.session_state[inp_k] = st.number_input(label_in, value=float(st.session_state.get(inp_k, default_val)), step=0.1, key=f"ui_{inp_k}")
                                    elif isinstance(default_val, int):
                                        st.session_state[inp_k] = st.number_input(label_in, min_value=1, value=int(st.session_state.get(inp_k, default_val)), step=1, key=f"ui_{inp_k}")
                                    elif isinstance(default_val, bool):
                                        st.session_state[inp_k] = st.toggle(label_in, value=bool(st.session_state.get(inp_k, default_val)), key=f"ui_{inp_k}")

                        with t_st:
                            s_cols = st.columns(2)
                            idx = 0
                            for k, default_val in cfg["style"].items():
                                st_k = f"{code}_st_{k}"
                                target_col = s_cols[idx % 2]
                                display_label = STYLE_LABELS.get(k, k.replace('_', ' ').title())
                                
                                if isinstance(default_val, bool):
                                    with target_col:
                                        st.session_state[st_k] = st.toggle(display_label, value=bool(st.session_state.get(st_k, default_val)), key=f"ui_{st_k}")
                                    idx += 1
                                elif "color" in k:
                                    with target_col:
                                        cur_color = st.session_state.get(st_k, default_val)
                                        base_color = str(cur_color) if str(cur_color).startswith("#") else "#2962ff"
                                        st.session_state[st_k] = st.color_picker(display_label, value=base_color, key=f"ui_{st_k}")
                                    idx += 1
                                elif "width" in k:
                                    with target_col:
                                        st.session_state[st_k] = st.slider(f"ความหนา {display_label}", 1, 4, value=int(st.session_state.get(st_k, default_val)), key=f"ui_{st_k}")
                                    idx += 1

try:
    @st.dialog("อินดิเคเตอร์ ตัวชี้วัด และกลยุทธ์ (Indicators Library & Pine Script)", width="large", on_dismiss=_on_modal_dismiss)
    def show_indicators_modal():
        _render_modal_body()
except TypeError:
    @st.dialog("อินดิเคเตอร์ ตัวชี้วัด และกลยุทธ์ (Indicators Library & Pine Script)", width="large")
    def show_indicators_modal():
        _render_modal_body()

def show_indicators_library_modal():
    show_indicators_modal()