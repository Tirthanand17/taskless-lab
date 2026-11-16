# FlowMinute Lab — audience-first growth recovery, not more blind uploads

**Updated November 16, 2026.** Scope: **FlowMinute Lab** (`@flowminutelab`), not the separate CLIVOX channel or recycled third-party clips. This is a measurable intervention plan, **not** a claim of guaranteed subscribers or views.

## Current verified baseline / blockers

- Connected vidIQ **free channel snapshot**: **92 public videos**, **5 subscribers**, **1,949 lifetime views**. This is cumulative context, NOT the 28-day trend, impressions, stayed-to-watch, session retention or meaningful growth rate. Do not divide lifetime totals into fake recent rates.
- Older authenticated review found **21.2% Shorts stayed to watch**, **58s long average duration**, **4.8% long impressions CTR**, **2.3% Suggested traffic**, and **zero subscriber gains** in its previous cohort. Different age windows/series make these observational historical references only.
- Direct Google YouTube API owner audit [#43896534947](https://github.com/Tirthanand17/taskless-lab/actions/runs/43896534947) was blocked by **OAUTH_REFRESH_FAILED**. This remains the release/authenticated Studio inventory blocker. Do not copy OAuth JSON into GitHub source, browser chat, public documents or logs.
- Connected vidIQ has **zero credit balance**, reported refill on **December 2, 2026**. Do not purchase credits to replace authentic Studio observations. Connected Metricool account has **no YouTube social account connected**, so Metricool cannot provide this channel's real Studio metrics yet.
- New real-pixel video engineering passed: original Python CSV long and Calc TRIM Short. The long exact MP4 and timed SRT are preserved in [private GitHub artifact #14240127005](https://github.com/Tirthanand17/taskless-lab/actions/runs/43898583072/artifacts/14240127005) until **December 16, 2026**. The earlier Chrome Find-in-Log Short has a different viewer intent and is **out of the first cohort**. Technical QA is not an audience outcome.
- Owner's chat approval applied to the one long Python video, not a replacement media hash or all Shorts. Private Studio slot reconciliation, independently signed exact rights/facts/captions release and protected OAuth access must precede uploading.

## Hard decisions that stop repeating previous failures

**Audience:** beginner English learners fixing spreadsheet/CSV data errors. Do not interleave unrelated Chrome privacy, AI hype, productivity facts and gaming in this first pilot; they confuse who should come back for the next episode.

**Promise:** one real problem and one verified solution in every video. Open on true executed evidence in the first 2 seconds of a Short, or as early as possible in the long video. Never play generic animated logos, decorative circles, synthetic before/after UIs, fake recordings, or copy other creators' videos.

**Niche-first release order:** one approved original Python CSV long, plus the separately reviewed Calc TRIM Short *only after its own owner approval*. Hold the Chrome Find pilot until a consistent data-workflow audience emerges. Do not automatically resume two Shorts and one long every day while performance is unmeasured.

**Long-form packaging, after verified future release:** original 3:35 video title: “Why Your CSV Total Is Wrong: 3 Data-Cleaning Bugs in Python.” Thumbnail proof from an actual recorded terminal frame showing the **fictional** $2,656.25 → $1,430.75 correction. Other truthful title options for *eligible, public, native Studio A/B experiments only*:
1. “Fix Wrong CSV Totals in Python: Spaces, Duplicates & Decimal”
2. “CSV Total Doesn't Match? Find 3 Python Data-Cleaning Errors”

Do not schedule an A/B test for private uploads, nor for Shorts. Current official native YouTube A/B allows up to three combinations on eligible long-form videos; it optimizes for watch-time contribution, not a universal CTR threshold: https://support.google.com/youtube/answer/16391400

**Series reason to subscribe:** “Real Data Fixes — one actual spreadsheet or CSV problem solved in each lesson.” Use a brief, honest related next-step promise in future owned content after showing the real payoff. Not a generic subscribe plea in the opening.

## Obtain authoritative private Studio evidence

Use YouTube Studio **Analytics / Insights** (UI varies during the 2026 rollout) → Content and the particular video's Reach/Engagement/Audience reports; in Advanced Mode export owner-verified CSV. Documentation: https://support.google.com/youtube/answer/9002587

Never commit raw Studio CSV, YouTube OAuth JSON, unpublished titles, private video IDs, unique viewer demographics, or owner emails into GitHub. Create a private local transient CSV with the *exact header* in [`content/recovery_pilot/studio_24_72_168_blank_template.csv`](../content/recovery_pilot/studio_24_72_168_blank_template.csv), containing only non-PII age-matched aggregate data. For traffic mix use [`content/recovery_pilot/traffic_sources_blank_template.csv`](../content/recovery_pilot/traffic_sources_blank_template.csv). **These files contain NO actual metrics and are NOT data evidence.** The populated private CSV must stay outside the repo.

Minimum fields:
- **Short**: actual video ID (used only transiently), cohort baseline/pilot, age 24h/72h/168h, format+series, views, engaged views, shown in feed, directly observed stayed-to-watch%, 3s retention and subscriber gains. Do **not** derive stayed-to-watch from views.
- **Long**: own impressions, CTR, 30s retention, average view duration, views, engaged views and real subscriber gains. Do **not** compare a Short’s feed viewed percentage to long-form CTR.
- **Traffic**: actual baseline and recovery source totals from Suggested, Browse, Search, Shorts Feed, External and other. Total must match sources. Low Suggested share does not prove a shadowban.

Check the *same video* at the closest permitted age windows: 24±6h, 72±12h, 168±24h. The underlying `autopilot.branch1_age_matched_learning` prevents counting one video's 3 snapshots as 3 separate uploads, and rejects contradictory cumulative totals.

## One command: translate real evidence into grounded next actions

Without any data, get an honest missing-evidence checklist:

```bash
python -B -m autopilot.branch1_growth_action_engine
```

With **privately curated owner Studio exports only** (do not run in a public PR, issue or Actions log):

```bash
python -B -m autopilot.branch1_growth_action_engine \
  --curated-csv /private/studio_24_72_168.csv \
  --traffic-csv /private/traffic_sources.csv
```

It will recommend a *new* genuine Short’s first-two-second correction only when own 72h age-matched chose-to-watch underperforms same-format same-series baseline, a new long’s 0–30s edit if early retention declines, truthful title/cover changes if eligible long-format CTR is weaker, subscriber-return promise if engaged viewers do not subscribe, and a recommendation-source investigation when matching source shares fall. It will **not** infer any growth win from tiny samples, suggest buying fake engagement, claim shadowbans, upload videos, publish Studio data, or relabel an existing clip as newly approved.

The current sample contract requires **at least five independent videos and adequate authentic same-format feed exposures/impressions in BOTH comparable cohorts** before even a descriptive comparison. This is an internal conservative analysis policy, not a YouTube ranking rule, and observational performance is not causal proof.

## 14-day editorial intervention outline — not a calendar of scheduled uploads

**Days 1–2:** Reauthorize YouTube owner OAuth securely, verify full current upload/schedule inventory and any restrictions. Have the exact long video rights/caption/fact package signed via the existing independent owner process; determine one future collision-free slot. No blind old-video deletion, no mass rescheduling.

**Days 3–7:** If cleared, publish only the approved genuine long tutorial. Collect real 24h and 72h metrics. Manually inspect precise first-30s drop-offs, traffic-source splits, and comments suggesting confusion. Do not change many variables at once.

**Days 8–10:** Separately review/approve the original Calc TRIM Short; release only if coherent with the same learning audience. Teach the next most-requested data error (e.g., real duplicate normalization or date parsing) in new footage rather than repeating earlier thumbnails or animations.

**Days 11–14:** Examine actual seven-day data. Run the read-only action engine; if underpowered, label results **inconclusive** and extend the coherent cohort. If sufficient, make one evidence-directed next production change (hook first, or 30s pacing, or truthful packaging), then monitor the next comparable release. Do not reset the audience topic every day.

## What would count as growth recovery?

**Not:** 3 rendered MP4s, a codec pass, 92 video uploads, one higher public view count, a higher artificial motion percentage, or a synthetic sample in unit tests.

**Yes, gradually:** matched-format, same-age published-viewer evidence that Shorts feed audiences *choose to watch* more and stay, long-form first-30s retention and average duration improve, Suggested/Browse qualified viewing improves, returning viewers emerge and real subscribers convert. No guarantee of virality or a fixed schedule for algorithm distribution.

**External blocking action:** Owner reauthorization and exact-file signed publishing flow remain required. After approved publication, private Studio exports or a newly connected authorized analytics source are needed to prove results. This plan does not falsely mark the nine original problems all solved.
