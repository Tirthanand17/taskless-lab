# Operating plan, experiments and capacity

## Analytics taxonomy
Every published release records: clip ID, channel ID, source rightsholder, source video ID, niche, clip duration, publication UTC and IST, hook experiment ID, overlay design ID, original commentary review ID, music/license status, final video SHA, YouTube video ID, title/metadata version and consent expiry.

**Official Analytics API metrics where permitted:** engagedViews, views, averageViewDuration, averageViewPercentage, shares, subscribersGained, likes, comments. Need correct dimensions/filters and scopes; exclude hidden/unavailable combinations.

**Studio-specific manual or supported API metrics:** shown in feed, chose to view vs swiped and audience-retention curves. If unavailable, write null + reason, never fill 0 or invent.

## Feedback loops
- Baseline: after 10 authorized uploads, compare median engaged views per 1000 feed impressions, chose-to-view, early retention, avg % viewed, shares and subs gained per engaged view.
- Campaigns: randomize original hooks within comparable source topics; compare cohorts, confidence and minimum samples. Avoid per-day claims of causal performance.
- Clip evaluation: rights pass is binary and non-negotiable; marketing score alone cannot override rights. Rank by first-frame clarity, surprise, payoff, motion, emotional variation, accessible caption framing and accurate promises.
- First few uploads: target 25–55 seconds as an experiment, not a safe-harbor rule or requirement.
- Do not spam, manipulate traffic, force engagement, publish bots/views or mislead titles/metadata.

## Robustness SLOs (proposed, not measured)
- 100% hard-stopped on missing permission/rights; zero unauthorized source downloads.
- 100% writes bound to exact Clivox channel ID, all uploaded videos private until signed scheduled.
- 100% signed-media releases with real remote video readback and collision check.
- No accidental duplicate upload on timeout; halt and reconcile.
- >= 95% expected CI unit and content QA success only after a pilot dataset is collected.
- Source/contract access logged with actor and expiry; compare license current at production and scheduling time.

## Cadence
- Week 0: create architecture, tests, rights-grant example, owner review setup (CURRENT).
- Week 1: verify authentic creator participation, sign per-source contract/rights, agree secure media storage design. No clip if permissions missing.
- Weeks 2–3: develop deterministic source-approved rendering plus human editorial QA, review on phone, publish first 1–3 approved private-first clips.
- Week 4+: gather 1/3/7/14-day metrics, run controlled experiments and increment cadence only if quality remains high.

## Cost discipline
- **GitHub Actions:** limit job runtime; prune temporary files; set short retention, use real storage budget metrics.
- **YouTube API:** avoid repeated public searching if source/campaign known; owner channel identity is a cheap authenticated read. Verify current YouTube quota configuration when adding real integration; docs have changed.
- **AI tools:** cheap text-only discovery and storyboard proposals first; do costly video/audio only after rights verification and owner approval.
- **Private media storage:** priced per GB-month / traffic, TBD by owner; no public Git media.
- **No automated publishing** until owner has accepted configuration, verified credentials, environment protections, source licensing and final release.

## Release monitoring
Observe GitHub Actions status, permission expiry, blocked QA, upload errors, actual video privacy state, processing/copyright status, schedule readback and analytics lag. Do not silently replace missing data with plausible synthetic values. Manual weekly review for copyright or channel policy changes.

