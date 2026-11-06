# ADR-0065 — B4d2 source-observed daily editorial triage, not fabricated news scripts

**Date:** November 6, 2026 (IST). **Track:** Branch 2 laptop-off, GitHub-hosted daily research. **Current production authorization:** zero real YouTube uploads, zero approved cloud deployment, no external paid model requests.

## Verified gap after B4e7

The existing daily GitHub foundation runs a bounded three-publisher RSS scout and optionally obtains three read-only source-byte observations. The planner historically assigned the **first three RSS leads**, without ensuring they refer to **different topics** or even that any of those three matched the source pages subsequently observed. Green source fetches are not independent fact corroboration; the existing optional Gemini `script_draft_agent.py` correctly requires external owner permission, verified provider terms and strict budget. We must not treat unverified headlines as video scripts.

The preceding completed physical source demo proof [run 42197821807](https://github.com/Tirthanand17/taskless-lab/actions/runs/42197821807) did generate real two Shorts and one long **from previously authored** NASA/NIST/USGS scripts. It did *not* research fresh daily topics. B4d2 starts closing that different gap without overriding fact or rights review.

## Implemented

- `autopilot/daily_editorial_board.py` accepts only existing `daily_cloud_plan.build_plan`, `scout.scout` and `evidence_probe.probe_report` schemas. It verifies all no-release/no-media/no-spend fields and exact three IST slots: **11:00 Short, 16:00 long, 20:30 Short**.
- Reconciles source observation ID as the first 24 characters of SHA256(exact HTTPS allowlisted URL), same publisher, **same normalized title**, complete observed-body SHA256 and strict unfalsified status. A source fetch can be `ARTICLE_BYTES_OBSERVED_NO_FACT_APPROVAL`, or an exact matched RSS entry can be `RSS_ENTRY_OBSERVED_ARTICLE_NOT_READ`. Otherwise a headline is clearly labeled `SCOUT_HEADLINE_ONLY_UNOBSERVED`. A fabricated approval flag, missing bytes, invalid source origin, report counter mismatch or stale timestamps fails closed.
- A **freshness filter** rejects obviously stale/future headlines (when the original RSS pubdate exists) and rejects reusing known prior subject hashes. A deterministic lexical subject-overlap detector and editorial family taxonomy avoid near-identical daily leads; a source/family/publisher diversity preference makes three slots more distinct whenever independent topics exist.
- Builds a *research question*, original scientific visual direction and a **different angle** for each slot: what to test first (AM Short), explain and demonstrate (long), misconception/limitation (PM Short). These questions are **not generated factual claims** and contain no script, narration, voice or publishable media.
- Produces a **private-to-the-run ephemeral** detailed board with unverified titles/URLs and a separate **hash-only public receipt** containing episode IDs, subject/source hashes and status counters. The daily GitHub workflow **does not archive raw story headlines, source URLs, copyrighted page bodies, scripts or tokens**, and deletes the detailed temporary board at exit. Its usual small public receipt artifact now also retains the sanitized B4d2 receipt for up to 14 days.
- Adds adversarial offline fake-source tests with actual existing `evidence_probe.probe_report` fake HTTP-body metadata, including conflicts in source ID, origin, publisher, claim/status escalations, stale date, duplicate stories, weak status counters, no-topic days, prior-topic history, CLI outputs and retention content. No live URL/model/API is needed for PR tests.

## Limits and honesty about source evidence

A digest proves only that the **source fetcher claims to have observed bytes**, not that a human verified the story or that two publishers are corroborating the same fact. Publisher diversity proves independent labels, not semantic fact agreement. Taxonomic/lexical novelty is a useful duplicate screen, but can miss rephrased duplicates and **does not demonstrate YouTube engagement improvement**. The daily workflow has no private long-lived historic headline database; a hash list can be supplied in a future private system, but B4d2 alone does not prove cross-day complete anti-duplication.

Source bodies are deliberately not retained in the public repository or public Actions artifacts for privacy/copyright. Therefore this milestone **cannot generate grounded original scripts automatically from page content**. Scripts still require approved source review, rights validation, and explicit optional provider consent/budget before separate draft generation. A headline-only research pitch must never be promoted to an approved narration by this workflow.

## Successful acceptance

Exact-head GitHub PR tests and broad repo Content Quality/Cloud Scout/Render Smoke green. The trusted main daily workflow must show a fresh run producing **three distinct, typed research tasks** (or appropriately fewer when sources unavailable), reconciled source observations and safe small artifact containing both sanitized receipts. Zero calls to Gemini, AWS, Google OAuth or YouTube; no modifications to Branch 1's previously scheduled videos.

**Readiness baseline remains approximately 40/100, real authenticated seven-day unattended YouTube release proof 0/21** until deployed systems and 21 actual owner-channel releases are verified.
