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
  yellow:'#cf931d',
  white:'#ffffff',
};

const lerp=(f:number,ins:number[],outs:number[])=>interpolate(f,ins,outs,{
  extrapolateLeft:'clamp',
  extrapolateRight:'clamp',
  easing:Easing.bezier(.2,.75,.2,1),
});

const capItems=[
  [0,90,'Power Query can keep the wrong duplicate.'],
  [90,210,'Newest row is sorted to the top.'],
  [210,336,'Then Remove Duplicates keeps an older row.'],
  [336,510,'Distinct does not guarantee which duplicate survives.'],
  [510,675,'Buffer the sorted table before Distinct.'],
  [675,861,'Table.Buffer → then Table.Distinct on Customer ID.'],
  [861,948,'Now verify the latest date remains.'],
] as const;

const Caption:React.FC=()=>{
  const f=useCurrentFrame();
  const item=capItems.find(([a,b])=>f>=a&&f<b);
  if(!item)return null;
  const [a,b,text]=item;
  const op=Math.min(lerp(f,[a,a+5],[0,1]),lerp(f,[b-6,b],[1,0]));
  return <div style={{
    position:'absolute',left:68,right:68,top:1542,zIndex:70,
    display:'flex',justifyContent:'center',opacity:op,pointerEvents:'none'
  }}>
    <div style={{
      background:'rgba(17,23,31,.80)',color:'#fff',
      borderRadius:14,padding:'12px 18px 13px',
      fontFamily:'Segoe UI, Arial, sans-serif',
      fontSize:39,lineHeight:1.12,fontWeight:650,whiteSpace:'nowrap',
      boxShadow:'0 8px 24px rgba(0,0,0,.22)'
    }}>{text}</div>
  </div>;
};

const Cursor:React.FC<{x:number;y:number;click?:number;opacity?:number}>=({x,y,click=0,opacity=1})=>{
  const s=1-click*.16;
  return <div style={{
    position:'absolute',left:x,top:y,width:34,height:48,zIndex:65,
    opacity,transform:`scale(${s})`,transformOrigin:'4px 4px',
    filter:'drop-shadow(0 2px 2px rgba(0,0,0,.25))'
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
  fontSize:22,fontWeight:800,letterSpacing:1,color:'#566270',zIndex:50
}}>
  <span>FLOWMINUTE LAB</span>
  <span style={{color:C.blue}}>POWER QUERY / DUPLICATES</span>
</div>;

type Row={id:string;updated:string;status:string;owner:string};

const rows:Row[]=[
  {id:'C-104',updated:'01 Oct 2026',status:'Active',owner:'Maya'},
  {id:'C-104',updated:'12 Sep 2026',status:'Active',owner:'Maya'},
  {id:'C-104',updated:'18 Aug 2026',status:'Pending',owner:'Maya'},
  {id:'C-219',updated:'29 Sep 2026',status:'Active',owner:'Arjun'},
  {id:'C-332',updated:'27 Sep 2026',status:'Active',owner:'Leah'},
];

const GridRow:React.FC<{
  row:Row;top:number;
  wrong?:boolean;latest?:boolean;fade?:number
}>=({row,top,wrong=false,latest=false,fade=1})=>{
  const vals=[row.id,row.updated,row.status,row.owner];
  const widths=[190,250,210,190];
  let x=0;
  return <div style={{
    position:'absolute',left:0,top,right:0,height:68,
    display:'flex',opacity:fade,
    background:wrong?'#fff2f2':latest?'#effaf4':'#fff'
  }}>
    {vals.map((v,i)=>{
      const left=x;
      x+=widths[i];
      return <div key={i} style={{
        position:'absolute',left,width:widths[i],height:68,
        borderRight:'1px solid #e0e5eb',borderBottom:'1px solid #e0e5eb',
        display:'flex',alignItems:'center',padding:'0 12px',
        boxSizing:'border-box',fontFamily:'Segoe UI, Arial',
        fontSize:19,color:wrong&&i===1?C.red:latest&&i===1?C.green:C.text,
        fontWeight:(wrong||latest)&&i===1?800:500
      }}>{v}</div>;
    })}
  </div>;
};

const PowerQueryWindow:React.FC=()=>{
  const f=useCurrentFrame();
  const wrongPhase=f>=210&&f<520;
  const formulaPhase=f>=510&&f<805;
  const fixedPhase=f>=805;
  const removeP=lerp(f,[210,260],[0,1]);
  const fixP=lerp(f,[780,825],[0,1]);

  const cursorX=lerp(f,[0,70,120,175,235,300,560,650,760,825],[720,720,525,525,335,335,510,650,720,820]);
  const cursorY=lerp(f,[0,70,120,175,235,300,560,650,760,825],[660,660,320,320,320,360,890,890,1030,1130]);
  const click=Math.max(
    lerp(f,[72,75,80],[0,1,0]),
    lerp(f,[176,179,184],[0,1,0]),
    lerp(f,[258,261,266],[0,1,0]),
    lerp(f,[560,563,568],[0,1,0]),
    lerp(f,[760,763,768],[0,1,0])
  );

  const visibleRows = fixedPhase
    ? [rows[0],rows[3],rows[4]]
    : wrongPhase
      ? [rows[1],rows[3],rows[4]]
      : rows;

  return <div style={{position:'absolute',left:24,top:136,width:1032,height:1298,zIndex:10}}>
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
          background:f>=220&&f<330?'#eaf2fb':'#fff',
          color:f>=220&&f<330?C.blue:C.text,fontWeight:f>=220&&f<330?700:500
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
          {formulaPhase
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
              background:i===0&&f>=205&&f<330?'#eaf3fb':'#eef2f5',
              display:'flex',alignItems:'center',padding:'0 12px',
              fontFamily:'Segoe UI, Arial',fontSize:18,fontWeight:750,
              color:i===0&&f>=205&&f<330?C.blue:C.text
            }}>{h}{i===1&&f<210?<span style={{marginLeft:'auto',color:C.blue}}>▼</span>:null}</div>)}
          </div>

          {visibleRows.map((row,i)=><GridRow
            key={row.id+'-'+row.updated}
            row={row}
            top={54+i*68}
            wrong={wrongPhase&&row.id==='C-104'}
            latest={fixedPhase&&row.id==='C-104'}
            fade={1}
          />)}

          {f>=84&&f<205&&<div style={{
            position:'absolute',left:190,top:330,width:370,
            padding:'16px 18px',borderRadius:12,
            background:'#eef6ff',border:'1px solid #a9c8ea',
            fontFamily:'Segoe UI, Arial',boxShadow:'0 12px 30px rgba(30,60,90,.12)'
          }}>
            <div style={{fontSize:17,fontWeight:800,color:C.blue}}>SORTED NEWEST FIRST</div>
            <div style={{fontSize:28,fontWeight:850,color:C.text,marginTop:7}}>01 Oct 2026 is on top</div>
          </div>}

          {wrongPhase&&<div style={{
            position:'absolute',left:90,top:330,width:600,
            padding:'18px 20px',borderRadius:14,
            background:'#fff2f2',border:'1px solid #e6a5a5',
            fontFamily:'Segoe UI, Arial',boxShadow:'0 16px 36px rgba(70,30,30,.15)',
            opacity:removeP
          }}>
            <div style={{fontSize:18,fontWeight:900,color:C.red,letterSpacing:1}}>WRONG ROW KEPT</div>
            <div style={{fontSize:30,fontWeight:850,color:C.text,marginTop:8}}>12 Sep survived — not 01 Oct</div>
          </div>}

          {f>=345&&f<515&&<div style={{
            position:'absolute',left:65,top:520,width:690,
            padding:'20px 22px',borderRadius:14,
            background:'#fffaf0',border:'1px solid #e3c67c',
            fontFamily:'Segoe UI, Arial'
          }}>
            <div style={{fontSize:18,fontWeight:850,color:C.yellow}}>WHY THIS CAN HAPPEN</div>
            <div style={{fontSize:24,lineHeight:1.26,fontWeight:700,color:C.text,marginTop:9}}>
              Distinct can be folded or optimized. The kept duplicate is not guaranteed.
            </div>
          </div>}

          {formulaPhase&&<div style={{
            position:'absolute',left:55,top:420,width:720,
            borderRadius:14,background:'#f7f9fb',border:'1px solid #cad3dd',
            padding:22,fontFamily:'Segoe UI, Arial',boxShadow:'0 16px 40px rgba(25,40,60,.12)'
          }}>
            <div style={{fontSize:18,fontWeight:850,color:C.blue}}>DETERMINISTIC KEEP-FIRST PATTERN</div>
            <div style={{
              marginTop:16,padding:'14px 16px',borderRadius:8,
              background:'#1f2934',color:'#e8f1f7',
              fontFamily:'Consolas, monospace',fontSize:20,lineHeight:1.4
            }}>
              <div><span style={{color:'#8ed0ff'}}>Buffered</span> = Table.Buffer(#"Sorted Rows"),</div>
              <div><span style={{color:'#94e5b9'}}>LatestOnly</span> = Table.Distinct(Buffered, {'{"CustomerID"}'})</div>
            </div>
            <div style={{fontSize:17,color:C.muted,marginTop:12}}>Evaluate the sorted table before Distinct decides what to keep.</div>
          </div>}

          {fixedPhase&&<div style={{
            position:'absolute',left:78,top:330,width:650,
            padding:'18px 20px',borderRadius:14,
            background:'#eefaf4',border:'1px solid #9fd4b8',
            fontFamily:'Segoe UI, Arial',boxShadow:'0 16px 36px rgba(25,70,45,.12)',
            opacity:fixP
          }}>
            <div style={{fontSize:18,fontWeight:900,color:C.green,letterSpacing:1}}>VERIFIED</div>
            <div style={{fontSize:31,fontWeight:850,color:C.text,marginTop:8}}>C-104 → 01 Oct 2026 remains</div>
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
            formulaPhase||fixedPhase?'Buffered':'Removed Duplicates',
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
    <Cursor x={cursorX} y={cursorY} click={click} opacity={f<900?1:0}/>
  </div>;
};

const FinalRule:React.FC=()=>{
  const f=useCurrentFrame();
  const p=lerp(f,[930,980],[0,1]);
  return <div style={{
    position:'absolute',left:100,right:100,top:350,zIndex:80,
    opacity:p,transform:`translateY(${(1-p)*24}px)`,
    textAlign:'center',fontFamily:'Segoe UI, Arial'
  }}>
    <div style={{fontSize:28,fontWeight:850,color:C.blue,letterSpacing:1.4}}>MEMORY RULE</div>
    <div style={{fontSize:56,lineHeight:1.07,fontWeight:900,color:C.text,marginTop:22}}>
      Sort shows an order.
    </div>
    <div style={{fontSize:56,lineHeight:1.07,fontWeight:900,color:C.text,marginTop:10}}>
      Buffer makes that order <span style={{color:C.green}}>deterministic.</span>
    </div>
  </div>;
};

export const DuplicateLatestShort:React.FC=()=>{
  const f=useCurrentFrame();
  const windowOpacity=lerp(f,[910,950],[1,0]);
  return <AbsoluteFill style={{
    background:'linear-gradient(180deg,#e8edf2 0%,#f4f6f9 72%,#e8edf2 100%)',
    fontFamily:'Segoe UI, Arial, sans-serif'
  }}>
    <Header/>
    <div style={{opacity:windowOpacity}}><PowerQueryWindow/></div>
    <FinalRule/>

    <Sequence from={0}><Audio src={staticFile('voice-v5.mp3')} volume={1}/></Sequence>
    <Sequence from={225}><Audio src={staticFile('warning.wav')} volume={0.30}/></Sequence>
    {[72,176,258,560,760].map((fr,i)=>
      <Sequence key={i} from={fr}><Audio src={staticFile('ui-click.wav')} volume={0.25}/></Sequence>
    )}
    <Sequence from={812}><Audio src={staticFile('confirm.wav')} volume={0.30}/></Sequence>

    <Caption/>

    <div style={{
      position:'absolute',left:60,right:60,bottom:68,height:3,
      background:'rgba(40,56,72,.10)',borderRadius:3
    }}>
      <div style={{
        height:'100%',width:`${(f/1019)*100}%`,
        background:`linear-gradient(90deg,${C.red},${C.blue},${C.green})`,
        borderRadius:3
      }}/>
    </div>
  </AbsoluteFill>;
};

// render-trigger: v5-001
