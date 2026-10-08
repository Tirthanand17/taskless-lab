import React from 'react';
import {AbsoluteFill,Audio,staticFile,useCurrentFrame,interpolate,Easing} from 'remotion';
const c={ink:'#193242',muted:'#607486',bg:'#edf3f8',line:'#d5e1e8',white:'#fff',green:'#187c4e',red:'#c63c49',blue:'#296ca6',navy:'#14283a'};
const ff='Segoe UI, Arial, sans-serif';
const fade=(f:number,a:number,b:number)=>interpolate(f,[a,b],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.bezier(.2,.75,.2,1)});
const Pad:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style={}})=><div style={{fontFamily:ff,background:'#fff',border:'1px solid #cfdae4',borderRadius:15,boxShadow:'0 17px 43px rgba(15,35,50,.13)',overflow:'hidden',...style}}>{children}</div>;
const Status:React.FC<{ok:boolean;text:string}>=({ok,text})=><span style={{display:'inline-flex',alignItems:'center',padding:'8px 13px',background:ok?'#e5f7ec':'#ffebed',color:ok?c.green:c.red,borderRadius:8,fontWeight:850,fontSize:19}}>{ok?'✓ ':'! '}{text}</span>;
const Top:React.FC<{vertical?:boolean;title:string;subtitle?:string}>=({vertical=false,title,subtitle})=><>
  <div style={{position:'absolute',top:vertical?48:28,left:vertical?58:95,right:vertical?58:95,display:'flex',justifyContent:'space-between',fontFamily:ff,fontSize:vertical?17:18,fontWeight:900,letterSpacing:1,color:c.green}}><span>FLOWMINUTE LAB</span><span>EXCEL · POWER QUERY</span></div>
  <div style={{position:'absolute',top:vertical?128:94,left:vertical?65:110,right:vertical?65:110,fontFamily:ff,color:c.ink}}>
    <div style={{fontSize:vertical?49:53,fontWeight:950,lineHeight:1.03,letterSpacing:-1.2}}>{title}</div>
    {subtitle&&<div style={{fontSize:vertical?22:22,color:c.muted,marginTop:12}}>{subtitle}</div>}
  </div>
</>;
const Source:React.FC<{fresh?:boolean;vertical?:boolean}>=({fresh=true,vertical=false})=><div style={{fontFamily:ff,height:'100%',background:'#fff'}}>
 <div style={{height:54,padding:'0 20px',background:'#eef4f8',display:'flex',alignItems:'center',justifyContent:'space-between',fontWeight:850,fontSize:vertical?19:20,color:c.ink}}><span>📁 Regional CSV source</span><span style={{fontSize:13,color:c.muted}}>DEMO DATA</span></div>
 {['North.csv','South.csv','West.csv',...(fresh?['East-new.csv']:[])].map((name,i)=><div key={name} style={{display:'flex',justifyContent:'space-between',alignItems:'center',height:vertical?67:62,padding:'0 24px',borderBottom:'1px solid #e1e8ed',fontSize:vertical?23:21,color:i===3?c.green:c.ink,fontWeight:700,background:i===3?'#e9f8ee':'#fff'}}><span>▤ &nbsp;{name}</span><span>4 orders</span></div>)}
 <div style={{display:'flex',justifyContent:'space-between',padding:'19px 22px',fontWeight:950,fontSize:vertical?30:34,color:c.ink}}><span>{fresh?'16 orders':'12 orders'}</span><span>{fresh?'$24,600':'$18,400'}</span></div>
 </div>;
const Flow:React.FC<{vertical?:boolean}>=({vertical=false})=><div style={{background:'#fbfcfe',height:'100%',fontFamily:ff}}>
 <div style={{height:56,background:'#eaf1f7',padding:'0 20px',display:'flex',alignItems:'center',fontWeight:850,fontSize:vertical?21:22,color:'#235278'}}>Power Automate · Cloud flow</div>
 <div style={{padding:vertical?17:25}}>
 {['New file detected','Run Office Script','Flow completed'].map((text,i)=><React.Fragment key={text}><div style={{background:'#fff',border:'1px solid #cdd8e2',borderRadius:9,padding:vertical?'16px 14px':'20px 23px',display:'flex',justifyContent:'space-between',alignItems:'center',fontWeight:750,fontSize:vertical?19:23,color:c.ink}}><span>{i===0?'⤵':i===1?'ƒ':'✓'} {text}</span><Status ok text="Success"/></div>{i<2&&<div style={{height:vertical?21:25,marginLeft:39,width:2,background:'#b2c7d6'}}/>}</React.Fragment>)}
 </div></div>;
const Report:React.FC<{fresh?:boolean;vertical?:boolean}>=({fresh=false,vertical=false})=><div style={{fontFamily:ff,height:'100%',background:'#fff'}}>
 <div style={{height:57,background:'#185e3d',color:'#fff',display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 18px',fontWeight:850,fontSize:vertical?19:21}}><span>Excel · Sales report</span><span style={{fontSize:13}}>DEMO WORKBOOK</span></div>
 <div style={{padding:vertical?'25px 23px':'24px 30px'}}>
 <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14}}>
 {[['Orders',fresh?'16':'12'],['Revenue',fresh?'$24,600':'$18,400']].map(([name,value])=><div key={name} style={{border:'1px solid #d1dfe6',background:fresh?'#e9f7ec':'#fff0f1',padding:vertical?'19px 12px':'21px 18px',borderRadius:11}}>
 <div style={{fontSize:vertical?19:19,color:c.muted,fontWeight:850}}>{name}</div><div style={{fontSize:vertical?36:45,color:fresh?c.green:c.red,fontWeight:950,marginTop:6}}>{value}</div></div>)}
 </div>
 <div style={{fontSize:vertical?19:20,color:c.muted,marginTop:23}}>Last order ID</div><div style={{fontFamily:'Consolas, monospace',fontSize:vertical?31:35,color:c.ink,fontWeight:850,marginTop:3}}>{fresh?'ORD-016':'ORD-012'}</div>
 <div style={{marginTop:24}}><Status ok={fresh} text={fresh?'Verified fresh':'STALE DATA'}/></div>
 </div></div>;
const FolderTable:React.FC<{fresh?:boolean;vertical?:boolean}>=({fresh=false,vertical=false})=><div style={{height:'100%',background:'#fff',fontFamily:ff}}>
 <div style={{height:54,background:'#e5f0e9',padding:'0 20px',display:'flex',alignItems:'center',fontWeight:850,fontSize:vertical?20:22,color:c.green}}>Power Query · Combine Files</div>
 <div style={{height:47,display:'flex',alignItems:'center',gap:21,padding:'0 18px',borderBottom:'1px solid #d9e5eb',fontSize:vertical?16:19,color:c.ink}}>Home <span style={{color:c.muted}}>Transform</span> <span style={{color:c.muted}}>Add Column</span></div>
 <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',background:'#e5f1e9',height:53,alignItems:'center',fontSize:vertical?19:21,fontWeight:900,color:'#274337'}}>{['OrderID','Region','Amount'].map(t=><span key={t} style={{paddingLeft:13}}>{t}</span>)}</div>
 {['North','South','West',...(fresh?['East']:[])].flatMap(reg=>[1,2,3,4].map(n=>reg)).map((reg,i)=><div key={i} style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',height:vertical?38:39,borderBottom:'1px solid #e1e8ed',alignItems:'center',fontSize:vertical?16:19,color:c.ink,background:i%2?'#f9fbfc':'#fff'}}><span style={{paddingLeft:12}}>{'ORD-'+String(i+1).padStart(3,'0')}</span><span style={{paddingLeft:12}}>{reg}</span><span style={{paddingLeft:12}}>{i<4?'$1,500':'$1,550'}</span></div>)}
 </div>;
const Caption:React.FC<{text:string;vertical?:boolean}>=({text,vertical=false})=><div style={{position:'absolute',top:vertical?1510:929,left:vertical?65:250,right:vertical?65:250,zIndex:100,display:'flex',justifyContent:'center'}}><span style={{padding:vertical?'13px 17px':'11px 18px',background:'rgba(12,29,43,.94)',color:'#fff',fontSize:vertical?35:28,fontFamily:ff,fontWeight:730,lineHeight:1.15,textAlign:'center',borderRadius:11}}>{text}</span></div>;
const Progress:React.FC<{f:number;max:number;vertical?:boolean}>=({f,max,vertical=false})=><div style={{position:'absolute',bottom:vertical?75:22,left:vertical?70:90,right:vertical?70:90,height:5,borderRadius:4,background:'#d1dce3'}}><div style={{width:(f/max*100)+'%',height:5,background:c.green,borderRadius:4}}/></div>;
const Stale:React.FC=()=>{const f=useCurrentFrame();const seq:[number,number,string][]=[[0,150,'The flow says success. But the dashboard is old.'],[150,360,'A cloud Office Script can finish without refreshing this CSV.'],[360,650,'The source has sixteen orders. Excel still has twelve.'],[650,895,'Microsoft documents why this happens.'],[895,1170,'Verify row count and source data, not just the green badge.']];
 const current=seq.find(([a,b])=>f>=a&&f<b);
 return <AbsoluteFill style={{background:'linear-gradient(140deg,#eff4f7,#e7eff4)',overflow:'hidden'}}><Top vertical title="SUCCESS… BUT STALE." subtitle="The green check did not update the report."/>
 <Pad style={{position:'absolute',left:55,right:55,top:365,height:500}}><Flow vertical/></Pad>
 <Pad style={{position:'absolute',left:55,right:55,top:905,height:545}}><Report vertical/></Pad>
 {current&&<Caption vertical text={current[2]}/>}<Progress f={f} max={1170} vertical/><Audio src={staticFile('voice-v11.mp3')}/></AbsoluteFill>;};
const Folder:React.FC=()=>{const f=useCurrentFrame(),fresh=f>580;const seq:[number,number,string][]=[[0,155,'Still copying CSV files one by one?'],[155,380,'Data → Get Data → From File → From Folder.'],[380,600,'Combine matching files into one table.'],[600,875,'Add a matching file, then run Refresh.'],[875,1140,'You can stop copying and pasting. Refresh still must run.']];
 const current=seq.find(([a,b])=>f>=a&&f<b);
 return <AbsoluteFill style={{background:'linear-gradient(135deg,#f1f4f6,#e8eff4)',overflow:'hidden'}}><Top vertical title="3 FILES → 1 TABLE" subtitle="Repeatable Power Query From Folder."/>
 <Pad style={{position:'absolute',left:55,right:55,top:345,height:488}}><Source fresh={fresh} vertical/></Pad>
 <div style={{position:'absolute',left:488,top:834,color:c.green,fontSize:52,fontWeight:900}}>↓</div>
 <Pad style={{position:'absolute',left:55,right:55,top:906,height:550}}><FolderTable fresh={fresh} vertical/></Pad>
 {current&&<Caption vertical text={current[2]}/>}<Progress f={f} max={1140} vertical/><Audio src={staticFile('voice-v12.mp3')}/></AbsoluteFill>;};
const Step:React.FC<{n:string;title:string;desc:string}>=({n,title,desc})=><Pad style={{height:220,padding:30,boxSizing:'border-box'}}><div style={{fontSize:21,color:c.green,fontWeight:950}}>{n}</div><div style={{fontSize:31,color:c.ink,fontWeight:950,marginTop:11}}>{title}</div><div style={{fontSize:23,color:c.muted,lineHeight:1.24,marginTop:12}}>{desc}</div></Pad>;
const Long:React.FC=()=>{const f=useCurrentFrame(),s=f/24;const stage=s<22?'hook':s<72?'stale':s<125?'why':s<182?'desktop':s<239?'cloud':s<285?'ingest':s<330?'folder':s<376?'verify':'outro';
 const info:{[key:string]:[string,string,string]}={
 hook:['ONE GREEN CHECK. OLD DATA.','The cloud flow finished. The workbook did not refresh.','Fictional sample workbook · supported Microsoft behavior'],
 stale:['THE PROOF','The source changed. The Excel dashboard did not.','Compare sixteen source orders against twelve old report rows'],
 why:['THE MICROSOFT LIMITATION','Some refresh calls succeed without refreshing data.','Power Automate Office Scripts: non-Power BI sources can be skipped'],
 desktop:['SOLUTION 1','Refresh when opening Excel Desktop.','Application refresh-on-open and intervals are not overnight cloud scheduling'],
 cloud:['SOLUTION 2','Choose a supported cloud refresh platform.','Power BI dataflow/semantic model · check licensing and credentials'],
 ingest:['SOLUTION 3','Move new records upstream.','Use supported connectors; handle duplicates and retries'],
 folder:['REAL PRACTICAL WORKFLOW','Use Power Query From Folder.','Matching CSV files, repeatable cleanup, refresh when needed'],
 verify:['THREE TRUST CHECKS','Verify the source, execution, and output.','A green badge alone cannot prove fresh records'],
 outro:['FLOWMINUTE RULE','Never trust only the green badge.','Check the source. Check the refresh. Check the result.']};
 const [category,title,sub]=info[stage];
 return <AbsoluteFill style={{background:'linear-gradient(145deg,#edf2f7,#f9fafb)',overflow:'hidden'}}><Top title={title} subtitle={sub}/>
 <div style={{position:'absolute',top:78,left:110,fontSize:17,color:c.green,fontWeight:900,fontFamily:ff,letterSpacing:1.1}}>{category}</div>
 {['hook','stale'].includes(stage)&&<div style={{position:'absolute',top:301,left:108,right:108,display:'grid',gridTemplateColumns:'1fr 1fr',gap:22}}><Pad style={{height:595}}><Source/></Pad><Pad style={{height:595}}><Report/></Pad></div>}
 {stage==='why'&&<div style={{position:'absolute',top:301,left:108,right:108,display:'grid',gridTemplateColumns:'1fr 1fr',gap:22}}><Pad style={{height:570}}><Flow/></Pad><Pad style={{height:570,padding:32,boxSizing:'border-box'}}><div style={{fontSize:21,fontWeight:900,color:c.red}}>WHAT THE SCRIPT ACTUALLY DID</div><div style={{background:'#eff4f8',borderRadius:12,marginTop:28,padding:23,fontFamily:'Consolas,monospace',fontWeight:800,fontSize:25,color:c.ink}}>workbook.refreshAllDataConnections()</div><div style={{fontSize:27,lineHeight:1.3,color:c.ink,marginTop:30}}>In a cloud flow, Microsoft says this refreshes only Power BI sources; for other sources it can return success and do nothing.</div><div style={{marginTop:31}}><Status ok={false} text="SUCCESS IS NOT FRESHNESS"/></div></Pad></div>}
 {stage==='desktop'&&<Pad style={{position:'absolute',top:309,left:120,right:120,padding:35,height:548}}><div style={{fontSize:25,fontWeight:900,color:c.green}}>EXCEL DESKTOP · CONNECTION USAGE</div>{['Data → Queries & Connections → Connection Properties','☑ Refresh data when opening the file','☑ Refresh every N minutes for supported connections','These options require an active Excel environment.'].map((x,i)=><div key={x} style={{background:i===3?'#e9f7ed':'#f5f8fa',padding:'18px 24px',border:'1px solid #d7e3e9',borderRadius:10,marginTop:20,color:i===3?c.green:c.ink,fontWeight:750,fontSize:26}}>{x}</div>)}</Pad>}
 {['cloud','ingest','verify'].includes(stage)&&<div style={{position:'absolute',top:324,left:123,right:123,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:25}}>
 {(stage==='cloud'?[['01','Supported scheduler','Refresh dataflows or semantic models in an appropriate cloud environment.'],['02','Access','Check permissions, credentials, gateway and licensing.'],['03','History','Confirm refresh actually completed and new data arrived.']]:stage==='ingest'?[['01','Collect','Use a supported connector to read new files or rows.'],['02','Validate','Handle failed files, duplicates, schema and retries.'],['03','Write','Update the target table and verify stored rows.']]:[['01','Source','Did new data arrive?'],['02','Refresh','Did a supported data refresh run?'],['03','Result','Did row count and totals change?']]).map(([n,h,b])=><Step key={n} n={n} title={h} desc={b}/>)}
 <Pad style={{gridColumn:'span 3',padding:28,marginTop:19,fontSize:27,color:c.ink,fontWeight:840}}>{stage==='cloud'?'Power BI is one possible route, not a required purchase for every Excel user.':stage==='ingest'?'Direct ingestion is not the same thing as telling Excel to refresh.':'Expected demo output: 16 orders • $24,600 • last ID ORD-016'}</Pad>
 </div>}
 {stage==='folder'&&<div style={{position:'absolute',top:307,left:105,right:105,display:'grid',gridTemplateColumns:'1fr 1.35fr',gap:23}}><Pad style={{height:573}}><Source fresh={s>309}/></Pad><Pad style={{height:573}}><FolderTable fresh={s>309}/></Pad></div>}
 {stage==='outro'&&<div style={{position:'absolute',top:345,left:120,right:120,fontFamily:ff,textAlign:'center'}}><div style={{fontSize:76,lineHeight:1.04,fontWeight:950,color:c.green}}>Flow status ≠ data freshness.</div><div style={{fontSize:33,marginTop:35,color:c.muted}}>Build for supported refresh. Verify the records.</div></div>}
 <Progress f={f} max={9120}/><Audio src={staticFile('voice-long-005.mp3')}/></AbsoluteFill>;
};
const Thumb:React.FC=()=> <AbsoluteFill style={{fontFamily:ff,background:'radial-gradient(circle at 76% 18%,#1f5361,#071927 72%)'}}>
 <div style={{position:'absolute',top:64,left:95,fontSize:23,fontWeight:900,color:'#9df4c5',letterSpacing:2}}>FLOWMINUTE LAB · POWER QUERY</div>
 <div style={{position:'absolute',top:159,left:93,right:120,fontSize:111,fontWeight:950,lineHeight:.98,letterSpacing:-2,color:'#fff'}}>SUCCESS.<br/>DATA STILL OLD.</div>
 <div style={{position:'absolute',top:516,left:98,right:98,display:'grid',gridTemplateColumns:'1fr 1fr',gap:28}}>
  <div style={{background:'#163e2e',border:'4px solid #44db8c',borderRadius:23,padding:29}}><div style={{fontSize:31,color:'#b4f7d0',fontWeight:900}}>POWER AUTOMATE</div><div style={{fontSize:83,color:'#fff',fontWeight:950}}>✓ SUCCESS</div></div>
  <div style={{background:'#512732',border:'4px solid #fc6e7b',borderRadius:23,padding:29}}><div style={{fontSize:31,color:'#ffd1d5',fontWeight:900}}>EXCEL OUTPUT</div><div style={{fontSize:83,color:'#fff',fontWeight:950}}>! STALE</div></div>
 </div>
 <div style={{position:'absolute',bottom:100,left:108,fontSize:44,fontWeight:800,color:'#e4f1f8'}}>3 real alternatives explained</div>
 </AbsoluteFill>;
export const StaleFlowShort:React.FC=()=> <Stale/>;
export const FromFolderShort:React.FC=()=> <Folder/>;
export const RefreshTruthLong:React.FC=()=> <Long/>;
export const RefreshTruthThumbnail:React.FC=()=> <Thumb/>;
