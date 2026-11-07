# ADR-0085 — B4f3 read-only recovery of an already uploaded pending YouTube video

**Date:** 2026-11-07 IST | Flowminute Lab Branch 2 | No automatic video uploads, no release authorization.

## Specific failure found after B4f2

B4f2 now refuses a premature success receipt if YouTube's `processingDetails.processingStatus` is still `processing`, or the uploaded SRT caption track is still `syncing`. This is necessary but a normal YouTube upload can require additional processing time. Starting another `videos.insert` would create a duplicate; B4e9 permanent GitHub episode/slot attempt refs deliberately forbid that. The existing `*.pending.json` previously saved the remote video ID but **did not save the exact remote caption track ID**, so subsequent authenticated readback could not reconcile the same transcript.

## Changes

1. The manual publisher now saves the exact intended channel ID into both the pre-upload and existing-video pending checkpoints. After `captions.insert` returns an `id`, `scripts.youtube_pending_checkpoint_b4f3.save_existing_caption_identity` checks the already-uploaded pending state, exact remote video ID, and valid track ID and **atomically replaces the existing local pending JSON** with its specific caption ID, using an O_EXCL temporary file and fsync. This happens **before** the immediate B4f2 post-upload verification. A crash or failed write leaves a blocking pending marker; no automatic reinsert.
2. New `scripts.reconcile_pending_youtube_b4f3` accepts exactly one previously committed `state/published/NAME.json.pending.json` and matching `content/episodes/NAME.json`. Refuses symlinks, path traversal, missing media ID/caption ID/channel/hash, altered episode/title/description/locale and incorrect state. Owner-authenticated **read-only** calls:
   - `channels.list(mine=true,part=id)` to check current credential owner channel
   - `videos.list(part=snippet,status,processingDetails,contentDetails,id=...)` for exact private schedule, processed MP4 and thumbnail
   - `captions.list(part=snippet,videoId=...)` for the same previously reported uploaded caption ID in `serving` state
3. The separate **manual-only** GitHub Actions workflow `FlowMinute YouTube Readonly Recovery (NO UPLOAD)` runs only on main, repository `Tirthanand17/taskless-lab`, with a specifically enabled repository variable `FLOWMINUTE_READONLY_RECOVERY_ENABLED=true`, protected `youtube-production` environment and owner OAuth token. Permission `contents:read`; checkout disables credential persistence. It **cannot commit to main, create/upload/edit/delete YouTube videos, auto-launch, or retry videos.insert**. It produces only a seven-day sanitized GitHub artifact (hashes/times and honest read-only flags), then deletes its temporary output.
4. A strict no-secrets unit suite injects fake YouTube API clients to test wrong channel, missing or swapped caption ID, in-progress/failed processing, malformed pending receipt, symlinked local file, workflow context mismatch, no YouTube insert/write path, and one-time atomic caption checkpoint. No production OAuth, YouTube call or manual workflow_dispatch occurs during PR CI.

## References

- [Official YouTube videos processing status](https://developers.google.com/youtube/data/reference/rest/v3/videos) — processing status can remain `processing` after `videos.insert`; verify `succeeded` with an owner-authenticated `videos.list`.
- [Official YouTube captions.list](https://developers.google.com/youtube/data/reference/rest/v3/captions/list) — exact caption track videoId, language and serving status. `captions.list` requires a suitably authorized token, such as `youtube.force-ssl`; a narrowly scoped `youtube.readonly` token alone may not allow this endpoint.

## Operational boundary and remaining work

This is a **read-only reconciliation** workflow. It does not automatically poll periodically, persist protected production readiness in an independent database, or certify that the video actually appeared publicly at the scheduled time. When initial upload crashes **before** receipt of remote video ID or before exact caption ID is durably saved, this strict recovery cannot infer the missing ID. Owner must inspect the channel and reconcile manually, **not initiate another insert**. Processing can still take longer than one short action run.

The repo remains public and `state/published` receipts are repository-visible; the new *sanitized* recovery artifact excludes raw YouTube IDs, media/title/source text, token, signed release, and caption body. Its digest fields are **not** actual remote media byte verification.

This is still the **legacy manually approved publisher bridge**, not independent fully autonomous daily service. Actual facts, licensing, original final media approval, creator signing-key enrollment, YouTube OAuth, a protected durable state store, real private-first schedule results and seven-day 21/21 remote public releases remain unverified. The user must deliberately enable the read-only recovery variable and authorize the protected workflow to use owner credentials.

No owner token, publishing toggle, cloud database, billable API request, actual video or release was created by this change.
