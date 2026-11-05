# FlowMinute Lab — source-locked narration acquisition handoff

**18 October 2026 · Phase 3 voice readiness research-only · existing Draft PR #5**

The original script plan contains exactly three separately authored episodes: a **42 s Hindi Short (narrator_hindi_a)**, a **42 s English Short (narrator_english_b)** and a **432 s Hindi long tutorial (narrator_hindi_long_c)**. Each requires a separately sourced genuine, rights-cleared PCM WAV complete narration and corrected subtitles based on **actual speech**. Two Short voices must also be audibly distinct; different WAV hashes or narrator labels are not sufficient proof.

## Deliverable

`autopilot/phase3_voice_acquisition_readiness.py` emits a stable, **source-locked, machine-readable evidence request**, without logging/publishing the actual authored script. The packet binds the exact original repository Markdown SHA-256, section digests, full spoken-script digests, original language, runtime, narrator plan, scene count and original estimated draft SRT hashes. It verifies the entire source scene timeline and caption/language metadata match existing Phase 2/3 plans. It lists audio format, size and duration prerequisites, eight evidence categories required for every episode, and the two candidate acquisition paths:

- **Owner-recorded speech:** authentic voice recording accompanied by real consent and legally reviewed commercial-use, adaptation and attribution rights; check bilingual native pronunciation/natural delivery and separately review the two Shorts' audible narrator distinctness.
- **Owner-approved offline TTS:** requires separate explicit authorization for the model download/use, pinned audited safe model loader, verified individual voice/model license/rights, commercial output use, pronunciation and quality review, with zero recurring costs and no unsafe PyTorch pickle deserialization. The existing Kokoro exploration is *not* approval to download or run it, or proof that Hindi naturalness is satisfactory.

For both options, exact full episode WAVs must be independently checked via existing `phase3_complete_narration_intake.py`, `phase3_voice_signal_screen.py` and `phase3_voice_pacing_audit.py`. Corrected, independently listened-to spoken-word/timecode SRTs then go through `phase3_caption_candidate_intake.py` and `phase3_three_video_handoff.py`. Actual asset rights and project factual/visual quality remain separate checks.

**A generated packet is not a review:** all real audio, speech/voice, legal, original language, consent, alignment, mix and release approval fields remain **FALSE** and evidence lists are explicitly `not_collected`. A caller-controlled changed packet or signature-less hash cannot impersonate an independent reviewer or authorize anything. The marker SHA is only a byte-change detector.

## Safety and cloud boundaries

This implementation **does not collect or upload recordings**, create audio, download weights, contact providers, use the user's laptop/Nirala, copy legal records into a public repo, connect YouTube/Google/Cloudflare, change D1, schedule jobs, merge a PR, or publish a Short/video. No external budget or new service is used. Project's **₹0/month recurring** infrastructure hard limit remains in force. No private GitHub Actions run was triggered. Both PRs remain **DRAFT/unmerged**. Existing **21 production acceptance subphases across six unfinished top-level phases** remain open; this packet shortens future owner-approved intake but does not constitute genuine source evidence.

The tests exercise complete episode/language/timing/digest binding, deterministic redacted packet hashing, altered script or scene timing, and negative-by-construction authority flags using the existing authored Markdown; they generate **no actual speech**.
