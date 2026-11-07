# ADR-0101 — B4g9 privacy-limited near-duplicate spoken-rehearsal check

**2026-11-07 IST | Branch 2 | no-publish, unapproved synthetic voiceovers**

## Problem
B4g8 detects exact normalized scripted repetitions across 7 days. A punctuation change, single filler sentence or small wording edit changes its 256-bit digest while leaving most of the spoken lesson unchanged. That is a weak engagement/originality signal when the current 4/9/4 scenes still use six fixed educational topic-family templates.

## Decision
- Keep B4g8 **exact script SHA-256** as the only exact-match evidence.
- Independently compute a 64-bit SimHash of the set of lowercase alphanumeric **4-word** terms in every original synthetic narration. Each n-gram is fed to domain-separated SHA-256 before the 64-dimensional vote. The 16-hex SimHash is not a security token and is *not* a unique-content proof.
- Record exactly three opaque signatures per day, without prose, words, source titles, URLs, quotes, user data, or proprietary footage, in the existing bounded GitHub research receipt (14-day artifact retention).
- Retrieve only trusted, SHA-verified main-branch historical receipts from the previous seven days. B4g8-era receipts have zero similarity-history coverage. Never invent missing coverage.
- Mark <=8/64 Hamming-bit distance a *suspected near repeat* for editorial review, **not proof** of copying, novelty, copyright/rights status or suitability for upload. Independently generated unrelated texts can collide.
- Reject malformed, oversized or authority-claiming fingerprints; leave owner final playback, verified claims, rights approval, protected production settings, OAuth, scheduling and YouTube release disabled.

## Acceptance
Tests must show an edited word changes exact SHA while retaining a near-repeat warning, benign empty/legacy history returns zero coverage, forged signature arrays or approval claims fail closed, and the public retained receipt includes only hashes. The GitHub no-publish PR must pass its exact-head CI gates; an actual later main-branch run is needed before treating the seven-day similarity history as operationally proven.

**Production-readiness stays at 45/100 and independently verified unattended releases stay at 0/21.** This is a cautious QA enhancement, not a solution to the outstanding static-template content-generation defect.
