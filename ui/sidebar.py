# ui/sidebar.py
import streamlit as st
from ui.dock_menu import render_dock_menu


def render_sidebar():
    # 1. การ์ดนาฬิกาเรียลไทม์ขนาดกะทัดรัด (ตัวเลขบรรทัดเดียว ไม่แตกแถว)
    st.markdown(
        """
    <div style="
        background: #0B0E14;
        border: 1px solid #FF7A00;
        border-radius: 8px;
        padding: 5px 8px;
        margin-bottom: 2px;
        box-shadow: 0 0 8px rgba(255, 122, 0, 0.2);
    ">
        <div style="font-size: 8.5px; color: #8F9CAE; margin-bottom: 1px;">ตัวอย่างแบบเรียลไทม์</div>
        <div id="sb-clock" style="
            font-family: 'Courier New', Consolas, monospace;
            font-size: 1.15rem;
            font-weight: 800;
            color: #00FF66;
            text-align: center;
            letter-spacing: 1px;
            white-space: nowrap;
            text-shadow: 0 0 8px rgba(0, 255, 102, 0.6);
            margin: 1px 0 3px 0;
        ">
            --:--:--
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255, 122, 0, 0.2); padding-top: 2px;">
            <span style="font-size: 8px; color: #8F9CAE;">📍 BKK (UTC+7)</span>
            <span style="font-size: 8px; color: #00FF66; font-weight: 700; background: rgba(0, 255, 102, 0.12); padding: 1px 4px; border-radius: 3px;">● ออนไลน์</span>
        </div>
    </div>
    <script>
    function updateSbClock() {
        const el = document.getElementById('sb-clock');
        if (el) {
            el.textContent = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Bangkok', hour12: false });
        }
    }
    if (window.sbClockTimer) clearInterval(window.sbClockTimer);
    window.sbClockTimer = setInterval(updateSbClock, 1000);
    updateSbClock();
    </script>
    """,
        unsafe_allow_html=True,
    )

    # 2. หมวดการแสดงผล
    st.markdown(
        """
    <div style="font-size: 10.5px; font-weight: 700; color: #D1D4DC; margin: 4px 0 2px 0; display: flex; align-items: center; gap: 4px;">
        <span style="width: 3px; height: 10px; background: #FF7A00; border-radius: 1px;"></span>
        การแสดงผล
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.toggle(
        "แสดงแถบควบคุมด้านบน (TF/บาร์)",
        value=st.session_state.get("show_toolbar", True),
        key="show_toolbar",
    )
    st.toggle(
        "แสดงแถบเครื่องมือวาดบนกราฟ",
        value=st.session_state.get("show_drawing_tools", True),
        key="show_drawing_tools",
    )

    # 3. หมวดแผงควบคุมระบบ (Dock Menu)
    st.markdown(
        """
    <div style="font-size: 10.5px; font-weight: 700; color: #D1D4DC; margin: 5px 0 2px 0; display: flex; align-items: center; gap: 4px;">
        <span style="width: 3px; height: 10px; background: #FF7A00; border-radius: 1px;"></span>
        รูปลักษณ์ & ระบบ
    </div>
    """,
        unsafe_allow_html=True,
    )

    render_dock_menu()