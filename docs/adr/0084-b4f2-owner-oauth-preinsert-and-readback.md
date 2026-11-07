# ADR-0084 — B4f2 owner channel BEFORE upload and processed media readback AFTER upload

**Date:** 2026-11-07 IST | Branch 2 production bridge hardening. **YouTube upload/production automation remains disabled.**

## Problem found on the actual main branch

The existing `scripts/publish_youtube.py` uses a service built from `YOUTUBE_TOKEN_JSON` then calls `videos.insert` without first verifying that the token belongs to the intended owner channel. It only checked `snippet.channelId` in a `videos.list` response **after** the video had already been uploaded. A stale or swapped authorized account could therefore send a real upload to the wrong channel, with no safe way to move the uploaded video.

The old post-upload check also accepted `status.uploadStatus=uploaded` as a verified schedule, did not request `processingDetails`, ignored `contentDetails.hasCustomThumbnail`, and never independently read back the uploaded caption track ID. These are incomplete technical readiness claims.

## Official current API references

- [YouTube channels.list](https://developers.google.com/youtube/data/reference/rest/v3/channels/list): `mine=true` is an authenticated **read-only** query returning the channel(s) owned by the logged-in OAuth identity. Use `part=id`; it is not a write permission or channel-ownership proof for any other account.
- [YouTube videos resource](https://developers.google.com/youtube/data/reference/rest/v3/videos): `processingDetails.processingStatus=succeeded` is the required postprocessing state; `uploaded` alone is not processed. `contentDetails.hasCustomThumbnail` can be read for a confirmed custom cover; `status.publishAt` requires `private` and a never-published video. YouTube may return time with RFC3339 offset; compare exact **UTC instant**, not raw string.
- [YouTube captions.list](https://developers.google.com/youtube/data/reference/rest/v3/captions/list): read back the exact `id` returned by `captions.insert` and confirm its `snippet.videoId`, `language`, `status=serving`, and `isDraft=false`. This is a read-only API check and does **not** prove byte-for-byte SRT text identity; `captions.download` is separate.

## Implementation

1. `verify_authenticated_owner_channel(service, expected_id)` executes **one** `youtube.channels().list(part="id", mine=True, maxResults=2)` **before** B4e9 GitHub reservation refs and before `videos.insert`. Require one and only one matching channel, no next page and (if supplied) `pageInfo.totalResults==1`. Any wrong identity, zero results, multiple results, expired token, missing scope, network error or malformed response blocks before upload. Errors are redacted to avoid OAuth credential leaks.
2. `scripts/publish_youtube.py` captures the exact caption-track `id` returned by `captions.insert`. If absent, leave the pending upload checkpoint; NEVER start another `videos.insert`.
3. Once uploaded, read `videos.list(part=snippet,status,processingDetails,contentDetails,id=...)` and `captions.list(part=snippet,videoId=...)`. Require exact video ID, channel, title, description, intended private schedule, processing status **succeeded**, upload status **processed**, thumbnail present, synthetic-media and audience declarations matching original request, and the **specific** uploaded caption ID in serving/non-draft status with matching language.
4. If YouTube has not finished processing or captions remain syncing, **do not mark the upload scheduled_verified**. Leave the existing B4e9 local+GitHub no-retry attempt fence and remote video ID pending for owner-authenticated, **read-only** reconciliation. Do not blindly re-upload and do not claim 21/21.
5. New offline adversarial tests cover wrong/multiple/zero OAuth channels, unreadable or wrong processing status, missing thumbnail, wrong video/channel/title/description/time, changed synthetic/audience flags, missing caption ID and syncing/failed captions, leaked-exception suppression, and source-order guarantees. Dedicated no-secret publisher preflight CI runs them.

## Operational cautions

- Both methods are read-only, but an actual YouTube token must support the relevant authorized `mine` and captions endpoints. For captions list, Google documents the `youtube.force-ssl` or `youtubepartner` scope. If the current owner OAuth token lacks the required scope, the script **will now stop rather than permit unverified publication**.
- Immediately after upload, processing of a four-minute long video or captions may still be underway. This patch is intentionally fail-closed; **a separate authenticated read-only recovery/polling workflow** is the next requirement for unattended reliability. There is no new automatic retry of `videos.insert`.
- No actual YouTube MP4 hash can be verified solely from API resource metadata. The signed B4f1 local media SHA, complete owner watch, facts/rights and any caption-text comparison are separate gates. A successful owner identity/API readback cannot substitute for them.
- No YouTube client credential, owner key, publish flag, new cost, deployed cloud account, manual artifact export or live API call was created in this PR. The 7-day independently verified release proof remains **0/21**.
