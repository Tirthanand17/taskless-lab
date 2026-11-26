# B1v10 development status — v0.1.0
Updated 2026-11-26. Branch 1. REVIEW ONLY. No YouTube mutations; B1v9 Nov27 schedule preserved. Source and development requirements: ../../docs/production/BRANCH1_B1V10_PREMIUM_MOTION_REQUIREMENTS.md.
## Milestones (2/10 fully verified, 1 partial, 7 pending)
| # | Milestone | State | Evidence / acceptance |
|---|---|---|---|
| 1 | Reference analysis and requirements | PASS | 7e494237ba44beb1fb713ed75a04472f284c46bd |
| 2 | Dependency and license audit | PARTIAL | DEPENDENCIES.md; runtime and license terms checked. Remotion operator eligibility and EDStudio license unresolved; EDStudio not reused. |
| 3 | Isolated Remotion integration | PASS | smoke.tsx corrected; 90-frame native HD vertical render decoded, landscape native-HD still, sampled actual frames inspected. |
| 4 | Three.js integration and GPU/fallback benchmark | TODO | Isolate pinned dependencies, verify React peers, benchmark hardware/software WebGL and measure peak resources. |
| 5 | Reusable scene and asset library | TODO | SVG/GLB provenance and reusable effects in both aspect ratios. |
| 6 | Original mascot | TODO | Original visual design, pose rig and frame-driven animation; no reference copy. |
| 7 | Narration-synchronized timeline | TODO | Typed event contract, actual word timestamps, caption QA and meaningful motion. |
| 8 | Realistic licensed Foley | TODO | Recorded rights-cleared sound assets, event tracks and audio mix. |
| 9 | Premium pilot and quality comparison | TODO | Complete episode, actual frame/voice review, repair loop and benchmark. |
| 10 | Assisted production integration | TODO | Gate exact assets/metadata, test protected publisher handoff, matched-age performance tracking. |
## Executed smoke test
Windows i3-1115G4, 2 cores / 4 threads, 7.74 GiB RAM, Intel UHD. Existing Remotion/CLI 4.0.534 with Node 24.18.0, npm 12.2.0. Local isolated directory C:\Users\Dell\Desktop\youtube con\b1v10-dev, node_modules junction points to existing flowminute-oct11/motion-v2/node_modules; do not install into junction. Test source commit faab97ef5c0763fb7a021ab77d504f9ea1e63950, factual reveal correction 7675dd1ea8a9e0dbfdd78255e3faa9973545e6b3, verifier 96da7b2e9950d02b57cdd2c01c6bf58d4c275686.
First render took 44.737s. Sampled review caught misleading transient GiB values. Corrected version displays 128 GB then exact rounded 119.21 GiB; no intermediate values shown as actual capacity. Re-render took 51.557s (including bundle/startup/encode). Corrected output: 1080x1920, 30fps, 90 frames / 3s, H264 CRF17, full decoding passed; 1920x1080 still frame 89 passed. Four corrected decoded frames visually inspected. 11 transitions at 8-frame interval all exceeded 0.5 grayscale delta on 227x402; this short deliberately moving smoke scene is not comparable to full reel quality or retention. No audio (intentional smoke test); no human playback approval, 3D rendering or full landscape video. Webpack cache warnings missing undici-types and @types/json-schema did not prevent success; do not change legacy dependencies to suppress warnings. Peak RAM not measured. No paid installs.
Final source SHA256 2f2f5069a68d4d614d218b315382f3e9db5fda89a99a60f5ea2afa9762c2839b
Final MP4 SHA256 34f3d8773f7a1b8d35ed002411b4716d951ee0a4bee8a85a2a8ef252682b5a8e
Landscape PNG SHA256 8214b0a71939b546df4800df5030368596976181e9cf0e0dcc5a055b65cc5ff4
Local evidence: vertical-smoke.mp4, landscape-smoke.png, smoke-contact.jpg, SMOKE_QA.json. No bulk media committed.
## Resume
Resolve eligibility before production deployment. EDStudio reference-only until license established; no copying. Next technical phase #4: isolated Three.js dependency/renderer benchmark with lightweight GLB or procedural geometry, frame-driven motion, renderer fallback and real resource readings. Preserve earlier releases and full listening gate. Update this status after every completed acceptance test; bump version on behavior changes. No claim of reference parity or audience improvement. No new automation.
