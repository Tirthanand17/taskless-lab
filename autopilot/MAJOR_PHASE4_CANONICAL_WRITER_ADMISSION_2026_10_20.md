# Major Phase 4 — canonical D1 single-use upload reservation

**20 Oct 2026 | Existing draft PR #5 | NOT deployed | No production writes.**

This component addresses the fundamental at-most-once publishing problem. The live canonical database has `releases` and `release_events`, `UNIQUE(youtube_id)` and a primary key of `(release_date,episode_id)`, but the live `idx_release_date_slot` is **nonunique**. Two distinct episodes can claim the same publication slot unless a new constraint is approved and migrated. Repeating the old shadow-table writer from `cloud_d1_worker_candidate.mjs` would fail because its lease/shadow tables do not exist.

## Prototype decision
- New source: `autopilot/phase4_canonical_writer_admission.py`, synthetic tests `autopilot/test_phase4_canonical_writer_admission.py`. The module **only creates disposable in-memory SQLite**; it cannot access real Cloudflare, GitHub, YouTube or OAuth and has no deployable Worker entrypoint.
- It requires a verified **unique composite date/slot index**, confirmed from SQLite index metadata, before any admission can occur. It does not confuse existing unique YouTube IDs with date/slot uniqueness.
- Under a single SQLite transaction it compare-and-sets `MEDIA_QA_PASSED -> UPLOAD_STARTED` for one immutable channel/episode/date/UTC time/media SHA-256 and appends a bounded simulated event. Another attempt is rejected, including after unknown upload acknowledgement or scheduling ambiguity. An interrupted local transaction rolls back state **and** event.
- It never performs `videos.insert`. A successful simulated reservation is **not** proof that a remote upload occurred or that retry is safe. Without a verified reservation index, missing/mismatched source identity or an unresolved remote upload, the result is HOLD.
- It does not implement a renewable lease or multi-Worker fencing; after an uncertain cloud-side reservation a human-reviewed YouTube owner recheck must resolve the remote ID. A durable writer epoch/single active Worker must still be proven in the real Cloudflare production design.

## Real production acceptance still blocked
1. Independently verify recoverable D1 backup and safe disposable restore, plus global ₹0 budget and all Worker triggers/routes.
2. Review `UNIQUE(release_date,slot_ist)` against **all existing canonical data**, then obtain explicit owner production migration/index/backfill approval before any schema/data change. No index applied here.
3. Implement D1-native prepared statements and atomic `batch()` with a provable single-writer/remote-ack policy. SQLite `BEGIN IMMEDIATE` is **not** portable into D1 Worker bindings; D1 `batch` transactions cover D1 SQL only, not YouTube network side effects.
4. Verify renewable cloud OAuth custody, safe media rights/QA, a single bounded private pilot with owner approval, then test actual end-to-end consistency with Nirala OFF.

Official Cloudflare documentation: https://developers.cloudflare.com/d1/worker-api/d1-database/ and https://developers.cloudflare.com/d1/worker-api/prepared-statements/.

**Major Phase 4/5 status:** in progress. This source/test milestone alone does not change accepted major phases (2/8 = 25%).