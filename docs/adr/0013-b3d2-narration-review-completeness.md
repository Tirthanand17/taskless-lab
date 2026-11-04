# ADR-0013 — Branch 2 B3d2: completeness of every spoken sentence before independent claim review

**2026-11-04 — decision:** put every sentence of a B3d1-integrity-checked script narration into an explicit **PENDING** review docket, even if the model self-reports no factual claims.

## Why, and relationship to previous work

- B3c (PR #14 / ADR-0011) collects only model-*proposed* claim candidates and source observation metadata; it explicitly says the candidate list is incomplete and not fact checked.
- B3d1 (PR #15 / ADR-0012) binds exact narration, model draft, observed sources, B3c dossier and an IST release slot to an externally anchored Ed25519 seal. It authenticates content continuity only, not fact truth or legal rights. It already reuses earlier Phase 3C Ed25519 reviewer concepts and does not activate rendering.
- The model's claim list can omit factual statements from narration. Therefore, restricting independent review to that list would leave unexamined claims. A complete *sentence* inventory is necessary but NOT sufficient: one sentence may contain many claims, and facts may also appear in unspoken title, thumbnail or graphics.

## Architecture

Inputs: a B3d1 detached signed handoff, independent external digest and trusted custodian registry, proposal, planned slot and source observations. Recompute B3d1 integrity before examining narration. No model call or source retrieval is made by this stage.

The new pure CPU module (autopilot/narration_review_inventory.py) splits the **original exact narration** into Unicode-character spans. It checks that joining the original raw spans reconstructs the full narration without dropping any character. Each span has a content-bound SHA256, stable review ID, position and exact spoken text. Every span has PENDING classification, source/context/corroboration/rights statuses all false. Publisher and model-generated candidate claim citations are only untrusted hints; even a zero-item model claim list still produces a full pending sentence docket.

Coarse punctuation boundaries are intentionally not semantic fact extraction. Abbreviations, decimals, multiple assertions within a sentence, quotes, numerical claims and unstated assumptions require **independent reviewer segmentation and contextual review**. Claim truth or originality cannot be certified by lexical matching, a hash, a high count of sources or the existence of a signature.

No per-sentence positive conclusion is ever emitted. No rights license, real account, external private key, cloud storage, billing, YouTube API, model endpoint, video rendering or laptop storage is used.

## Tests

- autopilot/test_narration_review_inventory.py: 2 Shorts + 1 long fixtures, reconstruct Unicode text exactly, unpunctuated tail, abbreviation fragments, punctuation-only errors, oversized/excessive narration, modified scripts/sources/calendar slots, invalid anchor and removed trusted keys.
- Negative scenario: a **new, validly detached-signed test proposal** with zero model-reported claim candidates still creates PENDING rows for every spoken sentence. All test keys are created ephemerally and cannot be used to release videos.
- .github/workflows/flowminute-narration-review-coverage.yml: public GitHub-hosted contents:read, no secrets; replay B3c and B3d1 regressions; no output persistence or publication.

## Gate sequence after B3d2

1. **B3d3 independent factual evidence**: use actual primary content and a complete reviewer-reconciled atomic claim inventory covering all spoken, visual and title assertions. Store excerpt URL/archived source body digest, observed date, context and corroboration with human/editorial verified reviewer identity and signed opinion. No self-review; don't falsely call multiple syndicated articles independent. Reject unclear or false claims. Always inspect real data demos.
2. **B3d4 original media binding**: connect separately authorized real AI script inference and full 2 Shorts + 1 long cloud rendering, exact audio/caption/visual QA, four independently signed Phase 3C media review dimensions and lawful rights. Signed script handoff must be mapped to final spoken subtitles, correct full MP4 and approved source evidence.
3. **B4 privileged production**: only privately authorized and deployed ledger/secret provider, explicit YouTube private upload, thumbnail/caption and future publishAt remote verification; exactly-once cloud writer and owner-signed release policies, no uncontrolled paid bills.
4. **B5 laptop-off acceptance**: 21 real, distinct, original and verified uploads over seven days without local dependencies and no duplicates.

**No change to Branch 1 assisted schedule. No assertion that autonomous publication has been deployed.**
