# B1v10 dependency and licensing review — 2026-11-26
Status: audited for isolated development. Commercial deployment remains conditional on eligibility and asset-specific rights.
## Existing runtime
Repository motion-v2/package.json already declares Remotion, React 18.3.1 and React DOM 18.3.1; historical src/Root.tsx contains many compositions. Remote machine: Node 24.18.0, npm 12.2.0, Remotion/CLI 4.0.534 in flowminute-oct11/motion-v2/node_modules. Existing runtime reused via local junction in b1v10-dev; no changes to historical code or dependency tree, no paid installs. Do not run npm install inside that junction. For future Three.js testing use an isolated pinned dependency set; record lockfile and validate React peer versions. Hardware Intel i3-1115G4 (2C/4T), 7.74 GiB RAM, Intel UHD. Blender not found in PATH; no assumption of GPU acceleration.
## Decisions
| Component | Decision | Evidence/condition |
|---|---|---|
| Remotion 4.0.534 | Reuse existing, isolate entrypoint | https://www.remotion.dev/docs/license/pricing and https://www.remotion.dev/docs/license/faq: free commercial use for eligible individuals/teams of up to three people, subject to terms. Confirm operator eligibility before deployment; no billing activation. |
| Three.js | Next benchmark | MIT: https://github.com/mrdoob/three.js/blob/dev/LICENSE ; use frame-driven integration via https://www.remotion.dev/docs/three-canvas and GL angle test, not assumed GPU support. |
| EDStudio | Architecture inspiration ONLY | Repository https://github.com/dylann4500/EDStudio ; exact license page not successfully retrieved. No code/assets copied, no clone. |
| Blender | Optional asset creation | Use only if benchmark justifies; no automatic installation. |
| Motion Canvas | Alternative only | Avoid duplicate motion engines. |
| SVG / CSS | Default lightweight 2.5D | Original geometry, gradients, shadows, frame-timed movement. |
| Kokoro af_heart / Whisper / FFmpeg | Retain previous workflow | Verify exact model/source/voice and dependency licenses on asset manifest; ASR is not listening approval. |
| YouTube Audio Library | Preferred source of recorded effects | https://support.google.com/youtube/answer/3376882 ; check each asset's terms/attribution and record hashes. No reference reel audio. |
## Scope
Initial smoke test only, no upload, no paid services, no new subscription. Dependency discovery is complete; Three.js installation, runtime and production eligibility remain open. Retain mandatory natural-narration listening gate and established release verification. No blind clone of public projects.
