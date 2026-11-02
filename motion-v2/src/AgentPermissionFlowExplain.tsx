import React from 'react';
import {AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame} from 'remotion';
import flowTiming from './flowExplainTiming.json';

/**
 * FLOW//EXPLAIN: original animated, persistent dashboard.
 * SILENT / REVIEW ONLY until approved English voice, SRT and final creative gates.
 * 1080x1920 at 30 fps, 36 seconds, deterministic and zero external assets.
 */
const colors = {bg:'#080E19',panel:'#101B2B',raised:'#192638',border:'#314860',white:'#F3F7FB',muted:'#8EA3B6',cyan:'#37D4D0',amber:'#F0BA56',red:'#F16B73',green:'#55D7A2'};
const beats=[
  {start:0,end:6,step:'THE QUESTION',title:'What can an AI agent do?',sub:'A suggestion is not an action.',cap:'Can an AI agent delete your files?',tag:'REQUEST',color:colors.red},
  {start:6,end:12,step:'ONE IMPORTANT DIFFERENCE',title:'Reply vs. tool call',sub:'Words do not grant access.',cap:'Agents can request tool actions.',tag:'ACCESS',color:colors.cyan},
  {start:12,end:19,step:'SIMULATED EXAMPLE',title:'Delete request',sub:'No real files are touched.',cap:'A request arrives for demo files.',tag:'PREVIEW',color:colors.amber},
  {start:19,end:26,step:'SAFETY CHECK',title:'Permissions decide',sub:'Only allowed operations can run.',cap:'Check tool scope before approval.',tag:'PERMISSION',color:colors.cyan},
  {start:26,end:31,step:'HIGH-RISK ACTION',title:'Delete: blocked',sub:'Files remain in the sandbox.',cap:'Deny risky actions you do not need.',tag:'DENY',color:colors.red},
  {start:31,end:36,step:'MEMORY RULE',title:'Least privilege.',sub:'Grant only the access needed.',cap:'Read-only first. Review. Keep backups.',tag:'SAFE',color:colors.green},
] as const;
const card:React.CSSProperties={borderRadius:24,border:'2px solid '+colors.border,background:'#101B2B'};
const label:React.CSSProperties={fontSize:21,letterSpacing:1.2,fontWeight:700,color:colors.muted};
const dot=(color:string)=><span style={{display:'inline-block',width:12,height:12,borderRadius:'50%',background:color,marginRight:14}}/>;
const row:React.CSSProperties={display:'flex',alignItems:'center',padding:'15px 19px',borderRadius:14,background:'#15263A',border:'1px solid #2B4055',minHeight:70};
export const AgentPermissionFlowExplain:React.FC<{includeNarration?:boolean}>=({includeNarration=false})=>{
  const frame=useCurrentFrame();
  const sec=frame/30;
  const idx=Math.max(0,flowTiming.beat_starts.reduce((found,start,i)=>frame>=start?i:found,0));
  const beatStart=flowTiming.beat_starts[idx]/30;
  const beatEnd=(flowTiming.beat_starts[idx+1]??flowTiming.duration_frames)/30;
  const beat={...beats[idx],start:beatStart,end:beatEnd};
  const caption=flowTiming.cues.find(c=>frame>=c.start_frame && frame<c.end_frame)?.text??beat.cap;
  const progress=interpolate(frame,[0,flowTiming.duration_frames],[0,1],{extrapolateRight:'clamp'});
  const entered=interpolate(sec,[beat.start,beat.start+0.55],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const indicator=interpolate(sec,[beat.start,beat.end],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const inspector=
    idx===0?<><div style={{color:colors.red,fontWeight:800}}>REQUEST</div><div style={{fontSize:44,color:colors.red,textAlign:'center',marginTop:65}}>◈</div><div style={{marginTop:40,fontSize:24}}>delete(folder)</div><div style={{color:colors.muted,marginTop:12}}>not executed</div></>:
    idx===1?<><div style={{color:colors.cyan}}>TOOL REQUEST</div><div style={{marginTop:66,fontSize:29}}>ask()</div><div style={{marginTop:19,color:colors.muted}}>versus</div><div style={{marginTop:19,color:colors.amber,fontSize:27}}>execute()</div></>:
    idx===2?<><div style={{color:colors.amber}}>PENDING</div><div style={{marginTop:70,fontSize:28}}>delete(</div><div style={{color:colors.amber,fontSize:25,marginTop:6}}>"reports/"</div><div style={{fontSize:28,marginTop:6}}>)</div></>:
    idx===3?<><div style={{color:colors.cyan}}>CHECKING</div>{[['Scope','read only'],['Tool','no delete'],['Review','required']].map(([key,value],i)=>{const checked=indicator>(i+1)*0.22;return <div key={key} style={{border:'1px solid '+(checked?colors.green:colors.border),padding:13,borderRadius:10,marginTop:18,fontSize:22,color:checked?colors.green:colors.white}}>{dot(checked?colors.green:colors.muted)}{key}<div style={{color:colors.muted,fontSize:17,marginLeft:28}}>{value}</div></div>})}</>:
    idx===4?<><div style={{color:colors.red,fontWeight:800}}>DENIED</div><div style={{color:colors.red,fontSize:72,textAlign:'center',marginTop:70}}>×</div><div style={{color:colors.green,fontWeight:800,marginTop:40,textAlign:'center'}}>FILES SAFE</div></>:
    <><div style={{color:colors.green}}>SAFE MODE</div><div style={{border:'2px solid '+colors.green,color:colors.green,borderRadius:12,padding:20,marginTop:70,fontWeight:800}}>READ ONLY</div><div style={{marginTop:50}}>Approve only what is needed</div></>;
  return <AbsoluteFill style={{background:colors.bg,color:colors.white,fontFamily:'Inter, Arial, sans-serif',padding:'84px 72px',boxSizing:'border-box',overflow:'hidden'}}>
    <AbsoluteFill style={{opacity:.16,backgroundImage:'linear-gradient(#2A4B60 1px,transparent 1px),linear-gradient(90deg,#2A4B60 1px,transparent 1px)',backgroundSize:'68px 68px',pointerEvents:'none'}}/>
    {includeNarration ? <Audio src={staticFile('flow-explain-voice.wav')} /> : null}
    <div style={{...card,height:90,display:'flex',alignItems:'center',padding:'0 28px',gap:15,zIndex:1}}>
      <div style={{width:34,height:34,borderRadius:9,background:colors.cyan}}/><b style={{fontSize:29,letterSpacing:1}}>FLOWMINUTE</b>
      <span style={{...label,marginLeft:16}}> // EXPLAIN</span><span style={{marginLeft:'auto',color:colors.amber,fontSize:23,fontWeight:800}}>0{idx+1} / 06</span>
    </div>
    <div style={{position:'relative',marginTop:72,height:275,zIndex:1}}>
      <div style={{...label,color:beat.color}}>{beat.step}</div>
      <div style={{fontSize:61,lineHeight:1.08,fontWeight:850,letterSpacing:-1.5,marginTop:22,maxWidth:910,opacity:entered,transform:`translateY(${(1-entered)*12}px)`}}>{beat.title}</div>
      <div style={{fontSize:34,marginTop:22,color:colors.muted}}>{beat.sub}</div>
    </div>
    <div style={{...card,marginTop:0,height:915,zIndex:1,padding:25,boxSizing:'border-box'}}>
      <div style={{height:85,borderRadius:17,background:colors.raised,display:'flex',alignItems:'center',padding:'0 27px',gap:9}}>
        {dot(colors.red)}{dot(colors.amber)}{dot(colors.green)}
        <span style={{fontSize:25,marginLeft:20,fontWeight:750}}>agent_workspace / demo</span>
        <span style={{fontSize:19,color:colors.cyan,marginLeft:'auto'}}>SIM</span>
      </div>
      <div style={{display:'flex',gap:14,margin:'27px 10px 30px'}}>{beats.map((b,i)=><div key={i} style={{flex:1,height:9,background:i===idx?beat.color:i<idx?'#3A5669':'#1B3044',borderRadius:8}}/>)}</div>
      <div style={{display:'flex',gap:20,height:550}}>
        <div style={{...card,flex:1,padding:24,background:'#0C1728'}}>
          <div style={label}>FILES / SAMPLE</div>
          <div style={{borderBottom:'2px solid #294154',margin:'24px 0'}}/>
          {['reports/','budget_2026.csv','notes.txt'].map((f,i)=><div key={f} style={{...row,marginBottom:22,borderColor:idx===0&&i===0?colors.red:'#2B4055'}}>
            <span style={{color:i===0?colors.amber:colors.cyan,marginRight:18,fontSize:27}}>{i===0?'▣':'▤'}</span><b style={{fontSize:25,whiteSpace:'nowrap'}}>{f}</b>
          </div>)}
        </div>
        <div style={{...card,width:310,padding:23,background:'#0C1728',boxSizing:'border-box',fontSize:25}}>
          <div style={{...label,fontSize:19}}>ACTION INSPECTOR</div>
          <div style={{borderBottom:'2px solid #294154',margin:'24px 0'}}/>
          {inspector}
        </div>
      </div>
      <div style={{...card,marginTop:24,padding:'17px 25px',background:'#132437',fontSize:22,color:colors.muted,textAlign:'center'}}>TRAINING SIMULATION · NO REAL FILE ACCESS</div>
    </div>
    <div style={{...card,marginTop:40,height:124,padding:'24px 34px',boxSizing:'border-box',display:'flex',alignItems:'center',gap:24,zIndex:1}}>
      <div style={{width:8,height:72,background:beat.color,borderRadius:6}}/>
      <div style={{fontSize:29,fontWeight:730,lineHeight:1.18,overflowWrap:'break-word',maxWidth:810}}>{caption}</div>
    </div>
    <div style={{display:'flex',marginTop:'auto',fontSize:22,color:colors.muted,justifyContent:'space-between'}}>
      <span>0{idx+1} / 06  ·  {beat.tag}</span><span>ORIGINAL EXAMPLE</span>
    </div>
    <div style={{height:12,background:'#1D3041',borderRadius:10,marginTop:35,overflow:'hidden'}}><div style={{width:`${100*progress}%`,height:'100%',background:beat.color,borderRadius:10}}/></div>
  </AbsoluteFill>;
};
