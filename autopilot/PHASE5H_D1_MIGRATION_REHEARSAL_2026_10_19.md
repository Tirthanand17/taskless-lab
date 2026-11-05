# FlowMinute Phase 5H — Canonical D1 recovery and uniqueness migration rehearsal

**19 October 2026. Software rehearsal COMPLETED, production migration NOT AUTHORIZED.** This source remains in existing **DRAFT PR #5**. User instruction: ₹0 new charges, GitHub primary, Nirala files only under `youtube con`, no live D1 writes, no credential transfer.

## Baseline actually observed in Cloudflare during Phase 5E/5F

- Existing D1 `flowminute-controller-free` bound as `DB` to the existing owner Worker.
- Real canonical `releases`: `release_date`, `episode_id`, `channel_id`, `slot_ist`, `publish_at_utc`, `state`, `media_sha256`, `youtube_id`, `updated_at_utc`.
- Real `release_events`: `id`, `release_date`, `episode_id`, `event_kind`, `detail_json`, `at_utc`.
- Verified `releases` primary key `(release_date,episode_id)` and unique `youtube_id`; observed `idx_release_date_slot` is **nonunique**. Date/time slot uniqueness is **not** enforced by that index.
- Read-only counts at the inspection were **zero canonical release rows and zero event rows**; separate historical `youtube_release_observations` rows were stale and were NOT owner API evidence for October 20.
- Owner-approved YouTube API checks already yielded three scheduled October 20 video receipts (two Shorts, one long). Real video IDs, media digests and titles remain in private release-watch and local publisher, not public test fixtures.

## Implementation

`autopilot/phase5h_d1_migration_rehearsal.py` and `autopilot/test_phase5h_d1_migration_rehearsal.py`:

1. Only **synthetic, sanitized caller metadata** can be passed; inputs are never promoted to live provider attestation. Fixed exact channel, three slots (11:00, 16:00, 20:30 IST), unique episode IDs, distinct 11-character video IDs, lower-case SHA-256 metadata, correct date/slot UTC times, Private/processed/succeeded owner claims and bounded observation freshness.
2. Validates the observed D1 schema/index list and zero counts before starting the isolated rehearsal; refuses any schema drift, nonzero canonical records or untrusted/secret-bearing input fields.
3. Creates a **new in-memory SQLite connection only**. It reconstructs the observed `releases` / `release_events` keys and then rehearses the proposed unique `(release_date,slot_ist)` index, three parameterized inserts, and three append-only synthetic event records inside an SQLite transaction.
4. Tests that a **fourth, different episode ID** claiming the same date/slot is blocked by the *new slot index*, not by the existing episode primary key.
5. Injects faults before index creation, after first insert and before commit, then verifies full rollback of simulated indexes, releases and events. No real D1 database is accessed.
6. Output is a **safe aggregate-only report**. Never returns title, SHA, private video ID, raw receipt or owner OAuth data. Flags for live D1 writes, YouTube uploads, scheduling, owner authentication, real provider backup verification and production readiness always remain **false**.
7. `python -m unittest autopilot.test_phase5h_d1_migration_rehearsal -v`: **28 passed, 0 failed** on authorized Nirala in `C:\Users\Dell\Desktop\youtube con\phase5h-acceptance`, tested against commit `1412c0c06f4da8fd805b9494b3f8465084e69180` (the source was last edited at `2a977688`). No real secrets or videos processed.

## Future production migration protocol (NOT EXECUTED)

**Gate A — evidence refresh:** Independently read live D1 schema, all constraint/index identities, duplicate-slot aggregates and release/event row counts again, and read back each immutable YouTube receipt using approved channel-scoped OAuth. Stop on any drift or uncertainty. Demand complete private metadata/provenance and verified media hashes; partial snapshot is insufficient.

**Gate B — safe recovery window:** Freeze any existing production writer before considering migration. Verify Cloudflare database storage subsystem/version, the exact native Time Travel bookmark supported by the plan, and a separate recovery option. Cloudflare documents D1 Time Travel, with a **7-day retention on Free**; a global restore overwrites the database in place and could undo unrelated updates. Do **not** treat an automatic historical bookmark as a tested surgical rollback. No `restore` API call has been made.

**Gate C — uniqueness transition:** Independently audit existing `(release_date,slot_ist)` conflicts. In a separately approved migration, a unique index may be added only with a verified clean schema and a single active writer. The existing `youtube_id` uniqueness and `(release_date,episode_id)` primary key must be preserved. The in-memory index is **not** a D1 migration script and did not establish production fencing or distributed idempotency.

**Gate D — atomic publication metadata:** Staging must use the provider's actual D1 API and bound parameterized statements, not Python `BEGIN IMMEDIATE` code moved into a Worker. Cloudflare says `D1Database.batch([...])` executes prepared statements sequentially as an atomic transaction, rolling back the batch if one statement fails. Production write semantics, lifecycle/lease fencing, durable pre-insert reservation and event-history checks must be implemented and reviewed before any authorized backfill. External YouTube API uploads and D1 transactions **cannot** be committed atomically together; remote reconciliation remains mandatory.

**Gate E — replay/rollback signoff:** Rehearse failure injection against a non-production clone or local fixture and test D1-compatible batch behavior, versioned migration, index and backup recovery. Store production backup bookmarks or sensitive release metadata only in the owner's private protected environment. Require a **separate explicit authorization** to perform production D1 writes or a destructive rollback.

## Out-of-scope blockers

No proven global ₹0 no-overage protection; no complete rights/captions review; no durable private cloud media; no managed renewable Google OAuth grant; no owner-approved cloud publisher Worker; no D1 single-writer fenced CAS; no live production backfill or index migration.

**Scope acceptance:** Phase 5H is complete as **a tested offline migration-and-rollback rehearsal**. **Major Phase 5 remains incomplete; overall 2/8 major phases = 25%**. Original 21 production acceptance obligations are not silently decremented.

Official provider references for future review:
- https://developers.cloudflare.com/d1/worker-api/d1-database/
- https://developers.cloudflare.com/d1/reference/time-travel/
- https://developers.cloudflare.com/d1/reference/migrations/
