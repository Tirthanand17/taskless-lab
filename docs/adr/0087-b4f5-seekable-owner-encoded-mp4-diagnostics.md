# ADR-0087 — B4f5 SHA-locked timecoded warning seek controls in the original offline MP4 player

**Date:** 2026-11-07 IST | Flowminute Lab Branch 2 | Owner review only, NO PUBLISH.

## Implementation decision

PR #100 (B4f4) diagnoses final encoded H.264/AAC originals with FFmpeg blackdetect, freezedetect, silencedetect and sample-volume metrics, but previously the owner had to manually transcribe timestamps from an independent JSON report into the HTML video player. This increases the chance of skipping an audio or motion anomaly and cannot automatically find a spinner. This increment converts that technical signal evidence into **click-to-seek, per-video review hints** in the *same* standalone offline HTML dashboard.

The newly attached `autopilot.owner_signal_timeline_b4f5` validates the three B4e3 SHA-bound original MP4 files (4/9/4 scenes) against the exact `REVIEW_ONLY_NO_PUBLISH.json` manifest, the original B4e5 blank 47-assessment worksheet (17 scenes + 30 video checks), and the B4f4 encoded signal report. It rejects changed media SHA, slot order, original PCM duration, unsupported marker labels, missing/malformed/unsorted time ranges, inconsistent encoded audio warning flags, fake release status, rightsholder approval or fabricated human inspection.

The runner-only `annotate_existing_owner_player` recomputes SHA256 of the original three MP4s, compares existing HTML to the original B4e7 builder, and atomically replaces it with the same validated offline reviewer, augmented by embedded JSON of strictly numeric signal timing. **No external JavaScript, HTTP, CDN, `fetch`, iframe, remote image, browser storage or uploads** are needed, including when the page is opened as `file://`.

Each video panel displays sorted clickable FFmpeg warnings:

- `Possible black frame` — suspicious all-black interval, check with human playback.
- `Possible freeze / static frame` — a truly frozen frame *or an intentionally static teaching diagram*, requires human judgment.
- `Long silence` — inspect whether the soundtrack intentionally pauses, cuts or loses speech.
- The panel also gives sample peak and mean dBFS, explicitly **not** true peak dBTP or integrated loudness LUFS.

Clicking a warning seeks the matching local video player to its original timestamp and pauses; it **does not autoplay**, and cannot mark PASS/FAIL, sign an owner release, approve rights/facts or publish a video. An empty warning list never counts as proof a video is polished or free from spinning circles. The original blank worksheet remains independently exportable as private JSON and needs manual human completion.

## Workflow and privacy

`.github/workflows/flowminute-daily-cloud-foundation.yml` runs the annotation **only after** an explicit manual `workflow_dispatch` on `main` with `retain_rehearsal_review_artifact=true`. It is not run on PRs/push/schedules, and normal automated research-only receipts are unchanged. The three original media files and updated HTML are included only in the existing public-repo-reader-visible one-day artifact, then deleted on all execution paths; no source articles, speech weights, raw WAV, third-party assets, signatures or credentials are uploaded.

For detection definitions, consult [FFmpeg's current filters documentation](https://ffmpeg.org/ffmpeg-filters.html). Tests cover malformed/forged warnings and swapped exact MP4s, original empty player compatibility, atomic one-shot rewrite, 3 videos/17 scenes/47 unfilled assessments, no upload/network/autoplay, and Node syntax validation of the actual embedded JavaScript when available. B4f4 already runs an actual hosted FFmpeg smoke MP4 regression.

## Remaining real milestones

This only makes **technical review actionable**; no real person has yet watched these three original rehearsals, no independent source claim or music/image/voice license is approved, no protected production owner signing/OAuth credentials are enrolled and no actual YouTube publication is verified. GitHub Actions CI success is not the same as successfully triggering/retaining a one-day opt-in artifact on main; that manual evidence remains outstanding. The production acceptance remains two shorts and one long per day for seven consecutive days, with verified actual channel publishing (currently 0/21).
