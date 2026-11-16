# Branch 1 — Exact-video Chrome audit: blocked from release (2026-11-16)

## Evidence, verified from *actual encoded files*

- [PR #255](https://github.com/Tirthanand17/taskless-lab/pull/255): real Selenium radio interactions in a disposable Chrome profile (no user settings changed).
- [PR #256](https://github.com/Tirthanand17/taskless-lab/pull/256): expose early actual application worker failures rather than an opaque parent exception.
- [PR #258](https://github.com/Tirthanand17/taskless-lab/pull/258): wait for Chrome's real asynchronously loaded selected notification option. The full main-only [source capture run #43840144086](https://github.com/Tirthanand17/taskless-lab/actions/runs/43840144086) successfully captured Chrome and Calc.
- [Narrated physical media run #43840551562](https://github.com/Tirthanand17/taskless-lab/actions/runs/43840551562) successfully encoded, decoded and checksum-verified both 1080×1920 H264/AAC MP4 files; Chrome **33.007 seconds**, SHA256 `ebfd874cd30ad8908d2693e1cbd46e52e9f464df81a688808d490902fce51a23`; Calc **26.542 seconds**, SHA256 `d453c581abfaf795908ca79b973085d0a920c9c6b4a7d8953901840368035680`. Both remain **UNAPPROVED** and review only.
- [Independent exact-video audit #43840999906](https://github.com/Tirthanand17/taskless-lab/actions/runs/43840999906): **Calc PASS**, 44.2% near-static central app pixel-pairs; **Chrome FAIL**, 81.5% near-static central app pixel-pairs, **11.5-second** maximum near-frozen interval, despite real visual change in first three seconds. Strict creative-motion threshold unchanged.
- Contact frames and the real **33-second Chrome MP4** from the GitHub review artifact were inspected at phone scale. The video uses actual Chrome pages, but the main Notifications page is repeatedly nearly identical. A real radio-button selection moves only a tiny fraction of visible pixels. From about 25s to the end, the same blocked screen remains while narration explains the throwaway profile. Chrome text is also small at phone size with large empty areas. These are **creative failures** even though genuine browser interaction and media codecs work.
- `content/recovery_pilot/real_chrome_notifications_short.json` and the Calc pilot JSON specify an **11-second editorial concept**, while the real outputs are **33.007s and 26.542s**, respectively. This is not necessarily a technical codec error, but it is a serious **editorial planning/actual-length mismatch** that must be reconciled before any release approval.

## Safe next iteration — optimize for the viewer, not motion metric

1. **Remove duplicate/static tail**. Rewrite the tutorial as one concise problem → native Settings route → actual Block click → visually meaningful persisted result, and integrate the disposable-profile caveat without another long unchanged screen. A concrete first-party action must be visible while each instructional claim is heard.
2. **Use authentic Chrome UI only** on the disposable GitHub runner. Testing a more readable native browser scale or a real settings detail expansion is permitted as an experiment; never fabricate UI, synthetic success, fake cursor movement, unrelated scrolling, or a settings-page flip loop solely to improve pixel percentages.
3. **Synchronize spoken sentences with real route events**, reduce excess speech, and have the production duration derived from the actual voice and source windows. The 11s pilot brief is **not** the narrated Short duration. Add a fail-closed release/readiness consistency check rather than misreporting runtime.
4. **Inspect complete phone-resolution video and audio**, with legible native labels and no clipped notification text, then create genuinely new media on main and rerun the unchanged independent exact-video pixel gate. A pass is only *technical*; human full watch/listen, facts/rights verification, and explicit final owner decision remain separate.
5. Only after authentic, useful content passes all creative/technical reviews should any owner-approved YouTube scheduling be discussed.

## Release matrix

| Candidate | First-party capture | Narrated H264/AAC | Actual central-app pixel QA | Human full watch/rights | YouTube |
|---|---|---|---|---|---|
| Calc TRIM | PASS | PASS, 26.542s | PASS, 44.2% near-static | Not approved | Zero uploads/schedules |
| Chrome notifications | PASS | PASS, 33.007s | **FAIL**, 81.5% near-static, 11.5s freeze | Not approved | Zero uploads/schedules |

**No purchases, no personal browser/profile, no local laptop media storage, no YouTube uploads or schedules, no changed pixel thresholds, and no creator rights assertion.** Engineering provenance is not demonstrated audience retention or virality.