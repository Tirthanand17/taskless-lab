# Phase 4D — signed, time-bounded read-only evidence contract

**17 October 2026 | GitHub offline software CI only. No actual Cloudflare D1 or YouTube readback, no production writes.**

## What changed

- `phase4d_signed_observations.py` defines a small, purely offline protocol for two *detached* Ed25519 signed metadata-inspection receipts: `d1_schema` and `youtube_history`.
- Each signed observation binds the exact FlowMinute channel, purpose, collector/key ID, sanitized metadata payload SHA-256, caller nonce, bounded UTC collection/expiry timestamps, schema version and `read_only` scope.
- A separate externally supplied trust registry pins public keys and allowed purposes. Invalid signatures, wrong channel/purpose/scope, stale/future/expired receipts, wrong nonce, revoked trust entry, duplicate collector or reused signing public key are rejected.
- The verifier requires both independent collector roles and returns `signature_integrity_valid=True` only when the cryptographic checks pass.
- It **always** returns `provider_connection_observed=False`, `authenticated_channel_readback=False`, `production_migration_ready=False`, `production_upload_ready=False`, and `production_schedule_ready=False`.

## What signatures cannot prove

A signature proves only that the holder of an enrolled signing key signed the digest. It **does not prove** that the holder actually queried Cloudflare D1, that an OAuth token belongs to the correct Brand Account, that the YouTube API response is current, or that any video is private/scheduled/public. A malicious caller can supply its own trust registry unless the deployed verifier pins keys independently. The `already_seen_nonces` argument is an offline stand-in; replay prevention needs a real authenticated durable store. The helper `sanitized_snapshot_hash` hashes input but does NOT redact secrets; only pre-sanitized metadata may ever be passed.

Private key issuance, key rotation/revocation, identity authentication, Cloudflare Security Events/1010 remediation, actual provider API calls and an owner-approved collector service do **not** exist here.

## Validation

- `autopilot/test_phase4d_signed_observations.py`: twenty synthetic/regression tests using disposable in-process Ed25519 keys. These are not real Cloudflare or YouTube credentials.
- First full code/test GitHub quality run (commit `d555151329`) **321 tests plus 13 subtests passed**: https://github.com/Tirthanand17/taskless-lab/actions/runs/39043052432
- Latest documentation-only commits may trigger their own CI. Check those separately before asserting head CI is green.

## Phase 4D acceptance

**Software integrity contract implemented offline**; production proof remains **BLOCKED**. This is not an owner-signed migration approval. Do not merge/deploy as a publishing control merely because tests pass.

## Next production tasks

- 4E: owner-approved provider-supported read-only Cloudflare D1 schema/history and exact authenticated channel-owned YouTube readback; secure private public-key registry with safe enrollment and actual authenticated collectors.
- 4F: actual schema-specific reversible migration diff and verified rollback, separate explicit approval before D1 writes.
- 4G: one deployed D1 single writer with trusted clock, concurrency/fencing, remote reconciliation, no duplicate retries, production CI/operations tests.

Related total roadmap: [8 phases and 21 remaining production acceptance subphases](REMAINING_PHASES_21_SUBPHASES_2026_10_17.md).

**Operating constraints:** ₹0 recurring cost ceiling; no Nirala access; no new provider connection or OAuth permission without owner approval; no secret-bearing public CI; no YouTube uploading, scheduling or publishing.
