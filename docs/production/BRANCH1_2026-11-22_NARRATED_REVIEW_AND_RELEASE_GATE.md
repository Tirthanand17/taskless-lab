# Branch 1 — 2026-11-22 media candidates and blocked YouTube release

**Date:** Sunday 2026-11-22 Asia/Kolkata  
**Channel:** FlowMinute Lab `UCCcL9Q_jqVq6LJmnYUSAFZA`  
**Scope:** user-requested 2 Shorts + 1 long-form, assisted (Track A).  
**Overall verdict: NOT APPROVED, NOT UPLOADED, NOT SCHEDULED.**

## Produced locally for owner review, not committed media

All non-secret working files are in the existing authorized Windows media workspace, `youtube con/nov22-branch1-recovery/`. This record is source/status only; no credentials, private video binaries or tokens are committed.

| Video | Verified duration | Dimensions / FPS | H264/AAC full decode | SRT cues | Exact MP4 SHA256 |
| --- | ---: | --- | --- | ---: | --- |
| `short1_FINAL_CANDIDATE_REVIEW_REQUIRED.mp4` — CSV leading-zero ID | 27.292 s | 1080×1920 / 24 | PASS | 10 | `01f872176328fcdd6ec73a806b439fed134e509b01acb2b09a5f9737e5ebc995` |
| `short2_FINAL_CANDIDATE_REVIEW_REQUIRED.mp4` — Excel nonbreaking space | 28.042 s | 1080×1920 / 24 | PASS | 9 | `49777ad5dcbf0c0f4fcd3392cede0a98193b0aa242f48b43656d546af65ce190` |
| `long_FINAL_CANDIDATE_REVIEW_REQUIRED.mp4` — safe CSV cleaning | 113.667 s | 1920×1080 / 24 | PASS | 37 | `7cd4faeb1f941eaac6ccc93b9ba2d75f18d1e0816fb4e247f8ebcc940f5abad1` |

**Technical QA:** Full video and audio decodes pass, SRT cues end before each video end, original static data demonstration verified. 3 custom PNG thumbnails generated; YouTube title, description, tags and hashtags drafted. Two Shorts have different generated voice personas. The long narration was synthesized in five sections, with measured-duration caption offsets. The previous recurring spinner is absent.

**Data proof:** Generated 9-row CSV plus executed `verified_demo.py`: first ID `'00123'`, normalized name `'Maya'`, 1 exact duplicate removed, 2 conflicting rows and 1 missing-amount row for review, 5 ready rows totaling **₹1,218**. No real customer data.

## Editorial/media still NOT APPROVED

- Automated decode success does **not** mean natural narration was listened to. Full headphones/phone playback and narration rights remain unverified.
- Contact-sheet visual inspection found the novel rendered terminal cards still too uniform, with code size/creative pacing inferior to adopted **B1v4** native case UI. This is a **creative QA fail**, not a launch-ready format. Earlier missing-font symbols were corrected, but the overall visualization still needs a differentiated, demonstrable redesign.
- Real app/demo workflows and genuine source/context should be shown before final approval; do not present a graphic as real software capture.
- Owner has **not** reviewed or signed the exact file hashes. No release reservation is granted.

## YouTube API result, 2026-11-22

Owner-connected vidIQ confirmed exact channel in a separate identity-only call, but paid-credit retrieval/update is unavailable until December 2. An authorized **read-only** direct YouTube API calendar request on the existing publisher virtual environment was attempted. Refreshing the existing stored OAuth credential returned `google.auth.exceptions.RefreshError: invalid_grant`; no owner authenticated inventory was returned. No credentials were logged or changed. Do not bypass revocation, retry uploads blindly or use a different channel.

No YouTube `videos.insert`, `videos.update`, `captions.insert`, thumbnail action or Studio schedule verification was performed. Planned **11:00 / 16:00 / 20:30 IST** on this date are NOT scheduled appointments. Never set `publishAt` in the past, as that can publish immediately.

## Next safe recovery sequence

1. Redesign the three visual narratives toward the repo's B1v4 case-native media standard (actual examples and comparison states), then run full-audio/visual playback, factual/rights QA, caption/thumbnail legibility QA.
2. Obtain exact media SHA-based final owner approval before any new YouTube upload. Do not silently reuse an old approval for different media.
3. Owner reauthorizes the exact YouTube channel through the existing secure OAuth publisher; never paste refresh tokens into chat or source.
4. Perform an authenticated read-only calendar inventory to prevent duplicates.
5. Use the existing once-only private YouTube API upload workflow, safely process/attach approved SRT and thumbnails, schedule only a future local instant, and independently read back channel/ID/privacy/publishAt.
6. Inspect each video manually in YouTube Studio for title, description, hashtags, tags, captions, thumbnail, audience, rights/restrictions, processing and explicit schedule confirmation. Store exact video IDs and receipts.

**Repro:** `generate_narration.py`, `generate_long_chunks.py`, `render_nov22.py`, `qa_and_thumbnails.py`, `verified_demo.py` in the authorized working folder. Temporary dependency installs were isolated to the working folder and did not alter global Python. No daily unattended automation has been enabled.