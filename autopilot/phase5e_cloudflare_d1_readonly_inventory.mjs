/**
 * Phase 5E: Cloudflare D1 restricted, read-only structural inventory candidate.
 *
 * NOT deployed. No D1 data row, private OAuth schema, token, credential,
 * migration, upload, schedule, or storage operation. Constant SELECT/PRAGMA
 * queries only; not a free-billing or authentic-Cloudflare attestation.
 */
export const LIVE_D1_INSPECTION_DEPLOYED = false;
const TABLES=Object.freeze([
 "fm_release_writer_lease",
 "fm_writer_release_shadow",
 "fm_releases_shadow",
 "fm_releases"
]);
const BRAND_PROOF="fm_oauth_channel_proofs";
const SQL="SELECT name, type FROM sqlite_master WHERE type='table' AND name IN ('fm_release_writer_lease','fm_writer_release_shadow','fm_releases_shadow','fm_releases','fm_oauth_channel_proofs') ORDER BY name LIMIT 6";
const PRAGMA=Object.freeze({
 "fm_release_writer_lease":'PRAGMA table_info("fm_release_writer_lease")',
 "fm_writer_release_shadow":'PRAGMA table_info("fm_writer_release_shadow")',
 "fm_releases_shadow":'PRAGMA table_info("fm_releases_shadow")',
 "fm_releases":'PRAGMA table_info("fm_releases")'
});
const COLUMN=/^[a-zA-Z_][a-zA-Z0-9_]{0,63}$/;
const REDACT=/oauth|token|refresh|secret|password|cookie|credential|private|cipher|nonce|signature|key/i;
const HEADERS={"content-type":"application/json; charset=utf-8",
 "cache-control":"no-store, max-age=0","x-content-type-options":"nosniff",
 "referrer-policy":"no-referrer"};
const RATES=Object.freeze({key:"flowminute:d1:read-only-inventory"});
function reply(data,status=200){return new Response(JSON.stringify(data),{status,headers:HEADERS});}
function block(reason,status=403){return reply({
  state:"HOLD_UNVERIFIED",reason,cloud_autopilot_ready:false,
  production_migration_authorized:false,production_d1_writes:0,
  youtube_uploads:0,youtube_schedules:0
 },status);}
function safeEnv(e){
 return !!e && e.FM_D1_READONLY_INSPECT_ENABLED==="1" &&
  e.FM_UPLOADS_ENABLED==="0" && e.FM_SCHEDULING_ENABLED==="0" &&
  e.FM_D1_WRITES_ENABLED==="0" && e.FM_OWNER_READONLY_INSPECTION_APPROVED==="1" &&
  e.FM_HARD_ZERO_OVERAGE_VERIFIED==="1" &&
  typeof e.FM_D1_ADMIN_KEY==="string" && e.FM_D1_ADMIN_KEY.length>=32 &&
  e.FM_D1_ADMIN_KEY.length<=256 && e.DB && typeof e.DB.prepare==="function" &&
  typeof e.FM_D1_RATE_LIMITER?.limit==="function";
}
async function authenticate(given,secret){
 if(typeof given!=="string" || !given.startsWith("Bearer ") ||
  given.length>300) return false;
 const entered=given.slice(7);
 if(!/^[A-Za-z0-9._~-]{32,256}$/.test(entered)) return false;
 const encoder=new TextEncoder();
 const a=new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(entered)));
 const b=new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(secret)));
 if(a.length!==b.length)return false;
 let diff=0;for(let i=0;i<a.length;i++)diff|=a[i]^b[i];
 return diff===0;
}
async function select(db,sql,max){
 // Constant query strings only. Never construct SQL from request or
 // provider-result names. Require success and bounded result shape.
 if(sql!==SQL && !Object.values(PRAGMA).includes(sql))throw Error("UNKNOWN_QUERY");
 const bound=db.prepare(sql);
 if(!bound || typeof bound.all!=="function")throw Error("NO_ALL");
 const result=await bound.all();
 if(result?.success!==true || !Array.isArray(result.results) ||
    result.results.length>max)throw Error("BAD_D1_RESULT");
 if(result.results.some(r=>!r || typeof r!=="object" || Array.isArray(r)))
  throw Error("INVALID_ROWS");
 return result.results;
}
async function inspect(db){
 const rows=await select(db,SQL,5);
 const seen=new Set();
 for(const row of rows){
  if(typeof row.name!=="string" || typeof row.type!=="string" ||
     row.type!=="table" ||
     (row.name!==BRAND_PROOF && !TABLES.includes(row.name)) ||
     seen.has(row.name))throw Error("MALFORMED_CATALOG");
  seen.add(row.name);
 }
 const output=[];
 for(const name of TABLES){
  if(!seen.has(name))continue;
  const columns=await select(db,PRAGMA[name],64);
  const all=new Set(),report=[];
  for(const col of columns){
   if(typeof col.name!=="string" || !COLUMN.test(col.name) ||
      all.has(col.name))throw Error("INVALID_COLUMN");
   all.add(col.name);
   if(!REDACT.test(col.name))report.push({
     name:col.name,
     primary_key_position:Number.isInteger(col.pk) && col.pk>=0 && col.pk<=16?col.pk:0
   });
  }
  output.push({name,visible_columns:report.sort((a,b)=>a.name.localeCompare(b.name)),
    protected_column_count:columns.length-report.length,
    unknown_unique_indexes:true});
 }
 return {
  state:"READ_ONLY_D1_SCHEMA_SNAPSHOT_UNATTESTED",
  source_trust:"INJECTED_D1_BINDING_NOT_PROVEN_IN_OFFLINE_TEST",
  observed_candidate_tables:output,
  found_candidate_count:output.length,
  historically_known_brand_proof_table_present:seen.has(BRAND_PROOF),
  complete_cloudflare_account_inventory:false,
  data_rows_read:0,
  oauth_ciphertext_or_secrets_read:false,
  uniqueness_constraints_verified:false,
  global_zero_cost_cap_verified:false,
  current_cloudflare_admin_provenance_verified:false,
  migration_approved:false,production_d1_writes:0,youtube_uploads:0,
  youtube_schedules:0,cloud_autopilot_ready:false
 };
}
export default {
 async fetch(request,env){
  try{
   const url=new URL(request.url);
   if(url.pathname==="/health" && request.method==="GET" && !url.search){
    return reply({phase:"5E",deployed_verified:false,live_writes_enabled:false});
   }
   if(url.pathname!=="/v1/d1/schema-inventory" || request.method!=="POST" ||
      url.search || request.headers.get("content-length")!=="0")
    return block("ROUTE_OR_BODY_DENIED",404);
   if(!safeEnv(env))return block("READ_ONLY_D1_INSPECTION_DISABLED");
   if(!await authenticate(request.headers.get("authorization"),env.FM_D1_ADMIN_KEY))
    return block("UNAUTHORIZED",401);
   const rate=await env.FM_D1_RATE_LIMITER.limit(RATES);
   if(rate?.success!==true)return block("LIMITED_OR_NO_GLOBAL_QUOTA_PROOF",429);
   const data=await inspect(env.DB);
   return reply(data);
  }catch{
   // Nothing from D1, OAuth, admin credentials or dynamic exceptions returned.
   return block("INVENTORY_QUERY_UNVERIFIED",503);
  }
 }
};
