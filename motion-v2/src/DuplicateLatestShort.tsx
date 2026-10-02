import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';

const C={
  bg:'#eef2f6',
  dark:'#263746',
  ribbon:'#f6f8fa',
  text:'#1f2934',
  muted:'#697584',
  grid:'#d8dee6',
  blue:'#2f78c4',
  green:'#23875a',
  red:'#d94848',
  amber:'#c68a16',
  white:'#ffffff',
};

const lerp=(f:number,ins:number[],outs:number[])=>interpolate(f,ins,outs,{
  extrapolateLeft:'clamp',
  extrapolateRight:'clamp',
  easing:Easing.bezier(.2,.75,.2,1),
});

const capItems=[
  [0,78,'Newest is 01 Oct. Watch what survives.'],
  [78,195,'Sorted newest first.'],
  [195,300,'Remove Duplicates keeps 12 Sep.'],
  [300,435,'Distinct does not guarantee keep-first.'],
  [435,645,'Buffer the sorted table first.'],
  [645,780,'Then Distinct on Customer ID.'],
  [780,855,'Verify: 01 Oct now remains.'],
  [855,900,'Sort first. Buffer before Distinct.'],
] as const;

const Caption:React.FC=()=>{
  const f=useCurrentFrame();
  const item=capItems.find(([a,b])=>f>=a&&f<b);
  if(!item)return null;
  const [a,b,text]=item;
  const op=Math.min(lerp(f,[a,a+5],[0,1]),lerp(f,[b-6,b],[1,0]));
  return <div style={{
    position:'absolute',left:64,right:64,top:1544,zIndex:90,
    display:'flex',justifyContent:'center',opacity:op,pointerEvents:'none'
  }}>
    <div style={{
      background:'rgba(17,23,31,.82)',color:'#fff',
      borderRadius:14,padding:'12px 18px 13px',
      fontFamily:'Segoe UI, Arial, sans-serif',
      fontSize:38,lineHeight:1.12,fontWeight:650,whiteSpace:'nowrap',
      boxShadow:'0 8px 24px rgba(0,0,0,.22)'
    }}>{text}</div>
  </div>;
};

const Cursor:React.FC<{x:number;y:number;click?:number;opacity?:number}>=({x,y,click=0,opacity=1})=>{
  const s=1-click*.16;
  return <div style={{
    position:'absolute',left:x,top:y,width:34,height:48,zIndex:75,
    opacity,transform:`scale(${s})`,transformOrigin:'4px 4px',
    filter:'drop-shadow(0 2px 2px rgba(0,0,0,.28))'
  }}>
    <div style={{
      width:28,height:38,background:'#fff',
      clipPath:'polygon(0 0,0 34px,8px 26px,14px 39px,20px 36px,14px 23px,27px 22px)',
      border:'1px solid #111'
    }}/>
  </div>;
};

const Header:React.FC=()=> <div style={{
  position:'absolute',left:32,right:32,top:44,height:64,
  display:'flex',alignItems:'center',justifyContent:'space-between',
  fontFamily:'Segoe UI, Arial, sans-serif',
  fontSize:22,fontWeight:800,letterSpacing:1,color:'#566270',zIndex:55
}}>
  <span>FLOWMINUTE LAB</span>
  <span style={{color:C.blue}}>POWER QUERY / KEEP LATEST</span>
</div>;

type Row={id:string;updated:string;status:string;owner:string};
const newest:Row={id:'C-104',updated:'01 Oct 2026',status:'Active',owner:'Maya'};
const older:Row={id:'C-104',updated:'12 Sep 2026',status:'Active',owner:'Maya'};
const oldest:Row={id:'C-104',updated:'18 Aug 2026',status:'Pending',owner:'Maya'};
const otherA:Row={id:'C-219',updated:'29 Sep 2026',status:'Active',owner:'Arjun'};
const otherB:Row={id:'C-332',updated:'27 Sep 2026',status:'Active',owner:'Leah'};

const widths=[190,250,210,190];

const DataRow:React.FC<{
  row:Row;top:number;latest?:boolean;wrong?:boolean;opacity?:number;shiftY?:number;
}>=({row,top,latest=false,wrong=false,opacity=1,shiftY=0})=>{
  const vals=[row.id,row.updated,row.status,row.owner];
  let x=0;
  return <div style={{
    position:'absolute',left:0,top,right:0,height:68,
    opacity,transform:`translateY(${shiftY}px)`,
    background:wrong?'#fff1f1':latest?'#effaf4':'#fff'
  }}>
    {vals.map((v,i)=>{
      const left=x;x+=widths[i];
      return <div key={i} style={{
        position:'absolute',left,width:widths[i],height:68,
        borderRight:'1px solid #e0e5eb',borderBottom:'1px solid #e0e5eb',
        display:'flex',alignItems:'center',padding:'0 12px',boxSizing:'border-box',
        fontFamily:'Segoe UI, Arial',fontSize:19,
        color:wrong&&i===1?C.red:latest&&i===1?C.green:C.text,
        fontWeight:(wrong||latest)&&i===1?850:500
      }}>{v}</div>;
    })}
  </div>;
};

const ProofRail:React.FC=()=>{
  const f=useCurrentFrame();
  const p=lerp(f,[0,10,68,78],[0,1,1,0]);
  const swap=lerp(f,[26,44],[0,1]);
  return <div style={{
    position:'absolute',left:82,right:82,top:150,zIndex:70,
    opacity:p,transform:`translateY(${(1-p)*-18}px)`,
    borderRadius:16,background:'rgba(255,255,255,.97)',
    border:'1px solid #c8d2dc',boxShadow:'0 18px 45px rgba(30,45,60,.18)',
    padding:'16px 20px',fontFamily:'Segoe UI, Arial'
  }}>
    <div style={{fontSize:17,fontWeight:850,color:C.muted,letterSpacing:1}}>PROOF FIRST</div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 34px 1fr',alignItems:'center',gap:10,marginTop:10}}>
      <div style={{padding:'12px 14px',borderRadius:10,background:'#edf8f2',border:'1px solid #aad7bf'}}>
        <div style={{fontSize:15,color:C.green,fontWeight:800}}>SORTED TOP</div>
        <div style={{fontSize:29,fontWeight:900,color:C.text,marginTop:3}}>01 Oct</div>
      </div>
      <div style={{fontSize:28,color:C.muted,textAlign:'center'}}>→</div>
      <div style={{padding:'12px 14px',borderRadius:10,background:'#fff1f1',border:'1px solid #e5adad'}}>
        <div style={{fontSize:15,color:C.red,fontWeight:800}}>DUPLICATE KEPT</div>
        <div style={{
          fontSize:29,fontWeight:900,color:C.text,marginTop:3,
          transform:`scale(${.96+.04*swap})`
        }}>12 Sep</div>
      </div>
    </div>
  </div>;
};

const OutcomeSplit:React.FC=()=>{
  const f=useCurrentFrame();
  const p=lerp(f,[785,805,838,850],[0,1,1,0]);
  return <div style={{
    position:'absolute',left:72,right:72,top:1035,zIndex:72,
    opacity:p,display:'grid',gridTemplateColumns:'1fr 1fr',gap:16,
    fontFamily:'Segoe UI, Arial'
  }}>
    <div style={{borderRadius:14,background:'#fff1f1',border:'1px solid #e5aaaa',padding:'16px 18px'}}>
      <div style={{fontSize:16,fontWeight:900,color:C.red,letterSpacing:1}}>WRONG</div>
      <div style={{fontSize:30,fontWeight:900,color:C.text,marginTop:5}}>12 Sep survived</div>
    </div>
    <div style={{borderRadius:14,background:'#edf9f2',border:'1px solid #a7d4ba',padding:'16px 18px'}}>
      <div style={{fontSize:16,fontWeight:900,color:C.green,letterSpacing:1}}>FIXED</div>
      <div style={{fontSize:30,fontWeight:900,color:C.text,marginTop:5}}>01 Oct remains</div>
    </div>
  </div>;
};

const PowerQueryWindow:React.FC=()=>{
  const f=useCurrentFrame();
  const wrongPhase=f>=195&&f<435;
  const fixPhase=f>=435&&f<780;
  const fixedPhase=f>=780;
  const failZoom=Math.max(
    lerp(f,[190,225,285],[0,1,0]),
    lerp(f,[775,810,850],[0,1,0])
  );
  const scale=1+failZoom*.018;

  const removeP=lerp(f,[190,230],[0,1]);
  const newestGhost=f>=190&&f<285;
  const ghostOpacity=lerp(f,[190,208,260,285],[0,1,1,0]);
  const ghostShift=lerp(f,[190,285],[0,-72]);

  const cursorX=lerp(f,[78,120,165,205,435,520,630,720,790],[720,535,535,310,490,620,690,740,810]);
  const cursorY=lerp(f,[78,120,165,205,435,520,630,720,790],[690,335,335,340,905,905,1035,1110,1150]);
  const click=Math.max(
    lerp(f,[126,129,134],[0,1,0]),
    lerp(f,[205,208,213],[0,1,0]),
    lerp(f,[520,523,528],[0,1,0]),
    lerp(f,[720,723,728],[0,1,0])
  );

  const visibleRows=fixedPhase?[newest,otherA,otherB]:wrongPhase||fixPhase?[older,otherA,otherB]:[newest,older,oldest,otherA,otherB];

  return <div style={{
    position:'absolute',left:24,top:136,width:1032,height:1298,zIndex:10,
    transform:`scale(${scale})`,transformOrigin:'50% 45%'
  }}>
    <div style={{
      position:'absolute',inset:0,borderRadius:18,overflow:'hidden',
      background:'#fff',border:'1px solid #b7c0cb',
      boxShadow:'0 30px 80px rgba(22,34,48,.24)'
    }}>
      <div style={{
        height:56,background:C.dark,color:'#fff',display:'flex',alignItems:'center',
        padding:'0 18px',fontFamily:'Segoe UI, Arial',fontSize:21,fontWeight:650
      }}>
        Power Query Editor
        <span style={{marginLeft:18,opacity:.8,fontWeight:500}}>customer_updates.csv</span>
      </div>

      <div style={{
        height:55,background:C.ribbon,display:'flex',alignItems:'center',gap:28,
        padding:'0 22px',borderBottom:'1px solid #d6dde4',
        fontFamily:'Segoe UI, Arial',fontSize:18,color:'#3d4855'
      }}>
        {['Home','Transform','Add Column','View'].map((t,i)=><span key={t} style={{
          color:i===0?C.blue:'#3d4855',fontWeight:i===0?750:500
        }}>{t}</span>)}
      </div>

      <div style={{
        height:82,background:'#fff',borderBottom:'1px solid #dce2e8',
        display:'flex',alignItems:'center',gap:12,padding:'0 18px',
        fontFamily:'Segoe UI, Arial',fontSize:17
      }}>
        <div style={{padding:'10px 14px',border:'1px solid #cbd3dc',borderRadius:5}}>Keep Rows</div>
        <div style={{
          padding:'10px 14px',border:'1px solid #cbd3dc',borderRadius:5,
          background:f>=185&&f<285?'#eaf2fb':'#fff',
          color:f>=185&&f<285?C.blue:C.text,fontWeight:f>=185&&f<285?750:500
        }}>Remove Duplicates</div>
        <div style={{padding:'10px 14px',border:'1px solid #cbd3dc',borderRadius:5}}>Remove Rows</div>
      </div>

      <div style={{
        height:58,background:'#fafbfd',borderBottom:'1px solid #dce2e8',
        display:'flex',alignItems:'center',gap:10,padding:'0 16px',
        fontFamily:'Consolas, monospace',fontSize:16,color:'#33404d'
      }}>
        <div style={{
          width:34,height:34,border:'1px solid #c7d0d9',borderRadius:4,
          display:'flex',alignItems:'center',justifyContent:'center',
          fontFamily:'Segoe UI, Arial',color:C.muted,fontStyle:'italic'
        }}>fx</div>
        <div style={{
          flex:1,height:34,border:'1px solid #c7d0d9',borderRadius:4,
          display:'flex',alignItems:'center',padding:'0 10px',background:'#fff'
        }}>
          {fixPhase
            ? 'Buffered = Table.Buffer(#"Sorted Rows")'
            : fixedPhase
              ? 'LatestOnly = Table.Distinct(Buffered, {"CustomerID"})'
              : '#"Sorted Rows" = Table.Sort(Source,{{"Updated At", Order.Descending}})'}
        </div>
      </div>

      <div style={{position:'absolute',left:0,right:0,top:251,bottom:0,background:'#fff'}}>
        <div style={{position:'absolute',left:0,top:0,width:840,bottom:0,borderRight:'1px solid #d7dde5'}}>
          <div style={{
            position:'absolute',left:0,top:0,right:0,height:54,
            display:'grid',gridTemplateColumns:'190px 250px 210px 190px'
          }}>
            {['CustomerID','Updated At','Status','Owner'].map((h,i)=><div key={h} style={{
              borderRight:'1px solid #d9dfe6',borderBottom:'1px solid #d9dfe6',
              background:i===0&&f>=180&&f<285?'#eaf3fb':'#eef2f5',
              display:'flex',alignItems:'center',padding:'0 12px',
              fontFamily:'Segoe UI, Arial',fontSize:18,fontWeight:750,
              color:i===0&&f>=180&&f<285?C.blue:C.text
            }}>{h}{i===1&&f<195?<span style={{marginLeft:'auto',color:C.blue}}>▼</span>:null}</div>)}
          </div>

          {visibleRows.map((row,i)=><DataRow
            key={row.id+'-'+row.updated}
            row={row}
            top={54+i*68}
            wrong={(wrongPhase||fixPhase)&&row.id==='C-104'}
            latest={fixedPhase&&row.id==='C-104'}
            opacity={1}
          />)}

          {newestGhost&&<div style={{
            position:'absolute',left:0,top:54,right:0,height:68,zIndex:18,
            opacity:ghostOpacity,transform:`translateY(${ghostShift}px)`,
            background:'#effaf4',borderTop:'2px solid #8ac9a8',
            fontFamily:'Segoe UI, Arial',display:'flex',alignItems:'center'
          }}>
            <div style={{position:'absolute',left:12,top:10,bottom:10,width:816,border:'2px solid #df6b6b',borderRadius:7}}/>
            <div style={{
              position:'absolute',left:190,top:32,width:250,height:3,
              background:C.red,transform:`scaleX(${removeP})`,transformOrigin:'left'
            }}/>
            <div style={{paddingLeft:205,fontSize:20,fontWeight:900,color:C.red}}>01 Oct removed</div>
          </div>}

          {f>=80&&f<190&&<div style={{
            position:'absolute',left:188,top:410,width:430,
            padding:'16px 18px',borderRadius:12,
            background:'#eef6ff',border:'1px solid #a9c8ea',
            fontFamily:'Segoe UI, Arial',boxShadow:'0 12px 30px rgba(30,60,90,.12)'
          }}>
            <div style={{fontSize:16,fontWeight:900,color:C.blue,letterSpacing:1}}>SORTED NEWEST FIRST</div>
            <div style={{fontSize:31,fontWeight:900,color:C.text,marginTop:6}}>01 Oct is first</div>
          </div>}

          {wrongPhase&&<div style={{
            position:'absolute',left:74,top:405,width:675,
            padding:'18px 20px',borderRadius:14,
            background:'#fff1f1',border:'1px solid #e6a5a5',
            fontFamily:'Segoe UI, Arial',boxShadow:'0 16px 36px rgba(70,30,30,.15)'
          }}>
            <div style={{fontSize:17,fontWeight:900,color:C.red,letterSpacing:1}}>UNEXPECTED SURVIVOR</div>
            <div style={{fontSize:32,fontWeight:900,color:C.text,marginTop:7}}>12 Sep remained — not 01 Oct</div>
          </div>}

          {f>=300&&f<435&&<div style={{
            position:'absolute',left:64,top:560,width:700,
            padding:'17px 20px',borderRadius:12,
            background:'#fffaf0',border:'1px solid #e2c778',
            fontFamily:'Segoe UI, Arial'
          }}>
            <div style={{fontSize:17,fontWeight:900,color:C.amber}}>WHY</div>
            <div style={{fontSize:23,lineHeight:1.25,fontWeight:750,color:C.text,marginTop:6}}>
              Folding or optimization means “first row wins” is not guaranteed.
            </div>
          </div>}

          {fixPhase&&<div style={{
            position:'absolute',left:52,top:390,width:724,
            borderRadius:14,background:'#f7f9fb',border:'1px solid #cad3dd',
            padding:22,fontFamily:'Segoe UI, Arial',boxShadow:'0 16px 40px rgba(25,40,60,.12)'
          }}>
            <div style={{fontSize:17,fontWeight:900,color:C.blue,letterSpacing:1}}>MAKE KEEP-FIRST PREDICTABLE</div>
            <div style={{
              marginTop:14,padding:'15px 16px',borderRadius:8,
              background:'#1f2934',color:'#e8f1f7',
              fontFamily:'Consolas, monospace',fontSize:19,lineHeight:1.45
            }}>
              <div><span style={{color:'#8ed0ff'}}>Buffered</span> = Table.Buffer(#"Sorted Rows"),</div>
              <div><span style={{color:'#94e5b9'}}>LatestOnly</span> = Table.Distinct(Buffered, {'{"CustomerID"}'})</div>
            </div>
            <div style={{fontSize:17,color:C.muted,marginTop:11}}>Buffer the sorted result before Distinct decides what survives.</div>
          </div>}

          {fixedPhase&&<div style={{
            position:'absolute',left:76,top:400,width:660,
            padding:'18px 20px',borderRadius:14,
            background:'#edf9f2',border:'1px solid #9fd4b8',
            fontFamily:'Segoe UI, Arial',boxShadow:'0 16px 36px rgba(25,70,45,.12)'
          }}>
            <div style={{fontSize:17,fontWeight:900,color:C.green,letterSpacing:1}}>VERIFIED</div>
            <div style={{fontSize:32,fontWeight:900,color:C.text,marginTop:7}}>C-104 → 01 Oct remains</div>
          </div>}
        </div>

        <div style={{
          position:'absolute',right:0,top:0,width:192,bottom:0,background:'#f7f9fb',
          fontFamily:'Segoe UI, Arial',padding:16
        }}>
          <div style={{fontSize:19,fontWeight:800,color:C.text}}>Query Settings</div>
          <div style={{fontSize:14,fontWeight:750,color:C.muted,marginTop:25}}>APPLIED STEPS</div>
          {[
            'Source',
            'Changed Type',
            'Sorted Rows',
            fixPhase||fixedPhase?'Buffered':'Removed Duplicates',
            fixedPhase?'LatestOnly':null
          ].filter(Boolean).map((x,i)=><div key={String(x)} style={{
            marginTop:9,padding:'9px 10px',borderRadius:6,
            background:(x==='Buffered'||x==='LatestOnly')?'#e9f4ed':'#fff',
            border:'1px solid #dce2e7',fontSize:14,
            color:(x==='Buffered'||x==='LatestOnly')?C.green:C.text
          }}>{x}</div>)}
        </div>
      </div>
    </div>
    <Cursor x={cursorX} y={cursorY} click={click} opacity={f<830?1:0}/>
  </div>;
};

const FinalRule:React.FC=()=>{
  const f=useCurrentFrame();
  const p=lerp(f,[840,865],[0,1]);
  return <div style={{
    position:'absolute',left:100,right:100,top:395,zIndex:95,
    opacity:p,transform:`translateY(${(1-p)*20}px)`,
    textAlign:'center',fontFamily:'Segoe UI, Arial'
  }}>
    <div style={{fontSize:27,fontWeight:900,color:C.blue,letterSpacing:1.4}}>MEMORY RULE</div>
    <div style={{fontSize:57,lineHeight:1.06,fontWeight:900,color:C.text,marginTop:22}}>
      Sort first.
    </div>
    <div style={{fontSize:57,lineHeight:1.06,fontWeight:900,color:C.text,marginTop:8}}>
      Buffer before <span style={{color:C.green}}>Distinct.</span>
    </div>
  </div>;
};

export const DuplicateLatestShort:React.FC=()=>{
  const f=useCurrentFrame();
  const windowOpacity=lerp(f,[835,865],[1,0]);
  return <AbsoluteFill style={{
    background:'linear-gradient(180deg,#e8edf2 0%,#f4f6f9 72%,#e8edf2 100%)',
    fontFamily:'Segoe UI, Arial, sans-serif'
  }}>
    <Header/>
    <div style={{opacity:windowOpacity}}><PowerQueryWindow/></div>
    <ProofRail/>
    <OutcomeSplit/>
    <FinalRule/>

    <Sequence from={0}><Audio src={staticFile('voice-v5.mp3')} volume={1}/></Sequence>
    <Sequence from={195}><Audio src={staticFile('warning.wav')} volume={0.30}/></Sequence>
    {[126,205,520,720].map((fr,i)=>
      <Sequence key={i} from={fr}><Audio src={staticFile('ui-click.wav')} volume={0.25}/></Sequence>
    )}
    <Sequence from={782}><Audio src={staticFile('confirm.wav')} volume={0.30}/></Sequence>

    <Caption/>

    <div style={{
      position:'absolute',left:60,right:60,bottom:68,height:3,
      background:'rgba(40,56,72,.10)',borderRadius:3
    }}>
      <div style={{
        height:'100%',width:`${(f/899)*100}%`,
        background:`linear-gradient(90deg,${C.red},${C.blue},${C.green})`,
        borderRadius:3
      }}/>
    </div>
  </AbsoluteFill>;
};

// render-trigger: v5-002
