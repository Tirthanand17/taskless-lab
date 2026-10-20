# FlowMinute Lab — Phase 3 HD capacity benchmark (18 October 2026)

**Research PR #5 DRAFT ONLY; no publishing, TTS model downloads, channel access or production video assets.**

## Purpose

Previous public GitHub cloud-render checks **successfully generated** two full 42-second silent Shorts (360×640/8fps) and one full 7m12s silent Hindi long video (640×360/8fps). They also encoded one second of each 1080p / 24fps format. A one-second first-scene probe cannot prove a 42-second or 432-second full-HD production run is stable, efficient or free at 2 Shorts + 1 long per day.

`autopilot/phase3_hd_capacity_benchmark.py` makes the next measurable step without raising production risk:

- Three **real** one-second (24-frame) original H.264 samples at native publishing-oriented *resolution* only: English Short 1080×1920 at authored timestamp 22s; Hindi Short 1080×1920 at timestamp 31s; Hindi/Hinglish long 1920×1080 at timestamp 254s. Using later authored scenes checks actual data/code/totals beyond static introductions.
- Measures wall-clock video-generation/encoding runtime per 1-second sample, sample MP4 bytes, effective frame throughput, and Linux process/child peak RSS high-water observations.
- FFprobe independently enforces **exactly one H.264 video stream, no audio**, correct dimensions, 24 frames, exactly one second, and FFmpeg fully decodes each sample. No auditable voice, real speech, licensed sound or published output is involved.
- Never overwrites existing output files; requires an existing scratch folder; original renderers refuse 1080p batches over 36 frames and have individual audio/media release flags FALSE. The runner deletes the three sample MP4s after the benchmark and the workflow's existing cleanup deletes all other media. Neither stores a GitHub Actions artifact nor commits media.
- Computes explicitly named `naive_linear_render_seconds_UNVALIDATED` and `naive_linear_media_megabytes_UNVALIDATED`. **These are illustrations, NOT conservative capacity forecasts or an approved render schedule**; scene complexity, ffmpeg settings, hosting variance, quota, storage and audio load can change the result. The benchmark always sets `full_hd_daily_batch_capacity_verified=false`, `sustained_zero_cost_verified=false`, `publishing_authorized=false`.
- Replaces (rather than doubles) the existing three original 1-second native-HD smoke clips in `.github/workflows/flowminute-cloud-render-smoke.yml`, using the public standard GitHub runner only. No new external service connection or billing.
- Bounded tests in `autopilot/test_phase3_hd_capacity_benchmark.py` cover incomplete/mismatched measured frames, nonfinite clocks, unsupported dimensions, fabricated audio, unrealistic sample times, duplicate episodes, and cleanup. Tests with injected fake probe data are not described as actual renders.

## Required independent evidence

Record exact HEAD SHA, Content Quality test count, Cloud Scout run, public Cloud Render Smoke result, three **measured** wall times, frame rates, memory high-waters, sample output bytes and cleanup. Do not claim this was executed until the final run's logs explicitly show the measurements and a passing conclusion.

## What this does not solve

Final full 1080p/24fps **42s + 42s + 432s** delivery, rightfully licensed natural Hindi/English speakers (two audibly distinct Short narrators), genuine phoneme-to-subtitle alignment, polished cinematic 3D/real-world demonstrations, independent research facts and rights QA, owner-authorized cloud D1/YouTube OAuth and public upload/scheduling are not approved or complete. A sample measurement does **not** close Phase 3R3 or any of the existing **21 production acceptance subphases**.

Hard controls stay in force: ₹0/month infrastructure, no Nirala/laptop, new account/service/model download, paid cloud run, production DB mutation, real YouTube upload/schedule/publish, or unapproved external service connection. Separate release-controller PR #4 remains draft/unmerged.
