# Branch 1 — Stop static real-app footage at the source (16 November 2026)

## Actual evidence, not a guess

The first two successfully encoded narrated Shorts from run [43726849969](https://github.com/Tirthanand17/taskless-lab/actions/runs/43726849969) **failed** the independent actual-pixel creative audit in [43811573881](https://github.com/Tirthanand17/taskless-lab/actions/runs/43811573881):

| Source app | Near-unchanged source application frame pairs | Longest near-frozen app region | Real UI pixel change in first 3s |
| --- | ---: | ---: | --- |
| Chrome Notifications | 90.6% | 15 seconds | No |
| LibreOffice Calc TRIM | 96.2% | 19.5 seconds | No |

That measured *rendered application pixels*, excluding moving subtitle/header areas. This is **not** YouTube retention data, and it cannot predict whether a future video goes viral. It does show that both outputs are unacceptable as viewer-first creative experiments. **Do not schedule or publish them.**

The root issue in `autopilot/branch1_narrated_real_app_short.py`: a 10-second actual recorded application scene was split into five chapter subclips totaling around 11.5 seconds of reused source windows. Narration lasts around 27 seconds. FFmpeg `tpad` clones the last genuine frame for the rest of the chapter. The resulting files were valid MP4/AAC but mostly static.

## New preventive integration

`autopilot/branch1_real_action_coverage_gate.py` evaluates actual chapter narration clocks against the genuine available application source window duration **before** it can produce another improperly stretched edit.

Internal edit heuristics (not YouTube metrics):

- At most **1.25 seconds** of cloned source footage per chapter.
- At most **25%** aggregate cloned source footage across the narrated Short.
- Valid, finite, bounded chapter clocks and actual footage windows.
- A report of minimum **genuine** screen recording seconds needed per chapter to replace cloned/held frames.
- All owner release/schedule flags explicitly false.

The previous 10-second pilot source must fail for its 27-second narration. A hypothetical future 5-chapter, 27-second genuine recording schedule can pass the **planning** check, but cannot be called real footage until an actual screen capture, hash binding and frame analysis also pass.

This guard is integrated directly into the visual FFmpeg graph constructor. Even if an engineer invokes the narrator rather than the separate independent audit, current under-recorded footage will now refuse to render. The independent actual-pixel audit remains a second post-render quality gate; numerical planning **does not replace physical video inspection**.

## Next implementation: genuine synchronized re-recording

1. Record a **new actual 25–35-second application session**, with first-party fabricated spreadsheet data or a throwaway isolated Chrome profile.
2. Perform real on-screen actions across the time the narration explains them. For Calc, move through the original comparison, show the hidden space and type/verify a `TRIM` formula in the real worksheet. For Chrome, move through real built-in settings pages and demonstrate where permissions reside, without changing user permissions.
3. Allocate genuine action windows to narrator-specific chapter durations. Do not insert fake product UI, manufacture login screens, add meaningless looping motion or pad ten seconds with 17 seconds of freeze.
4. Render from newly hashed source MP4 and real application observation, encode narrated H.264/AAC with accurate SRT/ASS captions and run both post-AAC and real application-pixel screening.
5. Full human viewing for facts, mobile readability, pronunciation, timing, rights and truthful product branding; owner must separately authorize any actual YouTube scheduling.
6. Only actual age-matched YouTube Studio observations after authorized publication can demonstrate improved stayed-to-watch, watch duration or subscribers.

## GitHub-only protections

- Existing schedule through November 18 is untouched.
- No personal data, credentials, third-party clips, paid tools or laptop media storage.
- All new CI uses fabricated source windows and original scripts.
- Passing source-level tests or even passing audio encoding **must never override** a failed real-pixel motion audit.

**Status:** current narrated media render = technically valid but **creative rejected**. Preventive source coverage gate = implemented and unit-tested. Next step = genuinely re-record longer application actions, not merely hide the static portions with decorative overlays.
