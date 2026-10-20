# Phase 4J — D1-shaped CAS writer lease and pre-upload reservation

19 October 2026 | public DRAFT PR #5 | OFFLINE SQLite model ONLY

## Verified provider facts

- D1 processes queries against a single database one at a time, making one conditional UPDATE preferable to an unguarded read-then-write lock. Source: https://developers.cloudflare.com/d1/platform/limits/
- D1 Workers prepared statements accept bound parameters and their run() results contain success and metadata such as changes and rows_written. https://developers.cloudflare.com/d1/worker-api/prepared-statements/ and https://developers.cloudflare.com/d1/worker-api/return-object/
- D1 batch transactions provide atomic SQL batches. First-primary sessions enable current primary-based sequential reads but DO NOT atomically commit the external YouTube API. https://developers.cloudflare.com/d1/worker-api/d1-database/ and https://developers.cloudflare.com/d1/best-practices/read-replication/
- From September 1, 2026, Workers Free D1 daily read/write row limits are enforced by query failures until midnight UTC. Any quota error while reserving an upload must block publication and require review rather than permit an unfenced upload. https://developers.cloudflare.com/changelog/post/2026-09-01-d1-free-tier-limit-enforcement/
- Documented Workers Free: 5 million D1 rows read per day, 100,000 written per day, 5 GB per-account storage, 500 MB per database, 50 D1 query subrequests per invocation. This is public documentation, NOT evidence of remaining quota or the owner's account tier. https://developers.cloudflare.com/d1/platform/pricing/ and https://developers.cloudflare.com/d1/platform/limits/

## Code

autopilot/cloud_d1_cas_lease_design.py contains fixed parameterized UPDATE statement constants and a local SQLite-memory model:
1. CLAIM_SQL updates one synthetic lease row only when the expected fence epoch, expiration and monotonic-clock predicates match. It increments the epoch exactly once. Wrong epochs, competing owners, unexpired leases and zero affected rows fail.
2. RENEW_SQL extends an unexpired lease only for the exact current owner nonce and fence epoch. Expired/stolen ownership cannot be revived.
3. RESERVE_UPLOAD_SQL atomically changes ONE local shadow release from media_qa_passed to upload_started ONLY if its media SHA matches and an unexpired exact owner/epoch lease exists. Repeated reservation is denied. This reserves local state; it NEVER calls Google.

No D1 account, schema migration, filesystem, real provider connection or HTTP was used. Both test connections are ephemeral SQLite shared-memory connections. No real Cloudflare CAS receipt, D1 primary/race, lease clock, network partition, backend transport or cross-service semantics were verified.

autopilot/test_cloud_d1_cas_lease_design.py contains 11 synthetic tests for competing claims, stale epochs, owner-only renewal, reservation race, duplicate prevention, media mismatch, clock bounds, malformed nonces, constant SQL and RAM-only connections. Exact code checkpoint 705462b4fbb0dd8066ac10b57c7e6f588d9b1550 has public CI 950 passed, 2 skipped and 639 subtests passed.

## Production blockers

The actual private ledger does NOT have a production D1 lease table. No database migration, real lease, cloud writer, deploy, publishing, live Cloudflare binding, owner OAuth scope or backup is authorized.

The model uses a caller-supplied integer tick. Real Workers must prove a trusted timebase, correct stale-worker fencing through partitions/restarts, multi-region source consistency and secure transfer of claims. Even an atomic D1 release reservation CANNOT fence an external YouTube videos.insert call or tell whether a timeout means a remote upload succeeded. An upload_started with missing remote ACK is ALWAYS operator-held; never automatically repeat it after lease expiry.

The companion private DRAFT branch has dormant control/phase4j_private_d1_cas_preflight.py validating the public model's no-production-permission output, with 8 private mock tests committed but NOT run due private Actions quota restriction. Public CI does not cover private code. Independent D1 schema, quota, data backup/restore, source authentication and writer deployment evidence are mandatory before live use.

All 21 production acceptance subphases across six unfinished phases remain OPEN. Software ~45% / actual autonomous readiness ~20% subjective estimates unchanged. No laptop/Nirala, provider connection, production D1 mutation, OAuth action, YouTube upload, scheduling, paid resource or publish; INR 0 monthly authorization respected. Both PRs remain DRAFT/unmerged.
