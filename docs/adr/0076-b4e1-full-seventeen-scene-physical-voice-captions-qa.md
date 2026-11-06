# ADR-0076 — B4e1 full 17-scene physical original narration and caption rehearsal

**Date:** 2026-11-06 IST. **Track:** Branch 2. **Protected:** Original nonfactual demonstration only; no source-news claims or YouTube publication.

## Verified input

Trusted main [42243709708](https://github.com/Tirthanand17/taskless-lab/actions/runs/42243709708) after PR #85 physically synthesized Kokoro audio and decoded 3 actual illustrated 2-scene MP4 **excerpts** (AM 8.94s, long 10.55s, PM 7.08s); passed pinned model hashes and erased all video bytes. This proves authentic new media for only **6 of the 17 authored scenes**. Neither the 58-second two Shorts nor 240-second long had complete spoken voice and media.

## Full physical technical media pipeline

New `autopilot/full_original_rehearsal_media_b4e1.py` receives **all nine ephemeral original source/planner/editorial/report/review/rehearsal JSONs** and re-derives the canonical B4d5-B4d9 article-selected plan; refuses changed title, source evidence digest, altered storyboard, unapproved quoting or forged owner rights/factual/release flags. Reuses the exact public pinned Kokoro CPU model and SHA256-verified voice weights from PR #85 (no new paid provider or credentials). It uses **every complete original spoken paragraph** from **4 AM Short + 9 long + 4 PM Short** storyboard scenes. Each sentence is split into bounded original text chunks, maintaining all original words; voice synthesis produces a real PCM WAV, and SRT caption cues start/end at **actual physical PCM sample indices**, not approximate static script duration. Cues are **phrase-level timed**; this is explicitly NOT phoneme/word forced alignment.

Original Pillow creates **17 unique** vertical/landscape synthetic educational scene cards with high contrast, a rectangular three-step scientific-testing illustration, static on-screen branding and a bottom safe caption zone. No third-party images, paper charts, publisher article text, premium music, circular loading ring, or endless rotation. The pinned FFmpeg wheel's libass subtitles filter **burns captions into all actual decoded frames**, with H.264 video at 24fps yuv420p and original AAC audio. Each MP4 must pass independent full FFmpeg decode, physical audio+video stream metadata verification, unique original physical scene PNG hash QA, scene-to-PCM timing consistency, source text completeness and bounds. The workflow prints only **safe totals, true measured PCM seconds, target duration comparison and 0 publication/rights approval**.

The original target lengths of 58/240/58 seconds were based on text word counts, **not physical measured voices**. The new physical report stores both the actual PCM-derived video length and the target separately. It NEVER silently pads minutes of silence or claims to have reached 58/240/58 when not within ±3s. This permits actual creative tuning of pacing and style rather than fake completion.

Because source pages remain unverified and rights review unfinished, all 17-scene full rehearsal WAV/SRT/PNG/MP4 files are runner-local `/tmp/flowminute-b4e1-*` only; they are destroyed with unconditional `if: always()` cleanup. The same public research artifact contains only the prior two sanitized JSON receipts with no publisher or narration text. Full physical technical rehearsal success does **not** make real news scripts, final videos, owner approval, authenticated YouTube OAuth or the still-unproven 21 daily releases.

## Resource and safety bounds

- Only GitHub-hosted Linux and previously used local Kokoro/FFmpeg/Pillow wheels; no owner laptop, paid AI model or new external cloud account.
- Same 3-episode daily research, 3 short excerpt AV previews and now **3 longer complete VO rehearsal technical videos** run in one bounded job (38-minute ceiling; full rendering capped at 19 minutes). Public runner minutes are finite; monitor quotas; do not purchase additional capacity.
- No sudo apt, no system FFmpeg installation, no copyright-bypassing article download.
- Original SRT sentence wrapping uses DejaVu open fonts and validates cue time and preserved words; true real human watch/listen and per-word forced synchronization are separate later quality stages.

## Live acceptance

Require four exact-head checks: Daily Foundation full adversarial source/media planning tests, repo Content Quality tests, public scout, real Remotion smoke (legacy). After merge, trust only a **real main-branch daily** job logging three physically encoded full rehearsal videos **all 17 scenes and all voice text spoken** and three physical full H.264/AAC decodes, actual durations, 0 news fact review/rights/YouTube actions, and deletion of all temporary rendered video bytes. Any missing voice chunk/scene, poor timing, unsupported libass or FFmpeg failure must be treated as a failure and corrected. 
