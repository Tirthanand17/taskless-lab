# ADR-0064 — B4e7 stop redundant expensive legacy video renders in CI

**Date:** 2026-11-06 IST. **Scope:** GitHub Actions event and budget safety only. No changes to source storyboards, video bytes, Branch 1 YouTube schedule, live cloud identities or Google OAuth.

## Problem demonstrated by real GitHub events

Merging a one-line science-v7 report mapping change in [PR #73](https://github.com/Tirthanand17/taskless-lab/pull/73) caused an expensive main push fanout, including redundant retired rendered **cinematic_v3**, **floating_v6** and the newly active **science_v7** three-video demo jobs. A separately retired full three-video Kokoro smoke also ran for common renderer PRs, and another historical one-short AAC physical demo ran for the same changes. Re-downloading an open voice model and encoding these already reviewed old styles spends hosted Actions minutes and public artifact storage without advancing the current video release candidate. There are no real owner revenue, copyright or deployment approvals in these jobs.

The current active science-v7 source/pixel tests and the main-only **real** three-video proof have now separately succeeded on [run 42197821807](https://github.com/Tirthanand17/taskless-lab/actions/runs/42197821807), and an independent read of artifact **13493447004** confirmed three distinct H264/AAC MP4s with 61.80s, 219.04s and 59.92s durations and source-scene hashes. All are unapproved, previously-authored science examples, not current daily fresh topics.

## Budget gate policy

- **B4e3 older cinematic-v3** and **B4e4c older floating-v6**: their normal PR and main lightweight native-art, narration, source and copyright boundary tests **remain enabled**. Their three-video model/FFmpeg step is now explicit **workflow_dispatch + refs/heads/main + exact owner repository only**. No scheduled/main push or untrusted PR fires those heavy jobs.
- **B3d4c2c3b original-narration**: retain ordinary PR script/source/timeline unit tests. The old full 3-video Kokoro job is manual main-only rather than automatically running on every renderer update.
- **B4e3d real AAC original short**: add workflow_dispatch event and require main/manual for the large one-short voice download/full encoded AAC challenge. General AAC regression is already covered by broad Content Quality and B4e4c source test jobs.
- The **current B4e6b science-v7 three-video proof** still runs automatically on trusted main source changes with fixed public model hashes, strict no-publish flags, 58-minute job ceiling and 7-day public artifact. On PR it runs only quick art/source tests and does not download model weights.
- New **B4e7 no-download quick regression** statically inspects job names, exact on-event/branch conditions, permission scopes, public OAuth-off/publish-off flags and the fact that current science-v7 physical proof remains. Any changes silently re-enabling heavy PR/push old jobs fail CI.

## Explicit limits

This does **not** prove a reduction in billed GitHub usage until future exact GitHub runs show the old jobs skipped and actual Actions usage is inspected. Manual historical renders still consume quota when explicitly dispatched. GitHub cron, artifact retention and backend quotas must be owner-monitored; never promise free unlimited compute. Does not authorize owner cloud billing, private persistent media, real YouTube OAuth, human editorial approval or actual scheduling.

**End-to-end production score remains approximately 40/100, independent Branch 2 unattended YouTube upload proof 0/21.** Completing a hosted three-video demo is an engineering proof, not the unattended publishing target.
