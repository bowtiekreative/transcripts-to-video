  // LAVC Studio renderer — ported from studio/lavc-engine.js renderSceneV2.
  // It keeps the Element Library's motion-first compositions as the output authority.
  function studioHash(value) {
    let hash=2166136261;
    for (const character of String(value)) {
      hash^=character.charCodeAt(0);
      hash=Math.imul(hash,16777619);
    }
    return hash>>>0;
  }

  function studioTrim(value, limit) {
    const tokens=String(value||"").trim().split(/\s+/).filter(Boolean);
    return tokens.length>limit ? `${tokens.slice(0,limit).join(" ")}…` : tokens.join(" ");
  }

  function renderStudioTemplate(scene,p,t) {
    if (scene.layout==="image_overlay") return renderTitle(scene,p);
    if (["audio_wave","matrix"].includes(scene.template)) return renderTemplate(scene,p,t);
    const P=scene.payload||{};
    const items=P.items||P.nodes||P.children||[];
    const seed=studioHash(scene.id);
    const studioPhase=(start,end,easing=easeOut)=>easing(clamp((p-start)/Math.max(.0001,end-start)));
    const micro=(text,delay=0)=>text ? `<div style="opacity:${studioPhase(delay,delay+.2)};font:600 ${px(2.4*U)}/1 ${font};letter-spacing:.14em;text-transform:uppercase;color:${colors.muted};">${esc(text)}</div>` : "";
    const kinetic=(text,delay=.06,size=8,maxWidth=W*.8,color=colors.text)=>{
      const tokens=String(text||"").split(/\s+/).slice(0,12);
      return `<div style="display:flex;flex-wrap:wrap;gap:${px(size*.26*U)} ${px(size*.22*U)};max-width:${px(maxWidth)};">${tokens.map((word,index)=>{
        const q=studioPhase(delay+index*.045,delay+index*.045+.22);
        return `<span style="display:inline-block;opacity:${q};transform:translateY(${px((1-q)*3*U)}) rotate(${((1-q)*2).toFixed(1)}deg);font:600 ${px(size*U)}/1.02 ${font};letter-spacing:-.05em;color:${color};">${esc(word)}</span>`;
      }).join("")}</div>`;
    };
    const dotField=(density=7,dim=.16)=>{
      let dots="";
      const spacing=Math.min(W,H)/density;
      for(let row=0;row<density+2;row++) for(let column=0;column<Math.ceil(W/spacing)+1;column++) {
        const index=row*13+column;
        const offset=(seed%97)/97*Math.PI*2+index*.7;
        const x=column*spacing+Math.sin(t*.5+offset)*U*.9;
        const y=row*spacing+Math.cos(t*.36+offset*1.3)*U*.9;
        const q=studioPhase(.02+((index*37)%20)/100,.3);
        dots+=`<div style="position:absolute;left:${px(x)};top:${px(y)};width:${px(.5*U)};height:${px(.5*U)};border-radius:50%;background:${colors.muted};opacity:${(dim*q).toFixed(2)};"></div>`;
      }
      return dots;
    };
    let body="";

    if (scene.template==="big_number") {
      const percentage=/%/.test(P.number||"");
      const value=parseFloat(String(P.number||0).replace(/[^\d.]/g,""))||0;
      const shown=Math.round(value*studioPhase(.1,.9,easeInOut));
      const cx=landscape?W*.32:W*.5, cy=H*(landscape?.5:.42), size=Math.min(W,H)*.56;
      let ring="";
      if (percentage) {
        const radius=size/2-2*U, q=studioPhase(.1,1,easeInOut), circumference=2*Math.PI*radius;
        ring=`<svg style="position:absolute;left:${px(cx-size/2)};top:${px(cy-size/2)};" width="${size}" height="${size}"><circle cx="${size/2}" cy="${size/2}" r="${radius}" fill="none" stroke="${colors.hairSoft}" stroke-width="${1.1*U}"/><circle cx="${size/2}" cy="${size/2}" r="${radius}" fill="none" stroke="${colors.accent}" stroke-width="${1.1*U}" stroke-linecap="round" stroke-dasharray="${circumference}" stroke-dashoffset="${circumference*(1-clamp(value/100)*q)}" transform="rotate(-90 ${size/2} ${size/2})"/></svg>`;
      }
      body=`${ring}<div style="position:absolute;left:${px(cx)};top:${px(cy)};transform:translate(-50%,-50%);font:600 ${px(15*U)}/.9 ${font};letter-spacing:-.06em;color:${colors.text};">${shown}${percentage?`<span style="font-size:.45em;color:${colors.accent};">%</span>`:""}</div><div style="position:absolute;${landscape?`left:${px(W*.58)};right:${px(edge)};top:50%;transform:translateY(-50%);`:`left:${px(edge)};right:${px(edge)};top:${px(H*.68)};`}display:flex;flex-direction:column;gap:${px(2*U)};">${micro(P.unit||"Measured",.02)}${kinetic(P.label,.5,4.6,landscape?W*.36:W*.85,colors.body)}</div>`;
    } else if (scene.template==="bar_chart") {
      const series=arr(P.series).slice(0,8), max=Math.max(1,...series.map(item=>Number(item.value)||0));
      const chartHeight=H*(landscape?.5:.36), barWidth=Math.min(14*U,(W-edge*2)/(Math.max(1,series.length)*1.8)), gap=barWidth*.8;
      const left=(W-(series.length*barWidth+Math.max(0,series.length-1)*gap))/2, base=H*(landscape?.72:.62);
      const bars=series.map((item,index)=>{
        const q=studioPhase(.2+index*.12,.6+index*.12,easeInOut), height=chartHeight*(Number(item.value)||0)/max*q;
        return `<div style="position:absolute;left:${px(left+index*(barWidth+gap))};top:${px(base-height)};width:${px(barWidth)};height:${px(height)};border-radius:${px(.8*U)} ${px(.8*U)} 0 0;background:${index===0?colors.accent:colors.raised};border:1px solid ${index===0?colors.accent:colors.hair};"></div><div style="position:absolute;left:${px(left+index*(barWidth+gap)-gap/2)};top:${px(base-height-4.6*U)};width:${px(barWidth+gap)};text-align:center;font:600 ${px(3.4*U)}/1 ${font};color:${colors.text};opacity:${q};">${Math.round((Number(item.value)||0)*q)}${esc(item.unit||"")}</div><div style="position:absolute;left:${px(left+index*(barWidth+gap)-gap/2)};top:${px(base+1.6*U)};width:${px(barWidth+gap)};text-align:center;font:600 ${px(2.4*U)}/1.2 ${font};letter-spacing:.08em;text-transform:uppercase;color:${colors.muted};opacity:${q};">${esc(studioTrim(item.label,2))}</div>`;
      }).join("");
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(base)};height:1px;background:${colors.hair};transform:scaleX(${studioPhase(.08,.4,easeInOut)});"></div>${bars}<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.1)};display:flex;flex-direction:column;gap:${px(1.8*U)};">${micro(P.unit==="Share"?"Share":"Data",.02)}${kinetic(P.headline,.06,6.2,W*.8)}</div>`;
    } else if (["before_after","comparison_split","transformation_arrow","cause_effect","problem_solution","condition_cards"].includes(scene.template)) {
      const count=14, leftX=landscape?W*.28:W*.5, leftY=landscape?H*.52:H*.34, rightX=landscape?W*.72:W*.5, rightY=landscape?H*.52:H*.66, radius=Math.min(W,H)*.13;
      const organize=studioPhase(.3,.75,easeInOut);
      let dots="";
      for(let index=0;index<count;index++) {
        const jitter=axis=>((studioHash(`${scene.id}|${index}|${axis}`)%1000)/1000-.5);
        const startX=leftX+jitter(1)*radius*2.4, startY=leftY+jitter(2)*radius*2.4, angle=index/count*Math.PI*2;
        const endX=rightX+Math.cos(angle)*radius, endY=rightY+Math.sin(angle)*radius;
        const x=startX+(endX-startX)*organize, y=startY+(endY-startY)*organize, q=studioPhase(.08+index*.02,.28+index*.02);
        dots+=`<div style="position:absolute;left:${px(x-U*.8)};top:${px(y-U*.8)};width:${px(1.6*U)};height:${px(1.6*U)};border-radius:50%;background:${organize>.6?colors.accent:colors.muted};opacity:${q};"></div>`;
      }
      const arrowQ=studioPhase(.34,.6,easeInOut);
      const arrow=landscape?`<div style="position:absolute;left:${px(leftX+radius*1.4)};top:${px(leftY)};width:${px((rightX-leftX-radius*2.8)*arrowQ)};height:${px(.4*U)};background:${colors.accent};"></div><div style="position:absolute;left:${px(leftX+radius*1.4+(rightX-leftX-radius*2.8)*arrowQ)};top:${px(leftY-2*U)};opacity:${arrowQ};font:600 ${px(4*U)}/1 ${font};color:${colors.accent};">→</div>`:`<div style="position:absolute;left:50%;top:${px(leftY+radius*1.5)};transform:translateX(-50%) rotate(90deg);opacity:${arrowQ};font:600 ${px(4.6*U)}/1 ${font};color:${colors.accent};">→</div>`;
      const labels={before_after:["Before","After"],comparison_split:["A","B"],cause_effect:["Cause","Effect"],problem_solution:["Problem","Response"],condition_cards:["If","Then"]}[scene.template]||["From","To"];
      const tag=(text,label,x,y,q,hot)=>`<div style="position:absolute;left:${px(x)};top:${px(y)};transform:translateX(-50%);text-align:center;opacity:${q};display:flex;flex-direction:column;gap:${px(U)};align-items:center;max-width:${px(landscape?W*.34:W*.8)};"><div style="font:600 ${px(2.4*U)}/1 ${font};letter-spacing:.14em;text-transform:uppercase;color:${hot?colors.accent2:colors.muted};">${esc(label)}</div><div style="font:600 ${px(4.4*U)}/1.18 ${font};letter-spacing:-.03em;color:${colors.text};">${esc(studioTrim(text,6))}</div></div>`;
      body=`${dots}${arrow}${tag(P.left,labels[0],leftX,leftY+radius*1.9,studioPhase(.14,.34),false)}${tag(P.right,labels[1],rightX,rightY+radius*1.9,studioPhase(.55,.8),true)}<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.09)};">${kinetic(P.headline,.04,6.8,W*.84)}</div>`;
    } else if (["list_stack","steps","timeline","funnel"].includes(scene.template)) {
      const values=(P.events&&P.events.length?P.events.map(event=>event.event):items).slice(0,6), ordered=scene.template!=="list_stack";
      const columns=landscape?Math.min(3,Math.max(1,values.length)):1, rows=Math.ceil(values.length/columns), cellWidth=(W-edge*2-(columns-1)*3*U)/columns, cellHeight=Math.min(16*U,(H*.52)/Math.max(1,rows)-2*U);
      const cells=values.map((value,index)=>{
        const q=studioPhase(.18+index*.1,.44+index*.1,easeBack), x=edge+(index%columns)*(cellWidth+3*U), y=H*.34+Math.floor(index/columns)*(cellHeight+2.4*U), glyph=ordered?String(index+1).padStart(2,"0"):"→";
        return `<div style="position:absolute;left:${px(x)};top:${px(y)};width:${px(cellWidth)};height:${px(cellHeight)};display:flex;align-items:center;gap:${px(2.2*U)};padding:0 ${px(2.4*U)};border:1px solid ${colors.hairSoft};border-radius:${px(1.4*U)};background:${colors.surface};opacity:${q};transform:scale(${.88+.12*q}) translateY(${px((1-q)*2*U)});"><div style="font:600 ${px(4.6*U)}/1 ${font};color:${colors.accent};">${glyph}</div><div style="font:600 ${px(3.2*U)}/1.2 ${font};letter-spacing:-.02em;color:${colors.text};">${esc(studioTrim(value,5))}</div></div>`;
      }).join("");
      body=`${cells}<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.1)};display:flex;flex-direction:column;gap:${px(1.8*U)};">${micro(P.label||(ordered?"In order":"Key points"),.02)}${kinetic(P.headline,.06,6.2,W*.84)}</div>`;
    } else if (["network","cycle","hierarchy_tree"].includes(scene.template)) {
      const nodes=items.slice(0,6), cx=landscape?W*.64:W*.5, cy=landscape?H*.52:H*.58, radius=Math.min(W*(landscape?.22:.34),H*.26), centerQ=studioPhase(.06,.28,easeBack), edgeQ=studioPhase(.25,.7,easeInOut);
      let lines="", labels="";
      nodes.forEach((node,index)=>{
        const angle=-Math.PI/2+Math.PI*2*index/Math.max(1,nodes.length)+Math.sin(t*.4+index)*.02, x=cx+Math.cos(angle)*radius, y=cy+Math.sin(angle)*radius, q=studioPhase(.3+index*.07,.5+index*.07,easeBack);
        if (scene.template==="cycle"&&nodes.length>1) { const next=-Math.PI/2+Math.PI*2*((index+1)%nodes.length)/nodes.length; lines+=`<line x1="${x}" y1="${y}" x2="${cx+Math.cos(next)*radius}" y2="${cy+Math.sin(next)*radius}" stroke="${colors.accent}" stroke-width="${.3*U}" opacity="${edgeQ*.7}"/>`; }
        else lines+=`<line x1="${cx}" y1="${cy}" x2="${cx+(x-cx)*edgeQ}" y2="${cy+(y-cy)*edgeQ}" stroke="${colors.hair}" stroke-width="${.28*U}"/>`;
        const pulse=1+.05*Math.sin(t*2+index*1.3), text=typeof node==="object"?node.event:node;
        labels+=`<div style="position:absolute;left:${px(x-2*U)};top:${px(y-2*U)};width:${px(4*U)};height:${px(4*U)};border-radius:50%;background:${colors.accent};opacity:${q};transform:scale(${(.7+.3*q)*pulse});"></div><div style="position:absolute;left:${px(x-9*U)};top:${px(y+3*U)};width:${px(18*U)};text-align:center;opacity:${q};font:600 ${px(2.7*U)}/1.2 ${font};color:${colors.body};">${esc(studioTrim(text,3))}</div>`;
      });
      body=`<svg style="position:absolute;inset:0;" width="${W}" height="${H}">${lines}</svg><div style="position:absolute;left:${px(cx-6.5*U)};top:${px(cy-6.5*U)};width:${px(13*U)};height:${px(13*U)};border-radius:50%;background:${colors.raised};border:${px(.3*U)} solid ${colors.accent};display:grid;place-items:center;text-align:center;padding:${px(U)};opacity:${centerQ};transform:scale(${.75+.25*centerQ});font:600 ${px(2.7*U)}/1.12 ${font};color:${colors.text};">${esc(studioTrim(P.center||P.parent,3))}</div>${labels}<div style="position:absolute;left:${px(edge)};top:${px(H*.1)};width:${px(landscape?W*.38:W*.85)};display:flex;flex-direction:column;gap:${px(1.8*U)};">${micro(P.label||"System",.02)}${kinetic(P.headline,.06,6,landscape?W*.38:W*.8)}</div>`;
    } else if (scene.template==="question_card") {
      const q=studioPhase(.05,.4,easeBack), pulse=1+.04*Math.sin(t*2.2);
      body=`<div style="position:absolute;left:50%;top:${px(H*.36)};transform:translate(-50%,-50%) scale(${q*pulse});width:${px(16*U)};height:${px(16*U)};border-radius:50%;border:${px(.35*U)} solid ${colors.accent};display:grid;place-items:center;font:600 ${px(9*U)}/1 ${font};color:${colors.accent};">?</div><div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.52)};display:flex;justify-content:center;">${kinetic(P.headline||scene.text,.25,landscape?6.4:5.2,W*.78)}</div>`;
    } else if (scene.template==="cta_card") {
      const buttonQ=studioPhase(.45,.72,easeBack), sweep=studioPhase(.02,.5,easeInOut);
      body=`<div style="position:absolute;inset:0;background:${colors.accent};transform:scaleY(${sweep});transform-origin:bottom;opacity:.96;"></div><div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(3*U)};opacity:${sweep};">${kinetic(P.headline,.3,landscape?8.4:6.6,W*.85,"#FFFFFF")}<div style="display:flex;align-items:center;gap:${px(3*U)};margin-top:${px(2*U)};"><div style="opacity:${buttonQ};transform:scale(${.88+.12*buttonQ});padding:${px(2.2*U)} ${px(4.2*U)};border-radius:999px;background:#FFFFFF;font:600 ${px(2.7*U)}/1 ${font};color:#0A0F1E;">${esc(P.action||"Learn more")} →</div>${P.destination?`<div style="opacity:${studioPhase(.62,.82)};font:600 ${px(2.4*U)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.8);">${esc(P.destination)}</div>`:""}</div></div>`;
    } else if (scene.template==="definition_card") {
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(3*U)};">${micro(P.label||"Definition",.02)}${kinetic(P.term||P.headline,.07,7.4,W*.8)}<div style="height:${px(.3*U)};width:${studioPhase(.3,.58,easeInOut)*44}%;background:${colors.accent};"></div><div style="opacity:${studioPhase(.42,.7)};font:400 ${px(3.2*U)}/1.42 ${font};color:${colors.body};max-width:${px(W*.7)};">${esc(studioTrim(P.definition||P.supporting,20))}</div></div>`;
    } else if (scene.template==="warning_card") {
      const q=studioPhase(.05,.35,easeBack), blink=.6+.4*Math.abs(Math.sin(t*2));
      body=`<div style="position:absolute;left:50%;top:${px(H*.32)};transform:translate(-50%,-50%) scale(${q});width:${px(11*U)};height:${px(11*U)};border-radius:50%;border:${px(.35*U)} solid ${colors.danger};display:grid;place-items:center;font:600 ${px(6*U)}/1 ${font};color:${colors.danger};opacity:${blink};">!</div><div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.46)};display:flex;flex-direction:column;align-items:center;gap:${px(2*U)};text-align:center;">${micro(P.label||"Important",.1)}<div style="display:flex;justify-content:center;">${kinetic(P.headline,.2,5.4,W*.78)}</div></div>`;
    } else {
      const quote=scene.template==="quote_focus";
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(2.6*U)};">${quote?`<div style="opacity:${studioPhase(.02,.22)};font:600 ${px(10*U)}/.5 ${font};color:${colors.accent};">“</div>`:micro(P.label||"",.02)}${kinetic(P.headline||scene.text,.1,landscape?8.6:7,W*.84)}</div>`;
    }

    const showDots=["title_card","quote_focus","question_card","big_number","warning_card"].includes(scene.template);
    return `<div style="position:absolute;inset:0;background:${colors.canvas};overflow:hidden;font-family:${font};"><div style="position:absolute;inset:-2%;transform:scale(${1+.016*easeInOut(p)});transform-origin:50% 44%;"><div style="position:absolute;inset:0;background:radial-gradient(circle at 86% 15%,rgba(63,110,233,.14),transparent 32%);"></div>${showDots?dotField():""}${body}</div></div>`;
  }
