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
