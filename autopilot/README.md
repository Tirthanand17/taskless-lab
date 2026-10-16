# FlowMinute Cloud Autopilot — ₹0 foundation

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
