# CLIVOX A6 — original-video editorial review attestation (unsigned by default)

**Engineering milestone:** 2026-11-14. This is the review/approval bridge between the real-file A6 owner handoff and any future, independent production release signing. **No owner approval, signer key enrollment, release or YouTube upload has occurred.**

## Exactly what the new code does

[Original arcade reviewer render workflow](../../.github/workflows/branch3-clivox-original-arcade-pilots.yml) already renders two 36-second vertical Shorts and a 108-second landscape episode with original scripted graphics, eSpeak NG synthetic narration and draft SRT captions. Each video has a real-byte SHA-256 owner-handoff JSON. The new **scripts/branch3_a6_original_review_signature.py** independently reopens and revalidates the exact MP4, WAV, SRT, source catalog, metadata and ffprobe QA, then adds an **owner-editorial-review-UNSIGNED.json** to each 7-day GitHub Actions artifact.

Each unsigned worksheet includes the hashes of the exact handoff, video, audio, subtitle and metadata, plus five explicit review fields. **Every review field defaults to false** and the review timestamp is empty. The workflow never creates a private key, supplies a public-key fingerprint, forges a review attestation, uploads to YouTube or marks the video as approved.

The same module provides an **offline Ed25519 cryptographic verifier** for a detached signature on a domain-separated, canonical signed review claim. Tests generate ephemeral **test-only** Ed25519 keys to exercise the verifier, then discard them. Production keys are not stored in this project, in workflow output, or in GitHub Actions test fixtures.

## Owner's real-world human editorial requirements

Before anyone should sign or change a review worksheet to true, a human owner/editor must actually:

1. Watch the **entire exact MP4 file** whose digest appears in the worksheet (including first-frame hook, safe text bounds, story coherence, ending, and absence of repeated spinning circles).
2. Listen to the entire soundtrack and confirm voice, background tone, effects, intelligibility, commercial acceptability and sound levels. eSpeak NG is only a draft synthesizer; use independently approved final narration if needed.
3. Compare **all captions to the final audible speech**. The current SRT is time-estimated by scripted beats, **not forced-aligned**. An inaccurate draft cannot pass genuine editorial review.
4. Verify commercial rights for all original graphics, audio, production software/tools, voice and branding, and inspect the fictional-versus-actual-gameplay claims. This original-first pack uses no borrowed game footage, but that does not prove every downstream asset right.
5. Review exact title, description, fictional-program disclosure, intended initial private visibility, accessibility and destination channel identity.

If any asset changes (voice/WAV, graphics/video, subtitle timing, title/description), regenerate the MP4 and fresh A6 packet, **discard old worksheet/signature**, and repeat the actual human review. Never manually copy a positive checklist to an unreviewed new video.

## Signature contract

The optional **signed review claim** must keep the exact file/video/audio/caption/metadata/episode/channel binding of its freshly rebuilt unsigned template, mark all five checklist fields true, and include a strict UTC review timestamp. The signature is an Ed25519 signature over `CLIVOX-A6-ORIGINAL-EDITORIAL-REVIEW-V1\n` plus canonical JSON of that exact claim.

To verify a signed claim, the code requires both a public Ed25519 key and its SHA-256 fingerprint. **Those are caller-supplied inputs**. A matching caller-supplied fingerprint plus a valid signature proves only cryptographic consistency. It does **not** prove the key is owned by the CLIVOX channel owner, privately enrolled through a distinct trust path, non-revoked, that anyone actually watched the clip, or that its assets are legally cleared.

Any invalid signature, forged owner approval, changed digest, incorrect channel, missing positive check, false timestamp, unexpected field, wrong public key or altered signed data fails closed. A mathematically valid signed editorial claim still returns **all YouTube upload, scheduling and publishing permissions false**.

A real production release must separately satisfy an independently enrolled owner signing identity, revocation checkpoint, a reviewed **A6 exact release payload** (distinct from editorial attestation), rights evidence, production durable upload reservation and Clivox-only Google OAuth. This PR does **not** implement or activate those external trust decisions.

## How to review new artifacts

After a fresh render on the [GitHub workflow](../../.github/workflows/branch3-clivox-original-arcade-pilots.yml) using `selection=all` and `render_mode=full`, download the review artifact within seven days. Each of the three original episodes will now contain:

- `original-review-preview.mp4` and the exact metadata/technical QA files
- `original-tts-and-procedural-ambience.wav`, `narration-timing-draft.srt`, and original scene cards
- `owner-handoff-quarantined.json` — actual-file hash binding
- `owner-editorial-review-UNSIGNED.json` — **five owner-review flags all false, no signature**

The filename `owner-editorial-review-UNSIGNED.json` is deliberate: it is only a checklist invitation, never permission to post. No owner private key should be added to GitHub, PR comments, the artifact or chat.

**Current status:** 0 actual approved final video signatures, 0 authenticated production Google upload tokens, 0 YouTube uploads, 0 authenticated third-party grants, A9 0%; Branches 1 and 2 paused.
