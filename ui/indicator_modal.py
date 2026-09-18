import streamlit as st

INDICATOR_REGISTRY = {
    "EMA": {
        "name": "EMA Ribbon (7, 13, 45)",
        "desc": "เส้นค่าเลี่ยเคลื่อนที่ 3 เส้นระบุแนวน้มบนกราฟหลัก",
        "state_key": "show_ema",
        "default_on": True,
    },
    "RSI": {
        "name": "Relative Strength Index (RSI 14)",
        "desc": "ดัชนีโมเมนตัมวัดภาวะซื้อมากเกินไป / ขายมากเกินไป (Sub-pane ล่าง)",
        "state_key": "show_rsi_pane",
        "default_on": True,
    },
    "MACD": {
        "name": "MACD (12, 26, 9)",
        "desc": "เส้นสัญญาณแนวโน้มและโมเมนตัมพร้อม Histogram (Sub-pane ล่างสุด)",
        "state_key": "show_macd_pane",
        "default_on": True,
    },
    "VOL": {
        "name": "Volume (ปริมาื้อขาย)",
        "desc": "แท่งแสดงปริมาการื้อขายใต้แท่งเทียนหลัก",
        "state_key": "show_volume",
        "default_on": True,
    },
}

def init_indicator_state():
    if "favorite_indicators" not in st.session_state:
        st.session_state["favorite_indicators"] = ["EMA", "RSI", "MACD"]
    for code, meta in INDICATOR_REGISTRY.items():
        if meta["state_key"] not in st.session_state:
            st.session_state[meta["state_key"]] = meta["default_on"]

@st.dialog("📊 คลังอินดิเคเตอร (Indicators & Strategies)", width="large")
def show_indicators_modal():
    init_indicator_state()
    st.caption("คลิกเปิด-ปิดการแสดงผล หรือกด ⭐ เพื่อปักหมุดเปนปุ่มลัดด่วนบน Top Bar")

    favs = set(st.session_state["favorite_indicators"])
    st.markdown("<hr style='margin: 8px 0 14px 0; border: 0.5px solid #2a2e39;'>", unsafe_allow_html=True)

    for code, meta in INDICATOR_REGISTRY.items():
        c_star, c_info, c_toggle = st.columns([0.6, 5.2, 1.2], vertical_alignment="center")

        with c_star:
            is_fav = code in favs
            if st.button("⭐" if is_fav else "☆", key=f"fav_btn_{code}", help="ปักหมุดบน Top Bar"):
                if is_fav:
                    favs.remove(code)
                else:
                    favs.add(code)
                st.session_state["favorite_indicators"] = list(favs)
                try:
                    st.rerun(scope="app")
                except TypeError:
                    st.rerun()

        with c_info:
            st.markdown(f"**{meta['name']}**")
            st.caption(meta["desc"])

        with c_toggle:
            cur_val = st.session_state.get(meta["state_key"], True)
            new_val = st.toggle("แสดง", value=cur_val, key=f"tg_{code}", label_visibility="collapsed")
            if new_val != cur_val:
                st.session_state[meta["state_key"]] = new_val
                try:
                    st.rerun(scope="app")
                except TypeError:
                    st.rerun()

        st.markdown("<hr style='margin: 6px 0; border: 0.5px solid #1e222d;'>", unsafe_allow_html=True)
