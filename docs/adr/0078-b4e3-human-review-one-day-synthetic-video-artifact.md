# ADR-0078 — B4e3 explicitly opted-in one-day original MP4 review package

**Date:** 2026-11-07 IST | Branch 2 | GitHub-only, no owner laptop or YouTube publishing.

## Verified baseline and update

Trusted main post-PR88 [workflow run 42325905744](https://github.com/Tirthanand17/taskless-lab/actions/runs/42325905744) physically generated, encoded and independently decoded all three original educational narrated media rehearsals (4-scene AM Short **57.831 sec**, 9-scene long **241.491 sec**, 4-scene PM Short **57.286 sec**). The tuned synthetic voice speed is now near 58/240/58. The 34 distinct original still/reveal diagrams, PCM-timed subtitles and no circular-spinner motion also passed automated media inspection. However, the workflow immediately and unconditionally deleted all unapproved MP4/WAV/SRT/PNG, leaving the owner with **no video file to watch** and no real human visual/audio QA. Technical decode is not human playback.

## Explicit-review-only artifacts

The existing daily workflow has a new **workflow_dispatch Boolean** `retain_rehearsal_review_artifact`, default **false**. Scheduled runs, branch pushes, and pull requests **can never upload video review files**. Only a human-started, **default-branch** GitHub workflow_dispatch with the Boolean intentionally set to **true** runs `autopilot.manual_rehearsal_review_export_b4e3` *after* all 17 scenes have actually been synthesized, compressed, decoded, duration-measured and verified.

The exporter verifies the exact B4e1 official unapproved media report's digest and numeric integrity for all 3 episode slots, target original scene counts [4,9,4], full real decoder success, one-shot visual checks, actual voice/caption evidence, and all rights, claims, human-watch and YouTube approvals explicitly **false**. It then reads exactly the three known local MP4 file paths, computes each full SHA256 and size before copying, comparing against the actual decoder evidence. It refuses symlinks and mismatches, more than 240MB per clip or 360MB aggregate, wrong source episode, extra file contamination, wrong root or existing review directory. A failure deletes partial copies.

When manually invoked, the **one-day GitHub Actions artifact** contains only:

- `01_MORNING_SHORT_UNAPPROVED_REHEARSAL.mp4`
- `02_LONG_VIDEO_UNAPPROVED_REHEARSAL.mp4`
- `03_EVENING_SHORT_UNAPPROVED_REHEARSAL.mp4`
- `REVIEW_ONLY_NO_PUBLISH.json` containing only safe numeric media durations, hash values and explicit zero approval flags
- `READ_ME_FIRST.txt` with a human review checklist and no publication authorization.

**Public repository warning:** A GitHub user with repository read access can download workflow artifacts. These are **not private**, even with the one-day retention. In the current project, the spoken contents are *original fictional/hypothetical educational rehearsals*, not scraped article wording or personal data. The package explicitly excludes publisher headlines, HTML, article passages, original unapproved source JSON, model weights, raw WAV, SRT, and private Google/YouTube tokens. The app does **not** make a public YouTube release, and the MANUAL media export toggle is strictly separate from factual/voice/licensing approval. The existing default daily run still retains only the two sanitized hash-only research JSON receipts.

The normal unconditional temporary file purges remain intact for both full video files and the new optional review package. One-day artifacts expire under the repository's effective retention settings; no indefinite storage is promised. The workflow has only GitHub `contents: read` and `actions: read` permissions (upload-artifact uses runner artifact credentials, not a repository write permission).

## How the owner uses it

On GitHub open **Actions → FlowMinute Daily Cloud Autopilot Foundation (NO PUBLISH) → Run workflow**, select **main**, set **retain_rehearsal_review_artifact = true**, run. After the exact same source-grounded research/storyboard/free CPU TTS/full media QA completes, the run's Artifacts area will contain `flowminute-UNAPPROVED-owner-review-<run_id>-<attempt>`. Download and watch all three MP4s. Check attention hooks, narration pronunciations, caption legibility/safe areas, human listening pace, scene design, source accuracy, source rights and any repeated looping visual. None of these subjective checks are automatically approved. After the 1-day retention, the package may disappear.

If any source/media stage fails, **no review upload** should take place. Never set this default to true or upload unreviewed output from `push` / `schedule` / `pull_request`. No owner-channel OAuth, automated publication, or paid provider call is added.

## Tests and live acceptance

A 12-case no-network adversarial suite tests exactly 3 physically copied hash-matched source files (using mock-media bytes and upstream decoder flag fixtures; it does **not** pretend mock bytes are videos), source/approval forgery, wrong root, symlinks, failed video cleanup, upload trigger/manual Boolean, and absence of extra publisher/audio/model artifacts. Four exact PR-head standard GitHub checks must pass before merge. Post-merge trusted push run must succeed **with manual review export NOT triggered**, proving no accidental video artifact retention.

**Limitations:** User explicitly controls if/when to run and download the additional one-day review artifact; this assistant's current Github connector does not expose a workflow_dispatch action. The new capability is built but not physically exercised in opted-in mode until the owner triggers it. Independent real owner watch and approved factual-news media/YouTube releases still stand at **0/21**.
