/* LAVC browser engine — verbatim port of grammar/{templates,lexicon,motion,defaults}.yml v1.0.0 */
(() => {
"use strict";
const DEFAULTS = { timing:{min_scene_seconds:3.5,target_scene_seconds:7.5,max_scene_seconds:12.0,min_reveal_seconds:0.55,pause_scene_boundary_seconds:0.55,tail_seconds:2.0},
  text:{max_words_on_screen:18,max_items_auto:6,headline_min_words:2,headline_max_words:9,dense_speech_wps:3.2},
  selection:{repeat_window:3,tie_epsilon:0.05,weights:{semantic:35,payload:15,timing:10,density:10,aspect:8,audio:5,continuity:7,variation:5,brand:3,preference:2},
    penalties:{same_previous_template:8,three_in_window:14,weak_pair:12,medium_risk:4,high_risk:10}} };

/* templates.yml — verbatim (data templates included; rejected without data by hard constraint) */
const TEMPLATES = [
  {id:'title_card',relations:{identity:100,emphasis:78,question:55,cta:45},required_any:[['headline']],required_all:[],item_range:[0,8],duration_range:[2,11],density:'sparse',layouts:['vertical_rail','centered','image_overlay'],motion_family:'reveal',semantic_risk:'low',requires_data:false},
  {id:'quote_focus',relations:{emphasis:100,identity:55,warning:45},required_any:[['headline']],required_all:[],item_range:[0,8],duration_range:[3,12],density:'sparse',layouts:['centered','vertical_rail'],motion_family:'reveal',semantic_risk:'low',requires_data:false},
  {id:'big_number',relations:{quantity:100,timeline:35,identity:20},required_any:[],required_all:['number','label'],item_range:[1,1],duration_range:[3,10],density:'sparse',layouts:['centered','number_rail'],motion_family:'reveal',semantic_risk:'low',requires_data:false},
  {id:'list_stack',relations:{list:100,sequence:55,hierarchy:30,network:25},required_any:[['items'],['nodes'],['children']],required_all:[],item_range:[2,6],duration_range:[4,14],density:'low',layouts:['vertical_stack','two_column_grid'],motion_family:'stagger',semantic_risk:'low',requires_data:false},
  {id:'steps',relations:{sequence:100,problem_solution:35},required_any:[['items']],required_all:[],item_range:[2,6],duration_range:[5,16],density:'low',layouts:['vertical_path','horizontal_path'],motion_family:'trace',semantic_risk:'low',requires_data:false},
  {id:'timeline',relations:{timeline:100,sequence:55,contrast:25},required_any:[['events'],['items']],required_all:[],item_range:[2,6],duration_range:[5,18],density:'low',layouts:['vertical_rail','horizontal_axis'],motion_family:'trace',semantic_risk:'low',requires_data:false},
  {id:'before_after',relations:{contrast:100,timeline:72,transformation:82,comparison:55},required_any:[],required_all:['left','right'],item_range:[2,2],duration_range:[4,13],density:'low',layouts:['stacked_split','side_split'],motion_family:'transform',semantic_risk:'low',requires_data:false},
  {id:'comparison_split',relations:{comparison:100,contrast:88,warning:35},required_any:[],required_all:['left','right'],item_range:[2,2],duration_range:[4,14],density:'low',layouts:['stacked_split','side_split'],motion_family:'compare',semantic_risk:'low',requires_data:false},
  {id:'transformation_arrow',relations:{transformation:100,problem_solution:78,cause_effect:60,contrast:50},required_any:[],required_all:['left','right'],item_range:[2,2],duration_range:[4,13],density:'low',layouts:['vertical_bridge','horizontal_bridge'],motion_family:'transform',semantic_risk:'low',requires_data:false},
  {id:'cause_effect',relations:{cause_effect:100,problem_solution:50,sequence:35},required_any:[],required_all:['left','right'],item_range:[2,2],duration_range:[4.5,14],density:'low',layouts:['vertical_bridge','horizontal_bridge'],motion_family:'trace',semantic_risk:'medium',requires_data:false},
  {id:'problem_solution',relations:{problem_solution:100,transformation:68,contrast:50},required_any:[],required_all:['left','right'],item_range:[2,2],duration_range:[5,15],density:'low',layouts:['vertical_bridge','side_split'],motion_family:'transform',semantic_risk:'low',requires_data:false},
  {id:'definition_card',relations:{definition:100,identity:35,emphasis:30},required_any:[],required_all:['term','definition'],item_range:[2,2],duration_range:[4,13],density:'low',layouts:['equation_stack','term_left'],motion_family:'reveal',semantic_risk:'low',requires_data:false},
  {id:'hierarchy_tree',relations:{hierarchy:100,list:35,network:30},required_any:[],required_all:['parent','children'],item_range:[2,7],duration_range:[6,18],density:'medium',layouts:['vertical_tree','horizontal_tree'],motion_family:'trace',semantic_risk:'low',requires_data:false},
  {id:'network',relations:{network:100,hierarchy:42,list:20},required_any:[],required_all:['center','nodes'],item_range:[3,8],duration_range:[6,18],density:'medium',layouts:['radial','offset_hub'],motion_family:'trace',semantic_risk:'low',requires_data:false},
  {id:'cycle',relations:{cycle:100,sequence:40,network:25},required_any:[['items'],['nodes']],required_all:[],item_range:[3,7],duration_range:[6,18],density:'medium',layouts:['radial_cycle'],motion_family:'trace',semantic_risk:'medium',requires_data:false},
  {id:'condition_cards',relations:{conditional:100,sequence:35,cause_effect:30},required_any:[['left','right'],['items']],required_all:[],item_range:[2,4],duration_range:[4.5,16],density:'low',layouts:['vertical_stack','side_split'],motion_family:'stagger',semantic_risk:'low',requires_data:false},
  {id:'question_card',relations:{question:100,problem_solution:20},required_any:[['headline']],required_all:[],item_range:[0,8],duration_range:[3,12],density:'sparse',layouts:['centered','vertical_rail'],motion_family:'reveal',semantic_risk:'low',requires_data:false},
  {id:'cta_card',relations:{cta:100,identity:20},required_any:[['headline'],['action']],required_all:[],item_range:[0,8],duration_range:[4,15],density:'low',layouts:['vertical_rail','centered','qr_split'],motion_family:'reveal',semantic_risk:'low',requires_data:false},
  {id:'warning_card',relations:{warning:100},required_any:[['headline']],required_all:[],item_range:[0,8],duration_range:[3,12],density:'low',layouts:['centered','vertical_rail'],motion_family:'reveal',semantic_risk:'low',requires_data:false},
  {id:'funnel',relations:{sequence:55,quantity:40,problem_solution:25},required_any:[['items']],required_all:[],item_range:[3,7],duration_range:[6,18],density:'medium',layouts:['vertical_funnel','horizontal_funnel'],motion_family:'accumulate',semantic_risk:'medium',requires_data:true},
  {id:'bar_chart',relations:{quantity:90,comparison:60,timeline:35},required_any:[],required_all:['series'],item_range:[2,12],duration_range:[6,20],density:'medium',layouts:['vertical_bars','horizontal_bars'],motion_family:'accumulate',semantic_risk:'medium',requires_data:true},
  {id:'matrix',relations:{comparison:50,hierarchy:25},required_any:[],required_all:['x_axis','y_axis','points'],item_range:[2,20],duration_range:[8,25],density:'high',layouts:['matrix_grid'],motion_family:'stagger',semantic_risk:'high',requires_data:true},
];

/* lexicon.yml — verbatim patterns */
const LEXICON = {
  identity:{w:4,p:["\\bmy name is\\b","\\bi am\\b","\\bi['\u2019]m\\b","\\bintroduc(?:e|ing|tion)\\b","\\bwelcome\\b","^hello\\b"]},
  definition:{w:5,p:["(?<!that )\\bmeans?\\b","\\brefers? to\\b","\\bdefined as\\b","\\bis an?\\b"]},
  list:{w:3,p:["\\bincluding\\b","\\bsuch as\\b","\\bthings like\\b","\\bcovering\\b","\\bfor example\\b","\\bamong them\\b"]},
  sequence:{w:5,p:["(?:^|[.!?]\\s+|,\\s*)first(?:ly)?\\b","(?:^|[.!?]\\s+|,\\s*)second(?:ly)?\\b","(?:^|[.!?]\\s+|,\\s*)third(?:ly)?\\b","\\bnext\\b","\\bthen\\b","\\bfinally\\b","\\bstart(?:s|ed|ing)? with\\b","\\bstep\\b","\\bfollowed by\\b"]},
  timeline:{w:4,p:["\\bbefore\\b","\\bafter\\b","\\byears? ago\\b","\\btoday\\b","\\blater\\b","\\bat (?:age |forty|thirty|twenty|\\d)","\\bwhen\\b","\\bin (?:19|20)\\d{2}\\b"]},
  contrast:{w:5,p:["\\bbut\\b","\\bhowever\\b","\\binstead(?: of)?\\b","\\brather than\\b","\\bwhile\\b","\\byet\\b","\\bnot only\\b","\\bdifferent(?:ly| from)?\\b"]},
  comparison:{w:5,p:["\\bmore than\\b","\\bless than\\b","\\bcompared (?:with|to)\\b","\\bversus\\b","\\bvs\\.?\\b","\\bsimilar to\\b","\\bdifferent from\\b"]},
  transformation:{w:6,p:["\\bfrom .{1,80}\\bto\\b","\\bturn(?:s|ed|ing)? .{1,80}\\binto\\b","\\bconvert(?:s|ed|ing)?\\b","\\bbecome(?:s|ing)?\\b","\\bchanged? into\\b","\\btransform(?:s|ed|ing|ation)?\\b"]},
  cause_effect:{w:5,p:["\\bbecause\\b","\\btherefore\\b","\\bas a result\\b","\\bleads? to\\b","\\bresults? in\\b","\\bcauses?\\b","\\bcreates?\\b","\\bso that\\b"]},
  problem_solution:{w:5,p:["\\bproblem\\b","\\bchallenge\\b","\\bobstacle\\b","\\bissue\\b","\\bpain point\\b","\\bsolve(?:s|d|ing)?\\b","\\bsolution\\b","\\banswer\\b","\\bworkaround\\b","\\buseful to build\\b"]},
  hierarchy:{w:5,p:["\\bpart of\\b","\\bconsists? of\\b","\\bincludes?\\b","\\bcontains?\\b","\\bwithin\\b","\\bunder\\b","\\bcategory\\b"]},
  network:{w:5,p:["\\bconnect(?:s|ed|ing|ion)?\\b","\\btogether\\b","\\blink(?:s|ed|ing)?\\b","\\bnetwork\\b","\\becosystem\\b","\\bsources\\b","\\brelationships?\\b"]},
  cycle:{w:3,p:["\\bcycle\\b","\\bloop\\b","\\brepeat(?:s|ed|ing)?\\b","\\bfeedback\\b","\\bagain\\b","\\bevolve(?:s|d|ing)?\\b","\\bcontinuous(?:ly)?\\b"]},
  quantity:{w:4,p:["\\b\\d+(?:\\.\\d+)?%?\\b","\\$\\s?\\d+","\\bpercent\\b","\\bper cent\\b","\\bmillion\\b","\\bbillion\\b"]},
  question:{w:6,p:["\\?$","\\bthe question\\b","\\b(?:ask|asking|asks)\\s+(?:what|why|how|who|where|when|which)\\b"]},
  cta:{w:6,p:["\\bvisit\\b","\\bbook\\b","\\bdownload\\b","\\bjoin\\b","\\bsubscribe\\b","\\bexplore\\b","\\bcall\\b","\\bbring the problem\\b","\\blet['\u2019]s\\b","\\blearn more\\b"]},
  warning:{w:5,p:["\\bwarning\\b","\\bdanger\\b","\\brisk\\b","\\bavoid\\b","\\bdo not\\b","\\bdon['\u2019]t\\b","\\bmust not\\b"]},
  emphasis:{w:1,p:[]},
  conditional:{w:5,p:["\\bif\\b","\\bunless\\b","\\bwhen\\s+[^,.!?]{1,90},\\s+(?:we|you|it|i|they|the system)\\s+(?:should|can|must|will|need|know|use|change|understand)\\b"]},
};
const SENSITIVE = ["\\bdiagnos(?:is|ed)\\b","\\bautis(?:m|tic)\\b","\\badhd\\b","\\btrauma\\b","\\bdeath\\b","\\bviolence\\b"];

/* style presets */
const BRANDS = {
  dark:{key:'dark',name:'Ryan Perez — Dark',colors:{canvas:'#07090D',surface:'#1A1D24',raised:'#23262F',text:'#F5F7FA',body:'#C5C7CE',muted:'#8A8D96',accent:'#3F6EE9',accent2:'#8AA4FF',danger:'#D8574F',hair:'rgba(255,255,255,0.15)',hairSoft:'rgba(255,255,255,0.08)'},wash:'radial-gradient(circle at 86% 15%,rgba(63,110,233,.14),transparent 32%)'},
  light:{key:'light',name:'Ryan Perez — Light',colors:{canvas:'#EDEFF4',surface:'#FFFFFF',raised:'#F7F8FB',text:'#10131A',body:'#3A3F4C',muted:'#7A7F8C',accent:'#3F6EE9',accent2:'#2D55C4',danger:'#C44840',hair:'rgba(16,19,26,0.16)',hairSoft:'rgba(16,19,26,0.08)'},wash:'radial-gradient(circle at 86% 15%,rgba(63,110,233,.10),transparent 32%)'},
  accent:{key:'accent',name:'Ryan Perez — Accent cut',colors:{canvas:'#101B45',surface:'#1A2857',raised:'#233369',text:'#FFFFFF',body:'#C8D3F5',muted:'#8B9AD1',accent:'#8AA4FF',accent2:'#F5F7FA',danger:'#FF8A80',hair:'rgba(255,255,255,0.2)',hairSoft:'rgba(255,255,255,0.1)'},wash:'radial-gradient(circle at 86% 15%,rgba(138,164,255,.22),transparent 36%)'},
};
const ASPECTS = {'16:9':{w:1920,h:1080},'9:16':{w:1080,h:1920},'1:1':{w:1080,h:1080}};

/* ---------- utilities ---------- */
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const easeOut=p=>1-Math.pow(1-clamp(p),3);
const easeInOut=p=>{p=clamp(p);return p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2;};
const easeBack=p=>{p=clamp(p);const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(p-1,3)+c1*Math.pow(p-1,2);};
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
function hash53(str){let h1=0xdeadbeef,h2=0x41c6ce57;for(let i=0;i<str.length;i++){const ch=str.charCodeAt(i);h1=Math.imul(h1^ch,2654435761);h2=Math.imul(h2^ch,1597334677);}h1=Math.imul(h1^(h1>>>16),2246822507)^Math.imul(h2^(h2>>>13),3266489909);h2=Math.imul(h2^(h2>>>16),2246822507)^Math.imul(h1^(h1>>>13),3266489909);return 4294967296*(2097151&h2)+(h1>>>0);}

/* ---------- SRT ---------- */
function parseTime(s){const m=s.trim().match(/(\d+):(\d+):(\d+)[,.](\d+)/);if(!m)return 0;return(+m[1])*3600+(+m[2])*60+(+m[3])+(+m[4])/1000;}
function parseSRT(text){
  const blocks=text.replace(/\r/g,'').split(/\n\n+/).map(b=>b.trim()).filter(Boolean);
  const cues=[];
  for(const b of blocks){
    const lines=b.split('\n');
    const ti=lines.findIndex(l=>l.includes('-->'));
    if(ti<0)continue;
    const [a,z]=lines[ti].split('-->');
    let txt=lines.slice(ti+1).join(' ').trim();
    const tags={};
    txt=txt.replace(/\[\[LAKA([^\]]*)\]\]/gi,(_,body)=>{
      const re=/(\w+)=("([^"]*)"|\S+)/g;let m;
      while((m=re.exec(body)))tags[m[1]]=m[3]!==undefined?m[3]:m[2];
      return '';
    }).replace(/\s+/g,' ').trim();
    if(txt)cues.push({start:parseTime(a),end:parseTime(z),text:txt,tags:Object.keys(tags).length?tags:null});
  }
  return cues;
}

/* ---------- segmentation: sentence-level scenes within cue timing ---------- */
function segment(cues){
  const t=DEFAULTS.timing,scenes=[];
  for(const cue of cues){
    const sents=cue.text.match(/[^.!?]+[.!?]+(?:["\u201d'])?|[^.!?]+$/g)||[cue.text];
    const total=cue.text.length,dur=cue.end-cue.start;
    let cursor=cue.start,buf=[],bufLen=0;
    const flush=()=>{if(!buf.length)return;const segDur=dur*(bufLen/total);scenes.push({text:buf.join(' ').trim(),start:cursor,end:cursor+segDur,tags:cue.tags});cursor+=segDur;buf=[];bufLen=0;};
    for(const s of sents){
      const sDur=dur*(s.length/total);
      const bufDur=dur*(bufLen/total);
      if(bufLen&&(bufDur+sDur>t.max_scene_seconds||bufDur>=t.target_scene_seconds))flush();
      buf.push(s.trim());bufLen+=s.length;
    }
    flush();
  }
  /* merge scenes shorter than min into the previous */
  const merged=[];
  for(const s of scenes){
    const prev=merged[merged.length-1];
    if(prev&&(s.end-s.start)<t.min_scene_seconds&&(s.end-prev.start)<=t.max_scene_seconds+2){prev.text+=' '+s.text;prev.end=s.end;prev.tags=prev.tags||s.tags;}
    else merged.push({...s});
  }
  return merged.map((s,i)=>({...s,id:'scene-'+String(i+1).padStart(2,'0'),index:i,duration:s.end-s.start}));
}

/* ---------- classification ---------- */
function classify(text){
  const low=text.toLowerCase(),scores={};
  for(const[rel,def]of Object.entries(LEXICON)){
    let sc=0;
    for(const p of def.p){try{const re=new RegExp(p,'gim');const m=low.match(re);if(m)sc+=def.w*Math.min(m.length,3);}catch(e){}}
    scores[rel]=sc;
  }
  if(/\?\s*$/.test(text.trim()))scores.question+=4;
  if(/:/.test(text))scores.list+=1.5;
  if((text.match(/,/g)||[]).length>=3)scores.list+=3;
  if(/\d/.test(text))scores.quantity+=3;
  if(/\bnot\b.*\b(?:but|a|an)\b/i.test(text))scores.contrast+=2;
  scores.emphasis=Math.max(scores.emphasis,1);
  const sensitive=SENSITIVE.some(p=>new RegExp(p,'i').test(low));
  const max=Math.max(...Object.values(scores),0.001);
  const norm={};for(const k in scores)norm[k]=scores[k]/max;
  const ranked=Object.entries(scores).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]);
  return{scores,norm,ranked,sensitive};
}

/* ---------- payload extraction ---------- */
const STOP=new Set('a an and are as at be been but by for from had has have he her here him his i if in into is it its me my of on or our she so that the their them there these they this those through to was we were what when where which who why will with you your'.split(' '));
function trimWords(s,n){const w=String(s).trim().replace(/[.!?]+$/,'').split(/\s+/);return w.length<=n?w.join(' '):w.slice(0,n).join(' ')+'\u2026';}
function extractPayload(text,cls,tags){
  const P={};
  const sents=text.match(/[^.!?]+[.!?]*/g)||[text];
  P.headline=trimWords(sents[0],DEFAULTS.text.headline_max_words);
  if(sents.length>1)P.supporting=sents.slice(1).join(' ').trim();
  /* number */
  const num=text.match(/(\$?\d+(?:[,.]\d+)?\s?(?:%|percent|million|billion)?)/i);
  if(num){P.number=num[1].replace(/\s?percent/i,'%').replace(/,(?=\d{3}\b)/g,',');
    const after=text.slice(text.indexOf(num[1])+num[1].length).replace(/^[%\s]*(?:percent)?\s*(?:of)?\s*/i,'');
    P.label=trimWords(after||sents[0],8);P.unit=/%|percent/i.test(num[0])?'Share':/\$/.test(num[0])?'Value':'Measured';}
  /* numeric series: 2+ quantified values with local context → truthful chart data */
  {const nre=/(\$?\d+(?:[,.]\d+)?)\s?(%|percent|million|billion)?/gi;let m;const found=[];
   while((m=nre.exec(text))){const v=parseFloat(m[1].replace(/[$,]/g,''));if(isNaN(v))continue;
     const pre=text.slice(Math.max(0,m.index-60),m.index).split(/[,.;:\u2014]/).pop().trim();
     const post=text.slice(m.index+m[0].length,m.index+m[0].length+60).split(/[,.;:\u2014]/)[0].trim();
     const ctx=(post.replace(/^of\s+/i,'')||pre);
     found.push({label:trimWords(ctx,4)||('Value '+(found.length+1)),value:v,unit:m[2]?(/%|percent/i.test(m[2])?'%':' '+m[2]):''});}
   const uniq=found.filter((f,i)=>f.value>0&&found.findIndex(g=>g.value===f.value&&g.label===f.label)===i);
   if(uniq.length>=2&&uniq.length<=8)P.series=uniq;}
  /* items: comma/and series of 3+ */
  const seriesSrc=sents.find(s=>(s.match(/,/g)||[]).length>=2)||text;
  const rawItems=seriesSrc.split(/,|\band\b|;|\u2014/).map(s=>s.trim()).filter(s=>s&&s.split(/\s+/).length<=7&&s.split(/\s+/).some(w=>!STOP.has(w.toLowerCase())));
  if(rawItems.length>=3)P.items=rawItems.slice(0,DEFAULTS.text.max_items_auto).map(s=>trimWords(s,6));
  /* pairs */
  const pairSplits=[/\bfrom\s+(.{3,80}?)\s+to\s+(.{3,120})/i,/(.{6,140}?)\s*[,;\u2014]\s*but\s+(.{6,140})/i,/(.{6,140}?)\s+but\s+(.{6,140})/i,/(.{6,140}?)\s+(?:leads? to|results? in|becomes?|turn(?:s|ed)? into)\s+(.{4,140})/i,/(.{6,140}?)\s+instead of\s+(.{4,140})/i,/if\s+(.{4,120}?),\s*(?:then\s+)?(.{4,140})/i,/because\s+(.{4,120}?),\s*(.{4,140})/i];
  for(const re of pairSplits){const m=text.match(re);if(m){P.left=trimWords(m[1],10);P.right=trimWords(m[2],10);break;}}
  /* definition */
  const def=text.match(/^(.{2,60}?)\s+(?:is|are|means?|refers to)\s+(.{6,200})/i);
  if(def&&cls.scores.definition>0){P.term=trimWords(def[1],6);P.definition=trimWords(def[2],22);}
  /* hierarchy / network */
  if(P.items){P.children=P.items;P.parent=P.headline;P.nodes=P.items;P.center=trimWords(P.headline,4);
    if(cls.scores.timeline>0)P.events=P.items.map((e,i)=>({time:String(i+1).padStart(2,'0'),event:e}));}
  /* cta */
  const url=text.match(/\b[\w-]+\.(?:com|ca|org|net|io)\b/i);if(url)P.destination=url[0];
  const act=text.match(/\b(visit|book|download|join|subscribe|explore|call|learn more)\b[^,.!?]{0,40}/i);
  if(act)P.action=trimWords(act[0],6);
  /* author tags override everything */
  if(tags){for(const[k,v]of Object.entries(tags)){
    if(k==='items'||k==='nodes'||k==='children')P[k]=String(v).split('|').map(s=>s.trim());
    else if(k==='data')P.series=String(v).split('|').map(s=>{const[l,val]=s.split(':');return{label:(l||'').trim(),value:parseFloat(val)||0,unit:''};});
    else if(k!=='relation'&&k!=='infographic'&&k!=='motion')P[k]=v;}}
  return P;
}

/* ---------- selection ---------- */
function hardConstraints(tpl,scene,P,aspect){
  const reasons=[];
  if(tpl.requires_data&&!(P.series||P.points))reasons.push('requires_data');
  if(tpl.id==='funnel'&&!P.series)reasons.push('requires_data');
  for(const f of tpl.required_all)if(P[f]==null)reasons.push('missing:'+f);
  if(tpl.required_any.length&&!tpl.required_any.some(g=>g.every(f=>P[f]!=null)))reasons.push('required_any');
  const n=Math.max((P.items||P.nodes||P.children||[]).length,(P.series||[]).length,(P.points||[]).length)||((P.left&&P.right)?2:(P.number?1:0));
  if(tpl.item_range[0]>0&&n<tpl.item_range[0])reasons.push('too_few_items');
  const[dMin,dMax]=tpl.duration_range;
  if(scene.duration<dMin*0.55||scene.duration>dMax*1.6)reasons.push('duration');
  return reasons;
}
function scoreCandidate(tpl,layout,scene,cls,P,history,cfg){
  const W=DEFAULTS.selection.weights,PEN=DEFAULTS.selection.penalties;
  const pos={},pen={};
  let best=0,second=0;
  for(const[rel,w]of Object.entries(tpl.relations)){const v=(cls.norm[rel]||0)*(w/100);if(v>best){second=best;best=v;}else if(v>second)second=v;}
  pos.semantic=+(W.semantic*(best+0.15*second)).toFixed(1);
  let pf=0.5;const n=(P.items||[]).length;
  if(tpl.required_all.every(f=>P[f]!=null))pf+=0.2;
  if(n>=tpl.item_range[0]&&n<=tpl.item_range[1])pf+=0.15;
  if(scene.tags)pf+=0.15;
  pos.payload=+(W.payload*clamp(pf)).toFixed(1);
  const[dMin,dMax]=tpl.duration_range,mid=(dMin+dMax)/2;
  pos.timing=+(W.timing*clamp(1-Math.abs(scene.duration-mid)/(dMax-dMin))).toFixed(1);
  const words=scene.text.split(/\s+/).length;
  const cap={sparse:14,low:26,medium:40,high:60}[tpl.density]||26;
  pos.density=+(W.density*clamp(1-Math.max(0,words-cap)/cap)).toFixed(1);
  pos.aspect=+(W.aspect*(layout===tpl.layouts[0]?1:0.8)).toFixed(1);
  pos.audio=+(W.audio*0.6).toFixed(1);
  const prevKey=history.topics[history.topics.length-1];
  pos.continuity=+(W.continuity*(prevKey&&cls.ranked[0]&&prevKey===cls.ranked[0][0]?0.8:0.4)).toFixed(1);
  pos.variation=+(W.variation*(history.templates.slice(-DEFAULTS.selection.repeat_window).includes(tpl.id)?0:1)).toFixed(1);
  pos.brand=W.brand;
  pos.preference=(scene.tags&&scene.tags.infographic===tpl.id)?W.preference*10:0;
  if(history.templates[history.templates.length-1]===tpl.id)pen.same_previous=PEN.same_previous_template;
  if(history.templates.slice(-DEFAULTS.selection.repeat_window).filter(t=>t===tpl.id).length>=2)pen.three_in_window=PEN.three_in_window;
  if(tpl.required_all.includes('left')&&!scene.tags&&P.left&&(P.left.split(/\s+/).length<2||P.right.split(/\s+/).length<2))pen.weak_pair=PEN.weak_pair;
  if(tpl.semantic_risk==='medium')pen.risk=PEN.medium_risk;
  if(tpl.semantic_risk==='high')pen.risk=PEN.high_risk;
  /* seeded variation: bounded deterministic jitter (LAVC seeded-variation mode) */
  const jitter=+((hash53(cfg.seed+'|'+scene.id+'|'+tpl.id)%1000)/1000*3.5).toFixed(2);
  pos.seed_jitter=jitter;
  const total=Object.values(pos).reduce((a,b)=>a+b,0)-Object.values(pen).reduce((a,b)=>a+b,0);
  return{template:tpl.id,layout,motion:tpl.motion_family,score:+total.toFixed(1),positive:pos,penalties:pen};
}
function selectScene(scene,history,cfg){
  const cls=classify(scene.text);
  if(scene.tags&&scene.tags.relation)cls.norm[scene.tags.relation]=1.2;
  const P=extractPayload(scene.text,cls,scene.tags);
  const cands=[],rejected=[];
  for(const tpl of TEMPLATES){
    const hc=hardConstraints(tpl,scene,P,cfg.aspect);
    if(hc.length){rejected.push({template:tpl.id,reasons:hc});continue;}
    for(const layout of tpl.layouts)cands.push(scoreCandidate(tpl,layout,scene,cls,P,history,cfg));
  }
  cands.sort((a,b)=>b.score-a.score||(hash53(cfg.seed+'|'+scene.id+'|'+a.template+'|'+a.layout)-hash53(cfg.seed+'|'+scene.id+'|'+b.template+'|'+b.layout)));
  const sel=cands[0]||{template:'title_card',layout:'vertical_rail',motion:'reveal',score:0,positive:{},penalties:{}};
  return{...scene,primary_relation:(cls.ranked[0]||['emphasis'])[0],sensitive:cls.sensitive,payload:P,template:sel.template,layout:sel.layout,motion:sel.motion,score:sel.score,trace:{candidates:cands.slice(0,5),rejected_count:rejected.length,selected:sel.template}};
}
function compile(cues,cfg,locks){
  const scenes=segment(cues);
  const history={templates:[],topics:[]};
  const out=[];
  for(const sc of scenes){
    let sel;
    if(locks&&locks[sc.index]){sel={...sc,...locks[sc.index]};}
    else sel=selectScene(sc,history,cfg);
    history.templates.push(sel.template);
    history.topics.push(sel.primary_relation);
    out.push(sel);
  }
  const total=+(out.reduce((a,s)=>a+(s.score||0),0)/Math.max(1,out.length)).toFixed(1);
  return{config:cfg,scenes:out,duration:out.length?out[out.length-1].end+DEFAULTS.timing.tail_seconds:0,meanScore:total};
}
function generateVersions(srtText,baseSeed){
  const cues=parseSRT(srtText);
  if(!cues.length)return{cues,versions:[]};
  const axes=[
    {seed:baseSeed,aspect:'16:9',brand:'dark',note:'Baseline'},
    {seed:baseSeed+1,aspect:'16:9',brand:'dark',note:'Alternate seed'},
    {seed:baseSeed+2,aspect:'16:9',brand:'dark',note:'Alternate seed B'},
    {seed:baseSeed,aspect:'9:16',brand:'dark',note:'Vertical / social'},
    {seed:baseSeed,aspect:'1:1',brand:'dark',note:'Square / feed'},
    {seed:baseSeed,aspect:'16:9',brand:'light',note:'Light mode'},
    {seed:baseSeed,aspect:'16:9',brand:'accent',note:'Accent cut'},
    {seed:baseSeed+3,aspect:'9:16',brand:'light',note:'Vertical light, alt seed'},
  ];
  const versions=axes.map((cfg,i)=>({id:'v'+(i+1),...compile(cues,cfg,null)}));
  versions.sort((a,b)=>b.meanScore-a.meanScore);
  return{cues,versions};
}
function recompile(srtText,version,locks){
  const cues=parseSRT(srtText);
  const cfg={...version.config,seed:version.config.seed+7};
  const lockMap={};
  (version.scenes||[]).forEach(s=>{if(locks.has(s.index))lockMap[s.index]={primary_relation:s.primary_relation,sensitive:s.sensitive,payload:s.payload,template:s.template,layout:s.layout,motion:s.motion,score:s.score,trace:s.trace,locked:true};});
  return{id:version.id,...compile(cues,cfg,lockMap)};
}

/* ---------- renderer (port of player.html.j2 render functions, RP-tuned) ---------- */
function renderScene(scene,p,brandKey,aspect,t){
  const B=BRANDS[brandKey]||BRANDS.dark,c=B.colors;
  const {w:W,h:H}=ASPECTS[aspect]||ASPECTS['16:9'];
  const U=Math.min(W,H)/108,edge=W*0.075,font="'Inter',sans-serif";
  const px=n=>`${Math.round(n*100)/100}px`;
  const phase=(pp,s,e,ez=easeOut)=>ez(clamp((pp-s)/Math.max(.0001,e-s)));
  const es=(pp,delay=0,span=.22,pop=false)=>{
    const q=pop?easeBack(clamp((pp-delay)/span)):phase(pp,delay,delay+span);
    const op=clamp(q*1.35)*(1-phase(pp,.94,1));
    return`opacity:${op};transform:translateY(${px(2.2*U*(1-q))}) scale(${pop?(.85+.15*q):1});`;
  };
  const label=(txt,delay=0)=>txt?`<div style="${es(p,delay,.18)}font:600 ${px(1.9*U)}/1 ${font};letter-spacing:.13em;text-transform:uppercase;color:${c.muted};">${esc(txt)}</div>`:'';
  const headline=(txt,delay=.06,size=8.6)=>`<div style="${es(p,delay,.25)}font:600 ${px(size*U)}/1.05 ${font};letter-spacing:-.05em;color:${c.text};overflow-wrap:anywhere;">${esc(txt||'')}</div>`;
  const P=scene.payload||{};
  const wide=W>H;
  const col=`position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*(wide?0.22:0.16))};display:flex;flex-direction:column;gap:${px(2.6*U)};`;
  const card=(inner,extra='')=>`<div style="padding:${px(2.6*U)} ${px(3*U)};border:1px solid ${c.hairSoft};border-radius:${px(1.6*U)};background:${c.surface};${extra}">${inner}</div>`;
  let body='';
  const items=P.items||P.nodes||P.children||[];
  switch(scene.template){
    case 'big_number':{
      const q=phase(p,.08,.48,easeBack);
      body=`<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${px(2.4*U)};text-align:center;padding:${px(edge)};">
        ${label(P.unit||'Measured')}
        <div style="opacity:${clamp(p*4)};transform:scale(${.75+.25*q});font:600 ${px(22*U)}/0.9 ${font};letter-spacing:-.06em;color:${c.text};">${esc(P.number||'')}</div>
        <div style="${es(p,.34,.22)}font:600 ${px(3.6*U)}/1.25 ${font};letter-spacing:-.02em;color:${c.body};max-width:${px(W*.72)};">${esc(P.label||'')}</div></div>`;break;}
    case 'list_stack':case 'condition_cards':{
      if((scene.template==='condition_cards')&&P.left&&P.right){body=null;}
      else{const rows=items.slice(0,6).map((it,i)=>{const q=phase(p,.16+i*.09,.38+i*.09);
        return`<div style="opacity:${q};transform:translateY(${px((1-q)*2*U)});display:flex;gap:${px(2*U)};align-items:baseline;font:600 ${px(3.1*U)}/1.25 ${font};letter-spacing:-.02em;color:${c.text};padding:${px(1.8*U)} 0;border-bottom:1px solid ${c.hairSoft};"><span style="color:${c.accent};">\u2192</span><span>${esc(it)}</span></div>`;}).join('');
      body=`<div style="${col}">${label(P.label||'Key points')}${headline(P.headline,0.05,5.8)}<div style="display:flex;flex-direction:column;margin-top:${px(U)};">${rows}</div></div>`;}
      if(body)break;/* else fall through to pair */}
    case 'before_after':case 'comparison_split':case 'transformation_arrow':case 'cause_effect':case 'problem_solution':{
      const lbl={before_after:['Before','After'],comparison_split:['A','B'],cause_effect:['Cause','Effect'],problem_solution:['Problem','Response'],condition_cards:['Condition','Response']}[scene.template]||['From','To'];
      const lq=phase(p,.12,.34),cq=phase(p,.38,.6,easeInOut),rq=phase(p,.52,.76,easeBack);
      const half=(W-edge*2-14*U)/2;
      const pane=(t2,txt,q,hot)=>`<div style="width:${px(wide?half:W-edge*2)};padding:${px(2.6*U)} ${px(3*U)};border-radius:${px(1.6*U)};background:${hot?c.raised:c.surface};border:1px solid ${hot?c.accent:c.hairSoft};opacity:${q};transform:translateY(${px((1-q)*2.4*U)});">
        <div style="font:600 ${px(1.6*U)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:${hot?c.accent2:c.muted};">${esc(t2)}</div>
        <div style="margin-top:${px(1.6*U)};font:600 ${px(3.4*U)}/1.2 ${font};letter-spacing:-.03em;color:${c.text};">${esc(txt||'')}</div></div>`;
      body=`<div style="${col}">${label(P.label||scene.primary_relation.replace(/_/g,' '))}${headline(P.headline,0.05,5.4)}
        <div style="display:flex;flex-direction:${wide?'row':'column'};align-items:${wide?'center':'stretch'};gap:${px(2.2*U)};margin-top:${px(2*U)};">
          ${pane(lbl[0],P.left,lq,false)}
          <div style="opacity:${cq};font:600 ${px(5*U)}/1 ${font};color:${c.accent};text-align:center;${wide?'':`transform:rotate(90deg);width:${px(5*U)};margin:0 auto;`}">\u2192</div>
          ${pane(lbl[1],P.right,rq,true)}
        </div></div>`;break;}
    case 'steps':case 'timeline':{
      const evs=(P.events&&P.events.length?P.events:items.map((e,i)=>({time:String(i+1).padStart(2,'0'),event:e}))).slice(0,6);
      const lineQ=phase(p,.13,.7,easeInOut);
      const rows=evs.map((ev,i)=>{const at=.18+i*(.5/Math.max(1,evs.length-1));const q=phase(p,at,at+.18,easeBack);
        return`<div style="display:flex;gap:${px(2.6*U)};align-items:baseline;opacity:${q};transform:translateY(${px((1-q)*1.6*U)});padding:${px(1.7*U)} 0;">
          <div style="font:600 ${px(1.8*U)}/1 ${font};letter-spacing:.1em;color:${c.accent2};min-width:${px(6*U)};">${esc(ev.time||'')}</div>
          <div style="font:600 ${px(3*U)}/1.25 ${font};letter-spacing:-.02em;color:${c.text};">${esc(ev.event||ev)}</div></div>`;}).join('');
      body=`<div style="${col}">${label(P.label||(scene.template==='steps'?'Process':'Timeline'))}${headline(P.headline,0.05,5.6)}
        <div style="position:relative;padding-left:${px(3*U)};margin-top:${px(1.5*U)};">
          <div style="position:absolute;left:0;top:${px(U)};width:${px(.34*U)};height:${lineQ*100}%;background:${c.accent};border-radius:999px;"></div>${rows}</div></div>`;break;}
    case 'definition_card':{
      const line=phase(p,.3,.58,easeInOut);
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(3.2*U)};">
        ${label(P.label||'Definition')}
        <div style="${es(p,.07,.24)}font:600 ${px(8*U)}/1.02 ${font};letter-spacing:-.05em;color:${c.text};">${esc(P.term||P.headline||'')}</div>
        <div style="height:${px(.3*U)};width:${line*44}%;background:${c.accent};"></div>
        <div style="${es(p,.42,.28)}font:400 ${px(3.4*U)}/1.42 ${font};color:${c.body};max-width:${px(W*.72)};">${esc(P.definition||P.supporting||'')}</div></div>`;break;}
    case 'network':case 'cycle':case 'hierarchy_tree':{
      const nodes=items.slice(0,6);
      const cx=wide?W*0.68:W/2,cy=wide?H*0.52:H*0.56,radius=Math.min(W*(wide?0.2:0.32),H*0.24);
      const cQ=phase(p,.06,.28,easeBack),eQ=phase(p,.25,.7,easeInOut);
      let svg='',lbls='';
      nodes.forEach((nd,i)=>{const ang=-Math.PI/2+Math.PI*2*i/Math.max(1,nodes.length);
        const x=cx+Math.cos(ang)*radius,y=cy+Math.sin(ang)*radius;
        const q=phase(p,.3+i*.06,.5+i*.06,easeBack);
        if(scene.template==='cycle'&&nodes.length>1){const na=-Math.PI/2+Math.PI*2*((i+1)%nodes.length)/nodes.length;
          svg+=`<line x1="${x}" y1="${y}" x2="${cx+Math.cos(na)*radius}" y2="${cy+Math.sin(na)*radius}" stroke="${c.hair}" stroke-width="${.28*U}" opacity="${eQ}"/>`;}
        else svg+=`<line x1="${cx}" y1="${cy}" x2="${cx+(x-cx)*eQ}" y2="${cy+(y-cy)*eQ}" stroke="${c.hair}" stroke-width="${.26*U}"/>`;
        lbls+=`<div style="position:absolute;left:${px(x-9*U)};top:${px(y-3.4*U)};width:${px(18*U)};padding:${px(1.2*U)};display:grid;place-items:center;text-align:center;border:1px solid ${c.hairSoft};border-radius:${px(1.2*U)};background:${c.surface};opacity:${q};transform:scale(${.75+.25*q});font:600 ${px(1.9*U)}/1.2 ${font};color:${c.text};">${esc(typeof nd==='object'?nd.event:nd)}</div>`;});
      body=`<div style="position:absolute;left:${px(edge)};top:${px(H*0.14)};width:${px(wide?W*0.34:W-edge*2)};display:flex;flex-direction:column;gap:${px(2.4*U)};">${label(P.label||'Connected system')}${headline(P.headline,0.05,5.2)}</div>
        <svg style="position:absolute;inset:0;" width="${W}" height="${H}">${svg}</svg>
        <div style="position:absolute;left:${px(cx-8*U)};top:${px(cy-3.6*U)};width:${px(16*U)};padding:${px(1.6*U)};display:grid;place-items:center;text-align:center;border-radius:999px;background:${c.raised};border:1px solid ${c.accent};opacity:${cQ};transform:scale(${.75+.25*cQ});font:600 ${px(2*U)}/1.15 ${font};color:${c.text};">${esc(P.center||P.parent||'')}</div>${lbls}`;break;}
    case 'bar_chart':{
      const series=(P.series||[]).slice(0,8);
      const max=Math.max(1,...series.map(x=>x.value));
      const rows=series.map((it,i)=>{const q=phase(p,.18+i*.09,.5+i*.09);
        return`<div style="display:flex;align-items:center;gap:${px(2.4*U)};">
          <div style="width:${px(wide?26*U:20*U)};font:600 ${px(2*U)}/1.2 ${font};color:${c.body};text-align:right;overflow:hidden;">${esc(it.label)}</div>
          <div style="flex:1;height:${px(2.4*U)};background:${c.hairSoft};border-radius:${px(.5*U)};overflow:hidden;"><div style="width:${(it.value/max*100*q).toFixed(1)}%;height:100%;background:${i===0?c.accent:c.muted};"></div></div>
          <div style="min-width:${px(9*U)};font:600 ${px(2.6*U)}/1 ${font};letter-spacing:-.02em;color:${c.text};opacity:${q};">${esc(Math.round(it.value*10)/10)}${esc(it.unit||'')}</div></div>`;}).join('');
      body=`<div style="${col}">${label(P.unit==='Share'?'Share':'Data')}${headline(P.headline,0.05,5.4)}
        <div style="display:flex;flex-direction:column;gap:${px(2*U)};margin-top:${px(2*U)};">${rows}</div></div>`;break;}
    case 'funnel':{
      const fitems=(P.series||[]).map(s=>s.label+(s.unit?` — ${s.value}${s.unit}`:` — ${s.value}`)).length?(P.series||[]).map(s=>`${s.label} — ${s.value}${s.unit||''}`):items;
      const rows=fitems.slice(0,7).map((it,i,arr)=>{const q=phase(p,.16+i*.08,.42+i*.08);const wdt=100-i*10;
        return`<div style="width:${wdt}%;margin:0 auto;padding:${px(1.8*U)} ${px(2.4*U)};clip-path:polygon(3% 0,97% 0,93% 100%,7% 100%);background:${i===arr.length-1?c.accent:c.surface};border:1px solid ${c.hairSoft};opacity:${q};transform:scaleX(${.75+.25*q});text-align:center;font:600 ${px(2.4*U)}/1.2 ${font};color:${i===arr.length-1?'#fff':c.text};">${esc(it)}</div>`;}).join('');
      body=`<div style="${col}">${label(P.label||'Stages')}${headline(P.headline,0.05,5.4)}
        <div style="display:flex;flex-direction:column;gap:${px(1.2*U)};margin-top:${px(2*U)};">${rows}</div></div>`;break;}
    case 'matrix':{
      const pts=(P.points||[]).slice(0,20),xA=P.x_axis||['Low','High'],yA=P.y_axis||['Low','High'];
      const gL=edge+6*U,gR=W-edge-2*U,gT=H*.34,gB=H*.82;
      const dots=pts.map((pt,i)=>{const q=phase(p,.25+i*.03,.48+i*.03,easeBack);
        const x=gL+clamp(Number(pt.x))*(gR-gL),y=gB-clamp(Number(pt.y))*(gB-gT);
        return`<div style="position:absolute;left:${px(x-2*U)};top:${px(y-2*U)};width:${px(4*U)};height:${px(4*U)};border-radius:50%;background:${c.accent};opacity:${q};transform:scale(${.6+.4*q});display:grid;place-items:center;font:600 ${px(1.3*U)}/1 ${font};color:#fff;">${esc(pt.label||i+1)}</div>`;}).join('');
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*0.12)};display:flex;flex-direction:column;gap:${px(2*U)};">${label(P.label||'Matrix')}${headline(P.headline,0.05,5)}</div>
        <div style="position:absolute;left:${px(gL)};top:${px(gT)};width:${px(gR-gL)};height:${px(gB-gT)};border-left:1px solid ${c.hair};border-bottom:1px solid ${c.hair};background:linear-gradient(${c.hairSoft} 1px,transparent 1px),linear-gradient(90deg,${c.hairSoft} 1px,transparent 1px);background-size:25% 25%;"></div>
        <div style="position:absolute;left:${px(gL)};top:${px(gB+1.4*U)};font:600 ${px(1.6*U)}/1 ${font};letter-spacing:.1em;text-transform:uppercase;color:${c.muted};">${esc(xA[0])}</div>
        <div style="position:absolute;right:${px(edge)};top:${px(gB+1.4*U)};font:600 ${px(1.6*U)}/1 ${font};letter-spacing:.1em;text-transform:uppercase;color:${c.muted};">${esc(xA[1]||'High')}</div>
        <div style="position:absolute;left:${px(edge)};top:${px(gT)};font:600 ${px(1.6*U)}/1 ${font};letter-spacing:.1em;text-transform:uppercase;color:${c.muted};">${esc(yA[1]||'High')}</div>${dots}`;break;}
    case 'question_card':{
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(3*U)};">
        <div style="${es(p,.02,.2)}font:600 ${px(12*U)}/1 ${font};color:${c.accent};">?</div>
        ${headline(P.headline||scene.text,0.1,8.2)}</div>`;break;}
    case 'warning_card':{
      const q=phase(p,.05,.35,easeBack);
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:50%;transform:translateY(-50%) scale(${.92+.08*q});opacity:${q};padding:${px(4*U)};border:1px solid ${c.danger};border-radius:${px(2.2*U)};background:${c.surface};display:flex;flex-direction:column;gap:${px(2.2*U)};">
        <div style="font:600 ${px(1.8*U)}/1 ${font};letter-spacing:.13em;text-transform:uppercase;color:${c.danger};">${esc(P.label||'Important')}</div>${headline(P.headline,0.12,6.4)}</div>`;break;}
    case 'cta_card':{
      const bq=phase(p,.45,.72,easeBack);
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:${px(3*U)};">
        ${label(P.label||'Next step')}${headline(P.headline,0.07,7.2)}
        <div style="opacity:${bq};transform:scale(${.88+.12*bq});margin-top:${px(1.5*U)};padding:${px(2.2*U)} ${px(4.2*U)};border-radius:999px;background:${c.text};font:600 ${px(2.7*U)}/1 ${font};letter-spacing:-.01em;color:${c.canvas};">${esc(P.action||'Learn more')} \u2192</div>
        ${P.destination?`<div style="${es(p,.62,.2)}font:600 ${px(2*U)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:${c.accent2};">${esc(P.destination)}</div>`:''}</div>`;break;}
    case 'quote_focus':{
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(2.8*U)};">
        <div style="${es(p,.02,.2)}font:600 ${px(9*U)}/0.6 ${font};color:${c.accent};">\u201c</div>
        ${headline(P.headline||scene.text,0.08,7)}
        ${label(P.label||'',0.4)}</div>`;break;}
    default:{/* title_card */
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(2.8*U)};">
        ${label(P.label||'')}
        ${headline(P.headline||scene.text,0.08,wide?9.4:8.4)}
        ${P.supporting&&P.supporting!==P.headline?`<div style="${es(p,.34,.24)}font:400 ${px(3*U)}/1.42 ${font};color:${c.muted};max-width:${px(W*.66)};">${esc(trimWords(P.supporting,24))}</div>`:''}</div>`;}
  }
  const drift=1+0.014*easeInOut(p);
  return`<div style="position:absolute;inset:0;background:${c.canvas};overflow:hidden;font-family:${font};">
    <div style="position:absolute;inset:-2%;transform:scale(${drift});transform-origin:50% 44%;">
      <div style="position:absolute;inset:0;background:${B.wash};"></div>${body}</div></div>`;
}

/* ---------- motion-first renderer v2: the graphic IS the scene; text is secondary ---------- */
function renderSceneV2(scene,p,brandKey,aspect,t){
  const B=BRANDS[brandKey]||BRANDS.dark,c=B.colors;
  const {w:W,h:H}=ASPECTS[aspect]||ASPECTS['16:9'];
  const U=Math.min(W,H)/108,edge=W*0.075,font="'Inter',sans-serif";
  const px=n=>`${Math.round(n*100)/100}px`;
  const phase=(pp,s,e,ez=easeOut)=>ez(clamp((pp-s)/Math.max(.0001,e-s)));
  const P=scene.payload||{},wide=W>H,seedN=hash53(scene.id);
  const items=P.items||P.nodes||P.children||[];
  /* ambient layer: drifting dot lattice, always animating */
  const dotField=(density=7,dim=0.16)=>{
    let d='';const sp=Math.min(W,H)/density;
    for(let r=0;r<density+2;r++)for(let cix=0;cix<Math.ceil(W/sp)+1;cix++){
      const i=r*13+cix,ph=(seedN%97)/97*6.28+i*.7;
      const dx=Math.sin(t*.5+ph)*U*.9,dy=Math.cos(t*.36+ph*1.3)*U*.9;
      const q=phase(p,.02+((i*37)%20)/100,.3);
      d+=`<div style="position:absolute;left:${px(cix*sp+dx)};top:${px(r*sp+dy)};width:${px(.5*U)};height:${px(.5*U)};border-radius:50%;background:${c.muted};opacity:${(dim*q).toFixed(2)};"></div>`;}
    return d;};
  /* kinetic word-by-word type */
  const kinetic=(txt,delay=.06,size=8,maxW=W*.8,color=c.text)=>{
    const words=String(txt||'').split(/\s+/).slice(0,12);
    return`<div style="display:flex;flex-wrap:wrap;gap:${px(size*.26*U)} ${px(size*.22*U)};max-width:${px(maxW)};">${words.map((w,i)=>{
      const q=phase(p,delay+i*.045,delay+i*.045+.22);
      return`<span style="opacity:${q};transform:translateY(${px((1-q)*3*U)}) rotate(${((1-q)*2).toFixed(1)}deg);display:inline-block;font:600 ${px(size*U)}/1.02 ${font};letter-spacing:-.05em;color:${color};">${esc(w)}</span>`;}).join('')}</div>`;};
  const microLabel=(txt,delay=0)=>txt?`<div style="opacity:${phase(p,delay,delay+.2)};font:600 ${px(1.7*U)}/1 ${font};letter-spacing:.14em;text-transform:uppercase;color:${c.muted};">${esc(txt)}</div>`:'';
  /* proportion ring for percentages */
  const ring=(val,size,cx,cy,delay=.1)=>{
    const R=size/2-2*U,q=phase(p,delay,delay+.9,easeInOut),v=clamp(val/100)*q,circ=2*Math.PI*R;
    return`<svg style="position:absolute;left:${px(cx-size/2)};top:${px(cy-size/2)};" width="${size}" height="${size}">
      <circle cx="${size/2}" cy="${size/2}" r="${R}" fill="none" stroke="${c.hairSoft}" stroke-width="${1.1*U}"/>
      <circle cx="${size/2}" cy="${size/2}" r="${R}" fill="none" stroke="${c.accent}" stroke-width="${1.1*U}" stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${circ*(1-v)}" transform="rotate(-90 ${size/2} ${size/2})"/></svg>`;};
  let body='';
  switch(scene.template){
    case 'big_number':{
      const isPct=/%/.test(P.number||''),val=parseFloat(String(P.number).replace(/[^\d.]/g,''))||0;
      const shown=Math.round(val*phase(p,.1,.9,easeInOut));
      const cx=wide?W*.32:W*.5,cy=H*(wide?.5:.42),sz=Math.min(W,H)*.56;
      body=`${isPct?ring(val,sz,cx,cy):''}
        <div style="position:absolute;left:${px(cx)};top:${px(cy)};transform:translate(-50%,-50%);text-align:center;">
          <div style="font:600 ${px(15*U)}/0.9 ${font};letter-spacing:-.06em;color:${c.text};">${shown}${isPct?'<span style="font-size:.45em;color:'+c.accent+'">%</span>':''}</div></div>
        <div style="position:absolute;${wide?`left:${px(W*.58)};right:${px(edge)};top:50%;transform:translateY(-50%);`:`left:${px(edge)};right:${px(edge)};top:${px(H*.68)};`}display:flex;flex-direction:column;gap:${px(2*U)};">
          ${microLabel(P.unit||'Measured',0.02)}${kinetic(P.label,0.5,4.6,wide?W*.36:W*.85,c.body)}</div>`;break;}
    case 'bar_chart':{
      const series=(P.series||[]).slice(0,8),max=Math.max(1,...series.map(x=>x.value));
      const chartH=H*(wide?.5:.36),bw=Math.min(14*U,(W-edge*2)/(series.length*1.8)),gap=bw*.8;
      const left=(W-(series.length*bw+(series.length-1)*gap))/2,base=H*(wide?.72:.62);
      const bars=series.map((it,i)=>{const q=phase(p,.2+i*.12,.6+i*.12,easeInOut);const h=chartH*(it.value/max)*q;
        const shown=Math.round(it.value*q);
        return`<div style="position:absolute;left:${px(left+i*(bw+gap))};top:${px(base-h)};width:${px(bw)};height:${px(h)};border-radius:${px(.8*U)} ${px(.8*U)} 0 0;background:${i===0?c.accent:c.raised};border:1px solid ${i===0?c.accent:c.hair};"></div>
        <div style="position:absolute;left:${px(left+i*(bw+gap)-gap/2)};top:${px(base-h-4.6*U)};width:${px(bw+gap)};text-align:center;font:600 ${px(3.2*U)}/1 ${font};letter-spacing:-.03em;color:${c.text};opacity:${q};">${shown}${esc(it.unit||'')}</div>
        <div style="position:absolute;left:${px(left+i*(bw+gap)-gap/2)};top:${px(base+1.6*U)};width:${px(bw+gap)};text-align:center;font:600 ${px(1.6*U)}/1.2 ${font};letter-spacing:.08em;text-transform:uppercase;color:${c.muted};opacity:${q};">${esc(trimWords(it.label,2))}</div>`;}).join('');
      const baseline=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(base)};height:1px;background:${c.hair};transform:scaleX(${phase(p,.08,.4,easeInOut)});"></div>`;
      body=`${baseline}${bars}<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.1)};display:flex;flex-direction:column;gap:${px(1.8*U)};">${microLabel(P.unit==='Share'?'Share':'Data',.02)}${kinetic(P.headline,.06,4.4,W*.8)}</div>`;break;}
    case 'before_after':case 'comparison_split':case 'transformation_arrow':case 'cause_effect':case 'problem_solution':case 'condition_cards':{
      /* morph field: scattered dots organize into a circle */
      const n=14,cxL=wide?W*.28:W*.5,cyL=wide?H*.52:H*.34,cxR=wide?W*.72:W*.5,cyR=wide?H*.52:H*.66,R=Math.min(W,H)*.13;
      const q=phase(p,.3,.75,easeInOut);
      let dots='';
      for(let i=0;i<n;i++){
        const rnd=a=>((hash53(scene.id+'|'+i+'|'+a)%1000)/1000-0.5);
        const sx=cxL+rnd(1)*R*2.4,sy=cyL+rnd(2)*R*2.4;
        const ang=i/n*Math.PI*2,ex=cxR+Math.cos(ang)*R,ey=cyR+Math.sin(ang)*R;
        const x=sx+(ex-sx)*q,y=sy+(ey-sy)*q,ap=phase(p,.08+i*.02,.28+i*.02);
        dots+=`<div style="position:absolute;left:${px(x-U*.8)};top:${px(y-U*.8)};width:${px(1.6*U)};height:${px(1.6*U)};border-radius:50%;background:${q>.6?c.accent:c.muted};opacity:${ap};"></div>`;}
      const arrowQ=phase(p,.34,.6,easeInOut);
      const arrow=wide?`<div style="position:absolute;left:${px(cxL+R*1.4)};top:${px(cyL)};width:${px((cxR-cxL-R*2.8)*arrowQ)};height:${px(.4*U)};background:${c.accent};"></div><div style="position:absolute;left:${px(cxL+R*1.4+(cxR-cxL-R*2.8)*arrowQ)};top:${px(cyL-2*U)};opacity:${arrowQ};font:600 ${px(4*U)}/1 ${font};color:${c.accent};">\u2192</div>`
        :`<div style="position:absolute;left:50%;top:${px(cyL+R*1.5)};transform:translateX(-50%) rotate(90deg);opacity:${arrowQ};font:600 ${px(4.6*U)}/1 ${font};color:${c.accent};">\u2192</div>`;
      const lbl={before_after:['Before','After'],comparison_split:['A','B'],cause_effect:['Cause','Effect'],problem_solution:['Problem','Response'],condition_cards:['If','Then']}[scene.template]||['From','To'];
      const tag=(txt,sub,x,y,q2,hot)=>`<div style="position:absolute;left:${px(x)};top:${px(y)};transform:translateX(-50%);text-align:center;opacity:${q2};display:flex;flex-direction:column;gap:${px(U)};align-items:center;max-width:${px(wide?W*.34:W*.8)};">
        <div style="font:600 ${px(1.6*U)}/1 ${font};letter-spacing:.14em;text-transform:uppercase;color:${hot?c.accent:c.muted};">${esc(sub)}</div>
        <div style="font:600 ${px(3.2*U)}/1.18 ${font};letter-spacing:-.03em;color:${c.text};">${esc(trimWords(txt||'',6))}</div></div>`;
      body=`${dots}${arrow}
        ${tag(P.left,lbl[0],cxL,cyL+R*1.9,phase(p,.14,.34),false)}
        ${tag(P.right,lbl[1],cxR,cyR+R*1.9,phase(p,.55,.8),true)}
        <div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.09)};">${kinetic(P.headline,.04,3.8,W*.8)}</div>`;break;}
    case 'list_stack':case 'steps':case 'timeline':case 'funnel':{
      const evs=(P.events&&P.events.length?P.events.map(e=>e.event):items).slice(0,6);
      const n2=evs.length,ordered=scene.template!=='list_stack';
      const cols=wide?Math.min(3,n2):1,rows=Math.ceil(n2/cols);
      const cw=(W-edge*2-(cols-1)*3*U)/cols,chh=Math.min(16*U,(H*.52)/rows-2*U);
      const cells=evs.map((it,i)=>{const q=phase(p,.18+i*.1,.44+i*.1,easeBack);
        const cx2=edge+(i%cols)*(cw+3*U),cy2=H*.34+Math.floor(i/cols)*(chh+2.4*U);
        const glyph=ordered?String(i+1).padStart(2,'0'):'\u2192';
        return`<div style="position:absolute;left:${px(cx2)};top:${px(cy2)};width:${px(cw)};height:${px(chh)};display:flex;align-items:center;gap:${px(2.2*U)};padding:0 ${px(2.4*U)};border:1px solid ${c.hairSoft};border-radius:${px(1.4*U)};background:${c.surface};opacity:${q};transform:scale(${.88+.12*q}) translateY(${px((1-q)*2*U)});">
          <div style="font:600 ${px(4.6*U)}/1 ${font};letter-spacing:-.04em;color:${c.accent};">${glyph}</div>
          <div style="font:600 ${px(2.5*U)}/1.2 ${font};letter-spacing:-.02em;color:${c.text};">${esc(trimWords(it,5))}</div></div>`;}).join('');
      const rail=ordered&&cols===1?`<div style="position:absolute;left:${px(edge-1.4*U)};top:${px(H*.34)};width:${px(.34*U)};height:${px((rows-1)*(chh+2.4*U)*phase(p,.15,.7,easeInOut)+chh*.5)};background:${c.accent};border-radius:999px;"></div>`:'';
      body=`${rail}${cells}<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.1)};display:flex;flex-direction:column;gap:${px(1.8*U)};">${microLabel(P.label||(ordered?'In order':'Key points'),.02)}${kinetic(P.headline,.06,4.4,W*.8)}</div>`;break;}
    case 'network':case 'cycle':case 'hierarchy_tree':{
      const nodes=items.slice(0,6),cx=wide?W*.64:W*.5,cy=wide?H*.52:H*.58,R=Math.min(W*(wide?.22:.34),H*.26);
      const cQ=phase(p,.06,.28,easeBack),eQ=phase(p,.25,.7,easeInOut);
      let svg='',lbls='';
      nodes.forEach((nd,i)=>{const ang=-Math.PI/2+Math.PI*2*i/Math.max(1,nodes.length)+Math.sin(t*.4+i)*0.02;
        const x=cx+Math.cos(ang)*R,y=cy+Math.sin(ang)*R,q=phase(p,.3+i*.07,.5+i*.07,easeBack);
        if(scene.template==='cycle'&&nodes.length>1){const na=-Math.PI/2+Math.PI*2*((i+1)%nodes.length)/nodes.length;
          svg+=`<line x1="${x}" y1="${y}" x2="${cx+Math.cos(na)*R}" y2="${cy+Math.sin(na)*R}" stroke="${c.accent}" stroke-width="${.3*U}" opacity="${eQ*.7}"/>`;}
        else svg+=`<line x1="${cx}" y1="${cy}" x2="${cx+(x-cx)*eQ}" y2="${cy+(y-cy)*eQ}" stroke="${c.hair}" stroke-width="${.28*U}"/>`;
        const pulse=1+.05*Math.sin(t*2+i*1.3);
        lbls+=`<div style="position:absolute;left:${px(x-2*U)};top:${px(y-2*U)};width:${px(4*U)};height:${px(4*U)};border-radius:50%;background:${c.accent};opacity:${q};transform:scale(${(0.7+0.3*q)*pulse});"></div>
        <div style="position:absolute;left:${px(x-9*U)};top:${px(y+3*U)};width:${px(18*U)};text-align:center;opacity:${q};font:600 ${px(1.9*U)}/1.2 ${font};letter-spacing:-.01em;color:${c.body};">${esc(trimWords(typeof nd==='object'?nd.event:nd,3))}</div>`;});
      body=`<svg style="position:absolute;inset:0;" width="${W}" height="${H}">${svg}</svg>
        <div style="position:absolute;left:${px(cx-6.5*U)};top:${px(cy-6.5*U)};width:${px(13*U)};height:${px(13*U)};border-radius:50%;background:${c.raised};border:${px(.3*U)} solid ${c.accent};display:grid;place-items:center;text-align:center;padding:${px(U)};opacity:${cQ};transform:scale(${.75+.25*cQ});font:600 ${px(1.9*U)}/1.12 ${font};color:${c.text};">${esc(trimWords(P.center||P.parent||'',3))}</div>${lbls}
        <div style="position:absolute;left:${px(edge)};top:${px(H*.1)};width:${px(wide?W*.32:W*.85)};display:flex;flex-direction:column;gap:${px(1.8*U)};">${microLabel(P.label||'System',.02)}${kinetic(P.headline,.06,4.2,wide?W*.32:W*.8)}</div>`;break;}
    case 'question_card':{
      const q=phase(p,.05,.4,easeBack),pulse=1+.04*Math.sin(t*2.2);
      body=`<div style="position:absolute;left:50%;top:${px(H*.36)};transform:translate(-50%,-50%) scale(${q*pulse});width:${px(16*U)};height:${px(16*U)};border-radius:50%;border:${px(.35*U)} solid ${c.accent};display:grid;place-items:center;font:600 ${px(9*U)}/1 ${font};color:${c.accent};">?</div>
        <div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.52)};display:flex;justify-content:center;">${kinetic(P.headline||scene.text,.25,wide?6.4:5.2,W*.78)}</div>`;break;}
    case 'cta_card':{
      const bq=phase(p,.45,.72,easeBack),sweep=phase(p,.02,.5,easeInOut);
      body=`<div style="position:absolute;inset:0;background:${c.accent};transform:scaleY(${sweep});transform-origin:bottom;opacity:.96;"></div>
        <div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(3*U)};opacity:${sweep};">
          ${kinetic(P.headline,.3,wide?8.4:6.6,W*.85,'#FFFFFF')}
          <div style="display:flex;align-items:center;gap:${px(3*U)};margin-top:${px(2*U)};">
            <div style="opacity:${bq};transform:scale(${.88+.12*bq});padding:${px(2.2*U)} ${px(4.2*U)};border-radius:999px;background:#FFFFFF;font:600 ${px(2.7*U)}/1 ${font};color:#0A0F1E;">${esc(P.action||'Learn more')} \u2192</div>
            ${P.destination?`<div style="opacity:${phase(p,.62,.82)};font:600 ${px(2*U)}/1 ${font};letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.8);">${esc(P.destination)}</div>`:''}</div></div>`;break;}
    case 'definition_card':{
      const line=phase(p,.3,.58,easeInOut);
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(3*U)};">
        ${microLabel(P.label||'Definition',.02)}${kinetic(P.term||P.headline,.07,7.4,W*.8)}
        <div style="height:${px(.3*U)};width:${line*44}%;background:${c.accent};"></div>
        <div style="opacity:${phase(p,.42,.7)};font:400 ${px(3*U)}/1.42 ${font};color:${c.body};max-width:${px(W*.7)};">${esc(trimWords(P.definition||P.supporting||'',20))}</div></div>`;break;}
    case 'warning_card':{
      const q=phase(p,.05,.35,easeBack),blink=.6+.4*Math.abs(Math.sin(t*2));
      body=`<div style="position:absolute;left:50%;top:${px(H*.32)};transform:translate(-50%,-50%) scale(${q});width:${px(11*U)};height:${px(11*U)};border-radius:50%;border:${px(.35*U)} solid ${c.danger};display:grid;place-items:center;font:600 ${px(6*U)}/1 ${font};color:${c.danger};opacity:${blink};">!</div>
        <div style="position:absolute;left:${px(edge)};right:${px(edge)};top:${px(H*.46)};display:flex;flex-direction:column;align-items:center;gap:${px(2*U)};text-align:center;">
          ${microLabel(P.label||'Important',.1)}<div style="display:flex;justify-content:center;">${kinetic(P.headline,.2,5.4,W*.78)}</div></div>`;break;}
    default:{/* title_card, quote_focus, emphasis */
      const isQuote=scene.template==='quote_focus';
      body=`<div style="position:absolute;left:${px(edge)};right:${px(edge)};top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:${px(2.6*U)};">
        ${isQuote?`<div style="opacity:${phase(p,.02,.22)};font:600 ${px(10*U)}/0.5 ${font};color:${c.accent};">\u201c</div>`:microLabel(P.label||'',.02)}
        ${kinetic(P.headline||scene.text,.1,wide?8.6:7,W*.84)}</div>`;}
  }
  const drift=1+0.016*easeInOut(p);
  const showField=['title_card','quote_focus','question_card','big_number','warning_card'].includes(scene.template);
  return`<div style="position:absolute;inset:0;background:${c.canvas};overflow:hidden;font-family:${font};">
    <div style="position:absolute;inset:-2%;transform:scale(${drift});transform-origin:50% 44%;">
      <div style="position:absolute;inset:0;background:${B.wash};"></div>
      ${showField?dotField():''}${body}</div></div>`;
}

window.LAVC={DEFAULTS,TEMPLATES,LEXICON,BRANDS,ASPECTS,parseSRT,segment,classify,extractPayload,compile,generateVersions,recompile,renderScene:renderSceneV2,renderSceneText:renderScene,hash53,clamp};
})();
