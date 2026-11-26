# Branch 1 v10 (B1v10) — native-HD motion production upgrade

Status: isolated, review-only development. Baseline: main 7f4ef63. Recovered local renderer checkpoint v0.1.0 (2026-11-26 IST); this document reconstructs the available handoff, not a claim to reproduce every word of the unavailable shared chat.

## Non-negotiable production requirements

- Original, audience-relevant tech stories: current primary-source research, distinct angle, truthful hook, fact-check, real demonstration when applicable, useful payoff.
- Native 1080x1920 Shorts and 1920x1080 long-form, no upscaled blurry assets, H.264 deliverable and mobile-size visual review.
- Reference-reel-inspired composition, not imitation of copyrighted footage or branding: meaningful camera movement, motivated transitions, depth, deliberate hierarchy, clean contrast, intentional typography, no clipped text, persistent spinner, filler, or useless lower-screen void. Reserve space for platform overlays and synchronized captions.
- Preserve the preferred Kokoro af_heart voice as the candidate baseline. Use natural script phrasing, exact-word pronunciation checks, audio-aligned captions, balanced licensed effects/music and a recorded full listening review. No voice impersonation or invented performance evidence.
- Use Remotion 4.0.534, SVG and lightweight 2.5D first; evaluate Three.js selectively, Blender only where hardware and storytelling justify it. Whisper for timing, FFmpeg for encoding and audio QC. Do not add paid services or cloud billing.
- Reference visual parity is a human review decision, not a resolution or motion metric. No promise of virality.
- Preserve existing Branch 1 production/publisher gates and duplicate fences. No historical project edits, schedule edits, publication, or automatic release from this development branch. Daily target 2 Shorts + 1 long only when content clears all gates.

## Versioned milestones (equal-weight checklist, not time estimate)

| ID | Acceptance evidence | State |
|---|---|---|
| 01 | Versioned requirements and isolated branch | Implemented in this branch |
| 02 | Remotion runtime 4.0.534 and CLI verified locally | Verified |
| 03 | Native HD 9:16 animated benchmark, 90 decoded frames | Verified; SMOKE_QA.json |
| 04 | Native HD 16:9 animated benchmark, 90 decoded frames | Verified; DUAL_MOTION_QA.json (90 frames at 30 FPS) |
| 05 | Reusable visual tokens, typography, safe-area layout and scene primitives | Verified; DESIGN_REVIEW_QA.json (four native stills; layout/contrast checks) |
| 06 | Storyboard and research/evidence template for differentiated topics | Verified; EDITORIAL_REVIEW_QA.json (three official-source-linked review storyboards; 10 offline tests) |
| 07 | Meaningful transitions, camera, asset rights and sharpness checks | Verified benchmark and screening primitives; MOTION_REVIEW_QA.json (90 native-HD vertical frames; 8 offline tests; rights approval and full pilot review remain pending) |
| 08 | Preferred narration and real listening review, aligned captions | Technical implementation verified: NARRATION_REVIEW_QA.json, CAPTION_CORRECTION_QA.json, CAPTION_PREVIEW_QA.json; owner accepted current voice for now; full AV review pending |
| 09 | Licensed sound design, intelligibility and mix QC | Technical implementation verified: SOUND_MIX_QA.json, ENCODED_SPEECH_QA.json; subjective mix listening and full AV review pending |
| 10 | Complete original Short, visual and full playback review | Rendered and technical QA verified; SHORT_PILOT_QA.json (581 frames; representative-frame inspection); owner playback pending |
| 11 | Complete long-form pilot, full playback review | Pending |
| 12 | Owner acceptance, historical workflow regression and performance review plan | Pending |

## Runtime licensing

Official Remotion pricing and FAQ checked 2026-11-26: individuals and qualifying teams up to three may use the free license, including commercial and automated usage, subject to the full terms and combined headcount rules. Eligibility is not independently attested here; stop before any paid license or billing. https://www.remotion.dev/docs/license/faq ; https://www.remotion.dev/docs/terms .

## Evidence and reproduction

See motion-v2/b1v10/README.md. The three-second benchmark is an illustration only, with no audio and no approval. The original smoke source and report are preserved. Neither the storage-capacity illustration nor its benchmark outputs are new publication candidates. A landscape still is not a landscape motion pass. Do not treat technical motion as evidence of viewer retention or production parity.
