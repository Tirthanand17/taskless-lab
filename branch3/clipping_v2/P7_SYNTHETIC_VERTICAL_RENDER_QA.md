# CLIVOX V2 P7 — Synthetic-only portrait MP4 render and technical QA

**Scope (2026-11-14):** This is a **real FFmpeg render** of **wholly original, intentionally generated test imagery and tone**, not a licensed creator clip or publishable CLIVOX Short. The output is a 270×480 (9:16) *technical preview* held under ephemeral GitHub Actions runner temp, never a YouTube upload, video artifact or approved 1080×1920 master. The P6 written 1080×1920 canvas is only a future production specification. Prior P2/P3 commercial grants and P4 private vault remain unfulfilled.

## P5 → P6 → P7 connected integration

1. Existing read-only CI creates 6 seconds of black/white/black visuals with silence/sine/silence entirely using FFmpeg lavfi generators, tests MP4 integrity, then computes measured P5 acoustic/scene candidate timecodes.
2. Existing P5 evaluator compares source-free event windows against synthetic reference. Existing P6 creates an exact original commentary hook, event cue, contextual payoff and **written** edit-decision-list.
3. New \`scripts/branch3_v2_p7_synthetic_vertical_renderer.py\` enforces the existing actual **closed A3/P4/P5** policy, exact P6 EDL contract and fixed input filename. It **does not read or embed the original MP4 as footage**; it generates a new self-owned clip directly from six *fixed* FFmpeg \`lavfi\` color and audio generators and draws only the three fixed original P6 caption phrases. No creator dialogue, voice clone, scraped replay graph, commercial soundtrack or real facecam.
4. New FFmpeg output is precisely a 270×480 synthetic vertical H.264 yuv420p, AAC mono 48 kHz MP4, nominal 24 fps and 6 seconds with embedded caption overlays. One second of generated sine is bounded by generated silence. Actual 1080×1920 master and human typography/legibility remain unverified.
5. Existing P4 codec, SHA-256, byte and full-decode check is reused against the **new generated** output under a maximum 8 MiB cap. P7 separately validates two streams only, dimensions, codec, frame rate/count, stream start difference, durations and sample rate.
6. FFmpeg decodes real pixels at 1.0, 2.5 and 4.5 seconds and verifies black→white→black corner luminance; it also samples the overlay region for actual visual text contrast and audio samples for silence→tone→silence transition. This is **technical caption visibility and timing**, not accessibility/content review.
7. The output filename is fixed to \`synthetic_clivox_short.mp4\`. The module accepts no input video path, URL, file-download option, license flag, credential, creator transcript or uploader. It fails on unexpected P6 plan fields, local symlink, existing target file, codec mismatch, wrong scene/caption/audio transition, wrong timing and tool failure. Public report deliberately omits video bytes, private path and SHA.
8. Workflow \`.github/workflows/branch3-clivox-v2-p5-synthetic-candidates-qa.yml\` runs the full prior P4/P5/P6 source-free unit suites plus new P7 negative tests and end-to-end generated MP4, then asserts a safe non-release report. No \`upload-artifact\` step, no Cloudflare or GitHub media vault, no YouTube action. The runner and everything under \`RUNNER_TEMP\` are discarded after execution.

## Actual proof versus boundaries

What the prototype proves if CI passes:
- One carefully selected **synthetic** example can move through acoustic/visual timecode proposals, reference comparison, original CLIVOX caption/story draft, and an actual small vertical H.264/AAC output verified by independent probe, full decode, temporal scene/caption sampling and audio timing.
- The technical pipeline can fail closed on unsafe or false authority states.

What it cannot prove:
- A viral YouTube Short, real editing performance, human-validated storytelling, accurate quoting, creator commercial rights, real-speech caption accuracy, no third-party music, monetizability, copyright claim safety, authentic audience retention, 1080×1920 quality, device-level playback, or permission to upload.
- A 6-second test color flash with sparse text is **not** an attractive finished entertainment upload; actual P7 requires licensed source, meaningful transformative edit, durable private output, human review and separate release authorization.

## Acceptance dependency chain

- **P2:** Owner selects and independently confirms 3–5 real creator/rightsholder inquiry routes.
- **P3:** Authenticated signed commercial YouTube derivative/redistribution grant, third-party publisher/game/music/guest clearances and current revocation/territory scope.
- **P4:** Owner-approved, independently audited, access-controlled *private* source delivery and media vault (no public repo/CI footage).
- **P5:** True licensed-source analysis with allowed ASR/VAD/scene/quote checks, 40–60 independently human-labeled legal moments and held-out-by-source top-five quality reporting.
- **P6:** Actually original, context-true commentary and human selected final source boundaries/EDL with guest rights.
- **P7:** Separate protected real-source compositing, original voice, captions, crop/sync and full-resolution QA with private output; no public posting until **P8 owner-signature and P9 CLIVOX-only private-first uploader** gates.

**Roadmap: P0/P1 complete, 2 of 12 = 17%.** The source-free P7 implementation is technical engineering only, not a completed real clipping milestone. Older FlowMinute Branch 1/2 remain unchanged.

## Reproduction and security

- Closed mode: \`python -B -m scripts.branch3_v2_p7_synthetic_vertical_renderer --mode closed\`.
- Unit tests: \`python -B -m unittest -v scripts.test_branch3_v2_p7_synthetic_vertical_renderer\`.
- CI synthetic mode (ephemeral runner only): \`python -B -m scripts.branch3_v2_p7_synthetic_vertical_renderer --mode synthetic --scratch "$RUNNER_TEMP/clivox-p5-synthetic" --edl-file synthetic-edl-draft-only.json\`.
- The CI runner requires standard Ubuntu FFmpeg, fonts-dejavu-core installed **for local rendering only**, and Python 3.12; do not distribute font files. Run on an isolated scratch worker, do not accept outside file paths, and do not execute with permissions for real creator media/upload.

## Actual verification on merged main — 2026-11-14

- [Feature PR #218](https://github.com/Tirthanand17/taskless-lab/pull/218) passed **4/4 checks** and merged source-free P7 renderer at commit `34d4d7abd30169ce237ebbaa009fae5226e1cb11`.
- [PR P5/P6/P7 generated video QA #43590210618](https://github.com/Tirthanand17/taskless-lab/actions/runs/43590210618) **success** including actual FFmpeg synthetic MP4 rendering, fixed original captions and independent decoded-frame/audio checks.
- [Merged-main P5/P6/P7 original vertical render QA #43590313799](https://github.com/Tirthanand17/taskless-lab/actions/runs/43590313799) **success**.
- [Merged-main P4 codec/hash/source quarantine #43590313795](https://github.com/Tirthanand17/taskless-lab/actions/runs/43590313795) and [Content Quality Gate #43590313796](https://github.com/Tirthanand17/taskless-lab/actions/runs/43590313796) **success**.
- All results use a **newly generated** 270×480, six-second fixture under ephemeral GitHub Actions scratch, not a production 1080×1920 master or creator footage. No video artifact uploaded, no private media vault activated, no actual grant, no owner release or YouTube publish. **Roadmap unchanged: 2/12 = 17%.**
