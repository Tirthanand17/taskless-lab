# FlowMinute Lab — October 20 editorial captions, NOT verified speech

These are real, UTF-8 **SubRip (.srt) files** for the existing original
20 October 2026 narration *scripts*. They are editable in common video
editors, but the times are **SCENE-BASED ESTIMATES**, NOT obtained from audio,
word recognition, an approved person, a real captioning provider or YouTube.

| File | Language and format | Target duration | Cues | Original source scenes |
|---|---|---:|---:|---:|
| fm_20261020_short_en.draft_estimated.srt | English short | 42 s | 13 | 7 |
| fm_20261020_short_hi.draft_estimated.srt | Hindi short | 44 s | 14 | 7 |
| fm_20261020_long_hi.draft_estimated.srt | Hindi long | 480 s | 110 | 11 |

Use each file as a **temporary positioning guide** only. When real rights-cleared narration is available, do a full independent listening/transcription pass and retime every actual spoken word / cue in the audio editor. In particular, re-time the visual scenes to the human audio rather than trying to force unnatural playback speeds. Then repeat video/audio codec, caption legibility, original-media rights and pronunciation review. **Do not upload this draft as verified YouTube subtitles.**

All captions preserve every whitespace-separated token of the original,
three-lane source-verified October 20 script. There is a maximum of two
caption lines with no more than 36 Unicode code points each; any one cue
is no longer than 4.5 seconds. Scenes have no missing or overlapping time.
The generator balances words across each scene to avoid awkward single-word
caption fragments, and declares the entire asset ESTIMATED / NOT ASR.

Source-of-truth: ../2026-10-20-gemini-agent-control.json
Regeneration utility: ../../../autopilot/oct20_estimated_subtitles.py
Regression suite: ../../../autopilot/test_oct20_estimated_subtitles.py

Offline regeneration without cloud or YouTube connection:

    from pathlib import Path
    from autopilot.oct20_estimated_subtitles import export_oct20_estimated_srt
    export_oct20_estimated_srt(Path("/an/existing/empty/editor-folder"))

The exporter refuses to overwrite any existing .draft_estimated.srt file.
It writes no audio, no legal document and no account credential.

**Production truth:** No licensed human voice recorded or verified; no live
speech-to-text recognition; no real acoustic SRT synchronization; no real
English/Hindi narrator identity/rights verification; no final audiovisual
42/44/480-second production files; no Cloudflare changes, YouTube schedules,
uploads or public publishing. This batch requires real speech and rights
before any final media handoff. Monthly recurring cloud spend authorized ₹0.
The old 21 production acceptance subphases remain open.
