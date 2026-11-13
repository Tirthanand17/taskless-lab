# CLIVOX A2 — Human-review signed receipt + revocation PREVIEW

**2026-11-13:** An **offline mathematical verification and quarantine stage**, not a live creator-license approval or production review system. No creator has granted CLIVOX redistribution rights, no authorized review key has been enrolled, no owner-approved contract vault exists, no durable revocation ledger exists and no source-media download/upload may take place.

## Why this stage exists

The A1 metadata ranker and A2 case intake already create exact, unverified rights-review cases; A1→A2→A3 handoff checks them for integrity. However, plain JSON fields such as `creator_identity_manually_verified: true` can be authored by anyone who can edit a fixture. **A public review flag, SHA-256 digest or mathematically valid signature alone is not a creator-issued license.** This stage prepares two independent cryptographic capabilities for future *independent external verification*:

- A domain-separated **Ed25519 detached signature** on a human reviewer receipt tied to CLIVOX channel ID, exact A2 case SHA-256, source video and creator channel IDs, a digest of private grant evidence, exact reviewer claims, limited review time window and reviewer key ID. Changing any signed field breaks the signature. Reviewer signatures prove the signing key, not authority over source copyright.
- A **different signing domain** for a later revocation/tombstone event, tied to the exact reviewer receipt and source case, event sequence, revocation timestamp and reason. Correctly signed events invalidate the preview immediately. Invalid signatures, expired reviews, duplicate/reordered revocation events, mismatched source IDs, changed rights claims and asserted sequence rollback all fail closed.

The code's `verify_offline_receipt_preview` accepts explicit caller-provided public keys and test-checkpoint values. **This is not production trust.** Public keys need independent owner-controlled enrollment, an approved real-world reviewer process, signed and durably stored revocation snapshots and independent rightsholder authentication; the current script cannot do those steps. An empty revocation input *cannot establish* that permission was never revoked. Its only success result has **all** media/upload/schedule/publish authorizations `false`.

## Follow-up: signed snapshot hash-chain verifier (2026-11-13)

[Receipt-scoped revocation checkpoint security preview](checkpointed-revocations.md) now checks an exact hash chain, detached checkpoint signature, 15-minute timestamp window and a caller-supplied prior trusted-head anchor. Deleted/reordered events and signed revoked receipts fail closed in GitHub-only adversarial CI. **There is no actual owner-controlled persistent checkpoint, enrolled revocation key or remotely complete revocation feed. This check grants no copyright permission or media access.**

## Runtime and CI

- `scripts/branch3_a2_review_receipt.py` — restricted pending A2 cases, canonical digest/signature/revocation mathematical checks, strict zero-grant policy. Its CLI runs only the zero-license **pending-case quarantine**, not live receipt signing or registry promotion.
- `scripts/test_branch3_a2_review_receipt.py` — **ephemeral test-only Ed25519 keys** used solely to exercise success/forgery/mismatch/revocation logic; no real private keys or personal contact details are stored.
- `review-policy.json` — intentionally declares no enrolled human key, no revocation authority, no durable ledger, no real grants and no API writes.
- `.github/workflows/branch3-clivox-a2-signed-review.yml` — public GitHub PR CI, synthetic A1 source IDs/metrics, real A2 pending-case derivation, adversarial tests and a seven-day **sanitized, no-creator-ID, no-license** JSON report. No secrets or third-party footage.

The API-level integration step uses the existing `build_rights_cases` output with exact equality against recomputed A2 source cases. Any source mutation or forgery aborts the audit.

## Real-world next gates

1. Obtain actual rights-holder permission for **commercial YouTube** clipping and editing. Verify the rights holder's identity and their authority over underlying game publisher, music, guests and other embedded IP; never assume popularity, a general campaign link or uploader consent is sufficient.
2. Store full grants, contracts, revocations and private contacts in an owner-approved confidential vault, not `taskless-lab` or its public Actions artifacts.
3. Independently enroll and pin the correct human reviewer and revocation-authority public keys, prove authorization/role separation and implement a durable append-only, monotonic, signed revocation ledger. A caller-provided JSON list or sequence cannot prove completeness.
4. Revalidate rights at media acquisition, final render approval, private upload and scheduling, including genuine revocations and expiry.
5. Create a **separately audited production gate** that combines real rights evidence, publisher/underlying media rights, private storage, original editorial, A5 quality assurance, A6 exact-owner release and A7/A8 protected CLIVOX OAuth. This preview deliberately cannot activate any of those capabilities.

**Zero approved creators, zero legal sign-offs, zero licensed source files, zero YouTube uploads. Branches 1 and 2 untouched.**
