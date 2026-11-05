# ADR-0051 — B1q2b fix real MP4 double-caption and voice-to-hero scene drift

**2026-11-05 IST. Branch 1 real-media quality gate. No remote YouTube mutation.**

## Actual independently examined encoded evidence, not a source-code guess

B1q2 PR #55 passed all five exact-head CI checks and merged at 83c69b87c59021a827b27ff44e546cd4b853c225. Its real MAIN audio-and-video review run 42014676780 succeeded (two jobs) and retained actual three H264/AAC 1080x1920 Shorts in GitHub artifact **13407979969**, 6,691,587 bytes. I retrieved the ZIP and independently checked **all 21 media files** against manifest SHA256/byte lengths and inspected nine ACTUAL extracted MP4 frames: opening, proof and takeaway for each original Nov5 voice safety, Nov6 photo metadata and Nov7 Incognito lesson. Actual durations: 38.677s, 39.947s and 46.498s. Encoded AAC measured -18.35 / -17.90 / -18.18 LUFS, true peak -2.74 / -2.11 / -4.98 dBTP; all strict technical limits passed. Human listening and rights review remain FALSE.

**Critical visual failures discovered by looking at REAL final frames:** the big top headline unnecessarily duplicated the complete spoken caption ALSO burned in the lower native subtitle strip; and the INCOGNITO final frame sometimes showed the NEXT topic's full original sentence as the scene header while the ASS subtitle still displayed the PREVIOUS spoken line. This was caused by the FFconcat visual timeline omitting 0.13s of genuine PCM speech gap per original phrase. As many as ~10 gaps accumulate to ~1.3s of theme-to-speech drift. Green encoded-audio tests did not detect video-semantic drift.

## Surgical fixes

- Source-authorized three-topic video-mode title mapping: **three concise semantic headlines** per story, aligned to actual themed hook, proof and takeaway illustration, rather than duplicating the full spoken sentence at top. Original full spoken text still appears once in the genuine PCM-derived ASS and exported SRT. Static original source keyframe previews keep their original unmodified text.
- Video-specific original phase images now reject any headline which equals the entire spoken source caption, ensuring no regression to double text. Original hero illustration remains unchanged.
- FFconcat dynamic image segments include the **full PCM source cue start-to-next-cue start** interval, including 0.13s of silence between phrases; final segment extends through measured original PCM total. A zero-drift invariant verifies each hero start is aligned to the corresponding actual generated PCM cue start. Explicit receipts bind both total visual story time and source-audio duration, with permitted drift at most 0.005s. No artificial claim of true 24fps fully modelled 3D: video encodes at 24fps but art poses update at limited subframe granularity.
- The main-only 3 Short render GitHub workflow fails closed if any actual original Short lacks `true_caption_and_hero_starts_bound_to_same_pcm=true`, has >0.005s drift or source/art final duration differs. Strict real AAC, native subtitle, full-decoder and SHA validations remain enabled.

## Release boundary

PR CI must pass the exact source test and original 1080p glyph boundary checks; then MAIN must actually render all three corrected real H264/AAC MP4 files and retain a *new* owner-unapproved artifact, followed by independent frame-review. Neither B1q2 nor B1q2b changes the existing YouTube video ID, private scheduled time, captions or releases. Official [YouTube Help](https://support.google.com/youtube/answer/55770) states the uploaded video binary cannot be replaced at the same URL. Fresh authenticated read-only channel schedule inventory and an exact new-MP4 owner rights/facts/voice/creative approval are still missing. Source screenshots' original video ID link remains unknown; old videos are not quietly deleted or duplicated.

Future authentic engaged-views/retention loop remains observability-only with human creative approval, not fake causal reinforcement. Engineering progress estimate remains conservative at 40/100; real unattended uploads 0/21.
