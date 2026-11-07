# ADR-0090 — B4f7 classify owner OAuth failure without exposing tokens

**Date:** November 7, 2026 IST. Branch 1 (Nov05–11 inventory) and Branch 2 (independent cloud publishing). **READ-ONLY ONLY: zero YouTube writes.**

## Real evidence and why this matters

Real manually authorized YouTube owner read-only audits failed:
- [Run #42344627085](https://github.com/Tirthanand17/taskless-lab/actions/runs/42344627085) reported `owner_authenticated_youtube_channel_readback_verified=false`.
- [Run #42344990273](https://github.com/Tirthanand17/taskless-lab/actions/runs/42344990273), with the earlier safe secret-shape classifier, reported `OAUTH_CHANNEL_API_READBACK_UNAVAILABLE` before the Nov05–11 uploader-schedule scan. No YouTube uploads or mutations occurred. It **does not** prove which Google OAuth error occurred, what videos are scheduled, or that the channel has no videos.

The existing `verify_authenticated_owner_channel` deliberately removed exception causes, protecting credentials but losing the distinction between revoked refresh token, HTTP 403 scope/permission/quota, throttling, and Google API outages.

## Patch

1. In `scripts.owner_youtube_readback_b4f2`, continue throwing a sanitized constant-text exception on `channels.list(part=id,mine=true)` errors, with only two new **bounded structured attributes**: an allowed numeric HTTP response status (400, 401, 403, 404, 408, 429, 500, 502, 503, 504), or an exact recognized `google.auth.exceptions.RefreshError` / `TransportError` class. **No external exception message, URL, OAuth secret, HTTP body, refresh token, scope string, requested video ID or channel ID ever enters a diagnostic.**
2. In the separate B4f6 owner audit, allow only fixed categories: `OAUTH_REFRESH_FAILED`, `OAUTH_TRANSPORT_FAILED`, `YOUTUBE_CHANNEL_HTTP_401_OAUTH_REJECTED`, `YOUTUBE_CHANNEL_HTTP_403_SCOPE_QUOTA_OR_FORBIDDEN`, `YOUTUBE_CHANNEL_HTTP_429_THROTTLED`, `YOUTUBE_CHANNEL_HTTP_5XX_UPSTREAM`, and fixed categories for 400/404/408. No raw responses retained. Unknown cases remain `OAUTH_CHANNEL_API_READBACK_UNAVAILABLE`.
3. This changes **diagnostic reporting only**. The manual YouTube uploader still fails closed before `videos.insert` on every unverified channel; no retry, token refresh escalation, write permissions, YouTube changes, or automatic publisher enabling.
4. No new workflow, secret, artifact, or cloud dependency. Existing manual main-only `youtube-production` protected workflow remains owner-initiated; the test-only fake client injects response status and synthetic exception strings, verifies the no-write boundary and fails if a private token leaks.

## Safe interpretation of future failures

- **401 or refresh error**: owner may need to reauthorize and reinject **through protected GitHub secrets** (never through chat or repository commits).
- **403**: verify account permissions, YouTube API project access, OAuth scopes, or quota using Google Cloud console; 403 alone does not prove a specific cause.
- **429/5xx/transport**: likely service or transport availability and should not prompt a blind publisher retry.
- **Unknown**: do not infer success, or absence of scheduled Shorts; diagnose in protected account context before further steps.

The next successful read-only manual audit would establish actual owner channel identity and current Nov05–11 slot inventory; until then, current schedule coverage is **unverified**. Zero of twenty-one seven-day unattended real publications are independently verified.

Sources: [YouTube channels.list](https://developers.google.com/youtube/v3/docs/channels/list), [Google API HTTP errors](https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.errors.HttpError-class.html).
