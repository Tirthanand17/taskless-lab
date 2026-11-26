# B1v10 isolated HD motion benchmark

Use the existing motion-v2 runtime; locally verified Remotion and @remotion/cli 4.0.534. This folder is not imported into the historic Root.tsx. The renderer is silent, review-only, and uses an original illustrated device. No YouTube publishing code or credential is needed.

From the motion-v2 directory (with dependencies installed), render to a separate review folder:
```powershell
# PowerShell, Windows; create the review folder first.
$review = 'C:\path\to\review'
Copy-Item b1v10\smoke.tsx,b1v10\SMOKE_QA.json $review
.\node_modules\.bin\remotion.cmd render b1v10\smoke.tsx B1v10LandscapeSmoke "$review\landscape-motion-v010.mp4" --codec=h264 --crf=18 --concurrency=1
python b1v10\verify_dual_motion.py $review --ffmpeg 'C:\path\to\ffmpeg.exe'
```

The dual verifier requires the exact original vertical-smoke.mp4 whose SHA-256 is in SMOKE_QA.json. Preserve that locally generated artifact for historical evidence; newly rendered files may have different hashes, even with identical inputs, and cannot substitute for it. For a new independent benchmark generate and record new baseline evidence rather than overwriting historical hashes. The MP4s and contact sheets are local review artifacts, not committed media. Python requires OpenCV and NumPy, and FFmpeg (PATH, explicit option, or imageio-ffmpeg fallback).

The verifier validates full decode, frame count, dimensions, FPS, sampled frame change and SHA-256. These are technical checks, not evidence of sharpness, layout quality, voice, accessibility, factual quality, audience retention, or upload authorization.

## v0.2.0 — reusable visual design system (milestone 05)

- `design.json`: native 1080x1920 and 1920x1080 layout tokens, palette, responsive typography and four non-overlapping content regions.
- `visual-system.tsx`: shared Scene, Zone, Kicker, Headline, Surface, Caption, Chip and Rise components. CSS and SVG are rendered at native canvas size; the motion primitive uses frame-based eased interpolation.
- `design-demo.tsx`: original run-length-encoding teaching illustration. Eight input symbols can be written as six characters in the stated toy notation; this is not a claim about actual file sizes. The landscape variant shows explicit run-to-code mappings.
- `verify_design_tokens.py`: native-canvas and safe-rectangle geometry, typography floor, and 12 foreground/background contrast pair checks (minimum 4.5:1). Safe areas are conservative project presets, not a universal guarantee of current YouTube overlays. Validate real phone playback before release.
- `render_design_review.cjs` and `verify_design_review.py`: two native PNG frames per orientation, decoded and hashed, plus a contact sheet. The demo is not a complete episode, does not include sound, and its sample frames do not prove continuous-motion quality.

Run from an installed `motion-v2` runtime:
```powershell
python b1v10/verify_design_tokens.py
node b1v10/render_design_review.cjs C:\path\to\design-review
python b1v10/verify_design_review.py C:\path\to\design-review
```

The renderer and verifier use existing Remotion 4.0.534 / Pillow. The local PNGs and contact sheet are review artifacts; commit only the evidence report. Later milestones must cover real-device overlay checks, topic research, transition quality, asset rights, complete narration/audio, and full playback. Creative parity with the reference reels is not established.

## v0.3.0 — evidence-linked editorial handoff (milestone 06)

This local review-only adapter reuses the existing daily editorial board's subject tokenization. It complements rather than replaces autopilot/source_locked_script_briefs.py and the seven-day research history guard. It does not fetch live trends or call paid providers. The first three evergreen examples were researched against official Python and Git documentation on 2026-11-27; the original claims are paraphrases. The ranking is a manually assigned 0–5 score across the eight existing production criteria (40 points total), not estimated views, search volume or measured audience demand.

Run from the repository root:

```powershell
python -m unittest discover -s motion-v2/b1v10 -p test_editorial_handoff.py -v
python motion-v2/b1v10/editorial_handoff.py motion-v2/b1v10/editorial_fixture.json C:\path\to\new-review.json --receipt C:\path\to\NOV27_RELEASE_RECEIPTS.json
```

The optional receipt must be a local object with rows containing titles; it is treated as supplied history, not authenticated channel proof. The adapter scans existing episode JSON titles, blocks normalized exact and high-overlap title matches, enforces distinct topic families in the daily trio, and leaves slots empty instead of forcing duplicates. It verifies review-date recency relative to the plan date, HTTPS source metadata, evidence references, early proof, distinct topic families and timed storyboard structure. It does not authenticate source contents, rights, semantic originality or full channel history. Output is exclusive-create and review only. Recheck sources and live channel inventory for a new production date; do not simply update a date field.

The report includes reproducible Python float/Decimal and SHA-256 calculations and a clearly marked simulated linear-history bisect demonstration. The scenes bind to candidate/source and demo identifiers, not independently approved final narration. The visual-zone hints refer to v0.2.0 design primitives; actual video assets and scene rendering remain future milestones. No scheduled or published video was modified. Manual topic scoring, fixture choices and duration estimates are editorial defaults.

## v0.4.0 — camera, transitions and asset screening (milestone 07)

- motion-primitives.tsx provides bounded, eased 2.5D perspective camera movement, an explanatory reveal, and a localized focus light. It moves the hero art, not the caption or headline. No perpetual spinner, decorative repeating loop, external 3D model or new paid dependency.
- motion-benchmark.tsx consumes the previously executed SHA-256 A/B example from EDITORIAL_REVIEW_QA.json. The native-HD vertical three-second test shows identical bytes, a changed byte, two actual digest prefixes and the integrity takeaway. This is an original code-drawn SVG/CSS illustration, not recorded application footage or a complete Short.
- motion_quality.py validates a supplied raster asset's exact hash, declared provenance/rights evidence, sufficient source pixel dimensions and a Laplacian edge-detail threshold (25). It does not establish license authenticity; a record remains review-only. Flat intentional graphics may need alternative human inspection; artificially sharpened or upscaled images can evade this heuristic. Native vector art does not require raster upscaling.
- The benchmark checks all 90 decoded frames plus a full FFmpeg decode. Motion checks the hero region only (not changing captions), screens near-static intervals of 0.75 seconds or more and near-repeat fractions of 80% or more at lags 12/15/20/30 frames. This is a bounded review heuristic, not universal loop detection, and valid intentional holds or repetitive instructional demonstrations may need documented review.
- Eight offline tests cover good raster input, hash tampering, missing rights metadata, undersized raster, flat edge detail, frozen frames, repeated sequences and a changing non-repeating sequence. Four sampled frames were visually inspected as a contact sheet. No full human playback or publication approval is recorded.

Reproduce from motion-v2 with the existing local Remotion runtime:

```powershell
python -m unittest discover -s b1v10 -p test_motion_quality.py -v
node b1v10/render_motion_review.cjs C:\path\to\motion-review
python b1v10/motion_quality.py C:\path\to\motion-review --ffmpeg C:\path\to\ffmpeg.exe
```

The hash-linked MOTION_REVIEW_QA.json records the actual vertical render; the MP4 and contact sheet remain local. Landscape reuse of the new camera primitives and integration with complete rendered scenes require pilot validation. Benchmark thresholds and camera bounds are project defaults, not measured audience preferences. The existing publisher and historical videos remain unchanged.

## v0.5.0 — offline narration and measured word captions (milestone 08, technical implementation)

The existing local Kokoro ONNX model and af_heart voice are reused. No new provider, model download, billing, or voice cloning. The four-scene original SHA-256 explanation uses small phrase-level speed adjustments and explicit short pauses; these are editorial choices, not proof of emotional naturalness.

- narration_review.py produces mono 48 kHz PCM, normalized scene audio, integer-frame scene boundaries at 30 fps, local Whisper base word timestamps, raw ASR captions, SRT and a hash-bound QA report. Scene duration follows speech rather than stretching narration to an arbitrary storyboard estimate.
- Actual sample: 581 frames / 929,600 samples / 19.3667 seconds, 60 recognized words and 14 caption cues. Three of four raw scene transcripts match the locked script exactly; the first contains the homophone "bite" for "byte." The raw ASR gate remains false.
- correct_caption_homophone.py permits only that explicitly locked correction. It preserves all observed word timings and the original ASR record. Other mismatches require review. Corrected caption text matches the script; this does not establish pronunciation quality or semantic accuracy of arbitrary ASR corrections.
- word-caption.tsx uses actual word intervals to highlight the active word, and narration-caption-demo.tsx selects the scene by exact audio-derived frame boundaries. Three native-HD stills were rendered and visually inspected in both orientations. This is a timing preview, not a completed animation or proof of full AV playback synchronization.
- Human listening approval, actual pronunciation review, rights approval and final audio-video playback remain pending. This milestone is technically implemented but cannot be counted as fully accepted until the mandatory listening and synchronization review clears.

Local reproduction (existing vendor assets and FFmpeg required; output directory must be new):
```powershell
python b1v10/narration_review.py --assets C:\path\to\existing-kokoro-assets --ffmpeg C:\path\to\ffmpeg.exe --output C:\path\to\new-review
python b1v10/correct_caption_homophone.py C:\path\to\new-review
python -m unittest discover -s b1v10 -p "test_*.py" -v
node b1v10/render_narration_preview.cjs C:\path\to\caption-preview
```

Committed preview fixtures include the exact observed raw and corrected captions and QA reports; the locally generated WAV and preview images remain on the workstation. Do not publish the preview or modify existing scheduled videos. The preferred synthetic voice is a candidate baseline; it is not a human recording.

## v0.6.0 — narration-first original sound design

Owner said the v0.5.0 voice is good for now and requested it be kept (current project conversation). Preserve the exact reviewed narration SHA-256; this is voice acceptance for the current development sample, not approval of later audio mixes, video synchronization, or publication. The earlier raw ASR report remains unchanged.

sound_mix.py reuses the existing original procedural micro-effects from autopilot/polished_sound_design_v2.py. Four accents are anchored to observed words and rounded to exact 30-fps frame/sample coordinates for later visual integration. A quiet original non-melodic tonal bed ducks under speech using a smoothed RMS envelope. No third-party audio recordings, music downloads or paid services. The original narration samples remain the unmodified voice stem. This is a restrained ambient texture, not a full cinematic music composition.

The actual 19.3667-second mix preserves all 929600 samples, including after AAC encoding and decoding. FFmpeg measures integrated loudness and true peak; the encoded speech is independently transcribed using the existing offline Whisper base model. The numerical screening thresholds are engineering defaults, not evidence of perceived sound quality or viewer retention. Visual event alignment, subjective mix listening, final rights and publication approval remain pending.

Reproduce using the existing local v0.5.0 WAV and FFmpeg:
```powershell
python motion-v2/b1v10/sound_mix.py --narration C:\path\to\narration.wav --output C:\path\to\new-mix --ffmpeg C:\path\to\ffmpeg.exe
python motion-v2/b1v10/verify_encoded_speech.py C:\path\to\new-mix
python -m unittest discover -s motion-v2/b1v10 -p "test_*.py" -v
```
Audio files remain local; only QA reports and code are committed. The next full Short must use the same frame-bound event plan and independently verify rendered synchronization and review the final mix.

## v0.7.0 — integrated SHA-256 Short pilot

The first complete review-only pilot combines native 1080x1920 Remotion motion graphics, actual SHA-256 example values, the existing accepted voice, original sound mix and observed word captions. The four scenes use exact audio-derived frame boundaries and all four planned sound events produce measured visual changes at their target frames. No external imagery or music was added.

Local reproduction (existing dependencies and v0.6.0 audio required): copy the pilot source and its imported dependencies into the existing installed Remotion workspace, then run node render_short_pilot.cjs short-review-v070. From this repository's motion-v2/b1v10 directory run python verify_short_pilot.py <review-directory> --mix <v0.6.0 mix.m4a> --ffmpeg <ffmpeg.exe>. The verifier muxes without audio re-encoding, checks full decode, compares actual decoded PCM (not WAV metadata), measures loudness and hero-region motion, and produces SHORT_PILOT_QA.json and a 20-frame contact sheet.

Actual pilot: 581 frames at 30 fps, 19.3667 seconds; 929600 audio samples identical to the reviewed encoded mix after decode; -16.86 LUFS, -1.96 dBTP, no clipped samples. All four scenes clear the existing freeze/repetition screening heuristics. Representative frames inspected, not a claim of full subjective playback. The full-length hash reveal is animated and the final example labels a matching prefix rather than implying that prefix equality proves integrity. All 64 characters must be compared. The layout retains conservative Shorts UI margins; full phone playback and sound listening remain owner review tasks. The final MP4 and contact sheet are local artifacts, not committed media or approved releases.
