# chart_tools.py
import json
import pandas as pd
import streamlit.components.v1 as components

UP, DOWN = "#26a69a", "#ef5350"

_TPL = r"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>
html,body{margin:0;padding:0;background:#0e1117;overflow:hidden;
  font-family:-apple-system,"Segoe UI",sans-serif}
#app{display:flex;height:__H__px}
#bar{width:42px;background:#111418;border-right:1px solid #1e222d;
  display:flex;flex-direction:column;align-items:center;padding:6px 0;gap:2px}
.tb{width:32px;height:32px;border-radius:6px;display:flex;align-items:center;
  justify-content:center;cursor:pointer;color:#b2b5be;transition:.12s}
.tb:hover{background:#1e222d;color:#fff}
.tb.on{background:rgba(41,98,255,.15);color:#2962ff}
.sep{width:22px;height:1px;background:#1e222d;margin:5px 0}
#wrap{position:relative;flex:1}
#chart{position:absolute;inset:0}
#draw{position:absolute;inset:0;pointer-events:none}
#draw.act{pointer-events:auto;cursor:crosshair}
</style></head><body>
<div id="app">
  <div id="bar"></div>
  <div id="wrap"><div id="chart"></div><canvas id="draw"></canvas></div>
</div>
<script>
const DATA=__DATA__, UP="__UP__", DOWN="__DOWN__", KEY="lwc_dr___KEY__";
const wrap=document.getElementById('wrap');
const chart=LightweightCharts.createChart(document.getElementById('chart'),{
  layout:{background:{color:'#0e1117'},textColor:'#b2b5be',fontSize:11},
  grid:{vertLines:{color:'#171a21'},horzLines:{color:'#171a21'}},
  rightPriceScale:{borderColor:'#1e222d'},
  timeScale:{borderColor:'#1e222d',timeVisible:true,secondsVisible:false},
  crosshair:{mode:0}
});
const series=chart.addCandlestickSeries({upColor:UP,downColor:DOWN,
  borderUpColor:UP,borderDownColor:DOWN,wickUpColor:UP,wickDownColor:DOWN});
series.setData(DATA); chart.timeScale().fitContent();

const S='stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round"';
const TOOLS=[
 {id:'cursor',t:'เคอร์เซอร์',d:'<path d="M12 5v14M5 12h14"/>'},
 {id:'trend', t:'เส้นเทรนด์',d:'<path d="M6 18L18 6"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="6" r="2"/>'},
 {id:'hline', t:'เส้นแนวนอน',d:'<path d="M3 9h18M3 15h18"/>'},
 {id:'fib',   t:'Fibonacci',d:'<path d="M3 5h18M3 10h18M3 15h18M3 20h18"/>'},
 {id:'text',  t:'ข้อความ',  d:'<path d="M5 6h14M12 6v13"/>'},
 {id:'ruler', t:'ไม้บรรทัด',d:'<path d="M3 14L14 3l7 7L10 21z"/><path d="M7.5 10.5l1.5 1.5M10.5 7.5l1.5 1.5M13 13l1.5 1.5"/>'},
 {sep:1},
 {id:'lock',  t:'ล็อกภาพวาด',tg:1,d:'<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8.5 11V8a3.5 3.5 0 017 0v3"/>'},
 {id:'clear', t:'ลบทั้งหมด',ac:1,d:'<path d="M4 7h16M9.5 7V4.5h5V7M7 7l1 13h8l1-13"/>'}
];
const bar=document.getElementById('bar');
TOOLS.forEach(o=>{
  if(o.sep){bar.insertAdjacentHTML('beforeend','<div class="sep"></div>');return;}
  const b=document.createElement('div');
  b.className='tb'; b.title=o.t; b.dataset.id=o.id;
  b.innerHTML='<svg width="19" height="19" viewBox="0 0 24 24" '+S+'>'+o.d+'</svg>';
  b.onclick=()=>{
    if(o.ac){shapes=[];save();return;}
    if(o.tg){locked=!locked;b.classList.toggle('on',locked);return;}
    tool=o.id; draft=null;
    document.querySelectorAll('.tb').forEach(x=>{
      if(!TOOLS.find(z=>z.id===x.dataset.id&&(z.tg||z.ac)))
        x.classList.toggle('on',x.dataset.id===tool);});
    cv.classList.toggle('act',tool!=='cursor');
  };
  bar.appendChild(b);
});
document.querySelector('.tb').classList.add('on');

const cv=document.getElementById('draw'), ctx=cv.getContext('2d');
let tool='cursor', locked=false, draft=null, shapes=[];
try{shapes=JSON.parse(localStorage.getItem(KEY)||"[]")}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(shapes))}catch(e){}};

function fit(){const r=wrap.getBoundingClientRect(),d=devicePixelRatio||1;
  cv.width=r.width*d; cv.height=r.height*d;
  cv.style.width=r.width+'px'; cv.style.height=r.height+'px';
  ctx.setTransform(d,0,0,d,0,0);}
new ResizeObserver(fit).observe(wrap); fit();

const ts=()=>chart.timeScale();
const pt=(x,y)=>({l:ts().coordinateToLogical(x),p:series.coordinateToPrice(y)});
const xy=a=>{const x=ts().logicalToCoordinate(a.l),y=series.priceToCoordinate(a.p);
  return (x==null||y==null)?null:{x,y};};
const nf=v=>Math.abs(v)>=1000?v.toFixed(0):Math.abs(v)>=1?v.toFixed(2):v.toFixed(6);

const FIB=[[0,'#787b86'],[0.236,'#ef5350'],[0.382,'#ff9800'],[0.5,'#4caf50'],
           [0.618,'#26a69a'],[0.786,'#2962ff'],[1,'#787b86']];

function line(a,b,c,w,dash){ctx.save();ctx.strokeStyle=c;ctx.lineWidth=w||1.4;
  if(dash)ctx.setLineDash(dash);ctx.beginPath();ctx.moveTo(a.x,a.y);
  ctx.lineTo(b.x,b.y);ctx.stroke();ctx.restore();}
function tag(x,y,txt,c){ctx.save();ctx.font='11px Segoe UI';
  const w=ctx.measureText(txt).width+8;ctx.fillStyle=c;
  ctx.fillRect(x,y-8,w,16);ctx.fillStyle='#fff';ctx.fillText(txt,x+4,y+3.5);ctx.restore();}
function paint(s){
  const A=xy(s.a), B=s.b?xy(s.b):null; if(!A)return;
  const W=cv.clientWidth;
  if(s.k==='trend'&&B) line(A,B,'#2962ff',1.6);
  else if(s.k==='hline'){line({x:0,y:A.y},{x:W,y:A.y},'#2962ff',1.3,[5,4]);
    tag(W-72,A.y,nf(s.a.p),'#2962ff');}
  else if(s.k==='text'){ctx.save();ctx.font='13px Segoe UI';ctx.fillStyle='#e0e3eb';
    ctx.fillText(s.tx,A.x+4,A.y);ctx.restore();}
  else if(s.k==='fib'&&B){
    const x0=Math.min(A.x,B.x),x1=Math.max(A.x,B.x);
    FIB.forEach(([lv,c])=>{const y=B.y+(A.y-B.y)*lv;
      line({x:x0,y},{x:x1+40,y},c,1.2,[4,3]);
      ctx.save();ctx.font='10px Segoe UI';ctx.fillStyle=c;
      ctx.fillText(lv.toFixed(3)+'  '+nf(s.b.p+(s.a.p-s.b.p)*lv),x1+44,y+3);ctx.restore();});
    line(A,B,'#787b86',1,[2,3]);}
  else if(s.k==='ruler'&&B){
    const d=s.b.p-s.a.p, pc=d/s.a.p*100, up=d>=0, c=up?UP:DOWN;
    ctx.save();
    ctx.fillStyle='rgba('+(up?'38,166,154':'239,83,80')+',.12)';
    ctx.fillRect(A.x,A.y,B.x-A.x,B.y-A.y);ctx.restore();
    line(A,B,c,1.4);
    tag(B.x+6,B.y,nf(d)+' ('+pc.toFixed(2)+'%)  '+Math.abs(Math.round(s.b.l-s.a.l))+' แท่ง',c);}
}
function redraw(){ctx.clearRect(0,0,cv.clientWidth,cv.clientHeight);
  shapes.forEach(paint); if(draft)paint(draft);}
(function loop(){redraw();requestAnimationFrame(loop)})();

const rel=e=>{const r=cv.getBoundingClientRect();return[e.clientX-r.left,e.clientY-r.top]};
cv.addEventListener('mousedown',e=>{
  if(tool==='cursor'||locked)return;
  const[x,y]=rel(e), a=pt(x,y);
  if(tool==='text'){const t=prompt('ข้อความ:');if(t){shapes.push({k:'text',a,tx:t});save();}return;}
  if(tool==='hline'){shapes.push({k:'hline',a});save();return;}
  draft={k:tool,a,b:a};
});
cv.addEventListener('mousemove',e=>{if(!draft)return;const[x,y]=rel(e);draft.b=pt(x,y);});
cv.addEventListener('mouseup',()=>{if(draft){shapes.push(draft);draft=null;save();}});
cv.addEventListener('contextmenu',e=>{
  e.preventDefault(); if(locked)return;
  const[x,y]=rel(e);
  for(let i=shapes.length-1;i>=0;i--){
    const A=xy(shapes[i].a),B=shapes[i].b?xy(shapes[i].b):null;
    const near=q=>q&&Math.hypot(q.x-x,q.y-y)<12;
    if(near(A)||near(B)||(shapes[i].k==='hline'&&A&&Math.abs(A.y-y)<6)){
      shapes.splice(i,1);save();break;}
  }
});
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){draft=null;document.querySelector('.tb').click();}
  if(e.key==='Delete'){shapes=[];save();}
});
</script></body></html>
"""


def render_chart_with_tools(df: pd.DataFrame, height: int = 560,
                            key: str = "main", up: str = UP, down: str = DOWN):
    """แสดงชาร์ตแท่งเทียน + แถบเครื่องมือวาด (คอลัมน์: time/open/high/low/close/volume)"""
    d = df[["time", "open", "high", "low", "close"]].copy()
    d["time"] = pd.to_datetime(d["time"], errors="coerce")
    d = d.dropna()

    if getattr(d["time"].dt, "tz", None) is not None:
        d["time"] = d["time"].dt.tz_convert(None)

    candles = [{
        "time": int(t.timestamp()),
        "open": float(o), "high": float(h),
        "low": float(l), "close": float(c),
    } for t, o, h, l, c in zip(d["time"], d["open"], d["high"], d["low"], d["close"])]

    html = (_TPL
            .replace("__DATA__", json.dumps(candles))
            .replace("__H__", str(height))
            .replace("__UP__", up)
            .replace("__DOWN__", down)
            .replace("__KEY__", str(key)))

    components.html(html, height=height + 4, scrolling=False)
