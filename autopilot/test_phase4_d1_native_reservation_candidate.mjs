import test from 'node:test';
import assert from 'node:assert/strict';
import {D1_RESERVATION_SQL, LIVE_D1_RESERVATIONS_ENABLED, rehearseNativeD1Reservation} from './phase4_d1_native_reservation_candidate.mjs';
const packet=()=>({release_date:'2026-10-20',episode_id:'fm_20261020_long_hi',
channel_id:'UCCcL9Q_jqVq6LJmnYUSAFZA',slot_ist:'long',publish_at_utc:'2026-10-20T10:30:00Z',
media_sha256:'a'.repeat(64),observed_at_utc:'2026-10-20T06:00:00Z'});
function stub(o={}){
 let state=o.initialState??'MEDIA_QA_PASSED',events=0;
 const calls=[];
 const db={__flowminuteSyntheticD1:true,prepare(sql){
  calls.push(['prepare',sql]);return {
   async all(){
    if(o.readThrows)throw Error('PRIVATE_TOKEN');
    if(sql===D1_RESERVATION_SQL.indexes)return {success:true,results:o.noIndex?[]:[{name:'ux_release_date_slot',unique:o.nonUnique?0:1,partial:o.partial?1:0}]};
    if(sql===D1_RESERVATION_SQL.columns)return {success:true,results:o.badColumns?[{seqno:0,name:'episode_id',cid:1}]:[{seqno:0,name:'release_date',cid:0},{seqno:1,name:'slot_ist',cid:3}]};
    throw Error('UNEXPECTED_QUERY');
   },
   bind(...args){calls.push(['bind',sql,args.length]);return {async run(){
    calls.push(['run',sql]);
    if(sql===D1_RESERVATION_SQL.reserve){
     if(o.casThrows)throw Error('PRIVATE_TOKEN');
     if(state!=='MEDIA_QA_PASSED'||o.mismatch)return {success:true,meta:{changes:0}};
     state='UPLOAD_STARTED';
     return o.unknownCas?{success:true,meta:{}}:{success:true,meta:{changes:1}};
    }
    if(sql===D1_RESERVATION_SQL.event){
     if(o.eventThrows)throw Error('PRIVATE_TOKEN');
     if(o.eventLost||state!=='UPLOAD_STARTED'||events)return {success:true,meta:{changes:0}};
     events++;return {success:true,meta:{changes:1}};
    }
    throw Error('UNEXPECTED_MUTATION');
   }};}
  };
 }};
 return {db,calls,state:()=>state,events:()=>events};
}
const run=(s,p=packet())=>rehearseNativeD1Reservation(s.db,p);
function denied(r){
 assert.equal(r.decision,'HOLD_NO_PRODUCTION_AUTHORITY');
 assert.equal(r.actual_d1_writes,0);assert.equal(r.actual_youtube_uploads,0);
 assert.equal(r.automatic_upload_retry_allowed,false);assert.equal(r.cloud_autopilot_ready,false);
 assert.ok(!JSON.stringify(r).includes('PRIVATE_TOKEN'));
}
test('hard disabled production switch',()=>assert.equal(LIVE_D1_RESERVATIONS_ENABLED,false));
test('real binding without fixture marker rejected and not queried',async()=>{
 let count=0;const r=await rehearseNativeD1Reservation({prepare(){count++;}},packet());
 assert.equal(count,0);assert.equal(r.reason_code,'LIVE_D1_BINDING_DENIED');denied(r);
});
test('fixed SQL targets canonical tables only',()=>{
 assert.match(D1_RESERVATION_SQL.reserve,/^UPDATE releases SET/);
 assert.match(D1_RESERVATION_SQL.event,/^INSERT INTO release_events/);
 assert.ok(!JSON.stringify(D1_RESERVATION_SQL).includes('fm_writer_release_shadow'));
});
test('missing unique date slot index holds without writes',async()=>{
 const s=stub({noIndex:true}),r=await run(s);
 assert.equal(r.reason_code,'UNIQUE_SLOT_INDEX_NOT_VERIFIED');
 assert.equal(s.calls.filter(x=>x[0]==='run').length,0);denied(r);
});
test('nonunique or partial index rejected',async()=>{
 for(const x of [{nonUnique:true},{partial:true}])assert.equal((await run(stub(x))).reason_code,'UNIQUE_SLOT_INDEX_NOT_VERIFIED');
});
test('wrong index column order rejected',async()=>{
 const r=await run(stub({badColumns:true}));
 assert.equal(r.reason_code,'UNIQUE_SLOT_COLUMNS_NOT_VERIFIED');denied(r);
});
test('single CAS then append only after one-row acknowledgement',async()=>{
 const s=stub(),r=await run(s);
 assert.equal(s.state(),'UPLOAD_STARTED');assert.equal(s.events(),1);
 assert.deepEqual(s.calls.filter(x=>x[0]==='bind').map(x=>x[2]),[7,10]);
 assert.equal(r.synthetic_cas_match,true);denied(r);
});
test('second call does not create new event',async()=>{
 const s=stub();await run(s);const r=await run(s);
 assert.equal(r.reason_code,'CAS_NOT_CONFIRMED_EXACT_ONE');
 assert.equal(s.events(),1);denied(r);
});
test('unknown CAS acknowledgement makes sticky reservation without audit',async()=>{
 const s=stub({unknownCas:true}),r=await run(s);
 assert.equal(s.state(),'UPLOAD_STARTED');assert.equal(s.events(),0);
 assert.equal(r.reason_code,'CAS_NOT_CONFIRMED_EXACT_ONE');denied(r);
});
test('failed event does not undo sticky reservation',async()=>{
 const s=stub({eventThrows:true}),r=await run(s);
 assert.equal(s.state(),'UPLOAD_STARTED');assert.equal(s.events(),0);
 assert.equal(r.reason_code,'UNKNOWN_CAS_OR_AUDIT_ACK_NO_RETRY');denied(r);
});
test('missing event confirmation fails closed',async()=>{
 const r=await run(stub({eventLost:true}));
 assert.equal(r.reason_code,'EVENT_INSERT_NOT_CONFIRMED');denied(r);
});
test('preexisting unresolved or public state never reserved again',async()=>{
 for(const initialState of ['UPLOAD_STARTED','SCHEDULED_VERIFIED','PUBLIC_VERIFIED']){
 const r=await run(stub({initialState}));
 assert.equal(r.reason_code,'CAS_NOT_CONFIRMED_EXACT_ONE');denied(r);
 }
});
test('immutable mismatch prevents event insertion',async()=>{
 const s=stub({mismatch:true}),r=await run(s);
 assert.equal(s.events(),0);assert.equal(r.reason_code,'CAS_NOT_CONFIRMED_EXACT_ONE');denied(r);
});
test('provider exception not leaked or retried',async()=>{
 for(const options of [{readThrows:true},{casThrows:true}]){
 const r=await run(stub(options));assert.equal(r.reason_code,'UNKNOWN_CAS_OR_AUDIT_ACK_NO_RETRY');denied(r);
 }
});
test('invalid channel, date, sha, schedule, secret field rejected before DB access',async()=>{
 const cases=[p=>p.channel_id='UCbad',p=>p.release_date='2026-02-30',p=>p.media_sha256='BAD',
 p=>p.publish_at_utc='2026-10-20T16:00:00Z',p=>p.token='PRIVATE'];
 for(const change of cases){const p=packet();change(p);const s=stub(),r=await run(s,p);
 assert.equal(r.reason_code,'INVALID_RESERVATION_PACKET');assert.equal(s.calls.length,0);denied(r);}
});
