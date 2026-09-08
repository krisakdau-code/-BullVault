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


