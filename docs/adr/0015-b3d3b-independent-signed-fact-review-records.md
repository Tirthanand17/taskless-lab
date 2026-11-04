# ADR-0015 — Branch 2 B3d3b: independently signed factual-review *record* verification

**Decision date:** 2026-11-04 (Asia/Kolkata)  
**Status:** preproduction software verifier; NOT real human fact-checking, content approval or autonomous publication.

## Research and existing foundations

Official [NIST FIPS 186-5](https://csrc.nist.gov/pubs/fips/186-5/final) identifies signatures as tools to detect tampering and authenticate signatory keys. They do NOT establish that an independently signed claim is substantively true or that a real person did the review. The [pyca cryptography Ed25519 docs](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) define detached signature verification and invalid signatures. [GitHub's secure Actions guidance](https://docs.github.com/en/actions/reference/security/secure-use) warns against checking out untrusted PR code in secret-bearing privileged workflows.

Reuse existing [Phase 3C media-signature gate](../../autopilot/signed_review_gate.py) for principles: previously enrolled keys, signatory separation, short-lived receipts, signed evidence digests, complete required reviews, rejection blocking and NO RELEASE privileges. Do not add an independent YouTube writer. PR #15 established an externally anchored, signed *script*; PR #16 exhaustively enumerates original narration; PR #17 enumerates defined unspoken surfaces and proposed atomic claims and links exact original observed source response/excerpt hashes. **None established real reviewer identity, semantic accuracy or legal rights.**

## Engineering decision and boundary

Create a **pure-CPU, read-only receipt verifier**, not a private fact adjudication service. The caller must supply independently authenticated source evidence, an owner-controlled pinned script digest + custodian registry, and **separately enrolled** fact/coverage reviewer public keys and exclusions. A workflow that supplies its own keys/receipts is NOT authorized just because signatures verify. The public repository must never hold a real reviewer private key.

The verifier independently re-runs **B3d1 signature → B3d2 full narration → B3d3a full script surfaces, bounded excerpt references and atomic claim dossier**. It computes a versioned canonical review-docket SHA256 including all pending surface and atomic claim records plus exact complete source/excerpt fingerprints.

Two types of separately scoped detached signed Ed25519 review records are required:

1. **Coverage of every surface:** one record for each exact B3d3a surface ID; each says either NO_FACTUAL_ASSERTION (no proposed atomic claims mapped), CLAIMS_MAPPED (one or more are mapped), or REJECT. An invented zero-claim list cannot bypass entire-surface coverage; only a signature by a separately trusted coverage reviewer can assert classification, and this code does not know whether the classification is semantically correct.
2. **Each proposed atomic claim:** one record for each exact claim ID; SUPPORTED requires exactly its own known source-ID + excerpt-SHA references, UNRESOLVED or REJECT blocks. Explicit negative decisions, missing records, stale/expired attestations, duplicate/replayed receipts, source changes, revoked/wrong-role keys and absent trusted reviewer enrollment fail closed. Source hash alone is not evidence of factual support; a reviewer must read exact original context and independently assess meaning.

Enforce **separation between reviewers** doing complete-surface claim identification and those adjudicating the atomic claims. Exclude authenticated creator/publisher identities, reject cross-channel and cross-episode receipts, and ensure 24h maximum assessment age and 48h maximum validity. All canonical record bytes are domain-separated and signed to the specific existing B3d1 script manifest and B3d3a review docket, including all excerpts.

### Explicit nonauthorizing output

A mathematically complete signed set returns only **SIGNED_REVIEW_RECORDS_PRESENT_AWAITING_EXTERNAL_OWNER_APPROVAL_NO_PUBLISH**; it never grants any factual/rights approval or upload authority. Missing or negative records return BLOCKED_INDEPENDENT_REVIEW_RECORDS_NO_PUBLISH (or a fail-closed exception). Both outputs explicitly set:

- reviewers_real_identity_authenticated_by_software=false
- independent_fact_truth_verified_by_software=false
- independent_atomic_claim_completeness_proven=false
- external_private_review_ledger_deployed=false
- external_owner_review_and_release_grant_present=false
- full_final_render_or_thumbnail_reviewed=false
- originality_or_rights_approved=false
- media_render_enabled=false
- youtube_upload_enabled=false
- youtube_schedule_enabled=false
- release_authorized=false

A software signature check never silently substitutes for human review. Even if every hypothetical record is signed as SUPPORTED, the true factual/content decision may be wrong or misleading. The code also cannot detect a reviewer omitting a second assertion inside a sentence while still claiming all claims mapped. This needs separately authenticated real human/editorial review, private source-body evidence and protected append-only receipts.

## Implementation and test plan

- autopilot/independent_fact_review_gate.py: no signing, no producer-facing approval function, no disk/network access. Rebuild all upstream content, compare full docket hash, verify cryptographic records against externally supplied trusted registry, enforce complete review scopes and separate coverage/claim roles.
- autopilot/test_independent_fact_review_gate.py: disposable public/private keypairs only inside temporary GitHub-hosted Python tests. Simulates all three distinct episode slots, one synthetic exact source-backed claim, zero proposed claims across other surfaces, and many malicious tampering/replay/rejection/role cases. Fixtures NEVER represent real human approval.
- .github/workflows/flowminute-independent-fact-review-gate.yml: unprivileged normal pull_request; contents:read; no secrets, no private keys injected, no paid providers, no account connection, no laptop/remote computer, no media storage or YouTube mutations; run B3c→B3d3b regression suite plus separate existing scout/render/content-quality checks.

**Acceptance:** all four GitHub-hosted workflows pass on the PR, tests assert no release privileges, owner-visible status remains independent fact record infrastructure only. Do not merge a failed branch.

## Next after B3d3b

**B3d4**: authenticated human/independent claim-review enrollment and immutable private evidence receipts (where owner authorizes), genuinely available and approved generative provider with documented privacy and cost cap, content novelty and rights review, original 2 Shorts + 1 long cloud videos in full durations, exact generated-media technical QA, and complete Phase 3C signed media/video rights review. Verify final on-screen claims/thumbnail/captions too.

**B4**: private cloud durable artifact store, authorized OAuth/scopes, single-writer D1 fenced upload ledger, explicit status.privacyStatus=private before API insert, remote private verification and future scheduling with retries based on readback, owner-controlled credentials and approvals.

**B5**: 21 real, unique, source-reviewed scheduled/public videos over 7 consecutive days without any local machine, and verified costs/duplicate safeguards.

Branch 1 assisted YouTube releases are independent and remain unchanged.
