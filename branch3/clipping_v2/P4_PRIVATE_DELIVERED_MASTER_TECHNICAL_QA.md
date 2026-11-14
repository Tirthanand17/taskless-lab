# CLIVOX V2 P4 — Offline local-master technical inspection (not a rights or ingest service)

This integration extends the existing P4 **synthetic-only small-file preflight** with a separate technical inspection primitive for a creator-delivered *local* MP4 in a future independently approved private runtime. It does **not** connect to a private vault, contact creators, verify contracts, download YouTube footage, grant media processing rights, publish, or complete real P4.

## Implementation

- `scripts/branch3_v2_p4_private_master_technical_qa.py` exports `inspect_local_master(scratch=..., basename=..., expected_sha256=..., expected_bytes=...)` as a read-only function; it has **no active production CLI**, no HTTP clients, no video rendering, no copies, no upload, no signer.
- Private runtime requirements: absolute, canonical, owner-only (`0700`) scratch directory **outside** this public repository; strict opaque `master_*.mp4` basename; real regular file, no symlink or hardlink, `O_NOFOLLOW`, invariant inode/mtime/size across the check.
- Computes full-file SHA-256 twice (before and after probe) and requires an exact caller-specified byte count, max 3 GiB. The caller's digest is **not independently trusted evidence** or proof of source ownership.
- Uses subprocess argv with `ffprobe -protocol_whitelist file`; 45-second timeout, maximum 64 KiB JSON output. MP4, exactly one H.264/yuv420p video and one AAC audio track, 320–3840px width, 240–2160px height, 15–120fps, 10–7200s and 44.1/48kHz mono/stereo audio.
- The returned technical report omits source paths, file names, file SHA, private metadata, contacts and credentials. All licensing, rights/identity, vault ACL, revocation, source ingest/edit, owner review and YouTube upload/publish gates remain **false**. Full-media decoding is not claimed.
- `production_media_ingest()` always raises. No permission state is stored and no public artifacts are uploaded. The inspector is a reusable *technical building block*, not a production acceptance path.

## Testing and CI

- `python -B -m unittest -v scripts.test_branch3_v2_p4_private_master_technical_qa`
- Adversarial unit tests cover expected-hash mismatch, length, malformed MP4 prefix, unsafe filename, symlink/hardlink, nonprivate scratch permissions, mutation during probing, rejected codec/profile/framerate/duration/extra streams, timeout, unreadable probe and false rights/publishing promotion.
- The existing `.github/workflows/branch3-clivox-v2-p4-synthetic-handoff-qa.yml` generates **only a new 12-second lavfi MP4** in an ephemeral owner-only test directory and runs the actual ffprobe/hashing path, then discards the test file. This is NOT creator footage or an approved private-source delivery.

## Remaining real P4 acceptance requirements

1. An actual creator/rights administrator is independently authenticated; the legal scope explicitly covers this exact source's commercial YouTube Shorts editing/redistribution and underlying rights.
2. A real owner-approved, access-audited private storage location and isolated worker are provisioned; confidential contracts and media stay out of this public repo and Actions artifacts.
3. Creator directly delivers an original master through the approved private route; an **independent trusted delivery manifest** binds the source rights, original file digest, source owner, timestamps, expiry, revocations and contractual scope.
4. A private security-reviewed executor enforces positive rights verification and vault authorization **before** accepting or processing media. This source-free inspector does not implement that positive authorization path.
5. Full source decode, audio integrity, context and human editorial review precede P5. Passing this module is insufficient for any downstream action.

Until these are actually verified, **real clipping milestones stay P0/P1 = 2/12 (17%)** and no real creator licenses, footage, uploads or monetization are claimed.

See [P4 synthetic quarantine](P4_SYNTHETIC_PRIVATE_MEDIA_HANDOFF.md), [P3 licensing scope](P3_LICENSING_SCOPE_INTAKE.md), and [phased plan](PHASED_INTEGRATION_PLAN.md).
