# Track A — existing assisted YouTube releases (frozen working baseline)
**Branch:** `track/assisted-youtube-releases` · **Recorded:** 2026-11-04

This branch snapshots the pre-autopilot implementation from `main` before the cloud-only daily research foundation was merged. It represents the currently successful **ChatGPT-assisted, scoped exact-video** production and YouTube release process. It is **not** independent cloud production.

## Purpose
- Preserve media scripts, queue manifests, production/editorial standards, exact channel identity and YouTube publisher safety tests.
- Allow only explicit, one-time SHA-pinned owner releases with local/private ledger and authenticated remote verification.
- No duplicate video insertion after ambiguous API responses, no scheduling in the past, no silent privacy changes, and no broad `publishing_enabled=true`.
- Finish and verify all owner-authorized November 4–11 slots independently, then freeze this track to fixes and recovery. Do not copy YouTube OAuth tokens, private media files or personal Nirala storage into GitHub.

## Last verified release status (point-in-time)
24 video masters were produced and locally QA recorded; 18 slots had confirmed schedules, one video had already been published, one had a private upload awaiting assets/scheduling, and four had no upload yet. These numbers are **not live GitHub receipts** and must be refreshed against authenticated YouTube before any new action.

## Cloud migration boundary
The separate `feature/flowminute-cloud-autopilot-v1` branch develops the independent laptop-off service. Reuse proven safety contracts and CI, but do not presume the Windows laptop, local SQLite ledger, OAuth refresh token or prior user permission are automatically portable to cloud. A public GitHub `PUBLISH_ENABLED` variable cannot override the private cloud policy.

Owner roadmap: private `Tirthanand17/flowminute-control-private/docs/FLOWMINUTE_TWO_TRACK_ROADMAP_2026-11-04.md`.

**Track A acceptance:** individually authenticated remote videos and captions, correct YouTube channel and future approved UTC schedules, no duplicates, accurate already-public exceptions, and no unauthorized visibility changes.
