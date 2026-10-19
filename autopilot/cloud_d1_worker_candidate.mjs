/**
 * Phase 4K: DEPLOYMENT-DISABLED D1 Worker binding CAS candidate.
 *
 * Prepared statements are Cloudflare-shaped, but this module will invoke
 * them ONLY on an explicitly branded synthetic D1 adapter supplied by tests.
 * It exports no fetch/scheduled Worker entrypoint, account binding, database
 * migration, network client, retry logic, or YouTube interaction.
 *
 * The SQLite unixepoch('now') source is evaluated within the SAME D1 SQL
 * statement as conditional CAS; caller timestamps NEVER determine expiry.
 * A lost external YouTube videos.insert acknowledgement is UNKNOWN, never
 * an invitation to retry after the lease expires.
 */

export const LIVE_CLOUDFLARE_WRITES_ENABLED = false;

export const D1_CAS_SQL = Object.freeze({
  claim: [
    "UPDATE fm_release_writer_lease",
    "SET owner_nonce=?, fence_epoch=fence_epoch+1,",
    "expires_at_unix=unixepoch('now')+?,",
    "last_checked_unix=unixepoch('now')",
    "WHERE singleton=1 AND fence_epoch=?",
    "AND expires_at_unix<=unixepoch('now')",
    "AND last_checked_unix<=unixepoch('now')",
    "AND fence_epoch<1000000000"
  ].join(" "),
  renew: [
    "UPDATE fm_release_writer_lease",
    "SET expires_at_unix=unixepoch('now')+?,",
    "last_checked_unix=unixepoch('now')",
    "WHERE singleton=1 AND owner_nonce=? AND fence_epoch=?",
    "AND expires_at_unix>unixepoch('now')",
    "AND last_checked_unix<=unixepoch('now')"
  ].join(" "),
  reserve: [
    "UPDATE fm_writer_release_shadow",
    "SET stage='upload_started',",
    "updated_at_utc=strftime('%Y-%m-%dT%H:%M:%SZ','now')",
    "WHERE release_date=? AND episode_id=? AND media_sha256=?",
    "AND stage='media_qa_passed'",
    "AND EXISTS (SELECT 1 FROM fm_release_writer_lease",
    "WHERE singleton=1 AND owner_nonce=? AND fence_epoch=?",
    "AND expires_at_unix>unixepoch('now')",
    "AND last_checked_unix<=unixepoch('now'))"
  ].join(" ")
});

const NONCE = /^[A-Za-z0-9_-]{32,64}$/;
const EPISODE = /^[a-z][a-z0-9_]{2,63}$/;
const SHA256 = /^[a-f0-9]{64}$/;
const DAY = /^\d{4}-\d{2}-\d{2}$/;

const RESULT = Object.freeze({
  status: "SYNTHETIC_D1_CAS_NOT_PRODUCTION_AUTHORITY",
  real_cloud_d1_written: false,
  real_d1_writer_deployed: false,
  cloud_quota_verified: false,
  cloud_backup_restored: false,
  remote_upload_receipt_verified: false,
  upload_retry_authorized: false,
  youtube_upload_authorized: false,
  scheduling_or_publishing_authorized: false,
  external_network_requests: 0,
  live_d1_writes: 0,
  monthly_recurring_infrastructure_inr: 0
});

function base(accepted, reason) {
  return Object.freeze({
    ...RESULT,
    synthetic_prepared_statement_accepted: accepted,
    decision: accepted ? "SHADOW_CAS_ONLY" : "HOLD",
    reason_code: reason
  });
}

function canonicalUtcDay(value) {
  if (typeof value !== "string" || !DAY.test(value)) return false;
  const ms = Date.parse(value + "T00:00:00Z");
  return Number.isFinite(ms) &&
    new Date(ms).toISOString().slice(0,10) === value;
}

function assertInputs(operation, values) {
  if (typeof values !== "object" || values === null ||
      Array.isArray(values) || Object.getPrototypeOf(values) !== Object.prototype) {
    return null;
  }
  const nonce = values.nonce;
  const epoch = values.epoch;
  if (typeof nonce !== "string" || !NONCE.test(nonce) ||
      !Number.isSafeInteger(epoch) || epoch < 0 || epoch > 999999998) return null;
  if (operation === "claim" || operation === "renew") {
    const ttl = values.ttlSeconds;
    if (!Number.isSafeInteger(ttl) || ttl < 1 || ttl > 300 ||
        (operation === "renew" && epoch === 0)) return null;
    if (Object.keys(values).sort().join(",") !== "epoch,nonce,ttlSeconds") return null;
    return operation === "claim"
      ? [nonce,ttl,epoch] : [ttl,nonce,epoch];
  }
  if (operation === "reserve") {
    if (epoch === 0 || !canonicalUtcDay(values.releaseDate) ||
        typeof values.episodeId !== "string" || !EPISODE.test(values.episodeId) ||
        typeof values.mediaSha256 !== "string" || !SHA256.test(values.mediaSha256) ||
        Object.keys(values).sort().join(",") !==
          "episodeId,epoch,mediaSha256,nonce,releaseDate") return null;
    return [values.releaseDate,values.episodeId,values.mediaSha256,nonce,epoch];
  }
  return null;
}

export function inspectD1WriteResult(result) {
  // Both "primary" and single-row change are mandatory. If a D1 version
  // omits or changes these fields, stop: never infer success.
  if (typeof result !== "object" || result === null ||
      result.success !== true || typeof result.meta !== "object" ||
      result.meta === null || result.meta.served_by_primary !== true ||
      result.meta.changed_db !== true ||
      result.meta.changes !== 1 || result.meta.rows_written !== 1 ||
      !Number.isInteger(result.meta.total_attempts ?? 1) ||
      (result.meta.total_attempts ?? 1) !== 1) return false;
  // D1 statements for UPDATE return an empty results array (or null).
  return result.results === null || (
    Array.isArray(result.results) && result.results.length === 0
  );
}

export async function exerciseSyntheticD1PreparedCAS(db, operation, values) {
  // This is a strict synthetic adapter gate, NOT runtime proof of owner
  // authorization. Real Cloudflare D1 binding MUST NOT be passed in.
  if (LIVE_CLOUDFLARE_WRITES_ENABLED !== false ||
      typeof db !== "object" || db === null ||
      !Object.prototype.hasOwnProperty.call(db,"__flowminuteSyntheticD1") ||
      db.__flowminuteSyntheticD1 !== true ||
      typeof db.prepare !== "function") {
    return base(false, "REAL_D1_BINDING_OR_DISABLED_GATE_DENIED");
  }
  const bindings = assertInputs(operation, values);
  if (bindings === null || !Object.prototype.hasOwnProperty.call(D1_CAS_SQL,operation)) {
    return base(false, "INVALID_CAS_OPERATION_OR_BINDINGS");
  }
  try {
    const prepared = db.prepare(D1_CAS_SQL[operation]);
    if (typeof prepared?.bind !== "function") {
      return base(false, "INVALID_D1_PREPARE_INTERFACE");
    }
    const bound = prepared.bind(...bindings);
    if (typeof bound?.run !== "function") {
      return base(false, "INVALID_D1_RUN_INTERFACE");
    }
    const receipt = await bound.run();
    if (!inspectD1WriteResult(receipt)) {
      return base(false, "CAS_NOT_EXACTLY_ONE_PRIMARY_WRITE");
    }
    return base(true, "ONE_SYNTHETIC_PREPARED_WRITE_CONFIRMED");
  } catch {
    // Never echo provider exceptions, release IDs, owner nonce, SQL or tokens.
    return base(false, "D1_ERROR_QUOTA_TIMEOUT_OR_UNKNOWN_HOLD");
  }
}
