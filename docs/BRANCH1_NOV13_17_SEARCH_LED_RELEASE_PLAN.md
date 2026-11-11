# Flowminute Lab — November 13–17, 2026 source-led Branch 1 editorial and render plan

**Readiness:** owner-review draft only; no November 13–17 video uploaded, signed or confirmed scheduled through this package.

## Real analytics basis (vidIQ connected channel, retrieved Nov 11)

- Exact connected channel: **FlowMinute Lab** `UCCcL9Q_jqVq6LJmnYUSAFZA`, 78 public videos, 5 subscribers, 1,658 lifetime views at audit.
- YouTube Studio via vidIQ, 2026-10-01 through 2026-11-10: Shorts **1,414 views / 293 engaged views / 20 seconds average view duration**; on-demand long-form **146 views / 81 engaged views / 75 seconds average**. The exposed `views` and `engagedViews` are *different metrics*. Do not call their ratio the official stayed-to-watch or Shorts swipe-away rate.
- Traffic Oct 15–Nov 10: YouTube Search **326 views / 79 engaged**, Shorts feed **468 views / 67 engaged**, indicating meaningful search intent but not proof of causation; audiences and publication ages differ. Average Shorts feed viewing 17 seconds, search 41 seconds among those traffic-source rows. This supports **testable long-tail problem solving** rather than more generic news.
- Top connected video: "Incognito Mode Is NOT Invisible" 124 analytics views but only 5 engaged views, on a newer 44-second Short. A historical earlier Short "13,000 Signed Up to Fix India's Websites With AI" had 113 views and 33 engaged views. Do not extrapolate small cohorts or declare a viral guarantee.
- Physical Nov12 MP4s had been upgraded in PRs #125–127 and split into four SHA-bound candidates in #128, but YouTube owner read-only GitHub job `42959487882` returned `OAUTH_REFRESH_FAILED`. vidIQ's ability to read channel analytics does NOT confer YouTube upload authority.

## Sources and editorial line-up

Every day: **Short 1 at 11:00 IST**, **Long at 16:00 IST**, **Short 2 at 20:30 IST**. Exact date-specific UTC schedule is **05:30Z / 10:30Z / 15:00Z**. All are *requested future plans*; none represent actual `status.publishAt`.

| Date | Short 11:00 | Long 16:00 | Short 20:30 |
| --- | --- | --- | --- |
| Nov 13 | TRIM leaves nonbreaking space (160) | Why visually identical Excel names fail to match | COUNT vs COUNTA: numeric versus filled cells |
| Nov 14 | Stop unwanted Chrome site notifications | Five site/browser/account permissions worth checking | Remove unused third-party Google account connections |
| Nov 15 | Diagnose blocked Excel #SPILL! | Three formula symptoms: spill, not-found, silently wrong match | XLOOKUP defaults exact but returns first matching record |
| Nov 16 | Temporary Chat and up-to-30-day safety retention | Six documented differences between Temporary and Regular Chat | What changes when you save a Temporary Chat |
| Nov 17 | Google Sheets filter view without changing teammates' view | Five collaboration mistakes: filters, protected ranges, sharing | Protected ranges restrict edits but are not security |

**Vendor citations (official):** Microsoft [TRIM](https://support.microsoft.com/en-us/excel/functions/trim-function), [COUNT versus COUNTA](https://support.microsoft.com/en-us/excel/ways-to-count-values-in-a-worksheet), [#SPILL!](https://support.microsoft.com/en-us/excel/how-to-correct-a-spill-error), [XLOOKUP](https://support.microsoft.com/en-us/excel/functions/xlookup-function); Google [Chrome notification controls](https://support.google.com/chrome/answer/3220216), [Account linked-app controls](https://support.google.com/accounts/answer/13533235), [Sheets filter views](https://support.google.com/docs/answer/3540681), [Protected sheet/range caveats](https://support.google.com/docs/answer/1218656); OpenAI [Temporary Chat](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt).

## Production instructions and limitations

- Original complete scripts are `content/nov13_17_2026/day_YYYY-MM-DD.json`. Exactly **15 videos, 10 Shorts + 5 longs**, all English, all fictional educational scenarios. No third-party stock/music/screen recordings or claims to have operated real user accounts.
- `autopilot/branch1_nov13_17_original_batch.py` draws native 1080×1920 Shorts and 1920×1080 long source/compare states, with distinct spreadsheet, browser-permissions, AI answer and folder/CSV art, precise original Kokoro English narration, subtitle-safe ASS + SRT, one-way scene highlights **without a spinner**, original cover and contact sheets, and exact-final AAC post-encode LUFS/true-peak checks. Final videos undergo *full FFmpeg decode*. 5 original daily bundles are only produced with successful main workflow dispatch and per-date GitHub artifacts.
- `.github/workflows/flowminute-b1-nov13-17-real-review.yml` has a CI-only source/physical-font test gate on PRs. Manual main workflows render each day's **two real Shorts and one long** on disposable GitHub runners, confirm all hashes, and retain an unapproved review artifact for 7 days. Actions intentionally have no owner Google token, publishing ability, local laptop work or remote YouTube writes.
- **Real-world unresolved steps:** owner full-watches each exact MP4, checks voice/captions/facts/rights, independently signs each SHA-pinned release with the protected Ed25519 owner signer, restores the expired YouTube refresh OAuth safely, verifies expected channel/duplicate status, uploads private and reads back exact YouTube `status.publishAt`, processing and caption track. A green rendering CI run is not a scheduled YouTube video.
- Scheduled as requested is the target; current verified external **Nov13–17 schedules = 0/15** until authenticated readback proves otherwise. Do not overwrite or duplicate any existing private channel uploads or scheduled November 11 content.

## Growth experiment

For each published Short at 24h, 72h, and 7d: record actual Shorts feed impressions/shown, stayed-to-watch when available, engaged views, avg duration/percentage watched, first-3s/20s retention where reports have data, comments, shares and subscribers. Long videos: impressions, CTR, first-30s retention, total engaged watch time and search traffic. Match publication ages rather than comparing raw counts. Keep the best hook and edit the worst drop-off; do not publish filler just to meet volume.

## Live owner-channel duplicate protection (Nov 11)

Authenticated vidIQ `user_videos` returned current titles and privacy states, including **already public** November 9 `Excel Remove Duplicates? Check THIS Before You Click`, November 9 `Stop Copy-Pasting CSVs! Combine Monthly Files in Excel Power Query`, and November 10 `AI Made Up a Citation? Use This 5-Step Fact-Check Workflow`. A first draft of this new 5-day slate repeated these concepts too closely. **Rendering was deliberately cancelled for November 13, 16 and 17 and these three dates were rewritten**: Nov13 COUNT/hidden characters, Nov16 Temporary Chat and saved-chat retention, Nov17 Google Sheets filter views/permission restrictions. Nov14/15 original batches were not cancelled.

Do not promote an episode solely because a script or video passes CI if it reuses a topic already posted. Manual original-content and owner review remain required.

## Physical AAC discovery and correction (Nov 11)

The November 15 three-video real H264/AAC review run `42973951929` fully succeeded (33.765-second #SPILL! Short, 35.471-second XLOOKUP Short, 171.305-second formula-errors long). The original November 14 source run `42973947505` produced its two complete Shorts (38.322 and 32.751 seconds) but **refused** the 12-scene long when the independent exact-encoded B4g5 final AAC measurement did not pass; since the original exception was previously sanitized, the detailed first-run reason was unavailable. No failed artifact was promoted.

The renderer now retains its strict final LUFS and oversampled true-peak band. When the *actual* postencode AAC alone is outside that band, the code may apply **one** audio-only FFmpeg remaster with source video stream copied, conservative TP target of -2.5 dBTP, full independent H264/AAC decode, and strict final SHA-bound measurement again. Any second failure, non-audio defect, or inconsistent identity **still fails** the job. Exact owner voice listening, captions and publication approval remain unverified. This fallback never publishes.
