# Phase 3AC — Source-bound complete seven-scene 3D visual review for Oct 20 Shorts

19 October 2026 | Public DRAFT PR #5 | No Google, Nirala, third-party audio service or paid cloud.

## Actual implemented code, not just a renderer idea

- New `autopilot/oct20_full_mesh_story_timeline.py` composes **every authored scene** from the existing October 20 EN 42-second and HI 44-second scripts using the existing `oct20_mesh_cinematic_proof.py` 3D face projection and lighting helpers. No duplicate 3D engine or speech model. The exact original 7 scene start/end positions come from `oct20_full_silent_timeline.full_silent_scene_plan`. Full run contains **1008 English** or **1056 Hindi** real generated frames at 24fps.
- Seven distinct source-bound visual overlays per language cover the safety hook, fictional grocery list, cart draft, price/address/payment risk, four safety steps, feature availability and final human approval. Scene-specific labels and up to four projected 3D boxes are modeled; a 3D moving ground plane and connector pulse show actual frame-to-frame motion.
- Per-frame script cuts are validated and cached. An explicit requested output path must be a fresh .mp4 file in an existing nonsymlinked directory, with disk headroom. The renderer streams real 540x960 RGB images into installed FFmpeg at most 1056 frames, with bounded runtime and memory, and runs FFprobe verification of exact codec, frame count, dimensions, duration, and exactly **one VIDEO stream and ZERO AUDIO streams**. If rendering or post-encode verification fails, the incomplete output is deleted.
- New `autopilot/test_oct20_full_mesh_story_timeline.py` verifies original source-bound scene windows, 14 distinct headings/visual treatments, real independent frames at all seven scene starts per language, actual frame movement, wrong episode/cut/boundary refusals, no overwrite, and **actual one-second H264 + FFprobe** on public CI. Public CI does NOT export both full-length videos; this respects free runner constraints.
- All audio / rights / ASR / Google / YouTube privileges remain explicitly FALSE in receipts. Full-length geometry is **stylized original 3D**, not photorealistic cinema.

## Actual ChatGPT sandbox 42/44s media review

In an isolated ChatGPT workspace using the previous independently tested original cube-mesh visual prototype, an independent local editing script generated TWO full-length 7-scene concept MP4s. The local implementation matches scene cut times, animated 3D polygon concept and original bilingual topical headings, but is **not byte-for-byte output from the committed GitHub renderer** and still uses baseline ASK/PLAN/CHECK cube labels below the changing scene titles. It is a real moving original visual preview, not a fully polished scene-specific 3D treatment.

- `flowminute_oct20_en_7scene_mesh_SILENT_EDITOR_REVIEW.mp4`: FFprobe verified 42.000 seconds, 540x960 pixels, 24fps, 1008 H264 frames, one video stream, no audio; about 7.1 MB.
- `flowminute_oct20_hi_7scene_mesh_SILENT_EDITOR_REVIEW.mp4`: FFprobe verified 44.000 seconds, 540x960 pixels, 24fps, 1056 H264 frames, one video stream, no audio; about 7.4 MB.
- `flowminute_oct20_14_original_3d_scene_contact_sheet.png`: all seven EN and seven HI sections sampled from actual generated video file bytes, two rows of seven. No user PC or provider account was accessed.

**Creative QA finding, not closed:** repeated 3-box motifs and generic object labels remain visible across scenes in the local media. This is not good enough for the channel's original photorealistic grocery examples, diverse motion-VFX stories and differentiated footage. Implement unique scene-specific story props (grocery product meshes, generic approval/locked payment symbols, permission diagram) and independent artistic QA before advancing. Future scripts and video subjects must not appear as identical cards with merely changing titles.

## Unchanged high-priority production blocks

- Rights-cleared genuine natural varied English/Hindi narration with distinct speakers, verified pronunciation and model/voice rights not available.
- Authenticated actual speech-to-SRT word-level timing, audio loudness review and final 1080p shorts / 1920x1080 long production not available.
- Long 480-second tutorial does not have an analogous audiovisual final.
- Cloud-only zero-cost always-on production capacity and authenticated owner-approved private YouTube upload/readback/schedule/publish not verified.
- **No real video uploaded or scheduled**, no Google OAuth, Cloudflare D1 production, paid API, new external service, downloaded model, Nirala laptop, private Actions or charge occurred. User monthly recurring infrastructure cap ₹0. Both public/private PR #5 remain DRAFT/unmerged.
- The previous **21 production acceptance subphases across six unfinished major phases** remain open. Prior rough estimates **45% software architecture and 20% genuine autonomous production readiness** remain unchanged; preview rendering is not verified production release acceptance.

## Next meaningful move

Improve scene diversity and original 3D product demonstrations; independently vet high-quality Hindi/English audio sourcing with explicit license/model connection approval before trying a voice inference experiment. Actual approved audio must determine timing instead of fake SRT estimates. Never promote a silent storyboard MP4 to publication status.