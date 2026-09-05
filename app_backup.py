# app.py
import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data import fetch_ohlcv, fetch_binance_ohlcv
from diamond import diamond_armor

st.set_page_config(page_title="Trading Chart", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  .block-container {padding-top: 1rem; padding-bottom: 0rem; max-width: 99%;}
</style>
""", unsafe_allow_html=True)

# ----------------- 1. ระบบรายชื่อเหรียญ (Bitkub 115+ เหรียญ & Binance) -----------------
ALL_BITKUB_COINS = [
    "BTC_THB", "ETH_THB", "USDT_THB", "XRP_THB", "DOGE_THB", "SOL_THB", "ADA_THB", "KUB_THB",
    "BNB_THB", "NEAR_THB", "OP_THB", "ARB_THB", "SUI_THB", "PEPE_THB", "SHIB_THB", "AVAX_THB",
    "LINK_THB", "DOT_THB", "GALA_THB", "SAND_THB", "MANA_THB", "FTM_THB", "ATOM_THB", "AAVE_THB",
    "CRV_THB", "UNI_THB", "LTC_THB", "BCH_THB", "ETC_THB", "XLM_THB", "IOST_THB", "ZIL_THB",
    "BAT_THB", "CHZ_THB", "ENJ_THB", "THETA_THB", "AXS_THB", "ALGO_THB", "DYDX_THB", "APE_THB",
    "WLD_THB", "TIA_THB", "SEI_THB", "INJ_THB", "RENDER_THB", "FET_THB", "GRT_THB", "LDO_THB",
    "APT_THB", "JUP_THB", "PYTH_THB", "BLUR_THB", "IMX_THB", "SNX_THB", "COMP_THB", "MKR_THB",
    "SUSHI_THB", "1INCH_THB", "KNC_THB", "BAND_THB", "ALPHA_THB", "STX_THB", "KAVA_THB", "MINA_THB",
    "FLOW_THB", "ICP_THB", "FIL_THB", "XTZ_THB", "EOS_THB", "TRX_THB", "VET_THB", "NEO_THB",
    "QTUM_THB", "OMG_THB", "ZRX_THB", "KSM_THB", "BAL_THB", "YFI_THB", "GLM_THB", "POWR_THB",
    "CVC_THB", "ABT_THB", "CTXC_THB", "JFIN_THB", "SIX_THB", "GT_THB", "SAFE_THB", "STRK_THB",
    "ENA_THB", "ONDO_THB", "NOT_THB", "TON_THB", "PENDLE_THB", "W_THB", "ETHFI_THB", "BB_THB",
    "IO_THB", "ZK_THB", "LISTA_THB", "ZRO_THB", "BANANA_THB", "POL_THB", "HMSTR_THB", "CATI_THB",
    "EIGEN_THB", "NEIRO_THB", "TURBO_THB", "ME_THB", "MOVE_THB", "FLOKI_THB", "BONK_THB"
]

BINANCE_HOSTS = [
    "https://data-api.binance.vision",
    "https://api.binance.com",
    "https://api-gcp.binance.com",
]

_BAD_SUFFIX = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")
_STABLE = {"USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT", "USDPUSDT", "DAIUSDT", "EURUSDT"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


@st.cache_data(ttl=1800, show_spinner=False)
def bitkub_symbols() -> list[str]:
    found = set()
    for url in ["https://api.bitkub.com/api/v3/market/symbols", "https://api.bitkub.com/api/market/symbols"]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8).json()
            items = r.get("result", r) if isinstance(r, dict) else r
            if isinstance(items, list):
                for item in items:
                    sym = item.get("symbol", "").upper()
                    if sym.startswith("THB_"):
                        found.add(f"{sym[4:]}_THB")
                    elif sym.endswith("_THB"):
                        found.add(sym)
                    elif "_" in sym:
                        b, q = sym.split("_")
                        found.add(f"{b}_{q}" if q == "THB" else f"{q}_{b}")
        except Exception:
            pass

    combined = list(found.union(set(ALL_BITKUB_COINS)))
    top = ["BTC_THB", "ETH_THB", "USDT_THB", "XRP_THB", "DOGE_THB", "SOL_THB", "ADA_THB", "KUB_THB", "BNB_THB"]
    top_p = [c for c in top if c in combined]
    rest = sorted([c for c in combined if c not in top_p])
    return top_p + rest


@st.cache_data(ttl=1800, show_spinner=False)
def binance_symbols(quote: str = "USDT") -> list[str]:
    for host in BINANCE_HOSTS:
        try:
            r = requests.get(f"{host}/api/v3/exchangeInfo", headers=HEADERS, timeout=8).json()
            if "symbols" in r:
                valid = set()
                for s in r["symbols"]:
                    if s.get("status") == "TRADING" and s.get("quoteAsset") == quote:
                        sym = s["symbol"]
                        if not sym.endswith(_BAD_SUFFIX) and sym not in _STABLE:
                            valid.add(sym)

                tickers = requests.get(f"{host}/api/v3/ticker/24hr", headers=HEADERS, timeout=8).json()
                if isinstance(tickers, list):
                    vol = {t["symbol"]: float(t.get("quoteVolume", 0) or 0) for t in tickers if t.get("symbol") in valid}
                    return sorted(valid, key=lambda x: vol.get(x, 0), reverse=True)
                return sorted(valid)
        except Exception:
            continue
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]


def get_symbols(exchange: str) -> list[str]:
    return bitkub_symbols() if exchange == "Bitkub" else binance_symbols()


# ----------------- 2. ระบบวาดกราฟ Plotly -----------------
def build_plotly_chart(
    df: pd.DataFrame,
    symbol: str,
    stats: dict,
    tf: str = "1h",
    show_ema=True,
    show_vol=True,
    show_signals=True,
    show_labels=True,
    label_size=9,
):
    df = df.sort_values("time").drop_duplicates(subset=["time"]).reset_index(drop=True).copy()

    if show_vol:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.8, 0.2]
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # 1. แท่งเทียน Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol,
            increasing_line_color="#089981",
            increasing_fillcolor="#089981",
            decreasing_line_color="#f23645",
            decreasing_fillcolor="#f23645",
        ),
        row=1, col=1
    )

    # 2. เส้น EMA 7/13/45
    if show_ema:
        ema_configs = [
            ("ema_f", "EMA 7", "#2962ff", 1.5),
            ("ema_s", "EMA 13", "#ff9800", 1.5),
            ("ema_t", "EMA 45", "#9c27b0", 1.5),
        ]
        for col, label, color, width in ema_configs:
            if col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["time"],
                        y=df[col],
                        mode="lines",
                        name=label,
                        line=dict(color=color, width=width),
                        hoverinfo="skip"
                    ),
                    row=1, col=1
                )

    # 3. สัญญาณเทรด BUY, SELL ALL, TP, Early
    if show_signals:
        for _, row in df.iterrows():
            t = row["time"]
            if row.get("buy"):
                if show_labels:
                    fig.add_annotation(
                        x=t,
                        y=row["low"],
                        text="BUY",
                        showarrow=False,
                        yanchor="top",
                        font=dict(size=label_size, color="#FFFFFF", family="Arial Black"),
                        bgcolor="#26A69A",
                        borderpad=2,
                        row=1, col=1
                    )
                # วาด marker ลูกศรเดิม (ถ้าเดิมมี marker ลูกศรอยู่ด้วย ให้คงลูกศรไว้ตามเดิม)
                fig.add_annotation(
                    x=t,
                    y=row["low"],
                    text="",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    arrowcolor="#26A69A",
                    ay=25,
                    row=1, col=1
                )
            elif row.get("sell"):

                if show_labels:
                    fig.add_annotation(
                        x=t,
                        y=row["high"],
                        text="SELL ALL",
                        showarrow=False,
                        yanchor="bottom",
                        font=dict(size=label_size, color="#FFFFFF", family="Arial Black"),
                        bgcolor="#EF5350",
                        borderpad=2,
                        row=1, col=1
                    )
                # วาด marker ลูกศรเดิม

                fig.add_annotation(
                    x=t,
                    y=row["high"],
                    text="",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    arrowcolor="#EF5350",
                    ay=-25,
                    row=1, col=1
                )
            elif row.get("tp"):
                if show_labels:
                    fig.add_annotation(
                        x=t,
                        y=row["high"],
                        text="TP",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1,
                        arrowcolor="#ffb74d",
                        ay=-20,
                        bgcolor="#ffb74d",
                        font=dict(family="monospace", size=label_size, color="#000000"),
                        borderpad=2,
                        row=1, col=1
                    )
                else:
                    # ถ้าไม่แสดงป้าย ให้แสดงแค่หัวลูกศร (คงตำแหน่งเดิม)
                    fig.add_annotation(
                        x=t,
                        y=row["high"],
                        text="",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1,
                        arrowcolor="#ffb74d",
                        ay=-20,
                        row=1, col=1
                    )
            elif row.get("early"):
                fig.add_annotation(
                    x=t,
                    y=row["low"],
                    text="EARLY",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    arrowcolor="#00b0ff",
                    ay=20,
                    bgcolor="#00b0ff",
                    font=dict(family="monospace", size=9, color="#FFFFFF"),
                    borderpad=2,
                    row=1, col=1
                )

    # 4. Volume
    if show_vol:
        colors = ["rgba(8, 153, 129, 0.6)" if r["close"] >= r["open"] else "rgba(242, 54, 69, 0.6)" for _, r in df.iterrows()]
        fig.add_trace(
            go.Bar(
                x=df["time"],
                y=df["volume"],
                name="Volume",
                marker_color=colors,
                hoverinfo="x+y"
            ),
            row=2, col=1
        )

    # 5. Panel สถิติ overlay บนกราฟ
    if stats:
        # กำหนดสี
        win_color = "#26A69A" if stats["win_rate"] >= 50 else "#EF5350"
        net_color = "#26A69A" if stats["net"] >= 0 else "#EF5350"
        hold_txt = "YES" if stats["holding"] else "NO"
        hold_color = "#26A69A" if stats["holding"] else "#D1D4DC"
        sqz_color = "#00e5ff" if "BOOM" in stats["explosion"] else ("#e040fb" if "SQUEEZE" in stats["explosion"] else "#D1D4DC")

        stat_lines = [
            '<b><span style="color:#F0B90B">DIAMOND V11.3   DYNAMIC TP</span></b>',
            f'EXPLOSION      <span style="color:{sqz_color}">{stats["explosion"]}</span>',
            f'Win Rate       <span style="color:{win_color}">{stats["win_rate"]:.2f}%</span>',
            f'Net P/L        <span style="color:{net_color}">{stats["net"]:+.2f}%</span>',
            f'Total Profit   <span style="color:#26A69A">+{stats["profit"]:.2f}%</span>',
            f'Total Loss     <span style="color:#EF5350">-{stats["loss"]:.2f}%</span>',
            f'TP Count       <span style="color:#26A69A">{stats["tp_count"]} Times</span>',
            f'Holding        <span style="color:{hold_color}">{hold_txt}</span>',
            f'Early Bird     <span style="color:#26A69A">{"YES 🟢" if stats["early"] else "NONE"}</span>',
            f'Last Sell Hit? <span style="color:#D1D4DC">{"YES" if stats["just_sold"] else "NO"}</span>',
            f'Trailing High  <span style="color:#D1D4DC">{stats["trailing_high"]:,.2f}</span>',
            f'RSI Current    <span style="color:#F0B90B">{stats["rsi"]:.2f}</span>'
        ]
        stat_text = "<br>".join(stat_lines)

        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.01, y=0.02,
            xanchor="left", yanchor="bottom",
            align="left", showarrow=False,
            bgcolor="#0D0F14", bordercolor="#2A2E39", borderwidth=1,
            borderpad=6,
            font=dict(family="monospace", size=11, color="#D1D4DC"),
            text=stat_text
        )

    # Layout ตั้งค่ารูปแบบ TradingView Dark Theme
    fig.update_layout(
        height=750,
        margin=dict(l=10, r=60, t=10, b=10),
        plot_bgcolor="#0d1017",
        paper_bgcolor="#0d1017",
        showlegend=False,
        xaxis=dict(
            rangeslider=dict(visible=False),
            gridcolor="#1e222d",
            showgrid=True,
            linecolor="#2a2e39"
        ),
        yaxis=dict(
            side="right",
            gridcolor="#1e222d",
            showgrid=True,
            linecolor="#2a2e39"
        ),
    )

    if show_vol:
        fig.update_layout(
            yaxis2=dict(
                side="right",
                gridcolor="#1e222d",
                showgrid=False,
                linecolor="#2a2e39"
            ),
            xaxis2=dict(
                rangeslider=dict(visible=False),
                gridcolor="#1e222d",
                showgrid=True,
                linecolor="#2a2e39"
            )
        )

    return fig


# ----------------- 3. เมนูและการแสดงผล Dashboard -----------------
st.sidebar.header("⚙️ ตั้งค่า")
show_labels = st.sidebar.checkbox("แสดงป้ายข้อความ", value=True)
label_size = st.sidebar.slider("ขนาดป้าย", min_value=7, max_value=14, value=9)
show_macd = st.sidebar.checkbox("MACD", value=True)
label_types = st.sidebar.multiselect(
    "ประเภทป้ายที่แสดง",
    options=["BUY", "SELL ALL", "TP", "EARLY"],
    default=["BUY", "SELL ALL"]
)
max_labels = st.sidebar.number_input(
    "แสดงป้ายล่าสุดกี่จุด",
    min_value=10, max_value=500, value=50, step=10
)


exchange = st.sidebar.selectbox("กระดานเทรด", ["Bitkub", "Binance"])

symbols = get_symbols(exchange)
default_coin = "BTC_THB" if exchange == "Bitkub" else "BTCUSDT"
default_idx = symbols.index(default_coin) if default_coin in symbols else 0
symbol = st.sidebar.selectbox("เลือกเหรียญ", symbols, index=default_idx)

tf_list = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w"]
tf = st.sidebar.selectbox("Timeframe", tf_list, index=tf_list.index("30m") if "30m" in tf_list else 0)

st.sidebar.divider()

show_ema = st.sidebar.checkbox("EMA 7/13/45", value=True)
show_sig = st.sidebar.checkbox("Signals", value=True)
show_vol = st.sidebar.checkbox("Volume", value=True)

# ดึงประวัติยาวสูงสุด 5,000 แท่ง
with st.spinner(f"กำลังดึงข้อมูลประวัติย้อนหลัง {symbol} ({tf})..."):
    if exchange == "Bitkub":
        df = fetch_ohlcv(symbol, tf, bars=5000)
    else:
        df = fetch_binance_ohlcv(symbol, tf, bars=5000)

if df.empty or len(df) < 20:
    st.warning(f"⚠️ ไม่มีข้อมูลแท่งเทียนสำหรับ {symbol} ({tf})")
    st.stop()

# คำนวณสัญญาณ Diamond Armor
df, stats = diamond_armor(df)

win_rate_bg = "#2962ff" if stats["win_rate"] >= 50 else "#37474f"
net_bg = "#2e7d32" if stats["net"] >= 0 else "#c62828"
hold_bg = "#00c853" if stats["holding"] else "#455a64"
hold_txt = "YES" if stats["holding"] else "NO"
sqz_color = "#00e5ff" if "BOOM" in stats["explosion"] else ("#e040fb" if "SQUEEZE" in stats["explosion"] else "#b0bec5")

# แสดงกราฟ TradingView เต็มความกว้าง
fig = build_plotly_chart(
    df, symbol, stats, tf,
    show_ema=show_ema,
    show_vol=show_vol,
    show_signals=show_sig,
    show_labels=show_labels,
    label_size=label_size
)
st.plotly_chart(fig, use_container_width=True)
try:
    _last = pd.to_datetime(df.index[-1])
    st.caption(f"แท่งเทียน: {len(df)} แท่ง | อัปเดตล่าสุด: {_last.strftime('%d/%m/%Y %H:%M')}")
except:
    st.caption(f"แท่งเทียน: {len(df)} แท่ง")