# Phase 4G.4 — SQLite-clock guarded local and uncertain-intent transitions

18 Oct 2026. Source-only, DRAFT PR #4, not a deployed D1 writer.

The previous Phase 4G.3 database-clock claim was incomplete: older local_step, begin_upload_once and begin_schedule_once used caller-chosen UTC. The new methods in the existing Phase 4A OFFLINE SIMULATOR close that reference gap without introducing a second ledger.

The internal _db_clock_fenced_mutation starts a SQLite BEGIN IMMEDIATE transaction; selects UTC seconds from the same database connection; performs a conditional UPDATE with exact channel, episode, expected stage/version, owner, fence and lease_until > database time; and appends an event before commit. No request supplies now_utc.

local_step_db_clock_rehearsal allows only ordered research/script/media QA stages. Its media review digest is only a claimed byte binding, not lawful/creative review. begin_upload_intent_db_clock_rehearsal reserves a SIMULATED upload intent in upload_uncertain, never sends a request. begin_schedule_intent_db_clock_rehearsal simulates schedule_uncertain only after a caller-claimed remote private readback; caller-authenticated booleans have no production evidentiary value. Both intent paths forbid blind repeats.

The real SQLite regression tests cover legitimate transitions, stale/expired lease, wrong worker/fence/version, forged client time, QA/hash constraints, duplicate intents, simulated crash/reclaim and two competing SQLite connections; the existing Phase 4G read-only audit must accept the event chain while continuing to deny network/public authority.

LIMITATIONS: SQLite runner wall clock is not validated Cloudflare server clock; no production D1 binding, no actual migration, and no real channel-owner readback. Older test-only APIs accepting now_utc and caller booleans remain in the simulator. This new code is NOT permission to make any external call.

4E live read-only evidence, 4F backed-up real migration and 4G deployed authenticated writer remain OPEN. 21 production acceptance subphases across six unfinished major phases remain. No Nirala/laptop, account/provider connection, OAuth, D1 write, YouTube upload/schedule/publish or paid services. Budget ₹0 recurring/month.
