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
  bg:'#eef3f7',
  dark:'#243444',
  ribbon:'#f6f8fa',
  text:'#202a35',
  muted:'#687584',
  grid:'#d7dee6',
  green:'#1f7d52',
  red:'#d24747',
  blue:'#2878c7',
  amber:'#b98216',
  cyan:'#21a6c7',
  white:'#ffffff',
};

const tween=(f:number,ins:number[],outs:number[])=>interpolate(f,ins,outs,{
  extrapolateLeft:'clamp',
  extrapolateRight:'clamp',
  easing:Easing.bezier(.2,.75,.2,1),
});

const captions=[
  [0,75,'Same-looking IDs. XLOOKUP says #N/A.'],
  [75,180,'One invisible character is different.'],
  [180,300,'LEN: 7 vs 8. Last Unicode = 160.'],
  [300,420,'TRIM alone cannot remove NBSP 160.'],
  [420,660,'Replace character 160, then TRIM.'],
  [660,810,'Run XLOOKUP again: match found.'],
  [810,900,'Looks equal? Check LEN, then Unicode.'],
] as const;

const Caption:React.FC=()=>{
  const f=useCurrentFrame();
  const item=captions.find(([a,b])=>f>=a&&f<b);
  if(!item)return null;
  const [a,b,text]=item;
  const opacity=Math.min(tween(f,[a,a+5],[0,1]),tween(f,[b-6,b],[1,0]));
  return <div style={{
    position:'absolute',left:55,right:55,top:1546,zIndex:100,
    display:'flex',justifyContent:'center',opacity,pointerEvents:'none'
  }}>
    <div style={{
      background:'rgba(20,27,35,.84)',color:'#fff',borderRadius:14,
      padding:'12px 18px 13px',fontFamily:'Segoe UI, Arial, sans-serif',
      fontSize:37,fontWeight:650,lineHeight:1.12,whiteSpace:'nowrap',
      boxShadow:'0 8px 24px rgba(0,0,0,.2)'
    }}>{text}</div>
  </div>;
};

const Cursor:React.FC<{x:number;y:number;click?:number;opacity?:number}>=({x,y,click=0,opacity=1})=>{
  const s=1-click*.16;
  return <div style={{
    position:'absolute',left:x,top:y,width:32,height:46,zIndex:88,
    opacity,transform:`scale(${s})`,transformOrigin:'4px 4px',
    filter:'drop-shadow(0 2px 2px rgba(0,0,0,.28))'
  }}>
    <div style={{
      width:27,height:37,background:'#fff',
      clipPath:'polygon(0 0,0 33px,8px 25px,14px 38px,20px 35px,14px 22px,27px 21px)',
      border:'1px solid #111'
    }}/>
  </div>;
};

const Header:React.FC=()=> <div style={{
  position:'absolute',left:34,right:34,top:42,height:64,
  display:'flex',alignItems:'center',justifyContent:'space-between',
  fontFamily:'Segoe UI, Arial, sans-serif',fontSize:22,fontWeight:850,
  letterSpacing:1,color:'#566270',zIndex:60
}}>
  <span>FLOWMINUTE LAB</span>
  <span style={{color:C.green}}>EXCEL X-RAY / HIDDEN SPACE</span>
</div>;

const ProofCard:React.FC=()=>{
  const f=useCurrentFrame();
  const p=tween(f,[0,8,62,74],[0,1,1,0]);
  return <div style={{
    position:'absolute',left:92,right:92,top:146,zIndex:78,opacity:p,
    transform:`translateY(${(1-p)*-15}px)`,fontFamily:'Segoe UI, Arial',
    background:'rgba(255,255,255,.97)',border:'1px solid #c8d2dc',
    borderRadius:16,padding:'16px 20px',boxShadow:'0 18px 44px rgba(28,43,58,.18)'
  }}>
    <div style={{fontSize:16,fontWeight:900,color:C.muted,letterSpacing:1}}>PROOF FIRST</div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 34px 1fr',alignItems:'center',gap:10,marginTop:10}}>
      <div style={{padding:'12px 14px',borderRadius:10,background:'#eff8f3',border:'1px solid #a8d1ba'}}>
        <div style={{fontSize:14,fontWeight:900,color:C.green}}>LOOKUP VALUE</div>
        <div style={{fontSize:29,fontWeight:900,color:C.text,marginTop:3}}>AB-2048</div>
      </div>
      <div style={{fontSize:27,color:C.muted,textAlign:'center'}}>→</div>
      <div style={{padding:'12px 14px',borderRadius:10,background:'#fff0f0',border:'1px solid #e2aaaa'}}>
        <div style={{fontSize:14,fontWeight:900,color:C.red}}>XLOOKUP RESULT</div>
        <div style={{fontSize:29,fontWeight:900,color:C.red,marginTop:3}}>#N/A</div>
      </div>
    </div>
  </div>;
};

const XRayOverlay:React.FC=()=>{
  const f=useCurrentFrame();
  const opacity=tween(f,[78,90,164,178],[0,1,1,0]);
  if(opacity<=0)return null;
  const scan=tween(f,[92,150],[0,1]);
  const reveal=tween(f,[118,145],[0,1]);
  return <div style={{
    position:'absolute',left:160,top:392,width:260,height:74,zIndex:70,
    opacity,fontFamily:'Segoe UI, Arial',pointerEvents:'none'
  }}>
    <div style={{
      position:'absolute',left:0,top:0,right:0,bottom:0,
      border:'2px solid rgba(33,166,199,.9)',borderRadius:7,
      boxShadow:'0 0 0 4px rgba(33,166,199,.08), 0 0 26px rgba(33,166,199,.28)'
    }}/>
    <div style={{
      position:'absolute',left:scan*246,top:-7,width:4,height:88,
      background:'#6de3ff',boxShadow:'0 0 18px rgba(109,227,255,.9)'
    }}/>
    <div style={{
      position:'absolute',left:178,top:-74,width:360,padding:'12px 14px',
      borderRadius:12,background:'rgba(28,47,60,.97)',color:'#fff',
      opacity:reveal,transform:`translateY(${(1-reveal)*8}px)`,
      boxShadow:'0 14px 34px rgba(15,35,50,.25)'
    }}>
      <div style={{fontSize:14,fontWeight:900,letterSpacing:1.2,color:'#8eeaff'}}>EXPLANATORY X-RAY</div>
      <div style={{fontSize:23,fontWeight:900,marginTop:4}}>NBSP · U+00A0 · 160</div>
      <div style={{fontSize:14,opacity:.82,marginTop:3}}>Invisible trailing character</div>
    </div>
  </div>;
};

const SheetRow:React.FC<{top:number;id:string;name:string;clean?:string;focus?:boolean;fixed?:boolean}>=({top,id,name,clean='',focus=false,fixed=false})=>{
  const vals=[id,name,clean];
  const widths=[260,250,260];
  let left=0;
  return <div style={{position:'absolute',left:0,right:0,top,height:68,background:focus?'#fff8ec':'#fff'}}>
    {vals.map((v,i)=>{
      const x=left; left+=widths[i];
      return <div key={i} style={{
        position:'absolute',left:x,top:0,width:widths[i],height:68,
        display:'flex',alignItems:'center',padding:'0 12px',boxSizing:'border-box',
        borderRight:'1px solid #e0e5eb',borderBottom:'1px solid #e0e5eb',
        fontFamily:'Segoe UI, Arial',fontSize:20,color:C.text,
        fontWeight:(focus&&i===0)||(fixed&&i===2)?800:500,
        background:fixed&&i===2?'#eff9f3':undefined
      }}>{v}</div>;
    })}
  </div>;
};

const ExcelWindow:React.FC=()=>{
  const f=useCurrentFrame();
  const diagnose=f>=180&&f<420;
  const fix=f>=420&&f<690;
  const verify=f>=690;
  const cleanReady=f>=545;
  const resultOk=f>=710;

  const cursorX=tween(f,[0,70,180,245,305,420,520,620,700,780],[785,785,445,610,650,445,520,655,815,815]);
  const cursorY=tween(f,[0,70,180,245,305,420,520,620,700,780],[420,420,730,730,730,730,730,730,428,428]);
  const click=Math.max(
    tween(f,[44,47,52],[0,1,0]),
    tween(f,[238,241,246],[0,1,0]),
    tween(f,[520,523,528],[0,1,0]),
    tween(f,[704,707,712],[0,1,0])
  );

  const formula=f<180
    ? '=XLOOKUP(F4,B7:B10,C7:C10)'
    : f<300
      ? '=UNICODE(RIGHT(B7,1))'
      : f<420
        ? '=TRIM(B7)'
        : f<690
          ? '=TRIM(SUBSTITUTE(B7,UNICHAR(160)," "))'
          : '=XLOOKUP(F4,D7:D10,C7:C10)';

  return <div style={{
    position:'absolute',left:26,top:132,width:1028,height:1305,zIndex:15,
    fontFamily:'Segoe UI, Arial'
  }}>
    <div style={{
      position:'absolute',inset:0,borderRadius:18,overflow:'hidden',
      background:'#fff',border:'1px solid #b7c0cb',
      boxShadow:'0 30px 80px rgba(22,34,48,.23)'
    }}>
      <div style={{
        height:56,background:C.green,color:'#fff',display:'flex',alignItems:'center',
        padding:'0 18px',fontSize:21,fontWeight:700
      }}>
        Excel
        <span style={{marginLeft:18,opacity:.88,fontWeight:500}}>customer_lookup.xlsx</span>
      </div>

      <div style={{
        height:54,background:C.ribbon,display:'flex',alignItems:'center',gap:27,
        padding:'0 22px',borderBottom:'1px solid #d6dde4',fontSize:18,color:'#3d4855'
      }}>
        {['Home','Insert','Page Layout','Formulas','Data','Review','View'].map((t,i)=><span key={t} style={{
          color:i===0?C.green:'#3d4855',fontWeight:i===0?800:500
        }}>{t}</span>)}
      </div>

      <div style={{
        height:78,background:'#fff',borderBottom:'1px solid #dce2e8',
        display:'flex',alignItems:'center',gap:12,padding:'0 18px',fontSize:16
      }}>
        <div style={{padding:'9px 12px',border:'1px solid #cbd3dc',borderRadius:5}}>Paste</div>
        <div style={{padding:'9px 12px',border:'1px solid #cbd3dc',borderRadius:5}}>Wrap Text</div>
        <div style={{padding:'9px 12px',border:'1px solid #cbd3dc',borderRadius:5}}>Format as Table</div>
        <div style={{padding:'9px 12px',border:'1px solid #cbd3dc',borderRadius:5}}>Find & Select</div>
      </div>

      <div style={{
        height:58,background:'#fafbfd',borderBottom:'1px solid #dce2e8',
        display:'flex',alignItems:'center',gap:10,padding:'0 16px'
      }}>
        <div style={{
          width:34,height:34,border:'1px solid #c7d0d9',borderRadius:4,
          display:'flex',alignItems:'center',justifyContent:'center',
          color:C.muted,fontStyle:'italic'
        }}>fx</div>
        <div style={{
          flex:1,height:34,border:'1px solid #c7d0d9',borderRadius:4,
          display:'flex',alignItems:'center',padding:'0 10px',background:'#fff',
          fontFamily:'Consolas, monospace',fontSize:16,color:'#33404d'
        }}>{formula}</div>
      </div>

      <div style={{position:'absolute',left:0,right:0,top:246,bottom:0,background:'#fff'}}>
        <div style={{position:'absolute',left:0,top:0,width:770,bottom:0,borderRight:'1px solid #d7dde5'}}>
          <div style={{
            position:'absolute',left:0,top:0,right:0,height:52,
            display:'grid',gridTemplateColumns:'260px 250px 260px'
          }}>
            {['Customer ID','Customer','Clean ID'].map((h,i)=><div key={h} style={{
              borderRight:'1px solid #d9dfe6',borderBottom:'1px solid #d9dfe6',
              background:'#eef2f5',display:'flex',alignItems:'center',padding:'0 12px',
              fontSize:18,fontWeight:800,color:i===2&&fix?C.green:C.text
            }}>{h}</div>)}
          </div>

          <SheetRow top={52} id="AB-2048" name="Mira Stores" clean={cleanReady?'AB-2048':''} focus fixed={cleanReady}/>
          <SheetRow top={120} id="AB-3170" name="Northline" clean={cleanReady?'AB-3170':''}/>
          <SheetRow top={188} id="AB-5502" name="Haven Retail" clean={cleanReady?'AB-5502':''}/>
          <SheetRow top={256} id="AB-8124" name="Solace Co." clean={cleanReady?'AB-8124':''}/>

          {f>=180&&f<300&&<div style={{
            position:'absolute',left:70,top:382,width:625,padding:'18px 20px',
            borderRadius:14,background:'#eef7ff',border:'1px solid #a8c8e8',
            boxShadow:'0 15px 34px rgba(30,55,85,.12)'
          }}>
            <div style={{fontSize:15,fontWeight:900,color:C.blue,letterSpacing:1}}>DIAGNOSE</div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginTop:12}}>
              <div style={{padding:'12px 14px',background:'#fff',borderRadius:9,border:'1px solid #d8e3ed'}}>
                <div style={{fontSize:15,color:C.muted}}>Lookup value LEN</div>
                <div style={{fontSize:36,fontWeight:900,color:C.green}}>7</div>
              </div>
              <div style={{padding:'12px 14px',background:'#fff6e8',borderRadius:9,border:'1px solid #ead0a3'}}>
                <div style={{fontSize:15,color:C.muted}}>Source ID LEN</div>
                <div style={{fontSize:36,fontWeight:900,color:C.amber}}>8</div>
              </div>
            </div>
            <div style={{fontSize:20,fontWeight:800,color:C.text,marginTop:13}}>
              UNICODE(RIGHT(B7,1)) → <span style={{color:C.red}}>160</span>
            </div>
          </div>}

          {f>=300&&f<420&&<div style={{
            position:'absolute',left:72,top:390,width:620,padding:'18px 20px',
            borderRadius:14,background:'#fff1f1',border:'1px solid #e1adad'
          }}>
            <div style={{fontSize:15,fontWeight:900,color:C.red,letterSpacing:1}}>WHY TRIM FAILS</div>
            <div style={{fontSize:27,fontWeight:900,color:C.text,marginTop:8}}>TRIM(B7) still has LEN 8</div>
            <div style={{fontSize:17,color:C.muted,marginTop:7}}>Character 160 is not the normal space character 32.</div>
          </div>}

          {fix&&<div style={{
            position:'absolute',left:54,top:385,width:665,padding:'20px 22px',
            borderRadius:14,background:'#f7f9fb',border:'1px solid #cbd5df',
            boxShadow:'0 16px 38px rgba(28,45,62,.12)'
          }}>
            <div style={{fontSize:15,fontWeight:900,color:C.green,letterSpacing:1}}>FIX THE TEXT, NOT THE ERROR MESSAGE</div>
            <div style={{
              marginTop:13,padding:'15px 15px',borderRadius:8,background:'#1f2934',
              color:'#eef5fa',fontFamily:'Consolas, monospace',fontSize:18,lineHeight:1.42
            }}>
              =TRIM(SUBSTITUTE(B7,<br/>
              <span style={{color:'#8eeaff'}}>UNICHAR(160)</span>," "))
            </div>
            <div style={{fontSize:17,color:C.muted,marginTop:11}}>Replace the hidden NBSP, then trim normal spacing.</div>
          </div>}

          {verify&&<div style={{
            position:'absolute',left:72,top:388,width:620,padding:'18px 20px',
            borderRadius:14,background:'#edf9f2',border:'1px solid #9fd4b8',
            boxShadow:'0 16px 36px rgba(25,70,45,.12)'
          }}>
            <div style={{fontSize:15,fontWeight:900,color:C.green,letterSpacing:1}}>VERIFIED</div>
            <div style={{fontSize:29,fontWeight:900,color:C.text,marginTop:7}}>XLOOKUP → Mira Stores</div>
            <div style={{fontSize:17,color:C.muted,marginTop:5}}>Exact match works after the hidden character is removed.</div>
          </div>}
        </div>

        <div style={{
          position:'absolute',right:0,top:0,width:257,bottom:0,background:'#f7f9fb',
          padding:'18px 16px',boxSizing:'border-box'
        }}>
          <div style={{fontSize:17,fontWeight:850,color:C.text}}>Lookup test</div>
          <div style={{fontSize:13,fontWeight:800,color:C.muted,marginTop:22}}>LOOKUP ID</div>
          <div style={{
            marginTop:7,padding:'12px 10px',border:'2px solid #67a477',borderRadius:5,
            background:'#fff',fontSize:22,fontWeight:850,color:C.text
          }}>AB-2048</div>
          <div style={{fontSize:13,fontWeight:800,color:C.muted,marginTop:20}}>RESULT</div>
          <div style={{
            marginTop:7,padding:'13px 10px',borderRadius:7,
            background:resultOk?'#e9f7ef':'#fff0f0',
            border:`1px solid ${resultOk?'#a5d0b7':'#e1aaaa'}`,
            fontSize:24,fontWeight:900,color:resultOk?C.green:C.red
          }}>{resultOk?'Mira Stores':'#N/A'}</div>
          <div style={{fontSize:13,color:C.muted,marginTop:18,lineHeight:1.4}}>
            Exact-match XLOOKUP compares the text values, not how they look on screen.
          </div>
        </div>
      </div>
    </div>

    <XRayOverlay/>
    <Cursor x={cursorX} y={cursorY} click={click} opacity={f<800?1:0}/>
  </div>;
};

const FinalRule:React.FC=()=>{
  const f=useCurrentFrame();
  const p=tween(f,[805,835],[0,1]);
  return <div style={{
    position:'absolute',left:95,right:95,top:400,zIndex:96,
    opacity:p,transform:`translateY(${(1-p)*18}px)`,
    textAlign:'center',fontFamily:'Segoe UI, Arial'
  }}>
    <div style={{fontSize:26,fontWeight:900,color:C.cyan,letterSpacing:1.4}}>MEMORY RULE</div>
    <div style={{fontSize:54,lineHeight:1.08,fontWeight:900,color:C.text,marginTop:22}}>
      Looks equal?
    </div>
    <div style={{fontSize:54,lineHeight:1.08,fontWeight:900,color:C.text,marginTop:7}}>
      Check <span style={{color:C.green}}>LEN</span>, then <span style={{color:C.blue}}>Unicode.</span>
    </div>
  </div>;
};

export const HiddenSpaceXrayShort:React.FC=()=>{
  const f=useCurrentFrame();
  const windowOpacity=tween(f,[802,834],[1,0]);
  return <AbsoluteFill style={{
    background:'linear-gradient(180deg,#e7edf2 0%,#f5f7f9 72%,#e8edf2 100%)',
    fontFamily:'Segoe UI, Arial, sans-serif'
  }}>
    <Header/>
    <div style={{opacity:windowOpacity}}><ExcelWindow/></div>
    <ProofCard/>
    <FinalRule/>

    <Sequence from={0}><Audio src={staticFile('voice-v6.mp3')} volume={1}/></Sequence>
    <Sequence from={42}><Audio src={staticFile('warning.wav')} volume={0.28}/></Sequence>
    {[47,241,523,707].map((fr,i)=>
      <Sequence key={i} from={fr}><Audio src={staticFile('ui-click.wav')} volume={0.22}/></Sequence>
    )}
    <Sequence from={714}><Audio src={staticFile('confirm.wav')} volume={0.30}/></Sequence>

    <Caption/>

    <div style={{
      position:'absolute',left:60,right:60,bottom:68,height:3,
      background:'rgba(40,56,72,.10)',borderRadius:3
    }}>
      <div style={{
        height:'100%',width:`${(f/899)*100}%`,
        background:`linear-gradient(90deg,${C.red},${C.cyan},${C.green})`,
        borderRadius:3
      }}/>
    </div>
  </AbsoluteFill>;
};

// render-trigger: v6-001-hidden-space-xray
