import React from 'react';
import {AbsoluteFill, Audio, Easing, interpolate, staticFile, useCurrentFrame} from 'remotion';

// All app screens in this package are fictional workflow reconstructions.
// They are NOT screenshots or recordings of the Gemini agent product.
const C={bg:'#080e1b',bg2:'#14253b',paper:'#f6f9fc',cyan:'#4ce6d6',orange:'#ffbd66',violet:'#987cff',ink:'#17253b',muted:'#7290ac',red:'#ff6478',green:'#5ce7a9'};
const font='Inter,Segoe UI,Arial,sans-serif';
const anim=(f:number,start:number,end:number)=>interpolate(f,[start,end],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(0.21,0.75,0.20,1)});
const Zoom:React.FC<{f:number,start?:number;children:React.ReactNode;style?:React.CSSProperties}>=({f,start=0,children,style={}})=>{const p=anim(f,start,start+23);return <div style={{opacity:p,transform:`translateY(${(1-p)*34}px) scale(${0.975+p*.025})`,...style}}>{children}</div>};
const Glow:React.FC=()=> <><div style={{position:'absolute',top:-300,left:-290,width:970,height:970,borderRadius:'50%',background:'radial-gradient(circle,rgba(73,229,212,.21),transparent 69%)'}}/><div style={{position:'absolute',right:-270,bottom:-260,width:1050,height:1050,borderRadius:'50%',background:'radial-gradient(circle,rgba(139,101,255,.17),transparent 70%)'}}/><div style={{position:'absolute',inset:0,opacity:.15,background:'repeating-linear-gradient(110deg, transparent 0px, transparent 70px, rgba(255,255,255,.11) 71px, transparent 72px)'}}/></>;
const Tag:React.FC<{children:React.ReactNode;color?:string;small?:boolean}>=({children,color=C.cyan,small=false})=><span style={{display:'inline-block',color,background:color+'17',padding:small?'9px 17px':'12px 22px',border:`1px solid ${color}60`,borderRadius:30,fontWeight:800,letterSpacing:1.5,fontSize:small?16:22,textTransform:'uppercase'}}>{children}</span>;
const Pill:React.FC<{children:React.ReactNode;mode?:'green'|'orange'|'red'}>=({children,mode='green'})=><span style={{borderRadius:100,padding:'10px 17px',fontWeight:850,fontSize:20,color:mode==='red'?C.red:mode==='orange'?C.orange:C.green,background:'rgba(16,38,55,.94)'}}>{children}</span>;
const Panel:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{background:'linear-gradient(160deg,#fff,#edf3f8)',border:'1px solid #b5cce0',borderRadius:26,boxShadow:'0 28px 65px rgba(0,0,0,.32)',color:C.ink,overflow:'hidden',...style}}>{children}</div>;
const Workflow:React.FC<{vertical?:boolean;mode:'mail'|'sheet'|'report'|'danger'|'security';phase?:number}>=({vertical=false,mode,phase=0})=>{
 const mini=vertical,head=mini?26:27,body=mini?28:30,big=mini?52:61;
 const base:React.CSSProperties={padding:mini?'28px 30px':'35px 44px',height:'100%',boxSizing:'border-box',fontFamily:font};
 const header=(label:string,extra:string)=><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:15,paddingBottom:25,borderBottom:'1px solid #d7e3ee',fontSize:head,fontWeight:850}}><span>{label}</span><span style={{fontSize:mini?15:18,color:C.muted,fontWeight:700}}>{extra}</span></div>;
 if(mode==='mail')return <div style={base}>{header('✉ Project inbox','FICTIONAL DEMO')}
 <div style={{marginTop:25,color:C.muted,fontSize:21}}>New message · Customer support</div>
 <div style={{fontWeight:900,fontSize:big,letterSpacing:-1.5,marginTop:12}}>Order delayed?</div>
 <div style={{fontSize:body,marginTop:16,lineHeight:1.35}}>“Could you check the delivery date for order ORD-028?”</div>
 <div style={{marginTop:26,padding:'23px 27px',background:'#e9f6f1',border:'1px solid #bddfd0',borderRadius:16,fontSize:body}}>✓ Read order data <span style={{float:'right',fontWeight:900}}>Oct 14</span></div>
 <div style={{marginTop:21,padding:'22px 27px',background:'#e8edff',borderRadius:16,fontSize:body}}>Draft reply prepared · <b>Not sent</b></div>
 <div style={{marginTop:22}}><Pill mode="orange">HUMAN APPROVAL REQUIRED</Pill></div>
 </div>;
 if(mode==='sheet')return <div style={base}>{header('▦ Sales report','FICTIONAL DEMO')}
 <div style={{marginTop:23,display:'grid',gridTemplateColumns:'1.2fr 1fr .8fr',background:'#dceee9',borderRadius:12,color:'#286550',fontWeight:900,fontSize:head}}>
 {['Order','Source','Amount'].map(x=><div key={x} style={{padding:'16px 13px'}}>{x}</div>)}</div>
 {['ORD-029','ORD-030','ORD-031'].map((x,i)=><div key={x} style={{display:'grid',gridTemplateColumns:'1.2fr 1fr .8fr',fontSize:head,borderBottom:'1px solid #e1e9ed',background:i%2?'#f2f6fa':'#fff'}}><div style={{padding:'20px 13px'}}>{x}</div><div style={{padding:'20px 13px'}}>Verified</div><div style={{padding:'20px 13px'}}>${[200,350,180][i]}</div></div>)}
 <div style={{display:'flex',justifyContent:'space-between',marginTop:29,gap:12,alignItems:'center'}}><span style={{fontSize:head,fontWeight:850}}>Draft says 12 orders</span><Pill mode="red">SOURCE: 13</Pill></div>
 <div style={{marginTop:27,padding:20,borderRadius:14,background:'#fff0f2',color:'#ab3041',fontSize:body,fontWeight:850}}>⚠ Mismatch flagged before publishing</div>
 </div>;
 if(mode==='report')return <div style={base}>{header('▤ Weekly update','FICTIONAL DEMO')}
 <div style={{fontSize:big,fontWeight:950,marginTop:25}}>Project pulse</div>
 {['Shipment status — verified','Sales totals — review flagged','Slide draft — awaiting approval'].map((x,i)=><div key={x} style={{display:'flex',gap:22,alignItems:'center',fontSize:body,padding:'23px 18px',marginTop:17,background:i===1?'#fff4e2':'#eef5f9',borderRadius:13}}><span style={{fontSize:31}}>{i===1?'!':'✓'}</span>{x}</div>)}
 <div style={{marginTop:27}}><Pill mode="orange">DRAFT — NOT PUBLISHED</Pill></div>
 </div>;
 if(mode==='danger')return <div style={base}>{header('✖ Action chain','FICTIONAL DEMO')}
 <div style={{fontSize:body,color:C.muted,marginTop:27}}>An unverified invoice changes three systems</div>
 {['READ WRONG INVOICE','UPDATE WRONG RECORD','SEND WRONG EMAIL'].map((x,i)=><div key={x} style={{marginTop:24,padding:'26px 20px',border:'1px solid #ffd6d9',background:i===2?'#ffeaed':'#fff5f3',borderRadius:12,display:'flex',justifyContent:'space-between',fontWeight:900,fontSize:body,color:'#b23340'}}><span>{x}</span><span>✕</span></div>)}
 </div>;
 return <div style={base}>{header('◆ Permission gates','SAFER WORKFLOW')}
 {['READ & SUMMARIZE','DRAFT & VERIFY','APPROVE BEFORE ACTION'].map((x,i)=><div key={x} style={{marginTop:25,display:'flex',alignItems:'center',justifyContent:'space-between',padding:'24px 27px',borderRadius:16,background:['#e9f8f1','#fff5dd','#ffebef'][i]}}><span style={{fontSize:body,fontWeight:900,color:C.ink}}>{x}</span><span style={{fontSize:big,color:[C.green,C.orange,C.red][i]}}>●</span></div>)}
 <div style={{fontSize:head,marginTop:30,color:C.muted}}>Build audit trails. Limit access. Verify sources.</div></div>
};
type K='mail'|'sheet'|'report'|'danger'|'security';
const LongStages:{a:number;b:number;k:K;eyebrow:string;title:string;sub:string;cap:string}[]=[
 {a:0,b:23,k:'mail',eyebrow:'OCTOBER 2026 · THE NEW WORK AGENT',title:'WHAT IF AI DID THE ADMIN WORK?',sub:'Three connected tasks. One question: who hits Send?',cap:'The biggest breakthrough may be the approval step.'},
 {a:23,b:49,k:'security',eyebrow:'ANNOUNCED OCTOBER 8, 2026',title:'GOOGLE INTRODUCED A UNIVERSAL WORK AGENT',sub:'Across Workspace and authorized business systems.',cap:'An enterprise announcement — availability varies.'},
 {a:49,b:83,k:'mail',eyebrow:'ILLUSTRATIVE WORKFLOW 01',title:'READ → CHECK → DRAFT',sub:'A late shipment email becomes a prepared reply.',cap:'Reading a message is not permission to send one.'},
 {a:83,b:123,k:'sheet',eyebrow:'ILLUSTRATIVE WORKFLOW 02',title:'A POLISHED CHART CAN BE WRONG',sub:'Source has 13 orders. Draft says 12. Flag it.',cap:'Source verification beats confident-looking output.'},
 {a:123,b:159,k:'report',eyebrow:'ILLUSTRATIVE WORKFLOW 03',title:'FROM APPROVED NOTES TO A DRAFT REPORT',sub:'Draft useful work; do not invent quotes or publish.',cap:'Review-ready content beats automatic publication.'},
 {a:159,b:188,k:'security',eyebrow:'THE REAL CATCH',title:'ACCESS IS NOT UNIVERSAL',sub:'Enterprise rollout, permissions and governance matter.',cap:'Planning an action does not prove an integration can execute it.'},
 {a:188,b:224,k:'security',eyebrow:'PRACTICAL RULE FOR ANY AI AUTOMATION',title:'GREEN · YELLOW · RED',sub:'Read freely within permission. Draft with review. Approve high-impact actions.',cap:'Never silently send messages, make payments or change critical records.'},
 {a:224,b:249,k:'mail',eyebrow:'YOUR TURN',title:'WOULD YOU LET AI HIT SEND?',sub:'Tell us which task belongs behind a human approval gate.',cap:'More automation should mean more control — not less.'},
];
export const GeminiAgentLong:React.FC=()=>{const f=useCurrentFrame(),s=f/24,st=LongStages.find(x=>s>=x.a&&s<x.b)||LongStages[LongStages.length-1];const intro=anim(f,Math.ceil(st.a*24),Math.ceil(st.a*24)+16);
 return <AbsoluteFill style={{background:C.bg,color:'#f8fbff',fontFamily:font,overflow:'hidden'}}><Glow/>
 <div style={{position:'absolute',top:43,left:90,right:90,display:'flex',justifyContent:'space-between',alignItems:'center'}}><strong style={{fontSize:23,letterSpacing:3,color:C.cyan}}>FLOWMINUTE LAB</strong><Tag color={C.violet} small>AI AGENTS · 2026</Tag></div>
 <div style={{position:'absolute',top:118,left:100,width:1700,opacity:intro,transform:`translateY(${(1-intro)*22}px)`}}><div style={{color:C.cyan,fontSize:23,fontWeight:900,letterSpacing:3}}>{st.eyebrow}</div><div style={{fontSize:69,fontWeight:950,lineHeight:1.06,maxWidth:1700,marginTop:15,letterSpacing:-2.1}}>{st.title}</div><div style={{fontSize:29,color:'#bdcde1',marginTop:18}}>{st.sub}</div></div>
 <div style={{position:'absolute',left:110,right:110,top:369,height:475,display:'flex',gap:48,alignItems:'stretch'}}>
 <Zoom f={f} start={Math.ceil(st.a*24)+4} style={{flex:1}}><Panel style={{height:'100%',transform:'perspective(1800px) rotateY(-4deg) rotateX(2deg)'}}><Workflow mode={st.k}/></Panel></Zoom>
 <div style={{width:580,display:'flex',flexDirection:'column',gap:20,justifyContent:'center'}}><Zoom f={f} start={Math.ceil(st.a*24)+10}><div style={{fontSize:26,color:C.cyan,fontWeight:900,letterSpacing:3}}>THE FLOWMINUTE TEST</div></Zoom>
 {st.k==='mail'?['SOURCE VERIFIED','REPLY PREPARED','SEND REQUIRES APPROVAL'].map((q,i)=><Zoom f={f} start={Math.ceil(st.a*24)+17+i*10} key={q}><div style={{background:'rgba(255,255,255,.065)',border:'1px solid #42536a',borderRadius:16,padding:'18px 24px',fontSize:27,fontWeight:850}}><span style={{color:i===2?C.orange:C.green,marginRight:18}}>{i===2?'◇':'✓'}</span>{q}</div></Zoom>):
 st.k==='sheet'?['SHOW THE SOURCE','CHECK EACH ROW','FLAG THE MISMATCH'].map((q,i)=><Zoom f={f} start={Math.ceil(st.a*24)+17+i*10} key={q}><div style={{background:'rgba(255,255,255,.065)',border:'1px solid #42536a',borderRadius:16,padding:'18px 24px',fontSize:27,fontWeight:850}}><span style={{color:i===2?C.orange:C.green,marginRight:18}}>✓</span>{q}</div></Zoom>):
 ['CONTROL ACCESS','VERIFY THE OUTPUT','KEEP HUMAN APPROVAL'].map((q,i)=><Zoom f={f} start={Math.ceil(st.a*24)+17+i*10} key={q}><div style={{background:'rgba(255,255,255,.065)',border:'1px solid #42536a',borderRadius:16,padding:'18px 24px',fontSize:27,fontWeight:850}}><span style={{color:C.cyan,marginRight:18}}>◆</span>{q}</div></Zoom>)}
 </div></div>
 <div style={{position:'absolute',bottom:104,left:260,right:260,textAlign:'center',background:'rgba(2,10,25,.89)',border:'1px solid #3e5970',borderRadius:15,padding:'18px 25px',fontSize:31,fontWeight:800}}>{st.cap}</div>
 <div style={{position:'absolute',bottom:19,left:90,right:90,color:'#a7bbcc',fontSize:16,display:'flex',justifyContent:'space-between'}}><span>ILLUSTRATIVE RECONSTRUCTION · NOT LIVE GEMINI FOOTAGE</span><span>Google announcement: October 8, 2026</span></div>
 <div style={{position:'absolute',bottom:0,left:0,right:0,height:6,background:'#233248'}}><div style={{height:'100%',width:(f/5976*100)+'%',background:C.cyan}}/></div>
 <Audio src={staticFile('voice-long-006.mp3')}/></AbsoluteFill>
};
type ShortStage={a:number;b:number;mode:K;tag:string;title:string;body:string;cap:string};
const short13:ShortStage[]=[
 {a:0,b:165,mode:'mail',tag:'GOOGLE · OCT 8 ANNOUNCEMENT',title:'AI COWORKER HAS AN INBOX?',body:'A dedicated work-agent identity.',cap:'Google just announced a new kind of AI coworker.'},
 {a:165,b:440,mode:'security',tag:'NOT JUST A CHATBOT',title:'AN AGENT WITH A ROLE',body:'It can use authorized context and tools.',cap:'An ongoing role, not merely one chatbot reply.'},
 {a:440,b:760,mode:'mail',tag:'FICTIONAL EXAMPLE',title:'CHECK → DRAFT → REVIEW',body:'The email is prepared, NOT sent.',cap:'Our example keeps humans in charge of Send.'},
 {a:760,b:1050,mode:'security',tag:'IMPORTANT LIMIT',title:'NOT IN EVERY GMAIL ACCOUNT',body:'Enterprise rollout and permissions vary.',cap:'This does not mean you have access today.'},
 {a:1050,b:1260,mode:'mail',tag:'COMMENTS',title:'WOULD YOU TRUST IT?',body:'Would you give AI its own work inbox?',cap:'What would you let an AI coworker handle?'},
];
const short14:ShortStage[]=[
 {a:0,b:215,mode:'danger',tag:'THE REAL AI AGENT RISK',title:'WRONG ACTION > WRONG ANSWER',body:'One mistake can spread to other apps.',cap:'The biggest AI mistake may be a real action.'},
 {a:215,b:505,mode:'danger',tag:'FICTIONAL EXAMPLE',title:'ONE BAD INVOICE. THREE ERRORS.',body:'Read. Update. Email. Each step compounds.',cap:'One wrong source can contaminate the whole workflow.'},
 {a:505,b:860,mode:'security',tag:'HOW TO MAKE IT SAFER',title:'READ → VERIFY → APPROVE',body:'Check the source before anything gets sent.',cap:'Make human approval the final gate.'},
 {a:860,b:1230,mode:'security',tag:'YOUR DECISION',title:'WHAT SHOULD AI NEVER AUTO-SEND?',body:'Comment with your no-automation boundary.',cap:'Would you trust an agent with important emails?'},
];
const Short:React.FC<{kind:13|14}>=({kind})=>{const f=useCurrentFrame(),arr=kind===13?short13:short14,max=kind===13?1260:1230,st=arr.find(x=>f>=x.a&&f<x.b)||arr[arr.length-1],a=anim(f,st.a,st.a+18);
 return <AbsoluteFill style={{background:C.bg,fontFamily:font,color:'white',overflow:'hidden'}}><Glow/>
 <div style={{position:'absolute',top:76,left:70,right:70,display:'flex',justifyContent:'space-between',alignItems:'center'}}><strong style={{fontSize:22,letterSpacing:2.6,color:C.cyan}}>FLOWMINUTE LAB</strong><Tag small>AI AGENTS</Tag></div>
 <div style={{position:'absolute',top:187,left:73,right:73,opacity:a,transform:`translateY(${(1-a)*28}px)`}}><div style={{fontSize:22,fontWeight:900,letterSpacing:1.9,color:C.cyan}}>{st.tag}</div><div style={{fontSize:68,fontWeight:950,letterSpacing:-2.0,lineHeight:1.04,marginTop:17}}>{st.title}</div><div style={{marginTop:22,fontSize:34,lineHeight:1.25,color:'#c8d6e5'}}>{st.body}</div></div>
 <Zoom f={f} start={st.a+6} style={{position:'absolute',top:590,left:65,right:65,height:775}}><Panel style={{height:'100%',transform:'perspective(1250px) rotateY(-2deg) rotateX(1deg)'}}><Workflow vertical mode={st.mode}/></Panel></Zoom>
 <div style={{position:'absolute',top:1429,left:70,right:70,display:'flex',gap:10,alignItems:'center'}}><Tag color={C.orange} small>EXAMPLE · NOT LIVE PRODUCT</Tag></div>
 <div style={{position:'absolute',bottom:227,left:65,right:65,minHeight:132,display:'flex',alignItems:'center',justifyContent:'center',textAlign:'center',fontSize:37,fontWeight:900,lineHeight:1.18,padding:'19px 23px',boxSizing:'border-box',borderRadius:17,background:'rgba(5,16,29,.98)',border:'1px solid #4a718b'}}>{st.cap}</div>
 <div style={{position:'absolute',bottom:92,left:70,right:70,color:'#a9c6d4',fontWeight:850,letterSpacing:2,fontSize:19}}>GOOGLE GEMINI AGENT · ANNOUNCED OCT 8, 2026</div>
 <div style={{position:'absolute',bottom:0,left:0,right:0,height:9,background:'#1d2a3b'}}><div style={{height:'100%',width:f/max*100+'%',background:C.cyan}}/></div>
 <Audio src={staticFile(kind===13?'voice-v13.mp3':'voice-v14.mp3')}/></AbsoluteFill>;
};
export const GeminiInboxShort:React.FC=()=> <Short kind={13}/>;
export const AgentPermissionShort:React.FC=()=> <Short kind={14}/>;
export const GeminiAgentThumbnail:React.FC=()=> <AbsoluteFill style={{background:'#091021',fontFamily:font,color:'#fff',overflow:'hidden'}}><Glow/><div style={{position:'absolute',top:80,left:90,color:C.cyan,fontSize:31,fontWeight:900,letterSpacing:3}}>FLOWMINUTE LAB · BREAKING AI</div><div style={{position:'absolute',left:95,top:210,fontSize:129,fontWeight:950,lineHeight:1.04,letterSpacing:-4.5}}>AI<br/>COWORKER<span style={{color:C.orange}}>?</span></div><div style={{position:'absolute',left:105,top:710,fontSize:49,fontWeight:900,color:'#ccdef1'}}>CAN IT HIT SEND?</div><div style={{position:'absolute',left:1080,top:193,width:710,height:673,transform:'perspective(1300px) rotateY(-10deg)'}}><Panel style={{height:'100%'}}><Workflow mode="mail"/></Panel></div><div style={{position:'absolute',bottom:59,left:96,color:C.cyan,fontSize:29,fontWeight:900}}>GOOGLE'S NEW GEMINI AGENT</div></AbsoluteFill>;
