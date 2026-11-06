# ADR-0069 — B4d5 use the SAME researched topics in every daily plan receipt

**Date:** November 6, 2026 IST. **Scope:** GitHub-only, source/provenance research tasks, unapproved, zero paid API calls and zero YouTube writes.

## Actual independently observed mismatch

After B4d4b (#78) merged, trusted main [run 42218909813](https://github.com/Tirthanand17/taskless-lab/actions/runs/42218909813) **passed**, retained two real JSON receipts in GitHub artifact **13502457323**, and observed 2 full public article pages with one exact RSS entry fallback. Artifact archive was downloaded and read. Two receipts correctly had three episodes and no uploads/claim approval. However the legacy planner receipt's selected publishers were **The Verge, arXiv AI, arXiv AI** because `daily_cloud_plan.build_plan` selected the first three RSS leads. Separately, the B4d2 editorial board selected three topic IDs and differentiated research angles using source evidence. Their topic assignments were not required to match! That breaks the "one story per episode" provenance needed before writing any script or creating unique footage.

## Implementation

- `autopilot/reconcile_daily_editorial_plan.py`: A strict research-only handoff recomputes the FULL B4d2 editorial board from the original scout, original three-slot daily plan and actual exact-source observation report. It rejects a changed headline, URL, source response hash, episode identity, media/rights flag, invented model inference, duplicated topic or forged board, rather than trusting an uploaded JSON file. It finds each exact B4d2 selected unverified story in the original allowed scout leads, validates HTTPS origin, and copies **only the three actual editorial lead assignments and research-angle IDs** into a **new** daily plan. It never overwrites the source original and retains all original 48-agent workflow DAGs, 54 handoffs, IST/UTC schedule slots, zero progress, strict authorization flags and zero-spend settings.
- `autopilot.daily_evidence_bundle` optionally accepts the separate public B4d2 sanitized editorial receipt and checks the same 3 episode IDs, source URL hashes, normalized topic hashes and three creative angle IDs against the newly reconciled plan. It rejects a changed digest, mismatch, absent/approved source, fake release flag or future writer who silently goes back to first-three headlines. The public retained plan receipt now states `editorial_and_plan_reconciled=true` with the matching sanitized editorial receipt SHA256 and selected-count.
- The live GitHub daily workflow generates the same scout/source observer/initial DAG+editorial board as before, then performs one *unprivileged* alignment step. Only the aligned plan is used in the retained public research receipt. The originals and detailed board remain strictly ephemeral, are deleted after the job, and the public artifact contains only two hash-based reports, never titles, article bodies or URLs.
- Adversarial offline tests use the original fake HTTP source batch and simulate changed titles/source hashes, forged storyboard approvals, changed status, altered original scout inputs, swapped episode ID, duplicate source and forged public digest; also verify a genuinely empty-source day keeps all three research slots without fabricated videos.

## What alignment proves—and what it doesn't

A canonical shared research-topic identity is important for avoiding duplicate creative briefs. But stable IDs and source SHA hashes are **not legal source licenses, independent scientific truth checks, evidence quotations, human full watch/listen approval, original generated voice, or YouTube publishing success**. A publisher article HTTP 200 can be misinterpreted, and the arXiv papers remain unreviewed preprints. No raw copyright content is retained or automatically reworded into a fictional script.

Only the GitHub Actions PR and main run will prove both receipts reconcile from live publisher observations. We do not count a successful source-only proof as an independently uploaded daily video. Cloud deployment/owner AWS budget/Google OAuth/real 21-day publishing all remain **unverified and not activated**.

**Working production-readiness estimate remains about 40/100, verified unattended Branch 2 YouTube releases 0/21.**
