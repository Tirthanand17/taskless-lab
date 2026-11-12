# Clivox A2 — Rights review dossier workflow

**State on 2026-11-12:** rights review workflow implemented; zero creator licenses verified. This is not legal advice, a creator-issued license, an accepted contract or a media upload authorization.

## How A2 fits A1 → A3
- A1 returns public metadata / potential creator campaigns (always unlicensed research).
- A2 creates a sanitized source-specific case with original YouTube video ID, verified creator identity to collect, clipping-grant scope, expiry/revocation, third-party music/game/guest rights, marketplace ownership obligations, exact editorial timestamps and human verification fields.
- A3 confidential media sourcing is NOT enabled until verified creator-issued rights evidence and approved private storage exist.
- A2's current software deliberately has no right to promote a case to RIGHTS_VERIFIED: permission is granted by rights holders and verified by humans, not synthesized from a checklist. The fail-closed A2 tool only produces HOLD_FOR_HUMAN_RIGHTS_AND_CONTRACT_REVIEW reports.

## Existing pilot: YMH Studios — 2 Bears 1 Cave Ep347
Record: branch3/rights_cases/clivox_ymh_ep347_case.json

Missing requirements include:
1. Confirm original video's publisher's exact YouTube channel ID, full episode and context/timestamps; don't invent dialogue.
2. Confirm owner/issuer identity and authentic creator-issued commercial YouTube clipping authorization, not just a public invitation page.
3. Decide whether to join the Content Rewards campaign after personally reviewing its terms, including potential assignment of the final edit's IP.
4. Verify approved commercial YouTube Shorts, cuts/overlays/original commentary, duration, attribution and prohibitions.
5. Clear music, guests, on-screen third-party media, game footage where applicable, and sponsor-label requirements.
6. Privately retain contract or permission evidence; only public-safe fingerprint and generic proof reference belong in the primary repository.
7. Sign exact finalized asset and release separately only after licensed video has been created and reviewed.

**No marketplace terms have been accepted; no permission-request email has been sent.**

## How to run entirely in GitHub
- .github/workflows/branch3-clivox-a2-rights-review.yml triggers on PRs changing rights-case metadata or by manual workflow_dispatch.
- It runs scripts/branch3_rights_case_review.py and adversarial tests, generates an unlicensed HOLD report, and stores a short-lived public-safe JSON artifact.
- All workflow permissions are read-only; it uses no OAuth, source files, media downloads or release keys.
- Before new cases are added, make a separate immutable file under branch3/rights_cases/. Do not include private email, signed contract bytes, payment account identifiers or tokens.

## Trust rules
- Public creator campaign is NOT an actual grant.
- Checkboxes, GitHub commit authorship, a model summary and an AI-written certificate are NOT authenticated creator permission.
- An expired/revoked/rightsholder-disputed license is not actionable.
- The allowlist at branch3/creator_permissions.json stays empty until a separate human-attested process exists and evidence is independently confirmed. A2 is operational for review only.
- A2 cannot authorize media, OAuth, upload or scheduled publication.

## Current official reference material
- YouTube reused content and monetization: https://support.google.com/youtube/answer/1311392
- YouTube copyright and permission: https://support.google.com/youtube/answer/2797466
- YouTube Game footage: https://support.google.com/youtube/answer/138161
- Content Rewards Creator Terms: https://contentrewards.com/terms
