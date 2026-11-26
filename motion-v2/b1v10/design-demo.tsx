import React from 'react';
import {Composition, registerRoot, useCurrentFrame} from 'remotion';
import {C, Scene, Zone, Kicker, Headline, Surface, Caption, Chip, Rise, useLayout} from './visual-system';
import design from './design.json';

const Demo:React.FC=()=>{
  const f=useCurrentFrame(), {regions:r,type,width}=useLayout();
  const encoded=f>=30, payoff=f>=60;
  const small={fontSize:type.small,lineHeight:1.2,color:C.muted,fontWeight:600};
  return <Scene>
    <Zone name="header" region={r.header}>
      <Kicker>FLOWMINUTE / ORIGINAL ILLUSTRATION</Kicker>
      <Headline>Can repeated data<br/> <span style={{color:C.lime}}>take less space?</span></Headline>
    </Zone>
    <Zone name="hero" region={r.hero}>
      <Surface>
        <div style={small}>01 / ORIGINAL SEQUENCE</div>
        <div style={{display:'flex',gap:8,marginTop:18}}>
          {'AAABBCCC'.split('').map((s,i)=><Chip key={i} value={s} active={encoded}/>)}
        </div>
        <div style={{fontSize:type.body,fontWeight:700,marginTop:20}}>8 symbols, in three runs</div>
        <div style={{flex:1,minHeight:16,display:'flex',alignItems:'center',justifyContent:'center'}}>
          <svg width="90" height="52" viewBox="0 0 90 52"><path d="M45 3 V39 M28 25 L45 44 L62 25" fill="none" stroke={encoded?C.lime:C.edge} strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </div>
        <div style={small}>02 / COUNT + SYMBOL</div>
        <div style={{display:'flex',gap:14,marginTop:18}}>
          {['3A','2B','3C'].map((s,i)=><Chip key={i} value={encoded?s:'?'} active={encoded}/>)}
        </div>
        <div style={{fontSize:type.body,fontWeight:700,marginTop:20}}>{encoded?'6 characters in this notation':'Group adjacent repeats'}</div>
      </Surface>
    </Zone>
    <Zone name="proof" region={r.proof}>
      <Surface accent={payoff}>
        <Kicker>{payoff?'THE TAKEAWAY':'WHAT TO NOTICE'}</Kicker>
        <div style={{fontSize:payoff?65:50,lineHeight:1.08,fontWeight:800,marginTop:14,color:payoff?C.lime:C.ink}}>
          {payoff?'8 to 6':'Same sequence'}
        </div>
        <div style={{fontSize:type.body,lineHeight:1.2,marginTop:18}}>
          {payoff?'Count each run.':'The order stays A, B, C.'}
        </div>
        <div style={{...small,marginTop:14}}>Example notation, not file size.</div>
        {width===1920 && <div style={{marginTop:24,display:'flex',flexDirection:'column',gap:9}}>
          {[['AAA','3A'],['BB','2B'],['CCC','3C']].map(([run,code])=>
            <div key={run} style={{display:'flex',alignItems:'center',justifyContent:'space-between',background:'#101F2E',border:'1px solid '+C.edge,borderRadius:12,padding:'8px 18px',fontSize:31,lineHeight:1.1,fontWeight:700}}>
              <span style={{letterSpacing:4}}>{run}</span><span style={{color:C.muted}}>{encoded?'becomes':'run'}</span><span style={{color:C.lime,minWidth:70,textAlign:'right'}}>{encoded?code:'?'}</span>
            </div>)}
        </div>}
      </Surface>
    </Zone>
    <Zone name="caption" region={r.caption}>
      <Rise start={0}><Caption>{payoff?'Repeated patterns can save space.':encoded?'Store each run as a count and a symbol.':'Start with eight symbols in order.'}</Caption></Rise>
    </Zone>
  </Scene>;
};
const Root=()=> <>{Object.entries(design.formats).map(([key,v])=>
  <Composition key={key} id={key==='vertical'?'B1v10DesignVertical':'B1v10DesignLandscape'} component={Demo}
    width={v.width} height={v.height} fps={design.fps} durationInFrames={90}/>)}</>;
registerRoot(Root);
