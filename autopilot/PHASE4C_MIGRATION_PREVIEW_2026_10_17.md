# FlowMinute Lab — Phase 4C offline migration preview (17 October 2026)

**Safety status:** offline software only; no live Cloudflare D1 query, D1 migration, Google/YouTube access, upload, schedule change, charge, personal computer access, or new service connection.

## Why this is the next step

Previous project phases proved a simulated single-writer state machine and a read-only schema/conflict-check interface:

- Phase 4A: `phase4_offline_ledger.py` models fenced single-writer transitions, immutable media/video receipts and no blind upload retry. It is **NOT** the deployed writer.
- Phase 4B: `phase4b_readonly_audit.py` inspects **only disposable local SQLite schema**, redacts sensitive grant/token structures, and reports contradictory metadata. It **does not** inspect real Cloudflare D1 or issue authorized YouTube video readbacks.
- Phase 4C: `phase4c_migration_preview.py` creates a deterministic, no-SQL, no-write *review preview* for future operator-supplied sanitized metadata claims. There is **NO trusted live evidence yet**.

## Phase 4C protections

1. Map a claimed legacy private SQLite `release_date + episode_id` to an exact release timestamp only when a claimed UTC `planned_utc` exists. Compare release date to the **Asia/Kolkata calendar day**; do not guess 11:00/16:00/20:30 scheduling.
2. Detect mismatches across private SQLite, public draft, D1 and YouTube *claimed* records, including media hash, scheduled UTC instant, remote YouTube ID, legacy calendar day, or stage divergence.
3. Flag an ambiguous `upload_started`, `upload_uncertain`, `schedule_uncertain` or `schedule_unresolved` for reconciliation; never interpret these states as retry authorization.
4. If two episodes claim the same video ID or schedule instant, both are flagged; a missing video ID in a remote stage cannot be silently backfilled.
5. Never treat the caller's `source="youtube_claim"` / `source="d1_claim"` strings as credentials, signatures, owner identity or independent remote verification. Even perfectly aligned inputs remain **UNVERIFIED_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW**.
6. Prevent the preview from being applied directly: `generated_sql=[]`, `database_mutations=0`, `network_calls=0`, `production_migration_ready=false`, `production_upload_ready=false`, `production_schedule_ready=false`.
7. Produce a deterministic SHA-256 fingerprint for comparing two **offline candidate previews**, not as proof of live freshness or signatures. Ignore unrelated input keys; credentials MUST NOT be supplied to this tool.

## Test gate

- `autopilot/test_phase4c_migration_preview.py`: 24 intended regression cases covering empty and conflicting claims, legacy release dates, IST day rollover, remote ambiguity, unauthorized claimed identity, hash/ID/time collision, output secrecy, deterministic fingerprint and no-write status.
- The main GitHub `Content Quality Gate` runs repository pytest with these additions. The exact completed run and count must be verified before reporting a pass.

## Next live checkpoint remains blocked

**No Cloudflare connection available in this ChatGPT session.** To inspect the actual deployed D1, use only an independently authorized provider-supported read-only path; any new Cloudflare connection or account/permission change still requires explicit owner approval.

Only then:

1. Read live D1 table/index **metadata only**, never `SELECT *` from encrypted OAuth or grant tables and never publish raw secrets.
2. Authenticated YouTube readback of exact channel `UCCcL9Q_jqVq6LJmnYUSAFZA` and historical video IDs, processing status, privacy and exact UTC schedule.
3. Reconcile old private SQLite/Cloudflare/public draft rows. Mark unknown/mismatched entries quarantined, not published.
4. Draft a schema-specific, reversible one-time D1 migration after backups; do not copy reference SQLite transaction syntax blindly.
5. Explicit owner approval before D1 writes and a **separate** private upload pilot with durable OAuth/media storage/rights/fact checks.

Cloudflare D1 `batch()` is documented to run a transactional batch with rollback on statement failure, but production safety also requires correct expected-version predicates, fencing and trusted clocks; a batch alone does not prove safe exactly-once external YouTube effects.

Official sources:
- https://developers.cloudflare.com/d1/worker-api/d1-database/
- https://developers.cloudflare.com/d1/sql-api/sql-statements/
- https://developers.cloudflare.com/changelog/post/2026-09-01-d1-free-tier-limit-enforcement/
- https://developers.cloudflare.com/d1/platform/pricing/

**Operating limits remain:** ₹0/month, cloud-only, no Nirala/laptop access, no new paid service, no publishing/scheduling/OAuth scope changes. Keep PR in DRAFT until real provider reconciliation and sign-off.
