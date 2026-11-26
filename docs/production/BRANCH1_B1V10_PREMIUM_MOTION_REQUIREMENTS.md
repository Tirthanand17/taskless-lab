# B1v10 — Premium motion graphics engine (version 0.1.0 development)
Status: DEVELOPMENT / REVIEW ONLY. Date: 2026-11-26. Branch 1 (assisted releases). Existing B1v9 Nov 27 schedules and Branch 2 remain untouched.
## Objective and evidence
Create original, interesting technology explainers approaching the supplied reel's visual storytelling, not a copy of its mascot, branding, graphics, audio or claims. Reference 116.467 s, source recording 454x804/30 fps. Sampled quarter-second pixel changes >0.5: reference 61.56%, B1v9 storage 14.7%, QR 19.7%. Diagnostic only, not a quality or ranking score. Prior Studio baseline 20% stayed / 80% swiped; long 736 impressions, 3.9% CTR (Oct26-Nov22). No claim of causal improvement.
Previous release: [B1v9](BRANCH1_B1V9_2026-11-27_VERIFIED_RELEASE.md); [reference study](BRANCH1_B1V9_2026-11-27_REFERENCE_REEL_RESEARCH.md). Exact creator toolchain unknown.
## Architecture and constraints
Reuse existing motion-v2 Remotion runtime (repository package already exists; Windows installed version 4.0.534, Node 24.18.0/npm 12.2.0). New isolated composition/entrypoint under autopilot/b1v10, no changes to historic compositions. Hardware checked: i3-1115G4, 2 cores/4 threads, 7.74 GiB RAM, Intel UHD graphics; start concurrency 1, measure render seconds/frame and memory, use lightweight SVG/CSS 2.5D by default. Three.js selectively for true 3D after benchmark; Blender optional offline asset authoring, not every frame. No paid services, billing or large installs without justification and authorization; check Remotion license eligibility before production. Keep local non-secret artifacts within existing youtube con workspace; repo stores source, docs, tests, manifests, small original assets, not tokens or bulk video. Avoid duplicate framework copies. Maintain [growth standard](../FLOWMINUTE_GROWTH_PRODUCTION_STANDARD_V2.md), [narration standard](../NATURAL_NARRATION_STANDARD.md) and [workspace policy](../LOCAL_WORKSPACE_POLICY.md). Existing full listening gate remains mandatory unless separately and explicitly revised; automated ASR cannot substitute for it.
## Versioned requirements
R01 fresh candidate research (today/previous day), Studio trends where accessible, source links/dates, score at least three candidates, select 2 distinct Shorts + 1 long when instructed; quality overrides quota, evergreen fallback; no unsupported demand/viral guarantees.
R02 one clear promise, immediately visible truthful hook, actual evidence, coherent mechanism, practical payoff, scene-specific compositions; diagrams illustrative and real tests labeled.
R03 original native 1080x1920 and 1920x1080 at 30 fps, H264 yuv420p BT.709, sharp SVG/text, deliberate negative space; useful lower-screen takeaway above UI-safe areas; verify actual phone frames, no clipping, clutter, blur, overcrowding or logos at opening.
R04 frame-driven timeline, continuous purposeful object movement (not perpetual decorative loops), spring/eased transforms, numbers, comparison, animated mask/magnifier, process flow, perspective, camera tracking, depth/shadows, selectively realistic 3D. Motion matched to spoken events, readable holds.
R05 reusable original SVG/GLB asset registry (source/license/hash), original mascot with blink/point/think/surprise/success poses; no copy of reference. Prefer minimal mascot use for explanation.
R06 keep existing commercially licensed Kokoro af_heart baseline; natural phrasing/pauses/intonation; voice selected by prior observation not proven cause; Whisper word timestamps, semantic transcript verification, readable groups and word highlights, SRT, short cues corrected when practical.
R07 source-licensed real Foley/music (YouTube Audio Library first, original recorded sounds where possible); attribution and provenance; map sound to actions, no random beeps, measure peaks/mix, final listening review. No imitation of identifiable voice without consent.
R08 versioned episode schema with claim-source bindings, evidence files/hashes, scene timing, visual/animation/audio event tracks, asset rights, captions, release approval. Fail closed on invalid timelines, absent assets/rights, altered hashes, pending review.
R09 render/inspect/repair loop: actual decoded frames, phone and landscape preview, no overlaps, full decode, audio integrity, caption timing, meaningful animation compared with reference using same sampler, measured wall time and resource usage. Diagnostic motion goal ~50-65% only when meaningful; not a hard ranking threshold. No claim of reference parity from resolution or metric alone.
R10 package exact files, thumbnail/SEO/metadata, owner channel, English captions, policy/disclosures and audience designation; existing protected publisher handles duplicates, future slot checks and remote readback. Never replace existing scheduled releases. No autonomous scheduling created by this development work.
R11 performance feedback 24h/48h/7d with native Studio metrics (feed opportunities, stayed/swiped, engaged views, AVD/APV, long impressions/CTR/retention) and existing matched-age tracker. Separate small-sample exploratory results from causal conclusions.
## Ordered milestones (each requires evidence, not just source files)
1. Reference analysis and requirements recorded.
2. Dependency/license audit (EDStudio reference-only pending license review; Remotion eligibility, Three.js MIT, asset and audio licenses; no blind clone).
3. Isolated Remotion render smoke test, native HD and deterministic timeline.
4. Three.js integrated, actual renderer benchmark and fallback; no GPU assumptions.
5. Reusable asset/animation components, provenance and both aspect ratios.
6. Original mascot rig and expressive motion.
7. Narration-synchronized scene/event timeline, word highlights and accessible SRT.
8. Rights-cleared realistic sound library and event-driven mixing.
9. Complete premium pilot, technical/visual and genuine listening QA, comparable motion and render benchmark, correction loop; review only until release gates.
10. Daily assisted production integration and performance-feedback handoff. No changes to legacy releases; require release readiness and publish authorization.
## Sources and candidates
Remotion https://www.remotion.dev/docs/ ; https://www.remotion.dev/docs/license/pricing ; https://www.remotion.dev/docs/three ; https://www.remotion.dev/docs/spring ; https://github.com/remotion-dev/skills
Three.js https://github.com/mrdoob/three.js ; https://threejs.org/docs/
EDStudio https://github.com/dylann4500/EDStudio (study architecture; verify license before reuse).
Motion Canvas https://github.com/motion-canvas/motion-canvas (alternative only).
Blender https://docs.blender.org/manual/en/latest/advanced/command_line/render.html (optional assets).
YouTube Audio Library https://support.google.com/youtube/answer/3376882 ; encoding https://support.google.com/youtube/answer/1722171 ; Shorts https://support.google.com/youtube/answer/11914225 .
## Definition of done
All ten milestones independently evidenced and recorded in autopilot/b1v10/STATUS.md; no fake approval, quality percentages or claims of improved views. Source version increments when behavior changes; status explicitly distinguishes implemented/tested/pending. Future sessions read this file and STATUS first, resume earliest incomplete dependency, record commit/test results. Preserve older B1v versions for rollback.
