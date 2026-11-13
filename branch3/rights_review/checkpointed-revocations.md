# Clivox A2 — Signed revocation checkpoint and per-receipt hash-chain QA

**Status, 2026-11-13:** Mathematical protocol verifier and adversarial GitHub-only CI **implemented**. **No live ledger, authority keys, durable checkpoint, creator-issued commercial reuse grants, private media source or YouTube write permission is available.** This is not an operational rights service.

## Problem solved in code

PR #164 introduced exact pending-case-signed reviewer *claims* and a revocation signature preview. But a signed event by itself cannot prove that the entire event history was supplied: a caller could omit a revocation event or substitute an older valid snapshot. This milestone provides an additional verification layer for an individual receipt:

- A domain-separated chain starts from a fixed `GENESIS_HEAD_SHA256`. Each event's SHA-256 commits to its sequence, previous head, exact revocation subject and detached Ed25519 signature. Missing, mutated, reordered or replayed entries fail validation.
- The distinct checkpoint-signing domain binds the exact Clivox ID, case receipt ID, ledger ID, contiguous sequence number, final chain head, signing timestamp and checkpoint signer identifier. The verifier checks the separate checkpoint Ed25519 signature and a **15-minute maximum mathematical age**, never extrapolating it into a claim of live remote freshness.
- An **externally supplied anchor** (sequence and head digest) must match the reconstructed chain at the same position. If a later, separately persisted head was previously observed, replacing the snapshot with an earlier one fails. **The test anchor is caller-supplied and is not actual durable external storage.**
- Each event targets the exact reviewer receipt and must carry an independently verified revocation signature; even one valid revocation permanently quarantines that receipt. Signature tampering, future timestamps, expired review receipts and cross-channel reuse fail closed.
- The final report deliberately labels all real rights, enrolled identity, external durability, media acquisition and YouTube publishing flags **false**, even when every mathematical check passes.

This is a **per-receipt** log, *not* proof that all revocations across creators have been listed. A signing authority that can itself issue misleading checkpoints is not secured merely by a signature; owner-controlled key enrollment and operational checks are essential.

## Repository components

- `scripts/branch3_a2_checkpointed_revocations.py`: pure Python chain/checkpoint verifier and a harmless `--mode fixture` CLI, with no network or storage side effects.
- `scripts/test_branch3_a2_checkpointed_revocations.py`: ephemeral Ed25519 keys to test mismatched heads, deleted signed revocations, stale/replaced checkpoints, wrong signer, invalid source IDs, forged authorization and wrong channel. Test keys are not persistent or real owner keys.
- `.github/workflows/branch3-clivox-a2-revocation-checkpoint.yml`: no-secret, no-artifact GitHub Actions job testing A2 receipts, hash chains and quarantines.
- `branch3/rights_review/review-policy.json`: unchanged fail-closed policy. It must still declare `durable_revocation_ledger=false` and `real_revocation_authority_key_enrolled=false`.
- `branch3/creator_permissions.json`: still empty. No automatic promotion to licensed creator.

## Subsequent global CAS protocol

[Global private GitHub Contents ledger SHA-CAS design](github-private-ledger-cas.md) is now implemented and tested offline to model cross-receipt append-only revocation sequencing and stale-blob write conflicts. The current trust anchors remain test inputs and no real private ledger has been connected or written.

## Mandatory production blockers

1. Obtain and independently verify actual rights-holder commercial clipping permissions and underlying soundtrack/game footage/guest clearances, stored in a private approved evidence vault. Never substitute signer mathematics for legal rights.
2. Establish real authenticated reviewer and revocation/checkpoint authority identities, independently enroll verified public keys and support key revocation/rotation.
3. Provision **owner-approved private durable, append-only storage**, with transactional signed head updates, nonrollbackable trusted checkpoints and an authenticated read interface. A JSON blob, Git commit or CI artifact alone does not prove authoritative completeness or ongoing freshness.
4. Establish signed snapshots and enforce maximum staleness against a trusted clock. The 15-minute offline mathematical freshness threshold does not guarantee remote ledger service availability or absence of newer events.
5. Audit completeness of revocation records and permission status at every stage: media access, render/QA, final A6 release, private YouTube upload and scheduling. Failure to reach an authenticated ledger service must stop every action, never default allow.
6. Add owner and legal review and a separate production controller; **do not flip the offline policy or register a synthetic reviewer public key as the trusted production signer**.

**Real state:** 0 verified licenses, 0 media vaults activated, 0 rights-released clips, 0 CLIVOX uploads, no production release. Branch 1 and Branch 2 are paused.
