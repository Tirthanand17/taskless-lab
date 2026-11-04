# ADR-0014 — B3d3a exact source excerpts and all-script-surface atomic claim preflight

**Date:** 2026-11-04; **Track:** Branch 2 cloud autopilot; **status:** developer-only, deliberately nonpublishing.

## Why this is necessary

PR #16 B3d2 covered every spoken sentence, but model-proposed factual claims may be incomplete, sentences can contain multiple assertions, and titles/hooks/visual beats make further public-facing claims. PR #15 B3d1 proved only full draft/source-observation continuity using externally anchored Ed25519 signatures; PR #14 B3c rejected treating source headlines or digests as verified facts.

A byte-for-byte source or valid signature does not establish that quoted evidence supports a specific assertion, that syndicated reports are independent, that context/date/rights are correct, or that a human reviewed the claim.

Research and architecture references:

- [NIST FIPS 186-5 digital signature standard](https://csrc.nist.gov/pubs/fips/186-5/final): signatures detect tampering and authenticate signatories, not content truth.
- [GitHub Docs: Securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target): untrusted PR code belongs in unprivileged pull_request jobs. Never place private reviewer keys, YouTube tokens or production credentials in such workflows.
- Existing source retrieval: autopilot/evidence_probe.py supports public allowlisted HTTPS origins, bounded bodies, no redirect following, full response SHA256, explicit NOT_FACT_CHECKED status.

## Engineering decision

Add autopilot/source_claim_preflight.py with three strictly nonauthorizing stages.

### 1. Exact original HTTP excerpt
The source_excerpt_evidence function takes a previously observed allowlisted article record and original source response bytes; recomputes complete SHA256, validates optional HTTP status, size/MIME, UTF-8 and tight quote-byte bounds, rejects RSS-only and forged approvals. Returns only IDs, source URL, excerpt/context byte SHA256 and byte offsets. No original source body, copyrighted excerpt text, private media or keys leave process memory. The original response must be supplied independently, not silently re-downloaded and substituted.

### 2. All defined script surfaces
The script_surface_docket function revalidates the upstream B3d1 detached signature and B3d2 complete narration. It also covers exact title, hook, viewer benefit, demo walkthrough, and each visual beat, all PENDING. It records the exact response SHA from B3d1-signed source observations. Actual thumbnail, captions, final video graphics and edited media do not yet exist and cannot be reviewed.

### 3. Proposed atomic claims
The atomic_claim_docket function maps human/reviewer-proposed spans to exact text offsets in signed script surfaces, checks source excerpt SHA and original complete response SHA against the same B3d1 source registry, rejects unsupported IDs, malformed bounds, repeated claims and citations, and refuses forged support/rights claims. All results remain PENDING; no claim completeness or factual corroboration is inferred.

**Trust boundary:** The public caller-provided dossier alone is not a separately authenticated reviewer decision. Hashes are content identifiers, not evidence of correct origin or truth. A separate private audited source service, independently authenticated B3d1 anchor, source-retrieval authority and trusted reviewer identity must be verified at production admission. None is deployed here.

## Validation

- autopilot/test_source_claim_preflight.py covers three full 2 Shorts + 1 long scripts, signed synthetic source HTTP bytes, byte/hash/bounds/MIME failures, forged verified flags, RSS-only, nonmatching source SHA, false claim/surface text, duplicate citations, and explicit no-release outputs.
- .github/workflows/flowminute-source-claim-preflight.yml runs on an ordinary read-only pull_request hosted job, installing only the public cryptography verification package and running B3c, B3d1, B3d2 and B3d3a unit tests. No secrets, model provider, expensive API, laptop, media artifact or YouTube API call.

## Next gates

1. **B3d3b independently signed fact review**: an authenticated independent reviewer identifies every atomic claim across all spoken and unspoken content, reads actual primary source context, verifies independent corroboration (not multiple syndicated copies), documents date, contradiction/abstention/rejection, and signs genuine explicit verdicts bound to the exact script, excerpt digests and reviewers. AI self-approval prohibited.
2. **B3d4 real AI + video**: owner-authorized real generative script provider with privacy and budget proof, distinct useful demos, independent fact/rights/creative/AI-disclosure approval, original narration, scene animation, and whole encoded-file QA. Reuse B3b and existing Phase 3C signatures, not fixture assertions.
3. **B4**: private cloud durable media, private renewable OAuth, explicit PRIVATE YouTube uploads/readback, canonical D1 single-writer slot reservation and safe future UTC schedule, owner-approved account authority.
4. **B5**: seven laptop-off days of 21 unique actual releases, no duplicates/missed slots/uncontrolled charges.

**B3d3a grants neither media rendering nor YouTube upload. Branch 1 assisted releases remain untouched.**
