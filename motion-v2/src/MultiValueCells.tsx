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
  excel:'#217346',excelDark:'#185c37',bg:'#edf2f6',text:'#1f2933',muted:'#697684',
  grid:'#d9dfe5',ribbon:'#f7f9fb',white:'#fff',blue:'#2f80d1',cyan:'#1aa7c7',
  green:'#218653',red:'#d74b4b',amber:'#c58a16',purple:'#7957c7',ink:'#0d1722'
};

const ease=(f:number,i:number[],o:number[])=>interpolate(f,i,o,{
  extrapolateLeft:'clamp',extrapolateRight:'clamp',
  easing:Easing.bezier(.2,.75,.2,1)
});

const Fade:React.FC<{from:number;to:number;children:React.ReactNode}>=({from,to,children})=>{
  const f=useCurrentFrame();
  const op=Math.min(ease(f,[from,from+8],[0,1]),ease(f,[to-8,to],[1,0]));
  return <div style={{opacity:op}}>{children}</div>;
};

const Brand:React.FC<{label:string;vertical?:boolean}>=({label,vertical=false})=><div style={{
  position:'absolute',left:vertical?48:56,right:vertical?48:56,top:vertical?38:30,zIndex:80,
  display:'flex',alignItems:'center',justifyContent:'space-between',
  fontFamily:'Segoe UI,Arial',fontSize:vertical?19:18,fontWeight:850,letterSpacing:1.1,color:'#5c6875'
}}>
  <span>FLOWMINUTE LAB</span><span style={{color:C.excel}}>{label}</span>
</div>;

const Cursor:React.FC<{x:number;y:number;click?:number;scale?:number}>=({x,y,click=0,scale=1})=><div style={{
  position:'absolute',left:x,top:y,width:28,height:40,zIndex:90,
  transform:`scale(${scale*(1-click*.12)})`,transformOrigin:'3px 3px',
  filter:'drop-shadow(0 2px 2px rgba(0,0,0,.26))'
}}>
  <div style={{width:27,height:38,background:'#fff',border:'1px solid #111',
    clipPath:'polygon(0 0,0 34px,8px 26px,14px 39px,20px 36px,14px 23px,27px 22px)'}}/>
</div>;

const Caption:React.FC<{items:Array<[number,number,string]>;vertical?:boolean}>=({items,vertical=false})=>{
  const f=useCurrentFrame();
  const it=items.find(([a,b])=>f>=a&&f<b);
  if(!it)return null;
  const [a,b,t]=it;
  const op=Math.min(ease(f,[a,a+5],[0,1]),ease(f,[b-6,b],[1,0]));
  return <div style={{
    position:'absolute',left:vertical?55:210,right:vertical?55:210,
    top:vertical?1540:930,zIndex:120,display:'flex',justifyContent:'center',opacity:op
  }}>
    <div style={{
      background:'rgba(11,18,25,.86)',color:'#fff',borderRadius:vertical?14:12,
      padding:vertical?'11px 17px 12px':'10px 17px 11px',
      fontFamily:'Segoe UI,Arial',fontSize:vertical?37:31,fontWeight:650,lineHeight:1.12,
      boxShadow:'0 8px 24px rgba(0,0,0,.20)',textAlign:'center'
    }}>{t}</div>
  </div>;
};

const CinematicDesk:React.FC<{vertical?:boolean;warning?:boolean}>=({vertical=false,warning=false})=>{
  const f=useCurrentFrame();
  const drift=ease(f,[0,90],[0,1]);
  const W=vertical?1080:1920,H=vertical?1920:1080;
  return <AbsoluteFill style={{overflow:'hidden',background:`radial-gradient(circle at 62% 20%,${warning?'#4a171b':'#164458'} 0%,#0a141d 43%,#05090d 100%)`}}>
    <div style={{position:'absolute',left:-100,top:-80,width:W+200,height:H+160,
      transform:`scale(${1.03+drift*.02}) translateX(${-drift*12}px)`,
      background:'linear-gradient(120deg,rgba(255,255,255,.04),transparent 40%,rgba(54,201,255,.05))'}}/>
    <div style={{
      position:'absolute',left:vertical?90:250,right:vertical?90:250,bottom:vertical?300:120,height:vertical?860:650,
      transform:'perspective(1200px) rotateX(2deg)',borderRadius:24,
      background:'linear-gradient(180deg,#151d24,#0b1116)',boxShadow:'0 60px 150px rgba(0,0,0,.6)'
    }}>
      <div style={{
        position:'absolute',left:'12%',right:'12%',top:'5%',height:'58%',borderRadius:16,
        background:'linear-gradient(180deg,#181f24,#10171c)',border:'5px solid #202a31',
        boxShadow:'0 0 75px rgba(50,185,220,.18)'
      }}>
        <div style={{position:'absolute',inset:18,borderRadius:6,overflow:'hidden',background:'#f8fafb'}}>
          <div style={{height:'11%',background:C.excelDark}}/>
          <div style={{height:'9%',background:'#f6f8fa',borderBottom:'1px solid #d8dee5'}}/>
          <div style={{position:'absolute',left:'7%',top:'28%',right:'7%',bottom:'9%',
            backgroundImage:'linear-gradient(#e2e7eb 1px,transparent 1px),linear-gradient(90deg,#e2e7eb 1px,transparent 1px)',
            backgroundSize:'11% 13%'}}/>
          <div style={{position:'absolute',left:'18%',top:'39%',width:'35%',height:'13%',
            border:`3px solid ${C.excel}`,background:'#eef8f2',boxShadow:'0 0 24px rgba(33,115,70,.22)'}}/>
          <div style={{position:'absolute',left:'20%',top:'42%',fontFamily:'Segoe UI,Arial',fontSize:vertical?19:22,fontWeight:800,color:C.text}}>
            Carlos · Henrietta · Jacob
          </div>
        </div>
      </div>
      <div style={{position:'absolute',left:'18%',right:'18%',bottom:'13%',height:'13%',borderRadius:'10px 10px 30px 30px',
        background:'linear-gradient(180deg,#29333b,#11181e)',boxShadow:'0 24px 45px rgba(0,0,0,.45)'}}/>
      <div style={{position:'absolute',left:'44%',bottom:'16%',width:'12%',height:'4%',borderRadius:20,background:'#0a0e12'}}/>
    </div>
    <div style={{position:'absolute',left:vertical?80:170,bottom:vertical?160:72,
      fontFamily:'Segoe UI,Arial',color:'#fff'}}>
      <div style={{fontSize:vertical?19:18,fontWeight:900,letterSpacing:2,color:warning?'#ff9b9b':'#8fe8ff'}}>CINEMATIC CONTEXT</div>
      <div style={{fontSize:vertical?43:52,fontWeight:900,marginTop:8,lineHeight:1.04,maxWidth:vertical?760:980}}>
        {warning?'New does not mean production-ready.':'One cell is becoming more than one value.'}
      </div>
    </div>
  </AbsoluteFill>;
};

const ListBadge:React.FC<{items:string[];compact?:boolean}>=({items,compact=false})=><div style={{
  display:'inline-flex',alignItems:'center',gap:compact?6:8,maxWidth:'100%',
  padding:compact?'4px 7px':'7px 9px',borderRadius:7,background:'#edf8f1',
  border:'1px solid #9fceb2',color:C.text,fontWeight:700,fontSize:compact?14:17
}}>
  <span style={{width:compact?16:19,height:compact?16:19,borderRadius:4,background:C.excel,color:'#fff',
    display:'inline-flex',alignItems:'center',justifyContent:'center',fontSize:compact?10:11}}>≡</span>
  <span>{items.length} items</span>
</div>;

const ListPopup:React.FC<{items:string[];x:number;y:number;w?:number;filter?:boolean}>=({items,x,y,w=300,filter=false})=><div style={{
  position:'absolute',left:x,top:y,width:w,zIndex:60,background:'#fff',
  border:'1px solid #bcc7d0',borderRadius:9,boxShadow:'0 20px 55px rgba(30,45,60,.22)',
  padding:'9px 0',fontFamily:'Segoe UI,Arial'
}}>
  {filter&&<div style={{padding:'8px 14px 12px',fontSize:13,fontWeight:850,color:C.muted,borderBottom:'1px solid #edf0f3'}}>FILTER BY LIST ITEM</div>}
  {items.map((x,i)=><div key={x} style={{height:40,display:'flex',alignItems:'center',padding:'0 14px',gap:10,
    background:i===1?'#f1f8f4':'#fff',fontSize:17,color:C.text}}>
    {filter&&<span style={{width:16,height:16,borderRadius:3,border:'1px solid #8ea0af',
      background:i===1?C.excel:'#fff',color:'#fff',fontSize:12,textAlign:'center',lineHeight:'15px'}}>{i===1?'✓':''}</span>}
    {x}
  </div>)}
</div>;

const ExcelShell:React.FC<{
  children:React.ReactNode;
  title?:string;
  ribbon?:'Home'|'Insert'|'Data'|'Formulas';
  formula?:string;
  vertical?:boolean;
}>=({children,title='project_tracker.xlsx',ribbon='Home',formula='',vertical=false})=>{
  const left=vertical?35:120, top=vertical?138:105, width=vertical?1010:1680, height=vertical?1280:850;
  return <div style={{position:'absolute',left,top,width,height,fontFamily:'Segoe UI,Arial',zIndex:20}}>
    <div style={{position:'absolute',inset:0,borderRadius:vertical?18:16,overflow:'hidden',
      background:'#fff',border:'1px solid #b7c0c9',boxShadow:'0 34px 90px rgba(20,36,50,.20)'}}>
      <div style={{height:vertical?56:45,background:C.excelDark,color:'#fff',display:'flex',alignItems:'center',
        padding:'0 18px',fontSize:vertical?20:18,fontWeight:650}}>
        <span style={{fontWeight:850,marginRight:18}}>Excel</span>{title}
        <span style={{marginLeft:'auto',opacity:.78,fontSize:vertical?15:14}}>Microsoft 365 Beta</span>
      </div>
      <div style={{height:vertical?54:47,background:C.ribbon,borderBottom:'1px solid #d8dee4',
        display:'flex',alignItems:'center',gap:vertical?24:30,padding:'0 20px',fontSize:vertical?17:16}}>
        {['File','Home','Insert','Page Layout','Formulas','Data','Review','View'].map(t=><div key={t} style={{
          height:'100%',display:'flex',alignItems:'center',fontWeight:t===ribbon?800:500,
          color:t===ribbon?C.excel:C.text,borderBottom:t===ribbon?`3px solid ${C.excel}`:'3px solid transparent'
        }}>{t}</div>)}
      </div>
      <div style={{height:vertical?80:66,display:'flex',alignItems:'center',gap:12,padding:'0 18px',borderBottom:'1px solid #dde2e7'}}>
        <div style={{padding:'9px 12px',border:'1px solid #c7d0d9',borderRadius:5,fontSize:vertical?16:15}}>Paste</div>
        {ribbon==='Insert'&&<div style={{padding:'10px 15px',border:'2px solid #72aa88',borderRadius:6,background:'#edf8f1',color:C.excel,fontWeight:850,fontSize:vertical?17:16}}>List</div>}
        {ribbon==='Data'&&<div style={{padding:'9px 12px',border:'1px solid #c7d0d9',borderRadius:5,fontSize:vertical?16:15}}>Filter</div>}
        <div style={{padding:'9px 12px',border:'1px solid #c7d0d9',borderRadius:5,fontSize:vertical?16:15}}>Format as Table</div>
      </div>
      <div style={{height:vertical?54:47,display:'flex',alignItems:'center',gap:10,padding:'0 15px',background:'#fbfcfd',borderBottom:'1px solid #dde2e7'}}>
        <div style={{width:36,height:31,border:'1px solid #c8d0d8',borderRadius:4,display:'flex',alignItems:'center',justifyContent:'center',fontStyle:'italic',color:C.muted}}>fx</div>
        <div style={{height:31,flex:1,border:'1px solid #c8d0d8',borderRadius:4,display:'flex',alignItems:'center',padding:'0 10px',
          fontFamily:'Consolas,monospace',fontSize:vertical?15:15,color:'#34414e',background:'#fff'}}>{formula}</div>
      </div>
      <div style={{position:'absolute',left:0,right:0,top:vertical?244:205,bottom:0,background:'#fff'}}>{children}</div>
    </div>
  </div>;
};

const Grid:React.FC<{vertical?:boolean;mode:'old'|'list'|'filter'|'spill'|'array'|'functions'|'tickets'}>=({vertical=false,mode})=>{
  const f=useCurrentFrame();
  const widths=vertical?[190,320,300,200]:[250,430,430,340];
  const headers=mode==='array'?['Run','Splits','Average','Best']:mode==='tickets'?['Ticket','Labels','Owner','Status']:['Task','Owners','Due','Status'];
  const rows=mode==='array'
    ?[['Morning 5K','5 items','4:47','4:43'],['Tempo','4 items','4:31','4:22'],['Easy','5 items','5:12','5:03']]
    :mode==='tickets'
      ?[['T-104','3 items','Mira','Open'],['T-105','2 items','Sam','Open'],['T-106','3 items','Ava','Closed']]
      :[['Launch page',mode==='old'?'Carlos, Henrietta, Jacob':'3 items','12 Oct','In progress'],['Pricing QA',mode==='old'?'Henrietta, Sam':'2 items','13 Oct','Blocked'],['Docs refresh',mode==='old'?'Ava, Carlos':'2 items','15 Oct','Ready']];
  const selectedRow=mode==='filter'?0:-1;
  return <div style={{position:'absolute',left:0,top:0,right:0,bottom:0}}>
    <div style={{position:'absolute',left:0,top:0,width:42,bottom:0,background:'#f2f5f7',borderRight:'1px solid #d8dee5'}}/>
    <div style={{position:'absolute',left:42,top:0,right:0,height:36,background:'#f2f5f7',borderBottom:'1px solid #d8dee5'}}/>
    {['A','B','C','D'].map((h,i)=><div key={h} style={{position:'absolute',left:42+widths.slice(0,i).reduce((a,b)=>a+b,0),top:0,width:widths[i],height:36,
      display:'flex',alignItems:'center',justifyContent:'center',borderRight:'1px solid #d8dee5',fontSize:13,color:C.muted}}>{h}</div>)}
    {headers.map((h,i)=><div key={h} style={{position:'absolute',left:42+widths.slice(0,i).reduce((a,b)=>a+b,0),top:36,width:widths[i],height:54,
      display:'flex',alignItems:'center',padding:'0 12px',boxSizing:'border-box',borderRight:'1px solid #d8dee5',borderBottom:'1px solid #d8dee5',
      background:'#eef5f0',fontSize:vertical?17:16,fontWeight:800,color:C.text}}>{h}</div>)}
    {rows.map((row,r)=>row.map((v,c)=>{
      const x=42+widths.slice(0,c).reduce((a,b)=>a+b,0),y=90+r*64;
      const listCell=c===1&&mode!=='old';
      return <div key={r+'-'+c} style={{position:'absolute',left:x,top:y,width:widths[c],height:64,padding:'0 12px',boxSizing:'border-box',
        display:'flex',alignItems:'center',borderRight:'1px solid #e0e5ea',borderBottom:'1px solid #e0e5ea',fontSize:vertical?18:17,color:C.text,
        background:selectedRow===r&&c===1?'#f1f9f4':'#fff',boxShadow:selectedRow===r&&c===1?`inset 0 0 0 3px ${C.excel}`:'none'}}>
        {listCell?<ListBadge items={r===0?['Carlos','Henrietta','Jacob']:['A','B']} compact={vertical}/>:v}
      </div>;
    }))}
    {mode==='spill'&&<>
      {['Carlos','Henrietta','Jacob'].map((x,i)=><div key={x} style={{position:'absolute',left:42+widths[0]+widths[1]+32,top:318+i*52,width:260,height:52,
        display:'flex',alignItems:'center',padding:'0 12px',background:'#eef8f2',border:'1px solid #9dcdb0',fontWeight:750,color:C.text}}>{x}</div>)}
      <div style={{position:'absolute',left:42+widths[0]+widths[1]+32,top:286,fontSize:14,fontWeight:850,color:C.green}}>REFERENCE B2 → SPILLS</div>
    </>}
    {mode==='array'&&<ListPopup items={['4:52','4:47','4:49','4:43','4:45']} x={42+widths[0]+35} y={170} w={250}/>}
    {mode==='tickets'&&<ListPopup items={['billing','login','urgent']} x={42+widths[0]+40} y={170} w={260}/>}
    {mode==='filter'&&<ListPopup filter items={['Carlos','Henrietta','Jacob','Sam','Ava']} x={42+widths[0]+widths[1]-60} y={42} w={300}/>}
    {mode==='functions'&&<div style={{position:'absolute',left:75,top:315,right:80,display:'grid',gridTemplateColumns:'1fr 1fr',gap:14}}>
      {[
        ['HAS','Does this cell contain Henrietta?','TRUE'],
        ['HASANY','Any requested tag exists?','TRUE'],
        ['HASALL','Every requested tag exists?','FALSE'],
        ['FLATTEN','Flatten nested arrays','3 × 1']
      ].map(([fn,desc,res])=><div key={fn} style={{padding:'15px 16px',borderRadius:11,border:'1px solid #cbd5de',background:'#f9fbfc'}}>
        <div style={{fontSize:15,fontWeight:900,color:C.purple}}>{fn}</div>
        <div style={{fontSize:14,color:C.muted,marginTop:4}}>{desc}</div>
        <div style={{fontSize:25,fontWeight:900,color:res==='FALSE'?C.red:C.green,marginTop:8}}>{res}</div>
      </div>)}
    </div>}
  </div>;
};

const ShortHook:React.FC<{warning?:boolean}>=({warning=false})=>{
  const f=useCurrentFrame();
  const p=ease(f,[0,10,68,78],[0,1,1,0]);
  return <div style={{position:'absolute',left:65,right:65,top:145,zIndex:100,opacity:p,transform:`translateY(${(1-p)*-10}px)`}}>
    <div style={{background:'#fff',borderRadius:18,padding:'18px 22px',boxShadow:'0 18px 52px rgba(20,35,48,.18)',border:'1px solid #cad3dc',
      fontFamily:'Segoe UI,Arial'}}>
      <div style={{fontSize:16,fontWeight:900,letterSpacing:1.2,color:warning?C.red:C.excel}}>{warning?'BETA WARNING':'PROOF FIRST'}</div>
      <div style={{fontSize:48,lineHeight:1.02,fontWeight:900,color:C.text,marginTop:8}}>{warning?'Amazing feature. Not production-ready yet.':'One Excel cell. Three real values.'}</div>
    </div>
  </div>;
};

const ShortExcel:React.FC<{warning?:boolean}>=({warning=false})=>{
  const f=useCurrentFrame();
  const list=warning?true:f>=90;
  const filter=!warning&&f>=300&&f<570;
  const spill=!warning&&f>=570;
  const mode=warning?'list':filter?'filter':spill?'spill':list?'list':'old';
  const formula=warning?'=B2':spill?'=B2':filter?'Filter: Henrietta':list?'Insert > List':'Carlos, Henrietta, Jacob';
  const curX=ease(f,[0,80,180,320,520,690,900],[780,780,620,760,820,680,680]);
  const curY=ease(f,[0,80,180,320,520,690,900],[780,780,490,380,490,760,760]);
  const click=Math.max(ease(f,[180,184,190],[0,1,0]),ease(f,[420,424,430],[0,1,0]),ease(f,[665,669,675],[0,1,0]));
  return <div>
    <ExcelShell vertical title={warning?'beta_workbook.xlsx':'project_tracker.xlsx'} ribbon={filter?'Data':list?'Insert':'Home'} formula={formula}>
      <Grid vertical mode={mode as any}/>
    </ExcelShell>
    <Cursor x={curX} y={curY} click={click}/>
  </div>;
};

const WarningCards:React.FC=()=>{
  const f=useCurrentFrame();
  const cards=[
    ['PivotTables','Array values are not read as source data.'],
    ['Charts','Arrays are not expanded into plotted data points.'],
    ['Power Query','Does not load or emit array-valued columns.'],
    ['Data validation','Cannot use list/array values as dropdown items.']
  ];
  return <div style={{position:'absolute',left:72,right:72,top:360,zIndex:85,display:'grid',gridTemplateColumns:'1fr 1fr',gap:15}}>
    {cards.map((x,i)=>{
      const p=ease(f,[180+i*75,198+i*75],[0,1]);
      return <div key={x[0]} style={{opacity:p,transform:`translateY(${(1-p)*15}px)`,padding:'17px 18px',borderRadius:14,
        background:'rgba(255,255,255,.96)',border:'1px solid #e0b5b5',boxShadow:'0 14px 35px rgba(50,24,24,.12)',fontFamily:'Segoe UI,Arial'}}>
        <div style={{fontSize:22,fontWeight:900,color:C.red}}>{x[0]}</div>
        <div style={{fontSize:16,lineHeight:1.3,color:C.text,marginTop:5}}>{x[1]}</div>
      </div>;
    })}
  </div>;
};

export const MultiValueRuleShort:React.FC=()=>{
  const f=useCurrentFrame();
  const caps:Array<[number,number,string]>=[
    [0,95,'Excel just broke one of its oldest rules.'],
    [95,245,'One cell can now hold a real list — not just comma-separated text.'],
    [245,430,'Filter by an individual item inside the list.'],
    [430,625,'Reference the cell and its values can spill back out.'],
    [625,820,'New functions like HAS and FLATTEN work with this model.'],
    [820,1050,'It is still Beta — but this changes what one cell can be.']
  ];
  return <AbsoluteFill style={{background:'linear-gradient(180deg,#e9eef2,#f7f9fa)',overflow:'hidden'}}>
    <Brand vertical label="EXCEL BETA · LISTS IN CELLS"/>
    <ShortExcel/>
    <ShortHook/>
    <Caption items={caps} vertical/>
    <Sequence from={0}><Audio src={staticFile('voice-v7.mp3')} volume={1}/></Sequence>
    <div style={{position:'absolute',left:55,right:55,bottom:55,height:4,background:'rgba(30,50,65,.09)',borderRadius:5}}>
      <div style={{height:'100%',width:`${Math.min(100,f/1049*100)}%`,background:`linear-gradient(90deg,${C.excel},${C.cyan})`,borderRadius:5}}/>
    </div>
  </AbsoluteFill>;
};

export const MultiValueWarningShort:React.FC=()=>{
  const f=useCurrentFrame();
  const caps:Array<[number,number,string]>=[
    [0,120,'Excel’s new multi-value cells look amazing.'],
    [120,270,'But Microsoft says this is still a Beta preview.'],
    [270,520,'PivotTables, charts, Power Query, and validation still have limits.'],
    [520,760,'So test it — don’t rebuild an important workbook around it yet.'],
    [760,1140,'Promising? Yes. Production-ready for every workflow? Not yet.']
  ];
  const broll=ease(f,[0,65,110,145],[1,1,0,0]);
  return <AbsoluteFill style={{background:'linear-gradient(180deg,#f0ecec,#f8f8f8)',overflow:'hidden'}}>
    <div style={{opacity:broll}}><CinematicDesk vertical warning/></div>
    <div style={{opacity:ease(f,[105,145],[0,1])}}>
      <Brand vertical label="EXCEL BETA · LIMITATIONS"/>
      <ShortExcel warning/>
      <ShortHook warning/>
      <WarningCards/>
    </div>
    <Caption items={caps} vertical/>
    <Sequence from={0}><Audio src={staticFile('voice-v8.mp3')} volume={1}/></Sequence>
    <div style={{position:'absolute',left:55,right:55,bottom:55,height:4,background:'rgba(60,25,25,.08)',borderRadius:5}}>
      <div style={{height:'100%',width:`${Math.min(100,f/1139*100)}%`,background:`linear-gradient(90deg,${C.red},${C.amber})`,borderRadius:5}}/>
    </div>
  </AbsoluteFill>;
};

const LongSceneTitle:React.FC<{eyebrow:string;title:string;sub?:string;color?:string}>=({eyebrow,title,sub,color=C.cyan})=><div style={{
  position:'absolute',left:110,right:110,top:160,zIndex:70,fontFamily:'Segoe UI,Arial'
}}>
  <div style={{fontSize:18,fontWeight:900,letterSpacing:1.6,color}}>{eyebrow}</div>
  <div style={{fontSize:61,lineHeight:1.02,fontWeight:900,color:C.text,marginTop:10,maxWidth:1250}}>{title}</div>
  {sub&&<div style={{fontSize:25,lineHeight:1.35,color:C.muted,marginTop:14,maxWidth:1120}}>{sub}</div>}
</div>;

const LongExcelScene:React.FC<{mode:'old'|'list'|'filter'|'spill'|'array'|'functions'|'tickets';ribbon?:'Home'|'Insert'|'Data'|'Formulas';formula?:string;title?:string}>=({mode,ribbon='Home',formula='',title})=>
  <ExcelShell title={title??'project_tracker.xlsx'} ribbon={ribbon} formula={formula}><Grid mode={mode}/></ExcelShell>;

const LimitationGrid:React.FC=()=> <div style={{position:'absolute',left:150,right:150,top:315,bottom:120,display:'grid',gridTemplateColumns:'1fr 1fr',gap:22,fontFamily:'Segoe UI,Arial'}}>
  {[
    ['PivotTables','Do not read array values as source data.'],
    ['Charts','Do not expand an array into chart points.'],
    ['Power Query','Does not load or emit array-valued columns.'],
    ['Data validation','Cannot use a list or array as dropdown items.'],
    ['Find & Replace','Cannot replace items inside lists or arrays.'],
    ['Compatibility v3','Required for many nested-array calculations.']
  ].map(([h,b])=><div key={h} style={{padding:'21px 22px',borderRadius:14,background:'#fff',border:'1px solid #e2c2c2',boxShadow:'0 16px 38px rgba(40,25,25,.08)'}}>
    <div style={{fontSize:23,fontWeight:900,color:C.red}}>{h}</div><div style={{fontSize:19,color:C.text,lineHeight:1.35,marginTop:7}}>{b}</div>
  </div>)}
</div>;

const Decision:React.FC=()=> <div style={{position:'absolute',left:165,right:165,top:250,bottom:150,display:'grid',gridTemplateColumns:'1fr 1fr',gap:28,fontFamily:'Segoe UI,Arial'}}>
  <div style={{padding:30,borderRadius:18,background:'#eef9f2',border:'1px solid #9ccdb0'}}>
    <div style={{fontSize:19,fontWeight:900,color:C.green,letterSpacing:1}}>USE IT NOW FOR</div>
    {['Learning and experiments','Disposable Beta workbooks','Testing trackers and tags','Exploring new formulas'].map(x=><div key={x} style={{fontSize:28,fontWeight:750,color:C.text,marginTop:23}}>✓ {x}</div>)}
  </div>
  <div style={{padding:30,borderRadius:18,background:'#fff3f1',border:'1px solid #e0aaa4'}}>
    <div style={{fontSize:19,fontWeight:900,color:C.red,letterSpacing:1}}>WAIT FOR PRODUCTION IF</div>
    {['Power Query is critical','PivotTables/charts depend on it','Others need stable compatibility','The workbook is business-critical'].map(x=><div key={x} style={{fontSize:28,fontWeight:750,color:C.text,marginTop:23}}>× {x}</div>)}
  </div>
</div>;

export const MultiValueCellsLong:React.FC=()=>{
  const f=useCurrentFrame();
  const total=8640;
  const section=
    f<250?'hook':f<1100?'old':f<2300?'list':f<3300?'filter':f<4300?'array':
    f<5350?'functions':f<6450?'tickets':f<7550?'limits':f<8300?'decision':'outro';
  const scene=(s:string)=>section===s?1:0;
  return <AbsoluteFill style={{background:'linear-gradient(180deg,#edf2f6,#f7f9fb)',overflow:'hidden'}}>
    <Brand label={
      section==='hook'?'EXCEL CHANGED AFTER 40 YEARS':
      section==='limits'?'BETA LIMITATIONS':
      section==='decision'?'SHOULD YOU USE IT?':'LISTS + ARRAYS IN CELLS'
    }/>

    <div style={{opacity:scene('hook')}}><CinematicDesk/></div>

    {section==='old'&&<>
      <LongSceneTitle eyebrow="THE OLD PAIN" title="Three owners. One text blob." sub="It looks organized, but Excel mainly sees one long string." color={C.amber}/>
      <LongExcelScene mode="old" formula="Carlos, Henrietta, Jacob"/>
    </>}

    {section==='list'&&<>
      <LongSceneTitle eyebrow="NEW IN EXCEL BETA" title="One cell can hold a real list." sub="Insert > List, add the values, and Excel keeps the items structured." color={C.excel}/>
      <LongExcelScene mode="list" ribbon="Insert" formula="Insert > List · Carlos · Henrietta · Jacob"/>
      {f>1700&&<ListPopup items={['Carlos','Henrietta','Jacob']} x={680} y={410} w={330}/>}
    </>}

    {section==='filter'&&<>
      <LongSceneTitle eyebrow="PRACTICAL WIN #1" title="Filter by one item inside the cell." sub="The list behaves differently from comma-separated text." color={C.blue}/>
      <LongExcelScene mode={f<2820?'filter':'spill'} ribbon={f<2820?'Data':'Formulas'} formula={f<2820?'Filter: Henrietta':'=B2'}/>
    </>}

    {section==='array'&&<>
      <LongSceneTitle eyebrow="PRACTICAL WIN #2" title="Arrays can live inside a cell." sub="Keep variable-length measurements together, then spill or calculate when needed." color={C.purple}/>
      <LongExcelScene mode="array" ribbon="Formulas" formula={'={{4:52;4:47;4:49;4:43;4:45}}'} title="training_log.xlsx"/>
    </>}

    {section==='functions'&&<>
      <LongSceneTitle eyebrow="NEW ARRAY TOOLS" title="HAS, HASANY, HASALL, FLATTEN." sub="These functions make structured values easier to test and reshape." color={C.purple}/>
      <LongExcelScene mode="functions" ribbon="Formulas" formula={'=HAS(B2,"Henrietta")'}/>
    </>}

    {section==='tickets'&&<>
      <LongSceneTitle eyebrow="REAL WORKFLOW" title="A support ticket can keep several labels in one record." sub="Useful when the values naturally belong together — not as an excuse to hide an entire table in one cell." color={C.cyan}/>
      <LongExcelScene mode="tickets" ribbon="Data" formula={'=HAS(B2,"urgent")'} title="support_queue.xlsx"/>
    </>}

    {section==='limits'&&<>
      <div style={{position:'absolute',inset:0,background:'linear-gradient(180deg,#f4ecec,#faf8f8)'}}/>
      <LongSceneTitle eyebrow="HERE’S THE CATCH" title="This is still a preview." sub="Microsoft recommends not using it in important workbooks until general availability." color={C.red}/>
      <LimitationGrid/>
    </>}

    {section==='decision'&&<>
      <LongSceneTitle eyebrow="THE VERDICT" title="Learn it now. Use it selectively." sub="The goal is a clearer data model — not clever complexity." color={C.green}/>
      <Decision/>
    </>}

    {section==='outro'&&<div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 50% 30%,#153d32,#07120d 70%)'}}>
      <div style={{position:'absolute',left:210,right:210,top:250,textAlign:'center',fontFamily:'Segoe UI,Arial',color:'#fff'}}>
        <div style={{fontSize:19,fontWeight:900,letterSpacing:2,color:'#83e3ad'}}>FLOWMINUTE RULE</div>
        <div style={{fontSize:72,fontWeight:900,lineHeight:1.02,marginTop:25}}>Use multi-value cells when they make the data clearer.</div>
        <div style={{fontSize:31,color:'#bad3c5',marginTop:24}}>Not just because they are new.</div>
      </div>
    </div>}

    <Sequence from={0}><Audio src={staticFile('voice-long-003.mp3')} volume={1}/></Sequence>
    <div style={{position:'absolute',left:55,right:55,bottom:25,height:4,zIndex:200,background:'rgba(35,50,64,.10)',borderRadius:5}}>
      <div style={{height:'100%',width:`${Math.min(100,f/(total-1)*100)}%`,background:`linear-gradient(90deg,${C.excel},${C.cyan},${C.purple})`,borderRadius:5}}/>
    </div>
  </AbsoluteFill>;
};
