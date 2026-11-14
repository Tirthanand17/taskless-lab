# CLIVOX V2 — Phased Integration Roadmap and Acceptance Plan

**Research 2026-11-14; P1 integration verified 2026-11-14.** P0 architecture and P1 score-free API-source/rights/provenance code are completed on GitHub using synthetic CI data; no live creator metadata key, permissions, source downloading, clip renderer, outreach, uploads or publishing are enabled. Other phases remain a blueprint. Existing FlowMinute Branches 1 and 2 remain untouched.

## Critical dependency sequence

| ID | Feature and planned work | Gate to move forward | Verified status |
|---|---|---|---|
| **P0 — COMPLETE** | V2 master architecture, primary-source policies, tooling, creator research, evaluation and integration gates | [PR #203](https://github.com/Tirthanand17/taskless-lab/pull/203) merged with CI green | **COMPLETE DESIGN / NO LIVE CLIPS** |
| **P1 — COMPLETE SOURCE-ONLY** | Removed API-derived views/engagement source scores, rewired A2 pending cases and strict A123 handoff, seven-day metadata expiry | [PR #204](https://github.com/Tirthanand17/taskless-lab/pull/204) 24/24 green plus [main CI #43577935757](https://github.com/Tirthanand17/taskless-lab/actions/runs/43577935757) success | **VERIFIED OFFLINE; NO API KEY, MEDIA OR UPLOAD** |
| **P2 — TECHNICAL INTEGRATION UNDER CI** | Curated five public creator-branded business inquiry pages; strict no-contact prospect validator, **unsent** three-private-Short pilot proposal drafts, privacy-adversarial CI | Owner still must authentically reverify identity/route and personally select 3–5 partnership prospects; no creator contacted or approved by AI | **ENGINEERING IN REVIEW; HUMAN SHORTLIST PENDING** |
| **P3 — TECHNICAL SCOPE VERIFIED** | Implemented 30 unanswered commercial rights/identity clauses per prospect and two unlinked synthetic A2 pending cases. Rejects forged approvals; [PR #208](https://github.com/Tirthanand17/taskless-lab/pull/208) passed 4/4, [main run #43580815591](https://github.com/Tirthanand17/taskless-lab/actions/runs/43580815591) succeeded | Need actual human-verified commercial grant, publisher/music/guest rights, private evidence, real reviewer keys and complete fresh revocation state | **ENGINEERING DONE; 0 REAL LICENSES / HUMAN BLOCKED** |
| **P3T (optional)** | Twitch Helix Get Clips references; only creator-authorized editor Clip Downloads API after distinct actual commercial permission | Authenticated editor scopes **and** verified commercial reuse grant | **NOT STARTED** |
| **P4 — SYNTHETIC TECHNICAL QA VERIFIED** | Reuse closed A3 storage policy; added local SHA-256/byte/MP4 H.264/AAC/decoded-frame checks against a **new synthetic runner-only fixture**. See [P4 quarantine runbook](P4_SYNTHETIC_PRIVATE_MEDIA_HANDOFF.md). No actual media delivered or private vault provisioned | Owner-approved and privately audited vault, genuine creator-issued complete rights and direct delivery of at least one licensed file; no public Git/artifact leak | **TECHNICAL FIXTURE VERIFIED [main run #43583149761](https://github.com/Tirthanand17/taskless-lab/actions/runs/43583149761); REAL P4 NOT COMPLETE** |
| **P5 — SYNTHETIC SIGNAL QA VERIFIED; REFERENCE EVALUATOR UNDER CI** | Source-free acoustic RMS/luma-cut proposal extractor verified on main; now adds a synthetic golden-event overlap/false-positive/missed-event evaluator and direct CI handoff. [P5 signal runbook](P5_SYNTHETIC_SIGNAL_CANDIDATE_QA.md), [P5 synthetic evaluator](P5_SYNTHETIC_REFERENCE_EVALUATION.md). No ASR, VAD, PySceneDetect, real footage or viral prediction | Genuine eligible sources, private rights/creator-approved ASR/scene pipeline, 40–60 editor-labeled legal moments, top-5 suggestion evaluation | **SOURCE-FREE [P5 main QA #43585035896](https://github.com/Tirthanand17/taskless-lab/actions/runs/43585035896) SUCCEEDED; REAL P5 NOT COMPLETE** |
| **P6** | Original CLIVOX editorial commentary, honest source-context checks, segment edit-decision-list (EDL), human selected time boundaries | Human confirms quoted content, original value, guest rights, attribution; storyboard private | **NOT STARTED** |
| **P7** | New licensed-source 9:16 FFmpeg video compositor with real creator video + original narrative, SRT, sound design, frame/caption/crop/sync technical checks | New H.264/AAC video passes real independent A5 QA and is stored privately | **NOT STARTED** |
| **P8** | Owner exact-final media playback, true voice/speaker verification, rights freshness, contract/music checks and A6 detached signature | Trusted key enrolled and 1 authentic signed exact-final-media owner authorization | **NOT STARTED** |
| **P9** | A7/A8 real Clivox-only OAuth, approved protected environment, private-first YouTube upload, full remote readback and idempotent ledger, optional explicit schedule | Correct channel ID + one **owner-approved** real video in private YouTube Studio | **NOT STARTED** |
| **P10** | Authenticated CLIVOX account-only analytics, official engagedViews, Stayed to watch, retention, experiment evidence; rights/claim audits | Real published pilot outcomes, report after 24h/72h/7d/14d | **NOT STARTED** |
| **P11** | Scale to recurring approved clips + optional podcasts/interviews; measure costs and publisher/creator supply | Multiple current creator agreements, proven QA/signing/storage and editor capacity | **NOT STARTED** |

V2 roadmap checkpoint progress: **P0 and P1 complete, 2/12 = 17%**. P2 research tooling and unsent drafts are implemented **pending CI and human owner verification**; no further phase is counted complete. The remaining 10 nonoptional phases are not complete. This unweighted percent is **not product/clip readiness**. The older Branch 3 fictional arcade 78% is a separate scope and must not be presented as clipping progress. Licensed real-world clipping and publishing are still at zero.

## P1 implementation — completed on merged PR #204

The following engineering brief was implemented and verified; it remains as a reproducibility checklist. New work moves to P2 without bypassing creator consent and media rights.


**Do not create a second discovery service; revise the existing module.**

1. Inspect all uses of YouTube API statistics and composite ranking in the existing source file scripts/branch3_discovery.py, including test fixtures.
2. Remove or disable algorithmic view-velocity/engagement ratios and weighted derived popularity scores. Policies: https://developers.google.com/youtube/terms/developer-policies ; especially API Data derived-score and cross-owner aggregation constraints.
3. Preserve safe canonical source ID, fixed API hostname, source URL, immutable provenance and raw API response values only as current/attributed and within retention. Ranking by **independent editorial observations** after lawful access to media is a separate function and not based on public platform API statistics.
4. Update scripts/branch3_rights_case_intake.py to read the modified **research-only** A1 schema. No score can advance rights from pending to verified. Keep creator permissions registry empty.
5. Update source-free unit/negative tests, data-reuse/deletion checks, cache/max age <=30 days, cross-channel boundary and no platform-media downloads.
6. Recheck current documented quota: YouTube search.list separate default 100 calls/day at cost 1 unit each (as of Nov 2026), videos.list at 1 unit; project-level quotas may vary.
7. Run GitHub PR workflows, merge only once green, verify main; record new compliance evidence and never enable actual metadata API key, publisher credentials, live creator search, rights approvals or upload in P1 without separate authorization.

**Acceptance:** no forbidden statistics-derived metric generated; tests pass; rights remain UNVERIFIED, no copyrighted video import, API calls bounded, user Clivox channel ID checked, no impact on Branch 1/2. This is a **compliance hardening change**, not a new verified clip or release.

## P2 creator research and licensing preparation

- Reconfirm official target creator links and relevant primary content categories; big names IShowSpeed/Kai Cenat/CaseOh/Jynxzi/Techno Gamerz/CarryisLive etc are *examples*, not authorized licensors.
- Prioritize small-to-mid-size creators actively seeking a Shorts clip editor or revenue-share distribution partner; avoid unverified "clip anyone" claims.
- Human owner approves whether to send a written inquiry. Include exact Clivox channel and a proposed 3-short privately reviewed licensing trial. **No automated outreach is authorized by architecture.**
- Legal grant should explicitly cover: source IDs and delivery, commercial monetization, edited clips, original commentary, territory, timestamps, expiry/revocation, credit, game/music/guest clearances, final edit rights, creator claim protocol, compensation/revenue split, notice method and claim handling.
- Signed permission/contract data and contact details remain private; source watchlist and public URLs only in Git.

## P3T Twitch option

- Official Twitch API Get Clips can list existing highlight metadata and sometimes VOD offsets, with app/user token and rate limits.
- Get Clips Download is only possible under broadcaster/editor OAuth with appropriate editor scopes, **plus** commercial rights contract and Twitch developer policy compliance. Do not use unrestricted public downloaders.
- Do not assume a Twitch clip is commercially sublicensable to YouTube. If editor access is revoked, stop and destroy temporary media per agreed retention.

## P4 private media and storage

- Owner approves actual confidential media storage. Public taskless-lab and public Actions artifacts must not hold restricted creator video.
- Require creator-provided file or permitted Twitch editor delivery, valid grant, exact video SHA, content-length limits, source period, MIME/codec validation and short-lived signed private access.
- No scripts that download arbitrary YouTube/TikTok/Instagram videos by URL. External share URL and actual media file delivery are different.
- Incident test: raw license/creators' video appears in public logs/CI/PR/artifacts => stop and remove/revoke access, not proceed.

## P5 candidate detection experiments

- Start with authorized 10–30 minute sample, not 12-hour full stream. FFmpeg proxy and audio extract -> VAD speech intervals -> small CPU Whisper ASR -> PySceneDetect cuts -> timestamped segment candidates.
- Human editor confirms source context, speaker, real words, payout/guest/game restrictions and a **standalone entertaining complete mini-story**.
- Ranking from observed media and human rubric only, not YouTube Data API derived view/like counts. Must show uncertainty and can always return NO GOOD MOMENT.
- Collect at least 40–60 **legal**, privately labeled moments across multiple approved sources before assessing top-5 suggestion precision. No benchmark score claims without tests.

## P6/P7 real editing

- An edit decision list pins source file SHA, allowed frames/timestamps, all license references, story line, credit, narration, captions and music/sfx licenses.
- Original CLIVOX commentary is substantive: new explanation/joke/analysis/context, not a reused-video montage with crop+auto subtitles.
- Use 1080x1920, H264 yuv420p AAC with 25–55s **creative experiment** length; Shorts can be up to 3 min, but active claims on >1min Shorts can block. Never claim sub-60s is legally safe.
- Audio clipping, sudden flash, quote-context accuracy, SRT text against real spoken words, facecam/game split framing, actual decoded frame ink and QA must all be independently checked.
- Private preview only. If any revision changes audio/frame/title/rights, previous A6 signature invalid.

## P8/P9 real release

- Rights check again just before exact media sign-off and publication. Authorized owner must actually watch video, approve original value, legal source, final metadata and rights.
- Protected GitHub environment + independently enrolled signature verify + explicit Clivox channel OAuth ID + private-first real upload + remote processing/readback.
- No unapproved immediate public video, no schedule before future date, no duplicate upload after ambiguous server reply; use existing CAS/inventory controls. No autonomous rights grant or signature issuance.

## P10 analytics + operational learning

- Only Clivox-owned verified Analytics/Studio: official engagedViews, average view duration/percentage, Stayed to watch when available, retention, shares and subscriber change.
- Existing YouTube public views changed to play-start counts; do not use public starts as monetization payout proxy. Never fabricate inaccessible replay graphs or earnings.
- Review claim/reused-content enforcement and owner/editor response; clips can earn zero even after YPP eligibility if ineligible/claimed.
- YouTube Studio's official A/B thumbnail/title tool does not support Shorts; compare cohorts as observational and mark confounders. Scale only after owner agrees.

## Adversarial acceptance matrix

| Malicious or uncertain case | Required behavior |
|---|---|
| Famous creator video has 10 million views, no grant | Metadata only; no source media |
| Public "Most replayed" curve not in authorized API | No verified retention claim |
| Creator only says "credit me", no monetization grant | Hold |
| Stream has unlicensed song, game, guest or footage | Hold / re-edit with new clearance |
| Twitch clip public, no editor OAuth/creator commercial contract | No download |
| Audio is loud laughter, ASR uncertain | Human listen; no invented quote |
| Source quote context altered to imply false meaning | Reject |
| Captions or facecam cropped after 9:16 rendering | Block and rerender |
| Fake approved flag in YAML/CSV/PR/transcript | Ignore as untrusted data |
| Old owner signature used on new MP4/SRT/title | Reject hash mismatch |
| FlowMinute OAuth supplied for CLIVOX | Reject wrong channel |
| Public artifact includes private media | Fail / incident |
| Timeout during video upload | Remote reconcile, no automatic duplicate retry |
| Missing platform analytics | Null with reason, never invented number |

## Change control and success criteria

Each future integration PR includes exact source-level tests, no-public-source-media proof, threat review, bounded resource/cost statement, separated actor permissions, a real GitHub CI evidence link and explicit state transitions. Synthetic fixture success ≠ real creator license, final human approval or live revenue.

Before **any** media or actual publication: owner separately approves rights, secure storage, API credentials, commercial terms and final clip release. Do not increase the V2 completion metric based on architecture docs alone.

**User instruction honored:** research + architecture FIRST, integration one by one only in a later user turn.
