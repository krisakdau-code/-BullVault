# drawing_chart.py — Multi-Pane Anchored Drawing Terminal
import json
import streamlit.components.v1 as components

def render_drawing_chart(charts_config: list, height: int = None, key: str = "draw_chart"):
    if not charts_config:
        return

    # คำนวณความสูงรวมจริงของทุกหน้าต่าง (กราฟหลัก 520 + RSI 120 + MACD 120 = ~790px)
    real_total_h = 0
    for c in charts_config:
        real_total_h += int(c.get("chart", {}).get("height", 130)) + 6
    real_total_h += 30

    chart_json = json.dumps(charts_config)

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
                gap: 2px;
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
            #drawing-canvas.active-draw {{
                pointer-events: auto;
                cursor: crosshair;
            }}
            .draw-toolbar {{
                position: absolute;
                top: 12px;
                left: 12px;
                z-index: 20;
                display: flex;
                flex-direction: column;
                gap: 4px;
                background: rgba(19, 23, 34, 0.88);
                backdrop-filter: blur(6px);
                border: 1px solid #2a2e39;
                border-radius: 6px;
                padding: 4px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.6);
            }}
            .tool-btn {{
                width: 30px;
                height: 30px;
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                color: #b2b5be;
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.15s ease;
            }}
            .tool-btn:hover {{
                background: #2a2e39;
                color: #ffffff;
            }}
            .tool-btn.active {{
                background: #2962ff;
                border-color: #2962ff;
                color: #ffffff;
            }}
            .tool-sep {{
                width: 20px;
                height: 1px;
                background: #2a2e39;
                margin: 2px auto;
            }}
            .sub-pane {{
                width: 100%;
                background: #000000;
            }}
        </style>
    </head>
    <body>
        <div id="container">
            <div id="main-pane-container">
                <div class="draw-toolbar">
                    <button class="tool-btn active" id="btn-cursor" title="โหมดเมาส์ปกติ (เลื่อน/ซูมกราฟ)">↖</button>
                    <div class="tool-sep"></div>
                    <button class="tool-btn" id="btn-trend" title="เส้นแนวโน้ม (Trendline)">╱</button>
                    <button class="tool-btn" id="btn-horz" title="เส้นแนวนอน (Horizontal Level)">―</button>
                    <button class="tool-btn" id="btn-box" title="กล่องโซน (Rectangle Zone)">▭</button>
                    <div class="tool-sep"></div>
                    <button class="tool-btn" id="btn-undo" title="ย้อนกลับ (Undo)">↩</button>
                    <button class="tool-btn" id="btn-clear" title="ล้างเส้นทั้งหมด">🗑️</button>
                </div>
                <div id="chart-main"></div>
                <canvas id="drawing-canvas"></canvas>
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

            const initWidth = container.clientWidth || window.innerWidth;
            const mainH = mainConfig.chart?.height || 520;
            mainPaneBox.style.height = mainH + 'px';

            // 1. เรนเดอร์กราฟหลัก
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
                }});
            }}

            // 2. เรนเดอร์ช่อง RSI และ MACD
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
                        if (s.type === "Line") {{
                            series = subChart.addLineSeries(opts);
                        }} else if (s.type === "Histogram") {{
                            series = subChart.addHistogramSeries(opts);
                        }} else if (s.type === "Candlestick") {{
                            series = subChart.addCandlestickSeries(opts);
                        }}
                        if (series && s.data) series.setData(s.data);
                    }});
                }}
            }});

            // 3. ซิงค์แกนเวลาเลื่อนและซูมพร้อมกันทุกหน้าต่าง
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

            // 4. ระบบวาดและพิกัด Canvas
            function resizeCanvas() {{
                canvas.width = mainPaneBox.clientWidth;
                canvas.height = mainPaneBox.clientHeight;
                redrawAll();
            }}

            const storageKey = 'tv_drawings_' + (mainConfig.chart?.watermark?.text || 'default');
            let drawings = [];
            try {{
                const saved = localStorage.getItem(storageKey);
                if (saved) drawings = JSON.parse(saved);
            }} catch (e) {{}}

            let currentTool = 'cursor';
            let isDrawing = false;
            let startPx = null;
            let currentPx = null;

            const toolBtns = {{
                cursor: document.getElementById('btn-cursor'),
                trend: document.getElementById('btn-trend'),
                horz: document.getElementById('btn-horz'),
                box: document.getElementById('btn-box')
            }};

            function setTool(tool) {{
                currentTool = tool;
                Object.keys(toolBtns).forEach(k => {{
                    if (toolBtns[k]) toolBtns[k].classList.toggle('active', k === tool);
                }});
                canvas.classList.toggle('active-draw', tool !== 'cursor');
            }}

            Object.keys(toolBtns).forEach(tool => {{
                if (toolBtns[tool]) {{
                    toolBtns[tool].addEventListener('click', () => setTool(tool));
                }}
            }});

            document.getElementById('btn-undo').addEventListener('click', () => {{
                drawings.pop();
                saveAndRedraw();
            }});

            document.getElementById('btn-clear').addEventListener('click', () => {{
                drawings = [];
                saveAndRedraw();
            }});

            function saveAndRedraw() {{
                try {{ localStorage.setItem(storageKey, JSON.stringify(drawings)); }} catch (e) {{}}
                redrawAll();
            }}

            canvas.addEventListener('mousedown', (e) => {{
                if (currentTool === 'cursor') return;
                const rect = canvas.getBoundingClientRect();
                isDrawing = true;
                startPx = {{ x: e.clientX - rect.left, y: e.clientY - rect.top }};
                currentPx = {{ ...startPx }};
            }});

            canvas.addEventListener('mousemove', (e) => {{
                if (!isDrawing) return;
                const rect = canvas.getBoundingClientRect();
                currentPx = {{ x: e.clientX - rect.left, y: e.clientY - rect.top }};
                redrawAll();
                drawPreview();
            }});

            canvas.addEventListener('mouseup', () => {{
                if (!isDrawing) return;
                isDrawing = false;

                if (startPx && currentPx && mainSeries) {{
                    const tScale = mainChart.timeScale();
                    const t1 = tScale.coordinateToTime(startPx.x);
                    const t2 = tScale.coordinateToTime(currentPx.x);
                    const p1 = mainSeries.coordinateToPrice(startPx.y);
                    const p2 = mainSeries.coordinateToPrice(currentPx.y);

                    if (p1 !== null && p2 !== null) {{
                        drawings.push({{
                            tool: currentTool,
                            t1: t1 || 0,
                            p1: p1,
                            t2: t2 || 0,
                            p2: p2,
                            fixedY1: startPx.y,
                            fixedY2: currentPx.y,
                            color: '#2962ff'
                        }});
                        saveAndRedraw();
                    }}
                }}
            }});

            function drawPreview() {{
                if (!startPx || !currentPx) return;
                ctx.save();
                ctx.strokeStyle = '#2962ff';
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
                    ctx.fillStyle = 'rgba(41, 98, 255, 0.15)';
                    ctx.fillRect(startPx.x, startPx.y, w, h);
                    ctx.strokeRect(startPx.x, startPx.y, w, h);
                }}
                ctx.restore();
            }}

            function redrawAll() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                if (!mainSeries) return;

                const tScale = mainChart.timeScale();

                drawings.forEach(d => {{
                    ctx.save();
                    ctx.strokeStyle = d.color || '#2962ff';
                    ctx.lineWidth = 2;

                    const y1 = mainSeries.priceToCoordinate(d.p1);
                    const y2 = mainSeries.priceToCoordinate(d.p2);

                    if (d.tool === 'horz') {{
                        const targetY = y2 !== null ? y2 : d.fixedY2;
                        ctx.beginPath();
                        ctx.moveTo(0, targetY);
                        ctx.lineTo(canvas.width, targetY);
                        ctx.stroke();
                    }} else if (d.tool === 'trend' || d.tool === 'box') {{
                        let x1 = tScale.timeToCoordinate(d.t1);
                        let x2 = tScale.timeToCoordinate(d.t2);

                        if (x1 !== null && x2 !== null && y1 !== null && y2 !== null) {{
                            if (d.tool === 'trend') {{
                                ctx.beginPath();
                                ctx.moveTo(x1, y1);
                                ctx.lineTo(x2, y2);
                                ctx.stroke();
                            }} else if (d.tool === 'box') {{
                                const w = x2 - x1;
                                const h = y2 - y1;
                                ctx.fillStyle = 'rgba(41, 98, 255, 0.15)';
                                ctx.fillRect(x1, y1, w, h);
                                ctx.strokeRect(x1, y1, w, h);
                            }}
                        }}
                    }}
                    ctx.restore();
                }});
            }}

            mainChart.timeScale().subscribeVisibleTimeRangeChange(redrawAll);
            mainChart.timeScale().subscribeVisibleLogicalRangeChange(redrawAll);

            function updateAllWidths() {{
                const newW = container.clientWidth || window.innerWidth;
                allCharts.forEach(c => c.applyOptions({{ width: newW }}));
                resizeCanvas();
            }}

            window.addEventListener('resize', updateAllWidths);
            setTimeout(updateAllWidths, 100);
            setTimeout(updateAllWidths, 300);
        }})();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=real_total_h)