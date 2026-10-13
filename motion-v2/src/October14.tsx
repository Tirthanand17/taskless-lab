import React from 'react';
import {AbsoluteFill,Audio,Img,OffthreadVideo,interpolate,staticFile,useCurrentFrame} from 'remotion';

// Editorial simulation, NOT Google's actual product interface or a live task.
const P={dark:'#081522',navy:'#0D2940',cyan:'#55E8F4',mint:'#3ADBB6',white:'#F9FCFF',soft:'#AFC7D8',gold:'#FFD08C',red:'#FF8A9A'};
const font='Inter, Segoe UI, Arial, sans-serif';
const sat=(n:number)=>Math.max(0,Math.min(1,n));
const tween=(f:number,start:number)=>sat((f-start)/19);
const card:React.CSSProperties={border:'2px solid #467B88',borderRadius:25,background:'linear-gradient(147deg,#123449 0%,#061B2C 100%)',boxShadow:'0 20px 80px #0009'};
const Label:React.FC<{children:React.ReactNode;size?:number;color?:string}>=({children,size=23,color=P.mint})=><div style={{fontSize:size,letterSpacing:1.3,fontWeight:900,color,textTransform:'uppercase'}}>{children}</div>;
const T:React.FC<{children:React.ReactNode;size?:number;color?:string;style?:React.CSSProperties}>=({children,size=36,color=P.white,style})=><div style={{fontWeight:850,fontSize:size,color,lineHeight:1.14,...style}}>{children}</div>;
const Brand:React.FC<{vertical?:boolean}>=({vertical=false})=><Label size={vertical?27:24} color={P.cyan}>FM  /  FLOWMINUTE LAB</Label>;
const Back:React.FC<{f:number;variant?:number}>=({f,variant=0})=><AbsoluteFill style={{background:'radial-gradient(circle at 70% 20%,#245C7077,transparent 55%),#071622',overflow:'hidden'}}>
 <Img src={staticFile(variant===1?'office-desks.jpg':variant===2?'office-collaboration.jpg':'office-cinematic.jpg')} style={{width:'100%',height:'100%',objectFit:'cover',opacity:variant===0?.18:.22,filter:'blur(2px) contrast(1.06) saturate(.85)',transform:'scale('+(1.055+f/29000)+') translateX('+Math.sin(f/160)*.4+'%)'}}/>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(92deg,#071523F0,#0C263BD8 60%,#071523D8)'}}/>
 <div style={{position:'absolute',width:700,height:700,top:'-20%',right:-160,borderRadius:'50%',background:'radial-gradient(circle,#22D8C91B,transparent 65%)'}}/>
 </AbsoluteFill>;
const Progress:React.FC<{f:number;total:number}>=({f,total})=><div style={{position:'absolute',bottom:0,left:0,right:0,height:8,background:'#214357'}}><div style={{height:'100%',width:100*sat(f/total)+'%',background:P.mint}}/></div>;
const Entrance:React.FC<{f:number;from:number;children:React.ReactNode;style?:React.CSSProperties}>=({f,from,children,style})=>{const a=tween(f,from);return <div style={{opacity:a,transform:'translateY('+Math.round((1-a)*34)+'px)',...style}}>{children}</div>};
type View='search'|'summary'|'shopping'|'plan'|'checks'|'limits'|'vote';
const chip=(text:string,bg='#1E4555',color=P.white)=><div style={{background:bg,color,borderRadius:12,padding:'11px 16px',fontSize:23,fontWeight:850,border:'1px solid #59838F'}}>{text}</div>;
const Browser:React.FC<{view:View;f:number;vertical?:boolean}>=({view,f,vertical=false})=>{
 const size=vertical?28:24;
 const active=Math.floor(f/42)%3;
 const step=['Choose a trusted site','Compare the results','Approve before purchase'][active];
 return <div style={{...card,height:'100%',boxSizing:'border-box',padding:vertical?'33px 31px':'31px 33px',borderRadius:vertical?38:24,color:'#182F3E',overflow:'hidden'}}>
  <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',gap:10}}>
   <div style={{display:'flex',gap:12}}>{['#FF8677','#FFD487','#46DBA7'].map(x=><div key={x} style={{height:16,width:16,borderRadius:'50%',background:x}}/>)}</div>
   <Label size={vertical?21:18} color={P.cyan}>Concept interface · not live Chrome</Label>
  </div>
  <div style={{marginTop:25,background:'#EAF4FA',borderRadius:15,padding:'18px 24px',fontSize:vertical?23:19,fontWeight:800,color:'#346170'}}>◁   ▶   ⟳    demo.example / illustrative</div>
  {view==='search'||view==='summary'?<>
   <div style={{background:'#F6FAFF',marginTop:29,borderRadius:19,padding:vertical?33:29}}>
   <T size={vertical?47:39} color="#193850">Long article: 8-minute read</T>
   <div style={{marginTop:24,borderTop:'1px solid #BDCFDA',paddingTop:28}}>
   <T size={vertical?30:26} color="#3C566C">Lots of text. You only need the takeaway.</T>
   {Array.from({length:4},(_,i)=><div key={i} style={{background:'#D9E7EE',height:16,width:(90-i*12)+'%',borderRadius:11,marginTop:25}}/>)}
   </div></div>
   <div style={{...card,marginTop:26,padding:vertical?31:26,borderColor:P.mint}}>
   <Label size={22}>Gemini in Chrome · illustrative</Label><T size={vertical?35:30}>{view==='summary'?'THREE KEY POINTS':'SUMMARIZE THIS PAGE'}</T>
   <T size={vertical?24:22} color={P.soft} style={{marginTop:18}}>Ask a question about what you're reading.</T>
   </div>
  </>:view==='shopping'?<>
   <div style={{marginTop:26}}><Label size={25}>Groceries · fictional example</Label><T size={vertical?43:42}>DINNER UNDER ₹1,200</T></div>
   <div style={{marginTop:22,background:'#EAF5F6',padding:vertical?20:23,borderRadius:18}}>
   {['Rice — ₹230','Vegetables — ₹315','Paneer — ₹330','Spices — ₹270'].map((x,i)=><div key={x} style={{display:'flex',justifyContent:'space-between',padding:'15px 8px',borderBottom:'1px solid #BFDBE0',fontSize:size,fontWeight:800,color:'#23505A'}}><span>{x}</span><span>{i===active?'◉':'✓'}</span></div>)}
   </div>
   <div style={{marginTop:22,padding:22,background:'#1D665C',borderRadius:15}}><T size={vertical?52:40}>₹1,145 <span style={{fontSize:24,color:'#CBF7E8'}}>planned cart</span></T></div>
   <T size={vertical?24:22} color={P.soft} style={{marginTop:20}}>Not a real order. Prices are invented.</T>
  </>:view==='plan'?<>
   <div style={{marginTop:30}}><Label>BEFORE YOU START</Label><T size={vertical?45:43}>REVIEW THE PLAN</T></div>
   {['Which websites will open?','What information is shared?','Who approves the purchase?'].map((x,i)=><div key={x} style={{marginTop:26,borderRadius:15,border:'1px solid #4A8695',padding:'23px 18px',background:i===active?'#29606D':'#14384C',display:'flex',justifyContent:'space-between',alignItems:'center'}}><T size={vertical?27:24}>{x}</T><T size={30} color={i===active?P.gold:P.mint}>{i===active?'!':'✓'}</T></div>)}
   <div style={{marginTop:40,display:'flex',gap:18,justifyContent:'flex-end'}}>{chip('TAKE OVER','#36536C')}{chip('START TASK?','#185D64',P.gold)}</div>
  </>:view==='checks'?<>
   <div style={{marginTop:30}}><T size={vertical?53:45}>3-SECOND CHECKLIST</T></div>
   {['1 / SITES','2 / SHARED DATA','3 / APPROVAL'].map((x,i)=><div key={x} style={{padding:'25px 28px',background:i===active?'#145A5C':'#17384E',border:'1px solid #447D88',borderRadius:17,marginTop:28}}><T size={vertical?36:30} color={i===active?P.mint:P.white}>{x}</T></div>)}
   <T size={vertical?26:23} color={P.soft} style={{marginTop:39}}>The plan is not a receipt. Review every sensitive action.</T>
  </>:view==='limits'?<>
   <div style={{marginTop:31}}><Label>WHO CAN USE WHAT?</Label></div>
   <div style={{...card,marginTop:18,padding:vertical?34:28,borderColor:P.cyan}}><Label>ANDROID IN INDIA</Label><T size={vertical?40:36}>Gemini in Chrome</T><T size={vertical?29:25} color={P.soft} style={{marginTop:10}}>Page summaries · Q&A · gradual rollout</T></div>
   <div style={{...card,marginTop:25,padding:vertical?34:28,borderColor:P.gold}}><Label color={P.gold}>GOOGLE AI PRO / ULTRA</Label><T size={vertical?40:36}>Auto browse</T><T size={vertical?29:25} color={P.soft} style={{marginTop:10}}>Multi-step web tasks · eligibility applies</T></div>
   <T size={vertical?24:22} color={P.soft} style={{marginTop:26}}>English settings and supported devices required.</T>
  </>:<>
   <div style={{marginTop:44,textAlign:'center'}}><T size={vertical?54:62}>WHICH ONE?</T><div style={{display:'flex',gap:20,marginTop:48}}><div style={{...card,flex:1,padding:vertical?26:40,borderColor:P.cyan}}><T size={vertical?39:42}>FORM</T></div><div style={{...card,flex:1,padding:vertical?26:40,borderColor:P.gold}}><T size={vertical?39:42}>CART</T></div></div><T size={vertical?35:35} color={P.mint} style={{marginTop:45}}>COMMENT YOUR PICK ↓</T></div>
  </>}
 </div>;
};
type Beat={start:number;end:number;view:View;kicker:string;title:string;sub:string;take:string;photo?:number};
const long:Beat[]=[
 {start:0,end:21,view:'shopping',kicker:'THE SHOPPING TEST · ILLUSTRATIVE',title:'CAN CHROME SHOP FOR YOU?',sub:'Your browser can attempt multi-step tasks. But look at the plan first.',take:'A plan is NOT a completed purchase.',photo:1},
 {start:21,end:38,view:'limits',kicker:'GOOGLE · INDIA ROLLOUT · OCT 7',title:'FREE HELP OR PAID AUTO BROWSE?',sub:'Understanding a page is different from acting on the web.',take:'Availability depends on plan, device and rollout.',photo:0},
 {start:38,end:49,view:'summary',kicker:'USE CASE 01 · UNDERSTAND',title:'A LONG ARTICLE → THREE POINTS',sub:'Summarize a page or ask what it means.',take:'Illustrative page, not a captured product demo.',photo:2},
 {start:49,end:72,view:'limits',kicker:'AUTO BROWSE · THE PAID PART',title:'MULTI-STEP TASKS NEED A PLAN',sub:'Google AI Pro or Ultra in India, subject to eligibility.',take:'Paid access does not guarantee immediate rollout.',photo:0},
 {start:72,end:95,view:'shopping',kicker:'USE CASE 02 · ACT',title:'GROCERIES UNDER ₹1,200?',sub:'Fictional task: find ingredients, compare the budget, prepare a cart.',take:'The cart, amounts and sites are illustrative.',photo:1},
 {start:95,end:133,view:'plan',kicker:'WHERE TRUST MATTERS',title:'REVIEW THE PLAN FIRST',sub:'A browser can use real sites and share details.',take:'Never approve a purchase you have not verified.',photo:0},
 {start:133,end:156,view:'checks',kicker:'THREE SECURITY CHECKS',title:'SITES · DATA · APPROVAL',sub:'Know where it goes, what it shares, and when it asks you.',take:'Take over if the plan is not what you intended.',photo:2},
 {start:156,end:183,view:'limits',kicker:'THE ACCESS CATCH',title:'IT MAY NOT SHOW UP TODAY',sub:'English + eligibility + current Chrome + sign-in.',take:'AI Pro or Ultra for auto browse. Gradual rollout.',photo:0},
 {start:183,end:211,view:'vote',kicker:'THE VERDICT · YOU DECIDE',title:'FORM OR CART?',sub:'Which task would you let an AI browser prepare?',take:'Follow FlowMinute for useful AI workflows, without the hype.',photo:1},
];
type ShortBeat={start:number;end:number;view:View;head:string;sub:string;accent:string};
const short19:ShortBeat[]=[
 {start:0,end:6,view:'limits',head:'CHROME AI IN INDIA: FREE?',sub:'Here is what costs money.',accent:'GOOGLE · OCT 2026'},
 {start:6,end:19,view:'summary',head:'ASK ABOUT A WEB PAGE',sub:'Summaries and questions in Chrome.',accent:'ANDROID ROLLOUT · ACCESS VARIES'},
 {start:19,end:31,view:'limits',head:'AUTO BROWSE? PAID.',sub:'AI Pro / Ultra · multi-step web tasks.',accent:'ELIGIBILITY MATTERS'},
 {start:31,end:42,view:'limits',head:'WHICH WOULD YOU USE?',sub:'COMMENT 1: SUMMARIZE · 2: AUTO BROWSE',accent:'MORE DETAIL IN THE LONG VIDEO'}
];
const short20:ShortBeat[]=[
 {start:0,end:7,view:'shopping',head:'AI ORDERING GROCERIES?',sub:'WAIT before pressing Start.',accent:'ILLUSTRATIVE SCENARIO'},
 {start:7,end:17,view:'plan',head:'FIRST: REVIEW THE PLAN',sub:'Which sites and details will it use?',accent:'REAL WEBSITES · REAL DATA'},
 {start:17,end:28,view:'checks',head:'THREE CHECKS. ALWAYS.',sub:'SITES. SHARED DATA. APPROVAL.',accent:'VERIFY BEFORE ACTION'},
 {start:28,end:37,view:'vote',head:'FORM OR CART?',sub:'WHICH TASK WOULD YOU TRUST?',accent:'COMMENT YOUR CHOICE'}
];
const MobileShort:React.FC<{kind:19|20}>=({kind})=>{
 const f=useCurrentFrame(),sec=f/30,items=kind===19?short19:short20,stage=items.find(x=>sec>=x.start&&sec<x.end)||items[items.length-1],start=stage.start*30;
 return <AbsoluteFill style={{fontFamily:font,color:P.white,background:P.dark}}>
 <Back f={f} variant={kind===19?2:1}/><div style={{position:'absolute',top:88,left:72}}><Brand vertical/></div>
 <Entrance f={f} from={start} style={{position:'absolute',top:216,left:72,right:72}}>
 <Label size={24}>{stage.accent}</Label><T size={78} style={{letterSpacing:-2,lineHeight:1.05,marginTop:19}}>{stage.head}</T><T size={34} color={P.soft} style={{marginTop:28}}>{stage.sub}</T>
 </Entrance>
 <Entrance f={f} from={start+5} style={{position:'absolute',top:688,left:68,right:68,height:675}}>{sec<5?<div style={{...card,position:'relative',height:'100%',overflow:'hidden'}}><OffthreadVideo muted src={staticFile('oct14-hands-phone-stock.mp4')} style={{width:'100%',height:'100%',objectFit:'cover'}}/><div style={{position:'absolute',bottom:20,left:26,padding:'12px 17px',background:'#071C2ACC'}}><Label size={20} color={P.cyan}>REAL LIFE STOCK FOOTAGE · NOT CHROME DEMO</Label></div></div>:<Browser view={stage.view} f={f} vertical/>}</Entrance>
 <div style={{position:'absolute',left:75,right:75,top:1450,borderLeft:'7px solid '+P.mint,padding:'20px 26px',background:'#06253CD9'}}><T size={30} color={P.cyan}>{kind===19?'SUMMARIZE = DIFFERENT FROM AUTO BROWSE':'THE PLAN IS NOT A PURCHASE RECEIPT'}</T></div>
 <Label size={18} color={P.soft}><span style={{position:'absolute',bottom:100,left:75,right:75}}>Original illustrations · NOT live Google footage</span></Label>
 <Progress f={f} total={kind===19?1260:1110}/>
 <Audio src={staticFile(kind===19?'voice-v19.mp3':'voice-v20.mp3')}/>
 </AbsoluteFill>;
};
export const ChromeIndiaShort:React.FC=()=> <MobileShort kind={19}/>;
export const BrowserSafetyShort:React.FC=()=> <MobileShort kind={20}/>;
export const ChromeAutoBrowseLong:React.FC=()=>{
 const f=useCurrentFrame(),sec=f/24,stage=long.find(x=>sec>=x.start&&sec<x.end)||long[long.length-1],start=stage.start*24;
 return <AbsoluteFill style={{fontFamily:font,color:P.white,background:P.dark}}>
 <Back f={f} variant={stage.photo}/><div style={{position:'absolute',top:47,left:91,right:91,display:'flex',justifyContent:'space-between'}}><Brand/><Label size={23} color={P.gold}>CHROME AUTO BROWSE · INDIA</Label></div>
 <Entrance f={f} from={start} style={{position:'absolute',top:198,left:91,width:790}}>
 <Label size={23}>{stage.kicker}</Label><T size={76} style={{letterSpacing:-2.1,marginTop:21}}>{stage.title}</T>
 <T size={32} color={P.soft} style={{marginTop:30}}>{stage.sub}</T>
 <div style={{marginTop:52,padding:'24px 27px',borderLeft:'7px solid '+P.gold,background:'#10364ABB'}}><T size={28}>{stage.take}</T></div>
 </Entrance>
 <Entrance f={f} from={start+6} style={{position:'absolute',top:185,left:950,right:78,height:740,transform:'perspective(1700px) rotateY(-1deg)'}}>{sec<8?<div style={{...card,position:'relative',height:'100%',overflow:'hidden'}}><OffthreadVideo muted src={staticFile('oct14-payment-stock.mp4')} style={{width:'100%',height:'100%',objectFit:'cover'}}/><div style={{position:'absolute',bottom:18,left:25,padding:'12px 18px',background:'#051824DD'}}><Label size={21}>REAL LIFE STOCK FOOTAGE · NOT AN AI CHECKOUT</Label></div></div>:<Browser view={stage.view} f={f}/>}</Entrance>
 <div style={{position:'absolute',bottom:60,left:95,right:95,display:'flex',justifyContent:'space-between',alignItems:'center'}}><Label size={19} color={P.soft}>ILLUSTRATIVE UI · NOT A REAL SHOPPING DEMO</Label><Label size={19} color={P.cyan}>SOURCE: GOOGLE INDIA · OCT 7, 2026</Label></div>
 <Progress f={f} total={211*24}/><Audio src={staticFile('voice-long009.mp3')}/>
 </AbsoluteFill>;
};
export const ChromeBrowseThumbnail:React.FC=()=> <AbsoluteFill style={{fontFamily:font,background:P.dark,color:P.white}}><Back f={0} variant={1}/>
 <div style={{position:'absolute',top:88,left:104}}><Brand/></div>
 <div style={{position:'absolute',top:250,left:109,width:1030}}><T size={148} style={{letterSpacing:-6}}>AI SHOPS</T><T size={146} color={P.gold} style={{letterSpacing:-5}}>FOR YOU?</T><T size={44} color={P.cyan} style={{marginTop:35}}>CHROME AUTO BROWSE · INDIA</T></div>
 <div style={{position:'absolute',left:1090,right:100,top:177,height:740,transform:'perspective(1400px) rotateY(-7deg) rotate(-2deg)'}}><Browser view="plan" f={100}/></div>
 <div style={{position:'absolute',left:110,bottom:95,background:'#D85C39',borderRadius:16,padding:'18px 30px'}}><T size={39}>FREE OR PAID?</T></div>
 </AbsoluteFill>;
