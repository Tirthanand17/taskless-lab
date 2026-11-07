# ADR-0088 — B4f6 real owner-authenticated, read-only YouTube identity and Nov 5–11 coverage audit

**Date:** November 7, 2026 IST | Branch 1 + Branch 2 convergence | No video edits, uploads, publishing or approval.

## Motivation

B4f2 and B1q6 had extensive mocked `channels.list(mine=true)`, `playlistItems.list` and `videos.list` tests but no externally confirmed owner OAuth readback. Historical GitHub scheduled-upload receipts and 21-slot inventories cannot establish the current private YouTube schedule. Branch 2 cannot safely enable production without independently confirming which channel the stored credential actually owns.

This work adds a new **manually dispatched, read-only GitHub Actions workflow** and an audit module that reuse the existing, in-memory `YOUTUBE_TOKEN_JSON` secret-loading path *without using the publisher's upload CLI*. Only the user-selected GitHub `main` branch, exact repository and an explicit `confirm_readonly_channel_audit=true` can execute it. Job permission is `contents:read`; there is no trigger from a pull request, push or cron.

## Guarded real API calls

1. With an existing owner secret provided only by the `youtube-production` environment, call `channels.list(part=id, mine=true, maxResults=2)`; accept **one and only one** matching `UCCcL9Q_jqVq6LJmnYUSAFZA`. Unreadable tokens, a different channel, pagination ambiguity or any errors result in `OWNER_OAUTH_CHANNEL_NOT_INDEPENDENTLY_VERIFIED`, never a publisher enablement. The Google SDK may contact the OAuth refresh endpoint to refresh an existing token; it does not authorize a video write.
2. If owner identity is confirmed, call the previously implemented B1q6 complete Nov 5–11 uploader inventory (21 expected slots, four historical GitHub receipts) **using a wrapper that exposes only `.list()`** on `channels`, `playlistItems`, and `videos`; `insert/update/delete`, `captions`, `thumbnails` are not available through this wrapper.
3. Require the existing B1q6 scanner to exhaust the current uploader playlist, bind historical IDs to returned owner videos and the real private `status.publishAt` clock, and establish exactly 21 Nov 5–11 slots. If scan is incomplete, return `INCOMPLETE_STOP_NO_MUTATION` and **do not turn missing evidence into zero scheduled videos**.
4. Write only a one-day, sanitized GitHub artifact containing `owner_authenticated_youtube_channel_readback_verified`, `schedule_scan_complete`, aggregate confirmed-private slots, historical matches, current uploads count, collisions and audit timestamp. Never retain the OAuth JSON, refresh token, channel/video IDs, titles, description, thumbnails or individual article claims.
5. All logs are fixed safe status lines/counters; Google errors are redacted and exception causes discarded. The workflow destroys its temporary sanitized receipt at the end.

## Scope and limitations

- A successful read-only channel match proves that an existing token can access the **intended channel at audit time**. It does not prove that the token will remain valid, that it has upload/caption scopes, or that any video is factual, original or licensed.
- A complete 21-slot Nov 5–11 **readback inventory** is not the same as 21 completed live publications and cannot prove creative absence of rotating circles. A short scheduled for a past day can already have become public; the scanner counts currently private-scheduled status and keeps past/public historical states separate.
- No environment protection rules, secrets, owner signing keys, release flags, branch rules or user settings are created/changed by B4f6. Environment protection and independent owner release authorization must be configured and separately reviewed before attempting real `videos.insert`.
- This is a **read-only production connectivity milestone**, not activation of the multi-agent automatic 3/day publisher. CI only uses fake clients; only a successful owner-authorized manual production workflow supplies real evidence.
- Existing Branch 1 Nov 5–11 repair plans cannot be executed until the currently scheduled videos have been visually checked; no edit/reupload/delete occurred.

## Official references

- [YouTube Data API channels.list](https://developers.google.com/youtube/data/reference/rest/v3/channels/list) — `mine=true` requires OAuth, owner channel readback.
- [YouTube Data API playlistItems.list](https://developers.google.com/youtube/data/reference/rest/v3/playlistItems/list) — authenticated uploads-playlist membership.
- [YouTube Data API videos.list](https://developers.google.com/youtube/data/reference/rest/v3/videos/list) — owner video status and private `publishAt` readback.

## Test and acceptance

Offline adversarial tests check no owner-match bypass, no schedule report when pagination/slot evidence incomplete, no raw account/token/video/title leaks, no writable YouTube methods available on the audit client, strict manual main-only context, and no unguarded GitHub workflow triggers.

After PR checks succeed, an owner-authorized manually dispatched GitHub Actions run on `main` with `confirm_readonly_channel_audit=true` is necessary to establish real OAuth connectivity. A failed live audit **must not be represented as success** and must not invoke the publisher.
