# ADR-0092 — B4f9 cinematic editorial storyboard redesign after first real owner MP4 inspection

**November 7, 2026. Flowminute Lab Branch 2. Never a publish authorization.**

## Why a complete scene redesign

The user supplied the actual montage from the first owner review package [run 42344844198](https://github.com/Tirthanand17/taskless-lab/actions/runs/42344844198) showing giant subtitle text clipping the picture, tiny repeated educational cards and poor framing. Native-resolution subtitles were corrected by merged PR #107. A second actual cloud review package [run 42346571052](https://github.com/Tirthanand17/taskless-lab/actions/runs/42346571052) successfully confirmed no giant top-spanning captions: the actual 1080x1920 Short and 1920x1080 long contained readable native ASS two-line captions inside lower cards. However the video still resembled a simple PowerPoint: all 17 scenes repeated essentially one three-card motif, with a generic identical “Testing a claim — synthetic test” heading and no strong idea-first hook.

We cannot call this high-engagement video merely because H.264 decodes and there is no rotating circle. Video must be judged by the actual rendered pixels and real human full-watch; synthetic rehearsals have no factual news rights or independently verified claims.

## Replacement implementation

`autopilot/cinematic_scene_board_b4f9.py` is a dedicated original diagram painter. It accepts only the exact source-derived, original, unapproved 4/9/4-scene plan and returns a full 1080×1920 or 1920×1080 frame, independent of channel OAuth, YouTube or external imagery. Eleven editorial beats each have their own concise, question-led headline, short subheading and one of **four distinct visual grammars**:

- **compare:** two large contrasted paths with an explicit “same question / different path” takeaway
- **steps:** a numbered vertical decision/process sequence with the currently revealed checkpoint highlighted once
- **matrix:** three synthetic sample columns with numbered conditions, not fabricated observed outcomes
- **gate:** an unanswered verification barrier, clearly preventing accidental factual or licensing assertions

Emphasis changes **once per scene only**, matching the existing `REVEAL_SECONDS=0.36` and physical base/revealed PNG provenance checks. No concentric spinner, rotating dial, perpetual animation or generic progress loader. Each scene displays a conspicuous position in the episode and a nonmoving per-scene progress strip. Shorts use an editorial left-aligned 100px title above a dominant original illustration, and long video positions the large editorial headline left of a substantial right-hand diagram. All source-independent narration and actual PCM speech/caption timing are completely unchanged.

Crucially, the lower caption panel is deliberately blank in the underlying PNG. It keeps its original native-pixel ASS (`PlayResX=1080/1920`, 2-line microcards) after the full video composite; diagram and reveal pixels are never allowed into that reserved panel. Every text field is checked by Pillow's **actual font `textbbox`**, not only by word/character length. Overflow fails the render rather than silently clipping. The source file hashes and all prior non-factual review/rights flags remain unchanged.

## Test and acceptance

`autopilot.test_cinematic_scene_board_b4f9` renders **all 34 actual full-resolution before/after PNGs** for the 17 original scenes on the CPU cloud worker, checks per-episode unique picture hashes, visible one-time change constrained to the correct safe region and *exactly unchanged subtitle pixels*, non-factual scene metadata and all 11 beat headlines/layout families. The test is wired into the existing main cloud foundation PR test suite; published-video work remains disabled. Earlier B4f7 native-ass tests continue to verify the actual subtitle glyph region.

**This PR cannot guarantee good visual storytelling, readability on every screen or 100% engagement.** After merge, re-run the explicit opt-in cloud review export, download its original three new encoded MP4s, inspect actual beginning/middle/end decoded frames in all scenes and watch videos in full. The real YouTube owner OAuth refresh currently fails, so live uploads, edits, scheduled slots and seven consecutive days of 2 Shorts + 1 long remain unverified and blocked.
