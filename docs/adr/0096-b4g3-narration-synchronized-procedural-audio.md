# ADR-0096 — B4g3 deterministic narration-synchronized original audio design

**2026-11-07 IST | Flowminute Lab Branch 2, synthetic rehearsal only | NO PUBLISH**

## Problem and reference

The original full 17-scene speech pipeline at `autopilot/full_original_rehearsal_media_b4e1.py` inserted one fixed 60ms 480Hz beep into the first spoken chunk of every scene. That cue was not aligned with the successive B4g2 visual focus events, which now occur **multiple times per scene**. It also used no ambience or scene-specific sound vocabulary, leaving the new editorial visuals and the narrator disconnected.

The owner has deferred their actual playback approval until later; this implementation can therefore improve and technically test the independent sound layer, but **does not claim the new full MP4s sound good, or that human listening/rights/YouTube release has happened.**

## Technical decision

Use the repository's existing `autopilot.polished_sound_design_v2._sfx` (purely original programmatic tick/ping/sweep/pulse, no external media or music samples), rather than downloading sound effects. `autopilot.original_pcm_sound_design_b4g3`:

1. Accepts only 4/9 source-derived original scene identifiers, actual measured PCM scene durations, and an explicit 16–48kHz supported mono sample rate. Calls B4g2 `grammar_for_original_scene`, `active_focus_sequence` and `stage_hold_seconds` to plan the same consecutive original **visual** cut boundaries. Unknown, duplicate, non-finite, missing and physically impossible clocks fail closed.
2. Schedules a light procedural accent at **each distinct one-way focus reveal**. Genre families have deliberately different fixed original textures (compare: tick → ping; verification: tick → pulse; steps: tick → ping → tick; sample matrix: tick → sweep → pulse). The schedule includes exact PCM sample offsets and keeps the overall count below 30 per original episode. No repeated circular visual or timer loop.
3. Adds an extremely quiet, freshly synthesized three-oscillator harmonic background (110, 164.81 and 220 Hz, peak oscillator sum at most 0.0024, around -52.4 dBFS before fades), with smooth 1-second attack / 1.2-second release. This is **not** a third-party composition, recording or melody; it is an original synthesized ambience. Effect gain is 34% of already bounded soft SFX; all physical sample math is deterministic.
4. Preserves every original sentence and PCM cue start/end time; no extra playback duration. If physical narration is extremely hot, applies a bounded **linear** input gain for headroom; the combined PCM must remain below **0.96 peak** and the sound layer may differ from the appropriately gain-adjusted original by at most 0.022 samples (linear full scale). Bad/corrupt PCM, changed sample rate, NaN/Inf, silence, clipping or uncertain phase alignment fails closed. The finished WAV remains original PCM16 speech plus original procedural sound, using only existing hosted CPU Python dependencies.
5. Removes the old fixed beep from the first TTS chunk. After actual voice synthesis, the sound design report is written to an ephemeral, non-exported file; the full MP4 renderer matches its exact scene events and duration to the post-decode inspected source video and then includes **only sanitized numeric technical metadata** in existing ephemeral QA. GitHub review artifact still copies **exactly three SHA-locked MP4s**, the original unapproved worksheet, offline player, exact diagnostics and README.
6. Leaves protected YouTube `PUBLISH_ENABLED` disabled, factual/rightsholder signoff missing, owner review blank and OAuth untouched. No rights can be inferred from mathematically generated audio alone.

## Tests and limitations

`autopilot.test_original_pcm_sound_design_b4g3` runs dependency-free in Content Quality Gate to verify 4/9-stage source planning against B4g2's exact FFconcat cut times, malformed timing and IDs, quantitative accent count and strict recipe bounds. The existing Daily Cloud Foundation installs NumPy and soundfile for additional **actual mono PCM waveform** tests: output identical duration/dtype, deterministic output for the same original inputs, low effect amplitude, peak ceiling, no unapproved release, out-of-bounds and invalid inputs rejected. `flowminute-daily-cloud-foundation.yml` has this test wired on PR/push.

Passing numerical tests establishes only physical deterministic rendering, **not** integrated loudness LUFS, true peak dBTP, voice articulation, perceptual loudness, voice/music mix balance, mobile playback, copyright of the entire video, or human editorial approval. Those require a **new** actual complete three-MP4 review run after merging and independent listening. No previously retained MP4 is altered.

The project goal of verified 2 Shorts + 1 long every day remains blocked from unattended live YouTube publication by `OAUTH_REFRESH_FAILED`, independent facts/rights approval, bounded owner release signoff and the missing seven-day verified run.
