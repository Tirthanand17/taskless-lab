# FlowMinute Lab — November 13–17 YouTube publishing readback (November 11, 2026)

**Scope:** Only actual verified data from the authenticated vidIQ owner channel (`UCCcL9Q_jqVq6LJmnYUSAFZA`) and GitHub protected read-only OAuth audit, no inferred publication. The owner approved a private-first upload/scheduling fallback. Do not call finished renders or vidIQ drafts "scheduled."

## 1. Three schedules actually confirmed in owner YouTube readback

On Nov 11, authenticated vidIQ `vidiq_update_video` returned `status=updated`, `privacyStatus=private`, correct target `publishAt`, and the subsequent independent owner `vidiq_user_videos(privacyStatus=[private])` returned the **same exact `scheduledPublishAt`** for each video ID:

| IST time | UTC time | Exact video | YouTube ID | Verified outcome |
|---|---|---|---|---|
| Nov 13 11:00 | 2026-11-13T05:30:00Z | Why Excel TRIM Didn't Remove That Hidden Space #Shorts | `TdAQYjplHa0` | Private, processed and scheduled |
| Nov 13 16:00 | 2026-11-13T10:30:00Z | Excel Values Look the Same but Won't Match? Fix Hidden Characters | `OHHrOiZ3XQE` | Private, processed and scheduled |
| Nov 13 20:30 | 2026-11-13T15:00:00Z | Excel COUNT Says 2 but You Have 4 Values? Here's Why #Shorts | `1XSBoAkRH0s` | Private, scheduled (was still `uploaded` at earliest readback) |

These three are the **only independently confirmed Nov13–17 schedules**. Never upload those clips again. Owner channel verified before every release: `UCCcL9Q_jqVq6LJmnYUSAFZA`.

## 2. One later upload without a confirmed schedule — MUST NOT DUPLICATE

The November 14 11:00 Chrome notification Short (`fm_20261114_chrome_notifications_short_en`, title `Chrome Website Notifications Won't Stop? Fix the Permission #Shorts`) was submitted through a vidIQ zero-credit draft specifying `privacyStatus=private` and future publishAt; it returned YouTube video ID **`_DJLdqAr2iI`**. Independent `vidiq_social_post_status` reported `status=completed` but `scheduledFor=null`. Independent `vidiq_social_post_list` likewise showed `completed`, `scheduledFor=null`. Because owner `vidiq_user_videos` needs 5 credits and quota is exhausted, **actual YouTube visibility and `status.publishAt` for this upload are NOT VERIFIED**. Do not claim private or scheduled, do not upload it again, do not try to publish its duplicate draft. The owner needs to inspect it in YouTube Studio (Content, filter title/ID, Visibility), set **Private** if needed, and use Schedule for **2026-11-14 11:00 IST** if not already scheduled. This is the first urgent unresolved item.

## 3. Provider operational blockers verified November 11

- vidIQ `vidiq_balance` returned `totalCredits=0`, `renewableCredits=0`, `maxRenewableCredits=150`, `addOnCredits=0`, `renewableResetsAt=2026-12-02T02:43:22.365790Z`. The required `vidiq_user_videos` owner readback and `vidiq_update_video` scheduling actions cost 5 credits each. The provider explicitly said **do not retry** a rejected credit-cost action. Future time verification is therefore blocked through this integration until more credits are legitimately available.
- GitHub protected `youtube-production` read-only owner workflow [42992511791](https://github.com/Tirthanand17/taskless-lab/actions/runs/42992511791) independently returned `B4F6_REDACTED_FAILURE_CLASS=OAUTH_REFRESH_FAILED`, `B4F6_REAL_OWNER_CHANNEL_READBACK_VERIFIED=false`. No write. vidIQ MFA succeeding does not refresh the unrelated GitHub token.
- vidIQ draft creation/update with future `publishAt` returned a correct date, but independent `vidiq_social_post_draft_get` returned `scheduledFor=null` for the 15 former drafts. A subsequent **actual** future-draft `social_post_publish` for Nov14 Chrome Short returned `completed, scheduledFor=null`; thus do not use this path as a reliable scheduler.
- There are **15** final B1v4 H264/AAC owner-review video files and SHA-bound release packages, all imported into the vidIQ media library, but only the three Nov13 slots have authoritative future schedule confirmation.
- A third-party alternative, Metricool, supports YouTube Shorts and long-video scheduling according to [Metricool's official guide](https://help.metricool.com/schedule-and-publish-on-youtube-gof0k), but **it is not connected in this chat** as of the audit. Connecting must be completed by the owner. Do not claim it is ready for owner channel actions.

## 4. Required remaining slots — do not duplicate YouTube uploads

| Date | 11:00 AM IST Short | 4:00 PM IST long | 8:30 PM IST Short |
|---|---|---|---|
| Nov 13 | **CONFIRMED** `TdAQYjplHa0` | **CONFIRMED** `OHHrOiZ3XQE` | **CONFIRMED** `1XSBoAkRH0s` |
| Nov 14 | **Uploaded, schedule unverified** `_DJLdqAr2iI` | Browser permissions — NOT YET UPLOADED | Old Google third-party app access — NOT YET UPLOADED |
| Nov 15 | Excel #SPILL! — NOT YET UPLOADED | Formula-error walkthrough — NOT YET UPLOADED | XLOOKUP first match — NOT YET UPLOADED |
| Nov 16 | Temporary Chat retention — NOT YET UPLOADED | Temporary vs regular Chat — NOT YET UPLOADED | Saving Temporary Chat — NOT YET UPLOADED |
| Nov 17 | Google Sheets filter views — NOT YET UPLOADED | Team collaboration — NOT YET UPLOADED | Protected ranges — NOT YET UPLOADED |

All intended times are local IST (UTC+05:30): **11:00 IST = 05:30Z**, **16:00 IST = 10:30Z**, **20:30 IST = 15:00Z**. The user required 2 Shorts and 1 long video daily. No date/time may be changed without owner approval. All videos should be private until scheduled publication.

## 5. Fail-closed continuation

Continue ONLY through a verified authorized interface with enough quota to schedule or through the owner's YouTube Studio. Do not call `vidiq_social_post_publish` again to work around its null schedule readback. A protected private upload alone is not a confirmed scheduled YouTube video; do not promote drafts, generated artifact manifests, or plugin connector success to scheduled status. Independently verify exact owner channel, per-video YouTube ID, privacy Private, and `publishAt` at each intended UTC time. For videos already uploaded, edit the existing YouTube ID instead of uploading another.

**Verified release progress: 3 / 15 scheduled (20%). 12 / 15 publication times not verified; one of those 12 is already uploaded with missing readback.**
