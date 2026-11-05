# ADR-0041 — B4e1: reference-video quality audit and Flowminute visual rescue

**Date:** November 5, 2026 IST. **Branch:** 2, source-only until real rerender is verified. **Reference:** user-uploaded original 20261105-0544-34.8137863.mp4; inspected only in the conversation. Do NOT commit this third-party recording, soundtrack, images, audio transcription, branding, likeness, logos or exact visual assets to this PUBLIC repository.

## Creative sign-off is BLOCKED

The owner reviewed all three real generated videos and rated them **0/10**. Their screenshots visibly show absurdly large black-outlined caption words crossing the central artwork, a large blank outlined panel unrelated to the subtitle position, basic SVG graphics and poorly differentiated slide-like title-card thumbnails. A green technical FFmpeg decode, complete captions or video SHA does NOT prove a usable video. Any creative release remains blocked pending a real watched-and-listened owner approval.

## Recorded reference analysis

The actual uploaded video is 147.533 seconds, 450x806 portrait, H264 at 30 fps with two-channel AAC 48 kHz, ~1.706 Mbit/s multiplexed. Its audio analysis indicated approximately -22.1 LUFS integrated, ~2.5 LU loudness range and -11 dBTP true peak, plus mostly narrow/mono content despite two channels. These measurements are not voice cloning identification, and cannot distinguish a narrator consonant from a specific UI-click notification. Do not claim a specific pop/click/SFX or gender/timbre has been verified without an A/B human listen.

| Approx. clip time | Observed visual grammar | Original Flowminute analogue |
|---|---|---|
| 0–6 s | Dark cinematic lock/incident hook, one focal item, big high-contrast number | One original surprising numerical/educational hook |
| 6–14 s | Floating smartphone UI, short message, small timestamp; ample negative space | Original low-clutter notification-style measurement card |
| 14–28 s | Dimensional tilted laptop, search and red warning overlay | Original 2.5D device and data-state reveal |
| 28–42 s | Profile/video-call UI, date progression and card transition | Tight sequence of 3D-style evidence cards, no stock faces |
| 42–70 s | ZIP file, multiple laptop screens, chat/terminal and container panels | Original perspective object transitions following story beats |
| 70–88 s | Document stack, red evidence grid and dossier | Source-linked fact card with a single meaningful quantity |
| 88–110 s | Case file, comparison panels and large numbers | Scientifically accurate visual comparison and units |
| 110–130 s | Repeated wallet illustrations, particles, number reveals | Repeated original icons, chart and 2.5D parallax |
| 130–143 s | Checklist, visual return to opening motif | One concise lesson, original continuity callback |
| 143–147.5 s | Distinct closing/avatar moment | Original Flowminute outro and clean call-to-action |

Strong scene-replacement moments appear approximately around 6, 28–33, 41–42, 69–70, 82, 88, 100–102, 117, 127, 137 and 142 seconds. Smaller object movement, staged numeral reveals and progress steps occur between. These look 2.5D/3D-style, but the recording alone does not prove use of Blender or another true 3D modeling package. The reference includes Hindi-English narration and sparse keyword emphasis; it does not use the former Flowminute practice of covering the entire illustration with sentence-sized subtitles. Its composition should inform general design principles only, never imitation of protected footage or unique branded art.

## Root-cause diagnosis: the text catastrophe

The previous original-topic renderer used FFmpeg default SRT -> libass subtitles with forced style FontSize=23 and a 38-character line wrap, but WITHOUT native 1080x1920 PlayRes or a true pixel-safe glyph test. ASS subtitle coordinates then scaled relative to its internal reference canvas and large sentence cues bloated into enormous on-video text. The separate dark rounded rectangle was drawn at the bottom, nowhere near the rendered huge subtitle glyphs. The old test checked text existence/order but never bounded subtitle pixels. This was a renderer/layout error, not a factual-science problem.

## New original quality rules and concrete code

- Caption renderer: autopilot/polished_caption_v2.py emits native ASS with PlayResX=1080, PlayResY=1920 for Shorts or 1920x1080 for long. Short font=49 **native pixels**, at most 7 words/card, <=2 lines, <=29 characters/line, case-preserved original narration, voice-time-split microcards, 65/80-ms fade and 130-ms pop, contextual selective highlights. Portrait safe band y1295..1570 center y1420; landscape safe band y756..935 center y845. Never intentionally position text over source evidence.
- Scene renderer: autopilot/full_topic_narrated_pack.py now masks the real caption-safe band with a quiet solid dark field, moves signal indicator above it, and uses the native ASS visual subtitle file for the burned text. Separate SRT remains for accessibility and checking speech words. Frame-level pixel test on physical 1080x1920 FFmpeg output guards subtitle leakage above/below band.
- Original editorial covers: autopilot/polished_thumbnail_v2.py creates 1280x720 artwork with bold left typography, restrained left text grid, a right-side original dimensional subject illustration, concise focal metric and a tiny UNAPPROVED demo marker. No stretched full-screen legal warning or giant empty presentation border.
- Original procedural micro-SFX: autopilot/polished_sound_design_v2.py adds 5 Short or <=8 long small mathematical-only UI sounds (soft tick, gentle notification ping, airy sweep, number reveal), anchored to measured WAV scene timestamps. They are not borrowed audio from the uploaded clip and are bounded to <=0.05 peak per generated effect, with final FFmpeg loudness/limiter. They do NOT certify human audio quality, Voice-model licence or narration timbre.
- Tests: autopilot/test_polished_caption_v2.py validates exact text preservation, maximum two lines, no ASS injection, native pixel positioning and every real NASA/NIST/USGS script. The thumbnail suite physically renders three original PNGs in CI; sound suite actually synthesizes PCM and verifies source times/peaks; existing source/scene tests also run. The new main-only workflow separately renders two full source-linked Shorts for review, extracts genuine frame images at 4s and 16s and retains a seven-day GitHub artifact.
- Real FFmpeg visual acceptance: in a 1080x1920 constant dark background, non-background caption glyphs must appear only in the designated band. If captions are absent or escape above y1295/below y1570, fail the release-preflight suite. This is a visual technical guard, NOT a substitute for a subjective owner watch/listen.

## Limits and next creative phase

These steps are a necessary FIX to legibility and cover composition, not yet full professional reference-level VFX. The original story SVGs remain fairly simple and dated; to reach a rich cinematic visual level, continue with ORIGINAL subject-specific layered 2.5D cards/perspective devices, scene-to-scene camera animation, shot variety, realistic shadows, object motion on speech beats, speech pacing and deliberate sound placement. Voice content still requires human listening for pronouncing numbers, inflection, breathing/pauses, loudness and style. References do not grant reuse rights. An original low-level SFX pulse is not an assertion the reference uses that exact effect.

A new render must be inspected by the owner before any upload, factual approval, copyright/voice/model rights sign-off or workflow billing enablement. Branch 1 assisted uploader remains untouched. Branch 2 is **40/100 production-capability evidence** but real unattended YouTube publication still **0/21**. The owner gave explicit negative creative feedback, and we must never silently treat a technically passing video as approved.
