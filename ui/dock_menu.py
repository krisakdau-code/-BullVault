# ui/dock_menu.py
import streamlit as st

def render_dock_menu():
    st.markdown('<div style="font-size: 11px; font-weight: 700; color: #D1D4DC; margin-bottom: 4px;">⚡ แผงควบคุมระบบ</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        with st.popover("🅧", use_container_width=True):
            st.write("ตั้งค่าหน้าจอหลัก")
        with st.popover("📐", use_container_width=True):
            st.write("เครื่องมือวาดกราฟ")
    with c2:
        with st.popover("📊", use_container_width=True):
            st.write("ข้อมูลตลาด")
        with st.popover("⚙️", use_container_width=True):
            st.write("ตั้งค่าระบบ")
            st.radio("Display Mode", ["Desktop", "Mobile"], horizontal=True, key="device_mode")
            if st.button("🧹 ล้างแคชระบบ", use_container_width=True):
                st.cache_data.clear()
                st.rerun()