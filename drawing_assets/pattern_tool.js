/**
 * pattern_tool.js — Professional Edition
 * โมดูลคำนวณและวาดรูปแบบชาร์ต 14 รูปแบบ (Chart Patterns, Harmonic, Elliott Waves & Cycles)
 * พร้อมระบบคำนวณสัดส่วน Fibonacci Ratios และโครงสร้างทางเทคนิคระดับมืออาชีพ
 */

window.PatternTool = {
    settings: {
        lineColor: '#00FFA3',
        selectedColor: '#00e5ff',
        fillOpacity: 12,
        showRatios: true,
        showLabels: true
    },

    toolsConfig: {
        'pat_xabcd':        { name: 'XABCD Pattern', points: 5, labels: ['X', 'A', 'B', 'C', 'D'], type: 'harmonic' },
        'pat_cypher':       { name: 'Cypher Pattern', points: 5, labels: ['X', 'A', 'B', 'C', 'D'], type: 'harmonic' },
        'head_shoulders':   { name: 'Head and Shoulders', points: 5, labels: ['LS', 'NL1', 'H', 'NL2', 'RS'], type: 'head_shoulders' },
        'pat_abcd':         { name: 'ABCD Pattern', points: 4, labels: ['A', 'B', 'C', 'D'], type: 'abcd' },
        'triangle':         { name: 'Triangle Pattern', points: 4, labels: ['A', 'B', 'C', 'D'], type: 'triangle' },
        'pat_threedrives':  { name: 'Three Drives Pattern', points: 5, labels: ['1', 'A', '2', 'B', '3'], type: 'harmonic' },
        'elliott_impulse':  { name: 'Elliott Impulse (1-2-3-4-5)', points: 5, labels: ['1', '2', '3', '4', '5'], type: 'elliott_impulse' },
        'elliott_abc':      { name: 'Elliott Correction (A-B-C)', points: 3, labels: ['A', 'B', 'C'], type: 'elliott_abc' },
        'elliott_triangle': { name: 'Elliott Triangle (A-B-C-D-E)', points: 5, labels: ['A', 'B', 'C', 'D', 'E'], type: 'elliott_triangle' },
        'elliott_double':   { name: 'Elliott Double Combo (W-X-Y)', points: 3, labels: ['W', 'X', 'Y'], type: 'elliott_combo' },
        'elliott_triple':   { name: 'Elliott Triple Combo (W-X-Y-X-Z)', points: 5, labels: ['W', 'X', 'Y', 'X', 'Z'], type: 'elliott_combo' },
        'cycle_lines':      { name: 'Cyclic Lines', points: 2, labels: ['1', '2'], type: 'cycle_lines' },
        'time_cycles':      { name: 'Time Cycles', points: 2, labels: ['1', '2'], type: 'time_cycles' },
        'sine_line':        { name: 'Sine Line', points: 2, labels: ['P1', 'P2'], type: 'sine_line' }
    },

    isPatternTool: function(tool) { return !!this.toolsConfig[tool]; },
    getRequiredPoints: function(tool) { return this.toolsConfig[tool] ? this.toolsConfig[tool].points : 0; },

    getScreenPoint: function(pt, mainChart, mainSeries) {
        let x = pt.x, y = pt.y;
        if (mainChart && pt.l !== undefined && pt.l !== null) {
            try { const cx = mainChart.timeScale().logicalToCoordinate(pt.l); if (cx !== null && !isNaN(cx)) x = cx; } catch(e) {}
        }
        if (mainSeries && pt.p !== undefined && pt.p !== null) {
            try { const cy = mainSeries.priceToCoordinate(pt.p); if (cy !== null && !isNaN(cy)) y = cy; } catch(e) {}
        }
        return { x: x, y: y };
    },

    draw: function(ctx, d, mainChart, mainSeries, isSelected, canvasWidth, canvasHeight, drawHandleFn) {
        const conf = this.toolsConfig[d.tool];
        if (!conf || !d.points || d.points.length < conf.points) return;

        const pts = d.points.map(pt => this.getScreenPoint(pt, mainChart, mainSeries));
        const color = isSelected ? '#00e5ff' : (d.color || '#00FFA3');
        const alpha = (this.settings.fillOpacity / 100).toFixed(2);
        const fillRgba = isSelected ? 'rgba(0, 229, 255, 0.15)' : `rgba(0, 255, 163, ${alpha})`;

        ctx.save();
        ctx.strokeStyle = color;
        ctx.fillStyle = fillRgba;
        ctx.lineWidth = isSelected ? 2.5 : 2;

        switch (conf.type) {
            case 'head_shoulders': this.drawHeadAndShoulders(ctx, pts, color, isSelected); break;
            case 'harmonic': this.drawHarmonic(ctx, pts, d.points, color); break;
            case 'abcd': this.drawABCD(ctx, pts, d.points, color); break;
            case 'triangle': this.drawTriangle(ctx, pts, color); break;
            case 'elliott_impulse':
            case 'elliott_abc':
            case 'elliott_triangle':
            case 'elliott_combo': this.drawElliott(ctx, pts, d.points, color); break;
            case 'cycle_lines':
            case 'time_cycles':
            case 'sine_line': this.drawCycles(ctx, conf.type, pts, color, canvasWidth, canvasHeight); break;
        }

        if (this.settings.showLabels) {
            pts.forEach((p, idx) => {
                const label = conf.labels && conf.labels[idx] ? conf.labels[idx] : String(idx + 1);
                this.drawPointBadge(ctx, p.x, p.y, label, color, isSelected);
                if (isSelected && typeof drawHandleFn === 'function') drawHandleFn(p.x, p.y);
            });
        }
        ctx.restore();
    },

    drawHeadAndShoulders: function(ctx, pts, color, isSelected) {
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.stroke();
        ctx.fill();

        if (pts.length >= 4) {
            ctx.save();
            ctx.strokeStyle = isSelected ? '#ffffff' : '#ffd54f';
            ctx.lineWidth = 1.8;
            ctx.setLineDash([6, 4]);
            const dx = pts[3].x - pts[1].x, dy = pts[3].y - pts[1].y;
            ctx.beginPath();
            ctx.moveTo(pts[1].x - dx * 0.3, pts[1].y - dy * 0.3);
            ctx.lineTo(pts[3].x + dx * 0.6, pts[3].y + dy * 0.6);
            ctx.stroke();
            ctx.fillStyle = '#ffd54f';
            ctx.font = 'bold 10px Roboto Mono, monospace';
            ctx.fillText('Neckline', pts[3].x + 8, pts[3].y - 4);
            ctx.restore();
        }
    },

    drawHarmonic: function(ctx, pts, rawPts, color) {
        if (pts.length >= 5) {
            ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y); ctx.lineTo(pts[1].x, pts[1].y); ctx.lineTo(pts[2].x, pts[2].y); ctx.closePath(); ctx.fill();
            ctx.beginPath(); ctx.moveTo(pts[2].x, pts[2].y); ctx.lineTo(pts[3].x, pts[3].y); ctx.lineTo(pts[4].x, pts[4].y); ctx.closePath(); ctx.fill();
        }
        ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.stroke();

        if (this.settings.showRatios && rawPts.length >= 5) {
            ctx.save(); ctx.setLineDash([3, 3]); ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
            ctx.beginPath();
            ctx.moveTo(pts[0].x, pts[0].y); ctx.lineTo(pts[2].x, pts[2].y);
            ctx.moveTo(pts[1].x, pts[1].y); ctx.lineTo(pts[3].x, pts[3].y);
            ctx.moveTo(pts[0].x, pts[0].y); ctx.lineTo(pts[4].x, pts[4].y);
            ctx.stroke();
            const ratio = (a, b, c) => Math.abs(b - a) > 0 ? (Math.abs(c - b) / Math.abs(b - a)).toFixed(3) : '0.000';
            const badge = (p1, p2, txt) => {
                const mx = (p1.x + p2.x)/2, my = (p1.y + p2.y)/2;
                ctx.fillStyle = '#1e222d'; ctx.strokeStyle = color; ctx.font = 'bold 9px monospace';
                const tw = ctx.measureText(txt).width + 6;
                ctx.fillRect(mx - tw/2, my - 7, tw, 14); ctx.strokeRect(mx - tw/2, my - 7, tw, 14);
                ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(txt, mx, my);
            };
            badge(pts[0], pts[2], ratio(rawPts[0].p, rawPts[1].p, rawPts[2].p));
            badge(pts[1], pts[3], ratio(rawPts[1].p, rawPts[2].p, rawPts[3].p));
            badge(pts[0], pts[4], ratio(rawPts[0].p, rawPts[1].p, rawPts[4].p));
            ctx.restore();
        }
    },

    drawABCD: function(ctx, pts, rawPts, color) {
        ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.stroke();
        if (this.settings.showRatios && rawPts.length >= 4) {
            const ab = Math.abs(rawPts[1].p - rawPts[0].p), bc = Math.abs(rawPts[2].p - rawPts[1].p), cd = Math.abs(rawPts[3].p - rawPts[2].p);
            ctx.save(); ctx.font = 'bold 10px monospace'; ctx.fillStyle = '#00FFA3';
            ctx.fillText(`BC/AB: ${ab > 0 ? (bc/ab).toFixed(3) : '0'}`, (pts[1].x+pts[2].x)/2+6, (pts[1].y+pts[2].y)/2);
            ctx.fillText(`CD/BC: ${bc > 0 ? (cd/bc).toFixed(3) : '0'}`, (pts[2].x+pts[3].x)/2+6, (pts[2].y+pts[3].y)/2);
            ctx.restore();
        }
    },

    drawTriangle: function(ctx, pts, color) {
        ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.closePath(); ctx.fill();
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y); ctx.lineTo(pts[2].x, pts[2].y);
        ctx.moveTo(pts[1].x, pts[1].y); ctx.lineTo(pts[3].x, pts[3].y);
        ctx.stroke();
    },

    drawElliott: function(ctx, pts, rawPts, color) {
        ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
        ctx.stroke();
        if (this.settings.showRatios && pts.length >= 3) {
            ctx.save(); ctx.strokeStyle = 'rgba(255,255,255,0.3)'; ctx.setLineDash([2,2]);
            ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y); ctx.lineTo(pts[2].x, pts[2].y); ctx.stroke();
            ctx.restore();
        }
    },

    drawCycles: function(ctx, type, pts, color, canvasWidth, canvasHeight) {
        if (pts.length < 2) return;
        const dx = Math.abs(pts[1].x - pts[0].x);
        if (dx < 6) return;
        ctx.save();
        if (type === 'cycle_lines') {
            ctx.setLineDash([4, 4]);
            for (let x = (pts[0].x % dx); x < canvasWidth; x += dx) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvasHeight); ctx.stroke();
            }
        } else if (type === 'time_cycles') {
            const radius = dx / 2, baseY = pts[0].y;
            for (let cx = (Math.min(pts[0].x, pts[1].x) % dx); cx < canvasWidth + radius; cx += dx) {
                ctx.beginPath(); ctx.arc(cx + radius, baseY, radius, 0, Math.PI, false); ctx.stroke();
            }
        } else if (type === 'sine_line') {
            const amp = Math.abs(pts[1].y - pts[0].y) || 40, midY = pts[0].y, period = dx * 2;
            ctx.beginPath();
            for (let x = 0; x < canvasWidth; x += 3) {
                const y = midY + amp * Math.sin(((x - pts[0].x) / period) * Math.PI * 2);
                if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.stroke();
        }
        ctx.restore();
    },

    drawPointBadge: function(ctx, x, y, label, color, isSelected) {
        ctx.save();
        ctx.beginPath(); ctx.arc(x, y, 11, 0, Math.PI * 2);
        ctx.fillStyle = '#131722'; ctx.fill();
        ctx.strokeStyle = color; ctx.lineWidth = isSelected ? 2 : 1.5; ctx.stroke();
        ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, x, y);
        ctx.restore();
    },

    drawPreview: function(ctx, tool, points, currentMouse, mainChart, mainSeries) {
        const conf = this.toolsConfig[tool];
        if (!conf || points.length === 0) return;
        const screenPts = points.map(pt => this.getScreenPoint(pt, mainChart, mainSeries));
        ctx.save(); ctx.strokeStyle = '#00FFA3'; ctx.lineWidth = 1.8;
        if (screenPts.length > 1) {
            ctx.beginPath(); ctx.moveTo(screenPts[0].x, screenPts[0].y);
            for (let i = 1; i < screenPts.length; i++) ctx.lineTo(screenPts[i].x, screenPts[i].y);
            ctx.stroke();
        }
        const last = screenPts[screenPts.length - 1];
        ctx.beginPath(); ctx.setLineDash([4, 4]); ctx.moveTo(last.x, last.y); ctx.lineTo(currentMouse.x, currentMouse.y); ctx.stroke();
        screenPts.forEach((p, idx) => {
            const label = conf.labels && conf.labels[idx] ? conf.labels[idx] : String(idx + 1);
            this.drawPointBadge(ctx, p.x, p.y, label, '#00FFA3', false);
        });
        const nxt = screenPts.length;
        this.drawPointBadge(ctx, currentMouse.x, currentMouse.y, conf.labels && conf.labels[nxt] ? conf.labels[nxt] : String(nxt + 1), '#00e5ff', true);
        ctx.restore();
    },

    hitTest: function(x, y, d, mainChart, mainSeries) {
        if (!d.points || d.points.length < 2) return false;
        const screenPts = d.points.map(pt => this.getScreenPoint(pt, mainChart, mainSeries));
        const dist = (x1, y1, x2, y2) => Math.hypot(x2 - x1, y2 - y1);
        const segDist = (px, py, x1, y1, x2, y2) => {
            const l2 = (x2 - x1)**2 + (y2 - y1)**2;
            if (l2 === 0) return dist(px, py, x1, y1);
            let t = ((px - x1)*(x2 - x1) + (py - y1)*(y2 - y1)) / l2;
            t = Math.max(0, Math.min(1, t));
            return dist(px, py, x1 + t*(x2 - x1), y1 + t*(y2 - y1));
        };
        for (let i = 0; i < screenPts.length - 1; i++) {
            if (segDist(x, y, screenPts[i].x, screenPts[i].y, screenPts[i+1].x, screenPts[i+1].y) < 8) return true;
        }
        return false;
    }
};