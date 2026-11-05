# Phase 3U — full 7-scene 42/44 second ORIGINAL visual review cut

19 October 2026 | public DRAFT PR #5 | no third-party cloud service / Google / Nirala

## What changed beyond the 9-second kinetic snippets

- Source-of-truth original scripts: content/production-packs/2026-10-20-gemini-agent-control.json
- New reusable script-bound compositor: autopilot/oct20_full_silent_timeline.py
- New adversarial tests: autopilot/test_oct20_full_silent_timeline.py

The English Short has EXACT seven scene boundaries (seconds) 0,4,10,16,22,29,36,42. The Hindi Short has EXACT seven boundaries 0,5,11,17,24,31,38,44. The production code validates the existing October 20 source editorial packet's draft status and existing seven scene plan. No made-up word timings are substituted. Each original keyframe generated with the existing programmatic Pillow renderer has bounded camera zoom/pan composed in FFmpeg, exact 24 fps, 432x768 output and one H264 stream only. Each independent segment is checked with FFprobe before concat into one full video-only MP4; final exact frame count and duration are checked again.

The public CI tests use a REAL one-second H264 smoke to conserve free GitHub execution time. They assert the complete 7-scene frame ledger, full timeline lengths, invalid source rejection, existing file preservation, non-MP4 rejection, false test-mode input denial, and the permanently disabled voice/upload/publish privileges. Public CI does not render 42+44 seconds of final video as an Actions media farm.

## Actual local render evidence (ChatGPT isolated sandbox, not Nirala)

An independent local scratch implementation using the same October 20 original scene headings, exact script scene boundaries, Pillow storyboard design and FFmpeg zoom/pan produced two full-length silent review files:
- fm_20261020_short_en_full_7scene_silent_review.mp4: 42.000 seconds, 1008 H264 frames, 432x768, 24fps, 1 video stream, no audio
- fm_20261020_short_hi_full_7scene_silent_review.mp4: 44.000 seconds, 1056 H264 frames, 432x768, 24fps, 1 video stream, no audio. It uses a separate localized Hindi lower approval panel.

Both were FFprobe-checked in the isolated ChatGPT workspace and offered as conversation attachments. These are NOT persistent GitHub binary artifacts, NOT actual channel uploads, and NOT a claim that the exact GitHub compositor produced the two local binaries. GitHub's source-bound one-second output is independently tested in CI.

## Acceptance truth and creative limitations

These clips are moving camera previews of intentionally original 2.5D cards, not genuine photorealistic/3D cinematic footage. Their seven scenes cover the full intended script-time grid but do not use word-by-word recorded speech, sound design, actual human narration, validated voice rights or independently measured sound-to-caption timing. No shopping account, AI task execution, real vendor UI or remote approval action is simulated as real.

Required next acceptance work: licensed rights-cleared natural English/Hindi distinct speakers, recorded full take WAVs, independent true speech recognition and subtitle alignment, full HD original cinematic VFX scene assets, human audiovisual quality judgment, verified sustainable INR 0 remote production/storage capacity, and separately approved private YouTube upload/readback before scheduling or public publishing. No production acceptance subphase is closed solely because a silent preview runs end to end.

No Nirala laptop access, new paid service, Cloudflare production DB, Google OAuth, owner video upload, public YouTube publication or external connection. Both PRs remain DRAFT. Approximate previous software 45%, actual autonomous production 20%; 21 production acceptance subphases across six major unfinished phases remain open. Monthly recurring budget INR 0.
