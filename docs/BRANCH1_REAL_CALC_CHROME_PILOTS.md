# Branch 1 — genuine Calc and Chrome demo pilots (no publishing)

**Status:** first-party real GUI recording code + source-free briefs + adversarial tests + main-only GitHub Actions recording plan. No new video scheduled, no paid tool, no personal profile, no local laptop files.

## Rationale

The channel's earlier Studio audit showed 21.2% Shorts stayed to watch and an average 58-second long-form view duration, with no subscribers gained in the reviewed 28-day window. Our old fixed-template renderers made original illustrations but not real app walkthroughs. The earlier recovery PR #239 proved a real Python terminal video. This integration expands that to two actual GUI applications.

## Verified subjects and precise claims

- **LibreOffice Calc**: real spreadsheet application controlled through its own UNO API on a dummy workbook. Cell B2 evaluates =A2=A3 to FALSE for a leading-space mismatch; cell B3 evaluates =TRIM(A2)=TRIM(A3 to TRUE; an actual ODS workbook is saved. This is **LibreOffice Calc**, not Microsoft Excel. Never show Calc UI and claim it is Excel.
- **Google Chrome**: real fresh browser profile, Selenium navigates from chrome://settings/ to chrome://settings/content/notifications and verifies actual built-in settings UI and final URL. Permissions are **not changed**. Never claim this tutorial has disabled notifications.

## Production and proof chain

1. Creative briefs in content/recovery_pilot/real_calc_trim_short.json and real_chrome_notifications_short.json inherit proof-first constraints: hook by 2s, first demonstrative app phase by 3s, fix, payoff and final rule. All approval flags remain false.
2. On a disposable GitHub Ubuntu runner, free Xvfb, FFmpeg, LibreOffice Calc, python3-uno and Selenium operate actual GUI software using synthetic dummy data only.
3. The recorder waits for a genuine application before state, captures 10 seconds of 720x1280 desktop screen, performs the real action and checks the software's observed final state. FFmpeg checks H.264, complete decode and distinct source frames at 1s and 7s.
4. An 11-second 1080x1920 SILENT proof-first preview opens with actual result frames, followed by the original action clip. **Not publish-ready. No voice, audio, subtitles, final design approval, or release consent.**
5. A strict JSON receipt binds the exact source MP4, preview, app observation and optional real ODS file to SHA-256. Verifier rejects altered bytes, wrong mode, forged permissions, fake Chrome URL, wrong Calc evaluation and non-ODS worksheet.
6. PR QA runs without real GUI dependencies. A separate manual GitHub Actions main-only job actually records both applications, retains review media for 3 days, and destroys runner copies. No YouTube token, upload or schedule.

## Files

- autopilot/branch1_real_app_capture.py
- autopilot/test_branch1_real_app_capture.py
- content/recovery_pilot/real_calc_trim_short.json
- content/recovery_pilot/real_chrome_notifications_short.json
- .github/workflows/branch1-real-calc-chrome-demo-qa.yml

## Commands

Source-free unit QA: python -B -m unittest -v autopilot.test_branch1_real_app_capture

After actual GitHub main capture, independently verify a downloaded artifact with:
python -B -m autopilot.branch1_real_app_capture --app calc --verify --out /tmp/flowminute-actual-calc
python -B -m autopilot.branch1_real_app_capture --app chrome --verify --out /tmp/flowminute-actual-chrome

Keep exact private Studio metrics exports, media and account profiles out of public Git.

## Unfinished work

This is original, demonstrable software evidence only. Need visual review of output readability, a real narration/SRT integration, further purposeful edits, user-controlled factual/rights final signoff and age-matched real YouTube performance data. No claim of increased views, subscribers, or safe publication is made by successful software CI. Already scheduled videos through November 18 remain untouched. 
