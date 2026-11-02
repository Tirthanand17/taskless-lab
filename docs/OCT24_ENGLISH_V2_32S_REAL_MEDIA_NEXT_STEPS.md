# FlowMinute Lab — REAL cinematic V2 assets and next production action

**Source-of-truth:** `state/production/oct24_english_v2_32s_stage_receipt.json`. This progress is **not** a finished video and **not** a YouTube publication.

## What exists

1. The original *approved* Asha/Jay character dialogue, re-exported as exactly 8 seconds at 720×1280 without changing characters. SHA-256 `536652db768052c69e640d0bcd5c950cafcfcee37cc062286dcef2e2d4938517`. The MP4 is a conversation download, **not stored in GitHub**.
2. A **REAL 24s continuous spoken track**, generated from offline open-weight Kokoro, GitHub Actions [run 39981996084](https://github.com/Tirthanand17/taskless-lab/actions/runs/39981996084), SHA-256 `f81dba668732b01b4fc4bbad0e54414f01765e13ec47879dbdb789a334e7d203`. Natural voice generation starts without the old repeated 8s clip padding. Vocal-only -36 dB silence detection found **zero gaps over 1.2s**. Human voice quality still unapproved.
3. One **REAL 32s audio-only preview** combining Jay/Asha original speech 0–8s and the continuous narrator 8–32s, SHA-256 `71e8a4539b99e9d7c09c33723209d471359ae644e03173ca3c62ede41f0e3dcd`. This audio is not a video.
4. **Three cinematic story prompts** in `content/flow/oct24_english_v2_cinematic_scene_0{2,3,4}.txt`, plus the actual extracted character reference stills in the conversation production kit `FlowMinute_Oct24_32s_Cinematic_3D_Production_Kit.zip`.

## Remaining true blocker: real cinematic scenes 02, 03 and 04

The Google Flow rendering UI is **not connected** as a callable tool in this chat. It cannot be truthfully described as autonomously rendered here. No credits were spent, no new scenes generated, and there is no full 32s MP4.

If using Google Flow outside chat, feed the actual approved opening and frames into each eight-second generation, one actual output per prompt, preserving characters and physical prop continuity. Confirm the actual current balance and model credit cost before submitting; the earlier estimate of 36 total credits is **not live verified**. Do not buy credits or use the laptop/Nirala.

## One-command real MP4 intake and assembly (after new files exist)

Place these exact REAL media files together in one authorized, non-symlinked folder:

- `Asha_Jay_Approved_8s_Reference.mp4` — exact supplied approved opening
- `scene_02_real.mp4` — generated 3D cabinet/shelf scene
- `scene_03_real.mp4` — generated 3D model/workflow scene
- `scene_04_real.mp4` — generated 3D access/pricing scene

Then:

```bash
python -m scripts.stage_oct24_cinematic_v2 \
  --directory /authorized/media \
  --manifest /authorized/media/cinematic_v2_manifest.json

python -m scripts.assemble_oct24_cinematic_v2 \
  --manifest /authorized/media/cinematic_v2_manifest.json \
  --voice /authorized/media/FlowMinute_Oct24_V2_24s_CONTINUOUS_VOICE_REVIEW_ONLY.wav \
  --output /authorized/media/FlowMinute_Cinematic_V2_32s_REVIEW_ONLY.mp4 \
  --report /authorized/media/FlowMinute_Cinematic_V2_32s_QA.json
```

This validates **real four-part media bytes**, exact approved opening checksum, unique source hashes and paths, source duration, expected 9:16 ratio, decoder stability, actual continuous narrator source digest and audible-gap test. Missing videos or an attempted vector-graphic duplicate must be blocked. A technical pass does **not** approve realism, character identity continuity, rights, voice performance or exact captions; humans must approve these separately.

There is no direct YouTube scheduling until the *new* 32-second MP4 is actually generated and approved, correct OAuth confirmed, and provider schedule ID/time read back. The explicitly rejected old 48-second video stays blocked. User budget ₹0; no laptop or Nirala access.
