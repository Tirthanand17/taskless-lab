import assert from "node:assert/strict";
import test from "node:test";
import worker from "./phase5e_cloudflare_d1_readonly_inventory.mjs";
const ADMIN="Z".repeat(48);
const URL="https://candidate.invalid/v1/d1/schema-inventory";
const NAMES=["fm_release_writer_lease","fm_writer_release_shadow","fm_releases_shadow","fm_releases","releases","release_events","audit_heartbeats","youtube_release_observations"];
const BRAND="fm_oauth_channel_proofs";
const SQL="SELECT name, type FROM sqlite_master WHERE type='table' AND name IN ('fm_release_writer_lease','fm_writer_release_shadow','fm_releases_shadow','fm_releases','releases','release_events','audit_heartbeats','youtube_release_observations','fm_oauth_channel_proofs') ORDER BY name LIMIT 10";
const PRAGMAS=Object.fromEntries(NAMES.map(x=>[x,'PRAGMA table_info("'+x+'")']));
function harness({rows=[{name:NAMES[0],type:"table"},{name:BRAND,type:"table"}], columns=null, overrides={}}={}){
 const queries=[];
 const db={prepare(sql){
  queries.push(sql);
  if(sql===SQL)return {all:async()=>({success:true,results:rows})};
  if(sql==='PRAGMA index_list("releases")')
   return {all:async()=>({success:true,results:[
     {name:"idx_release_state",unique:0,partial:0},
     {name:"idx_release_date_slot",unique:0,partial:0},
     {name:"sqlite_autoindex_releases_2",unique:1,partial:0},
     {name:"sqlite_autoindex_releases_1",unique:1,partial:0}
   ]})};
  if(sql==='PRAGMA index_info("sqlite_autoindex_releases_2")')
   return {all:async()=>({success:true,results:[{seqno:0,cid:7,name:"youtube_id"}]})};
  if(Object.values(PRAGMAS).includes(sql))
   return {all:async()=>({success:true,results:columns??[
    {name:"singleton",pk:1},{name:"owner_nonce",pk:0},
    {name:"fence_epoch",pk:0},{name:"expires_at_unix",pk:0}
   ]})};
  throw Error("UNAUTHORIZED_SQL");
 }};
 const environment={
  FM_D1_READONLY_INSPECT_ENABLED:"1",FM_UPLOADS_ENABLED:"0",FM_SCHEDULING_ENABLED:"0",
  FM_D1_WRITES_ENABLED:"0",FM_OWNER_READONLY_INSPECTION_APPROVED:"1",
  FM_HARD_ZERO_OVERAGE_VERIFIED:"1",FM_D1_ADMIN_KEY:ADMIN,
  FM_D1_RATE_LIMITER:{async limit({key}){assert.equal(key,"flowminute:d1:read-only-inventory");return {success:true};}},
  DB:db,...overrides
 };
 return {queries,env:environment};
}
async function call(env, {url=URL,auth="Bearer "+ADMIN,method="POST",body=""}={}){
 const request=new Request(url,{method,headers:{
  authorization:auth,"content-length":String(body.length)},body:method==="POST"?body:undefined});
 return worker.fetch(request,env);
}
test("static health never reads database",async()=>{
 const h=harness();
 const r=await call(h.env,{url:"https://candidate.invalid/health",method:"GET"});
 assert.equal(r.status,200);assert.equal((await r.json()).deployed_verified,false);
 assert.equal(h.queries.length,0);
});
test("read-only snapshot contains safe whitelist only; no data rows",async()=>{
 const h=harness();
 const r=await call(h.env);
 assert.equal(r.status,200);
 const body=await r.json();
 assert.equal(body.state,"READ_ONLY_D1_SCHEMA_SNAPSHOT_UNATTESTED");
 assert.equal(body.found_candidate_count,1);
 assert.equal(body.historically_known_brand_proof_table_present,true);
 assert.deepEqual(body.observed_candidate_tables[0].visible_columns.map(c=>c.name),
  ["expires_at_unix","fence_epoch","singleton"]);
 assert.equal(body.observed_candidate_tables[0].protected_column_count,1);
 assert.equal(body.data_rows_read,0);assert.equal(body.oauth_ciphertext_or_secrets_read,false);
 assert.equal(body.cloud_autopilot_ready,false);assert.equal(body.production_d1_writes,0);
 assert.deepEqual(h.queries,[SQL,PRAGMAS[NAMES[0]]]);
});
test("rate limit missing or exhausted blocks before D1",async()=>{
 for(const item of [null,{async limit(){return {success:false};}}]){
  const h=harness({overrides:{FM_D1_RATE_LIMITER:item}});
  const r=await call(h.env);
  assert.equal(r.status,item===null?403:429);
  assert.equal(h.queries.length,0);
 }
});
test("flags forbid access to D1 even with matching admin key",async()=>{
 const variants=[
  {FM_D1_READONLY_INSPECT_ENABLED:"0"},
  {FM_UPLOADS_ENABLED:"1"},
  {FM_SCHEDULING_ENABLED:"1"},
  {FM_D1_WRITES_ENABLED:"1"},
  {FM_OWNER_READONLY_INSPECTION_APPROVED:"0"},
  {FM_HARD_ZERO_OVERAGE_VERIFIED:"0"}
 ];
 for(const override of variants){
  const h=harness({overrides:override});
  assert.equal((await call(h.env)).status,403);assert.equal(h.queries.length,0);
 }
});
test("invalid admin key blocked with no D1 read",async()=>{
 const h=harness();
 for(const key of ["Bearer "+ "X".repeat(48),"Bearer short","missing"]){
  assert.equal((await call(h.env,{auth:key})).status,401);
 }
 assert.equal(h.queries.length,0);
});
test("rejects all requests containing body, query, wrong path or method",async()=>{
 const h=harness();
 for(const opt of [{body:"{}"},{url:URL+"?token=secret"},
   {url:"https://candidate.invalid/v1/d1/migrate"},
   {method:"GET"}]){
  const r=await call(h.env,opt);
  assert.equal(r.status,404);
 }
 assert.equal(h.queries.length,0);
});
test("never expose D1 exception message or secret-bearing columns",async()=>{
 const h=harness({columns:[{name:"oauth_refresh_token",pk:0},
  {name:"ciphertext",pk:0},{name:"episode_id",pk:1}]});
 const r=await call(h.env);assert.equal(r.status,200);
 const body=await r.text();
 assert.ok(!body.includes("oauth_refresh_token"));assert.ok(!body.includes("ciphertext"));
 assert.ok(body.includes("episode_id"));
});
test("synthetic D1 failure redacted and no write",async()=>{
 const h=harness({overrides:{DB:{prepare(){throw Error("REFRESH_TOKEN=secret");}}}});
 const r=await call(h.env);assert.equal(r.status,503);
 assert.ok(!(await r.text()).includes("REFRESH_TOKEN"));
});
test("reject malformed catalog including duplicate or invented table names",async()=>{
 for(const rows of [
  [{name:NAMES[0],type:"table"},{name:NAMES[0],type:"table"}],
  [{name:"oauth_access_token",type:"table"}],
  [{name:NAMES[0],type:"view"}]
 ]){
  const h=harness({rows});
  assert.equal((await call(h.env)).status,503);
 }
});
test("reject malformed column names and catalog size",async()=>{
 for(const columns of [
  [{name:"x; DROP TABLE",pk:0}],
  [{name:"dup",pk:0},{name:"dup",pk:1}]
 ]){
  const h=harness({columns});
  assert.equal((await call(h.env)).status,503);
 }
 const h=harness({rows:Array.from({length:7},(_,i)=>({name:"table_"+i,type:"table"}))});
 assert.equal((await call(h.env)).status,503);
});
test("never claims uniqueness, hard budget proof or migrations from metadata",async()=>{
 const h=harness();
 const body=await (await call(h.env)).json();
 for(const field of ["uniqueness_constraints_verified","global_zero_cost_cap_verified",
 "current_cloudflare_admin_provenance_verified","migration_approved","cloud_autopilot_ready"]){
  assert.equal(body[field],false);
 }
 assert.equal(body.youtube_uploads,0);assert.equal(body.youtube_schedules,0);
});
test("no-cache response and no CORS grant",async()=>{
 const h=harness();const r=await call(h.env);
 assert.equal(r.headers.get("cache-control"),"no-store, max-age=0");
 assert.equal(r.headers.get("access-control-allow-origin"),null);
});

test("real-world canonical releases and event table names are accepted and uniqueness is index-backed",async()=>{
 const rows=[{name:"releases",type:"table"},{name:"release_events",type:"table"},
   {name:BRAND,type:"table"}];
 const h=harness({rows,columns:[{name:"release_date",pk:1},
  {name:"episode_id",pk:2},{name:"youtube_id",pk:0}]});
 const response=await call(h.env);
 assert.equal(response.status,200);
 const result=await response.json();
 assert.equal(result.existing_canonical_release_tables_detected,true);
 assert.equal(result.observed_youtube_id_unique_index,true);
 assert.equal(result.release_slot_uniqueness_verified,false);
 assert.equal(result.production_d1_writes,0);
 assert.equal(result.cloud_autopilot_ready,false);
 assert.ok(h.queries.some(x=>x==='PRAGMA index_list("releases")'));
 assert.ok(h.queries.some(x=>x==='PRAGMA index_info("sqlite_autoindex_releases_2")'));
});
