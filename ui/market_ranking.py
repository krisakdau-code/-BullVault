# ui/market_ranking.py — 24H Market Ranking Tab
import requests
import streamlit as st


@st.cache_data(ttl=15)
def fetch_all_24h_markets():
  """ดึงข้อมูล 24 ชั่วโมงของทุกสินทรัพย์ทั้ง Binance (USDT) และ Bitkub (THB)"""
  items = []

  # 1. ดึงคู่เหรียญ USDT ทั้งหมดจาก Binance
  try:
    res = requests.get(
        "https://api.binance.com/api/v3/ticker/24hr", timeout=3.5
    ).json()
    for t in res:
      sym = t.get("symbol", "")
      if sym.endswith("USDT"):
        items.append({
            "symbol": sym,
            "display_name": sym.replace("USDT", ""),
            "pair": "USDT",
            "last_price": float(t.get("lastPrice", 0)),
            "change_pct": float(t.get("priceChangePercent", 0)),
            "volume_quote": float(t.get("quoteVolume", 0)),
        })
  except Exception:
    pass

  # 2. ดึงคู่เหรียญ THB ทั้งหมดจาก Bitkub
  try:
    res_bk = requests.get(
        "https://api.bitkub.com/api/market/ticker", timeout=3.5
    ).json()
    for k, v in res_bk.items():
      if k.startswith("THB_"):
        sym_clean = k.replace("THB_", "")
        items.append({
            "symbol": f"{sym_clean}THB",
            "display_name": sym_clean,
            "pair": "THB",
            "last_price": float(v.get("last", 0)),
            "change_pct": float(v.get("percentChange", 0)),
            "volume_quote": float(v.get("baseVolume", 0))
            * float(v.get("last", 0)),
        })
  except Exception:
    pass

  return items


def render_market_ranking_tab():
  """แสดงผลแท็บจัดอันดับ 24 ชม. พร้อมตัวกรอง ปริมาณ / เพิ่มสูงสุด / ลดสูงสุด"""
  if "rank_sort_mode" not in st.session_state:
    st.session_state["rank_sort_mode"] = "vol"
  if "rank_currency_filter" not in st.session_state:
    st.session_state["rank_currency_filter"] = "all"

  # แถบปุ่มเลือกการจัดอันดับ 3 หัวข้อหลัก
  col_s1, col_s2, col_s3 = st.columns(3, gap="small")
  with col_s1:
    if st.button(
        "ปริมาณ 24 ชม.",
        type=(
            "primary"
            if st.session_state["rank_sort_mode"] == "vol"
            else "secondary"
        ),
        use_container_width=True,
    ):
      st.session_state["rank_sort_mode"] = "vol"
      st.rerun()
  with col_s2:
    if st.button(
        "% เพิ่มสูงสุด",
        type=(
            "primary"
            if st.session_state["rank_sort_mode"] == "gain"
            else "secondary"
        ),
        use_container_width=True,
    ):
      st.session_state["rank_sort_mode"] = "gain"
      st.rerun()
  with col_s3:
    if st.button(
        "% ลดสูงสุด",
        type=(
            "primary"
            if st.session_state["rank_sort_mode"] == "loss"
            else "secondary"
        ),
        use_container_width=True,
    ):
      st.session_state["rank_sort_mode"] = "loss"
      st.rerun()

  # แถบปุ่มกรองสกุลเงิน (ทั้งหมด / THB / USDT)
  col_f1, col_f2, col_f3 = st.columns([1, 1, 1], gap="small")
  with col_f1:
    if st.button(
        "ทั้งหมด",
        type=(
            "primary"
            if st.session_state["rank_currency_filter"] == "all"
            else "secondary"
        ),
        use_container_width=True,
    ):
      st.session_state["rank_currency_filter"] = "all"
      st.rerun()
  with col_f2:
    if st.button(
        "THB",
        type=(
            "primary"
            if st.session_state["rank_currency_filter"] == "THB"
            else "secondary"
        ),
        use_container_width=True,
    ):
      st.session_state["rank_currency_filter"] = "THB"
      st.rerun()
  with col_f3:
    if st.button(
        "USDT",
        type=(
            "primary"
            if st.session_state["rank_currency_filter"] == "USDT"
            else "secondary"
        ),
        use_container_width=True,
    ):
      st.session_state["rank_currency_filter"] = "USDT"
      st.rerun()

  # ดึงข้อมูลและคัดกรอง
  raw_data = fetch_all_24h_markets()
  curr = st.session_state["rank_currency_filter"]
  if curr != "all":
    filtered_data = [x for x in raw_data if x["pair"] == curr]
  else:
    filtered_data = raw_data

  # จัดเรียงลำดับตามตัวเลือก
  sort_mode = st.session_state["rank_sort_mode"]
  if sort_mode == "vol":
    sorted_data = sorted(
        filtered_data, key=lambda x: x["volume_quote"], reverse=True
    )
  elif sort_mode == "gain":
    sorted_data = sorted(
        filtered_data, key=lambda x: x["change_pct"], reverse=True
    )
  elif sort_mode == "loss":
    sorted_data = sorted(filtered_data, key=lambda x: x["change_pct"])

  # หัวตาราง
  st.markdown(
      """
    <div style="display:flex; justify-content:space-between; font-size:11px; color:#8b949e; padding:6px 4px 2px 4px; border-bottom:1px solid #1e2433;">
        <span style="flex:1.2;">สินทรัพย์</span>
        <span style="flex:1; text-align:right;">ราคาล่าสุด</span>
        <span style="flex:1; text-align:right;">24 ชม.</span>
    </div>
    """,
      unsafe_allow_html=True,
  )

  # แสดงรายการ 50 อันดับแรก
  st.markdown(
      "<div style='max-height: 58vh; overflow-y: auto; padding-right: 2px;'>",
      unsafe_allow_html=True,
  )
  for item in sorted_data[:50]:
    sym = item["symbol"]
    chg = item["change_pct"]
    price = item["last_price"]
    chg_color = "#089981" if chg >= 0 else "#f23645"
    sign = "+" if chg > 0 else ""

    # ปรับรูปแบบทศนิยมราคา
    if price >= 100:
      p_str = f"{price:,.2f}"
    elif price >= 1:
      p_str = f"{price:,.4f}"
    else:
      p_str = f"{price:,.6f}"

    c_row1, c_row2 = st.columns([1.2, 1.8], gap="small")
    with c_row1:
      # กดชื่อเหรียญแล้วสลับหน้ากราฟทันที
      if st.button(
          f"🪙 {item['display_name']}",
          key=f"rk_btn_{sym}",
          use_container_width=True,
      ):
        st.session_state["current_symbol"] = sym
        st.session_state.pop("selected_symbol", None)
        for t in st.session_state.get("chart_tabs", []):
          if t.get("id") == st.session_state.get("active_tab_id"):
            t["symbol"] = sym
        st.rerun()

    with c_row2:
      st.markdown(
          f"""
            <div style="display:flex; justify-content:space-between; align-items:center; height:32px; font-size:12px; font-weight:600;">
                <span style="color:#d1d4dc;">{p_str}</span>
                <span style="color:{chg_color}; background:rgba({ '8,153,129' if chg >= 0 else '242,54,69' }, 0.15); padding:2px 6px; border-radius:4px;">
                    {sign}{chg:.2f}%
                </span>
            </div>
            """,
          unsafe_allow_html=True,
      )

  st.markdown("</div>", unsafe_allow_html=True)