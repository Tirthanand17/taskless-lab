# Phase 4E.5 — Offline uploads playlist / video detail crosswalk

18 October 2026. Draft PR #4 only; no actual Cloudflare, Google, OAuth, live SQL or upload.

## Why necessary

The preceding offline Phase 4E.4 sanitization could collect *videos.list* shaped pages, but Google's recommended enumeration of channel uploads is:
1. With separately approved and privately protected YouTube OAuth (read-only), channels.list(mine=true, part=contentDetails) determines the uploads playlist for the EXACT owner channel.
2. playlistItems.list(part=contentDetails,snippet; playlistId=<uploads playlist>; maxResults<=50) supplies the channel's uploaded video IDs; follow every nextPageToken.
3. videos.list(id=<up to 50 IDs>,part=snippet,status,processingDetails) supplies video privacy, schedule, processing and owner fields for each uploaded video. Video ID coverage must equal playlist ID coverage; do not silently skip deleted/inaccessible videos.

A simple claimed videos.list page is NOT proof of complete channel uploads.

References (official):
- https://developers.google.com/youtube/data/reference/rest/v3/playlistItems/list
- https://developers.google.com/youtube/data/sample_requests
- https://developers.google.com/youtube/v3/docs/channels/list
- https://developers.google.com/youtube/v3/docs/videos/list

## New module and tests

autopilot/phase4e5_upload_playlist_crosscheck.py accepts *only* caller-supplied JSON-shaped objects, normalizes the original owner uploads playlist and follows up to 12 linked playlist pages (max 50/page, max 500 uploads). It checks the exact owner channel, uploads playlist ID, token chain, duplicates, missing terminal page, and matching sets of requested and returned videos.list IDs. It fails closed if details are omitted or do not match the uploaded ID inventory. Sensitive channel/video titles, descriptions and raw page tokens are not returned. It outputs the EXACT untrusted sanitized YouTube snapshot shape required by the existing Phase 4E.2 signed snapshot bridge.

The new test suite uses fabricated provider-shaped data for all positive/negative scenarios and checks no network or write claims. Unknown processing remains explicitly uncertain.

## Narrow authorization boundary (NOT acted upon)

Future actual 4E inspection needs explicit separate owner approval. Official least-privilege capabilities to request at that time:
- Cloudflare account token permission D1 Read, never D1 Write. D1 REST query uses POST even for SELECT/PRAGMA: the request method POST is not itself evidence of write authority, so a future collector must strictly allowlist SELECT/PRAGMA statements, never accept caller-supplied SQL, and verify the token scope.
- YouTube Data API scope https://www.googleapis.com/auth/youtube.readonly, not youtube.upload / youtube.force-ssl. Privately verify channels.list(mine=true) resolves the exact configured FlowMinute channel and that the uploads playlist belongs to that channel.
- Keep real credentials, raw DB rows, signed trust-root keys, private video IDs, nonce ledger and channel data outside the PUBLIC GitHub repository and its Actions logs. Set up independently verified collector enrollment and an owner-held nonce store.
- No new external account, connection, scope or consent was requested in this work. The present output cannot authenticate a real provider request. Even independently signed simulated evidence remains untrusted for migration and publishing.

Official least privilege references:
- https://developers.cloudflare.com/fundamentals/api/reference/permissions/
- https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/query/
- https://developers.google.com/youtube/v3/guides/auth/devices

Phase 4E provider-backed real data collection, 4F actual backed-up reversible migration, 4G authenticated production single writer, Phase 5 uploads and public publishing remain BLOCKED until separate approvals. ₹0/month recurring infrastructure cap, no Nirala/laptop, no charges and no production changes. Both PR #4 and PR #5 remain DRAFT and unmerged. The 21 production acceptance subphases across six incomplete major phases remain OPEN.
