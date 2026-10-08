import React from 'react';
import {AbsoluteFill, Audio, staticFile, interpolate, useCurrentFrame, Easing} from 'remotion';

const P={ink:'#17232f',muted:'#637284',teal:'#166c4a',green:'#137748',mint:'#eaf8f0',red:'#c63b46',rose:'#fff0f1',gold:'#d69a23',bg:'#edf2f6',line:'#dbe3e9',white:'#fff',blue:'#2969ac'};
const L='Segoe UI, Arial, sans-serif';
const tween=(f:number,a:number,b:number)=>interpolate(f,[a,b],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(.19,.8,.18,1)});
const appear=(f:number,start:number,end:number)=>Math.min(tween(f,start,start+12),1-tween(f,end-12,end));
const Panel:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style={}})=><div style={{background:'#fff',border:'1px solid #cdd7df',borderRadius:16,boxShadow:'0 18px 46px rgba(15,30,45,.12)',overflow:'hidden',...style}}>{children}</div>;
const Eyebrow:React.FC<{children:React.ReactNode;red?:boolean}>=({children,red=false})=><span style={{fontFamily:L,fontSize:17,fontWeight:900,letterSpacing:1.1,color:red?P.red:P.teal}}>{children}</span>;
const GridTable:React.FC<{kind:'sum'|'names'|'margin';compact?:boolean;correct?:boolean}>=({kind,compact=false,correct=false})=>{
 const f=useCurrentFrame();
 const rows=kind==='sum'?
   [['INV-401','North','4,200'],['INV-402','West','3,800'],['INV-403','East','5,700'],['INV-404','South','5,200'],['INV-405','Central','3,600']]:
 kind==='names'?[['Ava Stone','Ava','Ava'],['Leo Kim','Leo','Leo'],['Dr Maya Chen','Dr','Maya'],['Sam Patel','Sam','Sam']]:
 [['Product A','100','150'],['Product B','80','120'],['Product C','200','260']];
 const heads=kind==='sum'?['Invoice','Region','Amount ($)']:kind==='names'?['Full name','Rule output','Desired']:['Product','Cost ($)','Price ($)'];
 const isWrong=kind==='sum'?!correct:kind==='names'?!correct:!correct;
 const selected=Math.floor(tween(f,25,75)*3);
 return <div style={{height:'100%',width:'100%',position:'relative',background:'#fff',fontFamily:L}}>
   <div style={{height:compact?45:48,background:'#176742',color:'#fff',display:'flex',alignItems:'center',padding:'0 19px',justifyContent:'space-between'}}>
     <span style={{fontWeight:800,fontSize:compact?16:17}}>Excel  |  Formula Audit.xlsx</span>
     <span style={{fontSize:12,opacity:.85}}>ILLUSTRATIVE WORKSHEET</span>
   </div>
   <div style={{height:compact?42:42,background:'#f7f9fa',borderBottom:'1px solid #d7dfe5',display:'flex',gap:26,alignItems:'center',padding:'0 17px',fontSize:compact?14:15,fontWeight:600,color:'#394956'}}>
     {['Home','Insert','Formulas','Data','Review','View'].map((x,i)=><span key={x} style={{color:i===2?P.teal:undefined,borderBottom:i===2?'3px solid #178653':'3px solid transparent',height:'100%',display:'flex',alignItems:'center'}}>{x}</span>)}
   </div>
   <div style={{height:compact?49:52,display:'flex',alignItems:'center',background:'#f8fafb',borderBottom:'1px solid #dce3e8',gap:10,padding:'0 13px'}}>
     <span style={{color:'#607789',fontStyle:'italic',fontSize:18,fontWeight:600}}>fx</span>
     <div style={{flex:1,background:'#fff',border:'1px solid #bcc9d3',borderRadius:5,padding:'7px 12px',fontFamily:'Consolas,monospace',fontSize:compact?25:18,whiteSpace:'nowrap',overflow:'hidden'}}>
       {kind==='sum'?(correct?'=SUM(C2:C6)':'=SUM(C2:C5)'):kind==='names'?'=TEXTBEFORE(A2," ")':correct?'=(C2-B2)/C2':'=(C2-B2)/B2'}
     </div>
   </div>
   <div style={{padding:compact?'13px 19px':'20px 30px'}}>
     <div style={{display:'grid',gridTemplateColumns:kind==='names'?'1.4fr 1fr 1fr':'1.4fr 1fr 1fr',height:compact?58:56,background:'#e4f2e9',border:'1px solid #c9ddd0'}}>
       {heads.map(h=><div key={h} style={{borderRight:'1px solid #c9ddd0',display:'flex',alignItems:'center',paddingLeft:14,fontWeight:800,fontSize:compact?26:20,color:'#1b4030'}}>{h}</div>)}
     </div>
     {rows.map((row,i)=><div key={i} style={{display:'grid',gridTemplateColumns:'1.4fr 1fr 1fr',height:compact?78:65,background:i%2?'#f8fbfc':'#fff',borderBottom:'1px solid #dce4e8',borderLeft:'1px solid #dce4e8'}}>
       {row.map((cell,j)=>{
         const highlight=kind==='sum'&&j===2&&((i===4&&isWrong)||(correct&&i===4));
         const badName=kind==='names'&&i===2&&j===1&&isWrong;
         return <div key={j} style={{borderRight:'1px solid #dce4e8',display:'flex',alignItems:'center',paddingLeft:14,fontWeight:highlight||badName?900:560,fontSize:compact?29:21,background:(highlight||badName)?(isWrong?'#ffe6e8':'#e7f7e9'):undefined,color:(highlight||badName)?(isWrong?P.red:P.teal):P.ink,position:'relative'}}>
           {cell}
           {highlight&&<span style={{position:'absolute',right:6,top:6,fontSize:11,fontWeight:800,color:P.red}}>ROW {i+2}</span>}
         </div>
       })}
     </div>)}
     <div style={{marginTop:16,display:'flex',alignItems:'center',justifyContent:'space-between',borderRadius:10,padding:compact?'14px 16px':'14px 20px',background:correct?P.mint:P.rose,border:correct?'1px solid #95cfa9':'1px solid #e2b0b5'}}>
       <span style={{fontWeight:850,fontSize:compact?25:20,color:correct?P.teal:P.red}}>
         {kind==='sum'?(correct?'ALL 5 ROWS':'ONLY 4 OF 5 ROWS'):kind==='names'?(correct?'EXCEPTION VERIFIED':'THE THIRD NAME BREAKS THE RULE'):(correct?'MARGIN, NOT MARKUP':'WRONG BUSINESS METRIC')}
       </span>
       <span style={{fontSize:compact?39:34,fontWeight:950,letterSpacing:-1.1,color:correct?P.teal:P.red}}>
         {kind==='sum'?(correct?'$22,500':'$18,900'):kind==='names'?(correct?'Maya':'Dr'):(correct?'33.3%':'50%')}
       </span>
     </div>
   </div>
 </div>;
};
const Brand:React.FC<{vertical?:boolean}>=({vertical=false})=><div style={{position:'absolute',top:vertical?48:34,left:vertical?50:82,right:vertical?50:82,zIndex:30,display:'flex',justifyContent:'space-between',fontFamily:L,fontWeight:900,fontSize:vertical?18:19,letterSpacing:1,color:'#526372'}}>
 <span>FLOWMINUTE LAB</span><span style={{color:P.teal}}>FORMULA CHECK</span>
 </div>;
const Lower:React.FC<{text:string;vertical?:boolean}>=({text,vertical=false})=><div style={{position:'absolute',left:vertical?78:320,right:vertical?78:320,top:vertical?1500:962,fontFamily:L,zIndex:90,display:'flex',justifyContent:'center',textAlign:'center'}}>
 <span style={{background:'rgba(19,32,44,.92)',color:'#fff',borderRadius:12,padding:vertical?'13px 16px':'10px 17px',fontSize:vertical?36:28,fontWeight:700,lineHeight:1.13}}>{text}</span>
 </div>;
const Title:React.FC<{eyebrow:string;headline:string;sub?:string;vertical?:boolean;warning?:boolean}>=({eyebrow,headline,sub,vertical=false,warning=false})=><div style={{position:'absolute',left:vertical?70:95,right:vertical?70:95,top:vertical?140:95,zIndex:40,fontFamily:L}}>
 <Eyebrow red={warning}>{eyebrow}</Eyebrow><div style={{fontSize:vertical?52:62,lineHeight:1.03,fontWeight:950,letterSpacing:-1.4,marginTop:10,color:P.ink}}>{headline}</div>
 {sub&&<div style={{fontSize:vertical?23:25,color:P.muted,marginTop:12,lineHeight:1.22}}>{sub}</div>}
 </div>;
const Stats:React.FC<{correct:boolean;vertical?:boolean}>=({correct,vertical=false})=><div style={{display:'flex',gap:15,alignItems:'center',fontFamily:L}}>
 <div style={{background:'#fff0f1',border:'1px solid #eab0b9',borderRadius:12,padding:vertical?'16px 19px':'20px 27px',flex:1}}>
  <div style={{fontSize:vertical?15:18,color:P.red,fontWeight:900}}>FORMULA OUTPUT</div><div style={{fontSize:vertical?39:53,fontWeight:950,color:P.red}}>$18,900</div>
 </div>
 <div style={{fontSize:40,color:P.muted,fontWeight:900}}>≠</div>
 <div style={{background:'#e9f8ef',border:'1px solid #95d1ae',borderRadius:12,padding:vertical?'16px 19px':'20px 27px',flex:1}}>
  <div style={{fontSize:vertical?15:18,color:P.teal,fontWeight:900}}>ACTUAL TOTAL</div><div style={{fontSize:vertical?39:53,fontWeight:950,color:P.teal}}>$22,500</div>
 </div>
 </div>;
const ShotShort:React.FC<{variant:'range'|'name'}>=({variant})=>{
 const f=useCurrentFrame();
 const isRange=variant==='range',fix=isRange?f>=530:f>=605;
 const captionRange:[[number,number,string],...Array<[number,number,string]>]=[[0,130,'A perfect-looking formula can still be wrong.'],[130,300,'Five invoices. One missing row.'],[300,530,'It sums four invoices, not five.'],[530,795,'Check the range. Then verify the total.'],[795,1080,'The formula is valid. The answer was wrong.']];
 const captionName:[[number,number,string],...Array<[number,number,string]>]=[[0,135,'Excel can learn a formula from examples.'],[135,330,'Ava and Leo work perfectly.'],[330,610,'Now meet Doctor Maya Chen.'],[610,845,'The shortcut returns Doctor, not Maya.'],[845,1020,'Test the exceptions before filling a column.']];
 const cap=(isRange?captionRange:captionName).find(([a,b])=>f>=a&&f<b);
 return <AbsoluteFill style={{background:'linear-gradient(160deg,#f4f7fa,#e8eff4)',overflow:'hidden'}}>
  <Brand vertical/>
  <Title vertical eyebrow={isRange?'VERIFY BEFORE ACCEPTING':'FORMULA BY EXAMPLE'} headline={isRange?'$3,600 VANISHED.':'IT WORKED… UNTIL ROW 3.'} warning sub={isRange?'An illustrative invoice audit':'A rule that looked right — until it didn’t'}/>
  <Panel style={{position:'absolute',top:410,left:51,width:978,height:790}}>
    <GridTable kind={isRange?'sum':'names'} compact correct={fix}/>
  </Panel>
  <Panel style={{position:'absolute',top:1230,left:78,right:78,padding:'19px 22px',minHeight:170,fontFamily:L}}>
    {isRange?<><Eyebrow red>MISSING INPUT</Eyebrow><div style={{fontSize:35,fontWeight:940,color:P.ink,margin:'8px 0 6px'}}>INV-405: $3,600</div><div style={{fontSize:27,color:P.muted}}>Follow the highlighted range: C2:C5 → C2:C6.</div></>:<><Eyebrow red>ONE EXCEPTION CHANGES THE RULE</Eyebrow><div style={{fontSize:34,fontWeight:940,color:P.ink,margin:'8px 0 6px'}}>“Dr Maya Chen” → {fix?'Maya':'Dr'}</div><div style={{fontSize:21,color:P.muted}}>Illustrative formula — inspect every edge case.</div></>}
  </Panel>
  {cap&&<Lower vertical text={cap[2]}/>}
  <div style={{position:'absolute',bottom:80,left:82,right:82,height:5,borderRadius:5,background:'#d2dce3'}}><div style={{height:5,width:(f/(isRange?1079:1019)*100)+'%',background:P.teal,borderRadius:5}}/></div>
  <Audio src={staticFile(isRange?'voice-v9.mp3':'voice-v10.mp3')}/>
 </AbsoluteFill>;
};
const LongVideo:React.FC=()=>{
 const f=useCurrentFrame();
 const t=f*5760/6384;
 const section=t<250?'hook':t<1260?'range':t<2080?'correct':t<3070?'meaning':t<4290?'name':t<5070?'feature':t<5550?'settings':'outro';
 const sections:any={hook:['THE $3,600 PROBLEM','This total looks right. It is not.'],range:['CHECK #1 · RANGE','The last invoice was invisible to the formula.'],correct:['FIX AND VERIFY','Count the records. Then confirm the total.'],meaning:['CHECK #2 · MEANING','Profit margin is not the same as markup.'],name:['CHECK #3 · EDGE CASES','Two good examples may hide a bad rule.'],feature:['HOW EXCEL COPILOT HELPS','Formula completion + Formula by Example.'],settings:['TAKE CONTROL','Two Copilot suggestion settings.'],outro:['THE THREE-CHECK RULE','Range. Meaning. Edge cases.']};
 const [b,h]=sections[section],correct=section==='correct'||section==='outro';
 return <AbsoluteFill style={{background:'linear-gradient(145deg,#eff3f6,#e9f0f4)',overflow:'hidden'}}>
  <Brand/><Title eyebrow={b} headline={h} sub={section==='hook'?'Illustrative invoices — not a real incident':section==='feature'?'Suggestions are helpful, not automatically authoritative.':undefined}/>
  {['hook','range','correct'].includes(section)&&<>
    <Panel style={{position:'absolute',top:325,left:105,width:1150,height:700}}><GridTable kind="sum" correct={correct}/></Panel>
    <div style={{position:'absolute',left:1288,right:105,top:355}}>
      <Panel style={{padding:24}}>
        <Eyebrow red={!correct}>{correct?'ALL RECORDS INCLUDED':'VALID SYNTAX · WRONG RANGE'}</Eyebrow>
        <div style={{fontSize:57,fontFamily:L,fontWeight:950,color:correct?P.teal:P.red,marginTop:15}}>{correct?'$22,500':'$18,900'}</div>
        <div style={{fontSize:24,color:P.muted,lineHeight:1.32,marginTop:8}}>The last record contains <b>$3,600</b>. Always verify where the range ends.</div>
      </Panel>
      <Panel style={{padding:23,marginTop:18}}>
       <Eyebrow>TRACE THE CELLS</Eyebrow><div style={{fontFamily:'Consolas,monospace',fontSize:26,marginTop:16,fontWeight:800,color:P.ink}}>{correct?'SUM(C2:C6)':'SUM(C2:C5)'}</div>
      </Panel>
    </div>
  </>}
  {section==='meaning'&&<>
   <Panel style={{position:'absolute',left:115,top:337,width:1030,height:650}}><GridTable kind="margin" correct/></Panel>
   <div style={{position:'absolute',left:1190,right:110,top:350}}><Panel style={{padding:28}}><Eyebrow red>MARKUP ON COST</Eyebrow><div style={{fontSize:75,color:P.red,fontWeight:950}}>50%</div><div style={{fontSize:27,marginBottom:23}}>Profit ÷ Cost</div><Eyebrow>MARGIN ON PRICE</Eyebrow><div style={{fontSize:75,color:P.teal,fontWeight:950}}>33.3%</div><div style={{fontSize:27}}>Profit ÷ Selling price</div></Panel></div>
  </>}
  {section==='name'&&<>
   <Panel style={{position:'absolute',left:105,top:332,width:1110,height:680}}><GridTable kind="names" correct={t>3740}/></Panel>
   <div style={{position:'absolute',left:1250,right:110,top:350}}><Panel style={{padding:26}}><Eyebrow red>EDGE CASE</Eyebrow><div style={{fontSize:40,fontWeight:950,marginTop:15}}>“Dr Maya Chen”</div><div style={{fontSize:25,lineHeight:1.3,color:P.muted,marginTop:19}}>TEXTBEFORE returns <b>Dr</b>. The desired first name is <b>Maya</b>.</div><div style={{marginTop:25,fontSize:19,color:P.red,fontWeight:900}}>ILLUSTRATIVE RULE — NOT A LIVE COPILOT TEST</div></Panel></div>
  </>}
  {section==='feature'&&<div style={{position:'absolute',left:160,right:160,top:335,display:'grid',gridTemplateColumns:'1fr 1fr',gap:30}}>
   {[['FORMULA COMPLETION','Type = in a cell','Uses headers, cells and tables to suggest a formula and preview the result.'],['FORMULA BY EXAMPLE','Type sample outputs','Detects a pattern and suggests a reusable formula for the remaining rows.']].map(([head,lead,detail])=><Panel key={head} style={{padding:'35px 38px',minHeight:395}}><Eyebrow>{head}</Eyebrow><div style={{fontSize:43,fontWeight:950,color:P.ink,marginTop:18}}>{lead}</div><div style={{fontSize:30,lineHeight:1.35,color:P.muted,marginTop:24}}>{detail}</div><div style={{fontSize:16,color:P.blue,fontWeight:850,marginTop:25}}>Availability depends on your Excel/Copilot experience.</div></Panel>)}
  </div>}
  {section==='settings'&&<Panel style={{position:'absolute',top:332,left:180,right:180,padding:35,minHeight:525}}>
   <Eyebrow>TURN SUGGESTIONS OFF OR ON</Eyebrow>
   {['Excel for Windows: File → Options → Copilot','Excel for web: File → Options (…) → Copilot Settings','Formula completion: suggests after typing =','Formula by Example: suggests formulas from sample outputs'].map((s,i)=><div key={s} style={{marginTop:25,fontSize:29,fontWeight:740,color:P.ink,borderBottom:'1px solid #dbe3e9',paddingBottom:18}}>{i+1}. {s}</div>)}
   <div style={{marginTop:23,fontSize:21,color:P.teal,fontWeight:900}}>Microsoft says the setting remains off until you turn it back on.</div>
  </Panel>}
  {section==='outro'&&<div style={{position:'absolute',top:330,left:130,right:130,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:26}}>
   {[['01','RANGE','All rows included?'],['02','MEANING','The right business metric?'],['03','EDGE CASES','Messy data tested?']].map(([i,a,b])=><Panel key={a} style={{padding:35,height:400}}><div style={{fontSize:25,color:P.teal,fontWeight:900}}>{i}</div><div style={{fontSize:46,fontWeight:950,color:P.ink,marginTop:25}}>{a}</div><div style={{fontSize:27,color:P.muted,marginTop:24,lineHeight:1.2}}>{b}</div></Panel>)}
  </div>}
  <div style={{position:'absolute',bottom:23,left:100,right:100,height:5,borderRadius:4,background:'#d9e2e7'}}><div style={{width:(f/6383*100)+'%',height:5,background:P.teal,borderRadius:4}}/></div>
  <Audio src={staticFile('voice-long-004.mp3')}/>
 </AbsoluteFill>;
};
const Thumb:React.FC=()=> <AbsoluteFill style={{background:'radial-gradient(circle at 54% 12%,#22495a,#0a1622 76%)',fontFamily:L}}>
 <div style={{position:'absolute',left:85,top:62,color:'#8bd2b2',letterSpacing:2,fontSize:22,fontWeight:900}}>FLOWMINUTE LAB  •  EXCEL AI</div>
 <div style={{position:'absolute',left:87,top:160,fontSize:93,fontWeight:950,lineHeight:.99,color:'#fff',maxWidth:1310}}>ONE ROW.<br/>$3,600 MISSING.</div>
 <div style={{position:'absolute',left:85,top:475,right:87,display:'grid',gridTemplateColumns:'1fr 1fr',gap:24}}>
  <div style={{background:'#54242c',border:'4px solid #fd7482',borderRadius:23,padding:30,boxShadow:'0 25px 70px #0007'}}><div style={{fontSize:27,fontWeight:900,color:'#ffb3b8'}}>FORMULA SAID</div><div style={{fontSize:92,fontWeight:950,color:'#fff'}}>$18,900</div></div>
  <div style={{background:'#184936',border:'4px solid #50d98e',borderRadius:23,padding:30,boxShadow:'0 25px 70px #0007'}}><div style={{fontSize:27,fontWeight:900,color:'#b6f9ce'}}>ACTUAL TOTAL</div><div style={{fontSize:92,fontWeight:950,color:'#fff'}}>$22,500</div></div>
 </div>
 <div style={{position:'absolute',left:96,bottom:105,fontSize:52,color:'#fff',fontWeight:850}}>3 checks before you trust Excel AI</div>
 <div style={{position:'absolute',right:105,top:94,width:260,height:260,borderRadius:130,background:'#f4bd4b',display:'flex',alignItems:'center',justifyContent:'center',fontSize:145,fontWeight:950,color:'#362414',transform:'rotate(14deg)',boxShadow:'0 20px 60px #0009'}}>!</div>
</AbsoluteFill>;
export const FormulaRangeShort:React.FC=()=> <ShotShort variant="range"/>;
export const FormulaExampleShort:React.FC=()=> <ShotShort variant="name"/>;
export const FormulaAuditLong:React.FC=()=> <LongVideo/>;
export const FormulaAuditThumbnail:React.FC=()=> <Thumb/>;
