# CLIVOX A6 — exact video owner review handoff (no signing, no YouTube)

**2026-11-13.** The original arcade trio has already rendered both preview and full-size MP4s on **GitHub Actions**. This milestone adds a **real-byte verified** owner review packet to each new review run, not a release signature or publishing authorization.

## Verified original review master runs

- [Two 36-second Shorts + one 108-second widescreen preview](https://github.com/Tirthanand17/taskless-lab/actions/runs/43380418384) — GitHub-hosted actual video/FFprobe QA passed.
- [All three full-size reviews](https://github.com/Tirthanand17/taskless-lab/actions/runs/43380650008) — 1080×1920 Shorts and 1920×1080 long episode, actual FFprobe QA passed.
- New runs of [Original Arcade Renders](../../.github/workflows/branch3-clivox-original-arcade-pilots.yml) automatically add A6 review packets once the change is merged. The historic two runs predate this A6 handoff implementation and therefore do **not** contain A6 packet JSON.

## Exact artifact integrity contract

For each episode, the A6 handoff recomputes the **real MP4 SHA-256 and byte size**, original raw narration WAV hash, timed subtitle draft SRT hash, full creative catalog hash, canonical preview metadata digest and a freshly regenerated independent FFprobe QA report. The QA file must **exactly match** the newly computed report; preexisting `actual_ffprobe_checks_passed=true` is not trusted alone.

The handoff places in the temporary GitHub runner's episode directory:

- `owner-handoff-quarantined.json` — canonical SHA-256 for a fixed-domain packet, exact video/audio/caption/catalog/metadata/QA binding, and explicit negatives for human review, commercial rights approval, genuine A6 signer, Google OAuth, scheduling and upload.
- `metadata-preview.json` — canonical video title, description, Clivox channel identity, fictional-original content disclosure and **NOT_UPLOADED** status.
- Existing `original-review-preview.mp4`, `narration-timing-draft.srt`, `review-manifest.json`, `technical-review-qa.json`, scene cards, and intermediate synthetic-original audio WAV.

The files are included only as **public-safe original-first review** GitHub Actions artifacts (seven-day retention). The repo never stores downloaded third-party footage or confidential contract/media, and the workflow has read-only GitHub permissions and no Google credentials.

## What the owner must do next

Watch and listen to the **exact MP4 file** whose digest appears in the packet (not merely a prior preview). Review spelling and mobile crop, timing/CTA, human-sounding speech, music/audio licensing, caption sync and source originality. If edits are necessary, rerender and regenerate the packet—the old digest is invalid for the new MP4. Human approval of that exact asset is a **separate decision**, not the result of this module.

Before any upload, the owner must independently enroll a trusted release signing key, authenticate any rights evidence, sign the exact A6 canonical payload (video digest, metadata digest, rights digest, release identity, private-first visibility and future UTC schedule), and configure Clivox-only production Google OAuth and a production-grade durable upload ledger. The original game-show package avoids third-party **clipping** rights but still requires human asset/tool-license approval. No owner signing key was enrolled and no release is issued by the packet.

The existing `scripts/branch3_a6_signed_release.py` remains the separate mathematical Ed25519 verifier with a deliberately disabled production release entrypoint. The new packet may be used for review/checklist preparation; **its hash alone cannot substitute for an authenticated signer or legal approval**. A9 first actual public/published pilot remains 0%.

## How to verify

- PR tests: `scripts/test_branch3_a6_original_handoff.py` checks MP4/audio/SRT tampering, metadata replacement, false approval, wrong channel, catalog/QA substitutions, symlink/missing assets and no silent packet overwrite. Its fake in-memory MP4 is never considered a real production asset.
- Real media workflow: after actual FFprobe QA, it invokes `python -B -m scripts.branch3_a6_original_handoff --mode build --selection all --directory "$RUNNER_TEMP/clivox-original"`. The script rehashes the actual generated video, WAV and SRT, and the review artifact contains the resulting packet.
- A separate no-secrets workflow `.github/workflows/branch3-clivox-a6-original-handoff-qa.yml` runs adversarial unit tests and guarantees release/publish flags false.

**No creator source downloads, Clivox Google API calls, upload attempts, schedule or public video publication are performed.** Branches 1 and 2 stay paused.
