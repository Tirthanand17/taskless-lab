# ADR-0093 — B4g0 17 original scene quick-visual contact sheet without TTS/video

**November 7, 2026 | Branch 2 design QA | NO PUBLISH**

The first real audio/video review proved that passing source-code tests does not guarantee visual quality. The B4f9 original editorial redraw now needs **rapid image-level iteration** before a full eleven-minute GitHub video rendering pass. This change adds a separate manual GitHub Actions visual-preview workflow, without voice-model download, FFmpeg, video codec, Youtube API or long-form rendering.

Workflow: `.github/workflows/flowminute-editorial-storyboard-review-b4g0.yml`, explicit `workflow_dispatch` on `main` with `confirm_original_visual_review_only=true`. It generates the same 11 source-independent original editorial beats across the exact 4 + 9 + 4 scene storyboard plan and saves only three labeled PNG contact sheets (`1080×2020` for each Short and `1920×1230` for the long), plus an aggregate status/sha receipt. The original full-size Pillow render is performed for each scene, scaled only in the exported contact composite.

The one-day GitHub artifact is **public-repository-readable**. It contains neither user/private data nor YouTube assets, credentials, TTS model, news article quotes, external screenshots, audio or raw original narration. Strict actions `contents:read`, checkout `persist-credentials:false`, no deploy environment, no automatic schedule and no writes to GitHub. The output reports `publication_authorized=false`, `human_approved_videos=0`, and `actual_queued_video_render_verified_here=false`. Visual diagrams are non-factual practice only and cannot confer source/rights or factual approval.

The existing hosted Daily Cloud PR test suite now **physically generates and verifies these same three contact sheets**, including exact 17 scenes, expected images/dimensions, one-shot preview behavior, and no-video/no-publication flags.

**Important:** These are still-image proofs of scene composition; they are not the final burned-in captions, speech/intonation, actual encoded transitions, or long-video pacing. The independently triggered, 3-MP4 complete owner review remains necessary after any artistic revision.
