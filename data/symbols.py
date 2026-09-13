import json
import os

def _load_json(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(path):
        path = os.path.join("data", filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return list(data.keys())
                elif isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def get_full_binance_symbols():
    return _load_json("binance_crypto.json")

def get_full_bitkub_symbols():
    return _load_json("bitkub_crypto.json")

def get_full_binance_th_symbols():
    return _load_json("binance_th_crypto.json")

def get_full_okx_symbols():
    return _load_json("okx_crypto.json")

def get_full_bybit_symbols():
    return _load_json("bybit_crypto.json")

def get_full_gate_symbols():
    return _load_json("gateio_crypto.json")

def get_full_mexc_symbols():
    return _load_json("mexc_crypto.json")

def get_full_kucoin_symbols():
    return _load_json("kucoin_crypto.json")

def get_full_china_stocks():
    return _load_json("china_stocks.json")

def get_full_commodities():
    return _load_json("commodities.json")

def get_full_forex():
    return _load_json("forex.json")

def get_full_sp500_symbols():
    return _load_json("us_stocks.json")

def get_full_vietnam_symbols():
    return _load_json("vietnam_stocks.json")