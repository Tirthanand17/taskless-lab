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
| 11 | Complete long-form pilot, full playback review | Rendered and technical QA verified: LONG_PILOT_QA.json (3360 frames; 112 seconds; actual Git test); playback and raw ASR review pending |
| 12 | Owner acceptance, historical workflow regression and performance review plan | RC1 audit implemented; FINAL_READINESS_QA.json; owner acceptance, actual capture gate, daily production integration and real symlink regression pending |

## Runtime licensing

Official Remotion pricing and FAQ checked 2026-11-26: individuals and qualifying teams up to three may use the free license, including commercial and automated usage, subject to the full terms and combined headcount rules. Eligibility is not independently attested here; stop before any paid license or billing. https://www.remotion.dev/docs/license/faq ; https://www.remotion.dev/docs/terms .

## Evidence and reproduction

See motion-v2/b1v10/README.md. The three-second benchmark is an illustration only, with no audio and no approval. The original smoke source and report are preserved. Neither the storage-capacity illustration nor its benchmark outputs are new publication candidates. A landscape still is not a landscape motion pass. Do not treat technical motion as evidence of viewer retention or production parity.

## RC2 follow-up

Actual Windows console footage integrated into the Short; see REAL_CAPTURE_QA.json and REAL_PROOF_SHORT_QA.json. Legacy validator and full creative approval remain blocked. Long-form actual capture and daily production integration remain open.

## RC3 follow-up

Actual Git console excerpts integrated into the long pilot and verified: GIT_CAPTURE_QA.json and REAL_PROOF_LONG_QA.json. Both original pilots now have actual-capture variants. Creative/mobile review, full playback, legacy receipt compatibility, second Short and daily integration remain open.

## RC4 follow-up

Mobile-focused hybrid Short rendered and verified (FOCUS_SHORT_QA.json). Five focused real-evidence panels with staged reveal timing. Long-video creative pass and owner playback remain pending.

## RC4 phase 2 follow-up

Long-video focused evidence alternate rendered and verified (FOCUS_LONG_QA.json); both pilots have initial creative-polish variants. Full subjective acceptance remains open. Next: second complete Short, production validator and daily workflow integration.

## RC5 follow-up

Second Short rendered and technically verified (FLOAT_SHORT_QA.json). Two Shorts and one long pilot now exist. Production validator compatibility, daily workflow integration and final release acceptance remain pending.

## RC6 follow-up

Review-only Windows capture adapter and independent media verification implemented for all three pilots (RC6_PRODUCTION_REVIEW_QA.json). All technically pass, all remain blocked by unchanged proof-first creative gate. General receipt and daily workflow integration and final release approval remain open.

## RC7 phase 1

Three opening evidence revisions independently verified (RC7_OPENING_QA.json); proof starts at frame zero in each. Legacy creative and approval holds remain; editorial copy corrections and daily production integration pending.

## RC7 phase 2

Corrected Short opening copy and tested local daily review intake of all three exact pilots. RC7_EDITORIAL_QA.json and RC7_DAILY_REVIEW_QA.json. Generic receipt identity screening implemented; legacy approval and real action gate remain open. No unattended daily rendering or YouTube scheduling.
