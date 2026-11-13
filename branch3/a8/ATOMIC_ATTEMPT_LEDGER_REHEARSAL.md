# CLIVOX A8 — Transactional upload-attempt ledger REHEARSAL

**2026-11-13:** This adds real SQLite transactions and database uniqueness constraints **inside one temporary GitHub Actions runner**. It is an engineering safety test only. There is **no durable shared ledger across runs**, real upload attempt, licensed footage, owner-signed production release, uploader OAuth or live YouTube readback.

## Why this matters

The existing A8 dry run uses an in-memory list to preview idempotency keys. Two independent jobs could both check that list and then upload duplicates. A network error is similarly ambiguous: YouTube might accept an upload even if a client never receives a success response.

This milestone now exercises an **actual on-disk SQLite database** with transaction-level locking (`BEGIN IMMEDIATE`), a unique exact-attempt hash, unique release ID and unique exact video digest. Parallel thread tests prove that just one contender can reserve the same release (or the same media under a different release ID) **on the same SQLite database file**.

A reservation transitions monotonically from `RESERVED_NO_NETWORK` to `UNKNOWN_REMOTE_NO_RETRY`. Duplicate reservation, multiple transitions, missing rows, invalid state, wrong channel, malformed timestamps or tampered DB identity all block. The system has **no state or code path that uploads, retries an ambiguous action, claims a remote video ID or schedules publication**.

## Files

- `scripts/branch3_a8_attempt_ledger.py`: SQLite transaction-based, checked single-file reservation, ambiguous-state transition and no-retry inspection; `perform_production_upload` always denies.
- `scripts/test_branch3_a8_attempt_ledger.py`: adversarial tests with concurrent threads and strict DB constraints; no real media, API or upload.
- `.github/workflows/branch3-clivox-a8-atomic-ledger-qa.yml`: read-only CI on GitHub-managed Ubuntu runners, runs both the new atomic tests and existing A8 dry run.
- Existing `scripts/branch3_a8_private_first_dryrun.py` and its archived empty ledger fixture remain strict quarantine checks and are **not** modified to claim a durable controller.

## Critical distinction: local atomicity is NOT distributed durability

SQLite on one GitHub Actions runner provides real atomic transactions **only among processes sharing the same file**. A second runner will have a different file. Jobs are ephemeral, and the CLI deletes its test directory. GitHub workflow `concurrency` is **not** a full distributed, durable idempotency mechanism.

Do **not** copy this local DB into the public repository or interpret a green QA suite as permission to upload. No real remote inventory was queried, and a synthetic hash/SQLite row cannot validate copyright or A6 owner release.

## Next production gates (NOT implemented)

1. Authenticate genuine creator commercial reuse rights, private media storage, final exact asset and the owner's A6 signature.
2. Establish a **private, durable cross-run transaction store** with atomic unique reservations, crash recovery, encrypted credentials and reliable independent backup. Review rollback/restore behavior, rate limits and auditing before activation.
3. Integrate a separate protected CLIVOX OAuth uploader with a pre-network atomic reservation, single resumable-upload attempt, non-sensitive session state and reliable remote identity checks.
4. On timeout/unknown HTTP state, hold the reservation and require independently authenticated CLIVOX remote inventory reconciliation. Never blind-retry after an ambiguous upload.
5. Require processing/Content ID review, private-first upload and owner-approved UTC scheduling, with remote readback of exact asset/schedule before success is recorded.
6. Implement owner-authorized manual recovery and takedown paths, and confirm that revocation events invalidate pending actions.

**Actual state:** 0 creator licenses, 0 uploads, private vault not provisioned, no production signing key or Clivox upload OAuth. A9 licensed pilot 0%. Branches 1 and 2 untouched.
