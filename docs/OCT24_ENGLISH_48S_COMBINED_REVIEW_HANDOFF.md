# FlowMinute Lab — Actual complete 48-second English Short review cut (Oct 24)

**Completed review-only video exists**, distinct from storyboards or conceptual clips.

- [Successful authenticated GitHub Actions cloud composition](https://github.com/Tirthanand17/taskless-lab/actions/runs/39971905081): combined owner-approved 8-second HeyGen Asha/Jay opening with 40-second Kokoro ONNX narrated animated explanation.
- Independently downloaded the GitHub artifact in the conversation runtime, extracted and confirmed MP4 bytes (source SHA-256 `e5634ee7dc27cef520a4430a54ff6bb9a13df3226a0bb0e4f4f14b5878a51ea3`), 48.0213s, 720×1280 H.264, AAC and complete FFmpeg decode. **No placeholder animation or test file used in composition.**
- Visually sampled frames from both scenes and all five diagram beats.
- Fixed an 11 dB audio-level mismatch by attenuating 0–8s opening to 32% of its original amplitude. The six eight-second windows subsequently have RMS levels -23.92 / -25.39 / -24.76 / -25.47 / -25.37 / -24.62 dBFS respectively.
- Produced a clean audio-balanced complete video, SHA-256 `84286bec5278b45cc95c5704ce8920d7219a2cf77dd106908305c00842330c15` and a captioned audio-balanced review export, SHA-256 `2f3bd87b93f36113595021b2917cd0a65bf370690f949e82e73be421f8f9e59a`. Both have verified complete video/audio decode, 720×1280, ≈48s.
- The first caption attempt was rejected because typography overlaid the central lesson; corrected to a three-line lower-third style with readable contrast; manually checked a representative frame.
- Conversation review package: `FlowMinute_Oct24_English_48s_Complete_Review_Pack.zip` includes clean/captioned exports, source cloud MP4, SRT, contact sheet and QA reports. It is **not** uploaded as binary into this public GitHub branch. Original cloud artifact `12510000965` expires after one day.
- `state/production/oct24_english_48s_review_bundle.json` is the authoritative *production* audit record; `docs/OCT24_DIRECT_YOUTUBE_RELEASE_STATUS.json` is the authoritative *schedule* state.

### Outstanding gate before direct YouTube scheduling
1. Human playback approval of synthesized explanatory voice naturalness, pronunciation and audio mixing.
2. Verify what the HeyGen opening actually says and add accurate 0–8s subtitles. Sentence-level 8–48s subtitles require spoken-word alignment review.
3. Review original source rights, disclosure classification and claim accuracy.
4. Confirm a working YouTube OAuth uploader; current `publish-artifact-youtube.yml` requires `vars.PUBLISH_ENABLED` and `secrets.YOUTUBE_TOKEN_JSON`, whose actual values **cannot be inspected through the available connector**.
5. Upload only the approved final MP4, read back the authentic YouTube video ID, scheduled UTC time and processing status.
6. Hindi Short and Hindi long video are still not complete, so October 24 **0/3 verified scheduled**.

**Do not claim published or scheduled.** No paid service activated, user laptop Nirala not accessed.