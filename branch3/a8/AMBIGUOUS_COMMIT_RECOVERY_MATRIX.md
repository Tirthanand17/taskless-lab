# CLIVOX A8 — crash and unknown-upload recovery safety case

**Implemented 2026-11-13:** OFFLINE model/CI only. No live production upload writer, actual Google OAuth, YouTube uploads, independently immutable checkpoint, or owner-signed exact-video release exists.

Core rule: **a GitHub ledger reservation is never YouTube upload permission. An absent reservation after an ambiguous update does not prove the update never committed.** All ambiguous outcomes remain held for owner review.

## Implementation

**scripts/branch3_a8_crash_recovery.py** provides an offline no-network recovery decision function. It validates a caller-supplied canonical A8 journal, prior sequence/head floor, exact CLIVOX identity, release/media/metadata/rights SHA-256 identifiers and duplicates. An optional read-only inventory JSON is validated only for its schema: its authenticity is NOT established by caller-provided JSON.

**scripts/test_branch3_a8_crash_recovery.py** runs recovery on 12 named possible failures with/without a reservation, then checks an explicit unknown-state marker, duplicate releases, corrupted chains, falsified inventory flags, wrong channels and anchors, and **99 deterministic 2–12-worker synthetic CAS interleavings**.

**.github/workflows/branch3-clivox-a8-crash-recovery-qa.yml** executes the no-secret unit suite and a 32-schedule offline contention sample. GitHub credentials, private video IDs, and Google API calls are absent.

## Failure decisions

| Failure case | Required action |
|---|---|
| No GitHub reservation or GET failed | HOLD; no automatic new PUT or upload |
| GitHub 409 Conflict or 422 validation failed | HOLD; reconcile against fresh protected readback |
| Timeout, HTTP 500 or crash after sending the PUT | HOLD; lack of a visible attempt does not prove the write failed |
| Commit response success without independent exact readback | HOLD; Git response is not final remote-video proof |
| Valid canonical reservation already visible | HOLD; reservation is not owner signing or YouTube permission |
| Repeated release ID, media hash or attempt key | HOLD; no duplicate/new automatic reservation |
| A8 journal has MARK_UNKNOWN_NO_RETRY | HOLD; owner must investigate the prior upload state |
| YouTube upload response unknown or video ID unverified | HOLD; independent owner and upload receipt reconciliation needed |
| Bounded YouTube playlist shows zero videos | HOLD; API snapshot may not be complete, fresh or tied to exact original MP4 |
| Claim of original binary SHA from ordinary YouTube metadata | DENY; YouTube metadata does not supply a reliable original MP4 SHA-256 |

The new function **never** returns retry, upload, schedule or publish authority. It returns sanitized hold decisions only, without private media hashes, receipts, private video IDs or credentials.

## Official sources and engineering limitations

GitHub's [Contents API](https://docs.github.com/en/rest/repos/contents) requires the prior file blob SHA on updates and documents HTTP 409 conflicts, while advising serial handling of concurrent Contents operations. A prior milestone observed one real stale-SHA 409 in a private CLIVOX sandbox, but that was a sequential proof, NOT a multi-runner linearizability guarantee.

YouTube's [video resource](https://developers.google.com/youtube/data/reference/rest/v3/videos) contains channel, privacy and some owner-only file metadata, but **does not establish the cryptographic SHA-256 of the original uploaded MP4**. Therefore neither a matching title, owner-visible file size, metadata status nor a locally invented receipt automatically clears an ambiguous upload.

The local model chooses one synthetic CAS winner and rejects other stale proposals. This establishes only that our **modeled** state machine stays conservative. It does not establish a live remote cross-run lock or independently trusted immutable rollback anchor.

## Owner-controlled blockers to first real pilot

1. Human watch and commercial asset/voice/captions review of the exact CLIVOX original video.
2. Enrolled trusted A6 signing keys and actual owner signature bound to exact MP4, metadata, rights and schedule.
3. Separate private media approval, immutable external journal anchor, credential/ACL and app-access audit.
4. Real production global reservation writer with crash/race tests; no such writer is deployed.
5. Clivox-only Google owner OAuth, secure receipts and authenticated read-only inventory, without FlowMinute fallback.
6. One expressly approved private-first video upload and post-upload readback; NEVER blind retry.

**Current:** actual global ledger has zero upload events; A9 remains 0% and publishing is disabled. Branches 1 and 2 paused.
