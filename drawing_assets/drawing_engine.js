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

    canvas.width = initWidth;
    canvas.height = mainH;

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

    // =========================================================================
    // เชื่อมต่อ Live WebSocket Ticking สำหรับ Binance (เพิ่มแท่งเทียนต่อท้ายแบบเรียลไทม์)
    // =========================================================================
    try {
        if (window.__activeWs) {
            try { window.__activeWs.close(); } catch(e) {}
            window.__activeWs = null;
        }
        const wmText = (mainConfig.chart?.watermark?.text || '').toUpperCase();
        let sym = "";
        let tf = "1h";
        if (wmText.includes('•')) {
            const parts = wmText.split('•');
            sym = parts[0].trim();
            tf = parts[1].trim().toLowerCase();
        } else if (wmText) {
            sym = wmText.split(' ')[0].trim();
        }

        if (sym && (sym.endsWith('USDT') || sym.endsWith('BUSD') || sym.endsWith('USDC')) && mainSeries) {
            const wsInterval = (tf.endsWith('m') || tf.endsWith('h') || tf.endsWith('d') || tf.endsWith('w')) ? tf : '1h';
            const wsUrl = `wss://stream.binance.com:9443/ws/${sym.toLowerCase()}@kline_${wsInterval}`;
            const ws = new WebSocket(wsUrl);
            window.__activeWs = ws;

            ws.onmessage = function(event) {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg && msg.k) {
                        const k = msg.k;
                        const liveBar = {
                            time: Math.floor(k.t / 1000),
                            open: parseFloat(k.o),
                            high: parseFloat(k.h),
                            low: parseFloat(k.l),
                            close: parseFloat(k.c)
                        };
                        // อัปเดตแท่งเทียนปัจจุบัน หรือดันแท่งใหม่ต่อท้ายแบบ TradingView ทันที
                        mainSeries.update(liveBar);

                        const diff = liveBar.close - liveBar.open;
                        const pct = liveBar.open !== 0 ? (diff / liveBar.open) * 100 : 0;
                        const isUp = liveBar.close >= liveBar.open;
                        const color = isUp ? '#089981' : '#F23645';

                        const pEl = document.getElementById('leg-price');
                        const cEl = document.getElementById('leg-change');
                        if (pEl) {
                            pEl.textContent = liveBar.close.toLocaleString('en-US', {minimumFractionDigits: 2});
                            pEl.style.color = color;
                        }
                        if (cEl) {
                            cEl.textContent = (diff >= 0 ? '+' : '') + pct.toFixed(2) + '%';
                            cEl.style.color = color;
                        }
                        const sVal = document.getElementById('qt-sell-val');
                        const bVal = document.getElementById('qt-buy-val');
                        if (sVal) sVal.textContent = liveBar.close.toLocaleString('en-US', {minimumFractionDigits: 2});
                        if (bVal) bVal.textContent = (liveBar.close * 1.0001).toLocaleString('en-US', {minimumFractionDigits: 2});
                    }
                } catch(err) {}
            };
        }
    } catch(e) {}

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

    if (dragHandle && toolbar) {
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
    }

    const rangeStorageKey = 'tv_chart_range_' + (mainConfig.chart?.watermark?.text || 'default');
    let isSyncing = false;
    allCharts.forEach((c, idx) => {
        c.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (!range) return;
            if (idx === 0) {
                try { sessionStorage.setItem(rangeStorageKey, JSON.stringify(range)); } catch(e) {}
            }
            if (isSyncing) return;
            isSyncing = true;
            allCharts.forEach((other, oIdx) => {
                if (idx !== oIdx) {
                    try { other.timeScale().setVisibleLogicalRange(range); } catch(err) {}
                }
            });
            isSyncing = false;
        });
    });

    // กู้คืนระดับการซูมและตำแหน่งเลื่อน เพื่อป้องกันไม่ให้กราฟกระโดดกลับ
    try {
        const savedRange = sessionStorage.getItem(rangeStorageKey);
        if (savedRange) {
            const parsedRange = JSON.parse(savedRange);
            if (parsedRange && parsedRange.from !== undefined && parsedRange.to !== undefined) {
                mainChart.timeScale().setVisibleLogicalRange(parsedRange);
            }
        }
    } catch(e) {}

    const storageKey = 'tv_vector_drawings_' + (mainConfig.chart?.watermark?.text || 'default');
    let drawings = [];
    try {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed)) {
                drawings = parsed.filter(d => d && d.tool && (d.p1 !== undefined || d.points || d.l1 !== undefined));
            }
        }
    } catch (e) {}

    let currentTool = 'cursor';
    let selectedIdx = -1;
    let activeHandle = null;
    let isDragging = false;
    let isDrawing = false;
    let startPx = null;
    let currentPx = null;
    let penPoints = [];
    let fibClickPoints = [];
    let extPoints = [];
    let tzPoints = [];
    let patternClickPoints = [];
    let dragOrigObj = null;

    function getLogicalFromX(x) {
        if (!mainChart) return 0;
        const logical = mainChart.timeScale().coordinateToLogical(x);
        return logical !== null ? logical : 0;
    }

    function getPriceFromY(y) {
        if (!mainSeries) return 0;
        const p = mainSeries.coordinateToPrice(y);
        return p !== null ? p : 0;
    }

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
        fibClickPoints = [];
        extPoints = [];
        tzPoints = [];
        patternClickPoints = [];
        isDrawing = false;

        document.querySelectorAll('.tool-btn, .sub-item').forEach(el => {
            el.classList.remove('active', 'eraser-active');
        });

        if (tool === 'cursor') {
            const btn = document.getElementById('btn-cursor');
            if (btn) btn.classList.add('active');
        } else if (toolBtns && toolBtns[tool]) {
            toolBtns[tool].classList.add(tool === 'eraser' ? 'eraser-active' : 'active');
        } else {
            const sub = document.querySelector(`[data-tool="${tool}"]`);
            if (sub) {
                sub.classList.add('active');
                const parent = sub.closest('.tool-btn');
                if (parent) parent.classList.add('active');
            }
        }

        const fibTools = ['fib', 'fib_ext', 'fib_tz'];
        const patTools = ['head_shoulders', 'triangle', 'elliott_impulse', 'elliott_abc', 'pat_xabcd', 'pat_cypher', 'pat_threedrives', 'pat_abcd', 'elliott_triangle', 'elliott_double', 'elliott_triple', 'cycle_lines', 'time_cycles', 'sine_line'];
        const calcTools = ['pos_long', 'pos_short', 'price_range', 'date_range'];
        
        const bFib = document.getElementById('btn-fib-group');
        const bPat = document.getElementById('btn-pattern-group');
        const bCalc = document.getElementById('btn-calc-group');
        if (bFib) bFib.classList.toggle('active', fibTools.includes(tool));
        if (bPat) bPat.classList.toggle('active', (window.PatternTool && window.PatternTool.isPatternTool(tool)) || patTools.includes(tool));
        if (bCalc) bCalc.classList.toggle('active', calcTools.includes(tool));

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
    window.setTool = setTool;

    Object.keys(toolBtns).forEach(tool => {
        if (toolBtns[tool]) {
            toolBtns[tool].addEventListener('click', (e) => {
                e.stopPropagation();
                document.querySelectorAll('.tool-item-wrap').forEach(w => w.classList.remove('open'));
                setTool(tool);
            });
        }
    });

    const toolItemWraps = document.querySelectorAll('.tool-item-wrap');
    toolItemWraps.forEach(wrap => {
        const btn = wrap.querySelector('.tool-btn.has-sub');
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const wasOpen = wrap.classList.contains('open');
                toolItemWraps.forEach(w => w.classList.remove('open'));
                if (!wasOpen) {
                    wrap.classList.add('open');
                }
            });
        }
    });

    document.querySelectorAll('.sub-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const chosen = item.dataset.tool;
            const wrap = item.closest('.tool-item-wrap');
            if (wrap) wrap.classList.remove('open');
            if (chosen) setTool(chosen);
        });
    });

    window.addEventListener('click', (e) => {
        if (!e.target.closest('.tool-item-wrap')) {
            toolItemWraps.forEach(w => w.classList.remove('open'));
        }
    });

    function updateSelectionUI() {
        if (!btnDeleteSelected) return;
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

    if (btnDeleteSelected) {
        btnDeleteSelected.addEventListener('click', () => {
            if (selectedIdx >= 0 && selectedIdx < drawings.length) {
                deleteSelected();
            } else {
                setTool('eraser');
            }
        });
    }

    const btnUndo = document.getElementById('btn-undo');
    if (btnUndo) {
        btnUndo.addEventListener('click', () => {
            drawings.pop();
            selectedIdx = -1;
            updateSelectionUI();
            saveAndRedraw();
        });
    }

    const btnClear = document.getElementById('btn-clear');
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            drawings = [];
            fibClickPoints = [];
            extPoints = [];
            tzPoints = [];
            patternClickPoints = [];
            selectedIdx = -1;
            updateSelectionUI();
            try { localStorage.removeItem(storageKey); } catch(e) {}
            redrawAll();
        });
    }

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            fibClickPoints = [];
            extPoints = [];
            tzPoints = [];
            patternClickPoints = [];
            isDrawing = false;
            const fMod = document.getElementById('fib-settings-modal');
            const pMod = document.getElementById('pattern-settings-modal');
            if (fMod) fMod.classList.remove('open');
            if (pMod) pMod.classList.remove('open');
            redrawAll();
            setTool('cursor');
        } else if ((e.key === 'Delete' || e.key === 'Backspace') && selectedIdx !== -1) {
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
        const w = mainPaneBox.clientWidth || container.clientWidth || window.innerWidth;
        const h = mainPaneBox.clientHeight || mainH;
        if (w > 0 && h > 0 && (canvas.width !== w || canvas.height !== h)) {
            canvas.width = w;
            canvas.height = h;
        }
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

    function safeCoordX(l, t) {
        const tScale = mainChart.timeScale();
        if (l !== undefined && l !== null) {
            try {
                const cx = tScale.logicalToCoordinate(l);
                if (cx !== null && !isNaN(cx)) return cx;
            } catch(e) {}
        }
        if (t !== undefined && t !== null && t !== 0 && t !== '') {
            try {
                const cx = tScale.timeToCoordinate(t);
                if (cx !== null && !isNaN(cx)) return cx;
            } catch(e) {}
        }
        return null;
    }

    function getScreenCoords(d) {
        const x1 = safeCoordX(d.l1, d.t1);
        const x2 = safeCoordX(d.l2, d.t2);
        const x3 = safeCoordX(d.l3, d.t3);
        const y1 = (d.p1 !== undefined && d.p1 !== null) ? mainSeries.priceToCoordinate(d.p1) : null;
        const y2 = (d.p2 !== undefined && d.p2 !== null) ? mainSeries.priceToCoordinate(d.p2) : null;
        const y3 = (d.p3 !== undefined && d.p3 !== null) ? mainSeries.priceToCoordinate(d.p3) : null;
        return { x1, y1, x2, y2, x3, y3 };
    }

    function hitTest(x, y) {
        if (!mainSeries) return { idx: -1, handle: null };
        if (selectedIdx !== -1 && drawings[selectedIdx]) {
            const d = drawings[selectedIdx];
            const pts = getScreenCoords(d);
            if (pts.x1 !== null && pts.y1 !== null && ptDist(x, y, pts.x1, pts.y1) < 12) return { idx: selectedIdx, handle: 'h1' };
            if (pts.x2 !== null && pts.y2 !== null && ptDist(x, y, pts.x2, pts.y2) < 12) return { idx: selectedIdx, handle: 'h2' };
            if (pts.x3 !== null && pts.y3 !== null && ptDist(x, y, pts.x3, pts.y3) < 12) return { idx: selectedIdx, handle: 'h3' };
        }

        for (let i = drawings.length - 1; i >= 0; i--) {
            const d = drawings[i];
            const pts = getScreenCoords(d);
            const { x1, y1, x2, y2 } = pts;

            if (d.tool === 'horz') {
                const targetY = y1 !== null ? y1 : d.fixedY;
                if (targetY !== null && Math.abs(y - targetY) < 8) return { idx: i, handle: 'body' };
            } else if (d.tool === 'trend') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    if (distToSegment(x, y, x1, y1, x2, y2) < 8) return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'fib_ext') {
                if (window.FibonacciTool && window.FibonacciTool.hitTestExt(x, y, d, mainChart, mainSeries)) {
                    return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'fib_tz') {
                if (window.FibonacciTool && window.FibonacciTool.hitTestTimeZones(x, y, d, mainChart)) {
                    return { idx: i, handle: 'body' };
                }
            } else if (window.PatternTool && window.PatternTool.isPatternTool(d.tool)) {
                if (window.PatternTool.hitTest(x, y, d, mainChart, mainSeries)) {
                    return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'box' || d.tool === 'pos_long' || d.tool === 'pos_short' || d.tool === 'price_range' || d.tool === 'date_range') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    const minX = Math.min(x1, x2), maxX = Math.max(x1, x2);
                    const minY = Math.min(y1, y2), maxY = Math.max(y1, y2);
                    if (x >= minX - 6 && x <= maxX + 6 && y >= minY - 6 && y <= maxY + 6) return { idx: i, handle: 'body' };
                }
            } else if (d.tool === 'fib') {
                if (window.FibonacciTool && window.FibonacciTool.hitTest(x, y, pts)) {
                    return { idx: i, handle: 'body' };
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
                for (let j = 0; j < d.points.length - 1; j++) {
                    const px1 = safeCoordX(d.points[j].l, d.points[j].t);
                    const py1 = mainSeries.priceToCoordinate(d.points[j].p);
                    const px2 = safeCoordX(d.points[j+1].l, d.points[j+1].t);
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
                canvas.style.cursor = (hit.handle && hit.handle.startsWith('h')) ? 'pointer' : 'move';
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

        // โหมดคลิก 2 จุดสำหรับ Fib Retracement
        if (currentTool === 'fib') {
            const l = getLogicalFromX(mouseX);
            const p = getPriceFromY(mouseY);
            if (fibClickPoints.length === 0) {
                fibClickPoints.push({ x: mouseX, y: mouseY, l: l, p: p });
                redrawAll();
            } else if (fibClickPoints.length === 1) {
                drawings.push({
                    tool: 'fib',
                    l1: fibClickPoints[0].l, p1: fibClickPoints[0].p,
                    l2: l, p2: p,
                    color: '#00FFA3'
                });
                fibClickPoints = [];
                setTool('cursor');
                saveAndRedraw();
            }
            return;
        }

        // โหมดคลิก 3 จุดสำหรับ Trend-Based Fib Extension
        if (currentTool === 'fib_ext') {
            const l = getLogicalFromX(mouseX);
            const p = getPriceFromY(mouseY);
            extPoints.push({ x: mouseX, y: mouseY, l: l, p: p });
            if (extPoints.length === 3) {
                drawings.push({
                    tool: 'fib_ext',
                    l1: extPoints[0].l, p1: extPoints[0].p,
                    l2: extPoints[1].l, p2: extPoints[1].p,
                    l3: extPoints[2].l, p3: extPoints[2].p,
                    color: '#00FFA3'
                });
                extPoints = [];
                setTool('cursor');
                saveAndRedraw();
            } else {
                redrawAll();
            }
            return;
        }

        // โหมดคลิก 2 จุดสำหรับ Fib Time Zones
        if (currentTool === 'fib_tz') {
            const l = getLogicalFromX(mouseX);
            const p = getPriceFromY(mouseY);
            if (tzPoints.length === 0) {
                tzPoints.push({ x: mouseX, y: mouseY, l: l, p: p });
                redrawAll();
            } else if (tzPoints.length === 1) {
                drawings.push({
                    tool: 'fib_tz',
                    l1: tzPoints[0].l, p1: tzPoints[0].p,
                    l2: l, p2: p,
                    color: '#00FFA3'
                });
                tzPoints = [];
                setTool('cursor');
                saveAndRedraw();
            }
            return;
        }

        // โหมดคลิกสำหรับ Chart Patterns (14 รูปแบบ)
        if (window.PatternTool && window.PatternTool.isPatternTool(currentTool)) {
            const l = getLogicalFromX(mouseX);
            const p = getPriceFromY(mouseY);
            patternClickPoints.push({ x: mouseX, y: mouseY, l: l, p: p });
            const req = window.PatternTool.getRequiredPoints(currentTool);

            if (patternClickPoints.length >= req) {
                drawings.push({
                    tool: currentTool,
                    points: [...patternClickPoints],
                    color: '#00FFA3'
                });
                patternClickPoints = [];
                setTool('cursor');
                saveAndRedraw();
            } else {
                redrawAll();
                patternClickPoints.forEach((pt, i) => {
                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
                    ctx.fillStyle = '#00FFA3';
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                    ctx.fillStyle = '#00FFA3';
                    ctx.font = 'bold 12px sans-serif';
                    ctx.fillText(String(i + 1), pt.x + 8, pt.y - 8);
                    ctx.restore();
                });
            }
            return;
        }

        if (currentTool === 'text') {
            if (textOverlay && textInput) {
                textOverlay.style.left = mouseX + 'px';
                textOverlay.style.top = mouseY + 'px';
                textOverlay.style.display = 'block';
                textInput.value = '';
                textInput.focus();
            }
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

    if (textInput && textOverlay) {
        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const val = textInput.value.trim();
                if (val && startPx && mainSeries) {
                    const l1 = getLogicalFromX(startPx.x);
                    const p1 = getPriceFromY(startPx.y);
                    if (p1 !== null) {
                        drawings.push({
                            tool: 'text',
                            text: val,
                            l1: l1,
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
    }

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        currentPx = { x: mouseX, y: mouseY, l: getLogicalFromX(mouseX), p: getPriceFromY(mouseY) };

        if (isDragging && selectedIdx !== -1 && dragOrigObj && mainSeries) {
            const dx = mouseX - startPx.x;
            const dy = mouseY - startPx.y;
            const d = drawings[selectedIdx];

            if (activeHandle === 'h1') {
                const curOrig = getScreenCoords(dragOrigObj);
                d.l1 = getLogicalFromX(curOrig.x1 + dx);
                d.p1 = getPriceFromY(curOrig.y1 + dy);
            } else if (activeHandle === 'h2') {
                const curOrig = getScreenCoords(dragOrigObj);
                d.l2 = getLogicalFromX(curOrig.x2 + dx);
                d.p2 = getPriceFromY(curOrig.y2 + dy);
            } else if (activeHandle === 'h3') {
                const curOrig = getScreenCoords(dragOrigObj);
                d.l3 = getLogicalFromX(curOrig.x3 + dx);
                d.p3 = getPriceFromY(curOrig.y3 + dy);
            } else if (activeHandle === 'body') {
                const curOrig = getScreenCoords(dragOrigObj);
                if (curOrig.x1 !== null && curOrig.y1 !== null) {
                    d.l1 = getLogicalFromX(curOrig.x1 + dx);
                    d.p1 = getPriceFromY(curOrig.y1 + dy);
                }
                if (curOrig.x2 !== null && curOrig.y2 !== null) {
                    d.l2 = getLogicalFromX(curOrig.x2 + dx);
                    d.p2 = getPriceFromY(curOrig.y2 + dy);
                }
                if (curOrig.x3 !== null && curOrig.y3 !== null) {
                    d.l3 = getLogicalFromX(curOrig.x3 + dx);
                    d.p3 = getPriceFromY(curOrig.y3 + dy);
                }
                if (d.tool === 'horz') {
                    d.fixedY = (dragOrigObj.fixedY || curOrig.y1) + dy;
                }
            }
            redrawAll();
            return;
        }

        // Live Preview: Fib Retracement
        if (currentTool === 'fib' && fibClickPoints.length === 1) {
            redrawAll();
            if (window.FibonacciTool) {
                window.FibonacciTool.drawPreview(ctx, fibClickPoints[0], currentPx, mainSeries);
            }
            return;
        }

        // Live Preview: Trend-Based Fib Extension
        if (currentTool === 'fib_ext' && extPoints.length > 0) {
            redrawAll();
            if (window.FibonacciTool) {
                window.FibonacciTool.drawExtPreview(ctx, extPoints, currentPx, mainSeries, canvas.width);
            }
            return;
        }

        // Live Preview: Fib Time Zones
        if (currentTool === 'fib_tz' && tzPoints.length === 1) {
            redrawAll();
            if (window.FibonacciTool) {
                window.FibonacciTool.drawTimeZonesPreview(ctx, tzPoints[0], currentPx, mainChart, canvas.height);
            }
            return;
        }

        // Live Preview: Chart Patterns
        if (patternClickPoints.length > 0 && window.PatternTool && window.PatternTool.isPatternTool(currentTool)) {
            redrawAll();
            window.PatternTool.drawPreview(ctx, currentTool, patternClickPoints, { x: mouseX, y: mouseY, l: getLogicalFromX(mouseX), p: getPriceFromY(mouseY) }, mainChart, mainSeries, canvas.width, canvas.height);
            patternClickPoints.forEach((pt, i) => {
                ctx.save();
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
                ctx.fillStyle = '#00FFA3';
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.5;
                ctx.stroke();
                ctx.fillStyle = '#00FFA3';
                ctx.font = 'bold 12px sans-serif';
                ctx.fillText(String(i + 1), pt.x + 8, pt.y - 8);
                ctx.restore();
            });
            return;
        }

        if (!isDrawing) return;
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

        if (currentTool === 'fib' || currentTool === 'fib_ext' || currentTool === 'fib_tz' || (window.PatternTool && window.PatternTool.isPatternTool(currentTool))) {
            return;
        }

        if (!isDrawing) return;
        isDrawing = false;

        if (startPx && currentPx && mainSeries) {
            const l1 = getLogicalFromX(startPx.x);
            const l2 = getLogicalFromX(currentPx.x);
            const p1 = getPriceFromY(startPx.y);
            const p2 = getPriceFromY(currentPx.y);

            if (currentTool === 'pen') {
                const pts = penPoints.map(pt => ({
                    l: getLogicalFromX(pt.x),
                    p: getPriceFromY(pt.y)
                }));
                if (pts.length > 1) {
                    drawings.push({ tool: 'pen', points: pts, color: '#f5c518' });
                    saveAndRedraw();
                }
                penPoints = [];
            } else if (p1 !== null) {
                drawings.push({
                    tool: currentTool,
                    l1: l1,
                    p1: p1,
                    l2: l2,
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

        if (currentTool === 'trend') {
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

    function drawHandle(x, y) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, 4.5, 0, Math.PI * 2);
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
            } else if (d.tool === 'trend') {
                if (x1 !== null && y1 !== null && x2 !== null && y2 !== null) {
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                    if (isSelected) { drawHandle(x1, y1); drawHandle(x2, y2); }
                }
            } else if (d.tool === 'fib_ext') {
                if (window.FibonacciTool) {
                    window.FibonacciTool.drawExt(ctx, d, mainChart, mainSeries, isSelected, canvas.width, drawHandle);
                }
            } else if (d.tool === 'fib_tz') {
                if (window.FibonacciTool) {
                    window.FibonacciTool.drawTimeZones(ctx, d, mainChart, isSelected, canvas.height, drawHandle);
                }
            } else if (window.PatternTool && window.PatternTool.isPatternTool(d.tool)) {
                window.PatternTool.draw(ctx, d, mainChart, mainSeries, isSelected, canvas.width, canvas.height, drawHandle);
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
                if (window.FibonacciTool) {
                    window.FibonacciTool.draw(ctx, d, pts, isSelected, mainSeries, drawHandle);
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
                    const px = safeCoordX(pt.l, pt.t);
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
            if (!p || !p.chart || !p.boxEl || !p.viewEl) return;
            if (p.boxEl.dataset && p.boxEl.dataset.collapsed) return;
            const h = Math.max(30, p.boxEl.clientHeight);
            const w = p.boxEl.clientWidth || (p.viewEl ? p.viewEl.clientWidth : 0);
            if (p.viewEl && p.viewEl.style) {
                p.viewEl.style.height = h + 'px';
            }
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
            if (view && view.style) view.style.height = Math.max(20, newH - hdrH) + 'px';
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
        if (!p || !p.viewEl) return;
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
        if (!p || !p.boxEl || !p.viewEl) return;
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
        if (!p || !p.boxEl) return;
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
        } else if (t && typeof t === 'object' && t.year && t.month && t.day) {
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
                if (vLine && vLine.style) vLine.style.display = 'none';
                if (vBadge && vBadge.style) vBadge.style.display = 'none';
            } else {
                const mainView = document.getElementById('chart-main');
                const offLeft = (mainView && chartWrap) ? (mainView.getBoundingClientRect().left - chartWrap.getBoundingClientRect().left) : 0;
                const posX = (param.point.x + offLeft) + 'px';
                if (vLine && vLine.style) {
                    vLine.style.left = posX;
                    vLine.style.display = 'block';
                }
                if (vBadge && vBadge.style) {
                    vBadge.style.left = posX;
                    vBadge.innerText = _fmtTimeBadge(param.time);
                    vBadge.style.display = 'block';
                }
            }
        });
    });

    resizeCanvas();
    window.addEventListener('resize', updateAllWidths);
    window.addEventListener('resize', () => { try { paneResizeAll(); } catch(e) {} });
    setTimeout(updateAllWidths, 100);
    setTimeout(paneResizeAll, 150);
    setTimeout(updateAllWidths, 300);
    setTimeout(paneResizeAll, 350);

    // เชื่อมต่อการคลิกเลือกเครื่องมือรูปแบบชาร์ต (14 รูปแบบ)
    document.addEventListener('click', (e) => {
        const item = e.target.closest('[data-tool]');
        if (item) {
            const tool = item.getAttribute('data-tool');
            if (tool && tool !== 'cursor') {
                e.stopPropagation();
                setTool(tool);
                document.querySelectorAll('.tool-item-wrap').forEach(w => w.classList.remove('open'));
            }
        }
    });

    // =========================================================================
    // ระบบจัดการหน้าต่างตั้งค่า PRO SETTINGS MODAL (FIBONACCI & PATTERNS)
    // =========================================================================

    function setupTabSwitching(tabBarId, containerSelector) {
        const tabBar = document.getElementById(tabBarId);
        if (!tabBar) return;
        const buttons = tabBar.querySelectorAll('.pro-tab-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const targetId = btn.getAttribute('data-tab');
                const container = tabBar.closest(containerSelector);
                if (container) {
                    container.querySelectorAll('.pro-tab-page').forEach(page => {
                        page.classList.remove('active');
                    });
                    const targetPage = container.querySelector('#' + targetId);
                    if (targetPage) targetPage.classList.add('active');
                }
            });
        });
    }

    setupTabSwitching('fib-tab-bar', '#fib-settings-modal');
    setupTabSwitching('pat-tab-bar', '#pattern-settings-modal');

    const fibOpSlider = document.getElementById('cfg-fib-opacity');
    const fibOpVal = document.getElementById('cfg-fib-opacity-val');
    if (fibOpSlider && fibOpVal) {
        fibOpSlider.addEventListener('input', () => {
            fibOpVal.innerText = fibOpSlider.value + '%';
        });
    }

    const patOpSlider = document.getElementById('cfg-pat-opacity');
    const patOpVal = document.getElementById('cfg-pat-opacity-val');
    if (patOpSlider && patOpVal) {
        patOpSlider.addEventListener('input', () => {
            patOpVal.innerText = patOpSlider.value + '%';
        });
    }

    // --- ควบคุม Modal Fibonacci ---
    const proFibModal = document.getElementById('fib-settings-modal');
    const btnOpenFibSet = document.getElementById('btn-open-fib-settings');
    const btnCloseFibSet = document.getElementById('btn-close-fib-settings');
    const btnCancelFibSet = document.getElementById('btn-cancel-fib-settings');
    const btnSaveFibSet = document.getElementById('btn-save-fib-settings');

    function closeFibModal() {
        if (proFibModal) proFibModal.classList.remove('open');
    }

    if (btnOpenFibSet && proFibModal) {
        btnOpenFibSet.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.tool-item-wrap').forEach(w => w.classList.remove('open'));
            if (fibOpSlider && window.FibonacciTool) {
                const curOp = window.FibonacciTool.fillOpacity !== undefined ? window.FibonacciTool.fillOpacity : 12;
                fibOpSlider.value = curOp;
                if (fibOpVal) fibOpVal.innerText = curOp + '%';
            }
            proFibModal.classList.add('open');
        });
    }

    if (btnCloseFibSet) btnCloseFibSet.addEventListener('click', closeFibModal);
    if (btnCancelFibSet) btnCancelFibSet.addEventListener('click', closeFibModal);

    if (btnSaveFibSet) {
        btnSaveFibSet.addEventListener('click', () => {
            const levelRows = document.querySelectorAll('#fib-levels-grid .pro-level-item');
            const activeLevels = [];
            levelRows.forEach(row => {
                const chk = row.querySelector('.pro-check');
                const valInput = row.querySelector('.pro-val-input');
                const colInput = row.querySelector('.pro-color-btn');
                if (chk && valInput && colInput) {
                    activeLevels.push({
                        active: chk.checked,
                        value: parseFloat(valInput.value) || 0,
                        color: colInput.value
                    });
                }
            });

            const newOpacity = fibOpSlider ? parseInt(fibOpSlider.value) || 12 : 12;
            const showBg = document.getElementById('cfg-fib-bg') ? document.getElementById('cfg-fib-bg').checked : true;
            const showPrices = document.getElementById('cfg-fib-prices') ? document.getElementById('cfg-fib-prices').checked : true;
            const showLevels = document.getElementById('cfg-fib-levels') ? document.getElementById('cfg-fib-levels').checked : true;

            if (window.FibonacciTool) {
                window.FibonacciTool.customLevels = activeLevels;
                window.FibonacciTool.fillOpacity = newOpacity;
                window.FibonacciTool.showBackground = showBg;
                window.FibonacciTool.showPrices = showPrices;
                window.FibonacciTool.showLevels = showLevels;
            }

            try {
                localStorage.setItem('tv_fib_user_settings', JSON.stringify({
                    levels: activeLevels,
                    opacity: newOpacity,
                    showBg: showBg,
                    showPrices: showPrices,
                    showLevels: showLevels
                }));
            } catch(e) {}

            closeFibModal();
            redrawAll();
        });
    }

    // --- ควบคุม Modal Patterns ---
    const patModal = document.getElementById('pattern-settings-modal');
    const btnOpenPatSet = document.getElementById('btn-open-pattern-settings');
    const btnClosePatSet = document.getElementById('btn-close-pattern-settings');
    const btnCancelPatSet = document.getElementById('btn-cancel-pattern-settings');
    const btnSavePatSet = document.getElementById('btn-save-pattern-settings');

    function closePatModal() {
        if (patModal) patModal.classList.remove('open');
    }

    if (btnOpenPatSet && patModal) {
        btnOpenPatSet.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.tool-item-wrap').forEach(w => w.classList.remove('open'));
            const colInput = document.getElementById('cfg-pat-linecolor');
            const ratCheck = document.getElementById('cfg-pat-ratios');
            const labCheck = document.getElementById('cfg-pat-labels');
            
            if (window.PatternTool && window.PatternTool.settings) {
                if (colInput) colInput.value = window.PatternTool.settings.lineColor || '#00FFA3';
                if (patOpSlider) {
                    patOpSlider.value = window.PatternTool.settings.fillOpacity || 12;
                    if (patOpVal) patOpVal.innerText = patOpSlider.value + '%';
                }
                if (ratCheck) ratCheck.checked = window.PatternTool.settings.showRatios !== false;
                if (labCheck) labCheck.checked = window.PatternTool.settings.showLabels !== false;
            }
            patModal.classList.add('open');
        });
    }

    if (btnClosePatSet) btnClosePatSet.addEventListener('click', closePatModal);
    if (btnCancelPatSet) btnCancelPatSet.addEventListener('click', closePatModal);

    if (btnSavePatSet) {
        btnSavePatSet.addEventListener('click', () => {
            const colInput = document.getElementById('cfg-pat-linecolor');
            const ratCheck = document.getElementById('cfg-pat-ratios');
            const labCheck = document.getElementById('cfg-pat-labels');
            
            if (window.PatternTool) {
                if (!window.PatternTool.settings) window.PatternTool.settings = {};
                window.PatternTool.settings.lineColor = colInput ? colInput.value : '#00FFA3';
                window.PatternTool.settings.fillOpacity = patOpSlider ? parseInt(patOpSlider.value) || 12 : 12;
                window.PatternTool.settings.showRatios = ratCheck ? ratCheck.checked : true;
                window.PatternTool.settings.showLabels = labCheck ? labCheck.checked : true;

                try {
                    localStorage.setItem('tv_pattern_user_settings', JSON.stringify(window.PatternTool.settings));
                } catch(e) {}
            }

            closePatModal();
            redrawAll();
        });
    }

    // =========================================================================
    // ระบบ Dropdown สลับหน่วยราคา (ปุ่ม เดิม ⌵)
    // =========================================================================
    const btnScaleToggle = document.getElementById('btn-scale-toggle');
    const scaleMenu = document.getElementById('price-scale-menu');
    const activeLabel = document.getElementById('scale-active-label');
    const USD_TO_THB_RATE = 35.0;

    if (btnScaleToggle && scaleMenu) {
        btnScaleToggle.onclick = function(e) {
            e.stopPropagation();
            e.preventDefault();
            const isOpen = scaleMenu.style.display === 'flex';
            scaleMenu.style.display = isOpen ? 'none' : 'flex';
        };

        window.addEventListener('click', function(e) {
            if (!e.target.closest('#price-scale-dropdown-wrap')) {
                scaleMenu.style.display = 'none';
            }
        });

        const items = scaleMenu.querySelectorAll('.scale-menu-item');
        items.forEach(function(item) {
            item.onclick = function(e) {
                e.stopPropagation();
                e.preventDefault();

                items.forEach(function(b) {
                    b.style.color = '#d1d4dc';
                    b.classList.remove('active');
                });
                item.style.color = '#00FFA3';
                item.classList.add('active');

                const mode = item.getAttribute('data-mode');
                const labelText = item.innerText.split(' ')[0];
                if (activeLabel) activeLabel.innerText = labelText;

                if (mainChart && mainSeries) {
                    if (mode === 'percent') {
                        mainChart.priceScale('right').applyOptions({ mode: 2 });
                        mainSeries.applyOptions({ priceFormat: { type: 'percent' } });
                    } else if (mode === 'thb') {
                        mainChart.priceScale('right').applyOptions({ mode: 0 });
                        mainSeries.applyOptions({
                            priceFormat: {
                                type: 'custom',
                                formatter: function(p) {
                                    return '฿' + (p * USD_TO_THB_RATE).toLocaleString('th-TH', { maximumFractionDigits: 0 });
                                }
                            }
                        });
                    } else if (mode === 'usd') {
                        mainChart.priceScale('right').applyOptions({ mode: 0 });
                        mainSeries.applyOptions({
                            priceFormat: {
                                type: 'custom',
                                formatter: function(p) {
                                    return '$' + p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                                }
                            }
                        });
                    } else {
                        mainChart.priceScale('right').applyOptions({ mode: 0 });
                        mainSeries.applyOptions({
                            priceFormat: { type: 'price', precision: 2, minMove: 0.01 }
                        });
                    }
                    if (typeof redrawAll === 'function') redrawAll();
                }

                scaleMenu.style.display = 'none';
            };
        });
    }
})();