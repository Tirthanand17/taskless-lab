# Phase 3V — October 20 natural human voice handoff and PCM intake

19 October 2026 | Public DRAFT PR #5 | no voice recorded or provider connected

## Why this is new rather than a duplicate

Earlier phase3_complete_narration_intake.py and phase3_voice_subtitle_handoff.py belong to CSV tutorial scripts (42/42/432 seconds). Their WAV inspector is reusable, but the new original October 20 AI-agent pack has DIFFERENT 42-second English Short, 44-second Hindi Short, and 480-second Hindi long scripts. Reusing old IDs or transcripts would misbind voices and SRT.

autopilot/oct20_owned_voice_handoff.py is source-locked to the Oct20 editorial pack used for the seven-scene previews. It imports the EXISTING inspect_external_voice_wav PCM inspector rather than duplicating its waveform analysis.

## Actual concrete deliverables

1. create_oct20_voice_session_packet() binds 25 original script lines (7 EN, 7 HI, 11 HI-long) to episode/language, exact script SHA-256 and per-cue hashes, storyboard scene target windows and intended **unlicensed** voice-role placeholders. Cue seconds are EDITORIAL WINDOWS, NOT observed speech/word-level timing.
2. content/production-packs/2026-10-20-narrator-reading-sheet.md has all 25 lines arranged for a human narrator, with instructions for natural speech, consented/distinct EN/HI Short speakers, quiet PCM16 recording, commercial-use permissions and independent pronunciation/timing review.
3. export_oct20_narrator_notes() can explicitly write exactly THREE per-episode original text-note files to an already existing directory, refusing overwrite/conflicting paths before any write. Never automatically uploads text, WAV or private legal documents.
4. Oct20OwnedVoiceTake and screen_oct20_owned_voice_takes() inspect three owner-supplied real PCM16 WAV takes and locally supplied rights-file hashes, script-digest match, runtime, sample rate, amplitude, SHA integrity and file-byte distinctness via the pre-existing inspector. They return only sanitized aggregate technical status with ALL independent speech, identity, legal rights, ASR, caption synchronization, mux and YouTube release approval bits FALSE.
5. autopilot/test_oct20_owned_voice_handoff.py creates three ephemeral ACTUAL PCM WAVs containing **synthetic square-wave tones**, not language or human speech. They deliberately last the real full target lengths 42/44/480 seconds and can pass technical WAV checks WITHOUT proving a consenting human narrator. Other tests cover wrong episode, legacy ID, duplicate assets, SHA mismatches, mismatch between EN 42-second and HI 44-second WAV, tampered/symlink rights files, unknown source, falsely promoted speech/rights claim, local export conflict and missing folder. Fixtures are destroyed after testing.

## Real human voice capture runbook (not yet executed)

First arrange THREE real performances from rights-cleared consenting human narrators, using distinct people for English and Hindi Shorts. Record full PCM16 mono 48kHz WAV ideally in a quiet space. Do not automatically use voice cloning or paid TTS in place of a consenting natural human speaker. Keep genuine signed rights files strictly in owner-controlled private storage, not the public repo or PR comments.

When actual WAVs exist, screen their format and exact source hash with this adapter, then independently listen and verify genuine spoken Hindi/English, voice distinctness, natural delivery and source/legal consent. Use independently observed ASR word timestamps to align subtitles. Visuals should be re-timed to audio rather than artificially speeding up voices to meet the draft scenes.

Existing user restrictions remain: do not touch Nirala without separate permission; if later expressly allowed to use the PC, use only the youtube con folder for FlowMinute assets, never new Desktop folders. No connection to any outside account/service without explicit approval. No usage of paid models, private GitHub Actions quotas or cloud media renders unless separately authorized.

A declared speaker consent Boolean, a hashed private file or WAV waveform is NOT evidence of authentic human identity, legally adequate permission or true subtitle timing. Never turn a technical pass into final release authority.

## Safety and readiness

**No natural human voice has been recorded, sourced, authenticated, licensed or added to the channel.** Prior silent previews remain only visual. There are no new uploaded videos, final rendered audio-visual films, transcript timing verifications, new providers, Cloudflare writes, Google OAuth changes or Nirala access.

Monthly recurring infrastructure authorization **INR 0**. Both repositories' PR #5 remain DRAFT. Previous 21 production acceptance subphases across six unfinished major phases remain OPEN; software ~45%, autonomous production readiness ~20%, unchanged by an offline handoff.

Run offline synthetic tests only from an already-authorized source checkout using:
python -m unittest autopilot.test_oct20_owned_voice_handoff

Tests produce synthetic temporary sounds and delete them; no actual human speech/recordings or provider access occur.
