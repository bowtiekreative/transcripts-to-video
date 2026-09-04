/* "Bullies detect autism first" — 2:47 narrated motion piece, Ryan Perez system */
const { useComposition, CompositionStage, Captions, Easing, clamp,
        useTweaks, TweaksPanel, TweakSection, TweakToggle } = window;

const C = { canvas:'#07090D', surface:'#1A1D24', head:'#F5F7FA', body:'#C5C7CE', muted:'#8A8D96',
  accent:'#3F6EE9', bad:'#D8574F',
  hairSoft:'rgba(255,255,255,0.08)', hair:'rgba(255,255,255,0.15)' };
const F = "'Inter', sans-serif";

/* the three motion helpers */
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

/* dot field geometry */
const COLS = 10, ROWS = 4, SP = 88, GX = 1000, GY = 330, ODD = { r:1, c:5 };
const oddX = GX + ODD.c * SP, oddY = GY + ODD.r * SP;
const dotAt = (r, c) => [GX + c * SP, GY + r * SP];
const RETICLE_STOPS = [[2,1],[0,3],[3,5],[1,8],[2,6],[ODD.r,ODD.c]];
const NET_SOURCES = [[0,0],[3,2],[2,9],[0,7],[3,7],[1,1],[2,3],[0,5],[3,4],[1,9]];

/* captions — the narration, timed to the SRT */
const CAPS = [
  { at:0.0,  text:"The bullies knew before anyone else did." },
  { at:2.9,  text:"Before my doctors, before my teachers, before my own family —" },
  { at:6.5,  text:"the kids in the hallway had me figured out." },
  { at:9.7,  text:"I didn't get my autism diagnosis until I was an adult," },
  { at:13.7, text:"but the bullying started in elementary school," },
  { at:16.2, text:"and the numbers say my story is the standard one." },
  { at:19.8, text:"A study in the Archives of Pediatrics and Adolescent Medicine" },
  { at:23.4, text:"found that about 46 percent of autistic teens were bullied at school in a single year," },
  { at:29.2, text:"compared to roughly 11 percent of kids in general —" },
  { at:32.4, text:"nearly five times the rate." },
  { at:34.2, text:"And a Kennedy Krieger survey of over a thousand autistic children" },
  { at:38.2, text:"found that 63 percent had been bullied at some point in their lives." },
  { at:42.9, text:"Think about what that means." },
  { at:44.7, text:"Most of these kids didn't have a diagnosis on their forehead." },
  { at:48.7, text:"Many, like me, didn't have a diagnosis at all." },
  { at:51.9, text:"The bullies found us anyway." },
  { at:54.2, text:"So how did children with no medical training outperform the entire adult world at spotting autism?" },
  { at:60.0, text:"The answer sits in a 2017 study by Sasson and colleagues." },
  { at:64.0, text:"They showed people short clips of autistic adults — some just a few seconds long —" },
  { at:69.0, text:"and asked for first impressions." },
  { at:70.8, text:"The ratings came back less favorable across the board:" },
  { at:74.0, text:"less desire to talk to them, less desire to sit near them." },
  { at:78.3, text:"The raters had no idea who was autistic." },
  { at:81.2, text:"They just sensed difference, instantly, from a few seconds of video." },
  { at:85.2, text:"Now put that finding in a school hallway." },
  { at:88.1, text:"A bully's entire job is scanning for difference —" },
  { at:91.0, text:"for the kid who moves differently, talks differently, reacts differently." },
  { at:94.6, text:"Adults needed me to fail a formal assessment." },
  { at:97.5, text:"The kids by the lockers needed about ten seconds." },
  { at:100.7, text:"The detection system was always there." },
  { at:103.5, text:"It just belonged to the wrong people." },
  { at:111.2, text:"And once bullies find an autistic kid, researchers say we make what they have actually called the perfect victim." },
  { at:118.0, text:"We often can't tell an insult from a joke, so the bully rarely gets caught." },
  { at:123.4, text:"We struggle to report what we can't fully name." },
  { at:126.6, text:"Some bullies go further —" },
  { at:128.5, text:"the Kennedy Krieger research found autistic kids being deliberately triggered into meltdowns," },
  { at:132.3, text:"so the victim looks like the problem while the bully watches the show." },
  { at:137.0, text:"Here's the part I can't stop thinking about:" },
  { at:139.9, text:"for decades, the most accurate autism-detection network in every school was the bullies." },
  { at:144.6, text:"They screened earlier than the doctors, faster than the teachers, and for free —" },
  { at:149.3, text:"and then they used the results as a weapon." },
  { at:152.5, text:"Every autistic adult who says \u201cthe bullies found me first\u201d is describing the same failure." },
  { at:157.9, text:"The signal was visible the whole time." },
  { at:160.4, text:"The only people paying attention were the ones looking for a target.", until:166.2 },
];

function Film() {
  const { T, CUES } = useComposition();
  const OP = CUES.Opening, DIA = CUES.Diagnosis, FIVE = CUES.FiveTimes, SIX = CUES.SixtyThree,
        FOUND = CUES.FoundAnyway, QUE = CUES.Question, SAS = CUES.Sasson, HALL = CUES.Hallway,
        WRONG = CUES.WrongPeople, PV = CUES.PerfectVictim, MELT = CUES.Meltdown, NET = CUES.Network,
        SIG = CUES.Signal, REF = CUES.Reframe, CLOSE = CUES.Close;

  /* ---- camera over the dot world ---- */
  const zoomIn = draw(T, HALL + 9.8, 2.2);
  const zoomOut = draw(T, NET + 0.2, 2.0);
  const push = 0.22 * draw(T, SIG + 1, 9);
  const z = clamp(zoomIn - zoomOut, 0, 1) + push;
  const s = 1 + 1.35 * z;
  const tx = z * (960 - oddX * 2.35), ty = z * (540 - oddY * 2.35);
  const wOp = clamp(1 - draw(T, QUE + 0.2, 0.7) + draw(T, HALL + 0.2, 0.7) - draw(T, REF - 0.6, 0.7), 0, 1);
  const meltP = draw(T, MELT + 0.4, 1.5) * (1 - draw(T, NET, 1.2));
  const sigP = draw(T, SIG + 0.5, 1.5);

  /* ---- dots ---- */
  const dots = [];
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const i = r * COLS + c, odd = (r === ODD.r && c === ODD.c);
    const ap = pop(T, FOUND + 0.15 + i * 0.028);
    const amp = odd ? draw(T, FOUND + 1.2, 1.6) : 1;
    let dx = odd ? Math.sin(T * 1.6 + 1.3) * 8 * amp : 0;
    let dy = odd ? Math.cos(T * 1.05 + 0.5) * 9 * amp : Math.sin(T * 0.9 + i * 0.7) * 3;
    if (odd) { dx += Math.sin(T * 9 + 2) * 10 * meltP; dy += Math.cos(T * 8) * 9 * meltP; }
    const dim = odd ? 1 : (1 - 0.6 * z) * (1 - 0.92 * sigP);
    dots.push(React.createElement('div', { key: i, style: {
      position:'absolute', left: GX + c * SP - 6, top: GY + r * SP - 6, width:12, height:12,
      borderRadius:'50%', background: odd ? C.head : C.muted,
      opacity: ap.opacity * dim, transform: `translate(${dx}px,${dy}px) ${ap.transform}` } }));
    if (odd) dots.push(React.createElement('div', { key:'oddglow', style: {
      position:'absolute', left: GX + c * SP - 6, top: GY + r * SP - 6, width:12, height:12,
      borderRadius:'50%', background: C.accent, opacity: ap.opacity * sigP,
      transform: `translate(${dx}px,${dy}px) scale(${1 + 0.35 * sigP * (0.5 + 0.5 * Math.sin(T * 3))})` } }));
  }

  /* ---- circle, reticle, network lines (world svg) ---- */
  const cd = draw(T, FOUND + 9.0, 1.0);
  const netLines = NET_SOURCES.map(([r, c], i) => {
    const [x1, y1] = dotAt(r, c);
    const dxl = oddX - x1, dyl = oddY - y1, L = Math.hypot(dxl, dyl), ux = dxl / L, uy = dyl / L;
    const ld = draw(T, NET + 2.9 + i * 0.14, 0.7);
    return <line key={i} x1={x1 + ux * 16} y1={y1 + uy * 16} x2={oddX - ux * 48} y2={oddY - uy * 48}
      stroke={C.hair} strokeWidth={0.9} opacity={1 - sigP} pathLength="1" strokeDasharray="1" strokeDashoffset={1 - ld} />;
  });
  /* reticle scan */
  let rx = 0, ry = 0;
  { const [x0, y0] = dotAt(...RETICLE_STOPS[0]); rx = x0; ry = y0;
    for (let i = 0; i < RETICLE_STOPS.length - 1; i++) {
      const [xa, ya] = dotAt(...RETICLE_STOPS[i]), [xb, yb] = dotAt(...RETICLE_STOPS[i + 1]);
      const f = draw(T, HALL + 2 + i * 1.56, 1.0);
      rx += (xb - xa) * f; ry += (yb - ya) * f;
    } }
  const retOp = draw(T, HALL + 1.4, 0.6) * (1 - draw(T, WRONG, 0.6));

  /* ---- scene-local values ---- */
  const diaDot = draw(T, DIA + 1.5, 6.5);
  const v46 = Math.round(46 * draw(T, FIVE + 3.6, 2.0));
  const v11 = Math.round(11 * draw(T, FIVE + 9.4, 1.2));
  const v63 = Math.round(63 * draw(T, SIX + 3.8, 1.8));
  const secsCount = Math.round(10 * draw(T, HALL + 12.3, 2.2));
  const wp = draw(T, CLOSE - 0.05, 0.55);
  const oDrift = 1 + 0.04 * clamp(T / 9.7, 0, 1);

  const secs = [['Opening',OP],['Diagnosis',DIA],['FiveTimes',FIVE],['SixtyThree',SIX],['FoundAnyway',FOUND],
    ['Question',QUE],['Sasson',SAS],['Hallway',HALL],['WrongPeople',WRONG],['PerfectVictim',PV],
    ['Meltdown',MELT],['Network',NET],['Signal',SIG],['Reframe',REF],['Close',CLOSE]];
  let label = 'Opening'; for (const [n, st] of secs) if (T >= st) label = n;

  const barRow = (labelTxt, val, w, color, tStart, out) =>
    <div style={{ display:'flex', alignItems:'center', gap:32, ...enter(T, tStart, { out }) }}>
      <div style={{ ...micro, width:260 }}>{labelTxt}</div>
      <div style={{ height:22, width:w, background:color, borderRadius:4 }} />
      <div style={{ fontFamily:F, fontWeight:600, fontSize:44, letterSpacing:'-0.03em', color:C.head }}>{val}%</div>
    </div>;

  return <div data-screen-label={`${label} · t=${Math.floor(T)}s`}
    style={{ position:'absolute', inset:0, background:C.canvas, overflow:'hidden', fontFamily:F }}>
    <div style={{ position:'absolute', inset:0, background:'radial-gradient(1100px 760px at 0% 32%, rgba(255,255,255,0.06), transparent 62%)' }} />

    {/* dot world */}
    <div style={{ position:'absolute', inset:0, opacity:wOp, transform:`translate(${tx}px,${ty}px) scale(${s})`, transformOrigin:'0 0' }}>
      {dots}
      <svg width="1920" height="1080" style={{ position:'absolute', left:0, top:0, overflow:'visible' }}>
        {netLines}
        <rect x={rx - 30} y={ry - 30} width={60} height={60} fill="none" stroke={C.hair} strokeWidth={1.2} opacity={retOp} rx={8} />
        <circle cx={oddX} cy={oddY} r={36} fill="none" stroke={C.accent} strokeWidth={1.6}
          pathLength="1" strokeDasharray="1" strokeDashoffset={1 - cd} transform={`rotate(-90 ${oddX} ${oddY})`} />
        <circle cx={oddX} cy={oddY} r={50} fill="none" stroke={C.bad} strokeWidth={1.4}
          opacity={meltP * (0.45 + 0.45 * Math.sin(T * 6))} />
      </svg>
    </div>

    {/* Opening */}
    <div style={{ position:'absolute', left:150, top:300, transform:`scale(${oDrift})`, transformOrigin:'0 40%' }}>
      <div style={{ ...eyebrow, ...enter(T, 0.5, { out:9.0 }) }}>Ryan Perez — Keynote</div>
      <h1 style={{ ...h1, fontSize:132, marginTop:30, ...enter(T, 1.0, { out:9.0 }) }}>Bullies detect</h1>
      <h1 style={{ ...h1, fontSize:132, ...enter(T, 1.3, { out:9.05 }) }}>autism first.</h1>
      <p style={{ ...lead, marginTop:38, color:C.muted, fontSize:34, ...enter(T, 3.2, { out:9.1 }) }}>The first people to notice weren't doctors.</p>
    </div>

    {/* Diagnosis — life timeline */}
    <div style={{ position:'absolute', left:150, top:430, width:1440 }}>
      <div style={{ ...eyebrow, ...enter(T, DIA + 0.4, { out:DIA + 9.5 }) }}>One life, two discoveries</div>
      <div style={{ position:'relative', marginTop:110, height:100, ...enter(T, DIA + 0.8, { out:DIA + 9.5 }) }}>
        <div style={{ position:'absolute', left:0, top:30, height:1, width:1340, background:C.hairSoft, transform:`scaleX(${draw(T, DIA + 0.8, 1.5)})`, transformOrigin:'left' }} />
        <div style={{ position:'absolute', left:0, top:24, width:1, height:13, background:C.hair }} />
        <div style={{ position:'absolute', left:1339, top:24, width:1, height:13, background:C.hair, opacity:draw(T, DIA + 7.2, 0.5) }} />
        <div style={{ position:'absolute', left:1340 * diaDot - 5, top:25, width:10, height:10, borderRadius:'50%', background:C.accent }} />
        <div style={{ ...micro, position:'absolute', left:0, top:58, ...enter(T, DIA + 1.2, { rise:10 }) }}>Elementary school — the bullying starts</div>
        <div style={{ ...micro, position:'absolute', right:0, top:58, textAlign:'right', opacity:draw(T, DIA + 7.2, 0.5) }}>Adulthood — the diagnosis</div>
      </div>
    </div>

    {/* FiveTimes — 46% vs 11% */}
    <div style={{ position:'absolute', left:150, top:300 }}>
      <div style={{ ...eyebrow, ...enter(T, FIVE + 0.5, { out:FIVE + 13.9 }) }}>Bullied in one school year</div>
      <div style={{ display:'flex', flexDirection:'column', gap:44, marginTop:70 }}>
        {barRow('Autistic teens', v46, 900 * draw(T, FIVE + 3.6, 2.0), C.accent, FIVE + 3.3, FIVE + 13.9)}
        {barRow('All students', v11, 215 * draw(T, FIVE + 9.4, 1.2), C.muted, FIVE + 9.1, FIVE + 13.95)}
      </div>
      <div style={{ display:'flex', alignItems:'baseline', gap:28, marginTop:80, ...pop(T, FIVE + 12.6, { out:FIVE + 14.0 }) }}>
        <div style={{ fontFamily:F, fontWeight:600, fontSize:150, lineHeight:1, letterSpacing:'-0.05em', color:C.head }}>≈5×</div>
        <div style={{ ...lead, fontSize:34, color:C.muted }}>the rate</div>
      </div>
      <div style={{ ...micro, marginTop:56, ...enter(T, FIVE + 1.2, { out:FIVE + 13.9 }) }}>Archives of Pediatrics &amp; Adolescent Medicine</div>
    </div>

    {/* SixtyThree */}
    <div style={{ position:'absolute', left:150, top:260 }}>
      <div style={{ ...eyebrow, ...enter(T, SIX + 0.4, { out:SIX + 8.4 }) }}>Kennedy Krieger Institute · 1,000+ autistic children</div>
      <div style={{ fontFamily:F, fontWeight:600, fontSize:330, lineHeight:1, letterSpacing:'-0.05em', color:C.head, marginTop:24, ...enter(T, SIX + 3.6, { out:SIX + 8.4 }) }}>{v63}%</div>
      <p style={{ ...lead, marginTop:30, ...enter(T, SIX + 5.6, { out:SIX + 8.45 }) }}>bullied at some point in their lives.</p>
    </div>

    {/* FoundAnyway */}
    <div style={{ position:'absolute', left:150, top:420, width:760 }}>
      <h1 style={{ ...h1, fontSize:76, ...enter(T, FOUND + 1.8, { out:QUE - 0.3 }) }}>No diagnosis.</h1>
      <h1 style={{ ...h1, fontSize:76, ...enter(T, FOUND + 3.4, { out:QUE - 0.3 }) }}>No label.</h1>
      <h1 style={{ ...h1, fontSize:76, color:C.accent, marginTop:20, ...enter(T, FOUND + 9.0, { out:QUE - 0.25 }) }}>Found anyway.</h1>
    </div>

    {/* Question */}
    <div style={{ position:'absolute', left:150, top:340, width:1100 }}>
      <h1 style={{ ...h1, fontSize:190, ...enter(T, QUE + 0.4, { out:QUE + 5.4 }) }}>How?</h1>
      <p style={{ ...lead, fontSize:42, marginTop:36, width:860, ...enter(T, QUE + 1.3, { out:QUE + 5.45 }) }}>No medical training. Better detection than the entire adult world.</p>
    </div>

    {/* Sasson study */}
    <div style={{ position:'absolute', left:150, top:190 }}>
      <div style={{ ...eyebrow, ...enter(T, SAS + 0.5, { out:SAS + 24.6 }) }}>Sasson et al., 2017 · First impressions of autistic adults</div>
      <div style={{ display:'flex', gap:32, marginTop:56 }}>
        {[0,1,2,3,4].map(i => {
          const q = draw(T, SAS + 18.3, 0.6);
          return <div key={i} style={{ width:252, height:158, background:C.surface, border:`1px solid ${C.hairSoft}`, borderRadius:16, position:'relative', ...pop(T, SAS + 4 + i * 0.18, { out:SAS + 24.6 }) }}>
            <div style={{ position:'absolute', left:24, top:24, width:14, height:14, borderRadius:'50%', background:C.muted, opacity:1 - q }} />
            <div style={{ position:'absolute', left:20, top:8, fontFamily:F, fontWeight:600, fontSize:40, color:C.head, opacity:q }}>?</div>
            <div style={{ ...micro, position:'absolute', left:24, bottom:20 }}>Clip 0{i + 1} · 0:0{3 + i}</div>
          </div>; })}
      </div>
      <div style={{ display:'flex', flexDirection:'column', gap:34, marginTop:72 }}>
        {[['Want to talk with them', 0], ['Want to sit near them', 0.5]].map(([lab, d], i) =>
          <div key={i} style={{ display:'flex', alignItems:'center', gap:32, ...enter(T, SAS + 10.6 + d, { out:SAS + 24.65 }) }}>
            <div style={{ ...micro, width:300 }}>{lab}</div>
            <div style={{ position:'relative', width:620, height:14, background:'rgba(255,255,255,0.05)', borderRadius:4 }}>
              <div style={{ position:'absolute', left:0, top:0, bottom:0, borderRadius:4, background:C.bad, width:620 * (0.78 - 0.46 * draw(T, SAS + 11 + d, 1.8)) }} />
            </div>
          </div>)}
      </div>
      <div style={{ ...micro, marginTop:64, color:C.body, ...enter(T, SAS + 18.3, { out:SAS + 24.7 }) }}>The raters were never told who was autistic</div>
    </div>

    {/* Hallway */}
    <div style={{ position:'absolute', left:150, top:280, width:760 }}>
      <div style={{ ...eyebrow, ...enter(T, HALL + 1.2, { out:WRONG - 0.4 }) }}>Time to detect</div>
      <p style={{ ...lead, fontSize:36, marginTop:40, color:C.muted, ...enter(T, HALL + 9.4, { out:WRONG - 0.4 }) }}>Adults — a formal assessment.</p>
      <div style={{ display:'flex', alignItems:'baseline', gap:24, marginTop:26, ...enter(T, HALL + 12.1, { out:WRONG - 0.35 }) }}>
        <p style={{ ...lead, fontSize:36, margin:0 }}>The kids —</p>
        <div style={{ fontFamily:F, fontWeight:600, fontSize:120, lineHeight:1, letterSpacing:'-0.05em', color:C.head }}>{secsCount}</div>
        <p style={{ ...lead, fontSize:36, margin:0, color:C.muted }}>seconds.</p>
      </div>
    </div>

    {/* WrongPeople */}
    <div style={{ position:'absolute', left:150, top:320, width:1000 }}>
      <h1 style={{ ...h1, fontSize:72, ...enter(T, WRONG + 0.4, { out:WRONG + 10.0 }) }}>The detection system was always there.</h1>
      <h1 style={{ ...h1, fontSize:72, marginTop:22, ...enter(T, WRONG + 2.6, { out:WRONG + 10.05 }) }}>It just belonged to the <span style={{ color:C.bad }}>wrong people.</span></h1>
    </div>

    {/* PerfectVictim */}
    <div style={{ position:'absolute', left:150, top:280, width:900 }}>
      <div style={{ ...eyebrow, ...enter(T, PV + 0.8, { out:PV + 15.0 }) }}>“The perfect victim” — the researchers' own term</div>
      <div style={{ display:'flex', flexDirection:'column', gap:40, marginTop:64 }}>
        {[["Can't tell an insult from a joke", 6.6], ['So the bully rarely gets caught', 8.4], ["Struggles to report what they can't name", 12.0]].map(([txt, d], i) =>
          <div key={i} style={{ display:'flex', gap:28, alignItems:'baseline', fontFamily:F, fontWeight:600, fontSize:44, letterSpacing:'-0.02em', color:C.head, ...enter(T, PV + d, { out:PV + 15.05 }) }}>
            <span style={{ color:C.accent }}>→</span> {txt}
          </div>)}
      </div>
    </div>

    {/* Meltdown */}
    <div style={{ position:'absolute', left:150, top:320, width:900 }}>
      <div style={{ ...eyebrow, color:C.bad, ...enter(T, MELT + 1.6, { out:NET - 0.4 }) }}>Deliberately triggered</div>
      <h1 style={{ ...h1, fontSize:72, marginTop:26, ...enter(T, MELT + 5.7, { out:NET - 0.4 }) }}>So the victim looks like the problem.</h1>
    </div>

    {/* Network */}
    <div style={{ position:'absolute', left:150, top:270, width:820 }}>
      <div style={{ ...eyebrow, ...enter(T, NET + 2.7, { out:NET + 15.1 }) }}>Every school's fastest screening network</div>
      <div style={{ display:'flex', flexDirection:'column', gap:30, marginTop:56 }}>
        {['Earlier than the doctors', 'Faster than the teachers', 'For free'].map((txt, i) =>
          <div key={i} style={{ display:'flex', gap:28, alignItems:'baseline', fontFamily:F, fontWeight:600, fontSize:44, letterSpacing:'-0.02em', color:C.head, ...enter(T, NET + 7.4 + i * 0.9, { out:NET + 15.1 }) }}>
            <span style={{ color:C.accent }}>→</span> {txt}
          </div>)}
      </div>
      <h1 style={{ ...h1, fontSize:60, color:C.bad, marginTop:56, ...enter(T, NET + 12.3, { out:NET + 15.15 }) }}>Used as a weapon.</h1>
    </div>

    {/* Signal */}
    <div style={{ position:'absolute', left:150, top:300, width:1200 }}>
      <h1 style={{ ...h1, fontSize:78, ...enter(T, SIG + 5.4, { out:SIG + 13.4 }) }}>The signal was visible the whole time.</h1>
      <p style={{ ...lead, fontSize:42, marginTop:34, color:C.muted, ...enter(T, SIG + 7.9, { out:SIG + 13.45 }) }}>The only people paying attention were looking for a target.</p>
    </div>

    {/* Reframe */}
    <div style={{ position:'absolute', left:150, top:340 }}>
      <h1 style={{ ...h1, fontSize:100, ...enter(T, REF + 0.5, { out:REF + 8.5 }) }}>Detection without support</h1>
      <h1 style={{ ...h1, fontSize:100, ...enter(T, REF + 0.8, { out:REF + 8.55 }) }}>is just <span style={{ color:C.bad }}>targeting.</span></h1>
      <div style={{ display:'flex', gap:72, marginTop:70 }}>
        {[['Detection', 'Support'], ['Margin', 'Center']].map((p, i) =>
          <div key={i} style={{ fontFamily:F, fontWeight:600, fontSize:42, letterSpacing:'-0.02em', color:C.body, ...pop(T, REF + 4 + i * 0.3, { out:REF + 8.6 }) }}>
            {p[0]} <span style={{ color:C.accent }}>→</span> <span style={{ color:C.head }}>{p[1]}</span>
          </div>)}
      </div>
    </div>

    {/* Close — the one saturated cut */}
    <div style={{ position:'absolute', inset:0, background:C.accent, transform:`scaleY(${wp})`, transformOrigin:'bottom' }} />
    <div style={{ position:'absolute', left:150, top:300, opacity:wp }}>
      <div style={{ ...eyebrow, color:'rgba(255,255,255,0.75)', ...enter(T, CLOSE + 0.8) }}>The keynote</div>
      <h1 style={{ ...h1, fontSize:128, color:'#FFFFFF', marginTop:28, ...enter(T, CLOSE + 1.1) }}>Not inspiration.</h1>
      <h1 style={{ ...h1, fontSize:128, color:'#FFFFFF', ...enter(T, CLOSE + 1.4) }}>Infrastructure.</h1>
      <div style={{ display:'flex', alignItems:'center', gap:40, marginTop:60, ...pop(T, CLOSE + 3.2) }}>
        <div style={{ fontFamily:F, fontWeight:600, fontSize:30, letterSpacing:'-0.01em', color:C.canvas, background:C.head, padding:'24px 52px', borderRadius:999 }}>Book the keynote →</div>
        <div style={{ ...eyebrow, color:'rgba(255,255,255,0.75)', ...enter(T, CLOSE + 4.0, { rise:10 }) }}>ryanperez.ca</div>
      </div>
    </div>

    <Captions items={CAPS} style={{ font:`400 33px Inter, sans-serif`, color:C.body, bottom:'4.5%', textShadow:'none', lineHeight:1.4 }} />
  </div>;
}

function BulliesFilm() {
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
window.BulliesFilm = BulliesFilm;
