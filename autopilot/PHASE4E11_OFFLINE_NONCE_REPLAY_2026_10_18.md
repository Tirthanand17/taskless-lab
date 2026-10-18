# FlowMinute Phase 4E.11 — offline memory-only nonce replay rehearsal

18 October 2026. **Research/testing only**, on public DRAFT PR #4. NOT a live Cloudflare D1 database, durable replay store, provider credential or approval to publish.

## Why

The existing Phase 4D + Phase 4E.2 chain verifies bounded Ed25519 receipts from two distinct caller-pinned keys, exact sanitized SHA-256 payload hashes, signed claimed UTC times and one request nonce. It accepts a supplied `already_seen_nonces` set but never persists it. A process restart or two independent verifiers can therefore each accept a repeated bundle.

## New implementation

`autopilot/phase4e11_offline_nonce_replay.py` wraps the **existing** `inspect_signed_sanitized_phase4e_snapshots` validator, without rewriting validation or adding a new ledger. It only accepts SQLite with a single, truly **in-memory** main database (or shared memory URI). File-backed or attached databases are rejected. Setup makes one disposable UNIQUE primary key table of **purpose-separated SHA256 nonce hashes**, at most 256 observations.

Each attempt uses `BEGIN IMMEDIATE`: look up the digest, refuse replay, check the bounded capacity, call the existing signed-snapshot verifier, INSERT the digest, COMMIT, and return exactly the original untrusted report. Invalid signatures, wrong channel/metadata, invalid nonce, already used hash or transaction failures roll back and do not consume a new nonce. The in-memory single-use guarantee only applies while that SQLite memory database exists. Lock acquisition errors do not grant approval.

Synthetic regression cases exercise first-use/replay rejection, invalid-signature recovery, hostile extra-field rejection, two separately signed request nonces, two shared-memory connections, active transaction/attached database refusal, malformed nonces, injected insert failure rollback and **successful replay after in-memory database shutdown**. That last test deliberately documents the missing *durable* protection.

## Boundaries

- **Do not deploy as the actual production nonce registry**. Durable unique keys across restarts, rotation/revocation, genuine provider origin, trusted timing, authenticated live D1/YouTube read-only inspection, and privacy-preserving reconciliation remain unresolved.
- Input snapshot channel labels and caller-enrolled Ed25519 keys are not proof of remote service ownership. Attacker-controlled signatures can validate for invented keys.
- `database_writes=0` in the returned report refers to **production provider writes**; the local ephemeral test table itself gets one nonce-hash insertion. That distinction is intentional.
- No token, OAuth scope, private account read, remote D1 mutation, provider secret, real video ID/media, migration SQL, cloud production writer, upload, schedule, publish, paid resource or Nirala/laptop use.
- Both public and private PRs stay DRAFT/unmerged. ₹0 monthly recurring infrastructure budget. **21 production acceptance subphases remain** across six incomplete top-level phases.

The test and module use only Python standard-library SQLite plus the project's existing signature verification dependencies. No new workflow is needed; ordinary public draft PR CI validates them.


## Phase 4E.12 — fail-closed replay fixture invariants and production storage specification (18 October 2026)

**Bug/risk:** The 4E.11 simulator checked its table shape only during setup, did not prove the nonce row remained present after an INSERT, and passed through raw SQLite exceptions. A synthetic malicious `RAISE(IGNORE)` trigger can pretend a successful INSERT without storing a nonce; a delete-after-insert trigger can remove it. A caller could also replace/ALTER the memory-only table after initialization. These are meaningful test harness risks, **not** evidence that the deployed system has a durable replay registry.

**Changes:** Every single-use verification now checks the exact synthetic fixture schema and absence of triggers inside `BEGIN IMMEDIATE`, before the replay lookup; this includes the original TEXT, NOT NULL, PRIMARY KEY and fixed-length SHA-256 CHECK definition. It checks `INSERT` row count, presence of the specific purpose-separated digest and count increment by one **before** COMMIT. Schema drift, trigger interception, full 256-row capacity, SQLite busy/locked/ABORT states, transaction failures and mismatched consent/evidence all fail closed, with rollback. SQLite failures use one fixed redacted `ObservationBlocked` error rather than exposing an attacker-supplied trigger message. The interface and the validated report remain unchanged. Nothing is persisted beyond the lifetime of synthetic in-memory SQLite; the existing restart/replay test deliberately demonstrates this limitation.

**Regression tests:** suppressing and deletion triggers; fake/weakened schema; ALTER TABLE drift after setup; file-backed DB rejection; shared-memory database write-lock contention and later recovery; the 256 hash cap; SHA-256 digests only (no literal nonce); attacker-defined trigger secret redaction; and earlier successful/failed nonce scenarios. These tests must run on public GitHub CI with synthetic sample keys and snapshots only.

### Required real production design before any owner-approved enrollment

1. Trust roots: two **genuinely enrolled**, independent collector signing keys with out-of-band owner/provider bindings, role scope, rotation and revocation; never infer actual provider access from a detached signature alone.
2. Request identity: unpredictable high-entropy nonce generated by an authorized trusted initiator, channel/operation scope, exact read-only purpose, server-validated receipt freshness and independent verification; a caller-selected nonce is insufficient.
3. **Durable**, transactionally UNIQUE storage shared by all workers/regions/restarts, atomic check+consume, defined retention longer than receipt replay windows, replay denial even during provider outages, collision/crash/retry/restart tests. No in-memory/session-only substitute.
4. Production privacy: minimize stored nonce fingerprints; restrict reads, logs, error details, keys, OAuth tokens and account/media IDs; prove backups, deletion policy and incident handling. Provider connection proof and historical release-row readback remain separate.
5. Resource limits: independently verify that proposed storage/runner/network usage fits **₹0 recurring** with hard no-overage gates before provisioning. Require fresh explicit owner approval for external account connections, live D1 reads/writes, migrations, OAuth or upload.
6. Release gates: no publication from cryptographic integrity alone; require real authenticated D1 and exact-channel YouTube readback, safe historical reconciliation, reviewed D1 migration/rollback and a separately authorized single writer.

**Current acceptance:** 4E.12 is only offline engineering staging, not 4E production completion. All **21 production acceptance subphases across six incomplete major phases** remain. Public/private PRs stay DRAFT and unmerged; no laptop/Nirala, Cloudflare/YouTube requests, new services/charges or uploads/schedules.


## Phase 4E.13 — complete offline failure recovery and replay-consistency checkpoint (18 October 2026)

**Scope and acceptance:** The requested 4E.13 SOFTWARE checkpoint is complete only after a successful full public GitHub quality gate, cloud-scouter and synthetic render-smoke CI on one exact branch SHA, and a recorded PR checkpoint. It does not imply completion of overarching **production Phase 4E**.

**Failure handling repair:** An unexpected exception from a validator or malformed caller could previously be re-raised with attacker-controlled diagnostic text. `verify_and_reserve_once_offline` now rolls back and translates arbitrary ordinary Python `Exception` errors into fixed `ObservationBlocked("Offline evidence verification failed closed")`, while maintaining its original fixed validation errors. `sqlite3.Error` remains redacted, and true cancellation/KeyboardInterrupt/SystemExit cause best-effort rollback and propagate. A failed rollback leaves an open transaction, which the next invocation explicitly refuses until the caller repairs or discards its connection. No failure path yields a success report or grants release authority.

**Deterministic recovery matrix** added to existing synthetic suite:

| Failure point | Expected result |
| --- | --- |
| Begin transaction denied by SQLite authorizer | Error, no nonce consumed, clean retry succeeds |
| Insert denied | Rollback, no nonce, retry succeeds |
| Commit denied | Rollback, no nonce, retry succeeds |
| Both commit and rollback denied | Error, active transaction blocks all reuse until recovery |
| Signed validator raises arbitrary secret-containing RuntimeError | Fixed redacted error, no nonce, subsequent valid input succeeds |
| Fake validator returns authenticated/provider authorization | Refused; no nonce consumed |
| Same request nonce signed again for a DIFFERENT metadata hash | Refused despite new valid signatures |
| Worker closes before COMMIT (uncommitted synthetic insertion) | Automatic rollback, survivor may make one verified attempt |
| Two simultaneous worker attempts sharing one in-memory DB | Exactly one success and one blocked attempt; one recorded nonce |
| Reopening a brand-new memory DB after final shutdown | Replay remains possible: explicit evidence of missing durable production storage |

The tests intentionally never touch actual Cloudflare D1, any persistent SQLite files, Google OAuth, provider accounts or media; all are disposable in-memory synthetic fixtures and ephemeral signing keys. Existing Phase 4E.11/4E.12 tests remain in place.

**Non-negotiable production 4E closure blockers:** (1) separately approved actual read-only D1 schema/index and release-row history inventory, including protected-content handling and pagination; (2) exact owner-authorized YouTube channel history with privacy, processing, schedule and full pages; (3) independently configured trusted collector signing keys, durable cross-worker nonce database and trusted server clock with replay tested across process crashes; (4) reconciliation of historical release/video identities and missing/duplicate releases; (5) evidence retained privately with real provenance and explicit ₹0 recurring hard limits. This offline branch accomplishes **none** of these real provider operations. Production 4E remains OPEN, 4F/4G remain blocked, and **21 production acceptance subphases across six incomplete major phases remain**. Both GitHub PRs remain drafts/unmerged. Never use Nirala without fresh authorization, create a new service/charge, connect accounts, change OAuth or perform upload/schedule/publish without the required separate approvals.
