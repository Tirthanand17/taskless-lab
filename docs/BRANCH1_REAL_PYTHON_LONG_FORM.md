# Branch 1 — real first-party long-form data-cleaning pilot

**Intent:** address the *missing long-form creative format* without recycling 2 Shorts into a padded slideshow or pretending source-code QA proves viewers will watch for longer.

**Asset:** `fm_real_python_csv_three_bugs_long_en`, 12 linked educational acts in a continuous real Python XTerm data investigation: hidden string whitespace, duplicate invoice keys and parsing comma-formatted amounts with `decimal.Decimal`.

## Truthful fictional exercise and expected answers

The ephemeral runner creates `source_fictional.csv` with eight invented invoice records, two duplicate records after trimming, and one whitespace-padded identifier. All eight amounts sum to **$2,656.25** if duplicates are incorrectly counted. Reading, normalizing, deduplicating with matched amounts/status, and computing with Decimal yields **six invoices and $1,430.75**, a **$1,225.50** difference.

All values are computed by the actual Python source in `autopilot/branch1_real_csv_long.py`. The script refuses inconsistent duplicate amounts or malformed identifiers; it never silently invents money totals. The source CSV remains untouched. Chapter 11 physically writes and reopens `clean_fictional.csv` and rechecks both rows and totals.

The live desktop footage is a genuine XTerm running the Python software on this data, not a fabricated product interface, vendor screenshot, AI illustration or third-party video. Its 12 chapters are recorded on an ephemeral GitHub Xvfb session. The first 3 seconds show real proof and a second real live calculation, with no brand-first interstitial. Original Kokoro TTS provides 12 narrative sections and source-timed captions; actual voice length governs the real terminal recording, rather than looping frozen frames to meet a guessed runtime.

## QA and release boundary

- On PR, only source code and adversarial tests run. They check exact Decimal arithmetic, duplicates, saved-file reimport, the specific single-problem story, malformed source rejection and the no-local/no-YouTube boundary. Source-only CI is *not* a physically rendered video.
- A manual dispatch to [`.github/workflows/branch1-real-python-long-review.yml`](../.github/workflows/branch1-real-python-long-review.yml) on `main` records real app pixels, synthesizes original narration, encodes H.264/AAC 1920×1080 long-form, verifies final encoded AAC against the existing strict internal LUFS/true-peak bands, and produces bounded SHA-linked original files.
- An independent landscape real-XTerm source-region temporal audit detects long static sections; it does not mistake speech subtitle movements for meaningful changes in the live app. Six *actual* decoded 16:9 phone-preview frames are archived alongside the final review MP4 for 3 days. Any source or media failure blocks export.
- Owner must watch/listen end-to-end on a real phone, verify step accuracy and creative watchability, approve exact hash and original rights, and explicitly authorize release. **None of this code authorizes uploads, schedules, titles, badges claiming viral status or OAuth access.**
- The genuine 12-act long educational problem is still an *experimental candidate*. It does not repair the historical long average view duration of 58 seconds until a controlled, age-matched, actually published Studio cohort has adequate audience viewing/30s retention data.

## Proposed nonpublished packaging

- Title: **Why Your CSV Total Is Wrong: 3 Data-Cleaning Bugs in Python**
- Audience problem: raw invoice files may overcount due to duplicate keys and hidden spaces, and money strings need exact parsing
- Honest promise: run original Python on a fictional local file; catch three data errors and prove before/after totals
- Cover from exact executed program frame: incorrect **$2,656.25** versus corrected **$1,430.75**, clearly labeled fictional data. No simulated terminal frame or fabricated vendor UI.
- Captions: original source-timed narration. Do not assert all duplicate invoice IDs are invalid in real business systems; the example verifies duplicate amounts/status exactly.
- End prompt: ask viewers whether they want an authentic follow-up on missing dates or double-counted pivot-table records.

## Independent audience validation after approval

- Pair this with the existing two real Shorts under the **Real Data Fixes** series (not a promise of a true randomized A/B test).
- Do not publish the historical high-volume 2 Shorts/1 Long daily quota automatically. Owner signoff and live schedule duplicate checks are mandatory.
- At 24h/72h/7d, inspect long-video 30-second retention, avg view duration, total qualified watch time, impressions and CTR as distinct metrics; keep Shorts feed swipe metrics entirely separate.
- Current status is **review-only, no YouTube uploads, zero release approvals**. The channel's public count and old analytics observations are not a growth guarantee. Free-first engineering; no local laptop storage.
