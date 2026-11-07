# ADR-0105 — Mobile-readable original infographic labels at physical output resolution

**2026-11-07 IST | Branch 2 | no-publish visual quality**

## Verified source-level readability issue
B4h1 and B4h2 made 42 fictional case names and diagram steps source-bound and varied inside the rendered visual. However, several visually important cards were still authored at only 24–33 source pixels on a 1080×1920 Short. At a representative 360-pixel phone viewing width, these display at only 8–11 pixels, making the meaning harder to read. A technically valid, non-looping MP4 is not automatically a good learning video.

## Decision
- Introduce native editorial text-size constants for scene eyebrow, narrative description, case name and diagram heading/primary/secondary labels.
- Enlarge the key glyphs for portrait Shorts and landscape long videos while retaining the exact source-validated synthetic case titles, 11 beats, four distinct diagram grammars, one-way highlight stages and native ASS caption reserve.
- Use the **actual** scale from native 1080px→360px Shorts and 1920px→960px long view to enforce at least 12 display pixels for selected important infographic labels. This is an internal conservative minimum for visual QA, **not** an assertion about actual phone DPI, platform UI rendering or an official YouTube typography standard.
- Retain bounding-box refusal for all text placed on native frames; test all 42 case labels with real Pillow/DejaVu glyph metrics and all existing 17 B4f9 scene rendering and subtitle-pixel tests. Reject clipping instead of abbreviating original narration/claims.
- Require primary color contrasts against the darkest and lighter gradient colors to exceed a conservative 4.5:1 engineering threshold. This is **not** web accessibility certification.
- Zero new external images, article sources, model provider, secrets, network, paid API, YouTube upload, publish authorization, or live schedule edits.

## Acceptance and remaining gaps
Pass 4/4 exact-head GitHub PR workflows, including actually rendered 17 unique original scenes. Recheck the main no-publish workflow after merge. The B4g0 17-scene manually dispatched GitHub contact-sheet artifact is only a visual preview—not owner watch of encoded MP4s. A human still needs to review final voice, captions, graphics, pacing, full three videos and rights/factual claims. Desktop memory remains unused for source/media work.

Readiness stays 45/100; verified unattended public releases remain 0/21 until authenticated YouTube evidence.
