/**
 * FlowMinute Lab — Major Phases 4/5 canonical D1 adapter.
 *
 * Only reads the existing releases / release_events tables. The adapter
 * accepts a synthetic test double only; it must NOT be wired into a deployed
 * Worker until separately reviewed. No fetch/cron entrypoint, OAuth, writes,
 * re-uploads, scheduling, migrations or retry behavior.
 */
export const LIVE_D1_ENABLED = false;
export const CANONICAL_SELECT = Object.freeze({
  releases: 'SELECT release_date,episode_id,channel_id,slot_ist,publish_at_utc,state,media_sha256,youtube_id FROM releases WHERE release_date=? ORDER BY slot_ist,episode_id LIMIT 16',
  events: 'SELECT episode_id,event_kind,at_utc FROM release_events WHERE release_date=? ORDER BY id DESC LIMIT 100',
});
const CHANNEL = 'UCCcL9Q_jqVq6LJmnYUSAFZA';
const SLOTS = Object.freeze({short_morning: '05:30:00Z', long: '10:30:00Z', short_evening: '15:00:00Z'});
const VID = /^[A-Za-z0-9_-]{11}$/;
const EP = /^fm_\d{8}_(?:short|long)_(?:en|hi)$/;
const HASH = /^[a-f0-9]{64}$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
const STAGES = new Set(['PLANNED', 'RESEARCH_VERIFIED', 'SCRIPT_VERIFIED', 'MEDIA_QA_PASSED',
  'UPLOAD_STARTED', 'REMOTE_PRIVATE_VERIFIED', 'SCHEDULED_VERIFIED', 'PUBLIC_VERIFIED',
  'RENDERING', 'SCHEDULING_UNRESOLVED']);
function exactObject(obj, fields) {
  return obj !== null && typeof obj === 'object' && !Array.isArray(obj) &&
    Object.getPrototypeOf(obj) === Object.prototype &&
    Object.keys(obj).sort().join('|') === fields.slice().sort().join('|');
}
function canonicalDay(value) {
  if (typeof value !== 'string' || !DATE.test(value)) return false;
  const dt = new Date(value + 'T00:00:00Z');
  return !Number.isNaN(dt.getTime()) && dt.toISOString().slice(0, 10) === value;
}
const slotTime = (day, slot) => day + 'T' + SLOTS[slot];
function validManifest(manifest) {
  if (!exactObject(manifest, ['date', 'channel_id', 'slots']) ||
      manifest.channel_id !== CHANNEL || !canonicalDay(manifest.date) ||
      !exactObject(manifest.slots, Object.keys(SLOTS))) return false;
  const seenVideo = new Set(), seenEpisode = new Set();
  for (const slot of Object.keys(SLOTS)) {
    const item = manifest.slots[slot];
    if (!exactObject(item, ['episode_id', 'youtube_id', 'media_sha256', 'publish_at_utc']) ||
        typeof item.episode_id !== 'string' || !EP.test(item.episode_id) ||
        !item.episode_id.startsWith('fm_' + manifest.date.replaceAll('-', '') + '_') ||
        seenEpisode.has(item.episode_id) ||
        (slot === 'long') !== item.episode_id.includes('_long_') ||
        typeof item.media_sha256 !== 'string' || !HASH.test(item.media_sha256) ||
        item.publish_at_utc !== slotTime(manifest.date, slot)) return false;
    seenEpisode.add(item.episode_id);
    if (item.youtube_id !== null) {
      if (typeof item.youtube_id !== 'string' || !VID.test(item.youtube_id) ||
          seenVideo.has(item.youtube_id)) return false;
      seenVideo.add(item.youtube_id);
    }
  }
  return true;
}
function hold(code) {
  return {
    decision: 'HOLD_NO_PRODUCTION_AUTHORITY', reason_code: code,
    source_trust: 'SYNTHETIC_LOCAL_FIXTURE_ONLY',
    real_provider_readback: false, real_cloudflare_writes: 0,
    real_youtube_uploads: 0, real_schedule_writes: 0,
    reupload_authorized: false, retry_uncertain_upload: false,
    migration_authorized: false, backfill_authorized: false,
    cloud_autopilot_ready: false,
  };
}
function validateReply(reply, maxCount) {
  if (!reply || typeof reply !== 'object' || reply.success !== true ||
      reply.meta?.served_by_primary !== true || !Array.isArray(reply.results) ||
      reply.results.length > maxCount ||
      !reply.results.every(x => x && typeof x === 'object' &&
        !Array.isArray(x) && Object.getPrototypeOf(x) === Object.prototype)) return null;
  return reply.results;
}
function validRow(r, day) {
  if (!exactObject(r, ['release_date', 'episode_id', 'channel_id', 'slot_ist',
                       'publish_at_utc', 'state', 'media_sha256', 'youtube_id'])) return false;
  if (r.release_date !== day || r.channel_id !== CHANNEL ||
      typeof r.episode_id !== 'string' || !EP.test(r.episode_id) ||
      !r.episode_id.startsWith('fm_' + day.replaceAll('-', '') + '_') ||
      typeof r.slot_ist !== 'string' || !Object.hasOwn(SLOTS, r.slot_ist) ||
      typeof r.state !== 'string' || !STAGES.has(r.state)) return false;
  return (r.publish_at_utc === null || r.publish_at_utc === slotTime(day, r.slot_ist)) &&
    (r.media_sha256 === null || typeof r.media_sha256 === 'string' && HASH.test(r.media_sha256)) &&
    (r.youtube_id === null || typeof r.youtube_id === 'string' && VID.test(r.youtube_id));
}
function validEvent(e, day) {
  return exactObject(e, ['episode_id', 'event_kind', 'at_utc']) &&
    typeof e.episode_id === 'string' && EP.test(e.episode_id) &&
    e.episode_id.startsWith('fm_' + day.replaceAll('-', '') + '_') &&
    typeof e.event_kind === 'string' && /^[A-Z_]{1,48}$/.test(e.event_kind) &&
    typeof e.at_utc === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(e.at_utc);
}
function compare(manifest, rows, events) {
  if (!rows.every(r => validRow(r, manifest.date)) ||
      !events.every(e => validEvent(e, manifest.date))) return hold('MALFORMED_CANONICAL_ROW');
  if (rows.length === 16 || events.length === 100) return hold('TRUNCATED_CANONICAL_RESULT');
  const dbEpisodes = new Set(), dbVideoIds = new Set(), dbSlots = new Set();
  for (const row of rows) {
    if (dbEpisodes.has(row.episode_id)) return hold('DUPLICATE_CANONICAL_EPISODE');
    if (dbSlots.has(row.slot_ist)) return hold('DUPLICATE_CANONICAL_SLOT');
    if (row.youtube_id !== null && dbVideoIds.has(row.youtube_id)) return hold('DUPLICATE_VIDEO_ID');
    dbEpisodes.add(row.episode_id); dbSlots.add(row.slot_ist);
    if (row.youtube_id !== null) dbVideoIds.add(row.youtube_id);
  }
  if (events.some(e => !dbEpisodes.has(e.episode_id))) return hold('ORPHAN_RELEASE_EVENT');
  const lanes = {};
  let gaps = 0, conflicts = 0, unknown = 0;
  for (const slot of Object.keys(SLOTS)) {
    const planned = manifest.slots[slot];
    const found = rows.find(r => r.slot_ist === slot);
    if (!found) {
      lanes[slot] = 'CANONICAL_ROW_MISSING'; gaps++;
    } else if (found.episode_id !== planned.episode_id ||
               found.youtube_id !== planned.youtube_id ||
               found.media_sha256 !== planned.media_sha256 ||
               found.publish_at_utc !== planned.publish_at_utc) {
      lanes[slot] = 'IMMUTABLE_RECEIPT_CONFLICT'; conflicts++;
    } else if (found.state !== 'SCHEDULED_VERIFIED' && found.state !== 'PUBLIC_VERIFIED') {
      lanes[slot] = 'STATE_OR_REMOTE_ACK_UNCERTAIN_NO_RETRY'; unknown++;
    } else {
      lanes[slot] = 'CANONICAL_MATCH_UNATTESTED';
    }
  }
  return {...hold('CANONICAL_CONSISTENCY_IS_NOT_PUBLISH_AUTHORITY'),
    rows_checked: rows.length, events_checked: events.length,
    missing_lanes: gaps, conflicting_lanes: conflicts, uncertain_lanes: unknown,
    lanes};
}
export async function syntheticReadback(db, manifest) {
  if (LIVE_D1_ENABLED !== false || !db || typeof db !== 'object' ||
      !Object.hasOwn(db, '__flowminuteSyntheticD1') ||
      db.__flowminuteSyntheticD1 !== true || typeof db.prepare !== 'function')
    return hold('LIVE_BINDING_REJECTED');
  if (!validManifest(manifest)) return hold('INVALID_RELEASE_MANIFEST');
  try {
    const releaseReply = await db.prepare(CANONICAL_SELECT.releases).bind(manifest.date).all();
    const rows = validateReply(releaseReply, 16);
    if (rows === null) return hold('CANONICAL_READ_RECEIPT_UNKNOWN');
    const eventReply = await db.prepare(CANONICAL_SELECT.events).bind(manifest.date).all();
    const events = validateReply(eventReply, 100);
    if (events === null) return hold('EVENT_READ_RECEIPT_UNKNOWN');
    return compare(manifest, rows, events);
  } catch {
    return hold('D1_UNKNOWN_ERROR_HOLD');
  }
}
