/* LAVC Elements — motion-graphic element registry (Remotion-Elements-class palette, LAKA styled) */
(() => {
"use strict";
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const eo=p=>1-Math.pow(1-clamp(p),3);
const eio=p=>{p=clamp(p);return p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2;};
const eb=p=>{p=clamp(p);const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2);};
const esc=v=>String(v??'').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
const ph=(p,s,e,ez=eo)=>ez(clamp((p-s)/Math.max(.0001,e-s)));

/* ctx: W,H,U,c(colors),F,px */
function ctx(brandKey,aspect){
  const B=(window.LAVC?LAVC.BRANDS[brandKey]:null)||{colors:{canvas:'#07090D',surface:'#1A1D24',raised:'#23262F',text:'#F5F7FA',body:'#C5C7CE',muted:'#8A8D96',accent:'#3F6EE9',accent2:'#8AA4FF',danger:'#D8574F',hair:'rgba(255,255,255,0.15)',hairSoft:'rgba(255,255,255,0.08)'},wash:''};
  const A=(window.LAVC?LAVC.ASPECTS[aspect]:null)||{w:1920,h:1080};
  return{c:B.colors,wash:B.wash,W:A.w,H:A.h,U:Math.min(A.w,A.h)/108,F:"'Inter',sans-serif",px:n=>`${Math.round(n*100)/100}px`};
}
const wrap=(x,inner)=>`<div style="position:absolute;inset:0;background:${x.c.canvas};overflow:hidden;font-family:${x.F};"><div style="position:absolute;inset:0;background:${x.wash};"></div>${inner}</div>`;
const centerCol=(x,inner,top=0)=>`<div style="position:absolute;left:${x.px(x.W*.08)};right:${x.px(x.W*.08)};top:${top||0};bottom:0;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:${x.px(2.6*x.U)};">${inner}</div>`;

/* hand-drawn wobble path around a rect */
function sketchEllipse(cx,cy,rx,ry,seed){
  let d='';const n=14;
  for(let i=0;i<=n;i++){const a=i/n*Math.PI*2;
    const wob=1+0.06*Math.sin(seed+i*2.7);
    const X=cx+Math.cos(a)*rx*wob,Y=cy+Math.sin(a)*ry*wob;
    d+=(i===0?`M ${X} ${Y}`:` L ${X} ${Y}`);}
  return d;}

const ELEMENTS=[
/* ---------------- TEXT ---------------- */
{id:'kinetic_title',cat:'Text',name:'Kinetic Title',desc:'Word-by-word tumble-in headline.',
 demo:{headline:'Not inspiration. Infrastructure.'},
 render(p,t,x,P){const words=String(P.headline||'').split(/\s+/);
  return wrap(x,centerCol(x,`<div style="display:flex;flex-wrap:wrap;gap:${x.px(2*x.U)} ${x.px(1.8*x.U)};max-width:${x.px(x.W*.84)};">${words.map((w,i)=>{const q=ph(p,.08+i*.09,.34+i*.09,eb);
   return`<span style="display:inline-block;opacity:${Math.min(1,q*1.4)};transform:translateY(${x.px((1-q)*4*x.U)}) rotate(${((1-q)*3).toFixed(1)}deg);font:600 ${x.px(9*x.U)}/1 ${x.F};letter-spacing:-.05em;color:${i===words.length-1?x.c.accent:x.c.text};">${esc(w)}</span>`;}).join('')}</div>`));}},
{id:'circle_marker',cat:'Text',name:'Circle Marker',desc:'Hand-drawn circle around one word.',
 demo:{before:'The bullies knew',mark:'first',after:''},
 render(p,t,x,P){const q=ph(p,.35,.85,eio);
  const inner=`<div style="position:relative;display:flex;gap:${x.px(2*x.U)};align-items:baseline;flex-wrap:wrap;max-width:${x.px(x.W*.84)};font:600 ${x.px(8*x.U)}/1.15 ${x.F};letter-spacing:-.05em;color:${x.c.text};">
    <span style="opacity:${ph(p,.05,.3)}">${esc(P.before||'')}</span>
    <span style="position:relative;opacity:${ph(p,.15,.4)}">${esc(P.mark||'')}
      <svg style="position:absolute;left:-14%;top:-32%;width:128%;height:164%;overflow:visible;" viewBox="0 0 100 60" preserveAspectRatio="none">
        <path d="${sketchEllipse(50,30,46,25,3)}" fill="none" stroke="${x.c.accent}" stroke-width="4" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${1-q}"/></svg></span>
    <span style="opacity:${ph(p,.2,.45)}">${esc(P.after||'')}</span></div>`;
  return wrap(x,centerCol(x,inner));}},
{id:'strike_through',cat:'Text',name:'Strike Through',desc:'Hand-drawn line removes a word; the reframe lands after.',
 demo:{before:'Not a',mark:'milder',after:'disability.',replace:'taxed'},
 render(p,t,x,P){const q=ph(p,.3,.6,eio),rq=ph(p,.62,.85,eb);
  return wrap(x,centerCol(x,`<div style="display:flex;gap:${x.px(2*x.U)};align-items:baseline;flex-wrap:wrap;font:600 ${x.px(8*x.U)}/1.15 ${x.F};letter-spacing:-.05em;color:${x.c.text};max-width:${x.px(x.W*.86)};">
    <span style="opacity:${ph(p,.05,.3)}">${esc(P.before||'')}</span>
    <span style="position:relative;opacity:${ph(p,.1,.35)};color:${x.c.muted};">${esc(P.mark||'')}
      <span style="position:absolute;left:-4%;top:52%;width:${(q*108).toFixed(1)}%;height:${x.px(.6*x.U)};background:${x.c.danger};transform:rotate(-2deg);"></span></span>
    ${P.replace?`<span style="opacity:${rq};transform:translateY(${x.px((1-rq)*2*x.U)});display:inline-block;color:${x.c.accent};">${esc(P.replace)}</span>`:''}
    <span style="opacity:${ph(p,.15,.4)}">${esc(P.after||'')}</span></div>`));}},
{id:'text_marker',cat:'Text',name:'Text Marker',desc:'Highlighter sweep behind a key phrase.',
 demo:{before:'Believe people',mark:'the first time',after:''},
 render(p,t,x,P){const q=ph(p,.35,.7,eio);
  return wrap(x,centerCol(x,`<div style="display:flex;gap:${x.px(2*x.U)};align-items:baseline;flex-wrap:wrap;font:600 ${x.px(8*x.U)}/1.15 ${x.F};letter-spacing:-.05em;color:${x.c.text};max-width:${x.px(x.W*.86)};">
    <span style="opacity:${ph(p,.05,.3)}">${esc(P.before||'')}</span>
    <span style="position:relative;opacity:${ph(p,.12,.36)};"><span style="position:absolute;left:-3%;top:8%;width:${(q*106).toFixed(1)}%;height:92%;background:${x.c.accent};opacity:.32;border-radius:${x.px(.6*x.U)};"></span><span style="position:relative;">${esc(P.mark||'')}</span></span>
    <span style="opacity:${ph(p,.18,.42)}">${esc(P.after||'')}</span></div>`));}},
{id:'word_wheel',cat:'Text',name:'Spinning Word Wheel',desc:'A wheel spins through options and lands on one.',
 demo:{options:['Doctors','Teachers','Family','Bullies'],pick:3},
 render(p,t,x,P){const opts=P.options||[],pick=P.pick??opts.length-1;
  const spin=eio(ph(p,.1,.8,eio));const pos=spin*(opts.length*2+pick);
  const rows=opts.map((o,i)=>{
    let best=99;for(let k=0;k<=Math.ceil(pos/opts.length)+1;k++){const d=Math.abs(pos-(k*opts.length+i));if(d<best)best=d;}
    const dist=best;const sel=p>.8&&i===pick;
    return`<div style="height:${x.px(9*x.U)};display:flex;align-items:center;justify-content:center;font:600 ${x.px(sel?8*x.U:5.4*x.U)}/1 ${x.F};letter-spacing:-.05em;color:${sel?x.c.accent:x.c.muted};opacity:${clamp(1.1-dist*.55)};transform:translateY(${x.px(-dist*0)}) scale(${1-clamp(dist*.14,0,.5)});transition:none;">${esc(o)}</div>`;});
  const idx=Math.round(pos)%opts.length;
  const order=[(idx-1+opts.length)%opts.length,idx,(idx+1)%opts.length];
  return wrap(x,`<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;">${order.map(i=>rows[i]).join('')}</div>`);}},
/* ---------------- DATA ---------------- */
{id:'number_counter',cat:'Data',name:'Number Counter',desc:'Counts to the value; precision is the brand.',
 demo:{number:240720,label:'nodes in the Second Brain'},
 render(p,t,x,P){const v=Math.round((P.number||0)*eio(ph(p,.1,.85,eio)));
  return wrap(x,`<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:${x.px(2.6*x.U)};">
    <div style="font:600 ${x.px(17*x.U)}/0.9 ${x.F};letter-spacing:-.06em;color:${x.c.text};font-variant-numeric:tabular-nums;">${v.toLocaleString()}</div>
    <div style="opacity:${ph(p,.5,.75)};font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div></div>`);}},
{id:'ring_percent',cat:'Data',name:'Proportion Ring',desc:'A percentage drawn as an arc with count-up.',
 demo:{value:74,label:'nothing visible at all'},
 render(p,t,x,P){const q=ph(p,.1,.85,eio),v=(P.value||0)*q,sz=Math.min(x.W,x.H)*.58,R=sz/2-2*x.U,circ=2*Math.PI*R;
  return wrap(x,`<div style="position:absolute;inset:0;display:grid;place-items:center;">
    <svg width="${sz}" height="${sz}"><circle cx="${sz/2}" cy="${sz/2}" r="${R}" fill="none" stroke="${x.c.hairSoft}" stroke-width="${1.2*x.U}"/>
    <circle cx="${sz/2}" cy="${sz/2}" r="${R}" fill="none" stroke="${x.c.accent}" stroke-width="${1.2*x.U}" stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${circ*(1-v/100)}" transform="rotate(-90 ${sz/2} ${sz/2})"/></svg>
    <div style="position:absolute;text-align:center;"><div style="font:600 ${x.px(12*x.U)}/1 ${x.F};letter-spacing:-.06em;color:${x.c.text};">${Math.round(v)}<span style="font-size:.45em;color:${x.c.accent};">%</span></div>
    <div style="margin-top:${x.px(1.4*x.U)};font:600 ${x.px(1.8*x.U)}/1.3 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};max-width:${x.px(sz*.7)};">${esc(P.label||'')}</div></div></div>`);}},
{id:'bar_chart_v',cat:'Data',name:'Vertical Bar Chart',desc:'Bars grow from a drawn baseline, values count.',
 demo:{series:[{label:'Autistic teens',value:46,unit:'%'},{label:'All students',value:11,unit:'%'}],headline:'Bullied in one school year'},
 render(p,t,x,P){return LAVC.renderScene({template:'bar_chart',payload:P,primary_relation:'quantity',id:'el'},p,'dark','16:9',t).replace(/^<div[^>]*>|<\/div>$/g,m=>m);/* full scene reuse */}},
{id:'line_chart',cat:'Data',name:'Line Chart',desc:'A trend line draws itself; the last point gets the badge.',
 demo:{series:[{label:'Mar',value:24},{label:'May',value:31},{label:'Jul',value:52},{label:'Sep',value:74}],headline:'Monthly reach',unit:'K'},
 render(p,t,x,P){const s=(P.series||[]).slice(0,8),max=Math.max(...s.map(d=>d.value))*1.15;
  const L=x.W*.12,R=x.W*.88,T=x.H*.3,B=x.H*.78,q=ph(p,.15,.75,eio);
  const pts=s.map((d,i)=>[L+(R-L)*i/(s.length-1),B-(B-T)*(d.value/max)]);
  const path=pts.map((pt,i)=>(i?'L':'M')+pt[0]+' '+pt[1]).join(' ');
  const dots=pts.map((pt,i)=>{const dq=ph(p,.2+i*(.5/s.length),.3+i*(.5/s.length),eb);
   return`<circle cx="${pt[0]}" cy="${pt[1]}" r="${.9*x.U}" fill="${x.c.canvas}" stroke="${x.c.accent}" stroke-width="${.4*x.U}" opacity="${dq}"/>`;}).join('');
  const last=pts[pts.length-1],bq=ph(p,.78,.95,eb);
  const labels=s.map((d,i)=>`<div style="position:absolute;left:${x.px(pts[i][0]-6*x.U)};top:${x.px(B+2*x.U)};width:${x.px(12*x.U)};text-align:center;font:600 ${x.px(1.7*x.U)}/1 ${x.F};letter-spacing:.1em;text-transform:uppercase;color:${x.c.muted};opacity:${ph(p,.2+i*.08,.34+i*.08)};">${esc(d.label)}</div>`).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(L)};top:${x.px(x.H*.14)};font:600 ${x.px(4.4*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};opacity:${ph(p,.04,.25)};">${esc(P.headline||'')}</div>
   <svg style="position:absolute;inset:0;" width="${x.W}" height="${x.H}">
    <line x1="${L}" y1="${B}" x2="${L+(R-L)*ph(p,.08,.3,eio)}" y2="${B}" stroke="${x.c.hair}" stroke-width="1"/>
    <path d="${path}" fill="none" stroke="${x.c.accent}" stroke-width="${.5*x.U}" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${1-q}"/>${dots}</svg>${labels}
   <div style="position:absolute;left:${x.px(last[0]-5*x.U)};top:${x.px(last[1]-6.4*x.U)};padding:${x.px(.9*x.U)} ${x.px(1.6*x.U)};border-radius:${x.px(.8*x.U)};background:${x.c.accent};font:600 ${x.px(2.2*x.U)}/1 ${x.F};color:#fff;opacity:${bq};transform:scale(${.8+.2*bq});">${esc(s[s.length-1].value)}${esc(P.unit||'')}</div>`);}},
{id:'pie_chart',cat:'Data',name:'Pie Chart',desc:'Slices sweep in, legend counts alongside.',
 demo:{series:[{label:'Focused work',value:42},{label:'Meetings',value:26},{label:'Planning',value:18},{label:'Admin',value:14}],headline:'How we spend a workday'},
 render(p,t,x,P){const s=(P.series||[]).slice(0,6),tot=s.reduce((a,d)=>a+d.value,0);
  const cx=x.W*.32,cy=x.H*.55,R=Math.min(x.W,x.H)*.26,q=ph(p,.12,.7,eio);
  const shades=[x.c.accent,x.c.muted,x.c.raised,'#3A3F4C','#565B68','#6E7480'];
  let a0=-Math.PI/2,paths='';
  s.forEach((d,i)=>{const sweep=(d.value/tot)*Math.PI*2*q,a1=a0+sweep;
   const large=sweep>Math.PI?1:0;
   paths+=`<path d="M ${cx} ${cy} L ${cx+Math.cos(a0)*R} ${cy+Math.sin(a0)*R} A ${R} ${R} 0 ${large} 1 ${cx+Math.cos(a1)*R} ${cy+Math.sin(a1)*R} Z" fill="${shades[i%shades.length]}" stroke="${x.c.canvas}" stroke-width="${.4*x.U}"/>`;a0=a1;});
  const legend=s.map((d,i)=>{const lq=ph(p,.3+i*.1,.46+i*.1);
   return`<div style="display:flex;align-items:center;justify-content:space-between;gap:${x.px(2*x.U)};padding:${x.px(1.3*x.U)} ${x.px(2*x.U)};border-radius:${x.px(.8*x.U)};background:${i===0?x.c.accent:x.c.surface};opacity:${lq};transform:translateX(${x.px((1-lq)*2*x.U)});min-width:${x.px(26*x.U)};">
    <span style="font:600 ${x.px(2.1*x.U)}/1 ${x.F};color:${i===0?'#fff':x.c.body};">${esc(d.label)}</span>
    <span style="font:600 ${x.px(2.1*x.U)}/1 ${x.F};color:${i===0?'#fff':x.c.text};">${Math.round(d.value*q)}%</span></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.08)};top:${x.px(x.H*.13)};font:600 ${x.px(4.4*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};opacity:${ph(p,.04,.25)};">${esc(P.headline||'')}</div>
   <svg style="position:absolute;inset:0;" width="${x.W}" height="${x.H}">${paths}</svg>
   <div style="position:absolute;left:${x.px(x.W*.58)};top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:${x.px(1.2*x.U)};">${legend}</div>`);}},
/* ---------------- STORYTELLING ---------------- */
{id:'chat_messages',cat:'Storytelling',name:'On-Screen Messages',desc:'iMessage-style exchange, staggered reveals.',
 demo:{messages:[{side:'l',text:'You look fine to me.'},{side:'r',text:'That\u2019s the point. You can\u2019t see it.'},{side:'l',text:'So how bad can it be?'},{side:'r',text:'96% of chronic illness is invisible.'}]},
 render(p,t,x,P){const ms=(P.messages||[]).slice(0,6);
  const rows=ms.map((m,i)=>{const q=ph(p,.1+i*.18,.28+i*.18,eb);const right=m.side==='r';
   return`<div style="display:flex;justify-content:${right?'flex-end':'flex-start'};opacity:${q};transform:translateY(${x.px((1-q)*2.4*x.U)}) scale(${.92+.08*q});">
    <div style="max-width:${x.px(x.W*.44)};padding:${x.px(1.8*x.U)} ${x.px(2.6*x.U)};border-radius:${x.px(2.6*x.U)};border-bottom-${right?'right':'left'}-radius:${x.px(.7*x.U)};background:${right?x.c.accent:x.c.raised};font:400 ${x.px(2.9*x.U)}/1.3 ${x.F};letter-spacing:-.01em;color:${right?'#fff':x.c.text};">${esc(m.text)}</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.18)};right:${x.px(x.W*.18)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(1.8*x.U)};">${rows}</div>`);}},
{id:'social_comments',cat:'Storytelling',name:'Social Comments Popup',desc:'Comment cards pop over the canvas with hearts ticking.',
 demo:{comments:[{user:'@teacher_km',text:'We saw it years before the paperwork did.'},{user:'@lateDXclub',text:'Diagnosed at 44. The bullies knew at 9.'},{user:'@ryanperez',text:'Detection without support is just targeting.',hot:true}],likes:1284},
 render(p,t,x,P){const cs=(P.comments||[]).slice(0,4);
  const rows=cs.map((cm,i)=>{const q=ph(p,.12+i*.22,.32+i*.22,eb);
   const off=(i%2?1:-1)*x.U*3;
   return`<div style="position:relative;left:${x.px(off)};max-width:${x.px(x.W*.5)};padding:${x.px(2*x.U)} ${x.px(2.6*x.U)};border-radius:${x.px(1.6*x.U)};background:${cm.hot?x.c.raised:x.c.surface};border:1px solid ${cm.hot?x.c.accent:x.c.hairSoft};opacity:${q};transform:translateY(${x.px((1-q)*3*x.U)}) scale(${.9+.1*q});">
    <div style="display:flex;align-items:center;gap:${x.px(1.4*x.U)};"><div style="width:${x.px(3.2*x.U)};height:${x.px(3.2*x.U)};border-radius:50%;background:${cm.hot?x.c.accent:x.c.muted};"></div>
    <span style="font:600 ${x.px(1.9*x.U)}/1 ${x.F};color:${cm.hot?x.c.accent2:x.c.muted};">${esc(cm.user)}</span></div>
    <div style="margin-top:${x.px(1.2*x.U)};font:400 ${x.px(2.6*x.U)}/1.35 ${x.F};color:${x.c.text};">${esc(cm.text)}</div></div>`;}).join('');
  const lq=ph(p,.7,.95,eio),likes=Math.round((P.likes||0)*lq);
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.24)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2*x.U)};">${rows}</div>
   <div style="position:absolute;right:${x.px(x.W*.1)};bottom:${x.px(x.H*.14)};display:flex;align-items:center;gap:${x.px(1.4*x.U)};opacity:${lq};transform:scale(${.85+.15*lq});">
    <div style="font-size:${x.px(3.6*x.U)};color:${x.c.danger};">\u2665</div>
    <div style="font:600 ${x.px(2.8*x.U)}/1 ${x.F};color:${x.c.text};font-variant-numeric:tabular-nums;">${likes.toLocaleString()}</div></div>`);}},
{id:'news_highlight',cat:'Storytelling',name:'News Article Highlight',desc:'Framed article; passages get the marker as the camera settles.',
 demo:{kicker:'ARCHIVES OF PEDIATRICS',headline:'46% of autistic teens bullied in a single school year',body:'compared to roughly 11 percent of students overall \u2014 nearly five times the rate, before most had any diagnosis at all.',mark:'nearly five times the rate'},
 render(p,t,x,P){const q=ph(p,.05,.3),hq=ph(p,.5,.8,eio);
  const bodyTxt=esc(P.body||'').replace(esc(P.mark||''),`<span style="position:relative;"><span style="position:absolute;left:-1%;top:6%;width:${(hq*102).toFixed(1)}%;height:90%;background:${x.c.accent};opacity:.35;"></span><span style="position:relative;">${esc(P.mark||'')}</span></span>`);
  const drift=1.03-0.03*ph(p,0,1,eio);
  return wrap(x,`<div style="position:absolute;inset:0;display:grid;place-items:center;">
   <div style="width:${x.px(x.W*.62)};padding:${x.px(4*x.U)} ${x.px(4.6*x.U)};background:#F5F3EC;border-radius:${x.px(1*x.U)};opacity:${q};transform:scale(${drift}) rotate(-0.5deg);box-shadow:0 ${x.px(3*x.U)} ${x.px(9*x.U)} rgba(0,0,0,.5);">
    <div style="font:600 ${x.px(1.5*x.U)}/1 ${x.F};letter-spacing:.16em;color:#8A8478;border-bottom:1px solid #D8D4C8;padding-bottom:${x.px(1.2*x.U)};">${esc(P.kicker||'')}</div>
    <div style="margin-top:${x.px(2*x.U)};font:600 ${x.px(4.2*x.U)}/1.12 Georgia,serif;letter-spacing:-.02em;color:#14120E;">${esc(P.headline||'')}</div>
    <div style="margin-top:${x.px(1.8*x.U)};font:400 ${x.px(2.3*x.U)}/1.5 Georgia,serif;color:#3B382F;">${bodyTxt}</div></div></div>`);}},
/* ---------------- MEDIA ---------------- */
{id:'image_reveal',cat:'Media',name:'Image Reveal (Ken Burns)',desc:'Drop any image/SVG URL; slow dolly inside a locked frame, notch caption.',
 demo:{src:'',caption:'Drop an image URL into payload.src'},
 render(p,t,x,P){const q=ph(p,.05,.35),scale=1.08-0.06*ph(p,0,1,eio);
  const media=P.src?`<img src="${esc(P.src)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(.85) contrast(.92);"/>`
   :`<div style="position:absolute;inset:0;background:linear-gradient(135deg,${x.c.raised},${x.c.surface});display:grid;place-items:center;"><div style="font:600 ${x.px(2.4*x.U)}/1.4 ${x.F};letter-spacing:.1em;text-transform:uppercase;color:${x.c.muted};text-align:center;">Image slot<br/>payload.src = url \u00b7 png / jpg / svg</div></div>`;
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.08)};right:${x.px(x.W*.08)};top:${x.px(x.H*.12)};bottom:${x.px(x.H*.16)};border-radius:${x.px(2.4*x.U)};overflow:hidden;opacity:${q};">
    <div style="position:absolute;inset:0;transform:scale(${scale});transform-origin:60% 40%;">${media}</div>
    <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 55%,rgba(7,9,13,.82));"></div>
    <div style="position:absolute;left:${x.px(2.6*x.U)};bottom:${x.px(2.2*x.U)};opacity:${ph(p,.4,.65)};font:600 ${x.px(2.6*x.U)}/1.2 ${x.F};letter-spacing:-.02em;color:#F5F7FA;">${esc(P.caption||'')}</div>
    <div style="position:absolute;right:${x.px(2*x.U)};bottom:${x.px(2*x.U)};width:${x.px(5*x.U)};height:${x.px(5*x.U)};border-radius:50%;background:${x.c.accent};display:grid;place-items:center;font:600 ${x.px(2.6*x.U)}/1 ${x.F};color:#fff;opacity:${ph(p,.55,.8,eb)};">\u2192</div></div>`);}},
{id:'polaroids',cat:'Media',name:'Polaroid Stack',desc:'Instant photos deal onto the canvas with taped corners.',
 demo:{photos:[{src:'',caption:'grade four'},{src:'',caption:'diagnosed at 41'},{src:'',caption:'the keynote'}]},
 render(p,t,x,P){const phs=(P.photos||[]).slice(0,4);
  const cards=phs.map((f,i)=>{const q=ph(p,.12+i*.22,.36+i*.22,eb);
   const rot=(i-1)*7,offX=(i-(phs.length-1)/2)*x.W*.17;
   const img=f.src?`<img src="${esc(f.src)}" style="width:100%;height:100%;object-fit:cover;filter:saturate(.85) contrast(.92);"/>`:`<div style="width:100%;height:100%;background:linear-gradient(135deg,${x.c.raised},${x.c.muted});"></div>`;
   return`<div style="position:absolute;left:50%;top:46%;width:${x.px(26*x.U)};transform:translate(calc(-50% + ${x.px(offX)}),-50%) rotate(${rot}deg) translateY(${x.px((1-q)*8*x.U)});opacity:${q};background:#F5F3EC;padding:${x.px(1.4*x.U)} ${x.px(1.4*x.U)} ${x.px(4.4*x.U)};box-shadow:0 ${x.px(2*x.U)} ${x.px(6*x.U)} rgba(0,0,0,.45);">
    <div style="width:100%;aspect-ratio:1;overflow:hidden;">${img}</div>
    <div style="margin-top:${x.px(1.4*x.U)};font:400 ${x.px(2*x.U)}/1 cursive;color:#3B382F;text-align:center;">${esc(f.caption||'')}</div>
    <div style="position:absolute;left:38%;top:${x.px(-1.2*x.U)};width:24%;height:${x.px(2.2*x.U)};background:rgba(220,214,190,.85);transform:rotate(${-rot/2}deg);"></div></div>`;}).join('');
  return wrap(x,cards);}},
];

/* ---------------- QUANTITY (truth-contract morphologies) ---------------- */
ELEMENTS.push(
{id:'pictogram',cat:'Quantity',name:'Pictogram Count',desc:'Exact count: n of m units filled \u2014 never a fake chart.',
 demo:{count:3,total:5,label:'clients renewed'},
 render(p,t,x,P){const m=P.total||5,n=Math.min(P.count||0,m),sz=8*x.U,gap=2.4*x.U;
  const row=Array.from({length:m},(_,i)=>{const q=ph(p,.1+i*.1,.28+i*.1,eb);const on=i<n&&p>.45+i*.08;
   return`<div style="width:${x.px(sz)};height:${x.px(sz)};border-radius:50%;border:${x.px(.35*x.U)} solid ${on?x.c.accent:x.c.hair};background:${on?x.c.accent:'transparent'};opacity:${q};transform:scale(${.7+.3*q});"></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${x.px(3.4*x.U)};">
   <div style="display:flex;gap:${x.px(gap)};">${row}</div>
   <div style="opacity:${ph(p,.6,.85)};font:600 ${x.px(3.4*x.U)}/1 ${x.F};letter-spacing:-.03em;color:${x.c.text};">${n} of ${m} <span style="color:${x.c.muted};">${esc(P.label||'')}</span></div></div>`);}},
{id:'progress_bar',cat:'Quantity',name:'Progress Bar',desc:'Completion toward a target \u2014 not a proportion of people.',
 demo:{value:60,label:'of the project complete'},
 render(p,t,x,P){const q=ph(p,.15,.8,eio),v=(P.value||0)*q;
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.14)};right:${x.px(x.W*.14)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.6*x.U)};">
   <div style="font:600 ${x.px(10*x.U)}/1 ${x.F};letter-spacing:-.06em;color:${x.c.text};">${Math.round(v)}<span style="color:${x.c.accent};font-size:.5em;">%</span></div>
   <div style="height:${x.px(2.6*x.U)};background:${x.c.hairSoft};border-radius:999px;overflow:hidden;"><div style="width:${v}%;height:100%;background:${x.c.accent};border-radius:999px;"></div></div>
   <div style="font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div></div>`);}},
{id:'stepper',cat:'Quantity',name:'Progress Stepper',desc:'Instructions as numbered actions, activating in order.',
 demo:{items:['Research','Design','Build'],active:2},
 render(p,t,x,P){const its=(P.items||[]).slice(0,5);
  const cells=its.map((it,i)=>{const q=ph(p,.1+i*.16,.3+i*.16,eb);const on=p>.35+i*.2;
   return`<div style="display:flex;flex-direction:column;align-items:center;gap:${x.px(1.6*x.U)};opacity:${q};min-width:${x.px(20*x.U)};">
    <div style="width:${x.px(6*x.U)};height:${x.px(6*x.U)};border-radius:50%;display:grid;place-items:center;border:${x.px(.3*x.U)} solid ${on?x.c.accent:x.c.hair};background:${on?x.c.accent:'transparent'};font:600 ${x.px(2.6*x.U)}/1 ${x.F};color:${on?'#fff':x.c.muted};">${i+1}</div>
    <div style="font:600 ${x.px(2.4*x.U)}/1 ${x.F};letter-spacing:-.02em;color:${on?x.c.text:x.c.muted};">${esc(it)}</div></div>`;}).join(`<div style="flex:1;height:1px;background:${x.c.hair};margin-top:${x.px(-4*x.U)};max-width:${x.px(12*x.U)};"></div>`);
  return wrap(x,`<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:${x.px(2*x.U)};padding:0 ${x.px(x.W*.1)};">${cells}</div>`);}},
{id:'delta',cat:'Quantity',name:'Delta (Old \u2192 New)',desc:'Change between two states \u2014 the honest form of \u201cincreased 37%\u201d.',
 demo:{from:'$1M',to:'$2M',label:'revenue, over four years'},
 render(p,t,x,P){const lq=ph(p,.08,.3),aq=ph(p,.3,.55,eio),rq=ph(p,.5,.78,eb);
  return wrap(x,`<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${x.px(3*x.U)};">
   <div style="display:flex;align-items:center;gap:${x.px(4*x.U)};">
    <div style="opacity:${lq};font:600 ${x.px(9*x.U)}/1 ${x.F};letter-spacing:-.05em;color:${x.c.muted};">${esc(P.from||'')}</div>
    <div style="width:${x.px(14*x.U*aq)};height:${x.px(.4*x.U)};background:${x.c.accent};"></div>
    <div style="opacity:${aq};font:600 ${x.px(4.4*x.U)}/1 ${x.F};color:${x.c.accent};">\u2192</div>
    <div style="opacity:${rq};transform:scale(${.8+.2*rq});font:600 ${x.px(12*x.U)}/1 ${x.F};letter-spacing:-.06em;color:${x.c.text};">${esc(P.to||'')}</div></div>
   <div style="opacity:${ph(p,.68,.9)};font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div></div>`);}},
{id:'ranked_bars',cat:'Quantity',name:'Ranked Bars',desc:'Ranking as an ordered horizontal list.',
 demo:{series:[{label:'Bullies',value:96},{label:'Teachers',value:41},{label:'Doctors',value:22}],headline:'Who noticed first'},
 render(p,t,x,P){const s=(P.series||[]).slice(0,6),max=Math.max(...s.map(d=>d.value));
  const rows=s.map((d,i)=>{const q=ph(p,.15+i*.14,.5+i*.14,eio);
   return`<div style="display:flex;align-items:center;gap:${x.px(2.4*x.U)};">
    <div style="width:${x.px(16*x.U)};font:600 ${x.px(2.4*x.U)}/1 ${x.F};color:${x.c.body};text-align:right;">${esc(d.label)}</div>
    <div style="flex:1;height:${x.px(3.6*x.U)};background:${x.c.hairSoft};border-radius:${x.px(.7*x.U)};overflow:hidden;"><div style="width:${(d.value/max*100*q).toFixed(1)}%;height:100%;background:${i===0?x.c.accent:x.c.raised};border:1px solid ${i===0?x.c.accent:x.c.hair};"></div></div>
    <div style="min-width:${x.px(7*x.U)};font:600 ${x.px(2.6*x.U)}/1 ${x.F};color:${x.c.text};opacity:${q};">${Math.round(d.value*q)}</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.12)};right:${x.px(x.W*.12)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.2*x.U)};">
   <div style="font:600 ${x.px(4*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};opacity:${ph(p,.04,.24)};margin-bottom:${x.px(1.5*x.U)};">${esc(P.headline||'')}</div>${rows}</div>`);}},
{id:'dot_plot',cat:'Quantity',name:'Dot Plot',desc:'Distribution as positioned marks, no invented axes.',
 demo:{values:[.12,.2,.28,.31,.38,.42,.45,.51,.55,.58,.62,.7,.78,.9],label:'age at diagnosis'},
 render(p,t,x,P){const vs=P.values||[];const L=x.W*.14,R=x.W*.86,B=x.H*.6;
  const dots=vs.map((v,i)=>{const q=ph(p,.12+i*.05,.28+i*.05,eb);
   let stack=0;for(let k=0;k<i;k++)if(Math.abs(vs[k]-v)<.05)stack++;
   return`<div style="position:absolute;left:${x.px(L+(R-L)*v-1.4*x.U)};top:${x.px(B-stack*3.4*x.U-1.4*x.U)};width:${x.px(2.8*x.U)};height:${x.px(2.8*x.U)};border-radius:50%;background:${x.c.accent};opacity:${q*.9};transform:scale(${.6+.4*q});"></div>`;}).join('');
  return wrap(x,`${dots}<div style="position:absolute;left:${x.px(L)};right:${x.px(x.W-R)};top:${x.px(B+2.4*x.U)};height:1px;background:${x.c.hair};transform:scaleX(${ph(p,.05,.3,eio)});"></div>
   <div style="position:absolute;left:${x.px(L)};top:${x.px(B+4*x.U)};font:600 ${x.px(1.9*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};opacity:${ph(p,.5,.7)};">${esc(P.label||'')}</div>`);}},
/* ---------------- STRUCTURE ---------------- */
{id:'triptych',cat:'Structure',name:'Triptych',desc:'Exactly three peer concepts \u2014 three columns, equal status.',
 demo:{items:[{title:'Autistic',sub:'Pattern depth'},{title:'ADHD',sub:'Idea velocity'},{title:'Dyslexic',sub:'Systems sight'}]},
 render(p,t,x,P){const its=(P.items||[]).slice(0,3);
  const cols=its.map((it,i)=>{const q=ph(p,.12+i*.16,.36+i*.16,eb);
   return`<div style="flex:1;padding:${x.px(4*x.U)} ${x.px(3*x.U)};border:1px solid ${x.c.hairSoft};border-radius:${x.px(1.8*x.U)};background:${x.c.surface};opacity:${q};transform:translateY(${x.px((1-q)*3*x.U)});display:flex;flex-direction:column;gap:${x.px(1.6*x.U)};align-items:center;text-align:center;">
    <div style="font:600 ${x.px(4.2*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};">${esc(it.title)}</div>
    <div style="font:600 ${x.px(1.9*x.U)}/1.3 ${x.F};letter-spacing:.1em;text-transform:uppercase;color:${x.c.accent2};">${esc(it.sub||'')}</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.1)};right:${x.px(x.W*.1)};top:0;bottom:0;display:flex;align-items:center;gap:${x.px(3*x.U)};">${cols}</div>`);}},
{id:'grid_cards',cat:'Structure',name:'Card Grid',desc:'Four to eight equal-status items.',
 demo:{items:['Chronic pain','Autism','ADHD','PTSD','Lupus','Long COVID','Depression','Brain injury']},
 render(p,t,x,P){const its=(P.items||[]).slice(0,8),cols=4;
  const cells=its.map((it,i)=>{const q=ph(p,.1+i*.08,.28+i*.08,eb);
   return`<div style="padding:${x.px(2.6*x.U)} ${x.px(2*x.U)};border:1px solid ${x.c.hairSoft};border-radius:${x.px(1.4*x.U)};background:${x.c.surface};opacity:${q};transform:scale(${.9+.1*q});display:grid;place-items:center;text-align:center;font:600 ${x.px(2.4*x.U)}/1.2 ${x.F};letter-spacing:-.02em;color:${x.c.text};">${esc(it)}</div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.12)};right:${x.px(x.W*.12)};top:0;bottom:0;display:grid;grid-template-columns:repeat(${cols},1fr);gap:${x.px(2*x.U)};align-content:center;">${cells}</div>`);}},
{id:'flow_diagram',cat:'Structure',name:'Flow Diagram',desc:'Process as nodes and drawn arrows.',
 demo:{items:['Signal','Detection','Support']},
 render(p,t,x,P){const its=(P.items||[]).slice(0,4),n=its.length;
  const cw=18*x.U,total=n*cw+(n-1)*12*x.U,L=(x.W-total)/2,cy=x.H*.5;
  let out='';its.forEach((it,i)=>{const q=ph(p,.12+i*.2,.34+i*.2,eb);const X=L+i*(cw+12*x.U);
   out+=`<div style="position:absolute;left:${x.px(X)};top:${x.px(cy-5*x.U)};width:${x.px(cw)};height:${x.px(10*x.U)};display:grid;place-items:center;border:1px solid ${i===n-1?x.c.accent:x.c.hairSoft};border-radius:${x.px(1.6*x.U)};background:${i===n-1?x.c.raised:x.c.surface};opacity:${q};transform:scale(${.85+.15*q});font:600 ${x.px(2.7*x.U)}/1 ${x.F};letter-spacing:-.02em;color:${x.c.text};">${esc(it)}</div>`;
   if(i<n-1){const aq=ph(p,.26+i*.2,.42+i*.2,eio);
    out+=`<div style="position:absolute;left:${x.px(X+cw+2*x.U)};top:${x.px(cy-.2*x.U)};width:${x.px(8*x.U*aq)};height:${x.px(.4*x.U)};background:${x.c.accent};"></div><div style="position:absolute;left:${x.px(X+cw+2*x.U+8*x.U*aq)};top:${x.px(cy-2*x.U)};opacity:${aq};font:600 ${x.px(3.4*x.U)}/1 ${x.F};color:${x.c.accent};">\u2192</div>`;}});
  return wrap(x,out);}},
{id:'equation',cat:'Structure',name:'Equation',desc:'Formula or dependency: A + B \u2192 C.',
 demo:{a:'Detection',b:'Support',c:'Belonging'},
 render(p,t,x,P){const seg=(txt,d,hot)=>{const q=ph(p,d,d+.2,eb);
   return`<div style="opacity:${q};transform:scale(${.85+.15*q});padding:${x.px(2.4*x.U)} ${x.px(3.6*x.U)};border:1px solid ${hot?x.c.accent:x.c.hairSoft};border-radius:${x.px(1.6*x.U)};background:${hot?x.c.raised:x.c.surface};font:600 ${x.px(4*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};">${esc(txt)}</div>`;};
  const op=(ch,d)=>`<div style="opacity:${ph(p,d,d+.15)};font:600 ${x.px(5*x.U)}/1 ${x.F};color:${x.c.accent};">${ch}</div>`;
  return wrap(x,`<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:${x.px(3*x.U)};">${seg(P.a,0.08)}${op('+',0.26)}${seg(P.b,0.34)}${op('\u2192',0.52)}${seg(P.c,0.62,true)}</div>`);}},
{id:'parts_diagram',cat:'Structure',name:'Parts Diagram',desc:'Composition: a container and its components.',
 demo:{parent:'The Second Brain',items:['Notes','Links','Patterns','Prompts']},
 render(p,t,x,P){const its=(P.items||[]).slice(0,6),pq=ph(p,.06,.28,eio);
  const cells=its.map((it,i)=>{const q=ph(p,.3+i*.12,.48+i*.12,eb);
   return`<div style="padding:${x.px(2*x.U)};border:1px solid ${x.c.hair};border-radius:${x.px(1.2*x.U)};background:${x.c.raised};opacity:${q};transform:scale(${.85+.15*q});display:grid;place-items:center;font:600 ${x.px(2.3*x.U)}/1.2 ${x.F};color:${x.c.text};">${esc(it)}</div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.16)};right:${x.px(x.W*.16)};top:${x.px(x.H*.18)};bottom:${x.px(x.H*.18)};border:${x.px(.3*x.U)} solid ${x.c.accent};border-radius:${x.px(2.4*x.U)};opacity:${pq};transform:scale(${.94+.06*pq});padding:${x.px(3*x.U)};">
   <div style="font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.accent2};">${esc(P.parent||'')}</div>
   <div style="margin-top:${x.px(2.4*x.U)};display:grid;grid-template-columns:repeat(2,1fr);gap:${x.px(2*x.U)};height:70%;">${cells}</div></div>`);}},
/* ---------------- STATE & CHANGE ---------------- */
{id:'versus',cat:'State & Change',name:'Versus',desc:'Opposition: A \u2194 B closing on each other.',
 demo:{a:'Inspiration',b:'Infrastructure'},
 render(p,t,x,P){const q=ph(p,.1,.5,eio),fq=ph(p,.55,.8,eb);
  return wrap(x,`<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
   <div style="transform:translateX(${x.px(-(1-q)*14*x.U)});opacity:${q};font:600 ${x.px(7.2*x.U)}/1 ${x.F};letter-spacing:-.05em;color:${x.c.muted};">${esc(P.a)}</div>
   <div style="margin:0 ${x.px(4*x.U)};opacity:${fq};transform:scale(${.7+.3*fq});width:${x.px(8*x.U)};height:${x.px(8*x.U)};border-radius:50%;border:${x.px(.35*x.U)} solid ${x.c.accent};display:grid;place-items:center;font:600 ${x.px(2.6*x.U)}/1 ${x.F};color:${x.c.accent};">VS</div>
   <div style="transform:translateX(${x.px((1-q)*14*x.U)});opacity:${q};font:600 ${x.px(7.2*x.U)}/1 ${x.F};letter-spacing:-.05em;color:${x.c.text};">${esc(P.b)}</div></div>`);}},
{id:'check_x',cat:'State & Change',name:'Accept / Reject',desc:'Items receive a drawn check or X verdict.',
 demo:{items:[{text:'Believe people first',ok:true},{text:'Demand proof',ok:false},{text:'Skip the audit',ok:true}]},
 render(p,t,x,P){const its=(P.items||[]).slice(0,4);
  const rows=its.map((it,i)=>{const q=ph(p,.1+i*.18,.3+i*.18),vq=ph(p,.32+i*.18,.48+i*.18,eb);
   const mark=it.ok?`<span style="color:#3FA46A;">\u2713</span>`:`<span style="color:${x.c.danger};">\u2715</span>`;
   return`<div style="display:flex;align-items:center;gap:${x.px(2.6*x.U)};opacity:${q};transform:translateY(${x.px((1-q)*2*x.U)});">
    <div style="width:${x.px(5.4*x.U)};height:${x.px(5.4*x.U)};border-radius:${x.px(1.2*x.U)};border:1px solid ${x.c.hair};display:grid;place-items:center;font:600 ${x.px(3.2*x.U)}/1 ${x.F};opacity:${vq};transform:scale(${.6+.4*vq});">${mark}</div>
    <div style="font:600 ${x.px(3.4*x.U)}/1.2 ${x.F};letter-spacing:-.03em;color:${it.ok?x.c.text:x.c.muted};${it.ok?'':'text-decoration:line-through;'}">${esc(it.text)}</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.2)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.6*x.U)};">${rows}</div>`);}},
{id:'accumulation',cat:'State & Change',name:'Accumulation',desc:'Repeated units collect into a stack \u2014 \u201ccosts kept piling up\u201d.',
 demo:{count:14,label:'unpaid energy, day after day'},
 render(p,t,x,P){const n=P.count||12,cols=7,bw=6*x.U,bh=3*x.U,L=x.W/2-cols*bw/2,B=x.H*.66;
  const blocks=Array.from({length:n},(_,i)=>{const q=ph(p,.08+i*(.7/n),.2+i*(.7/n),eio);
   const col=i%cols,row=Math.floor(i/cols);
   return`<div style="position:absolute;left:${x.px(L+col*bw)};top:${x.px(B-row*bh-bh+(1-q)*-10*x.U)};width:${x.px(bw-.6*x.U)};height:${x.px(bh-.6*x.U)};border-radius:${x.px(.4*x.U)};background:${row>0?x.c.accent:x.c.raised};border:1px solid ${x.c.hair};opacity:${q};"></div>`;}).join('');
  return wrap(x,`${blocks}<div style="position:absolute;left:0;right:0;top:${x.px(B+3*x.U)};text-align:center;opacity:${ph(p,.65,.9)};font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div>`);}},
{id:'ripple',cat:'State & Change',name:'Ripple / Propagation',desc:'One origin, controlled expanding rings \u2014 \u201cthe idea spread\u201d.',
 demo:{label:'one keynote, outward'},
 render(p,t,x,P){const cx=x.W/2,cy=x.H*.48;
  const rings=[0,1,2,3].map(i=>{const q=ph(p,.12+i*.16,.65+i*.16,eio);
   const R=q*Math.min(x.W,x.H)*.34;
   return`<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${x.c.accent}" stroke-width="${.3*x.U}" opacity="${(1-q)*.8}"/>`;}).join('');
  return wrap(x,`<svg style="position:absolute;inset:0;" width="${x.W}" height="${x.H}">${rings}</svg>
   <div style="position:absolute;left:${x.px(cx-1.6*x.U)};top:${x.px(cy-1.6*x.U)};width:${x.px(3.2*x.U)};height:${x.px(3.2*x.U)};border-radius:50%;background:${x.c.accent};transform:scale(${1+.15*Math.sin(t*3)});"></div>
   <div style="position:absolute;left:0;right:0;top:${x.px(x.H*.78)};text-align:center;opacity:${ph(p,.5,.75)};font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div>`);}},
{id:'merge_branch',cat:'State & Change',name:'Merge / Branch',desc:'Paths converging into one \u2014 or one splitting.',
 demo:{inputs:['Autistic','ADHD','Dyslexic'],out:'One operating system'},
 render(p,t,x,P){const ins=(P.inputs||[]).slice(0,4),cy=x.H*.5,jx=x.W*.56,q=ph(p,.2,.7,eio);
  let svg='',lbl='';
  ins.forEach((s,i)=>{const sy=x.H*(.24+i*(.52/Math.max(1,ins.length-1)));const lq=ph(p,.08+i*.08,.26+i*.08);
   svg+=`<path d="M ${x.W*.24} ${sy} C ${x.W*.4} ${sy}, ${x.W*.42} ${cy}, ${jx} ${cy}" fill="none" stroke="${x.c.hair}" stroke-width="${.32*x.U}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${1-q}"/>`;
   lbl+=`<div style="position:absolute;left:${x.px(x.W*.1)};top:${x.px(sy-1.6*x.U)};width:${x.px(x.W*.13)};text-align:right;opacity:${lq};font:600 ${x.px(2.3*x.U)}/1.2 ${x.F};color:${x.c.body};">${esc(s)}</div>`;});
  const oq=ph(p,.66,.88,eb);
  return wrap(x,`<svg style="position:absolute;inset:0;" width="${x.W}" height="${x.H}">${svg}</svg>${lbl}
   <div style="position:absolute;left:${x.px(jx+2*x.U)};top:${x.px(cy-4*x.U)};padding:${x.px(2.2*x.U)} ${x.px(3.2*x.U)};border:1px solid ${x.c.accent};border-radius:${x.px(1.6*x.U)};background:${x.c.raised};opacity:${oq};transform:scale(${.85+.15*oq});font:600 ${x.px(3*x.U)}/1.15 ${x.F};letter-spacing:-.03em;color:${x.c.text};">${esc(P.out||'')}</div>`);}},
{id:'uncertainty_range',cat:'State & Change',name:'Uncertainty Range',desc:'A bounded possible region, never a false point estimate.',
 demo:{low:'2\u20136\u00d7',label:'reported range of bullying risk',lowPos:.3,highPos:.75},
 render(p,t,x,P){const L=x.W*.16,R=x.W*.84,cy=x.H*.5,q=ph(p,.15,.6,eio);
  const a=L+(R-L)*(P.lowPos??.3),b=L+(R-L)*(P.highPos??.75);
  return wrap(x,`<div style="position:absolute;left:${x.px(L)};right:${x.px(x.W-R)};top:${x.px(cy)};height:1px;background:${x.c.hair};"></div>
   <div style="position:absolute;left:${x.px(a)};top:${x.px(cy-3.2*x.U)};width:${x.px((b-a)*q)};height:${x.px(6.4*x.U)};background:linear-gradient(90deg,transparent,${x.c.accent}44,${x.c.accent}44,transparent);border-radius:${x.px(1*x.U)};"></div>
   <div style="position:absolute;left:${x.px((a+b)/2-12*x.U)};top:${x.px(cy-12*x.U)};width:${x.px(24*x.U)};text-align:center;opacity:${ph(p,.45,.7)};font:600 ${x.px(5.4*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};">${esc(P.low||'')}</div>
   <div style="position:absolute;left:0;right:0;top:${x.px(cy+6*x.U)};text-align:center;opacity:${ph(p,.55,.8)};font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div>`);}},
/* ---------------- METAPHOR & VOICE ---------------- */
{id:'quote_card',cat:'Storytelling',name:'Quote Card',desc:'Quote with attribution \u2014 for actual quotations.',
 demo:{quote:'The bullies found me first.',who:'Every late-diagnosed adult, eventually'},
 render(p,t,x,P){return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.14)};right:${x.px(x.W*.14)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.6*x.U)};">
   <div style="opacity:${ph(p,.02,.2)};font:600 ${x.px(10*x.U)}/0.5 ${x.F};color:${x.c.accent};">\u201c</div>
   <div style="opacity:${ph(p,.12,.4)};transform:translateY(${x.px((1-ph(p,.12,.4))*3*x.U)});font:600 ${x.px(6.8*x.U)}/1.1 ${x.F};letter-spacing:-.05em;color:${x.c.text};">${esc(P.quote||'')}</div>
   <div style="opacity:${ph(p,.5,.72)};font:600 ${x.px(1.9*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">\u2014 ${esc(P.who||'')}</div></div>`);}},
{id:'metaphor_fall',cat:'Metaphor',name:'Controlled Metaphor: Falling Units',desc:'\u201cMake it rain\u201d \u2014 sense-gated: currency, rain, or neutral text.',
 demo:{mode:'currency',label:'revenue, not weather'},
 render(p,t,x,P){const glyph=P.mode==='rain'?'|':'$';const n=26;
  const drops=Array.from({length:n},(_,i)=>{const seed=(i*137)%100/100;
   const fall=((t*.35+seed*2)%1.2)/1.2;const X=x.W*(.1+.8*((i*61)%100)/100);
   const q=ph(p,.1+seed*.3,.3+seed*.3);
   return`<div style="position:absolute;left:${x.px(X)};top:${x.px(fall*x.H*1.1-x.H*.05)};opacity:${(q*(1-fall)*.9).toFixed(2)};font:600 ${x.px((2.2+seed*2)*x.U)}/1 ${x.F};color:${P.mode==='rain'?x.c.accent2:x.c.accent};transform:rotate(${(seed-0.5)*30}deg);">${glyph}</div>`;}).join('');
  return wrap(x,`${drops}<div style="position:absolute;left:0;right:0;top:${x.px(x.H*.8)};text-align:center;opacity:${ph(p,.4,.65)};font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div>`);}},
{id:'caption_only',cat:'Text',name:'Caption Only (D0)',desc:'The minimum sufficient visual \u2014 when no structure would clarify.',
 demo:{text:'Some sentences carry their own weight.'},
 render(p,t,x,P){const q=ph(p,.15,.5);
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.1)};right:${x.px(x.W*.1)};bottom:${x.px(x.H*.1)};text-align:center;opacity:${q};font:400 ${x.px(3.2*x.U)}/1.4 ${x.F};letter-spacing:-.01em;color:${x.c.body};">${esc(P.text||'')}</div>`);}}
);

/* ---------------- SCENE TEMPLATES (the compiler's full grammar, as live tiles) ---------------- */
const TPL_DEMOS={
  title_card:{name:'Title Card',demo:{headline:'Bullies detect autism first.',label:'Ryan Perez \u2014 Keynote'}},
  quote_focus:{name:'Quote Focus',demo:{headline:'The signal was visible the whole time.',label:'From the keynote'}},
  big_number:{name:'Big Number',demo:{number:'63%',label:'bullied at some point in their lives',unit:'Share'}},
  list_stack:{name:'List Stack',demo:{headline:'The reality',label:'Key points',items:['Chronic pain','Autism','ADHD','PTSD','Long COVID','Depression']}},
  steps:{name:'Steps',demo:{headline:'The friction audit',label:'Process',items:['Map the system','Find the friction','Name the cost','Redesign the default']}},
  timeline:{name:'Timeline',demo:{headline:'One life, two discoveries',events:[{time:'1989',event:'The bullying starts'},{time:'2003',event:'Coping systems built'},{time:'2021',event:'Diagnosed at 41'},{time:'2024',event:'The keynote'}]}},
  before_after:{name:'Before / After',demo:{headline:'What changed',left:'Masking through every meeting',right:'Systems that fit the brain'}},
  comparison_split:{name:'Comparison Split',demo:{headline:'Two detection systems',left:'Adults: formal assessment, years',right:'Kids: ten seconds by the lockers'}},
  transformation_arrow:{name:'Transformation Arrow',demo:{headline:'The reframe',left:'Margin',right:'Center'}},
  cause_effect:{name:'Cause \u2192 Effect',demo:{headline:'Why silence wins',left:'Constant disbelief',right:'Nine in ten never tell their employer'}},
  problem_solution:{name:'Problem \u2192 Solution',demo:{headline:'The ask',left:'Auditing every invisible condition',right:'Believe people the first time'}},
  definition_card:{name:'Definition Card',demo:{term:'Invisible disability',definition:'a full disability plus a tax \u2014 paid in energy, pain, and explanations nobody believes',label:'Definition'}},
  hierarchy_tree:{name:'Hierarchy',demo:{headline:'The Second Brain',parent:'240,720 nodes',children:['Projects','People','Patterns','Pain points']}},
  network:{name:'Network',demo:{headline:'Every school\u2019s fastest network',center:'The different kid',nodes:['Hallway','Lockers','Gym class','Lunchroom','Bus stop']}},
  cycle:{name:'Cycle',demo:{headline:'The invalidation loop',items:['Disclose','Disbelief','Withdraw','Struggle','Disclose less']}},
  condition_cards:{name:'Condition Cards',demo:{headline:'The rule',left:'Someone names a condition you cannot see',right:'Skip the audit'}},
  question_card:{name:'Question Card',demo:{headline:'How did kids outperform the adult world?'}},
  cta_card:{name:'CTA Card',demo:{headline:'Not inspiration. Infrastructure.',action:'Book the keynote',destination:'ryanperez.ca'}},
  warning_card:{name:'Warning Card',demo:{headline:'Detection without support is just targeting.',label:'Important'}},
  bar_chart:{name:'Bar Chart (scene)',demo:{headline:'Bullied in one school year',unit:'Share',series:[{label:'Autistic teens',value:46,unit:'%'},{label:'All students',value:11,unit:'%'}]}},
  funnel:{name:'Funnel',demo:{headline:'From signal to support',label:'Stages',series:[{label:'Noticed',value:100,unit:'%'},{label:'Named',value:52,unit:'%'},{label:'Believed',value:24,unit:'%'},{label:'Supported',value:9,unit:'%'}],items:['Noticed','Named','Believed','Supported']}},
  matrix:{name:'Matrix',demo:{headline:'Where conditions land',label:'Matrix',x_axis:['Rare','Common'],y_axis:['Visible','Invisible'],points:[{x:.8,y:.9,label:'1'},{x:.55,y:.75,label:'2'},{x:.3,y:.6,label:'3'},{x:.7,y:.3,label:'4'},{x:.2,y:.2,label:'5'}]}},
};
for(const[tid,cfgT]of Object.entries(TPL_DEMOS)){
  ELEMENTS.push({id:tid,cat:'Scene Templates',name:cfgT.name,desc:'Compiler template \u2014 selectable by the grammar.',demo:cfgT.demo,
    render(p,t,x,P){return window.LAVC?LAVC.renderScene({template:tid,payload:P,primary_relation:'emphasis',id:'lib-'+tid,text:P.headline||''},p,'dark','16:9',t):'';}});
}
/* drop the duplicate hand-made vertical bar tile in favor of the scene one */
const dupIx=ELEMENTS.findIndex(e=>e.id==='bar_chart_v');if(dupIx>=0)ELEMENTS.splice(dupIx,1);

/* ---------------- LAYOUT TOPOLOGY ---------------- */
ELEMENTS.push(
{id:'two_column',cat:'Layout',name:'Two Columns (A | B)',desc:'Split topology for comparison, before/after, problem/solution.',
 demo:{a:{label:'Problem',text:'Proving an invisible condition, daily'},b:{label:'Response',text:'Believe people the first time'}},
 render(p,t,x,P){const pane=(s,d,hot)=>{const q=ph(p,d,d+.24,eio);
   return`<div style="flex:1;height:${x.px(x.H*.56)};padding:${x.px(4*x.U)};border-radius:${x.px(2*x.U)};background:${hot?x.c.raised:x.c.surface};border:1px solid ${hot?x.c.accent:x.c.hairSoft};opacity:${q};transform:translateY(${x.px((1-q)*3*x.U)});display:flex;flex-direction:column;gap:${x.px(2*x.U)};justify-content:center;">
    <div style="font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.13em;text-transform:uppercase;color:${hot?x.c.accent2:x.c.muted};">${esc(s.label)}</div>
    <div style="font:600 ${x.px(4*x.U)}/1.15 ${x.F};letter-spacing:-.04em;color:${x.c.text};">${esc(s.text)}</div></div>`;};
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.09)};right:${x.px(x.W*.09)};top:0;bottom:0;display:flex;align-items:center;gap:${x.px(3*x.U)};">${pane(P.a,.08,false)}${pane(P.b,.3,true)}</div>`);}},
{id:'image_text_column',cat:'Layout',name:'Image + Text Columns',desc:'Media column with dolly, text column with staggered copy.',
 demo:{src:'',label:'The keynote',headline:'Raw. Funny. Devastating.',points:['Lived experience','Systems, not sympathy']},
 render(p,t,x,P){const iq=ph(p,.06,.3),scale=1.08-0.05*ph(p,0,1,eio);
  const media=P.src?`<img src="${esc(P.src)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(.85) contrast(.92);"/>`:`<div style="position:absolute;inset:0;background:linear-gradient(150deg,${x.c.raised},${x.c.surface});display:grid;place-items:center;font:600 ${x.px(2*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:${x.c.muted};">Image slot</div>`;
  const pts=(P.points||[]).map((pt2,i)=>`<div style="opacity:${ph(p,.4+i*.14,.56+i*.14)};display:flex;gap:${x.px(1.6*x.U)};font:600 ${x.px(2.6*x.U)}/1.3 ${x.F};color:${x.c.body};"><span style="color:${x.c.accent};">\u2192</span>${esc(pt2)}</div>`).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.08)};top:${x.px(x.H*.14)};bottom:${x.px(x.H*.14)};width:${x.px(x.W*.4)};border-radius:${x.px(2*x.U)};overflow:hidden;opacity:${iq};"><div style="position:absolute;inset:0;transform:scale(${scale});">${media}</div>
   <div style="position:absolute;right:${x.px(-2*x.U)};bottom:${x.px(-2*x.U)};width:${x.px(9*x.U)};height:${x.px(9*x.U)};border-radius:${x.px(2*x.U)} 0 0 0;background:${x.c.canvas};"></div>
   <div style="position:absolute;right:${x.px(1*x.U)};bottom:${x.px(1*x.U)};width:${x.px(5.6*x.U)};height:${x.px(5.6*x.U)};border-radius:50%;background:${x.c.accent};display:grid;place-items:center;font:600 ${x.px(2.8*x.U)}/1 ${x.F};color:#fff;opacity:${ph(p,.5,.75,eb)};">\u2192</div></div>
   <div style="position:absolute;left:${x.px(x.W*.54)};right:${x.px(x.W*.08)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.4*x.U)};">
    <div style="opacity:${ph(p,.16,.36)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">${esc(P.label||'')}</div>
    <div style="opacity:${ph(p,.22,.46)};transform:translateY(${x.px((1-ph(p,.22,.46))*3*x.U)});font:600 ${x.px(6*x.U)}/1.06 ${x.F};letter-spacing:-.05em;color:${x.c.text};">${esc(P.headline||'')}</div>${pts}</div>`);}},
{id:'media_text_cards',cat:'Layout',name:'Media + Text Card Row',desc:'Columns that each carry an image slot and copy.',
 demo:{cards:[{title:'Detection',sub:'Who notices first'},{title:'Invalidation',sub:'The proving tax'},{title:'Infrastructure',sub:'What support looks like'}]},
 render(p,t,x,P){const cs=(P.cards||[]).slice(0,3);
  const cols=cs.map((cd,i)=>{const q=ph(p,.1+i*.16,.34+i*.16,eb);
   const media=cd.src?`<img src="${esc(cd.src)}" style="width:100%;height:100%;object-fit:cover;filter:saturate(.85) contrast(.92);"/>`:`<div style="width:100%;height:100%;background:linear-gradient(${140+i*40}deg,${x.c.raised},${x.c.surface});"></div>`;
   return`<div style="flex:1;opacity:${q};transform:translateY(${x.px((1-q)*3*x.U)});border:1px solid ${x.c.hairSoft};border-radius:${x.px(1.8*x.U)};overflow:hidden;background:${x.c.surface};">
    <div style="height:${x.px(x.H*.3)};">${media}</div>
    <div style="padding:${x.px(2.4*x.U)} ${x.px(2.6*x.U)};display:flex;flex-direction:column;gap:${x.px(1*x.U)};">
     <div style="font:600 ${x.px(3*x.U)}/1 ${x.F};letter-spacing:-.03em;color:${x.c.text};">${esc(cd.title)}</div>
     <div style="font:400 ${x.px(2*x.U)}/1.4 ${x.F};color:${x.c.muted};">${esc(cd.sub||'')}</div></div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.09)};right:${x.px(x.W*.09)};top:0;bottom:0;display:flex;align-items:center;gap:${x.px(2.6*x.U)};">${cols}</div>`);}},
{id:'callout',cat:'Layout',name:'Callout',desc:'A drawn leader line from a point of interest to an annotation.',
 demo:{src:'',target:{px:.38,py:.44},title:'The signal',text:'visible years before the paperwork'},
 render(p,t,x,P){const tq=ph(p,.08,.3,eb),lq=ph(p,.3,.55,eio),cq=ph(p,.52,.75,eio);
  const tx2=x.W*(P.target?.px??.4),ty=x.H*(P.target?.py??.45);
  const bx=x.W*.64,by=x.H*.3;
  const media=P.src?`<img src="${esc(P.src)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.5;filter:saturate(.7) contrast(.9);"/>`:`<div style="position:absolute;inset:0;background:radial-gradient(700px 500px at 30% 55%,${x.c.raised},transparent 70%);"></div>`;
  return wrap(x,`${media}
   <div style="position:absolute;left:${x.px(tx2-2.4*x.U)};top:${x.px(ty-2.4*x.U)};width:${x.px(4.8*x.U)};height:${x.px(4.8*x.U)};border-radius:50%;border:${x.px(.35*x.U)} solid ${x.c.accent};opacity:${tq};transform:scale(${(0.7+0.3*tq)*(1+0.08*Math.sin(t*2.4))});"></div>
   <svg style="position:absolute;inset:0;" width="${x.W}" height="${x.H}"><path d="M ${tx2+2.6*x.U} ${ty-1.5*x.U} L ${bx-2*x.U} ${by+6*x.U} L ${bx} ${by+6*x.U}" fill="none" stroke="${x.c.accent}" stroke-width="${.28*x.U}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${1-lq}"/></svg>
   <div style="position:absolute;left:${x.px(bx)};top:${x.px(by)};max-width:${x.px(x.W*.26)};padding:${x.px(2.2*x.U)} ${x.px(2.6*x.U)};border:1px solid ${x.c.hairSoft};border-left:${x.px(.35*x.U)} solid ${x.c.accent};border-radius:0 ${x.px(1.4*x.U)} ${x.px(1.4*x.U)} 0;background:${x.c.surface};opacity:${cq};transform:translateY(${x.px((1-cq)*2*x.U)});">
    <div style="font:600 ${x.px(2.6*x.U)}/1 ${x.F};letter-spacing:-.02em;color:${x.c.text};">${esc(P.title||'')}</div>
    <div style="margin-top:${x.px(1*x.U)};font:400 ${x.px(2*x.U)}/1.4 ${x.F};color:${x.c.body};">${esc(P.text||'')}</div></div>`);}},
{id:'lower_third',cat:'Layout',name:'Lower Third',desc:'Speaker identity strip \u2014 slides in, holds, exits.',
 demo:{name:'Ryan Perez',title:'Cognitive Architect \u00b7 Bow Tie Kreative',tag:'ryanperez.ca'},
 render(p,t,x,P){const q=ph(p,.1,.32,eio),out=ph(p,.85,.98,eio);
  const sq=ph(p,.24,.44,eio);
  return wrap(x,`<div style="position:absolute;inset:0;background:radial-gradient(900px 600px at 70% 30%,${x.c.raised}55,transparent 60%);"></div>
   <div style="position:absolute;left:${x.px(x.W*.07)};bottom:${x.px(x.H*.12)};transform:translateX(${x.px((1-q)*-6*x.U)});opacity:${q*(1-out)};display:flex;align-items:stretch;">
    <div style="width:${x.px(.7*x.U)};background:${x.c.accent};"></div>
    <div style="padding:${x.px(2*x.U)} ${x.px(3.2*x.U)};background:rgba(7,9,13,.82);backdrop-filter:blur(12px);border:1px solid ${x.c.hairSoft};border-left:none;">
     <div style="font:600 ${x.px(3.4*x.U)}/1 ${x.F};letter-spacing:-.03em;color:${x.c.text};">${esc(P.name||'')}</div>
     <div style="margin-top:${x.px(.9*x.U)};opacity:${sq};font:400 ${x.px(1.9*x.U)}/1.2 ${x.F};color:${x.c.body};">${esc(P.title||'')}</div></div>
    <div style="align-self:flex-end;padding:${x.px(1.1*x.U)} ${x.px(2*x.U)};background:${x.c.accent};opacity:${ph(p,.4,.6)};font:600 ${x.px(1.6*x.U)}/1 ${x.F};letter-spacing:.12em;text-transform:uppercase;color:#fff;">${esc(P.tag||'')}</div></div>`);}},
{id:'z_space_person',cat:'Layout',name:'Person in Z-Space',desc:'Speaker silhouette in depth; items float on parallax layers around them.',
 demo:{items:['46%','\u2192','63%','ADHD','Autism'],name:'The keynote'},
 render(p,t,x,P){const its=(P.items||[]).slice(0,6);
  const pq=ph(p,.08,.34,eio);
  const cx=x.W*.5,base=x.H*.92,ph2=x.H*.62;
  const person=`<div style="position:absolute;left:${x.px(cx-11*x.U)};top:${x.px(base-ph2)};width:${x.px(22*x.U)};height:${x.px(ph2)};opacity:${pq};transform:translateY(${x.px((1-pq)*4*x.U)});">
    <div style="position:absolute;left:50%;top:0;transform:translateX(-50%);width:${x.px(9*x.U)};height:${x.px(9*x.U)};border-radius:50%;background:linear-gradient(180deg,${x.c.raised},${x.c.surface});"></div>
    <div style="position:absolute;left:50%;top:${x.px(9.6*x.U)};transform:translateX(-50%);width:${x.px(20*x.U)};height:${x.px(ph2-9*x.U)};border-radius:${x.px(9*x.U)} ${x.px(9*x.U)} 0 0;background:linear-gradient(180deg,${x.c.raised},${x.c.canvas});"></div></div>`;
  const orbit=its.map((it,i)=>{const depth=i%3;const spd=[.3,.5,.8][depth],R=[x.W*.34,x.W*.27,x.W*.2][depth];
   const ang=(i/its.length)*Math.PI*2+t*spd*.3;
   const X=cx+Math.cos(ang)*R,Y=x.H*.42+Math.sin(ang)*x.H*.14*[1.1,.9,.7][depth];
   const behind=Math.sin(ang)<0;const q=ph(p,.2+i*.08,.4+i*.08,eb);
   const s=[1.15,.95,.75][depth]*(behind?.8:1);
   return`<div style="position:absolute;left:${x.px(X)};top:${x.px(Y)};transform:translate(-50%,-50%) scale(${s});z-index:${behind?1:3};opacity:${q*(behind?.4:1)};padding:${x.px(1.4*x.U)} ${x.px(2.4*x.U)};border:1px solid ${behind?x.c.hairSoft:x.c.accent};border-radius:${x.px(1.2*x.U)};background:${behind?x.c.surface:x.c.raised};font:600 ${x.px(3*x.U)}/1 ${x.F};letter-spacing:-.03em;color:${x.c.text};filter:blur(${behind?1.5:0}px);">${esc(it)}</div>`;}).join('');
  return wrap(x,`<div style="position:absolute;inset:0;background:radial-gradient(800px 500px at 50% 30%,${x.c.raised}66,transparent 65%);"></div>
   <div style="position:relative;z-index:2;">${person}</div>${orbit}
   <div style="position:absolute;left:0;right:0;bottom:${x.px(x.H*.05)};text-align:center;z-index:4;opacity:${ph(p,.5,.72)};font:600 ${x.px(1.9*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">${esc(P.name||'')}</div>`);}}
);

/* ---------------- PITCH DECK ---------------- */
ELEMENTS.push(
{id:'pd_section_header',cat:'Pitch Deck',name:'Section Header',desc:'Numbered divider \u2014 signals a major transition.',
 demo:{num:'03',title:'The Solution',sub:'What we built and why it holds'},
 render(p,t,x,P){const nq=ph(p,.05,.3,eio),lq=ph(p,.25,.5,eio);
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.09)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.4*x.U)};">
   <div style="opacity:${nq};font:600 ${x.px(16*x.U)}/0.9 ${x.F};letter-spacing:-.06em;color:${x.c.raised};-webkit-text-stroke:1px ${x.c.hair};">${esc(P.num||'')}</div>
   <div style="height:${x.px(.35*x.U)};width:${x.px(20*x.U*lq)};background:${x.c.accent};"></div>
   <div style="opacity:${ph(p,.32,.55)};transform:translateY(${x.px((1-ph(p,.32,.55))*3*x.U)});font:600 ${x.px(8*x.U)}/1 ${x.F};letter-spacing:-.05em;color:${x.c.text};">${esc(P.title||'')}</div>
   <div style="opacity:${ph(p,.48,.7)};font:400 ${x.px(2.6*x.U)}/1.4 ${x.F};color:${x.c.muted};">${esc(P.sub||'')}</div></div>`);}},
{id:'pd_problem',cat:'Pitch Deck',name:'The Problem',desc:'Problem statement + symptom marks stacking as evidence.',
 demo:{headline:'Detection happens. Support doesn\u2019t.',symptoms:['Diagnosis arrives decades late','Disclosure is punished','Talent exits quietly']},
 render(p,t,x,P){const rows=(P.symptoms||[]).slice(0,4).map((s,i)=>{const q=ph(p,.34+i*.16,.5+i*.16,eb);
   return`<div style="display:flex;align-items:center;gap:${x.px(2*x.U)};opacity:${q};transform:translateX(${x.px((1-q)*3*x.U)});">
    <div style="width:${x.px(3.6*x.U)};height:${x.px(3.6*x.U)};border-radius:50%;border:${x.px(.3*x.U)} solid ${x.c.danger};display:grid;place-items:center;font:600 ${x.px(2*x.U)}/1 ${x.F};color:${x.c.danger};">!</div>
    <div style="font:600 ${x.px(2.8*x.U)}/1.25 ${x.F};letter-spacing:-.02em;color:${x.c.body};">${esc(s)}</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.09)};right:${x.px(x.W*.09)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.4*x.U)};">
   <div style="opacity:${ph(p,.03,.2)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.danger};">The problem</div>
   <div style="opacity:${ph(p,.08,.32)};transform:translateY(${x.px((1-ph(p,.08,.32))*3*x.U)});font:600 ${x.px(6.6*x.U)}/1.05 ${x.F};letter-spacing:-.05em;color:${x.c.text};max-width:${x.px(x.W*.7)};">${esc(P.headline||'')}</div>
   <div style="display:flex;flex-direction:column;gap:${x.px(1.8*x.U)};margin-top:${x.px(1.5*x.U)};">${rows}</div></div>`);}},
{id:'pd_solution',cat:'Pitch Deck',name:'The Solution',desc:'Old way struck out; the solution replaces it.',
 demo:{old:'Awareness campaigns',headline:'Infrastructure, not inspiration',points:['Friction audits','Systems redesign','Support defaults']},
 render(p,t,x,P){const sq=ph(p,.14,.34,eio),hq=ph(p,.36,.6,eb);
  const pts=(P.points||[]).slice(0,4).map((pt2,i)=>`<div style="opacity:${ph(p,.6+i*.1,.74+i*.1)};display:flex;gap:${x.px(1.6*x.U)};font:600 ${x.px(2.7*x.U)}/1.3 ${x.F};color:${x.c.body};"><span style="color:${x.c.accent};">\u2192</span>${esc(pt2)}</div>`).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.09)};right:${x.px(x.W*.09)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2.2*x.U)};">
   <div style="opacity:${ph(p,.03,.2)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.accent2};">The solution</div>
   <div style="position:relative;display:inline-block;align-self:flex-start;opacity:${ph(p,.06,.26)};font:600 ${x.px(4*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.muted};">${esc(P.old||'')}
    <span style="position:absolute;left:-2%;top:52%;width:${(sq*104).toFixed(1)}%;height:${x.px(.5*x.U)};background:${x.c.danger};transform:rotate(-1.5deg);"></span></div>
   <div style="opacity:${hq};transform:translateY(${x.px((1-hq)*3*x.U)});font:600 ${x.px(7.4*x.U)}/1.02 ${x.F};letter-spacing:-.05em;color:${x.c.text};max-width:${x.px(x.W*.74)};">${esc(P.headline||'')}</div>
   <div style="display:flex;gap:${x.px(4*x.U)};flex-wrap:wrap;margin-top:${x.px(1*x.U)};">${pts}</div></div>`);}},
{id:'pd_market_size',cat:'Pitch Deck',name:'Market Size (TAM / SAM / SOM)',desc:'Nested circles grow outward, labels count.',
 demo:{tam:{label:'TAM',value:'$14B'},sam:{label:'SAM',value:'$3.2B'},som:{label:'SOM',value:'$180M'}},
 render(p,t,x,P){const cx=x.W*.36,cy=x.H*.52;
  const rings=[[P.tam,.44,.08,x.c.hairSoft],[P.sam,.3,.28,x.c.hair],[P.som,.16,.48,x.c.accent]];
  let out='';rings.forEach(([d,rf,dl,stroke],i)=>{const q=ph(p,dl,dl+.3,eio);const R=Math.min(x.W,x.H)*rf*q;
   out+=`<div style="position:absolute;left:${x.px(cx-R)};top:${x.px(cy-R)};width:${x.px(R*2)};height:${x.px(R*2)};border-radius:50%;border:${x.px(i===2?.4*x.U:.25*x.U)} solid ${stroke};background:${i===2?x.c.accent+'22':'transparent'};"></div>`;});
  const legend=rings.map(([d],i)=>{const q=ph(p,.5+i*.12,.66+i*.12);
   return`<div style="display:flex;align-items:baseline;gap:${x.px(2*x.U)};opacity:${q};transform:translateX(${x.px((1-q)*2*x.U)});">
    <div style="font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;color:${i===2?x.c.accent2:x.c.muted};min-width:${x.px(7*x.U)};">${esc(d?.label||'')}</div>
    <div style="font:600 ${x.px(i===2?6*x.U:4.2*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${i===2?x.c.text:x.c.body};">${esc(d?.value||'')}</div></div>`;}).join('');
  return wrap(x,`${out}<div style="position:absolute;left:${x.px(x.W*.62)};top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:${x.px(2.6*x.U)};">${legend}</div>
   <div style="position:absolute;left:${x.px(x.W*.09)};top:${x.px(x.H*.1)};opacity:${ph(p,.02,.2)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">Market size</div>`);}},
{id:'pd_business_model',cat:'Pitch Deck',name:'Business Model',desc:'Value \u2192 customer \u2192 revenue as a drawn loop.',
 demo:{nodes:['Keynotes','Friction Audits\u2122','Advisory retainers'],center:'Lived-experience IP'},
 render(p,t,x,P){const its=(P.nodes||[]).slice(0,4),cx=x.W*.5,cy=x.H*.52,R=Math.min(x.W,x.H)*.28;
  const cQ=ph(p,.06,.28,eb);
  let arcs='',cards='';
  its.forEach((nd,i)=>{const a=-Math.PI/2+Math.PI*2*i/its.length;
   const X=cx+Math.cos(a)*R,Y=cy+Math.sin(a)*R*.72;const q=ph(p,.28+i*.14,.46+i*.14,eb);
   const na=-Math.PI/2+Math.PI*2*((i+1)%its.length)/its.length;
   const eQ=ph(p,.4+i*.14,.6+i*.14,eio);
   arcs+=`<path d="M ${X} ${Y} Q ${cx+Math.cos((a+na)/2)*R*1.25} ${cy+Math.sin((a+na)/2)*R*.9} ${cx+Math.cos(na)*R} ${cy+Math.sin(na)*R*.72}" fill="none" stroke="${x.c.hair}" stroke-width="${.26*x.U}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${1-eQ}"/>`;
   cards+=`<div style="position:absolute;left:${x.px(X)};top:${x.px(Y)};transform:translate(-50%,-50%) scale(${.85+.15*q});opacity:${q};padding:${x.px(1.8*x.U)} ${x.px(2.8*x.U)};border:1px solid ${x.c.hairSoft};border-radius:${x.px(1.4*x.U)};background:${x.c.surface};font:600 ${x.px(2.6*x.U)}/1 ${x.F};letter-spacing:-.02em;color:${x.c.text};white-space:nowrap;">${esc(nd)}</div>`;});
  return wrap(x,`<svg style="position:absolute;inset:0;" width="${x.W}" height="${x.H}">${arcs}</svg>
   <div style="position:absolute;left:${x.px(cx)};top:${x.px(cy)};transform:translate(-50%,-50%) scale(${.8+.2*cQ});opacity:${cQ};padding:${x.px(2.2*x.U)} ${x.px(3.4*x.U)};border:${x.px(.3*x.U)} solid ${x.c.accent};border-radius:999px;background:${x.c.raised};font:600 ${x.px(2.6*x.U)}/1 ${x.F};color:${x.c.text};">${esc(P.center||'')}</div>${cards}
   <div style="position:absolute;left:${x.px(x.W*.09)};top:${x.px(x.H*.1)};opacity:${ph(p,.02,.2)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">Business model</div>`);}},
{id:'pd_pricing',cat:'Pitch Deck',name:'Pricing Strategy',desc:'Three tiers; the anchor tier lands last with the accent.',
 demo:{tiers:[{name:'Talk',price:'$15K',note:'60-min keynote'},{name:'Talk + Audit',price:'$28K',note:'Keynote + Friction Audit\u2122',hot:true},{name:'Partner',price:'$90K',note:'Quarterly advisory'}]},
 render(p,t,x,P){const ts=(P.tiers||[]).slice(0,3);
  const cols=ts.map((tr,i)=>{const d=tr.hot?.42:.12+i*.12;const q=ph(p,d,d+.24,eb);
   return`<div style="flex:1;padding:${x.px(3.4*x.U)} ${x.px(3*x.U)};border:${tr.hot?x.px(.3*x.U):'1px'} solid ${tr.hot?x.c.accent:x.c.hairSoft};border-radius:${x.px(2*x.U)};background:${tr.hot?x.c.raised:x.c.surface};opacity:${q};transform:translateY(${x.px((1-q)*4*x.U)}) scale(${tr.hot?1.04:1});display:flex;flex-direction:column;gap:${x.px(1.6*x.U)};align-items:center;text-align:center;">
    <div style="font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.13em;text-transform:uppercase;color:${tr.hot?x.c.accent2:x.c.muted};">${esc(tr.name)}</div>
    <div style="font:600 ${x.px(6.2*x.U)}/1 ${x.F};letter-spacing:-.05em;color:${x.c.text};">${esc(tr.price)}</div>
    <div style="font:400 ${x.px(2*x.U)}/1.4 ${x.F};color:${x.c.muted};">${esc(tr.note||'')}</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.09)};top:${x.px(x.H*.1)};opacity:${ph(p,.02,.2)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">Pricing strategy</div>
   <div style="position:absolute;left:${x.px(x.W*.09)};right:${x.px(x.W*.09)};top:${x.px(x.H*.24)};bottom:${x.px(x.H*.14)};display:flex;align-items:stretch;gap:${x.px(2.6*x.U)};">${cols}</div>`);}},
{id:'pd_use_of_funds',cat:'Pitch Deck',name:'Use of Funds',desc:'Allocation as a segmented bar that fills in order.',
 demo:{segments:[{label:'Product',value:45},{label:'Go-to-market',value:30},{label:'Team',value:18},{label:'Ops',value:7}],headline:'How the funds will be used'},
 render(p,t,x,P){const segs=(P.segments||[]).slice(0,5),tot=segs.reduce((a,s)=>a+s.value,0);
  const L=x.W*.09,Wd=x.W*.82,shades=[x.c.accent,'#5B82ED',x.c.muted,x.c.raised,'#3A3F4C'];
  let acc=0;const parts=segs.map((s,i)=>{const q=ph(p,.2+i*.16,.42+i*.16,eio);const w=Wd*(s.value/tot);
   const el=`<div style="position:absolute;left:${x.px(L+acc)};top:${x.px(x.H*.44)};width:${x.px(w*q)};height:${x.px(7*x.U)};background:${shades[i]};border-right:2px solid ${x.c.canvas};"></div>
    <div style="position:absolute;left:${x.px(L+acc)};top:${x.px(x.H*.44+8.6*x.U)};opacity:${ph(p,.32+i*.16,.5+i*.16)};display:flex;flex-direction:column;gap:${x.px(.6*x.U)};">
     <div style="font:600 ${x.px(3.2*x.U)}/1 ${x.F};letter-spacing:-.03em;color:${x.c.text};">${Math.round(s.value*ph(p,.2+i*.16,.42+i*.16,eio))}%</div>
     <div style="font:600 ${x.px(1.7*x.U)}/1 ${x.F};letter-spacing:.1em;text-transform:uppercase;color:${x.c.muted};">${esc(s.label)}</div></div>`;
   acc+=w;return el;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(L)};top:${x.px(x.H*.16)};opacity:${ph(p,.02,.22)};font:600 ${x.px(5*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};">${esc(P.headline||'')}</div>${parts}`);}},
{id:'pd_growth',cat:'Pitch Deck',name:'Growth Projection',desc:'Actuals draw solid; projection continues dashed inside an uncertainty fan.',
 demo:{actual:[{label:'\u201924',value:12},{label:'\u201925',value:21},{label:'\u201926',value:38}],projected:[{label:'\u201927',value:64},{label:'\u201928',value:105}],unit:'K',headline:'Growth projection'},
 render(p,t,x,P){const all=[...(P.actual||[]),...(P.projected||[])],na=(P.actual||[]).length;
  const max=Math.max(...all.map(d=>d.value))*1.15,L=x.W*.12,R=x.W*.88,T=x.H*.28,B=x.H*.76;
  const pts=all.map((d,i)=>[L+(R-L)*i/(all.length-1),B-(B-T)*(d.value/max)]);
  const q1=ph(p,.12,.5,eio),q2=ph(p,.5,.85,eio);
  const solid=pts.slice(0,na).map((pt,i)=>(i?'L':'M')+pt[0]+' '+pt[1]).join(' ');
  const dash=pts.slice(na-1).map((pt,i)=>(i?'L':'M')+pt[0]+' '+pt[1]).join(' ');
  const lastA=pts[na-1],lastP=pts[pts.length-1];
  const fan=`M ${lastA[0]} ${lastA[1]} L ${lastP[0]} ${lastP[1]-18*x.U*q2} L ${lastP[0]} ${Math.min(B,lastP[1]+14*x.U*q2)} Z`;
  const labels=all.map((d,i)=>`<div style="position:absolute;left:${x.px(pts[i][0]-5*x.U)};top:${x.px(B+2*x.U)};width:${x.px(10*x.U)};text-align:center;font:600 ${x.px(1.7*x.U)}/1 ${x.F};letter-spacing:.1em;color:${i>=na?x.c.accent2:x.c.muted};opacity:${ph(p,.15+i*.09,.3+i*.09)};">${esc(d.label)}</div>`).join('');
  const bq=ph(p,.82,.96,eb);
  return wrap(x,`<div style="position:absolute;left:${x.px(L)};top:${x.px(x.H*.13)};opacity:${ph(p,.02,.22)};font:600 ${x.px(4.6*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};">${esc(P.headline||'')}</div>
   <svg style="position:absolute;inset:0;" width="${x.W}" height="${x.H}">
    <line x1="${L}" y1="${B}" x2="${L+(R-L)*ph(p,.06,.26,eio)}" y2="${B}" stroke="${x.c.hair}" stroke-width="1"/>
    <path d="${fan}" fill="${x.c.accent}18"/>
    <path d="${solid}" fill="none" stroke="${x.c.accent}" stroke-width="${.5*x.U}" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${1-q1}"/>
    <path d="${dash}" fill="none" stroke="${x.c.accent2}" stroke-width="${.4*x.U}" stroke-dasharray="${1.6*x.U} ${1.2*x.U}" opacity="${q2}"/></svg>${labels}
   <div style="position:absolute;left:${x.px(lastP[0]-6*x.U)};top:${x.px(lastP[1]-7*x.U)};padding:${x.px(.9*x.U)} ${x.px(1.6*x.U)};border-radius:${x.px(.8*x.U)};background:${x.c.accent};font:600 ${x.px(2.2*x.U)}/1 ${x.F};color:#fff;opacity:${bq};transform:scale(${.8+.2*bq});">${esc(all[all.length-1].value)}${esc(P.unit||'')} \u00b7 proj.</div>`);}},
{id:'pd_sales_strategy',cat:'Pitch Deck',name:'Sales Strategy',desc:'Channel funnel: reach narrows to revenue, stage by stage.',
 demo:{stages:[{label:'Content & socials',value:'96M reach'},{label:'Event bookers',value:'1,400 leads'},{label:'Discovery calls',value:'220'},{label:'Signed keynotes',value:'48'}]},
 render(p,t,x,P){const ss=(P.stages||[]).slice(0,5);
  const rows=ss.map((s,i,arr)=>{const q=ph(p,.14+i*.15,.34+i*.15,eio);const wd=100-i*16;
   return`<div style="width:${wd}%;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:${x.px(1.9*x.U)} ${x.px(3*x.U)};clip-path:polygon(2.5% 0,97.5% 0,94% 100%,6% 100%);background:${i===arr.length-1?x.c.accent:x.c.surface};border:1px solid ${x.c.hairSoft};opacity:${q};transform:scaleX(${.8+.2*q});">
    <span style="font:600 ${x.px(2.4*x.U)}/1 ${x.F};letter-spacing:-.02em;color:${i===arr.length-1?'#fff':x.c.body};">${esc(s.label)}</span>
    <span style="font:600 ${x.px(2.6*x.U)}/1 ${x.F};letter-spacing:-.02em;color:${i===arr.length-1?'#fff':x.c.text};">${esc(s.value)}</span></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.09)};top:${x.px(x.H*.1)};opacity:${ph(p,.02,.2)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">Sales strategy</div>
   <div style="position:absolute;left:${x.px(x.W*.14)};right:${x.px(x.W*.14)};top:${x.px(x.H*.24)};display:flex;flex-direction:column;gap:${x.px(1.4*x.U)};">${rows}</div>`);}},
{id:'pd_swot',cat:'Pitch Deck',name:'SWOT Analysis',desc:'Two-axis quadrant; cells land in reading order.',
 demo:{s:'Lived-experience credibility',w:'Single-speaker capacity',o:'Corporate ND programs booming',th:'Awareness-washing competitors'},
 render(p,t,x,P){const cells=[['Strengths',P.s,x.c.accent,0],['Weaknesses',P.w,x.c.danger,1],['Opportunities',P.o,'#3FA46A',2],['Threats',P.th,x.c.muted,3]];
  const L=x.W*.14,T=x.H*.2,cw=(x.W*.72-2*x.U)/2,chh=(x.H*.62-2*x.U)/2;
  const grid=cells.map(([lab,txt,col,i])=>{const q=ph(p,.12+i*.14,.32+i*.14,eio);
   return`<div style="position:absolute;left:${x.px(L+(i%2)*(cw+2*x.U))};top:${x.px(T+Math.floor(i/2)*(chh+2*x.U))};width:${x.px(cw)};height:${x.px(chh)};padding:${x.px(2.6*x.U)};border:1px solid ${x.c.hairSoft};border-top:${x.px(.35*x.U)} solid ${col};border-radius:${x.px(1.4*x.U)};background:${x.c.surface};opacity:${q};transform:translateY(${x.px((1-q)*2.4*x.U)});display:flex;flex-direction:column;gap:${x.px(1.4*x.U)};">
    <div style="font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.13em;text-transform:uppercase;color:${col};">${esc(lab)}</div>
    <div style="font:600 ${x.px(2.7*x.U)}/1.25 ${x.F};letter-spacing:-.02em;color:${x.c.text};">${esc(txt||'')}</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.14)};top:${x.px(x.H*.1)};opacity:${ph(p,.02,.2)};font:600 ${x.px(1.8*x.U)}/1 ${x.F};letter-spacing:.14em;text-transform:uppercase;color:${x.c.muted};">SWOT analysis</div>${grid}`);}},
{id:'pd_market_share',cat:'Pitch Deck',name:'Market Share Comparison',desc:'Share bars with the company segment pulling ahead.',
 demo:{series:[{label:'Incumbent A',value:34},{label:'Incumbent B',value:27},{label:'Others',value:31},{label:'Us',value:8,hot:true}],headline:'Market share today'},
 render(p,t,x,P){const s=(P.series||[]).slice(0,6),max=Math.max(...s.map(d=>d.value));
  const rows=s.map((d,i)=>{const q=ph(p,.15+i*.13,.45+i*.13,eio);
   return`<div style="display:flex;align-items:center;gap:${x.px(2.4*x.U)};">
    <div style="width:${x.px(20*x.U)};font:600 ${x.px(2.3*x.U)}/1 ${x.F};color:${d.hot?x.c.accent2:x.c.body};text-align:right;">${esc(d.label)}</div>
    <div style="flex:1;height:${x.px(3.4*x.U)};background:${x.c.hairSoft};border-radius:${x.px(.7*x.U)};overflow:hidden;"><div style="width:${(d.value/max*100*q).toFixed(1)}%;height:100%;background:${d.hot?x.c.accent:x.c.raised};border:1px solid ${d.hot?x.c.accent:x.c.hair};"></div></div>
    <div style="min-width:${x.px(8*x.U)};font:600 ${x.px(2.6*x.U)}/1 ${x.F};color:${d.hot?x.c.accent2:x.c.text};opacity:${q};">${Math.round(d.value*q)}%</div></div>`;}).join('');
  return wrap(x,`<div style="position:absolute;left:${x.px(x.W*.1)};right:${x.px(x.W*.1)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${x.px(2*x.U)};">
   <div style="font:600 ${x.px(4.6*x.U)}/1 ${x.F};letter-spacing:-.04em;color:${x.c.text};opacity:${ph(p,.03,.24)};margin-bottom:${x.px(1.4*x.U)};">${esc(P.headline||'')}</div>${rows}</div>`);}}
);

/* quantifier scopes: one | partial | many | any | all — deterministic payload transforms */
function scopeAdapt(P0,scope){
  if(!scope||scope==='default')return P0;
  const P=JSON.parse(JSON.stringify(P0));
  const frac={one:0,partial:.4,many:.75,any:.5,all:1}[scope];
  if(P.total!=null){P.count=scope==='one'?1:scope==='any'?1:Math.max(1,Math.round(P.total*frac));if(scope==='all')P.count=P.total;if(scope==='any')P.label='at least one \u2014 '+(P.label||'');}
  if(typeof P.value==='number'){P.value=scope==='one'?Math.max(4,Math.round(P.value*.1)):scope==='all'?100:Math.round(100*frac);if(scope==='any')P.label='some \u2014 '+(P.label||'');}
  if(Array.isArray(P.items)&&typeof P.items[0]!=='object'){const n=P.items.length;
    P.items=scope==='one'?P.items.slice(0,1):scope==='partial'?P.items.slice(0,Math.max(2,Math.ceil(n*.5))):P.items;}
  if(Array.isArray(P.series)){P.series=P.series.map((s,i)=>({...s,value:scope==='one'?(i===0?s.value:Math.round(s.value*.12)):scope==='all'?Math.max(s.value,90):scope==='any'?s.value:Math.round(s.value*(scope==='partial'?.5:1))}));
    if(scope==='one')P.series=P.series.slice(0,1);}
  if(P.active!=null)P.active=scope==='one'?1:scope==='all'?99:scope==='partial'?2:3;
  if(P.count!=null&&P.total==null)P.count=scope==='one'?1:scope==='all'?24:Math.max(2,Math.round((P.count||10)*(frac||.5)));
  return P;
}
window.LAVC_SCOPE_ADAPT=scopeAdapt;
window.LAVC_ELEMENTS=ELEMENTS;
window.LAVC_ELEMENT_CTX=ctx;
})();
