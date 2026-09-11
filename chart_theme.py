# chart_theme.py — Theme, Colors & Drawing Defaults
CHART_BG        = "#000000"
TEXT_COLOR      = "#787B86"
GRID_COLOR      = "#131722"
BORDER_COLOR    = "#2A2E39"
CROSSHAIR_COLOR = "rgba(255, 255, 255, 0.25)"

# แท่งเทียน
CANDLE_UP        = "#089981"
CANDLE_DOWN      = "#F23645"
PRICE_SCALE_TOP  = 0.08
PRICE_SCALE_BTM  = 0.22

# วอลุ่มล่างสุด
SHOW_VOLUME      = True
VOL_UP           = "rgba(8, 153, 129, 0.45)"
VOL_DOWN         = "rgba(242, 54, 69, 0.45)"
VOL_TOP_MARGIN   = 0.80

# เส้น EMA
EMA_FAST_COLOR   = "#2962FF"
EMA_SLOW_COLOR   = "#FF6D00"
EMA_TREND_COLOR  = "#FFFFFF"

# RSI มาตรฐาน
RSI_LINE_COLOR   = "#2962FF"
RSI_MA_COLOR     = "#FF6D00"
RSI_TITLE_COLOR  = "rgba(41, 98, 255, 0.8)"
RSI_TOP_MARGIN   = 0.05
RSI_BTM_MARGIN   = 0.05

# MACD มาตรฐาน (Histogram 4 สี)
MACD_HIST_H0     = "#00E676"  # เขียวสว่าง (แรงซื้อเพิ่ม)
MACD_HIST_H1     = "#00897B"  # เขียวหม่น (แรงซื้อลด)
MACD_HIST_H2     = "#FF5252"  # แดงสว่าง (แรงขายเพิ่ม)
MACD_HIST_H3     = "#B71C1C"  # แดงหม่น (แรงขายลด)
MACD_LINE_COLOR  = "#00E676"
MACD_SIG_COLOR   = "#FFD700"
MACD_ZERO_COLOR  = "#787B86"
MACD_TITLE_COLOR = "rgba(0, 230, 118, 0.8)"
MACD_TOP_MARGIN  = 0.08
MACD_BTM_MARGIN  = 0.08