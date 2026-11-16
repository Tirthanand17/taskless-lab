# Branch 1 — real Studio video-aging analysis: 24h / 72h / 7 days

This closes a measurement-engineering gap: the earlier `autopilot.branch1_recovery` parser intentionally accepted **one** age-matched observation per video, so it could not track the same video across 24, 72 and 168 hours. The new `autopilot.branch1_age_matched_learning` separately supports **three snapshots for the exact same video** and rejects duplicates or inconsistent cohorts.

## Input is OWNER-curated genuine YouTube Studio data only

Never commit a raw YouTube Studio export, channel token, viewer record, email address, video ID or private dashboard screenshot into the public GitHub repo. The following is the exact header for an ephemeral, owner-curated CSV. The optional metric fields may be blank, but never fabricated or filled with zeros when unavailable.

`video_id,cohort,format,series,age_hours,duration_seconds,views,engaged_views,shown_in_feed,stayed_to_watch_pct,impressions,impressions_ctr_pct,average_view_duration_seconds,subscribers_gained,retention_3s_pct,retention_30s_pct`

- `video_id`: actual 11-character YouTube video identifier, **only** on private input, never in the report. It may appear once for 24h, once for 72h and once for 168h; the same identifier must remain in the same cohort, format, series and duration.
- `cohort`: exactly `baseline` (comparable pre-recovery videos) or `pilot` (owner-approved new recovery videos). These are descriptive groups, **not randomized experiments**.
- `format`: `short` or `long`. No cross-format comparison of CTR or Shorts "stayed to watch."
- `series`: use existing IDs `excel_sheets`, `privacy_browser` or `python_automation`; do not invent another audience category to make numbers look better.
- `age_hours`: 24 ±6h, 72 ±12h or 168 ±24h after first publication. All rows must be **cumulative since publishing** up to their reported age, not unrelated calendar-day averages.
- For Shorts, use Studio's *shown in feed* and *stayed to watch* when available. Do **not** estimate stayed-to-watch from video views or engaged views. Leave impressions and impression CTR blank for these rows.
- For long videos, provide genuine impressions, CTR, average view duration and 30-second retention. Leave Shorts-only fields blank. No unfounded claim that a high CTR is evidence of good retention.
- Views, engaged views, shown-in-feed, impressions and subscribers gained must not decrease as the **same** video ages through successive cumulative snapshots.
- Because YouTube's definition of views changed in 2026, use consistent-format, same-era comparison and interpret engaged views separately; 24h and 72h observations cannot prove causal improvement.

Run **only** on a secure ephemeral authorized machine/cloud with access to a privately curated CSV:

```sh
python -B -m autopilot.branch1_age_matched_learning --curated-csv /private/owner_studio_age_snapshots.csv > /private/age_matched_results.json
```

The output contains format/series/age/cohort aggregates, a weighted Shorts stayed-to-watch percentage or long-video impressions CTR, median viewing duration, optional 30-second retention and subscriber yield. It **never** writes video IDs or audience PII into the JSON output. Real audience metrics are **not yet available for the new recovery videos**, which remain unpublished. The tests use **strictly synthetic fixture numbers**.

## How a result becomes actionable

The program uses the existing conservative **internal** sample heuristics: at least five videos in **each** comparable group, 500 shown-in-feed and 100 engaged Shorts views (or 500 long impressions and 100 long views) to show a descriptive cohort difference. These are *not official YouTube algorithm thresholds*. Any smaller cohort reports `INSUFFICIENT_OR_INCOMPLETE_STUDIO_DATA`.

- The Shorts comparison uses the directly reported *stayed to watch* percentage, not thumbnail CTR. Its reading informs the first-second opening treatment.
- Long-form comparison prioritizes 30-second audience retention and checks average viewing duration separately; CTR belongs to packaging, not automatically a good watch experience.
- Do not recommend more uploads merely because the channel has few views; determine whether the first audience response and episode topic justify an additional test.
- Do not label an observational difference a winner, say all nine growth causes are fixed, or automatically publish.

## State of the actual pilot as of 16 November 2026

Two original narrated real-software Shorts are technically verified and hash-locked in `content/recovery_pilot/real_app_release_review_candidates.json` but lack exact owner release consent. A real 12-act Python CSV long-form experiment has a separate PR and physical workflow; its actual release still needs a full approved render and human watch. There are **zero** genuine postpublication 24h/72h/168h records for the new recovery assets. That is a *missing external observation*, not a code or calculation defect.

Official guidance checked Nov 16: YouTube measures **appeal, engagement and satisfaction**, not only upload frequency. YouTube's native A/B title/thumbnail testing is currently a **long-form** facility, not available for Shorts: https://support.google.com/youtube/answer/16559650 and https://support.google.com/youtube/answer/16391400. If eligible, test long-form packaging inside YouTube Studio rather than inventing simultaneous Shorts title A/B tests.

All file operations here are read-only to YouTube, and no paid tools, user laptop video folders, OAuth secrets or channel writes are used.
