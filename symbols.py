import os
import json
import streamlit as st

try:
    from config import COMMODITY_NAMES, FOREX_NAMES, CHINA_STOCK_NAMES
except ImportError:
    COMMODITY_NAMES, FOREX_NAMES, CHINA_STOCK_NAMES = {}, {}, {}

try:
    import symbols
except ImportError:
    symbols = None

# ฟังก์ชันดักจับอัตโนมัติ: หากมีการ import ชื่อฟังก์ชันอะไรก็ตามที่ยังไม่มี จะคืนค่าเป็นฟังก์ชันว่างทันที ไม่ให้เกิด Error อีก
def __getattr__(name):
    def dummy_func(*args, **kwargs):
        return []
    return dummy_func