# ADR-0061 — B4e6 make original video visuals follow the exact science scene

**2026-11-06 IST. Source/pixel/real-render proof work only. No YouTube publication, AWS deployment, independent claim or commercial media-rights approvals.**

## Actual visual evidence that motivated this implementation

B4e5 physically generated and retained [run 42183265488](https://github.com/Tirthanand17/taskless-lab/actions/runs/42183265488), an artifact with **all 32 science scenes** (6 Moon Short, 20 long data-transfer scenes and 6 earthquake Short scenes) and 96 source-motion frame observations. Direct review of those images showed a quality limitation: the Moon Short repeatedly alternated the same Earth/Moon composition and generic slider bars; the earthquake Short reused the same three histogram bars and energy waves; the long recycled a five-motif set of laptop cards, sliders and bars over twenty beats. Pixel changes alone are not creative variety. This is NOT proof of verified engagement or a claim that repeating diagrams are inherently bad. User feedback specifically requested fewer unrelated central circles and more design polish.

## B4e6 creative correction

Add `autopilot/action_specific_floating_v7.py`, introducing a **new opt-in `science_v7` rendering mode** in `autopilot/full_topic_narrated_pack.py`. It uses ONLY the 2026-11-12 existing original NASA/NIST/USGS science stories and creates **nineteen story-action-specific source illustrations**, retaining the other thirteen already suitable science shots:

- **Moon Short — 4 changed of 6:** lunar distance ruler, straight radio-signal waveform, physical one-way travel-time calculation and separately directed reply waveform. The Earth and Moon still appear where scientifically appropriate, but generic back-and-forth repeating bars are not used for every physics point.
- **Earthquake Short — 4 changed of 6:** magnitude-to-energy curve, two-step logarithmic comparison, illustrated ground/building caveat, clear logarithmic-scale conclusion. Original earthquake wave introduction is retained where it directly illustrates measured wave amplitude.
- **Long data-transfer video — 11 changed of 20:** eight distinct bits, precise Mb/s label, theoretical transfer duration, network bottlenecks, decimal-vs-binary unit comparison, paired transfer times from **the original sourced calculations**, unit-conversion workflow, lowercase/uppercase b/B typography, binary/decimal multipliers and an action-specific final takeaway.

The code uses deterministic Pillow original art, no copied clip/image, no generated copyrighted footage, no real modeled 3D, no time-dependent looping radial spinner motif. It keeps all scene source titles, verified original research calculation values, voice script, citation IDs and frozen source `draft_sha256` unchanged. It wipes the old generic hero only within the native art region, preserving top original heading and the lower real ASS caption zone **pixel for pixel**. New visual recipe is opt-in; every existing `classic_v2`, `cinematic_v3` and `floating_v6` render remains compatible.

The additional source review builder `autopilot/retain_action_specific_three_v8.py` produces three physically rendered side-by-side contact sheets of all 32 original beats plus **eight direct old-versus-new physical before/after images**. It checks 19 changed and 13 unchanged scene hero crops, source identity, frame bounds, unchanged outside-hero pixels and explicitly denies implicit release approval.

## Scope of technical proof

The new GitHub Actions source-art workflow has only `contents: read`, uses zero secrets/OIDC or provider calls, installs locally cached Pillow/CairoSVG and runs real native-size frame pixel tests. A successful run stores only **public original science demo** source-art PNGs and sanitized metadata for seven days; it is not a private escrow, licensed production source, real new story, actual YouTube live media, or a user-approved edit.

The `science_v7` style is wired into the actual existing FFmpeg/Kokoro production renderer, but **source-scene-only proof is not the same as an actually encoded, fully decoded final H.264/AAC MP4**. Real encoded v7 2 Shorts+long media and full independent playback/rights approval remain a separate required downstream check.

## False-certification controls

- No automated assertion that all spinners or repeated patterns have been eliminated; correct source-driven circles can still exist.
- `human_visual_preference_verified=false`, `generic_spinner_absence_human_verified=false`, `release_authorized=false`, existing source editorial facts/rights/voice still false.
- The public original drafts are dated November 12, 2026. They are **not** tomorrow's new researched content, not external human or owner-approved media, not 21 distinct future releases.
- Branch 1 published/scheduled YouTube MP4s and video IDs are untouched; they cannot be byte-edited in place.

## Explicit remaining production blockers

A model/provider and real daily current research, owner-signed human facts/rights/final full-watch approvals, protected private persistent artifact vault and PostgreSQL session fencing, exact trusted cloud IAM network/billing consent, production Google OAuth with egress, safe private-first YouTube upload and verified 21 distinct laptop-off releases remain unimplemented or unverified.

**Readiness evidence score remains 40/100; independent Branch 2 YouTube releases 0/21.** A visual-quality code PR does not count as production deployment or actual channel improvement until verified viewer metrics are obtained legitimately.
