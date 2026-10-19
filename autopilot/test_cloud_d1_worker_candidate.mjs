import test from "node:test";
import assert from "node:assert/strict";
import {
  LIVE_CLOUDFLARE_WRITES_ENABLED,D1_CAS_SQL,
  inspectD1WriteResult,exerciseSyntheticD1PreparedCAS
} from "./cloud_d1_worker_candidate.mjs";

const NONCE="A".repeat(32);
const SHA="a".repeat(64);
const CLAIM={nonce:NONCE,epoch:3,ttlSeconds:60};
const RESERVE={
  releaseDate:"2026-10-20",
  episodeId:"tutorial_short_en",
  mediaSha256:SHA,nonce:NONCE,epoch:4
};

function fakeD1(reply,exception=null) {
  const observed=[];
  const adapter={
    __flowminuteSyntheticD1:true,
    prepare(sql) {
      observed.push({kind:"sql",value:sql});
      return {
        bind(...params) {
          observed.push({kind:"params",value:params});
          return {
            async run() {
              observed.push({kind:"run"});
              if(exception!==null) throw new Error(exception);
              return reply;
            }
          };
        }
      };
    }
  };
  return {adapter,observed};
}

function receipt(opts={}) {
  return {
    success:true,
    meta:{
      served_by_primary:true,changed_db:true,
      changes:1,rows_written:1,total_attempts:1,...opts
    },
    results:[]
  };
}

test("module never enables live D1 writes or publishes",()=>{
  assert.equal(LIVE_CLOUDFLARE_WRITES_ENABLED,false);
  assert.deepEqual(Object.keys(D1_CAS_SQL).sort(),["claim","renew","reserve"]);
  assert.equal(typeof globalThis.fetch,"function"); // no host call made
});

test("claim calls precisely one parameterized prepared UPDATE",async()=>{
  const {adapter,observed}=fakeD1(receipt());
  const result=await exerciseSyntheticD1PreparedCAS(adapter,"claim",CLAIM);
  assert.equal(result.decision,"SHADOW_CAS_ONLY");
  assert.equal(result.synthetic_prepared_statement_accepted,true);
  assert.equal(result.real_cloud_d1_written,false);
  assert.equal(result.upload_retry_authorized,false);
  assert.equal(result.youtube_upload_authorized,false);
  assert.equal(result.scheduling_or_publishing_authorized,false);
  assert.equal(result.external_network_requests,0);
  assert.equal(result.live_d1_writes,0);
  assert.deepEqual(observed.map(x=>x.kind),["sql","params","run"]);
  assert.equal(observed[0].value,D1_CAS_SQL.claim);
  assert.deepEqual(observed[1].value,[NONCE,60,3]);
  assert.ok(!String(result).includes(NONCE));
  assert.ok(!JSON.stringify(result).includes(NONCE));
});

test("renew order is fixed, and never accepts client timestamps",async()=>{
  const {adapter,observed}=fakeD1(receipt());
  const outcome=await exerciseSyntheticD1PreparedCAS(adapter,"renew",{
    nonce:NONCE,epoch:4,ttlSeconds:15
  });
  assert.equal(outcome.synthetic_prepared_statement_accepted,true);
  assert.deepEqual(observed[1].value,[15,NONCE,4]);
  const invalid=await exerciseSyntheticD1PreparedCAS(adapter,"renew",{
    nonce:NONCE,epoch:4,ttlSeconds:15,nowTick:500
  });
  assert.equal(invalid.decision,"HOLD");
  assert.equal(observed.length,3);
});

test("fenced upload reservation requires exact media hash and epoch",async()=>{
  const {adapter,observed}=fakeD1(receipt());
  const outcome=await exerciseSyntheticD1PreparedCAS(adapter,"reserve",RESERVE);
  assert.equal(outcome.synthetic_prepared_statement_accepted,true);
  assert.deepEqual(observed[1].value,[
    RESERVE.releaseDate,RESERVE.episodeId,SHA,NONCE,4
  ]);
  assert.ok(D1_CAS_SQL.reserve.includes("stage='media_qa_passed'"));
  assert.ok(D1_CAS_SQL.reserve.includes("stage='upload_started'"));
  assert.ok(D1_CAS_SQL.reserve.includes("fence_epoch=?"));
});

test("missing fake gate, even on D1-like object, executes nothing",async()=>{
  let executions=0;
  const liveLookalike={
    prepare(){executions++;throw new Error("must not run");}
  };
  const out=await exerciseSyntheticD1PreparedCAS(liveLookalike,"claim",CLAIM);
  assert.equal(out.decision,"HOLD");
  assert.equal(out.reason_code,"REAL_D1_BINDING_OR_DISABLED_GATE_DENIED");
  assert.equal(executions,0);
});

test("zero changed rows, unknown acknowledgement, or multiple writes HOLD",async()=>{
  for(const values of [
    {changes:0,rows_written:0,changed_db:false},
    {changes:2,rows_written:2},
    {changes:1,rows_written:0},
    {changes:0,rows_written:1},
    {served_by_primary:false},
    {served_by_primary:null},
    {changed_db:false},
    {total_attempts:2}
  ]) {
    const {adapter}=fakeD1(receipt(values));
    const outcome=await exerciseSyntheticD1PreparedCAS(adapter,"claim",CLAIM);
    assert.equal(outcome.decision,"HOLD");
    assert.equal(outcome.synthetic_prepared_statement_accepted,false);
  }
});

test("malformed, missing, forged metadata or results array denied",()=>{
  for(const result of [
    {},null,false,{success:true,meta:{}},
    {success:false,meta:receipt().meta,results:[]},
    {...receipt(),results:[{videoId:"leak"}]},
    {...receipt(),meta:{...receipt().meta,rows_written:"1"}},
    {...receipt(),meta:{...receipt().meta,total_attempts:0}},
    {...receipt(),meta:{...receipt().meta,changes:true}},
  ]) {
    assert.equal(inspectD1WriteResult(result),false);
  }
});

test("invalid nonce, invalid epoch, ttl, SHA, dates and extra keys never prepare",async()=>{
  const candidates=[
    ["claim",{...CLAIM,nonce:"invalid"}],
    ["claim",{...CLAIM,epoch:1.5}],
    ["claim",{...CLAIM,epoch:-1}],
    ["claim",{...CLAIM,ttlSeconds:301}],
    ["claim",{...CLAIM,ttlSeconds:0}],
    ["claim",{...CLAIM,ttlSeconds:"30"}],
    ["claim",{...CLAIM,cloudToken:"SHOULD_NOT_LEAK"}],
    ["reserve",{...RESERVE,mediaSha256:"b".repeat(63)}],
    ["reserve",{...RESERVE,releaseDate:"2026-02-30"}],
    ["reserve",{...RESERVE,episodeId:"../bad"}],
    ["reserve",{...RESERVE,epoch:0}],
    ["renew",{nonce:NONCE,epoch:0,ttlSeconds:1}],
    ["extra",CLAIM]
  ];
  let called=0;
  const fake={
    __flowminuteSyntheticD1:true,
    prepare() {called++;throw new Error("unexpected");}
  };
  for(const [operation,params] of candidates){
    const result=await exerciseSyntheticD1PreparedCAS(fake,operation,params);
    assert.equal(result.decision,"HOLD");
    assert.equal(result.reason_code,"INVALID_CAS_OPERATION_OR_BINDINGS");
  }
  assert.equal(called,0);
});

test("provider error including quota details is redacted and not retried",async()=>{
  const secret="PRIVATE_DB_KEY_DO_NOT_ECHO";
  const {adapter,observed}=fakeD1(null,secret);
  const out=await exerciseSyntheticD1PreparedCAS(adapter,"reserve",RESERVE);
  assert.equal(out.decision,"HOLD");
  assert.equal(out.reason_code,"D1_ERROR_QUOTA_TIMEOUT_OR_UNKNOWN_HOLD");
  assert.equal(observed.filter(x=>x.kind==="run").length,1);
  assert.ok(!JSON.stringify(out).includes(secret));
  assert.ok(!JSON.stringify(out).includes(SHA));
});

test("broken D1 prepare/bind/run contract is terminal HOLD",async()=>{
  for(const adapter of [
    {__flowminuteSyntheticD1:true,prepare:()=>null},
    {__flowminuteSyntheticD1:true,prepare:()=>({bind:()=>null})},
    {__flowminuteSyntheticD1:true,prepare:()=>({bind:()=>({run:null})})}
  ]) {
    const out=await exerciseSyntheticD1PreparedCAS(adapter,"claim",CLAIM);
    assert.equal(out.decision,"HOLD");
    assert.equal(out.synthetic_prepared_statement_accepted,false);
  }
});

test("constant SQL has database-side time and no worker/API triggers",()=>{
  for(const [name,sql] of Object.entries(D1_CAS_SQL)){
    assert.ok(sql.startsWith("UPDATE "));
    assert.ok(sql.includes("unixepoch('now')") || name==="reserve" && sql.includes("unixepoch('now')"));
    assert.ok(sql.includes("WHERE "));
    assert.ok(sql.length<2000);
    assert.ok(!sql.includes("CREATE TABLE"));
    assert.ok(!sql.includes("INSERT INTO"));
    assert.ok(!sql.includes("DELETE FROM"));
    assert.ok(!sql.includes("DROP TABLE"));
    assert.ok(!sql.includes("youtube.com"));
    assert.ok(!sql.includes("https://"));
  }
});

test("safe result is only generic non-authorizing metadata",async()=>{
  const {adapter}=fakeD1(receipt());
  const result=await exerciseSyntheticD1PreparedCAS(adapter,"reserve",RESERVE);
  const serialized=JSON.stringify(result);
  for(const sensitive of [NONCE,SHA,RESERVE.episodeId,RESERVE.releaseDate]){
    assert.ok(!serialized.includes(sensitive));
  }
  assert.equal(result.monthly_recurring_infrastructure_inr,0);
  assert.equal(result.cloud_quota_verified,false);
  assert.equal(result.cloud_backup_restored,false);
  assert.equal(result.remote_upload_receipt_verified,false);
});
