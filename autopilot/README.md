# FlowMinute Cloud Autopilot — ₹0 foundation

> **Phase 3B (17 October 2026):** [Actual synthetic media/rights preflight report](PHASE3B_MEDIA_RIGHTS_REVIEW_2026_10_17.md). `media_rights_review.py` checks actual FFmpeg video/audio streams, measured hashes, current screenplay/voice/subtitle bindings, and hashed local declared license files; the MP4 inspector also verifies H.264/AAC codecs. [Full CI: 221 tests + 6 subtests passed](https://github.com/Tirthanand17/taskless-lab/actions/runs/39038547204). **These are technical inspection and claimed-evidence checks, not natural voice/creative quality or legal license approval. Uploads OFF.**

> **Phase 3 (17 October 2026):** [Production handoffs and audio/SRT QA](PHASE3_MEDIA_PRODUCTION_2026_10_17.md) are now coded and software-CI tested: reviewed-script storyboards, distinct narrator profiles, claimed audio metadata, English/Hindi subtitle timelines, render recipes, actual FFmpeg narration-file technical inspection, and safe SRT text export. [Full repository CI: 202 tests, 6 subtests passed](https://github.com/Tirthanand17/taskless-lab/actions/runs/39037503878). These are **draft contracts plus synthetic media tests**—no real Hindi/English narration, video, rights approval, upload, scheduling or cloud deployment was produced.

> **Phase 2 (17 October 2026):** [Research → fact review → bilingual script staging and language review](PHASE2_RESEARCH_LOCALIZATION_2026_10_17.md) is now connected to the bounded Master DAG by `phase2_pipeline.py` (27 focused regression tests). English and Hindi versions must have a separate matching language-review record before narration planning. [Full GitHub CI: 169 tests and 6 subtests passed](https://github.com/Tirthanand17/taskless-lab/actions/runs/39036189001). Inputs are independently submitted draft artifacts, not autonomously created scripts, verified real facts, or live cloud services. **Uploads and scheduling OFF.**

> **NEW — Hierarchical 8-department agent architecture (17 October 2026):** [Full researched architecture and ordered implementation roadmap](FULL_AUTOPILOT_ARCHITECTURE_2026_10_17.md). [Deterministic master orchestrator](agent_org.py) defines 48 limited specialist roles, 18 staging handoffs per video, at most 3 active videos/9 queued, safe bounded retries and local checkpoint recovery. [Offline demonstration](agent_org_demo.py) never uploads; [25 GitHub CI tests passed](https://github.com/Tirthanand17/taskless-lab/actions/runs/39034764977). The wider [Content Quality Gate](https://github.com/Tirthanand17/taskless-lab/actions/runs/39034919120) passed **141 tests** after adding FFmpeg to its CI environment. **Neither orchestration nor publishing is cloud deployed.** No paid API usage, new provider, laptop access, secrets, or media uploads.

> **Adaptive growth workstream (17 October 2026):** [Implementation and tested limits](THREE_WORKSTREAM_IMPLEMENTATION_2026_10_17.md). New `calendar.py` and `preview_calendar.py` support 90 draft monthly release slots and exact temporary/weekend overrides; `editorial_gate.py` and `launch_gate.py` enforce pre-render evidence, rights and launch fact-check gates. **78 local isolated tests passed**, including synthetic FFmpeg file inspection and atomic ledger bridge checks. This is planning/review code only, not deployed to YouTube or Cloudflare; uploads and scheduling remain disabled. Existing legacy fixed-slot reservations are preserved; adaptive local SQLite reservations now have a tested bridge, but the private production/cloud ledger is not connected. No laptop was used.

**Cloud research and hosted render smoke: tested. Autonomous production and YouTube publishing: NOT DEPLOYED.**

This repo is PUBLIC and must NOT store YouTube OAuth refresh tokens, personal account data, private drafts or privileged self-hosted runners.

## Working cloud foundation
- `core.py`: exact IST release windows, fail-closed source and media gates, SQLite idempotency and approved-provider budget limits.
- `scout.py`: scheduled GitHub-hosted RSS/Atom **unverified topic leads** (not independent fact confirmation or AI-generated scripts).
- `growth.py`: statistically gated, format-separated, age-matched audience-analysis logic (requires real Analytics measurements, not connected to a cloud account yet).
- `cloud_guard.py`: laptop use OFF by default, private cloud worker and approved zero-budget preflight.
- `test_core.py`, `test_cloud_foundation.py`: security/quality unit tests.
- `.github/workflows/flowminute-cloud-scout.yml`: daily 18:45 IST topic source scout after merge to default branch, runs on FREE standard public GitHub runner, no stored artifacts, no tokens and no publish permissions. Source leads are visible in Actions logs only.
- `.github/workflows/flowminute-cloud-render-smoke.yml`: cloud-only rendering probe using a **previously published** Short and existing audio: 60 frames, 1080×1920, H264+AAC, FFmpeg full decode, thumbnail. Outputs deleted at job end. This does not benchmark full daily videos.
- `.github/workflows/flowminute-full-pack-benchmark.yml`: no-secret, no-publish complete **2 Shorts + 1 long** cloud render benchmark on standard free public Ubuntu runner. Triggered by the workflow's source commit on October 16; validate actual run result before calling it a PASS. QA checks full decode and sizes; it deletes outputs, does not store video artifacts or upload anything. [First full benchmark run](https://github.com/Tirthanand17/taskless-lab/actions/runs/38866227531).
- The scheduled public scout now writes a **GitHub Actions run summary** for leads; this is NOT a verified editorial plan and does not contact YouTube accounts.

## Hard stop before production
Private control repo/isolated secrets and verified YouTube OAuth, durable media storage, legitimate source-backed research, 3-video full-duration hosted production benchmark, per-frame/caption/audio/rights QA, authenticated scheduling and Analytics adapter are all **missing**. Never call a draft "published."

We are limited to **₹0** monthly. No Render cron or paid service may be created, no paid API use, no Google OAuth connection without explicit owner approval. Existing Nirala/Windows jobs are outside authorization. Cloud-only `/app/work` path is enforced for the future publisher.

Run tests:
```bash
python -m unittest discover -s autopilot -p 'test_*.py' -v
python -m pytest -q
```

See [migration and optional owner-run Windows-job disable guide](../docs/FLOWMINUTE_CLOUD_AUTOPILOT_MIGRATION_V2.md).
