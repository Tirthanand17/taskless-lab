# FlowMinute YouTube API — private upload pilot prepared

Date: 2026-10-11 (Asia/Kolkata).

## October 11 — private API test PASSED

The channel owner completed Google OAuth authorization for `youtube.force-ssl` in Google's consent screen. The publisher's `doctor` read-back verified the authorized account belongs to **FlowMinute Lab**, channel `UCCcL9Q_jqVq6LJmnYUSAFZA`.

A single explicitly approved API upload of the eight-second original test slate returned video ID **`1s-qSriHWGg`**. Official `videos.list(part=status,snippet,processingDetails)` independently confirmed:

- Video: https://youtu.be/1s-qSriHWGg (private; not a publicly accessible link)
- Correct FlowMinute Lab channel, expected test title.
- `privacyStatus=private`, `publishAt=null`.
- `uploadStatus=processed`, `processingStatus=succeeded`.
- Three existing October 12 videos were checked again and their planned `publishAt` values were unchanged.

**Bug caught in pilot:** the original default ledger was relative to the command's working directory, which is Desktop Commander's own installation tree when invoked remotely. The publisher's default was fixed to `Path.home() / ".flowminute-private" / "youtube-ledger.json"`. The genuine upload receipt was migrated to that private user folder after matching SHA-256 checksums, and the stale copy was removed. The receipt remains `uploaded_private` with the real video ID. The production safety tests now pass **24/24**, including a new home-anchored ledger test.

No scheduling, public release, metadata mutation of existing productions, duplicate upload, or deletion was performed.

### Remaining release gates

1. Keep this test slate private; `api_private_test_*` episodes have a hard-coded scheduling prohibition.
2. Google OAuth app is currently in Testing mode; refresh token lifetime may be limited. Do not declare unattended automation production-ready yet.
3. Before any new production episode's API upload, ensure full visual/audio QA, a reviewed final SHA-256, correct metadata and channel, and a precise future scheduling plan. Run a separate controlled end-to-end test with a new non-test episode rather than altering an already scheduled video.
4. A secure unattended credential-storage and scheduled publishing pipeline have **not** been activated; the owner should approve these only after controls and monitoring are reviewed.

---

## Current milestone

1. Read-only Google OAuth and the channel ID `UCCcL9Q_jqVq6LJmnYUSAFZA` were independently verified.
2. The existing October 12 schedule was checked against the official API and confirmed intact.
3. A **new and original** 8-second test clip was created locally (1280×720, ~77 KiB) with clear on-screen labels `PRIVATE API TEST`, `DO NOT PUBLISH`, and `NO SCHEDULING`.
4. Test media and release files are **not in GitHub**: `%USERPROFILE%\.flowminute-private\api-private-test-001\`.
5. The release manifest uses new ID `api_private_test_001`, correct FlowMinute Lab channel, explicit audience/altered-media declarations, and SHA-256 `97781412de232948010068ab62eeb22cb05926d91d1bf52c177a1108dbb7d2c9`.
6. The publisher `prepare` dry run validated the test file and metadata without any API writes.
7. All **23 Windows regression tests passed**. A new hard-coded guard in the publisher refuses to schedule any episode prefixed `api_private_test_`, even if it has been privately uploaded.
8. Temporary OAuth setup screenshots were removed from the repository worktree before committing anything. Secret/token files remain in the private user folder.

## Pending user-controlled authorization

Google's `youtube.force-ssl` write scope has **not been authorized**; its use is broader than read-only and permits managing channel video resources. Do not use the read-only credential for writes, reuse or share tokens, or upload with browser-session hacks.

To begin the consent flow manually, in PowerShell on the authorized Windows computer from the worktree:

```powershell
& 'C:\Users\Dell\Desktop\flowminute-publisher-worktree\.venv\Scripts\python.exe' 'C:\Users\Dell\Desktop\flowminute-publisher-worktree\scripts\youtube_publisher.py' authorize --client-secret "$HOME\.flowminute-private\client_secret.json" --token-file "$HOME\.flowminute-private\youtube_publish_token.json" --mode publish
```

Review Google's warning and requested channel management permissions in the browser, choose **FlowMinute Lab** Brand Account, and approve only if you agree. Treat the new OAuth token as secret. The Google app is still in Testing mode; test-user refresh tokens may expire and need reauthorization.

After consent, run channel `doctor` with the publishing token and the expected UC ID. Only then is a **private-only** test upload possible, requiring a separate `--confirm-private-upload` flag. Do not schedule this test clip under any circumstances. The uploader refuses this test prefix.

## Next acceptance criteria

- OAuth write scope explicitly granted by the channel owner in Google's own consent UI.
- Doctor confirms exact expected channel.
- A single resumable private test upload succeeds, YouTube returns its video ID, `videos.list` confirms `privacyStatus=private`, correct owner/channel/title and video processing.
- No publication date is assigned to the test, and existing production schedule remains unchanged.
- Any interrupted upload is reconciled manually before retrying: local ledger will block blind duplicate requests.

Historical status before approval: authorization pending. Current status: **OWNER OAUTH GRANTED; ONE PRIVATE-ONLY API TEST UPLOAD VERIFIED; AUTOMATIC PUBLISHING STILL DISABLED**.
