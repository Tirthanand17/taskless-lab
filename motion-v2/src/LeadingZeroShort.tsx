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

const C = {
  bg: '#050a12',
  panel: '#0b1524',
  text: '#f4f8fc',
  muted: '#9cb0c6',
  cyan: '#5ee7ff',
  green: '#77efae',
  red: '#ff6f78',
  yellow: '#ffd86e',
  purple: '#b895ff',
};

const clamp = (frame:number, input:number[], output:number[]) =>
  interpolate(frame,input,output,{
    extrapolateLeft:'clamp',
    extrapolateRight:'clamp',
    easing:Easing.bezier(0.2,0.72,0.2,1),
  });

const captions = [
  [0,96,'Excel can change an ID before you touch the file.'],
  [96,216,'00123 can silently become 123.'],
  [216,330,'Long identifiers can change too.'],
  [330,453,'IDs are not numbers just because they use digits.'],
  [453,588,'Import with Data → From Text/CSV.'],
  [588,708,'Transform Data → set the ID column to Text.'],
  [708,795,'Then load with the original values preserved.'],
  [795,870,'Sometimes digits are identity, not math.'],
] as const;

const Caption:React.FC=()=>{
  const frame=useCurrentFrame();
  const item=captions.find(([a,b])=>frame>=a&&frame<b);
  if(!item) return null;
  const [a,b,text]=item;
  const opacity=Math.min(clamp(frame,[a,a+5],[0,1]),clamp(frame,[b-6,b],[1,0]));
  return <div style={{
    position:'absolute',left:105,right:105,top:1505,display:'flex',justifyContent:'center',opacity,zIndex:20
  }}>
    <div style={{
      padding:'12px 20px',borderRadius:16,background:'rgba(2,7,13,.72)',
      border:'1px solid rgba(255,255,255,.10)',fontSize:39,lineHeight:1.12,
      fontWeight:650,color:C.text,whiteSpace:'nowrap',boxShadow:'0 10px 28px rgba(0,0,0,.26)'
    }}>{text}</div>
  </div>;
};

const Background:React.FC=()=>{
  const frame=useCurrentFrame();
  const drift=(frame*0.8)%120;
  return <AbsoluteFill style={{
    background:'radial-gradient(circle at 50% 18%, #12233b 0%, #08111e 46%, #050a12 100%)',
    overflow:'hidden'
  }}>
    <div style={{
      position:'absolute',inset:-220,opacity:.32,
      transform:`perspective(1000px) rotateX(67deg) translateY(${250+drift}px)`,
      backgroundImage:'linear-gradient(rgba(94,231,255,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(94,231,255,.10) 1px,transparent 1px)',
      backgroundSize:'90px 90px',
      maskImage:'linear-gradient(to bottom,transparent,black 28%,black 78%,transparent)'
    }}/>
    <div style={{
      position:'absolute',left:210,top:420,width:660,height:660,borderRadius:'50%',
      background:'rgba(184,149,255,.09)',filter:'blur(110px)'
    }}/>
  </AbsoluteFill>;
};

const Header:React.FC=()=> <div style={{
  position:'absolute',left:58,right:58,top:55,display:'flex',justifyContent:'space-between',
  fontSize:23,fontWeight:900,letterSpacing:1.4,color:C.muted,zIndex:15
}}>
  <span>FLOWMINUTE LAB</span><span style={{color:C.cyan}}>DATA INTEGRITY / 02</span>
</div>;

const FileCard:React.FC=()=>{
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const enter=spring({frame,fps,config:{damping:17,stiffness:95,mass:.8}});
  const out=clamp(frame,[410,455],[1,0]);
  const rot=7-clamp(frame,[0,160],[0,6]);
  return <div style={{
    position:'absolute',left:130,top:310,width:820,height:730,
    transform:`translateY(${(1-enter)*80}px) rotateY(${rot}deg) scale(${.9+enter*.08})`,
    transformOrigin:'center',perspective:1200,opacity:out,zIndex:4
  }}>
    <div style={{
      borderRadius:34,overflow:'hidden',
      background:'linear-gradient(150deg,#13253d,#091625)',
      border:'1px solid rgba(150,195,230,.22)',
      boxShadow:'0 50px 120px rgba(0,0,0,.42),0 0 55px rgba(94,231,255,.08)'
    }}>
      <div style={{
        height:86,padding:'0 26px',display:'flex',alignItems:'center',justifyContent:'space-between',
        background:'#102035',borderBottom:'1px solid #213b57'
      }}>
        <span style={{fontSize:24,color:C.text,fontWeight:900}}>customer_ids.csv</span>
        <span style={{fontSize:20,color:C.muted}}>CSV</span>
      </div>
      <div style={{padding:30}}>
        <div style={{
          display:'grid',gridTemplateColumns:'180px 1fr',gap:10,marginBottom:10
        }}>
          {['customer_id','name'].map((h)=><div key={h} style={{
            padding:'17px 14px',borderRadius:12,background:'#162b47',
            border:'1px solid #24415f',fontSize:22,fontWeight:850,color:C.text
          }}>{h}</div>)}
        </div>
        {[
          ['00123','Maya'],
          ['00047','Arjun'],
          ['9876543210987654','Leah'],
          ['00301','Ravi'],
        ].map((row,i)=><div key={i} style={{
          display:'grid',gridTemplateColumns:'180px 1fr',gap:10,marginBottom:9
        }}>
          {row.map((cell,j)=><div key={j} style={{
            padding:'18px 14px',borderRadius:12,background:'#0e2035',
            border:'1px solid #1f3954',fontSize:22,fontWeight:j===0?900:650,color:C.text
          }}>{cell}</div>)}
        </div>)}
      </div>
    </div>
  </div>;
};

const AutoConvertPortal:React.FC=()=>{
  const frame=useCurrentFrame();
  const opacity=clamp(frame,[45,78,410,445],[0,1,1,0]);
  const pulse=.88+Math.sin(frame/6)*.03;
  const beam=clamp(frame,[70,120],[0,1]);
  return <div style={{position:'absolute',inset:0,opacity,zIndex:8}}>
    <div style={{
      position:'absolute',left:420,top:212,width:240,height:78,borderRadius:999,
      border:`1px solid ${C.red}88`,background:'rgba(60,12,18,.8)',
      color:C.red,fontSize:24,fontWeight:950,display:'flex',alignItems:'center',justifyContent:'center',
      transform:`scale(${pulse})`,boxShadow:`0 0 34px ${C.red}24`
    }}>AUTO-CONVERT</div>
    <div style={{
      position:'absolute',left:530,top:292,width:4,height:740,
      background:`linear-gradient(to bottom,${C.red},transparent)`,
      opacity:beam,boxShadow:`0 0 22px ${C.red}`
    }}/>
  </div>;
};

const ChangedId:React.FC=()=>{
  const frame=useCurrentFrame();
  const p1=clamp(frame,[95,125],[0,1]);
  const p2=clamp(frame,[205,245],[0,1]);
  const warn=clamp(frame,[120,145,350,385],[0,1,1,0]);
  return <>
    <div style={{
      position:'absolute',left:182,top:1115,width:716,opacity:warn,zIndex:10
    }}>
      <div style={{
        padding:24,borderRadius:24,background:'rgba(31,8,14,.94)',
        border:`1px solid ${C.red}77`,boxShadow:'0 28px 70px rgba(0,0,0,.34)'
      }}>
        <div style={{fontSize:21,fontWeight:950,color:C.red,letterSpacing:1.4}}>DATA CHANGED</div>
        <div style={{display:'grid',gridTemplateColumns:'1fr 120px 1fr',alignItems:'center',marginTop:18,gap:12}}>
          <div style={{fontSize:54,fontWeight:950,color:C.text,textAlign:'right',opacity:1-p1*.55}}>00123</div>
          <div style={{fontSize:44,textAlign:'center',color:C.red}}>→</div>
          <div style={{fontSize:54,fontWeight:950,color:C.red,transform:`scale(${.85+p1*.15})`}}>123</div>
        </div>
        <div style={{
          marginTop:18,paddingTop:18,borderTop:'1px solid rgba(255,255,255,.08)',
          display:'grid',gridTemplateColumns:'1fr 90px 1fr',alignItems:'center',gap:12
        }}>
          <div style={{fontSize:25,fontWeight:800,color:C.text,textAlign:'right'}}>9876543210987654</div>
          <div style={{fontSize:30,textAlign:'center',color:C.yellow}}>→</div>
          <div style={{fontSize:28,fontWeight:900,color:C.yellow,opacity:p2}}>9.87654E+15</div>
        </div>
      </div>
    </div>
  </>;
};

const Pipeline:React.FC=()=>{
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const enter=spring({frame:Math.max(0,frame-430),fps,config:{damping:18,stiffness:100}});
  const opacity=clamp(frame,[430,470,815,850],[0,1,1,0]);
  const stages=[
    ['CSV FILE',C.cyan],
    ['FROM TEXT / CSV',C.purple],
    ['TRANSFORM DATA',C.yellow],
    ['TYPE: TEXT',C.green],
  ];
  return <div style={{
    position:'absolute',left:74,right:74,top:390,opacity,
    transform:`translateY(${(1-enter)*80}px)`,zIndex:7
  }}>
    <div style={{
      padding:30,borderRadius:32,background:'rgba(7,16,29,.96)',
      border:'1px solid rgba(150,190,225,.18)',boxShadow:'0 36px 100px rgba(0,0,0,.4)'
    }}>
      <div style={{fontSize:26,fontWeight:950,color:C.text,marginBottom:24}}>SAFER IMPORT PIPELINE</div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
        {stages.map(([label,color],i)=>{
          const local=clamp(frame,[470+i*55,500+i*55],[0,1]);
          return <div key={label} style={{
            position:'relative',minHeight:210,borderRadius:22,padding:'22px 16px',
            background:'#0e2035',border:`1px solid ${String(color)}55`,
            opacity:local,transform:`translateY(${(1-local)*26}px)`
          }}>
            <div style={{
              width:42,height:42,borderRadius:42,background:String(color),
              color:'#061019',fontSize:22,fontWeight:950,display:'flex',alignItems:'center',
              justifyContent:'center',boxShadow:`0 0 22px ${String(color)}45`
            }}>{i+1}</div>
            <div style={{fontSize:22,fontWeight:900,color:String(color),marginTop:28,lineHeight:1.18}}>{label}</div>
          </div>;
        })}
      </div>
      <div style={{
        marginTop:24,height:10,borderRadius:999,background:'rgba(255,255,255,.08)',overflow:'hidden'
      }}>
        <div style={{
          height:'100%',width:`${clamp(frame,[470,720],[0,100])}%`,
          background:`linear-gradient(90deg,${C.cyan},${C.purple},${C.green})`
        }}/>
      </div>
    </div>
  </div>;
};

const PreservedId:React.FC=()=>{
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const enter=spring({frame:Math.max(0,frame-700),fps,config:{damping:15,stiffness:110}});
  const opacity=clamp(frame,[700,735,868,870],[0,1,1,1]);
  return <div style={{
    position:'absolute',left:140,right:140,top:1040,opacity,zIndex:12,
    transform:`scale(${.85+enter*.15}) translateY(${(1-enter)*28}px)`
  }}>
    <div style={{
      borderRadius:28,padding:28,textAlign:'center',
      background:'rgba(7,40,30,.95)',border:`1px solid ${C.green}77`,
      boxShadow:`0 28px 80px rgba(0,0,0,.35),0 0 40px ${C.green}18`
    }}>
      <div style={{fontSize:21,fontWeight:950,letterSpacing:1.5,color:C.green}}>VALUE PRESERVED</div>
      <div style={{fontSize:76,fontWeight:1000,color:C.text,marginTop:14,letterSpacing:3}}>00123</div>
      <div style={{fontSize:24,color:C.muted,marginTop:8}}>stored as text, not converted</div>
    </div>
  </div>;
};

const FinalLine:React.FC=()=>{
  const frame=useCurrentFrame();
  const p=clamp(frame,[790,835],[0,1]);
  return <div style={{
    position:'absolute',left:130,right:130,top:260,opacity:p,textAlign:'center',zIndex:14
  }}>
    <div style={{fontSize:56,lineHeight:1.04,fontWeight:1000,color:C.text}}>
      DIGITS ≠ MATH
    </div>
    <div style={{fontSize:28,fontWeight:850,color:C.green,marginTop:16}}>
      sometimes they are identity
    </div>
  </div>;
};

export const LeadingZeroShort:React.FC=()=>{
  const frame=useCurrentFrame();
  return <AbsoluteFill style={{fontFamily:'Arial, Helvetica, sans-serif',color:C.text}}>
    <Background/>
    <Header/>
    <FileCard/>
    <AutoConvertPortal/>
    <ChangedId/>
    <Pipeline/>
    <PreservedId/>
    <FinalLine/>
    <Sequence from={0}><Audio src={staticFile('voice-v3.mp3')} volume={1}/></Sequence>
    <Caption/>
    <div style={{
      position:'absolute',left:58,right:58,bottom:82,height:2,background:'rgba(255,255,255,.10)'
    }}>
      <div style={{
        height:'100%',width:`${(frame/869)*100}%`,
        background:`linear-gradient(90deg,${C.red},${C.yellow},${C.green})`
      }}/>
    </div>
  </AbsoluteFill>;
};

// render-trigger: v3-001
