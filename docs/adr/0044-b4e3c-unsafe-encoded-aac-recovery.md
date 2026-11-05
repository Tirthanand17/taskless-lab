# ADR-0044 — B4e3c recover unsafe AAC preflight without weakening independent output limits

**Date:** November 5, 2026 IST. **Branch:** 2. **Scope:** GitHub-only technical video preview repair. No OAuth, real channel upload, owner rights approval or paid/cloud deployment. Assisted Branch 1 remains untouched.

## Actual failure evidence and impact

B4e3 cinematic render bridge PR #48 merged into main at SHA 87a7a9176c8e59f5a173f527dc98948963968122 after all seven exact-head GitHub checks green. Full old-style 3-topic video regression run #41989587915 actually passed all three voice files and strict independently decoded AAC checks: Moon Short -17.68 LUFS/-2.86 dBTP; 219-second long -17.51 LUFS/-3.11 dBTP; earthquake Short -17.42 LUFS/-3.08 dBTP. However, **the first new fully cinematic production proof attempt on main run 41990778510 failed** at its first enhanced Short's encoded AAC: true peak **+0.17 dBTP**, after otherwise successful native visual pixel CI. This is NOT an accepted/published video; no preview artifact was uploaded. Actual job #127122647863 threw ReviewerError from independent_av_review.parse_loudnorm. User must not be told a cinematic MP4 exists without an actual GitHub artifact.

## Exact root cause

The prior audio repair design ran _encoded_audio_loudness() BEFORE trying to repair encoded AAC, but it reused parse_loudnorm(), a *strict final-output validator* that REFUSES over-ceiling raw peaks above 0 dBTP. That threw before the audio-only correction could execute. Even though the quality gate was protecting outputs, the intended recovery path was unreachable for exactly the case it was designed to fix: an over-peak intermediate lossy AAC master. Do not weaken independent_av_review.parse_loudnorm or its -20..-12 LUFS and <= -1.5 dBTP diagnostic.

## B4e3c technical resolution

The pre-repair measurement now has two distinct modes. **Raw observation** parses a single real FFmpeg loudnorm JSON summary with strict syntax, finite values, bounded plausible integrated loudness (-31 to -7 LUFS), bounded true peak, bounded LRA, and real local MP4 file preconditions. An unsafe +0.17 dBTP input is labeled explicitly **raw_over_ceiling_only_for_repair=true** and is NEVER labeled technically acceptable. **Strict final mode** invokes the EXISTING independent parse_loudnorm code unchanged. If raw AAC fails the target band, exactly ONE bounded real FFmpeg audio-only correction is allowed while H264 video is stream-copied; the repaired AAC is then strictly remeasured, and the original is replaced only when the repaired file itself passes. independent_av_review still independently inspects final media after the correction. An unfixable, silent, malformed, overly hot or absent file fails closed.

Seven dedicated adversarial Python tests cover an actual unsafe measurement JSON with +0.17 dBTP; strict refusal of identical bytes; valid actual target confirmation; forged/gross invalid/silent numbers; missing/symlink paths; a bounded corrected-result path where FFmpeg video codec is stream copied; failed correction leaves original untouched; safe originals are not reencoded. These exercises include mocked FFmpeg stderr for unit-level recovery flow. They do NOT substitute for a real on-run full encoded video: the new B4e3 workflow now triggers a full three-cinematic-video review run on main audio-pipeline changes, in addition to strict PR checks.

## Acceptance evidence only

1. Every exact-head PR check green, especially B4e3 fast physical 2-Shorts/long scene/caption tests and seven B4e3c sound-recovery cases, plus real full original Kokoro 3-voice regressions, content and source safety. Do not merge on skipped or red checks.
2. After merge, MAIN GitHub Actions must independently render all three source-pinned **cinematic_v3** MP4 videos with actual Kokoro narration, repaired-on-demand H264/AAC mastering, timed subtitles and visuals, original thumbnails, three same-source classic/cinematic side-by-sides and screenshots from the actual encoded media. A real nonexpired download artifact with the correct manifest and SHA files is the minimum objective proof.
3. No owner full video watch/listen, legal rights verification, strong subjective creative rating, live channel OAuth or publish is earned by these technical tests. Real unattended YouTube uploads remain **0/21**, production readiness rubric **40/100** until a different measurable production milestone occurs.

The owner's uploaded third-party reference video/soundtrack is NOT copied to the GitHub repo, which is public. No owner's laptop storage was used.