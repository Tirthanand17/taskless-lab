# Branch 2 B4e4 — Owner media inspection and publish-release decision record

**Status:** review template only. No YouTube upload authority. Synthetic educational rehearsals are **NOT factual daily news**, even when all technical tests pass.

## Obtain and watch actual MP4s (manual, explicit opt-in)

1. In [GitHub Actions](https://github.com/Tirthanand17/taskless-lab/actions/workflows/flowminute-daily-cloud-foundation.yml), open **FlowMinute Daily Cloud Autopilot Foundation (NO PUBLISH)**.
2. Select **Run workflow** on **main** and opt in to **retain_rehearsal_review_artifact = true**. Default is false. This GitHub artifact is accessible to users with repo read access and expires after one day. Only use the currently synthetic, unapproved rehearsal assets.
3. After a successful run, download the `flowminute-UNAPPROVED-owner-review-...` artifact, extract, and **play all three MP4s with sound**. Record the workflow URL, commit SHA and media SHA256 values from the artifact manifest. A success badge/FFmpeg decode is **not** a substitute for watching.
4. If the manual run/export fails or has not been run, mark **NOT REVIEWED**, do not mark published or production-ready.

## Three-video audit sheet (copy one row for each film)

| Field | AM Short | Long video | PM Short |
| --- | --- | --- | --- |
| Workflow URL / commit SHA | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Filename / SHA256 match manifest | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Actual viewed duration; audio fully audible | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Hook in opening 2 seconds is specific and comprehensible | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Scene-by-scene novelty; no spinner/repetitive moving circle | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Clear spoken English, pronunciations, pacing, no clipped words | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Music/SFX levels do not mask speech; SFX licenses checked | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Readable subtitles, portrait/landscape safe margins, spelling | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Legible original diagrams on phone; no cut-off/tiny labels | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Logical narrative payoff and credible ending/CTA | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Copyright/voice/model/music/video asset rights evidence | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| External factual claims checked to primary sources | NOT REVIEWED | NOT REVIEWED | NOT REVIEWED |
| Overall owner decision | BLOCKED | BLOCKED | BLOCKED |

For each cell record **PASS / FAIL / NOT REVIEWED** with a timestamp (mm:ss) and one reproducible note. Do not change a cell to PASS without opening the exact MP4 corresponding to its SHA256.

## Separate factual and rights release gate (not satisfied by synthetic media)

A daily factual episode must have a fresh **source-to-claim ledger**: exact claim text, authoritative original source URL, publication/event time and timezone, independent corroborating source where needed, checked timestamp, evidence for visual/audio/voice licenses, and human editorial signoff. Any unsourced or contradictory material is a BLOCKER, not a candidate for automatic disclaimer-only publishing.

Never infer approval from source scraping, hash matching, technical video decoding, timing targets or synthetic demonstrations. Keep `fact_approved=false`, `rights_approved=false`, `owner_approved=false`, and `youtube_publish_enabled=false` until a **separately designed and authenticated** production release path is fully verified.

## Defect triage and release acceptance

- **P0:** unsourced fact, rights violation, wrong identity, potential privacy exposure, accidental public upload or credential exposure. Block all publishing; file an issue.
- **P1:** audio missing, clipped captions, recurring spinner, unreadable phone UI, timing failure, wrong aspect ratio or noticeably misleading visuals. Block the affected film.
- **P2:** cosmetic spacing, animation refinement, less engaging hook, voice cadence or optional background ambience. Improve then rerender and rewatch.
- Record issue URL, scene/timestamp, expected vs. observed behavior, media SHA256 and retest evidence; **never attach unapproved copyrighted/private media to a public issue**.

**Acceptance for this checkpoint:** a human opens all three actual MP4s, records pass/fail per item, opens actionable issues, and explicitly determines if a *new factual and rights-cleared content pipeline* should progress. This checklist changes no CI, protected IAM, credentials, cloud deployment or YouTube upload configuration. **Independent publishing remains unproven (0/21 seven-day release checks).**
