# Branch 1 — Actual mobile-frame visual review and clarity repairs (16 November 2026)

## Why motion checks were insufficient

An independent check of the exact main-branch narrated files in [run 43827319760](https://github.com/Tirthanand17/taskless-lab/actions/runs/43827319760), plus six timestamped mobile preview screenshots per video from [visual QA run 43827791077](https://github.com/Tirthanand17/taskless-lab/actions/runs/43827791077), revealed problems **not** detected by the successful unchanged-pixel test:

- **LibreOffice Calc**: long A1/B1 worksheet headings visibly overflow and obscure neighboring cell information; the enlarged lower detail crop shows the end of long labels, not a clean comparison. When selecting cells at the old 185% Calc zoom, the input column can scroll off the left side. The proof chapter displays the real FALSE/TRUE outcomes while its narration says only that the comparison fails; the hook needs to acknowledge the cleaned TRUE outcome.
- **Chrome**: the exact video crop starts 60 source pixels from the left, visibly removing the beginning of settings labels. Repeated back-and-forth settings-page navigation may create measurable motion but remains confusing as a user tutorial. A successful motion audit does **not** mean that this sequence teaches the correct clicks.

These were observations of extracted, genuine review frames. The exact audio files have been technically validated for codec and loudness, but this record does **not** claim an independent human listening review of pronunciation, music, pauses or final acceptance.

## Specific source-first repairs in this PR

- Real LibreOffice worksheet now uses compact A1 section titles (**RESULT: TRUE**, **BEFORE: INPUTS**, **CAUSE: SPACES**, **FIX: TRIM**, **AFTER: TRUE**), compact B1 step labels (all 8–18 characters) and concise original C1/C2 explanatory values. This removes overflow from the **actual captured application**, rather than painting over it later.
- Real worksheet data/result columns A and B have reduced widths, making the original `"  Invoice"` and `"Invoice"` cells and actual `=A2=A3` FALSE and `=TRIM(A2)=TRIM(A3)` TRUE results more likely to remain visible together at 185% zoom.
- The expanded lower Calc panel crops more closely around the real result rows, rather than replaying large, clipped worksheet headings. The source remains a real LibreOffice Calc screen recording and verified ODS, **not an Excel mock**.
- The Chrome editor crop begins closer to the actual left edge, preserving labels such as `Sites can ask to send notifications`. The browser remains a fresh temporary Chrome profile; **no notification settings are changed**.
- The spoken proof chapter states the actual two values that are visible: the direct comparison is FALSE and the trimmed comparison is TRUE. No false virality claim or fabricated permission state.
- Additional unit tests prevent regressions in readable title lengths, crop geometry and fact-matched opening narration.

## What this DOES NOT prove or change

These changes are expected visual repairs, not automatically accepted creative. A new main-only GitHub render and **independent exact-file source-pixel check** must pass first. Then inspect the **new** actual phone-sized frames and the full narrated MP4. The audience's 21.2% historical stayed-to-watch baseline cannot be claimed to improve merely because our local frame-crop and motion tests pass.

**Chrome's repeated page navigation still requires a coherent user-first redesign before a release decision**, even if its new mobile crop passes. Do not approve based on the number of moving pixels.

All output remains **REVIEW ONLY, NO YOUTUBE UPLOAD/SCHEDULING, NO PURCHASE, NO REAL USER ACCOUNTS OR LAPTOP MEDIA STORAGE**. Already scheduled videos are unchanged.
