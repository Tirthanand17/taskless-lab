import assert from "node:assert/strict";
import test from "node:test";
import worker from "./phase5d_cloudflare_owner_readback.mjs";

const CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA";
const API="https://www.googleapis.com/youtube/v3/";
const ADMIN="A".repeat(40);
const TOKEN="stub-only-readonly-token-never-record";
const future=(mins)=>new Date(Date.now()+mins*60000).toISOString().slice(0,19)+"Z";
const day=()=>new Date(Date.now()+3*86400000).toISOString().slice(0,10);
const planned=()=>({
  date:day(),
  slots:{
    short_morning:{video_id:"abcdefghijk",title:"safe english tutorial"},
    long:{video_id:null,title:"Hindi tutorial pending"},
    short_evening:{video_id:"LMNOPQRSTUV",title:"safe hindi tutorial"}
  }
});
const env=(overrides={})=>({
  FM_OWNER_READBACK_ENABLED:"1",FM_UPLOADS_ENABLED:"0",FM_SCHEDULING_ENABLED:"0",
  FM_HARD_ZERO_OVERAGE_VERIFIED:"1",FM_EXPECTED_CHANNEL_ID:CHANNEL,
  FM_YOUTUBE_ACCESS_TOKEN:TOKEN,FM_YOUTUBE_ACCESS_EXPIRES_AT:future(60),
  FM_ADMIN_READBACK_KEY:ADMIN,
  FM_READBACK_RATE_LIMITER:{async limit({key}){assert.equal(key,"flowminute:owner-readback");return {success:true};}},
  ...overrides
});
const expected=(date,slot)=>{
  const time=slot==="short_morning"?"11:00":slot==="long"?"16:00":"20:30";
  return new Date(date+"T"+time+":00+05:30").toISOString().replace(".000Z","Z");
};
const makeRequest=(body=planned(),auth="Bearer "+ADMIN,method="POST",path="/v1/owner-readback")=>
 new Request("https://candidate.invalid"+path,{
   method,headers:{Authorization:auth,"content-type":"application/json"},
   ...(method==="POST"?{body:JSON.stringify(body)}:{})
 });
const run=({body=planned(),runtime=env(),auth="Bearer "+ADMIN,
           method="POST",path="/v1/owner-readback"}={})=>
  worker.fetch(makeRequest(body,auth,method,path),runtime);
const fakeGoogle=(rewrite=(_url,obj)=>obj)=>{
  const orig=globalThis.fetch;
  const calls=[];
  globalThis.fetch=async(uri,options)=>{
    const address=String(uri);
    calls.push({address,options});
    assert.ok(address.startsWith(API));
    assert.equal(options.method,"GET");
    assert.equal(options.redirect,"error");
    assert.equal(options.headers.Authorization,"Bearer "+TOKEN);
    let obj;
    if(address.includes("/channels?")){
      obj={items:[{id:CHANNEL}]};
    }else{
      const id=new URL(address).searchParams.get("id");
      const slot=id==="abcdefghijk"?"short_morning":"short_evening";
      obj={items:[{id,snippet:{channelId:CHANNEL,
                 title:slot==="short_morning"?"safe english tutorial":"safe hindi tutorial"},
        status:{privacyStatus:"private",uploadStatus:"processed",
                publishAt:expected(day(),slot)},
        processingDetails:{processingStatus:"succeeded"}}]};
    }
    return new Response(JSON.stringify(rewrite(address,obj)),{status:200,
      headers:{"content-type":"application/json"}});
  };
  return {calls,restore(){globalThis.fetch=orig;}};
};

test("disabled gate never touches Google",async()=>{
 const m=fakeGoogle();
 try{
  const r=await run({runtime:env({FM_OWNER_READBACK_ENABLED:"0"})});
  assert.equal(r.status,403);assert.equal(m.calls.length,0);
 }finally{m.restore();}
});
test("upload, scheduling, hard budget and wrong channel toggles prohibit probe",async()=>{
 const m=fakeGoogle();
 try{
  for(const x of [
   {FM_UPLOADS_ENABLED:"1"},{FM_SCHEDULING_ENABLED:"1"},
   {FM_HARD_ZERO_OVERAGE_VERIFIED:"0"},{FM_EXPECTED_CHANNEL_ID:"UCwrong"}]){
    assert.equal((await run({runtime:env(x)})).status,403);
  }
  assert.equal(m.calls.length,0);
 }finally{m.restore();}
});
test("real Worker runtime shape returns two safe scheduled slots without identifiers",async()=>{
 const m=fakeGoogle();
 try{
  const response=await run();assert.equal(response.status,200);
  const body=await response.json();
  assert.equal(body.verified_platform_state_count,2);
  assert.deepEqual(body.lanes.map(x=>x.status),[
    "SCHEDULED_VERIFIED","MISSING_VIDEO","SCHEDULED_VERIFIED"]);
  assert.equal(body.cloud_autopilot_ready,false);
  assert.equal(body.uploads_attempted,0);
  assert.equal(m.calls.length,3);
  const serialized=JSON.stringify(body);
  for(const item of [ADMIN,TOKEN,"abcdefghijk","LMNOPQRSTUV","safe english tutorial"]){
    assert.ok(!serialized.includes(item));
  }
 }finally{m.restore();}
});
test("invalid admin authentication never reaches Google",async()=>{
 const m=fakeGoogle();
 try{
  for(const auth of ["Bearer "+"Z".repeat(40),"foo","Bearer "+"short"]){
    assert.equal((await run({auth})).status,401);
  }
  assert.equal(m.calls.length,0);
 }finally{m.restore();}
});
test("expires early or implausibly late prevents readback",async()=>{
 const m=fakeGoogle();
 try{
  for(const expires of [future(4),future(19),future(130),
    "2026-10-19T12:20:00+05:30"]){
    assert.equal((await run({runtime:env({FM_YOUTUBE_ACCESS_EXPIRES_AT:expires})})).status,403);
  }
  assert.equal(m.calls.length,0);
 }finally{m.restore();}
});
test("duplicate video id, invalid release day and unsafe manifest fields are denied",async()=>{
 const m=fakeGoogle();
 try{
  const a=planned();a.slots.long.video_id=a.slots.short_morning.video_id;
  const b=planned();b.date="2026-02-30";
  const c=planned();c.refresh_token=TOKEN;
  const d=planned();d.slots.short_morning.title="";
  const e=planned();e.slots.long.video_id="../path";
  for(const body of [a,b,c,d,e])assert.equal((await run({body})).status,400);
  assert.equal(m.calls.length,0);
 }finally{m.restore();}
});
test("wrong channel identity halts all video queries",async()=>{
 const m=fakeGoogle((url,body)=>url.includes("/channels?")
   ?{items:[{id:"UCother"}]}:body);
 try{
  assert.equal((await run()).status,403);
  assert.equal(m.calls.length,1);
 }finally{m.restore();}
});
test("missing video record, wrong title or unfinished processing always hold",async()=>{
 const m=fakeGoogle((url,body)=>{
  if(url.includes("/videos?")){
    body.items[0].snippet.title="wrong";
    body.items[0].processingDetails.processingStatus="processing";
  }
  return body;
 });
 try{
  const p=await (await run()).json();
  assert.equal(p.verified_platform_state_count,0);
  assert.equal(p.lanes[0].status,"HOLD_UNVERIFIED");
 }finally{m.restore();}
});
test("token-bearing provider exception never appears in response",async()=>{
 const previous=globalThis.fetch;
 globalThis.fetch=async()=>{throw Error("BURN "+TOKEN);};
 try{
  const response=await run();
  assert.equal(response.status,400);
  assert.ok(!(await response.text()).includes(TOKEN));
 }finally{globalThis.fetch=previous;}
});
test("routes fail closed: no upload endpoint, query tokens or cached CORS",async()=>{
 const m=fakeGoogle();
 try{
  const health=await run({method:"GET",path:"/health"});
  assert.equal(health.status,200);
  assert.equal((await health.json()).source_status,"NOT_DEPLOYED_UNATTESTED_READONLY_SOURCE");
  assert.equal((await run({path:"/upload"})).status,404);
  assert.equal((await run({path:"/v1/owner-readback?token=secret"})).status,404);
  assert.equal((await run({method:"GET"})).status,404);
  assert.equal(m.calls.length,0);
  const response=await run();
  assert.equal(response.headers.get("cache-control"),"no-store, max-age=0");
  assert.equal(response.headers.get("access-control-allow-origin"),null);
 }finally{m.restore();}
});
test("future release marked public is NOT a verified scheduled release",async()=>{
 const m=fakeGoogle((u,o)=>{
  if(u.includes("/videos?"))o.items[0].status.privacyStatus="public";
  return o;
 });
 try{
  const result=await (await run()).json();
  assert.equal(result.verified_platform_state_count,0);
  assert.equal(result.anonymous_playability_verified,false);
 }finally{m.restore();}
});

test("fail-closed absent or denied rate limiter before Google read",async()=>{
 const m=fakeGoogle();
 try{
  for(const limiter of [null,{async limit(){return {success:false};}}]){
   const r=await run({runtime:env({FM_READBACK_RATE_LIMITER:limiter})});
   assert.equal(r.status,limiter===null?403:429);
  }
  assert.equal(m.calls.length,0);
 }finally{m.restore();}
});
