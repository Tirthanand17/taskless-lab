# FlowMinute Lab — Phase 3R1 voice/subtitle handoff checkpoint (2026-10-18)

**New software:** `autopilot/phase3_voice_subtitle_handoff.py` and `autopilot/test_phase3_voice_subtitle_handoff.py`, on public research DRAFT PR #5, separate from cloud publishing DRAFT PR #4.

## Useful outputs, not yet finished media

1. Read the **actual** authored bilingual CSV content at `autopilot/research_briefs/2026-10-17_csv_bilingual_one_day_scripts_DRAFT.md`: four beats each in the Hindi and English 42-second Shorts, and 24 beats in the 7-minute-12-second Hindi/Hinglish long lesson.
2. Generate three **genuine standards-formatted SRT subtitle strings** from that screenplay, with numbered cues, exact end-of-video timecodes, no gaps/overlap, bounded line length and <=6-second screen intervals. The words are preserved exactly from the authored document.
3. Export `csv_tutorial_short_hi.draft_estimated.srt`, `csv_tutorial_short_en.draft_estimated.srt`, and `csv_tutorial_long_hi.draft_estimated.srt` into an **explicit, already existing directory** on a permitted runner only. Refuse symlinks and preflight all destinations before writing to avoid overwriting/partial release.
4. When an independently sourced WAV becomes available, `inspect_external_voice_wav()` technically inspects the **actual WAV bytes**: PCM16, mono/stereo, permitted sample rate, expected-duration tolerance, bounded file size, silence/low-energy rejection, SHA256, RMS and peak. It NEVER automatically labels a speaker natural/human, independently identifiable, licensed or factually approved.
5. Synthetic tone WAV regression tests are deliberately used to show **a waveform can pass audio technical checks without being real speech**. Code thus always marks `real_speech_verified=false`, `human_naturalness_verified=false`, `license_rights_verified=false`, `audio_caption_alignment_verified=false`, `publishable=false`.
6. Captions are **script-interval estimates**, NOT word-level timed forced alignment or an ASR-verified transcript. Do not burn these cues into a final public render without independently checking recorded pronunciation, pace and spoken caption correspondence.

## Testing and dependencies

- Standard library only: `wave`, `hashlib`, `re`, timing and bounded file I/O; uses existing typed authored-screenplay parser and project WorkflowError.
- Tests check exact authored text conservation, Hindi and English SRT timings, endpoint 42 seconds/432 seconds, deterministic generation, malicious time gaps, template-approval rejection, safe export, actual WAV byte processing, silent sample denial, duration mismatches, false languages/narrator labels and missing/unsafe files.
- Public GitHub Content Quality Gate has to pass on the exact latest SHA before claiming this is green. Existing Cloud Scout and Cloud Render Smoke are separate tests; neither records a voice.
- No provider accounts, real audio recordings, speech-to-text services, new subscriptions, PyPI dependencies, or external connections have been used by the new module.

## Actual upcoming production blockers

- **3R1 voice licensing:** approved owned recording or permitted offline TTS with verified commercial-use right and two *audibly distinct* narrator identities, separately reviewed for Hindi/Hinglish pronunciation.
- **3R4 subtitle sync:** listen or independently transcribe actual recorded speech; independently correct word-level timing; verify spelling, readability, safe areas, visual QA and asset rights.
- **3R3 complete media:** render and QA two complete portrait Shorts and a genuine 7-minute-12-second landscape long-form video; prove FFmpeg decode, actual audio, no black/silent sections, duration/metadata and a sustainable, secure, included-quota media store at ₹0.
- **2R1/2R2 and 4E/5:** real authenticated source capture, independent factual and copyright editorial clearance, authorized D1/YouTube OAuth/account ownership, release controller and YouTube playback verification remain blocked.

**Hard limits:** ₹0/month cloud infra, no Nirala/desktop, no new external service connection or paid provider without fresh approval, no production secrets in public CI, no unapproved YouTube upload/schedule/publish. 21 tracked remaining **production acceptance subphases** remain. The new functionality is one part of 3R1/3R4, not completion.
