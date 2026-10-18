# FlowMinute Lab Phase 3R1 — offline three-voice pilot admission

**Date: 2026-10-18 | DRAFT ONLY | No TTS installed, no model weights downloaded, no actual human speech recorded, no video published.**

## New code

- `autopilot/phase3_voice_pilot_admission.py` enforces one pilot WAV candidate per existing authored episode: Hindi Short (`csv_tutorial_short_hi`), English Short (`csv_tutorial_short_en`), Hindi/Hinglish long (`csv_tutorial_long_hi`).
- Each candidate binds a **local existing WAV** to the exact first utterance's SHA-256 from the actual authored screenplay, fixed language, existing planned narrator ID and expected short pilot duration (0.5–8 seconds), plus a supplied local rights-document hash.
- Runs the actual existing PCM16 WAV technical inspector. Rejects missing/tampered/silent audio, input symlinks, duplicate audio hashes, changed first-utterance text, duplicate episodes, invalid narrator/lang, mismatched rights-document hash, non-commercial/unknown license declarations and unpinned source.
- Accepts only two claimed audio origins: `owned_recording` with a declared consent/rights contract; or a `offline_tts` limited to a `hexgrad/Kokoro-82M` label, pinned 40-hex revision, weights+voice-artifact SHA-256 declarations, Apache-2.0 declared license and **safetensors-only** artifact format. **The strings are caller-supplied; they are NOT verification that Kokoro assets exist, match those hashes, or are legal.** Actual model assets are never read by this module.
- Explicitly rejects PyTorch `.pth` / pickle model loading; no exception that silently imports an unsafe serialized model. Upstream Kokoro v1.0 currently offers a `kokoro-v1_0.pth` in its repository; the pilot cannot run that raw model format without a separately audited safe inference/conversion path, approved source download and independent rights review.
- No third-party provider, URL, model download/install, TTS inference, audio generation, GitHub artifact upload, account connection, cloud data store, user desktop, YouTube or media publisher integration exists in this step.

## Evidence from official upstream model cards (researched, not installed)

- Main model card: https://huggingface.co/hexgrad/Kokoro-82M — published weights are tagged **Apache-2.0**. This does not establish that every associated pretrained voice file, training-data-derived asset or generated output has passed a separate independent legal review.
- Upstream official voice notes: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md — supports Hindi female/male voices (`hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`). Upstream currently grades each listed Hindi voice around **C**; it explicitly warns that non-English front ends and shorter utterances may be weaker. **We have not heard or benchmarked a sample.** Hindi naturalness is uncertain.
- Upstream model repo contains a PyTorch `.pth` weight artifact; that format can invoke pickle-based deserialization with unsafe loading patterns. Source revision/hash/voice provenance must be pinned and the loader audited; this step does NOT download or deserialize weights.
- Hindi and English narration for commercial YouTube additionally require independent voice-asset usage terms, permission/consent when using a real person's voice, correct pronunciation, audience testing, word-to-speech subtitle alignment, CPU runner costs/capacity and safe artifact retention. The model's high-level license label is **not** a substitute.

## Test scope

- New `autopilot/test_phase3_voice_pilot_admission.py` uses **three fake sine-wave recordings** and an explicitly fabricated local license document. A synthetic packet can be structurally valid, which is why it always returns `natural_speech_authenticated=false`, `speaker_distinctness_audibly_verified=false`, `license_legality_authenticated=false`, `captions_word_aligned_to_speech=false`, `publishing_authorized=false`.
- Tests reject duplicate audio, tampered WAV rights, noncommercial licenses, missing consent declarations, unknown provider, unsafe pickle model, unpinned revision, wrong narrator/language and invalid output assumptions. Plain metadata cannot certify actual rights.
- Standard full public GitHub quality suite already ran on commit `2dfdb8f699f8ef758a7f0b19c94b9092ad776d8a`: **462 tests + 56 subtests passed** (https://github.com/Tirthanand17/taskless-lab/actions/runs/39088574858). Separate Cloud Render and Scout checks should be observed for their exact HEAD.

## Next *actual* production milestone

Before trying a human-style voice, the user must explicitly approve the specific new external model download/service connection if one is needed, and any costs must remain **₹0/month**. Then: review a pinned real source/voice license, audit safe loader/container, benchmark disposable CPU speed and memory without Nirala, listen to real Hindi/English output, confirm two audibly distinct Short narrators, and independently verify caption-to-speech timing. **No automatic permission to publish follows from a passing pilot.**

Cloud source provenance/independent fact review, Cloudflare D1 readback, brand-channel OAuth and an authorized YouTube upload pilot remain separately blocked. **21 tracked production acceptance subphases remain incomplete.** PR #5 and PR #4 remain drafts and unmerged.
