# Branch 1 — Source-pixel visual audit of real-app narrated Shorts

## Purpose

Previous recovery PRs #239–#241 introduced actual LibreOffice Calc and Google Chrome screen recordings and pinned synthetic narration. Main-branch narrated job 43726849969 **passed real H.264/AAC media production** on both apps. That is not proof of watchable videos: the genuine application was recorded for 10 seconds while some narrated chapters are longer, and the editor uses `tpad=stop_mode=clone` to hold the source screen. Static footage is a plausible direct reason for viewer swipes.

**This package adds a second, independent creative-media QA gate. It does not schedule, publish, approve, or buy anything.**

## Pixel motion and readability review

`autopilot/branch1_short_motion_audit.py` takes a previously emitted final narrated MP4 and its exact hash-bound `NARRATED_REAL_APP_PROVENANCE_NOT_RELEASE_APPROVED.json`. It fails closed on forged release flags, invalid app identity, incorrect SHA-256 or file size, missing source-derived pixels, wrong video/audio codecs, resolution or duration. It samples genuine decoded **central source-app pixels** only (80 × 100 grayscale at 2 fps), cropping out the non-app chapter header and lower subtitle region, so animated captions alone cannot counterfeit actual software activity.

It reports:

- Share of nearly unchanged source-screen frame pairs.
- Longest consecutive near-frozen application region.
- Whether actual source region changes in the opening three seconds.
- Median contrast and actual sample count.
- Reasons for failing an **internal editorial heuristic**: greater than 45% near-still pair share, more than three consecutive near-frozen seconds, low visual contrast, or no first-three-seconds source change.

These are **our own conservative screening criteria**, not YouTube recommendation-system thresholds and not scientifically validated proxies for satisfaction. A static frame can be educational, and motion can be meaningless, so neither passing nor failing the screen predicts views. Any passing clip still needs a human full watch with accurate app/voice/caption factual checking.

It also extracts six **actual frames** from the finished MP4 at selected moments to support a manual mobile-viewing and readability review (no invented thumbnail image, no mocked app UI).

## GitHub-only execution

`.github/workflows/branch1-short-motion-audit.yml`

- PRs: synthetic unit tests for real motion vs static UI, early hook, blank region, malformed media, falsified receipt and release-signoff bypass; no media download.
- Manual **main** only: securely read the specified successful main-branch narrated review run. Confirm workflow identity, event type and success status; download only the two narrowly named **unapproved** Calc/Chrome artifacts; run screen audit on an ephemeral GitHub runner; archive review reports and six actual rendered frames per app for three days.
- If the pixel-static heuristic is triggered, **fail the creative QA job**, while preserving its evidence artifact. A failed creative screening is a valuable, honest outcome and should trigger a reshoot; never redefine it as success simply to get green GitHub badges.
- GitHub permissions are `contents:read` and `actions:read`; no uploader, OAuth, channel upload, schedule, media on a laptop, user account or external paid service.

Manual workflow input for the existing validated narrated run: `source_run_id=43726849969` (artifact currently retains until 2026-11-18; this workflow does not prolong the original MP4).

## Next actions based on actual measured footage

1. If the narrated Calc or Chrome video has excessive frozen app content, extend **actual source recording coverage** and synchronize the software actions with voice pacing; remove prolonged cloned holds. Purposeful, relevant zoom/cursor emphasis may support true actions but must not counterfeit them.
2. Visually inspect six keyframes and whole videos on a mobile-sized preview; confirm Calc is identified as Calc rather than Excel and Chrome has not changed notification permission.
3. Only after media clears creative review and a separate owner exact-video approval should any new upload be considered. Continue the publishing pause.
4. Measure real Shorts stayed-to-watch and retention after authorized publication. A technically better edit has not yet proven growth.

**Channel growth baseline from the prior Studio audit:** 21.2% stayed to watch for Shorts. This is context only, not a QA acceptance threshold.

**No YouTube operations in this package. No purchase.**
