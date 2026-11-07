# ADR-0086 — B4f4 final encoded MP4 audio/visual signal scan (owner review only)

**Date:** 2026-11-07 IST | Branch 2 | Release state: NO PUBLISH.

## Why this implementation, instead of another simulated YouTube uploader

The cloud daily foundation physically generates three complete synthetic narrated rehearsal clips (4 + 9 + 4 original scenes, three H.264/AAC MP4s) and already verifies spoken/caption coverage, original one-time scene reveals, PCM timing and complete video decode. The separate quality modules `independent_av_review.py` and `visual_motion_review_v7.py` provide tests against their respective source fixtures. However the owner-facing one-day final encoded MP4 review export had **no per-video list of actual extended black, frozen/static or silent intervals**. A real viewer needs timecodes to prioritize visual repairs, audio polishing and the known distracting-circles issue.

## New diagnostic

`autopilot/rehearsal_encoded_signal_review_b4f4.py` runs only following the explicit `workflow_dispatch` main-branch opt-in `retain_rehearsal_review_artifact=true`, **after** the original three verified MP4s were created and SHA256-checked and **before** the one-day GitHub review artifact is uploaded.

On each exact original MP4, recheck byte-for-byte SHA256 against `REVIEW_ONLY_NO_PUBLISH.json`, then scan the actual encoded video and audio streams using the FFmpeg binary already provided by the pinned `imageio-ffmpeg` dependency:

- Video: `blackdetect=d=0.8:pix_th=0.1:pic_th=0.99,freezedetect=n=-60dB:d=5` detects extended all-black frames and long unchanged-picture intervals.
- Audio: `silencedetect=noise=-48dB:d=1.6,volumedetect` detects extended near-silence and measures PCM sample mean/peak in dBFS.
- The exact timestamped diagnostics are capped, range checked against the original measured PCM duration, and recorded as `ENCODED_MP4_SIGNAL_WARNINGS_UNAPPROVED.json` alongside the three MP4s, blank reviewer worksheet and offline HTML viewer. The existing review artifact remains **explicit, public-repo-reader-visible and retained for one day only**.
- New read-only GitHub run summary prints counts of black/frozen/silent events and sample peak. No raw audio, text, voice weights, article bodies, external LLM calls, or re-encoded video are preserved. The whole temporary artifact is deleted as before.
- A test suite uses injected FFmpeg transcripts and test-only synthetic media bytes to check all 17 scene identity binding, tampering/forged approval rejection, malformed/clipping intervals, missing volume, unfinished frozen tail, range bounds, subprocess error, and truthful nonrelease states. Required manual opt-in and main-only checks remain unchanged.

## Meaning and strict limits

FFmpeg [blackdetect, freezedetect, silencedetect and volumedetect](https://ffmpeg.org/ffmpeg-filters.html) measure **signal characteristics**, not story engagement, caption aesthetics, licensing or factual accuracy. Freeze detection can legitimately flag an intentionally static teaching diagram or paused screen. Long silence can be deliberate. A near-0 dBFS sample peak is a clipping warning, **not** oversampled true-peak dBTP; mean dBFS is **not** LUFS. Silence detection cannot substitute for hearing pronunciation or voice/music ducking. A 0-warning result **must never be converted into human approval**, a source fact check, a spinner absence guarantee, or YouTube release authorization.

Because an audio/video format can differ from the trusted PCM duration by a small muxing tolerance, the detection accepts timestamps within two seconds of the measured original and rejects impossible intervals. If the real FFmpeg binary, decode or logs fail, the optional owner export step fails closed and does not create a falsely passed diagnostic.

The system still needs a real human to watch all three clips in the existing HTML player, mark all 17 scenes and 30 checks, verify rights and factual claims independently, then enroll owner-controlled private signing/OAuth under protected policy before any release. No real uploads and no independently verified 21/21 unattended releases result from this PR.
