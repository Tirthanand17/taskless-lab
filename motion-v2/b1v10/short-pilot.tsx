import React from 'react';
import {Composition,registerRoot,useCurrentFrame} from 'remotion';
import {C,Scene,Zone,Kicker,Headline,Surface,useLayout,ease} from './visual-system';
import {CameraStage,FocusLight} from './motion-primitives';
import {WordCaption} from './word-caption';
import cues from './word_captions_review.json';
import narration from './NARRATION_REVIEW_QA.json';
import mix from './SOUND_MIX_QA.json';
import editorial from './EDITORIAL_REVIEW_QA.json';
const hashes=editorial.selected.find(x=>x.id==='sha256-change')!.demo_result as {sha256_a:string;sha256_b:string};
const event=(anchor:string)=>mix.events.find(x=>x.anchor===anchor)!.frame;
const mono='Consolas, monospace';
const FileTile:React.FC<{letter:string;active:boolean;label:string}>=({letter,active,label})=>
 <div style={{width:286,height:270,borderRadius:28,background:'linear-gradient(145deg,#395C74,#132536)',border:'3px solid '+(active?C.lime:C.edge),boxShadow:'0 16px 0 #07111C,0 24px 32px #050A12AA',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:18}}>
  <div style={{width:224,height:140,borderRadius:18,background:'#09131F',display:'flex',alignItems:'center',justifyContent:'center',fontSize:104,fontWeight:800,color:active?C.lime:C.ink}}>{letter}</div>
  <div style={{fontSize:28,fontWeight:700,color:C.muted}}>{label}</div>
 </div>;
const Digest:React.FC<{value:string;label:string;progress:number;accent?:boolean}>=({value,label,progress,accent})=>
 <div style={{padding:20,borderRadius:18,background:'#09131F',border:'2px solid '+(accent?C.lime:C.edge),display:'flex',flexDirection:'column',gap:10}}>
  <div style={{fontSize:26,color:C.muted,fontWeight:700}}>{label}</div>
  <div style={{fontFamily:mono,fontSize:34,lineHeight:1.4,letterSpacing:1,overflowWrap:'anywhere'}}>
    {Array.from(value).map((c,i)=><span key={i} style={{color:i<Math.ceil(progress*64)?(accent?C.lime:C.ink):C.edge}}>{i<Math.ceil(progress*64)?c:'·'}</span>)}
  </div>
 </div>;
const Short:React.FC=()=>{
 const f=useCurrentFrame(),{regions:r,type}=useLayout();
 const idx=narration.scene_timeline.findIndex(s=>s.start_frame<=f&&f<s.end_frame);
 const s=narration.scene_timeline[idx];const local=f-s.start_frame;
 const p=ease(f,s.start_frame,s.end_frame-1);
 const a=f>=event('a'),b=f>=event('b'),reveal=f>=event('fingerprints'),trusted=f>=event('trusted');
 const titles=['One byte changes.','Two tiny files.','Two digital fingerprints.','Check the trusted hash.'];
 const sub=['Will the hash change?','A versus B','SHA-256 / 64 hex digits','Integrity, not safety'];
 return <Scene>
  <Zone name="header" region={r.header}><Kicker>FLOWMINUTE / FILE INTEGRITY</Kicker><Headline>{titles[idx]}<br/><span style={{color:C.lime,fontSize:52}}>{sub[idx]}</span></Headline></Zone>
  <Zone name="hero" region={r.hero}><Surface>
   <CameraStage start={s.start_frame} end={s.end_frame-1}>
    <FocusLight x={30+40*p} y={35}/>
    <div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',justifyContent:'center',gap:24,padding:16}}>
     {idx<2?<><div style={{display:'flex',justifyContent:'space-evenly',alignItems:'center',gap:24}}>
      <div style={{transform:'translateY('+(-10*ease(f,event('a'),event('a')+14))+'px)'}}><FileTile letter="A" active={idx===0||a} label="FILE 01"/></div>
      <div style={{transform:'translateY('+(-10*ease(f,event('b'),event('b')+14))+'px)'}}><FileTile letter={idx===0?(local<24?'A':'B'):b?'B':'?'} active={idx===0?local>=24:b} label="FILE 02"/></div>
     </div><div style={{fontSize:35,fontWeight:700,textAlign:'center',color:C.muted}}>{idx===0?'Change one input byte':b?'Different input bytes':a?'First input: A':'Two one-byte examples'}</div></>:
     idx===2?<><Digest value={hashes.sha256_a} label="SHA-256 OF A" progress={ease(f,s.start_frame,s.start_frame+50)}/><Digest value={hashes.sha256_b} label="SHA-256 OF B" progress={ease(f,s.start_frame+52,event('fingerprints')+8)} accent={reveal}/></>:
     <><div style={{fontSize:28,color:C.muted,fontWeight:700}}>EXPECTED / TRUSTED SOURCE</div><div style={{fontFamily:mono,fontSize:48,fontWeight:700,color:C.ink,padding:24,background:'#09131F',borderRadius:16}}>{hashes.sha256_a.slice(0,12)}...</div>
      <div style={{height:50,textAlign:'center',fontSize:40,color:trusted?C.lime:C.edge}}>↓</div><div style={{fontSize:28,color:C.muted,fontWeight:700}}>OBSERVED / FILE A</div><div style={{fontFamily:mono,fontSize:48,fontWeight:700,color:trusted?C.lime:C.ink,padding:24,background:'#09131F',border:'2px solid '+(trusted?C.lime:C.edge),borderRadius:16}}>{hashes.sha256_a.slice(0,12)}...</div></>}
    </div>
   </CameraStage>
  </Surface></Zone>
  <Zone name="proof" region={r.proof}><Surface accent={idx>=2}>
   <Kicker>{['THE QUESTION','ACTUAL INPUT','COMPUTED RESULT','THE LIMIT'][idx]}</Kicker>
   <div style={{fontSize:52,lineHeight:1.1,fontWeight:800,marginTop:14,color:C.lime}}>{['A → B','1 byte each',reveal?'Different hashes':'Computing hashes',trusted?'Matching prefix':'Compare the digest'][idx]}</div>
   <div style={{fontSize:type.body,lineHeight:1.2,marginTop:16}}>{['The input changes, not the hash algorithm.','Original example: ASCII A and B.','Actual computed SHA-256 values.','Compare all 64 characters. A match alone does not prove safety.'][idx]}</div>
  </Surface></Zone>
  <Zone name="caption" region={r.caption}><WordCaption cues={cues}/></Zone>
 </Scene>;
};
registerRoot(()=> <Composition id="B1v10Sha256Short" component={Short} width={1080} height={1920} fps={30} durationInFrames={narration.frames_at_30fps}/>);
