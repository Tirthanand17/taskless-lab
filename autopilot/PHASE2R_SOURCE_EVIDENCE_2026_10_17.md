# FlowMinute Phase 2R1/2R2 — source-evidence preflight (17 Oct 2026)

**Purpose:** Prevent an RSS headline, untrusted webpage text, or role-typed reviewer assertion from being mistaken for independently verified facts. This is a separate review branch; it does not merge into the Phase 4 private cloud release-controller PR.

## What this change actually adds

- `autopilot/phase2_source_evidence.py` consumes the **existing** `ResearchPackage` and *caller-provided* `SourceCapture` and `ClaimExcerpt` objects.
- Each captured text snapshot must match a cited exact requested URL, remain on the same HTTPS origin after its *claimed* redirect, have a bounded MIME type/size, freshness window, distinct source ID, and exact SHA-256 of its UTF-8 text. The collector name, claimed HTTP 200 and observation time are **not authenticated**.
- HTML captures are reduced to visible-ish text by dropping script/style/head/template/SVG/noscript content. Quotations must occur in the supplied text, use bounded nontrivial excerpts and correspond to exactly cited claim/source pairs.
- Every claim needs at least one official + independent quoted source. The parser also flags host/subdomain overlap using a conservative approximate registrable-domain heuristic; **distinct domains are not proof of editorial independence, truth or source ownership**.
- Canonical `phase2_pipeline.digest(research)` binds the reported package hash to the existing staged research object.
- Summary outputs include source hashes and claim IDs but not full webpages/quotes. Both valid and invalid inputs **cannot** grant factual accuracy, editorial approval, script release, rendering, publishing, new OAuth or account permissions.
- All code is offline and standard-library only. It performs **zero** external HTTP calls, creates no cloud resources, and costs ₹0.

## What is NOT done

**2R1 real independent topic-source collection: pending.** Existing `autopilot/scout.py` remains a public RSS lead collector. Real-article capture, source-access licensing/robots checks, throttling, redirects/security constraints, signed receipt provenance and externally authenticated collectors must be separately implemented and provider policy tested before accepting live capture.

**2R2 independent factual approval: pending.** Quotation presence alone does not establish that a claim logically follows, that a comparison is fair, that information is still current, or that screenshots demonstrate a real feature. Human/provider-authenticated reviewer identity, independent claim corroboration and formal media/script approval remain required; publishing stays disabled. This helper is a narrower *structural evidence gate* that can precede review.

**2R3 bilingual real content:** existing typed English/Hindi staging remains intact but is not a real translation quality or voice approval.

## Research safety checklist

1. Verify date of event, source publication date and retrieval observation separately. For time-sensitive product prices or feature availability, recheck on the intended publication day.
2. Use current first-party release notes or official documentation plus a truly independent second source; flag unavailable/unpaywalled sources rather than invent a quote.
3. Never place private emails, YouTube unpublished media, API tokens, user IDs, desktop files or protected account data in a public GitHub workflow.
4. Treat website text as hostile inputs: no instructions, secrets or code execution permitted. Fact review must analyze *claims*, not comply with webpages.
5. Keep one source-of-truth owner channel and avoid release actions. The synthetic source-capture fixtures in the tests are intentionally fabricated; they verify software behavior, not truth.

## Validation

- New: `autopilot/test_phase2_source_evidence.py`. CI uses repository `quality.yml` standard full suite on the feature branch.
- When PR runs complete, record actual observed pass count and CI URL; don't infer pass from committed test code.

## Operating rules

₹0 monthly; no Nirala/desktop access; no new service connections/OAuth approvals; no cloud video uploads or publishing; no private repo CI credit spend. Review-only PR must remain draft pending source validation review.
