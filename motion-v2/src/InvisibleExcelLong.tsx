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

const C={bg:'#071018',panel:'#0d1b29',panel2:'#132638',text:'#f6f9fc',muted:'#9cb0c2',green:'#58d68d',cyan:'#50d7ff',yellow:'#ffd166',red:'#ff6b6b',purple:'#b79cff',excel:'#217346'};
const clamp=(f:number,i:number[],o:number[])=>interpolate(f,i,o,{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(.2,.75,.2,1)});
const chapters=[
  [0,480,'WHY CLEAN DATA STILL BREAKS'],
  [480,1920,'BUG 1 · INVISIBLE SPACE'],
  [1920,3360,'BUG 2 · DATE LOCALE'],
  [3360,4800,'BUG 3 · DUPLICATE ORDER'],
  [4800,5760,'VERIFY · DON’T GUESS'],
] as const;

const Bg:React.FC=()=>{const f=useCurrentFrame();return <AbsoluteFill style={{background:'radial-gradient(circle at 50% 0%,#173650 0%,#081522 42%,#050a10 100%)',overflow:'hidden'}}>
  <div style={{position:'absolute',inset:-260,opacity:.22,transform:`perspective(1100px) rotateX(72deg) translateY(${360+(f*.14)%120}px)`,backgroundImage:'linear-gradient(rgba(80,215,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(80,215,255,.12) 1px,transparent 1px)',backgroundSize:'90px 90px',maskImage:'linear-gradient(to bottom,transparent,black 25%,black 78%,transparent)'}}/>
</AbsoluteFill>};

const Header:React.FC=()=>{const f=useCurrentFrame();const ch=chapters.find(([a,b])=>f>=a&&f<b);return <div style={{position:'absolute',top:32,left:54,right:54,zIndex:30,display:'flex',justifyContent:'space-between',fontFamily:'Arial',fontWeight:900,letterSpacing:1.4}}>
  <div style={{color:C.muted,fontSize:20}}>FLOWMINUTE LAB</div><div style={{color:C.cyan,fontSize:19}}>{ch?.[2]??''}</div>
</div>};

const Progress:React.FC=()=>{const f=useCurrentFrame();return <div style={{position:'absolute',left:54,right:54,bottom:24,height:4,zIndex:40,background:'rgba(255,255,255,.09)',borderRadius:6}}>
  <div style={{height:'100%',width:`${f/5759*100}%`,borderRadius:6,background:`linear-gradient(90deg,${C.cyan},${C.purple},${C.green})`}}/>
</div>};

const Chip:React.FC<{children:React.ReactNode;color?:string}>=({children,color=C.cyan})=><span style={{display:'inline-flex',padding:'7px 13px',borderRadius:999,border:`1px solid ${color}66`,background:`${color}18`,color,fontSize:18,fontWeight:900,letterSpacing:.6}}>{children}</span>;

const Window:React.FC<{title:string;children:React.ReactNode;accent?:string}>=({title,children,accent=C.excel})=><div style={{background:'#f7fafc',borderRadius:22,overflow:'hidden',boxShadow:'0 34px 95px rgba(0,0,0,.42)',border:'1px solid rgba(255,255,255,.18)'}}>
  <div style={{height:46,background:accent,display:'flex',alignItems:'center',padding:'0 18px',color:'white',fontFamily:'Arial',fontSize:17,fontWeight:800}}>
    <div style={{display:'flex',gap:8,marginRight:20}}><i style={{width:10,height:10,borderRadius:10,background:'#ff8a8a'}}/><i style={{width:10,height:10,borderRadius:10,background:'#ffd36b'}}/><i style={{width:10,height:10,borderRadius:10,background:'#82e3a7'}}/></div>{title}
  </div>{children}
</div>;

const Cell:React.FC<{children:React.ReactNode;head?:boolean;bad?:boolean;good?:boolean}>=({children,head,bad,good})=><div style={{padding:'13px 15px',fontFamily:'Arial',fontSize:20,fontWeight:head?900:650,color:bad?'#b4232c':good?'#117a43':'#203246',background:head?'#e7eef4':bad?'#fff0f1':good?'#edfff4':'white',borderRight:'1px solid #d7e0e8',borderBottom:'1px solid #d7e0e8'}}>{children}</div>;

const Hook:React.FC=()=>{const f=useCurrentFrame();const {fps}=useVideoConfig();const e=spring({frame:f,fps,config:{damping:17,stiffness:90}});const fade=clamp(f,[430,480],[1,0]);const cards=[
  ['XLOOKUP','#N/A','IDs look identical',C.red],
  ['DATE','03/08/2026','March 8… or 3 August?',C.yellow],
  ['DUPLICATES','Older row survived','Sorted first. Still wrong.',C.purple],
] as const;
return <div style={{position:'absolute',inset:'95px 86px 65px',fontFamily:'Arial',opacity:fade}}>
  <div style={{transform:`translateY(${(1-e)*28}px)`,textAlign:'center'}}><Chip color={C.red}>THREE INVISIBLE DATA BUGS</Chip><div style={{fontSize:68,lineHeight:1.04,color:C.text,fontWeight:1000,marginTop:20}}>Your Excel data looks clean.<br/>Why does it still break?</div><div style={{fontSize:27,color:C.muted,marginTop:20}}>Prove the failure. Diagnose the invisible cause. Fix it. Verify again.</div></div>
  <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:24,marginTop:55}}>
    {cards.map(([tag,value,desc,color],i)=><div key={tag} style={{padding:28,borderRadius:24,background:'rgba(13,27,41,.94)',border:`1px solid ${color}55`,transform:`translateY(${(1-clamp(f,[45+i*30,90+i*30],[0,1]))*30}px)`}}>
      <div style={{color,fontSize:17,fontWeight:950,letterSpacing:1.3}}>{tag}</div><div style={{color:C.text,fontSize:35,fontWeight:1000,marginTop:18}}>{value}</div><div style={{color:C.muted,fontSize:21,lineHeight:1.35,marginTop:15}}>{desc}</div>
    </div>)}
  </div>
</div>};

const HiddenSpace:React.FC=()=>{const f=useCurrentFrame();const l=f-480;const opacity=clamp(l,[0,30,1390,1440],[0,1,1,0]);const sweep=clamp(l,[260,520],[0,1]);const fixed=l>930;return <div style={{position:'absolute',inset:'88px 72px 58px',opacity,fontFamily:'Arial'}}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'end'}}><div><Chip color={C.cyan}>BUG 1 · XLOOKUP</Chip><div style={{fontSize:52,fontWeight:1000,color:C.text,marginTop:18}}>Two IDs look identical. One contains U+00A0.</div></div><div style={{fontSize:21,color:C.muted}}>non-breaking space · decimal 160</div></div>
  <div style={{display:'grid',gridTemplateColumns:'1.18fr .82fr',gap:30,marginTop:34}}>
    <Window title="Excel · customer_lookup.xlsx"><div style={{padding:20,position:'relative'}}>
      <div style={{display:'grid',gridTemplateColumns:'110px 1fr 1fr 1fr'}}>
        {['Row','Source ID','LEN','XLOOKUP'].map(x=><Cell key={x} head>{x}</Cell>)}
        <Cell>2</Cell><Cell>{fixed?'AB-2048':'AB-2048'}</Cell><Cell good={fixed}>{fixed?'7':'8'}</Cell><Cell bad={!fixed} good={fixed}>{fixed?'Maya Stone':'#N/A'}</Cell>
        <Cell>3</Cell><Cell>AB-3912</Cell><Cell>7</Cell><Cell>Arjun Rao</Cell>
      </div>
      <div style={{marginTop:24,padding:18,borderRadius:14,background:'#f3f6f9',border:'1px solid #d6e0e8',fontFamily:'Consolas',fontSize:22,color:'#24394b'}}>{fixed?'=TRIM(SUBSTITUTE(A2,UNICHAR(160),""))':'=UNICODE(RIGHT(A2,1))  →  160'}</div>
      {!fixed&&<div style={{position:'absolute',top:65,left:`${160+sweep*390}px`,width:90,height:110,background:'linear-gradient(90deg,transparent,rgba(80,215,255,.28),transparent)',borderLeft:`2px solid ${C.cyan}`,borderRight:`2px solid ${C.cyan}`,opacity:sweep}}/>}
    </div></Window>
    <div style={{display:'flex',flexDirection:'column',gap:18}}>
      <div style={{padding:25,borderRadius:22,background:'rgba(13,27,41,.94)',border:`1px solid ${C.cyan}55`}}><div style={{color:C.cyan,fontWeight:950,fontSize:20}}>DIAGNOSE</div><div style={{color:C.text,fontSize:31,fontWeight:1000,marginTop:12}}>LEN: 8 vs 7</div><div style={{color:C.muted,fontSize:22,lineHeight:1.4,marginTop:10}}>If strings look equal but lengths differ, inspect the character code.</div></div>
      <div style={{padding:25,borderRadius:22,background:'rgba(13,27,41,.94)',border:`1px solid ${C.green}55`}}><div style={{color:C.green,fontWeight:950,fontSize:20}}>FIX</div><div style={{color:C.text,fontSize:28,fontWeight:1000,marginTop:12}}>Replace 160, then TRIM</div><div style={{color:C.muted,fontSize:22,lineHeight:1.4,marginTop:10}}>TRIM alone targets normal ASCII spaces. Remove the non-breaking space explicitly.</div></div>
      <div style={{padding:21,borderRadius:18,background:fixed?'rgba(88,214,141,.13)':'rgba(255,107,107,.11)',border:`1px solid ${fixed?C.green:C.red}66`,color:fixed?C.green:C.red,fontSize:25,fontWeight:950}}>{fixed?'✓ XLOOKUP MATCH VERIFIED':'✕ LOOKUP FAILS'}</div>
    </div>
  </div>
</div>};

const DateLocale:React.FC=()=>{const f=useCurrentFrame();const l=f-1920;const opacity=clamp(l,[0,30,1390,1440],[0,1,1,0]);const split=clamp(l,[160,360],[0,1]);const fix=l>850;return <div style={{position:'absolute',inset:'88px 72px 58px',opacity,fontFamily:'Arial'}}>
  <Chip color={C.yellow}>BUG 2 · POWER QUERY DATES</Chip><div style={{fontSize:52,fontWeight:1000,color:C.text,marginTop:18}}>“03/08/2026” has no meaning without a culture.</div>
  <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:28,marginTop:40}}>
    <div style={{padding:30,borderRadius:26,background:'rgba(13,27,41,.95)',border:`1px solid ${C.yellow}55`}}><div style={{fontSize:21,color:C.muted}}>Same source text</div><div style={{fontSize:64,color:C.text,fontWeight:1000,marginTop:18}}>03/08/2026</div><div style={{height:2,background:'rgba(255,255,255,.08)',margin:'26px 0'}}/><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:18,opacity:split}}>
      <div style={{padding:22,borderRadius:18,background:'#17283a'}}><div style={{color:C.cyan,fontWeight:950}}>en-US</div><div style={{fontSize:35,color:C.text,fontWeight:1000,marginTop:14}}>Mar 8</div><div style={{color:C.muted,marginTop:7}}>month/day</div></div>
      <div style={{padding:22,borderRadius:18,background:'#17283a'}}><div style={{color:C.purple,fontWeight:950}}>en-GB</div><div style={{fontSize:35,color:C.text,fontWeight:1000,marginTop:14}}>3 Aug</div><div style={{color:C.muted,marginTop:7}}>day/month</div></div>
    </div></div>
    <Window title="Power Query Editor" accent="#2b579a"><div style={{padding:26}}>
      <div style={{fontSize:18,color:'#617487',fontWeight:800}}>TRANSFORM · DATA TYPE · USING LOCALE…</div>
      <div style={{marginTop:26,padding:22,borderRadius:15,background:'#eaf0f6'}}><div style={{fontSize:17,color:'#617487'}}>Data type</div><div style={{fontSize:25,fontWeight:900,color:'#203246',marginTop:7}}>Date</div></div>
      <div style={{marginTop:16,padding:22,borderRadius:15,background:fix?'#eafff1':'#fff7e2',border:`1px solid ${fix?'#99ddb3':'#f2ce76'}`}}><div style={{fontSize:17,color:'#617487'}}>Locale</div><div style={{fontSize:25,fontWeight:900,color:'#203246',marginTop:7}}>{fix?'English (United Kingdom)':'System default'}</div></div>
      <div style={{marginTop:25,fontSize:22,fontWeight:900,color:fix?'#167845':'#a76b00'}}>{fix?'✓ 03/08/2026 → 3 August 2026':'? Meaning depends on machine / query culture'}</div>
    </div></Window>
  </div>
  <div style={{marginTop:25,padding:'16px 22px',borderRadius:16,background:'rgba(255,209,102,.10)',border:'1px solid rgba(255,209,102,.35)',color:C.yellow,fontSize:22,fontWeight:900}}>Fix rule: parse text dates with an explicit locale or explicit format, then verify against a known source row.</div>
</div>};

const Duplicates:React.FC=()=>{const f=useCurrentFrame();const l=f-3360;const opacity=clamp(l,[0,30,1390,1440],[0,1,1,0]);const locked=l>770;const wrong=l>280&&l<770;return <div style={{position:'absolute',inset:'88px 72px 58px',opacity,fontFamily:'Arial'}}>
  <Chip color={C.purple}>BUG 3 · REMOVE DUPLICATES</Chip><div style={{fontSize:52,fontWeight:1000,color:C.text,marginTop:18}}>Sorted newest-first… but the older row survived.</div>
  <div style={{display:'grid',gridTemplateColumns:'1.15fr .85fr',gap:28,marginTop:36}}>
    <Window title="Power Query Editor" accent="#2b579a"><div style={{padding:22}}>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1.2fr'}}>
        {['CustomerID','Status','UpdatedAt'].map(x=><Cell key={x} head>{x}</Cell>)}
        <Cell>A-100</Cell><Cell good={!wrong||locked}>Gold</Cell><Cell>2026-10-06 09:12</Cell>
        {!locked&&<><Cell>A-100</Cell><Cell bad={wrong}>Silver</Cell><Cell>2026-09-28 14:03</Cell></>}
        <Cell>B-410</Cell><Cell>Active</Cell><Cell>2026-10-05 18:20</Cell>
      </div>
      <div style={{marginTop:22,padding:17,borderRadius:14,background:'#edf2f7',fontFamily:'Consolas',fontSize:19,color:'#203246'}}>{locked?'Buffered = Table.Buffer(Sorted)\nResult = Table.Distinct(Buffered, {"CustomerID"})':'Sorted = Table.Sort(Source, {{"UpdatedAt", Order.Descending}})\nResult = Table.Distinct(Sorted, {"CustomerID"})'}</div>
    </div></Window>
    <div>
      <div style={{padding:26,borderRadius:22,background:'rgba(13,27,41,.95)',border:`1px solid ${wrong?C.red:C.purple}55`}}><div style={{color:wrong?C.red:C.purple,fontWeight:950,fontSize:20}}>{wrong?'UNEXPECTED SURVIVOR':'WHY THIS CAN HAPPEN'}</div><div style={{color:C.text,fontSize:28,lineHeight:1.25,fontWeight:1000,marginTop:13}}>{wrong?'Older “Silver” row kept':'Table.Distinct does not promise which duplicate is preserved.'}</div><div style={{color:C.muted,fontSize:21,lineHeight:1.4,marginTop:14}}>Query folding and optimization can change evaluation. A visible sort is not a guarantee.</div></div>
      <div style={{marginTop:18,padding:26,borderRadius:22,background:locked?'rgba(88,214,141,.13)':'rgba(183,156,255,.11)',border:`1px solid ${locked?C.green:C.purple}66`}}><div style={{fontSize:20,color:locked?C.green:C.purple,fontWeight:950}}>{locked?'BUFFERED · ORDER FIXED':'PREDICTABLE PATTERN'}</div><div style={{fontSize:25,color:C.text,fontWeight:900,marginTop:12}}>Sort → Buffer → Distinct</div><div style={{fontSize:20,color:C.muted,lineHeight:1.4,marginTop:10}}>Use buffering here for correctness of the keep-first pattern—not as a universal performance optimization.</div></div>
    </div>
  </div>
</div>};

const Final:React.FC=()=>{const f=useCurrentFrame();const l=f-4800;const {fps}=useVideoConfig();const e=spring({frame:Math.max(0,l),fps,config:{damping:18,stiffness:90}});const items=[
  ['1','Strings look equal?','Compare LEN, then inspect character codes.',C.cyan],
  ['2','Dates look obvious?','Make the culture or format explicit.',C.yellow],
  ['3','Rows are sorted?','Verify evaluation order before deduping.',C.purple],
] as const;return <div style={{position:'absolute',inset:'88px 110px 58px',fontFamily:'Arial',transform:`translateY(${(1-e)*28}px)`}}>
  <Chip color={C.green}>FINAL CHECKLIST</Chip><div style={{fontSize:60,fontWeight:1000,color:C.text,marginTop:20}}>When data looks right but behaves wrong…</div><div style={{fontSize:27,color:C.muted,marginTop:14}}>Test invisible characters, culture, and evaluation order before blaming the formula.</div>
  <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:22,marginTop:55}}>{items.map(([n,h,b,color],i)=><div key={n} style={{padding:28,borderRadius:24,background:'rgba(13,27,41,.95)',border:`1px solid ${color}55`,opacity:.35+.65*clamp(l,[80+i*90,150+i*90],[0,1])}}><div style={{width:44,height:44,borderRadius:44,background:color,color:'#061018',display:'flex',alignItems:'center',justifyContent:'center',fontWeight:1000,fontSize:22}}>{n}</div><div style={{fontSize:28,color:C.text,fontWeight:1000,marginTop:20}}>{h}</div><div style={{fontSize:21,color:C.muted,lineHeight:1.42,marginTop:12}}>{b}</div></div>)}</div>
  <div style={{marginTop:45,padding:24,borderRadius:20,background:'rgba(88,214,141,.12)',border:'1px solid rgba(88,214,141,.38)',color:C.green,fontSize:28,fontWeight:950,textAlign:'center'}}>PROVE → DIAGNOSE → FIX → VERIFY</div>
</div>};

export const InvisibleExcelLong:React.FC=()=>{const f=useCurrentFrame();return <AbsoluteFill style={{fontFamily:'Arial',color:C.text}}><Bg/><Header/>
  {f<480&&<Hook/>}
  {f>=480&&f<1920&&<HiddenSpace/>}
  {f>=1920&&f<3360&&<DateLocale/>}
  {f>=3360&&f<4800&&<Duplicates/>}
  {f>=4800&&<Final/>}
  <Sequence from={0}><Audio src={staticFile('voice-long-002.mp3')} volume={1}/></Sequence>
  <Progress/>
</AbsoluteFill>};

// render-trigger: long-002-001
