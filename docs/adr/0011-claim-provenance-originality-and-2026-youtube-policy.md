# ADR-0011 — Branch 2 B3c: evidence-linked claim dossiers and daily originality screen

- **Decision date:** 2026-11-04 (Asia/Kolkata)
- **Track:** Branch 2 / Autopilot; never change Branch 1 assisted releases.
- **Decision:** build a strict **nonpublishing** source-to-claim editorial handoff and a three-episode textual similarity screen before real model-generated scripts may enter a render pipeline.
- **Implementation:** autopilot/claim_review_dossier.py, test_claim_review_dossier.py and .github/workflows/flowminute-claim-review-gate.yml.
- **Authority boundary:** 0 paid calls, 0 external LLMs, 0 OAuth, 0 YouTube mutation, 0 self-hosted/laptop runners, no generated MP4 persisted.

## Why this gate exists

PR #13 (B3b, merged) proved *actual* 3-video technical render and independent audio/pixel/caption QA, but it used **human-authored illustrative CSV teaching fixtures**, not an autonomously selected/verified batch of three publishable scripts. PR #10's model draft agent structurally validates a proposed script and references source IDs, but **retrieval success and model citation IDs are not proof that a claim is true**. Both paths have been correctly kept separate.

Authoritative YouTube documentation consulted 2026-11-04:

1. **API revision 2026-11-02:** uploads from unverified API projects no longer have a privacy-only restriction. A videos.insert request without status.privacyStatus now **defaults to public** unless account settings override; future B4 must set status.privacyStatus=private explicitly on every insert and verify returned remote privacy before any scheduling operation. Never infer safety from historical 2020 restrictions. https://developers.google.com/youtube/data/revision_history
2. **API revision 2026-11-03:** Shorts custom thumbnails through thumbnails.set are supported **after video processing completes**. Future asset verifier should read back this result, not claim a thumbnail is already served because an upload call returned success. https://developers.google.com/youtube/data/revision_history
3. **Publishing date:** status.publishAt is allowed only with a private never-published video. A past timestamp causes *immediate public publication*. Future writer must independently verify UTC future time, private processing and owner scope. https://developers.google.com/youtube/data/reference/rest/v3/videos
4. **Inauthentic/repetitive content:** channel monetization policy excludes low-value mass-produced/repetitive material. A merely different title, voice or image is insufficient: distinct verified demonstrations, truthful narrative and substantive viewer value need review. https://support.google.com/youtube/answer/1311392
5. **Synthetic/altered media:** meaningful realistic alterations and realistic fabricated scenes/person depictions may require disclosure. The future uploader needs an explicit editorial disclosure determination, transmitted in the proper API field; do not silently assume false. https://support.google.com/youtube/answer/14328491 and https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
6. **Spam:** automated high-volume near-identical content is not an acceptable shortcut to the requested 3/day cadence. https://support.google.com/youtube/answer/2801973

These rules are not substitutes for creative, rights, accuracy or YouTube account review. They drive fail-closed gates, not publication permission.

## B3c design and evidence trust

Input: unprivileged planned slot (build_plan), bounded public-source observations from evidence_probe, and a model **proposal** validated by script_draft_agent. Rebuild upstream draft input from observations and recompute validated proposal; reject modified status fields, mismatched episode/format/source IDs and invalid source URLs. Source URLs are included for subsequent human review but are **not fetched again** by B3c; observation hashes remain nonsemantic.

Each candidate claim gets a stable ID, its untrusted exact text, an annotated list of observed sources, source hashes and publisher labels, plus **all review status fields set false/PENDING**. Two independent publisher *labels* do not establish independent reporting, actual corroboration, rights or correctness; syndicated sources could share a primary author. The candidate claim inventory itself may omit narration assertions and is **not certified complete**.

On a 2 Shorts + 1 long proposal batch, require exact slot order, one IST date, distinct episode IDs, distinct titles/hooks and non-near-duplicate narration/walkthrough text. This is only a deterministic similarity floor, **not human/semantic originality clearance**, copyright clearance or a YouTube spam-policy finding.

### No-authority state machine

Draft + observed source metadata → **CLAIM_EVIDENCE_AND_ORIGINALITY_REVIEW_PENDING_NO_PUBLISH** → independent factual/editorial/rights/AI-disclosure/video review (not implemented) → separately admitted media build (not implemented) → B4 private publisher (not enabled).

A successful B3c workflow has **no power** to approve publication.

### Files and checks

- autopilot/claim_review_dossier.py: no network, deterministic per-claim review packets and strict cross-video text similarity/replay controls.
- autopilot/test_claim_review_dossier.py: forged fact/upload/rights status, unknown/tampered source URL, duplicate source, replayed episode, poor original variety, missing pack and safe results.
- .github/workflows/flowminute-claim-review-gate.yml: public GitHub-hosted Python stdlib-only job, contents:read, no secrets, no publishing or storage.
- Existing independent source evidence and model draft tests run in the same job.

## Important limitations and next engineering order

1. **Human/independent semantic claim confirmation** is still missing. A real reviewer must open cited primary content, check *each actual claim* and context/date, seek genuinely independent evidence, verify data/process demos and mark uncertain or unsafe claims for rewrite. A source SHA proves identical bytes, not truth.
2. **Script integrity needs a trusted producer-to-review artifact seal** in future B3d, stored in a private/durable signed or fenced ledger. This module computes a digest of the supplied candidate for reference but cannot detect a *structurally valid, malicious edit made upstream* without an external trusted digest/signature. Never report it as cryptographic proof of immutable authorship.
3. **Originality/rights review** must cover the rendered visuals, audio, licenses, consent, actual demonstration and contextual novelty, not just title/narration fuzzy similarity. Independent human complete viewing remains unfulfilled.
4. **Real model pipeline** still requires an explicitly permitted model/provider, documented privacy, stable actual endpoint, spend cap and factual benchmark on 3 distinct scripts. PR #10's Gemini mock is not live inference.
5. **Future B4 privileged boundary:** explicit private upload, durable immutable media, single-writer D1 leases, remote readback and never blindly retry ambiguous uploads. OAuth/Cloudflare billing changes require separate owner authorization. No secrets belong in the public repo.
6. **B5 acceptance:** 7 consecutive laptop-off days of 21 *original* confirmed releases, no duplicate, controlled cost, correct captions/thumbnails/rights, and 3–7-day inventory buffer.

## Acceptance criterion for this PR

GitHub-hosted B3c checks green on branch PR; all negative cases remain blocked; reviewer records and one synthetic 3-episode test result carry explicit release_authorized=false and youtube_upload_enabled=false. Even with all checks green, **B3c is a nonpublishing editorial-preflight milestone, not autonomous publishing deployment**.
