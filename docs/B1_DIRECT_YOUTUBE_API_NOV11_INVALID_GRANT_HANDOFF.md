# FlowMinute Lab Branch 1 — Direct YouTube API release state, Nov 11, 2026

**Owner instruction:** Schedule directly through the **YouTube Data API**, **do not open additional browser tabs** and do not schedule through Metricool or vidIQ. Do not repeat previously uploaded videos.

## Confirmed scheduled on the correct YouTube channel

All dates are November **2026**, local time zone **Asia/Kolkata (UTC+05:30)**, channel `UCCcL9Q_jqVq6LJmnYUSAFZA`.

| Date | Local slot | YouTube ID | Topic | Evidence |
| --- | --- | --- | --- | --- |
| Nov 13 | 11:00 | `TdAQYjplHa0` | Excel TRIM hidden-space Short | Authenticated vidIQ owner YouTube `scheduledPublishAt` readback, Private |
| Nov 13 | 16:00 | `OHHrOiZ3XQE` | Excel hidden-characters long | Authenticated vidIQ owner YouTube `scheduledPublishAt` readback, Private |
| Nov 13 | 20:30 | `1XSBoAkRH0s` | COUNT vs COUNTA Short | Authenticated vidIQ owner YouTube `scheduledPublishAt` readback, Private |
| Nov 14 | 11:00 | `_DJLdqAr2iI` | Chrome website notifications Short | **Direct YouTube Studio** visibility editor readback: Nov 14 11:00, GMT+05:30, private before publication |
| Nov 14 | 16:00 | `qA2YVfIuQRs` | Browser permissions long | **Direct YouTube Studio** schedule confirmation: Nov 14 16:00, GMT+05:30, private before publication. Source-exact title/description saved and verified after a new Studio load; timed original English SRT and thumbnail uploaded. |

**Total verified scheduled at this checkpoint: 5/15 (33.3%).** Do not upload duplicates of these exact five IDs.

## Incomplete sixth Studio upload — must inspect before retrying

On Nov 11, the `fm_20261114_thirdparty_access_short_en` Short (proposed **Nov 14, 20:30 IST**) was selected from the exact GitHub V4 release artifact through the existing Studio upload flow. Its original MP4, cover and SRT files passed SHA-256 verification; the exact metadata title/description and audience=not made for kids appeared in the upload dialog; copyright checks were clear. A timed-SRT file chooser was reached but the **final caption save, remote YouTube video ID, privacy and scheduled time were not confirmed**. It may remain as a **private Studio draft**. **DO NOT UPLOAD ANOTHER COPY** until authenticated YouTube Data API owner inventory confirms whether the first draft exists and its video ID. It is not counted among the five schedules.

Temporary MP4/SRT/cover files used during the Studio flow were deleted from the connected Windows computer. The owner subsequently instructed **no more browser tabs; use API exclusively**. Do not resume GUI tab manipulation under this instruction.

## Direct API outage reproduced on Nov 11, without browser interaction

- The project's existing local YouTube OAuth client and two prior **PUBLISH-scope** token files were located in the owner's existing authenticated workspace. A temporary script imported the existing publishing Python environment and attempted a **read-only** `youtube.channels.list(mine=true)` check, refreshing existing credentials in memory when necessary.
- Both prior publishing OAuth tokens **failed refresh with `RefreshError: invalid_grant`**. Neither produced a usable authenticated channel API session. The temporary probe source was deleted and token values were **never displayed or copied**. This is an authorization failure, not evidence that the YouTube Data API itself was removed.
- The separate protected GitHub environment `youtube-production` already contains `YOUTUBE_TOKEN_JSON`, last modified Nov 5, but its latest existing protected owner read-only check [42992511791](https://github.com/Tirthanand17/taskless-lab/actions/runs/42992511791) also failed with `OAUTH_REFRESH_FAILED`.
- The local existing CLI authorization routine invokes Google OAuth `run_local_server(open_browser=True)`; **DO NOT** invoke that CLI unchanged because the owner explicitly forbids opening tabs. Google OAuth owner reauthorization requires an explicit owner consent action in a secure Google login flow; it cannot be silently reconstructed from cookies or bypassed. Never paste token or client-secret material in ChatGPT.
- The existing GitHub publish action also requires owner-controlled exact-byte authorization and offline Ed25519 signature. Refrain from silently weakening or bypassing that gate.

## Remaining slots

| Date | 11:00 IST | 16:00 IST | 20:30 IST |
| --- | --- | --- | --- |
| Nov 14 | **CONFIRMED** | **CONFIRMED** | Third-party app access Short — upload/draft unverified; **duplicate fence** |
| Nov 15 | #SPILL! Short | Formula errors long | XLOOKUP Short |
| Nov 16 | Temporary Chat retention Short | Temporary Chat privacy long | Save Temporary Chat Short |
| Nov 17 | Google Sheets filter view Short | Team collaboration long | Protected range Short |

There are **10 unconfirmed release slots**, **9 without any known upload** and **1 with an incomplete Studio upload**. Original 15 final B1v4 video candidates and captions remain in prior successful GitHub Actions source runs and SHA-bound release packages. If direct YouTube API OAuth is restored, first read `channels.list(mine=true)` and the owner's uploads/video state, reconcile the incomplete short by exact title/time/source SHA before any new upload, and schedule remaining private originals one by one. Every success requires actual YouTube `status.privacyStatus=private`, `status.publishAt` matching target UTC and a verified video ID. Set targets only while still in the future.

**Blocker:** Owner must securely reauthorize the existing direct YouTube publishing OAuth scope; prior token files and the GitHub secret no longer refresh. **No additional scheduling may be truthfully claimed via the API until then.**
