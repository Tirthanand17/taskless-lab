# FlowMinute Lab — full Hindi/English narration intake and zero-cost sourcing research

**18 October 2026 | DRAFT, OFFLINE and NOT release-authorized.**

## User's required result

- Hindi-speaking viewers: separately scripted **Hindi/Hinglish 42-second Short**, original native-language title, description, Hindi subtitle track and distinct natural narrator A.
- English-speaking viewers: separately scripted **English 42-second Short**, English metadata and subtitles and audibly different natural narrator B.
- Current original **432-second Hindi/Hinglish long tutorial**: native Hindi script/captions with distinct narrator C in the current design.
- Distribution is **language-intent**, not geo-exclusive or algorithmically guaranteed; do not invent actual viewer-language reach.

## Implemented full-recording technical intake

`autopilot/phase3_complete_narration_intake.py` accepts an explicit set of **three externally supplied full-length PCM WAV recordings** and locally held claimant rights records. It binds each WAV against the exact language-separated episode, planned narrator ID, duration (42 / 42 / 432 seconds, ±1.5 seconds), SHA256 audio file digest and declared origin/license record. It uses existing `inspect_external_voice_wav` to reject malformed headers, inconsistent sample rate, raw PCM silence/implausible audio energy, invalid frame count, oversized audio and mismatched duration. A **70 MiB max WAV input** still applies via the existing inspector: full 432-second **24kHz/16-bit mono** is roughly 20.7 MB, within the technical cap; 48kHz stereo PCM can be larger than the cap. These are input-format limits, not inferred production needs.

The local rights document must be present, bounded to 200,000 bytes and match the claimant-supplied hash. The owned-recording path requires declared owner/speaker consent and a claimed commercial/adaptation contract. Offline TTS claims require a pinned model-byte digest plus a declared Apache-2.0 license but are **not authenticated** merely by the declarations. Full set must have distinct narrator IDs and distinct WAV hashes. The auditor reports only metadata/hashes: **no WAV, speech, raw rights documents or model weights printed or uploaded**.

**Security truth:** A sine wave or differently encoded duplicate speaker can pass PCM-energy/unique-byte tests. Language labels cannot prove which language is spoken; claimed rights docs can be fabricated; a WAV cannot demonstrate naturalness, consent or legal commercial rights. Therefore `three_licensed_human_sounding_voices_verified=false`, `two_distinct_short_narrators_audibly_verified=false`, `human_language_or_legal_review_verified=false`, `real_audio_caption_alignment_verified=false`, `publishing_authorized=false` are permanent outputs. The module cannot connect a TTS provider, download model weights, synthesize audio, mux/publish a video, or turn on automatic runs.

`autopilot/test_phase3_complete_narration_intake.py` uses explicitly simulated rights docs and mocked WAV receipts for orchestration; one genuine **1-second synthetic tone WAV** is rejected as an invalid full 42s narration. Regression tests cover wrong language/voice, missing files, identical WAVs, changed audio/licensing docs, noncommercial clauses, unpinned model claims and fake approval flags. **No real voice is generated or licensed by these tests.**

## Public research only — zero-cost voice choices, NOT approved to download

- [Original Kokoro project](https://github.com/hexgrad/kokoro) provides sample configurations including language code `h` for Hindi and `a`/`b` for American/British English.
- [Original Kokoro-82M model repository](https://huggingface.co/hexgrad/Kokoro-82M) identifies **Apache-2.0** model distribution, but actual voice-pack, runtime dependency and downstream commercial permissions must be inspected individually.
- [Original Hindi voice notes](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) list `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`; model publishers describe approximately **six hours total Hindi training audio**, with Hindi overall quality graded C in the model notes. That does **not** satisfy the user's required human-like natural Hindi by default.
- The original model repository currently exposes a `.pth` PyTorch weights file. The FlowMinute offline voice pilot gate intentionally rejects unsafe untrusted pickle/`.pth` deserialization and requires a pinned safe serialization format. **Do not bypass the gate or download/load the model to test it until explicitly approved and security-reviewed.**
- [YouTube's altered/synthetic media disclosure guidance](https://support.google.com/youtube/answer/14328491): creators must disclose realistic, meaningfully AI-generated/altered media under the published criteria. Whether a particular finished FlowMinute video needs disclosure requires reviewing the **actual finished assets** rather than blanket assumptions.

## Actual remaining acceptance procedure

1. Obtain separately owner-approved, legally reusable natural English and Hindi narration assets via owned recordings or an approved pinned offline TTS provider/model.
2. Run the full-take PCM/document intake on **actual** recordings, recording language/narrator/rights claims as *unverified*.
3. Independent listening in each language for authentic pronunciation, pacing, no clipped words, and audible difference between Hindi Short and English Short; obtain genuine model/voice licenses, consent and commercial usage evidence.
4. Use a separate authenticated/human-checked speech-to-text or forced-alignment step to update the script-estimated SRT to **actual spoken timing**, then inspect the muxed full MP4 with caption burn-in or selectable captions.
5. Independently review factual sources, 3D/media rights and publication policy. Only after these and secure owner-approved release accounts/storage may publishing gates be considered.

**Hard limits:** monthly cloud infrastructure ₹0; public standard GitHub Actions runners, no laptop/Nirala; NO new service connection, model download, paid TTS tier, OAuth scope, Cloudflare production write, persistent video artifact, or YouTube upload/schedule/publication. Original PR #5 and independent publishing PR #4 remain DRAFT and unmerged. **21 existing production acceptance subphases remain unfinished**.
