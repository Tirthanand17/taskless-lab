import React from 'react';
import {AbsoluteFill,Audio,Img,OffthreadVideo,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';

// Editorial reconstruction. Original layout; never represents a live Meta Muse demo.
const C={bg:'#061521',cyan:'#65F2EB',blue:'#0C3048',white:'#F8FCFF',muted:'#B4CDDE',gold:'#FFCE7D',red:'#FF8197',lime:'#87EFC6'};
const font='Inter, Segoe UI, Arial, sans-serif';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const fade=(f:number,start:number)=>clamp((f-start)/17);
const panel:React.CSSProperties={background:'linear-gradient(145deg,#143950F5,#081D32F6)',border:'2px solid #488599',borderRadius:32,boxShadow:'0 22px 65px #0008'};
const Txt:React.FC<{children:React.ReactNode;size?:number;color?:string;style?:React.CSSProperties}>=({children,size=42,color=C.white,style})=><div style={{fontFamily:font,fontSize:size,color,fontWeight:860,lineHeight:1.11,...style}}>{children}</div>;
const Tiny:React.FC<{children:React.ReactNode;color?:string;size?:number}>=({children,color=C.cyan,size=24})=><div style={{fontFamily:font,fontSize:size,color,letterSpacing:1.1,fontWeight:900}}>{children}</div>;
const Scene:React.FC<{f:number;start:number;children:React.ReactNode;style?:React.CSSProperties}>=({f,start,children,style})=><div style={{opacity:fade(f,start),transform:'translateY('+Math.round((1-fade(f,start))*32)+'px)',...style}}>{children}</div>;
const Bg:React.FC<{f:number;photo?:'office'|'travel'}>=({f,photo='travel'})=><AbsoluteFill style={{background:'radial-gradient(circle at 75% 17%,#2C5A7970,transparent 53%),#061521'}}>
 <Img src={staticFile(photo==='office'?'office-desks.jpg':'office-collaboration.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',opacity:.22,filter:'blur(3px) saturate(.75)',transform:'scale('+(1.05+f/35000)+')'}}/>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(140deg,#061521E9,#09253BD9,#061521E9)'}}/>
 <div style={{position:'absolute',inset:0,opacity:.10,background:'repeating-linear-gradient(0deg,transparent 0px,transparent 59px,#68D7DA 60px),repeating-linear-gradient(90deg,transparent 0px,transparent 59px,#68D7DA 60px)'}}/>
 </AbsoluteFill>;
const Footer:React.FC<{vertical?:boolean}>=({vertical=false})=><div style={{fontSize:vertical?17:17,color:C.muted,fontFamily:font,fontWeight:750,letterSpacing:.3}}>ORIGINAL EXPLANATION · ILLUSTRATIVE UI · NOT A LIVE META DEMO</div>;
const Brand:React.FC=()=> <Tiny>FM  /  FLOWMINUTE LAB</Tiny>;
const Progress:React.FC<{f:number;total:number}>=({f,total})=><div style={{position:'absolute',bottom:0,left:0,right:0,height:7,background:'#315369'}}><div style={{height:'100%',width:100*clamp(f/total)+'%',background:C.cyan}}/></div>;
const Pill:React.FC<{children:React.ReactNode;color?:string}>=({children,color=C.cyan})=><div style={{border:'1.5px solid '+color,color,background:'#103445',padding:'11px 18px',borderRadius:13,fontWeight:900,fontSize:23,display:'inline-block'}}>{children}</div>;
const Stock:React.FC<{kind:'phone'|'laptop';vertical?:boolean}>=({kind,vertical=false})=><div style={{...panel,position:'relative',height:'100%',overflow:'hidden'}}>
 <Img src={staticFile(kind==='phone'?'oct15-phone-still.jpg':'oct15-laptop-still.jpg')} style={{height:'100%',width:'100%',objectFit:'cover',transform:'scale(1.065)'}}/>
 <div style={{position:'absolute',left:20,bottom:20,padding:'11px 16px',background:'#06243CEB',borderRadius:8,fontWeight:850,fontSize:vertical?20:20}}>LICENSED REAL-LIFE STOCK · NOT META FOOTAGE</div>
 </div>;
type CardMode='memory'|'focus'|'access'|'privacy'|'vote'|'trip';
const Sim:React.FC<{mode:CardMode;f:number;vertical?:boolean}>=({mode,f,vertical=false})=>{
 const big=vertical?37:32,small=vertical?27:25;const step=Math.floor(f/40)%3;
 return <div style={{...panel,padding:vertical?32:35,boxSizing:'border-box',height:'100%',overflow:'hidden'}}>
 <div style={{display:'flex',justifyContent:'space-between',borderBottom:'1px solid #4A7185',paddingBottom:22,alignItems:'center'}}>
 <Tiny size={vertical?20:21} color={C.lime}>CONCEPT EXAMPLE</Tiny><Tiny size={vertical?18:18} color={C.muted}>NOT A PRODUCT SCREEN</Tiny></div>
 {mode==='trip'||mode==='memory'?<div>
 <Txt size={vertical?45:40} style={{marginTop:35}}>Weekend travel planner</Txt>
 <div style={{marginTop:34,borderRadius:17,background:'#20475C',padding:24}}><Tiny color={C.muted}>MONDAY · USER NOTES</Tiny>
 {['Budget ₹5,000','Prefer train','Keep the itinerary relaxed'].map((x,i)=><div key={x} style={{borderLeft:'6px solid '+(i===step?C.gold:C.lime),marginTop:15,padding:'9px 18px',background:i===step?'#37606D':'#173B4C',borderRadius:8}}><Txt size={small}>{x}</Txt></div>)}
 </div><div style={{marginTop:33,borderRadius:17,background:'#214E5D',padding:28,border:'1px solid '+C.cyan}}>
 <Tiny>FRIDAY · RELATED CONTEXT</Tiny><Txt size={big} style={{marginTop:18}}>{mode==='memory'?'Bring relevant preferences back':'Can you plan my weekend?'}</Txt></div>
 <Tiny color={C.gold} size={vertical?22:21}><span style={{display:'block',marginTop:25}}>CONCEPTUAL ONLY — NO REAL PERSONAL DATA</span></Tiny>
 </div>:mode==='focus'?<div style={{paddingTop:29}}>
 <Txt size={vertical?48:44}>Build an expense tracker</Txt>
 {['1   Read the request','2   First approach failed','3   Try another path','4   Check before action'].map((x,i)=><div key={x} style={{background:step===i%3?'#275967':'#14394E',border:'1px solid #427E90',borderRadius:14,marginTop:22,padding:'23px 25px',display:'flex',gap:15,alignItems:'center'}}>
 <Txt size={small} color={i===1?C.red:i===3?C.gold:C.white}>{x}</Txt></div>)}
 <Tiny color={C.gold}><span style={{display:'block',marginTop:25}}>ILLUSTRATIVE TASK, NOT A LIVE TEST</span></Tiny>
 </div>:mode==='access'?<div style={{paddingTop:35}}>
 <Txt size={vertical?52:48}>WHO GETS WHAT?</Txt>
 {[['MUSE WONDER','Meta Model API + Muse Code',C.cyan],['WONDER FULL','Muse Code subscribers',C.gold],['MUSE PERSONAL AGENT','Wonder integration coming later',C.lime]].map(([name,desc,color],i)=><div key={name} style={{marginTop:27,padding:'27px 22px',border:'2px solid '+color,borderRadius:17,background:'#183D52'}}>
 <Tiny size={vertical?28:25} color={color}>{name}</Tiny><Txt size={small} style={{marginTop:12}}>{desc}</Txt></div>)}
 </div>:mode==='privacy'?<div style={{paddingTop:37}}>
 <Txt size={vertical?53:45}>MEMORY NEEDS CONTROL</Txt>
 {['What does it remember?','Can I correct outdated details?','What information can it access?'].map((q,i)=><div key={q} style={{marginTop:31,padding:27,borderRadius:16,border:'1px solid #51879B',background:i===step?'#245F69':'#163E51'}}><Txt size={small}>{i+1}. {q}</Txt></div>)}
 <Tiny color={C.gold}><span style={{display:'block',marginTop:27}}>NO PASSWORDS OR PRIVATE FINANCIAL SECRETS</span></Tiny>
 </div>:<div style={{paddingTop:45,textAlign:'center'}}>
 <Txt size={vertical?66:67}>WHICH ONE?</Txt><div style={{display:'flex',gap:14,marginTop:56}}>
 {['MEMORY','FOCUS'].map((q,i)=><div key={q} style={{flex:1,padding:vertical?'33px 8px':'43px 9px',borderRadius:17,background:i===step%2?'#285F6C':'#133B53',border:'2px solid '+(i?C.gold:C.cyan)}}><Txt size={vertical?32:38} color={i?C.gold:C.cyan}>{q}</Txt></div>)}
 </div><Txt size={vertical?40:35} color={C.lime} style={{marginTop:60}}>TELL US IN THE COMMENTS ↓</Txt>
 </div>}
 </div>;
};
type ShortBeat={a:number;b:number;tag:string;head:string;sub:string;view:CardMode};
const memory:ShortBeat[]=[
 {a:0,b:.17,tag:'NEW META AI · OCT 12',head:'AI REMEMBERS YOU?',sub:'Does it know what you said last week?',view:'trip'},
 {a:.17,b:.50,tag:'MUSE WONDER',head:'ACTIVE MEMORY',sub:'Bring relevant context across conversations.',view:'memory'},
 {a:.50,b:.75,tag:'IMPORTANT LIMIT',head:'NOT IN EVERY CHAT TODAY',sub:'Wider Muse rollout comes later.',view:'access'},
 {a:.75,b:1,tag:'YOUR CHOICE',head:'WOULD YOU ENABLE IT?',sub:'COMMENT YES OR NO ↓',view:'vote'}
];
const access:ShortBeat[]=[
 {a:0,b:.17,tag:'TWO NEW META MODELS',head:'WHO CAN USE THEM?',sub:'Not everyone gets the same access.',view:'access'},
 {a:.17,b:.48,tag:'WONDER VS WONDER FULL',head:'BUILDERS FIRST',sub:'API and Muse Code vs subscribers.',view:'access'},
 {a:.48,b:.73,tag:'THE ROLLOUT CATCH',head:'MUSE APP LATER',sub:'Do not assume it is in Instagram or WhatsApp.',view:'access'},
 {a:.73,b:1,tag:'WHICH MATTERS MORE?',head:'MEMORY OR FOCUS?',sub:'COMMENT YOUR PICK ↓',view:'vote'}
];
const Short:React.FC<{which:21|22}>=({which})=>{
 const f=useCurrentFrame(),{durationInFrames:total}=useVideoConfig(),t=f/total,all=which===21?memory:access,beat=all.find(x=>t>=x.a&&t<x.b)||all[all.length-1],start=Math.round(total*beat.a);
 return <AbsoluteFill style={{fontFamily:font,color:C.white}}><Bg f={f}/>
 <div style={{position:'absolute',top:78,left:69}}><Brand/></div>
 <Scene f={f} start={start} style={{position:'absolute',top:200,left:69,right:69}}>
 <Tiny size={26} color={C.gold}>{beat.tag}</Tiny><Txt size={78} style={{marginTop:19,letterSpacing:-2}}>{beat.head}</Txt><Txt color={C.muted} size={35} style={{marginTop:23}}>{beat.sub}</Txt>
 </Scene>
 <Scene f={f} start={start+6} style={{position:'absolute',left:64,right:64,top:670,height:660}}>
 {t<.11?<Stock kind="phone" vertical/>:<Sim mode={beat.view} f={f} vertical/>}</Scene>
 <div style={{position:'absolute',top:1438,left:66,right:66,background:'#0A2C40EA',padding:29,borderLeft:'6px solid '+C.cyan}}>
 <Txt size={28} color={C.cyan}>{which===21?'ACTIVE MEMORY IS A MODEL CAPABILITY — NOT A LIVE DEMO':'WONDER FULL ≠ FREE FOR EVERYONE'}</Txt>
 <Txt size={23} color={C.muted} style={{marginTop:14}}>Source: Meta, October 12, 2026</Txt></div>
 <div style={{position:'absolute',left:70,bottom:91,right:70}}><Footer vertical/></div>
 <Progress f={f} total={total}/><Audio src={staticFile(which===21?'oct15-v21.mp3':'oct15-v22.mp3')}/></AbsoluteFill>
};
type LongBeat={a:number;b:number;tag:string;head:string;sub:string;view:CardMode;stock?:boolean};
const long:LongBeat[]=[
 {a:0,b:.095,tag:'HYPOTHETICAL SCENARIO',head:'WHAT IF AI REMEMBERED?',sub:'Your trip preferences from last week… without typing them again.',view:'trip',stock:true},
 {a:.095,b:.20,tag:'META · OCTOBER 12',head:'TWO NEW AI MODELS',sub:'Muse Wonder and Muse Wonder Full. Different access, different claims.',view:'access'},
 {a:.20,b:.365,tag:'CAPABILITY 01 · CONTEXT',head:'ACTIVE MEMORY',sub:'Relevant preferences across conversations — according to Meta.',view:'memory'},
 {a:.365,b:.485,tag:'THE HUMAN QUESTION',head:'WHAT SHOULD IT REMEMBER?',sub:'Stored details can be wrong, outdated, or too personal.',view:'privacy'},
 {a:.485,b:.675,tag:'CAPABILITY 02 · CONTINUITY',head:'ACTIVE FOCUS',sub:'Recover from errors, retry different approaches, ask when necessary.',view:'focus'},
 {a:.675,b:.84,tag:'AVAILABILITY CHECK',head:'WHO CAN USE IT TODAY?',sub:'Meta Model API, Muse Code and subscriber tiers. Muse app rollout later.',view:'access'},
 {a:.84,b:.92,tag:'OUR TAKEAWAY',head:'CONTROL MATTERS',sub:'Never confuse launch claims with a verified independent test.',view:'privacy'},
 {a:.92,b:1,tag:'YOUR TURN',head:'MEMORY OR FOCUS?',sub:'Which one would actually help you? Comment your answer.',view:'vote'}
];
export const MuseMemoryShort:React.FC=()=> <Short which={21}/>;
export const MuseAccessShort:React.FC=()=> <Short which={22}/>;
export const MuseWonderLong:React.FC=()=>{
 const f=useCurrentFrame(),{durationInFrames:total}=useVideoConfig(),t=f/total,beat=long.find(x=>t>=x.a&&t<x.b)||long[long.length-1],start=Math.round(total*beat.a);
 return <AbsoluteFill style={{fontFamily:font,color:C.white}}><Bg f={f} photo={beat.view==='focus'?'office':'travel'}/>
 <div style={{position:'absolute',top:47,left:83,right:83,display:'flex',justifyContent:'space-between'}}><Brand/><Tiny size={22} color={C.gold}>META MUSE WONDER · EXPLAINED</Tiny></div>
 <Scene f={f} start={start} style={{position:'absolute',left:90,top:198,width:775}}>
 <Tiny color={C.gold}>{beat.tag}</Tiny><Txt size={74} style={{marginTop:25,letterSpacing:-2}}>{beat.head}</Txt><Txt size={32} color={C.muted} style={{marginTop:32}}>{beat.sub}</Txt>
 <div style={{marginTop:55,border:'1px solid #4D7F87',borderLeft:'8px solid '+C.cyan,background:'#12394CCC',padding:27}}>
 <Txt size={26}>Real-life illustration. No access to a live Muse Wonder account is claimed.</Txt></div>
 </Scene>
 <Scene f={f} start={start+7} style={{position:'absolute',left:952,top:173,right:78,height:740}}>
 {t<.055?<Stock kind="laptop"/>:<Sim mode={beat.view} f={f}/>}
 </Scene>
 <div style={{position:'absolute',left:88,bottom:75,right:88,display:'flex',justifyContent:'space-between'}}>
 <Footer/><Tiny size={18}>SOURCE: META NEWSROOM · OCT 12 2026</Tiny></div>
 <Progress f={f} total={total}/><Audio src={staticFile('oct15-long010.mp3')}/></AbsoluteFill>
};
export const MuseWonderThumbnail:React.FC=()=> <AbsoluteFill style={{fontFamily:font,color:C.white}}><Bg f={0}/>
 <div style={{position:'absolute',top:78,left:100}}><Brand/></div>
 <div style={{position:'absolute',left:95,top:205,width:1050}}>
 <Txt size={143} style={{letterSpacing:-5}}>AI KNOWS</Txt><Txt size={146} color={C.gold} style={{letterSpacing:-5}}>YOUR PAST?</Txt>
 <Txt size={42} color={C.cyan} style={{marginTop:40}}>META MUSE WONDER</Txt>
 <Txt size={29} color={C.muted} style={{marginTop:30}}>MEMORY + FOCUS · ACCESS EXPLAINED</Txt></div>
 <div style={{position:'absolute',right:70,top:175,width:665,height:745,transform:'rotate(-4deg)'}}><Sim mode="memory" f={120}/></div>
 </AbsoluteFill>;
