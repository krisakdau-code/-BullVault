import os
import time
import json
import requests
import pandas as pd
import streamlit as st
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ──────────────────────────── NETWORK SESSION ────────────────────────────
BITKUB_API_KEY = st.secrets.get("BITKUB_API_KEY", "")
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update(BROWSER_HEADERS)
retry_strategy = Retry(
    total=3,
    backoff_factor=0.8,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
http_adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=25, pool_maxsize=25)
HTTP_SESSION.mount("https://", http_adapter)
HTTP_SESSION.mount("http://", http_adapter)

THREAD_POOL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10)

