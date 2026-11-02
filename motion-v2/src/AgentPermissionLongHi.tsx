import React from 'react';
import {AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame} from 'remotion';
import timing from './flowExplainLongHiTiming.json';

/**
 * FLOWMINUTE original Hindi 16:9 longer-form training example.
 * A request is NOT a real filesystem operation. This whole screen is simulated.
 * Preview only; no real tool call, approval or YouTube upload.
 */
const C={bg:'#07101C',panel:'#102133',raised:'#172B40',border:'#315067',white:'#F2F7FB',muted:'#8FAABC',amber:'#F1BB62',cyan:'#41D2D6',red:'#F2727A',green:'#57D8A4'};
const chapters=[
 {step:'01 / सवाल',title:'एजेंट फाइल हटा देगा?',description:'सुझाव और असली एक्शन अलग हैं।',status:'REQUESTED',accent:C.red,kind:'question'},
 {step:'02 / बुनियाद',title:'चैट बनाम टूल',description:'बिना टूल एक्सेस कोई कार्रवाई नहीं।',status:'TOOL CHECK',accent:C.cyan,kind:'difference'},
 {step:'03 / डेमो',title:'फोल्डर डिलीट रिक्वेस्ट',description:'यह फाइल-सिस्टम डेमो पूरी तरह काल्पनिक है।',status:'PREVIEW',accent:C.amber,kind:'demo'},
 {step:'04 / परमिशन',title:'रीड-ओनली की सीमा',description:'सूची पढ़ना ALLOW, हटाना DENY।',status:'SCOPE CHECK',accent:C.cyan,kind:'permission'},
 {step:'05 / सुरक्षा',title:'अप्रूवल या ब्लॉक?',description:'जोखिम वाले काम से पहले परिणाम जाँचें।',status:'DENIED',accent:C.red,kind:'approval'},
 {step:'06 / नियम',title:'कम से कम एक्सेस',description:'प्रीव्यू, लॉग और बैकअप के साथ काम करें।',status:'SAFE PATH',accent:C.green,kind:'safe'},
] as const;

const panel:React.CSSProperties={border:'2px solid '+C.border,background:C.panel,borderRadius:22,boxSizing:'border-box'};
const pill=(label:string,tone:string)=><span style={{display:'inline-block',fontSize:20,color:tone,background:'#172B3C',border:'1px solid '+tone,borderRadius:12,padding:'7px 17px',fontWeight:750}}>{label}</span>;
const Permission:React.FC<{title:string,sub:string,tone:string}>=({title,sub,tone})=><div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'19px 22px',marginBottom:15,border:'1px solid '+C.border,borderRadius:13,background:'#0E2030',minHeight:68}}>
 <div style={{fontSize:24,fontWeight:700}}>{title}</div><div style={{fontSize:18,color:tone,fontWeight:800}}>{sub}</div>
</div>;
export const AgentPermissionLongHi:React.FC<{includeNarration?:boolean}>=({includeNarration=false})=>{
 const frame=useCurrentFrame();
 const idx=timing.chapter_starts.reduce((n,start,i)=>frame>=start?i:n,0);
 const part=chapters[idx];
 const next=timing.chapter_starts[idx+1]??timing.duration_frames;
 const start=timing.chapter_starts[idx];
 const progress=interpolate(frame,[start,next],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const total=interpolate(frame,[0,timing.duration_frames],[0,1],{extrapolateRight:'clamp'});
 const ease=interpolate(frame,[start,start+15],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const cue=timing.cues.find(x=>frame>=x.start_frame&&frame<x.end_frame)?.text;
 const copy=cue??part.description;
 const isScope=idx>=3;const isDenied=idx===4;const isSafe=idx===5;
 const cursor=isScope?isDenied?54:isSafe?83:36+18*progress:12+progress*34;
 const fileHighlights=idx===2||idx===3||idx===4;
 return <AbsoluteFill style={{background:C.bg,color:C.white,fontFamily:'Noto Sans Devanagari, Noto Sans, Arial, sans-serif',overflow:'hidden',padding:'45px 72px',boxSizing:'border-box'}}>
  <AbsoluteFill style={{opacity:.18,backgroundImage:'linear-gradient(#30495F 1px,transparent 1px),linear-gradient(90deg,#30495F 1px,transparent 1px)',backgroundSize:'64px 64px',pointerEvents:'none'}}/>
  {includeNarration?<Audio src={staticFile('flow-explain-long-hi.wav')}/>:null}
  <div style={{height:80,...panel,display:'flex',alignItems:'center',padding:'0 26px',gap:16,position:'relative'}}>
    <div style={{width:28,height:28,background:C.cyan,borderRadius:8}}/>
    <span style={{fontSize:30,fontWeight:850,letterSpacing:.6}}>FLOWMINUTE LAB</span>
    <span style={{color:C.muted,fontWeight:700,fontSize:22,marginLeft:12}}> // EXPLAIN  ·  हिंदी</span>
    <span style={{marginLeft:'auto'}}>{pill('शैक्षणिक डेमो',C.cyan)}</span>
  </div>
  <div style={{display:'flex',gap:28,marginTop:34,height:733,position:'relative'}}>
    <div style={{...panel,width:565,padding:'38px 35px',display:'flex',flexDirection:'column',boxSizing:'border-box'}}>
      <div style={{color:part.accent,fontWeight:850,fontSize:24,letterSpacing:1}}>{part.step}</div>
      <div style={{fontSize:53,fontWeight:850,lineHeight:1.23,marginTop:27,opacity:ease,transform:`translateY(${(1-ease)*10}px)`,maxHeight:195,overflow:'hidden'}}>{part.title}</div>
      <div style={{fontSize:28,color:C.muted,lineHeight:1.42,marginTop:27}}>{part.description}</div>
      <div style={{marginTop:'auto'}}>
        <div style={{fontSize:20,color:C.muted,letterSpacing:1,marginBottom:17}}>हर कदम जाँच के बाद</div>
        {chapters.map((c,i)=><div key={i} style={{height:13,borderRadius:10,background:i===idx?part.accent:i<idx?'#3A6271':'#24384A',marginBottom:14,opacity:i===idx?1:.7}}/>)}
        <div style={{color:C.muted,fontSize:19,marginTop:15}}>नया काम शुरू करने से पहले परमिशन देखें।</div>
      </div>
    </div>
    <div style={{...panel,flex:1,padding:'28px',boxSizing:'border-box'}}>
      <div style={{background:C.raised,borderRadius:14,height:67,display:'flex',alignItems:'center',padding:'0 24px',gap:11}}>
        <span style={{height:14,width:14,borderRadius:'50%',background:C.red}}/>
        <span style={{height:14,width:14,borderRadius:'50%',background:C.amber}}/>
        <span style={{height:14,width:14,borderRadius:'50%',background:C.green}}/>
        <span style={{fontSize:22,fontWeight:750,marginLeft:20}}>agent_workspace / sample_data</span>
        <span style={{marginLeft:'auto',fontSize:19,color:part.accent,fontWeight:800}}>SIMULATION · {part.status}</span>
      </div>
      <div style={{display:'flex',gap:24,height:459,marginTop:28}}>
        <div style={{...panel,flex:1,padding:24,background:'#0B1B2B'}}>
          <div style={{fontSize:23,color:C.muted,fontWeight:800}}>डेमो फाइल ब्राउज़र</div>
          <div style={{height:1,background:C.border,margin:'20px 0'}}/>
          {['reports/','budget_2026.csv','notes.txt','archive/'].map((name,i)=><div key={name} style={{display:'flex',alignItems:'center',gap:15,border:'2px solid '+(i===0&&fileHighlights?isDenied?C.red:C.amber:C.border),borderRadius:12,padding:'16px 18px',marginBottom:15,background:i===0&&fileHighlights?'#253142':'#112739',fontSize:23,fontWeight:700}}>
            <span style={{fontSize:28,color:i===0?C.amber:C.cyan}}>{i===0||i===3?'▣':'▤'}</span>{name}
            {i===0&&isSafe?<span style={{marginLeft:'auto',color:C.green,fontSize:17}}>सुरक्षित</span>:null}
          </div>)}
        </div>
        <div style={{...panel,width:376,padding:24,background:'#0B1B2B'}}>
          <div style={{fontSize:22,color:C.muted,fontWeight:800}}>टूल अनुमति</div>
          <div style={{height:1,background:C.border,margin:'20px 0'}}/>
          <Permission title="LIST" sub="ALLOW" tone={C.green}/>
          <Permission title="READ" sub="ALLOW" tone={C.green}/>
          <Permission title="DELETE" sub={isScope?'DENY':'NOT GRANTED'} tone={C.red}/>
          <div style={{marginTop:24,fontSize:20,color:part.accent,fontWeight:850}}>{isDenied?'×  डिलीट ऑपरेशन रोका':isSafe?'✓  डेटा सुरक्षित':idx<2?'अनुमति का इंतजार':'एक्शन की जाँच जारी'}</div>
        </div>
      </div>
      <div style={{position:'relative',marginTop:23,height:94,background:'#0B1C2C',border:'1px solid '+C.border,borderRadius:14,boxSizing:'border-box',overflow:'hidden'}}>
        <div style={{position:'absolute',left:'12%',right:'10%',top:30,height:5,background:'#355367',borderRadius:5}}/>
        <div style={{position:'absolute',left:'12%',top:30,height:5,width:`${Math.max(0,cursor-12)}%`,background:part.accent,borderRadius:5}}/>
        {[['एजेंट',12],['परमिशन',54],['टूल',88]].map(([name,n])=><React.Fragment key={name}>
          <div style={{position:'absolute',left:`calc(${n}% - 11px)`,top:20,width:24,height:24,border:'3px solid '+C.border,borderRadius:'50%',background:C.bg,zIndex:2}}/>
          <div style={{position:'absolute',left:`calc(${n}% - 85px)`,top:57,width:170,textAlign:'center',fontSize:18,color:C.muted}}>{name}</div>
        </React.Fragment>)}
        <div style={{position:'absolute',left:`calc(${cursor}% - 14px)`,top:18,width:28,height:28,borderRadius:'50%',background:part.accent,boxShadow:`0 0 ${8+progress*19}px ${part.accent}`,zIndex:3}}/>
      </div>
      <div style={{fontSize:18,color:C.muted,marginTop:14,textAlign:'center'}}>डेमो स्क्रीन · किसी असली फाइल तक पहुंच नहीं</div>
    </div>
  </div>
  <div style={{...panel,marginTop:22,height:123,padding:'19px 32px',boxSizing:'border-box',display:'flex',alignItems:'center',gap:25,position:'relative'}}>
    <div style={{height:75,width:8,borderRadius:6,background:part.accent}}/>
    <div style={{fontSize:33,fontWeight:720,lineHeight:1.25,maxWidth:1650}}>{copy}</div>
  </div>
  <div style={{height:8,marginTop:20,background:'#254256',borderRadius:6,overflow:'hidden',position:'relative'}}>
    <div style={{height:'100%',width:`${Math.min(100,total*100)}%`,background:C.cyan,borderRadius:6}}/>
  </div>
 </AbsoluteFill>;
};
