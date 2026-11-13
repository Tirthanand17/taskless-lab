# CLIVOX A10 — actual owner-authorized read-only Analytics adapter

**Code and GitHub environment implemented:** 2026-11-13. **Live Google connection has not happened.** There are no Clivox uploads, authenticated channel metrics or optimization conclusions yet. The prior A10 synthetic data stays synthetic.

## What exists

- `scripts/branch3_a10_owner_readonly.py`: a separately protected three-request-only read: (1) OAuth refresh, (2) `channels.list(mine=true)` on the **exact CLIVOX brand channel**, (3) `YouTube Analytics reports.query` for a bounded nonmonetary video sample. The script never executes a Google upload/edit/delete, download, schedule or Google Analytics write.
- `.github/workflows/branch3-clivox-a10-owner-readonly.yml`: manual dispatch **only from public-controller `main` by the repository owner**, first attempt only; uses a newly created `clivox-analytics-readonly` environment with a verified owner reviewer, `main` deployment restriction and disabled administrator bypass. **This environment currently contains 0 secrets.**
- `scripts/test_branch3_a10_owner_readonly.py` and `.github/workflows/branch3-clivox-a10-owner-readonly-qa.yml`: synthetic Google responses and adversarial tests, no real OAuth or video IDs, no protected PR secrets.
- Existing `scripts/branch3_a10_analytics.py` + `branch3/a10/analytics-policy.json` remain a completely independent **synthetic-only** data validation/experiment demonstration. Do not change their test data into real metrics.

## OAuth requirements — strictly separate from Clivox upload

Current official references:
- [YouTube Analytics Reports Query](https://developers.google.com/youtube/analytics/reference/reports/query) — `GET https://youtubeanalytics.googleapis.com/v2/reports` with `ids=channel==MINE`, date range, metrics and dimensions. Google currently says this method also requires `youtube.readonly` access.
- [Authorization scopes for YouTube Analytics](https://developers.google.com/youtube/reporting/guides/authorization) — `yt-analytics.readonly` is the separate nonmonetary analytics reporting scope.
- [YouTube Analytics metrics](https://developers.google.com/youtube/analytics/metrics) — `views`, `engagedViews`, `averageViewDuration`, `averageViewPercentage`, `shares`, `subscribersGained` are defined metrics. Availability/lag can vary.
- [YouTube Analytics dimensions](https://developers.google.com/youtube/analytics/dimensions) — `video` is a per-video dimension.

The adapter **requires both and only these two OAuth scopes**, verified from refresh response:

`https://www.googleapis.com/auth/youtube.readonly`

`https://www.googleapis.com/auth/yt-analytics.readonly`

It **rejects** `youtube.upload`, `youtube`, `youtube.force-ssl`, monetary analytics or any additional scope. No Clivox publishing token can be reused as Analytics. Absolutely no FlowMinute credentials can be reused.

## Owner setup (not performed by this PR)

1. Independently register/review the correct Google Cloud project and OAuth application. The actual Clivox owner must sign in, **explicitly select Clivox, not FlowMinute**, and grant exactly the two read-only scopes. Consent, Google quota, Google Cloud project verification and privacy requirements remain the owner's responsibility.
2. Inside the existing protected GitHub environment `clivox-analytics-readonly`, configure **four environment secrets only after scope review**: `CLIVOX_A10_ANALYTICS_CLIENT_ID`, `CLIVOX_A10_ANALYTICS_CLIENT_SECRET`, `CLIVOX_A10_ANALYTICS_REFRESH_TOKEN` and `CLIVOX_A10_ANALYTICS_READ_APPROVED=approved-clivox-a10-readonly-v1`.
3. Manually dispatch **Clivox A10 Owner-Reviewed Analytics Sample READ-ONLY** from `main`. Review and approve the environment. It cannot be used for a PR, rerun, other GitHub actor or branch.
4. The script validates the authorized account using the exact `UCfPEvy0SefE_5nNlYlY_CyQ` CLIVOX channel identity, then requests 50 or fewer video rows over a **seven-day interval ending two days ago** to allow some reporting lag.
5. Review only the **aggregate result in job logs**. The script never outputs raw OAuth tokens, private video IDs, individual user data or raw Google response bodies, and it creates no artifact. A zero-row result means **no data in this bounded snapshot**, NOT proof of zero channel views.

## Limits and editorial safety

- This is a **bounded sample**, not a complete inventory or statistically reliable experiment. `sort=-views` with `maxResults=50` means there may be unreturned videos. The code reports `sample_exhaustiveness_proven=false`, `valid_causal_ab_test_proven=false` and `real_time_complete_audience_coverage_proven=false`.
- Missing metrics remain `null` in output; there is no imputed zero. Short feed impressions, viewed-versus-swiped and actual retention curves remain unavailable without separately supported evidence.
- Do not interpret the metric as an exact real-time count; YouTube reporting can lag.
- A metric report is not a license, clip permission, approval for metadata changes, a predictive virality guarantee, or permission to schedule anything.
- This workflow makes **one** Analytics report GET only after owner identity validation. It never changes existing videos, calendar events, workflow schedules, rights flags, GitHub ledger files or YouTube uploads.
- **Current state:** environment exists with 0 secrets; genuine consent and live adapter readback **not configured**, zero real Clivox uploads, zero A9 licensed pilot, no media publishing.

Branch 1 and Branch 2 remain paused.
