# ADR-0094 — B4g1 original voice-driven 17-scene seek navigation in offline MP4 review

**2026-11-07 IST | Branch 2 owner-review quality bridge. No publication.**

## Actual visual evidence

The redesigned three-MP4 cloud render [run 42349401200](https://github.com/Tirthanand17/taskless-lab/actions/runs/42349401200) completed, generated actual fully decoded narrated H.264/AAC original rehearsals and produced the opt-in one-day review ZIP. Downloaded MP4s were SHA-256 validated against their manifest; representative decoded frames from short_am, long and short_pm show the giant subtitles fixed and the new editorial composition visible. Encoded-media FFmpeg scan observed no long black frames, no long silences and one possibly static/frozen interval; that does not certify animation-free or owner approval.

However the offline player previously had seventeen numbered review fields without actual per-scene start times. Reviewers could only guess boundaries from the progress bar, making inspection of full-length hold/static intervals and specific scene defects more difficult.

## Change

1. `audio_scene_navigation_b4g1.build_audio_scene_timeline` derives the exact 4/9/4 scene start/end times from the **actual synthesized PCM durations** used by the ffconcat renderer. It accepts only finite physical durations (2–55s) whose sum matches original audio and whose monotone boundaries cover the entire 20–340s video within 3ms precision. It carries no authored narration, third-party source, user credential or private article.
2. `full_original_rehearsal_media_b4e1._inspect_full` verifies the scene clock only **after** full ffmpeg audio/video decoding, exact unique stage evidence and MP4 SHA are proven; it returns `pcm_derived_scene_timeline_seconds` and an honest origin marker. The existing voice, soundtrack, visuals, reveal duration, SRT/ASS and YouTube flags remain unchanged.
3. `manual_rehearsal_review_export_b4e3` requires this origin in each previously inspected SHA-bound episode and exports only the numeric start/end pairs into both the public review-only manifest and the originally blank private-copy worksheet.
4. `review_worksheet_validator_b4e6` rejects forged or reordered source clock positions, modified source media SHA and unassociated timestamps. Historical artifacts without scene navigation remain readable for backwards compatibility and cannot add unassociated scene positions.
5. `offline_review_portal_b4e7` shows one **Jump to scene** button beside each of the 17 individual human-review controls. Clicking seeks 0.12s after the PCM scene boundary, pauses and focuses the matching embedded local MP4; it **never autoplay, mark any check PASS/FAIL, grant factual/rights approval, call network or upload anything**.
6. New offline adversarial tests verify finite/contiguous 17-scene timeline, exact last audio duration, reordered/missing/overlapping/extra/boolean/nonfinite entries, SHA-bound worksheet anti-forgery and no-autoplay/offline JS. The full GitHub Foundation no-publish CI runs this suite before any cloud rendered media.

## Limitations and next visual acceptance

PCM timings reconstruct the source visual ffconcat stage clock, but FFmpeg encodes at 24fps and some scene transitions can be displaced by one frame. A seek button is a *review navigation hint*, not proof that the video was watched or that it is safe to publish. A static/potentially frozen long-video segment is a creator design decision requiring full human inspection, and the original narrations remain **non-factual synthetic training examples**.

Actual production YouTube channel OAuth refresh is blocked (`OAUTH_REFRESH_FAILED` in [run 42346682195](https://github.com/Tirthanand17/taskless-lab/actions/runs/42346682195)); no schedule or daily unattended release can be asserted. Human approvals remain 0/3 and independently verified unattended seven-day releases 0/21.
