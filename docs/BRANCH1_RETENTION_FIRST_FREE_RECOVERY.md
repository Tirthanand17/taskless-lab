# FlowMinute Lab — Branch 1 free-first viewer-retention recovery

**Decision: engineering only. No new YouTube uploads, schedule changes, purchases or owner release approvals.** Existing scheduled videos through November 18, 2026 are not modified.

## Why this changes

The signed-in channel's October/November Studio audit reported **21.2% Shorts stayed to watch**, **78.8% swiped away**, **58 seconds average long-video view duration**, **4.8% video-only CTR** and zero subscribers gained during the 28-day window. This is observational channel performance, not an experiment or a prediction.

The earlier Branch 1 renderer has fixed five-act Shorts/twelve-act long videos, illustration-based software interfaces and safe encoding. Its checks validate media mechanics, not viewer satisfaction or actual product demonstrations. Keep that already-scheduled work unchanged. New *future* content should prove the payoff, demonstrate genuine software work and pass a creative review before publishing.

Official YouTube references (reviewed November 2026):
- Viewer appeal, engagement and satisfaction: https://support.google.com/youtube/answer/16559650
- Shorts and video analytics definitions: https://support.google.com/youtube/answer/12220281
- Audience quality over publishing frequency: https://support.google.com/youtube/answer/16533387
- Inauthentic/repetitive content monetization: https://support.google.com/youtube/answer/1311392

## A. Proof-first creative quality validator

**autopilot/branch1_recovery.py** rejects a future creative brief unless:
1. The *actual software outcome or problem* is on screen by 2 seconds; no brand-first intro.
2. The first real app action begins by 3 seconds.
3. A demonstrated fix precedes the visible payoff, which starts before 85% of total runtime.
4. A meaningful takeaway ends the story. Narrative beat count may vary from 4 to 12 rather than forcing identical formats.
5. Every beat's intended footage is an actual executed-software frame, not a fake application screenshot labeled as real.
6. All release and rights approvals remain false, with zero YouTube mutation.

These checks validate a **creative proposal**, not whether an actual audience likes the result. Independent human watching is still required; no software here guarantees retention or monetization.

Example:
python -B -m autopilot.branch1_recovery --creative content/recovery_pilot/real_csv_proof_first_short.json

## B. Genuine, first-party software capture

**autopilot/branch1_record_real_demo.py** uses free Linux software on a disposable GitHub runner: Python, Xvfb, XTerm and FFmpeg.

It writes an original, completely fictional four-row CSV, executes actual Python data-cleaning code in a real terminal, verifies that the resulting CSV contains three unique invoices, and screen-records the running program to H.264 MP4. No simulated screenshot, customer data, account login, external media or third-party channel content is used.

A separate 11-second **silent review-only proof-first preview** starts with the recorded outcome, then replays the real action. The capture and preview are SHA-256 bound, verified by full decoding, and kept as temporary GitHub Actions artifacts for three days. None of these files is publish-ready: there is no approved narration, rights sign-off, final watch or YouTube publishing step.

This validates a *real Python terminal workflow* only. It is not proof of a real Gmail or Excel demonstration. Actual Excel/browser app adapters can be added later under the same source, rights and media-check boundary.

To check a real capture file and its exact receipt after a successful review run:
python -B -m autopilot.branch1_recovery --creative content/recovery_pilot/real_csv_proof_first_short.json --capture /tmp/ACTUAL_PYTHON_TERMINAL_CAPTURE.mp4 --capture-receipt /tmp/EXACT_REAL_CAPTURE_UNAPPROVED.json

SHA equality proves file identity, **not** pedagogical value. The runner separately requires that the recording is valid H.264 and fully decodes.

## C. Privacy-safe Studio analytics scorecard

**parse_metrics_csv** accepts a strict, curated CSV with exactly these columns:

video_id,format,series,age_hours,duration_seconds,views,engaged_views,shown_in_feed,stayed_to_watch_pct,impressions,impressions_ctr_pct,average_view_duration_seconds,subscribers_gained,retention_3s_pct,retention_30s_pct

Studio exports can have differing headers and definitions; manually curate numeric metrics rather than claiming that any raw export will work directly. Percentages are from 0 to 100. Missing metrics must be left blank, not zero or fabricated. Never estimate stayed-to-watch as engaged_views divided by views.

Example, using a LOCAL private file, never committed:
python -B -m autopilot.branch1_recovery --studio-csv /tmp/curated_youtube_studio_72h.csv

Analysis is **read-only** and outputs only aggregates by format and series, not video IDs, titles, messages or viewer data. It compares age-matched videos at 60–84 hours after publication. Eligibility requires five age-matched videos and a meaningful sample: for Shorts, at least 500 shown in feed and 100 engaged views; for long videos, at least 500 impressions and 100 views. These are internal experiment heuristics, not YouTube algorithm thresholds. There are no claims of statistical significance or causal effects.

Do not commit private Studio exports or credentials to this public repository. The test suite uses fabricated numeric rows only, and rejects any extra columns that could carry personal data.

## D. Nonpublishing GitHub QA

Workflow: **.github/workflows/branch1-retention-first-free-recovery-qa.yml**

- On PR: validate code, proof-first storyboard, actual fake-data Python execution, fail-closed creative policy, percent range, sample sizes, format separation and private-column rejection. No purchases or YouTube tokens.
- When manually dispatched **on main only**: run actual Xvfb/XTerm screen recording, verify synthetic input/output data and H.264 files, write exact SHA receipts, create a brief silent proof-first review edit and upload three-day GitHub artifacts. Clean runner files.
- No YouTube insert, scheduling, publishAt, OAuth, private upload or laptop media storage.
- Existing scheduled November 14–18 videos remain untouched. A green GitHub check is NOT a creator approval or YouTube schedule.

## E. Proposed viewer-first trial, not a release instruction

Create four genuinely demonstrative Shorts in one Excel/data series and four in a privacy/browser series, with one explanatory long tutorial for each. Compare only similar formats, comparable ages and meaningful cohort sizes. Show the problem/result instantly, record real software with first-party dummy data, keep cuts purposeful, ensure subtitles and narration match actual evidence, and use a compelling but truthful title.

At review, examine the first 3 seconds and the demonstrated payoff; reject filler and misleading app mocks. Then track stayed-to-watch, engaged views, percentage viewed, viewing duration, impressions, CTR, returning audience and subscriber yield separately. The 21.2% and 58-second channel readings are reference observations, not universal ranking thresholds.

**Next still required:** validate the main-branch authentic capture job on a GitHub runner; integrate actual footage with a fully narrated, manual-reviewed video; add specific Excel/Chrome demo capture adapters; privately acquire accurate 72h Studio CSV metrics for the experiment; and receive owner final release approval. This PR does not do any of those actions automatically.
