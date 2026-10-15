import React from 'react';
import {AbsoluteFill,Audio,Img,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';

/** FlowMinute Lab Oct 18. All app scenes are clearly labeled original illustrations, not product captures. */
const P={navy:'#041420',blue:'#0B2940',panel:'#113D56',cyan:'#66E7E7',mint:'#85E8BC',gold:'#FFD38B',white:'#F8FCFD',muted:'#B5CFD9',red:'#FC8B9C'};
const font='Inter,Segoe UI,Arial,sans-serif';
const cap=(x:number)=>Math.max(0,Math.min(1,x));
const T:React.FC<{children:React.ReactNode;n?:number;ink?:string;style?:React.CSSProperties}>=({children,n=46,ink=P.white,style})=><div style={{fontFamily:font,color:ink,fontSize:n,fontWeight:900,lineHeight:1.12,letterSpacing:-.5,...style}}>{children}</div>;
const Tag:React.FC<{children:React.ReactNode;ink?:string}>=({children,ink=P.cyan})=><div style={{fontFamily:font,color:ink,fontSize:22,fontWeight:850,letterSpacing:1.1}}>{children}</div>;
const Panel:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{borderRadius:24,background:'linear-gradient(137deg,#163C53F7,#0B2941F8)',border:'2px solid #4C8596',padding:30,boxSizing:'border-box',boxShadow:'0 24px 60px #0007',...style}}>{children}</div>;
const Bg:React.FC<{f:number}>=({f})=><AbsoluteFill style={{background:P.navy}}><Img src={staticFile('office-desks.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',opacity:.24,filter:'blur(4px) saturate(.8)',transform:'scale('+(1.06+f/26000)+')'}}/><div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 80% 25%,#12546C88,transparent 60%),linear-gradient(110deg,#031322EF,#061B31E8)'}}/></AbsoluteFill>;
const Brand=()=> <Tag>FM / FLOWMINUTE LAB</Tag>;
const CardLabel:React.FC<{children:React.ReactNode}>=({children})=><div style={{fontFamily:font,fontSize:18,fontWeight:760,color:P.muted,letterSpacing:1}}>{children}</div>;
type Mode='clock'|'brief'|'prompt'|'research'|'permissions'|'plans'|'compare'|'vote1'|'vote2'|'vote3';
const DotCard:React.FC<{mode:Mode;f:number;compact?:boolean}>=({mode,f,compact=false})=>{
 const n=compact?32:30;
 const li=(head:string,sub:string,color:string,idx:number)=><div key={head} style={{padding:compact?'18px 16px':'23px 18px',marginTop:15,borderRadius:12,background:idx===Math.floor(f/55)%3?'#24576E':'#10374D',border:'1px solid #4F8A9B',display:'flex',gap:17,alignItems:'center'}}>
 <div style={{flexShrink:0,width:36,height:36,borderRadius:20,background:color,display:'grid',placeItems:'center',fontSize:23,fontWeight:900,color:'#042437'}}>{idx+1}</div><div><T n={n} ink={P.white}>{head}</T><T n={compact?21:23} ink={P.muted} style={{marginTop:7}}>{sub}</T></div></div>;
 return <Panel style={{height:'100%',overflow:'hidden',padding:compact?24:30}}>
 <div style={{display:'flex',justifyContent:'space-between',gap:7,paddingBottom:17,borderBottom:'1px solid #4A778D'}}><Tag ink={P.mint}>ORIGINAL EXAMPLE</Tag><CardLabel>NOT A LIVE PRODUCT RECORDING</CardLabel></div>
 {mode==='clock'?<><Tag ink={P.gold}>TONIGHT'S PROBLEM</Tag><T n={compact?105:110} style={{marginTop:29}}>11:00</T><T n={compact?49:48} ink={P.gold}>PM</T><T n={compact?43:42} style={{marginTop:30}}>RESEARCH STILL UNFINISHED</T><div style={{marginTop:33}}>{li('7 tabs open','Sources not verified yet',P.red,0)}{li('Empty presentation','Meeting tomorrow',P.gold,1)}</div></>:
 mode==='brief'?<><Tag>THE IDEAL MORNING REPORT</Tag><T n={compact?67:66} ink={P.mint} style={{marginTop:34}}>9:00 AM</T>{li('Summary drafted','One page, not a novel',P.mint,0)}{li('3 source links','Original pages included',P.cyan,1)}{li('Uncertainties listed','Check before you trust',P.gold,2)}</>:
 mode==='prompt'?<><Tag ink={P.gold}>A BETTER AGENT PROMPT</Tag><T n={compact?47:50} style={{marginTop:26}}>GIVE IT BOUNDARIES</T>{li('Research 3 sources','Use clear, attributable links',P.cyan,0)}{li('Draft only','Do not email or delete',P.gold,1)}{li('Flag uncertainties','Ask me to review',P.mint,2)}</>:
 mode==='research'?<><Tag ink={P.mint}>WHAT A DOT CAN DO</Tag><T n={compact?50:55} style={{marginTop:29}}>WORK ACROSS TOOLS</T>{li('Explore sources','Research and summarize',P.cyan,0)}{li('Prepare drafts','Documents and presentations',P.gold,1)}{li('Report progress','Results for you to review',P.mint,2)}</>:
 mode==='permissions'?<><Tag ink={P.gold}>THE SAFETY CHECK</Tag><T n={compact?48:52} style={{marginTop:28}}>NOT UNLIMITED ACCESS</T>{li('Connect only needed apps','Permission is scoped',P.mint,0)}{li('Review sensitive actions','Approvals may be required',P.gold,1)}{li('Keep passwords private','Sensitive actions need takeover',P.red,2)}</>:
 mode==='plans'?<><Tag ink={P.gold}>ROLLING OUT · CHECK ELIGIBILITY</Tag><T n={compact?52:57} style={{marginTop:25}}>NOT ON EVERY PLAN</T>{li('Pro','Eligible regions; gradual rollout',P.cyan,0)}{li('Business Premium','Available in supported regions',P.mint,1)}{li('Enterprise beta','Admin must enable access',P.gold,2)}<T n={compact?26:26} ink={P.red} style={{marginTop:23}}>Standard Plus is not listed in the rollout.</T></>:
 mode==='compare'?<><Tag>WHICH TOOL DO YOU NEED?</Tag><T n={compact?54:60} style={{marginTop:26}}>AGENT vs REMINDER</T>{li('REMINDER','Sends a scheduled nudge',P.gold,0)}{li('DOT','Can work toward a task result',P.cyan,1)}{li('REVIEW','Check source and permission choices',P.mint,2)}</>:
 <><Tag ink={P.gold}>YOUR CHOICE</Tag><T n={compact?54:58} style={{marginTop:43}}>{mode==='vote1'?'TRUST IT OVERNIGHT?':mode==='vote2'?'EMAIL OR TO-DO?':'WHAT WOULD YOU DELEGATE?'}</T><div style={{display:'flex',gap:12,marginTop:48}}>{(mode==='vote1'?['YES','NOT YET']:mode==='vote2'?['EMAIL','TO-DO']:['RESEARCH','EMAIL','SLIDES']).map((s,i)=><div key={s} style={{flex:1,minWidth:0,textAlign:'center',border:'2px solid '+(i%2?P.gold:P.mint),borderRadius:13,padding:compact?'30px 4px':'38px 8px'}}><T n={mode==='vote3'?(compact?23:25):(compact?29:32)} ink={i%2?P.gold:P.mint}>{s}</T></div>)}</div><T n={compact?27:32} ink={P.cyan} style={{marginTop:52,textAlign:'center'}}>COMMENT YOUR PICK ↓</T></>}
 </Panel>;
};
type Beat={a:number;b:number;tag:string;head:string;sub:string;mode:Mode};
const shortA:Beat[]=[
{a:0,b:.23,tag:'YOUR WORK ISN’T DONE',head:'11 PM. STILL WORKING?',sub:'What if an AI kept going?',mode:'clock'},
{a:.23,b:.49,tag:'MEET THE ALWAYS-ON AGENT',head:'RESEARCH OVERNIGHT?',sub:'Drafts, sources, follow-up questions.',mode:'research'},
{a:.49,b:.74,tag:'CONTROL MATTERS',head:'NOT A FREE PASS.',sub:'Permissions and approvals still apply.',mode:'permissions'},
{a:.74,b:1,tag:'YOUR CALL',head:'YES OR NOT YET?',sub:'Would you trust an overnight draft?',mode:'vote1'}
];
const shortB:Beat[]=[
{a:0,b:.24,tag:'THE ACCESS CATCH',head:'CAN YOU GET DOTS?',sub:'Not on every ChatGPT plan.',mode:'plans'},
{a:.24,b:.50,tag:'PLAN DETAILS',head:'PRO / BUSINESS',sub:'Enterprise requires beta approval.',mode:'plans'},
{a:.50,b:.77,tag:'WHAT IT CAN ACCESS',head:'CHECK PERMISSIONS',sub:'Connected apps are not unlimited access.',mode:'permissions'},
{a:.77,b:1,tag:'PICK YOUR FIRST TASK',head:'EMAIL OR TO-DO?',sub:'Start with the lowest risk.',mode:'vote2'}
];
const Short:React.FC<{kind:'a'|'b'}>=({kind})=>{
const f=useCurrentFrame(),{durationInFrames:all}=useVideoConfig(),t=f/all,beats=kind==='a'?shortA:shortB,b=beats.find(x=>t>=x.a&&t<x.b)||beats[beats.length-1],alpha=cap((f-b.a*all)/13);
return <AbsoluteFill><Bg f={f}/><div style={{position:'absolute',top:78,left:64}}><Brand/></div><div style={{position:'absolute',top:201,left:64,right:64,opacity:alpha,transform:'translateY('+((1-alpha)*26)+'px)'}}><Tag ink={P.gold}>{b.tag}</Tag><T n={75} style={{marginTop:20}}>{b.head}</T><T n={34} ink={P.muted} style={{marginTop:17}}>{b.sub}</T></div>
<div style={{position:'absolute',left:64,right:64,top:635,height:755,opacity:alpha}}><DotCard mode={b.mode} f={f} compact/></div>
<div style={{position:'absolute',left:65,right:65,top:1520,padding:20,background:'#0A3349',borderLeft:'7px solid '+P.cyan}}><T n={24}>Illustrative workflow · No actual dot was tested</T></div>
<div style={{position:'absolute',bottom:93,left:64,right:64}}><Tag ink={P.muted}>OPENAI PRODUCT SOURCES · FLOWMINUTE ORIGINAL ANIMATION</Tag></div>
<div style={{position:'absolute',bottom:0,left:0,height:8,width:(100*t)+'%',background:P.cyan}}/><Audio src={staticFile(kind==='a'?'oct18-v27.mp3':'oct18-v28.mp3')}/></AbsoluteFill>
};
export const DotsWorkShort:React.FC=()=> <Short kind='a'/>;
export const DotsAccessShort:React.FC=()=> <Short kind='b'/>;
const longBeats:Beat[]=[
 {a:0,b:.125,tag:'THE NIGHT BEFORE A DEADLINE',head:'11 PM. STILL UNFINISHED?',sub:'An agent could keep working. But should it?',mode:'clock'},
 {a:.125,b:.255,tag:'THE IDEAL RESULT',head:'WAKE UP TO A DRAFT',sub:'Sources, uncertainty, next actions — not magic.',mode:'brief'},
 {a:.255,b:.405,tag:'TELL IT EXACTLY WHAT TO DO',head:'BOUNDARIES MAKE IT BETTER',sub:'Three sources. Draft only. Ask before sharing.',mode:'prompt'},
 {a:.405,b:.545,tag:'WHAT OPENAI ANNOUNCED',head:'AN ALWAYS-ON DOT',sub:'Its own cloud computer and approved app connections.',mode:'research'},
 {a:.545,b:.695,tag:'DON’T SKIP THE SAFETY',head:'PERMISSIONS FIRST.',sub:'Scope app access. Review sensitive actions.',mode:'permissions'},
 {a:.695,b:.815,tag:'THE ACCESS CATCH',head:'NOT EVERY PLAN.',sub:'Pro and Business Premium rollout; Enterprise beta.',mode:'plans'},
 {a:.815,b:.925,tag:'CHOOSE THE RIGHT TOOL',head:'AGENT vs REMINDER',sub:'One nudges you; the other works on a task.',mode:'compare'},
 {a:.925,b:1,tag:'YOUR TURN',head:'RESEARCH, EMAIL OR SLIDES?',sub:'What would you delegate first?',mode:'vote3'}
];
export const DotsNightLong:React.FC=()=>{
 const f=useCurrentFrame(),{durationInFrames:all}=useVideoConfig(),t=f/all,b=longBeats.find(x=>t>=x.a&&t<x.b)||longBeats[longBeats.length-1],alpha=cap((f-b.a*all)/14);
 return <AbsoluteFill><Bg f={f}/><div style={{position:'absolute',top:58,left:92,right:92,display:'flex',justifyContent:'space-between'}}><Brand/><Tag ink={P.gold}>AI WORKFLOWS · NOT A LIVE PRODUCT DEMO</Tag></div>
 <div style={{position:'absolute',left:94,top:222,width:790,opacity:alpha,transform:'translateY('+((1-alpha)*25)+'px)'}}><Tag ink={P.gold}>{b.tag}</Tag><T n={76} style={{marginTop:27}}>{b.head}</T><T n={34} ink={P.muted} style={{marginTop:28}}>{b.sub}</T><Panel style={{marginTop:65,padding:22,borderLeft:'7px solid '+P.mint}}><T n={26} ink={P.mint}>Simulated example · Check sources and permissions.</T></Panel></div>
 <div style={{position:'absolute',left:955,right:81,top:171,height:743,opacity:alpha}}><DotCard mode={b.mode} f={f}/></div>
 <div style={{position:'absolute',bottom:65,left:91,right:91,display:'flex',justifyContent:'space-between'}}><Tag ink={P.muted}>ILLUSTRATIVE SCENARIOS · NO REAL DOT TASK EXECUTED</Tag><Tag>OpenAI Docs · Sep–Oct 2026</Tag></div>
 <div style={{position:'absolute',bottom:0,height:8,width:(100*t)+'%',background:P.cyan}}/><Audio src={staticFile('oct18-long013.mp3')}/></AbsoluteFill>;
};
export const DotsNightThumbnail:React.FC=()=> <AbsoluteFill><Bg f={0}/>
 <div style={{position:'absolute',left:94,top:73}}><Brand/></div>
 <div style={{position:'absolute',left:94,top:236,width:1150}}>
 <T n={135}>AI WORKS</T><T n={135} ink={P.gold}>WHILE YOU SLEEP?</T>
 <T n={43} ink={P.cyan} style={{marginTop:40}}>OPENAI DOTS · THE REAL CATCH</T>
 <T n={31} ink={P.muted} style={{marginTop:25}}>AUTOMATION, PERMISSIONS & ELIGIBILITY</T></div>
 <div style={{position:'absolute',left:1220,top:197,width:585,height:660,transform:'rotate(-4deg)'}}><DotCard mode='brief' f={60}/></div>
 </AbsoluteFill>;
