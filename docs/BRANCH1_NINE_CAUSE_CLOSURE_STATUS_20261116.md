# Branch 1 — the nine low-view reasons: evidence gate (2026-11-16)

The target is returning viewers, qualified watch time and subscriber conversion, **not a count of AI-generated uploads**. This is an operational diagnostic for the original nine reasons. It does not certify their resolution.

## What can be verified now

- Real-app capture, H.264/AAC source checks, source hash receipts, actual-pixel motion checks, and fail-closed release safeguards are implemented. See PR #260.
- Source-only unit tests confirm controls are present. A successful source-only test is **not** a successful watched video, a public upload or an improvement in viewers.
- The last real exact-media audit #43840999906 passed Calc at 44.2% near-static app pixels and rejected Chrome at 81.5%, longest near-freeze 11.5s. A new main-only narrated run is required before deciding whether the shorter Chrome storyboard works.
- Historic Studio observation: 21.2% Shorts stayed to watch, 58s long average duration and 4.8% long-video-only CTR. These are reference observations, **not** universal YouTube thresholds.
- Private Studio 24/72-hour/7-day results for newly approved recovery content are not available. No engineering artifact can supply them.

## Nine causes and closure evidence

| Cause | Engineering response | Required real proof before declaring improvement |
|---|---|---|
| 1. Poor Shorts initial appeal | Result-first hook validator and real application opening | Age-matched Shorts feed shown, stayed-to-watch and first seconds retention |
| 2. Low long-form retention | Proof-first long storyboard rules and human edit gate | Long 30s retention, avg view duration and watchtime from impressions |
| 3. Weak Suggested/Browse reach | Traffic-source-specific, anonymous Studio analysis | Matched baseline and recovery Suggested/Browse/Search traffic cohorts |
| 4. No subscriber conversion | Audience metric rollups and viewer-value promise | Subscribers gained per qualified engaged view, then repeat observations |
| 5. Mixed niche and language | Focused Excel/data and Chrome/privacy experiment series | Returning-viewer and topic/language data from comparable cohorts |
| 6. Repetitive circular visuals | Physical real-app recording, no-loop policy, independent source-pixel QA | Pass actual final MP4 + full phone-size human inspection |
| 7. Fake-looking demonstrations | Genuine first-party app execution with fixture data | Viewers see understandable real result and facts/voice are reviewed |
| 8. Uploading quantity over quality | Fail-closed no-publish workflows and sample-size guards | New releases pass review; 24/72-hour/7-day learning actually changes future production |
| 9. Weak packaging | Short first-frame, long thumbnail/title review playbook | Long thumbnail impression CTR paired with the promised video retention |

No result above is declared permanently fixed. Thumbnail CTR alone does not prove poor packaging; suggested traffic alone does not diagnose an algorithm penalty. There is no verified shadowban.

## Offline Studio diagnostics (no paid tools, no secrets)

Use a private **curated** file, never a raw Studio export committed to GitHub. The existing `autopilot.branch1_recovery` command accepts:

`video_id,format,series,age_hours,duration_seconds,views,engaged_views,shown_in_feed,stayed_to_watch_pct,impressions,impressions_ctr_pct,average_view_duration_seconds,subscribers_gained,retention_3s_pct,retention_30s_pct`

Source-share export is **optional** and must have exactly:

`period,format,views,suggested_views,search_views,browse_views,shorts_feed_views,external_views,other_views`

Use only manually verified, anonymous aggregates for comparable 60–84-hour video-age cohorts, with every view assigned to exactly one source category (use other_views for the remainder). Never calculate Shorts stayed-to-watch from ordinary views or engaged views; it must come directly from Studio. If the fields cannot be mapped without ambiguity, leave the traffic dataset unavailable instead of manufacturing shares.

Run on a secure, ephemeral authorized environment:

```sh
python -B -m autopilot.branch1_nine_cause_diagnosis --studio-csv /private/curated_studio.csv --traffic-csv /private/curated_traffic.csv
```

The output deliberately contains **no video IDs, private audience identifiers, email addresses, claimed cures or upload authorization**. It labels improvements only as `DESCRIPTIVE_SIGNAL_ONLY`, and leaves unsampled causes as `NEEDS_REAL_AUDIENCE_EVIDENCE`. It permanently returns `automatic_publishing_approved=false`, `proven_fixed_count=0` because that decision needs actual human and real-world validation.

## Next release boundary

1. Complete the shorter Chrome physical render and run the *independent exact-file* pixel audit unchanged.
2. Watch and listen to the entire finished Chrome and Calc videos on a phone-size screen; check genuine action timing, readability and correct software claims.
3. Approve exact factual, original, accessible assets. Only separately authorized YouTube releases may enter a small controlled one-series experiment, not a 3/day quota.
4. Gather qualified post-publication Studio readings at about 24h, 72h and seven days, compare same ages and formats, deliberately change one factor per test.
5. Never mark any of the nine audience-performance causes solved based on source code or internal FFmpeg QA alone.

**Scope: GitHub-only engineering and private read-only metrics. No YouTube writes, no paid tools, no creator clip reuse, no personal browser modification.**
