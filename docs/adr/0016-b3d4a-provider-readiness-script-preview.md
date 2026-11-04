# ADR-0016 — Branch 2 B3d4a: modern AI provider readiness and signed-script-to-video storyboard preview

**Date:** 2026-11-04 Asia/Kolkata. **Scope:** nonpublishing GitHub-only development and real *preview* media QA, not autonomous creation or YouTube publication.

## Research and decision

The prior B3a optional generative drafting adapter had an explicit owner approval/free-tier lease and mock-only tests, while B3b actually encoded full-duration media with Kokoro speech and synthetic CSV fixtures. The two were never connected: B3b's graphics and narration were hardcoded to an invented membership CSV dataset. Arbitrarily feeding a newly generated video script into that CSV-only graphics renderer could fabricate claimed examples, and mock AI payloads do not establish the quality of a real model.

Current official provider information consulted 2026-11-04:

- [Gemini 3.8 Flash model guide](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash): the supported stable model ID is gemini-3.8-flash; supports JSON structured output and low/medium/high thinking levels.
- [Gemini 3.8 Flash migration guide](https://ai.google.dev/gemini-api/docs/latest-model): 3.8 requests should remove the legacy temperature/top-k/top-p parameters and use thinkingLevel; minimal is unsupported. The repository's pre-existing default 2.5 Flash is limited for some new projects; prefer 3.8 Flash for a *future, explicitly approved* production evaluation.
- [Legacy generateContent thinking configuration](https://ai.google.dev/gemini-api/docs/generate-content/thinking): thinkingConfig.thinkingLevel=low is the documented REST shape, not a numeric thinking budget.
- [Gemini Developer API pricing and privacy](https://ai.google.dev/gemini-api/docs/pricing): free tier access is not unlimited and may allow provider product improvement using submitted content. Being labelled free does not prove the actual account is enrolled, eligible or capped at zero spend; owner must approve API key, data use, provider project tier, quotas and a durable budget lease before any call.
- [GitHub Actions security](https://docs.github.com/en/actions/reference/security/secure-use): ordinary unprivileged pull_request test jobs, contents:read, no secrets in code, and GitHub-hosted disposable runners for test output.

**Decision:** First implement a verified, no-approval *script to dynamic storyboard and actually encoded 3 temporary MP4 previews* bridge. Do NOT send unreviewed model narration into the CSV-specific B3b renderer or claim the new previews are finished 1080p voiced Shorts/long videos.

## Architecture

1. Use existing B3d1 externally anchored Ed25519 signed script → B3d2 exhaustive spoken sentence spans → B3d3a all script surfaces. Recheck exact input integrity for every video; **do not** treat B3d3b test signed review records as genuine factual clearance.
2. Map a model-script's exact Unicode narration into contiguous scene sequences in the same ordering as the model's bounded visual-beat list. Every original source character must be preserved and every proposed scene must have spoken text assigned. This algorithm handles only *alignment on whole punctuation spans*, not natural prosody or semantic scene match. Refuse fewer spoken segments than visual beats rather than silently duplicating/dropping claims.
3. Render each proposed beat into a *new original* watermarked typography/diagram-like storyboard card with clear "UNVERIFIED MODEL VISUAL DIRECTION", "NO FACT CHECK", "NO TTS", "NO UPLOAD" labels. Never display pretend source findings or generic CSV results as if real evidence of another story. No external stock photos, borrowed audio, scraping or paid model.
4. Use real Pillow raster encoding and FFmpeg H.264+AAC (silent audio placeholder only) on GitHub-hosted CPU runners to produce one half-resolution temporary preview MP4 per daily episode: 540x960 for Short A and Short B, 960x540 for long. Inspect actual stream codecs/dimensions/durations with FFprobe, fully decode every encoded frame and audio packet with FFmpeg and check distinct result digests. Destroy the MP4s and PNGs at the end of the hosted run. These are **rough motionless scene-board previews**, not completed long/Short final masters or actual AI model creations.
5. Model adapter changes: future explicit granted calls default to the documented 3.8 Flash model and use low thinking without obsolete temperature; 2.5 remains explicitly selectable for already-entitled projects with legacy temperature. Both models require the pre-existing owner approval, provider data-use acknowledgement, proven free-tier project, private key and zero-paid-use request lease. All GitHub tests use fake responses and fake keys, no external requests.

The source-to-storyboard interface returns hard-coded FALSE flags for factual clearance, human creative assessment, music/voice rights, media readiness, provider-live inference, media upload/schedule and actual release. A preview never unlocks B3d3b, Phase 3C reviewer gate or any YouTube uploader.

## Tests, files and CI

- autopilot/script_to_preview_bridge.py: pure signed-script dynamic partitioning and optional hosted-only Pillow/FFmpeg preview rendering. Exact narration/visual beat SHA256 and cursor checks are revalidated at the rendering edge; no ad hoc story data.
- autopilot/test_script_to_preview_bridge.py: all three slots, complete contiguous original narration, empty/altered/moved script guardrails, distinct manifest identities, no-approval assertions.
- autopilot/preview_bridge_cloud_smoke.py: creates three **real decoded H264/AAC previews**, tests forged publish/narration changes and cleanup using a Python hosted TemporaryDirectory. No video artifact upload or real TTS.
- autopilot/script_draft_agent.py and test_script_draft_agent.py: 3.8 model request compatibility, legacy explicit fallback and existing mandatory grants verified via fake transport.
- .github/workflows/flowminute-b3d4a-script-preview.yml: read-only normal pull request with two GitHub-hosted jobs: source/scene tests, and real 3-video encode/decode with public open-source dependencies. 0 YouTube credentials, 0 real provider calls, 0 direct local laptop use.

## Known limitations and next engineering order

**B3d4a produces real *technical preview* video files only in ephemeral hosted CI, not a real AI-generated 2 Shorts + 1 long uploadable pack.** The external producer identity and script anchor are artificial ephemeral keys in the tests, real AI prompts have not been executed, no factual review has occurred, and preview video is silent/no actual demonstration.

**B3d4b:** owner-authorized genuine provider evaluation, independently verified source-to-claim citations, human-reviewed three distinct genuinely useful model scripts, budget/data-use consent records and protected cloud credential handling. Require release forecast/cost and claim originality. Do not promote free-tier access merely because the public pricing page says "free."

**B3d4c:** turn separately approved scripts and real independently validated examples into full 2 Shorts + 1 long per-day original narrated cloud videos with proper original content-specific visuals/animations, voice tone, SFX, captions timed to actual spoken audio, thumbnails and final playback; gate against existing audio/visual/fact/rights Phase 3C records and actual final assets. Never auto-use the CSV-only synthetic frame engine for unrelated content.

**B4:** owner-authorized private durable media store, reviewer identity and immutable ledger, private OAuth, fenced exact-once YouTube writer, explicit privacyStatus=private and remote processing, captions/thumbnail scheduling readbacks. Do not connect laptop or public secrets.

**B5:** laptop-off seven consecutive days of 21 actually published independently reviewed original videos with verified costs, safety, no duplicates and no missing uploads.

Branch 1 assisted releases remain independent.
