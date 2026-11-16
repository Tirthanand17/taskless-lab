# Branch 1 — physical-media gate per app (2026-11-16)

Main narrated run [43851422878](https://github.com/Tirthanand17/taskless-lab/actions/runs/43851422878) proved the new 780-row Chrome native Find capture and final narrated 20.542s H.264/AAC video encode. Chrome hash: `f944f208604f9b2e15964f296e01262742ffb38aee010716c7e5f5639bb1ef31`. The sister Calc job **failed strict post-AAC loudness** even after its permitted one remaster. This failure is a legitimate QA rejection, and *not* evidence that original media is absent or that any threshold should be relaxed.

The existing separate automatic `workflow_run` pixel audit in PR #262 triggers only after a successful *overall* narrated workflow. Because the other matrix job failed, Chrome's exact MP4 had no independent pixel verdict despite having physically rendered.

## Correction

A standalone per-app independent source-region pixel measurement is now run inside each exact-media job *after* its own hash-verified encoding. It produces the same `REAL_VISUAL_CREATIVE_REVIEW.json` and six actual phone-size frames using the unchanged existing independent `autopilot.branch1_short_motion_audit`. The same per-app short-lived GitHub artifact includes both exact MP4 and score before the final creative fail gate. One app's mastering failure does not suppress available verdicts on its successful sibling.

**Nothing here gives release approval.** Passing codec, pixel movement and signed hashes is not the same as independently listening to voice or confirming viewer value. Original Calc audio remains blocked until exact encoded loudness meets the existing strict bounds; never declare a passing clip by suppressing its mastering error.

After merge, run a new main-only review and inspect exact Chrome score even if Calc audio fails. All source and on-run checks operate on free GitHub-hosted ephemeral storage. No YouTube uploads, scheduling, Google account use, purchased software or user laptop media.
