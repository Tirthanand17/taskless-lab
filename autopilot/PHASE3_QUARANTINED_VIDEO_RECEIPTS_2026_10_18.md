# FlowMinute — quarantined SHA-256 video/source receipts (18 Oct 2026)

**Draft Phase 3R4 technical evidence; NOT authorization to retain, upload, schedule, monetize or publish.**

### Why this stage exists

The native HD cloud runners now successfully render the complete **42-second English Short**, **42-second Hindi Short**, and **432-second Hindi/Hinglish long video**, decode them and pixel-check actual scenes. But the resulting MP4s are deliberately deleted and the project has no authorized narrators, licensed music, real human factual review or verified user-owned YouTube publishing credentials. A metadata receipt must not be mistaken for a finished video or a signed human-release gate.

### Implemented

- `autopilot/phase3_quarantined_video_receipt.py` accepts only one of three fixed original authored CSV episode IDs and an existing ordinary bounded H264 MP4 in local scratch space.
- Calls actual `inspect_authored_visual_signal` with source-bound geometry, frame counts, duration and sampled pixel QA: **five real frames per 42s Short; 26 real frames across all 24 long-video beats**.
- Rejects unrendered/tampered files, missing source sections, failing visual signal, altered sample coverage and local file symlinks.
- Creates a compact metadata-only receipt including SHA-256 of **complete actual video bytes**, SHA-256 of the **specific authored screenplay section**, SHA-256 of the **whole source document**, and SHA-256 of **script-derived estimated SRT**; frame geometry, 24 fps, duration, count, byte size, visual-quality summary and sample-hash digest.
- `verify_quarantined_receipt` locally recomputes integrity hashes against the same actual media and current original source/SRT. A hash-chain check **does not authenticate the issuer or prove who/what created the data**; malicious parties can recalculate unsigned hashes. Receipt always declares `receipt_issuer_authenticated=false`, `receipt_cryptographically_signed=false`.
- Hard DENIAL fields remain false for `media_has_narration`, rights, real spoken subtitle alignment, 2 distinct Short narrators, independent factual/editorial/legal signoff, durable media storage and YouTube publishing. All recorded metadata avoid printing scripts or actual voice or audio samples.
- `autopilot/test_phase3_quarantined_video_receipt.py` includes offline regression for all three scripted episodes, changed MP4 bytes, tampered receipts, forged rights/approval flags even after rehashing, swapped IDs, unsafe symlink/missing files, rejected visual failures and incorrect sample count. Synthetic bytes and mocked pixel inspection **do not claim real media QA**.
- Existing public `.github/workflows/flowminute-cloud-render-smoke.yml` now issues quarantine receipts directly after **actual encoded pixel QA** in the English/Hindi Short job and in the full native-HD 432s Hindi long job. Performs immediate local integrity verification, logs compact receipt (no real media), then retains existing unconditional removal of all MP4s. **No workflow artifact upload or durable media storage is added**.

### Strict interpretation

A receipt is a time-local proof that *this test run saw bytes* conforming to original source and scene signals, not a signed trusted provenance chain. Since videos are deleted, a future release pipeline still needs separately authorized durable media storage, fresh hash verification, independent rights/voice/fact review, and owner-approved YouTube channel authentication. The script-derived SRT has NOT been aligned to real audio.

No new service, TTS model download, account, paid runner, user laptop/Nirala, Cloudflare D1 production mutation, OAuth scope or YouTube upload/publish. Existing ₹0/month recurring budget unchanged. PR #5 remains DRAFT/unmerged and separate release-control PR #4 DRAFT. **21 production acceptance subphases remain unfinished**.

### Validation

Code and CI are committed, but check exact final public HEAD Content Quality, Cloud Scout, and Cloud Render Smoke conclusions before claiming all three real production renders emitted receipts and passed. Full native-HD long render from previous source and 26-scene visual inspection passed previously at https://github.com/Tirthanand17/taskless-lab/actions/runs/39093926130.
