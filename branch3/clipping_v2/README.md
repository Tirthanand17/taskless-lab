# CLIVOX Viral Clipping V2 — Research and Architecture Index

**Status (2026-11-14): P1 SOURCE-ONLY INTEGRATION VERIFIED IN CI.** Research/architecture P0 and offline YouTube metadata compliance P1 are complete (2/12 roadmap phases, 17% checkpoint progress). **No actual licensed creator clipping pipeline, rights grants, real source media, live metadata API access, or uploads yet.** No real source footage is acquired, scheduled or published. This is the **intended viral-clipping product**, not the earlier fictional-arcade render test system.

## Read in this order

1. [Master Architecture](MASTER_ARCHITECTURE.md): the complete permission-first discovery → licensed acquisition → high-potential moment detection → original commentary → editing → signed release → CLIVOX analytics architecture.
2. [Policy and Primary-Source Evidence](POLICY_AND_SOURCE_EVIDENCE.md): current YouTube/Twitch developer policies, copyright, reused-content/YPP monetization and platform data/rights constraints.
3. [Creator Research Watchlist](CREATOR_RESEARCH_WATCHLIST.md): famous global/India gaming and livestream creators to study and potentially approach, **none authorized**; partner-fit prioritization.
4. [Free and Open-Source Tooling](FREE_TOOLING_AND_COST.md): FFmpeg/ffprobe, faster-whisper/whisper.cpp, Silero VAD, PySceneDetect, official APIs and GitHub Actions resource/privacy trade-offs.
5. [Moment and Experiment Evaluation Protocol](EVALUATION_PROTOCOL.md): human/source-observation scoring only after licensing, context and originality gates; real CLIVOX-owned analytics.
6. [Phased Integration Plan](PHASED_INTEGRATION_PLAN.md): ordered P0–P11, human blockers, exact future P1 API policy remediation and tests.
7. [Architecture Status (JSON)](architecture-status.json): machine-readable, fail-closed **NOT STARTED** V2 status, separate from the older original-fiction engineering percentage.

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
