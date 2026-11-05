# ADR-0035 — Branch 2 B4b2: same-session-only YouTube resumable upload recovery

**Date:** 2026-11-05 IST. **State:** Source-only, unapproved, offline synthetic contract. **No upload, OAuth, protected vault, paid model, real cloud data or actual media.**

## Context and verified official YouTube API protocol

B4b1 proved a one-shot uploader-intent unique key across 24 competing workers on real ephemeral PostgreSQL 16, but no session recovery. The independent owner-owned YouTube upload service is absent; an interrupted upload can have accepted bytes or completed despite an HTTP timeout. A new videos.insert after an uncertain response can create a duplicate. This branch adds a precise **read-only protocol decision model**, not a network connector.

Google YouTube official reference:

- [Resumable Uploads guide](https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol): the successful session initiation returns a Location URI which must be saved. On interrupted upload or 500/502/503/504, send a status query as **PUT on that SAME session URI**, zero body, Content-Length: 0, Content-Range: bytes */TOTAL.
- HTTP **308 Resume Incomplete** signals an incomplete upload; zero-indexed Range header is inclusive. If Range is bytes=0-999999, resume at **byte 1,000,000** (no overlap/gap) with Content-Range: bytes 1000000-(N-1)/N, Content-Length: N-1000000. Missing Range means begin at 0. 308 claiming terminal byte, an invalid range or a regressive acknowledgement is treated as unsafe and must be reconciled.
- The status probe may return the **original successful completion response (typically 201; some clients use 200)**. A reported video ID does not prove owner channel, processing, thumbnail, caption text or media identity. Synthetic response-body readback NEVER authenticates a real Google account.
- **404 expired session**: Google's general guidance allows starting a fresh session. In this project's stricter exact-once owner-safety policy, this is BLOCKED pending independent human investigation and remote channel reconciliation. Do not silently start a second videos.insert when original completion cannot be excluded.
- A bounded number of server 5xx/unknown replies may lead to status re-probe with bounded Retry-After; any unsupported status, malformed headers, 401/403/404/429, quota denial, expired session or recurring uncertainty stops the upload. No hidden automatic paid/request retries.
- [videos.insert reference](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert): enforce privacyStatus=private on a future real upload; never rely on unverified-project default privacy.
- [videos resource](https://developers.google.com/youtube/data/reference/rest/v3/videos): scheduled publishAt requires private, never-previously-published video and future UTC; verify separately with actual owner-authenticated readback.

## What code delivers now

- Pure Python autopilot/youtube_resumable_recovery_contract.py: fake session descriptor with B4a canonical MP4/content SHA, exact owner channel, total length and a synthetic SHA256 of an imaginary encrypted session reference. It stores NO actual URI/credentials. A passed boolean synthetic_checkpoint_saved proves nothing real.
- make_status_probe generates only a protocol description for zero-body PUT with Content-Range: bytes */N.
- interpret_fake_status_reply parses synthetic 308 responses, checks every inclusive range and returns exact next-byte and remaining PUT headers for **the same** session only. It models transient 5xx and zero-response retry limits, bounded Retry-After, error stop decisions, and 200/201 mock completion metadata with only *UNVERIFIED* ID.
- It rejects malformed/duplicate HTTP header maps, regressions/overflow, public/unlisted returned privacy, a wrong channel/ID, forged mock owner/cloud flags, and any replay after terminal states.
- All decision outputs explicitly report actual_http_executed=false, actual_video_uploaded=false, actual_video_scheduled=false, release_authorized=false.
- autopilot/test_youtube_resumable_recovery_contract.py: no-network adversarial fixture tests of every case and source metadata tampering, exact offsets, latency/timeout, unauthorized wrong channel, false release, 404 expiration. Read-only GitHub-hosted workflow runs suite and static dependency guard.

## Remaining real production work (NOT done)

The future service requires an actual protected per-owner single publisher, independent OAuth owner authentication, token vault, verified Google Cloud project and quota, durable **encrypted** session URI written before any media byte transfer, checked per-media-body SHA256, network timeout/restart/308 replay testing against an authorized sandbox, fault-tolerant external PostgreSQL lease and backup/restore, normalized remote video/channel/processing metadata, SRT content verification, custom thumbnail readback, explicit final human rights/disclosure/full-watch approval and scheduled publishAt verification.

A public PR cannot grant consent, authenticate human reviewers, deploy billable AWS infrastructure or use a real YouTube OAuth credential. B4b2 must never be connected to Branch 1's assisted publisher or allowed to call live APIs. A source-only CI test, even when green, is not proof of a real resumable session, remote YouTube upload, 21 live videos, or exactly-once network delivery.

**Branch 2 estimated production completion remains approximately 38% / 62% remaining; 0/21 independently verified unattended actual releases.** Do not increase percentage for test-only code. Review, require exact-head green CI and merge only source contracts. Other external approvals and B5 seven-day production proof remain future work.
