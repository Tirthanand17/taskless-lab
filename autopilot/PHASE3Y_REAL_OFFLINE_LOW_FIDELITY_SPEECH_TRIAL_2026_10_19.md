# Phase 3Y — actual offline bilingual WAV generation; baseline REJECTED

19 October 2026 | PUBLIC GitHub DRAFT PR #5 | NO downloaded model or provider connection

## Why this is real new production evidence, not simulated transcript success

The ChatGPT isolated work environment already had the command-line eSpeak 1.48.15 engine and FFmpeg/FFprobe. Its installed voices include English en-us and Hindi hi. The team executed this existing local binary against the exact ORIGINAL first-scene English and Hindi text in content/production-packs/2026-10-20-gemini-agent-control.json. No user Nirala machine, login, TTS provider, external weights, subscription or API was accessed.

The two REAL waveform WAVs, generated in an isolated scratch folder (not GitHub):
- English: first scene "Chatbots answer questions. Agents can act. But who approves?" at eSpeak en-us speed 150, 22,050 Hz, PCM16 mono. Measured 5.396 seconds and 238022 bytes; original editorial scene slot 4.0 sec, over by **1.396 sec**.
- Hindi: first scene "AI से सामान मंगवाना है? पहले एक ज़रूरी गलती रोकिए।" at eSpeak hi speed 135, 22,050 Hz, PCM16 mono. Measured 5.686 sec and 250816 bytes; editorial scene slot 5.0 sec, over by **0.686 sec**.
- Both have nonzero waveform RMS (EN 0.0968, HI 0.144 approximately) and verifiable byte digests. These audio files are downloadable from the ChatGPT conversation as low-quality mechanical evaluations; they are deliberately NOT inserted into the public repo, private voice system, actual final video or YouTube.

Technical audio exists, so this is NOT merely hypothetical PCM mock output. However eSpeak uses formant synthesis, widely known to sound robotic. These samples are **REJECTED FOR PRODUCTION NARRATION** without ambiguity. It is a poor match for FlowMinute Lab's intentionally natural human-like tone, distinct narrator voices, expressive Hindi pronunciation and engaging content. eSpeak has no verified commercial speaker consent/rights record in this task. WAV amplitude, PCM codec and duration DO NOT establish natural speech, human narrator, distinct person, intelligibility in each locale, exact spoken word timing or licensed commercial use.

This gives one actionable issue: the current script's opening scenes were timed before actual voice. A simple available mechanical synthesizer overran English by 1.40s and Hindi by 0.69s. Genuine recorded narration durations could be different in either direction. Retiming the visuals and draft captions against the eventual real audio is necessary, and forced speech-speed compensation is not acceptable.

## Source code and reproducibility

New **autopilot/oct20_preinstalled_voice_baseline.py**:
- Reads and validates the exact October 20 original scene text and immutable script hash via the already-existing source-locked narrator packet.
- Optionally executes only an already-installed eSpeak binary through Python subprocess argument arrays + stdin; never uses shell execution or accepts user-provided command/code, never downloads new weights, never runs unapproved providers, never accesses audio recording devices.
- Refuses any existing output or unsafe path and produces a fresh WAV at an explicit caller-provided existing directory; cleans up a failed write.
- REUSES the existing full real bounded PCM inspector rather than fabricating a check. Compares its observed duration to the original editorial first-scene target.
- Returns a permanent status ACTUAL_ESPEAK_MECHANICAL_BASELINE_REJECTED_FOR_NARRATION and sets human/natural/rights/word-alignment/mux/YouTube privilege flags FALSE even after valid WAV data.
- It cannot render the entire 42/44/480-second original episodes through this code; it is strictly an audition for the two opening scenes.

New **autopilot/test_oct20_preinstalled_voice_baseline.py**:
- Original EN/HI source/digests and expected scene windows checked even without installed eSpeak.
- Refuses legacy CSV/unknown/long videos, overwriting existing files, wrong extensions/missing directories, or missing local synthesizer; no model download.
- If eSpeak is preinstalled on a particular public runner, runs a real actual WAV byte-generation/inspection test; otherwise correctly SKIPS that one environment-dependent test. Tests cannot substitute a synthetic waveform pass for natural speech approval.

## Voice selection: public research, NOT an authorized model download

- Kokoro-82M (hexgrad upstream) lists English voices and four Hindi voices hf_alpha, hf_beta, hm_omega and hm_psi, under an Apache-2.0 model tag: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Upstream explicitly labels Hindi quality around C with only about six hours of Hindi training data, so native Hindi naturalness, accent, emotion, diction, model performance and commercial voice-specific rights remain unknown. LiteRT quantized model advertises an on-device multilingual build at https://huggingface.co/litert-community/Kokoro-82M
- This research does not prove that an actual Kokoro voice is licensed/appropriately sourced for this use, nor that it can run for free in an always-on service; benchmark and human listening are necessary.
- No model file was fetched, installed, connected, deployed or executed. The user's specific approval is still required before any new model download or external service connection.
- Do not use legacy eSpeak robotic voice as the production solution merely because it is installed; do not rely on model rating alone to decide voice quality.

## Gates and project restrictions unchanged

No genuinely accepted natural narrator or three full WAV recordings exist. No word-level independent ASR or authentic rights evidence exists, no final full-HD 3D/photoreal movie with natural speech, and no real YouTube/private upload. The isolated audio samples are NOT ready to mux, publish, schedule or use commercially until separate rights and quality review.

No Nirala laptop access; no new folders on the laptop; no paid provider or app service connection; no Cloudflare D1 writer/deployment; no Google OAuth changes; no new charges, videos.insert or YouTube publishing. User's monthly infrastructure budget is still INR 0. Both repository PRs stay DRAFT/unmerged. The 21 pending production acceptance subphases across six unfinished major phases remain OPEN; previously rough software 45% and autonomous readiness 20% estimates are not increased by a deliberately rejected voice sample.
