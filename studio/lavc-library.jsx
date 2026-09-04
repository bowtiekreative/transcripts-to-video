/* LAVC Element Library — browsable animated gallery */
const { useState, useEffect, useRef } = React;
const RPL = { canvas:'#07090D', surface:'#1A1D24', head:'#F5F7FA', body:'#C5C7CE', muted:'#8A8D96', accent:'#3F6EE9', hair:'rgba(255,255,255,0.15)', hairSoft:'rgba(255,255,255,0.08)' };
const FL = "'Inter', sans-serif";
const microL = { fontFamily:FL, fontWeight:600, fontSize:11, letterSpacing:'0.12em', textTransform:'uppercase', color:RPL.muted };

function ElementTile({ el, clock, scope }) {
  const W = 1920, H = 1080, tileW = 356, scale = tileW / W;
  const loop = 5.5;
  const p = ((clock % loop) / loop);
  const x = window.LAVC_ELEMENT_CTX('dark', '16:9');
  const payload = window.LAVC_SCOPE_ADAPT ? window.LAVC_SCOPE_ADAPT(el.demo, scope) : el.demo;
  let html = '';
  try { html = el.render(Math.min(1, p * 1.15), clock, x, payload); } catch (e) { html = `<div style="color:#D8574F;font:12px monospace;padding:20px;">${String(e)}</div>`; }
  return <div style={{ width:tileW, background:RPL.surface, border:`1px solid ${RPL.hairSoft}`, borderRadius:14, overflow:'hidden' }}>
    <div style={{ position:'relative', width:tileW, height:tileW*H/W, overflow:'hidden' }}>
      <div style={{ width:W, height:H, transform:`scale(${scale})`, transformOrigin:'0 0', position:'absolute' }} dangerouslySetInnerHTML={{ __html:html }} />
    </div>
    <div style={{ padding:'14px 18px 18px' }}>
      <div style={{ fontFamily:FL, fontWeight:600, fontSize:15, letterSpacing:'-0.01em', color:RPL.head }}>{el.name}</div>
      <div style={{ fontFamily:FL, fontWeight:400, fontSize:12.5, lineHeight:1.5, color:RPL.muted, marginTop:5 }}>{el.desc}</div>
      <div style={{ ...microL, fontSize:10, marginTop:10, color:RPL.accent }}>{el.id}</div>
    </div>
  </div>;
}

function ElementLibrary() {
  const [clock, setClock] = useState(0);
  const [cat, setCat] = useState('All');
  const [scope, setScope] = useState('default');
  useEffect(() => {
    let raf, start = performance.now();
    const tick = (now) => { setClock((now - start) / 1000); raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);
  const els = window.LAVC_ELEMENTS || [];
  const cats = ['All', ...new Set(els.map(e => e.cat))];
  const shown = cat === 'All' ? els : els.filter(e => e.cat === cat);
  const groups = [...new Set(shown.map(e => e.cat))];
  return <div style={{ minHeight:'100vh', background:RPL.canvas, fontFamily:FL, padding:'0 0 80px' }}>
    <div style={{ position:'sticky', top:0, zIndex:50, background:'rgba(7,9,13,0.8)', backdropFilter:'blur(16px)', borderBottom:`1px solid ${RPL.hairSoft}`, padding:'18px 40px', display:'flex', alignItems:'center', gap:24, flexWrap:'wrap' }}>
      <div style={{ fontFamily:FL, fontWeight:600, fontSize:19, letterSpacing:'-0.03em', color:RPL.head }}>LAVC Element Library</div>
      <div style={{ ...microL }}>{els.length + ' animated elements \u00b7 all live'}</div>
      <div style={{ flex:1 }} />
      <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
        {cats.map(c2 => <div key={c2} onClick={() => setCat(c2)}
          style={{ cursor:'pointer', fontFamily:FL, fontWeight:600, fontSize:12.5, padding:'7px 16px', borderRadius:999,
            color: cat===c2?RPL.canvas:RPL.body, background: cat===c2?RPL.head:'transparent', border:`1px solid ${cat===c2?RPL.head:RPL.hair}` }}>{c2}</div>)}
      </div>
      <a href="LAVC Variant Studio.dc.html" style={{ fontFamily:FL, fontWeight:600, fontSize:12.5, padding:'7px 16px', borderRadius:999, border:`1px solid ${RPL.hair}` }}>{'Variant Studio \u2192'}</a>
    </div>
    <div style={{ maxWidth:1220, margin:'0 auto', padding:'24px 40px 0', display:'flex', alignItems:'center', gap:12, flexWrap:'wrap' }}>
      <div style={{ ...microL }}>Quantifier scope</div>
      {['default','one','partial','many','any','all'].map(s => <div key={s} onClick={() => setScope(s)}
        style={{ cursor:'pointer', fontFamily:FL, fontWeight:600, fontSize:12, padding:'6px 15px', borderRadius:999,
          color: scope===s?'#fff':RPL.body, background: scope===s?RPL.accent:'transparent', border:`1px solid ${scope===s?RPL.accent:RPL.hair}` }}>{s}</div>)}
      <div style={{ ...microL, fontSize:10, textTransform:'none', letterSpacing:'0.02em' }}>every element re-parameterized deterministically: 1 / partial / many / any / all</div>
    </div>
    <div style={{ maxWidth:1220, margin:'0 auto', padding:'36px 40px 0' }}>
      {groups.map(g => <div key={g} style={{ marginBottom:44 }}>
        <div style={{ fontFamily:FL, fontWeight:600, fontSize:24, letterSpacing:'-0.04em', color:RPL.head, marginBottom:18 }}>{g}</div>
        <div style={{ display:'flex', flexWrap:'wrap', gap:20 }}>
          {shown.filter(e => e.cat === g).map(el => <ElementTile key={el.id + scope} el={el} clock={clock} scope={scope} />)}
        </div>
      </div>)}
    </div>
  </div>;
}
window.ElementLibrary = ElementLibrary;
