# FlowMinute Lab — Natural Narration Standard

**Adopted October 12, 2026. Applies to EVERY future Short and long video.** This supplements the channel's existing growth and editorial standard. It does not retroactively alter the three scheduled October 12 videos.

## Quality goal

Narration should sound like an interested, natural, clear educator, not a rapid monotonous TTS announcer. It can still be synthetic; **never describe it as a human recording unless a real person recorded it**. No "perfect human voice" claims: the actual listening test determines the result.

## Scriptwriting and delivery

- Write for spoken conversation, not a formal article: direct address, varied sentence lengths, comfortable contractions and natural transitions.
- Begin with a relatable problem, surprise, demonstration or concrete fact. Avoid lengthy introductions or repetitive "in today's video."
- Allow the question/hook to land, then show the payoff; keep pauses purposeful, not artificial.
- Read dates, rupee amounts, AI model names, abbreviations and formula terms aloud before synthesis. Spell ambiguous words phonetically in the **narration script only** when necessary.
- Keep narration honest: simulated tool screens are labeled illustrative; never claim an experiment ran without evidence.
- Do not force every Short to the same duration, use fake breaths or random pitch swings. Shorten the script rather than accelerating too far.
- Reuse a consistent narrator within an episode; change voices only if the content genuinely requires it.

## New narration pipeline

Implementation: motion-v2/natural_narration.py and motion-v2/generate_voice_cli.py.

**Natural mode is the default for new CLI renders.** It splits a script at thought boundaries and key questions, synthesizes short phrases via Edge TTS with modest changes in rate, inserts gentle pauses and decodes/join audio to prevent seam clicks. It records a JSON voice QA report. Human listening review is still mandatory.

Presets:
- curious-short — engaging, not shouty (AvaNeural).
- warm-explainer — warmer documentary / technology context (AndrewNeural).
- calm-tutorial — steady screen demonstration (ChristopherNeural).

Historical Oct 12 workflow is explicitly pinned to **legacy** to avoid changes to the already released output. Do NOT replace existing scheduled videos.

### Commands

From repository root, with edge-tts and ffmpeg available:

    python motion-v2/natural_narration.py --script motion-v2/new-script.txt --output motion-v2/public/new-voice.mp3 --preset warm-explainer --max-duration 65 --report motion-v2/new-voice-qa.json

Offline pacing plan without network or audio writes:

    python motion-v2/natural_narration.py --script motion-v2/new-script.txt --output voice-preview.mp3 --preset curious-short --dry-run

From the motion-v2 directory, the compatibility entry point supports:

    python generate_voice_cli.py --script new-script.txt --output new-voice.mp3 --style natural --preset curious-short --max-duration 55 --report new-voice-qa.json

Use --style legacy ONLY for reproducing previously produced voice tracks.

## Mandatory hard gate BEFORE scheduling

1. Listen to **the entire final MP3** on headphones and phone speaker; assess pronunciation, intonation, emphasis, emotional believability, clarity and conversational flow.
2. Check first 10 seconds have a natural, specific hook; pauses feel intentional; numbers and proper names sound correct.
3. Check no cutoff or excessively long silence and no audible seam clicks. Narration finishes before the video; do not trim mid-word.
4. Mix voice above music/effects; no distracting ducking or excessive compression.
5. Captions must faithfully reflect the final audio and real timings. Scene cue subtitles are not substitutes for accessible captions.
6. Complete human listening QA approval and retain the audio hash/report with the per-episode release manifest. No approval = NO upload or schedule.
7. Confirm rights for music, footage, and narration. Do not misrepresent synthetic content or clone an identifiable person's voice without consent.

The script's automated tests verify chunk planning, timing, PCM joining and reproducible QA metadata. **Tests do not evaluate perceived human naturalness**. Make two preview takes when feasible and choose after listening. Record audience retention and meaningful feedback; no guaranteed views or engagement.

## Provider selection

We retain the existing Edge TTS baseline without introducing a payment requirement. It allows rate, volume, pitch but not arbitrary SSML markup. For high-emotion storytelling, a properly licensed expressive voice provider or a consented human narrator may outperform it. A Gemini Pro consumer subscription does NOT imply API entitlement. ElevenLabs commercial usage requires an eligible plan: never activate billing without owner approval.

Sources:
- https://github.com/rany2/edge-tts
- https://elevenlabs.io/docs/eleven-creative/playground/text-to-speech

## Status

Natural mode implemented and regression tested. Real voice preview and subjective listening approval are separate acceptance steps. Existing YouTube scheduling remains unchanged.
