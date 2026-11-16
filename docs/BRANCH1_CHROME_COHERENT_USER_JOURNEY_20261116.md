# Branch 1 — Chrome notification tutorial: useful route, not page-flip motion

## Actual visual review finding

The source-linked narrated Chrome Shorts in render runs [43827319760](https://github.com/Tirthanand17/taskless-lab/actions/runs/43827319760) and [43831559819](https://github.com/Tirthanand17/taskless-lab/actions/runs/43831559819) passed technical validation and the separate pixel-motion gate. Actual extracted mobile review frames show the browser **repeatedly jumps between Site settings and Notifications**, often without showing any clicking or sustained explanation of the controls. The existing code performs **30 browser navigations** across 5 chapters primarily to generate screen changes. A high motion score is not equivalent to a useful tutorial and is not evidence of improved YouTube distribution.

The same frame review confirmed that PR #253 repaired most lost left-edge Chrome labels, but the **semantic navigation defect remains**. This is the last major first-party browser creative issue before a human final-watch evaluation.

## Corrective implementation

- Replace the 30 page-jump commands with **one intended forward browser route**:
  1. Proof-first look at the actual `chrome://settings/content/notifications` screen in an isolated temporary profile.
  2. Show `chrome://settings/`, followed by `chrome://settings/privacy` and `chrome://settings/content` in user-facing sequence.
  3. Review built-in permissions on the **Site settings** page.
  4. Navigate to `chrome://settings/content/notifications` only once.
  5. Review the actual notification defaults and any present allow/block lists without selecting or changing a radio button.
- Use **real browser scrolling** on those exact Chrome settings screens to reveal contextual controls within each chapter; never fabricate an interface, add fake browser elements or toggle notification permissions. Each page change has a narrative reason.
- The Chrome worker verifies the observed route history equals the one-way path and refuses if Chrome leaves its internal settings.
- Original voiceover teaches *Settings → Privacy and security → Site settings → Notifications*, rather than saying only that controls are nested. It says that no permissions are changed.
- Existing first-party captured original media, no-account protections, SHA receipt, source-synchronized audio, captions, AAC mastering, strict pixel-motion gate and unapproved state remain unchanged.
- Tests verify the unique one-way routes, 5×6 genuine story actions, allowed browser internal operations only and narration claims.

## Hard tradeoff

With fewer abrupt full-page changes, the conservative **45% central-pixel stillness heuristic may fail**. That is not a reason to add meaningless page flicker or quietly lower thresholds. We must inspect the exact new mobile frames and use a human review to determine whether the intended action sequence is actually understandable. If the motion audit fails, keep this video blocked and improve real Chrome UI scrolling and click-based navigation rather than gaming the metric.

**No paid tools, no user data, no personal browser profile, no YouTube upload or schedule, no rights approval.** The older published/scheduled videos are untouched. This workflow remains a review-only proof of concept until the final human full-watch and authorized release.
