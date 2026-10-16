import React from 'react';
import {AbsoluteFill,Audio,Img,staticFile,useCurrentFrame,useVideoConfig,interpolate} from 'remotion';

/** Original editorial visualization, not real hackathon software / official government UI. */
const C={night:'#051523',panel:'#102F45',glass:'#17435D',white:'#F7FCFF',teal:'#7BE6DB',gold:'#FFD07A',muted:'#BACDD7',red:'#FF8E9A',green:'#99EEC1'};
const FONT='Inter,Segoe UI,Arial,sans-serif';
const cap=(n:number)=>Math.max(0,Math.min(1,n));
const TXT:React.FC<{children:React.ReactNode;n?:number;ink?:string;style?:React.CSSProperties}>=({children,n=46,ink=C.white,style})=><div style={{fontFamily:FONT,fontSize:n,fontWeight:880,lineHeight:1.12,letterSpacing:-.5,color:ink,...style}}>{children}</div>;
const TAG:React.FC<{children:React.ReactNode;ink?:string;n?:number}>=({children,ink=C.teal,n=20})=><div style={{fontFamily:FONT,fontSize:n,fontWeight:900,letterSpacing:1.3,color:ink}}>{children}</div>;
const PANEL:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{boxSizing:'border-box',borderRadius:22,border:'2px solid #537F92',boxShadow:'0 18px 65px #0008',background:'linear-gradient(150deg,#1C4A61F7,#0B263DF8)',padding:30,...style}}>{children}</div>;
const BG:React.FC<{f:number;kind?:string}>=({f,kind})=><AbsoluteFill style={{background:C.night}}><Img src={staticFile(kind==='scam'||kind==='truth'?'oct15-phone-still.jpg':kind==='blood'||kind==='visa'?'office-collaboration.jpg':'office-cinematic.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',opacity:.31,filter:'blur(4px) saturate(.65)',transform:'scale('+(1.04+f/23000)+')'}}/><div style={{position:'absolute',inset:0,background:'linear-gradient(130deg,#041523EB,#071D33DD),radial-gradient(circle at 75% 20%,#17506AB0,transparent 63%)'}}/><div style={{position:'absolute',inset:0,opacity:.065,background:'repeating-linear-gradient(0deg,transparent,transparent 80px,#7BE6DB 81px)'}}/></AbsoluteFill>;
const Logo=()=> <TAG>FM / FLOWMINUTE LAB</TAG>;
const Subline:React.FC<{children:React.ReactNode}>=({children})=><TXT n={22} ink={C.muted} style={{marginTop:13}}>{children}</TXT>;
type PanelMode='funnel'|'blood'|'scam'|'visa'|'rules'|'steps'|'truth'|'vote1'|'vote2'|'vote3';
const Step:React.FC<{title:string;detail:string;index:number;active:boolean;compact:boolean}>=({title,detail,index,active,compact})=><div style={{marginTop:compact?13:18,display:'flex',gap:16,padding:compact?'15px 16px':'20px 20px',background:active?'#245B6A':'#0F334A',border:'1px solid #46768A',borderRadius:12,alignItems:'center'}}><div style={{width:40,height:40,borderRadius:22,display:'grid',placeItems:'center',background:active?C.teal:C.gold,color:C.night,fontFamily:FONT,fontWeight:900,fontSize:24}}>{index+1}</div><div style={{flex:1}}><TXT n={compact?26:27}>{title}</TXT><TXT n={compact?20:22} ink={C.muted} style={{marginTop:5}}>{detail}</TXT></div></div>;
const Cases:React.FC<{type:PanelMode;f:number;compact?:boolean}>=({type,f,compact=false})=>{
 const active=Math.floor(f/56)%3,small=compact?26:28,big=compact?50:59;
 let title:string='',subtitle:string='',bullets:[string,string][]=[];
 if(type==='funnel'){title='13,000 REGISTERED';subtitle='Independent AI hackathon · not 13,000 finished apps';bullets=[['13,000','People registered'],['250','Builds shortlisted'],['10','Finalist teams']];}
 if(type==='blood'){title='RAKTKHOJ';subtitle='Prototype idea · not an emergency service';bullets=[['01 • NEED','A clearer blood-bank search'],['02 • OPTIONS','Find potentially relevant locations'],['03 • VERIFY','Confirm with qualified professionals']];}
 if(type==='scam'){title='SAMARTHAN';subtitle='Draft help · not a government filing portal';bullets=[['01 • COLLECT','Organize screenshots and messages'],['02 • CHECK','Verify dates, amounts, and names'],['03 • REPORT','Official portal or call 1930 for fraud']];}
 if(type==='visa'){title='ATITHI';subtitle='A concept for easier visa instructions';bullets=[['01 • START','Explain the process in plain language'],['02 • PHOTO','Clarify document requirements'],['03 • CONFIRM','Check official rules independently']];}
 if(type==='rules'){title='THE REAL LIMITS';subtitle='Prototype is not a government-approved service';bullets=[['NO REAL DATA','Use mock accounts and example records'],['NOT DEPLOYED','No promise of government adoption'],['VERIFY FIRST','Safety and usability before release']];}
 if(type==='steps'){title='HOW TO BUILD ONE';subtitle='One small problem. One complete journey.';bullets=[['FIND THE PAIN','Watch a real user attempt the task'],['BUILD A MOCK','Three screens. Sample data only.'],['TEST IT','Accuracy, accessibility and privacy']];}
 if(type==='truth'){title='DON’T CONFUSE';subtitle='Concepts with official public services';bullets=[['PROTOTYPE','A demonstration for reviewers'],['OFFICIAL','Use the correct government service'],['SECURE','Never give OTPs to unofficial apps']];}
 if(type.startsWith('vote')){title=type==='vote1'?'BLOOD OR VISA?':type==='vote2'?'YES OR NO?':'WHAT WOULD YOU FIX?';subtitle=type==='vote1'?'Which problem should get a redesign?':type==='vote2'?'Would you use AI to prepare a draft?':'One service. One clear improvement.';bullets=type==='vote1'?[['BLOOD','Blood-bank discovery'],['VISA','Simpler document requirements'],['COMMENT','Explain why']]:type==='vote2'?[['YES','As a verified draft only'],['NO','Keep the official system'],['COMMENT','Tell us your reason']]:[['BLOOD BANKS','Find verified options'],['CYBERCRIME','Clear and accurate reporting'],['VISA FORMS','Understand requirements']];}
 return <PANEL style={{height:'100%',padding:compact?24:34}}>
 <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',borderBottom:'1px solid #527F91',paddingBottom:17}}><TAG ink={C.teal}>FLOWMINUTE EXPLAINER</TAG><TAG n={16} ink={C.muted}>ILLUSTRATION</TAG></div>
 <TXT n={big} ink={type==='funnel'?C.gold:C.white} style={{marginTop:26}}>{title}</TXT>
 <Subline>{subtitle}</Subline>
 <div style={{marginTop:compact?20:30}}>
 {bullets.map(([head,detail],i)=><Step key={head} title={head} detail={detail} index={i} active={i===active} compact={compact}/>)}
 </div>
 <TAG n={compact?17:18} ink={type==='scam'||type==='truth'?C.red:C.gold} ><span style={{display:'block',marginTop:compact?25:29}}>{type==='scam'?'OFFICIAL: CYBERCRIME.GOV.IN · FINANCIAL FRAUD: 1930':type==='funnel'?'ORGANIZER REPORTED THE REGISTRATIONS':type.startsWith('vote')?'ANSWER IN THE COMMENTS ↓':'FICTIONAL VISUAL · VERIFY REAL-WORLD CLAIMS'}</span></TAG>
 </PANEL>;
};
type Beat={a:number;b:number;tag:string;head:string;sub:string;mode:PanelMode};
const aBeats:Beat[]=[
{a:0,b:.29,tag:'THE INDIA CHALLENGE',head:'13,000 SIGNED UP!',sub:'To rethink frustrating websites.',mode:'funnel'},
{a:.29,b:.62,tag:'ONE FINALIST IDEA',head:'BLOOD BANK SEARCH?',sub:'RaktKhoj: a prototype concept.',mode:'blood'},
{a:.62,b:.82,tag:'DON’T SKIP THIS',head:'PROTOTYPE ≠ SERVICE',sub:'Professional verification still matters.',mode:'truth'},
{a:.82,b:1,tag:'YOUR IDEA',head:'BLOOD OR VISA?',sub:'Which would you fix?',mode:'vote1'}
];
const bBeats:Beat[]=[
{a:0,b:.27,tag:'THE REAL-WORLD PROBLEM',head:'SCAMMED ONLINE?',sub:'Messages, screenshots, confusing forms.',mode:'scam'},
{a:.27,b:.59,tag:'AN AI PROTOTYPE',head:'DRAFT, DON’T FILE.',sub:'Samarthan explored organizing evidence.',mode:'scam'},
{a:.59,b:.82,tag:'OFFICIAL REPORTING',head:'1930 FOR FRAUD',sub:'Report at cybercrime.gov.in.',mode:'truth'},
{a:.82,b:1,tag:'YOUR VERDICT',head:'YES OR NO?',sub:'Would you use an AI draft?',mode:'vote2'}
];
const Short:React.FC<{kind:'a'|'b'}>=({kind})=>{
 const f=useCurrentFrame(),{durationInFrames:frames}=useVideoConfig(),t=f/frames,bs=kind==='a'?aBeats:bBeats,b=bs.find(x=>t>=x.a&&t<x.b)||bs[bs.length-1],alpha=cap((f-b.a*frames)/12);
 return <AbsoluteFill><BG f={f} kind={b.mode}/>
 <div style={{position:'absolute',left:62,top:76}}><Logo/></div>
 <div style={{position:'absolute',left:62,right:62,top:212,opacity:alpha,transform:'translateY('+((1-alpha)*30)+'px)'}}>
 <TAG ink={C.gold} n={28}>{b.tag}</TAG><TXT n={77} style={{marginTop:21}}>{b.head}</TXT><TXT n={34} ink={C.muted} style={{marginTop:18}}>{b.sub}</TXT></div>
 <div style={{position:'absolute',left:62,right:62,top:636,height:752,opacity:alpha}}><Cases type={b.mode} f={f} compact/></div>
 <div style={{position:'absolute',left:65,right:65,top:1525,background:'#103B52D9',padding:23,borderLeft:'7px solid '+C.teal}}><TXT n={23}>Independent initiative · Concept visuals, not official apps.</TXT></div>
 <div style={{position:'absolute',bottom:86,left:64,right:64}}><TAG n={16} ink={C.muted}>SOURCE: BUILD WHAT MOVES INDIA · FINALISTS REPORTED IN PRESS</TAG></div>
 <div style={{position:'absolute',bottom:0,left:0,width:(100*t)+'%',height:9,background:C.teal}}/><Audio src={staticFile(kind==='a'?'oct19-v29.mp3':'oct19-v30.mp3')}/></AbsoluteFill>;
};
export const IndiaHackathonShort:React.FC=()=> <Short kind='a'/>;
export const IndiaCybercrimeShort:React.FC=()=> <Short kind='b'/>;
const lBeats:Beat[]=[
{a:0,b:.11,tag:'FRUSTRATING ONLINE FORMS',head:'THE PROBLEM ISN’T THE CHATBOT.',sub:'It’s knowing the next step when time matters.',mode:'truth'},
{a:.11,b:.255,tag:'THE REAL HACKATHON',head:'13,000 REGISTERED. 10 FINALISTS.',sub:'Independent Build What Moves India initiative.',mode:'funnel'},
{a:.255,b:.425,tag:'IDEA ONE',head:'RAKTKHOJ: BLOOD-BANK SEARCH',sub:'Guide the citizen. Verify with real professionals.',mode:'blood'},
{a:.425,b:.610,tag:'IDEA TWO',head:'SAMARTHAN: ORGANIZE EVIDENCE',sub:'AI can help draft. Official authorities handle reports.',mode:'scam'},
{a:.610,b:.716,tag:'IDEA THREE',head:'ATITHI: CLEARER VISA FORMS',sub:'Simpler photo and document guidance.',mode:'visa'},
{a:.716,b:.822,tag:'OFFICIAL BUILDER BRIEF',head:'MOCK DATA, REAL USER JOURNEY',sub:'Meaningful use of Codex. No promised adoption.',mode:'rules'},
{a:.822,b:.934,tag:'TRY THE FRAMEWORK',head:'BUILD ONE SMALL USEFUL FLOW',sub:'Discover the problem → draft → verify → test.',mode:'steps'},
{a:.934,b:1,tag:'YOUR CHOICE',head:'WHAT WOULD YOU FIX?',sub:'BLOOD BANKS, CYBERCRIME, or VISA FORMS?',mode:'vote3'}
];
export const IndiaHackathonLong:React.FC=()=>{
 const f=useCurrentFrame(),{durationInFrames:frames}=useVideoConfig(),t=f/frames,b=lBeats.find(x=>t>=x.a&&t<x.b)||lBeats[lBeats.length-1],alpha=cap((f-frames*b.a)/12);
 return <AbsoluteFill><BG f={f} kind={b.mode}/><div style={{position:'absolute',top:56,left:86,right:86,display:'flex',justifyContent:'space-between'}}><Logo/><TAG ink={C.gold}>3 INDIA AI PROTOTYPES · NOT OFFICIAL SERVICES</TAG></div>
 <div style={{position:'absolute',top:211,left:94,width:782,opacity:alpha,transform:'translateY('+((1-alpha)*22)+'px)'}}><TAG ink={C.gold} n={24}>{b.tag}</TAG><TXT n={70} style={{marginTop:28}}>{b.head}</TXT><TXT n={35} ink={C.muted} style={{marginTop:38}}>{b.sub}</TXT><PANEL style={{marginTop:68,padding:22,borderLeft:'7px solid '+C.teal}}><TXT n={26} ink={C.teal}>Original illustrated example · Validate real services.</TXT></PANEL></div>
 <div style={{position:'absolute',top:169,left:934,right:86,height:740,opacity:alpha}}><Cases type={b.mode} f={f}/></div>
 <div style={{position:'absolute',bottom:58,left:88,right:88,display:'flex',justifyContent:'space-between'}}><TAG ink={C.muted} n={17}>NOT ACTUAL PRODUCT FOOTAGE OR GOVERNMENT UI</TAG><TAG n={18}>SOURCE: BUILDER BRIEF + REPORTED FINALISTS</TAG></div>
 <div style={{position:'absolute',bottom:0,left:0,width:(100*t)+'%',height:9,background:C.teal}}/><Audio src={staticFile('oct19-long014.mp3')}/></AbsoluteFill>;
};
export const IndiaHackathonThumbnail:React.FC=()=> <AbsoluteFill><BG f={0}/>
 <div style={{position:'absolute',left:92,top:72}}><Logo/></div>
 <div style={{position:'absolute',left:96,top:210,width:1010}}><TXT n={158} ink={C.gold}>13,000</TXT><TXT n={112}>SIGNED UP</TXT><TXT n={108} ink={C.teal}>TO FIX INDIA?</TXT><TXT n={36} style={{marginTop:29}}>3 AI APP IDEAS THAT MATTER</TXT><TXT n={27} ink={C.muted} style={{marginTop:26}}>OpenAI-partnered hackathon · prototypes</TXT></div>
 <div style={{position:'absolute',left:1160,top:158,width:650,height:755,transform:'rotate(-3deg)'}}><Cases type='funnel' f={90}/></div></AbsoluteFill>;
