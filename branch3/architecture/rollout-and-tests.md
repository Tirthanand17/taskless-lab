# Implementation roadmap and engineering acceptance gates

**Milestones:** A0 architecture complete; A1 public metadata discovery implemented and smoke-tested on GitHub; A2 **pending human-rights review intake** added to each discovery workflow. A3 **media-storage preflight and public-repo leakage checks** added, but the private vault is not provisioned. A4 **original source-free scripting and storyboard validation** implemented; A5 **original-only synthetic rendering, technical AV/SRT QA, and A4→A5→A6→A8 integration rehearsal** implemented, while rights-cleared edit, professional narration and final QA remain blocked. No source rights have been verified. Live use of A1 `ids` or `query` still requires a Clivox metadata API key. Licensed media acquisition and all publishing remain NOT implemented.

## Work packages
| ID | Deliverable | Dependencies | Exit criterion |
|---|---|---|---|
| A0 | Research, architecture, schema, state graph, tests | None | CI green; no API calls; channel and publishing disabled invariants |
| A1 | Public metadata discovery adapter | A0 | **Implemented:** manually dispatched GitHub Action + fixed-host YouTube API source metadata + deterministic ranking + fail-closed rights fields + provenance URLs. **Live integration pending restricted metadata API key.** |
| A2 | Rights-review cases and audit receipts | A1 | **Intake implemented**: pending human-review JSON case per A1 candidate, provenance digest, 14 mandatory checks and zero self-approvals. **Authentic grant verification and signed audit receipt still pending**. |
| A3 | Private media storage decision and approved provider | A2 | **Public/media boundary implemented and tested**; private GitHub release-asset vault proposed, but **not created/linked/approved**; real provider identity/ACL and exact licensed source access remain blocked |
| A4 | Original story editor + segment scoring | A2 | **Source-free original script/beat validation implemented with CI**; verified quotes/precise source segment, licensed edit and human originality review not yet possible without rights |
| A5 | H.264/AAC/SRT deterministic renderer and professional 9:16 QA | A3,A4 | **Synthetic original-only render + FFprobe, SHA-256, visual SRT check and cross-stage real-file rehearsal implemented**; real licensed source editing, narration/voice mix and final QA blocked until verified rights/private vault |
| A6 | Signed owner release manifest and quarantine | A5 | **Offline Ed25519 canonical digest binding + unsigned quarantine CI and integrated A5 media QA hold implemented**; actual owner key enrollment, rights verification, real video signing and protected release integration not implemented |
| A7 | Distinct Clivox OAuth and owner read-only inventory | A0, owner consent | **Read-only client and manual-only live bridge implemented; separate GitHub `clivox-readonly` environment created and verified (owner reviewer, main-only, no admin bypass)**; Google consent, Clivox-only secrets and live YouTube readback still pending |
| A8 | Protected private-first uploader and schedule ledger | A6,A7, approved protected environment | **Offline private-first schedule, 30-min UTC margin, deterministic attempt hash and duplicate/ambiguous-attempt holds; integrated rehearsal confirms no-write gate**; durable atomic ledger, protected environment, live upload/readback and scheduling NOT implemented |
| A9 | Owner-approved production pilot (1 Short) | A8 + live rights grant | only approved clip, source-ownership evidence and no claim after checks |
| A10 | Analytics reader and controlled growth experiments | A9 | **Synthetic-only YouTube Analytics result parser, null-aware Shorts Studio metric separation, per-category hook comparison and adversarial CI implemented**; real Analytics OAuth, live channel data, credible A/B tests and publishing optimization not connected |

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
The branch3-clivox-architecture.yml runs standard-library static validators and unittest. The separate `branch3-clivox-a1-discovery.yml` is manual-only, may make **read-only public metadata calls** when a distinct restricted API key exists, and cannot fetch video media. Both workflows have **read-only GitHub permissions and no media download or publishing**. The manual discovery workflow can call YouTube's *public read-only metadata* endpoints using an optional **metadata-only API key** in Actions secrets; its test/fixture mode requires no key and performs no network calls. Neither workflow has a scheduled trigger. The A3 `branch3-clivox-a3-media-boundary.yml` workflow and A4 `branch3-clivox-a4-editorial.yml` workflow also run offline with read-only permissions and produce only public-safe JSON reports, never media bytes. The existing branch3-clivox-prelaunch.yml remains intact. A7 `branch3-clivox-a7-readonly-preflight.yml` and `branch3-clivox-a7-live-bridge-qa.yml` run offline synthetic channel/playlist tests only. The separate manual-only `branch3-clivox-a7-live-readonly.yml` can execute only from main, protected by the independently verified `clivox-readonly` environment; it currently has no OAuth secrets, without any Google token or network readback. A8 `branch3-clivox-a8-dryrun.yml` is an offline plan with zero network writes and only a public-safe JSON report. A10 `branch3-clivox-a10-analytics.yml` is likewise offline synthetic-only; it publishes no private video IDs or customer data and cannot change releases. Integrated original-only rehearsal: `.github/workflows/branch3-clivox-integration-rehearsal.yml` reuses A4 storyboard, A5 actual synthetic MP4/SRT and FFprobe, A6 unsigned quarantine and A8 private-first dry-run on ephemeral GitHub runner. Public original-only artifact (7 days), no licensed media or YouTube API writes. All future live OAuth or publication workflows require separately reviewed owner authorization and an independent PR.

## Current status
- Channel identity and logo/banner: complete.
- Intermediate YouTube features: enabled; advanced eligible.
- Rights allowlist: empty, so A2 is blocked pending actual creator-issued grant.
- Campaign pilot YMH Ep347: purely a research treatment; no terms accepted, media downloaded or clips uploaded.
- A0: complete. A1: implemented and fixture workflow smoke-tested, live API-key connection not yet verified. A2: **unverified-rights case intake implemented**, actual rightsholder verification pending. A3: fail-closed media boundary and private-vault plan implemented; provisioning and licensed source access outstanding. A4: source-free original storyboard engine implemented, licensed-source editorial QA pending. A5: synthetic original-only media preview and technical QA implemented; licensed production/video reviews pending. A6: cryptographic signature verification and unsigned quarantine preflight implemented; live signing/rights checks remain blocked. A7: offline OAuth identity/playlist API preflight implemented with synthetic fixtures; live owner OAuth consent and protected deployment pending. A8: dry-run private-first and idempotency safety tests implemented; live Google write scope, atomic persistent ledger, authenticated remote reconciliation and signed licensed media are missing. A9: **0% real licensed pilot**; the integrated original-only 40-second GitHub rehearsal is NOT a licensed source clip or an approved upload. A10: synthetic-only analytics evaluation implemented; real channel metrics and decisions pending owner OAuth and published samples. Overall planning estimate: 54% implementation / 46% remaining; see `progress-tracker.json`.

