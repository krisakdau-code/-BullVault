# drawing_chart.py — Multi-Pane Anchored Drawing Terminal (Floating Header, Top-Left Legend & Price Lines Support)
import json
import streamlit.components.v1 as components

def render_drawing_chart(
    charts_config: list, 
    height: int = None, 
    key: str = "draw_chart",
    show_toolbar: bool = True
):
    if not charts_config:
        return
    import streamlit as st
    from data.fetchers import resolve_market_info
    curr_sym = st.session_state.get("current_symbol", "BTCUSDT")
    meta = resolve_market_info(curr_sym)
    display_title = meta.get("display_name", curr_sym)
    exchange_name = meta.get("exchange", "MARKET")
    # คำนวณความสูง: ไม่มีแถบ Header 26px มาแย่งพื้นที่อีกต่อไป
    if len(charts_config) == 1:
        charts_config[0]["chart"]["height"] = 650
        real_total_h = 660
    elif len(charts_config) == 2:
        charts_config[0]["chart"]["height"] = 540
        real_total_h = 540 + int(charts_config[1].get("chart", {}).get("height", 140)) + 10
    else:
        real_total_h = 0
        for c in charts_config:
            real_total_h += int(c.get("chart", {}).get("height", 130))
        _n_sub = max(0, len(charts_config) - 1)
        real_total_h += (_n_sub * 6) + 20+250

    chart_json = json.dumps(charts_config)
    toolbar_display = "flex" if show_toolbar else "none"

    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Trading Terminal</title>
        <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            html, body {{
                width: 100%;
                height: 100%;
                background-color: #000000;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            #container {{
                position: relative;
                width: 100%;
                display: flex;
                flex-direction: column;
                background: #000000;
            }}
            #main-pane-container {{
                position: relative;
                width: 100%;
            }}
            #chart-main {{
                width: 100%;
                z-index: 1;
            }}
            #drawing-canvas {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 5;
                pointer-events: none;
            }}

            /* ─── 1. ป้ายสถานะราคาและเหรียญมุมซ้ายบน (วงสีเขียว) ─── */
            .chart-legend {{
                position: absolute;
                top: 8px;
                left: 52px;
                z-index: 12;
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 12px;
                background: rgba(19, 23, 34, 0.75);
                backdrop-filter: blur(6px);
                border: 1px solid rgba(42, 46, 57, 0.8);
                padding: 3px 10px;
                border-radius: 6px;
                pointer-events: none;
                user-select: none;
            }}
            .legend-symbol {{ font-weight: 800; color: #ffffff; letter-spacing: 0.5px; }}
            .legend-badge {{ font-size: 10px; background: rgba(0, 255, 163, 0.15); color: #00FFA3; padding: 1px 5px; border-radius: 3px; font-weight: 700; }}
            .legend-price {{ font-weight: 800; font-family: 'Roboto Mono', monospace; font-size: 13px; }}
            .legend-change {{ font-weight: 700; font-size: 11px; }}
            .legend-ohlc {{ color: #787b86; font-size: 11px; margin-left: 6px; font-family: 'Roboto Mono', monospace; }}

            /* ─── 2. ปุ่มควบคุมลอยมุมขวาบนของแต่ละกราฟ (วงสีแดง) ─── */
            .pane-box {{
                display: flex;
                flex-direction: column;
                width: 100%;
                overflow: hidden;
                position: relative;
            }}
            .pane-header {{
                position: absolute;
                top: 6px;
                right: 62px;
                height: 24px;
                background: rgba(19, 23, 34, 0.7);
                backdrop-filter: blur(4px);
                border: 1px solid rgba(42, 46, 57, 0.6);
                border-radius: 5px;
                display: flex;
                align-items: center;
                padding: 0 4px;
                z-index: 20;
                user-select: none;
                opacity: 0.6;
                transition: opacity 0.2s ease;
            }}
            .pane-header:hover {{
                opacity: 1;
                border-color: #00FFA3;
                box-shadow: 0 0 8px rgba(0, 255, 163, 0.2);
            }}
            .pane-title {{ display: none; }}
            .pane-actions {{ display: flex; gap: 3px; }}
            .pane-btn {{
                background: transparent;
                border: none;
                color: #787b86;
                font-size: 12px;
                line-height: 1;
                cursor: pointer;
                padding: 3px 5px;
                border-radius: 3px;
                transition: all 0.15s ease;
            }}
            .pane-btn:hover {{ background: rgba(0, 255, 163, 0.15); color: #00FFA3; }}
            .pane-btn.off {{ color: #3a3f4b; }}
            .pane-btn-x:hover {{ background: rgba(239, 83, 80, 0.2); color: #ef5350; }}

            /* ─── 3. เส้นคั่นยืดหด (Splitter Bar) ─── */
            .splitter-bar {{
                height: 5px;
                min-height: 5px;
                flex: 0 0 5px;
                background: #141722;
                cursor: ns-resize;
                position: relative;
                z-index: 25;
                transition: background 0.15s;
            }}
            .splitter-bar:hover, .splitter-bar.dragging {{
                background: #00FFA3;
                box-shadow: 0 0 10px rgba(0, 255, 163, 0.8);
            }}
            .pane-box .chart-view {{
                flex: 1 1 auto;
                min-height: 0;
                width: 100%;
                height: 100%;
            }}

            /* แถบเครื่องมือ TradingView ชิดขอบซ้าย */
            /* แถบเครื่องมือ TradingView ขอบซ้าย */
            /* แถบเครื่องมือ TradingView ขอบซ้าย */
            .draw-toolbar {{
                position: absolute;
                top: 12px;
                left: 10px;
                z-index: 25;
                display: {toolbar_display} !important;
                flex-direction: column;
                gap: 3px;
                background: rgba(20, 24, 35, 0.45) !important;
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 6px;
                padding: 4px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
                user-select: none;
            }}
            
            .drag-handle {{
                width: 100%; height: 14px; display: flex; align-items: center; justify-content: center;
                cursor: grab; color: #787b86; font-size: 13px; font-weight: bold; letter-spacing: 2px;
                user-select: none; margin-bottom: 2px; border-radius: 3px; transition: background 0.15s ease;
            }}
            .drag-handle:hover {{ background: #2a2e39; color: #00FFA3; }}
            .drag-handle:active {{ cursor: grabbing; }}
            .tool-btn {{
                width: 32px; height: 32px; background: transparent; border: 1px solid transparent;
                border-radius: 4px; color: #b2b5be; font-size: 15px; display: flex; align-items: center;
                justify-content: center; cursor: pointer; transition: all 0.15s ease;
            }}
            .tool-btn:hover {{ background: #2a2e39; color: #ffffff; }}
            .tool-btn.active {{
                background: rgba(0, 255, 163, 0.15); border-color: #00FFA3; color: #00FFA3;
                box-shadow: 0 0 8px rgba(0, 255, 163, 0.3);
            }}
            .tool-btn.eraser-active {{
                background: #f23645 !important; border-color: #f23645 !important;
                color: #ffffff !important; box-shadow: 0 0 8px rgba(242,54,69,0.5) !important;
            }}
            .tool-btn.danger-active {{
                background: rgba(242, 54, 69, 0.3) !important; color: #f23645 !important;
                border-color: #f23645 !important; box-shadow: 0 0 8px rgba(242, 54, 69, 0.5) !important;
            }}
            .tool-btn.danger-btn:hover {{ background: rgba(242, 54, 69, 0.25); color: #f23645; }}
            .tool-sep {{ width: 22px; height: 1px; background: #2a2e39; margin: 2px auto; }}
            .sub-pane {{ width: 100%; background: #000000; }}
            #text-overlay-box {{
                display: none; position: absolute; z-index: 30; background: #1e222d;
                border: 1px solid #00FFA3; border-radius: 4px; padding: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            }}
            #text-overlay-box input {{
                background: transparent; border: none; outline: none; color: #ffffff;
                font-size: 13px; width: 140px; font-family: inherit;
            }}
            /* สไตล์ปุ่มซื้อ-ขายแบบ Floating TradingView */
            .quick-trade-box {{
                display: flex;
                gap: 4px;
                margin-left: 10px;
                pointer-events: auto;
            }}
            .qt-btn {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid transparent;
                cursor: pointer;
                min-width: 65px;
                transition: all 0.15s ease;
            }}
            .qt-btn .qt-side {{
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }}
            .qt-btn .qt-val {{
                font-size: 11px;
                font-weight: 700;
                font-family: 'Roboto Mono', monospace;
            }}
            .qt-sell {{
                background: rgba(242, 54, 69, 0.2);
                border-color: rgba(242, 54, 69, 0.4);
                color: #f23645;
            }}
            .qt-sell:hover {{
                background: #f23645;
                color: #ffffff;
                box-shadow: 0 0 8px rgba(242, 54, 69, 0.4);
            }}
            .qt-buy {{
                background: rgba(0, 255, 163, 0.18);
                border-color: rgba(0, 255, 163, 0.4);
                color: #00FFA3;
            }}
            .qt-buy:hover {{
                background: #00FFA3;
                color: #000000;
                box-shadow: 0 0 8px rgba(0, 255, 163, 0.4);
            }}
        </style>
    </head>
    <body>
        <div id="container">
            <div id="main-pane-container">
                <div class="draw-toolbar" id="main-draw-toolbar">
                    <div class="drag-handle" id="tb-drag-handle" title="คลิกค้างเพื่อลากย้าย">⋮⋮</div>
                    <button class="tool-btn active" id="btn-cursor" title="↖ เคอร์เซอร์ / เลือกวัตถุเพื่อขยับหรือลบ (V)">↖</button>
                    <button class="tool-btn" id="btn-eraser" title="🧽 ยางลบเจาะจง / คลิกลบวัตถุทีละชิ้น (E)">🧽</button>
                    <div class="tool-sep"></div>
                    <button class="tool-btn" id="btn-trend" title="เส้นแนวโน้ม (Trendline)">╱</button>
                    <button class="tool-btn" id="btn-horz" title="เส้นแนวนอน (Horizontal Level)">―</button>
                    <button class="tool-btn" id="btn-box" title="กล่องโซน (Rectangle Zone)">▭</button>
                    <button class="tool-btn" id="btn-fib" title="ฟิโบนัชชี (Fibonacci Retracement)">📐</button>
                    <button class="tool-btn" id="btn-circle" title="วงกลมไฮไลต์ (Circle)">⭕</button>
                    <button class="tool-btn" id="btn-pen" title="ปากกาวาดอิสระ (Pen Brush)">✏️</button>
                    <button class="tool-btn" id="btn-text" title="ข้อความกำกับ (Text Note)">T</button>
                    <div class="tool-sep"></div>
                    <button class="tool-btn danger-btn" id="btn-delete-selected" title="ลบวัตถุที่เลือก (Delete Key)">🗑️</button>
                    <button class="tool-btn" id="btn-undo" title="ย้อนกลับ (Undo)">↩</button>
                    <button class="tool-btn danger-btn" id="btn-clear" title="ล้างทั้งหมด">💥</button>
                </div>

               <div class="chart-legend" id="main-chart-legend">
                    <span class="legend-symbol" id="leg-symbol">BTCUSDT</span>
                    <span class="legend-badge">Binance</span>
                    <span class="legend-price" id="leg-price">--</span>
                    <span class="legend-change" id="leg-change">--</span>
                    <span class="legend-ohlc" id="leg-ohlc"></span>

                    <!-- ปุ่ม ซื้อ-ขาย สไตล์ Quick Trading (วงสีส้ม) -->
                    <div class="quick-trade-box">
                        <button class="qt-btn qt-sell" id="btn-qt-sell" title="เปิดคำสั่งขาย (Sell)">
                            <span class="qt-side">SELL</span>
                            <span class="qt-val" id="qt-sell-val">--</span>
                        </button>
                        <button class="qt-btn qt-buy" id="btn-qt-buy" title="เปิดคำสั่งซื้อ (Buy)">
                            <span class="qt-side">BUY</span>
                            <span class="qt-val" id="qt-buy-val">--</span>
                        </button>
                    </div>
                </div>

                <div id="chart-main"></div>
                <canvas id="drawing-canvas"></canvas>
                
                <div id="text-overlay-box">
                    <input type="text" id="text-input" placeholder="พิมพ์ข้อความแล้วกด Enter..." />
                </div>
            </div>
            <div id="sub-panes"></div>
        </div>

        <script>
        (function() {{
            const config = {chart_json};
            if (!config || !Array.isArray(config) || config.length === 0) return;

            const allCharts = [];
            const mainConfig = config[0];
            const subConfigs = config.slice(1);

            const container = document.getElementById('container');
            const mainContainer = document.getElementById('chart-main');
            const mainPaneBox = document.getElementById('main-pane-container');
            const canvas = document.getElementById('drawing-canvas');
            const ctx = canvas.getContext('2d');
            const textOverlay = document.getElementById('text-overlay-box');
            const textInput = document.getElementById('text-input');
            const btnDeleteSelected = document.getElementById('btn-delete-selected');

            const initWidth = container.clientWidth || window.innerWidth;
            const mainH = mainConfig.chart?.height || 520;
            mainPaneBox.style.height = mainH + 'px';

            // 1. สร้างกราฟหลัก
            const mainChart = LightweightCharts.createChart(mainContainer, {{
                ...(mainConfig.chart || {{}}),
                width: initWidth,
                height: mainH
            }});
            allCharts.push(mainChart);

            let mainSeries = null;
            if (mainConfig.series) {{
                mainConfig.series.forEach(s => {{
                    let series = null;
                    const opts = Object.assign({{}}, s.options || {{}});
                    if (opts.priceScaleId && opts.priceScaleId !== 'left' && opts.priceScaleId !== 'right') {{
                        delete opts.priceScaleId;
                    }}
                    if (s.type === "Candlestick") {{
                        series = mainChart.addCandlestickSeries(opts);
                        if (!mainSeries) mainSeries = series;
                    }} else if (s.type === "Line") {{
                        series = mainChart.addLineSeries(opts);
                        if (!mainSeries) mainSeries = series;
                    }} else if (s.type === "Histogram") {{
                        series = mainChart.addHistogramSeries(opts);
                    }}
                    if (series && s.data) series.setData(s.data);
                    if (series && s.markers) series.setMarkers(s.markers);

                    // อัปเดตราคาป้าย Legend ตามแท่งล่าสุด
                    if (series && s.type === "Candlestick" && s.data && s.data.length > 0) {{
                        const lastBar = s.data[s.data.length - 1];
                        const prevBar = s.data.length > 1 ? s.data[s.data.length - 2] : lastBar;
                        const diff = lastBar.close - prevBar.close;
                        const pct = (diff / prevBar.close) * 100;
                        const isUp = diff >= 0;
                        const color = isUp ? '#089981' : '#F23645';

                        const pEl = document.getElementById('leg-price');
                        const cEl = document.getElementById('leg-change');
                        if (pEl) {{
                            pEl.textContent = lastBar.close.toLocaleString('en-US', {{minimumFractionDigits: 2}});
                            pEl.style.color = color;
                        }}
                        if (cEl) {{
                            cEl.textContent = (isUp ? '+' : '') + pct.toFixed(2) + '%';
                            cEl.style.color = color;
                        }}
                        
                        // ซิงก์ราคาเข้าปุ่ม SELL และ BUY
                        const sVal = document.getElementById('qt-sell-val');
                        const bVal = document.getElementById('qt-buy-val');
                        if (sVal) sVal.textContent = lastBar.close.toLocaleString('en-US', {{minimumFractionDigits: 2}});
                        if (bVal) bVal.textContent = (lastBar.close * 1.0001).toLocaleString('en-US', {{minimumFractionDigits: 2}});
                    }}
                }});
            }}

            // 2. สร้าง Sub-panes (RSI, MACD) พร้อมรองรับเส้นโซน PriceLines
            const subPanesDiv = document.getElementById('sub-panes');
            subConfigs.forEach((subConf) => {{
                const paneH = subConf.chart?.height || 120;
                const paneWrapper = document.createElement('div');
                paneWrapper.className = 'sub-pane';
                paneWrapper.style.height = paneH + 'px';
                subPanesDiv.appendChild(paneWrapper);

                const subChart = LightweightCharts.createChart(paneWrapper, {{
                    ...(subConf.chart || {{}}),
                    width: initWidth,
                    height: paneH
                }});
                allCharts.push(subChart);

                if (subConf.series) {{
                    subConf.series.forEach(s => {{
                        let series = null;
                        const opts = Object.assign({{}}, s.options || {{}});
                        if (opts.priceScaleId && opts.priceScaleId !== 'left' && opts.priceScaleId !== 'right') {{
                            delete opts.priceScaleId;
                        }}
                        if (s.type === "Line") series = subChart.addLineSeries(opts);
                        else if (s.type === "Histogram") series = subChart.addHistogramSeries(opts);
                        else if (s.type === "Candlestick") series = subChart.addCandlestickSeries(opts);
                        
                        if (series && s.data) series.setData(s.data);

                        // วาดเส้นระดับโซน (Upper/Middle/Lower Bands)
                        if (series && s.priceLines && Array.isArray(s.priceLines)) {{
                            s.priceLines.forEach(pl => {{
                                try {{ series.createPriceLine(pl); }} catch(e) {{}}
                            }});
                        }}
                    }});
                }}
            }});

            // ── ระบบ Crosshair สำหรับ Legend มุมซ้ายบน ──
            if (mainChart && mainSeries) {{
                mainChart.subscribeCrosshairMove(param => {{
                    const ohlcEl = document.getElementById('leg-ohlc');
                    if (!ohlcEl) return;
                    if (!param || !param.time || !param.seriesData.has(mainSeries)) {{
                        ohlcEl.textContent = '';
                        return;
                    }}
                    const d = param.seriesData.get(mainSeries);
                    if (d.open !== undefined) {{
                        ohlcEl.textContent = `O: ${{d.open.toFixed(2)}}  H: ${{d.high.toFixed(2)}}  L: ${{d.low.toFixed(2)}}  C: ${{d.close.toFixed(2)}}`;
                    }}
                }});
            }}

            // --- ระบบลากย้ายแถบเครื่องมืออิสระ (Draggable Toolbar) ---
            const toolbar = document.getElementById('main-draw-toolbar');
            const dragHandle = document.getElementById('tb-drag-handle');
            let isTbDragging = false;
            let tbOffsetX = 0, tbOffsetY = 0;

            dragHandle.addEventListener('mousedown', (e) => {{
                isTbDragging = true;
                tbOffsetX = e.clientX - toolbar.offsetLeft;
                tbOffsetY = e.clientY - toolbar.offsetTop;
                dragHandle.style.cursor = 'grabbing';
                e.preventDefault();
                e.stopPropagation();
            }});

            window.addEventListener('mousemove', (e) => {{
                if (!isTbDragging) return;
                let newX = e.clientX - tbOffsetX;
                let newY = e.clientY - tbOffsetY;
                const maxX = mainPaneBox.clientWidth - toolbar.offsetWidth - 6;
                const maxY = mainPaneBox.clientHeight - toolbar.offsetHeight - 6;
                newX = Math.max(6, Math.min(newX, maxX));
                newY = Math.max(6, Math.min(newY, maxY));
                toolbar.style.left = newX + 'px';
                toolbar.style.top = newY + 'px';
            }});

            window.addEventListener('mouseup', () => {{
                if (isTbDragging) {{
                    isTbDragging = false;
                    dragHandle.style.cursor = 'grab';
                }}
            }});

            // 3. ซิงค์แกนเวลาระหว่างกราฟ
            let isSyncing = false;
            allCharts.forEach((c, idx) => {{
                c.timeScale().subscribeVisibleLogicalRangeChange(range => {{
                    if (isSyncing || !range) return;
                    isSyncing = true;
                    allCharts.forEach((other, oIdx) => {{
                        if (idx !== oIdx) {{
                            try {{ other.timeScale().setVisibleLogicalRange(range); }} catch(err) {{}}
                        }}
                    }});
                    isSyncing = false;
                }});
            }});

            // 4. จัดการข้อมูล Vector Engine
            const storageKey = 'tv_vector_drawings_' + (mainConfig.chart?.watermark?.text || 'default');
            let drawings = [];
            try {{
                const saved = localStorage.getItem(storageKey);
                if (saved) drawings = JSON.parse(saved);
            }} catch (e) {{}}

            let currentTool = 'cursor';
            let selectedIdx = -1;
            let activeHandle = null;
            let isDragging = false;
            let isDrawing = false;
            let startPx = null;
            let currentPx = null;
            let penPoints = [];
            let dragOrigObj = null;

            const toolBtns = {{
                cursor: document.getElementById('btn-cursor'),
                eraser: document.getElementById('btn-eraser'),
                trend: document.getElementById('btn-trend'),
                horz: document.getElementById('btn-horz'),
                box: document.getElementById('btn-box'),
                fib: document.getElementById('btn-fib'),
                circle: document.getElementById('btn-circle'),
                pen: document.getElementById('btn-pen'),
                text: document.getElementById('btn-text')
            }};

            function setTool(tool) {{
                currentTool = tool;
                Object.keys(toolBtns).forEach(k => {{
                    if (toolBtns[k]) {{
                        toolBtns[k].classList.toggle('active', k === tool && tool !== 'eraser');
                        toolBtns[k].classList.toggle('eraser-active', k === tool && tool === 'eraser');
                    }}
                }});

                if (tool === 'cursor') {{
                    canvas.style.pointerEvents = (selectedIdx !== -1) ? 'auto' : 'none';
                    canvas.style.cursor = 'default';
                }} else if (tool === 'eraser') {{
                    canvas.style.pointerEvents = 'auto';
                    canvas.style.cursor = 'crosshair';
                    selectedIdx = -1;
                    updateSelectionUI();
                }} else {{
                    canvas.style.pointerEvents = 'auto';
                    canvas.style.cursor = 'crosshair';
                    selectedIdx = -1;
                    updateSelectionUI();
                }}
                redrawAll();
            }}

            Object.keys(toolBtns).forEach(tool => {{
                if (toolBtns[tool]) toolBtns[tool].addEventListener('click', () => setTool(tool));
            }});

            function updateSelectionUI() {{
                if (selectedIdx !== -1) {{
                    btnDeleteSelected.classList.add('danger-active');
                    btnDeleteSelected.style.opacity = '1';
                }} else {{
                    btnDeleteSelected.classList.remove('danger-active');
                    btnDeleteSelected.style.opacity = '0.7';
                }}
            }}

            function deleteSelected() {{
                if (selectedIdx >= 0 && selectedIdx < drawings.length) {{
                    drawings.splice(selectedIdx, 1);
                    selectedIdx = -1;
                    updateSelectionUI();
                    saveAndRedraw();
                }}
            }}

            btnDeleteSelected.addEventListener('click', () => {{
                if (selectedIdx >= 0 && selectedIdx < drawings.length) {{
                    deleteSelected();
                }} else {{
                    setTool('eraser');
                }}
            }});

            document.getElementById('btn-undo').addEventListener('click', () => {{
                drawings.pop();
                selectedIdx = -1;
                updateSelectionUI();
                saveAndRedraw();
            }});

            document.getElementById('btn-clear').addEventListener('click', () => {{
                drawings = [];
                selectedIdx = -1;
                updateSelectionUI();
                saveAndRedraw();
            }});

            window.addEventListener('keydown', (e) => {{
                if ((e.key === 'Delete' || e.key === 'Backspace') && selectedIdx !== -1) {{
                    deleteSelected();
                }} else if (e.key === 'e' || e.key === 'E') {{
                    setTool('eraser');
                }} else if (e.key === 'v' || e.key === 'V') {{
                    setTool('cursor');
                }}
            }});

            function saveAndRedraw() {{
                try {{ localStorage.setItem(storageKey, JSON.stringify(drawings)); }} catch (e) {{}}
                redrawAll();
            }}

            function resizeCanvas() {{
                canvas.width = mainPaneBox.clientWidth;
                canvas.height = mainPaneBox.clientHeight;
                redrawAll();
            }}

            function ptDist(x1, y1, x2, y2) {{ return Math.hypot(x2 - x1, y2 - y1); }}
            function distToSegment(px, py, x1, y1, x2, y2) {{
                const l2 = (x2 - x1)**2 + (y2 - y1)**2;
                if (l2 === 0) return ptDist(px, py, x1, y1);
                let t = ((px - x1)*(x2 - x1) + (py - y1)*(y2 - y1)) / l2;
                t = Math.max(0, Math.min(1, t));
                return ptDist(px, py, x1 + t*(x2 - x1), y1 + t*(y2 - y1));
            }}

            function getScreenCoords(d) {{
                const tScale = mainChart.timeScale();
                const x1 = tScale.timeToCoordinate(d.t1);
                const x2 = tScale.timeToCoordinate(d.t2);
                const y1 = mainSeries.priceToCoordinate(d.p1);
                const y2 = mainSeries.priceToCoordinate(d.p2);
                return {{ x1, y1, x2, y2 }};
            }}

            function hitTest(x, y) {{
                if (!mainSeries) return {{ idx: -1, handle: null }};
                if (selectedIdx !== -1 && drawings[selectedIdx]) {{
                    const d = drawings[selectedIdx];
                    const pts = getScreenCoords(d);
                    if (pts.x1 !== null && pts.y1 !== null && ptDist(x, y, pts.x1, pts.y1) < 10) return {{ idx: selectedIdx, handle: 'h1' }};
                    if (pts.x2 !== null && pts.y2 !== null && ptDist(x, y, pts.x2, pts.y2) < 10) return {{ idx: selectedIdx, handle: 'h2' }};
                }}

                for (let i = drawings.length - 1; i >= 0; i--) {{
                    const d = drawings[i];
                    const pts = getScreenCoords(d);
                    const {{ x1, y1, x2, y2 }} = pts;

                    if (d.tool === 'horz') {{
                        const targetY = y1 !== null ? y1 : d.fixedY;
                        if (targetY !== null && Math.abs(y - targetY) < 8) return {{ idx: i, handle: 'body' }};
                    }} else if (d.tool === 'trend') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            if (distToSegment(x, y, x1, y1, x2, y2) < 8) return {{ idx: i, handle: 'body' }};
                        }}
                    }} else if (d.tool === 'box') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            const minX = Math.min(x1, x2), maxX = Math.max(x1, x2);
                            const minY = Math.min(y1, y2), maxY = Math.max(y1, y2);
                            if (x >= minX - 6 && x <= maxX + 6 && y >= minY - 6 && y <= maxY + 6) return {{ idx: i, handle: 'body' }};
                        }}
                    }} else if (d.tool === 'fib') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
                            for (let lvl of levels) {{
                                const curY = y1 + (y2 - y1) * lvl;
                                if (Math.abs(y - curY) < 8 && x >= Math.min(x1, x2) - 10 && x <= Math.max(x1, x2) + 150) {{
                                    return {{ idx: i, handle: 'body' }};
                                }}
                            }}
                        }}
                    }} else if (d.tool === 'circle') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            const r = ptDist(x1, y1, x2, y2);
                            const dMouse = ptDist(x, y, x1, y1);
                            if (Math.abs(dMouse - r) < 8 || dMouse < r) return {{ idx: i, handle: 'body' }};
                        }}
                    }} else if (d.tool === 'text') {{
                        if (x1 !== null && y1 !== null) {{
                            if (Math.abs(x - x1) < 60 && Math.abs(y - y1) < 20) return {{ idx: i, handle: 'body' }};
                        }}
                    }} else if (d.tool === 'pen' && d.points) {{
                        const tScale = mainChart.timeScale();
                        for (let j = 0; j < d.points.length - 1; j++) {{
                            const px1 = tScale.timeToCoordinate(d.points[j].t);
                            const py1 = mainSeries.priceToCoordinate(d.points[j].p);
                            const px2 = tScale.timeToCoordinate(d.points[j+1].t);
                            const py2 = mainSeries.priceToCoordinate(d.points[j+1].p);
                            if (px1 && py1 && px2 && py2 && distToSegment(x, y, px1, py1, px2, py2) < 8) {{
                                return {{ idx: i, handle: 'body' }};
                            }}
                        }}
                    }}
                }}
                return {{ idx: -1, handle: null }};
            }}

            mainPaneBox.addEventListener('mousemove', (e) => {{
                if (isDragging || isDrawing) return;
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                if (currentTool === 'cursor') {{
                    const hit = hitTest(mouseX, mouseY);
                    if (hit.idx !== -1) {{
                        canvas.style.pointerEvents = 'auto';
                        canvas.style.cursor = (hit.handle === 'h1' || hit.handle === 'h2') ? 'pointer' : 'move';
                    }} else if (selectedIdx === -1) {{
                        canvas.style.pointerEvents = 'none';
                    }}
                }} else if (currentTool === 'eraser') {{
                    const hit = hitTest(mouseX, mouseY);
                    canvas.style.cursor = (hit.idx !== -1) ? 'pointer' : 'crosshair';
                }}
            }});

            canvas.addEventListener('mousedown', (e) => {{
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                if (currentTool === 'eraser') {{
                    const hit = hitTest(mouseX, mouseY);
                    if (hit.idx !== -1) {{
                        drawings.splice(hit.idx, 1);
                        selectedIdx = -1;
                        updateSelectionUI();
                        saveAndRedraw();
                    }}
                    return;
                }}

                if (currentTool === 'cursor') {{
                    const hit = hitTest(mouseX, mouseY);
                    if (hit.idx !== -1) {{
                        selectedIdx = hit.idx;
                        activeHandle = hit.handle;
                        isDragging = true;
                        startPx = {{ x: mouseX, y: mouseY }};
                        dragOrigObj = JSON.parse(JSON.stringify(drawings[selectedIdx]));
                        canvas.style.pointerEvents = 'auto';
                        updateSelectionUI();
                        redrawAll();
                    }} else {{
                        selectedIdx = -1;
                        activeHandle = null;
                        updateSelectionUI();
                        redrawAll();
                        canvas.style.pointerEvents = 'none';
                    }}
                    return;
                }}

                if (currentTool === 'text') {{
                    textOverlay.style.left = mouseX + 'px';
                    textOverlay.style.top = mouseY + 'px';
                    textOverlay.style.display = 'block';
                    textInput.value = '';
                    textInput.focus();
                    startPx = {{ x: mouseX, y: mouseY }};
                    return;
                }}

                isDrawing = true;
                startPx = {{ x: mouseX, y: mouseY }};
                currentPx = {{ ...startPx }};
                if (currentTool === 'pen') {{
                    penPoints = [{{ x: mouseX, y: mouseY }}];
                }}
            }});

            textInput.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter') {{
                    const val = textInput.value.trim();
                    if (val && startPx && mainSeries) {{
                        const t1 = mainChart.timeScale().coordinateToTime(startPx.x);
                        const p1 = mainSeries.coordinateToPrice(startPx.y);
                        if (p1 !== null) {{
                            drawings.push({{
                                tool: 'text',
                                text: val,
                                t1: t1 || 0,
                                p1: p1,
                                color: '#ffffff'
                            }});
                            saveAndRedraw();
                        }}
                    }}
                    textOverlay.style.display = 'none';
                    setTool('cursor');
                }} else if (e.key === 'Escape') {{
                    textOverlay.style.display = 'none';
                }}
            }});

            canvas.addEventListener('mousemove', (e) => {{
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                if (isDragging && selectedIdx !== -1 && dragOrigObj && mainSeries) {{
                    const dx = mouseX - startPx.x;
                    const dy = mouseY - startPx.y;
                    const d = drawings[selectedIdx];
                    const tScale = mainChart.timeScale();

                    if (activeHandle === 'h1') {{
                        const curOrig = getScreenCoords(dragOrigObj);
                        d.t1 = tScale.coordinateToTime(curOrig.x1 + dx) || d.t1;
                        d.p1 = mainSeries.coordinateToPrice(curOrig.y1 + dy) || d.p1;
                    }} else if (activeHandle === 'h2') {{
                        const curOrig = getScreenCoords(dragOrigObj);
                        d.t2 = tScale.coordinateToTime(curOrig.x2 + dx) || d.t2;
                        d.p2 = mainSeries.coordinateToPrice(curOrig.y2 + dy) || d.p2;
                    }} else if (activeHandle === 'body') {{
                        const curOrig = getScreenCoords(dragOrigObj);
                        if (curOrig.x1 !== null && curOrig.y1 !== null) {{
                            d.t1 = tScale.coordinateToTime(curOrig.x1 + dx) || d.t1;
                            d.p1 = mainSeries.coordinateToPrice(curOrig.y1 + dy) || d.p1;
                        }}
                        if (curOrig.x2 !== null && curOrig.y2 !== null) {{
                            d.t2 = tScale.coordinateToTime(curOrig.x2 + dx) || d.t2;
                            d.p2 = mainSeries.coordinateToPrice(curOrig.y2 + dy) || d.p2;
                        }}
                        if (d.tool === 'horz') {{
                            d.fixedY = (dragOrigObj.fixedY || curOrig.y1) + dy;
                        }}
                    }}
                    redrawAll();
                    return;
                }}

                if (!isDrawing) return;
                currentPx = {{ x: mouseX, y: mouseY }};
                if (currentTool === 'pen') {{
                    penPoints.push({{ x: mouseX, y: mouseY }});
                }}
                redrawAll();
                drawPreview();
            }});

            canvas.addEventListener('mouseup', () => {{
                if (isDragging) {{
                    isDragging = false;
                    activeHandle = null;
                    dragOrigObj = null;
                    saveAndRedraw();
                    return;
                }}

                if (!isDrawing) return;
                isDrawing = false;

                if (startPx && currentPx && mainSeries) {{
                    const tScale = mainChart.timeScale();
                    const t1 = tScale.coordinateToTime(startPx.x);
                    const t2 = tScale.coordinateToTime(currentPx.x);
                    const p1 = mainSeries.coordinateToPrice(startPx.y);
                    const p2 = mainSeries.coordinateToPrice(currentPx.y);

                    if (currentTool === 'pen') {{
                        const pts = penPoints.map(pt => ({{
                            t: tScale.coordinateToTime(pt.x) || 0,
                            p: mainSeries.coordinateToPrice(pt.y) || 0
                        }}));
                        if (pts.length > 1) {{
                            drawings.push({{ tool: 'pen', points: pts, color: '#f5c518' }});
                            saveAndRedraw();
                        }}
                        penPoints = [];
                    }} else if (p1 !== null) {{
                        drawings.push({{
                            tool: currentTool,
                            t1: t1 || 0,
                            p1: p1,
                            t2: t2 || 0,
                            p2: p2 !== null ? p2 : p1,
                            fixedY: startPx.y,
                            color: '#00FFA3'
                        }});
                        saveAndRedraw();
                    }}
                }}
                setTool('cursor');
            }});

            function drawPreview() {{
                if (!startPx || !currentPx) return;
                ctx.save();
                ctx.strokeStyle = '#00FFA3';
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 4]);

                if (currentTool === 'trend') {{
                    ctx.beginPath();
                    ctx.moveTo(startPx.x, startPx.y);
                    ctx.lineTo(currentPx.x, currentPx.y);
                    ctx.stroke();
                }} else if (currentTool === 'horz') {{
                    ctx.beginPath();
                    ctx.moveTo(0, currentPx.y);
                    ctx.lineTo(canvas.width, currentPx.y);
                    ctx.stroke();
                }} else if (currentTool === 'box') {{
                    const w = currentPx.x - startPx.x;
                    const h = currentPx.y - startPx.y;
                    ctx.fillStyle = 'rgba(0, 255, 163, 0.15)';
                    ctx.fillRect(startPx.x, startPx.y, w, h);
                    ctx.strokeRect(startPx.x, startPx.y, w, h);
                }} else if (currentTool === 'circle') {{
                    const r = ptDist(startPx.x, startPx.y, currentPx.x, currentPx.y);
                    ctx.beginPath();
                    ctx.arc(startPx.x, startPx.y, r, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(239, 83, 80, 0.12)';
                    ctx.fill();
                    ctx.stroke();
                }} else if (currentTool === 'fib') {{
                    const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
                    levels.forEach(lvl => {{
                        const y = startPx.y + (currentPx.y - startPx.y) * lvl;
                        ctx.beginPath();
                        ctx.moveTo(startPx.x, y);
                        ctx.lineTo(currentPx.x + 80, y);
                        ctx.stroke();
                    }});
                }} else if (currentTool === 'pen' && penPoints.length > 1) {{
                    ctx.setLineDash([]);
                    ctx.strokeStyle = '#f5c518';
                    ctx.beginPath();
                    ctx.moveTo(penPoints[0].x, penPoints[0].y);
                    for (let p of penPoints) ctx.lineTo(p.x, p.y);
                    ctx.stroke();
                }}
                ctx.restore();
            }}

            function drawHandle(x, y) {{
                ctx.save();
                ctx.beginPath();
                ctx.arc(x, y, 5, 0, Math.PI * 2);
                ctx.fillStyle = '#ffffff';
                ctx.fill();
                ctx.strokeStyle = '#00FFA3';
                ctx.lineWidth = 2;
                ctx.stroke();
                ctx.restore();
            }}

            function redrawAll() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                if (!mainSeries) return;

                const tScale = mainChart.timeScale();

                drawings.forEach((d, idx) => {{
                    const isSelected = (idx === selectedIdx);
                    ctx.save();
                    ctx.strokeStyle = isSelected ? '#00e5ff' : (d.color || '#00FFA3');
                    ctx.lineWidth = isSelected ? 2.5 : 2;

                    const pts = getScreenCoords(d);
                    const {{ x1, y1, x2, y2 }} = pts;

                    if (d.tool === 'horz') {{
                        const targetY = y1 !== null ? y1 : d.fixedY;
                        if (targetY !== null) {{
                            ctx.beginPath();
                            ctx.moveTo(0, targetY);
                            ctx.lineTo(canvas.width, targetY);
                            ctx.stroke();
                            if (isSelected) drawHandle(canvas.width / 2, targetY);
                        }}
                    }} else if (d.tool === 'trend') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            ctx.beginPath();
                            ctx.moveTo(x1, y1);
                            ctx.lineTo(x2, y2);
                            ctx.stroke();
                            if (isSelected) {{ drawHandle(x1, y1); drawHandle(x2, y2); }}
                        }}
                    }} else if (d.tool === 'box') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            const w = x2 - x1, h = y2 - y1;
                            ctx.fillStyle = isSelected ? 'rgba(0, 229, 255, 0.18)' : 'rgba(0, 255, 163, 0.15)';
                            ctx.fillRect(x1, y1, w, h);
                            ctx.strokeRect(x1, y1, w, h);
                            if (isSelected) {{ drawHandle(x1, y1); drawHandle(x2, y2); }}
                        }}
                    }} else if (d.tool === 'circle') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            const r = ptDist(x1, y1, x2, y2);
                            ctx.beginPath();
                            ctx.arc(x1, y1, r, 0, Math.PI * 2);
                            ctx.fillStyle = isSelected ? 'rgba(0, 229, 255, 0.18)' : 'rgba(239, 83, 80, 0.12)';
                            ctx.fill();
                            ctx.stroke();
                            if (isSelected) {{ drawHandle(x1, y1); drawHandle(x2, y2); }}
                        }}
                    }} else if (d.tool === 'fib') {{
                        if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {{
                            const levels = [
                                {{ r: 0.0, c: '#787b86' }},
                                {{ r: 0.236, c: '#f23645' }},
                                {{ r: 0.382, c: '#ff9800' }},
                                {{ r: 0.5, c: '#4caf50' }},
                                {{ r: 0.618, c: '#089981' }},
                                {{ r: 0.786, c: '#00bcd4' }},
                                {{ r: 1.0, c: '#787b86' }}
                            ];
                            const maxX = Math.max(x1, x2) + 120;
                            const minX = Math.min(x1, x2);
                            levels.forEach(lvl => {{
                                const curY = y1 + (y2 - y1) * lvl.r;
                                ctx.strokeStyle = lvl.c;
                                ctx.beginPath();
                                ctx.moveTo(minX, curY);
                                ctx.lineTo(maxX, curY);
                                ctx.stroke();

                                ctx.fillStyle = lvl.c;
                                ctx.font = '10px Roboto Mono, monospace';
                                ctx.fillText(lvl.r + ' (' + (mainSeries.coordinateToPrice(curY)?.toFixed(2) || '') + ')', maxX - 65, curY - 3);
                            }});
                            if (isSelected) {{ drawHandle(x1, y1); drawHandle(x2, y2); }}
                        }}
                    }} else if (d.tool === 'text') {{
                        if (x1 !== null && y1 !== null) {{
                            ctx.fillStyle = isSelected ? '#00e5ff' : '#ffffff';
                            ctx.font = 'bold 13px -apple-system, sans-serif';
                            ctx.fillText(d.text, x1, y1);
                            if (isSelected) drawHandle(x1 - 6, y1 - 4);
                        }}
                    }} else if (d.tool === 'pen' && d.points) {{
                        ctx.strokeStyle = isSelected ? '#00e5ff' : (d.color || '#f5c518');
                        ctx.beginPath();
                        let started = false;
                        for (let pt of d.points) {{
                            const px = tScale.timeToCoordinate(pt.t);
                            const py = mainSeries.priceToCoordinate(pt.p);
                            if (px !== null && py !== null) {{
                                if (!started) {{ ctx.moveTo(px, py); started = true; }}
                                else ctx.lineTo(px, py);
                            }}
                        }}
                        ctx.stroke();
                    }}
                    ctx.restore();
                }});
            }}

            mainChart.timeScale().subscribeVisibleTimeRangeChange(redrawAll);
            mainChart.timeScale().subscribeVisibleLogicalRangeChange(redrawAll);

            /* ===== 5. ระบบ FLOATING HEADER & SPLITTER (ไม่กินความสูงกราฟ) ===== */
            const paneRegistry = [];
            let _spDrag = null;

            function _spRedrawHooks() {{
                ['resizeCanvas','redrawAll','drawAll','renderDrawings','redraw']
                .forEach(fn => {{ if (typeof window[fn] === 'function') {{ try {{ window[fn](); }} catch(e) {{}} }} }});
            }}

            function paneResizeAll() {{
                paneRegistry.forEach(p => {{
                    if (!p.chart || !p.boxEl || !p.viewEl) return;
                    if (p.boxEl.dataset.collapsed) return;
                    const h = Math.max(30, p.boxEl.clientHeight);
                    const w = p.boxEl.clientWidth || p.viewEl.clientWidth;
                    p.viewEl.style.height = h + 'px';
                    try {{ p.chart.applyOptions({{ width: w, height: h }}); }} catch(e) {{}}
                }});
                _spRedrawHooks();
            }}

            function initPaneDrag(e, upperId, lowerId) {{
            e.preventDefault();
            const up = document.getElementById(upperId);
            const low = lowerId ? document.getElementById(lowerId) : null;
            if (!up) return;
            _spDrag = {{
                up: up,
                low: low,
                bar: e.currentTarget,
                y: e.clientY,
                uh: up.clientHeight,
                lh: low ? low.clientHeight : 0,
                isBottom: !low
            }};
            e.currentTarget.classList.add('dragging');
            document.body.style.cursor = 'ns-resize';
            document.body.style.userSelect = 'none';
            window.addEventListener('mousemove', onPaneDrag);
            window.addEventListener('mouseup', stopPaneDrag);
        }}

        function onPaneDrag(e) {{
            if (!_spDrag) return;
            const dy = e.clientY - _spDrag.y;
            if (_spDrag.isBottom) {{
                // กรณีลากเส้นขอบล่างสุดของ MACD: ขยาย/หดความสูง MACD ลงล่างโดยตรง
                _spDrag.up.style.flex = 'none';
                _spDrag.up.style.height = Math.max(40, _spDrag.uh + dy) + 'px';
            }} else {{
                // กรณีลากเส้นคั่นระหว่างหน้าต่าง: กราฟหลักกับ RSI ทำงานตามเดิม
                _spDrag.up.style.flex = 'none';
                _spDrag.low.style.flex = 'none';
                _spDrag.up.style.height = Math.max(80, _spDrag.uh + dy) + 'px';
                _spDrag.low.style.height = Math.max(46, _spDrag.lh - dy) + 'px';
            }}
            paneResizeAll();
        }}
            function stopPaneDrag() {{
                if (_spDrag && _spDrag.bar) _spDrag.bar.classList.remove('dragging');
                _spDrag = null;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                window.removeEventListener('mousemove', onPaneDrag);
                window.removeEventListener('mouseup', stopPaneDrag);
                paneResizeAll();
            }}
            

            function togglePaneVisibility(key) {{
                const p = paneRegistry.find(r => r.key === key);
                if (!p) return;
                const hidden = p.viewEl.style.visibility === 'hidden';
                p.viewEl.style.visibility = hidden ? 'visible' : 'hidden';
                const b = p.headerEl && p.headerEl.querySelector('[data-act="eye"]');
                if (b) {{
                    b.textContent = hidden ? '👁' : '🚫';
                    b.classList.toggle('off', !hidden);
                }}
            }}

            function togglePaneCollapse(boxId) {{
                const p = paneRegistry.find(r => r.boxEl && r.boxEl.id === boxId);
                if (!p) return;
                const box = p.boxEl;
                if (!box.dataset.collapsed) {{
                    box.dataset.prevH = box.clientHeight + 'px';
                    box.dataset.collapsed = '1';
                    p.viewEl.style.display = 'none';
                    box.style.flex = 'none';
                    box.style.height = '28px';
                }} else {{
                    delete box.dataset.collapsed;
                    p.viewEl.style.display = '';
                    box.style.height = box.dataset.prevH || '140px';
                }}
                paneResizeAll();
            }}

            function closePaneBox(boxId) {{
                const p = paneRegistry.find(r => r.boxEl && r.boxEl.id === boxId);
                if (!p) return;
                p.boxEl.style.display = 'none';
                if (p.splitterEl) p.splitterEl.style.display = 'none';
                paneResizeAll();
            }}

            function _spBuildHeader(key, title, boxId, canClose) {{
                const h = document.createElement('div');
                h.className = 'pane-header';
                h.innerHTML =
                  '<div class="pane-actions">' +
                    '<button class="pane-btn" data-act="eye" title="ซ่อน/แสดง">👁</button>' +
                    '<button class="pane-btn" data-act="col" title="พับเก็บ">⌵</button>' +
                    (canClose ? '<button class="pane-btn pane-btn-x" data-act="cls" title="ปิด">✕</button>' : '') +
                  '</div>';
                h.querySelector('[data-act="eye"]').onclick = () => togglePaneVisibility(key);
                h.querySelector('[data-act="col"]').onclick = () => togglePaneCollapse(boxId);
                const x = h.querySelector('[data-act="cls"]');
                if (x) x.onclick = () => closePaneBox(boxId);
                return h;
            }}

            function upgradePanes(titles) {{
                titles = titles || [];
                // 1. กราฟหลัก (ใส่ปุ่มลอยมุมขวาบนในกรอบ mainBox)
                const mainBox = document.getElementById('main-pane-container');
                const mainView = document.getElementById('chart-main');
                if (mainBox && mainView && !mainBox.dataset.spUpgraded) {{
                    mainBox.dataset.spUpgraded = '1';
                    if (!mainBox.style.height) mainBox.style.height = mainView.clientHeight + 'px';
                    const hdr = _spBuildHeader('main', titles[0] || 'MAIN CHART', 'main-pane-container', false);
                    mainBox.appendChild(hdr);
                    paneRegistry.push({{
                        key: 'main', chart: (typeof allCharts !== 'undefined' ? allCharts[0] : null),
                        viewEl: mainView, boxEl: mainBox, headerEl: hdr, splitterEl: null
                    }});
                }}

                // 2. Sub-panes (RSI / MACD)
                const subs = Array.from(document.querySelectorAll('#sub-panes > .sub-pane'));
                subs.forEach((pane, i) => {{
                    if (pane.dataset.spUpgraded) return;
                    pane.dataset.spUpgraded = '1';
                    const boxId = 'pane_box_' + i;
                    const origH = parseInt(pane.style.height, 10) || pane.clientHeight || 120;

                    const box = document.createElement('div');
                    box.className = 'pane-box';
                    box.id = boxId;
                    box.style.height = origH + 'px';
                    pane.parentNode.insertBefore(box, pane);

                    const hdr = _spBuildHeader('sub' + i, titles[i + 1] || ('PANE ' + (i + 2)), boxId, true);
                    box.appendChild(pane);
                    box.appendChild(hdr);
                    pane.classList.add('chart-view');

                    const sp = document.createElement('div');
                    sp.className = 'splitter-bar';
                    const upperId = (i === 0) ? 'main-pane-container' : ('pane_box_' + (i - 1));
                    sp.addEventListener('mousedown', e => initPaneDrag(e, upperId, boxId));
                    box.parentNode.insertBefore(sp, box);

                    paneRegistry.push({{
                        key: 'sub' + i, chart: (typeof allCharts !== 'undefined' ? allCharts[i + 1] : null),
                        viewEl: pane, boxEl: box, headerEl: hdr, splitterEl: sp
                    }});
                }});
                // ── เส้นเขียวใต้ MACD สำหรับดึงยืดลงข้างล่าง ──
        const lastPane = paneRegistry[paneRegistry.length - 1];
        if (lastPane && lastPane.boxEl && !document.getElementById('splitter-bar-bottom')) {{
            const botSp = document.createElement('div');
            botSp.id = 'splitter-bar-bottom';
            botSp.className = 'splitter-bar';
            lastPane.boxEl.parentNode.appendChild(botSp);
            botSp.addEventListener('mousedown', e => initPaneDrag(e, lastPane.boxEl.id, null));
        }}
                paneResizeAll();
            }}

            function updateAllWidths() {{
                const newW = container.clientWidth || window.innerWidth;
                allCharts.forEach(c => c.applyOptions({{ width: newW }}));
                resizeCanvas();
            }}

            upgradePanes(['MAIN CHART', 'RSI', 'MACD']);
            window.addEventListener('resize', updateAllWidths);
            window.addEventListener('resize', () => {{ try {{ paneResizeAll(); }} catch(e) {{}} }});
            setTimeout(updateAllWidths, 100);
            setTimeout(paneResizeAll, 150);
            setTimeout(updateAllWidths, 300);
            setTimeout(paneResizeAll, 350);
        }})();
        </script>
    </body>
    </html>
    """
    # อัปเดตชื่อเหรียญและกระดานเทรดให้ตรงกับสินทรัพย์ที่เลือก
    html_code = html_code.replace(">BTCUSDT<", f">{display_title}<").replace(">Binance<", f">{exchange_name}<").replace('"BTCUSDT"', f'"{display_title}"')
    components.html(html_code, height=real_total_h)