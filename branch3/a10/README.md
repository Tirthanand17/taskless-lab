# Clivox A10 — Analytics, experiments and feedback loop

**Implementation dates:** synthetic parser 2026-11-12; owner-only read-only API adapter 2026-11-13. **Status:** synthetic fixture plus tested Clivox-specific bounded live adapter code and an owner-protected GitHub environment with **zero OAuth secrets**. No genuine Clivox Analytics consent, view data, uploaded video or real optimization decision exists.

## Official research (recheck before live integration)
- [YouTube Analytics Reports API](https://developers.google.com/youtube/analytics/reference/reports/query): owner-authorized `GET https://youtubeanalytics.googleapis.com/v2/reports` with ids, time interval, metrics, dimensions and filters. Header column names/types must be mapped and missing rows may be omitted; data can lag several days.
- [Metrics reference](https://developers.google.com/youtube/analytics/metrics): engagedViews, views, averageViewDuration, averageViewPercentage, shares and subscribersGained are documented metrics; metric meanings and report compatibility must be checked per query.
- [YouTube Shorts Studio analytics](https://support.google.com/youtube/answer/12942217): shown in feed, viewed versus swiped away and retention displays require separate Studio-backed evidence. **Do not fabricate or infer these from YouTube Analytics API view totals.**
- OAuth for Analytics uses the dedicated `https://www.googleapis.com/auth/yt-analytics.readonly` scope for ordinary Analytics reports. A7 currently asks only for `youtube.readonly` for channel identity; production Analytics access requires separately reviewed owner consent and protected secrets.

## New protected actual Analytics read-only path (NOT CONNECTED)

[Owner-only CLIVOX Analytics setup and limitations](OWNER_ANALYTICS_READONLY_SETUP.md) adds a separate three-request read-only pathway with `youtube.readonly` and `yt-analytics.readonly` both required, verified Clivox Brand Account, and a maximum 50-row nonmonetary sample in a seven-day window. The separate `clivox-analytics-readonly` GitHub environment was created and checked owner-main-only with administrator bypass disabled; it currently has **zero secrets**. PR CI uses mocked Google responses exclusively. The existing synthetic-only experiment data and policies remain unchanged.

## What is implemented
- `scripts/branch3_a10_analytics.py`: validates a fixed YouTube Analytics result-table *shape*, with exact Clivox channel association, video annotations, metrics order and types. In A10 the only accepted input is explicitly `SYNTHETIC_YOUTUBE_ANALYTICS_API_RESPONSE`, never claimed to be a live report.
- `branch3/a10/fixtures/synthetic-analytics-export.json`: **12 invented example Shorts** dated hypothetically 2027-02-01, not real videos. Category comedy, six A-hook and six B-hook observations, all with synthetic views, engaged views, watch percentage, shares and subscribers gained.
- `branch3/a10/analytics-policy.json`: forbids real API requests, publishing, imported live clips and fake Studio feed metrics.
- `scripts/test_branch3_a10_analytics.py`: adversarial tests reject wrong/old channel ID, forged real-data claims, duplicate video IDs, invalid columns/metric values, synthetic-to-live status changes and premature hook-winner declarations.
- `.github/workflows/branch3-clivox-a10-analytics.yml`: read-only/offline GitHub QA and short-lived *public-safe synthetic* summary artifact; no credentials or Google API calls.

## Experiment methodology (research hypotheses, not guaranteed virality)
1. Keep a source-traceable, rights-reviewed editorial classification: gaming, livestream, comedy, entertainment or podcast/interview. Compare **within the same category** when possible; don't pit unequal niches directly.
2. Assign the hook variant A or B *before* seeing results. A scientific comparison also requires fair/random allocation and controls for topic, length, release time and source. This pipeline **does not** implement allocation or prove causation.
3. Study 1-, 3-, 7- and 14-day windows after each approved Short, with aligned exposure periods and known publication timestamps; the synthetic fixture only illustrates 7-day parsing. Analytics may lag.
4. Review views and engaged views separately; calculate median watch percentage and shares/subscriber gains **per 1,000 engaged views** where denominators are nonzero.
5. If a metric is missing, keep `null` and give a reason. In particular **shown-in-feed, chose-to-view and retention curves remain `null`** in this pipeline. A zero is recorded only when a trusted source explicitly reports zero.
6. Enforce at least **10 observations per arm** for preliminary review. More is needed for credible statistical claims. Even after this floor, an editor must review confounds, uncertainty, changes in content mix and platform exposure. A10 never declares a causal winner.
7. Never automatically change a title, upload time, clip selection, script, source license or YouTube scheduling based solely on these scores. Human and rights gates remain in place.

## Limitations and next requirements
- A10 is a **synthetic-data validation and experiment reporting prototype**, not an operating dashboard populated with real Clivox statistics.
- The separate A7 read-only client has no owner credentials and cannot infer Analytics access. A future protected read-only Google Analytics adapter must independently verify Clivox ownership and obtain owner consent without reusing FlowMinute Lab tokens.
- The public GitHub repo can hold non-sensitive aggregated results; do not commit private owner exports, private video IDs or individual user information. Owner-approved secure storage is required for real data.
- There are no eligible Clivox Shorts to analyze, so actual channel baselines and optimization outcomes are **unknown**, not zero-valued.
- Other critical blockers remain: creator-issued footage rights, approved private media vault, licensed video production and human-signed final release. Branches 1 and 2 remain paused.

## How to run
Run `branch3-clivox-a10-analytics.yml` on GitHub. It performs offline tests, generates `synthetic-report.json` and archives only the redacted synthetic aggregate for seven days. Do not interpret any test values as Clivox views or audience outcomes.
