import React from 'react';
import {AbsoluteFill,Audio,Img,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
// Demonstrative original reconstruction, not a product screen capture.
const P={dark:'#061827',panel:'#0B3448',cyan:'#55E5E5',gold:'#FFD18A',white:'#F9FCFE',mute:'#B7D0DF',green:'#89EEBA'};
const font='Inter,Segoe UI,Arial,sans-serif';
const clamp=(v:number)=>Math.min(1,Math.max(0,v));
const Head:React.FC<{children:React.ReactNode;n?:number;color?:string;style?:React.CSSProperties}>=({children,n=48,color=P.white,style})=><div style={{fontFamily:font,fontSize:n,fontWeight:900,color,lineHeight:1.13,...style}}>{children}</div>;
const Small:React.FC<{children:React.ReactNode;color?:string}>=({children,color=P.cyan})=><div style={{fontFamily:font,fontSize:23,fontWeight:800,color,letterSpacing:.6}}>{children}</div>;
const Bg:React.FC<{f:number}>=({f})=><AbsoluteFill style={{background:'radial-gradient(circle at 72% 12%,#2A7D8C40,transparent 50%),#061827'}}>
 <Img src={staticFile('office-desks.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',opacity:.14,filter:'blur(3px)',transform:'scale('+(1.055+f/32000)+')'}}/>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(120deg,#051624E8,#06273FE1)'}}/>
</AbsoluteFill>;
const Brand=()=> <Small>FM  /  FLOWMINUTE LAB</Small>;
const Panel:React.FC<{children:React.ReactNode}>=({children})=><div style={{height:'100%',boxSizing:'border-box',border:'2px solid #4F8493',background:'#0E3348F7',padding:27,borderRadius:25,boxShadow:'0 20px 60px #0007',overflow:'hidden'}}>{children}</div>;
const Label:React.FC<{children:React.ReactNode}>=({children})=><div style={{fontSize:18,color:P.green,fontWeight:850,letterSpacing:.7,fontFamily:font}}>{children}</div>;
type Mode='sheet'|'doc'|'slides'|'access'|'setup'|'vote';
const Demo:React.FC<{mode:Mode;frame:number;vertical?:boolean}>=({mode,frame,vertical=false})=>{
 const n=vertical?32:29;
 return <Panel><div style={{display:'flex',justifyContent:'space-between',borderBottom:'1px solid #578190',paddingBottom:17,marginBottom:27}}>
 <Small color={P.green}>CONCEPT FILE · NOT LIVE CLAUDE</Small><Small color={P.mute}>CLAUDE SIDEBAR · ILLUSTRATIVE</Small>
 </div>
 {mode==='sheet'?<><Head n={n+14}>SALES TRACKER</Head><div style={{marginTop:22,display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:4}}>
 {['ID','SALES','LOOKUP','101','₹750','#N/A','102','₹540','540','103','₹820','#N/A'].map((v,i)=><div key={i} style={{padding:'16px 5px',background:i>2&&i%3===2?'#873D4C':'#245266',fontSize:vertical?25:23,color:'#FFF',fontWeight:850,textAlign:'center',border:'1px solid #6292A3'}}>{v}</div>)}
 </div><div style={{marginTop:27,borderLeft:'6px solid '+P.gold,padding:'17px 20px',background:'#18475A'}}><Head n={n}>WHY DOES VLOOKUP FAIL?</Head><Head n={vertical?23:22} color={P.mute} style={{marginTop:13}}>Check whether IDs are text or numbers.</Head></div></>
 :mode==='doc'?<><Head n={n+12}>THE 12-PAGE PROPOSAL</Head><div style={{background:'#EFF6F8',borderRadius:11,padding:22,marginTop:22}}>
 <Head n={n-6} color='#17384A'>Project overview</Head>{Array.from({length:6},(_,i)=><div key={i} style={{height:13,width:(90-i*8)+'%',marginTop:17,background:'#BDD5DF',borderRadius:3}}/>)}
 </div><div style={{marginTop:31,background:'#265C63',padding:20,borderRadius:11}}><Head n={n}>KEEP REQUIREMENTS.</Head><Head n={n} color={P.green}>REMOVE REPETITION.</Head></div></>
 :mode==='slides'?<><Head n={n+12}>16 BULLETS ON ONE SLIDE?</Head><div style={{display:'flex',gap:17,marginTop:26}}>
 {[0,1].map((i)=><div key={i} style={{flex:1,minHeight:245,padding:15,borderRadius:12,background:i?'#285B64':'#485C65',border:'2px solid #85B0B4'}}>
 <Head n={vertical?27:25}>{i?'CLEARER STORY':'TEXT WALL'}</Head>{Array.from({length:i?3:9},(_,j)=><div key={j} style={{height:11,width:(78+(j%3)*6)+'%',background:i?'#9AE8CB':'#B2B9C4',marginTop:i?24:12}}/>)}</div>)}
 </div><Head n={vertical?24:23} color={P.gold} style={{marginTop:25}}>Generated charts are images, not live links.</Head></>
 :mode==='access'||mode==='setup'?<><Head n={n+12}>{mode==='access'?'WHO CAN USE IT?':'SETUP IN 3 STEPS'}</Head>
 {(mode==='access'?['Pro / Max','Team / Enterprise','Marketplace permission needed']:['1. Marketplace install','2. Extensions → Claude','3. Ask before edits']).map((v,i)=><div key={i} style={{padding:'23px 22px',border:'1px solid #538B99',background:i===Math.floor(frame/48)%3?'#275F6B':'#16445B',borderRadius:14,marginTop:20}}><Head n={n}>{v}</Head></div>)}
 <Head n={vertical?23:21} color={P.mute} style={{marginTop:29}}>Beta. Your account and admin rules matter.</Head></>
 :<><Head n={vertical?57:60}>WHICH HELPS YOU?</Head><div style={{display:'flex',gap:20,marginTop:54}}>{['SHEETS','DOCS'].map((v,i)=><div key={v} style={{flex:1,padding:'35px 10px',border:'2px solid '+(i?P.gold:P.green),borderRadius:12,textAlign:'center'}}><Head n={vertical?29:34} color={i?P.gold:P.green}>{v}</Head></div>)}</div><Head n={n} color={P.cyan} style={{textAlign:'center',marginTop:40}}>COMMENT BELOW ↓</Head></>}
 </Panel>
};
type Beat={from:number;to:number;mode:Mode;tag:string;title:string;sub:string};
const shortSheet:Beat[]=[
 {from:0,to:.15,mode:'sheet',tag:'GOOGLE SHEETS PAIN',title:'WHY #N/A?',sub:'Ask Claude to explain the formula.'},
 {from:.15,to:.47,mode:'sheet',tag:'THE ACTUAL PROBLEM',title:'TEXT VS NUMBER',sub:'Check the IDs. Verify the result.'},
 {from:.47,to:.74,mode:'access',tag:'THE PAID CATCH',title:'CLAUDE BETA',sub:'Pro, Max, Team, Enterprise.'},
 {from:.74,to:1,mode:'vote',tag:'YOUR CALL',title:'SHEETS OR DOCS?',sub:'COMMENT YOUR PICK.'}
];
const shortAccess:Beat[]=[
 {from:0,to:.17,mode:'access',tag:'NEW CLAUDE ADD-ON',title:'IS IT FREE?',sub:'Not for every account.'},
 {from:.17,to:.43,mode:'setup',tag:'GET STARTED',title:'EXTENSIONS → CLAUDE',sub:'Install officially, then sign in.'},
 {from:.43,to:.72,mode:'setup',tag:'SAFETY',title:'ASK BEFORE EDITS',sub:'Review every proposed change.'},
 {from:.72,to:1,mode:'vote',tag:'YOUR CHOICE',title:'ASK OR AUTO?',sub:'WHAT WOULD YOU SELECT?'}
];
const Short:React.FC<{type:23|24}>=({type})=>{
 const frame=useCurrentFrame(),{durationInFrames:total}=useVideoConfig(),t=frame/total;
 const beats=type===23?shortSheet:shortAccess,beat=beats.find(b=>t>=b.from&&t<b.to)||beats[beats.length-1],fade=clamp((frame-total*beat.from)/18);
 return <AbsoluteFill style={{fontFamily:font,color:P.white}}><Bg f={frame}/>
 <div style={{position:'absolute',top:82,left:66}}><Brand/></div>
 <div style={{position:'absolute',top:200,left:68,right:68,opacity:fade,transform:'translateY('+((1-fade)*35)+'px)'}}>
 <Small color={P.gold}>{beat.tag}</Small><Head n={76} style={{marginTop:24,letterSpacing:-2}}>{beat.title}</Head><Head n={35} color={P.mute} style={{marginTop:23}}>{beat.sub}</Head></div>
 <div style={{position:'absolute',left:64,right:64,top:675,height:700,opacity:fade}}><Demo mode={beat.mode} frame={frame} vertical/></div>
 <div style={{position:'absolute',left:68,right:68,top:1505,padding:23,borderLeft:'7px solid '+P.gold,background:'#08283FDE'}}><Head n={27}>REAL PRODUCT FEATURES · ILLUSTRATIVE VIDEO</Head><Small color={P.mute}>Source: Anthropic, Oct 2026</Small></div>
 <div style={{position:'absolute',bottom:103,left:68,right:68}}><Small color={P.mute}>FM · Original educational explainer</Small></div>
 <div style={{position:'absolute',bottom:0,height:8,background:P.cyan,width:100*t+'%'}}/>
 <Audio src={staticFile(type===23?'oct16-v23.mp3':'oct16-v24.mp3')}/></AbsoluteFill>
};
const longBeats:Beat[]=[
 {from:0,to:.12,mode:'sheet',tag:'ONE PROBLEM · THREE FILES',title:'CAN AI FIX THIS?',sub:'A broken spreadsheet and two unfinished documents.'},
 {from:.12,to:.30,mode:'sheet',tag:'TRICK 1 · SHEETS',title:'WHY VLOOKUP FAILS',sub:'Check real data types. Never blindly trust a fix.'},
 {from:.30,to:.46,mode:'doc',tag:'TRICK 2 · DOCS',title:'SHORTER, CLEARER REPORTS',sub:'Keep numbered requirements. Remove repeated paragraphs.'},
 {from:.46,to:.61,mode:'slides',tag:'TRICK 3 · SLIDES',title:'REBUILD THE TEXT WALL',sub:'Divide dense slides. Generated charts do not auto-refresh.'},
 {from:.61,to:.76,mode:'access',tag:'THE ACCESS CATCH',title:'PAID BETA',sub:'Pro, Max, Team, Enterprise. Google admins may block installation.'},
 {from:.76,to:.90,mode:'setup',tag:'APPROVALS & CONTROL',title:'ASK BEFORE EDITS',sub:'Review changes; recover using Google version history.'},
 {from:.90,to:1,mode:'vote',tag:'YOUR CHOICE',title:'SHEETS OR DOCS?',sub:'Which would make your work easier? Comment below.'}
];
export const ClaudeSheetsShort:React.FC=()=> <Short type={23}/>;
export const ClaudeAccessShort:React.FC=()=> <Short type={24}/>;
export const ClaudeWorkspaceLong:React.FC=()=>{
 const frame=useCurrentFrame(),{durationInFrames:total}=useVideoConfig(),t=frame/total;
 const beat=longBeats.find(b=>t>=b.from&&t<b.to)||longBeats[longBeats.length-1],fade=clamp((frame-total*beat.from)/18);
 return <AbsoluteFill style={{fontFamily:font,color:P.white}}><Bg f={frame}/>
 <div style={{position:'absolute',left:88,top:52,right:88,display:'flex',justifyContent:'space-between'}}><Brand/><Small color={P.gold}>CLAUDE IN GOOGLE WORKSPACE</Small></div>
 <div style={{position:'absolute',left:91,top:206,width:795,opacity:fade,transform:'translateY('+((1-fade)*30)+'px)'}}><Small color={P.gold}>{beat.tag}</Small><Head n={78} style={{marginTop:22}}>{beat.title}</Head><Head n={34} color={P.mute} style={{marginTop:28}}>{beat.sub}</Head>
 <div style={{marginTop:50,padding:25,background:'#134257D9',borderLeft:'8px solid '+P.cyan}}><Head n={28}>Illustration only. No live account or file edits shown.</Head></div>
 </div>
 <div style={{position:'absolute',left:942,right:85,top:175,height:740,opacity:fade}}><Demo mode={beat.mode} frame={frame}/></div>
 <div style={{position:'absolute',bottom:70,left:88,right:88,display:'flex',justifyContent:'space-between'}}><Small color={P.mute}>ORIGINAL SIMULATION · NOT AN ACTUAL PRODUCT RECORDING</Small><Small>Official Anthropic help · October 2026</Small></div>
 <div style={{position:'absolute',bottom:0,height:8,background:P.cyan,width:100*t+'%'}}/><Audio src={staticFile('oct16-long011.mp3')}/></AbsoluteFill>
};
export const ClaudeWorkspaceThumbnail:React.FC=()=> <AbsoluteFill style={{fontFamily:font}}><Bg f={0}/>
 <div style={{position:'absolute',top:90,left:100}}><Brand/></div>
 <div style={{position:'absolute',top:245,left:100,width:1060}}>
 <Head n={139}>FIX GOOGLE</Head><Head n={135} color={P.gold}>SHEETS WITH AI?</Head><Head n={43} color={P.cyan} style={{marginTop:37}}>CLAUDE · DOCS · SHEETS · SLIDES</Head>
 <Head n={32} color={P.mute} style={{marginTop:27}}>3 USE CASES + PAID ACCESS CATCH</Head></div>
 <div style={{position:'absolute',top:190,left:1110,width:710,height:680,transform:'rotate(-4deg)'}}><Demo mode='sheet' frame={0}/></div>
 </AbsoluteFill>;
