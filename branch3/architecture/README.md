# Clivox Branch 3 — Full Permission-First Production Architecture

**Version:** 1.0 design baseline, 2026-11-12
**Status:** Architecture + offline validators + **A1 public-metadata discovery and A2 human-rights-case intake implementations**. NOT a deployed licensing approval, video production or publishing service.
**Primary repository:** Tirthanand17/taskless-lab; all plans, schemas, workflows and safe metadata live here.
**Owner channel:** Clivox, @ClivoxPulse, UCfPEvy0SefE_5nNlYlY_CyQ.
**Unchanged:** Branch 1 FlowMinute Lab manual scheduling and Branch 2 autonomous FlowMinute are PAUSED.
**Rightsholder allowlist:** zero. **YouTube uploads by Clivox:** zero. **Publishing:** OFF.

## Mission
Identify compelling moments from **gaming / GTA VI, livestreams, comedy, entertainment and podcasts** that Clivox has permission to reuse, add meaningful original commentary, create exceptional mobile-first Shorts, and learn from legitimate YouTube audience feedback. No promise of virality or monetization. No scraped reupload farm.

## Design principles (highest priority first)
1. **Permission before download or source extraction.** Public clip campaigns are leads, not grants. Verified rights-holder policy or direct written commercial YouTube clipping grant plus game/music/guest clearances.
2. **Real originality.** Original narrative and contextual explanation must change the viewer experience; captions, crops, emojis and motion by themselves are not sufficient.
3. **No unapproved public uploads.** Disabled by default; exact media hash + separate owner signature + protected production environment + verified new channel identity are all mandatory.
4. **Reuse the *existing* Branch 3 permission gate** and owner channel state. Do not create duplicate entitlement databases or mix FlowMinute Lab and Clivox OAuth.
5. **Cloud-only.** GitHub Actions hosted runners, repo metadata, GitHub Issues/PRs for review. No use of the owner's laptop as rendering/publishing storage.
6. **Public repository is not a media vault.** Do not commit downloaded recordings, contracts, OAuth tokens, rendered media containing restricted footage, or private rightsholder contact data. When authorized media is necessary, require an approved confidential storage plan (ideally a separate private GitHub-controlled media repository or encrypted owner-approved storage). A public Actions artifact is *not* confidential.
7. **Everything versioned, auditable and restartable**: immutable source IDs, edit specification, checksums, actor ID, transition record, review evidence and scheduling readback.
8. **Agent proposals are never legal approvals.** Agents summarize, rank, storyboard and test; humans verify the rights, accept contracts, review exact rendered clips and approve release.

## Logical architecture

~~~mermaid
flowchart TD
  A[Public creator / campaign discovery] --> B[Source candidate registry]
  B --> C{Verified creator-issued permission?}
  C -- No --> X[Rights pending / deny media acquisition]
  C -- Yes --> D{Game, music, guests, commercial use cleared?}
  D -- No --> X
  D -- Yes --> E[Exact source and timestamp review]
  E --> F[Original story editor: script + added context]
  F --> G[Rights-approved media acquisition on ephemeral runner]
  G --> H[Video, audio, caption and thumbnail production]
  H --> I[QA: mobile preview, technical, content, originality, rights]
  I --> J{Exact asset owner-signed?}
  J -- No --> X2[Hold for revision]
  J -- Yes --> K[Preflight: channel identity, token scope, hashes, no duplicates]
  K --> L[Protected GitHub production environment]
  L --> M[Private-first YouTube upload and readback]
  M --> N{Processing / copyright / owner confirmation OK?}
  N -- No --> Q[Quarantine / stop release]
  N -- Yes --> O[Future UTC schedule with private publishAt]
  O --> P[Readback + verified publication ledger]
  P --> R[Analytics: day 1, 3, 7, 14 / retention]
  R --> S[Experiment review, score hypotheses, editorial learning]
  S --> A
~~~

The diagram shows a **target implementation**, not currently running publishing automation. **Stage A1 public metadata discovery is implemented**, with optional YouTube Data API public metadata key; **Stage A2 now creates pending human-rights review cases automatically after A1**. A2 does not grant any licenses, verify legal ownership or authorize acquiring source media. Licensed-media ingestion and uploading remain blocked.

## Roles and responsibilities
| Role / component | Safe autonomous work | Cannot self-authorize |
|---|---|---|
| Discovery agent | Analyze public metadata/trends/creator programs, shortlist and cite canonical URLs | Downloading copyrighted source or assuming campaign membership |
| Rights & attribution reviewer | Compile terms, expiration, holder identity, territories, game/music flags; recommend HOLD | Grant permission, sign contract, click join |
| Trend/hook editor | 2-s hook hypotheses, joke/climax detection after source grant, score evidence | Claim guaranteed virality, invent clip quotes |
| Story/transformative editor | Write original commentary, context, narrative, credit | Declare minimal changes monetizable |
| Media engineer | Licensed source trim, layout, narration, captions, sound mix, H.264 exports | Access sources before rights verification |
| QA and brand guardian | Crop, subtitle speed, audio peak, authenticity, factual quote compare, policy checklist | Mark human review complete |
| Release controller | Validate immutable hashes, signed approvals, channel ID, collision fences | Create or approve signatures, bypass GitHub environment |
| Analytics experimenter | Analyze official metrics and report hypotheses | Generate fake engagement, comment spam, artificial views |

## Data boundaries
- **Public primary GitHub:** code, schemas, source metadata, public permission-policy URLs, SHA-256 evidence fingerprints, sanitized human review receipts, analytics aggregates without personal info, harmless original storyboard.
- **Approved private storage only:** authorized third-party source, raw agreement, contact details, license documents, transcripts that must remain restricted, unapproved mixes and review renders.
- **Protected GitHub secrets/environment (future):** separate Clivox-only OAuth tokens / refresh process, signed-release public verification keys, storage credentials as needed. The production workflow **does not exist yet**.
- **Ephemeral GitHub runner storage:** temporaries erased after the job; do not upload licensed footage as public artifact.
- **YouTube:** private-first video, later publishAt only after final approval and rights check; readbacks recorded in sanitized audit ledger.

## Canonical records
- Branch 3 live account: branch3/channel_state.json
- Verified creator permissions (presently EMPTY): branch3/creator_permissions.json
- Research-only campaign leads: branch3/clip_source_watchlist_2026-11-12.json
- Existing source gate: scripts/branch3_creator_permission_gate.py
- A1 implementation and usage: branch3/architecture/a1-discovery-implementation.md
- A2 pending case intake: branch3/architecture/a2-rights-intake-implementation.md
- A1 read-only code: scripts/branch3_discovery.py and scripts/test_branch3_discovery.py
- New job schema: branch3/contracts/clip-job.schema.json
- New state graph: branch3/contracts/state-machine.json
- Example *unlicensed* job: branch3/contracts/example-discovered-job.json
- Architectural baseline: branch3/architecture/architecture-config.json
- Offline design validator: scripts/branch3_architecture_gate.py

## Release gate order
Rights holder verified -> source scope and underlying rights -> original editorial -> media QA -> per-version signed owner approval -> production environment protection -> authorized channel OAuth -> no-duplicate real inventory -> private upload -> real YouTube readback -> owner scheduling authorization -> strictly future timezone-aware UTC publication timestamp -> post-schedule readback. Every failure **stops**, never retries a public action blindly.

**Important:** GitHub Actions cannot validate real-world legal consent by itself. Structured metadata is a *record* of human-verifiable evidence, not a substitute for it.

## Architecture references
See research-evidence.md, workflows.md, security-and-storage.md, rollout-and-tests.md, ops-and-metrics.md and architecture-decisions.md.

