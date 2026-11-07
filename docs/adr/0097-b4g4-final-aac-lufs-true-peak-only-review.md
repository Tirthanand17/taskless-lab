# ADR-0097 — B4g4 measure actual final AAC integrated LUFS and true peak, no audio rewrite

**Date:** 2026-11-07 IST | Branch 2 review tooling | **NO PUBLISH, NO AUTOMATIC MASTERING**.

## Evidence and why it matters

PR #113 (B4g3) introduced strictly bounded original, quiet procedural effects, synchronized to the actual scene-phase PCM clock, and a low-level harmonic bed. Physical NumPy tests confirmed the source PCM waveform duration, peak ceiling, exact cue positions and no third-party media. However, *PCM peak amplitude cannot establish integrated perceived loudness or codec-induced true peak after AAC encode*. The existing B4f4 final-encoded MP4 review measures only **sample peak dBFS** and approximate mean dBFS, and explicitly warns these are **not** integrated LUFS or oversampled dBTP.

B4g4 closes this technical observability gap without claiming mobile playback, rights approval, copyright status or YouTube publishing.

## Implementation

The new `autopilot.encoded_aac_loudness_review_b4g4` executes **only after** the original three real H.264/AAC synthetic educational rehearsal MP4s have been rendered, fully decoded, separately SHA256-checked and packaged under the existing explicit one-day GitHub manual-review opt-in. For each `short_am` (4 scenes), `long` (9 scenes), and `short_pm` (4 scenes), it independently verifies the exact original media path, byte SHA256, slot/scene identity, physically measured PCM duration and all no-publish flags.

It then uses the pinned FFmpeg binary, a no-shell argument array and the audio stream of **the final original encoded AAC MP4**, invoking:

```shell
ffmpeg -hide_banner -nostdin -nostats -i ORIGINAL.mp4 -map 0:a:0 -vn \
  -af 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json' -ar 192000 -f null -
```

The loudnorm filter processes audio only **in memory to the null muxer**. Its `input_i`, `input_tp`, `input_lra` and `input_thresh` JSON values measure the decoded *original AAC input*. It may internally normalize its discarded output stream, but **does not modify the MP4** or the original waveform file. `-ar 192000` is explicit for measuring true peaks at a high output sample rate; FFmpeg's documented dynamic mode internally upsamples to 192 kHz for true peak detection. The parser rejects missing/multiple/malformed reports, NaN/Inf/silent or physically implausible metrics and any unsuccessful decode.

The resulting `ENCODED_AAC_LOUDNESS_TRUE_PEAK_UNAPPROVED.json` includes bounded final-input integrated LUFS, oversampled true peak dBTP, loudness range LU and gating threshold LUFS for all three original SHA-bound MP4s, plus exact cross-video integrated-loudness difference. The GitHub Actions run summary displays only finite measurements and locally defined advisory warning categories. The existing output package continues to contain the same three **unmodified** encoded MP4s, original player, scene worksheet, signal-review report and README; this adds exactly **one small numeric review file**.

## Warning policy and safety

Technical, adjustable local review guidelines—not claimed YouTube requirements—flag a true peak above -1.0 dBTP, integrated loudness lower than -23 LUFS or higher than -11 LUFS, loudness range wider than 18 LU, and >5 LU spread across the three videos. These are **advisory only**: high dynamic range might be intentional; integrated LUFS is not a complete speech-intelligibility metric; oversampled dBTP is not a listening test; channel normalization and playback devices vary. No filtering or mastering is automatically applied, and even zero warnings cannot confer voice, source, owner, factual, media-rights or release approval.

The scanner runs only on manually opted-in `workflow_dispatch` on `main`, with `FLOWMINUTE_EXPLICIT_REVIEW_OPT_IN=true` and the same exact owner package path. The one-day GitHub artifact remains readable to repository readers and intentionally contains only source-independent synthetic rehearsal files. It does not use account credentials, YouTube API, any write permission, external model, external sample, network fetch, or a laptop's storage.

## Test acceptance

`autopilot.test_encoded_aac_loudness_review_b4g4` includes real installed-FFmpeg synthesis + AAC encode + loudnorm measurement on a 22-second computer-generated test sine/tone clip (no person/voice), and adversarial fake-decoder tests: exact three SHA-bound MP4 slots/4+9+4 scenes, altered media bytes, forged publishing approval, malformed JSON, duplicated reports, Inf/NaN, invalid numeric ranges, false decoder success and absence of an output file after failure. Both Content Quality Gate and the Daily Cloud Foundation collect the tests. The real three-video manually opted-in cloud report must be verified after merge before any actual final LUFS/TP measurement is claimed.

Official FFmpeg filter specification: https://ffmpeg.org/ffmpeg-filters.html#loudnorm.
