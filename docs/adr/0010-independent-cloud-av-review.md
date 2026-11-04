# ADR-0010 — Independent cloud audio and visible-caption QA before any release gate
**Track:** Branch 2 — Cloud Autopilot · **Decision date:** 2026-11-04 · **Deployment posture:** technical QA only; YouTube and full editorial approval OFF.

## Measured foundation
The full GitHub-only three-video fixture [PR #12](https://github.com/Tirthanand17/taskless-lab/pull/12) succeeded: narrated 42.92s and 41.29s Shorts and a 186.35s long, with 28 storyboard scenes and 64 speech-timed caption cues, all H264/AAC and full decodes; all media deleted on exit. The renderer reports `subtitles_burned: true` when its FFmpeg command runs, but **command-success alone does not prove a human-readable on-screen caption, correct audio loudness or timing**.

## Decision
Add a **separate deterministic reviewer** on the same ephemeral GitHub runner. It reads only the newly encoded MP4, the original synthetic frame and the generated SRT. It does not create release approval or touch YouTube.

Checks:
1. Run FFmpeg's `loudnorm=print_format=json` in analysis-only mode to extract measured *input integrated LUFS*, *true peak dBTP* and *loudness range*. Use a conservative **diagnostic band** (−24 to −10 LUFS; true peak below −0.5 dBTP). Out-of-band results remain review findings and must not be silently normalized or called publish-ready. Official: https://ffmpeg.org/ffmpeg-filters.html#loudnorm .
2. Use `silencedetect=noise=-45dB:duration=1.25` over decoded audio to list unusually long empty intervals. Long pauses can be legitimate, so this is a diagnostic finding, not a substitute for listening. Official: https://ffmpeg.org/ffmpeg-filters.html#silencedetect .
3. At the first actual SRT cue midpoint, extract one video frame from the already-encoded MP4 and compare its **caption-safe panel** against the corresponding uncaptioned original image. Significant visually changed pixels in the caption region are evidence that text was truly burned in. This does not prove that every word is legible or semantically correct.
4. Extract a later scene and compare the content area (excluding subtitles/progress accent). Require a substantive difference: proves actual scene variation, not just different source PNGs.
5. Parse all SRT cue timestamps and compare every normalized cue text against the actual original script segments. Check unique monotone cue timings and audio length drift with ffprobe.
6. Emit only numeric findings / image-change counts, no private media, no article bodies, no uploads, no new external inference calls.

The reviewer must explicitly assert:
`machine_technical_checks_only=true`, `independent_factual_review=false`, `human_full_watch=false`, `rights_clearance=false`, `youtube_upload_enabled=false`.

## Caveats / threat model
- **Technical measurements ≠ legal editorial approval.** Nonzero captions and two distinct scenes do not establish viewer value, readable content, source accuracy or permission to use media. A signed, independent human reviewer is still required under the existing release policy.
- FFmpeg decoder must be used to inspect the encoded output, not fabricated metadata. Fail closed if audio has missing streams, volume metrics are malformed, captions mismatched/absent, or screenshots cannot be extracted. A visibly rendered subtitle is not proof it matches the spoken waveform; scene-level audio timing is checked using actual generated WAV chunk durations, but a full listening/word-alignment evaluation remains unimplemented.
- Renderer and reviewer are separate Python modules. This makes it harder for the renderer to mark its own unverified QA as `approved`.
- No laptop storage, private OAuth, Cloudflare D1 migrations, external model provider opt-in or GitHub artifact media storage. Everything resides on the public GitHub-hosted ephemeral runner and is deleted immediately after the check.

## Acceptance
Green unit tests with forged loudnorm output, wrong SRT text, no captions, unchanged scenes and malformed metadata rejected; live no-secret PR benchmark rechecks all three videos with actual FFmpeg and Pillow data; 3 independent numeric reports printed in job summary and repo issue #8, no media retained. If the voice measurements fail the broad diagnostic band, fix the encoder/voice gain in a subsequent exact measured iteration rather than loosening policy. Never upload benchmark clips.
