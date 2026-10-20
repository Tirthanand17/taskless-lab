# Phase 3AA: actual PCM anomaly quarantine for October 20 voice intake

19 October 2026 | public draft PR #5 | zero new external services or charges

## Substantive unsafe behavior corrected

Previously, the three-video intake verified PCM codec, duration, amplitude, WAV SHA and claimed rights document digest, yet a completely artificial **480-second WAV made of a 250-ms square-wave repeated 1,920 times** could pass. This is not plausible original natural narration. Basic technical tests were necessary but insufficient.

## Added real waveform screening

- autopilot/oct20_voice_signal_triage.py reads the real candidate PCM16 mono or stereo WAV in bounded quarter-second chunks, validates complete frame count, full-file SHA and unchanged filesystem identity, and holds obviously pathological audio.
- Exact repeated NONSILENT quarter-second block taking >=65% of active chunks (with 12+ repeated blocks): REPEATED_IDENTICAL_ACTIVE_PCM_BLOCKS.
- More than or equal to 2% full-scale-clipped samples: EXCESSIVE_FULL_SCALE_CLIPPING.
- More than or equal to 90% effectively silent chunks: MOSTLY_SILENT_PCM.
- All are conservative signal checks. They do NOT detect all automated tones, AI speech or falsified provenance and do NOT certify naturalness, pronunciation, separate people, consent, commercial licensing or transcript-to-audio word timing.
- The existing source-locked Oct20OwnedVoiceTake three-WAV intake now requires this additional screen to pass after independently inspecting codec/duration/RMS. It crosschecks the actual WAV SHA and rejects any forged speech/rights/YouTube status.

## Regression evidence

- autopilot/test_oct20_voice_signal_triage.py generates real short PCM WAV files covering exact repeating synthetic square tones, deliberately varying artificial tone, clipped audio, nearly all silence, missing/corrupt WAVs and symlink refusal. Passing a clean technical signal does not imply a human speaker.
- autopilot/test_oct20_owned_voice_handoff.py still exercises three full-duration 42/44/480-second PCM technical take fixtures, now with varying artificial tone amplitudes, and preserves earlier integrity/consent declaration/anti-reuse tests. A separate full 42-second repeated square-wave fixture must be blocked when substituted for a Short.
- The 250-ms sample pattern is intentionally selected to prove the old duration/energy/hash-only admission problem is closed. Natural genuine narration audio is NOT available and therefore not claimed tested here.

## Production and authorization boundaries

The phase includes no real person’s new voice, no verified Hindi pronunciation, no independently authenticated commercial rights, no complete audiovisual 3D final video, and no real YouTube upload/schedule/readback. Prior eSpeak audio remains REJECTED for publication regardless of these technical checks.

Next production requirement: genuinely natural rights-cleared English/Hindi narration with distinct Short speakers, independent listening/legal verification and word-by-word acoustic sync; complete cinematic visuals and obtain separately approved zero-cost cloud production and YouTube upload.

No Nirala laptop access, no model download, no external service connection, no paid TTS, no new Cloudflare D1 or Google OAuth operation and no YouTube publication. Monthly infrastructure authorization INR 0. Both draft PR #5 remain unmerged. All 21 previously open production acceptance subphases across six unfinished major phases remain open. Rough software ~45% and autonomous production ~20% estimates unchanged until real acceptance evidence.
