# CLIVOX Viral Clipping V2 — Research and Architecture Index

**Status (2026-11-14): RESEARCH / DESIGN ONLY.** No V2 production integrations have started. No creator has licensed content to CLIVOX; no real source footage is acquired, uploaded, scheduled or published. This is the **intended viral-clipping product**, not the earlier fictional-arcade render test system.

## Read in this order

1. [Master Architecture](MASTER_ARCHITECTURE.md): the complete permission-first discovery → licensed acquisition → high-potential moment detection → original commentary → editing → signed release → CLIVOX analytics architecture.
2. [Policy and Primary-Source Evidence](POLICY_AND_SOURCE_EVIDENCE.md): current YouTube/Twitch developer policies, copyright, reused-content/YPP monetization and platform data/rights constraints.
3. [Creator Research Watchlist](CREATOR_RESEARCH_WATCHLIST.md): famous global/India gaming and livestream creators to study and potentially approach, **none authorized**; partner-fit prioritization.
4. [Free and Open-Source Tooling](FREE_TOOLING_AND_COST.md): FFmpeg/ffprobe, faster-whisper/whisper.cpp, Silero VAD, PySceneDetect, official APIs and GitHub Actions resource/privacy trade-offs.
5. [Moment and Experiment Evaluation Protocol](EVALUATION_PROTOCOL.md): human/source-observation scoring only after licensing, context and originality gates; real CLIVOX-owned analytics.
6. [Phased Integration Plan](PHASED_INTEGRATION_PLAN.md): ordered P0–P11, human blockers, exact future P1 API policy remediation and tests.
7. [Architecture Status (JSON)](architecture-status.json): machine-readable, fail-closed **NOT STARTED** V2 status, separate from the older original-fiction engineering percentage.

## First recommended integration *after* user authorizes engineering

**P1: YouTube Data API derived-metrics compliance hardening in existing A1 discovery**. The current metadata-only adapter has derived view velocity / engagement composite scoring that needs current API developer-policy review and likely refactoring before live integration. Preserve existing deterministic source identity, bounds and rights-pending case plumbing; do not build a duplicative crawler. No video download, rights approval or live upload as part of P1.

**Guardrails:** Public GitHub only for code, docs, sanitized test metadata and original synthetic fixtures. Restricted creator media, contracts and private notes must be in separately approved confidential storage. User's laptop storage is not required. FlowMinute Branches 1 and 2 must remain unchanged.
