# ADR-0073 — B4d9 source-locked original 17-scene voiceover REHEARSALS, not news scripts

**2026-11-06 IST | Branch 2 | GitHub-only | No article facts approved, voice, media or publishing**

## Baseline

B4d8 merged PR #82 to prevent exact source/subject repeats across days. A trusted GitHub default-main run [42236380521](https://github.com/Tirthanand17/taskless-lab/actions/runs/42236380521) demonstrated two actually fetched source pages, four literal source-passage investigation questions, three 4/9/4 storyboard research OUTLINES, and zero fact/rights approvals, scripts, narration audio, fresh daily media or YouTube uploads. No original **spoken sentences** existed for those scheduled slots; a scene outline is not a voiceover.

## Implemented

`autopilot/nonfactual_narration_rehearsal.py` now constructs **actual original spoken text** for exactly three episode-locked *nonfactual educational rehearsals*: AM Short 58 seconds / four scenes / 1080×1920; long 240 seconds / nine scenes / 1920×1080; PM Short 58 seconds / four scenes / 1080×1920. This is **17 individual paragraphs of original voiceover text per day**, including hooks, an instructive imaginary baseline/demo, concrete invented failure cases, a limitation, an independent-review invitation and a viewer action. Every scene has target frames at 30 fps, original diagrams/synthetic sample visuals, a static captions safe area, an individual short SFX suggestion, one-time motion (no endless spinner), and restrained optional music guidance. Short AM and PM use different hooks/example structures even when both have the same research family. Six safe example families exist: agents, model comparisons, data quality, permission checks, developer tests and an agnostic illustrative scientific experiment.

These rehearsals **intentionally do NOT announce any new model, vendor feature, experiment result, statistic, or news claim**. The script text comes only from original code-authored hypothetical educational demonstration templates, NEVER from scraped publisher news headlines or copyrighted article passages. As such the rehearsal count is separate from the **0 factual news scripts** count. Word count and frame budgets are checked; voice waveform pacing is not tested because **there is no recorded voice** yet. Actual media rendering from these scripts is likewise not claimed.

Strong provenance: the generator independently recalculates the previous B4d5 plan/board, B4d6 per-source brief, B4d7 exact article/excerpt claim investigation docket; refuses tampered passage digest, changed source ID, mismatch across episodes, fictitious claim approval, altered editorial source, any model call or publication authority. Every rehearsal carries hashes of its own brief and review docket but **does not quote or disclose full source URLs, headlines, article sentences, images, or third-party figures**. Scripts and source evidence exist only ephemerally in the GitHub Actions runner, are not printed in logs/artifacts and are removed with unconditional final cleanup. Existing two sanitized metadata-only public receipts remain unchanged.

Adversarial tests exercise duration/frame continuity, 17 non-placeholder original voice paragraphs, distinct AM/PM/long style, no repeating spinner, 6 source-category scenarios, zero-source day fallback, source-byte hash mismatch, quote-rights flag forgery, fake review approval, actual CLI write-once and no network/provider calls.

## Not complete / crucial next milestones

1. **Current-news claims and semantic script drafting:** The present original scripts are practice demonstrations, not proof of what a named recent article announced. Need independent human factual+rights review, then a source-grounded approved final voice script; code templates cannot make an unverified fact true.
2. **Real audio and video:** Record/measure voice, sync sound effects and animations to actual waveforms, make genuinely fresh full Shorts and long video, watch all scenes for legibility and voice quality. Existing Remotion/FFmpeg cloud smoke test currently tests an older demo, NOT these new 17 scenes.
3. **Owner and publisher permissions:** Secure signing/review/YouTube OAuth grant and owner-approved budget remain disabled; none of the three rehearsal texts are allowed to release or schedule.
4. **Historical novelty:** Previous-research hash guard is partial when previous receipts are unavailable. Publishing needs separately authenticated *actual YouTube* readback.
5. **Operational proof:** Independently verified laptop-off 7-day, 2 Shorts + 1 long/day public release proof remains **0/21**.

## Verification gates

Require exact PR head to pass dedicated daily foundation/test script, repository-wide Content Quality, Cloud Scout and actual trusted previous-source Remotion/FFmpeg H264/AAC smoke. After squash merge, trusted main GitHub run should show **3 actually-written nonfactual rehearsal scripts, 17 original scene paragraphs, 58/240/58 targets, zero actual voice/video, zero model paid calls/YouTube writes**, plus precisely two public sanitized receipts. No factual scripting/media/publishing-readiness percentages should be inflated by rehearsal-only success.
