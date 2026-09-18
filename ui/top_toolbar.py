import streamlit as st
from ui.indicator_modal import show_indicators_modal, INDICATOR_REGISTRY, init_indicator_state

ALL_TIMEFRAMES = {
    "นาที": [
        ("1m", "1 นาที"), ("3m", "3 นาที"), ("5m", "5 นาที"),
        ("15m", "15 นาที"), ("30m", "30 นาที"), ("45m", "45 นาที")
    ],
    "ชั่วโมง": [
        ("1h", "1 ชั่วโมง"), ("2h", "2 ชั่วโมง"),
        ("3h", "3 ชั่วโมง"), ("4h", "4 ชั่วโมง")
    ],
    "วัน / สัปดาห์ / เดือน": [
        ("D", "1 วัน"), ("2D", "2 วัน"), ("3D", "3 วัน"),
        ("W", "1 สัปดาห์"), ("M", "1 เดือน"),
        ("3M", "3 เดือน"), ("6M", "6 เดือน"), ("12M", "12 เดือน")
    ]
}

DEFAULT_FAVORITES = ["5m", "15m", "30m", "1h", "2h", "3h", "4h", "D", "2D", "3D", "W", "M"]

def init_toolbar_state():
    if "selected_tf" not in st.session_state:
        st.session_state.selected_tf = "1h"
    if "favorite_tfs" not in st.session_state:
        st.session_state.favorite_tfs = DEFAULT_FAVORITES.copy()

def render_top_toolbar(current_symbol: str = "BTCUSDT", **kwargs):
    init_toolbar_state()
    
    st.markdown("""
        <style>
        .stButton button {
            border-radius: 4px !important;
            padding: 2px 8px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }
        div[data-testid="stPopover"] > button {
            background-color: transparent !important;
            border: 1px solid #363c4e !important;
            color: #d1d4dc !important;
            height: 34px !important;
            border-radius: 4px !important;
        }
        div[data-testid="stPopover"] > button:hover {
            background-color: #2a2e39 !important;
            color: #2962ff !important;
        }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns([2.2, 0.4, 6.5, 0.6, 2.3])

    # 1. ปุ่มชื่อเหรียญ
    with cols[0]:
        if st.button(f"💎 {current_symbol}", key="btn_sym_modal", use_container_width=True):
            st.session_state.show_symbol_search = True
            st.rerun()

    # 2. ปุ่มเปรียบเทียบ (+)
    with cols[1]:
        st.button("＋", key="btn_compare", help="เปรียบเทียบสินทรัพย์")

    # 3. แถบ Timeframe ติดดาว
    with cols[2]:
        fav_list = st.session_state.favorite_tfs
        if fav_list:
            fav_cols = st.columns(len(fav_list))
            for idx, tf_code in enumerate(fav_list):
                is_active = (st.session_state.selected_tf == tf_code)
                btn_type = "primary" if is_active else "secondary"
                if fav_cols[idx].button(tf_code, key=f"tf_bar_{tf_code}", type=btn_type):
                    st.session_state.selected_tf = tf_code
                    st.rerun()

    # 4. ปุ่มดรอปดาวน์ ⌵ เปิดแผงเลือก Timeframe
    with cols[3]:
        with st.popover("⌵"):
            st.markdown("##### ⏱️ เลือกช่วงเวลา")
            for cat_name, items in ALL_TIMEFRAMES.items():
                st.caption(f"**{cat_name}**")
                for code, label in items:
                    c1, c2 = st.columns([4, 1])
                    is_active = (st.session_state.selected_tf == code)
                    display_text = f"👉 {label} ({code})" if is_active else f"{label} ({code})"
                    
                    if c1.button(display_text, key=f"pop_sel_{code}", use_container_width=True):
                        st.session_state.selected_tf = code
                        st.rerun()

                    is_fav = code in st.session_state.favorite_tfs
                    star_icon = "★" if is_fav else "☆"
                    if c2.button(star_icon, key=f"pop_star_{code}"):
                        if is_fav:
                            if len(st.session_state.favorite_tfs) > 1:
                                st.session_state.favorite_tfs.remove(code)
                        else:
                            st.session_state.favorite_tfs.append(code)
                        st.rerun()
                st.divider()

    # 5. ปุ่มคลังอินดิเคเตอร์ + ปุ่มลัดด่วนติดดาว ⭐
    with cols[4]:
        init_indicator_state()
        fav_codes = [c for c in st.session_state.get("favorite_indicators", []) if c in INDICATOR_REGISTRY]
        
        # แบ่งคอลัมน์ย่อยแนวนอน: ปุ่มคลังหลัก + ชิปปุ่มลัดตามจำนวนดาวที่ปักไว้
        sub_cols = st.columns([1.6] + [1.0] * len(fav_codes))
        
        with sub_cols[0]:
            if st.button("📊 Indicators", key="btn_open_ind_modal", type="secondary", use_container_width=True, help="เปิดคลังอินดิเคเตอร์"):
                show_indicators_modal()

        for idx, code in enumerate(fav_codes):
            with sub_cols[idx + 1]:
                meta = INDICATOR_REGISTRY[code]
                is_active = st.session_state.get(meta["state_key"], True)
                btn_style = "primary" if is_active else "tertiary"
                if st.button(code, key=f"quick_fav_{code}", type=btn_style, use_container_width=True, help=f"เปิด/ปิด {meta['name']}"):
                    st.session_state[meta["state_key"]] = not is_active
                    try:
                        st.rerun(scope="app")
                    except TypeError:
                        st.rerun()

    return st.session_state.selected_tf