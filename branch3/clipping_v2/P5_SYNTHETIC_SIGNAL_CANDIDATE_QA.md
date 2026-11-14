# CLIVOX V2 P5 — Synthetic acoustic + scene signal candidate preflight

**Scope:** technical proof on a newly generated, original **6-second synthetic color/sine pattern**, NOT actual licensed creator-source moment detection. Intended CLIVOX channel: UCfPEvy0SefE_5nNlYlY_CyQ. Github public repo only stores code, text and QA. **No licensed creator media, transcripts, contact details, contracts or API keys.**

## Implementation
1. Validate exact real A3 + V2 P4 deny-by-default rights, source, vault, outreach and YouTube state *before attempting media processing*. No flag promotion, real source rights, private storage or publishing capability.
2. Reuse P4's strict exact SHA-256/file-length, no symlink and H.264/AAC MP4 full decode validation. This is a local fixture boundary, not legal source authentication. The GitHub Actions test generates the fixture itself in ephemeral RUNNER_TEMP.
3. Run FFmpeg with a fixed file-protocol-only input; extract raw 8-kHz mono PCM and tiny 16x9, 2-fps grayscale frames into bounded ephemeral process buffers, not files. Keep the test fixture under 8 MiB/10 seconds.
4. Compute 500-ms audio RMS windows and grayscale interframe pixel changes; propose deterministic intervals with surrounding setup/payoff context and merge overlapping events. Signals mean **possible editing review timecodes**, not comedy, original narrative value, speech recognition or trending/viral likelihood.
5. Redact paths, source hash, pixel/audio bytes and human names from the CLI result. Output only candidate time boundaries, generic evidence kinds and explicit rights/editorial denial booleans. The synthetic fixture result is thrown away when the ephemeral runner finishes.
6. Fail closed for malformed videos, mismatch, unsupported formats, corrupted output, command failures, timeouts, spoofed rights, wrong channel, unsafe paths and bad timecodes.

## What P5 deliberately does NOT claim
- No Silero VAD, faster-whisper ASR, PySceneDetect, on-real-source facecam, human quote checking, real creator-source data, rights, editing, Youtube upload, virality prediction or third-party retention graph. Pixel changes are **not** a PySceneDetect replacement and RMS jumps are **not** validated speech or laughter.
- No determination of a "good" moment merely because a sudden cut or loud sound appears; loud background music is an explicit false-positive risk.
- No legal permissions from a passed synthetic file, no cache of private source data, no footage in a public repo/CI output, no platform video downloaders.
- No truth/accuracy/commercial clearance of any external material and no real editor-rated precision/recall.

## QA
- Standard library unittest adversarial tests for true closed upstream policy and unauthorized activation, source hashing, frame/time bounds, path traversal, symlinks, malformed streams, FFmpeg failures, and no-peak/no-cut behavior.
- GitHub workflow .github/workflows/branch3-clivox-v2-p5-synthetic-candidates-qa.yml generates black (0–2 s), white (2–3 s), black (3–6 s) plus silence/sine/silence. Independently verifies there is at least one measured candidate, with both luma-cut and RMS-rise evidence and **no transcripts, scores, publisher authority or YouTube writes**.
- The exact generated sample is **not** committed or uploaded to an artifact; runner packages use available distro FFmpeg. The upstream P4 and P5 suites run inside read-only CI.

## Next real acceptance requirements
1. Real P2 creator selection and identity confirmation; P3 authenticated independently reviewed commercial grant and revocation status, including third-party publisher/music/guest rights.
2. Separate actual owner-approved, independently audited private media vault and real creator-supplied licensed source handoff under P4. Public repository must never contain restricted video or agreement bytes.
3. Protected, isolated real-source pipeline with authorized source access, permitted speech processing/model consent, VAD/ASR confidence/quote correction, longer media codec/storage bounds, and source-context verification.
4. At least 40–60 independently editor-labeled **legal** moments across approved sources, held-out evaluation by creator, top-5 editor-agreement/error analyses and meaningful time saved. No synthetic P5 fixture proves detector performance.
5. Separate P6 editorial value-add and P8 final owner signed release before any Clivox publication.

**Roadmap:** 2/12 phases = 17% verified complete. P5 signal engineering verified only after PR and main CI; real P5 milestone and real licensed clipping remain blocked. This estimate does **not** count synthetic test implementation as a finished creator-clipping system. FlowMinute B1/B2 untouched.
