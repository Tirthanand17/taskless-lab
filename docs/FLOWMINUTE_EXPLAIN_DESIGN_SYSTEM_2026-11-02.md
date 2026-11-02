# FLOWMINUTE LAB — FLOW//EXPLAIN Design System v2 (2026-11-02)

Status: original visual design standard, review-only until complete audiovisual approval.

## Decision and evidence
Two supplied Reel recordings were reviewed. @samjho.exe teaches through one persistent high-contrast simulated interface, progressive data changes, semantically coded colors and restrained captions; @ai.kira.creates uses animated science objects and evidence references. The exact authoring packages, voice vendors and AI generators cannot be verified from these screen recordings. We choose a code-first motion-design pipeline for recurring Excel/AI/data explainers, with the existing motion-v2 Remotion/React infrastructure as primary renderer, and Pillow+FFmpeg only as an isolated local visual proof. No new paid software is required or authorized.

Official Remotion references: https://www.remotion.dev/docs/idea and https://www.remotiondocs.com/docs/interpolate and https://www.remotion.dev/docs/flickering .

## Brand and mobile-first format
- Canvas 1080x1920, 30fps production target; allow 720x1280 24fps bounded reviewer proxy.
- Base coordinate grid 720x1280; use 1.5x scaling to deliver 1080x1920.
- Horizontal margin 48/720 (approx 72px at 1080p), never allow cards or text outside 48..672.
- Header y=56..116; eyebrow y=167; primary heading y=202..300; subordinate line y=321. A single left-aligned reading axis.
- Persistent demonstration dashboard y=398..1008. One visual state machine, no unrelated slide swaps.
- Restrained on-screen caption y=1034..1132; lower project footer / progress y=1178..1225. Verify actual YouTube player overlays; mobile platform UI changes.
- Long headings max 2 lines; reference font sizes in base coordinates: title 42px; context 23px; one-line caption 22px; diagram items 16–20px; small metadata 12–15px. Body items must not be more prominent than the teaching concept.
- Hard text-width assertions in the proof renderer; no invented screenshots, tables or authentic provider interfaces. Sample data is labelled SIM / TRAINING SIMULATION.
- 8px or 12px rhythm; consistent outer card padding, 10–22px corner radius. One focus element per beat.

## Semantic palette
Canvas #080E19, panel #0E1A2B, raised #14253A, title #F3F7FB, muted #8EA3B6, cyan #37D4D0 (technology and permission), amber #F0BA56 (attention/pending), red #F16B73 (destructive/reject), green #55D7A2 (verified safe), outline #294058. Never use color alone for states; show labels and symbols.

## Motion design, not slides
Six related states in one UI: 0-6s QUESTION, 6-12s ACCESS, 12-19s PREVIEW, 19-26s PERMISSION, 26-31s DENY, 31-36s SAFE. File-browser cards retain their positions. State inspector changes, an indicator travels along a route, permission rows appear progressively, destructive request visually blocks. Motion is driven by absolute frame position, easing/interpolation, and deterministic layout, not wall-clock JS or random frame jitter. Avoid transitions for their own sake.

## Creative and factual safety
Topic: AI agents may request tool actions, but requests are not evidence of capability. Actual operations depend on tool permission/scope and may have a separate approval step; product behavior varies. This video is a mock training simulation, not a real destructive action.
Do not claim a specific real product's default permissions, guarantee every agent has approval protection, demonstrate a fake real application, or pass invented engagement metrics as measurements.
Do not copy the creators' branding, source footage, soundtrack, exact text, visual trademark or private authoring assets.

## Current proof and limitations
A 36.0s 720x1280 24fps original motion-board prototype was rendered locally with Pillow+FFmpeg and fully decoded. SHA256 ce501ad19185df71ffcd1ee3683b0cb17b68aca589733b5bbfc35a8540a1637b. It has NO voice/audio stream and is not a release candidate. The companion source in motion-v2/src/AgentPermissionFlowExplain.tsx is an original Remotion implementation of the design contract but has not been independently executed through the GitHub Remotion render CI at the time of its creation. It must not be marked media-production accepted or YouTube ready.

## Release acceptance
1. Real natural English speech: exact fact-checked final script; source model/provider rights and human listening acceptance.
2. Animated teaching visuals: dynamic transitions and genuine instructional cause/effect in every beat; inspect every scene on 9:16 mobile screen for text, safe area, color contrast, alignment and flicker.
3. Proper timed captions, audio mix and rights-safe original SFX/music; silence on voice-only stem independently tested.
4. Licensed media and full FFmpeg decode / hash-pinned file, separate creative/factual/rights approvals.
5. Exact channel owner token and authorization, approved media, upload and public readback; no PR merge/publishing under a review-only render.
6. Reuse the existing scripts/publish_youtube.py strict schedule controls only after fixing legacy bypass, caption language, D1 and OAuth readiness.

## Existing repo paths
- motion-v2/src/Root.tsx — registered compositions
- motion-v2/src/AgentPermissionFlowExplain.tsx — FLOW//EXPLAIN original production blueprint
- docs/reference_reels/2026-11-02_two_reels_verified_evidence.md — observed reference frames
- docs/production/2026-11-02_agent_permission_pair.md — narrative/storyboard
- docs/production/2026-11-02_ai_agent_permission_render_status.md — prior crude prototype and blockers

All research/source belongs in the existing repo; generated files may be kept as approved GitHub artifacts only when licensing/quota and creator approval permit.
