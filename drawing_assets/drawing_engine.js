(function() {
    const config = window.__CHART_CONFIG__;
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

    const mainChart = LightweightCharts.createChart(mainContainer, {
        ...(mainConfig.chart || {}),
        width: initWidth,
        height: mainH
    });
    allCharts.push(mainChart);

    let mainSeries = null;
    if (mainConfig.series) {
        mainConfig.series.forEach(s => {
            let series = null;
            const opts = Object.assign({}, s.options || {});
            if (opts.priceScaleId && opts.priceScaleId !== 'left' && opts.priceScaleId !== 'right') {
                delete opts.priceScaleId;
            }
            if (s.type === "Candlestick") {
                series = mainChart.addCandlestickSeries(opts);
                if (!mainSeries) mainSeries = series;
            } else if (s.type === "Line") {
                series = mainChart.addLineSeries(opts);
                if (!mainSeries) mainSeries = series;
            } else if (s.type === "Histogram") {
                series = mainChart.addHistogramSeries(opts);
            } else if (s.type === "Area") {
                series = mainChart.addAreaSeries(opts);
            }
            if (series && s.data) series.setData(s.data);
            if (series && s.markers) series.setMarkers(s.markers);

            if (series && s.type === "Candlestick" && s.data && s.data.length > 0) {
                const lastBar = s.data[s.data.length - 1];
                const prevBar = s.data.length > 1 ? s.data[s.data.length - 2] : lastBar;
                const diff = lastBar.close - prevBar.close;
                const pct = (diff / prevBar.close) * 100;
                const isUp = diff >= 0;
                const color = isUp ? '#089981' : '#F23645';

                const pEl = document.getElementById('leg-price');
                const cEl = document.getElementById('leg-change');
                if (pEl) {
                    pEl.textContent = lastBar.close.toLocaleString('en-US', {minimumFractionDigits: 2});
                    pEl.style.color = color;
                }
                if (cEl) {
                    cEl.textContent = (isUp ? '+' : '') + pct.toFixed(2) + '%';
                    cEl.style.color = color;
                }
                
                const sVal = document.getElementById('qt-sell-val');
                const bVal = document.getElementById('qt-buy-val');
                if (sVal) sVal.textContent = lastBar.close.toLocaleString('en-US', {minimumFractionDigits: 2});
                if (bVal) bVal.textContent = (lastBar.close * 1.0001).toLocaleString('en-US', {minimumFractionDigits: 2});
            }
        });
    }

    const subPanesDiv = document.getElementById('sub-panes');
    subConfigs.forEach((subConf) => {
        const paneH = subConf.chart?.height || 120;
        const paneWrapper = document.createElement('div');
        paneWrapper.className = 'sub-pane';
        paneWrapper.style.height = paneH + 'px';
        subPanesDiv.appendChild(paneWrapper);

        const subChart = LightweightCharts.createChart(paneWrapper, {
            ...(subConf.chart || {}),
            width: initWidth,
            height: paneH
        });
        allCharts.push(subChart);

        if (subConf.series) {
            subConf.series.forEach(s => {
                let series = null;
                const opts = Object.assign({}, s.options || {});
                if (opts.priceScaleId && opts.priceScaleId !== 'left' && opts.priceScaleId !== 'right') {
                    delete opts.priceScaleId;
                }
                if (s.type === "Line") series = subChart.addLineSeries(opts);
                else if (s.type === "Histogram") series = subChart.addHistogramSeries(opts);
                else if (s.type === "Candlestick") series = subChart.addCandlestickSeries(opts);
                else if (s.type === "Area") series = subChart.addAreaSeries(opts);
                
                if (series && s.data) series.setData(s.data);

                if (series && s.priceLines && Array.isArray(s.priceLines)) {
                    s.priceLines.forEach(pl => {
                        try { series.createPriceLine(pl); } catch(e) {}
                    });
                }
            });
        }
    });

    if (mainChart && mainSeries) {
        mainChart.subscribeCrosshairMove(param => {
            const ohlcEl = document.getElementById('leg-ohlc');
            if (!ohlcEl) return;
            if (!param || !param.time || !param.seriesData.has(mainSeries)) {
                ohlcEl.textContent = '';
                return;
            }
            const d = param.seriesData.get(mainSeries);
            if (d.open !== undefined) {
                ohlcEl.textContent = `O: ${d.open.toFixed(2)}  H: ${d.high.toFixed(2)}  L: ${d.low.toFixed(2)}  C: ${d.close.toFixed(2)}`;
            }
        });
    }

    const toolbar = document.getElementById('main-draw-toolbar');
    const dragHandle = document.getElementById('tb-drag-handle');
    let isTbDragging = false;
    let tbOffsetX = 0, tbOffsetY = 0;

    dragHandle.addEventListener('mousedown', (e) => {
        isTbDragging = true;
        tbOffsetX = e.clientX - toolbar.offsetLeft;
        tbOffsetY = e.clientY - toolbar.offsetTop;
        dragHandle.style.cursor = 'grabbing';
        e.preventDefault();
        e.stopPropagation();
    });

    window.addEventListener('mousemove', (e) => {
        if (!isTbDragging) return;
        let newX = e.clientX - tbOffsetX;
        let newY = e.clientY - tbOffsetY;
        const maxX = mainPaneBox.clientWidth - toolbar.offsetWidth - 6;
        const maxY = mainPaneBox.clientHeight - toolbar.offsetHeight - 6;
        newX = Math.max(6, Math.min(newX, maxX));
        newY = Math.max(6, Math.min(newY, maxY));
        toolbar.style.left = newX + 'px';
        toolbar.style.top = newY + 'px';
    });

    window.addEventListener('mouseup', () => {
        if (isTbDragging) {
            isTbDragging = false;
            dragHandle.style.cursor = 'grab';
        }
    });

    // Auto Fib Control Listeners
    const autoFibEnable = document.getElementById('autofib-enable');
    const autoFibLookback = document.getElementById('autofib-lookback');
    const autoFibVal = document.getElementById('autofib-val');
    const autoFibGp = document.getElementById('autofib-gp');

    if (autoFibLookback) {
        autoFibLookback.addEventListener('input', () => {
            if (autoFibVal) autoFibVal.textContent = autoFibLookback.value;
            redrawAll();
        });
    }
    if (autoFibEnable) autoFibEnable.addEventListener('change', redrawAll);
    if (autoFibGp) autoFibGp.addEventListener('change', redrawAll);

    let isSyncing = false;
    allCharts.forEach((c, idx) => {
        c.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (isSyncing || !range) return;
            isSyncing = true;
            allCharts.forEach((other, oIdx) => {
                if (idx !== oIdx) {
                    try { other.timeScale().setVisibleLogicalRange(range); } catch(err) {}
                }
            });
            isSyncing = false;
        });
    });

    const storageKey = 'tv_vector_drawings_' + (mainConfig.chart?.watermark?.text || 'default');
    let drawings = [];
    try {
        const saved = localStorage.getItem(storageKey);
        if (saved) drawings = JSON.parse(saved);
    } catch (e) {}

    let currentTool = 'cursor';
    let selectedIdx = -1;
    let activeHandle = null;
    let isDragging = false;
    let isDrawing = false;
    let startPx = null;
    let currentPx = null;
    let penPoints = [];
    let dragOrigObj = null;

    const toolBtns = {
        cursor: document.getElementById('btn-cursor'),
        eraser: document.getElementById('btn-eraser'),
        trend: document.getElementById('btn-trend'),
        horz: document.getElementById('btn-horz'),
        box: document.getElementById('btn-box'),
        circle: document.getElementById('btn-circle'),
        pen: document.getElementById('btn-pen'),
        text: document.getElementById('btn-text')
    };

    function setTool(tool) {
        currentTool = tool;
        Object.keys(toolBtns).forEach(k => {
            if (toolBtns[k]) {
                toolBtns[k].classList.toggle('active', k === tool && tool !== 'eraser');
                toolBtns[k].classList.toggle('eraser-active', k === tool && tool === 'eraser');
            }
        });

        document.querySelectorAll('.sub-item').forEach(el => {
            el.classList.toggle('active', el.dataset.tool === tool);
        });

        const fibTools = ['fib', 'fib_ext'];
        const patTools = ['head_shoulders', 'triangle', 'elliott_impulse', 'elliott_abc'];
        const calcTools = ['pos_long', 'pos_short', 'price_range', 'date_range'];
        
        document.getElementById('btn-fib-group').classList.toggle('active', fibTools.includes(tool));
        document.getElementById('btn-pattern-group').classList.toggle('active', patTools.includes(tool));
        document.getElementById('btn-calc-group').classList.toggle('active', calcTools.includes(tool));

        if (tool === 'cursor') {
            canvas.style.pointerEvents = (selectedIdx !== -1) ? 'auto' : 'none';
            canvas.style.cursor = 'default';
        } else {
            canvas.style.pointerEvents = 'auto';
            canvas.style.cursor = 'crosshair';
            selectedIdx = -1;
            updateSelectionUI();
        }
        redrawAll();
    }

    Object.keys(toolBtns).forEach(tool => {
        if (toolBtns[tool]) toolBtns[tool].addEventListener('click', () => setTool(tool));
    });

    document.querySelectorAll('.sub-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const chosen = item.dataset.tool;
            setTool(chosen);
        });
    });

    function updateSelectionUI() {
        if (selectedIdx !== -1) {
            btnDeleteSelected.classList.add('danger-active');
            btnDeleteSelected.style.opacity = '1';
        } else {
            btnDeleteSelected.classList.remove('danger-active');
            btnDeleteSelected.style.opacity = '0.7';
        }
    }

    function deleteSelected() {
        if (selectedIdx >= 0 && selectedIdx < drawings.length) {
            drawings.splice(selectedIdx, 1);
            selectedIdx = -1;
            updateSelectionUI();
            saveAndRedraw();
        }
    }

    btnDeleteSelected.addEventListener('click', () => {
        if (selectedIdx >= 0 && selectedIdx < drawings.length) {
            deleteSelected();
        } else {
            setTool('eraser');
        }
    });

    document.getElementById('btn-undo').addEventListener('click', () => {
        drawings.pop();
        selectedIdx = -1;
        updateSelectionUI();
        saveAndRedraw();
    });

    document.getElementById('btn-clear').addEventListener('click', () => {
        drawings = [];
        selectedIdx = -1;
        updateSelectionUI();
        saveAndRedraw();
    });

    window.addEventListener('keydown', (e) => {
        if ((e.key === 'Delete' || e.key === 'Backspace') && selectedIdx !== -1) {
            deleteSelected();
        } else if (e.key === 'e' || e.key === 'E') {
            setTool('eraser');
        } else if (e.key === 'v' || e.key === 'V') {
            setTool('cursor');
        }
    });

    function saveAndRedraw() {
        try { localStorage.setItem(storageKey, JSON.stringify(drawings)); } catch (e) {}
        redrawAll();
    }

    function resizeCanvas() {
        canvas.width = mainPaneBox.clientWidth;
        canvas.height = mainPaneBox.clientHeight;
        redrawAll();
    }

    function ptDist(x1, y1, x2, y2) { return Math.hypot(x2 - x1, y2 - y1); }
    function distToSegment(px, py, x1, y1, x2, y2) {
        const l2 = (x2 - x1)**2 + (y2 - y1)**2;
        if (l2 === 0) return ptDist(px, py, x1, y1);
        let t = ((px - x1)*(x2 - x1) + (py - y1)*(y2 - y1)) / l2;
        t = Math.max(0, Math.min(1, t));
        return ptDist(px, py, x1 + t*(x2 - x1), y1 + t*(y2 - y1));
    }

    function getScreenCoords(d) {
        const tScale = mainChart.timeScale();
        const x1 = tScale.timeToCoordinate(d.t1);
        const x2 = tScale.timeToCoordinate(d.t2);
        const y1 = mainSeries.priceToCoordinate(d.p1);
        const y2 = mainSeries.priceToCoordinate(d.p2);
        return { x1, y1, x2, y2 };
    }

    function hitTest(x, y) {
        if (!mainSeries) return { idx: -1, handle: null };
        if (selectedIdx !== -1 && drawings[selectedIdx]) {
            const d = drawings[selectedIdx];
            const pts = getScreenCoords(d);
            if (pts.x1 !== null && pts.y1 !== null && ptDist(x, y, pts.x1, pts.y1) < 10) return { idx: selectedIdx, handle: 'h1' };
            if (pts.x2 !== null && pts.y2 !== null && ptDist(x, y, pts.x2, pts.y2) < 10) return { idx: selectedIdx, handle: 'h2' };
        }

        for (let i = drawings.length - 1; i >= 0; i--) {
            const d = drawings[i];
            const pts = getScreenCoords(d);
            const { x1, y1, x2, y2 } = pts;

            if (d.tool === 'horz') {
                const targetY = y1 !== null ? y1 : d.fixedY;
                if (targetY !== null && Math.abs(y - targetY) < 8) return { idx: i, handle: 'body' };
            } else if (d.tool === 'trend' || d.tool === 'fib_ext') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    if (distToSegment(x, y, x1, y1, x2, y2) < 8) return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'box' || d.tool === 'pos_long' || d.tool === 'pos_short' || d.tool === 'price_range' || d.tool === 'date_range') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const minX = Math.min(x1, x2), maxX = Math.max(x1, x2);
                    const minY = Math.min(y1, y2), maxY = Math.max(y1, y2);
                    if (x >= minX - 6 && x <= maxX + 6 && y >= minY - 6 && y <= maxY + 6) return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'fib') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
                    for (let lvl of levels) {
                        const curY = y1 + (y2 - y1) * lvl;
                        if (Math.abs(y - curY) < 8 && x >= Math.min(x1, x2) - 10 && x <= Math.max(x1, x2) + 160) {
                            return { idx: i, handle: 'body' };
                        }
                    }
                }
            } else if (d.tool === 'circle') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const r = ptDist(x1, y1, x2, y2);
                    const dMouse = ptDist(x, y, x1, y1);
                    if (Math.abs(dMouse - r) < 8 || dMouse < r) return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'text') {
                if (x1 !== null && y1 !== null) {
                    if (Math.abs(x - x1) < 60 && Math.abs(y - y1) < 20) return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'pen' && d.points) {
                const tScale = mainChart.timeScale();
                for (let j = 0; j < d.points.length - 1; j++) {
                    const px1 = tScale.timeToCoordinate(d.points[j].t);
                    const py1 = mainSeries.priceToCoordinate(d.points[j].p);
                    const px2 = tScale.timeToCoordinate(d.points[j+1].t);
                    const py2 = mainSeries.priceToCoordinate(d.points[j+1].p);
                    if (px1 && py1 && px2 && py2 && distToSegment(x, y, px1, py1, px2, py2) < 8) {
                        return { idx: i, handle: 'body' };
                    }
                }
            }
        }
        return { idx: -1, handle: null };
    }

    mainPaneBox.addEventListener('mousemove', (e) => {
        if (isDragging || isDrawing) return;
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        if (currentTool === 'cursor') {
            const hit = hitTest(mouseX, mouseY);
            if (hit.idx !== -1) {
                canvas.style.pointerEvents = 'auto';
                canvas.style.cursor = (hit.handle === 'h1' || hit.handle === 'h2') ? 'pointer' : 'move';
            } else if (selectedIdx === -1) {
                canvas.style.pointerEvents = 'none';
            }
        } else if (currentTool === 'eraser') {
            const hit = hitTest(mouseX, mouseY);
            canvas.style.cursor = (hit.idx !== -1) ? 'pointer' : 'crosshair';
        }
    });

    canvas.addEventListener('mousedown', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        if (currentTool === 'eraser') {
            const hit = hitTest(mouseX, mouseY);
            if (hit.idx !== -1) {
                drawings.splice(hit.idx, 1);
                selectedIdx = -1;
                updateSelectionUI();
                saveAndRedraw();
            }
            return;
        }

        if (currentTool === 'cursor') {
            const hit = hitTest(mouseX, mouseY);
            if (hit.idx !== -1) {
                selectedIdx = hit.idx;
                activeHandle = hit.handle;
                isDragging = true;
                startPx = { x: mouseX, y: mouseY };
                dragOrigObj = JSON.parse(JSON.stringify(drawings[selectedIdx]));
                canvas.style.pointerEvents = 'auto';
                updateSelectionUI();
                redrawAll();
            } else {
                selectedIdx = -1;
                activeHandle = null;
                updateSelectionUI();
                redrawAll();
                canvas.style.pointerEvents = 'none';
            }
            return;
        }

        if (currentTool === 'text') {
            textOverlay.style.left = mouseX + 'px';
            textOverlay.style.top = mouseY + 'px';
            textOverlay.style.display = 'block';
            textInput.value = '';
            textInput.focus();
            startPx = { x: mouseX, y: mouseY };
            return;
        }

        isDrawing = true;
        startPx = { x: mouseX, y: mouseY };
        currentPx = { ...startPx };
        if (currentTool === 'pen') {
            penPoints = [{ x: mouseX, y: mouseY }];
        }
    });

    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const val = textInput.value.trim();
            if (val && startPx && mainSeries) {
                const t1 = mainChart.timeScale().coordinateToTime(startPx.x);
                const p1 = mainSeries.coordinateToPrice(startPx.y);
                if (p1 !== null) {
                    drawings.push({
                        tool: 'text',
                        text: val,
                        t1: t1 || 0,
                        p1: p1,
                        color: '#ffffff'
                    });
                    saveAndRedraw();
                }
            }
            textOverlay.style.display = 'none';
            setTool('cursor');
        } else if (e.key === 'Escape') {
            textOverlay.style.display = 'none';
        }
    });

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        if (isDragging && selectedIdx !== -1 && dragOrigObj && mainSeries) {
            const dx = mouseX - startPx.x;
            const dy = mouseY - startPx.y;
            const d = drawings[selectedIdx];
            const tScale = mainChart.timeScale();

            if (activeHandle === 'h1') {
                const curOrig = getScreenCoords(dragOrigObj);
                d.t1 = tScale.coordinateToTime(curOrig.x1 + dx) || d.t1;
                d.p1 = mainSeries.coordinateToPrice(curOrig.y1 + dy) || d.p1;
            } else if (activeHandle === 'h2') {
                const curOrig = getScreenCoords(dragOrigObj);
                d.t2 = tScale.coordinateToTime(curOrig.x2 + dx) || d.t2;
                d.p2 = mainSeries.coordinateToPrice(curOrig.y2 + dy) || d.p2;
            } else if (activeHandle === 'body') {
                const curOrig = getScreenCoords(dragOrigObj);
                if (curOrig.x1 !== null && curOrig.y1 !== null) {
                    d.t1 = tScale.coordinateToTime(curOrig.x1 + dx) || d.t1;
                    d.p1 = mainSeries.coordinateToPrice(curOrig.y1 + dy) || d.p1;
                }
                if (curOrig.x2 !== null && curOrig.y2 !== null) {
                    d.t2 = tScale.coordinateToTime(curOrig.x2 + dx) || d.t2;
                    d.p2 = mainSeries.coordinateToPrice(curOrig.y2 + dy) || d.p2;
                }
                if (d.tool === 'horz') {
                    d.fixedY = (dragOrigObj.fixedY || curOrig.y1) + dy;
                }
            }
            redrawAll();
            return;
        }

        if (!isDrawing) return;
        currentPx = { x: mouseX, y: mouseY };
        if (currentTool === 'pen') {
            penPoints.push({ x: mouseX, y: mouseY });
        }
        redrawAll();
        drawPreview();
    });

    canvas.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            activeHandle = null;
            dragOrigObj = null;
            saveAndRedraw();
            return;
        }

        if (!isDrawing) return;
        isDrawing = false;

        if (startPx && currentPx && mainSeries) {
            const tScale = mainChart.timeScale();
            const t1 = tScale.coordinateToTime(startPx.x);
            const t2 = tScale.coordinateToTime(currentPx.x);
            const p1 = mainSeries.coordinateToPrice(startPx.y);
            const p2 = mainSeries.coordinateToPrice(currentPx.y);

            if (currentTool === 'pen') {
                const pts = penPoints.map(pt => ({
                    t: tScale.coordinateToTime(pt.x) || 0,
                    p: mainSeries.coordinateToPrice(pt.y) || 0
                }));
                if (pts.length > 1) {
                    drawings.push({ tool: 'pen', points: pts, color: '#f5c518' });
                    saveAndRedraw();
                }
                penPoints = [];
            } else if (p1 !== null) {
                drawings.push({
                    tool: currentTool,
                    t1: t1 || 0,
                    p1: p1,
                    t2: t2 || 0,
                    p2: p2 !== null ? p2 : p1,
                    fixedY: startPx.y,
                    color: '#00FFA3'
                });
                saveAndRedraw();
            }
        }
        setTool('cursor');
    });

    function drawPreview() {
        if (!startPx || !currentPx) return;
        ctx.save();
        ctx.strokeStyle = '#00FFA3';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);

        if (currentTool === 'trend' || currentTool === 'fib_ext') {
            ctx.beginPath();
            ctx.moveTo(startPx.x, startPx.y);
            ctx.lineTo(currentPx.x, currentPx.y);
            ctx.stroke();
        } else if (currentTool === 'horz') {
            ctx.beginPath();
            ctx.moveTo(0, currentPx.y);
            ctx.lineTo(canvas.width, currentPx.y);
            ctx.stroke();
        } else if (currentTool === 'box') {
            const w = currentPx.x - startPx.x;
            const h = currentPx.y - startPx.y;
            ctx.fillStyle = 'rgba(0, 255, 163, 0.15)';
            ctx.fillRect(startPx.x, startPx.y, w, h);
            ctx.strokeRect(startPx.x, startPx.y, w, h);
        } else if (currentTool === 'pos_long' || currentTool === 'pos_short') {
            const w = currentPx.x - startPx.x;
            const h = currentPx.y - startPx.y;
            const isLong = currentTool === 'pos_long';
            ctx.fillStyle = isLong ? 'rgba(8, 153, 129, 0.25)' : 'rgba(242, 54, 69, 0.25)';
            ctx.fillRect(startPx.x, startPx.y, w, h / 2);
            ctx.fillStyle = isLong ? 'rgba(242, 54, 69, 0.25)' : 'rgba(8, 153, 129, 0.25)';
            ctx.fillRect(startPx.x, startPx.y + h / 2, w, h / 2);
            ctx.strokeRect(startPx.x, startPx.y, w, h);
        } else if (currentTool === 'price_range' || currentTool === 'date_range') {
            const w = currentPx.x - startPx.x;
            const h = currentPx.y - startPx.y;
            ctx.fillStyle = 'rgba(41, 98, 255, 0.2)';
            ctx.fillRect(startPx.x, startPx.y, w, h);
            ctx.strokeStyle = '#2962ff';
            ctx.strokeRect(startPx.x, startPx.y, w, h);
        } else if (currentTool === 'circle') {
            const r = ptDist(startPx.x, startPx.y, currentPx.x, currentPx.y);
            ctx.beginPath();
            ctx.arc(startPx.x, startPx.y, r, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(239, 83, 80, 0.12)';
            ctx.fill();
            ctx.stroke();
        } else if (currentTool === 'fib') {
            const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
            levels.forEach(lvl => {
                const y = startPx.y + (currentPx.y - startPx.y) * lvl;
                ctx.beginPath();
                ctx.moveTo(startPx.x, y);
                ctx.lineTo(currentPx.x + 80, y);
                ctx.stroke();
            });
        } else if (currentTool === 'pen' && penPoints.length > 1) {
            ctx.setLineDash([]);
            ctx.strokeStyle = '#f5c518';
            ctx.beginPath();
            ctx.moveTo(penPoints[0].x, penPoints[0].y);
            for (let p of penPoints) ctx.lineTo(p.x, p.y);
            ctx.stroke();
        }
        ctx.restore();
    }

    // ฟังก์ชันคำนวณและวาด Auto Fib Retracement
    function drawAutoFib() {
        if (!autoFibEnable || !autoFibEnable.checked || !mainSeries) return;
        const rawSeries = mainConfig.series.find(s => s.type === "Candlestick" && s.data);
        if (!rawSeries || !rawSeries.data || rawSeries.data.length === 0) return;

        const lookback = parseInt(autoFibLookback?.value || 120, 10);
        const data = rawSeries.data;
        const slice = data.slice(-Math.min(data.length, lookback));
        if (slice.length < 2) return;

        let hi = -Infinity, lo = Infinity;
        let timeHi = null, timeLo = null;
        slice.forEach(bar => {
            if (bar.high > hi) { hi = bar.high; timeHi = bar.time; }
            if (bar.low < lo) { lo = bar.low; timeLo = bar.time; }
        });

        const uptrend = timeLo <= timeHi;
        const diff = hi - lo;
        const ratios = [
            { r: 0.0, c: '#787b86', lbl: '0.0%' },
            { r: 0.236, c: '#f23645', lbl: '23.6%' },
            { r: 0.382, c: '#ff9800', lbl: '38.2%' },
            { r: 0.5, c: '#4caf50', lbl: '50.0%' },
            { r: 0.618, c: '#00bcd4', lbl: '61.8% (Golden)' },
            { r: 0.786, c: '#2196f3', lbl: '78.6%' },
            { r: 1.0, c: '#787b86', lbl: '100%' }
        ];

        const tScale = mainChart.timeScale();
        const x0 = tScale.timeToCoordinate(slice[0].time);
        const x1 = tScale.timeToCoordinate(slice[slice.length - 1].time);
        if (x0 === null || x1 === null) return;

        ctx.save();
        
        if (autoFibGp && autoFibGp.checked) {
            const y618 = mainSeries.priceToCoordinate(uptrend ? (hi - diff * 0.618) : (lo + diff * 0.618));
            const y65 = mainSeries.priceToCoordinate(uptrend ? (hi - diff * 0.65) : (lo + diff * 0.65));
            if (y618 !== null && y65 !== null) {
                ctx.fillStyle = 'rgba(0, 188, 212, 0.12)';
                ctx.fillRect(Math.min(x0, x1), Math.min(y618, y65), Math.abs(x1 - x0) + 120, Math.abs(y65 - y618));
            }
        }

        ratios.forEach(lvl => {
            const price = uptrend ? (hi - diff * lvl.r) : (lo + diff * lvl.r);
            const y = mainSeries.priceToCoordinate(price);
            if (y === null) return;

            ctx.strokeStyle = lvl.c;
            ctx.lineWidth = (lvl.r === 0.5 || lvl.r === 0.618) ? 1.5 : 1;
            ctx.setLineDash(lvl.r === 0 || lvl.r === 1 ? [] : [3, 3]);
            
            ctx.beginPath();
            ctx.moveTo(Math.min(x0, x1), y);
            ctx.lineTo(Math.max(x0, x1) + 120, y);
            ctx.stroke();

            ctx.fillStyle = lvl.c;
            ctx.font = '10px Roboto Mono, monospace';
            ctx.fillText(`${lvl.lbl} (${price.toFixed(2)})`, Math.max(x0, x1) + 125, y + 3);
        });

        ctx.restore();
    }

    function drawHandle(x, y) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = '#00FFA3';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
    }

    function redrawAll() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (!mainSeries) return;

        // วาด Auto Fib Retracement
        drawAutoFib();

        const tScale = mainChart.timeScale();

        drawings.forEach((d, idx) => {
            const isSelected = (idx === selectedIdx);
            ctx.save();
            ctx.strokeStyle = isSelected ? '#00e5ff' : (d.color || '#00FFA3');
            ctx.lineWidth = isSelected ? 2.5 : 2;

            const pts = getScreenCoords(d);
            const { x1, y1, x2, y2 } = pts;

            if (d.tool === 'horz') {
                const targetY = y1 !== null ? y1 : d.fixedY;
                if (targetY !== null) {
                    ctx.beginPath();
                    ctx.moveTo(0, targetY);
                    ctx.lineTo(canvas.width, targetY);
                    ctx.stroke();
                    if (isSelected) drawHandle(canvas.width / 2, targetY);
                }
            } else if (d.tool === 'trend' || d.tool === 'fib_ext') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                    if (isSelected) { drawHandle(x1, y1); drawHandle(x2, y2); }
                }
            } else if (d.tool === 'box') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const w = x2 - x1, h = y2 - y1;
                    ctx.fillStyle = isSelected ? 'rgba(0, 229, 255, 0.18)' : 'rgba(0, 255, 163, 0.15)';
                    ctx.fillRect(x1, y1, w, h);
                    ctx.strokeRect(x1, y1, w, h);
                    if (isSelected) { drawHandle(x1, y1); drawHandle(x2, y2); }
                }
            } else if (d.tool === 'pos_long' || d.tool === 'pos_short') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const w = x2 - x1;
                    const h = y2 - y1;
                    const isLong = d.tool === 'pos_long';
                    const midY = (y1 + y2) / 2;

                    ctx.fillStyle = isLong ? 'rgba(8, 153, 129, 0.28)' : 'rgba(242, 54, 69, 0.28)';
                    ctx.fillRect(x1, y1, w, midY - y1);
                    ctx.strokeStyle = isLong ? '#089981' : '#f23645';
                    ctx.strokeRect(x1, y1, w, midY - y1);

                    ctx.fillStyle = isLong ? 'rgba(242, 54, 69, 0.28)' : 'rgba(8, 153, 129, 0.28)';
                    ctx.fillRect(x1, midY, w, y2 - midY);
                    ctx.strokeStyle = isLong ? '#f23645' : '#089981';
                    ctx.strokeRect(x1, midY, w, y2 - midY);

                    const tpPrice = d.p1;
                    const slPrice = d.p2;
                    const entryPrice = (d.p1 + d.p2) / 2;
                    const risk = Math.abs(entryPrice - slPrice);
                    const reward = Math.abs(tpPrice - entryPrice);
                    const rr = risk > 0 ? (reward / risk).toFixed(2) : '0.00';

                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 11px Roboto Mono, monospace';
                    ctx.fillText(`Target: ${tpPrice.toFixed(2)} | R:R: ${rr}`, x1 + 6, Math.min(y1, y2) + 16);
                    ctx.fillText(`Stop: ${slPrice.toFixed(2)}`, x1 + 6, Math.max(y1, y2) - 8);

                    if (isSelected) { drawHandle(x1, y1); drawHandle(x2, y2); drawHandle((x1+x2)/2, midY); }
                }
            } else if (d.tool === 'price_range' || d.tool === 'date_range') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const w = x2 - x1, h = y2 - y1;
                    ctx.fillStyle = 'rgba(41, 98, 255, 0.2)';
                    ctx.fillRect(x1, y1, w, h);
                    ctx.strokeStyle = '#2962ff';
                    ctx.strokeRect(x1, y1, w, h);

                    const diffPrice = Math.abs(d.p2 - d.p1);
                    const pctPrice = ((diffPrice / d.p1) * 100).toFixed(2);
                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 11px Roboto Mono, monospace';
                    ctx.fillText(`Δ ${diffPrice.toFixed(2)} (${pctPrice}%)`, x1 + 6, y1 + 16);
                    if (isSelected) { drawHandle(x1, y1); drawHandle(x2, y2); }
                }
            } else if (d.tool === 'circle') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const r = ptDist(x1, y1, x2, y2);
                    ctx.beginPath();
                    ctx.arc(x1, y1, r, 0, Math.PI * 2);
                    ctx.fillStyle = isSelected ? 'rgba(0, 229, 255, 0.18)' : 'rgba(239, 83, 80, 0.12)';
                    ctx.fill();
                    ctx.stroke();
                    if (isSelected) { drawHandle(x1, y1); drawHandle(x2, y2); }
                }
            } else if (d.tool === 'fib') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const levels = [
                        { r: 0.0, c: '#787b86' },
                        { r: 0.236, c: '#f23645' },
                        { r: 0.382, c: '#ff9800' },
                        { r: 0.5, c: '#4caf50' },
                        { r: 0.618, c: '#089981' },
                        { r: 0.786, c: '#00bcd4' },
                        { r: 1.0, c: '#787b86' }
                    ];
                    const maxX = Math.max(x1, x2) + 140;
                    const minX = Math.min(x1, x2);
                    levels.forEach(lvl => {
                        const curY = y1 + (y2 - y1) * lvl.r;
                        ctx.strokeStyle = lvl.c;
                        ctx.beginPath();
                        ctx.moveTo(minX, curY);
                        ctx.lineTo(maxX, curY);
                        ctx.stroke();

                        ctx.fillStyle = lvl.c;
                        ctx.font = '10px Roboto Mono, monospace';
                        ctx.fillText(lvl.r + ' (' + (mainSeries.coordinateToPrice(curY)?.toFixed(2) || '') + ')', maxX - 65, curY - 3);
                    });
                    if (isSelected) { drawHandle(x1, y1); drawHandle(x2, y2); }
                }
            } else if (d.tool === 'text') {
                if (x1 !== null && y1 !== null) {
                    ctx.fillStyle = isSelected ? '#00e5ff' : '#ffffff';
                    ctx.font = 'bold 13px -apple-system, sans-serif';
                    ctx.fillText(d.text, x1, y1);
                    if (isSelected) drawHandle(x1 - 6, y1 - 4);
                }
            } else if (d.tool === 'pen' && d.points) {
                ctx.strokeStyle = isSelected ? '#00e5ff' : (d.color || '#f5c518');
                ctx.beginPath();
                let started = false;
                for (let pt of d.points) {
                    const px = tScale.timeToCoordinate(pt.t);
                    const py = mainSeries.priceToCoordinate(pt.p);
                    if (px !== null && py !== null) {
                        if (!started) { ctx.moveTo(px, py); started = true; }
                        else ctx.lineTo(px, py);
                    }
                }
                ctx.stroke();
            }
            ctx.restore();
        });
    }

    mainChart.timeScale().subscribeVisibleTimeRangeChange(redrawAll);
    mainChart.timeScale().subscribeVisibleLogicalRangeChange(redrawAll);

    // Pane & Header Control
    const paneRegistry = [];
    let _spDrag = null;

    function _spRedrawHooks() {
        ['resizeCanvas','redrawAll','drawAll','renderDrawings','redraw']
        .forEach(fn => { if (typeof window[fn] === 'function') { try { window[fn](); } catch(e) {} } });
    }

    function paneResizeAll() {
        paneRegistry.forEach(p => {
            if (!p.chart || !p.boxEl || !p.viewEl) return;
            if (p.boxEl.dataset.collapsed) return;
            const h = Math.max(30, p.boxEl.clientHeight);
            const w = p.boxEl.clientWidth || p.viewEl.clientWidth;
            p.viewEl.style.height = h + 'px';
            try { p.chart.applyOptions({ width: w, height: h }); } catch(e) {}
        });
        _spRedrawHooks();
    }

    function initPaneDrag(e, upperId, lowerId) {
        e.preventDefault();
        const up = document.getElementById(upperId);
        const low = lowerId ? document.getElementById(lowerId) : null;
        if (!up) return;
        _spDrag = {
            up: up,
            low: low,
            bar: e.currentTarget,
            y: e.clientY,
            uh: up.clientHeight,
            lh: low ? low.clientHeight : 0,
            isBottom: !low
        };
        e.currentTarget.classList.add('dragging');
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none';
        window.addEventListener('mousemove', onPaneDrag);
        window.addEventListener('mouseup', stopPaneDrag);
    }

    function onPaneDrag(e) {
        if (!_spDrag) return;
        const dy = e.clientY - _spDrag.y;
        if (_spDrag.isBottom) {
            _spDrag.up.style.flex = 'none';
            _spDrag.up.style.overflow = 'hidden';
            const newH = Math.max(40, _spDrag.uh + dy);
            _spDrag.up.style.height = newH + 'px';
            const hdr = _spDrag.up.querySelector('.pane-header');
            const hdrH = hdr ? hdr.offsetHeight : 0;
            const view = _spDrag.up.querySelector('.chart-view') || _spDrag.up.children[0];
            if (view) view.style.height = Math.max(20, newH - hdrH) + 'px';
            if (typeof container !== 'undefined' && container) container.style.height = 'auto';
        } else {
            _spDrag.up.style.flex = 'none';
            _spDrag.low.style.flex = 'none';
            _spDrag.up.style.height = Math.max(80, _spDrag.uh + dy) + 'px';
            _spDrag.low.style.height = Math.max(46, _spDrag.lh - dy) + 'px';
        }
        paneResizeAll();
        if (typeof resizeCanvas === 'function') resizeCanvas();
        if (window.Streamlit && typeof window.Streamlit.setFrameHeight === 'function') {
            window.Streamlit.setFrameHeight();
        }
    }

    function stopPaneDrag() {
        if (_spDrag && _spDrag.bar) _spDrag.bar.classList.remove('dragging');
        _spDrag = null;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        window.removeEventListener('mousemove', onPaneDrag);
        window.removeEventListener('mouseup', stopPaneDrag);
        paneResizeAll();
    }

    function togglePaneVisibility(key) {
        const p = paneRegistry.find(r => r.key === key);
        if (!p) return;
        const hidden = p.viewEl.style.visibility === 'hidden';
        p.viewEl.style.visibility = hidden ? 'visible' : 'hidden';
        const b = p.headerEl && p.headerEl.querySelector('[data-act="eye"]');
        if (b) {
            b.textContent = hidden ? '👁' : '🚫';
            b.classList.toggle('off', !hidden);
        }
    }

    function togglePaneCollapse(boxId) {
        const p = paneRegistry.find(r => r.boxEl && r.boxEl.id === boxId);
        if (!p) return;
        const box = p.boxEl;
        if (!box.dataset.collapsed) {
            box.dataset.prevH = box.clientHeight + 'px';
            box.dataset.collapsed = '1';
            p.viewEl.style.display = 'none';
            box.style.flex = 'none';
            box.style.height = '28px';
        } else {
            delete box.dataset.collapsed;
            p.viewEl.style.display = '';
            box.style.height = box.dataset.prevH || '140px';
        }
        paneResizeAll();
    }

    function closePaneBox(boxId) {
        const p = paneRegistry.find(r => r.boxEl && r.boxEl.id === boxId);
        if (!p) return;
        p.boxEl.style.display = 'none';
        if (p.splitterEl) p.splitterEl.style.display = 'none';
        paneResizeAll();
    }

    function _spBuildHeader(key, title, boxId, canClose) {
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
    }

    function upgradePanes(titles) {
        titles = titles || [];
        const mainBox = document.getElementById('main-pane-container');
        const mainView = document.getElementById('chart-main');
        if (mainBox && mainView && !mainBox.dataset.spUpgraded) {
            mainBox.dataset.spUpgraded = '1';
            if (!mainBox.style.height) mainBox.style.height = mainView.clientHeight + 'px';
            const hdr = _spBuildHeader('main', titles[0] || 'MAIN CHART', 'main-pane-container', false);
            mainBox.appendChild(hdr);
            paneRegistry.push({
                key: 'main', chart: (typeof allCharts !== 'undefined' ? allCharts[0] : null),
                viewEl: mainView, boxEl: mainBox, headerEl: hdr, splitterEl: null
            });
        }

        const subs = Array.from(document.querySelectorAll('#sub-panes > .sub-pane'));
        subs.forEach((pane, i) => {
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

            paneRegistry.push({
                key: 'sub' + i, chart: (typeof allCharts !== 'undefined' ? allCharts[i + 1] : null),
                viewEl: pane, boxEl: box, headerEl: hdr, splitterEl: sp
            });
        });

        const lastPane = paneRegistry[paneRegistry.length - 1];
        if (lastPane && lastPane.boxEl && !document.getElementById('splitter-bar-bottom')) {
            const botSp = document.createElement('div');
            botSp.id = 'splitter-bar-bottom';
            botSp.className = 'splitter-bar';
            lastPane.boxEl.parentNode.appendChild(botSp);
            botSp.addEventListener('mousedown', e => initPaneDrag(e, lastPane.boxEl.id, null));
        }
        paneResizeAll();
    }

    function updateAllWidths() {
        const newW = container.clientWidth || window.innerWidth;
        allCharts.forEach(c => c.applyOptions({ width: newW }));
        resizeCanvas();
    }

    const paneTitles = config.map((c, i) => c.title || (i === 0 ? 'MAIN CHART' : ('PANE ' + i)));
    upgradePanes(paneTitles);

    let vLine = document.getElementById('global-sync-vline');
    let vBadge = document.getElementById('global-sync-vbadge');
    const chartWrap = (typeof mainBox !== 'undefined' && mainBox && mainBox.parentElement) ? mainBox.parentElement : document.body;
    
    if (!vLine && chartWrap) {
        vLine = document.createElement('div');
        vLine.id = 'global-sync-vline';
        vLine.style.cssText = 'position:absolute;top:0;bottom:0;width:0px;border-left:1px dashed rgba(255,255,255,0.45);pointer-events:none;z-index:80;display:none;';
        chartWrap.style.position = 'relative';
        chartWrap.appendChild(vLine);
    }

    if (!vBadge && chartWrap) {
        vBadge = document.createElement('div');
        vBadge.id = 'global-sync-vbadge';
        vBadge.style.cssText = 'position:absolute;bottom:2px;transform:translateX(-50%);background:#1e222d;color:#d1d4dc;border:1px solid #363a45;border-radius:2px;padding:2px 6px;font-size:11px;font-family:-apple-system,BlinkMacSystemFont,"Trebuchet MS",Roboto,sans-serif;pointer-events:none;z-index:95;display:none;white-space:nowrap;line-height:16px;box-shadow:0 2px 5px rgba(0,0,0,0.6);font-weight:500;';
        chartWrap.appendChild(vBadge);
    }

    const _thMonths = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
    function _fmtTimeBadge(t) {
        if (!t) return '';
        let dt;
        if (typeof t === 'number') {
            dt = new Date(t * 1000);
        } else if (t.year && t.month && t.day) {
            dt = new Date(Date.UTC(t.year, t.month - 1, t.day));
        } else {
            return '';
        }
        const d = dt.getUTCDate();
        const m = _thMonths[dt.getUTCMonth()];
        const y = String(dt.getUTCFullYear() % 100).padStart(2, '0');
        const hh = String(dt.getUTCHours()).padStart(2, '0');
        const mm = String(dt.getUTCMinutes()).padStart(2, '0');
        return d + ' ' + m + " '" + y + '  ' + hh + ':' + mm;
    }

    allCharts.forEach(c => {
        c.subscribeCrosshairMove(param => {
            if (!vLine) return;
            if (!param || !param.point || param.point.x === undefined || !param.time) {
                vLine.style.display = 'none';
                if (vBadge) vBadge.style.display = 'none';
            } else {
                const offLeft = (typeof mainView !== 'undefined' && mainView && chartWrap) ? (mainView.getBoundingClientRect().left - chartWrap.getBoundingClientRect().left) : 0;
                const posX = (param.point.x + offLeft) + 'px';
                vLine.style.left = posX;
                vLine.style.display = 'block';
                if (vBadge) {
                    vBadge.style.left = posX;
                    vBadge.innerText = _fmtTimeBadge(param.time);
                    vBadge.style.display = 'block';
                }
            }
        });
    });

    window.addEventListener('resize', updateAllWidths);
    window.addEventListener('resize', () => { try { paneResizeAll(); } catch(e) {} });
    setTimeout(updateAllWidths, 100);
    setTimeout(paneResizeAll, 150);
    setTimeout(updateAllWidths, 300);
    setTimeout(paneResizeAll, 350);
})();