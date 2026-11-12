# Implementation roadmap and engineering acceptance gates

**Milestones:** A0 architecture complete; A1 bounded public metadata discovery code/workflow implemented and covered by offline tests. Live use of A1 `ids` or `query` still requires a Clivox-specific public-metadata API key; only fixture mode is verified without it. Licensed media acquisition and all publishing are NOT implemented.

## Work packages
| ID | Deliverable | Dependencies | Exit criterion |
|---|---|---|---|
| A0 | Research, architecture, schema, state graph, tests | None | CI green; no API calls; channel and publishing disabled invariants |
| A1 | Public metadata discovery adapter | A0 | **Implemented:** manually dispatched GitHub Action + fixed-host YouTube API source metadata + deterministic ranking + fail-closed rights fields + provenance URLs. **Live integration pending restricted metadata API key.** |
| A2 | Rights-review cases and audit receipts | A1 | actual human verifies rights holder/terms, source-specific scope, game and music rights; zero self-approvals |
| A3 | Private media storage decision and approved provider | A2 | appropriate confidentiality, license compatibility, deletion/expiry access and secure job-only retrieval |
| A4 | Original story editor + segment scoring | A2 | transcript quotes only from approved source, original commentary and provenance |
| A5 | H.264/AAC/SRT deterministic renderer and professional 9:16 QA | A3,A4 | render SHA, mobile preview, captions, audio and technical media QC; no repetitive spinner |
| A6 | Signed owner release manifest and quarantine | A5 | full version digest + rights receipt + metadata + channel ID; revocation and expiration test |
| A7 | Distinct Clivox OAuth and owner read-only inventory | A0, owner consent | mine=true exact channel ID, zero writes, invalid_grant stops |
| A8 | Protected private-first uploader and schedule ledger | A6,A7, approved protected environment | manual rehearsal only; private upload, safe future publishAt, remote readback, duplicate and timeout reconciliation |
| A9 | Owner-approved production pilot (1 Short) | A8 + live rights grant | only approved clip, source-ownership evidence and no claim after checks |
| A10 | Analytics reader and controlled growth experiments | A9 | official reports, no fake metrics, iterate across 5 pillars |

## Tests required before A8
- Wrong Clivox channel ID and expired/invalid OAuth: NO WRITE.
- Missing, revoked, wrong-platform or non-commercial rightsholder grant: NO MEDIA DOWNLOAD.
- Live gaming footage lacking publisher commercial rights, unknown music/guest rights: DENY.
- Public campaign invitation alone or editor "approved=true" JSON: DENY.
- Unverified age or contract acceptance in third-party marketplaces: HUMAN OWNER ACTION REQUIRED.
- Missing or modified media SHA, metadata hash, consent fingerprint or owner signature: DENY.
- Empty source text/transcript, fabricated quote, unsafe title, unsuitable clip: editorial rejection.
- 9:16 render technical QC, no text outside mobile safe area, no forced circular looping overlay.
- Private upload explicit, never omit privacyStatus.
- publishAt missing/naive/past/less than safety margin or already-published: DENY.
- Network failure after upload accepted: reconcile remote before retry; no duplicate.
- Scheduled video rights revoked: stop and owner review.
- Recording of remote video ID and actual UTC schedule; publishing claim only after real readback.
- No use of Branch 1/2 secrets or GH workflow writes while paused.

## CI posture
The branch3-clivox-architecture.yml runs standard-library static validators and unittest. The separate `branch3-clivox-a1-discovery.yml` is manual-only, may make **read-only public metadata calls** when a distinct restricted API key exists, and cannot fetch video media. It must have **read-only GitHub permissions, no secrets, no YouTube calls, no media download, no scheduled triggers**. The existing branch3-clivox-prelaunch.yml remains intact. All future publication workflows require separate owner approval and independent PR.

## Current status
- Channel identity and logo/banner: complete.
- Intermediate YouTube features: enabled; advanced eligible.
- Rights allowlist: empty, so A2 is blocked pending actual creator-issued grant.
- Campaign pilot YMH Ep347: purely a research treatment; no terms accepted, media downloaded or clips uploaded.
- A0: architecture complete. A1: implementation and offline tests complete; live API-key connection not yet verified. A2–A10: outstanding.

