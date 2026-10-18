# Phase 3R3 — Full-duration disposable audiovisual mux adapter, **NOT deployed**

**18 October 2026 | Public software research PR #5 remains DRAFT/UNMERGED.**

## Added source components

- \`autopilot/phase3_three_video_handoff.py\`: exact-source multilingual all-media manifest preflight. Reopens and validates the original full-HD silent movie, complete full-take declared WAV and source-locked unverified SRT for all three episodes.
- \`autopilot/phase3_full_ephemeral_audio_batch.py\`: an **opt-in explicit function call** that invokes already-installed FFmpeg *only after* the three-episode input handoff passes, creates 42s English/Hindi and 432s Hindi long H.264 + AAC technical MP4s *only inside an automatic-removal temporary directory*, ffprobes 24fps native 1080p geometry, checks AAC 48 kHz and exact frame counts, decodes the complete muxes, returns compact SHA/metadata QA receipts and **removes every MP4 before returning even if an exception occurs**.
- It rejects a technical WAV with more than 0.25s discrepancy from original visual runtime to avoid arbitrary truncation or silence padding; complete recording intake still permits 1.5s technical tolerance **before** mux.
- It **does not burn in or attach candidate subtitle tracks**, because neither manually edited nor machine-generated SRT timing currently proves actually spoken word alignment. It does not persist any useful finished video, upload, publish or leave media on cloud storage.

## Regression scope

\`test_phase3_three_video_handoff.py\` and \`test_phase3_full_ephemeral_audio_batch.py\` cover exactly three original episodes, Hindi and English lanes, wrong video episode/format, SHA mismatch, reused input/output paths, symlinks, forged authorization flags, copy/trim padding hazards, normal batch cleanup and partial failure cleanup. **All batch mux execution tests use fake media/path inputs and mocks of the expensive subprocesses; these are orchestration/cleanup tests, not actual three full-length narrated media proofs.** Separate existing tests actually encode, decode and probe small synthetic H264/AAC clips.

## Production admission remains blocked

No new human or provider licensed recording, real speech SRT/ASR, independent native Hindi-English listening, rights verification, human visual/fact review, durable content storage, owner-held YouTube OAuth or publishing has been obtained. The system cannot legitimately mark its current silent clips as finished releases.

Commercial reuse, human-sounding delivery and copyright clearances require **independently inspected real recordings** and authentic legal sources. Future production full batch verification must be demonstrated with actual rights-cleared full WAV input and actual complete authored videos; mocked CI does not substitute.

**Safety:** ₹0/month recurring infrastructure; existing public standard GitHub Actions CI only; NO local laptop/Nirala access, no newly connected voice provider/model/voice clone, no external charges, secrets, D1 mutation, Google/YouTube OAuth changes, video upload, schedule or publication.

**Remaining count unchanged:** 21 separate production acceptance subphases remain open because this is another software-only subgate of Phase 3R3/3R4.
