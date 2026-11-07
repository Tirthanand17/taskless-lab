# ADR-0083 — B4f1 signed exact owner release guard (Ed25519; private key OFF GitHub)

**Date:** 2026-11-07 IST | Branch 2 security. User objective remains 2 Shorts + 1 Long/day; this ADR is a manual bridge safeguard, not autonomous release.

## Source finding

`scripts/publish_youtube.py` previously accepted five mutable `true` booleans in a repository approval JSON as sufficient to continue toward YouTube OAuth. B4e9 added GitHub ref deduplication and B4f0 removed workflow_dispatch shell injection, but a writable JSON checkbox **does not cryptographically authenticate the creator's intent**.

The existing `approval_allows_exact_video` remains for legacy source-level tests and does not itself create authority. A second **mandatory Ed25519 verification gate** now occurs *before* Google OAuth and before any `videos.insert`.

## Signing contract, no private signing key in repo or Actions

- Designated owner controls an **Ed25519 private signing key** outside GitHub, Actions, project artifacts, source-control, and model prompts. An independently managed hardware signer/KMS with owner access controls is recommended. This PR neither provisions nor stores a private key.
- Enroll only the 32-byte **public key** as 64 lowercase hex characters in the protected GitHub `youtube-production` environment variable `FLOWMINUTE_OWNER_RELEASE_ED25519_PUBLIC_HEX`, after independent out-of-band key fingerprint verification. This action is **not** performed by the pull request.
- The existing release approval JSON includes `signed_owner_release` with exactly:
  `{"schema":"FLOWMINUTE_OWNER_ED25519_EXACT_RELEASE_V1","payload":{...},"signature_hex":"<128 lowercase hex chars>"}`.
- Signed payload includes exactly `intent="ONE_EXACT_VIDEO_PRIVATE_FUTURE_SCHEDULE"`, expected owner `channel_id`, `episode_id`, `mp4_sha256`, `srt_sha256`, `thumbnail_sha256`, `metadata_sha256` (all SHA256 of the **actual file bytes**), intended UTC `publish_at_utc`, `signed_at_utc`, `expires_at_utc`, and a `checks` dictionary with six individually **true** statements: `human_voice_approved`, `exact_captions_approved`, `rights_cleared`, `factual_review_approved`, `final_video_approved`, `owner_publish_authorized`.
- Generate the 64-byte signature using the owner-controlled private key over UTF-8 **ASCII-stable canonical JSON** `json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=True, allow_nan=False).encode("ascii")` after validating schema. The public verifier exports `canonical_owner_release_bytes(payload)` to eliminate mismatched canonicalization between signing and verification.
- Signed and editable approval checkboxes must both agree. Each signed hash, channel, episode and scheduled UTC time must match the actual current file bytes/release inputs; no other signed payload keys accepted.
- Signed time must be within 5 minutes of trusted time in the future, the signed window is at most 72 hours, and the scheduled upload must be more than 15 minutes ahead and within 30 days of signature creation. Stale, replayed, wrong channel/media, bad/missing key, or invalid signature all stop before any YouTube action.
- Pinned public dependency: [PyCA cryptography 50.0.2](https://pypi.org/project/cryptography/50.0.2/), Ed25519 signature verification from the [documented API](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/). CI generates **throwaway in-memory test keys only** and makes zero network/API calls beyond standard free pip wheel install.

## Critical limitations, no production signoff

A valid signature confirms only that the corresponding private key signed the exact intent bytes. **It cannot establish that a human actually watched the video, that every news claim is factually correct, that licenses are valid, that the uploader belongs to the intended channel, or that a live YouTube upload completed.** Administrators who can replace a public key or pipeline code must also be considered in the trust model. Protect the environment with independent reviews.

A new owner signature would be required for each exact scheduled release unless a **separately reviewed bounded delegation policy** is eventually designed. This change **does not deliver autonomous 3/day publication** and does not enable `PUBLISH_ENABLED`, configure owner OAuth, connect any hardware signer, or grant approval. The existing external 0/21 seven-day proof is unchanged.

Do not allow the assistant/agent itself to create and attest its own source/fact/rights approvals and then call them independent human authority. A future autonomous system requires separately authorized safety policy and trustworthy evidence-gathering with audit/revocation.

## Acceptance

The publisher no-secrets CI imports the pinned free cryptography library, exercises generated test-only keypair success, forged signer, mutated title/metadata/video/captions/thumbnail/channel/episode/time, missing key, expired signature and unsigned approvals. The protected manual publish job still requires `main`, `youtube-production`, explicit `PUBLISH_ENABLED=true`, all metadata preflights, private-first UTC, local+cross-run B4e9 attempt locks and live authenticated YouTube verification.

No live YouTube action should occur in this PR.
