# FlowMinute Lab — source-locked provisional subtitle handoff after strict signed review

19 October 2026 | Public draft PR #5 | No approved subtitles or live voice

## Previously missing

The two-role Ed25519 transcript review, actual signed SHA-linked acoustic sidecar bytes, persisted command nonce and whole-duration cue-activity checks existed, but there was NO offline handoff that could generate an event-versioned subtitle without accidentally accepting outdated or unsigned content.

## Implementation

cloud_provisional_signed_srt.py adds stage_provisional_srt, which:

1. Checks the original video/audio technical observations and exact candidate word transcript against the unmodified source-script English/Hindi lesson and SRT SHA.
2. Requires SHA-aligned and safely shaped prior full-duration AAC cue activity with no sparse cue blockers; this is sound/energy detection only, NOT a genuine voice or language approval.
3. Converts submitted word timestamps back into SRT cue windows grouped by the original, exact authored word sequence and UTF-8 text. It enforces ordered non-overlap, duration and on-screen line-length constraints.
4. Takes SQLite BEGIN IMMEDIATE, verifies the entire existing signed review hash chain, refuses any event SHA not matching the current head, matches the same candidate transcript SHA/source MP4 SHA/source SRT SHA, requires exactly two committed signed evidence sidecar hashes and exactly one committed signed-command nonce for that same event.
5. Optionally exports exactly one editor-only event-versioned SRT to a caller-selected existing, absolute, non-symlink directory. The file name explicitly identifies the SRT as unverified; POSIX mode is 0600 and an O_EXCL/O_NOFOLLOW file creation never overwrites a prior revision. Source words are not stored in GitHub, output logs, a database or cloud objects by this component. A no-export invocation does not write any file.
6. Returns provenance metadata, hash and immutable FALSE flags for real speech, verified timing, reviewer identity, actual commercial rights, audiovisual mux clearance, upload and YouTube publishing.

This is an OFFLINE staging edit artifact and deliberately has NO channel credentials, producer/editor worker, automatic rendering/export route, source WAV collector or API calls. The word timings still come from an UNTRUSTED claimed transcript. If a fabricated transcript reproduces the source with synthetic timing, it may make a technically shaped SRT but CANNOT obtain a production-ready release claim. This component does not independently authenticate signers or ever claim that native Hindi/English speakers audibly said those words.

## Synthetic regression tests

test_cloud_provisional_signed_srt.py uses temporary local files, fabricated reviewer keys and synthetic candidate timings. It covers strict current nonce-bound review admission, actual 0600 exclusive export and UTF-8 Devanagari round-trip; no clobbering existing SRT; denied legacy detached-only or sidecar-only reviews; forged candidate/event/media/timing binding; missing/false AAC cue evidence; symlink/relative/missing destination refusal; tampered journal nonce preventing export; and no-export read-only behavior.

## Production requirements remain

Genuine licensed natural voice input and real human/ASR listening, independently authenticated reviewers, corrected word-level timings, rights, actual full-HD source/media production and an externally trusted cloud service are NOT accomplished by this artifact. Phase 4 durable cloud release-state migration, verified free sustainable voice/compute/storage capacity, persistent Google OAuth, read-only official analytics and separately owner-approved private upload/readback remain blocked.

All 21 outstanding production acceptance subphases across six unfinished phases remain open. Public PR #4/#5 and private PR #5 remain DRAFT/unmerged. No Nirala/laptop, paid capacity, service registration, account/OAuth change, real video/voice acquisition, YouTube publishing or scheduling. Recurring infrastructure budget ₹0.


## Additional checkpoint — secure editor artifact revalidation (19 Oct 2026)

The initial export is no longer the only protection against an outdated or changed subtitle file. The new cloud_provisional_srt_readback.py exposes verify_current_provisional_srt, a separate **read-only check immediately before any later editorial consumption**. It re-runs the original source and sound-shape checks, recomputes the exact expected subtitle SHA, opens the existing SRT with a pinned directory descriptor and final-component no-symlink-follow flag, reads and hashes actual disk bytes under a size cap, enforces owner-only 0600 file permissions, and re-checks the full journal integrity and current accepted head inside a fresh SQLite transaction. An overwritten SRT, missing file, replaced symlink, tampered review nonce, wrong event, or changed file metadata is denied rather than treated as a reusable approval. Returned fields are read-only metadata with all actual-speech, license and YouTube permissions FALSE.

The original export is additionally hardened: exclusive creation uses an open directory descriptor (relative, no-follow O_EXCL), requires the final destination to be owned by the process with no group/other write access, verifies final directory/file inode stability, and removes its own partially written output after an fsync/write failure. This contract assumes a trusted Linux same-UID process and private directory hierarchy; it is NOT a sandbox against a fully compromised service user or an adversary controlling parent directories. The code does not install/upload/play any audio.

Seven added synthetic local regression tests in test_cloud_provisional_signed_srt.py check valid re-opened bytes, changed SRT content, a symlink swap, world-readable file rejection, world-writable destination denial, missing/replaced journal evidence, and an injected fsync failure with no partial file retained. No tests use live channel content. Production acceptance remains blocked until real trusted and rights-cleared voices and reviewers, actual audio synchronization, independent media capacity and cloud release state are verified. This is a security/quality subfix, **not** closure of a production acceptance subphase.
