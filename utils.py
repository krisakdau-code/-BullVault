def to_tv(symbol: str) -> str:
    s = symbol.upper().strip()
    if s.startswith("THB_"):
        return f"{s[4:]}_THB"
    return s

def to_ticker(symbol: str) -> str:
    s = symbol.upper().strip()
    if s.endswith("_THB"):
        return f"THB_{s[:-4]}"
    return s

def smart_fmt(price: float) -> str:
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
    p = float(price or 0)
    if p >= 1000:
        return 2
    if p >= 1:
        return 4
    if p >= 0.01:
        return 6
    return 10

def _has_data(*args, **kwargs):
    return False

def fmt_price(val):
    try:
        return f"{float(val):,.2f}"
    except (TypeError, ValueError):
        return "0.00"

def fmt_chg(val):
    try:
        f = float(val)
        return f"+{f:,.2f}%" if f >= 0 else f"{f:,.2f}%"
    except (TypeError, ValueError):
        return "+0.00%"

def fmt_vol(val):
    try:
        return f"{float(val):,.0f}"
    except (TypeError, ValueError):
        return "0"