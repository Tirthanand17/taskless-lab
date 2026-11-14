# CLIVOX V2 P4 — Quarantined private-source technical preflight

**Integration state (2026-11-14):** synthetic-only code and no-secret workflow **verified on merged main**, actual P4 creator-media handoff **NOT COMPLETE**. This is NOT a legal permission verifier or an active vault. The public controller repository remains Tirthanand17/taskless-lab; target channel UCfPEvy0SefE_5nNlYlY_CyQ.

## What was added

- scripts/branch3_v2_p4_synthetic_handoff_preflight.py reuses the existing A3 closed-policy/creator-registry/channel checks, plus the V2 real-rights state. It **fails closed** on missing or prematurely enabled media, licensing, vault, OAuth and publishing flags.
- Source-free synthetic fixture handling only: reads a bounded (maximum 8 MiB) local MP4 in a caller-selected scratch directory. No external URLs, untrusted platform downloaders, GitHub API calls, uploader, open-source video finder, source cloning, files written or network clients.
- Verifies exact caller-supplied SHA-256, byte size, local regular file/no symlink and canonical single-file path. Local ffprobe checks MP4, H.264 yuv420p video, AAC audio, stream-count, dimensions, synthetic duration (0.1–10 sec) and declared size. Local ffmpeg decodes both streams to null output. This is **technical QA only**: the expected digest itself is not authenticated, codec inspection is not license validation, and tool safety requires an isolated runner.
- scripts/test_branch3_v2_p4_synthetic_handoff_preflight.py includes negative cases for wrong Clivox channel, forged grants, public/private storage switches, wrong source counts, traversal, symlinks, tampered hashes, malformed or contradictory probe data, unsupported streams, bad decode and unavailable tools.
- .github/workflows/branch3-clivox-v2-p4-synthetic-handoff-qa.yml exercises the real Python CLI with a brand-new generated 160x90 test pattern and synthetic sine audio created entirely under RUNNER_TEMP. There is no private licensed video, secret, upload artifact, channel operation or retained multimedia.
- Public CLI reports contain **no media path, digest, private repository name or raw ffprobe output**, and all media/YouTube/owner rights flags stay false.

## Explicit boundaries

P4 cannot move to full completion until a trusted human independently authenticates a creator/rightsholder and exact commercial YouTube editing rights, including guest/music/game and third-party components, revocation status and scope; the CLIVOX owner selects/approves the creator, actual source delivery method and confidential storage; the owner-approved private vault is independently reviewed for actual access controls, retention, leakage/expense and GitHub Apps; and exact licensed source content is supplied through the authorized separate route.

The current A3 private vault readback and private GitHub release storage are prior **design/limited preflight**, not proof an approved vault/media source exists. Do not move restricted video, agreements, private contacts or access links to this public repo, public CI, GitHub issues or artifacts. No YouTube or Twitch media download URLs may be accepted as media delivery.

Do not reinterpret the real-file inspection function as an authorization to process creator material: **the only supported execution in current public CI is a newly generated synthetic sample.** A later protected, independently reviewed private runner must address genuine authorization, consent/revocation, isolation, provenance, race safety, source-size limits, long-video codecs, private media encryption and short-lived access. A passing fixture is not a working licensed clipping pipeline.

## Verified GitHub code and test evidence

- [Feature PR #210](https://github.com/Tirthanand17/taskless-lab/pull/210) merged with **3/3** PR checks green; the [dedicated PR P4 QA run](https://github.com/Tirthanand17/taskless-lab/actions/runs/43583044360) passed after resolving missing distro FFmpeg on the runner.
- Merged main implementation SHA: `1f23a5081a1e6a75b256c58be6116f496d157b69`; [P4 synthetic integrity/codec/decoding QA run #43583149761](https://github.com/Tirthanand17/taskless-lab/actions/runs/43583149761) **success**.
- Merged-main [Content Quality Gate #43583149710](https://github.com/Tirthanand17/taskless-lab/actions/runs/43583149710) **success**.
- **21** source-free Python unit tests across the P4 and existing A3 closed-storage suites passed in dedicated QA, followed by an actual runner-generated synthetic MP4 transcode/FFprobe/FFmpeg validation. No rights-controlled media or private documents were used.

## Verification and progress

Test locally with standard Python, FFmpeg and ffprobe using your own newly generated synthetic file; the GitHub workflow independently generates its own. No external services, cloud credentials or billable APIs are necessary for this test. Record feature PR CI, merged-main run and exact commit separately. The source-free engineering is **P4 synthetic technical preflight verified on merged main**. P4 actual acceptance is still blocked by independent human rights verification and owner-approved confidential vault/source delivery.

V2 roadmap remains **2/12 (17%)**. No third-party uploads or live creator clips have occurred. FlowMinute Branches 1 and 2 and the original-only Branch 3 video staging are not modified.
