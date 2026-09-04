/* "Invisible disability" — 2:44 narrated motion piece + 10s CTA, Ryan Perez system */
const { useComposition, CompositionStage, Captions, Easing, clamp,
        useTweaks, TweaksPanel, TweakSection, TweakToggle } = window;

const C = { canvas:'#07090D', surface:'#1A1D24', head:'#F5F7FA', body:'#C5C7CE', muted:'#8A8D96',
  accent:'#3F6EE9', bad:'#D8574F', good:'#3FA46A',
  hairSoft:'rgba(255,255,255,0.08)', hair:'rgba(255,255,255,0.15)' };
const F = "'Inter', sans-serif";

function enter(T, start, o = {}) {
  const dur = o.dur ?? 0.8, rise = o.rise ?? 24;
  const p = Easing.easeOutCubic(clamp((T - start) / dur, 0, 1));
  let op = p, y = (1 - p) * rise;
  if (o.out != null) {
    const q = Easing.easeOutCubic(clamp((T - o.out) / (o.outDur ?? 0.5), 0, 1));
    op *= (1 - q); y -= q * 16;
  }
  return { opacity: op, transform: `translateY(${y}px)` };
}
function draw(T, start, dur = 1) { return Easing.easeInOutCubic(clamp((T - start) / dur, 0, 1)); }
function pop(T, start, o = {}) {
  const dur = o.dur ?? 0.6, p = clamp((T - start) / dur, 0, 1), e = Easing.easeOutBack(p);
  let op = Math.min(1, p * 2);
  if (o.out != null) {
    const q = Easing.easeOutCubic(clamp((T - o.out) / (o.outDur ?? 0.5), 0, 1));
    op *= (1 - q);
  }
  return { opacity: op, transform: `scale(${0.8 + 0.2 * e})` };
}

const eyebrow = { fontFamily:F, fontWeight:600, fontSize:21, letterSpacing:'0.14em', textTransform:'uppercase', color:C.muted };
const h1 = { fontFamily:F, fontWeight:600, lineHeight:1.05, letterSpacing:'-0.05em', color:C.head, margin:0 };
const lead = { fontFamily:F, fontWeight:400, fontSize:38, lineHeight:1.45, color:C.body, margin:0 };
const micro = { fontFamily:F, fontWeight:600, fontSize:17, letterSpacing:'0.12em', textTransform:'uppercase', color:C.muted };

const CONDITIONS = ['Chronic pain','Autism','ADHD','PTSD','Lupus','Long COVID','Depression','Brain injuries'];

const CAPS = [
  { at:0.0,  text:"Invisible disability is internalized pain that nobody can see." },
  { at:4.5,  text:"It lives in your body and your brain," },
  { at:7.3,  text:"it slows you down, and some days it stops you completely —" },
  { at:11.3, text:"but there is no cast, no cane, no wheelchair to announce it." },
  { at:15.5, text:"Here is the number that changes how you see this." },
  { at:18.6, text:"One in four adults in the United States lives with a disability." },
  { at:23.2, text:"And in one survey, 74 percent of disabled people used no wheelchair, no aid, nothing visible at all." },
  { at:30.0, text:"Among people with chronic illness, an estimated 96 percent carry a condition you cannot see." },
  { at:36.2, text:"Read those numbers again." },
  { at:38.4, text:"The wheelchair is the logo of disability." },
  { at:41.5, text:"It is not the reality of disability." },
  { at:44.3, text:"The reality is chronic pain, autism, ADHD, PTSD, lupus, long COVID, depression, brain injuries —" },
  { at:52.6, text:"conditions that drain the battery before the day even starts.", until:58.5 },
  { at:64.2, text:"Now here is the part nobody warns you about." },
  { at:67.3, text:"When your disability is invisible, you get handed a second job, and it pays nothing:" },
  { at:72.5, text:"proving it." },
  { at:74.3, text:"Researchers actually have a name for what happens when people fail that job — disability invalidation." },
  { at:80.5, text:"It is the coworker who says \u201cyou look fine to me.\u201d" },
  { at:84.3, text:"It is the stranger at the parking spot." },
  { at:87.0, text:"It is family members who think you are lazy or dramatic." },
  { at:90.7, text:"Studies link this constant disbelief to higher rates of anxiety, depression, and social withdrawal." },
  { at:96.5, text:"And it changes behavior." },
  { at:98.4, text:"In one survey, 88 percent of people with invisible disabilities felt negative about even telling their employer." },
  { at:104.8, text:"Think about that." },
  { at:106.5, text:"Nine out of ten of us would rather struggle in silence" },
  { at:109.8, text:"than risk the sentence \u201cyou don't look disabled.\u201d", until:114.6 },
  { at:116.0, text:"So let me redefine it, because the textbook version misses the point." },
  { at:120.2, text:"An invisible disability is not a milder disability." },
  { at:123.6, text:"It is a full disability plus a tax." },
  { at:126.7, text:"You pay in energy before work starts." },
  { at:129.6, text:"You pay in pain nobody counts." },
  { at:132.2, text:"You pay in explanations nobody believes." },
  { at:135.4, text:"When I seem slow, or blunt, or exhausted, that is not a character flaw —" },
  { at:140.3, text:"that is the tax being collected in public." },
  { at:143.4, text:"So here is my ask, and it costs you nothing." },
  { at:146.6, text:"When someone tells you about a condition you cannot see, skip the audit." },
  { at:151.5, text:"You were never owed proof." },
  { at:154.0, text:"Believe people the first time —" },
  { at:156.4, text:"because 96 percent of this fight was designed to be invisible," },
  { at:160.3, text:"and disbelief is the only part of it we can actually remove.", until:164.0 },
];

function Film() {
  const { T, CUES } = useComposition();
  const OP = CUES.Opening, QTR = CUES.OneInFour, S74 = CUES.SeventyFour, S96 = CUES.NinetySix,
        LOGO = CUES.Logo, REAL = CUES.Reality, JOB = CUES.SecondJob, INV = CUES.Invalidation,
        DIS = CUES.Disbelief, S88 = CUES.EightyEight, RED = CUES.Redefine, TAX = CUES.Tax,
        ASK = CUES.Ask, CLOSE = CUES.Close;

  const v74 = Math.round(74 * draw(T, S74 + 1.6, 2.2));
  const v96 = Math.round(96 * draw(T, S96 + 0.8, 2.4));
  const v88 = Math.round(88 * draw(T, S88 + 1.6, 2.2));
  const strike = draw(T, LOGO + 3.4, 0.9);
  const batt = 1 - 0.82 * draw(T, REAL + 9.0, 3.2);
  const wp = draw(T, CLOSE - 0.05, 0.55);
  const oDrift = 1 + 0.04 * clamp(T / 15.5, 0, 1);

  const secs = [['Opening',OP],['OneInFour',QTR],['SeventyFour',S74],['NinetySix',S96],['Logo',LOGO],
    ['Reality',REAL],['SecondJob',JOB],['Invalidation',INV],['Disbelief',DIS],['EightyEight',S88],
    ['Redefine',RED],['Tax',TAX],['Ask',ASK],['Close',CLOSE]];
  let label = 'Opening'; for (const [n, st] of secs) if (T >= st) label = n;

  return <div data-screen-label={`${label} · t=${Math.floor(T)}s`}
    style={{ position:'absolute', inset:0, background:C.canvas, overflow:'hidden', fontFamily:F }}>
    <div style={{ position:'absolute', inset:0, background:'radial-gradient(1100px 760px at 0% 32%, rgba(255,255,255,0.06), transparent 62%)' }} />

    {/* Opening */}
    <div style={{ position:'absolute', left:150, top:250, transform:`scale(${oDrift})`, transformOrigin:'0 40%' }}>
      <div style={{ ...eyebrow, ...enter(T, 0.4, { out:QTR - 0.4 }) }}>Ryan Perez — Keynote</div>
      <h1 style={{ ...h1, fontSize:126, marginTop:30, ...enter(T, 0.8, { out:QTR - 0.4 }) }}>Invisible disability.</h1>
      <p style={{ ...lead, marginTop:32, color:C.muted, fontSize:34, ...enter(T, 2.2, { out:QTR - 0.35 }) }}>Pain nobody can see.</p>
      <div style={{ display:'flex', gap:56, marginTop:64 }}>
        {['No cast', 'No cane', 'No wheelchair'].map((txt, i) =>
          <div key={i} style={{ position:'relative', fontFamily:F, fontWeight:600, fontSize:40, letterSpacing:'-0.02em', color:C.body, ...enter(T, 11.5 + i * 0.5, { out:QTR - 0.3 }) }}>
            {txt}
            <div style={{ position:'absolute', left:-6, right:-6, top:'52%', height:2, background:C.muted, transform:`scaleX(${draw(T, 11.8 + i * 0.5, 0.5)})`, transformOrigin:'left' }} />
          </div>)}
      </div>
    </div>

    {/* OneInFour */}
    <div style={{ position:'absolute', left:150, top:300 }}>
      <div style={{ ...eyebrow, ...enter(T, QTR + 0.3, { out:S74 - 0.35 }) }}>Adults in the United States</div>
      <div style={{ display:'flex', gap:56, marginTop:70 }}>
        {[0,1,2,3].map(i => {
          const on = i === 0 ? draw(T, QTR + 2.4, 0.8) : 0;
          return <div key={i} style={{ width:150, height:150, borderRadius:'50%', border:`1.5px solid ${C.hair}`,
            background: on ? C.accent : 'transparent', borderColor: on ? C.accent : C.hair,
            ...pop(T, QTR + 0.6 + i * 0.22, { out:S74 - 0.35 }) }} />; })}
      </div>
      <h1 style={{ ...h1, fontSize:76, marginTop:70, ...enter(T, QTR + 2.8, { out:S74 - 0.3 }) }}>1 in 4 lives with a disability.</h1>
    </div>

    {/* SeventyFour */}
    <div style={{ position:'absolute', left:150, top:270 }}>
      <div style={{ ...eyebrow, ...enter(T, S74 + 0.3, { out:S96 - 0.35 }) }}>Of disabled people, in one survey</div>
      <div style={{ fontFamily:F, fontWeight:600, fontSize:290, lineHeight:1, letterSpacing:'-0.05em', color:C.head, marginTop:20, ...enter(T, S74 + 1.4, { out:S96 - 0.35 }) }}>{v74}%</div>
      <p style={{ ...lead, marginTop:26, ...enter(T, S74 + 3.6, { out:S96 - 0.3 }) }}>No wheelchair. No aid. Nothing visible at all.</p>
    </div>

    {/* NinetySix */}
    <div style={{ position:'absolute', left:150, top:250 }}>
      <div style={{ ...eyebrow, ...enter(T, S96 + 0.3, { out:LOGO - 0.35 }) }}>Of people with chronic illness</div>
      <div style={{ fontFamily:F, fontWeight:600, fontSize:330, lineHeight:1, letterSpacing:'-0.05em', color:C.accent, marginTop:20, ...enter(T, S96 + 0.6, { out:LOGO - 0.35 }) }}>{v96}%</div>
      <p style={{ ...lead, marginTop:26, ...enter(T, S96 + 3.4, { out:LOGO - 0.3 }) }}>carry a condition you cannot see.</p>
    </div>

    {/* Logo vs reality */}
    <div style={{ position:'absolute', left:150, top:380 }}>
      <div style={{ position:'relative', display:'inline-block' }}>
        <h1 style={{ ...h1, fontSize:92, ...enter(T, LOGO + 0.4, { out:REAL - 0.35 }) }}>The wheelchair is the logo.</h1>
        <div style={{ position:'absolute', left:-8, right:-8, top:'54%', height:4, background:C.bad, transform:`scaleX(${strike})`, transformOrigin:'left', opacity:1 - draw(T, REAL - 0.35, 0.5) }} />
      </div>
      <h1 style={{ ...h1, fontSize:92, marginTop:26, color:C.body, ...enter(T, LOGO + 3.2, { out:REAL - 0.3 }) }}>It is not the reality.</h1>
    </div>

    {/* Reality — condition chips + battery */}
    <div style={{ position:'absolute', left:150, top:250, width:1440 }}>
      <div style={{ ...eyebrow, ...enter(T, REAL + 0.2, { out:JOB - 0.4 }) }}>The reality</div>
      <div style={{ display:'flex', flexWrap:'wrap', gap:24, marginTop:56, width:1300 }}>
        {CONDITIONS.map((txt, i) =>
          <div key={i} style={{ fontFamily:F, fontWeight:600, fontSize:36, letterSpacing:'-0.02em', color:C.head,
            border:`1px solid ${C.hair}`, borderRadius:16, padding:'26px 44px', background:C.surface,
            ...pop(T, REAL + 0.5 + i * 0.55, { out:JOB - 0.4 }) }}>{txt}</div>)}
      </div>
      <div style={{ marginTop:80, ...enter(T, REAL + 8.6, { out:JOB - 0.35 }) }}>
        <div style={{ ...micro }}>Battery — before the day even starts</div>
        <div style={{ position:'relative', marginTop:22, width:900, height:26, border:`1px solid ${C.hair}`, borderRadius:8 }}>
          <div style={{ position:'absolute', left:3, top:3, bottom:3, borderRadius:5, width:894 * batt, background: batt > 0.4 ? C.accent : C.bad }} />
        </div>
        <div style={{ fontFamily:F, fontWeight:600, fontSize:32, color: batt > 0.4 ? C.head : C.bad, marginTop:18 }}>{Math.round(batt * 100)}%</div>
      </div>
    </div>

    {/* SecondJob */}
    <div style={{ position:'absolute', left:150, top:300 }}>
      <div style={{ ...eyebrow, ...enter(T, JOB + 0.4, { out:INV - 0.4 }) }}>The part nobody warns you about</div>
      <div style={{ marginTop:56, width:820, background:C.surface, border:`1px solid ${C.hairSoft}`, borderRadius:24, padding:'56px 64px', ...enter(T, JOB + 3.4, { out:INV - 0.4 }) }}>
        <div style={{ ...micro }}>Second job — assigned, not applied for</div>
        <h1 style={{ ...h1, fontSize:84, marginTop:22, ...enter(T, JOB + 8.4, { rise:16 }) }}>Proving it.</h1>
        <div style={{ display:'flex', gap:40, marginTop:40, alignItems:'baseline' }}>
          <div style={{ ...micro }}>Salary</div>
          <div style={{ fontFamily:F, fontWeight:600, fontSize:48, letterSpacing:'-0.03em', color:C.bad, ...pop(T, JOB + 5.4) }}>$0</div>
        </div>
      </div>
    </div>

    {/* Invalidation */}
    <div style={{ position:'absolute', left:150, top:240, width:1100 }}>
      <div style={{ ...eyebrow, ...enter(T, INV + 0.4, { out:DIS - 0.4 }) }}>The researchers' term: disability invalidation</div>
      <div style={{ display:'flex', flexDirection:'column', gap:32, marginTop:56 }}>
        {[["\u201cYou look fine to me.\u201d", 'The coworker', 6.2], ["\u201cThat spot isn't for you.\u201d", 'The stranger at the parking spot', 10.0], ["\u201cYou're just lazy. Or dramatic.\u201d", 'Family', 12.7]].map(([q, who, d], i) =>
          <div key={i} style={{ width:900, background:C.surface, border:`1px solid ${C.hairSoft}`, borderRadius:16, padding:'34px 44px', ...enter(T, INV + d, { out:DIS - 0.4 }) }}>
            <div style={{ fontFamily:F, fontWeight:600, fontSize:42, letterSpacing:'-0.02em', color:C.head }}>{q}</div>
            <div style={{ ...micro, marginTop:16 }}>{who}</div>
          </div>)}
      </div>
    </div>

    {/* Disbelief */}
    <div style={{ position:'absolute', left:150, top:320, width:1100 }}>
      <div style={{ ...eyebrow, ...enter(T, DIS + 0.3, { out:S88 - 0.4 }) }}>What constant disbelief is linked to</div>
      <div style={{ display:'flex', gap:64, marginTop:64 }}>
        {['Anxiety', 'Depression', 'Social withdrawal'].map((txt, i) =>
          <div key={i} style={{ display:'flex', gap:20, alignItems:'baseline', fontFamily:F, fontWeight:600, fontSize:46, letterSpacing:'-0.02em', color:C.head, ...enter(T, DIS + 1.2 + i * 0.6, { out:S88 - 0.4 }) }}>
            <span style={{ color:C.bad }}>↑</span> {txt}
          </div>)}
      </div>
    </div>

    {/* EightyEight */}
    <div style={{ position:'absolute', left:150, top:230 }}>
      <div style={{ ...eyebrow, ...enter(T, S88 + 0.4, { out:RED - 0.4 }) }}>Felt negative about even telling their employer</div>
      <div style={{ fontFamily:F, fontWeight:600, fontSize:280, lineHeight:1, letterSpacing:'-0.05em', color:C.head, marginTop:16, ...enter(T, S88 + 1.4, { out:RED - 0.4 }) }}>{v88}%</div>
      <div style={{ display:'flex', gap:30, marginTop:56, ...enter(T, S88 + 7.6, { out:RED - 0.35 }) }}>
        {[...Array(10)].map((_, i) =>
          <div key={i} style={{ width:20, height:20, borderRadius:'50%', background: i < 9 ? C.muted : C.accent,
            opacity: i < 9 ? 0.5 : 1, ...pop(T, S88 + 8.0 + i * 0.12) }} />)}
      </div>
      <p style={{ ...lead, marginTop:36, ...enter(T, S88 + 8.4, { out:RED - 0.35 }) }}>Nine out of ten would rather struggle in silence</p>
      <p style={{ ...lead, marginTop:10, color:C.bad, ...enter(T, S88 + 11.4, { out:RED - 0.3 }) }}>{"than hear \u201cyou don't look disabled.\u201d"}</p>
    </div>

    {/* Redefine */}
    <div style={{ position:'absolute', left:150, top:360 }}>
      <h1 style={{ ...h1, fontSize:88, color:C.muted, ...enter(T, RED + 0.4, { out:TAX - 0.4 }) }}>Not a milder disability.</h1>
      <h1 style={{ ...h1, fontSize:88, marginTop:22, ...enter(T, RED + 7.4, { out:TAX - 0.35 }) }}>A full disability <span style={{ color:C.accent }}>+ a tax.</span></h1>
    </div>

    {/* Tax */}
    <div style={{ position:'absolute', left:150, top:230, width:1000 }}>
      <div style={{ ...eyebrow, ...enter(T, TAX + 0.2, { out:ASK - 0.4 }) }}>The invisible tax</div>
      <div style={{ display:'flex', flexDirection:'column', marginTop:52, width:880 }}>
        {[['Energy', 'paid before work starts', 0.3], ['Pain', 'nobody counts it', 3.2], ['Explanations', 'nobody believes them', 5.8]].map(([item, note, d], i) =>
          <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', padding:'30px 0', borderBottom:`1px solid ${C.hairSoft}`, ...enter(T, TAX + d, { out:ASK - 0.4 }) }}>
            <div style={{ fontFamily:F, fontWeight:600, fontSize:46, letterSpacing:'-0.02em', color:C.head }}>{item}</div>
            <div style={{ ...lead, fontSize:32, color:C.muted }}>{note}</div>
          </div>)}
      </div>
      <h1 style={{ ...h1, fontSize:62, marginTop:56, ...enter(T, TAX + 13.2, { out:ASK - 0.35 }) }}>Collected <span style={{ color:C.bad }}>in public.</span></h1>
    </div>

    {/* Ask */}
    <div style={{ position:'absolute', left:150, top:280, width:1250 }}>
      <div style={{ ...eyebrow, ...enter(T, ASK + 0.4, { out:CLOSE - 0.4 }) }}>The ask — it costs you nothing</div>
      <h1 style={{ ...h1, fontSize:96, marginTop:36, ...enter(T, ASK + 4.4, { out:CLOSE - 0.4 }) }}>Skip the audit.</h1>
      <h1 style={{ ...h1, fontSize:96, marginTop:16, color:C.body, ...enter(T, ASK + 8.4, { out:CLOSE - 0.4 }) }}>You were never owed proof.</h1>
      <h1 style={{ ...h1, fontSize:96, marginTop:16, color:C.accent, ...enter(T, ASK + 11.0, { out:CLOSE - 0.35 }) }}>Believe people the first time.</h1>
      <p style={{ ...lead, fontSize:34, marginTop:44, color:C.muted, ...enter(T, ASK + 13.4, { out:CLOSE - 0.35 }) }}>96% of this fight was designed to be invisible. Disbelief is the only part we can remove.</p>
    </div>

    {/* Close — the one saturated cut */}
    <div style={{ position:'absolute', inset:0, background:C.accent, transform:`scaleY(${wp})`, transformOrigin:'bottom' }} />
    <div style={{ position:'absolute', left:150, top:300, opacity:wp }}>
      <div style={{ ...eyebrow, color:'rgba(255,255,255,0.75)', ...enter(T, CLOSE + 0.8) }}>The keynote</div>
      <h1 style={{ ...h1, fontSize:120, color:'#FFFFFF', marginTop:28, ...enter(T, CLOSE + 1.1) }}>Believe people</h1>
      <h1 style={{ ...h1, fontSize:120, color:'#FFFFFF', ...enter(T, CLOSE + 1.4) }}>the first time.</h1>
      <div style={{ display:'flex', alignItems:'center', gap:40, marginTop:56, ...pop(T, CLOSE + 3.0) }}>
        <div style={{ fontFamily:F, fontWeight:600, fontSize:30, letterSpacing:'-0.01em', color:C.canvas, background:C.head, padding:'24px 52px', borderRadius:999 }}>Book the keynote →</div>
        <div style={{ ...eyebrow, color:'rgba(255,255,255,0.75)', ...enter(T, CLOSE + 3.8, { rise:10 }) }}>ryanperez.ca</div>
      </div>
    </div>

    <Captions items={CAPS} style={{ font:`400 33px Inter, sans-serif`, color:C.body, bottom:'4.5%', textShadow:'none', lineHeight:1.4 }} />
  </div>;
}

function InvisibleFilm() {
  const [t, setTweak] = useTweaks(window.TWEAK_DEFAULTS || { motionEditor: true });
  return <div style={{ width:'100%', height:'100%', background:C.canvas }}>
    <CompositionStage width={1920} height={1080} scenes={window.OM_SCENES} playback={window.OM_PLAYBACK} bg={C.canvas}>
      <Film />
    </CompositionStage>
    <TweaksPanel>
      <TweakSection label="Timeline" />
      <TweakToggle label="Motion editor" value={t.motionEditor} onChange={(v) => setTweak('motionEditor', v)} />
    </TweaksPanel>
  </div>;
}
window.InvisibleFilm = InvisibleFilm;
