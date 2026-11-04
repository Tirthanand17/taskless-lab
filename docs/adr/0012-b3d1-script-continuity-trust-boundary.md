# ADR-0012 — Branch 2 B3d1: externally anchored script continuity

**2026-11-04 · Decision:** introduce a cryptographically checked, **nonpublishing** script/source/dossier continuity boundary *before* AI-generated content can be treated as an editorial review candidate. Reuse existing Ed25519 verification practice from Phase 3C; do not build a second YouTube publisher or public signing service.

## Evidence and research

- [NIST FIPS 186-5](https://csrc.nist.gov/pubs/fips/186-5/final) describes digital signatures as an integrity and origin-authentication mechanism. A digest computed by the party also supplying an artifact is NOT an independently trusted receipt.
- [pyca cryptography Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) documents detached signatures and previously trusted public keys. Script signatures do not verify model semantic correctness.
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use) warns against untrusted PR code in privileged secret-bearing workflows. B3d1 uses only ordinary pull_request with contents:read, no signing keys, no private media and no YouTube uploads.
- Existing repository Phase 3C (autopilot/signed_review_gate.py) already verifies four detached signed media inspections with externally enrolled reviewers, including source_accuracy and asset_rights. It never grants publishing. It remains unchanged.
- PR #14 B3c established that HTTP observations and AI-generated claim candidates are NOT independent fact validation. B3d1 preserves that distinction.

## Explicit trust model

There are THREE independently supplied values:

1. Untrusted candidate: full script proposal (including exact narration and claim candidates), its B3c source observations, and one canonical IST release slot.
2. Externally PINNED anchor digest retrieved from a separately authenticated, immutable or fenced owner ledger; NOT computed from the candidate inside the consumer trust boundary.
3. Ed25519 detached custodian seal, verified against an independently enrolled public-key registry. Creator/publisher identities must be excluded by independently authenticated identity records.

The public code validates format and signature against caller-supplied trust roots, but cannot prove that caller fetched a private ledger, enrolled real people or checked factual content. Therefore all production integration flags remain false. Only disposable keys in GitHub-hosted tests.

### Exact data binding

The frozen sorted-JSON manifest contains:

- Fixed FlowMinute channel and episode ID; release day Asia/Kolkata; exact slot and derived release UTC identity (not approval).
- Proposal SHA256 and verbatim narration SHA256.
- Public source observation SHA256, B3c dossier SHA256 and candidate claim count.
- Explicit false factual review, rights, human-review, rendering and YouTube permissions.

Reject moved/replayed slots, mismatched project calendar, forged draft approval, absent separate anchor, altered script/source/claims even when structurally valid, invalid or revoked public-key signer, creator/publisher signer, old/future seals, wrong channel and wrong episode.

The signed claim uses a fixed versioned PURPOSE string and binds manifest digest, episode, channel, slot, UTC time, signer identity/key and a 24-hour freshness + 48-hour maximum expiry. No signature from a self-declared candidate key is trusted.

### Data flow

Research observation (unverified) → provider proposal (live generative model still unapproved and not exercised) → B3c source-linked claim dossier (still unverified) → B3d1 canonical manifest + external private anchor + independent detached signature → verified CONTINUITY-ONLY record → STOP: real claim verification, creative approval, rights, synthetic-media disclosure and playback review remain missing.

A signed B3d1 record returns media_render_enabled=false, youtube_upload_enabled=false, release_authorized=false and cannot unlock the existing media signed-review gate or scheduling.

## Files and tests

- autopilot/script_continuity_gate.py: pure CPU manifest/detached-signature verifier; no I/O, signer, keys, network, privileged actions or billing.
- autopilot/test_script_continuity_gate.py: disposable Ed25519 keys in hosted test process; three formats/slots; tampered narration/source/claim; fake anchor/seal; moved clock, replay/wrong channel; invalid/revoked signer; exclusion and no-publish checks.
- .github/workflows/flowminute-script-continuity-qa.yml: hosted contents:read, no privileged pull_request_target or persisted checkout token; cryptography verification dependency; reuses prior B3c and Phase 3C verifier regressions.

## Limitations and next implementation order

**B3d1 is not an operational trust service.** Private immutable anchor persistence, key custody, rotation, enrollment, reviewer identity proof, idempotent transaction fencing and append-only audits need private independently authenticated provider integration. Someone who can substitute both anchor and trust registry can evade the verifier; code therefore never asserts the external trust root itself was authenticated.

**B3d2:** independently inventory actual narration assertions, not just model-provided claim candidates; retrieve primary source content and compare exact claims/date/context; distinguish independent corroboration vs syndicated copies; add genuinely independent reviewer outcomes. Requires source provenance, reviewed evidence and account authorization.

**B3d3:** connect approved original AI-generated scripts to B3b full-duration rendering; bind resulting media SHA to independent existing Phase 3C signed visual/audio/factual/rights reviews with actual authorized playback and reviewer identity. No self-approval or unwarranted release authority.

**B4:** private durable media, renewable authorized YouTube OAuth, explicit private uploads and readback, canonical D1 one-writer lease, safe future UTC scheduling. November 2026 YouTube API no longer guarantees private on an omitted privacy status. Owner approval needed for all private credentials/provider billing or new rights.

**B5:** prove 21 distinct videos across 7 consecutive days with laptop off, no duplicate/missing release and controlled cost.

## Acceptance

B3d1 is a **nonpublishing developer preflight** only after all GitHub-hosted CI passes. No private keys, persistent media, user laptop dependencies or Branch 1 modifications are permitted.
