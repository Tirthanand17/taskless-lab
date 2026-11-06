# ADR-0068 — B4d4b retain newly approved source publisher as safe public metadata

**Date:** 2026-11-06 IST. **Scope:** actual post-merge GitHub foundation repair, not an article-truth or upload authorization.

## Exact observed regression

The trusted B4d4 [main GitHub run 42206952486](https://github.com/Tirthanand17/taskless-lab/actions/runs/42206952486) actually fetched **2 complete textual source pages of 3 direct requests**, used one publisher RSS fallback, and left **0 factual scripts**. This is a material improvement from earlier verified 0/3 direct pages.

The run later **failed**, however, during `autopilot.daily_evidence_bundle.build_retained_draft_receipt()` at its `Unexpected unverified research lead` check. That public-artifact validator still had a three-publisher static allowlist (`OpenAI`, `Google DeepMind`, `The Verge`) and had not been updated to include the newly code-reviewed **arXiv AI** official source. All other source observation and three-angle editorial steps succeeded. **No final two-receipt artifact was successfully retained by this failed run.**

## Correct repair

Update the deliberate public receipt allowlist with **arXiv AI**, and require equality to `autopilot.daily_cloud_plan.APPROVED_RESEARCH_ORIGINS` to prevent future silent publisher drift. Before retaining the publisher label, run `evidence_probe.verify_public_source_url` against the actual lead, restricting archive leads to `arxiv.org/abs` and rejecting PDF/search/feed/unknown hosts. This is an additional safety check, not a bypass.

Extend tests to create a real no-authority planner with the new publisher and zero independent claims; verify the small public receipt includes only the publisher label and hashes, **not** the paper title, URL, body or approved content. Also test forging an archive PDF or adversarial source host in a previously constructed plan.

The normal daily GitHub foundation must run unprivileged with only `contents: read`, no paid model/OAuth/costs/YouTube upload, and retain both tiny source-observation and editorial receipts in its standard 14-day public artifact. Exact-head CI and a **post-merge full successful daily run with two actual JSON receipts** are required for accepting the fix.

## Public scout CI reliability and metadata confidentiality

During PR #78's first set of checks, the **separate** source-only `flowminute-cloud-scout.yml` still ran an unnecessary `sudo apt-get update` / `apt-get install ffmpeg` before source unit tests. This can hang on GitHub's mirror and waste Actions minutes despite there being **no video to encode**. The workflow is now explicitly bounded to eight minutes, installs only the cryptographic verifier dependency by pip and executes a curated set of actual RSS/source/claim/authorization tests. Broad decoded-video tests remain enforced separately by the always-on **Content Quality Gate** and the real Cloud Render Smoke; we do not quietly waive media QA.

On the independent public scheduled scout job, raw unverified feed headlines and article URLs were previously printed directly into the public log and job summary. That was unnecessary: a separate daily foundation already retains sanitized SHA-only evidence. The scout now prints only **bounded per-publisher lead counts** (at most six each), tests permitted publisher names, deletes the temporary raw scout file and never archives external article URLs or titles. No scraped article content or full paper is stored; no privileged GitHub token or provider account is used.

The old scout Actions `concurrency.group` was one global constant, so a prior stalled apt install could queue every newer PR and daily check behind the same unrelated job. The new group is keyed by event and ref, with `cancel-in-progress` true **only for stale PR checks**, not for daily scheduled research. This is intended to avoid unnecessary queue delays and duplicate GitHub minutes; real cost savings are not claimed until measured.

Static CI tests guard the absence of `sudo apt-get`, private/paid endpoints, URL logging and source approvals. A passed source-only scout is not a licensed/peer-reviewed fact checker.

## Remaining research blockers

The result of 2/3 is a fetch count, not factual claim confirmation or independent validation. The source text/abstract and rights remain unreviewed; papers' figures may require author permission. No fresh narration scripts or licensed videos were created. No owner cloud or live YouTube release exists: original Branch 2 evidence remains **0/21** independently verified uploads; approximate readiness **40/100**.
