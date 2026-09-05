# utils.py

def to_tv(symbol: str) -> str:
    """THB_PEPE -> PEPE_THB (ฟอร์แมตที่ /tradingview/history ต้องการ)"""
    s = symbol.upper().strip()
    if s.startswith("THB_"):
        return f"{s[4:]}_THB"
    return s


def to_ticker(symbol: str) -> str:
    """PEPE_THB -> THB_PEPE (ฟอร์แมตที่ /api/market/* ต้องการ)"""
    s = symbol.upper().strip()
    if s.endswith("_THB"):
        return f"THB_{s[:-4]}"
    return s


def smart_fmt(price: float) -> str:
    """จัดทศนิยมอัตโนมัติตามขนาดราคา — กันเคส PEPE/SHIB กลายเป็น 0.00"""
    if price is None:
        return "-"
    p = float(price)
    if p >= 1000:
        return f"{p:,.2f}"
    if p >= 1:
        return f"{p:,.4f}"
    if p >= 0.01:
        return f"{p:,.6f}"
    txt = f"{p:.12f}".rstrip("0")
    return txt if not txt.endswith(".") else txt + "0"


def y_digits(price: float) -> int:
    """จำนวนทศนิยมสำหรับแกน Y ของกราฟ"""
    p = float(price or 0)
    if p >= 1000:
        return 2
    if p >= 1:
        return 4
    if p >= 0.01:
        return 6
    return 10