# FlowMinute Lab Phase 2R2 — claim-level editorial preflight (17 October 2026)

**Implementation: OFFLINE research-review preparation only. Not external independent factual verification, human-review authentication, or permission to publish.**

## Why another guard is necessary

Existing Phase 2 staging allows a FactReview role label to attest that a ResearchPackage is ready for a draft. The Phase 2R quotation checker finds exact passages in *caller-supplied* source texts. Neither proves a statement is true. This submodule makes explicit review positions and contradictions visible before anybody treats a research package as publishable.

## Software behavior

New `autopilot/phase2_fact_review_preflight.py`:

1. Re-runs `verify_source_text_evidence()` on the current typed ResearchPackage, SourceCapture and ClaimExcerpt artifacts. It cannot accept a forged "passed=true" report as substitute.
2. Requires each cited claim/source quotation pair to have a typed assessment with the exact SHA-256 of the quote and claimed statement. Rejects altered claims, swapped source IDs, missing pairs and duplicate review positions.
3. Allows SUPPORTS, CONTRADICTS, AMBIGUOUS and UNREVIEWED positions. Contradictory/uncertain evidence or an absence of official **and** independent SUPPORTS records returns a quarantine issue; it never silently counts mixed positions as consensus.
4. Distinguishes evergreen, news, product access, pricing and performance benchmark risk types; rapidly changing claims must use source/check captures from the last 24 hours. Benchmark assertions require explicit *claimed* attribution to the vendor and must still be independently checked.
5. Uses different claimed reviewer IDs for fact and demonstration review, and disallows the creator label from impersonating either role. **These identity strings are not cryptographic identities or human attendance proof.**
6. A proposed demonstration is hash-bound to the current ResearchPackage, with separate PASS/REJECT/NEEDS_REVIEW; simulations must be labeled and no real product recording can be inferred merely from a checkbox.
7. Produces a bounded no-text issue/claim-count report and deterministic report hash. Reviewer notes, webpage text, extracted quotations and full claim statements never appear in the public report.

## Critical truth and rights boundary

The complete-looking report status `STRUCTURALLY_COMPLETE_UNAUTHENTICATED_REVIEW` is **not an approval**. Every output, even if no conflicts occur, explicitly sets `reviewer_identity_authenticated=false`, `independent_source_factual_accuracy_verified=false`, `human_editorial_verdict_verified=false`, `ready_for_production_script=false` and `publishing_authorized=false`.

The reviewer can still lie about whether the quote supports a claim, whether publishers are genuinely independent, whether software/demo evidence was observed, and whether use of copyrighted material is permitted. Production review requires separately controlled reviewer registry/signatures, genuine source capture/provenance, spot-checking vendor performance claims and licensed real demo evidence. No reviewer security credentials or source data are accepted into GitHub workflows.

## Validation and integration

- Source: `autopilot/phase2_fact_review_preflight.py`
- Tests: `autopilot/test_phase2_fact_review_preflight.py`: synthetic cases for valid-looking but untrusted attestation, contradicted/ambiguous claims, altered hashes and demonstrations, creator/reviewer separation, stale releases/pricing/benchmark claims and prompt injection in notes.
- This is a **separate preflight** and does **not** modify the existing `Phase2Coordinator` DAG or fake its production approval flags. Only call it before independent editorial sign-off. Do not automatically generate videos from this report.
- When branch-head public Content Quality Gate completes, record the exact verified count and run link.
- Draft public research PR #5 remains a separate workstream from publishing PR #4.

## Current blockers and budget

2R1: no independently confirmed **live** provider collection from the restricted collector. 2R2: no externally authenticated factual/rights/editorial review despite this improved software preflight. 2R3: original real Hindi/English scripts and independent language review not demonstrated. **21 remaining production acceptance subphases** in the existing project count.

Limits: ₹0/month; do not touch Nirala/laptop, create any paid resource, connect external accounts, request OAuth scopes, mutate Cloudflare/YouTube, render paid media, schedule or publish. No production publication authorization.
