# ui/dock_menu.py
import streamlit as st

def render_dock_menu():
    st.markdown('<div style="font-size: 11px; font-weight: 700; color: #D1D4DC; margin-bottom: 4px;">⚡ แผงควบคุมระบบ</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        with st.popover("🅧", use_container_width=True):
            st.write("ตั้งค่าหน้าจอหลัก")
            st.session_state["mobile_mode"] = st.checkbox("โหมดมือถือ (Mobile Layout)", value=st.session_state.get("mobile_mode", False))
        with st.popover("📐", use_container_width=True):
            st.write("เครื่องมือวาดกราฟ")
            st.session_state["fib_confirm_on"] = st.checkbox("ยืนยัน Golden Zone", value=st.session_state.get("fib_confirm_on", False))
    with c2:
        with st.popover("📊", use_container_width=True):
            st.write("ข้อมูลตลาดด่วน")
            if st.button("เปิดหน้าต่างตลาด 24h", use_container_width=True):
                st.session_state["trigger_market_modal"] = True
                st.rerun()
        with st.popover("⚙️", use_container_width=True):
            st.write("ตั้งค่าระบบขั้นสูง")
            if st.button("🧹 ล้างแคชระบบ", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
                st.write("")
    if st.button("🌾 เช็คราคาข้าว", use_container_width=True):
        st.session_state["active_tab"] = "🌾 ราคาข้าว"
        st.rerun() 