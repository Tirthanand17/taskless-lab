import React from 'react';
import {Composition,registerRoot,useCurrentFrame} from 'remotion';
import {C,Scene,Zone,Kicker,Headline,Surface,Caption,useLayout,ease} from './visual-system';
import {CameraStage,Reveal,FocusLight} from './motion-primitives';
import design from './design.json';
import editorial from './EDITORIAL_REVIEW_QA.json';

const item=editorial.selected.find(x=>x.id==='sha256-change')!;
const result=item.demo_result as {sha256_a:string;sha256_b:string};
const Card:React.FC<{letter:string;active:boolean;index:number;progress:number}>=({letter,active,index,progress})=>
 <g transform={'translate('+(index===0?110:426)+' '+(86-18*progress)+')'}>
  <rect x="6" y="16" width="260" height="260" rx="28" fill="#050b13"/>
  <rect width="260" height="260" rx="28" fill="url(#metal)" stroke={active?C.lime:'#53748B'} strokeWidth="4"/>
  <rect x="25" y="25" width="210" height="128" rx="15" fill="#0A1725" stroke="#61839D" strokeWidth="2"/>
  <text x="130" y="114" fontSize="88" fontWeight="800" fill={active?C.lime:C.ink} textAnchor="middle">{letter}</text>
  <text x="130" y="191" fontSize="23" fill={C.muted} fontWeight="700" textAnchor="middle">ONE BYTE</text>
  <path d="M35 220 H225" stroke={active?C.lime:C.edge} strokeWidth="5" strokeLinecap="round"/>
 </g>;

const Benchmark:React.FC=()=>{
 const f=useCurrentFrame(),{regions:r,type}=useLayout();
 const p=ease(f,18,46), q=ease(f,46,78), changed=f>=20, revealed=f>=46;
 const prefix=changed?result.sha256_b.slice(0,12):result.sha256_a.slice(0,12);
 return <Scene>
  <Zone name="header" region={r.header}><Kicker>FLOWMINUTE / FILE INTEGRITY</Kicker><Headline>Change one byte.<br/><span style={{color:C.lime}}>Watch the hash change.</span></Headline></Zone>
  <Zone name="hero" region={r.hero}><Surface>
   <CameraStage start={0} end={84}>
    <FocusLight x={35+30*p} y={38}/>
    <svg width="100%" height="100%" viewBox="0 0 800 480" style={{position:'absolute',inset:0}}>
     <defs><linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#42627B"/><stop offset="0.48" stopColor="#253F55"/><stop offset="1" stopColor="#102030"/></linearGradient></defs>
     <ellipse cx="400" cy="370" rx="340" ry="44" fill="#06101B" opacity=".8"/>
     <Card letter="A" active={false} index={0} progress={0}/>
     <Card letter={changed?'B':'A'} active={changed} index={1} progress={p}/>
     <path d="M379 208 H415" stroke={changed?C.lime:C.edge} strokeWidth="6" strokeLinecap="round"/>
     <path d="M402 197 L415 208 L402 219" fill="none" stroke={changed?C.lime:C.edge} strokeWidth="5"/>
     <rect x="110" y="392" width="576" height="54" rx="14" fill="#0A1725" stroke="#45627A" strokeWidth="2"/>
     <text x="398" y="427" textAnchor="middle" fontSize="27" fill={C.ink} fontWeight="700">{changed?'Different input bytes':'Identical input bytes'}</text>
    </svg>
   </CameraStage>
  </Surface></Zone>
  <Zone name="proof" region={r.proof}><Surface accent={revealed}>
   <Kicker>SHA-256 / FIRST 12 HEX CHARACTERS</Kicker>
   <div style={{fontSize:type.small,color:C.muted,marginTop:13}}>Expected digest for A</div>
   <div style={{fontFamily:'Consolas, monospace',fontSize:38,fontWeight:700,color:C.ink}}>{result.sha256_a.slice(0,12)}</div>
   <div style={{fontSize:type.small,color:C.muted,marginTop:12}}>Observed digest for {changed?'B':'A'}</div>
   <div style={{fontFamily:'Consolas, monospace',fontSize:38,fontWeight:700,color:changed?C.lime:C.ink}}>{prefix}</div>
   <Reveal start={46}><div style={{fontSize:30,lineHeight:1.1,fontWeight:800,color:C.lime,marginTop:8,opacity:.75+.25*q}}>Full digests differ.</div></Reveal>
  </Surface></Zone>
  <Zone name="caption" region={r.caption}><Caption>{revealed?'A trusted expected hash helps verify integrity.':changed?'Now compare the computed fingerprints.':'Start with identical sample bytes.'}</Caption></Zone>
 </Scene>;
};
registerRoot(()=> <Composition id="B1v10MotionQualityVertical" component={Benchmark} width={design.formats.vertical.width} height={design.formats.vertical.height} fps={30} durationInFrames={90}/>);
