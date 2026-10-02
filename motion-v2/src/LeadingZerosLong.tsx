import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const C={bg:'#060d17',panel:'#0d1b2c',panel2:'#12263d',text:'#f4f8fc',muted:'#9db1c7',cyan:'#5ee7ff',green:'#75efad',red:'#ff7178',yellow:'#ffd76a',purple:'#b996ff'};
const fps=24;
const clamp=(f:number,i:number[],o:number[])=>interpolate(f,i,o,{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(.2,.72,.2,1)});

const chapters=[
  [0,480,'THE PROBLEM'],
  [480,960,'IDENTIFIER ≠ QUANTITY'],
  [960,2400,'SAFER CSV IMPORT'],
  [2400,3000,'LONG IDs & PRECISION'],
  [3000,3600,'AUTOMATIC CONVERSIONS'],
  [3600,4320,'TWO COMMON TRAPS'],
  [4320,5160,'VERIFY BEFORE EXPORT'],
] as const;

const Bg:React.FC=()=> {
 const frame=useCurrentFrame();
 return <AbsoluteFill style={{background:'radial-gradient(circle at 50% 8%,#15304e 0%,#091625 38%,#060d17 75%,#03070d 100%)',overflow:'hidden'}}>
   <div style={{position:'absolute',inset:-300,opacity:.24,transform:`perspective(1200px) rotateX(70deg) translateY(${380+(frame*.22)%100}px)`,backgroundImage:'linear-gradient(rgba(94,231,255,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(94,231,255,.10) 1px,transparent 1px)',backgroundSize:'100px 100px',maskImage:'linear-gradient(to bottom,transparent,black 25%,black 80%,transparent)'}}/>
 </AbsoluteFill>;
};

const TopBar:React.FC=()=> {
 const frame=useCurrentFrame();
 const ch=chapters.find(([a,b])=>frame>=a&&frame<b);
 return <div style={{position:'absolute',top:34,left:58,right:58,display:'flex',alignItems:'center',justifyContent:'space-between',zIndex:30,fontFamily:'Arial,Helvetica,sans-serif'}}>
   <div style={{color:C.muted,fontSize:22,fontWeight:900,letterSpacing:1.7}}>FLOWMINUTE LAB</div>
   <div style={{color:C.cyan,fontSize:20,fontWeight:900,letterSpacing:1.4}}>{ch?.[2]??''}</div>
 </div>;
};

const Progress:React.FC=()=> {
 const f=useCurrentFrame();
 return <div style={{position:'absolute',bottom:26,left:58,right:58,height:4,borderRadius:5,background:'rgba(255,255,255,.09)',zIndex:40}}>
   <div style={{height:'100%',width:`${(f/5159)*100}%`,borderRadius:5,background:`linear-gradient(90deg,${C.cyan},${C.purple},${C.green})`}}/>
 </div>;
};

const Chip:React.FC<{children:React.ReactNode;color?:string}>=({children,color=C.cyan})=><span style={{display:'inline-flex',padding:'8px 14px',borderRadius:999,background:`${color}18`,border:`1px solid ${color}66`,color,fontSize:20,fontWeight:900}}>{children}</span>;

const Hook:React.FC=()=> {
 const frame=useCurrentFrame();
 const {fps}=useVideoConfig();
 const enter=spring({frame,fps,config:{damping:16,stiffness:90}});
 const mutate=clamp(frame,[135,220],[0,1]);
 const fade=clamp(frame,[430,480],[1,0]);
 return <div style={{position:'absolute',inset:'100px 90px 70px',opacity:fade,fontFamily:'Arial,Helvetica,sans-serif'}}>
   <div style={{display:'grid',gridTemplateColumns:'1.05fr .95fr',gap:60,height:'100%',alignItems:'center'}}>
     <div style={{transform:`translateX(${(1-enter)*-55}px)`}}>
       <Chip color={C.red}>DATA TYPE PROBLEM</Chip>
       <div style={{fontSize:72,lineHeight:1.02,fontWeight:1000,color:C.text,marginTop:28,maxWidth:780}}>Excel keeps removing your leading zeros?</div>
       <div style={{fontSize:30,lineHeight:1.35,color:C.muted,marginTop:26,maxWidth:700}}>The CSV may be fine. Excel may be interpreting an identifier as a number.</div>
     </div>
     <div style={{position:'relative',height:610}}>
       <div style={{position:'absolute',inset:'40px 0',borderRadius:34,background:'linear-gradient(145deg,#132a45,#091726)',border:'1px solid rgba(150,195,230,.22)',boxShadow:'0 50px 120px rgba(0,0,0,.4)',padding:34}}>
         <div style={{display:'flex',justifyContent:'space-between',color:C.muted,fontSize:20}}><span>customer_ids.csv</span><span>CSV</span></div>
         <div style={{marginTop:50,fontSize:20,color:C.muted,fontWeight:850}}>CUSTOMER ID</div>
         <div style={{marginTop:15,display:'flex',alignItems:'center',gap:24}}>
           <div style={{fontSize:84,fontWeight:1000,color:C.text,opacity:1-mutate*.45}}>00123</div>
           <div style={{fontSize:60,color:C.red,opacity:mutate}}>→</div>
           <div style={{fontSize:84,fontWeight:1000,color:C.red,opacity:mutate,transform:`scale(${.85+mutate*.15})`}}>123</div>
         </div>
         <div style={{height:2,background:'rgba(255,255,255,.08)',margin:'44px 0'}}/>
         <div style={{fontSize:21,color:C.red,fontWeight:950,letterSpacing:1.6,opacity:mutate}}>VALUE CHANGED</div>
         <div style={{fontSize:25,color:C.muted,marginTop:13,opacity:mutate}}>Same digits? No. Same record? Maybe not.</div>
       </div>
     </div>
   </div>
 </div>;
};

const Concept:React.FC=()=> {
 const frame=useCurrentFrame();
 const local=frame-480;
 const enter=clamp(local,[0,40],[0,1]);
 const fade=clamp(local,[430,480],[1,0]);
 return <div style={{position:'absolute',inset:'110px 100px 70px',opacity:enter*fade,fontFamily:'Arial,Helvetica,sans-serif'}}>
   <div style={{textAlign:'center',fontSize:56,fontWeight:1000,color:C.text}}>Digits do not automatically mean “number”.</div>
   <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:34,marginTop:70}}>
     <div style={{padding:38,borderRadius:30,background:'rgba(14,31,51,.94)',border:`1px solid ${C.cyan}55`}}>
       <div style={{color:C.cyan,fontSize:26,fontWeight:950}}>QUANTITY</div>
       <div style={{fontSize:70,fontWeight:1000,color:C.text,marginTop:28}}>123</div>
       <div style={{fontSize:27,color:C.muted,lineHeight:1.4,marginTop:20}}>You can add it, average it, multiply it, compare magnitude.</div>
       <div style={{marginTop:36}}><Chip>math semantics</Chip></div>
     </div>
     <div style={{padding:38,borderRadius:30,background:'rgba(14,31,51,.94)',border:`1px solid ${C.green}55`}}>
       <div style={{color:C.green,fontSize:26,fontWeight:950}}>IDENTIFIER</div>
       <div style={{fontSize:70,fontWeight:1000,color:C.text,marginTop:28}}>00123</div>
       <div style={{fontSize:27,color:C.muted,lineHeight:1.4,marginTop:20}}>Customer ID, SKU, postal code or phone-like value. Its digits are identity.</div>
       <div style={{marginTop:36}}><Chip color={C.green}>text semantics</Chip></div>
     </div>
   </div>
 </div>;
};

const ImportFlow:React.FC=()=> {
 const frame=useCurrentFrame();
 const local=frame-960;
 const fadeIn=clamp(local,[0,35],[0,1]);
 const fadeOut=clamp(local,[1380,1440],[1,0]);
 const steps=[
  ['1','DATA','From Text / CSV',C.cyan],
  ['2','PREVIEW','Transform Data',C.purple],
  ['3','POWER QUERY','Data Type → Text',C.yellow],
  ['4','LOAD','Close & Load',C.green],
 ] as const;
 const step=Math.min(3,Math.floor(Math.max(0,local-110)/300));
 return <div style={{position:'absolute',inset:'98px 80px 65px',opacity:fadeIn*fadeOut,fontFamily:'Arial,Helvetica,sans-serif'}}>
   <div style={{display:'flex',justifyContent:'space-between',alignItems:'end'}}>
     <div><Chip color={C.green}>RECOMMENDED WORKFLOW</Chip><div style={{fontSize:56,fontWeight:1000,color:C.text,marginTop:22}}>Import the CSV. Don’t just double-click it.</div></div>
     <div style={{fontSize:24,color:C.muted}}>Microsoft-supported path</div>
   </div>
   <div style={{display:'grid',gridTemplateColumns:'440px 1fr',gap:40,marginTop:45,height:650}}>
     <div style={{display:'flex',flexDirection:'column',gap:16}}>
       {steps.map(([num,head,label,color],i)=>{
         const active=i<=step;
         const p=clamp(local,[70+i*300,120+i*300],[0,1]);
         return <div key={num} style={{padding:'22px 24px',borderRadius:22,background:active?`${color}12`:'rgba(13,27,44,.85)',border:`1px solid ${active?color+'70':'rgba(255,255,255,.08)'}`,opacity:.45+.55*p}}>
           <div style={{display:'flex',gap:16,alignItems:'center'}}>
             <div style={{width:46,height:46,borderRadius:46,display:'flex',alignItems:'center',justifyContent:'center',background:active?color:'#26394d',color:'#051018',fontWeight:1000,fontSize:22}}>{num}</div>
             <div><div style={{fontSize:17,letterSpacing:1.4,fontWeight:900,color:active?color:C.muted}}>{head}</div><div style={{fontSize:25,fontWeight:900,color:C.text,marginTop:5}}>{label}</div></div>
           </div>
         </div>;
       })}
     </div>
     <div style={{borderRadius:30,background:'linear-gradient(145deg,#132942,#081725)',border:'1px solid rgba(150,195,230,.18)',boxShadow:'0 40px 100px rgba(0,0,0,.38)',padding:30,position:'relative',overflow:'hidden'}}>
       {step===0 && <div><div style={{fontSize:25,color:C.muted}}>Excel / Data</div><div style={{fontSize:44,fontWeight:1000,color:C.text,marginTop:42}}>Get Data</div><div style={{marginTop:35,display:'inline-block',padding:'18px 26px',borderRadius:16,background:`${C.cyan}18`,border:`1px solid ${C.cyan}66`,color:C.cyan,fontSize:30,fontWeight:950}}>From Text / CSV</div></div>}
       {step===1 && <div><div style={{fontSize:25,color:C.muted}}>customer_ids.csv / preview</div><div style={{fontSize:42,fontWeight:1000,color:C.text,marginTop:38}}>Before loading...</div><div style={{display:'flex',gap:18,marginTop:45}}><div style={{padding:'17px 24px',borderRadius:15,background:'#1a314c',color:C.muted,fontSize:26}}>Load</div><div style={{padding:'17px 24px',borderRadius:15,background:`${C.purple}22`,border:`1px solid ${C.purple}77`,color:C.purple,fontSize:26,fontWeight:950}}>Transform Data</div></div></div>}
       {step===2 && <div><div style={{fontSize:25,color:C.muted}}>Power Query Editor</div><div style={{marginTop:32,display:'grid',gridTemplateColumns:'260px 1fr',gap:14}}><div style={{padding:18,borderRadius:13,background:`${C.yellow}18`,border:`1px solid ${C.yellow}77`,color:C.text,fontSize:24,fontWeight:900}}>customer_id</div><div style={{padding:18,borderRadius:13,background:'#0e2035',color:C.text,fontSize:24}}>00123<br/>00047<br/>00301</div></div><div style={{marginTop:42,display:'flex',alignItems:'center',gap:18}}><div style={{fontSize:25,color:C.muted}}>Data Type</div><div style={{padding:'16px 24px',borderRadius:14,background:`${C.green}18`,border:`1px solid ${C.green}70`,color:C.green,fontSize:30,fontWeight:1000}}>ABC  Text</div></div></div>}
       {step===3 && <div><div style={{fontSize:25,color:C.muted}}>Power Query / final step</div><div style={{fontSize:52,fontWeight:1000,color:C.green,marginTop:46}}>Values preserved</div><div style={{fontSize:82,fontWeight:1000,color:C.text,marginTop:38,letterSpacing:3}}>00123</div><div style={{marginTop:50,display:'inline-block',padding:'18px 28px',borderRadius:15,background:`${C.green}20`,border:`1px solid ${C.green}66`,color:C.green,fontSize:28,fontWeight:950}}>Close & Load ✓</div></div>}
     </div>
   </div>
 </div>;
};

const LongId:React.FC=()=> {
 const frame=useCurrentFrame();
 const local=frame-2400;
 const opacity=clamp(local,[0,35,560,600],[0,1,1,0]);
 const p=clamp(local,[120,230],[0,1]);
 return <div style={{position:'absolute',inset:'110px 100px 70px',opacity,fontFamily:'Arial,Helvetica,sans-serif'}}>
   <Chip color={C.red}>PRECISION WARNING</Chip>
   <div style={{fontSize:58,fontWeight:1000,color:C.text,marginTop:24}}>Long identifiers can be damaged, not just reformatted.</div>
   <div style={{marginTop:70,padding:40,borderRadius:30,background:'rgba(30,8,14,.9)',border:`1px solid ${C.red}55`}}>
     <div style={{display:'grid',gridTemplateColumns:'1fr 120px 1fr',alignItems:'center',gap:20}}>
       <div style={{textAlign:'right',fontSize:48,fontWeight:950,color:C.text}}>12345678901234567890</div>
       <div style={{textAlign:'center',fontSize:50,color:C.red}}>→</div>
       <div style={{fontSize:48,fontWeight:950,color:C.red,opacity:p}}>1.23457E+19</div>
     </div>
     <div style={{marginTop:34,fontSize:27,color:C.muted,lineHeight:1.45}}>Excel documents that numeric data beyond 15 digits can lose precision. If digits were already lost, visual formatting cannot reconstruct the source.</div>
   </div>
   <div style={{marginTop:34,color:C.yellow,fontSize:29,fontWeight:900}}>Recovery rule: go back to the original source and re-import as Text.</div>
 </div>;
};

const AutoConversions:React.FC=()=> {
 const frame=useCurrentFrame();
 const local=frame-3000;
 const opacity=clamp(local,[0,35,560,600],[0,1,1,0]);
 return <div style={{position:'absolute',inset:'100px 120px 65px',opacity,fontFamily:'Arial,Helvetica,sans-serif'}}>
   <div style={{display:'grid',gridTemplateColumns:'.85fr 1.15fr',gap:54,alignItems:'center',height:'100%'}}>
     <div><Chip color={C.purple}>MICROSOFT 365 / EXCEL 2024</Chip><div style={{fontSize:58,fontWeight:1000,color:C.text,marginTop:28}}>A newer setting can stop some automatic conversions.</div><div style={{fontSize:27,color:C.muted,lineHeight:1.45,marginTop:26}}>If your version has it: Excel Options → Data → Automatic Data Conversions.</div><div style={{fontSize:23,color:C.yellow,lineHeight:1.45,marginTop:25}}>If you do not see the setting, use the Power Query import method.</div></div>
     <div style={{padding:34,borderRadius:30,background:'#eef3f8',color:'#15243a',boxShadow:'0 40px 110px rgba(0,0,0,.36)'}}>
       <div style={{fontSize:28,fontWeight:1000}}>Excel Options</div><div style={{fontSize:20,color:'#5a6b7f',marginTop:8}}>Data → Automatic Data Conversions</div>
       {[['Remove leading zeros and convert to a number',false],['Keep first 15 digits of long numbers',true],['Convert digits surrounding E to scientific notation',true]].map(([label,on],i)=><div key={String(label)} style={{display:'flex',alignItems:'center',gap:18,marginTop:28,padding:20,borderRadius:16,background:i===0?'#fff3f3':'#f8fafc',border:i===0?'1px solid #ff9ea3':'1px solid #dce4ec'}}>
         <div style={{width:24,height:24,borderRadius:5,border:'2px solid #597086',background:on?'#2e73d1':'white',display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontSize:18}}>{on?'✓':''}</div><div style={{fontSize:22,fontWeight:i===0?900:650}}>{label}</div>
       </div>)}
     </div>
   </div>
 </div>;
};

const Traps:React.FC=()=> {
 const frame=useCurrentFrame();
 const local=frame-3600;
 const opacity=clamp(local,[0,35,680,720],[0,1,1,0]);
 return <div style={{position:'absolute',inset:'105px 95px 70px',opacity,fontFamily:'Arial,Helvetica,sans-serif'}}>
   <div style={{fontSize:58,fontWeight:1000,color:C.text}}>Two fixes that are useful—but easy to misunderstand.</div>
   <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:32,marginTop:60}}>
     <div style={{padding:34,borderRadius:28,background:'rgba(14,31,51,.94)',border:`1px solid ${C.yellow}55`}}>
       <Chip color={C.yellow}>TRAP 1</Chip><div style={{fontSize:38,fontWeight:1000,color:C.text,marginTop:24}}>Custom number format</div>
       <div style={{fontSize:70,fontWeight:1000,color:C.text,marginTop:28}}>123 <span style={{color:C.yellow}}>→ 00123</span></div>
       <div style={{fontSize:25,lineHeight:1.45,color:C.muted,marginTop:28}}>This can change how a cell looks without changing the underlying value. Re-check what actually gets written when exporting CSV.</div>
     </div>
     <div style={{padding:34,borderRadius:28,background:'rgba(14,31,51,.94)',border:`1px solid ${C.purple}55`}}>
       <Chip color={C.purple}>TRAP 2</Chip><div style={{fontSize:38,fontWeight:1000,color:C.text,marginTop:24}}>TEXT formula</div>
       <div style={{fontSize:34,fontWeight:950,color:C.purple,marginTop:35}}>TEXT(A2, "00000")</div>
       <div style={{fontSize:25,lineHeight:1.45,color:C.muted,marginTop:38}}>Great for a known fixed width—only if the original digits still exist. It cannot restore digits lost through precision conversion.</div>
     </div>
   </div>
 </div>;
};

const Verify:React.FC=()=> {
 const frame=useCurrentFrame();
 const local=frame-4320;
 const {fps}=useVideoConfig();
 const enter=spring({frame:Math.max(0,local),fps,config:{damping:18,stiffness:90}});
 const p1=clamp(local,[60,120],[0,1]),p2=clamp(local,[180,240],[0,1]),p3=clamp(local,[300,360],[0,1]),p4=clamp(local,[420,480],[0,1]);
 return <div style={{position:'absolute',inset:'95px 100px 70px',fontFamily:'Arial,Helvetica,sans-serif',transform:`translateY(${(1-enter)*35}px)`}}>
   <div style={{display:'grid',gridTemplateColumns:'1.1fr .9fr',gap:44,height:'100%',alignItems:'center'}}>
     <div>
       <Chip color={C.green}>FINAL VALIDATION</Chip><div style={{fontSize:57,fontWeight:1000,color:C.text,marginTop:24}}>Verify the file, not just the Excel display.</div>
       <div style={{marginTop:44,padding:30,borderRadius:26,background:'#08131f',border:'1px solid rgba(255,255,255,.12)',fontFamily:'Consolas,monospace'}}>
         <div style={{color:C.muted,fontSize:18}}>customer_id,name</div><div style={{color:C.green,fontSize:30,marginTop:18}}>00123,Maya</div><div style={{color:C.green,fontSize:30,marginTop:12}}>00047,Arjun</div><div style={{color:C.green,fontSize:30,marginTop:12}}>00301,Ravi</div>
       </div>
       <div style={{fontSize:24,color:C.muted,marginTop:22}}>Open the exported CSV in a plain text editor and inspect a few identifiers directly.</div>
     </div>
     <div style={{display:'flex',flexDirection:'column',gap:18}}>
       {[
        [p1,'1','Import instead of blindly opening'],
        [p2,'2','Set identifier columns to Text'],
        [p3,'3','Validate the transformed values'],
        [p4,'4','Export, then inspect the raw CSV'],
       ].map(([p,n,t]:any)=><div key={n} style={{padding:'20px 24px',borderRadius:20,background:`rgba(117,239,173,${.05+.09*p})`,border:`1px solid rgba(117,239,173,${.18+.45*p})`,opacity:.35+.65*p,display:'flex',alignItems:'center',gap:18}}>
         <div style={{width:44,height:44,borderRadius:44,background:C.green,color:'#06120d',display:'flex',alignItems:'center',justifyContent:'center',fontSize:22,fontWeight:1000}}>{n}</div><div style={{fontSize:25,color:C.text,fontWeight:850}}>{t}</div>
       </div>)}
       <div style={{marginTop:24,fontSize:33,lineHeight:1.3,color:C.text,fontWeight:1000}}>The correct data type is part of the data.</div>
     </div>
   </div>
 </div>;
};

export const LeadingZerosLong:React.FC=()=>{
 const frame=useCurrentFrame();
 return <AbsoluteFill style={{fontFamily:'Arial,Helvetica,sans-serif',color:C.text}}>
   <Bg/><TopBar/>
   {frame<480&&<Hook/>}
   {frame>=480&&frame<960&&<Concept/>}
   {frame>=960&&frame<2400&&<ImportFlow/>}
   {frame>=2400&&frame<3000&&<LongId/>}
   {frame>=3000&&frame<3600&&<AutoConversions/>}
   {frame>=3600&&frame<4320&&<Traps/>}
   {frame>=4320&&<Verify/>}
   <Sequence from={0}><Audio src={staticFile('voice-long-001.mp3')} volume={1}/></Sequence>
   <Progress/>
 </AbsoluteFill>;
};

// render-trigger: long-001-001
