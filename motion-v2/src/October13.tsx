import React from 'react';
import {AbsoluteFill,Audio,Img,interpolate,staticFile,useCurrentFrame} from 'remotion';

const C={bg:'#061421',panel:'#102C40',deep:'#091D2E',cyan:'#52E3EE',teal:'#3DE5B9',white:'#F5FAFF',muted:'#ABC7D8',orange:'#FFC477',red:'#FF7694'};
const font='Inter, Segoe UI, Arial, sans-serif';
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const reveal=(f:number,start:number)=>clamp((f-start)/16);
const shell:React.CSSProperties={background:'linear-gradient(148deg,#051320 0%,#0C2940 68%,#05131E 100%)',color:C.white,fontFamily:font,overflow:'hidden'};
const card:React.CSSProperties={background:'linear-gradient(140deg,rgba(16,44,64,.97),rgba(6,22,39,.98))',border:'2px solid #386F82',borderRadius:28,boxShadow:'0 22px 66px #0007'};
const Text:React.FC<{children:React.ReactNode;size?:number;color?:string;weight?:number;style?:React.CSSProperties}>=({children,size=34,color=C.white,weight=800,style})=><div style={{fontSize:size,color,fontWeight:weight,lineHeight:1.15,...style}}>{children}</div>;
const Label:React.FC<{children:React.ReactNode;color?:string}>=({children,color=C.teal})=><div style={{fontSize:22,fontWeight:900,letterSpacing:1.6,color,marginBottom:17}}>{children}</div>;
const Background:React.FC<{f:number;photo?:boolean}>=({f,photo=false})=><AbsoluteFill style={{background:'radial-gradient(circle at 10% 20%,#155E705E,transparent 45%),radial-gradient(circle at 90% 85%,#134F695A,transparent 50%),'+C.bg}}>
 {photo&&<Img src={staticFile('office-cinematic.jpg')} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',opacity:.18,filter:'blur(2px) saturate(.65)',transform:'scale('+(1.04+f/20000)+')'}}/>}
 <div style={{position:'absolute',inset:0,opacity:.14,background:'repeating-linear-gradient(0deg,transparent 0px,transparent 59px,#41D7DD 60px),repeating-linear-gradient(90deg,transparent 0px,transparent 59px,#41D7DD 60px)'}}/>
 <div style={{position:'absolute',width:700,height:700,borderRadius:'50%',left:-150,top:200,background:'radial-gradient(circle,#2DD4BA22,transparent 70%)',transform:'translateX('+Math.sin(f/160)*30+'px)'}}/>
</AbsoluteFill>;
const Branding:React.FC<{vertical?:boolean}>=({vertical=false})=><div style={{fontSize:vertical?26:24,fontWeight:950,color:C.cyan,letterSpacing:3}}>FM  /  FLOWMINUTE LAB</div>;
const SafeTag:React.FC<{vertical?:boolean}>=({vertical=false})=><div style={{fontSize:vertical?18:17,letterSpacing:1.3,color:C.muted,fontWeight:800}}>ILLUSTRATIVE RECONSTRUCTION — NOT LIVE PRODUCT FOOTAGE</div>;
const Progress:React.FC<{f:number;total:number}>=({f,total})=><div style={{position:'absolute',bottom:0,left:0,right:0,height:7,background:'#294054'}}><div style={{height:'100%',width:clamp(f/total)*100+'%',background:C.teal}}/></div>;
const Entry:React.FC<{f:number;start:number;children:React.ReactNode;style?:React.CSSProperties}>=({f,start,children,style})=>{const p=reveal(f,start);return <div style={{opacity:p,transform:'translateY('+((1-p)*34)+'px)',...style}}>{children}</div>};
const Bar:React.FC<{i:number;f:number}>=({i,f})=><div style={{width:12,height:18+(Math.abs(Math.sin(f/10+i*.82))*75),borderRadius:8,background:i%3?C.cyan:C.teal,boxShadow:'0 0 10px #2EDBC555'}}/>;
const Wave:React.FC<{f:number}>=({f})=><div style={{display:'flex',justifyContent:'center',alignItems:'center',gap:8,height:180,width:'100%'}}>{Array.from({length:43},(_,i)=><Bar key={i} i={i} f={f}/>)}</div>;
const Phone:React.FC<{f:number;kind:'audio'|'transcript'|'actions'|'check'}>=({f,kind})=><div style={{...card,width:760,maxWidth:'100%',minHeight:610,margin:'0 auto',padding:38,boxSizing:'border-box',borderRadius:55}}>
 <div style={{display:'flex',justifyContent:'space-between',color:C.muted,fontSize:21,fontWeight:700}}><span>9:41</span><span>●●●  ▰</span></div>
 <div style={{width:105,height:7,borderRadius:10,background:'#72A6B9',margin:'27px auto 35px'}}/>
 <Text size={49} style={{textAlign:'center'}}>{kind==='audio'?'Voice memo':kind==='transcript'?'Transcript':kind==='actions'?'Action items':'Review details'}</Text>
 {kind==='audio'?<><Wave f={f}/><div style={{borderRadius:18,background:'#1E4960',padding:'26px',textAlign:'center'}}><Text size={30} color={C.teal}>AUDIO FILE  ·  00:36</Text></div><Text size={25} color={C.muted} style={{marginTop:29,textAlign:'center'}}>Attach a supported recording</Text></>:
 <div style={{marginTop:40}}>{(kind==='transcript'?['Meeting with Alex — 2:30','Send draft to Priya','Check the invoice total']:kind==='actions'?['✓ Draft the summary','✓ Prepare follow-up','? Confirm who owns the task']:['? 2:30 or 3:30?','? Alex or Alec?','✓ Replay the original']).map((s,i)=><div key={s} style={{padding:'21px',marginBottom:15,borderRadius:14,background:i===2?'#245462':'#1B3C53',border:'1px solid #467486'}}><Text size={28} color={s.startsWith('?')?C.orange:C.white}>{s}</Text></div>)}</div>}
 <div style={{position:'absolute',bottom:30,right:40,color:C.muted,fontSize:18}}>CONCEPT UI</div>
 </div>;
const Composer:React.FC<{f:number;mode:'predict'|'tab'|'limit'}>=({f,mode})=><div style={{...card,margin:'0 auto',padding:36,width:'100%',boxSizing:'border-box',minHeight:570}}>
 <div style={{display:'flex',justifyContent:'space-between',paddingBottom:22,borderBottom:'1px solid #427B8B'}}><Text size={34}>Codex desktop</Text><Text size={21} color={C.teal}>BETA · ILLUSTRATIVE</Text></div>
 <div style={{marginTop:45,padding:25,borderRadius:18,background:'#12374B',border:'1px solid #437487'}}><Text size={27}>✓ Response complete</Text><Text size={24} color={C.muted} style={{marginTop:15}}>Changes reviewed. Tests passed.</Text></div>
 <div style={{marginTop:42,padding:25,borderRadius:16,background:'#091C2F',border:'2px solid #4DBFC1'}}>
 <Text size={22} color={C.muted}>NEXT MESSAGE</Text>
 <div style={{marginTop:17,minHeight:118}}><Text size={31} color={mode==='limit'?C.muted:C.cyan}>{mode==='predict'?'Suggest tests for the new feature.':mode==='tab'?'Suggest tests for the new feature.':'May appear only when eligible.'}</Text></div>
 </div>
 <div style={{display:'flex',gap:20,marginTop:26}}><div style={{padding:'17px 25px',borderRadius:12,background:'#32717A'}}><Text size={28}>{mode==='predict'?'TAB  →  ACCEPT':mode==='tab'?'TAB  →  EDIT':'PRO  ·  DESKTOP'}</Text></div><div style={{padding:'17px 25px',border:'1px solid #AA5669',borderRadius:12}}><Text size={28} color={mode==='tab'?C.orange:C.muted}>NOT AUTO-SENT</Text></div></div>
 </div>;
type Beat={from:number;to:number;eyebrow:string;headline:string;support:string;mode:string};
const audioBeats:Beat[]=[
 {from:0,to:4,eyebrow:'NEW · OCTOBER 2026',headline:'VOICE NOTE → TO-DO LIST?',support:'Stop replaying the same recording.',mode:'audio'},
 {from:4,to:13,eyebrow:'CHATGPT AUDIO UPLOADS',headline:'ATTACH THE RECORDING',support:'Paid-plan feature · access varies.',mode:'audio'},
 {from:13,to:23,eyebrow:'A USEFUL WORKFLOW',headline:'TRANSCRIBE + SUMMARIZE',support:'Extract decisions and action items.',mode:'transcript'},
 {from:23,to:30,eyebrow:'THE REAL CATCH',headline:'NAMES CAN BE WRONG',support:'Times, numbers and speakers too.',mode:'check'},
 {from:30,to:38,eyebrow:'YOUR PRACTICAL PROMPT',headline:'MARK WHAT IS UNCERTAIN',support:'Check the original audio before trusting.',mode:'actions'}
];
const codexBeats:Beat[]=[
 {from:0,to:7,eyebrow:'CODEX · OCTOBER 9 BETA',headline:'AI GUESSES YOUR NEXT PROMPT?',support:'What happens after the answer?',mode:'predict'},
 {from:7,to:17,eyebrow:'COMPOSER PREDICTIONS',headline:'A SUGGESTION APPEARS',support:'Press Tab to accept into the editor.',mode:'predict'},
 {from:17,to:24,eyebrow:'IMPORTANT DISTINCTION',headline:'TAB DOES NOT HIT SEND',support:'Review and edit it first.',mode:'tab'},
 {from:24,to:33,eyebrow:'ELIGIBLE USERS ONLY',headline:'CODEX DESKTOP · PRO BETA',support:'Supported models and regions only.',mode:'limit'},
];
const Short:React.FC<{variant:'audio'|'codex'}>=({variant})=>{
 const f=useCurrentFrame(),s=f/30,beats=variant==='audio'?audioBeats:codexBeats,beat=beats.find(b=>s>=b.from&&s<b.to)||beats[beats.length-1],start=beat.from*30,total=variant==='audio'?1140:990;
 return <AbsoluteFill style={shell}><Background f={f}/>
 <div style={{position:'absolute',top:86,left:67,right:67}}><Branding vertical/></div>
 <Entry f={f} start={start} style={{position:'absolute',left:65,right:65,top:210}}>
  <Label>{beat.eyebrow}</Label><Text size={72} style={{letterSpacing:-2.2}}>{beat.headline}</Text><Text color={C.muted} size={34} style={{marginTop:25}}>{beat.support}</Text>
 </Entry>
 <Entry f={f} start={start+7} style={{position:'absolute',left:70,right:70,top:630}}>{variant==='audio'?<Phone f={f} kind={beat.mode as 'audio'|'transcript'|'check'|'actions'}/>:<Composer f={f} mode={beat.mode as 'predict'|'tab'|'limit'}/>}</Entry>
 <div style={{position:'absolute',top:1450,left:65,right:65,padding:32,border:'1px solid #3C8290',borderRadius:20,background:'#071E31DD'}}>
 <Text size={29} color={C.cyan}>{variant==='audio'?'VERIFY NAMES, NUMBERS & SPEAKERS':'ACCEPTING A SUGGESTION ≠ SENDING'}</Text>
 <Text size={23} color={C.muted} style={{marginTop:12}}>{variant==='audio'?'Source: OpenAI, October 6, 2026':'Source: OpenAI, October 9, 2026'}</Text>
 </div>
 <div style={{position:'absolute',left:66,right:66,bottom:90}}><SafeTag vertical/></div>
 <Progress f={f} total={total}/>
 <Audio src={staticFile(variant==='audio'?'oct13-voice-017.mp3':'oct13-voice-018.mp3')}/>
 </AbsoluteFill>;
};
type LongBeat=Beat & {display:'folders'|'network'|'rules'|'split'};
const longBeats:LongBeat[]=[
 {from:0,to:18,eyebrow:'A REAL PROBLEM · HYPOTHETICAL EXAMPLE',headline:'WHAT CAN YOUR AI AGENT TOUCH?',support:'You asked it to organize invoices — not your entire computer.',mode:'folders',display:'folders'},
 {from:18,to:38,eyebrow:'GITHUB · OCTOBER 7, 2026',headline:'COPILOT LOCAL SANDBOXING',support:'Tool execution boundaries are different from model reasoning.',mode:'network',display:'network'},
 {from:38,to:62,eyebrow:'THE IDEA',headline:'THE MODEL THINKS. THE TOOLS ACT.',support:'A sandbox restricts tools through operating-system controls.',mode:'split',display:'split'},
 {from:62,to:91,eyebrow:'ILLUSTRATIVE EXAMPLE',headline:'ALLOW ONE FOLDER. PROTECT ANOTHER.',support:'An invoice project is not permission to read private records.',mode:'folders',display:'folders'},
 {from:91,to:112,eyebrow:'THREE PERMISSION LAYERS',headline:'FILES · NETWORK · CREDENTIALS',support:'Each needs its own explicit policy.',mode:'network',display:'network'},
 {from:112,to:137,eyebrow:'BEFORE YOU RUN THE AGENT',headline:'CHECK THE BOUNDARIES',support:'Where can it read? What can it change? Who approves?',mode:'rules',display:'rules'},
 {from:137,to:158,eyebrow:'IMPORTANT LIMIT',headline:'SANDBOXED DOES NOT MEAN INFALLIBLE',support:'Policies, integrations and review points still matter.',mode:'split',display:'split'},
 {from:158,to:173,eyebrow:'ONE QUESTION FOR YOU',headline:'WOULD YOU GIVE AI YOUR WHOLE COMPUTER?',support:'A workshop key is not a building key.',mode:'folders',display:'folders'}
];
const FeatureBox:React.FC<{title:string;sub:string;color:string;f:number}>=({title,sub,color,f})=><div style={{...card,padding:37,flex:1,minHeight:340,background:'#0C2438D9',borderColor:color}}>
 <div style={{fontSize:29,color,fontWeight:900,letterSpacing:1.2}}>{title}</div><div style={{marginTop:29}}><Text size={36}>{sub}</Text></div>
 <div style={{marginTop:46,height:10,borderRadius:9,background:'#284659',overflow:'hidden'}}><div style={{height:'100%',background:color,width:(25+65*Math.abs(Math.sin(f/54)))+'%'}}/></div>
 </div>;
const LongGraphic:React.FC<{f:number;display:LongBeat['display']}>=({f,display})=>{
 if(display==='folders')return <div style={{display:'flex',gap:32,width:'100%',height:'100%'}}>
 <FeatureBox title="✓ ALLOWED PROJECT" sub="📁 Project Files   ↳ Invoice.csv   ↳ Orders.csv" color={C.teal} f={f}/>
 <FeatureBox title="✕ PRIVATE AREA" sub="🔒 Private Records   ↳ Personal files   ↳ API keys" color={C.orange} f={f+44}/>
 </div>;
 if(display==='network')return <div style={{display:'flex',gap:24,width:'100%',height:'100%'}}>
 {([['FILES','Read/edit paths',C.teal],['NETWORK','Outside connections',C.cyan],['SECRETS','Stored credentials',C.orange]] as const).map(([head,desc,color],i)=><FeatureBox key={head} title={head} sub={desc} color={color} f={f+i*30}/>)}
 </div>;
 if(display==='rules')return <div style={{display:'flex',flexDirection:'column',gap:20,width:'100%'}}>{['01   ALLOW ONLY NECESSARY FILES','02   RESTRICT INTERNET AND CREDENTIALS','03   REVIEW IRREVERSIBLE ACTIONS'].map((x,i)=><div key={x} style={{...card,padding:31,borderColor:i===2?C.orange:C.teal}}><Text size={37}>{x}</Text></div>)}</div>;
 return <div style={{display:'flex',gap:40,height:'100%'}}>
 <FeatureBox title="THE LANGUAGE MODEL" sub="Suggests what to do next" color={C.cyan} f={f}/>
 <div style={{fontSize:75,color:C.orange,alignSelf:'center'}}>≠</div>
 <FeatureBox title="THE SANDBOX" sub="Constrains what tools can actually do" color={C.teal} f={f+55}/>
 </div>;
};
export const Oct13AudioShort:React.FC=()=> <Short variant="audio"/>;
export const Oct13CodexShort:React.FC=()=> <Short variant="codex"/>;
export const Oct13SandboxLong:React.FC=()=>{
 const f=useCurrentFrame(),s=f/24,beat=longBeats.find(b=>s>=b.from&&s<b.to)||longBeats[longBeats.length-1],start=beat.from*24;
 return <AbsoluteFill style={shell}><Background f={f} photo/>
 <div style={{position:'absolute',top:42,left:83,right:83,display:'flex',justifyContent:'space-between'}}><Branding/><Label>AI CODING AGENTS · GITHUB COPILOT</Label></div>
 <Entry f={f} start={start} style={{position:'absolute',top:170,left:95,right:95}}><Label>{beat.eyebrow}</Label><Text size={75} style={{letterSpacing:-2}}>{beat.headline}</Text><Text size={31} color={C.muted} style={{marginTop:19}}>{beat.support}</Text></Entry>
 <Entry f={f} start={start+7} style={{position:'absolute',left:95,right:95,top:435,height:380}}><LongGraphic f={f} display={beat.display}/></Entry>
 <div style={{position:'absolute',left:90,right:90,bottom:90,display:'flex',justifyContent:'space-between'}}><SafeTag/><Text size={19} color={C.muted}>SOURCE: GITHUB · OCT 7 2026</Text></div>
 <Progress f={f} total={4152}/>
 <Audio src={staticFile('oct13-voice-long008.mp3')}/>
 </AbsoluteFill>;
};
export const Oct13SandboxThumbnail:React.FC=()=> <AbsoluteFill style={shell}><Background f={0} photo/><div style={{position:'absolute',top:74,left:95}}><Branding/></div><div style={{position:'absolute',top:180,left:95,width:950}}><Text size={142} style={{letterSpacing:-5}}>AI AGENT</Text><Text size={141} color={C.orange} style={{letterSpacing:-5}}>ACCESS?</Text><Text size={44} color={C.muted} style={{marginTop:47}}>What actually stops it?</Text></div><div style={{position:'absolute',left:1110,right:80,top:255,height:600,transform:'rotate(-4deg)'}}><div style={{...card,padding:47,height:'100%',boxSizing:'border-box'}}><Text size={42} color={C.teal}>✓ PROJECT FILES</Text><div style={{height:2,background:'#457080',margin:'45px 0'}}/><Text size={51} color={C.red}>⛔ PRIVATE RECORDS</Text><div style={{marginTop:55,padding:21,border:'2px dashed '+C.orange,borderRadius:15}}><Text size={29}>PERMISSION BOUNDARY</Text></div></div></div></AbsoluteFill>;
