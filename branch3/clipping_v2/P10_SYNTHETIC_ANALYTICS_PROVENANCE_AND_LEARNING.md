# CLIVOX V2 P10 — Analytics provenance, Shorts-metric honesty and learning gates

**Implementation: 2026-11-14. This is entirely source-free, synthetic Analytics test data, not real channel performance.** The only verified CLIVOX V2 real milestones remain P0/P1 (2/12 = 17%). No licensed creator clip is uploaded, published or available to the live owner Analytics adapter. This P10 step does **not** measure virality, predict views, run an A/B test, contact creators, provision OAuth, schedule reports or authorize changes to YouTube.

## Primary-source platform definitions checked on 2026-11-14

- [Official YouTube Analytics Reports Query](https://developers.google.com/youtube/analytics/reference/reports/query): owner-authorized reports use an authenticated channel ID (\`channel==MINE\` or authorized channel ID), date range, supported \`metrics\`, \`dimensions\`, and \`filters\`. Availability may lag the requested end date. Use a video dimension only on content belonging to the connected channel.
- [Official Channel Reports supported metrics](https://developers.google.com/youtube/analytics/channel_reports): the basic channel/video report permits \`engagedViews\`, \`views\`, \`averageViewDuration\`, \`averageViewPercentage\`, \`shares\`, \`subscribersGained\`, subject to appropriate report combinations and authenticated scope. Never substitute public \`videos.list\` counts or a different creator's metrics for this.
- [YouTube Studio Content Performance](https://support.google.com/youtube/answer/12220281): *Engaged views* measures Shorts viewing past the initial seconds without loops; *Stayed to watch* describes the percent that stayed past those seconds. **They are different metrics**. Studio-specific viewed/swiped behavior and shown-in-feed details **are not part of this A10 basic API fixture** and must be \`null\` until separately verified with allowed authentic evidence. Retention curves are also **not queried by the existing bounded A10 adapter** (other Analytics reports can have audience-retention dimensions; absence here is NOT proof the entire API cannot offer them).
- [YouTube developer policy guide](https://developers.google.com/youtube/terms/developer-policies-guide), [Developer Policies](https://developers.google.com/youtube/terms/developer-policies) and [Additional derived metrics/data-storage rules](https://developers.google.com/youtube/terms/derived-metrics-policy): do not invent YouTube metric replacements, claim a proprietary virality score, conflate different platforms' data, extrapolate other channels, infer monetization, or store owner metrics beyond permitted terms. Additional custom derived metrics and storage allowances can require a separate audited use-case approval. **This P10 module generates no rate, multiplier, viral index, conversion prediction, revenue estimate or causal winner.**
- [OAuth authorization](https://developers.google.com/youtube/reporting/guides/authorization): use actual owner-controlled \`yt-analytics.readonly\` and required read-only channel identity scope, not \`youtube.upload\`. Existing \`branch3_a10_owner_readonly.py\` already implements a protected main/manual-only **read-only** adapter; it is not connected to actual credentials and is not invoked live in public PR CI.

## No duplicate A10 analytics connector

The repository already contains:
- \`scripts/branch3_a10_analytics.py\` and \`branch3/a10/fixtures/synthetic-analytics-export.json\`: strict mock API-report tables and fabricated A/B hook annotations. The older synthetic experiment harness demonstrates internal descriptive statistics, but those offline calculated examples are **not a green light to expose extra real API-derived metrics without policy review**.
- \`scripts/branch3_a10_owner_readonly.py\` and the protected manual \`clivox-analytics-readonly\` environment: bounded owner-only Analytics adapter, exact \`channels.mine\` check, double read-only scope and safe output shape; no real OAuth secrets/real observations presently connected. Real access must be separately owner-approved.
- \`scripts/branch3_v2_p9_private_first_preflight.py\`: source-free private-first upload planning with all real rights/YouTube write gates off.

P10 adds \`scripts/branch3_v2_p10_synthetic_analytics_gates.py\`, **not another Google API caller**. It first checks real A6/A7/A8/P9 release quarantine and absent owner Analytics consent, then consumes the existing A10 synthetic fixture and policy.

## Exact implementation

1. Run A10 \`validate_policy\` and \`validate_dataset\` on the existing **strictly synthetic** 12-row fixture. Reject real API claims, wrong channel, extra API columns, untyped/negative/NaN metrics, duplicate synthetic video IDs, altered missing Studio metrics or fake editorial approvals. No real Google network requests.
2. Emit only the **names and test-data availability counts** for six allowed official metrics: \`views\`, \`engagedViews\`, \`averageViewDuration\`, \`averageViewPercentage\`, \`shares\`, \`subscribersGained\`. The public JSON contains **no per-video private identifiers and no raw API metric values**. Every supposed real-channel metric value stays \`null\`; missing values are never converted to zero.
3. Explicitly preserve \`null\` for \`stayed_to_watch_percent\`, \`shown_in_feed\`, \`shorts_audience_retention_curve\`. Do not calculate swipe/retention from \`engagedViews/views\`, which would not be the same official metric and could violate data policies.
4. Validate fixed synthetic editorial A/B annotations **only as sample counts**. Even when a mocked group contains 10 or more examples in each arm, its real sample count remains zero, randomization unverified, causal winner false, real optimization disallowed. Do not rank different creators or videos by a fabricated score.
5. Build *hypothetical* owner inspection checkpoints **24h, 72h, 7d and 14d** after one fixed illustrative timestamp **2027-02-01 00:00 UTC**, with every actual-publish/evidence/review/learning flag false. This is not a created reminder, scheduled collection task, video upload time or claim that metrics are available exactly at those times.
6. Fail closed if anyone edits the output to claim OAuth connected, genuine stats, actual uploads, engagement predictions, publisher/youtube monetization status, retention curves, public video IDs, owner approval or automated experiment selection. The code only returns a source-free compliance demonstration and zero YouTube writes.
7. Existing \`.github/workflows/branch3-clivox-v2-p5-synthetic-candidates-qa.yml\` now checks the full **P5 → P9 generated-source and release-hold flow** plus P10 A10 synthetic provenance and review windows, with all media and ephemeral reports left in runner temp. No public metrics artifact, Google OAuth, YouTube network requests or video upload is added.

## What actual P10 requires

1. The real P2/P3 rightsholder license, licensed source handling, context-correct transformative original content and P4–P9 production safety gates, including **owner-signed exact final media and one owner-approved private-first CLIVOX pilot**. Without this, there are zero real V2 clipping-video outcomes to measure.
2. The owner must independently enable real A10 Analytics consent in a protected main-only environment for **the exact CLIVOX channel** and authorize read-only scopes, privacy/retention rules, export restrictions and deletion controls. Never use a different Google Brand Account or a creator's private channel without permission.
3. An owner-only evidence store should preserve source/time/window/owner and any applicable disclosure of YouTube API vs YouTube Studio data; no real personal video analytics should be committed to this public repository or public Actions artifacts.
4. For each actually published and approved video, retrieve genuine supported metrics, capturing as-of dates and report data lag; distinguish Shorts swipe-specific metrics and actual retention curve sources. Do not infer them from ordinary API video stats.
5. At 24h/72h/7d/14d *after an actual upload*, consider available own-channel evidence, consent/rights and claim status. Missing observations remain **UNKNOWN**, not 0. Do not declare a virality winner or causal A/B result from one or two uncontrolled videos.
6. A genuine experiment would additionally need preregistered content/hook definitions, stable cohorts, independent source rights, validated exposure assignment and adequate samples. No automated ranking/self-training or YouTube uploader control is enabled by this integration.

**Release status:** P10 technical-only; no real owner Analytics observation, no creator grant, no real Shorts engagement measurement, no publish actions. FlowMinute Branches 1/2 unchanged.

## Reproduce CI-safe checks

- \`python -B -m scripts.branch3_v2_p10_synthetic_analytics_gates --mode closed\`
- \`python -B -m unittest -v scripts.test_branch3_v2_p10_synthetic_analytics_gates\`
- \`python -B -m scripts.branch3_v2_p10_synthetic_analytics_gates --mode synthetic\`

Technical source-free P10 QA is now verified on PR and merged main. Actual CLIVOX audience Analytics and growth outcomes remain **unknown/not observed**; milestone completion still **2/12 = 17%**.

## Evidence of source-free integration on GitHub (2026-11-14)

- [Implementation PR #224](https://github.com/Tirthanand17/taskless-lab/pull/224) passed **4/4** PR checks; [dedicated PR P5→P10 integration QA #43594106599](https://github.com/Tirthanand17/taskless-lab/actions/runs/43594106599) **success**.
- Merged-main implementation SHA `d830d8c47c557973ac524cce37056272b564133c`; [P5→P10 synthetic events/video/review/HOLD + offline A10 provenance/Studio-null QA #43594259100](https://github.com/Tirthanand17/taskless-lab/actions/runs/43594259100) **success**.
- [Merged-main P4 video/media integrity regression #43594259097](https://github.com/Tirthanand17/taskless-lab/actions/runs/43594259097) and [Content Quality Gate #43594259076](https://github.com/Tirthanand17/taskless-lab/actions/runs/43594259076) **success**.
- All results are **synthetic technical test results**, not proof of current CLIVOX growth, replay heatmap, real viewer retention, monetization, owner authorization, licensed creator video, Google OAuth data or public upload. No real P10 phase accepted; overall 2/12 = 17%.
