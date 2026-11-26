// B1v10 v0.1.0: original 2.5D native-HD smoke test. No audio or publication.
// This is a renderer benchmark, not a completed video or proof of creative parity.
import React from 'react';
import {AbsoluteFill, Composition, interpolate, registerRoot, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

const palette={ink:'#0b1420',paper:'#edf5ff',cyan:'#64e4ee',lime:'#c2f76b',muted:'#94a9bf',steel:'#345268'};
const ramp=(f:number,a:number,b:number)=>interpolate(f,[a,b],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)});
const Disk:React.FC<{f:number}>=({f})=>{
  const turn=interpolate(f,[0,45,89],[-22,12,-5]);
  const rise=45*(1-ramp(f,0,23));
  const open=ramp(f,22,65);
  return <svg width="100%" height="100%" viewBox="0 0 900 780" style={{overflow:'visible'}}>
    <defs>
      <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">
        <stop stopColor="#8faaba"/><stop offset=".38" stopColor="#385469"/><stop offset="1" stopColor="#142637"/>
      </linearGradient>
      <linearGradient id="chip" x1="0" y1="0" x2="0" y2="1">
        <stop stopColor="#455769"/><stop offset="1" stopColor="#101a26"/>
      </linearGradient>
      <radialGradient id="light"><stop stopColor="#234f60"/><stop offset="1" stopColor="#101b29" stopOpacity="0"/></radialGradient>
      <filter id="shadow" x="-40%" y="-40%" width="180%" height="200%"><feDropShadow dx="10" dy="24" stdDeviation="22" floodColor="#02060a" floodOpacity=".9"/></filter>
    </defs>
    <ellipse cx="450" cy="420" rx="440" ry="350" fill="url(#light)"/>
    <g transform={'translate(450 '+(370+rise)+') rotate('+turn+')'} filter="url(#shadow)">
      <rect x="-300" y="-120" width="600" height="240" rx="46" fill="#0c1824" stroke="#435b6c" strokeWidth="3" transform="translate(0 18)"/>
      <rect x="-300" y="-120" width="600" height="240" rx="46" fill="url(#metal)" stroke="#9bb5c4" strokeWidth="3"/>
      <rect x="-269" y="-87" width="538" height="174" rx="30" fill="#153f43" stroke="#6bc8bf" strokeWidth="3"/>
      {Array.from({length:4},(_,i)=><g key={i} transform={'translate('+(-210+i*125)+' 0)'}>
        {Array.from({length:5},(_,j)=><path key={j} d={'M -59 '+(-46+j*22)+' H -47 M 47 '+(-46+j*22)+' H 59'} stroke="#d9ad6b" strokeWidth="5" strokeLinecap="round"/>)}
        <rect x="-47" y="-65" width="94" height="130" rx="9" fill="url(#chip)" stroke="#8392a0" strokeWidth="2"/>
        <path d="M -34 -45 H 34" stroke="#738a9d" strokeWidth="2"/>
      </g>)}
      <g transform={'translate('+(-30*open)+' '+(-190*open)+')'}>
        <rect x="-300" y="-120" width="600" height="240" rx="46" fill="url(#metal)" stroke="#a9c6d7" strokeWidth="4"/>
        <rect x="-272" y="-92" width="544" height="184" rx="32" fill="#162a3b" stroke="#60849c" strokeWidth="2"/>
        <text x="0" y="-5" fill={palette.paper} fontFamily="Segoe UI, sans-serif" fontSize="76" fontWeight="800" textAnchor="middle">128 GB</text>
        <text x="0" y="53" fill={palette.cyan} fontFamily="Segoe UI, sans-serif" fontSize="22" letterSpacing="6" textAnchor="middle">ILLUSTRATED DRIVE</text>
      </g>
    </g>
    <g opacity={ramp(f,35,60)}>
      <path d="M 675 437 L 788 536 L 788 625" stroke={palette.cyan} strokeWidth="4" fill="none" strokeDasharray="7 7"/>
      <circle cx="675" cy="437" r="20" fill="none" stroke={palette.lime} strokeWidth="4"/>
      <text x="785" y="665" textAnchor="end" fill={palette.cyan} fontSize="28" fontFamily="Segoe UI">Illustrated components</text>
    </g>
  </svg>;
};
const Smoke:React.FC=()=>{
  const f=useCurrentFrame(),{width,height}=useVideoConfig(),v=height>width;
  const count=128-(128-119.21)*ramp(f,46,80);
  return <AbsoluteFill style={{background:'radial-gradient(ellipse at 48% 42%,#183647 0%,#0b1420 62%,#070d15 100%)',color:palette.paper,fontFamily:'Segoe UI, Arial, sans-serif',overflow:'hidden'}}>
    <div style={{position:'absolute',left:v?64:90,top:70,fontWeight:700,fontSize:26,letterSpacing:4,color:palette.cyan}}>FLOWMINUTE LAB / B1V10 • DEV TEST</div>
    <div style={{position:'absolute',left:v?64:90,top:v?172:130,width:v?900:1700,fontSize:v?78:72,lineHeight:1.06,fontWeight:800}}>Same bytes.<br/><span style={{color:palette.lime}}>Different units.</span></div>
    <div style={{position:'absolute',left:v?40:40,top:v?360:280,width:v?960:920,height:v?820:700}}><Disk f={f}/></div>
    <div style={{position:'absolute',left:v?65:1030,top:v?1260:425,width:v?900:800,borderTop:'3px solid '+palette.cyan,paddingTop:25}}>
      <div style={{fontSize:30,letterSpacing:3,color:palette.muted}}>CALCULATED CAPACITY</div>
      <div style={{fontSize:v?112:110,fontWeight:800,fontVariantNumeric:'tabular-nums',color:palette.lime}}>{count.toFixed(2)} <span style={{fontSize:54}}>GiB</span></div>
      <div style={{fontSize:v?34:36,color:palette.paper,lineHeight:1.3}}>128,000,000,000 bytes ÷ 2³⁰<br/>Final result: 119.21 GiB</div>
      <div style={{marginTop:20,fontSize:26,color:palette.muted}}>Illustration only • before reserved space</div>
    </div>
  </AbsoluteFill>;
};
const Root=()=> <><Composition id="B1v10VerticalSmoke" component={Smoke} durationInFrames={90} fps={30} width={1080} height={1920}/><Composition id="B1v10LandscapeSmoke" component={Smoke} durationInFrames={90} fps={30} width={1920} height={1080}/></>;
registerRoot(Root);
