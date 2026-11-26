import React from 'react';
import {Composition,registerRoot,useCurrentFrame} from 'remotion';
import {C,Scene,Zone,Kicker,Headline,Surface,useLayout} from './visual-system';
import {WordCaption} from './word-caption';
import cues from './word_captions_review.json';
import report from './NARRATION_REVIEW_QA.json';
import design from './design.json';
const labels=['One small change','Two tiny files','Two fingerprints','Check against a trusted hash'];
const descriptions=['A single byte is enough.','A and B are different bytes.','A hash represents the input.','Integrity is not proof of safety.'];
const Preview:React.FC=()=>{
 const f=useCurrentFrame(),{regions:r,type}=useLayout();
 const index=report.scene_timeline.findIndex(s=>s.start_frame<=f&&f<s.end_frame);
 if(index<0)throw new Error('Frame outside narration timeline');
 return <Scene>
  <Zone name="header" region={r.header}><Kicker>FLOWMINUTE / NARRATION TIMING REVIEW</Kicker><Headline>{labels[index]}</Headline></Zone>
  <Zone name="hero" region={r.hero}><Surface accent={true}>
    <div style={{fontSize:type.small,color:C.muted}}>SCENE {index+1} / 4</div>
    <div style={{flex:1,display:'flex',alignItems:'center',justifyContent:'center',gap:26}}>
     {['A','B'].map((v,i)=><div key={v} style={{width:190,height:190,display:'flex',alignItems:'center',justifyContent:'center',fontSize:110,fontWeight:800,borderRadius:28,border:'3px solid '+(i?C.lime:C.edge),background:'#0a1725',color:i?C.lime:C.ink}}>{v}</div>)}
    </div><div style={{fontSize:type.body,fontWeight:700}}>{descriptions[index]}</div>
  </Surface></Zone>
  <Zone name="proof" region={r.proof}><Surface><Kicker>FRAME-LOCKED SCENE</Kicker><div style={{fontSize:type.body,marginTop:18}}>Visual scene follows the actual narration duration.</div></Surface></Zone>
  <Zone name="caption" region={r.caption}><WordCaption cues={cues}/></Zone>
 </Scene>;
};
registerRoot(()=> <>{Object.entries(design.formats).map(([k,v])=><Composition key={k} id={k==='vertical'?'NarrationVertical':'NarrationLandscape'} component={Preview} width={v.width} height={v.height} fps={30} durationInFrames={report.frames_at_30fps}/>)}</>);
