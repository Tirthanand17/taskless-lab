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
