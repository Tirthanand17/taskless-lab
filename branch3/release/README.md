# Clivox A6 — Signed exact-asset release preflight and quarantine

**2026-11-12:** Cryptographic **verification design and offline tests implemented**. No real Clivox owner signing key, approved media, verified creator license, release credential or YouTube upload is configured.

## Why the release needs two independent checks
1. Authentic creator-issued commercial clipping permission, active scope, separately cleared source music/game/guest rights, and human editorial/QA review. Software cannot grant these rights by setting a boolean.
2. A human-controlled cryptographic Ed25519 signature on a canonical release subject including **Clivox channel ID, release ID, exact MP4 SHA-256, metadata SHA-256, rights evidence SHA-256, explicit private-first upload status, and future UTC schedule**.

The signed bytes use the domain separator `CLIVOX-A6-EXACT-RELEASE-V1`. Changing the MP4, title, rights evidence, channel ID or planned time invalidates the signature. This is an offline demonstration; the production key holder and its authority are not enrolled.

## New exact-video editorial review signature bridge (unsigned by default)

[Original-video owner editorial attestation and unsigned checklist](ORIGINAL_EDITORIAL_OWNER_ATTESTATION.md) creates **five unchecked review fields** for every exact MP4/WAV/SRT/metadata A6 handoff; each GitHub original arcade render can package the `owner-editorial-review-UNSIGNED.json` document. A separate Ed25519 detached signature verifier proves **cryptographic consistency only** using ephemeral keys in tests, not the owner's identity, actual human playback, rights, trusted signer enrollment or release. No private key, Google OAuth or real YouTube upload is involved.

## New original first-party A6 exact-video handoff

The [original arcade exact-asset owner review handoff](ORIGINAL_VIDEO_OWNER_REVIEW_HANDOFF.md) rehashes each *actually rendered* MP4, WAV, SRT, source catalog, canonical metadata and independently regenerated FFprobe QA before producing `owner-handoff-quarantined.json`. It is integrated with the [GitHub original arcade render workflow](../../.github/workflows/branch3-clivox-original-arcade-pilots.yml) and adversarial no-secrets CI. All output remains quarantined; **no actual owner Ed25519 key, authentic detached release, approved commercial third-party licensing, Google upload or scheduled publication exists.**

## Files
- `branch3/release/fixtures/unapproved-release.json` — fully quarantined source-free A5 demo, missing video/metadata/rights hashes, no signature or schedule.
- `branch3/release/release-policy.json` — no production signing key, zero signed releases, zero creator licenses, release disabled.
- `scripts/branch3_a6_signed_release.py` — strict quarantine validator, canonical signing subject, Ed25519 detached signature verifier, UTC future-time checker. Actual `production_release()` always raises a blocked exception.
- `scripts/test_branch3_a6_signed_release.py` — generated **ephemeral private test keys** only, signature tampering, wrong signer, mutated source hashes, privacy, false owner grant, wrong channel, past schedule, quarantine tests.
- `.github/workflows/branch3-clivox-a6-release-quarantine.yml` — read-only GitHub-hosted CI, no owner keys, no YouTube token, only JSON report artifact.

## A6 workflow (target, not deployed)
1. Rights holder issues real proof; owner verifies and stores private contract outside public GitHub, while a sanitized digest can be checked.
2. Human quality reviewer watches the **licensed exact finished render** and approves original commentary, accuracy, subtitles, music and claim status.
3. Owner enrolls a signing **public key** through an independently audited process. Private key never enters GitHub PRs, GitHub Actions tests or source control.
4. Owner signs a release manifest for the **exact finished video**, metadata, rights record, target Clivox channel and future schedule.
5. Future protected release job checks owner-key trust, independently verified rights and media QA, expiry, signature, production environment reviewers and authenticated Clivox OAuth. The current A6 code DOES NOT implement those live authorizations.
6. If any evidence changes, permission expires/revokes, wrong channel appears or remote inventory is ambiguous: stop/quarantine, do not retry a public action.

## Do not confuse these states
- A cryptographically **valid signature** proves only that *one key* signed *those bytes*. It does **not** prove the key belongs to Clivox's owner, that the rights holder authorized the clip, or that the final content meets YouTube policy.
- Current `real_owner_signing_public_key_enrolled=false` is intentional. GitHub CI creates temporary keys for mathematical correctness testing and never stores them.
- The A5 synthetic preview is an original **demo**, not a signed licensed production asset.
- `upload`, `schedule`, `publish`, and third-party download remain **disabled**, and Branches 1/2 remain paused.

Next milestone: A7 distinct Clivox **read-only** YouTube channel OAuth and inventory, after owner authorization. Actual A6 release integration remains dependent on licensed source, media QA and human attestation.
