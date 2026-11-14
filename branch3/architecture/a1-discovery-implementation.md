# Clivox A1 — Operational metadata discovery and research ranking

> **CLIVOX V2 P1 compliance remediation (2026-11-14):** The new metadata adapter no longer calculates or emits forbidden cross-owner views-per-hour/likes-per-view engagement ratios, weighted full-video "viral" priority scores, ages or converted durations from API data. It instead preserves YouTube-provided public statistics individually, the original ISO-8601 duration and canonical source references; candidate records sort only by their literal source video IDs. A seven-day non-authorized API-data expiry is attached to each disposable report. The downstream A2 rights-case intake and A1→A2→A3 exact-shape handoff reject old derived fields, stale/forged TTLs and forged permissions. A separate, no-key/no-upload P1 GitHub workflow tests all three stages with wholly synthetic input. **No one has licensed any creator clips, and this is not live viral-moment extraction or an approval to upload.** Refer to [new V2 master architecture](../clipping_v2/MASTER_ARCHITECTURE.md) and [P1 implementation notes](../clipping_v2/P1_API_COMPLIANCE_IMPLEMENTATION.md).


**Implementation date:** 2026-11-12. A1 is *metadata-discovery only*. No third-party footage downloads, no rights grants, no uploads or publishing. This does NOT mean A2–A10 are operational.

## Implemented
- \`scripts/branch3_discovery.py\`: standard-library Python public YouTube Data API adapter and deterministic source ranking, with fixed \`www.googleapis.com\` host and strict ID/query limits.
- \`scripts/test_branch3_discovery.py\`: adversarial safety, duplicate, quota-bound, statistics, unknown-metric, source-quality and wrong-input checks.
- \`.github/workflows/branch3-clivox-a1-discovery.yml\`: manually triggered GitHub-hosted discovery with read-only repository permissions, no media downloads and JSON metadata artifact only.
- Output is explicitly \`A1_DISCOVERY_PUBLIC_METADATA_ONLY\`, with source rights \`UNVERIFIED\` and every download/upload/publication permission \`false\`.

## Two live discovery entry points
1. **Known public IDs**: give 1–30 public 11-character video IDs. Exactly one \`videos.list\` call (part \`snippet,statistics,contentDetails\`). Useful when investigating an exact creator or an existing rights-campaign lead.
2. **Single keyword query**: provide 3–90 characters and choose one of gaming, livestream, comedy, entertainment, podcast_interview. One \`search.list\` page, maximum 10 videos uploaded in the last 14 days, sorted by the API's \`viewCount\` order; then one \`videos.list\` details call. No pagination or repeated social-media scraping.
3. **Offline fixture**: synthetic metadata for checking that the cloud workflow and ranking work, clearly labelled \`is_synthetic_fixture=true\`; can run without a Google API key. Synthetic figures must never be represented as real channel metrics.

Each run searches **one category**. Running multiple categories requires separate explicitly initiated workflows. No cron schedule and no background autonomous discovery are installed.

## One-time API configuration for real metadata
Create/restrict a *public-data-only YouTube Data API v3 key* in Google Cloud Console and configure it as a GitHub repository secret named:

\`CLIVOX_YOUTUBE_METADATA_API_KEY\`

An API key is **not** an owner account OAuth token, does not authorize uploads, and does not validate clipping rights. Restrict it to YouTube Data API v3 and, if the environment permits reliable source-IP restriction, also apply appropriate application restrictions. Never paste keys in a public repo, chat response, workflow inputs, PR, console logs, or artifact. GH Actions hosted runner source IPs are dynamic, so IP allowlisting may require an approved stable egress solution; otherwise enforce quota/usage alerts and API restriction.

**The current workflow fails closed when this key is missing in \`ids\` or \`query\` mode**. Only \`fixture\` mode succeeds without it. No existing FlowMinute Lab OAuth credentials are used.

## Running on GitHub
GitHub → Actions → **Clivox A1 Public Metadata Discovery (RESEARCH ONLY)** → Run workflow.

Inputs:
- \`mode=fixture\`, \`category=gaming\` → safe synthetic test.
- \`mode=ids\`, \`category=comedy\`, \`video_ids=i6pmnpaOaZQ\` → metadata-only investigation of the YMH Ep347 *research* source after API-key setup.
- \`mode=query\`, \`category=livestream\`, \`search_query=funny streamer reactions\` → first page of recent results, metadata-only.
- The JSON artifact is \`clivox-a1-public-metadata-<run_id>\` and expires after 7 days. It contains only public video IDs, titles, source channel IDs, duration, public statistics and a research score. No third-party video or transcripts.

## Ranking is heuristic and conservative
- **Historical V1 weights are RETIRED, not active:** no API-derived velocity, engagement ratio, recency metric or numeric public-statistics-based source score is permitted in P1.

Scores are **0–100 and uncalibrated**. They rank *entire source videos*, not exact moments or the probability a future Short will go viral. Source audience size, upload time, creator fame, previous subscribers, topic and viewing behavior strongly confound comparisons. After A10 and sufficient authorized clips, evaluate real engaged views, shown in feed, swipe-vs-view, retention, shares and subscriber conversion. No AI model claims to predict viral success.

## Rights and ethics gate
Every output candidate is **UNVERIFIED**:
- A video being popular, searchable, a podcast or a public clip-campaign candidate is **never** copyright permission.
- Neither a creator's title nor API metadata authorizes downloading. Clivox permission-only source gate remains the single source of truth for the next stage.
- A2 must verify the actual rights holder, creator-issued policy or written license (commercial YouTube redistribution and editing), game publisher, third-party audio/visuals, guest permissions, expiry and allowed video IDs.
- Any future authorized Short requires original editorial context/commentary, honest metadata, technical QA and owner-signed exact release. The uploader is still OFF.

## API cost + availability (official source)
As checked 2026-11-12, \`videos.list\` costs 1 quota unit and Google currently describes \`search.list\` as a separate per-day bucket of 100 calls with cost 1 each. Future pricing can change; review live project quota in Cloud Console. Each A1 manual run is limited to at most one search and one video details call, and never retries blindly. Every run must still be counted against the actual project's configured quotas.
- https://developers.google.com/youtube/data/reference/rest/v3/videos/list
- https://developers.google.com/youtube/data/reference/rest/v3/search/list
- https://developers.google.com/youtube/data/determine_quota_cost

## A2 rights-case integration
Every A1 report now goes through `scripts/branch3_rights_case_intake.py` in the same GitHub workflow, generating human-rights review cases with all clearance flags false. See [A2 intake implementation](a2-rights-intake-implementation.md). This is not an approval of any creator or source.

## Implementation acceptance
- ✅ Offline fixture can run without secrets and produces a source-only report.
- ✅ Tests verify fixed YouTube API host and **no write/media API**.
- ✅ Invalid URLs, duplicates, missing/private stats and unsafe inputs fail closed.
- ⬜ Live search/IDs requires a new restricted metadata API key in GitHub Secrets.
- ⬜ A2 rights-case review remains unimplemented beyond existing eligibility checks.
- ⬜ A3 confidential licensed-media storage, A5 renderer and A8 release uploader are unimplemented.

## Safety note
This workflow accepts public metadata and user-curated search strings only. Do not put private personal data, confidential contracts, or passwords in a \`query\` input. Anyone able to read repository Actions artifacts may access reports; public metadata is appropriate there.
