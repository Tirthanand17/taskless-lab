# Clivox A7 — Separate read-only YouTube OAuth and channel binding

**Status (2026-11-12):** Read-only OAuth/token-refresh API client, strict authenticated channel check, limited uploads-playlist preview, and adversarial CI implemented. **No real Clivox OAuth client/token/Google consent is enrolled.** Current CI uses synthetic fixture responses, not real private YouTube data.

## Official requirements
- Google: https://developers.google.com/youtube/data/guides/authentication — `channels.list(mine=true)` requires OAuth 2.0. API keys cannot authorize access to private owner/channel information. Do not use a service account for the normal owner YouTube channel.
- Google read-only scope: `https://www.googleapis.com/auth/youtube.readonly`. This stage does **not** request `youtube.upload`, `youtube`, `youtube.force-ssl`, or analytics scopes.
- Google refresh tokens: https://developers.google.com/identity/protocols/oauth2 — a user-initiated OAuth consent flow with `access_type=offline` is needed for server/CI access without a browser session.
- Google testing mode: an External-consent-screen app in `Testing` commonly issues refresh tokens that expire in **7 days** for non-profile scopes. The owner must configure and verify the correct OAuth app lifecycle before persistent CI authorization.
- GitHub actions secrets/environment rules: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## Follow-up: A8 bounded owner uploads inventory verification

The [owner-only A8 uploads inventory runbook](../a8/OWNER_UPLOAD_INVENTORY_READBACK.md) extends the earlier one-page A7 preview to owner-authorized bounded full pagination plus `videos.list` privacy/schedule metadata checks, using the **same already-protected `clivox-readonly` environment** once separately approved. This follow-up is mock-tested only and does not imply owner OAuth secrets or live remote inventory exists.

## Account identity invariant
1. Get an OAuth access token using credentials of a **new, Clivox-specific** Google OAuth client. No FlowMinute Lab token reuse, fallback, or untrusted browser-session cookies.
2. GET `https://www.googleapis.com/youtube/v3/channels?part=id,snippet,contentDetails&mine=true` using the bearer token **in an Authorization header** (not query string).
3. Require exactly **one authenticated channel**, ID `UCfPEvy0SefE_5nNlYlY_CyQ`, and corresponding uploads playlist `UUfPEvy0SefE_5nNlYlY_CyQ`. A token for FlowMinute Lab (`UCCcL9Q_jqVq6LJmnYUSAFZA`) **must stop** immediately.
4. Only after identity matches, GET the first page of `playlistItems.list` for that one playlist. Treat it as a **sample**, not proof of zero private/scheduled videos or a complete release ledger.
5. Never print OAuth tokens, raw responses or potentially private video IDs in a public Actions log or artifact. The summary records counts, not a private inventory.
6. Any identity mismatch, 401/403, `invalid_grant`, wrong scope, missing scope evidence or malformed API data is a **hard stop**, not an invitation to try another account's token.

## Protected live-bridge status (GitHub configured, Google not connected)

- GitHub `clivox-readonly` environment **created and verified** on 2026-11-12: required reviewer `Tirthanand17`, main-only deployment branch policy, administrator bypass disabled; self-review allowed. Its secret count is **0**.
- New separate manual-main-only read-only bridge: `scripts/branch3_a7_live_readonly_bridge.py` and `.github/workflows/branch3-clivox-a7-live-readonly.yml`; all production credentials currently **missing**, so it cannot make a live connection.
- Independent no-secret test workflow: `.github/workflows/branch3-clivox-a7-live-bridge-qa.yml`.
- Secure owner steps: [OWNER_CONNECTION_SETUP.md](OWNER_CONNECTION_SETUP.md). No OAuth tokens should be copied into chat or public GitHub files.

## Implemented code (read-only, not live-connected)
- `scripts/branch3_a7_readonly_youtube.py`: fixed-host HTTPS only to `oauth2.googleapis.com/token` for refresh (POST) and `www.googleapis.com/youtube/v3/channels` or `/playlistItems` for read-only GET. No YouTube write endpoints.
- `scripts/test_branch3_a7_readonly_youtube.py`: synthetic API + token-refresh tests, wrong-channel and multiple-channel failures, over-broad scope rejection, forged metadata and secret-leak defenses.
- `branch3/a7/readonly-oauth-policy.json`: read-only scope; live OAuth disabled; all publisher flags false; no secrets, owner key or identity claims.
- `branch3/a7/fixtures/*.json`: **SYNTHETIC_NOT_FROM_GOOGLE** channel and empty-inventory responses.
- `.github/workflows/branch3-clivox-a7-readonly-preflight.yml`: PR/manual read-only, no secrets, no real HTTP calls, public-safe fixture artifact only.

### Run CI
Open the A7 workflow in GitHub Actions and run the offline test. It uses only fixtures; passing **does not** confirm Clivox OAuth is connected.

## What must happen before turning on live read-only integration
1. Owner creates or selects a **new dedicated Google Cloud OAuth 2.0 client** and enables the YouTube Data API v3, using the **Google account/Brand Account selector for Clivox**. The existing FlowMinute Lab connection must stay untouched.
2. Owner reviews the OAuth consent screen, Google app publishing/test-user policy, and grants only `youtube.readonly` to the Clivox-specific client. The Google OAuth callback/refresh-token acquisition must take place through a separately verified, secure owner-controlled flow—not by pasting tokens or authorization codes into chat or a public GitHub issue.
3. Owner configures a **separate protected GitHub environment** (suggested `clivox-readonly`) with actual required-reviewer/branch restrictions verified. The earlier `youtube-production` environment is **not** Clivox's environment.
4. Only there, securely install separately scoped secrets named `CLIVOX_A7_READONLY_CLIENT_ID`, `CLIVOX_A7_READONLY_CLIENT_SECRET`, and `CLIVOX_A7_READONLY_REFRESH_TOKEN`. These names are reserved; values are **NOT present** in this repository and must not be written to logs or artifacts.
5. Have security and owner review a **separate deployment PR** before changing `live_run_allowed` or adding a secret-consuming GitHub Action. Only the main branch and approved actor should gain access. Production workflow does not exist yet.
6. When permitted, a read-only live run must verify `channels.list(mine=true)` exact identity and inspect a limited first-page upload sample. It must never pretend the sample is an exhaustive scheduled/private video audit.
7. For upload/scheduling in A8, a new **separately authorized** Google upload grant plus protected release gate is required. Do not upgrade this read-only refresh token's scope or use it to write.

## Endpoint summary
| Stage | Method | Host/path | Credentials | Release privilege |
|---|---|---|---|---|
| OAuth refresh | POST | oauth2.googleapis.com/token | Clivox-only read-only OAuth client / refresh token | None |
| Owner identity | GET | www.googleapis.com/youtube/v3/channels?mine=true | Temporary bearer | None |
| Bounded upload sample | GET | www.googleapis.com/youtube/v3/playlistItems | Temporary bearer; only after ID verified | None |

## Invariants / unresolved dependencies
- Phone verification of Clivox is already complete, but it does not authorize use of the YouTube API.
- A7 read-only **client and tests** exist; A7 live **Google authorization and credentials** do not.
- Branches 1 and 2 remain paused. Public primary GitHub repository remains metadata/code only. Creator allowlist empty, no licensed footage, no upload/schedule activity.
- Passing an OAuth identity check does not establish any source clipping permission, guarantee YouTube monetization or mean an uploader is enabled.
