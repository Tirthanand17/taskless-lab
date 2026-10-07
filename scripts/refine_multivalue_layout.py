from pathlib import Path

p=Path("motion-v2/src/MultiValueCells.tsx")
c=p.read_text(encoding="utf-8")

repls=[
(
"const left=vertical?35:120, top=vertical?138:105, width=vertical?1010:1680, height=vertical?1280:850;",
"const left=vertical?35:120, top=vertical?310:300, width=vertical?1010:1680, height=vertical?600:690;"
),
(
"const list=warning?true:f>=90;",
"const list=warning?true:f>=15;"
),
(
"top:vertical?1540:930",
"top:vertical?1370:930"
),
(
"position:'absolute',left:110,right:110,top:160,zIndex:70,fontFamily:'Segoe UI,Arial'",
"position:'absolute',left:120,right:120,top:105,zIndex:70,fontFamily:'Segoe UI,Arial'"
),
(
"<div style={{fontSize:61,lineHeight:1.02,fontWeight:900,color:C.text,marginTop:10,maxWidth:1250}}>{title}</div>",
"<div style={{fontSize:54,lineHeight:1.02,fontWeight:900,color:C.text,marginTop:8,maxWidth:1450}}>{title}</div>"
),
(
"{sub&&<div style={{fontSize:25,lineHeight:1.35,color:C.muted,marginTop:14,maxWidth:1120}}>{sub}</div>}",
"{sub&&<div style={{fontSize:22,lineHeight:1.3,color:C.muted,marginTop:10,maxWidth:1320}}>{sub}</div>}"
),
(
"""  return <div>
    <ExcelShell vertical title={warning?'beta_workbook.xlsx':'project_tracker.xlsx'} ribbon={filter?'Data':list?'Insert':'Home'} formula={formula}>
      <Grid vertical mode={mode as any}/>
    </ExcelShell>
    <Cursor x={curX} y={curY} click={click}/>
  </div>;""",
"""  const inspectorTitle=warning?'DEPENDENCY CHECK':filter?'FILTER RESULT':spill?'CELL REFERENCE':list?'STRUCTURED LIST':'PLAIN TEXT';
  const inspectorMain=warning?'Beta feature — verify downstream tools first':filter?'Henrietta selected inside the list':spill?'=B2 → Carlos · Henrietta · Jacob':list?'Carlos · Henrietta · Jacob':'Carlos, Henrietta, Jacob';
  const inspectorSub=warning?'Power Query · PivotTables · Charts · Validation':filter?'Filter by an individual item, not one text blob':spill?'The list spills as separate values for calculation':list?'One cell · three structured values':'One cell · one long string';
  return <div>
    <ExcelShell vertical title={warning?'beta_workbook.xlsx':'project_tracker.xlsx'} ribbon={filter?'Data':list?'Insert':'Home'} formula={formula}>
      <Grid vertical mode={mode as any}/>
    </ExcelShell>
    <Cursor x={curX} y={curY} click={click}/>
    <div style={{
      position:'absolute',left:78,right:78,top:950,height:175,zIndex:75,
      borderRadius:15,background:'rgba(255,255,255,.96)',border:'1px solid #c8d2da',
      boxShadow:'0 16px 42px rgba(22,38,52,.14)',padding:'16px 19px',boxSizing:'border-box',
      fontFamily:'Segoe UI,Arial'
    }}>
      <div style={{fontSize:15,fontWeight:900,letterSpacing:1.2,color:warning?C.red:C.excel}}>{inspectorTitle}</div>
      <div style={{fontSize:29,fontWeight:900,color:C.text,marginTop:7,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{inspectorMain}</div>
      <div style={{fontSize:17,color:C.muted,marginTop:7}}>{inspectorSub}</div>
    </div>
  </div>;"""
)
]

for old,new in repls:
    if old not in c:
        raise SystemExit("missing patch target: "+old[:100])
    c=c.replace(old,new,1)

p.write_text(c,encoding="utf-8")
print("multi-value layout refinement applied")
