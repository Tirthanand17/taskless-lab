# CLIVOX V2 P1 — API-Derived Metrics Remediation (Integration #1)

**Date:** 2026-11-14. **Stage:** code integration; require actual PR + merged-main CI before calling phase complete. **No creator-footage access, licensing or YouTube publication.**

## What changed

### A1 public discovery
- \`scripts/branch3_discovery.py\` still supports read-only fixed-host YouTube Data API \`videos.list\` (known IDs) and bounded \`search.list\` → \`videos.list\` query on explicit manual workflow dispatch. Neither mode calls any media download, private caption, write or upload endpoint.
- Removed \`source_score\`, views-per-hour, observed likes/comments-to-views engagement ratios, source age hours, parsed duration seconds, title relevance components, \`research_priority_score_0_to_100\` and \`score_components\`.
- Returned records now contain source video/channel IDs, canonical YouTube URL, provided title/published date, original API duration ISO-8601, and **individual uncombined** public views/likes/comments. Values are official counts if provided; absent stays \`null\`. No fabricated most-replayed timestamp or heatmap.
- Sorting is lexical **video ID**, not views or other statistics. No cross-owner popularity score/analytics is synthesized.
- Adds a \`non_authorized_api_data_expires_at_utc\` timestamp and seven-day retention contract (matching the legacy 7-day Actions artifact). The repo's public discovery report is **not committed** to Git.
- Sources: [YouTube API Developer Policy §III.E.2 and §III.E.4.h](https://developers.google.com/youtube/terms/developer-policies), [Quota Calculator](https://developers.google.com/youtube/data/determine_quota_cost).

### A2 pending rights review cases
- \`scripts/branch3_rights_case_intake.py\` rejects all retired source score/derived data fields, untrusted caller-supplied flags, bad public counts and missing/fabricated/expired seven-day API-data timestamp.
- A2 no longer emits \`research_priority_score_only\`, sorts only by source video ID and records provenance/expiry. Each case remains \`AWAITING_REAL_RIGHTS_HOLDER_VERIFICATION\`. No grant/rights holder or publish authorization is issued.

### A1→A2→A3 provenance
- \`scripts/branch3_a1_a2_a3_handoff.py\` strict public field allowlist was migrated from old score-rich records to the new score-free source shape. It independently checks expiry, current owner/channel, exact-case digest and frozen A3 no-media/rights boundary.
- Existing private-control metadata journal, synthetic arcade audio/video runner, publication/release controllers and FlowMinute Branch 1/2 are not changed.

### CI
- New \`.github/workflows/branch3-clivox-v2-p1-discovery-policy.yml\` — PR/main + manual fixture-only GitHub Actions with 0 secrets/Google API calls; runs A1, A2, A123 and independent policy checks without uploading report files publicly.
- Updated \`.github/workflows/branch3-clivox-a1-discovery.yml\` existing manually dispatched workflow to assert score-free shape and source expiry, including A2 no-derived-score contract.
- Updated adversarial tests for A1, A2 and A123: absent API statistics, invalid/old scores, forged retention, altered rights flags, key leakage, wrong channel and old synthetic fixture compatibility.
- Existing A1 interactive live-query modes still require a separate restricted metadata API key; this PR **does not configure one**.

## What has NOT happened

- No real YouTube video discovery API query or creator watch page scraping;
- No "most replayed" timestamps (API cannot provide for third-party videos);
- No downloaded/cached creator videos, Twitch footage, source transcripts or rights contracts;
- No legal permission, human editing/review, source clip cropping, original narration against a real creator stream;
- No real Clivox uploader OAuth, video upload, schedule, paid account, outreach or YPP approval.

**P1 is API-metadata compliance hardening, not the finished viral clipping feature.** Next P2 is to shortlist partnership-ready creators; this must not use viral rankings derived from third-party YouTube API data.

## Verify and merge checklist

1. PR all checks pass, especially new dedicated policy-safe A1/A2/A3 CI and existing A123/no-download workflow.
2. Main after merge: full synthetic fixture workflow green. Collect exact run ID and SHA, link in \`architecture-status.json\` on separate evidence-only PR if needed.
3. Only then transition \`P1 → COMPLETE\`, update conservative roadmap progress **2 of 12 non-optional phases = 17%**. This percentage measures architecture and policy groundwork **not** readiness to produce or monetize clips.
4. \`P2...\` remain NOT_STARTED until separately integrated, and true creator grants/upload metrics remain zero.
