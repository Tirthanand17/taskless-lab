# FlowMinute Lab — YouTube Publisher Phase 3 readiness audit

Updated 2026-10-11 (Asia/Kolkata). Branch: `feature/youtube-api-publisher-v1`. The main production branch has not been changed by this phase.

## Verified accomplishments

- The official YouTube API has verified the FlowMinute Lab channel, `UCCcL9Q_jqVq6LJmnYUSAFZA`.
- A single private-only test upload, `1s-qSriHWGg`, previously succeeded and was confirmed processed, unscheduled and private. Its ledger record is still `uploaded_private`. **Do not publicly release this test slate.**
- The credential health command `auth-health` shows which OAuth scopes exist, whether a refresh token is present, and the access-token expiry **without printing the token values or claiming a known refresh-token expiry**.
- The queue audit `verify-queue` verifies actual channel, title, privacy, processing and publication time against recorded GitHub receipts. It handles up to 50 YouTube IDs per API call and returns a nonzero exit status on discrepancies.
- The Windows wrapper `scripts/flowminute_daily_preflight.ps1` runs these checks as a **read-only** workflow. It does not upload, schedule or change any video.
- The live October 12, 2026 release queue passed: `long_007` (16:00 IST), `pilot_015` (11:00 IST) and `pilot_016` (20:30 IST), with **three checks passed and zero discrepancies**.
- Added strict UTF-8 description byte limit and invalid-angle-bracket checks for metadata.
- Added timed, sequential, non-overlapping SRT cue format validation (still requires manual audio transcription review).
- **39/39 offline regression tests passed on Windows**. All Google API write calls in the unit suite were mocked; the live checks here were read-only.
- Temporary files and OAuth credentials remain in `%USERPROFILE%\.flowminute-private`, excluded from version control.

## Ready-to-use read-only command

PowerShell, from the local feature worktree or using the absolute path:

```powershell
& 'C:\Users\Dell\Desktop\youtube con\flowminute-publisher-worktree\scripts\flowminute_daily_preflight.ps1' -Date '2026-10-12'
```

This reports `PASS: no scheduled queue discrepancies detected` on a matching future schedule, or stops with an error on mismatch. To verify another day's receipts, use `-Date 'YYYY-MM-DD'` after their Studio/API upload receipts have been saved locally in `state/scheduled/`.

The feature branch is not merged to main and production publishing remains manual/explicit.

## Critical OAuth limitation

The Google Cloud OAuth app was configured as **External / Testing**. Google's official policy states that a test user's Google authorization and corresponding refresh token expire after seven days when requesting YouTube scopes, which are outside the basic profile exception. Access-token expiry in local credentials is **not** proof of refresh-token lifetime. See:
- https://developers.google.com/identity/protocols/oauth2
- https://support.google.com/cloud/answer/15549945

Therefore we cannot reliably start an unattended daily uploader until the app's OAuth publishing status and any required verification process are addressed. Do not bypass Google's review requirements. A safer fallback is preflight monitoring with explicit reauthorization when needed.

## Unfinished live API tests (do not misreport as complete)

1. A thumbnail file was created and hash-approved for private test `1s-qSriHWGg`, but the **actual thumbnail API write was blocked before execution**. There is no thumbnail-success receipt in the ledger.
2. A caption test requires a separately recorded voiced canary and exact, reviewed captions. The silent test video cannot meaningfully prove caption timing or transcription quality. Only offline SRT validation is implemented.
3. Actual future scheduling through this API is still not live-tested. Unit tests use mocked YouTube responses. The private test prefix has a permanent scheduling prohibition. To test safely, use a separate explicitly approved, non-test canary with a future publication and a planned cleanup; never alter already scheduled real productions.
4. Thumbnail and caption confirmation should include a `thumbnails` / `captions.list` read-back or Studio visual confirmation, not assume an API method return proves full processing.
5. GitHub CI Windows/Linux exists as **manual dispatch**; do not run a billable workflow when Actions credit may be limited.

## Recommendation for next phase

- Get an owner decision on Google OAuth Testing vs production/verification so long-lived unattended credentials can be supported.
- Finish a controlled real thumbnail and reviewed-caption API test when write access for that operation is available.
- Run a separate authorized private scheduling canary, verify remote state, and remove/revert it before its publication date.
- Keep an explicit human approval gate before promoting a new video to scheduled. Only after several clean pilots should regular daily scheduling be connected to the approved content-production pipeline.

**Release decision: NOT YET UNATTENDED-PUBLISHING READY.**
