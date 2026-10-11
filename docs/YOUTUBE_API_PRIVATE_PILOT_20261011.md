# FlowMinute YouTube API — private upload pilot prepared

Date: 2026-10-11 (Asia/Kolkata).

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

Status: **READY FOR OWNER PUBLISHING AUTHORIZATION, NO LIVE API UPLOAD PERFORMED**.
