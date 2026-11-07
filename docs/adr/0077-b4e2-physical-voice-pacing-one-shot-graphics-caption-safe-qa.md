# ADR-0077 — B4e2 measured-pacing calibration, real one-shot scene reveals and caption-safe QA

**Date:** 2026-11-07 IST. **Track:** Branch 2, free GitHub CPU media rehearsal. **Status:** Nonfactual, no publication rights/YouTube uploads.

## Real trusted measurement used

PR #86 merged and GitHub default branch [run 42246914153](https://github.com/Tirthanand17/taskless-lab/actions/runs/42246914153) actually synthesized all **17 complete original synthetic training/demo scenes** and fully encoded/decoded 3 real H.264/AAC MP4s with complete Kokoro narration. **Physical PCM durations**, not estimated script reading speeds:

| Slot | Prior Kokoro speed | Measured audio (s) | Goal (s) |
|---|---:|---:|---:|
| Short AM | 0.90 | 59.771 | 58 |
| Long | 0.91 | 227.366 | 240 |
| Short PM | 0.90 | 56.593 | 58 |

The long ended **12.634 seconds short**; Shorts were about +1.771 and −1.407 seconds respectively. Technical success did not mean that any video had been watched, claimed fact-approved, rights-approved or uploaded. The original 17 scene visuals were static variations of almost the same three-card diagram, and libass burned subtitles with no line-count check beyond six-line allowance. This can create dull repetition or caption overlap despite a green codec/full decode.

## B4e2 implementation

1. **Measured voice calibration, no arbitrary silence filler.** `VOICE_SPEED_BY_SLOT = {"short_am":0.93, "long":0.86, "short_pm":0.88}` calculated as prior `speed × measured_duration / target_duration` (close ~57.8, ~240.6, ~57.9s by first-order approximation). This is a **calibrated starting point**, not a guarantee for different scripts, topics or female/male voices. The next live run must physically measure all three again; the existing ±3-second target test remains, and the report states whether each passes. No new paid TTS calls, longer 24-hour jobs, script padding or quiet 12-second hold.
2. **11 authentic different didactic diagram beats.** The original 4/9/4 storyboard types map to **11 distinct card triads**: question, source-scope, mechanism, experimental control, two invented examples, counterexample, verification/rights, and safe viewer action. These synthetic diagrams contain no factual news data, borrowed figures, third-party screenshots or publisher quotation. Across 17 scenes, the painter draws **two physical source images per scene**—a question/example/checkpoint base and a highlighted checkpoint shown **exactly once** after 0.36 seconds. Then the scene holds until the next actual-audio-derived scene boundary. An ordered rectangular scene-progress marker is static, not a ring, spinner, continuous orbital motion, fake progress, or repeated flashing.
3. **Physical video-proof, not just metadata.** The H.264/AAC FFmpeg mux uses a 34-stage image list whose per-stage durations sum to the **same measured original audio scene times**. Actual encoded MP4 frames are then sampled at 0.100s (base) and 0.900s (revealed), decoded in grayscale memory at 192×108, and compared. A failing or identical encoded transition refuses the entire day; distinct original PNG hashes alone are not enough. Full independent FFmpeg stream decode and 3-way unique MP4 checks remain mandatory.
4. **Safe-area captions, actual spoken PCM clocks.** Retain exact source-independent speech and the physically measured phrase-level PCM start/end times. Wrap captions to **44 characters and at most 4 lines for 1080×1920 Shorts**, and **76 characters and at most 2 lines for 1920×1080 long**. Move subtitle bottoms up to y-margins 168px portrait and 148px landscape to avoid the branded footer and live illustration. Reject any long cue that cannot fit its actual panel. Record maximum actual caption lines and peak physical characters/second as **reading-speed diagnostic**, not as human approval. No fake phoneme alignment is asserted; punctuation and entire original spoken words must remain.
5. **Adversarial tests** on true six synthetic topic-family texts, 17 scene types, 34 unique physical Pillow scene images (when Pillow available), actual ffconcat two-stage durations, corrupted video frame samples, monotonic and bounded PCM subtitles, unchanged original licensing/publisher/source/YouTube/no-paid-provider locks. The GitHub daily Foundation workflow runs these on PR and, on trusted default branch, actually generates and decodes the new full films.

## Explicit remaining limitations

- The `atempo` time-stretch filter is intentionally **not** used. The sole voice-speed adjustment is based on observed last-run physical durations, so novel templates may miss target lengths. Report reality. If there is still more than ±3 seconds of long drift, address with a separately reviewed tempo/actual TTS iteration, not padding.
- The 34 stills are a **one-time discrete reveal animation**, not full character animation or fully custom animated infographics; voice, music, safe-area type and creative variety still need owner visual/audio review.
- Peak reading rate is a numeric indicator, not proof a real person found captions readable. Physical encoded frame comparisons verify that **a change** happened, not independent expert signoff that every scene is compelling. Full 17-scene human playback remains unperformed.
- No media bytes are retained after runner execution until source-content rights, voice model/weight redistribution rights and authorized owner-only review storage are settled. The public Actions artifact retains only **two existing safe sanitized source receipts**; raw spoken text, source articles, audio, image and MP4 bytes are purged.
- Real-time publisher claims are still **not fact checked**, so these are practice/nonfactual videos, not publishable AI/science news. No OAuth or autonomous YouTube writes. **0/21** independently proven daily releases.

## Mandatory acceptance

1. Four exact-commit CI: source/cloud foundation tests, full repository Content Quality, cloud scout, genuine Remotion/FFmpeg H.264/AAC smoke.
2. Trusted merged `main` daily run: 3 fully encoded original 4/9/4 scene voice videos, **34 physically different source PNG states**, physically sampled one-shot reveals in all 3 MP4s, visible caption-safe wrapping counts, PCM duration measurements including long target within ±3s if calibration holds, zero fact/rights/owner final-watch approval, zero YouTube uploads or billed providers.
3. Retained ZIP stays exactly two sanitized JSON receipts without captions, source URL/title, article text, license-unreviewed media or secret.
