# Phase 3Z — measured all 14 original Short scenes; nonbinding editor retime

19 October 2026 | public draft PR #5 | INR 0/month / no Nirala

## Concrete result

The previous Phase 3Y offline eSpeak test measured only ONE EN and ONE HI opening scene. Phase 3Z runs the whole first seven-scene script for each original October 20 bilingual Short, **14 genuine mechanical WAV synthesizations** in an isolated ChatGPT session with an already-installed eSpeak binary. They are REJECTED as FlowMinute production narration.

- English: original 42.000 second editorial script grid; sum of per-scene **actually generated mechanical PCM audio** 35.598 seconds. The first hook takes 5.396 seconds rather than its original 4.000 second cut (+1.396); 1 of 7 mechanical scenes exceeds its old slot.
- Hindi: original 44.000 second editorial grid; actual mechanical PCM speech sum 39.429 seconds. The first hook takes 5.686 seconds rather than its 5.000 second cut (+0.686); 1 of 7 scenes exceeds its old slot.
- Both tracks therefore have time budget in later cuts, but time needs to be reallocated at the hooks rather than artificially accelerating speech.

**Critical WAV parser finding:** eSpeak --stdout is an unseekable RIFF stream and declares a giant placeholder size in its WAV header. Python wave.getnframes() naively reports roughly 48,695 seconds. Phase 3Z explicitly counts actual bounded PCM bytes read, computes measured audio frames/sample rate and never trusts the streaming RIFF size sentinel for recorded duration. Independent regression test for a forged oversize RIFF header validates this behavior.

## GitHub deliverables

- autopilot/oct20_mechanical_scene_pacing.py — source-locked seven-scene original EN/HI scripts; explicit already-installed offline eSpeak binary only; bounded per-scene stdout WAV generation without saving model/audio files; exact raw PCM frame count, per-clip SHA, maximum runtime and immutable no-upload rights flags.
- propose_scene_frame_retime — deterministic 24 FPS frame allocation, preserving the original 42/44s exactly, with +250 ms mechanical speech headroom per scene; first-hook deficit borrows from later spare scenes. A too-long actual take is BLOCKED rather than being sped up. **This output is nonbinding until genuinely consented, natural recorded narration is available.**
- autopilot/test_oct20_mechanical_scene_pacing.py — source scene IDs, case/length bounds, exact runtime preservation, fake streaming WAV header handling, missing already-installed engine guard, no model download, and an OPTIONAL genuine all-14-scene eSpeak test when the public CI runner happens to include it; otherwise it is correctly skipped, not simulated.
- state/production/oct20_rejected_mechanical_scene_pacing_2026_10_19.json — actual measured 14-scene timing ledger and computed cut frames, never an upload manifest. Regression tests recompute each frame boundary from all fourteen genuine measurements.

Frame-exact visual retime proposal:
- EN original scene frame lengths [96,144,144,144,168,168,144] become [136,134,144,137,163,168,126], 1008 frames total at 24fps / 42.000s.
- HI original [120,144,144,168,168,168,144] become [143,130,144,159,168,168,144], 1056 frames at 24fps / 44.000s.

## Actual original silent VIDEO review renders

In the isolated ChatGPT working sandbox, using existing original card art and FFmpeg only (not Nirala), rendered two **new full 7-cut silent** visual reviews with these precise retimed frame durations. The rendered local code is a parallel preview using the existing original diagrams and measured frame proposals, not a claim that GitHub's new source module itself rendered both binary MP4s. Independent ffprobe confirmed:
- English fm_20261020_short_en_mechanical_retime_silent_preview_ONLY.mp4: 42.000s, 432x768, 24fps, exact 1008 H.264 frames, only video stream, zero voice/audio.
- Hindi fm_20261020_short_hi_mechanical_retime_silent_preview_ONLY.mp4: 44.000s, 432x768, 24fps, exact 1056 frames, no audio, translated Hindi diagram panel.
- The old estimated SRT cue boundaries have NOT been updated because these cut proposals are NOT measured human speech timing. Muxing those old captions with actual approved narration without retiming would be misleading. No actual YouTube upload/schedule/publish.

## Editorial and legal status

A robotic eSpeak cadence is **NOT** a measure of a future natural narrator's accent, expressive pacing or human pronunciation, and a clean waveform is not evidence of authentic human speech, consent or commercial rights. This phase supplies a concrete, reproducible offline video editor experiment and catches a real WAV-stream parsing problem; it does **not** prove 3D cinematic quality, high-definition output, genuine rights-cleared audio, separate speakers or authenticated ASR/caption synchronization. There is no provider-recognized speech or natural Hindi/English narration.

Do not download Kokoro or other new model weights, use new inference providers, run private Actions, change Cloudflare D1/Google OAuth, use the Nirala laptop, spend money, submit a YouTube video or mark a schedule published without the required separate approvals. User budget remains INR 0/month. Both PRs remain DRAFT/unmerged. Previously tracked 21 pending production acceptance subphases across six unfinished major phases stay open; old approximate software ~45% and production-autonomy ~20% estimates remain unchanged.

**Next real acceptance target:** consented commercially usable natural English/Hindi narrator recordings (or a separately authorized audited offline TTS pilot), independent native-language listening and transcription/word timings, actual full video/caption retime and source/rights review. Then genuinely free remote production capacity and a separately approved YouTube private release/reconciliation pilot.
