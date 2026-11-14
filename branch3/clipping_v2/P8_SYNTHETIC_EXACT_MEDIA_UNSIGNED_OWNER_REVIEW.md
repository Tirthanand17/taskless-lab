# CLIVOX V2 P8 — Exact synthetic media unsigned owner-review preflight

**2026-11-14 technical integration; no genuine P8 owner authorization.** This stage takes the actual small P7 original-only vertical test MP4, independently rechecks it, and prepares a strictly **UNSIGNED** owner-review request. It does **not** impersonate the CLIVOX owner, infer that video quality implies legal permission, create owner keys, enroll a signer, grant creator rights or make a YouTube upload.

## Architectural reuse instead of a duplicate signer

The repository already contains:
- \`scripts/branch3_a6_signed_release.py\`: domain-separated Ed25519 signing subject/verification demonstration, authentic **production_release() always denied**, and exact A6 release-policy quarantine validation.
- \`branch3/release/release-policy.json\`: **0 real enrolled owner signing keys, 0 licensed assets, 0 signed releases**, media downloads and YouTube writes denied.
- \`scripts/branch3_a6_original_review_signature.py\`: separate original fictional-arcade exact-video review signature math; a caller-supplied key is explicitly *not* independent owner enrollment.
- Existing \`scripts/branch3_v2_p7_synthetic_vertical_renderer.py\`: actually generates and checks a 270×480, H.264/AAC self-generated test MP4. It does not process other creators' content.

P8 deliberately **reuses** the current A6 quarantine validator and P4 MP4 SHA/codec/full decode plus P7 FFprobe, pixel caption/scene and PCM tone/silence checks. It does not add a competing production release workflow or a second cryptographic approval system. A signed release requires a separately independently enrolled owner's actual key, authenticated commercial rights/contract scope and fresh revocation evidence, real human inspection, a new protected production controller and correct Clivox account. None exists here.

## Concrete P8 integration

1. CLI \`scripts/branch3_v2_p8_synthetic_unsigned_review.py\` checks real A3/P4/P5 closed policy and the real A6 release policy **before** reading generated test media.
2. Accepts **only** fixed inputs under the ephemeral GitHub Actions \`RUNNER_TEMP/clivox-p5-synthetic\`: \`synthetic_clivox_short.mp4\`, \`synthetic-edl-draft-only.json\` and \`synthetic-render-qa-only.json\`. No arbitrary source URL, downloader, private media path, external keys or owner identity fields.
3. Validates the **exact P6 written storyboard** contract and **exact P7 technical report** schema (270×480, 6 s, codec/caption/audio checks true, zero creator footage/rights/YouTube actions). Any extra field or forged approval fails closed.
4. Reads the already-rendered P7 MP4 using Linux \`O_NOFOLLOW\` and a regular-file identity/size check, computes SHA-256 and bound size, then invokes P4 checksum and full media decode; FFprobe validates codec, aspect, 24 fps, stream starts and 6-second audio/video duration; P7 extracts frame pixels and PCM to independently confirm captions, scene transitions and sound cue. It hashes the MP4 again **after** media checks to detect changes.
5. Hashes exact canonical JSON for the P6 plan and P7 QA report; writes \`owner-review-UNSIGNED-synthetic.json\` using exclusive-create, no-overwrite \`O_NOFOLLOW\` and private file mode, only inside the same ephemeral runner. Includes raw SHA digests **within that runner-only request**, not in public repo, logs or artifacts.
6. Every checklist field defaults **false**: exact playback, voice/quotes, original value, authentic creator grant, music/publisher/guest rights, live revocation status, final caption/audio/crop, real owner key enrollment. Commercial rights SHA is \`null\`, signature \`null\`, reviewer identity false, approval false, scheduling timestamp \`null\`, all upload/publish authorizations false.
7. Output CLI log contains only safe booleans and channel ID—**no MP4, digest, file path or legal-document details**. New tests reject forged approval/signatures, rights evidence, creator source content, modified metadata hash, wrong channel, unsafe files/symlinks, oversize, and modified review fields.
8. The same read-only \`.github/workflows/branch3-clivox-v2-p5-synthetic-candidates-qa.yml\` now runs the end-to-end P5 → P6 → P7 → P8 integration. It generates all media from FFmpeg color/sine sources and discards both the MP4 and unsigned review packet when the runner terminates; **no upload-artifact** step.

## Review must remain unsigned

The P8 packet is a request describing **what a human and independent legal reviewer would still need to check**, not evidence they did. A SHA-256 digest identifies bytes but **is not a signature**, and an AI-written consent statement is not legal permission. A successful synthetic review gate cannot be promoted into an actual owner-signed release, nor reinterpreted as P9 upload approval.

Even a cryptographically valid Ed25519 signature with a newly generated test key would prove only test-key math; no real owner signer is currently independently enrolled. For this integration **no key is generated**, and the existing production_release() method stays permanently quarantined until an independently designed and approved future production process is deployed. The public repository must never store private signing keys, actual source footage, contracts, creator contacts or live OAuth credentials.

## Real-world acceptance still blocked

P2 real selected prospect and identity confirmation; P3 independently authenticated, signed **commercial YouTube clipping** rights (including music/guest/game publisher clearances), territory/expiry and revocation feed; P4 secure private media vault plus creator-delivered licensed footage; P5 valid licensed-source model analysis/human ground truth; P6 genuine transformative, accurate human-reviewed story; P7 finished 1080×1920 licensed edit with independent QA; and P8 actual owner exact-final playback, current verified rights/revocations, independently enrolled owner public key, real detached signature over exact media/metadata/licensing/schedule. Only after those may P9 separately seek protected CLIVOX-only OAuth and private-first publication approval.

**CLIVOX V2 real milestone progress stays P0/P1 = 2/12 = 17%.** Synthetic P8 QA does not count as real owner approval. Other FlowMinute Branches 1 and 2 untouched.

## Testing

- \`python -B -m scripts.branch3_v2_p8_synthetic_unsigned_review --mode closed\`
- \`python -B -m unittest -v scripts.test_branch3_v2_p8_synthetic_unsigned_review\`
- GitHub Actions ephemeral job, after P7 renders output: \`python -B -m scripts.branch3_v2_p8_synthetic_unsigned_review --mode synthetic --scratch "$RUNNER_TEMP/clivox-p5-synthetic"\`

**Technical source-free P8 QA is now verified on PR and merged main; real P8 human/legal release remains blocked.**

## Verified integration evidence (2026-11-14)

- [PR #220](https://github.com/Tirthanand17/taskless-lab/pull/220) passed **4/4** PR checks and was merged at implementation SHA `d2e50c5133b944a08ba30941b365572c1555abf5`.
- [PR P5→P8 source-free exact-video review QA #43591295340](https://github.com/Tirthanand17/taskless-lab/actions/runs/43591295340) **success**, including actual generated P7 MP4 reinspection and unsigned checklist.
- [Merged-main P5→P8 exact-media unsigned-review QA #43591405263](https://github.com/Tirthanand17/taskless-lab/actions/runs/43591405263) **success**, independently repeating the full runner-only pipeline.
- [Merged-main P4 media integrity regression #43591405303](https://github.com/Tirthanand17/taskless-lab/actions/runs/43591405303) and [main Content Quality Gate #43591405236](https://github.com/Tirthanand17/taskless-lab/actions/runs/43591405236) **success**.
- Results assert zero actual rights grants, zero owner signature, zero independently enrolled owner key, zero real creator footage, zero release permissions and no video or review packet uploaded as an artifact. This engineering proof does **not** complete real P8 or advance V2 above **2/12 = 17%**.
