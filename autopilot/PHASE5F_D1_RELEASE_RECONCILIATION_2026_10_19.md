# Phase 5F: release-ledger reconciliation dry-run (19 October 2026)

**Status: Source-only candidate, NOT a production backfill or migration.** Continue to use the existing D1 `releases` and `release_events` tables. This reconciliation code has no network, database, OAuth, Google API or YouTube mutation capabilities.

## Read-only live baseline (owner dashboard, Nirala)

Cloudflare `flowminute-controller-free` SQL console executed SELECT COUNT queries only. Aggregates:

| Table | Actual count |
| --- | ---: |
| `releases` | 0 |
| `release_events` | 0 |
| `youtube_release_observations` | 3 |
| `audit_heartbeats` | 4 |

The observation table is keyed by `(release_date, slot_ist)`. Its three existing rows refer to **2026-10-19**, include two `SCHEDULED_OBSERVED` statuses (long, evening) and one `PUBLIC_OBSERVED` (morning), with `api_rechecked_at_utc IS NULL` in all three. They were sourced from previously verified October 16 metadata, **not an independent new October 19 Google API owner recheck**. No row has been read out containing YouTube IDs, credentials, media hashes, private thumbnails, encrypted strings, event JSON or user data.

The private GitHub `flowminute-control-private/state/release-watch/2026-10-20.json` previously recorded two YouTube Shorts with actual remote video IDs and a Hindi long video still rendering. The direct YouTube schedule receipts were verified earlier; this phase did **not** repeat owner API readback or verify the long video was scheduled. **D1 contains zero release rows for those episodes**.

## Software integration

- `autopilot/phase5f_release_reconciliation.py` accepts a deliberately bounded sanitized private per-date snapshot with exactly three external episode slots, non-sensitive D1 row and event counts, and optional read-only D1 row identifiers supplied privately. It never reads a database or makes requests.
- Rejects incomplete D1 snapshots, wrong channel/day, duplicate video IDs or slot claims, conflicting immutable IDs, incorrect local-to-UTC schedule, unguarded `UPLOAD_STARTED`, stale observations, impossible input and extra credential fields.
- Returns safe per-slot discrepancies and **`BLOCKED_LEDGER_DIVERGENCE`** when canonical D1 rows are absent. Suppresses private episode IDs, raw YouTube video IDs, media digests, response bodies and secrets.
- Output **always** sets `automatic_backfill_authorized=false`, `automatic_upload_retry_authorized=false`, `canonical_ledger_write_authorized=false`, `cloud_autopilot_ready=false`, and `migration_sql_generated=[]`. Even all synthetic data matching is `CONSISTENT_UNATTESTED_NO_WRITE`, never evidence of live owner verification.
- Offline tests: `python -m unittest autopilot.test_phase5f_release_reconciliation -v`. Validated scenarios include live 0/0/3/4 aggregates, two Shorts with IDs outside D1, a missing long, duplicate slots/video IDs, replay uncertainty, mismatched schedules, injected secret fields and no false permissions.

## Blockers after this no-write scope

- Need separately authorized reconciliation/backfill review of the two known remote IDs against the live authenticated owner API, and durable reservation of planned day/slot without creating duplicate videos. **Never auto-insert to production D1 based on a GitHub JSON or stale observation.**
- Existing `idx_release_date_slot` is **not unique**; D1 has UNIQUE `youtube_id` and composite primary key `(release_date,episode_id)`, but no verified global one-slot uniqueness or fenced CAS. Migration and backup/rollback remain separate owner approval.
- No real renewable cloud OAuth credential, no durable private cloud media with hard ₹0 non-overage assurance and no cloud publisher deployment. Live production autopilot remains off.

**Milestone accounting remains 2/8 accepted major phases = 25%.** Scope-specific Phase 5F inventory/dry-run completion does not constitute major Phase 5 approval. The original 21 production acceptance obligations stay open until individually mapped.
