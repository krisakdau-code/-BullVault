# ui/dock_menu.py
import streamlit as st

def render_dock_menu():
    st.markdown('<div style="font-size: 11px; font-weight: 700; color: #D1D4DC; margin-bottom: 6px;">⚡ แผงควบคุมระบบ</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        with st.popover("⚙", use_container_width=True):
            st.write("ตั้งค่าหน้าจอหลัก")
            st.session_state["mobile_mode"] = st.checkbox("โหมดมือถือ (Mobile Layout)", value=st.session_state.get("mobile_mode", False))

        with st.popover("📐", use_container_width=True):
            st.write("เครื่องมือวาดกราฟ")
            st.session_state["fib_confirm_on"] = st.checkbox("ยืนยัน Golden Zone", value=st.session_state.get("fib_confirm_on", False))

    with c2:
        # ปุ่ม 2: เปิดหน้าต่างตลาด 24h
        if st.button("📊", key="dock_btn_mkt", use_container_width=True, help="เปิดหน้าต่างตลาด 24h"):
            st.session_state["trigger_market_modal"] = True
            st.rerun()

        # ปุ่ม 3: เปิดหน้าต่างการตั้งค่า TradingView กลางจอ
        if st.button("⚙️", key="dock_btn_settings", use_container_width=True, help="ตั้งค่ากราฟ & อินดิเคเตอร์"):
            st.session_state["trigger_settings_modal"] = True
            st.rerun()

    # ปุ่มสลับไปหน้าราคาข้าว
    if st.button("🌾 เช็คราคาข้าว", key="btn_dock_rice", use_container_width=True):
        st.session_state["app_mode"] = "rice"
        st.rerun()