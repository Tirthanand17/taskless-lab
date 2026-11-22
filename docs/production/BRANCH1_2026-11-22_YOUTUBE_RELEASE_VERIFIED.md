# Branch 1 — Sunday 22 November 2026 — YouTube release verified

**Channel:** FlowMinute Lab (`UCCcL9Q_jqVq6LJmnYUSAFZA`)  
**Release mode:** assisted Branch 1, original B1v5 video candidates  
**User consent:** user stated “Authorization done, videos approved” on 2026-11-22, following full-playback review instructions. This is conversational owner approval; it is not represented as a cryptographic signing event.  
**Status at verification:** **3/3 uploaded privately, 3/3 scheduled, 3/3 authenticated remote API readbacks, 3/3 manual YouTube Studio checks**. These releases were **not yet public at the checkpoint**; YouTube is set to publish at their scheduled local time.

| Video | Video ID / public URL once released | Time Asia/Kolkata | Scheduled UTC | Exact approved video SHA256 |
|---|---|---|---|---|
| Short 1 — Your CSV Deleted the Zeros in Your ID! Here’s the Fix #Shorts | [sKWO4F5hs9s](https://youtu.be/sKWO4F5hs9s) | **2026-11-22 19:00** | `2026-11-22T13:30:00Z` | `391abac1f9337fad052f43ac87dcd0d9fadc9074eeddc2b84798436257b8b1eb` |
| Long — Clean a Messy CSV in Python Without Deleting Good Orders | [8ht8nE2DnVs](https://youtu.be/8ht8nE2DnVs) | **2026-11-22 20:15** | `2026-11-22T14:45:00Z` | `38380ac479de5cbdc05c3691c91bc5d2e9be4d9f9c29cbd92fa182f581ef0e2f` |
| Short 2 — Your Python Merge Duplicated a Sale Without Warning #Shorts | [M4rSWzjl2jE](https://youtu.be/M4rSWzjl2jE) | **2026-11-22 21:30** | `2026-11-22T16:00:00Z` | `24d5eebb0b306cfdc0d208f4a1fbb1df1851f49be167b3f871d6af6bae7dfb2e` |

## Checks actually performed and passed

- Reauthorized the existing Google owner-scoped publisher, stored the new token only inside the existing secured `.flowminute-private` directory, and confirmed `channels.list(mine=true)` returned **exactly** `UCCcL9Q_jqVq6LJmnYUSAFZA`.
- Read-only channel inventory inspected **118 existing uploads** with complete pagination and no exact-title duplicate of these three candidates before upload. No repeat upload after ambiguous results.
- B1v5 source SHA-256 manifests validated against three exact local MP4s, original thumbnails, and reviewed timed English SRTs. Existing locked review manifests were preserved; separate owner-approved manifests were staged.
- Private `videos.insert` uploads confirmed unique YouTube IDs and private status before scheduling. All three HD processing checks succeeded.
- Publisher scheduling update initially returned a local post-write readback exception (`publish_at must be a string`). **No second schedule API mutation was attempted** for any ambiguous video. A guarded *read-only* reconciliation checked exact video ID, owner channel, title, private status, successful processing, and intended `status.publishAt`, then reconciled the private ledger to `scheduled_verified` for all three.
- All three original custom PNG thumbnails uploaded successfully through official `thumbnails.set`, including both Shorts. All three reviewed English SRTs uploaded through official `captions.insert`; `captions.list` returned `en` and `serving` for all three. No duplicate thumbnail/caption retries.
- Official `videos.list` independently checked exact title, description, tags, hashtags in description, channel, privacy, schedule, processing, audience `selfDeclaredMadeForKids=false`, and matching thumbnail variants. **13/13 audit checks passed per video.**
- Opened each exact video ID in owner **YouTube Studio** and visually inspected title, descriptions and hashtags, custom thumbnail, HD indicator, Scheduled visibility, plus the explicit Nov 22 time dialogs: **7:00 PM**, **8:15 PM**, **9:30 PM**, *private before publishing*. The channel Content > Videos list displays the long video as Scheduled and the Content > Shorts list displays both Shorts as Scheduled.
- Studio Languages pages initially showed language unset; fixed **Video language: English** on all three while explicitly unchecking the channel-wide default option. Final independent official API readback on all three confirmed `defaultAudioLanguage=en`, English captions still serving, all prior metadata/schedules unchanged. All 9/9 post-Studio checks passed per video.
- Wrote three non-secret exact-video receipts in the existing local publisher worktree `state/scheduled/fm_20261122_*.json`, including exact SHA, date in IST, YouTube ID, privacy, title, and documented source of verification.
- Ran the **existing publisher's** official `verify-queue --date 2026-11-22` against authenticated owner YouTube API: **checked=3, passed=3, needs_attention=0; process exit=0**.

## Evidence and no-secrets policy

The local Windows owner project folder `C:\Users\Dell\Desktop\youtube con\nov22-branch1-recovery\` contains:
- `FINAL_YOUTUBE_API_REMOTE_AUDIT_20261122.json` and `FINAL_YOUTUBE_OWNER_READBACK_AFTER_STUDIO_20261122.json`;
- exact media QA/owner approval manifests, sample data and scripts;
- Studio screenshots `STUDIO_MANUAL_short1_schedule.jpg`, `STUDIO_MANUAL_long_schedule.jpg`, `STUDIO_MANUAL_short2_schedule.jpg`, `STUDIO_ENGLISH_CONFIRMED_short1.jpg`, `STUDIO_ENGLISH_CONFIRMED_long.jpg`, `STUDIO_ENGLISH_CONFIRMED_short2.jpg`, `STUDIO_MANUAL_CHANNEL_CONTENT_AFTER_RELEASE.jpg`, `STUDIO_MANUAL_SHORTS_CONTENT_AFTER_RELEASE.jpg`;
- three SHA-bound `state/scheduled` receipts in the publisher worktree.

No OAuth token, refresh token, secret, unreleased media binary or private ledger was committed here. **Do not interpret a scheduled private status as proof the video has already published publicly**. The next analytics checks should use actual publication/retention data after 24h/48h/7d, not assumptions about virality.
