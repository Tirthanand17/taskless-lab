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

const C={
  bg:'#eef2f6',
  excel:'#217346',
  excelDark:'#185c37',
  ribbon:'#f7f9fb',
  grid:'#d8dde3',
  text:'#1d2530',
  muted:'#66717f',
  blue:'#2b7cd3',
  red:'#d64545',
  green:'#1f8a55',
  yellow:'#d5951c',
  purple:'#7656c7',
  white:'#ffffff',
};

const capItems=[
  [0,93,'This date can mean two different days.'],
  [93,210,'03/08/2026 = Mar 8 OR 3 Aug.'],
  [210,339,'The wrong locale can interpret the CSV incorrectly.'],
  [339,444,'Changing the cell format is not the real fix.'],
  [444,624,'Power Query → Change Type → Using Locale.'],
  [624,771,"Choose Date and the source file's locale."],
  [771,864,'Then verify the day and month.'],
] as const;

const lerp=(f:number,ins:number[],outs:number[])=>interpolate(f,ins,outs,{
  extrapolateLeft:'clamp',extrapolateRight:'clamp',
  easing:Easing.bezier(.2,.75,.2,1),
});

const Caption:React.FC=()=>{
  const f=useCurrentFrame();
  const item=capItems.find(([a,b])=>f>=a&&f<b);
  if(!item) return null;
  const [a,b,text]=item;
  const op=Math.min(lerp(f,[a,a+5],[0,1]),lerp(f,[b-6,b],[1,0]));
  return <div style={{
    position:'absolute',left:70,right:70,top:1538,zIndex:60,
    display:'flex',justifyContent:'center',opacity:op,pointerEvents:'none'
  }}>
    <div style={{
      padding:'12px 18px 13px',borderRadius:14,
      background:'rgba(17,23,31,.78)',color:'#fff',
      fontFamily:'Segoe UI, Arial, sans-serif',
      fontSize:39,fontWeight:650,lineHeight:1.12,
      whiteSpace:'nowrap',boxShadow:'0 8px 24px rgba(0,0,0,.22)'
    }}>{text}</div>
  </div>;
};

const Cursor:React.FC<{x:number;y:number;click?:number;opacity?:number}>=({x,y,click=0,opacity=1})=>{
  const s=1-click*.16;
  return <div style={{
    position:'absolute',left:x,top:y,width:34,height:48,zIndex:55,
    opacity,transform:`scale(${s})`,transformOrigin:'4px 4px',
    filter:'drop-shadow(0 2px 2px rgba(0,0,0,.3))'
  }}>
    <div style={{
      width:28,height:38,background:'#fff',
      clipPath:'polygon(0 0, 0 34px, 8px 26px, 14px 39px, 20px 36px, 14px 23px, 27px 22px)',
      border:'1px solid #111'
    }}/>
  </div>;
};

const Cell:React.FC<{
  x:number;y:number;w:number;h:number;text:string;
  selected?:boolean;fill?:string;color?:string;fontWeight?:number;
}>=({x,y,w,h,text,selected=false,fill='#fff',color=C.text,fontWeight=500})=>
  <div style={{
    position:'absolute',left:x,top:y,width:w,height:h,
    borderRight:`1px solid ${C.grid}`,borderBottom:`1px solid ${C.grid}`,
    background:fill,color,fontFamily:'Segoe UI, Arial, sans-serif',
    fontSize:24,fontWeight,display:'flex',alignItems:'center',
    padding:'0 12px',boxSizing:'border-box',
    boxShadow:selected?`inset 0 0 0 3px ${C.excel}`:'none',
    zIndex:selected?4:1
  }}>{text}</div>;

const SpreadsheetUI:React.FC=()=>{
  const f=useCurrentFrame();
  const formatPhase=lerp(f,[315,365],[0,1]);
  const fade=lerp(f,[420,455],[1,0]);
  const cursorX=lerp(f,[0,45,110,170,270,345,405],[720,720,510,510,700,760,760]);
  const cursorY=lerp(f,[0,45,110,170,270,345,405],[730,730,740,740,360,355,355]);
  const click=Math.max(
    lerp(f,[45,48,53],[0,1,0]),
    lerp(f,[345,348,353],[0,1,0])
  );
  const selectedDate=formatPhase>.45?'03-Aug-2026':'03/08/2026';

  return <div style={{position:'absolute',left:35,top:160,width:1010,height:1240,opacity:fade}}>
    <div style={{
      position:'absolute',inset:0,borderRadius:18,overflow:'hidden',
      boxShadow:'0 28px 70px rgba(26,39,53,.22)',border:'1px solid #b9c2cc',
      background:'#fff'
    }}>
      <div style={{
        height:56,background:C.excelDark,color:'#fff',display:'flex',
        alignItems:'center',padding:'0 18px',fontFamily:'Segoe UI, Arial',
        fontSize:21,fontWeight:600
      }}>
        <span style={{fontWeight:800,marginRight:20}}>Spreadsheet</span>
        <span style={{opacity:.9}}>orders_aug.csv</span>
        <span style={{marginLeft:'auto',opacity:.75}}>Local CSV</span>
      </div>
      <div style={{
        height:55,background:C.ribbon,borderBottom:'1px solid #d5dbe2',
        display:'flex',alignItems:'center',gap:26,padding:'0 22px',
        fontFamily:'Segoe UI, Arial',fontSize:19,color:'#36404d'
      }}>
        {['File','Home','Insert','Data','Formulas','Review','View'].map((t,i)=>
          <div key={t} style={{
            height:'100%',display:'flex',alignItems:'center',
            color:t==='Home'&&f<315?C.excel:(t==='Data'&&f>=315?C.excel:'#37414e'),
            borderBottom:(t==='Home'&&f<315)||(t==='Data'&&f>=315)?`3px solid ${C.excel}`:'3px solid transparent',
            fontWeight:(t==='Home'&&f<315)||(t==='Data'&&f>=315)?700:500
          }}>{t}</div>
        )}
      </div>
      <div style={{
        height:86,background:'#fff',borderBottom:'1px solid #d8dee5',
        display:'flex',alignItems:'center',gap:12,padding:'0 18px',
        fontFamily:'Segoe UI, Arial'
      }}>
        <div style={{width:112,height:40,border:'1px solid #c7ced7',borderRadius:3,display:'flex',alignItems:'center',paddingLeft:10,color:'#4a5562',fontSize:18}}>B2</div>
        <div style={{color:'#7a8490',fontStyle:'italic',fontSize:21}}>fx</div>
        <div style={{height:40,flex:1,border:'1px solid #c7ced7',borderRadius:3,display:'flex',alignItems:'center',padding:'0 12px',fontSize:20,color:'#303946'}}>03/08/2026</div>
        <div style={{
          width:170,height:44,border:'1px solid #c7ced7',borderRadius:4,
          display:'flex',alignItems:'center',justifyContent:'center',
          background:f>=315?'#f6f8fa':'#fff',fontSize:18,color:'#384350'
        }}>{formatPhase>.45?'dd-mmm-yyyy':'General'}</div>
      </div>

      <div style={{position:'absolute',left:0,right:0,top:197,bottom:0,background:'#fff'}}>
        <div style={{position:'absolute',left:0,top:0,width:48,bottom:0,background:'#f3f5f7',borderRight:'1px solid #d9dfe6'}}/>
        <div style={{position:'absolute',left:48,top:0,right:0,height:38,background:'#f3f5f7',borderBottom:'1px solid #d9dfe6'}}/>
        {['A','B','C','D'].map((h,i)=><div key={h} style={{
          position:'absolute',left:48+i*235,top:0,width:235,height:38,
          borderRight:'1px solid #d9dfe6',display:'flex',alignItems:'center',justifyContent:'center',
          fontFamily:'Segoe UI, Arial',fontSize:18,color:'#5b6673'
        }}>{h}</div>)}
        {[1,2,3,4,5,6,7].map((r,i)=><div key={r} style={{
          position:'absolute',left:0,top:38+i*70,width:48,height:70,
          borderBottom:'1px solid #d9dfe6',display:'flex',alignItems:'center',justifyContent:'center',
          fontFamily:'Segoe UI, Arial',fontSize:17,color:'#5b6673'
        }}>{r}</div>)}

        <Cell x={48} y={38} w={235} h={70} text="order_id" fill="#eef5f0" fontWeight={700}/>
        <Cell x={283} y={38} w={235} h={70} text="order_date" fill="#eef5f0" fontWeight={700}/>
        <Cell x={518} y={38} w={235} h={70} text="region" fill="#eef5f0" fontWeight={700}/>
        <Cell x={753} y={38} w={235} h={70} text="amount" fill="#eef5f0" fontWeight={700}/>

        <Cell x={48} y={108} w={235} h={70} text="A-1042"/>
        <Cell x={283} y={108} w={235} h={70} text={selectedDate} selected fill="#fff"/>
        <Cell x={518} y={108} w={235} h={70} text="London"/>
        <Cell x={753} y={108} w={235} h={70} text="$1,240"/>

        <Cell x={48} y={178} w={235} h={70} text="A-1043"/>
        <Cell x={283} y={178} w={235} h={70} text="12/09/2026"/>
        <Cell x={518} y={178} w={235} h={70} text="Manchester"/>
        <Cell x={753} y={178} w={235} h={70} text="$980"/>

        <Cell x={48} y={248} w={235} h={70} text="A-1044"/>
        <Cell x={283} y={248} w={235} h={70} text="25/12/2026"/>
        <Cell x={518} y={248} w={235} h={70} text="Leeds"/>
        <Cell x={753} y={248} w={235} h={70} text="$2,150"/>

        <div style={{
          position:'absolute',left:64,top:395,right:30,height:2,background:'#eef1f4'
        }}/>

        {f>=72&&f<225&&<div style={{
          position:'absolute',left:90,top:390,right:90,height:285,
          display:'grid',gridTemplateColumns:'1fr 1fr',gap:22,zIndex:10
        }}>
          <div style={{
            borderRadius:18,background:'#f9fbfd',border:'1px solid #c9d6e4',
            padding:24,boxShadow:'0 12px 32px rgba(30,50,70,.12)'
          }}>
            <div style={{fontFamily:'Segoe UI, Arial',fontSize:20,fontWeight:800,color:C.blue}}>US ORDER</div>
            <div style={{fontFamily:'Segoe UI, Arial',fontSize:46,fontWeight:800,color:C.text,marginTop:24}}>MAR 8</div>
            <div style={{fontFamily:'Segoe UI, Arial',fontSize:18,color:C.muted,marginTop:8}}>month / day / year</div>
          </div>
          <div style={{
            borderRadius:18,background:'#f9fbfd',border:'1px solid #c9d6e4',
            padding:24,boxShadow:'0 12px 32px rgba(30,50,70,.12)'
          }}>
            <div style={{fontFamily:'Segoe UI, Arial',fontSize:20,fontWeight:800,color:C.green}}>UK / INDIA ORDER</div>
            <div style={{fontFamily:'Segoe UI, Arial',fontSize:46,fontWeight:800,color:C.text,marginTop:24}}>3 AUG</div>
            <div style={{fontFamily:'Segoe UI, Arial',fontSize:18,color:C.muted,marginTop:8}}>day / month / year</div>
          </div>
          <div style={{
            position:'absolute',left:'50%',top:-26,transform:'translateX(-50%)',
            padding:'8px 16px',borderRadius:999,background:'#fff0f0',
            border:'1px solid #e7a2a2',color:C.red,fontFamily:'Segoe UI, Arial',
            fontSize:18,fontWeight:800
          }}>AMBIGUOUS</div>
        </div>}

        {f>=330&&f<444&&<div style={{
          position:'absolute',left:610,top:380,width:310,
          borderRadius:16,background:'#fff',border:'1px solid #ccd4dd',
          boxShadow:'0 18px 42px rgba(26,39,53,.2)',padding:18,zIndex:12,
          fontFamily:'Segoe UI, Arial'
        }}>
          <div style={{fontSize:18,fontWeight:700,color:C.text}}>Number format changed</div>
          <div style={{fontSize:17,color:C.muted,marginTop:8}}>Cell now displays 03-Aug-2026</div>
          <div style={{
            marginTop:14,padding:'9px 12px',borderRadius:8,
            background:'#fff3f3',color:C.red,fontSize:17,fontWeight:750
          }}>Display changed. Interpretation did not.</div>
        </div>}
      </div>
    </div>
    <Cursor x={cursorX} y={cursorY} click={click} opacity={f<425?1:0}/>
  </div>;
};

const PowerQueryUI:React.FC=()=>{
  const f=useCurrentFrame();
  const enter=lerp(f,[420,455],[0,1]);
  const exit=lerp(f,[840,875],[1,0]);

  const context=f>=510&&f<615;
  const submenu=f>=555&&f<650;
  const dialog=f>=620&&f<760;
  const applied=f>=760;
  const curX=lerp(f,[455,505,545,600,665,720,770],[700,520,565,650,600,605,810]);
  const curY=lerp(f,[455,505,545,600,665,720,770],[615,405,620,655,780,990,1120]);
  const click=Math.max(
    lerp(f,[505,508,513],[0,1,0]),
    lerp(f,[555,558,563],[0,1,0]),
    lerp(f,[620,623,628],[0,1,0]),
    lerp(f,[720,723,728],[0,1,0]),
    lerp(f,[755,758,763],[0,1,0])
  );

  return <div style={{
    position:'absolute',left:25,top:140,width:1030,height:1295,
    opacity:enter*exit,transform:`translateY(${(1-enter)*35}px)`
  }}>
    <div style={{
      position:'absolute',inset:0,borderRadius:18,overflow:'hidden',
      boxShadow:'0 30px 80px rgba(20,32,45,.24)',border:'1px solid #b7c0cb',background:'#fff'
    }}>
      <div style={{
        height:56,background:'#2c3e50',color:'#fff',display:'flex',alignItems:'center',
        padding:'0 18px',fontFamily:'Segoe UI, Arial',fontSize:21,fontWeight:650
      }}>
        Power Query Editor
        <span style={{marginLeft:18,opacity:.8,fontWeight:500}}>orders_aug.csv</span>
      </div>
      <div style={{
        height:55,background:'#f6f8fa',display:'flex',alignItems:'center',
        gap:28,padding:'0 22px',borderBottom:'1px solid #d6dce3',
        fontFamily:'Segoe UI, Arial',fontSize:18,color:'#3d4855'
      }}>
        {['Home','Transform','Add Column','View'].map((t,i)=><span key={t} style={{fontWeight:i===1?700:500,color:i===1?C.green:'#3d4855'}}>{t}</span>)}
      </div>
      <div style={{
        height:80,background:'#fff',borderBottom:'1px solid #dde2e8',
        display:'flex',alignItems:'center',gap:14,padding:'0 20px',
        fontFamily:'Segoe UI, Arial',fontSize:17,color:'#4b5663'
      }}>
        <div style={{padding:'10px 14px',border:'1px solid #cfd6de',borderRadius:5}}>Data Type: ABC 123</div>
        <div style={{padding:'10px 14px',border:'1px solid #cfd6de',borderRadius:5}}>Detect Data Type</div>
        <div style={{padding:'10px 14px',border:'1px solid #cfd6de',borderRadius:5}}>Replace Values</div>
      </div>

      <div style={{position:'absolute',left:0,right:0,top:191,bottom:0,background:'#fff'}}>
        <div style={{position:'absolute',left:0,top:0,width:780,bottom:0,borderRight:'1px solid #d7dee5'}}>
          <div style={{position:'absolute',left:0,top:0,right:0,height:52,display:'grid',gridTemplateColumns:'200px 280px 170px 130px'}}>
            {['order_id','order_date','region','amount'].map((h,i)=><div key={h} style={{
              borderRight:'1px solid #d9dfe6',borderBottom:'1px solid #d9dfe6',
              background:i===1?'#eaf5ee':'#eef2f5',display:'flex',alignItems:'center',
              padding:'0 12px',fontFamily:'Segoe UI, Arial',fontSize:18,fontWeight:750,
              color:i===1?C.green:C.text,boxShadow:i===1?`inset 0 3px 0 ${C.green}`:'none'
            }}>
              <span style={{fontSize:14,marginRight:8,color:i===1?C.green:'#65717f'}}>{i===1?(applied?'📅':'ABC 123'):'ABC'}</span>{h}
            </div>)}
          </div>
          {[
            ['A-1042',applied?'03/08/2026':'03/08/2026','London','$1,240'],
            ['A-1043',applied?'12/09/2026':'12/09/2026','Manchester','$980'],
            ['A-1044',applied?'25/12/2026':'25/12/2026','Leeds','$2,150'],
          ].map((row,r)=><div key={r} style={{
            position:'absolute',left:0,top:52+r*66,right:0,height:66,
            display:'grid',gridTemplateColumns:'200px 280px 170px 130px'
          }}>
            {row.map((v,c)=><div key={c} style={{
              borderRight:'1px solid #e0e5eb',borderBottom:'1px solid #e0e5eb',
              display:'flex',alignItems:'center',padding:'0 12px',
              fontFamily:'Segoe UI, Arial',fontSize:19,color:C.text,
              background:c===1&&applied?'#f2fbf5':'#fff'
            }}>{v}</div>)}
          </div>)}

          {applied&&<div style={{
            position:'absolute',left:18,top:300,width:720,height:150,
            borderRadius:12,background:'#f7fafc',border:'1px solid #d9e1e8',
            padding:18,fontFamily:'Segoe UI, Arial'
          }}>
            <div style={{fontSize:17,fontWeight:800,color:C.green}}>Locale conversion applied</div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:12,marginTop:14}}>
              <div style={{padding:12,borderRadius:8,background:'#fff',border:'1px solid #dbe2e8'}}><b>Date</b><br/>03 Aug 2026</div>
              <div style={{padding:12,borderRadius:8,background:'#fff',border:'1px solid #dbe2e8'}}><b>Day</b><br/>3</div>
              <div style={{padding:12,borderRadius:8,background:'#fff',border:'1px solid #dbe2e8'}}><b>Month</b><br/>8</div>
            </div>
          </div>}

          {context&&<div style={{
            position:'absolute',left:290,top:40,width:260,
            background:'#fff',border:'1px solid #bfc8d1',boxShadow:'0 12px 30px rgba(0,0,0,.18)',
            borderRadius:6,padding:'7px 0',fontFamily:'Segoe UI, Arial',zIndex:20
          }}>
            {['Remove','Rename','Change Type','Replace Values','Fill','Unpivot Columns'].map((x,i)=><div key={x} style={{
              height:42,display:'flex',alignItems:'center',padding:'0 16px',
              background:i===2&&f>=545?'#e8f1fb':'#fff',fontSize:17,color:C.text
            }}>{x}{i===2?<span style={{marginLeft:'auto'}}>›</span>:null}</div>)}
          </div>}

          {submenu&&<div style={{
            position:'absolute',left:540,top:120,width:255,
            background:'#fff',border:'1px solid #bfc8d1',boxShadow:'0 12px 30px rgba(0,0,0,.18)',
            borderRadius:6,padding:'7px 0',fontFamily:'Segoe UI, Arial',zIndex:21
          }}>
            {['Text','Whole Number','Decimal Number','Date','Using Locale…'].map((x,i)=><div key={x} style={{
              height:42,display:'flex',alignItems:'center',padding:'0 16px',
              background:i===4&&f>=600?'#e8f1fb':'#fff',fontSize:17,color:i===4?C.blue:C.text,fontWeight:i===4?700:500
            }}>{x}</div>)}
          </div>}

          {dialog&&<div style={{
            position:'absolute',left:110,top:270,width:560,height:430,
            borderRadius:10,background:'#fff',border:'1px solid #adb8c4',
            boxShadow:'0 28px 70px rgba(20,30,42,.28)',zIndex:30,
            fontFamily:'Segoe UI, Arial',padding:28
          }}>
            <div style={{fontSize:24,fontWeight:750,color:C.text}}>Change Column Type with Locale</div>
            <div style={{fontSize:17,color:C.muted,marginTop:8}}>Interpret the source value using an explicit locale.</div>
            <div style={{fontSize:16,color:C.muted,marginTop:28}}>Data Type</div>
            <div style={{height:48,border:'1px solid #bfc7d0',borderRadius:5,marginTop:6,display:'flex',alignItems:'center',padding:'0 14px',fontSize:20}}>Date <span style={{marginLeft:'auto'}}>⌄</span></div>
            <div style={{fontSize:16,color:C.muted,marginTop:22}}>Locale</div>
            <div style={{height:48,border:'1px solid #bfc7d0',borderRadius:5,marginTop:6,display:'flex',alignItems:'center',padding:'0 14px',fontSize:20}}>English (United Kingdom) <span style={{marginLeft:'auto'}}>⌄</span></div>
            <div style={{display:'flex',justifyContent:'flex-end',gap:12,marginTop:34}}>
              <div style={{padding:'10px 22px',border:'1px solid #bfc7d0',borderRadius:5,fontSize:18}}>Cancel</div>
              <div style={{padding:'10px 26px',borderRadius:5,fontSize:18,fontWeight:700,background:C.blue,color:'#fff'}}>OK</div>
            </div>
          </div>}
        </div>

        <div style={{
          position:'absolute',right:0,top:0,width:250,bottom:0,background:'#f7f9fb',
          fontFamily:'Segoe UI, Arial',padding:18
        }}>
          <div style={{fontSize:20,fontWeight:800,color:C.text}}>Query Settings</div>
          <div style={{fontSize:16,fontWeight:700,color:C.muted,marginTop:28}}>APPLIED STEPS</div>
          {['Source','Promoted Headers',applied?'Changed Type with Locale':'Changed Type'].map((x,i)=><div key={x} style={{
            marginTop:10,padding:'10px 12px',borderRadius:6,background:i===2?'#e9f3ec':'#fff',
            border:'1px solid #dce2e7',fontSize:16,color:i===2?C.green:C.text
          }}>{x}</div>)}
        </div>
      </div>
    </div>
    <Cursor x={curX} y={curY} click={click}/>
  </div>;
};

const FinalRule:React.FC=()=>{
  const f=useCurrentFrame();
  const p=lerp(f,[840,890],[0,1]);
  return <div style={{
    position:'absolute',left:100,right:100,top:320,zIndex:50,
    opacity:p,transform:`translateY(${(1-p)*26}px)`,
    fontFamily:'Segoe UI, Arial',textAlign:'center'
  }}>
    <div style={{fontSize:28,fontWeight:800,color:C.green,letterSpacing:1.5}}>MEMORY RULE</div>
    <div style={{fontSize:58,lineHeight:1.08,fontWeight:900,color:C.text,marginTop:22}}>
      Format changes how a date <span style={{color:C.blue}}>looks.</span>
    </div>
    <div style={{fontSize:58,lineHeight:1.08,fontWeight:900,color:C.text,marginTop:10}}>
      Locale changes what it <span style={{color:C.green}}>means.</span>
    </div>
  </div>;
};

export const DateLocaleShort:React.FC=()=>{
  const f=useCurrentFrame();
  return <AbsoluteFill style={{
    background:'linear-gradient(180deg,#e8edf2 0%,#f4f6f9 70%,#e9edf2 100%)',
    fontFamily:'Segoe UI, Arial, sans-serif'
  }}>
    <div style={{
      position:'absolute',left:32,top:46,right:32,height:64,
      display:'flex',alignItems:'center',justifyContent:'space-between',
      color:'#55616e',fontSize:22,fontWeight:800,letterSpacing:1
    }}>
      <span>FLOWMINUTE LAB</span>
      <span style={{color:C.green}}>EXCEL / POWER QUERY</span>
    </div>

    <SpreadsheetUI/>
    <PowerQueryUI/>
    <FinalRule/>

    <Sequence from={0}><Audio src={staticFile('voice-v4.mp3')} volume={1}/></Sequence>
    <Sequence from={93}><Audio src={staticFile('warning.wav')} volume={0.32}/></Sequence>
    {[45,505,555,620,720,755].map((fr,i)=>
      <Sequence key={i} from={fr}><Audio src={staticFile('ui-click.wav')} volume={0.26}/></Sequence>
    )}
    <Sequence from={760}><Audio src={staticFile('confirm.wav')} volume={0.28}/></Sequence>

    <Caption/>

    <div style={{
      position:'absolute',left:60,right:60,bottom:68,height:3,
      borderRadius:3,background:'rgba(40,56,72,.10)'
    }}>
      <div style={{
        height:'100%',width:`${(f/959)*100}%`,borderRadius:3,
        background:`linear-gradient(90deg,${C.red},${C.blue},${C.green})`
      }}/>
    </div>
  </AbsoluteFill>;
};

// render-trigger: v4-001
