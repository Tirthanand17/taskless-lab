# CLIVOX Viral Clipping V2 — Research and Architecture Index

**Status (2026-11-14): P0/P1 COMPLETE; P2/P3/P4/P5 TECHNICAL OFFLINE PROTOTYPES VERIFIED, REAL CREATOR RIGHTS AND MEDIA STILL BLOCKED.** Research/architecture P0 and offline YouTube metadata compliance P1 are complete (2/12 roadmap phases, 17% checkpoint progress). **No actual licensed creator clipping pipeline, rights grants, real source media, live metadata API access, or uploads yet.** No real source footage is acquired, scheduled or published. This is the **intended viral-clipping product**, not the earlier fictional-arcade render test system.

## Read in this order

1. [Master Architecture](MASTER_ARCHITECTURE.md): the complete permission-first discovery → licensed acquisition → high-potential moment detection → original commentary → editing → signed release → CLIVOX analytics architecture.
2. [Policy and Primary-Source Evidence](POLICY_AND_SOURCE_EVIDENCE.md): current YouTube/Twitch developer policies, copyright, reused-content/YPP monetization and platform data/rights constraints.
3. [Creator Research Watchlist](CREATOR_RESEARCH_WATCHLIST.md): famous global/India gaming and livestream creators to study and potentially approach, **none authorized**; partner-fit prioritization.
4. [Free and Open-Source Tooling](FREE_TOOLING_AND_COST.md): FFmpeg/ffprobe, faster-whisper/whisper.cpp, Silero VAD, PySceneDetect, official APIs and GitHub Actions resource/privacy trade-offs.
5. [Moment and Experiment Evaluation Protocol](EVALUATION_PROTOCOL.md): human/source-observation scoring only after licensing, context and originality gates; real CLIVOX-owned analytics.
6. [Phased Integration Plan](PHASED_INTEGRATION_PLAN.md): ordered P0–P11, human blockers, exact future P1 API policy remediation and tests.
7. [Architecture Status (JSON)](architecture-status.json): machine-readable, fail-closed V2 implementation state, separate from the older original-fiction engineering percentage.

## P3 licensing scope questions — engineering verified; real grants pending

The new [P3 commercial rights scope quarantine](P3_LICENSING_SCOPE_INTAKE.md) generates strictly **unsigned** requests for commercial YouTube redistribution and checks 30 terms/rights issues per public prospect. It is merged in [PR #208](https://github.com/Tirthanand17/taskless-lab/pull/208) with **4/4 PR checks passed**, and the [merged-main P3 scope test #43580815591](https://github.com/Tirthanand17/taskless-lab/actions/runs/43580815591) **succeeded**. It reuses existing A2 no-grant policy, authentic pending-case validation and two **synthetic, unlinked** source references. It never asserts that a source video belongs to a prospect and never grants download, editing or upload permission. A real rights-holder's authenticated commercial license, durable revocation evidence, owner-signed approval and secure contract/media vault remain outstanding. **The phase roadmap remains 17%** until actual milestones pass.

## P2 creator prospect research tooling — verified, human selection pending

The first [P2 creator prospect research intake](P2_CREATOR_PROSPECT_INTAKE.md)
uses [five creator-branded public business references](prospects/public-business-pages-2026-11-14.json)
(Ankitt, Eggmilk, Mr JD Gaming, MandarriaXL and CaseOh). The
[offline-only pipeline](../../scripts/branch3_v2_creator_prospect_intake.py)
validates them and generates recipient-less **UNSENT** trial proposal drafts
for a human owner to inspect. The dedicated GitHub Action
`branch3-clivox-v2-p2-prospect-intake.yml` never contacts creators or
downloads footage. **No legal identity, contact deliverability, owner
shortlist selection or commercial rights have yet been verified.**

P2 engineering is merged in [PR #206](https://github.com/Tirthanand17/taskless-lab/pull/206) with **4/4 passing PR checks**; the [actual main no-contact generator run #43579381280](https://github.com/Tirthanand17/taskless-lab/actions/runs/43579381280) **passed**. The actual human owner must still verify creator identities/business routes and select which 3–5 to approach. Therefore the **verified overall roadmap remains 2/12 (17%)**, separate from the old 78% source-free fictional media engineering estimate.

## P1 verified and the next workstream

[The P1 metadata/rights/provenance integration](P1_API_COMPLIANCE_IMPLEMENTATION.md) is now merged and validated on `main` with **24/24 PR CI** and [successful A1→A2→A3 source-safe integration run #43577935757](https://github.com/Tirthanand17/taskless-lab/actions/runs/43577935757). Public API derived viral scores were removed and a seven-day expiry plus strict deny-state lineage were added. The roadmap is **17% by phase count**, not 17% of a licensed media clipping/publishing product. No third-party licenses or uploads exist.

**Next P2:** approved creator prospect research and lawful partnership/outreach plan, with no unsolicited contact without permission; later real licensing/storage and highlight detection remain separately gated.

## First recommended integration *after* user authorizes engineering

**P1 is now implemented and verified in source-only GitHub CI.** The remaining high-priority work is P2 partner prospect verification and P3 real licensing before any approved video source acquisition. Do not mistake P1 synthetic checks for a functional clip-producing system.

**Guardrails:** Public GitHub only for code, docs, sanitized test metadata and original synthetic fixtures. Restricted creator media, contracts and private notes must be in separately approved confidential storage. User's laptop storage is not required. FlowMinute Branches 1 and 2 must remain unchanged.

## P4 synthetic-source technical QA (no creator media)

[P4 quarantined media integrity and format preflight](P4_SYNTHETIC_PRIVATE_MEDIA_HANDOFF.md) tests an FFmpeg-generated tiny synthetic sample on a temporary GitHub runner and rejects forged rights/vault/media switches. Engineering was **verified on main** in [P4 feature PR #210](https://github.com/Tirthanand17/taskless-lab/pull/210), [synthetic technical QA #43583149761](https://github.com/Tirthanand17/taskless-lab/actions/runs/43583149761) and [main Content Quality Gate #43583149710](https://github.com/Tirthanand17/taskless-lab/actions/runs/43583149710), implementation SHA `1f23a5081a1e6a75b256c58be6116f496d157b69`. The dedicated PR workflow and all three PR checks passed. No creator source downloads, private vault provisioning, genuine granted licenses, editing or YouTube uploads are enabled. Real P4 milestone remains blocked, and the verified V2 roadmap is still **2/12 = 17%**.

## P5 synthetic candidate timecode prototype (main CI verified)

[P5 source-free acoustic RMS + scene-cut proposal QA](P5_SYNTHETIC_SIGNAL_CANDIDATE_QA.md) generates only local, bounded **candidate evidence windows** from a newly generated synthetic MP4 using FFmpeg. The dedicated [merged-main P5 CI run #43585035896](https://github.com/Tirthanand17/taskless-lab/actions/runs/43585035896), [P4 regression #43585035920](https://github.com/Tirthanand17/taskless-lab/actions/runs/43585035920) and [main Content Quality Gate #43585036042](https://github.com/Tirthanand17/taskless-lab/actions/runs/43585036042) succeeded after [4/4 green PR #212 checks](https://github.com/Tirthanand17/taskless-lab/pull/212). This is not licensed footage processing, voice recognition, quote verification or a viral performance forecast. The existing P2/P3 legal and P4 private media/vault blockers remain, real P5 is not complete, and progress is still **2/12 = 17%**.

## P5 source-free candidate reference evaluator (CI pending)

[P5 synthetic reference evaluator](P5_SYNTHETIC_REFERENCE_EVALUATION.md) connects actual generated-scene/acoustic detector JSON to **generated synthetic golden events**. The test detects matched time windows, misses and false positives, rejects forged licenses, fabricated text/platform analytics, and never calls a real human-labeled result validated. It is not real creator-source processing, quality/retention estimation or publishing readiness. Dedicated CI pending; real phase progress stays **2/12 = 17%**.
