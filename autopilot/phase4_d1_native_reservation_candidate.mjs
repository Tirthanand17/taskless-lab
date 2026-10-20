/**
 * Major Phase 4 - D1-shaped one-way canonical reservation, fixture ONLY.
 * Not deployable. No real D1/Google/Worker entrypoint or migration.
 */
export const LIVE_D1_RESERVATIONS_ENABLED=false;
export const D1_RESERVATION_SQL=Object.freeze({
  indexes:"PRAGMA index_list('releases')",
  columns:"PRAGMA index_info('ux_release_date_slot')",
  reserve:"UPDATE releases SET state='UPLOAD_STARTED', updated_at_utc=? WHERE release_date=? AND episode_id=? AND channel_id=? AND slot_ist=? AND publish_at_utc=? AND media_sha256=? AND state='MEDIA_QA_PASSED' AND youtube_id IS NULL",
  event:"INSERT INTO release_events (release_date,episode_id,event_kind,detail_json,at_utc) SELECT release_date,episode_id,'UPLOAD_RESERVATION_STARTED','{}',? FROM releases WHERE release_date=? AND episode_id=? AND channel_id=? AND slot_ist=? AND publish_at_utc=? AND media_sha256=? AND state='UPLOAD_STARTED' AND updated_at_utc=? AND youtube_id IS NULL AND NOT EXISTS (SELECT 1 FROM release_events WHERE release_date=? AND episode_id=? AND event_kind='UPLOAD_RESERVATION_STARTED')"
});
const CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA";
const SLOTS={short_morning:"05:30:00Z",long:"10:30:00Z",short_evening:"15:00:00Z"};
const RE_DATE=/^\d{4}-\d{2}-\d{2}$/;
const RE_EPISODE=/^fm_\d{8}_(?:short|long)_(?:en|hi)$/;
const RE_SHA=/^[0-9a-f]{64}$/;
const RE_TIMESTAMP=/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/;
function plain(x,fields){
  return x!==null&&typeof x==="object"&&!Array.isArray(x)&&
    Object.getPrototypeOf(x)===Object.prototype&&
    Object.keys(x).sort().join("|")===fields.slice().sort().join("|");
}
function validDay(v){
  if(typeof v!=="string"||!RE_DATE.test(v))return false;
  const d=new Date(v+"T00:00:00Z");
  return !Number.isNaN(d.getTime())&&d.toISOString().slice(0,10)===v;
}
function valid(p){
  if(!plain(p,["release_date","episode_id","channel_id","slot_ist","publish_at_utc","media_sha256","observed_at_utc"]))return false;
  if(!validDay(p.release_date)||p.channel_id!==CHANNEL||
     typeof p.slot_ist!=="string"||!Object.hasOwn(SLOTS,p.slot_ist)||
     p.publish_at_utc!==p.release_date+"T"+SLOTS[p.slot_ist]||
     typeof p.episode_id!=="string"||!RE_EPISODE.test(p.episode_id)||
     !p.episode_id.startsWith("fm_"+p.release_date.replaceAll("-","")+"_")||
     (p.slot_ist==="long")!==p.episode_id.includes("_long_")||
     typeof p.media_sha256!=="string"||!RE_SHA.test(p.media_sha256)||
     typeof p.observed_at_utc!=="string"||!RE_TIMESTAMP.test(p.observed_at_utc))return false;
  const timestamp=new Date(p.observed_at_utc);
  return Number.isFinite(timestamp.getTime())&&timestamp.toISOString().replace(".000Z","Z")===p.observed_at_utc;
}
function hold(reason){
  return Object.freeze({decision:"HOLD_NO_PRODUCTION_AUTHORITY",reason_code:reason,
    evidence:"UNATTESTED_SYNTHETIC_FIXTURE_ONLY",
    actual_d1_queries:0,actual_d1_writes:0,actual_youtube_uploads:0,
    automatic_upload_retry_allowed:false,real_deployment_allowed:false,
    production_migration_authorized:false,cloud_autopilot_ready:false});
}
function indexesOk(r){
  return r?.success===true&&Array.isArray(r.results)&&r.results.length<=50&&
    r.results.some(x=>x?.name==="ux_release_date_slot"&&x.unique===1&&x.partial===0);
}
function columnsOk(r){
  const x=r?.results;
  return r?.success===true&&Array.isArray(x)&&x.length===2&&
    x[0]?.seqno===0&&x[0]?.name==="release_date"&&Number.isInteger(x[0]?.cid)&&x[0].cid>=0&&
    x[1]?.seqno===1&&x[1]?.name==="slot_ist"&&Number.isInteger(x[1]?.cid)&&x[1].cid>=0;
}
function one(r){return r?.success===true&&r.meta?.changes===1;}
/** Fixture marker is NOT an authentication boundary. Never wire this into a live Worker. */
export async function rehearseNativeD1Reservation(db,p){
  if(LIVE_D1_RESERVATIONS_ENABLED!==false||!db||typeof db!=="object"||
     !Object.hasOwn(db,"__flowminuteSyntheticD1")||
     db.__flowminuteSyntheticD1!==true||typeof db.prepare!=="function")
    return hold("LIVE_D1_BINDING_DENIED");
  if(!valid(p))return hold("INVALID_RESERVATION_PACKET");
  try{
    const ix=await db.prepare(D1_RESERVATION_SQL.indexes).all();
    if(!indexesOk(ix))return hold("UNIQUE_SLOT_INDEX_NOT_VERIFIED");
    const cols=await db.prepare(D1_RESERVATION_SQL.columns).all();
    if(!columnsOk(cols))return hold("UNIQUE_SLOT_COLUMNS_NOT_VERIFIED");
    const updated=await db.prepare(D1_RESERVATION_SQL.reserve).bind(
      p.observed_at_utc,p.release_date,p.episode_id,p.channel_id,
      p.slot_ist,p.publish_at_utc,p.media_sha256).run();
    if(!one(updated))return hold("CAS_NOT_CONFIRMED_EXACT_ONE");
    // Separate event write intentionally: if this fails, the durable
    // UPLOAD_STARTED reservation stays sticky; never compensate or retry.
    const event=await db.prepare(D1_RESERVATION_SQL.event).bind(
      p.observed_at_utc,p.release_date,p.episode_id,p.channel_id,
      p.slot_ist,p.publish_at_utc,p.media_sha256,p.observed_at_utc,
      p.release_date,p.episode_id).run();
    if(!one(event))return hold("EVENT_INSERT_NOT_CONFIRMED");
    return Object.freeze({...hold("SYNTHETIC_ONLY_CAS_AND_EVENT_MATCHED"),
      synthetic_cas_match:true,synthetic_event_match:true});
  }catch{return hold("UNKNOWN_CAS_OR_AUDIT_ACK_NO_RETRY");}
}
