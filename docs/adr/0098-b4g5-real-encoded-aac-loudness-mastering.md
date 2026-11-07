# ADR-0098 — B4g5 real final AAC loudness correction with true-peak limiting, independently verified after encode

**2026-11-07 IST | Branch 2 original education rehearsals | No YouTube writes or publication authorization.**

## Starting with genuine final-encoded measurements

B4g4 manual owner-review GitHub Actions run [#42355295469](https://github.com/Tirthanand17/taskless-lab/actions/runs/42355295469) completed with a one-day opt-in artifact and a real EBU R128 input-AAC report for its exact SHA256-bound 4/9/4-scene original educational MP4s:

| Physical original | Input integrated LUFS | Input oversampled dBTP | LRA LU |
|---|---:|---:|---:|
| Morning Short | -26.16 | -7.35 | 2.0 |
| Long video | -27.53 | -6.59 | 2.6 |
| Evening Short | -24.46 | -6.75 | 1.6 |

All three are quieter than the internal owner-review range. The 3.07-LU spread is not the main defect. A simple +8 to +10 dB static gain, without a true-peak limiter, could exceed 0 dBTP on transient samples. The earlier B4g3 pre-encode PCM peak guards do not establish loudness or encoded-AAC true peak.

In a separate CPU cloud-container experiment, **copies of the actual encoded audio** from that ZIP, with FFmpeg one-pass `loudnorm=I=-18:TP=-1.5:LRA=11`, AAC 112k/48k, were remeasured independently after encoding: morning **-18.25 LUFS, -1.42 dBTP**; long **-18.33 LUFS, -1.38 dBTP**; evening **-18.14 LUFS, -1.42 dBTP**. A second test explicitly using `linear=false` for dynamic peak-limited processing and the same PCM duration yielded a comparable **-18.23 LUFS, -1.42 dBTP** for the morning Short. These experiment clips **are not** the output of the new full media-rendering workflow; that must be tested separately after merging.

## Engineering decision

B4g5 modifies only the actual original rehearsal final FFmpeg audio encoding filter chain, with fixed parameters:

```text
-af loudnorm=I=-18:TP=-1.5:LRA=11:linear=false:print_format=none
-ar 48000
-c:a aac -b:a 112k
```

`linear=false` explicitly selects dynamic loudness processing and true-peak limiting; 48 kHz output sampling is explicit. This may change local audio dynamics/amplitude, so **the original spoken words and cue timestamps remain unchanged but the new waveform is intentionally not bit-identical**. The B4g3 original procedural sound timing and ambient oscillator recipe are still generated from the exact PCM cut times. No external music/media samples, third-party voice, credentials, publisher rights, channel ownership or online YouTube operations are added.

After each full H264/AAC video has actually encoded, passed a complete FFmpeg decode, and been SHA256-identified by the existing B4e1 proof, `autopilot.verified_aac_mastering_b4g5.verify_exact_encoded_master` invokes a **separate** full AAC-only decode with the B4g4 EBU R128 measurement, reading ONLY `input_i`, `input_tp` and `input_lra` from the final file. It refuses missing/altered media, nonfinite data, malformed/duplicated FFmpeg statistics, decoded integrated LUFS outside **-20.5 to -15.5**, oversampled true peak above **-1.0 dBTP**, or LRA above **18 LU**. These are conservative **internal QA acceptance values**, not declared YouTube standards or guarantees of perceived quality. The first-pass test uses -18 LUFS/-1.5 dBTP as targets, leaving margin in the post-codec check.

`verify_three_matching_masters` then requires **exactly the morning Short, long video, evening Short** with each exact MP4 digest and same physical source PCM duration, all 3 individually accepted, and no more than **4 LU** final integrated-loudness spread. Failure prevents the original owner-review package from being marked complete, so reviewers are never handed 'technically passed' original audio without independent post-encode evidence. The sanitized detailed audio measurement is included in the pre-existing ephemeral QA; the B4g4 manual-only report is separately retained when the owner explicitly requests the one-day public-repository-readable MP4 artifact.

## Evidence boundaries

Passing these tests does **not** mean it is pleasing to listen to: numerical targets cannot prove speech intelligibility, pronunciation, voice fatigue, whether procedural cues are distracting, mobile headset quality, aesthetic quality, channel upload, facts, rights, or owner listening. Source-dependent publication and OAuth gates stay blocked. All 17 full authored original scenes and PCM timecodes are unchanged. No existing YouTube published/scheduled videos can be retroactively altered by this work.

## Regression acceptance

New dependency-free tests simulate a realistic final AAC EBU R128 log and reject wrong hashes, unbounded/silent values, true-peak breaches, forged human/YouTube status and cross-video loudness mismatch. Hosted real-FFmpeg integration independently encodes a 22-second synthetic blue frame + 260 Hz test tone with very low audio input, processes it through the same `AUDIO_MASTERING_FILTER`, re-decodes the final AAC, and asserts exact measured output meets the internal band. The existing Daily Cloud Foundation workflow runs these tests, while Content Quality Gate collects the offline safety tests.

**Next real acceptance:** trigger one explicit manually opted-in main-branch three-video cloud rehearsal after merge; inspect its B4g5 post-encode proof and B4g4 final AAC loudness JSON. Compare all three actual MP4s and physically listen before human approval. No automatic publishing allowed.

FFmpeg official loudnorm documentation: https://ffmpeg.org/ffmpeg-filters.html#loudnorm.
