# Clivox integrated source-free production rehearsal

**Status:** A4→A5→A6→A8 tested handoff using real generated MP4, real FFprobe metadata and SRT hashes; **not** a creator-licensed A9 production pilot, authorized video, genuine narration or YouTube upload.

## Why this is the next valuable milestone

A4, A5, A6 and A8 previously passed their own unit checks separately, but isolated passing checks are not evidence that outputs are compatible. The integrated workflow now creates **one actual 40-second original-only demo** from the existing Clivox storyboard on an ephemeral GitHub runner, probes the rendered MP4, checks captions and media hashes, ties the renderer manifest to the exact A4 creative blueprint, and verifies that release and scheduling remain blocked.

## End-to-end execution

1. **A4:** validate the source-free 40-second original Clivox storyboard; return its canonical SHA-256 content digest. The third-party clip is represented by a visibly locked **14-second empty placeholder**. No invented transcript.
2. **A5 render:** generate five original scene cards, procedural low-volume tones (**NOT** voiceover), an H.264/AAC vertical demo MP4 and a proposed on-screen SRT (not a real speech transcript). Mode preview: **540×960 24fps**; manual full: **1080×1920 30fps**.
3. **A5 QA:** verify FFprobe video/audio tracks, FPS, 40-second duration, safe caption cue format, MP4 SHA-256 and SRT SHA-256.
4. **Cross-stage provenance:** independently read the created bytes and ensure the A5 manifest matches exactly the A4 blueprint digest, concept ID, media file bytes/hash, caption hash and recorded technical QA report. Any tamper/mismatch fails.
5. **A6 quarantine:** validate that no authentic creator grant, human approval, real owner key/signature, or released media exists. Real production release remains prohibited.
6. **A8 private-first rehearsal:** verify the fixed synthetic UTC scheduling *plan* stays unapproved, has no durable remote upload ledger and made **zero YouTube API writes**.
7. Produce a limited-retention **original-only demo video and public-safe evidence JSON** in GitHub Actions artifacts (seven-day retention). Nothing is uploaded to Clivox; no licensed or private third-party bytes are stored in the public repository or its artifacts.

## Files

- `scripts/branch3_integrated_rehearsal.py`: real file-based integration checker; accepts only the expected original-only demo layout **outside** the public Git repository.
- `scripts/test_branch3_integrated_rehearsal.py`: adversarial tests for altered MP4/SRT hashes, switched storyboard, forged technical QA, wrong files, missing rights, false signed release, fake scheduling and non-ephemeral output directories.
- `.github/workflows/branch3-clivox-integration-rehearsal.yml`: automated PR render and QA, plus manual `workflow_dispatch` with preview/full selection; always GitHub-hosted, read-only, and no tokens/YouTube calls.

## How to review the demo

Open GitHub Actions → **Branch 3 Clivox Integrated Original-Only Rehearsal (NO UPLOAD)** → successful run → **Artifacts** → download the `clivox-original-only-integrated-rehearsal-*` archive. The files include the synthetic video, editorial SRT (not an audio transcript), A5 manifest, technical QA evidence and integrated quarantine report.

Quality disclaimer: This is a legitimate engineering/render pipeline smoke test, but the prototype still uses demo-only typography, an empty source slot and synthetic tones. It is **not** fit for Clivox release or for claiming a creator clipping license. Neither its successful video codec test nor length proves engagement or monetization success.

## Real first licensed pilot remains blocked

- Obtain independently verifiable creator-issued **commercial** YouTube clipping permission and clear underlying music, guests, game publisher and any marketplace rights.
- Configure an owner-approved private media vault and human-verifiable grant receipt; **never put rights-controlled footage in this public Actions artifact**.
- Verify exact source transcript/timestamps and add genuinely original narration/story and licensed audiovisual assets.
- Complete human editorial review and sign exact released MP4, metadata, rights evidence and channel/schedule with an enrolled owner key.
- Only after Clivox-specific upload OAuth, real durable upload ledger and owner-approved protected release workflow exist may private-first uploads be considered.

**Branches 1 and 2 remain paused and untouched. No video from this workflow may be uploaded automatically.**
