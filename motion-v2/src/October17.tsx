import React from 'react';
import {AbsoluteFill,Audio,Img,staticFile,useCurrentFrame,useVideoConfig,interpolate,Easing} from 'remotion';

/** Original motion-design explainer. All UI, data and model output are illustrative, never a live Gemini Argon session. */
const C={dark:'#041320',mid:'#0D344A',blue:'#165577',cyan:'#63E8E9',white:'#F8FDFF',muted:'#B8CEDC',amber:'#FFC872',red:'#FF7790',green:'#80EBBE'};
const F='Inter,Segoe UI,Arial,sans-serif';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const ease=(x:number)=>Easing.out(Easing.cubic)(clamp(x));
const Txt:React.FC<{children:React.ReactNode;sz?:number;color?:string;style?:React.CSSProperties}>=({children,sz=43,color=C.white,style})=><div style={{fontFamily:F,fontSize:sz,fontWeight:850,color,lineHeight:1.14,...style}}>{children}</div>;
const Eyebrow:React.FC<{children:React.ReactNode;sz?:number;color?:string}>=({children,sz=22,color=C.cyan})=><div style={{fontFamily:F,fontSize:sz,letterSpacing:1.1,fontWeight:900,color}}>{children}</div>;
const Glass:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{borderRadius:26,background:'linear-gradient(145deg,#123D54F6,#08243BF4)',border:'2px solid #4F8295',boxShadow:'0 26px 85px #0007',boxSizing:'border-box',overflow:'hidden',...style}}>{children}</div>;
const Brand=()=> <Eyebrow color={C.cyan}>FM  /  FLOWMINUTE LAB</Eyebrow>;
const Note:React.FC=()=> <div style={{fontSize:17,color:C.muted,fontFamily:F,fontWeight:780}}>ILLUSTRATIVE DATA & UI · NOT A LIVE GEMINI 4 ARGON TEST</div>;
const Background:React.FC<{f:number;variant?:'desk'|'phone'}>=({f,variant='desk'})=><AbsoluteFill style={{background:C.dark}}>
 <Img src={staticFile(variant==='phone'?'oct15-phone-still.jpg':'office-desks.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',filter:'saturate(.8) blur(2px)',opacity:.26,transform:'scale('+(1.02+f/25000)+')'}}/>
 <div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 68% 30%,#174862BD,transparent 57%),linear-gradient(120deg,#03121CE9,#082337EC)'}}/>
 <div style={{position:'absolute',inset:0,opacity:.11,background:'repeating-linear-gradient(0deg,transparent,transparent 64px,#4FE3EB 65px),repeating-linear-gradient(90deg,transparent,transparent 64px,#4FE3EB 65px)'}}/>
 </AbsoluteFill>;
const Pill:React.FC<{children:React.ReactNode;color?:string}>=({children,color=C.cyan})=><span style={{display:'inline-block',borderRadius:10,padding:'10px 16px',background:'#104257',border:'1px solid '+color,color,fontFamily:F,fontWeight:850,fontSize:23}}>{children}</span>;
const Foot:React.FC<{f:number,total:number}>=({f,total})=><><div style={{position:'absolute',bottom:0,left:0,width:'100%',height:8,background:'#25465C'}}><div style={{height:'100%',background:C.cyan,width:(100*clamp(f/total))+'%'}}/></div></>;
const Table:React.FC<{f:number;compact?:boolean}>=({f,compact=false})=>{
 const rows=[['SALE A','+120'],['SALE B','+95'],['SALE C','+110'],['REFUND','−25']];
 const n=compact?25:26;
 return <Glass style={{height:'100%',padding:compact?22:35}}>
 <div style={{display:'flex',justifyContent:'space-between',borderBottom:'1px solid #568CA0',paddingBottom:16}}><Eyebrow>SHOP SALES</Eyebrow><Eyebrow sz={18} color={C.muted}>FICTIONAL DATA</Eyebrow></div>
 <Txt sz={compact?40:48} style={{marginTop:19}}>Which total is correct?</Txt>
 <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8,marginTop:26}}>
 {rows.flatMap(([name,amount],i)=>[<div key={'a'+i} style={{background:i===3?'#5F384E':'#21536A',padding:compact?16:20,borderRadius:8}}><Txt sz={n}>{name}</Txt></div>,<div key={'b'+i} style={{background:i===3?'#5F384E':'#21536A',padding:compact?16:20,borderRadius:8,textAlign:'right'}}><Txt sz={n} color={i===3?C.amber:C.white}>₹{amount.replace('−','-')}</Txt></div>])}
 </div>
 <div style={{marginTop:26,display:'flex',gap:12}}>
 <div style={{flex:1,background:'#733948',padding:compact?17:20,borderRadius:14}}><Eyebrow color={C.red}>WRONG</Eyebrow><Txt sz={compact?49:54}>₹350</Txt></div>
 <div style={{flex:1,background:'#1B5B57',padding:compact?17:20,borderRadius:14,border:'2px solid '+C.green}}><Eyebrow color={C.green}>NET</Eyebrow><Txt sz={compact?49:54}>₹300</Txt></div></div>
 <Eyebrow sz={compact?21:20} color={C.amber}><span style={{display:'block',marginTop:20}}>REFUNDS SUBTRACT FROM SALES.</span></Eyebrow>
 </Glass>
};
const Bars:React.FC<{f:number;type?:'wrong'|'correct';compact?:boolean}>=({f,type='correct',compact=false})=>{
 const width=clamp((f%110)/48);const wrong=type==='wrong';
 const vals=wrong?[120,95,110,25]:[120,95,110,-25],label=wrong?'BAD CHART':'CHECKED CHART',total=wrong?350:300;
 const max=125;
 return <Glass style={{height:'100%',padding:compact?25:36}}>
 <Eyebrow color={wrong?C.red:C.green}>{label} · CONCEPTUAL</Eyebrow><Txt sz={compact?45:51} style={{marginTop:24}}>Net sales</Txt><Txt color={wrong?C.red:C.green} sz={compact?100:108} style={{marginTop:17}}>₹{total}</Txt>
 <div style={{marginTop:33,display:'flex',height:compact?255:300,gap:15,alignItems:'end',padding:'0 14px 25px',borderBottom:'3px solid #78A3AD'}}>
 {vals.map((v,i)=><div key={i} style={{flex:1,height:'100%',display:'flex',flexDirection:'column',justifyContent:'end',alignItems:'center'}}>
 <Txt sz={compact?20:20} color={i===3?C.amber:C.muted}>{i===3?(wrong?'+25':'−25'):''+v}</Txt><div style={{marginTop:10,width:'85%',height:Math.max(15,Math.round((Math.abs(v)/max)*220*ease(width+.25)))+'px',background:i===3?(wrong?C.red:C.green):'#54CFE0',borderRadius:'8px 8px 1px 1px'}}/>
 </div>)}</div>
 <div style={{display:'flex',justifyContent:'space-between',marginTop:14}}>{['A','B','C','REFUND'].map(x=><Txt key={x} sz={compact?20:22} color={C.muted}>{x}</Txt>)}</div>
 <Txt sz={compact?23:25} color={C.muted} style={{marginTop:28}}>{wrong?'Refund was treated as revenue.':'120 + 95 + 110 − 25 = 300'}</Txt>
 </Glass>
};
const Steps:React.FC<{f:number;kind:'prompt'|'verify';compact?:boolean}>=({f,kind,compact=false})=>{
 const p=kind==='prompt'?['Inspect all columns','Treat refunds as deductions','Show checks before charts']:['Add sales: ₹325','Subtract refunds: ₹25','Confirm net: ₹300'];
 return <Glass style={{height:'100%',padding:compact?27:40}}>
 <Eyebrow color={C.amber}>{kind==='prompt'?'BETTER PROMPT':'INDEPENDENT CHECK'}</Eyebrow><Txt sz={compact?48:62} style={{marginTop:24}}>{kind==='prompt'?'Don’t just say “make a dashboard.”':'Make the math visible.'}</Txt>
 <div style={{marginTop:30}}>{p.map((s,i)=><div key={s} style={{display:'flex',gap:16,alignItems:'center',background:i===Math.floor(f/55)%3?'#2B6671':'#12394F',marginBottom:19,padding:compact?20:25,border:'1px solid #51899C',borderRadius:15}}>
 <div style={{flexShrink:0,width:compact?42:52,height:compact?42:52,borderRadius:'50%',background:C.cyan,textAlign:'center',fontSize:compact?27:32,color:'#002837',fontWeight:950,lineHeight:compact?'42px':'52px'}}>{i+1}</div>
 <Txt sz={compact?27:32}>{s}</Txt></div>)}</div>
 <Eyebrow color={C.green}>SHOW REASONING, THEN VERIFY OUTPUT</Eyebrow>
 </Glass>;
};
const Access:React.FC<{f:number;compact?:boolean}>=({f,compact=false})=><Glass style={{height:'100%',padding:compact?24:34}}>
 <Eyebrow color={C.amber}>ACCESS CHECK · OCTOBER 2026</Eyebrow><Txt sz={compact?47:56} style={{marginTop:26}}>App ≠ API</Txt>
 <div style={{marginTop:29,display:'flex',gap:14}}>
 {[['GEMINI APP','Pro + Ultra','Subscriber access',C.cyan],['GEMINI API','PAID TIER','No free Argon API',C.amber]].map(([h,a,b,color])=><div key={h} style={{flex:1,border:'2px solid '+color,padding:compact?'20px 12px':'24px 17px',borderRadius:18,background:'#164153'}}>
 <Eyebrow color={color} sz={compact?18:20}>{h}</Eyebrow><Txt sz={compact?30:36} style={{marginTop:16}}>{a}</Txt><Txt sz={compact?22:25} color={C.muted} style={{marginTop:14}}>{b}</Txt></div>)}</div>
 <div style={{marginTop:32,padding:compact?24:30,background:'#27536A',borderRadius:12}}><Eyebrow>INTRODUCTORY API PRICE</Eyebrow><Txt sz={compact?28:36} style={{marginTop:10}}>$2 input / $10 output</Txt><Txt sz={compact?22:24} color={C.muted}>per 1 million tokens, including thinking output</Txt></div>
 <Txt color={C.amber} sz={compact?24:26} style={{marginTop:23}}>Intro ends November 30, 2026.</Txt>
 </Glass>;
const Context:React.FC<{f:number;compact?:boolean}>=({f,compact=false})=><Glass style={{height:'100%',padding:compact?28:39}}>
 <Eyebrow color={C.amber}>MODEL FACTS · FROM GOOGLE</Eyebrow><Txt sz={compact?52:60} style={{marginTop:30}}>Gemini 4 Argon</Txt>
 <div style={{marginTop:36,background:'#20556B',padding:compact?27:36,borderRadius:19}}>
 <Eyebrow>DEVELOPER CONTEXT LIMIT</Eyebrow><Txt sz={compact?93:102} color={C.cyan} style={{marginTop:22}}>~1M</Txt><Txt sz={compact?35:40}>tokens</Txt></div>
 <div style={{marginTop:33}}>{['Complex multi-step coding','Long-form document analysis','Reasoning levels: low, medium, high'].map((v,i)=><Txt key={v} sz={compact?26:28} style={{marginTop:22}} color={i===Math.floor(f/60)%3?C.green:C.muted}>• {v}</Txt>)}</div>
 <Txt sz={compact?21:23} color={C.amber} style={{marginTop:25}}>CAPACITY ≠ GUARANTEED ACCURACY</Txt>
 </Glass>;
const Vote:React.FC<{compact?:boolean}>=({compact=false})=><Glass style={{height:'100%',padding:compact?35:48,textAlign:'center'}}>
 <Eyebrow color={C.amber}>YOUR DECISION</Eyebrow><Txt sz={compact?66:80} style={{marginTop:37}}>BUILD OR CHECK?</Txt>
 <div style={{display:'flex',gap:17,marginTop:67}}>{['BUILD','CHECK'].map((v,i)=><div key={v} style={{flex:1,padding:compact?'32px 8px':'45px 8px',border:'2px solid '+(i?C.green:C.cyan),borderRadius:15}}><Txt sz={compact?31:48} color={i?C.green:C.cyan}>{v}</Txt></div>)}</div>
 <Txt sz={compact?28:37} color={C.muted} style={{marginTop:70}}>Tell us which step you would trust AI to do.</Txt><Txt sz={compact?28:34} color={C.cyan} style={{marginTop:27}}>COMMENT BELOW ↓</Txt>
 </Glass>;
type Mode='table'|'wrong'|'correct'|'prompt'|'verify'|'access'|'context'|'vote';
const Data:React.FC<{mode:Mode;f:number;compact?:boolean}>=({mode,f,compact=false})=>mode==='table'?<Table f={f} compact={compact}/>:mode==='wrong'||mode==='correct'?<Bars type={mode} f={f} compact={compact}/>:mode==='prompt'||mode==='verify'?<Steps kind={mode} f={f} compact={compact}/>:mode==='access'?<Access f={f} compact={compact}/>:mode==='context'?<Context f={f} compact={compact}/>:<Vote compact={compact}/>;
type Beat={a:number;b:number;tag:string;head:string;sub:string;mode:Mode};
const s25:Beat[]=[
 {a:0,b:.20,tag:'SOMETHING IS WRONG',head:'THIS CHART LIES.',sub:'Refunds are counted as sales.',mode:'wrong'},
 {a:.20,b:.48,tag:'CHECK THE NUMBERS',head:'₹350 → ₹300',sub:'Sales minus refunds. Not a guess.',mode:'table'},
 {a:.48,b:.75,tag:'GEMINI 4 ARGON',head:'ASK AI TO CHECK',sub:'Explain the calculation before charting.',mode:'verify'},
 {a:.75,b:1,tag:'YOUR CHOICE',head:'BUILD OR CHECK?',sub:'Would you trust an AI dashboard?',mode:'vote'}
];
const s26:Beat[]=[
 {a:0,b:.23,tag:'GEMINI 4 ARGON',head:'FREE OR PAID?',sub:'App access is not API access.',mode:'access'},
 {a:.23,b:.53,tag:'THE PAID CATCH',head:'API COSTS EXTRA',sub:'No free Argon developer tier.',mode:'access'},
 {a:.53,b:.78,tag:'INTRODUCTORY OFFER',head:'PRICE DOUBLES',sub:'After November 30, 2026.',mode:'access'},
 {a:.78,b:1,tag:'BEFORE YOU PAY',head:'APP OR API?',sub:'What would you actually use?',mode:'vote'}
];
const shorts:Record<'25'|'26',Beat[]>={'25':s25,'26':s26};
const Short:React.FC<{which:'25'|'26'}>=({which})=>{
 const f=useCurrentFrame(),{durationInFrames:frames}=useVideoConfig(),t=f/frames,beats=shorts[which],b=beats.find(v=>t>=v.a&&t<v.b)||beats[beats.length-1];
 const show=ease((f-b.a*frames)/14);
 return <AbsoluteFill style={{color:C.white,fontFamily:F}}><Background f={f} variant={t<.18?'phone':'desk'}/>
 <div style={{position:'absolute',top:76,left:60}}><Brand/></div>
 <div style={{position:'absolute',top:194,left:66,right:66,opacity:show,transform:'translateY('+((1-show)*25)+'px)'}}>
 <Eyebrow color={C.amber} sz={26}>{b.tag}</Eyebrow><Txt sz={82} style={{letterSpacing:-2,marginTop:22}}>{b.head}</Txt><Txt sz={35} color={C.muted} style={{marginTop:22}}>{b.sub}</Txt></div>
 <div style={{position:'absolute',top:650,left:62,right:62,height:720,opacity:show,transform:'scale('+(0.965+.035*show)+')'}}><Data mode={b.mode} f={f} compact/></div>
 <div style={{position:'absolute',top:1490,left:68,right:68,padding:24,background:'#0B2D41E0',borderLeft:'6px solid '+C.cyan}}>
 <Txt sz={26} color={C.cyan}>{which==='25'?'ORIGINAL EXAMPLE · VERIFY YOUR OWN DATA':'GOOGLE ANNOUNCEMENT · OCT 13, 2026'}</Txt>
 <Txt sz={20} color={C.muted} style={{marginTop:14}}>Conceptual graphics, not a tested product session.</Txt>
 </div>
 <div style={{position:'absolute',bottom:92,left:68,right:68}}><Note/></div><Foot f={f} total={frames}/>
 <Audio src={staticFile(which==='25'?'oct17-v25.mp3':'oct17-v26.mp3')}/></AbsoluteFill>;
};
const longBeats:Beat[]=[
 {a:0,b:.095,tag:'THE CHART LOOKS PERFECT',head:'IT IS STILL WRONG.',sub:'A refund became revenue. Would you notice?',mode:'wrong'},
 {a:.095,b:.245,tag:'FIRST CHECK THE DATA',head:'THE REFUND TRAP',sub:'Three sales and one negative transaction.',mode:'table'},
 {a:.245,b:.405,tag:'PROMPT ENGINEERING',head:'MAKE AI SHOW ITS WORK',sub:'Inspect. State assumptions. Calculate. Verify.',mode:'prompt'},
 {a:.405,b:.55,tag:'VERIFY IT YOURSELF',head:'₹325 − ₹25 = ₹300',sub:'An independent check beats a confident mistake.',mode:'correct'},
 {a:.55,b:.695,tag:'OFFICIAL GEMINI RELEASE',head:'GEMINI 4 ARGON',sub:'Google says its newest reasoning model handles harder multi-step work.',mode:'context'},
 {a:.695,b:.83,tag:'WHO GETS ACCESS?',head:'APP ≠ DEVELOPER API',sub:'Pro/Ultra in the app. Separate paid API.',mode:'access'},
 {a:.83,b:.925,tag:'THE REAL LESSON',head:'TRUST THE CHECKS.',sub:'Good prompts plus independent verification.',mode:'verify'},
 {a:.925,b:1,tag:'LEARN TO WORK WITH AI',head:'BUILD OR CHECK?',sub:'Which step would you delegate?',mode:'vote'}
];
export const ArgonDataShort:React.FC=()=> <Short which='25'/>;
export const ArgonPricingShort:React.FC=()=> <Short which='26'/>;
export const ArgonDashboardLong:React.FC=()=>{
 const f=useCurrentFrame(),{durationInFrames:frames}=useVideoConfig(),t=f/frames,b=longBeats.find(v=>t>=v.a&&t<v.b)||longBeats[longBeats.length-1],show=ease((f-frames*b.a)/14);
 return <AbsoluteFill style={{fontFamily:F,color:C.white}}><Background f={f}/>
 <div style={{position:'absolute',top:48,left:87,right:87,display:'flex',justifyContent:'space-between'}}><Brand/><Eyebrow color={C.amber}>GEMINI 4 ARGON · PRACTICAL EXPLAINER</Eyebrow></div>
 <div style={{position:'absolute',left:91,top:188,width:760,opacity:show,transform:'translateY('+((1-show)*38)+'px)'}}>
 <Eyebrow color={C.amber}>{b.tag}</Eyebrow><Txt sz={75} style={{marginTop:24,letterSpacing:-2}}>{b.head}</Txt><Txt sz={34} color={C.muted} style={{marginTop:32}}>{b.sub}</Txt>
 <Glass style={{marginTop:60,padding:24,borderLeft:'7px solid '+C.cyan}}><Txt sz={25}>Original illustrative data; no claim of a live Gemini test.</Txt></Glass>
 </div>
 <div style={{position:'absolute',top:166,left:934,right:80,height:739,opacity:show,transform:'translateX('+((1-show)*27)+'px)'}}><Data mode={b.mode} f={f}/></div>
 <div style={{position:'absolute',bottom:69,left:86,right:86,display:'flex',justifyContent:'space-between'}}><Note/><Eyebrow sz={17}>SOURCE: GOOGLE, OCT 13, 2026</Eyebrow></div>
 <Foot f={f} total={frames}/><Audio src={staticFile('oct17-long012.mp3')}/></AbsoluteFill>;
};
export const ArgonDashboardThumbnail:React.FC=()=> <AbsoluteFill style={{fontFamily:F,color:C.white}}><Background f={0}/>
 <div style={{position:'absolute',left:92,top:76}}><Brand/></div>
 <div style={{position:'absolute',top:218,left:95,width:1010}}>
 <Txt sz={143} style={{letterSpacing:-5}}>THIS AI</Txt><Txt sz={155} color={C.amber} style={{letterSpacing:-5}}>CHART LIES?</Txt>
 <Txt sz={45} color={C.cyan} style={{marginTop:41}}>GEMINI 4 ARGON EXPLAINED</Txt><Txt sz={33} color={C.muted} style={{marginTop:30}}>CAN IT BUILD A BETTER DASHBOARD?</Txt>
 </div>
 <div style={{position:'absolute',left:1120,top:170,width:700,height:740,transform:'rotate(-3deg)'}}><Bars f={35} type='wrong'/></div>
 </AbsoluteFill>;
