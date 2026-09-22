/**
 * fibonacci_tool.js
 * โมดูลคำนวณและวาด Fib Retracement (2 จุด) และ Trend-Based Fib Extension (3 จุด) สไตล์ TradingView
 */
window.FibonacciTool = {
    retrLevels: [
        { r: 0.0,   c: '#787b86', bg: 'rgba(120, 123, 134, 0.10)', lbl: '0' },
        { r: 0.236, c: '#f23645', bg: 'rgba(242, 54, 69, 0.12)',   lbl: '0.236' },
        { r: 0.382, c: '#81c784', bg: 'rgba(129, 199, 132, 0.12)', lbl: '0.382' },
        { r: 0.5,   c: '#4caf50', bg: 'rgba(76, 175, 80, 0.12)',   lbl: '0.5' },
        { r: 0.618, c: '#00bcd4', bg: 'rgba(0, 188, 212, 0.14)',  lbl: '0.618' },
        { r: 0.786, c: '#64b5f6', bg: 'rgba(100, 181, 246, 0.12)', lbl: '0.786' },
        { r: 1.0,   c: '#787b86', bg: 'rgba(120, 123, 134, 0.14)', lbl: '1' },
        { r: 1.618, c: '#2962ff', bg: 'rgba(41, 98, 255, 0.15)',   lbl: '1.618' },
        { r: 2.0,   c: '#009688', bg: 'rgba(0, 150, 136, 0.12)',   lbl: '2' },
        { r: 2.618, c: '#f23645', bg: 'rgba(242, 54, 69, 0.14)',   lbl: '2.618' },
        { r: 3.0,   c: '#2196f3', bg: 'rgba(33, 150, 243, 0.12)',  lbl: '3' },
        { r: 3.618, c: '#9c27b0', bg: 'rgba(156, 39, 176, 0.14)',  lbl: '3.618' },
        { r: 4.236, c: '#e91e63', bg: 'rgba(233, 30, 99, 0.15)',   lbl: '4.236' }
    ],

    extLevels: [
        { r: 0.0,   c: '#787b86', bg: 'rgba(120, 123, 134, 0.10)', lbl: '0' },
        { r: 0.236, c: '#f23645', bg: 'rgba(242, 54, 69, 0.12)',   lbl: '0.236' },
        { r: 0.382, c: '#81c784', bg: 'rgba(129, 199, 132, 0.12)', lbl: '0.382' },
        { r: 0.5,   c: '#4caf50', bg: 'rgba(76, 175, 80, 0.12)',   lbl: '0.5' },
        { r: 0.618, c: '#00bcd4', bg: 'rgba(0, 188, 212, 0.14)',  lbl: '0.618' },
        { r: 0.786, c: '#64b5f6', bg: 'rgba(100, 181, 246, 0.12)', lbl: '0.786' },
        { r: 1.0,   c: '#787b86', bg: 'rgba(120, 123, 134, 0.14)', lbl: '1' },
        { r: 1.272, c: '#ff9800', bg: 'rgba(255, 152, 0, 0.14)',   lbl: '1.272' },
        { r: 1.618, c: '#2962ff', bg: 'rgba(41, 98, 255, 0.15)',   lbl: '1.618' },
        { r: 2.0,   c: '#009688', bg: 'rgba(0, 150, 136, 0.12)',   lbl: '2' },
        { r: 2.618, c: '#f23645', bg: 'rgba(242, 54, 69, 0.14)',   lbl: '2.618' },
        { r: 3.618, c: '#9c27b0', bg: 'rgba(156, 39, 176, 0.14)',  lbl: '3.618' },
        { r: 4.236, c: '#e91e63', bg: 'rgba(233, 30, 99, 0.15)',   lbl: '4.236' }
    ],

    _drawCircle: function(ctx, x, y, r, color) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, r || 4, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = color || '#00FFA3';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
    },

    // ── 1. FIB RETRACEMENT (2 จุด) ──
    drawPreview: function(ctx, startPx, currentPx, mainSeries) {
        if (!startPx || !currentPx) return;
        const minX = Math.min(startPx.x, currentPx.x);
        const maxX = Math.max(startPx.x, currentPx.x);
        const w = Math.max(1, maxX - minX);
        const baseY = currentPx.y;
        const diffY = startPx.y - currentPx.y;
        const p1 = (startPx.p !== undefined) ? startPx.p : (mainSeries ? mainSeries.coordinateToPrice(startPx.y) : null);
        const p2 = (currentPx.p !== undefined) ? currentPx.p : (mainSeries ? mainSeries.coordinateToPrice(currentPx.y) : null);
        const baseP = p2 !== null ? p2 : 0;
        const diffP = (p1 !== null && p2 !== null) ? (p1 - p2) : 0;

        for (let i = 0; i < this.retrLevels.length - 1; i++) {
            const yA = baseY + diffY * this.retrLevels[i].r;
            const yB = baseY + diffY * this.retrLevels[i + 1].r;
            ctx.fillStyle = this.retrLevels[i + 1].bg;
            ctx.fillRect(minX, Math.min(yA, yB), w, Math.abs(yB - yA));
        }

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(startPx.x, startPx.y);
        ctx.lineTo(currentPx.x, currentPx.y);
        ctx.stroke();

        ctx.setLineDash([]);
        this._drawCircle(ctx, startPx.x, startPx.y, 4, '#00FFA3');
        this._drawCircle(ctx, currentPx.x, currentPx.y, 4, '#00FFA3');

        this.retrLevels.forEach(lvl => {
            const y = baseY + diffY * lvl.r;
            const price = baseP + diffP * lvl.r;
            ctx.strokeStyle = lvl.c;
            ctx.lineWidth = (lvl.r === 0.5 || lvl.r === 0.618 || lvl.r === 1.618) ? 1.5 : 1;
            ctx.beginPath();
            ctx.moveTo(minX, y);
            ctx.lineTo(maxX, y);
            ctx.stroke();

            ctx.fillStyle = lvl.c;
            ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, sans-serif';
            const priceStr = (p1 !== null && p2 !== null) ? ` (${price.toFixed(4)})` : '';
            ctx.fillText(`${lvl.lbl}${priceStr}`, minX + 6, y - 4);
        });
    },

    draw: function(ctx, d, pts, isSelected, mainSeries, drawHandleFn) {
        const { x1, y1, x2, y2 } = pts;
        if (x1 === null || y1 === null || x2 === null || y2 === null) return;

        const minX = Math.min(x1, x2);
        const maxX = Math.max(x1, x2);
        const w = Math.max(1, maxX - minX);
        const baseY = y2;
        const diffY = y1 - y2;
        const baseP = d.p2;
        const diffP = d.p1 - d.p2;

        for (let i = 0; i < this.retrLevels.length - 1; i++) {
            const yA = baseY + diffY * this.retrLevels[i].r;
            const yB = baseY + diffY * this.retrLevels[i + 1].r;
            ctx.fillStyle = this.retrLevels[i + 1].bg;
            ctx.fillRect(minX, Math.min(yA, yB), w, Math.abs(yB - yA));
        }

        ctx.strokeStyle = isSelected ? '#00FFA3' : 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();

        ctx.setLineDash([]);
        this.retrLevels.forEach(lvl => {
            const curY = baseY + diffY * lvl.r;
            const price = baseP + diffP * lvl.r;
            ctx.strokeStyle = isSelected ? '#00FFA3' : lvl.c;
            ctx.lineWidth = (lvl.r === 0.5 || lvl.r === 0.618 || lvl.r === 1.618) ? 1.5 : 1;
            ctx.beginPath();
            ctx.moveTo(minX, curY);
            ctx.lineTo(maxX, curY);
            ctx.stroke();

            ctx.fillStyle = lvl.c;
            ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, sans-serif';
            ctx.fillText(`${lvl.lbl} (${price.toFixed(4)})`, minX + 6, curY - 4);
        });

        if (isSelected && typeof drawHandleFn === 'function') {
            drawHandleFn(x1, y1);
            drawHandleFn(x2, y2);
        }
    },

    hitTest: function(x, y, pts) {
        const { x1, y1, x2, y2 } = pts;
        if (x1 === null || y1 === null || x2 === null || y2 === null) return false;
        const minX = Math.min(x1, x2) - 10;
        const maxX = Math.max(x1, x2) + 10;
        const baseY = y2;
        const diffY = y1 - y2;
        const allY = this.retrLevels.map(lvl => baseY + diffY * lvl.r);
        const minY = Math.min(...allY) - 10;
        const maxY = Math.max(...allY) + 10;
        return (x >= minX && x <= maxX && y >= minY && y <= maxY);
    },

    // ── 2. TREND-BASED FIB EXTENSION (3 จุด A->B->C) ──
    drawExtPreview: function(ctx, pts, curPx, mainSeries, canvasWidth) {
        if (!pts || pts.length === 0) return;
        ctx.save();

        if (pts.length === 1) {
            ctx.strokeStyle = '#00FFA3';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(pts[0].x, pts[0].y);
            ctx.lineTo(curPx.x, curPx.y);
            ctx.stroke();

            ctx.setLineDash([]);
            this._drawCircle(ctx, pts[0].x, pts[0].y, 4.5, '#00FFA3');
            this._drawCircle(ctx, curPx.x, curPx.y, 4.5, '#00FFA3');

            ctx.fillStyle = '#00FFA3';
            ctx.font = 'bold 12px sans-serif';
            ctx.fillText('A', pts[0].x + 8, pts[0].y - 8);
            ctx.fillText('B (คลิกกำหนดจุด B)', curPx.x + 8, curPx.y - 8);
        } else if (pts.length === 2) {
            ctx.strokeStyle = '#00FFA3';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(pts[0].x, pts[0].y);
            ctx.lineTo(pts[1].x, pts[1].y);
            ctx.lineTo(curPx.x, curPx.y);
            ctx.stroke();

            ctx.setLineDash([]);
            this._drawCircle(ctx, pts[0].x, pts[0].y, 4.5, '#00FFA3');
            this._drawCircle(ctx, pts[1].x, pts[1].y, 4.5, '#00FFA3');
            this._drawCircle(ctx, curPx.x, curPx.y, 4.5, '#00FFA3');

            ctx.fillStyle = '#00FFA3';
            ctx.font = 'bold 12px sans-serif';
            ctx.fillText('A', pts[0].x + 8, pts[0].y - 8);
            ctx.fillText('B', pts[1].x + 8, pts[1].y - 8);
            ctx.fillText('C (คลิกกำหนดจุด C)', curPx.x + 8, curPx.y - 8);

            const p1 = pts[0].p, p2 = pts[1].p;
            const p3 = (mainSeries ? mainSeries.coordinateToPrice(curPx.y) : null) || 0;
            const diffP = p2 - p1;
            const startX = curPx.x;
            const endX = Math.max(startX + 180, canvasWidth);

            const yLevels = this.extLevels.map(lvl => {
                const targetPrice = p3 + diffP * lvl.r;
                const ly = mainSeries ? mainSeries.priceToCoordinate(targetPrice) : null;
                return { y: ly, price: targetPrice, lvl: lvl };
            }).filter(item => item.y !== null);

            for (let i = 0; i < yLevels.length - 1; i++) {
                const yA = yLevels[i].y;
                const yB = yLevels[i + 1].y;
                ctx.fillStyle = yLevels[i + 1].lvl.bg;
                ctx.fillRect(startX, Math.min(yA, yB), endX - startX, Math.abs(yB - yA));
            }

            ctx.setLineDash([]);
            yLevels.forEach(item => {
                ctx.strokeStyle = item.lvl.c;
                ctx.lineWidth = (item.lvl.r === 0.618 || item.lvl.r === 1.0 || item.lvl.r === 1.618) ? 1.5 : 1;
                ctx.beginPath();
                ctx.moveTo(startX, item.y);
                ctx.lineTo(endX, item.y);
                ctx.stroke();

                ctx.fillStyle = item.lvl.c;
                ctx.font = 'bold 11px -apple-system, sans-serif';
                ctx.fillText(`${item.lvl.lbl} (${item.price.toFixed(4)})`, startX + 6, item.y - 4);
            });
        }
        ctx.restore();
    },

    drawExt: function(ctx, d, mainChart, mainSeries, isSelected, canvasWidth, drawHandleFn) {
        const tScale = mainChart.timeScale();
        const x1 = tScale.timeToCoordinate(d.t1);
        const y1 = mainSeries.priceToCoordinate(d.p1);
        const x2 = tScale.timeToCoordinate(d.t2);
        const y2 = mainSeries.priceToCoordinate(d.p2);
        const x3 = tScale.timeToCoordinate(d.t3);
        const y3 = mainSeries.priceToCoordinate(d.p3);

        if (x1 === null || y1 === null || x2 === null || y2 === null || x3 === null || y3 === null) return;

        ctx.save();
        ctx.strokeStyle = isSelected ? '#00FFA3' : 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.lineTo(x3, y3);
        ctx.stroke();

        ctx.fillStyle = isSelected ? '#00FFA3' : 'rgba(255, 255, 255, 0.8)';
        ctx.font = 'bold 11px sans-serif';
        ctx.fillText('A', x1 + 6, y1 - 6);
        ctx.fillText('B', x2 + 6, y2 - 6);
        ctx.fillText('C', x3 + 6, y3 - 6);

        const diffP = d.p2 - d.p1;
        const startX = x3;
        const endX = Math.max(startX + 180, canvasWidth);

        const yLevels = this.extLevels.map(lvl => {
            const price = d.p3 + diffP * lvl.r;
            return {
                y: mainSeries.priceToCoordinate(price),
                price: price,
                lvl: lvl
            };
        }).filter(item => item.y !== null);

        for (let i = 0; i < yLevels.length - 1; i++) {
            const yA = yLevels[i].y;
            const yB = yLevels[i + 1].y;
            ctx.fillStyle = yLevels[i + 1].lvl.bg;
            ctx.fillRect(startX, Math.min(yA, yB), endX - startX, Math.abs(yB - yA));
        }

        ctx.setLineDash([]);
        yLevels.forEach(item => {
            ctx.strokeStyle = isSelected ? '#00FFA3' : item.lvl.c;
            ctx.lineWidth = (item.lvl.r === 0.618 || item.lvl.r === 1.0 || item.lvl.r === 1.618) ? 1.5 : 1;
            ctx.beginPath();
            ctx.moveTo(startX, item.y);
            ctx.lineTo(endX, item.y);
            ctx.stroke();

            ctx.fillStyle = item.lvl.c;
            ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, sans-serif';
            ctx.fillText(`${item.lvl.lbl} (${item.price.toFixed(4)})`, startX + 6, item.y - 4);
        });

        if (isSelected && typeof drawHandleFn === 'function') {
            drawHandleFn(x1, y1);
            drawHandleFn(x2, y2);
            drawHandleFn(x3, y3);
        }
        ctx.restore();
    },

    hitTestExt: function(x, y, d, mainChart, mainSeries) {
        const tScale = mainChart.timeScale();
        const x1 = tScale.timeToCoordinate(d.t1), y1 = mainSeries.priceToCoordinate(d.p1);
        const x2 = tScale.timeToCoordinate(d.t2), y2 = mainSeries.priceToCoordinate(d.p2);
        const x3 = tScale.timeToCoordinate(d.t3), y3 = mainSeries.priceToCoordinate(d.p3);
        if (x1 === null || y1 === null || x2 === null || y2 === null || x3 === null || y3 === null) return false;

        const dist = (px, py, ax, ay, bx, by) => {
            const l2 = (bx - ax)**2 + (by - ay)**2;
            if (l2 === 0) return Math.hypot(px - ax, py - ay);
            let t = Math.max(0, Math.min(1, ((px - ax)*(bx - ax) + (py - ay)*(by - ay)) / l2));
            return Math.hypot(px - (ax + t*(bx - ax)), py - (ay + t*(by - ay)));
        };

        if (dist(x, y, x1, y1, x2, y2) < 8 || dist(x, y, x2, y2, x3, y3) < 8) return true;

        const diffP = d.p2 - d.p1;
        for (let lvl of this.extLevels) {
            const ly = mainSeries.priceToCoordinate(d.p3 + diffP * lvl.r);
            if (ly !== null && Math.abs(y - ly) < 8 && x >= x3 - 10) return true;
        }
        return false;
    }
};