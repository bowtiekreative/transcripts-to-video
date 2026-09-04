/* LAVC Variant Studio — UI over window.LAVC */
const { useState, useEffect, useRef, useCallback } = React;
const RP = { canvas:'#07090D', surface:'#1A1D24', raised:'#23262F', head:'#F5F7FA', body:'#C5C7CE', muted:'#8A8D96',
  accent:'#3F6EE9', good:'#3FA46A', bad:'#D8574F', hair:'rgba(255,255,255,0.15)', hairSoft:'rgba(255,255,255,0.08)' };
const F = "'Inter', sans-serif";
const mono = "ui-monospace, SFMono-Regular, Menlo, monospace";
const micro = { fontFamily:F, fontWeight:600, fontSize:11, letterSpacing:'0.12em', textTransform:'uppercase', color:RP.muted };

const DEMO_SRT = `1
00:00:00,000 --> 00:01:03,680
Invisible disability is internalized pain that nobody can see. It lives in your body and your brain, it slows you down, and some days it stops you completely — but there is no cast, no cane, no wheelchair to announce it. Here is the number that changes how you see this. One in four adults in the United States lives with a disability. And in one survey, 74 percent of disabled people used no wheelchair, no aid, nothing visible at all. Among people with chronic illness, an estimated 96 percent carry a condition you cannot see. Read those numbers again. The wheelchair is the logo of disability. It is not the reality of disability. The reality is chronic pain, autism, ADHD, PTSD, lupus, long COVID, depression, brain injuries — conditions that drain the battery before the day even starts.

2
00:01:04,180 --> 00:01:55,540
Now here is the part nobody warns you about. When your disability is invisible, you get handed a second job, and it pays nothing: proving it. Researchers actually have a name for what happens when people fail that job — disability invalidation. It is the coworker who says you look fine to me. It is the stranger at the parking spot. It is family members who think you are lazy or dramatic. Studies link this constant disbelief to higher rates of anxiety, depression, and social withdrawal. And it changes behavior. In one survey, 88 percent of people with invisible disabilities felt negative about even telling their employer. Think about that. Nine out of ten of us would rather struggle in silence than risk the sentence you don't look disabled.

3
00:01:56,040 --> 00:02:44,040
So let me redefine it, because the textbook version misses the point. An invisible disability is not a milder disability. It is a full disability plus a tax. You pay in energy before work starts. You pay in pain nobody counts. You pay in explanations nobody believes. When I seem slow, or blunt, or exhausted, that is not a character flaw — that is the tax being collected in public. So here is my ask, and it costs you nothing. When someone tells you about a condition you cannot see, skip the audit. You were never owed proof. Believe people the first time — because 96 percent of this fight was designed to be invisible, and disbelief is the only part of it we can actually remove.

4
00:02:44,540 --> 00:02:54,000
Believe people the first time. Book the keynote at ryanperez.ca and bring this conversation to your team.`;

function SceneTile({ scene, version, tileW, locked, onLock, onReport, reportOpen }) {
  const asp = LAVC.ASPECTS[version.config.aspect];
  const tileH = tileW * asp.h / asp.w;
  const scale = tileW / asp.w;
  const html = LAVC.renderScene(scene, 0.85, version.config.brand, version.config.aspect, 0);
  return <div style={{ width:tileW, flex:'0 0 auto' }}>
    <div style={{ position:'relative', width:tileW, height:tileH, borderRadius:8, overflow:'hidden', border:`1px solid ${reportOpen?RP.accent:RP.hairSoft}`, cursor:'pointer' }} onClick={onReport} title="Toggle decision report">
      <div style={{ width:asp.w, height:asp.h, transform:`scale(${scale})`, transformOrigin:'0 0', position:'absolute' }} dangerouslySetInnerHTML={{ __html:html }} />
      <div onClick={(e)=>{e.stopPropagation();onLock();}} title={locked?'Unlock scene':'Lock scene'}
        style={{ position:'absolute', top:6, right:6, width:22, height:22, borderRadius:6, display:'grid', placeItems:'center',
          background: locked?RP.accent:'rgba(7,9,13,0.65)', border:`1px solid ${locked?RP.accent:RP.hair}`, color:'#fff', fontSize:11, fontFamily:F, fontWeight:600 }}>
        {locked?'\u25CF':'\u25CB'}</div>
    </div>
    <div style={{ ...micro, fontSize:10, marginTop:6, display:'flex', justifyContent:'space-between', gap:6 }}>
      <span style={{ color:RP.body, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{scene.template}</span>
      <span>{scene.score}</span>
    </div>
  </div>;
}

function Report({ scene }) {
  const t = scene.trace || {};
  return <div style={{ marginTop:10, padding:'14px 16px', background:RP.canvas, border:`1px solid ${RP.hairSoft}`, borderRadius:10, fontFamily:mono, fontSize:11, lineHeight:1.6, color:RP.body }}>
    <div style={{ color:RP.head, fontWeight:600 }}>{scene.id} · {scene.start.toFixed(1)}–{scene.end.toFixed(1)}s · relation: {scene.primary_relation}{scene.sensitive?' · sensitive':''}</div>
    <div style={{ color:RP.muted, margin:'4px 0 8px' }}>&ldquo;{scene.text.length>110?scene.text.slice(0,110)+'\u2026':scene.text}&rdquo;</div>
    {(t.candidates||[]).map((cd,i)=>{
      const sel = cd.template===t.selected && i===0;
      return <div key={i} style={{ display:'flex', gap:10, color: sel?RP.head:RP.muted, flexWrap:'wrap' }}>
        <span style={{ color: sel?RP.accent:RP.muted, minWidth:150 }}>{sel?'\u2192 ':'  '}{cd.template}/{cd.layout}</span>
        <span>{cd.score}</span>
        <span style={{ opacity:.8 }}>{Object.entries(cd.positive).map(([k,v])=>`${k}:${v}`).join(' ')}</span>
        {Object.keys(cd.penalties).length>0 && <span style={{ color:RP.bad }}>{Object.entries(cd.penalties).map(([k,v])=>`-${v} ${k}`).join(' ')}</span>}
      </div>;})}
    <div style={{ color:RP.muted, marginTop:4 }}>{t.rejected_count} templates rejected by hard constraints</div>
  </div>;
}

function Player({ version, onClose }) {
  const [t, setT] = useState(0);
  const [playing, setPlaying] = useState(true);
  const raf = useRef(null), last = useRef(null), tRef = useRef(0);
  const D = version.duration;
  useEffect(()=>{
    if(!playing){ cancelAnimationFrame(raf.current); last.current=null; return; }
    const tick=(now)=>{
      if(last.current!=null){ tRef.current=Math.min(D, tRef.current+(now-last.current)/1000); setT(tRef.current); if(tRef.current>=D) setPlaying(false); }
      last.current=now; raf.current=requestAnimationFrame(tick);
    };
    raf.current=requestAnimationFrame(tick);
    return ()=>cancelAnimationFrame(raf.current);
  },[playing,D]);
  const scene = version.scenes.find(s=>t>=s.start&&t<s.end) || version.scenes[version.scenes.length-1];
  const p = scene ? LAVC.clamp((t-scene.start)/Math.max(.001,scene.end-scene.start)) : 0;
  const asp = LAVC.ASPECTS[version.config.aspect];
  const html = scene ? LAVC.renderScene(scene, p, version.config.brand, version.config.aspect, t) : '';
  const boxRef = useRef(null);
  const [scale, setScale] = useState(0.3);
  useEffect(()=>{
    const fit=()=>{ const el=boxRef.current; if(!el)return; setScale(Math.min(el.clientWidth/asp.w,(el.clientHeight-90)/asp.h)); };
    fit(); window.addEventListener('resize',fit); return ()=>window.removeEventListener('resize',fit);
  },[asp.w,asp.h]);
  const cap = scene ? (scene.text.length>90?scene.text.slice(0,90)+'\u2026':scene.text) : '';
  const seek=(e)=>{ const r=e.currentTarget.getBoundingClientRect(); tRef.current=D*LAVC.clamp((e.clientX-r.left)/r.width); setT(tRef.current); };
  return <div style={{ position:'fixed', inset:0, zIndex:100, background:'rgba(3,4,7,0.92)', backdropFilter:'blur(16px)', display:'flex', flexDirection:'column' }}>
    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 24px' }}>
      <div style={{ ...micro, color:RP.body }}>{version.id} · {version.config.brand} · {version.config.aspect} · seed {version.config.seed} · {scene?scene.template:''}</div>
      <div onClick={onClose} style={{ cursor:'pointer', fontFamily:F, fontWeight:600, fontSize:13, color:RP.muted, padding:'8px 18px', border:`1px solid ${RP.hair}`, borderRadius:999 }} style-hover={{ color:RP.head }}>{'Close \u2715'}</div>
    </div>
    <div ref={boxRef} style={{ flex:1, display:'grid', placeItems:'center', overflow:'hidden', padding:'0 24px' }}>
      <div style={{ width:asp.w*scale, height:asp.h*scale, position:'relative', borderRadius:10, overflow:'hidden', border:`1px solid ${RP.hairSoft}` }}>
        <div style={{ width:asp.w, height:asp.h, transform:`scale(${scale})`, transformOrigin:'0 0', position:'absolute' }} dangerouslySetInnerHTML={{ __html:html }} />
        <div style={{ position:'absolute', left:'6%', right:'6%', bottom:'4%', textAlign:'center', fontFamily:F, fontWeight:400, fontSize:Math.max(11,16*scale*2.4), lineHeight:1.35, color:'#C5C7CE', textShadow:'0 1px 8px rgba(0,0,0,0.6)' }}>{cap}</div>
      </div>
    </div>
    <div style={{ display:'flex', alignItems:'center', gap:16, padding:'16px 24px 22px' }}>
      <div onClick={()=>{ if(t>=D){tRef.current=0;setT(0);} setPlaying(v=>!v); }} style={{ cursor:'pointer', width:40, height:40, borderRadius:'50%', background:RP.head, color:RP.canvas, display:'grid', placeItems:'center', fontSize:14 }}>{playing?'\u275A\u275A':'\u25B6'}</div>
      <div onClick={seek} style={{ flex:1, height:22, display:'flex', alignItems:'center', cursor:'pointer' }}>
        <div style={{ position:'relative', width:'100%', height:4, background:RP.hairSoft, borderRadius:999 }}>
          <div style={{ position:'absolute', left:0, top:0, bottom:0, width:`${t/D*100}%`, background:RP.accent, borderRadius:999 }} />
          {version.scenes.map((s,i)=><div key={i} style={{ position:'absolute', left:`${s.start/D*100}%`, top:-2, width:1, height:8, background:RP.hair }} />)}
        </div>
      </div>
      <div style={{ fontFamily:mono, fontSize:12, color:RP.muted, minWidth:86, textAlign:'right' }}>{fmt(t)} / {fmt(D)}</div>
    </div>
  </div>;
}
function fmt(s){ s=Math.max(0,Math.floor(s)); return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`; }

function VersionCard({ version, rank, srt, onUpdate, onPlay }) {
  const [locks, setLocks] = useState(new Set());
  const [openReport, setOpenReport] = useState(null);
  const cfg = version.config;
  const chip = (txt, hot) => <span style={{ ...micro, fontSize:10, padding:'5px 12px', border:`1px solid ${hot?RP.accent:RP.hairSoft}`, borderRadius:8, color:hot?'#8AA4FF':RP.muted, background:RP.canvas }}>{txt}</span>;
  const toggleLock=(i)=>setLocks(prev=>{ const n=new Set(prev); n.has(i)?n.delete(i):n.add(i); return n; });
  const regen=()=>onUpdate(LAVC.recompile(srt, version, locks));
  const tileW = cfg.aspect==='9:16'?110:(cfg.aspect==='1:1'?150:200);
  return <div style={{ background:RP.surface, border:`1px solid ${RP.hairSoft}`, borderRadius:16, padding:'24px 28px' }}>
    <div style={{ display:'flex', alignItems:'center', gap:16, flexWrap:'wrap' }}>
      <div style={{ fontFamily:F, fontWeight:600, fontSize:24, letterSpacing:'-0.03em', color:RP.head }}>#{rank}</div>
      <div style={{ fontFamily:F, fontWeight:600, fontSize:15, letterSpacing:'-0.01em', color:RP.body }}>{cfg.note}</div>
      <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
        {chip(cfg.aspect, false)}{chip(cfg.brand, cfg.brand!=='dark')}{chip('seed '+cfg.seed, false)}
        {chip('score '+version.meanScore, true)}{locks.size>0&&chip(locks.size+' locked', true)}
      </div>
      <div style={{ flex:1 }} />
      <div onClick={regen} style={{ cursor:'pointer', fontFamily:F, fontWeight:600, fontSize:13, color:RP.body, padding:'9px 20px', border:`1px solid ${RP.hair}`, borderRadius:999 }} style-hover={{ color:RP.head, borderColor:RP.accent }}>Regenerate unlocked</div>
      <div onClick={()=>onPlay(version)} style={{ cursor:'pointer', fontFamily:F, fontWeight:600, fontSize:13, color:RP.canvas, background:RP.head, padding:'9px 22px', borderRadius:999 }} style-hover={{ background:'#fff' }}>{'\u25B6 Play'}</div>
    </div>
    <div style={{ display:'flex', gap:12, marginTop:18, overflowX:'auto', paddingBottom:6 }}>
      {version.scenes.map((s,i)=>
        <SceneTile key={s.id+version.config.seed} scene={s} version={version} tileW={tileW}
          locked={locks.has(s.index)} onLock={()=>toggleLock(s.index)}
          onReport={()=>setOpenReport(openReport===i?null:i)} reportOpen={openReport===i} />)}
    </div>
    {openReport!=null && version.scenes[openReport] && <Report scene={version.scenes[openReport]} />}
  </div>;
}

function LavcStudio() {
  const [srt, setSrt] = useState(DEMO_SRT);
  const [seed, setSeed] = useState(33);
  const [result, setResult] = useState(null);
  const [playing, setPlaying] = useState(null);
  const [error, setError] = useState(null);
  const generate=()=>{
    try{ const r=LAVC.generateVersions(srt, seed);
      if(!r.versions.length){ setError('No cues parsed — paste a valid SRT.'); setResult(null); return; }
      setError(null); setResult(r);
    }catch(e){ setError(String(e.message||e)); }
  };
  useEffect(()=>{ generate(); },[]);
  const update=(nv)=>setResult(r=>({ ...r, versions:r.versions.map(v=>v.id===nv.id?nv:v) }));
  return <div style={{ minHeight:'100vh', background:RP.canvas, fontFamily:F, padding:'0 0 80px' }}>
    <div style={{ position:'sticky', top:0, zIndex:50, background:'rgba(7,9,13,0.8)', backdropFilter:'blur(16px)', borderBottom:`1px solid ${RP.hairSoft}`, padding:'18px 40px', display:'flex', alignItems:'baseline', gap:20 }}>
      <div style={{ fontFamily:F, fontWeight:600, fontSize:19, letterSpacing:'-0.03em', color:RP.head }}>LAVC Variant Studio</div>
      <div style={{ ...micro }}>{'Deterministic text \u2192 many films \u00b7 grammar v1.0.0'}</div>
    </div>
    <div style={{ maxWidth:1200, margin:'0 auto', padding:'40px 40px 0' }}>
      <div style={{ display:'flex', gap:24, alignItems:'stretch', flexWrap:'wrap' }}>
        <textarea value={srt} onChange={e=>setSrt(e.target.value)} spellCheck={false}
          style={{ flex:'1 1 560px', minHeight:180, resize:'vertical', background:RP.surface, border:`1px solid ${RP.hairSoft}`, borderRadius:12, padding:'18px 20px', color:RP.body, fontFamily:mono, fontSize:12, lineHeight:1.6, outline:'none' }} />
        <div style={{ display:'flex', flexDirection:'column', gap:14, justifyContent:'flex-end', minWidth:220 }}>
          <div>
            <div style={{ ...micro, marginBottom:8 }}>Project seed</div>
            <input type="number" value={seed} onChange={e=>setSeed(Number(e.target.value)||0)}
              style={{ width:110, background:RP.surface, border:`1px solid ${RP.hairSoft}`, borderRadius:8, padding:'10px 14px', color:RP.head, fontFamily:mono, fontSize:14, outline:'none' }} />
          </div>
          <div onClick={generate} style={{ cursor:'pointer', textAlign:'center', fontFamily:F, fontWeight:600, fontSize:15, color:'#fff', background:RP.accent, padding:'14px 28px', borderRadius:999 }} style-hover={{ background:'#5580ED' }}>{'Generate versions \u2192'}</div>
          <div style={{ ...micro, fontSize:10, lineHeight:1.6, textTransform:'none', letterSpacing:'0.02em' }}>{'Same SRT + same seed \u2192 identical output. Lock scenes you like, regenerate the rest.'}</div>
        </div>
      </div>
      {error && <div style={{ marginTop:16, color:RP.bad, fontFamily:mono, fontSize:12 }}>{error}</div>}
      {result && <div style={{ display:'flex', flexDirection:'column', gap:20, marginTop:36 }}>
        <div style={{ ...micro }}>{result.versions.length + ' versions \u2014 ranked best first by mean selector score'}</div>
        {result.versions.map((v,i)=><VersionCard key={v.id} version={v} rank={i+1} srt={srt} onUpdate={update} onPlay={setPlaying} />)}
      </div>}
    </div>
    {playing && <Player version={playing} onClose={()=>setPlaying(null)} />}
  </div>;
}
window.LavcStudio = LavcStudio;
