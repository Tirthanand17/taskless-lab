# Clivox architecture research — Primary-source evidence

Reviewed 2026-11-12. Pages and platform terms can change; verify live during each licensed release.

## YouTube policies
1. **YouTube monetization + reused content**: https://support.google.com/youtube/answer/1311392
   - Permission does not automatically pass the YPP reused-content review. Narrative, criticism, clearly original analysis and creative edits matter; generic repetitive template farms risk inauthentic-content enforcement. Channel-wide evaluation, not only isolated upload.
   - **Architecture:** a distinct original-commentary / meaningful-new-value editorial approval is mandatory in addition to copyright grants; reviewer can reject purely captioned reposts.
2. **Copyright ownership / authorization**: https://support.google.com/youtube/answer/2797466
   - **Architecture:** allow only verified creator-issued commercial clipping permission; separate clearance for publisher/game IP, guests, stock/music, and restrictions. Risk can never be claimed to be zero.
3. **Up to three-minute Shorts and claimed-content restrictions**: https://support.google.com/youtube/answer/15424877
   - Standard vertical or square videos up to 3 minutes qualify as Shorts. A Short over one minute with an active copyright claim is blocked globally.
   - **Architecture:** experiment baseline 25–55 seconds, not an algorithm limit or legal safe harbor; avoid claiming that under-60-second Shorts are copyright-safe.
4. **Shorts feed analytics**: https://support.google.com/youtube/answer/12942217
   - Shown in feed, chose to watch vs swiped away, viewers/subscribers metrics are useful. Some useful audience measures appear only in Studio and may not be available through the public API.
   - **Architecture:** separate Studio-derived manually reviewed metrics from official Analytics API data; never invent absent metrics.

## YouTube developer APIs
5. **OAuth access**: https://developers.google.com/youtube/data/guides/authentication
   - OAuth for private owner data or write operations, refreshable access when properly configured. Service accounts are NOT supported for normal owner uploads.
   - **Architecture:** new Clivox credentials only, channel ID exact match via authenticated channels.list(mine=true), least scopes; handle invalid_grant as STOP and owner reauthorization, never fall back to FlowMinute Lab token.
6. **Video API status / publishAt**: https://developers.google.com/youtube/data/reference/rest/v3/videos
   - If unspecified, API uploads can default public; an explicit status.privacyStatus=private is mandatory. publishAt is only valid for a never-published private video; a past timestamp can publish immediately.
   - **Architecture:** private-first insert with explicit privacyStatus; late/invalid schedule blocked **before** API call; readback owner-only fields, processing errors and status afterwards.
7. **Resumable uploads**: https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol
   - **Architecture:** resumable transfer and resumable-status reconciliation; after ambiguous success/error, query inventory before retrying to avoid duplicate uploads.
8. **Read-only owner channel verification**: https://developers.google.com/youtube/data/reference/rest/v3/channels/list
   - **Architecture:** channels.list(mine=true) must report UCfPEvy0SefE_5nNlYlY_CyQ; use no mutation if wrong or unverified.
9. **YouTube Analytics API**: https://developers.google.com/youtube/analytics/metrics and https://developers.google.com/youtube/analytics/reference/reports/query
   - API provides engagedViews, averageViewDuration, averageViewPercentage, shares and subscribersGained where available; metric/dimension compatibility varies.
   - **Architecture:** record source endpoint and "not available" rather than substituting synthetic retention data.
10. **Quota calculator**: https://developers.google.com/youtube/data/determine_quota_cost
    - The live page currently shows separate daily method quotas for search.list and videos.insert as well as a pooled allocation for other endpoints. Other older versions of documentation quote different per-call costs, so avoid hardcoding a historical price.
    - **Architecture:** quota preflight retrieves project quotas from Google's Cloud Console at integration time; rate-limit search, cap discovery requests and avoid retry storms.

## GitHub Actions and cloud-only constraints
11. **Protected environments / reviewer gate**: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
    - Required reviewers, environment-scoped secrets and branch allowlists are available subject to plan/repository visibility; configure and verify actual protection independently, not just a YAML environment name.
12. **Workflow concurrency**: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
    - **Architecture:** one in-flight publish attempt per clip and channel; pending runs can still race around API replies, so database/ledger locks plus actual remote inventory readback are required.
13. **Artifact retention**: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
    - GitHub Actions artifacts expire (default around 90 days); short-lived artifacts can be downloaded by users with read access. A PUBLIC repository is not safe private rights-media storage.
    - **Architecture:** keep only public-safe derived evidence/metadata in this repo; set deliberately short retention for non-sensitive build artifacts; private encrypted media storage needs owner-approved design.

## Third-party campaign contract example
14. **Content Rewards Creator Terms**: https://contentrewards.com/terms (checked 2026-11-12; website currently labels update 2026-10-26).
    - Joining/using platform can bind its terms, 18+ eligibility, brand-provided clips can have final edit IP assigned under Section 17.6; third-party rights clearance and other obligations remain.
    - **Architecture:** contract acceptance is a human/legal decision; clip program does not imply source licenses or perpetual creator ownership. YMH Ep.347 remains blocked pending verified participant terms and rights.

## Important limitations
- No system can promise viral views, exact revenue, universal fair use, zero copyright claims or YPP eligibility.
- Per creator permission + separate rights clearance is stricter than the legal minimum by Clivox's own choice.
- This research is not legal advice; rights-holder authenticity, contracts and specific disputed cases need owner/legal review.

