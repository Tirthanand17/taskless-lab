import test from 'node:test';
import assert from 'node:assert/strict';
import {CANONICAL_SELECT, LIVE_D1_ENABLED, syntheticReadback} from './canonical_d1_readback_candidate.mjs';
const channel = 'UCCcL9Q_jqVq6LJmnYUSAFZA';
const names = ['short_morning', 'long', 'short_evening'];
const episodes = ['fm_20261020_short_en', 'fm_20261020_long_hi', 'fm_20261020_short_hi'];
const videos = ['AbCdEfGhIj0', 'KlMnOpQrSt1', 'MnOpQrStUv2'];
const times = ['2026-10-20T05:30:00Z', '2026-10-20T10:30:00Z', '2026-10-20T15:00:00Z'];
function manifest() {
  return {date:'2026-10-20', channel_id:channel, slots:Object.fromEntries(names.map((name,i)=>
    [name, {episode_id:episodes[i], youtube_id:videos[i],
       publish_at_utc:times[i], media_sha256:String(i+1).repeat(64)}]))};
}
function rows() {
  return names.map((slot,i)=>({release_date:'2026-10-20', episode_id:episodes[i],
    channel_id:channel, slot_ist:slot, publish_at_utc:times[i],
    state:'SCHEDULED_VERIFIED',media_sha256:String(i+1).repeat(64),youtube_id:videos[i]}));
}
function events() {
  return [{episode_id:episodes[0],event_kind:'SCHEDULED',at_utc:'2026-10-19T20:00:00Z'}];
}
function db(rs=rows(),es=events(),bad=null) {
  const requests=[];
  let total=0;
  const object = {__flowminuteSyntheticD1:true,prepare(sql) {
    total++;
    if(!Object.values(CANONICAL_SELECT).includes(sql)) throw Error('Write query prohibited');
    return {bind(...args) { requests.push({sql, args}); return {async all() {
      if(bad==='exception')throw Error('PRIVATE_ACCESS_TOKEN_SHOULD_NEVER_BE_EXPOSED');
      const result = sql===CANONICAL_SELECT.releases ? rs : es;
      return {success:bad!=='failed', meta:{served_by_primary:bad!=='replica'},results:result};
    }}; }};
  }};
  return {object,requests,count:()=>total};
}
const check=(c,m=manifest())=>syntheticReadback(c.object,m);
function safe(result){
  assert.equal(result.real_cloudflare_writes,0);
  assert.equal(result.real_youtube_uploads,0);
  assert.equal(result.real_schedule_writes,0);
  assert.equal(result.cloud_autopilot_ready,false);
  assert.equal(result.reupload_authorized,false);
  assert.equal(result.migration_authorized,false);
  const raw=JSON.stringify(result);
  for(const secret of [...videos,...episodes,'PRIVATE_ACCESS_TOKEN_SHOULD_NEVER_BE_EXPOSED'])
    assert.equal(raw.includes(secret),false);
}

test('exact canonical D1 SELECT statements only; no legacy shadow table',()=>{
  assert.equal(LIVE_D1_ENABLED,false);
  assert.ok(CANONICAL_SELECT.releases.includes('FROM releases'));
  assert.ok(CANONICAL_SELECT.events.includes('FROM release_events'));
  for(const sql of Object.values(CANONICAL_SELECT)) {
    assert.ok(sql.startsWith('SELECT '));
    assert.ok(sql.includes('WHERE release_date=?'));
    assert.ok(!/INSERT|UPDATE|DELETE|ALTER|DROP|fm_writer_release_shadow/i.test(sql));
  }
});
test('matching three receipts remain hold; two bound read queries',async()=>{
  const c=db(); const r=await check(c);
  assert.equal(r.reason_code,'CANONICAL_CONSISTENCY_IS_NOT_PUBLISH_AUTHORITY');
  assert.equal(r.missing_lanes,0); assert.equal(r.conflicting_lanes,0);
  assert.deepEqual(c.requests.map(x=>x.args),[['2026-10-20'],['2026-10-20']]);
  assert.equal(c.count(),2); safe(r);
});
test('empty canonical D1 shows three missing episodes, never retries',async()=>{
  const r=await check(db([],[]));
  assert.equal(r.missing_lanes,3);safe(r);
});
test('unknown upload acknowledgement is quarantined',async()=>{
  const r=rows();r[1].state='UPLOAD_STARTED';
  const out=await check(db(r));
  assert.equal(out.uncertain_lanes,1);
  assert.equal(out.lanes.long,'STATE_OR_REMOTE_ACK_UNCERTAIN_NO_RETRY');safe(out);
});
test('unresolved scheduling is quarantined',async()=>{
  const r=rows();r[1].state='SCHEDULING_UNRESOLVED';
  const out=await check(db(r));assert.equal(out.uncertain_lanes,1);safe(out);
});
test('different episode claiming same date slot is blocked',async()=>{
  const r=rows().slice(0,2);r.push({...rows()[2],slot_ist:'short_morning',publish_at_utc:times[0]});
  const out=await check(db(r));
  assert.equal(out.reason_code,'DUPLICATE_CANONICAL_SLOT');safe(out);
});
test('immutable video ID mismatch detected',async()=>{
  const r=rows();r[0].youtube_id='aaaaaaaaaaa';
  const out=await check(db(r));assert.equal(out.conflicting_lanes,1);safe(out);
});
test('SHA mismatch or wrong publication time is rejected',async()=>{
  const r=rows();r[1].media_sha256='0'.repeat(64);
  const out=await check(db(r));assert.equal(out.conflicting_lanes,1);safe(out);
  const bad=rows();bad[1].publish_at_utc='2026-10-20T20:30:00Z';
  const out2=await check(db(bad));assert.equal(out2.reason_code,'MALFORMED_CANONICAL_ROW');safe(out2);
});
test('orphan release event holds reconciliation',async()=>{
  const es=events();es[0].episode_id='fm_20261020_short_hi';
  const r=await check(db(rows().slice(0,2),es));
  assert.equal(r.reason_code,'ORPHAN_RELEASE_EVENT');safe(r);
});
test('100 events indicates truncated history',async()=>{
  const es=Array.from({length:100},()=>({...events()[0]}));
  const r=await check(db(rows(),es));
  assert.equal(r.reason_code,'TRUNCATED_CANONICAL_RESULT');safe(r);
});
test('failed or replica query holds',async()=>{
  for(const flag of ['failed','replica','exception']) {
    const r=await check(db(rows(),events(),flag));
    assert.ok(r.reason_code.includes('UNKNOWN')||r.reason_code.includes('ERROR'));safe(r);
  }
});
test('real D1-like binding executes no query',async()=>{
  let called=0;
  const result=await syntheticReadback({prepare(){called++;throw Error('never');}},manifest());
  assert.equal(called,0);assert.equal(result.reason_code,'LIVE_BINDING_REJECTED');safe(result);
});
test('invalid channel, day or duplicate plan videos rejected before provider calls',async()=>{
  for(const mutate of [m=>m.channel_id='unrelated',m=>m.date='2026-02-30',
    m=>m.slots.long.youtube_id=m.slots.short_morning.youtube_id]) {
    const m=manifest();mutate(m);const c=db();
    const r=await check(c,m);assert.equal(r.reason_code,'INVALID_RELEASE_MANIFEST');
    assert.equal(c.count(),0);safe(r);
  }
});
test('unexpected credential field rejected without provider reads',async()=>{
  const m=manifest();m.refresh_token='SECRET';const c=db();
  const r=await check(c,m);assert.equal(c.count(),0);safe(r);
});
test('malformed state or extra payload fields are rejected',async()=>{
  const r=rows();r[0].state='UPLOAD_AGAIN';r[0].token='PRIVATE';
  const out=await check(db(r));
  assert.equal(out.reason_code,'MALFORMED_CANONICAL_ROW');safe(out);
});
