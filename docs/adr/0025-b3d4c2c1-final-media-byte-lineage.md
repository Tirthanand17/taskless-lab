# ADR-0025 — B3d4c2c1: final MP4, voice, captions, visuals and thumbnail byte lineage (UNAPPROVED)

**Date:** 2026-11-04 Asia/Kolkata. **Track:** Branch 2; GitHub-only development. **Status:** physical file-hash and caption-integrity preflight, **not a final release approval**.

## Research and risk

B3d4c1's existing actual Kokoro+FFmpeg demonstration renders three small CSV worked examples with animated progress, original frames, voice, burned SRT captions and thumbnails. The independent AV check confirms real codec/decode quality and per-scene caption rendering, but there has not been one evidence packet binding the **exact MP4, SRT, original WAV, thumbnail and every scene PNG** to the exact owner-signed script, computed demonstration and their full byte lengths. A file might change between producer QA and later independent review.

Primary sources:
- [YouTube monetization policies](https://support.google.com/youtube/answer/1311392?hl=en): material original variation matters. Merely changing topics/text between interchangeable templates or generating an AI script does not demonstrate originality; three different SHAs do not prove the quality of 21 videos.
- [YouTube GenAI disclosure](https://support.google.com/youtube/answer/14328491?hl=en): realistic generated/altered depictions have separate disclosure requirements and nuances; AI assistance alone is not a blanket disclosure answer. A real owner must review the actual final media.
- [YouTube videos API](https://developers.google.com/youtube/data/reference/rest/v3/videos): video status has containsSyntheticMedia and tightly constrained privacyStatus/publishAt. This PR does not call the API or set privacy/publishAt.
- [FFmpeg ffprobe](https://ffmpeg.org/ffprobe.html), [FFmpeg](https://ffmpeg.org/ffmpeg.html): independently decoding encoded media is essential; an MP4 box header or SHA is not a full AV quality test.
- [GitHub-hosted runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners): job-local files are ephemeral and do not provide lasting private reviewed-media storage.

## Decision

1. Add autopilot/final_media_evidence_gate.py, which independently rebuilds the original B3d4a source-bound screenplay plan from a detached Ed25519 script seal, externally supplied manifest anchor, trusted script custodian registry, original source observations, exact release slot and script. All CI signer keys are synthetic, not enrolled humans. Reject changed title, narration, scene, source response or unsigned slot.
2. Re-run the explicit allowlisted B3d4c1 computation algorithm and require exact resulting original-visual evidence tied to signed narration. Never execute model-authored arbitrary code.
3. Require exactly the physical local test MP4, original voice WAV, SRT, unapproved 1280×720 PNG thumbnail, all declared frame PNGs, FFmpeg concat instructions and small progress overlay PNG in an episode folder; reject extra files, wrong episode, missing files, symlinks, oversized assets, wrong PNG dimensions or invalid file signatures. Stream SHA256 of **all complete file bytes**, then compare MP4 SHA + bytes and thumbnail SHA against the independent producer report. Bind each other file SHA and length to an unapproved inventory digest.
4. Strictly parse SRT cue indices, timings and caption text; compare every spoken sentence chunk to the exact signed source narration in sequence. This file-level check cannot guarantee burned subtitle readability or true word-level forced alignment. The separately hosted independent FFmpeg decode and visual change probe is required for actual output.
5. Extend autopilot/executed_demo_cloud_smoke.py to rebuild the full byte inventory for each of the three genuinely encoded Kokoro MP4s and thumbnails while the files exist in the GitHub-hosted TemporaryDirectory, then revalidate and remove all artifacts when finished. Check that full MP4/thumb/script/demo hashes differ across 2 Shorts + 1 long on a common IST date. The three samples still share the same invented CSV data source and broadly similar template, so **do not** equate different hashes with substantive creative originality.
6. Add autopilot/test_final_media_evidence_gate.py, a fast unit/negative-test suite with intentionally **not playable** mock media headers for validation of hash mismatch, SRT tampering, replay, forged human/rights status, missing/extra/symlink files and cross-slot duplicates. Real files are tested only in the independently hosted Kokoro/FFmpeg B3d4c1 smoke, not in these mock-byte tests.
7. Add a dedicated read-only GitHub-hosted contract workflow and trigger the already existing B3d4c1 real media workflow through the integration change. Both must pass alongside repository-wide QA before merge.

## Deliberate missing approvals

Every final media inventory always reports: full human watch/listen false; independently registered real review identities false; source claim-level factual review false; actual final title/thumbnail/caption/visual semantic review false; material originality false; music/SFX/voice and image copyrights/licensing false; AI-synthetic-content disclosure decision false; private immutable media ledger false; owner copyright permission false; real generative-model script false; YouTube upload/scheduling/release authorization false.

Cryptographic hashes are not judgments of content originality, quality, legal rights or factual truth. A technical FFmpeg test and a disposable Ed25519 signature do not establish a human's independent approval. The three test demonstrations still use an invented four-row CSV, not a new trustworthy independent external factual source. All media and voice artifacts are deleted after their GitHub test; nothing is published.

## Next

**B3d4c2c2:** require separately authenticated real human source/claim, creative/originality, rights and full final playback reviewer receipts bound to exact MP4, SRT, voice, frames, thumbnail, title, description and external claim-source evidence. Re-verify all trust roots and signed receipts from private independent storage. Never let a model or test fixture pretend to be a human reviewer. Disallow vacuously empty claims on actual fact-bearing statements.

**B3d4c2c3:** with explicit owner approval of actual provider, data-use terms, cloud account, billed-cost controls, private IAM/vault and durable ledger, generate three genuinely distinct, thoroughly researched scripts and relevant original animations/illustrations, license-cleared music/voice/SFX, timed captions, fully observed final playback, fact-reviewed metadata and AI disclosure. Do not reuse synthetic CSV visuals for unrelated new topics.

**B4:** separately owner-authorized private YouTube OAuth, one fenced writer, remote private video insert, processing/SRT/thumbnail remote readback and verified IST schedule. **B5:** 21 genuinely original approved releases in seven laptop-off days at 11:00 / 16:00 / 20:30 IST. Branch 1 manual-assisted uploads/scheduling stay separate.
