/**
 * FlowMinute 5D: deployable-format, NOT DEPLOYED owner readback Worker.
 * No media or D1 writes, credential refresh, OAuth consent, upload or schedule.
 * Configuration assertions alone do not prove private secret custody or zero cost.
 */
export const STATUS = "NOT_DEPLOYED_UNATTESTED_READONLY_SOURCE";
export const CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA";
const API="https://www.googleapis.com/youtube/v3/";
const SLOTS=Object.freeze({short_morning:[11,0],long:[16,0],short_evening:[20,30]});
const NAMES=Object.keys(SLOTS);
const VID=/^[A-Za-z0-9_-]{11}$/;
const DAY=/^\d{4}-\d{2}-\d{2}$/;
const HEADERS={"content-type":"application/json; charset=utf-8",
               "cache-control":"no-store, max-age=0",
               "x-content-type-options":"nosniff","referrer-policy":"no-referrer"};
const MAX_REQUEST=8192;
function respond(obj,status=200){return new Response(JSON.stringify(obj),{status,headers:HEADERS});}
function denied(reason,status=403){return respond({
  state:"HOLD_UNVERIFIED",reason,uploads_attempted:0,schedules_written:0,
  cloud_autopilot_ready:false,anonymous_playability_verified:false
},status);}
function keys(x,allowed){return !!x && typeof x==="object" && !Array.isArray(x) &&
 Object.getPrototypeOf(x)===Object.prototype &&
 Object.keys(x).sort().join(",")===[...allowed].sort().join(",");}
function dayISO(s){if(typeof s!=="string"||!DAY.test(s))return null;
  const t=new Date(s+"T00:00:00Z");
  return Number.isFinite(t.getTime())&&t.toISOString().slice(0,10)===s?t:null;}
function slotUtc(day,slot){const [hour,minute]=SLOTS[slot];
 return new Date(Date.UTC(day.getUTCFullYear(),day.getUTCMonth(),day.getUTCDate(),
   hour-5,minute-30)).toISOString().replace(".000Z","Z");}
function manifest(body){
 if(!keys(body,["date","slots"]))return null;
 const d=dayISO(body.date);
 if(!d||!keys(body.slots,NAMES))return null;
 const seen=new Set();
 for(const name of NAMES){
  const item=body.slots[name];
  if(!keys(item,["video_id","title"])||typeof item.title!=="string"||
   item.title.trim()!==item.title||item.title.length<1||item.title.length>100)return null;
  const id=item.video_id;
  if(id!==null&&(typeof id!=="string"||!VID.test(id)||seen.has(id)))return null;
  if(id!==null)seen.add(id);
 }
 return {day:d,slots:body.slots};
}
async function adminOk(given,expected){
 if(typeof expected!=="string"||expected.length<32||expected.length>256||
    typeof given!=="string"||!given.startsWith("Bearer ")||given.length>300)return false;
 const entered=given.slice(7);
 if(!/^[A-Za-z0-9._~-]{32,256}$/.test(entered))return false;
 const encoder=new TextEncoder();
 const a=new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(entered)));
 const b=new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(expected)));
 if(a.length!==b.length)return false;
 let diff=0;for(let i=0;i<a.length;i++)diff|=a[i]^b[i];return diff===0;
}
function enabled(e,now){
 if(!e||e.FM_OWNER_READBACK_ENABLED!=="1"||e.FM_UPLOADS_ENABLED!=="0"||
    e.FM_SCHEDULING_ENABLED!=="0"||e.FM_HARD_ZERO_OVERAGE_VERIFIED!=="1"||
    e.FM_EXPECTED_CHANNEL_ID!==CHANNEL||
    typeof e.FM_YOUTUBE_ACCESS_TOKEN!=="string"||
    e.FM_YOUTUBE_ACCESS_TOKEN.length<16||
    typeof e.FM_YOUTUBE_ACCESS_EXPIRES_AT!=="string"||
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(e.FM_YOUTUBE_ACCESS_EXPIRES_AT))return false;
 const expiry=Date.parse(e.FM_YOUTUBE_ACCESS_EXPIRES_AT);
 return Number.isFinite(expiry)&&expiry>now+1200000&&expiry<=now+4500000;
}
async function limitedJson(response){
 if(!response||!response.ok||response.status!==200)throw Error("API_NOT_OK");
 const size=response.headers.get("content-length");
 if(size!==null&&(!/^\d+$/.test(size)||Number(size)>65536))throw Error("OVERSIZED");
 const reader=response.body?.getReader?.();
 if(!reader)throw Error("NOT_STREAMING");
 let total=0;const blocks=[];
 try{for(;;){const {done,value}=await reader.read();if(done)break;
   total+=value.byteLength;if(total>65536)throw Error("TOO_LONG");blocks.push(value);}
 }finally{try{await reader.cancel();}catch{}try{reader.releaseLock();}catch{}}
 const data=new Uint8Array(total);let n=0;
 for(const block of blocks){data.set(block,n);n+=block.length;}
 const object=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(data));
 if(!object||typeof object!=="object"||Array.isArray(object))throw Error("SHAPE");
 return object;
}
async function youtube(e,path,query){
 if(path!=="channels"&&path!=="videos")throw Error("ROUTE");
 const u=new URL(API+path);
 for(const [k,v]of Object.entries(query))u.searchParams.set(k,String(v));
 const response=await fetch(u.toString(),{method:"GET",redirect:"error",
  cache:"no-store",headers:{Authorization:"Bearer "+e.FM_YOUTUBE_ACCESS_TOKEN,
                           Accept:"application/json"}});
 return limitedJson(response);
}
function videoState(remote,id,title,time,now){
 if(remote?.id!==id||remote.snippet?.channelId!==CHANNEL||
    remote.snippet?.title!==title||remote.status?.uploadStatus!=="processed"||
    remote.processingDetails?.processingStatus!=="succeeded")return "HOLD_UNVERIFIED";
 if(remote.status?.privacyStatus==="private"&&remote.status?.publishAt===time&&
    Date.parse(time)>now)return "SCHEDULED_VERIFIED";
 if(remote.status?.privacyStatus==="public"&&Date.parse(time)<=now)
    return "PUBLIC_STATUS_ONLY";
 return "HOLD_UNVERIFIED";
}
export default{async fetch(req,e){
 try{
  const u=new URL(req.url);
  if(req.method==="GET"&&u.pathname==="/health"&&u.search==="")
   return respond({service:"FlowMinute Phase5D",source_status:STATUS,
                  real_provider_deployment_verified:false,publishing_enabled:false});
  if(req.method!=="POST"||u.pathname!=="/v1/owner-readback"||u.search!=="")
   return denied("ROUTE_NOT_AVAILABLE",404);
  const now=Date.now();
  if(!enabled(e,now))return denied("READBACK_NOT_APPROVED_OR_EXPIRED");
  if(!await adminOk(req.headers.get("authorization"),e.FM_ADMIN_READBACK_KEY))
   return denied("UNAUTHORIZED",401);
  // Cloudflare native rate limiter is a MANDATORY binding. No limiter means
  // no Google requests. Its counters are per edge location, NOT a global cost cap.
  if(typeof e.FM_READBACK_RATE_LIMITER?.limit!=="function")
   return denied("RATE_LIMIT_BINDING_MISSING");
  const rate=await e.FM_READBACK_RATE_LIMITER.limit({key:"flowminute:owner-readback"});
  if(rate?.success!==true)return denied("RATE_LIMITED",429);
  const claimed=req.headers.get("content-length");
  if(claimed!==null&&(!/^\d+$/.test(claimed)||Number(claimed)>MAX_REQUEST))
   return denied("REQUEST_TOO_LARGE",413);
  const body=await req.text();
  if(new TextEncoder().encode(body).byteLength>MAX_REQUEST)
   return denied("REQUEST_TOO_LARGE",413);
  const input=manifest(JSON.parse(body));
  if(!input)return denied("INVALID_THREE_SLOT_MANIFEST",400);
  const owner=await youtube(e,"channels",{part:"id",mine:"true",maxResults:50});
  if(!Array.isArray(owner.items)||!owner.items.some(x=>x?.id===CHANNEL))
   return denied("WRONG_OWNER_CHANNEL");
  const lanes=[];
  for(const name of NAMES){
   const {video_id,title}=input.slots[name];const at=slotUtc(input.day,name);
   let status="MISSING_VIDEO";
   if(video_id!==null){
    try{
     const obs=await youtube(e,"videos",{
       part:"snippet,status,processingDetails",id:video_id});
     status=Array.isArray(obs.items)&&obs.items.length===1
       ?videoState(obs.items[0],video_id,title,at,now):"HOLD_UNVERIFIED";
    }catch{status="HOLD_UNVERIFIED";}
   }
   lanes.push({slot:name,publish_at_utc:at,status});
  }
  return respond({state:"OWNER_READ_OBSERVED_UNATTESTED",channel_id:CHANNEL,
   slots_total:3,verified_platform_state_count:lanes.filter(x=>
     x.status==="SCHEDULED_VERIFIED"||x.status==="PUBLIC_STATUS_ONLY").length,
   lanes,source_trust:"UNATTESTED_WORKER_ENVIRONMENT",cloud_autopilot_ready:false,
   production_upload_authorized:false,production_schedule_authorized:false,
   uploads_attempted:0,schedules_written:0,anonymous_playability_verified:false});
 }catch{return denied("REMOTE_OR_MANIFEST_FAILED",400);}
}};
