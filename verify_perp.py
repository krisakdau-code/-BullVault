from data.candles import fetch_daily_bars, to_tv_symbol
from data.fetchers import get_52w_range, get_ticker_24h
from ui.right_panel import calc_calendar_perf, fmt_pct, fmt_price

SYM = "PERPTHB"
print("==================================================")
print("TV Symbol Mapping :", to_tv_symbol(SYM), "(ต้องได้ PERP_THB)")

t = get_ticker_24h(SYM)
if t:
  print(f"Last Price        : {fmt_price(t['last'])} | คาดหวัง: 0.7298")
  print(f"24h Change %      : {fmt_pct(t['change_pct'])} | คาดหวัง: -2.68%")
  print(
      f"Bid / Ask         : {fmt_price(t['bid'])} / {fmt_price(t['ask'])} |"
      " คาดหวัง: 0.6706 / 0.7285"
  )
  print(
      f"Day Range         : {fmt_price(t['low_24h'])} -"
      f" {fmt_price(t['high_24h'])} | คาดหวัง: 0.6702 - 0.7300"
  )
  print(f"24h Volume        : {t['base_volume']:,.0f} | คาดหวัง: ~88,380")
else:
  print("❌ ดึง Ticker ไม่สำเร็จ")

bars = fetch_daily_bars(SYM, 385)
print(f"Daily Bars Count  : {len(bars)} แท่ง")

r = get_52w_range(SYM)
print(
    f"52-Week Range     : {fmt_price(r['low'])} - {fmt_price(r['high'])} |"
    " คาดหวัง: 0.2508 - 9.9600"
)

perfs = calc_calendar_perf(bars)
print("--------------------------------------------------")
print("Performance Statistics (Calendar Anchored):")
for k, v in perfs.items():
  print(f"  {k:<22}: {fmt_pct(v)}")
print("==================================================")