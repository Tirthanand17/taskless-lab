# ADR-0088 — B4f6 repair real FFmpeg freeze detection in owner opt-in cloud export

**Date:** 2026-11-07 IST. Branch 2, **NO PUBLISH**. Reproducible GitHub Actions failure: [manual review #42342965222](https://github.com/Tirthanand17/taskless-lab/actions/runs/42342965222).

## First real opt-in review export finding

The manually dispatched full 17-scene three-MP4 rehearsal produced the original media and reached the B4f4 full encoded video/audio scan. The FFmpeg parser raised `SignalReviewRefused: Unmatched freeze start`, so the one-day review artifact was **not** retained and no actual human review completed. The source of the exception was wrong assumptions about the real FFmpeg log, not a failed video render or proof of an animation defect.

The urgent B4f4 hotfix PR #102 prevented that exception by ignoring unpaired start records and reconstructing completed freeze intervals from the (previously assumed) combined `freeze_end | freeze_duration` log line. That prevents the crash, but actual FFmpeg 7.x emits three **separate** stderr records, e.g.:

```text
lavfi.freezedetect.freeze_start: 7
lavfi.freezedetect.freeze_duration: 7
lavfi.freezedetect.freeze_end: 14
```

The earlier `FREEZE_END` regex did not match these records, meaning a report could silently drop **completed** static/frozen intervals even after the hotfix. This was reproduced against a 21-second completely synthetic moving–black–moving FFmpeg filter graph (no user MP4 or channel data).

## Correct repair

- Replace combined-line matching with `FREEZE_EVENT` events parsed in **source order**: `start -> duration -> end`. Require bounded event counts, finite timestamps, one active segment at a time, and exact `end - start = duration` within 0.45 seconds. Abort on orphan, duplicated, reordered or impossible event sequences.
- Include a trailing unfinished frozen interval **only** when a valid `freeze_start` appears and no ending record arrives before stream completion; label `unfinished_at_video_end=true`. Do not mistake an abandoned middle interval for a known complete freeze.
- Keep all three final-MP4 digest verification, original 4/9/4-scene count, full H.264/AAC decoding, timed black and silent warnings, numerical clipping checks, one-day opt-in artifact safeguards, no owner-review approval, and no YouTube uploads.
- Update the fake FFmpeg regression fixture to **actual three-line FFmpeg logs** and add a real installed-FFmpeg end-to-end integration test that synthesizes 7 seconds moving picture, 7 seconds still black, then 7 seconds moving picture plus original sine audio. Assert that a **completed** 7–14s freeze warning is detected; a mere trailing-open freeze test would not have caught this incident.
- Adversarial tests cover multiple complete segments and trailing static tail, orphan/reordered start/duration/end, missing media volume, physically impossible ranges, and unchanged false-approval flags.

## Release and operator scope

This repair allows a truthful technical warning report to be generated for **explicit manually opted-in original video reviews**, but cannot automatically classify rotating-circle graphics or guarantee engagement. A completed 7–14-second freeze might be an intentionally static instructional diagram; only the actual owner watching the MP4 can classify it. A 0-warning technical scan does **not** confer factual correctness, asset rights, human watch or approval to publish.

An opted-in GitHub cloud workflow, once all tests pass and code is merged, must be rerun on `main`. The resulting MP4 artifact expires in one day; no laptop files, account credentials or YouTube writes are necessary. The 7-day goal remains 0/21 independently verified releases until real authentication and approval stages are complete.
