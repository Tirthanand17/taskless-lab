# Branch 1 — Use full genuine action footage under each narrated chapter

## Verified creative issue

After earlier 10-second recordings produced 90–96% nearly static UI frames, the successful longer source capture and narration workflow `43817511871` reduced measured static pair share to **45.3% in LibreOffice Calc** and **50.9% in Chrome** (visual audit `43817954459`). Both newer versions now show genuine application change in the first three seconds and their worst frozen streaks are 0.5s and 1.5s respectively. Both still fail the strict internal 45% static-pixel screen and remain **not authorized for YouTube publication**.

The latest editor uses a genuine **8.5-second source segment** per chapter, but if the speech chapter lasts ~5 seconds, ordinary `trim=duration=5` takes only the *beginning* of those 8.5 seconds, discarding later real actions. Additional screen movement exists, yet it is not visible in the finished narration edit.

## Change

The editor now computes playback rate `authentic_source_speed = recorded_window_seconds / chapter_voice_seconds` and applies `setpts=(chapter_voice_seconds / recorded_window_seconds)*(PTS-STARTPTS)` **before** the frame rate conversion and final chapter trim. In an 8.5s source window with 5.0s spoken content, all eight and a half seconds of genuine application activity appear at **1.7x original speed** during the five-second explanation. FFmpeg does not invent interface interactions.

Source retiming is strictly **0.75–2.1x playback** to avoid illegible fast-forward; the existing action coverage check is retained, cloned holds are capped at 1.25s, and the independent postrender genuine-app pixel motion audit remains mandatory. Speed is not used to fabricate “genuine app” screenshots or guaranteed engagement.

### Safety checks

- Extra unit tests assert `setpts` per chapter uses the full original window rather than a pre-trimmed fraction, no 12-second frozen padding, and rejects non-finite or excessive speed.
- Exactly the original first-party dummy-data Calc or isolated Chrome UI provides app-related footage. It remains **LibreOffice Calc, not Excel**, and Chrome permissions are **not** changed.
- Full output must still satisfy the original SHA-256 source receipt, Kokoro voice checksum, post-AAC loudness, captions, full decode, and actual-pixel creative audit. A passing encoding test does not imply a watchable video.
- No changes to channel, scheduled videos, Google data, personal laptop, purchases or YouTube credentials.

**Next:** run source-only PR tests, manually render the two real-app Shorts from a new GitHub Actions run, then manually invoke the independent pixel motion audit on *that exact run*. Do not reduce the 45% creative threshold to get a green status. If the Chrome video still fails, replace repeated settings-page toggles with purposeful, explainable genuine navigation and improve its UI legibility; no auto-publishing.

**Outcome is unproved until the exact newly rendered video is measured and watched.**
