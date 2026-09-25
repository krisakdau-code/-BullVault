# ui/mobile_view.py — Dedicated Mobile View (TradingView Mobile Style)
import streamlit as st
from ui.right_panel import render_right_panel


def render_mobile_view(
    df,
    meta,
    is_thb_mode: bool,
    fx_rate: float,
    chart_renderer=None,
    watchlist_renderer=None,
):
  """จัดหน้าต่างแสดงผลแบบเต็มจอสำหรับสมาร์ตโฟน (Full-Width Tabs)

  พร้อมระบบซ่อนส่วนหัวเดิม จัดระเบียบปุ่มกรอง และรองรับการหมุนจอแนวนอนเต็มจอ
  100%
  """
  # ซ่อนแถบเครื่องมือวาดรูปเป็นค่าเริ่มต้นบนมือถือเพื่อให้กราฟกว้างเต็มจอ
  if "show_draw_toolbar" not in st.session_state:
    st.session_state["show_draw_toolbar"] = False

  # -------------------------------------------------------------------------
  # CSS จัดการเฉพาะโหมดมือถือ: ซ่อนส่วนหัวที่วงแดง + จัดปุ่มกรองแนวนอน + รองรับแนวนอนเต็มจอ
  # -------------------------------------------------------------------------
  st.markdown(
      """
    <style>
        /* 1. ซ่อนส่วนหัวเดิมของ Desktop ทั้งหมด (ที่วงสีแดงในรูปที่ 4) เมื่ออยู่ในโหมดมือถือ */
        div[data-testid="stHorizontalBlock"]:has(#top-tabs-marker) {
            display: none !important;
            height: 0px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        #toggle-btn-anchor {
            display: none !important;
        }
        div[data-testid="stColumn"]:has(div[role="radiogroup"]) {
            display: none !important;
        }
        div[data-testid="stColumn"]:has(#btn_open_ind_modal),
        div[data-testid="stColumn"]:has(button[key="btn_open_ind_modal"]) {
            display: none !important;
        }

        /* 2. จัดระเบียบปุ่มสวิตช์มือถือให้อยู่ด้านบนขวา ไม่กินพื้นที่หน้าจอ */
        div[data-testid="stColumn"]:has(div[data-testid="stToggle"]) {
            display: flex !important;
            justify-content: flex-end !important;
            padding: 0px 8px !important;
            margin-top: -6px !important;
            margin-bottom: 2px !important;
        }

        /* 3. สไตล์แท็บหลัก 3 แท็บด้านบนให้สัมผัสง่ายและกะทัดรัด */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px !important;
            width: 100% !important;
            background: #11141c !important;
            padding: 3px !important;
            border-radius: 8px !important;
            border: 1px solid #1e2433 !important;
            margin-bottom: 6px !important;
        }
        .stTabs [data-baseweb="tab"] {
            flex: 1 !important;
            text-align: center !important;
            padding: 6px 2px !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            color: #8b949e !important;
            border: none !important;
        }
        .stTabs [aria-selected="true"] {
            background: #1a2233 !important;
            color: #00e676 !important;
            box-shadow: 0 0 8px rgba(0, 230, 118, 0.3) !important;
        }

        /* 4. แก้ปัญหารูปที่ 2: บังคับให้ปุ่มสีตัวกรองใน Watchlist เรียงเป็นแนวนอนแถวเดียว */
        div[data-testid="stTabs"] div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
            align-items: center !important;
        }
        div[data-testid="stTabs"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: auto !important;
            flex: 1 1 0px !important;
            min-width: 0 !important;
        }

        /* 5. โหมดแนวนอน (Landscape Mode): บังคับให้กราฟขยายเต็มหน้าจอ 100% อัตโนมัติ */
        @media (orientation: landscape) and (max-height: 580px) {
            .stTabs [data-baseweb="tab-list"],
            div[data-testid="stColumn"]:has(div[data-testid="stToggle"]),
            .mobile-chart-controls {
                display: none !important;
            }
            div[data-testid="stCustomComponentV1"],
            iframe {
                height: 96vh !important;
                max-height: 96vh !important;
            }
        }
    </style>
    """,
      unsafe_allow_html=True,
  )

  # แท็บหลัก 3 แท็บสำหรับมือถือ
  tab_chart, tab_watch, tab_info = st.tabs(
      ["📈 ชาร์ต", "📋 รายการเฝ้าดู", "📊 ภาพรวม & เทคนิค"]
  )

  # =========================================================================
  # แท็บ 1: ชาร์ตกราฟ (Chart Tab)
  # =========================================================================
  with tab_chart:
    cur_tf = st.session_state.get("selected_tf", "1h")

    # แถบควบคุมบนชาร์ตแบบกะทัดรัด (TradingView Mobile Style)
    st.markdown('<div class="mobile-chart-controls">', unsafe_allow_html=True)
    m_c1, m_c2, m_c3 = st.columns([1.8, 1.2, 1.0], gap="small")

    with m_c1:
      tf_options = ["5m", "15m", "30m", "1h", "2h", "4h", "D", "W"]
      selected_m_tf = st.selectbox(
          "TF",
          options=tf_options,
          index=tf_options.index(cur_tf) if cur_tf in tf_options else 3,
          key="mobile_tf_selector",
          label_visibility="collapsed",
      )
      if selected_m_tf != cur_tf:
        st.session_state["selected_tf"] = selected_m_tf
        tabs = st.session_state.get("chart_tabs", [])
        active_id = st.session_state.get("active_tab_id")
        for t in tabs:
          if t["id"] == active_id:
            t["tf"] = selected_m_tf
        st.rerun()

    with m_c2:
      if st.button(
          "📊 ตัวชี้วัด",
          key="btn_m_ind",
          use_container_width=True,
          type="secondary",
      ):
        st.session_state["modal_indicators_open"] = True
        st.rerun()

    with m_c3:
      is_toolbar = st.session_state.get("show_draw_toolbar", False)
      draw_label = "✕ วาด" if is_toolbar else "✏️ วาด"
      if st.button(
          draw_label,
          key="btn_m_draw",
          use_container_width=True,
          type="secondary",
      ):
        st.session_state["show_draw_toolbar"] = not is_toolbar
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # วาดกราฟแท่งเทียน
    if chart_renderer:
      chart_renderer()
    else:
      st.info("กำลังโหลดกราฟ...")

  # =========================================================================
  # แท็บ 2: รายการเฝ้าดู (Watchlist Tab)
  # =========================================================================
  with tab_watch:
    if watchlist_renderer:
      watchlist_renderer()
    else:
      st.info("กำลังโหลดรายการเหรียญ...")

  # =========================================================================
  # แท็บ 3: ภาพรวม & เทคนิค (Overview & Technical Tab)
  # =========================================================================
  with tab_info:
    render_right_panel(
        df=df, meta=meta, is_thb_mode=is_thb_mode, fx_rate=fx_rate
    )