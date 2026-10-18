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
