# FlowMinute Lab — full-duration AAC sound-activity coverage for every estimated SRT cue

19 October 2026 | Public draft PR #5 | No video upload, external ASR or production acceptance

## Problem

The previously implemented whole-media FFmpeg/FFprobe decode and final AAC signal checker sampled just five short waveform windows across each finished video. An otherwise technically acceptable video could still contain a long silent stretch coinciding with the lesson narration or entire subtitle cues. Five globally sampled windows cannot establish complete speech coverage.

## Incremental safety improvement

The optional, read-only module cloud_cue_audio_activity.py accepts only:
- The existing, already independently decoded original H.264/AAC MP4 with exact source hash, lane, byte count and original frame count.
- Its original MuxedAudioScreen with valid previous five-window technical AAC screen, no false audio or release claims.
- The existing script-derived CandidateWordTranscript, whose exact words, cue timing structure, authored SRT SHA and same MP4 SHA are checked against the unmodified FlowMinute Hindi/English lesson specification.

It decodes the COMPLETE source soundtrack exactly once via local FFmpeg, 8 kHz mono little-endian PCM16, with a fixed 42-second or 432-second source-lane duration, bounded timeouts, expected PCM byte limits and no shell/network/temporary output file. The MP4 is SHA-256/size/inode rechecked before and after the audio decode. It scans 200 ms PCM energy windows and checks every original author-created subtitle cue for actual acoustic energy. A cue with fewer than 25% active windows is marked technically sparse. The report records the cue coverage count and explicit blockers, and always marks speech recognition, word correctness, language, narrator identity, actual speech-caption synchronization, commercial voice rights and release authorization FALSE.

This is a better check against accidental missing audio, NOT genuine ASR, diarization, subjective naturalness, voice identity, speech correctness or acoustic word-to-cue alignment. Music, noise or fabricated alternating samples may satisfy acoustic occupancy; likewise quiet intentional pauses may be flagged for further review. Estimated subtitle timings remain estimates and MUST NOT be automatically certified or published based on this check.

## Offline regression coverage

test_cloud_cue_audio_activity.py includes deterministic PCM fixtures (not real narration) showing full-duration synthetic energy coverage, a silent middle cue missed by five globally sampled points, all-silent failure, malformed or truncated/oversized decoded PCM refusal, invalid MP4 identity / symlink / route permissions refusal, source-file mutation during decode, all three original language lanes and no-approval constraints, and malformed PCM refusal.

These are synthetic mock FFmpeg bytes; they do not demonstrate that any recorded human-sounding FlowMinute episode was acquired, consented to, fully rendered with synchronized subtitles, privately retained or uploaded. Both PRs remain draft; there is no change to production cloud controller, Cloudflare D1, YouTube credentials, rights declarations, account or software deployment.

## Next actual production requirements

Collect **genuine rights-cleared narrator recordings** in the three languages/voices required by the owner, independently check actual spoken words and timestamps against these original media hashes, verify identity/consent and visual licensing, and obtain separate signed external reviewer evidence. In parallel, finish the owner-authorized cloud data and publishing prerequisites and independently confirm a sustainable ₹0 media production/storage budget. The original 21 production acceptance subphases across six incomplete major phases remain open. No laptop/Nirala, provider signup, Google/Cloudflare contact, media upload or new recurring charge occurred.
