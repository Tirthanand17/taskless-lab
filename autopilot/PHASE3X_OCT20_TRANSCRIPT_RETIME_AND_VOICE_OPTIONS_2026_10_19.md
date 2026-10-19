# Phase 3X — exact-source Oct20 transcript retiming intake and voice feasibility

19 Oct 2026 | PUBLIC draft PR #5 | local source audit, no voice model download

## Real implementation

autopilot/oct20_transcript_retime_intake.py connects all THREE current original October 20 episodes (42-second English Short, 44-second Hindi Short, 480-second Hindi long) to the exact checked-in estimated SRT assets and narrator script SHA-256 source.

It REUSES Unicode-preserving existing cloud_transcript_alignment_intake._normalized, instead of copying another punctuation/Hindi normalization routine. It reads the actual UTF-8 .draft_estimated.srt bytes and rejects differences from the regenerated current script-bound SRT. It handles one-/two-line SubRip cues, verifies complete original scene chronology and compares a supplied claimed word-timed transcript one token at a time.

An untrusted word-time proposal is allowed to have timing drift outside the old **estimated** SRT cues. That is not automatic failure; the evaluator reports the largest overshoot and explicitly tells an editor that a *video retime may be required*. Forcing actual human speech into fabricated script cue windows would produce unnatural pacing. Invalid time overlap, missing/inserted/changed words, wrong language, wrong script/SRT hash, old CSV episode reuse, SRT tampering and forged publishing rights are refused. All three current language lanes must be present and non-privileged for a summary.

Important: **a matching transcript is NOT evidence of genuine spoken words, ASR provenance, voice naturalness, legal rights, consent, different speakers or subtitle-to-audio alignment**. Even an asserted WAV SHA may be fabricated without authenticated source bytes. All such flags remain FALSE. The code performs no actual audio decoding, ASR recognition, model inference, cloud/provider connection, media processing or publishing.

Tests in autopilot/test_oct20_transcript_retime_intake.py exercise real source files and synthetic word timestamps for all three originals, including Unicode Devanagari, deliberate off-cue drift, stale script/SRT, punctuation/case, edits, overlaps, privacy redaction and forged authority. No original human voices were recorded or received.

## Current public research: possible ₹0 multilingual TTS experiment (NOT attempted)

An open-weight candidate for a future, separately reviewed *offline* voice-quality experiment exists:
- Original model hexgrad/Kokoro-82M model license is advertised as Apache-2.0. Its published voice catalogue lists Hindi hf_alpha, hf_beta, hm_omega and hm_psi in addition to many English voices. The upstream Hindi dataset was reportedly ~6 hours and Hindi voices are rated about C in the upstream quality list, so suitability for engaging native natural-sounding Hindi is UNKNOWN, not proven. Official voice catalogue: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- LiteRT community advertises a quantized multilingual Kokoro-82M package with self-contained Hindi/English frontends and Apache-2.0, but its size/runtime/cloud GPU/CPU performance, commercial reuse of specific voice materials and safety on the selected zero-cost platform require separate verification: https://huggingface.co/litert-community/Kokoro-82M
- Do not use arbitrary downloaded .pth or .pt checkpoints with unsafe pickle deserialization. Avoid downloading or connecting an external service without the owner's separate approval. Avoid mistaking a project-wide license label for independently confirmed voice-specific training rights, speaker consent, commercial YouTube usability or production-quality native pronunciation.
- Voice alternatives include three independently consenting human recordings under a clear commercial-use agreement; the user wants natural variation and two distinct Short narrators. Any human or synthetic voice needs actual listening, rights review and independent speech-to-caption alignment before release.

These are **research candidates only**: no new app/service account was connected, no model weights installed or fetched, no cloud GPU/paid plan used, no proof the selected model runs sustainably within INR 0, and no media audio produced. The user must authorize a future new provider connection, model download and actual account interaction as required by project policy.

## Production gate state

No actual English/Hindi 42/44/480-second narrated WAVs, no independently observed acoustic transcript, no ASR-based SRT, no rights/consent authenticated, no finished HD 3D video or Google/YouTube private upload. Only source-bound scripts/SRTs and silent visual review clips are presently available.

Real next step: obtain a rights-cleared natural narrator take or separately approved offline TTS experiment; measure intelligibility and native Hindi accent by independent listening; decode/align actual complete audio; retime scenes; then conduct final audiovisual QA and an explicitly owner-approved private YouTube pilot.

Unchanged: GitHub-first, owner Nirala laptop inaccessible without separate permission; monthly infrastructure budget INR 0; no private GitHub Actions use, paid cloud, Cloudflare live D1, YouTube OAuth modification, schedule or publication. Both PRs stay DRAFT/unmerged. Previously tracked 21 production acceptance subphases across six unfinished major phases remain OPEN. Prior ~45% software and ~20% genuine autonomous production readiness estimates remain provisional and unchanged until provider-backed acceptance.
