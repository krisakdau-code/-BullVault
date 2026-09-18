"""จัดการกลุ่มสีของเหรียญใน Watchlist — บันทึกลงดิสก์ถาวร ป้องกัน State หลุดหาย"""
import json
import os
import streamlit as st

CW_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".color_watchlists.json")

# นิยามกลุ่มสี (Single Source of Truth)
COLOR_TAGS = {
    "red":    {"dot": "🔴", "label": "แดง",    "hex": "#f6465d"},
    "green":  {"dot": "🟢", "label": "เขียว",   "hex": "#0ecb81"},
    "orange": {"dot": "🟠", "label": "ส้ม",     "hex": "#f0b90b"},
    "blue":   {"dot": "🔵", "label": "น้ำเงิน", "hex": "#2962ff"},
    "white":  {"dot": "⚪", "label": "ขาว",     "hex": "#eaecef"},
}
COLOR_KEYS = list(COLOR_TAGS.keys())


def norm_sym(s) -> str:
    """แปลงชื่อเหรียญให้เป็นตัวพิมพ์ใหญ่และตัดอักขระพิเศษออกทั้งหมด"""
    return "".join(ch for ch in str(s) if ch.isalnum()).upper()


def load_color_watchlists() -> dict:
    """โหลดข้อมูลกลุ่มสีจากไฟล์ JSON"""
    try:
        with open(CW_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {k: [norm_sym(x) for x in raw.get(k, []) if norm_sym(x)] for k in COLOR_KEYS}
    except Exception:
        return {k: [] for k in COLOR_KEYS}


def save_color_watchlists(cw: dict) -> None:
    """บันทึกข้อมูลกลุ่มสีลงไฟล์ JSON"""
    try:
        with open(CW_PATH, "w", encoding="utf-8") as f:
            json.dump(cw, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.toast(f"บันทึกสีไม่สำเร็จ: {e}", icon="⚠️")


def ensure_color_state() -> dict:
    """ดึงค่าสีเข้า st.session_state อย่างปลอดภัย"""
    if "color_watchlists" not in st.session_state:
        st.session_state["color_watchlists"] = load_color_watchlists()
    return st.session_state["color_watchlists"]


def assign_color(sym, color) -> None:
    """ตั้งสีให้เหรียญ (ถ้า color=None จะเป็นการปลดออกจากทุกกลุ่มสี)"""
    cw = ensure_color_state()
    s = norm_sym(sym)
    if not s:
        return
    for k in COLOR_KEYS:
        cw[k] = [x for x in cw[k] if x != s]
    if color in COLOR_KEYS:
        cw[color].append(s)
    st.session_state["color_watchlists"] = cw
    save_color_watchlists(cw)


def get_sym_color_key(sym):
    """คืนค่า key สีของเหรียญ (เช่น 'red') หรือ None หากไม่มีสี"""
    cw = ensure_color_state()
    s = norm_sym(sym)
    for k in COLOR_KEYS:
        if s in cw.get(k, []):
            return k
    return None


def get_sym_color_dot(sym) -> str:
    """คืนค่า emoji จุดสี (🔴, 🟢, ฯลฯ) หรือข้อความว่างถ้าไม่มีสี"""
    k = get_sym_color_key(sym)
    return COLOR_TAGS[k]["dot"] if k else ""