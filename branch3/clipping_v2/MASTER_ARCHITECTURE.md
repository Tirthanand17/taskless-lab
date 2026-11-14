# CLIVOX Viral Clipping Engine V2 — Master Architecture

**Research freeze:** 2026-11-14 (Asia/Kolkata). **Decision status:** DESIGN/RESEARCH ONLY; integration begins ONLY after separate user direction. **Not a live clipping bot.** All creator-footage ingestion, automated contact, licensing, live upload, scheduled publication and payment features are **OFF**.

**Canonical repository:** [taskless-lab](https://github.com/Tirthanand17/taskless-lab). **CLIVOX YouTube channel:** \`UCfPEvy0SefE_5nNlYlY_CyQ\`, \`@ClivoxPulse\`. **Branches 1 and 2:** FlowMinute remains isolated and paused; do not change those workflows or reuse their tokens.

## 0. What we are actually building

Find promising, publicly discoverable long videos/livestreams from creators such as IShowSpeed, Kai Cenat, CaseOh, Jynxzi, Ludwig, CarryisLive and GTA-focused streamers; identify moments that **might** work as engaging Shorts; obtain the necessary reuse rights and media through authorized channels; add original CLIVOX narration, storytelling and substantive editing; independently QA the new exact video; let an authorized human approve the actual result; release to the **correct** channel with audit trails; and learn from real CLIVOX audience feedback. Gaming and live reactions are primary; comedy, creator challenges, podcasts and interviews are secondary tracks. Names are **research leads, not licenses**.

**Critical correction to earlier project framing:** Branch 3 already has some real metadata-only discovery (A1), unapproved rights-case intake (A2), and extensive source-free fictional arcade rendering/security scaffolding (A4–A8). The *actual* creator-footage clipping engine (authorized source ingest, transcript/hook detection on actual media, licensed transformations, creator partnership and full deployment) **does not exist yet**. The historical **78% overall** metric measures the previous synthetic/original architecture, **NOT completion of this V2 product**. Do not reuse it as V2 completion. V2 is **design-only** until separately measured integrations and real rights grants.

### Non-negotiable principles

1. Public URL, Twitch clip, creator popularity, first-party API metadata, public "Most replayed" graph, Creative Commons label, and even casual creator endorsement are **not universal commercial sublicenses**.
2. No YouTube API-client downloading, importing or caching of YouTube audiovisual files without YouTube prior written approval. A **rights holder's separately delivered original media file** is a distinct permissible *source delivery mechanism*, subject to rights contract; it is not a loophole to bypass platform rules. Twitch Clips Downloads API may be a future authorized editor path after actual editor permissions, Twitch terms review **and** a separate commercial creator grant.
3. The platform's public \`videos.list\` does **not** expose individual third-party most-replayed timestamps; granular \`audienceWatchRatio\`/retention is an authorized **owner** Analytics feature. Never fake such data or scrape hidden graphs.
4. YouTube API Developer Policies currently restrict derived scores/metrics calculated from API Data and aggregation across unaffiliated content owners. **Audit and correct existing \`scripts/branch3_discovery.py\` derived view-velocity/engagement scores before live V2 discovery**. Independent editorial ratings derived from authorized **media content** and human notes are distinct; do not feed public API likes/views into invented "virality scores".
5. Permission does **not** pass YPP's separate reused-content/inauthentic-content test. Text overlays, effects, zooms, simple trimming and subtitles alone are a weak value-add. Required CLIVOX editorial narrative, critique, humor, explanation or contextual re-framing—not deceptive cuts.
6. Every actual creator partner must authorize commercial **YouTube** clipping, modification, monetization and redistribution to this exact channel (or defined channel family), with source IDs, territory, expiry, attribution and restrictions; separately resolve game-publisher, music, guest/third-party and performer rights.
7. No artificial views, fake engagement, deceptive "GTA VI gameplay" claims, forbidden stream downloads, stolen Shorts, account impersonation or scraping around access controls.
8. Zero-extra-cost **engineering preference**, not a guarantee of free unlimited compute, video rights, cloud storage, OAuth, commercialization or labor. Media/transcripts/contracts never go into a public repo, public CI artifact or unprotected PR.
9. Design approval and test pass never constitute human rights review, media acceptance, signed release or successful YouTube publishing.

## 1. Verified baseline / reuse map

| Existing element | Reuse in V2 | Gap |
|---|---|---|
| A1 \`scripts/branch3_discovery.py\` metadata-only adapter + bounded GitHub Actions | Preserve fixed host, API-key gating, bounded search, canonical IDs, provenance | **P0 compliance rework:** current API-derived view-velocity/engagement ranks conflict with API derived-data restrictions; live key not verified |
| A2 rights-case intake, signed-offline review/revocation, private journal prototypes | Preserve *pending* cases, existing cryptographic identity and fail-closed defaults | No authenticated creator grants, game/music permissions, live revocation head or valid signer key |
| A3 storage boundary and private-control metadata repository scaffolding | Preserve public/private separation, SHA checks and no-secret Actions | No approved **media** vault or actual media access rights |
| A4 synthetic fictional screenplay | Reuse storyboards, on-screen brand template, narration/caption layout and editorial script checks | No original context script written against real licensed footage |
| A5 FFmpeg/H.264/AAC/SRT renderer, AV QA, correction worksheets, private proposed revisions, synthetic sandbox | Reuse deterministic render modes, mobile safe zones, actual encoded cue/speech checks, hashing | Not yet a **third-party licensed media crop/render** or interview speaker-caption pipeline |
| A6–A8 hash-bound unsigned release, dry-run/live adapter scaffolding, inventory and CAS retries | Reuse release safety architecture | No real editor/owner signatures, Clivox upload OAuth or enabled protected write environment |
| A9 production pilot | No reuse of unperformed steps | **0 actual licensed uploads** |
| A10 analytics interface | Reuse official metrics/unknown-as-null rule | No real channel OAuth analytics/experiment validation |

**Public rights allowlist remains empty** (\`branch3/creator_permissions.json\`). **Do not convert a researched creator lead into an allowed source by editing the JSON manually.**

## 2. Logical system

\`\`\`mermaid
flowchart TD
  A[Creator watchlist / opt-in partners / public discovery] --> B[Candidate canonical ID and compliant metadata]
  B --> C[Manual outreach + verified rights review case]
  C --> D{Current authenticated commercial scope + media access?}
  D -- No --> X[REJECT or HOLD; no media acquisition]
  D -- Yes --> E[Authorized creator-delivered source or authenticated editor clip]
  E --> F[Private media SHA manifest and ingest QA]
  F --> G[Source transcription / VAD / scene / audio / manual timestamps]
  G --> H[Timestamp candidates and evidence cards]
  H --> I[Original-value hook / completeness scoring from media, not third-party YT metrics]
  I --> J[Human shortlist / source-context review]
  J --> K[CLIVOX added narration, story, split screen, ethical crop and SRT]
  K --> L[FFmpeg render, independent A5 decoded frame/audio QA]
  L --> M[Human review: quotes, originality, rights, music, gameplay, exact output]
  M --> N{Trusted A2 rights fresh and A6 exact-media signed owner release?}
  N -- No --> Q[QUARANTINE / REVISE]
  N -- Yes --> O[Protected Clivox-only OAuth + A8 private-first upload]
  O --> P{Processing, Content ID, metadata, inventory and owner check?}
  P -- No --> Q
  P -- Yes --> R[Explicit future scheduling / private readback]
  R --> S[Real CLIVOX engaged views, stayed-to-watch, retention, shares and subscribers]
  S --> T[Versioned editorial experiments + rights audit]
  T --> A
\`\`\`

**Data planes:** (1) public reference-only metadata; (2) strictly private licensed source files, grants and transcript; (3) short-lived private encoded review and feedback files; (4) protected owner credentials / isolated cryptographic release metadata; (5) official account-owned analytics. The repo remains code/docs/config/test-fixtures only.

## 3. Components, inputs, outputs and agent responsibilities

| ID | Component / role | Inputs | Output | Hard no-go |
|---|---|---|---|---|
| V2-01 | Watchlist researcher | Official creator channel URLs, editorial niche, approved YouTube/Twitch API; manually verified creator consent | Time-limited candidate references, **not** rights | Cross-owner API statistics aggregation or unauthorized downloads |
| V2-02 | Platform-policy and creator-rights guardian | Existing A2 cases, verified contract/policy, channel/territory/source, game/music checks | Authenticated scoped rights grant / hold | Agent self-signing or inferring agreement from views |
| V2-03 | Source-delivery boundary | Separate creator-uploaded raw MP4 or authorized Twitch-editor media link, matching approved source | Private SHA256 media manifest | YouTube video download via API client or unapproved public artifact |
| V2-04 | Transcript and event detectors | Authorized source audio/video only | Timed ASR hypotheses, speech spans, scene/audio peaks; confidence/error | Pretend generated text is guaranteed spoken dialogue |
| V2-05 | Highlight segment composer | Transcript + acoustic evidence + source narrative context + optional rights-holder retention hints | 10–30 candidate (start,end) segments with evidence; no public platform-derived score | Claim actual third-party Most replayed peak without authorized data |
| V2-06 | Human candidate/claim reviewer | Segment preview, source-context, original quote verification | Selected segment or rejection, initial editorial sign-off | Mistaking a popular streamer for copyright clearance |
| V2-07 | CLIVOX creative producer | Verified selected segment, approved legal terms, original hook/story/voice, crop intent | Edit Decision List (EDL) + attributable commentary | Copy-only compilation or synthetic imitation of creator voice |
| V2-08 | Renderer + QA | EDL + scoped licensed private footage + permitted music/sfx | 1080×1920 H.264 AAC review MP4, SRT, QA and hash manifest | Upload/public thumbnail leak, crop off faces, misquote, audio clipping |
| V2-09 | Owner final approver | Exact video, A2 grant identity, game/music proofs, source quote/context, A5 QA | New owner-signed exact-media claim/release | Agent-generated approval, reusing previous signed file after editing |
| V2-10 | Release controller | Signed exact bytes, protected Clivox OAuth, immutable upload intent | Private-first real YouTube ID, verified status and permitted schedule | Wrong channel, duplicate upload, unapproved immediate public release |
| V2-11 | Channel-own analytics | Real authenticated CLIVOX data, own release IDs | Evidence-driven hypotheses, not virality guarantee | Bots, impression manipulation, fabricated missing metrics |

Automation **can** propose and test; sensitive legal, identity, final-video and publication decisions require trusted humans.

## 4. Rights contract: acceptance rules before any media

Required independent yes/no answers, all backed by current evidence:
- Actual video owner / streamer / rights administrator has verified authority; a rep's contract can bind that owner; no impersonation.
- Commercial, advertising-supported YouTube clips on **CLIVOX**, in the relevant territory, with selected timestamps and transformation, attribution, future distribution and possible revenue terms.
- Permission to store/edit original **delivered source file** in the approved private vault; separate authorization path for Twitch clip editor credentials, if applicable. **Do not infer YouTube server-download permission.**
- Game publisher commercial creator rules, independent streamer overlay/music/stock/SFX, guest faces/voices, sponsor logos, TV/film overlays and image rights are resolved or removed.
- Effective dates and expiry, revocation channel/response, contact route, claims response, limits on original edit IP and sponsorship.
- Editor watches original context; quote not cut to imply another claim; accurate creator credit URL and consent-specified attribution.
- Agent and repository cannot mint rights; only authenticated rights-holder/human approvals. Trust keys/certificates independently enrolled before live grant.
- A2 rights grant is refreshed **again** before source acquisition and again before upload and scheduling; any revocation / uncertain state blocks.

A Content ID check, an absence of claims, YouTube CC BY marker, a Twitch clip endpoint or a creator saying "you can clip" are **not substitutes** for the above complete set.

## 5. Media / highlight engineering

**Legal inputs first.** The source can be hours long; perform bounded, staged processing on temporary approved runner workspace:
1. \`ffprobe\` source tracks, duration/resolution, audio streams, frame rate and hash. Reject altered, massive, missing or unauthorized media.
2. Separate 16-kHz mono ASR proxy using FFmpeg; retain original untouched. On CPU test **faster-whisper tiny/base int8** for English/Hindi and use **whisper.cpp** fallback; pin exact model weights + license and use only authorized transcripts. ASR is fallible; avoid assuming automatic word alignment.
3. Audio intensity, speech-rate/pause, laughter/yell/surprise **heuristics**; optional Silero-VAD speech regions. Gaming screams may cause ASR hallucination, so require human listening.
4. Shot changes with PySceneDetect; detect on **selected candidate windows** rather than running expensive dense ML over 10-hour streams. Scene activity is not inherently entertaining.
5. For Twitch channel-editor authorized cases, \`Get Clips\` returns existing clip popularity and optional \`vod_offset\`. \`Get Clips Download\` requires explicit editor/channel scopes; separate license still needed. Clip view counts are *signals*, not a legal or viral guarantee.
6. Segment candidates with context: [lead-in 1–3s] + [action/reaction/punchline 15–40s] + [payoff/CTA 1–3s], total **25–55s only as an initial creative experiment**. Leave longer if a full thought requires it; Shorts up to 3 minutes supported but >1-minute actively claimed Shorts blocked.
7. Story editor adds a truly original thesis, explanation, comedic comparison, editorial reaction, or contextual summary. Do not insert facts not in source, fabricate quotations, misidentify people or create fake creator voice.
8. Editable EDL JSON: licensed source file SHA, exact in/out frames/timebase, speed/crop, overlay/voice rights source, caption segments, music licenses, title/description and dependencies. This is NOT a proprietary platform-derived highlight dataset.
9. FFmpeg produce both QA preview and final 9:16 (1080×1920, H.264, yuv420p, AAC). Preserve recognizability and source credit; put game frame + facecam in context-aware layout; safe captions; no watermarks implying creator ownership.
10. Independent A5 \`ffprobe\`, decoded H.264 subtitle ink/frame sampling, SRT bounds, audio peak/energy/sync, real words verified **by human**, short CTA safe area, black frames, duplicate hashes, privacy checks, asset license manifest.
11. Render exact source-version hash; invalidates all A6 signatures after *any* change, including title, description, source bytes, audio or subtitle.

**Ranking** is separate and optional: original human/audio/visual *editorial attributes* such as clarity in first second, surprise/punchline, standalone comprehension, safe transformation opportunity, visual movement and caption readability. A binary right-grant gate precedes all ranking. **No automated model predicts virality**. See [Evaluation Protocol](EVALUATION_PROTOCOL.md).

## 6. State machine and immutable evidence

\`DISCOVERED → RIGHTS_PENDING → RIGHTS_VERIFIED → MEDIA_DELIVERED → SOURCE_QA_PASS → HIGHLIGHTS_PROPOSED → HUMAN_CANDIDATE_SELECTED → EDIT_PROPOSED → PREVIEW_QA_PASS → FINAL_OWNER_REVIEWED → EXACT_RELEASE_SIGNED → PRIVATE_UPLOAD_ATTEMPTED → REMOTE_PRIVATE_READBACK → SCHEDULE_APPROVED → SCHEDULED → ANALYTICS\`.

At every stage: \`DENIED\`, \`REVOKED\`, \`EXPIRED\`, \`QUARANTINED\`, \`UNAVAILABLE\` and \`UNRESOLVED_UPLOAD\` are fail-closed states. Never skip states or silently retry ambiguous upload.

Immutable **internal** case keys: creator_id, platform/channel/video IDs, rights case UID, source version SHA, license evidence fingerprint, allowed timestamp scope, content scope, A2 ledger head, EDL SHA, render SHA, owner signing ID and expiration, exact target Clivox ID, platform video ID, release attempt UID, edit/metadata version. Private details (contracts/contact, actual files/transcripts) are separate and unexposed.

\`\`\`text
source_reference (public metadata only, short-lived API-data TTL)
  -> rights_case (PENDING; authenticated human-only acceptance)
  -> media_manifest (PRIVATE; license-bound source SHA)
  -> candidate_segments (PRIVATE; timestamped evidence)
  -> creative_edit_spec (PRIVATE; original commentary and transformation rationale)
  -> final_media_manifest (PRIVATE; MP4/WAV/SRT/metadata hash)
  -> A6_exact_asset_release (signed/owner; independently verified)
  -> A8_attempt_ledger (single writer, idempotency, CAS, readback)
  -> clivox_owned_analytics (scoped OAuth)
\`\`\`

### Security threat model

Untrusted creator descriptions, captions, transcripts, audio instructions, subtitles, links, PR text and creator-name lookalikes must be treated strictly as **data**, not tool instructions. Block prompt-injection attempts, SSRF, non-HTTPS or non-allowlisted endpoints, local path traversal, symlink escapes, CSV formula injection, ZIP bombs, media decoder exploitation, inconsistent claimed creator identity, expired grants, race between rights approval and upload, forged signature flags, role crossover (researcher gaining OAuth write privileges), ambiguous retry duplicates, public artifact leaks, incorrect channel ID and release-after-revocation. Demand bounded sizes/times, sandboxed tools, pin dependencies/actions, robust log-redaction, least privileges and immutable audit evidence.

### Platform API data retention and policy contract

- YouTube API non-authorized metadata is temporary, **not longer than 30 days**; obey refresh/deletion and data visibility/usage rules. Do not construct platform-derived engagement ratios, view velocity, cross-channel totals, generic "YouTube insights" or other prohibited derived measurements from API Data.
- Search/list documentation as checked in November 2026: daily \`search.list\` bucket defaults to 100 calls/day at **1 quota unit per call** (recheck quota project live), \`videos.list\` costs 1 unit, combined other bucket defaults 10,000; app/API restrictions still apply. Do NOT use older \`search.list=100 units\` assumption.
- YouTube Analytics audience retention is authenticated **for the owner**, not available for third-party channels without separate authorization; API citations are not evidence that CLIVOX has that access.
- Twitch API Clips can return \`view_count\` and nullable \`vod_offset\`, but accessing clip media downloads requires proper creator-editor OAuth permissions and compliance; metadata does not grant commercial redistribution.
- A live YouTube API upload must satisfy its user-facing terms/consent notices. Scope only Clivox, check channel ID via authenticated response, no unapproved background writes.
- Do not conceal sources, obscure sponsor declarations, mislabel AI-modified real individuals or publish manipulated quote/context; review YouTube synthetic-content disclosure requirements.

## 7. Operations and economics

**Zero incremental subscription baseline:** Python 3.12, FFmpeg/ffprobe, faster-whisper or whisper.cpp tiny/base model, Silero VAD CPU, PySceneDetect, optional Kdenlive/LosslessCut for editor-only local review, GitHub Actions standard public runners for *open synthetic fixtures and non-sensitive source code*, public YouTube API quota under current limits, Twitch Helix only when credentials lawfully authorized. Free tools are not free content licenses. Public GitHub runners are not a rights-compliant private media vault; partner content and credentials require approved owner-controlled private storage and protected Actions environments, with possible included-tier limits.

**Compute guardrails (starting proposals, not measured guarantees):** one source and <=60 min at a time; lower-res/mono proxies; candidate preselection before ASR; CPU model tiny/base; short render experiments; 2GB input cap *subject to licensed agreement*, 30-minute max worker timeout per job until profiling, model cache only if license/storage permits, cap output 3 candidates per media. Avoid blindly processing 12-hour livestreams on free Actions or depending on paid SaaS "free trials".

**Release volume:** first seek 1–3 genuine commercial creator agreements; run 3–5 licensed-media candidate proofs privately; publish a single owner-approved **private-first** pilot; inspect day 1/3/7/14 outcomes. Scale to 2 Shorts/day or any long-form production only after measured capacity, legal supply, rights renewal and editorial quality. Throughput goals are *not publication instructions*.

**Revenue:** YPP requires both numerical eligibility and channel-level reused/inauthentic-content review. The verified official levels include 500 subscribers + 3 valid uploads + 3000 long-form hours / 3M qualified Shorts engaged views for early fan-funding eligibility (where available); and 1000 + 4000 long-form hours / 10M qualified Shorts views for ads. Creator contracts may allow or forbid ad share, sponsorship or reuse. YouTube notes Shorts public "views" are starts/replays since March 2025 (and extended play-start view standard to other formats August 2026); do not conflate public view starts with engaged views for YPP/quality. Creator fee/revenue share, sponsorship, production service, original long-form editorial show and authorized affiliate offers are *potential* revenue avenues; never promise payouts.

**Learning:** measure only **actual CLIVOX** authorized Analytics/Studio engaged views, stayed-to-watch, retention, average viewed %, share rates and subscriber change, missing-as-null. YouTube Studio native thumbnail/title A/B tests **do not support Shorts**; preregister and manually compare staged Shorts cohorts as observational experiments, not randomized platform experiments. No vanity-score optimization or forced engagement.

## 8. Decisions and dependencies

- **DEC-01**: retain current source-free arcade content as **technical fixtures only**; never substitute for creator clips.
- **DEC-02**: **do not implement live API-backed analytics scoring** until A1 developer-policy audit and rewrite.
- **DEC-03**: video sourcing via a **direct creator-provided original file** or audited official editor pathway; no generic public URL downloading.
- **DEC-04**: metadata research/watchlist does not approve rights, outreach or contact.
- **DEC-05**: choose engine-first FFmpeg offline, not paid clipping SaaS. LLM assistance optional and only locally/when privately vetted.
- **DEC-06**: keep native media, licensed contracts and creator notes in private vault; public repo only designs/code/sanitized synthetic tests.
- **DEC-07**: hard stop on any unanswered copyright, reused-content, fake-news/deepfake, identity or platform restriction.
- **DEC-08**: owner decisions required to acquire license, approve secure storage, enroll credentials/signing authority and issue first upload approval; no self-authorizing CI.
- **DEC-09**: global scope may attract English speakers, but first production language/editorial dialect selected from real partner and audience data; Hindi subtitles or dub are separate license/voice-clearance review.

For phased acceptance checklists, mocks, dependency graph and the **first proposed integration**, see [Phased Integration Plan](PHASED_INTEGRATION_PLAN.md). For sources and accuracy, see [Policy/Research Evidence](POLICY_AND_SOURCE_EVIDENCE.md), [Free Tooling](FREE_TOOLING_AND_COST.md), [Creator Research Watchlist](CREATOR_RESEARCH_WATCHLIST.md), and [Evaluation Protocol](EVALUATION_PROTOCOL.md). All are *design references*; no new production modules or write-enabled workflows exist in this plan PR.
