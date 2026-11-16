# FlowMinute Lab Branch 1 — long-video approval: private preservation and YouTube auth handoff

**16 November 2026 — owner said “I approved the video.”** Interpret the singular approval as the 214.833-second real Python CSV long-form video displayed immediately before their message. It does **not** automatically approve the two Shorts, fabricated assets, a different render, changed metadata, the owner's legal rights clearance, or cryptographic release signatures.

## Current source and release facts

- Correct YouTube channel: `UCCcL9Q_jqVq6LJmnYUSAFZA` / `@flowminutelab`.
- Exact long-form original approved *video candidate*: `REAL_PYTHON_LONG_NARRATED_REVIEW_ONLY.mp4`, SHA-256 `1a20dedf886f3228445ed718e1f2e93a7e38cd74abf8aeb211540e32b6683f42`, 214.833s, source physical run [#43880108409](https://github.com/Tirthanand17/taskless-lab/actions/runs/43880108409), source artifact `14232431513`.
- Exact source-timed captions `ORIGINAL_SOURCE_TIMED_CAPTIONS.srt`, SHA-256 `b4b317c8d1d9883294e9ebb32b23c6790a4cdb891be9bbd560fd459baa132a0e`. Do not silently replace exact bytes; package as separate caption track.
- Owner's existing protected YouTube publish OAuth read-only checkpoint was rerun on [Nov 16, #43896534947](https://github.com/Tirthanand17/taskless-lab/actions/runs/43896534947): **`B4F6_REDACTED_FAILURE_CLASS=OAUTH_REFRESH_FAILED`**. This is an **actual current external blocker**, not CI. No upload / schedule attempted.
- Connected vidIQ has **0 credits**, reset reported 2 Dec 2026; its owner upload inventory cannot be checked with paid endpoints. The API integration via GitHub is the project's preferred channel workflow and must not be replaced with guessed occupancy.
- Historical schedule inventory through 18 Nov is not a current authenticated inventory: preserve existing slots and do not duplicate. Do not invent an available slot or claim existing private videos have now published.

## Exact owner-review package without the PC or public exposure

[Manual GitHub-only private preservation workflow](../.github/workflows/branch1-preserve-exact-long-review.yml) verifies the immutable successful source run and precise video/captions SHA, original executed-software receipt, original long-motion QA and false release flags. On a disposable GitHub-hosted runner it creates a **real filmed 1280x720 frame** (not generative artwork, not a fabricated Python UI). It retains only exact MP4/SRT/provenance/motion/recorded thumbnail and a new private-review report for 30 days as an authenticated GitHub Actions artifact, never a public GitHub release. It leaves all protected environment secrets inaccessible and does not call YouTube.

The source artifact expires **19 Nov 2026 around 19:30 IST**. Preserve it before expiry to avoid an unnecessary *different hash* rerender. Repackaging copies exact bytes unchanged.

## Conditions before the first controlled upload

1. Owner must securely **reauthorize the direct YouTube Data API OAuth** for the correct FlowMinute Lab account, updating the existing `youtube-production` GitHub environment secret `YOUTUBE_TOKEN_JSON` using repository settings. **Never paste access tokens, refresh tokens, signing keys or OAuth JSON into ChatGPT, Issues, commits or PRs.** The owner should confirm after securely finishing this login step.
2. Rerun [owner-authenticated read-only audit](../.github/workflows/flowminute-owner-readonly-channel-audit-b4f6.yml). It must verify the correct channel and complete current inventory before selecting a future private `publishAt` date. Do not treat a source-code pass as an authorized channel readback.
3. The existing [protected YouTube publisher](../.github/workflows/publish-artifact-youtube.yml) requires one exact-file metadata/caption/thumbnail owner approval manifest, owner-controlled Ed25519 signature and `PUBLISH_ENABLED` protected variable. The user's chat-level approval for “the video” can be recorded as editorial intent but **cannot** silently substitute for verified caption listening, rights and factual review or the owner's independent offline signature. Never enroll/copy signer's private key into the repository.
4. Select a **future collision-free** slot *after actual private/scheduled inventory readback*, not an unverified legacy slot. In particular, don't silently alter any uploads scheduled before or on 18 Nov. Call the existing publisher only once per owner-signed exact-source bundle; if a request is ambiguous, first reconcile instead of retrying. Verify YouTube's **actual video ID, correct channel, private status, future UTC publishAt, serving captions, processing and thumbnail** before reporting scheduled.
5. After actual release, collect authentic 24/72/168h YouTube Studio data via `autopilot.branch1_age_matched_learning` (not public counters or vidIQ guesswork). Long first-30-second retention, average view duration and actual qualified watch time are the proof needed for the original weak-long-retention cause.

This workflow **does not publish**. It solves the ephemeral asset-preservation problem while holding at the real external OAuth, schedule and rights-approval boundary. The next task requiring user action is secure Google OAuth reauthorization—not more local video rendering, paid credits or a fabricated signature.
