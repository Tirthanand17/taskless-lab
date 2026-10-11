# FlowMinute YouTube API Phase 2 — QA and safety checkpoint

Date: 2026-10-11 (IST). Feature branch: `feature/youtube-api-publisher-v1`. Main branch and the existing October 11–12 publishing queue were not modified in this phase.

## Verified existing pilot
- YouTube Brand Account verified as FlowMinute Lab (channel `UCCcL9Q_jqVq6LJmnYUSAFZA`) using the official API and a locally stored OAuth token.
- The private test upload is `1s-qSriHWGg`, with the expected title and channel.
- Its actual remote upload status is `processed`, processing status `succeeded`, privacy `private`, and `publishAt=null`.
- Its local secure ledger has `uploaded_private`; the new `inspect` command verified the ledger against the remote YouTube state.
- The test video remains **unscheduled and unpublished**. It must never be scheduled; the code rejects `api_private_test_*` scheduling.

## Phase 2 changes
1. Added `inspect`, a **read-only** comparison of the expected account, local ledger, video title, privacy, processing status, and scheduling state.
2. Fail-closed scheduling checks now require the remote video to have completed processing successfully and the intended publish time to remain at least 30 minutes in the future at execution time, not just at initial manifest validation.
3. Added a cross-episode SHA-256 duplicate block: a differently named episode with the identical video bytes cannot be uploaded again through the same ledger.
4. Locked the recorded video title after reservation, preventing title drift between signed metadata and a subsequent schedule or thumbnail operation.
5. **30 offline regression tests passed on Windows**, including the above cases. These are unit tests with mock video API responses, **not** a claim of a live scheduling test.
6. Prepared a clear, original **1280×720 / ~28.2 KiB** custom thumbnail for the private pilot at `%USERPROFILE%\.flowminute-private\api-private-test-001\private-test-thumbnail.png`. Its SHA-256 was entered in the private release manifest and its offline validation passed.

## Honest remaining blockers
- **Thumbnail upload:** not performed. The live tool call to apply the thumbnail was blocked before it ran; no thumbnail API success receipt exists. The ledger still shows no confirmed asset uploads.
- **Caption upload:** not performed. The eight-second pilot has silent audio. It would be misleading to invent spoken captions or mark a caption file as human-reviewed. Use a separate voiced, personally reviewed canary to test captions.
- **Live scheduling API:** not performed. The pilot is permanently protected from being scheduled, and leaving a future-public test video on the channel would be an unacceptable default. The schedule API has only passed mocked tests; separately authorize a controlled temporary canary and its cleanup if a real scheduling test is desired.
- **Autonomous pipeline:** not enabled. Refresh tokens for an external Google OAuth app in Testing mode may expire quickly; perform refresh/consent hardening before unattended use.
- **Full production quality gates:** do not assume the application has watched or visually reviewed every output frame just because Python validations pass. Review content before release.

## Safe local commands

The publisher's default ledger is now permanently anchored to `%USERPROFILE%\.flowminute-private\youtube-ledger.json`, so its behavior no longer changes with the terminal's working directory.

Run a read-only inspection (does not publish or change video metadata):

```powershell
& 'C:\Users\Dell\Desktop\flowminute-publisher-worktree\.venv\Scripts\python.exe' 'C:\Users\Dell\Desktop\flowminute-publisher-worktree\scripts\youtube_publisher.py' inspect "$HOME\.flowminute-private\api-private-test-001\release.json" --token-file "$HOME\.flowminute-private\youtube_publish_token.json"
```

The separate write operation `assets` remains explicitly gated by `--confirm-assets` and can be run only after reviewing the prepared thumbnail and ensuring the correct test video ID appears in `inspect`. If an assets call is ambiguous, the ledger deliberately refuses blind retries.

**Current release decision:** Keep the API pilot in controlled testing; no unattended public-release switch or automatic scheduling should be activated yet.
