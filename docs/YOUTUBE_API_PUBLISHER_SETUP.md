# FlowMinute Lab — YouTube API Publisher: setup and safety guide

Status: **Implemented on feature/youtube-api-publisher-v1; no Google credentials connected or live upload tested yet.**

The new script is scripts/youtube_publisher.py. It uses Google's official YouTube Data API v3, not browser automation. Every write requires explicit confirmation, and every publish attempt starts as private.

## What is built

- Offline QA validation of original episode metadata, actual MP4 files, SHA-256 approval hashes, ownership/channel ID, and a future publication time with timezone.
- Desktop browser OAuth in READ mode and a separate PUBLISH mode. No service accounts or anonymous API keys for uploading.
- Read-only doctor to verify the connected YouTube channel and prevent uploading to the wrong Google / Brand Account.
- Resumable PRIVATE video upload, and a persistent local ledger that blocks duplicate retries after ambiguous responses.
- Optional separate upload of approved custom thumbnails and verbatim human-reviewed captions.
- Separate schedule operation. Requires private, never-published video with exact title and channel match, then confirms publishAt from a fresh API read.
- Verification command to inspect a video's actual privacy and scheduled publication time without writing.

## Important publishing rules

1. Never use this publisher to re-upload any October 11 or October 12 video. Those already have YouTube Studio receipts recorded in state/scheduled/.
2. All new releases require qa_approved=true, a genuine video_sha256, explicit made_for_kids and synthetic_media booleans, and the exact UC... expected_channel_id.
3. The publication datetime MUST specify an offset, for example 2026-10-15T11:00:00+05:30 for 11 a.m. India time. Scheduling into the past is rejected because the API could otherwise publish immediately.
4. The local private ledger at .flowminute-private/youtube-ledger.json records the state before network writes. If a request becomes uncertain, DO NOT retry blindly. Inspect the video in Studio and reconcile manually.
5. Never commit OAuth client secrets, refresh tokens, local ledger, or real credentials to GitHub. Never paste them in chat or CI logs.
6. Existing generated recap-like subtitle cues do not replace exact accessible captions. Caption API import is blocked until the SRT is checked against the actual spoken narration.
7. The YouTube API is not a full substitute for all settings in YouTube Studio. Classification as a Short is ultimately determined by YouTube, not a separate upload endpoint.

## Step A — Google Cloud setup (one-time user action)

1. Visit https://console.cloud.google.com/ with the Google account that controls FlowMinute Lab.
2. Create/select a Google Cloud project (without adding payment information unless Google explicitly requires something you agree to). Enable YouTube Data API v3 under API Library.
3. Configure the Google Auth Platform / OAuth consent screen, including audience, support email, and test users if the app is in Testing mode.
4. Create an OAuth client of type **Desktop app** and download the client JSON.
5. Store that JSON only in your local personal secret directory, e.g. C:\Users\Dell\.flowminute-private\client_secret.json. Do not place it in the repository.
6. During the local OAuth authorization, choose the correct Google/YouTube Brand Account and approve the requested scopes. Read-only authorization and publisher authorization use separate token files.

Note: Google OAuth apps in Testing mode can have expiring refresh tokens, so unattended scheduling should not be enabled until token behavior is verified. Only grant publishing scopes after you understand and accept them.

## Step B — Windows commands (PowerShell from repository root)

    py -3.11 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r scripts/youtube_api_requirements.txt

Read-only OAuth first:

    .\.venv\Scripts\python.exe scripts/youtube_publisher.py authorize --client-secret "$HOME\.flowminute-private\client_secret.json" --token-file "$HOME\.flowminute-private\youtube_readonly_token.json" --mode read

Confirm the exact YouTube channel ID (replace the placeholder with your own):

    .\.venv\Scripts\python.exe scripts/youtube_publisher.py doctor --token-file "$HOME\.flowminute-private\youtube_readonly_token.json" --expected-channel-id "UCxxxxxxxxxxxxxxxxxxxxxx"

Only after doctor passes and after user consent to publishing:

    .\.venv\Scripts\python.exe scripts/youtube_publisher.py authorize --client-secret "$HOME\.flowminute-private\client_secret.json" --token-file "$HOME\.flowminute-private\youtube_publish_token.json" --mode publish

## Step C — Prepare a NEW episode only

Start from examples/youtube_release.example.json and replace every placeholder. For video_sha256 compute:

    (Get-FileHash 'C:\path\to\final-video.mp4' -Algorithm SHA256).Hash.ToLower()

Required fields: episode_id (must match episode JSON id), episode_path, video_path, video_sha256, expected_channel_id, publish_at, made_for_kids, synthetic_media, qa_approved (true only after watching and accepting final edit).

Optional: thumbnail_path with thumbnail_sha256, caption_path with captions_reviewed=true and caption_sha256 (only for true/verbatim captions). All paths are relative to the release manifest file or absolute paths. File hashes prevent unnoticed last-minute swaps.

**Safe dry run:** 

    python scripts/youtube_publisher.py prepare C:\path\release.json

**Explicit live private upload** — only after OAuth, QA and approvals:

    python scripts/youtube_publisher.py upload C:\path\release.json --token-file "$HOME\.flowminute-private\youtube_publish_token.json" --confirm-private-upload

**Optional approved assets:**

    python scripts/youtube_publisher.py assets C:\path\release.json --token-file "$HOME\.flowminute-private\youtube_publish_token.json" --confirm-assets

**Schedule that verified private video:**

    python scripts/youtube_publisher.py schedule C:\path\release.json --token-file "$HOME\.flowminute-private\youtube_publish_token.json" --confirm-schedule

**Read-only remote status:**

    python scripts/youtube_publisher.py verify --video-id VIDEO_ID --expected-channel-id "UCxxxxxxxxxxxxxxxxxxxxxx" --token-file "$HOME\.flowminute-private\youtube_readonly_token.json"

A live schedule is considered successful only after the new API response and an independent videos.list verification agree on the future timestamp and private status.

## Linux

Use python3 -m venv .venv and .venv/bin/python rather than the Windows executable. The same subcommands and safety gates apply.

## Failure handling

- Wrong channel, missing OAuth permissions or mismatched title: abort, inspect account.
- Unresolved upload/schedule/caption/thumbnail: stop and check YouTube Studio. Do NOT delete the ledger file or automatically retry.
- A pre-existing Studio scheduled video is not eligible for this publisher's new-upload path.
- Any incorrect child-directed or realistic synthetic-media flag must be reviewed before uploading.
- If an OAuth file is mistakenly committed to Git, revoke the credentials immediately and remove the exposed secrets from history; .gitignore does not protect committed history.

## Source references (reviewed October 10, 2026)

- YouTube quota calculator, last updated October 8: https://developers.google.com/youtube/v3/determine_quota_cost
- Uploads: https://developers.google.com/youtube/v3/docs/videos/insert
- Scheduling rules: https://developers.google.com/youtube/v3/docs/videos/update
- Metadata publishAt: https://developers.google.com/youtube/v3/docs/videos
- Thumbnails: https://developers.google.com/youtube/v3/docs/thumbnails/set
- Captions: https://developers.google.com/youtube/v3/docs/captions/insert
- OAuth: https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps

The current upload reference says uploads from unverified API projects are NOT blanket-restricted to private-only; individual OAuth publishing, account policy, or app-review limitations may still apply. Always test with a harmless private file before automating future releases.

## Remaining work

1. Human sets up/authorizes OAuth Desktop client, validates the actual channel ID and scopes.
2. Perform a one-time harmless PRIVATE test upload only, confirm title/privacy, thumbnail capability and quota in real account.
3. Test scheduling a new approved private test video at a future safe date; confirm Studio read-back, then remove test content if desired.
4. Later add automatic quality-gated scheduling triggers, secure cloud token storage, sanitized GitHub receipts and analytics feedback. None of these are turned on yet.
