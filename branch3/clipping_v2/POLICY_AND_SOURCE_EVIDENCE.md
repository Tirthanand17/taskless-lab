# CLIVOX V2 — Verified Policy, Research and Source Evidence

**Checked 2026-11-14.** Sources are live official policies/documents except where specifically labelled community/creator background. **Not legal advice.** Policy versions, content restrictions, free quotas and creator status must be rechecked before each first-party or licensed-media integration.

## A. YouTube copyright / monetization — independent gates

1. **Channel-wide reused/inauthentic content policy:** https://support.google.com/youtube/answer/1311392
   - Repurposed footage without substantive original voice, critical review, new context/story and viewer value can be rejected for YPP. Similar repetitive templates and minimally changed reuploads can affect the entire channel.
   - Crucially, **permission from the source creator does not cure a YPP reused-content violation**. Require human editorial review of meaningful difference as an additional, separate gate.
   - Neither effects, crop, captions nor adding music alone is a guaranteed transformation.
2. **Common copyright myths / seconds rule:** https://support.google.com/youtube/answer/2797449
   - There is **no safe number of seconds** (5, 10, 30, 60) that automatically legalizes reuse; credit, "no copyright intended" or minimal editing do not grant rights. Fair use/fair dealing is context/jurisdiction specific, not an automatic uploader approval.
3. **Gaming rights:** https://support.google.com/youtube/answer/138161
   - Game video monetization depends on publisher commercial terms and transformative value. Creator permission to use stream performance does not license game publisher IP, music, mods or actor content.
4. **Shorts:** https://support.google.com/youtube/answer/15424877
   - Vertical/square Shorts up to 3 minutes; a **1–3-minute Short with an active claim can be blocked globally**. Use 25–55s as first experiments for storytelling and avoiding some long-Shorts restrictions, **not a copyright safe-harbor**.
5. **Native remixes:** https://support.google.com/youtube/answer/10623810
   - YouTube's in-product remix tooling may allow some content while the owner can restrict or remove it. Remix eligibility inside the official product **does not** authorize an unrelated API client to download/rehost raw footage.
6. **Content ID claims:** https://support.google.com/youtube/answer/6013276
   - Claim can block or monetize on behalf of claimant; claim ≠ strike; unresolved claims affect reach and revenue. Claims remain possible even with a real license and may require manual clearance. No automated unsupported disputes.
7. **YouTube Audio Library:** https://support.google.com/youtube/answer/3376882
   - Free in-product production music/sfx, with attribution when required and YouTube-oriented usage. Music heard *inside* a licensed stream must also be cleared or removed.
8. **Creator Music update:** https://support.google.com/youtube/answer/11610212
   - From August 2026 transition away from paid song licenses to no-cost/revenue-share options in eligible contexts; Creator Music eligibility/geography differs. Do not assume Indian/non-YPP CLIVOX access.
9. **GenAI/real-person disclosure:** https://support.google.com/youtube/answer/14328491
   - Meaningfully altered/generated realistic scenes or making a real person appear to say/do something they never did may require disclosure; no synthetic voice impersonation or misleading actor edits.
10. **YPP eligibility:** https://support.google.com/youtube/answer/94522 and https://support.google.com/youtube/answer/72851
    - Early features in eligible countries: 500 subscribers + 3 valid public uploads in last 90d + 3,000 qualified long-form hours/365d **or** 3 million qualified Shorts views/90d; advanced ad eligibility: 1,000 subscribers + 4,000 qualified long-form hours/365d **or** 10 million qualified Shorts views/90d. All subject to channel review and terms; not a revenue guarantee.
11. **Public view counts changed:** https://support.google.com/youtube/thread/333869549 and https://support.google.com/youtube/blog/433409976
    - Shorts view counting changed 2025-03-31 to starts/replays; **engaged views** retained for YPP/monetization comparisons. On 2026-08-24, the platform announced play-start public view counts for additional video formats. Raw public view totals are poor viral-performance evidence without context.
12. **Shorts Studio metrics:** https://support.google.com/youtube/answer/12220281
    - \`engagedViews\`, \`Stayed to watch\`, \`averageViewPercentage\`, \`averageViewDuration\`, retention and subscribers have differing definitions and platform availability. Preserve unknown as null, do not substitute inferred values.
13. **Shorts A/B testing:** https://support.google.com/youtube/answer/16391400
    - Native Studio thumbnail/title A/B tests **do not apply to Shorts**. Treat sequential Shorts hook tests as observations, not randomized A/B.
14. **Recommendations:** https://blog.youtube/inside-youtube/on-youtubes-recommendation-system/
    - Viewer satisfaction is multifactorial: valued watchtime, surveys, sharing, likes, dislikes, click and platform standards. No guaranteed viral recipe or valid claim to "beat the algorithm."

## B. Critical YouTube API changes and V1 compliance remediation

Primary developer policies: https://developers.google.com/youtube/terms/developer-policies
Full API terms: https://developers.google.com/youtube/terms/api-services-terms-of-service/

1. **No video downloads via YouTube API:** Policy III.E.1 prohibits an API Client from encouraging/facilitating downloading, importing, backing up, caching or storing YouTube audiovisual content without YouTube's prior written approval. Hence **use YouTube for discovery only** and obtain edited source files from the actual creator via separate contracted delivery (or explicit written platform approval as applicable).
2. **No cross-owner API aggregation:** Policy III.E.2 restricts aggregating API Data across unrelated content owners and using it for broad YouTube analytics. Do not turn CLIVOX into cross-channel popularity statistics reseller or analytical leaderboard.
3. **No derived metrics from API Data:** Policy III.E.4.6 restricts accessing/using API Data to derive metrics such as ratios from view/like counts. Existing \`scripts/branch3_discovery.py\` and \`branch3/architecture/a1-discovery-implementation.md\` describe \`views / age\`, engagement ratios and a composite numeric source score. **This is a high-priority compliance hazard**. Before live metadata integration, remove/disable policy-unsafe numeric ranks, retain raw official values with provenance and date, and separately rank using **independent editorial observation** unrelated to API-derived counts; seek API policy interpretation if needed. A score against an authorized license-supplied media scene is different from cross-owner API-statistics scoring.
4. **Retention:** Policy III.E.4 limits caching nonauthorized API data to **at most 30 days**, subject to refresh/delete and currentness requirements; do not commit historical channel metrics or cached descriptions indefinitely.
5. **Tokens/scope:** APIs need separate scopes and owner authorization for uploads/Analytics; API key alone is public metadata, not consent, access to private files, download rights or rights clearance.
6. **User-facing upload notice/consent:** API Terms 9.1 requires explicit warning/visibility options when the API client enables upload. Protected owner action, exact target channel, release signature and private-first readback must remain mandatory.
7. **Watch-history/Most replayed:** \`videos.list\` docs https://developers.google.com/youtube/data/reference/rest/v3/videos/list list snippet/statistics/contentDetails but no per-second Most replayed graph. YouTube Analytics https://developers.google.com/youtube/analytics/channel_reports and https://developers.google.com/youtube/analytics/metrics expose \`audienceWatchRatio\` by \`elapsedVideoTimeRatio\` for the **authorized channel/content owner** only. Never claim access to famous YouTubers' private retention.
8. **Caption download requires editor:** https://developers.google.com/youtube/v3/docs/captions/download — only authorized editors can download video caption tracks; a public watch-page transcript is not a blanket licensed transcription dataset. Use creator-supplied caption/transcript when permitted.
9. **Current documented quotas:** https://developers.google.com/youtube/data/determine_quota_cost and https://developers.google.com/youtube/data/reference/rest/v3/search/list — **as of Nov 2026** default \`search.list\` own bucket 100 requests/day costing **1 each**, \`videos.list\` 1; combined default other service bucket 10,000. Old guidance \`search.list=100 quota units\` is not current; verify your project quota in developer console at implementation time.
10. **API quota/terms are dynamic:** https://developers.google.com/youtube/data/guides/quota_and_compliance_audits; avoid planning unlimited free 24/7 tracking.

**V2 integration #1 is a compliance-hardening PR, before a live discovery key, new creator search, ranking or distribution.**

## C. Twitch as an attractive metadata signal—NOT a free media license

Primary: https://dev.twitch.tv/docs/api/reference/clips and https://dev.twitch.tv/docs/api/clips/
- \`GET /helix/clips\` accepts broadcaster/game/id and returns **public clip references**, view count and optional VOD offset. Twitch already has curated/highlighted segments—lower research cost than brute-force 12-hour VOD analysis.
- \`GET /helix/clips/downloads\` exists as of current documentation but requires the **broadcaster's or authorized editor's scoped OAuth** (\`editor:manage:clips\` / \`channel:manage:clips\`). It is **not** an anonymous public Twitch video downloader.
- A creator granting editor API permission or a Twitch clip being public does not by itself give CLIVOX commercial YouTube monetization/republication rights. Require direct grant, scope, original guest/game/music clearances and storage policy.
- API requests are rate-limited with headers/429 handling: https://dev.twitch.tv/docs/api/guide
- Future Twitch clip-view popularity can propose timestamp *candidates*, but manual editorial value, rights and fairness remain separate.

## D. GTA VI release and pre-release ethics (time-sensitive)

Rockstar official: https://www.rockstargames.com/VI and https://support.rockstargames.com/articles/29jV3Cv2cCgvwM1XgtMO5o/grand-theft-auto-vi-regional-pre-load-and-release-times-on-playstation-5-and-xbox-series-x-or-s
- As of **2026-11-14**, Rockstar lists official GTA VI launch **Thursday 2026-11-19**, with pre-load available before launch. Pre-load ≠ creator-permitted gameplay publication.
- Treat "FULL GTA VI GAMEPLAY" claims before release as potentially embargoed, leaked, fake or mislabeled. No download, reaction clip or monetization from suspected leaks. Mark \`PRE_RELEASE_UNVERIFIED\`, block source ingest.
- Game publisher policies, footage/guest/mix rights and streamer-granted reproduction are **separate**. After release check Rockstar's current commercial fan-use rules again (do not assume old fan-video policy grants unrestricted cross-channel monetization).

## E. GitHub, free tools, rights-aware cost

- Standard public GitHub Actions runner usage: https://docs.github.com/en/actions/concepts/billing-and-usage and https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job — free standard hosted runner compute for public repos, but subject to GitHub terms/policy and storage/quota/abuse limits. **Public artifacts and logs are not a private media vault.** Private repositories receive limited included compute/storage based on plan; further usage may cost.
- FFmpeg: https://github.com/FFmpeg/FFmpeg — codecs, probe, cuts, crops, audio, subtitle rendering; LGPL/GPL configuration depends on compilation.
- PySceneDetect: https://github.com/Breakthrough/PySceneDetect — BSD-3, cuts/transitions, not automatically "funny" or viral.
- faster-whisper: https://github.com/SYSTRAN/faster-whisper — MIT, CTranslate2, CPU int8 ASR; all model-weight/commercial-use terms separately review; model guesses are not accepted quotes.
- whisper.cpp: https://github.com/ggml-org/whisper.cpp — MIT C/C++ CPU-first fallback.
- Silero VAD: https://github.com/snakers4/silero-vad — MIT, audio activity only.
- LosslessCut: https://github.com/mifi/lossless-cut — open source, GitHub download free, GUI fast trim, not a rights workaround.
- Kdenlive: https://github.com/KDE/kdenlive — GPL, desktop editor optional; not a cloud-only automation dependency.

## F. Evidence discipline / exclusions

The watchlist contains **potential research/outreach** names, not endorsements or preapproved licenses. Third-party view-count leaderboards may have unstable samples and API/compliance restrictions; avoid publishing fabricated subscriber counts or directly calculated cross-channel viral scores. No creator has granted rights to CLIVOX yet. No rightsholder was contacted by this research PR.

Monetization compliance and copyright rights require human judgment and possibly professional counsel for contract/claim disputes. A claim-free preview is not proof of ownership. Every official link must be rechecked at the moment an operator decides to license or upload content.
