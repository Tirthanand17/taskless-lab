# ADR-0080 — B4e8 2026 YouTube private-first + resumable upload recovery, offline only

**Date:** 2026-11-07 IST | Flowminute Lab Branch 2 | GitHub-only; no real OAuth, uploads, account writes or rights approval.

## Research verified from official current YouTube docs

1. [November 2, 2026 YouTube Data API revision](https://developers.google.com/youtube/data/revision_history): unverified projects are **no longer forcibly limited to private videos**. A missing `status.privacyStatus` on `videos.insert` **defaults to public** unless channel-specific settings override. The future gateway MUST explicitly include `privacyStatus: private`, including when `publishAt` is set. This is a material change from older assumptions.
2. [videos.insert](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert): `snippet` and `status` include title, description, language, `status.publishAt`, `status.selfDeclaredMadeForKids`, and `status.containsSyntheticMedia`. The last two require real content-specific creator decisions; automated set-and-forget values must be reviewed.
3. [videos resource / publishAt](https://developers.google.com/youtube/data/reference/rest/v3/videos): scheduling requires a **private, not previously published** video. A publish time accidentally in the past can publish immediately. A `videos.update` request with `part=status` can clear omitted settings and must always specify private when changing `publishAt`. Avoid automatic metadata updates before accurate remote readback.
4. [Resumable upload protocol](https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol): start one session, retain its private Location URI, PUT video parts using correct Content-Range, and on timeout/5xx **query the same existing session** for the server-acknowledged last byte (HTTP 308, Range). Nonfinal chunk sizes are 256 KiB multiples. Do **not** initiate a fresh videos.insert on ambiguous responses: duplicates can be created.
5. [2026 quota buckets](https://developers.google.com/youtube/data/getting-started): default `videos.insert` bucket is 100 calls/day, `search.list` 100 calls/day, all other API calls sharing a separate default 10,000 units/day. Values may change; check the current Google Cloud console before live use. This code makes **zero requests**, uses **zero quota**, and cannot prove 3/day affordability.

## Implementation

`autopilot/youtube_private_resumable_contract_b4e8.py` uses the existing B4a immutable unapproved `DryRunUploadIntent` and recomputes its canonical SHA256 fingerprint. It refuses fake owner approval, OAuth, expired schedules, mismatched source/media hashes, invalid sizes, and any intent not in the strictly authorized 11:00 / 16:00 / 20:30 IST 2-Shorts + 1-Long slots.

- Builds an **OFFLINE, NONEXECUTABLE** `videos.insert` metadata specification with `snippet,status`; `privacyStatus` is always explicit `private`; `publishAt`, `selfDeclaredMadeForKids`, and `containsSyntheticMedia` are copied from hash-locked mock source context. There is no network client, Authorization header, upload URL or secret.
- Models one existing resumable session after 308, 200/201, transient 500/502/503/504, 4xx, and ambiguous responses. 200/201 with valid-looking video ID is still not owner-authenticated; 308 uses only the verified server Range and never starts another insertion. Error/uncertainty returns STOP/QUERY SAME SESSION, never re-upload.
- Produces a **7-day × 3-slot = 21 mock proposal** in exact IST order and checks one channel, one unique media/source/context per slot, no repeated release timestamps, and seven consecutive future days. The redacted receipt contains time, hashed IDs, zero actual uploads, zero owner authentication, zero fact/rights approvals and zero production attempt fence.
- New adversarial tests are included in Daily Cloud Foundation. The official current API docs, not 2025-era quota or private restrictions, are the design baseline.

## Boundary between simulation and production

The repo's B4b1 PostgreSQL fence is **CI-only** with imaginary roles; it is not a real cloud durable ledger. The next production implementation must separately establish:

- Owner-controlled cloud identity and YouTube `youtube.upload` OAuth, with encrypted refresh-token handling, explicit selected channel verification and revocation/recovery.
- A genuinely durable, atomic (channel, episode, content hash) attempt lock, persisted *before* contacting YouTube; never share session URIs or tokens in GitHub public artifacts.
- Truthful asset license approvals, independent line-level factual source verification, final actual full MP4 human watch and exact approved file hashes, captions, synthetic disclosure and audience designation.
- A hardened 1-way release state machine, constrained to private first then future `publishAt`; independent authenticated videos.list, captions.list, processingDetails and thumbnail readback, plus private-first rollback/manual reconciliation on error.
- Seven daily real **readback verified** 11:00/16:00/20:30 IST triplets. A 21-video simulated receipt counts as **0/21** live releases.

No workflow permissions, secrets, network calls, paid provider, media retention or real YouTube requests are changed by B4e8. Tests and results of this PR do **not** authorize publishing.
