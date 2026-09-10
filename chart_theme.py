# chart_theme.py — รวมการตั้งค่ากราฟิก สี เส้น และขนาดทั้งหมด
# 1. ธีมและเส้นขอบ TradingView Pro
CHART_BG        = "#000000"          # สีพื้นหลัง
TEXT_COLOR      = "#787B86"          # สีตัวเลขแกนราคา/เวลา
GRID_COLOR      = "#131722"          # สีเส้นตาราง Grid
BORDER_COLOR    = "#2A2E39"          # สีเส้นกรอบแบ่งช่องกราฟ
CROSSHAIR_COLOR = "rgba(255, 255, 255, 0.25)" # สีเส้นกากบาทไข่ปลา

# 2. แท่งเทียนกราฟหลัก
CANDLE_UP        = "#089981"         # เขียว TradingView
CANDLE_DOWN      = "#F23645"         # แดง TradingView
PRICE_SCALE_TOP  = 0.08              # เว้นขอบบน 8%
PRICE_SCALE_BTM  = 0.25              # เว้นขอบล่าง 25% (ยกแท่งเทียนลอยพ้น ไม่ทับ Volume)

# 3. วอลุ่มกราฟหลัก (Volume Overlay ล่างสุด)
SHOW_VOLUME      = True
VOL_UP           = "rgba(8, 153, 129, 0.45)"
VOL_DOWN         = "rgba(242, 54, 69, 0.45)"
VOL_TOP_MARGIN   = 0.80              # ตรึง Volume ให้อยู่เฉพาะล่างสุด 20%

# 4. เส้น EMA กราฟหลัก
EMA_FAST_COLOR   = "#2962FF"         # เส้นเร็ว (น้ำเงิน)
EMA_SLOW_COLOR   = "#FF6D00"         # เส้นช้า (ส้ม)
EMA_TREND_COLOR  = "#FFFFFF"         # เส้นเทรนด์ (ขาวประ)

# 5. กราฟ RSI
RSI_TITLE_COLOR  = "rgba(41, 98, 255, 0.8)"
RSI_LINE_COLOR   = "#CC2093"
RSI_LINE_WIDTH   = 2
RSI_LEVEL_70     = "rgba(242, 54, 69, 0.5)"
RSI_LEVEL_50     = "rgba(120, 123, 134, 0.25)"
RSI_LEVEL_30     = "rgba(8, 153, 129, 0.5)"
RSI_TOP_MARGIN   = 0.05
RSI_BTM_MARGIN   = 0.05

# 6. กราฟ MACD
MACD_TITLE_COLOR = "rgba(0, 230, 118, 0.8)"
MACD_LINE_COLOR  = "#00E676"
MACD_LINE_WIDTH  = 2
MACD_SIG_COLOR   = "#FFD700"
MACD_SIG_WIDTH   = 2
MACD_HIST_UP     = "rgba(8, 153, 129, 0.70)"
MACD_HIST_DOWN   = "rgba(242, 54, 69, 0.70)"
MACD_TOP_MARGIN  = 0.08
MACD_BTM_MARGIN  = 0.08