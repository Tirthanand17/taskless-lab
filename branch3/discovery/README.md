# Clivox A1 — Public-metadata discovery and permission-pending triage

**Implementation as of 2026-11-12:** API-capable **read-only metadata** discovery is implemented, but its GitHub API key is **not confirmed configured**; fixture and campaign metadata jobs work without a key. Source acquisition, rights approval, render, OAuth, YouTube upload and publishing remain **OFF**.

## Two independent input lanes

### Lane A: actual public YouTube video metadata (optional API key)
- \`scripts/branch3_discovery.py\` supports:
  - **fixture:** synthetic test input, no key/no network, always explicitly marked synthetic
  - **ids:** 1–30 specific canonical YouTube video IDs, one \`videos.list\` GET
  - **query:** one bounded recent public-video search (max 10 results, last 14 days) plus one \`videos.list\` GET
- Input category is one of gaming, livestream, comedy, entertainment or podcast_interview.
- Source statistics are read from the YouTube Data API response, not invented; missing likes/comments remain null. Source video rank = heuristic of source view velocity, public engagement, recency and title/topic relevance. It identifies possible **full videos to review**, NOT a valuable excerpt, proof of clip permission or predicted Shorts performance.
- The job never obtains full video files, audio, captions or livestream recordings. API key is for **public metadata only**, never the Clivox owner's OAuth token.
- A live run requires GitHub Actions repository secret **\`CLIVOX_YOUTUBE_METADATA_API_KEY\`** with a public YouTube Data API credential; it is **not a publishing credential**. API failures stop without leaking the key into log output.
- YouTube Data API 2026 updated quotas: \`search.list\` calls have a separate default bucket of 100 calls/day, \`videos.list\` draws from the shared bucket and costs 1 per call; check actual project quota. Sources:
  - https://developers.google.com/youtube/data/revision_history
  - https://developers.google.com/youtube/data/determine_quota_cost
  - https://developers.google.com/youtube/data/reference/rest/v3/search/list
  - https://developers.google.com/youtube/data/reference/rest/v3/videos/list
- **Do not run high-volume or repeatedly backfilled queries** without source budgets. No scheduled daily scanning is enabled by this PR.

### Lane B: creator clipping campaigns (no API or media)
- \`scripts/branch3_discovery_pipeline.py\` reads a strictly limited, public-safe JSON candidate file containing canonical campaign references and *human-editorial hypothesis flags*.
- Genuine example leads are YMH 2 Bears 1 Cave, IShowSpeed × Expedia, FaZe. Campaign view statistics are all null because public campaign pages do not establish the videos' official counts.
- Rejects malicious URLs, duplicates, extra "approved" flags and claimed campaign rights.
- Score: 0–100 for first-frame hook, clear payoff, humor/surprise, available context, proposed original commentary and potential to share. It is **not** real audience performance or license approval.
- The fixture has zero approved creators. Changing the fixture does not place a creator on the allowlist and does not advance the clip to production.

## Run in GitHub only
Workflow \`.github/workflows/branch3-clivox-a1-discovery.yml\` supports manual \`workflow_dispatch\` with \`fixture\`, \`ids\` or \`query\`. **No local video processing.** Both discovery reports, when generated, are public-safe GitHub Actions artifacts with seven-day retention. A second workflow \`.github/workflows/branch3-clivox-a1-intake-qa.yml\` automatically tests A1 source code and sample data on PRs without secrets or network.

For live public search:
1. Owner configures an API key for the YouTube Data API v3 as \`CLIVOX_YOUTUBE_METADATA_API_KEY\` in repository Actions secrets (Google Cloud console). Prefer API key restrictions to appropriate API; never paste credentials into chat or repository files.
2. Manually dispatch A1 discovery \`query\` for one topic. Check run log/artifact. Do not confuse discovery rankings with permission.
3. A **rights case** must be opened and independently verified before any clip footage is downloaded, edited or published.
4. Keep the existing \`branch3/creator_permissions.json\` empty until a verified rights holder actually grants commercial YouTube clipping rights.

## Trust and review states
Both lanes output a permission-pending shortlist, not a grants ledger. The candidate's source may still contain unlicensed game publisher assets, stream guests, music or shows. Rank cannot override \`scripts/branch3_creator_permission_gate.py\`.

**Safety invariant:** branch1/branch2 paused, Clivox ID only (\`UCfPEvy0SefE_5nNlYlY_CyQ\`), all download/upload disabled, no private recordings or personal contacts in public GitHub, no publishing API keys.
