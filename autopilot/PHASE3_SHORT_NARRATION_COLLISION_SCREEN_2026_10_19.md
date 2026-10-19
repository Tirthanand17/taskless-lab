# FlowMinute Lab — cross-language Short final-AAC reuse detection

19 October 2026 | public DRAFT PR #5 | synthetic offline tests only

## Why this was necessary

The channel owner requires different natural-sounding licensed voices for two daily Shorts, and native Hindi and English audio lanes. Prior planning used distinct narrator labels, while complete WAV intake only refused identical file hashes. Such checks cannot catch a producer reusing the same final AAC soundtrack in two visually different MP4 containers or rescaling the volume. Different labels and file hashes do NOT prove different speakers.

## Implemented, strictly negative technical screen

autopilot/cloud_short_voice_collision_screen.py performs an extra READ-ONLY comparison on the two original existing, SHA256-bound 42-second final H.264/AAC Shorts:

1. Requires matching full-media intake, approved purely technical muxed-audio screen, original authored SRT, typed transcript-candidate shape and fully covered per-cue AAC observation. Falsely elevated release/speaker/rights claims are denied.
2. Refuses relative paths, symlinks, changed media bytes, wrong language, unsupported lanes or source SRT revisions.
3. Re-decodes each entire final AAC soundtrack to fixed 8-kHz mono PCM16 with bounded FFmpeg commands, no shell and no temporary files.
4. Keeps SHA256 of decoded PCM and a sparsely sampled sign-pattern fingerprint in private in-process memory only; no waveform, path or media digest is returned in the aggregate status.
5. Detects exact reused video, identical decoded soundtrack and almost identical same-timestamp sample sign patterns, including simple global volume scaling and polarity flipping.
6. Produces specific technical collision blockers. Even a no-collision result keeps independent speaker identity, actual naturalness, Hindi/English spoken language, commercial voice rights, real word/subtitle sync, upload and publishing all FALSE.

## Synthetic regression coverage

test_cloud_short_voice_collision_screen.py checks distinct fabricated PCM vs copied same-track PCM with different MP4 bytes, gain changes and polarity inversion, forged narrator labels/publishing, missing or duplicated lanes, malformed fingerprints, bad SRT/reviewer/coverage contract, stale or swapped media, truncated decoder output, in-memory-only representation and no release authority.

These are not actual narrated recordings or real MP4 evidence; FFmpeg output is mocked. The algorithm cannot reliably find re-encoded/remixed or time-shifted duplicates, and actual different tracks may use the SAME real speaker. Neither fingerprint collision absence nor planned voice labels authenticate speaker distinctness. There is no actual voice recognition, ASR, legal review, consent proof, production cloud deployment, YouTube account change or upload.

## Remaining production acceptance

Genuine rights-cleared Hindi and English recordings, independent authenticated native-listener reviews, actual spoken-word synchronization, zero-cost private media compute/storage, OAuth durability, private readback and an owner-approved publishing pilot remain open. The original 21 production acceptance subphases across six unfinished major phases are unchanged. PR #4/#5 remain draft, no laptop/Nirala usage, external provider or model install, API connection, payment or YouTube publishing.
