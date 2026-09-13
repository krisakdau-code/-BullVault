# ui/sidebar.py
import streamlit as st
from ui.dock_menu import render_dock_menu

def render_sidebar():
    with st.sidebar:
        # 1. นาฬิกา JavaScript แบบเรียลไทม์ (ไม่มีการใช้ฟังก์ชันฝั่ง Python รันซ้ำซ้อน)
        st.markdown("""
        <div style="background: #0B0E14; border: 1px solid #FF7A00; border-radius: 8px; padding: 6px; margin-bottom: 8px;">
            <div style="font-size: 8px; color: #8F9CAE;">📍 BKK (UTC+7)</div>
            <div id="sb-clock" style="font-family: monospace; font-size: 1.2rem; font-weight: 800; color: #FF7A1A; text-align: center;">--:--:--</div>
        </div>
        <script>
        function updateClock() {
            const el = document.getElementById('sb-clock');
            if (el) el.textContent = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Bangkok', hour12: false });
        }
        if (window.clockInterval) clearInterval(window.clockInterval);
        window.clockInterval = setInterval(updateClock, 1000);
        updateClock();
        </script>
        """, unsafe_allow_html=True)

        st.divider()

        # 2. ตัวควบคุมหลักของแอป (ประกาศ Widget ที่นี่ที่เดียว ป้องกัน NameError และ Widget ชนกัน)
        show_top = st.toggle("แสดงแถบควบคุมด้านบน (TF/บาร์)", key="show_top_bar", value=True)
        show_tool = st.toggle("แสดงแถบเครื่องมือบนกราฟ", key="show_draw_toolbar", value=True)

        st.divider()

        # 3. แผงควบคุมระบบ (แยกส่วนการแสดงผลแบบ Read-Only)
        render_dock_menu()

    # ส่งค่าสถานะทั้งหมดกลับไปให้ app.py ควบคุมต่อ
    return {
        "show_top_bar": show_top,
        "show_draw_toolbar": show_tool
    }