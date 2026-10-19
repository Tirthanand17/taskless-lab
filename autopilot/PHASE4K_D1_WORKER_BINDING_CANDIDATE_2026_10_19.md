# Phase 4K — deployment-disabled Cloudflare D1 Worker binding candidate

19 October 2026 | PUBLIC draft PR #5 | no live service or cloud mutations

## What is new

Phase 4J previously proved three fixed conditional UPDATE operations only in a SQLite simulation. Phase 4K introduces autopilot/cloud_d1_worker_candidate.mjs, a genuine JavaScript ESM module calling Cloudflare-style D1 prepared statement interfaces (prepare, bind, run) and checking the returned D1Result metadata. It is NOT deployed and has NO Worker fetch or scheduled entrypoint, no Wrangler binding/migration, no Google API, no OAuth, no file write, and no production token.

LIVE_CLOUDFLARE_WRITES_ENABLED is hardcoded FALSE. The module refuses a normal Cloudflare binding, only using adapters carrying the explicit synthetic test marker. That marker is a test convention, not identity or deployment authority.

Constant parameterized SQL uses server-side SQLite unixepoch('now') for the claim/renew/reserve time checks. It does not accept client-supplied timestamps. Claims require the expected fence epoch and no currently live lease. Renewals require the exact active nonce/epoch and unexpired lease. Reservations require media_qa_passed, exact release date, episode/media digest and unexpired exact lease. A second upload reservation is refused. This cannot fence the Google videos.insert HTTP side effect or make a lost upload ACK safe to retry.

Success requires D1Result.success TRUE, meta.served_by_primary TRUE, meta.changed_db TRUE, changes exactly one, rows_written exactly one, a single attempt when total_attempts is reported, and empty UPDATE results. Missing primary/change proof, malformed metadata, quota errors, timeouts or thrown exceptions return sanitized HOLD with no raw details.

## Validation split

1. autopilot/test_cloud_d1_worker_candidate.mjs uses Node's real built-in test runner to exercise prepare/bind/run and adversarial/forged return metadata. A Python unittest in autopilot/test_cloud_d1_worker_node_bridge.py invokes those Node tests in public GitHub CI, skipping rather than falsely passing if Node is absent.
2. autopilot/test_cloud_d1_worker_sqlite_compat.py independently reconstructs the exact SQL from the JS source and executes it with in-memory SQLite tables. Claim, expiry, owner renewal, media/hash verification, stale nonce and duplicate reservation are validated. This is an independent SQL parsing and state-change test; still not a real Cloudflare D1 runtime.

## Provider references

- Cloudflare D1 Workers API and prepared statements: https://developers.cloudflare.com/d1/worker-api/ and https://developers.cloudflare.com/d1/worker-api/prepared-statements/
- D1Result metadata including primary/changes/writes/attempt count: https://developers.cloudflare.com/d1/worker-api/return-object/
- Cloudflare Workers Free limits and Cron: https://developers.cloudflare.com/workers/platform/limits/
- D1 storage/free quotas: https://developers.cloudflare.com/d1/platform/limits/ and https://developers.cloudflare.com/d1/platform/pricing/

## Production gate remains CLOSED

No real Cloudflare D1 schema migration, Worker deployment, D1 account inspection, backup/restore, lease, primary CAS query, Google upload, OAuth persistence, analytics or licensed media production was performed. Cloudflare Workers limits and verified ₹0 account quota remain open issues. In particular, no on-disk/mounted private ledger or owner channel was accessed.

A real videos.insert can succeed even when its HTTP response is lost. The upload_started row must remain quarantined and MUST NEVER be auto retried merely because an epoch or lease expires. Real cloud provider identity, owner approval, clock/race semantics, writer exclusion and restore/rollback remain mandatory independent acceptance criteria before any deploy.

The public and private repositories' PR #5 remain DRAFT/unmerged. User constraints: INR 0 monthly cost, no Nirala laptop without separate permission, no new provider connection or paid service, and no publishing without authorization. The 21 real production acceptance subphases across six unfinished major phases remain OPEN; estimated software implementation 45%, live autonomous readiness 20%, unchanged.
