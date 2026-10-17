# FlowMinute Lab — Phase 2 research, creative and bilingual staging (17 Oct 2026)

## What is implemented

Existing `autopilot/agent_org.py` orchestrates the complete **18-stage** per-episode draft DAG (increased from 17 to add independent language review before voice planning). The new `autopilot/phase2_pipeline.py` provides the first seven implemented typed handoffs:

| Stage | Task owner | Accepted artifact | Gate |
| --- | --- | --- | --- |
| research | research.launch_researcher | ResearchPackage | At least one official and one independent HTTPS domain, checked within seven days; each claim linked to an official source; no RSS-only leads |
| fact_review | quality.fact_reviewer | FactReview | Every claim explicitly attested, digest matches exactly the submitted research package |
| script | creative.shorts_writer or creative.longform_writer | CreativeScript | Original practical steps, only attested claim IDs, exact research and review digests |
| hooks | creative.hook_writer | HookVariants | Alternative truthful opening lines tied to already reviewed claims |
| english | language.english_editor | LocalizedDraft | Exact current script digest, narrator copy, subtitle draft and terminology notes; explicitly unreviewed |
| hindi | language.hindi_editor | LocalizedDraft | Same requirements with natural Hindi copy; explicitly unreviewed |
| language_review | language.language_reviewer | LanguageReview | BOTH Hindi and English draft SHA-256 digests, designated reviewer role and explicit attestation; blocks voice_plan if absent/rejected/stale |

**All records above are staging claims** and belong to an in-process `Phase2Coordinator` instance, not the production DB. Even a submitted `ATTESTED_FOR_DRAFT` reviewer record is only a role-attributed input, **not independent proof of real-world source accuracy or verified human approval**: no external reviewer authentication/cryptographic signature integration has been deployed.

The existing `scout.py` still returns **unverified leads**. This pipeline *requires* separately researched claims rather than automatically promoting RSS news to facts. It performs no source downloads, model-generated writing, machine translation or voice synthesis. Both localizations are preserved as drafts and are not automatically approved by the translation specialists.

### Flow and safety

```text
RSS/evergreen leads (unverified)
    → separately researched source-linked claims
    → independent fact-review role attestation
    → creative script + hook options in parallel
    → English draft + Hindi draft
    → distinct language-review role attestation
    → voice_plan unblocked for next staging phase
    ↳ storyboard may proceed in parallel from script + hook
```

- Content fingerprints are SHA-256 of canonical JSON for each typed artifact.
- The existing Workflow checks the owner, evidence references, episode ID and dependencies; failure does **not** auto-unblock downstream tasks.
- Untrusted source/article content has no authority to issue agent commands.
- An unreviewed language draft cannot self-label as approved; later changes invalidate the review hash.
- The pipeline has no API to upload, schedule, alter OAuth permissions, connect providers or charge money.
- Source support checks rely on submitted evidence metadata; the pipeline does not claim network verification or comprehensive factual correctness.

### Tests and deployment state

The repository's **Content Quality Gate** passed **169 tests and 6 subtests** on GitHub-hosted software CI: [run #39036189001](https://github.com/Tirthanand17/taskless-lab/actions/runs/39036189001).

The specific Phase-2 module has **27 regression tests**, with tests for stale sources, unsupported/private URLs, RSS-only leads, wrong actor, wrong review digest, incomplete fact review, altered demo, unreviewed script claims, unauthorized language status, changed Hindi draft, and missing or rejected independent language review.

The Master Orchestrator's unit suite also verifies its 18-stage graph and dependency requirements. This is **software CI**, not a live 24/7 cloud service or a completed episode.

### Next phase (do not imply enabled)

1. Implement typed storyboard, natural narration plan and subtitle synchronization; require independent language/audio QA before rendering.
2. Integrate original/demo footage, reusable motion/3D assets and `render_inspection.py` actual-file checks with rights attestation.
3. Replace staging-only hash references with a single authorized durable artifact/metadata store and authenticated reviewer identity; do not duplicate the existing private ledger.
4. Set up verified free-compute/media storage within zero spend and official provider policies.
5. Separately resolve Google OAuth External/Testing seven-day token lifetime; do not make a public upload until a later owner-approved pilot and exact receipt readback.
6. Connect official analytics and controlled experiments rather than infer growth from staging metrics.

**No Nirala access, new service connections, charges, real channel operations or uploads were used for this phase.**
