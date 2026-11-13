# Branch 3 — Clivox (SECOND YouTube channel)

**Status:** **Clivox was created and publicly verified on 2026-11-12**, with the exact chrome-and-orange logo, premium banner, About description and channel keywords live. The new channel has zero videos and zero approved third-party clip creators; publishing automation remains disabled.

**Isolation:** Branch 1 (existing FlowMinute Lab scheduling) and Branch 2 (autonomous FlowMinute publishing) are paused. Do not change their code, channels, schedules or credentials. This branch shares the existing repository for planning and branding but uses completely separate channel identity, source-rights registry, approval process and future credentials.

## Live channel identity (YouTube-verified)
- Display name: **Clivox**
- Verified handle: **@ClivoxPulse** (`@Clivox` was unavailable)
- Verified channel ID: `UCfPEvy0SefE_5nNlYlY_CyQ`
- Official channel: https://www.youtube.com/@ClivoxPulse
- Focus: **viral-worthy creator-approved highlights across gaming (including GTA VI), livestreams, comedy/jokes, entertainment, podcasts and interviews**, always with meaningful original editorial context
- Language: English first; no assumption of language rights
- Tagline: **Clips worth watching. Context worth knowing.**
- Video style: creator-approved excerpt + original commentary/critique/story, source attribution and clear factual context
- Profile and banner SVG: `branch3/branding/`
- Final channel About copy: `branch3/channel-profile.md`

## Viral-first multi-category content strategy
**Current content priorities:** (1) gaming/GTA VI, (2) livestream reactions, (3) comedy/jokes, (4) entertainment/pop culture, and (5) podcasts/interviews. The goal is to find the strongest original, shareable moment in a creator-permitted full video, podcast or livestream rather than copy its most-viewed excerpt. See `viral-content-strategy.json`. This is an editorial testing order, not an assertion that one category will go viral. Keep performance decisions tied to actual Clivox analytics after launch.

**GTA VI is a topic watchlist, not a license.** Rockstar/Take-Two's published fan-video guidance emphasizes non-commercial gameplay and excludes leaked pre-release footage and other restricted clips. Commercial Clivox clips need separately verified publisher/game footage rights when applicable, in addition to streamer permission; no leaks or spoiler compilations.

## Explicit creator-permission rule
Only material covered by direct written creator/rights-holder permission or an authentic public clipping policy from that creator enters the candidate pipeline. We never treat a viral video, Fair Use speculation, a general downloadable link, third-party CC upload, or credit-only attribution as blanket permission. See `scripts/branch3_creator_permission_gate.py` and `creator_permissions.json` (empty by default). A permissions record can qualify a proposed candidate for human review; it **never** authorizes upload itself.

## Hard launch gates
1. **DONE** — New channel created via YouTube UI and verified distinct from FlowMinute Lab; exact channel ID is recorded in `channel_state.json`.
2. **Studio owner UI access verified.** New channel publishing API OAuth is NOT configured; never copy existing FlowMinute Lab OAuth tokens to this channel.
3. For every reused segment: prove original publisher's ownership, creator-issued written permission or an authenticated creator-published clipping policy for reuse **and** editing, redistribution, Shorts and commercial use where applicable; verify underlying third-party footage/music rights separately. Store only consent reference and non-sensitive metadata in repo.
4. Add substantial original educational/critical context. Avoid bare reuploads, generic templates and misleading crops.
5. Independent creator/rights/editorial and final playback review; no uploads while approval is missing.
6. No guarantee of zero Content ID claims, strikes or monetization eligibility.
7. Keep all publishing automation off until the user separately approves after channel creation.

## Branch 3 development status — A0–A10 partial implementation

The standalone architecture, research evidence, state graph, agent responsibilities, release safeguards and step-by-step implementation roadmap live at [architecture/README.md](architecture/README.md). **A1 source discovery, A2 rights-case intake, A3 storage safeguards, A4 original scripts, A5 synthetic rendering/QA, A6 cryptographic release checks, A7 read-only OAuth client and A8 dry-run scheduling safeguards are implemented in part**; real lookup mode requires a separately configured public-metadata API key. No clipping rights, media downloads or publishing are allowed.

- **Architecture docs:** [overview](architecture/README.md), [primary research](architecture/research-evidence.md), [workflow and agent roles](architecture/workflows.md), [security and cloud-only media strategy](architecture/security-and-storage.md), [analytics and operating plan](architecture/ops-and-metrics.md), [rollout and testing](architecture/rollout-and-tests.md), [ADRs](architecture/architecture-decisions.md).
- **Machine-checkable architecture:** `architecture/architecture-config.json`, `contracts/state-machine.json`, `contracts/clip-job.schema.json`, `contracts/example-discovered-job.json`.
- **No-publish offline CI:** `.github/workflows/branch3-clivox-architecture.yml`; `scripts/branch3_architecture_gate.py` with adversarial tests.
- **Implementation reality:** A0 design + A1 read-only metadata ranking + A2 human-rights-review **case intake** are implemented, **not** real rights approval, licensed media extraction or a deployed multi-agent clipping/rendering/publishing platform. See [A1 run instructions](architecture/a1-discovery-implementation.md) and [A2 case intake](architecture/a2-rights-intake-implementation.md) and `.github/workflows/branch3-clivox-a1-discovery.yml`. No third-party media may be fetched before permission; no new Clivox OAuth token, release signer or production environment has been configured.
- **A3 owner-reviewed private vault readback (code only):** [owner setup and exact security limits](media_storage/OWNER_PRIVATE_VAULT_READBACK.md), `scripts/branch3_a3_private_vault_readback.py` and two GitHub Actions workflows add owner-triggered, manual/main-only, fixed-host metadata + collaborator readback for a future separately owner-approved private repository. **No vault exists/has been accessed or verified in live mode, no approved footage, no source media access and no CLIVOX YouTube writes.**
- **A3 media boundary:** [media storage README](media_storage/README.md) documents the chosen GitHub-first private-vault approach and provides public-media leak checks; **no private vault has been provisioned or approved**. Source footage may not be downloaded until creator-granted rights are verified.
- **A8 transactional upload-attempt ledger rehearsal:** [SQLite atomic single-runner QA](a8/ATOMIC_ATTEMPT_LEDGER_REHEARSAL.md) verifies no-duplicate reservations and no-blind-retry after an ambiguous result with adversarial concurrent GitHub CI. **No cross-run durable ledger, real upload, authenticated inventory or publish credentials exist.**
- **A2/A3 owner-only private-journal readback bridge (not connected):** [private journal owner setup](rights_review/OWNER_LIVE_JOURNAL_READBACK.md) adds manual/main-only protected GitHub Actions, a fixed three-GET private repo/owner/journal read and journal signature/anchor checks. **No owner vault, credentials, production keys or live run exist; no source or YouTube write authorization.**\n- **A2 private revocation journal CAS protocol (offline):** [private GitHub revocation journal guide](rights_review/github-private-ledger-cas.md) adds globally chained signed tombstones, GitHub Contents readback SHA checks and stale-blob conflict prevention tests. **Only synthetic tests; no private repository, production key, live journal or uploader exists.**
- **A2 signed checkpoint anti-rollback preview:** [A2 chain/checkpoint design](rights_review/checkpointed-revocations.md) checks signer mathematics, receipt-scoped revocation histories, 15-minute timestamp validity, and anchored hash continuity with synthetic-only tests. No live authority, durable checkpoint or creator grant exists; no uploads or downloads can follow from this report.
- **A2 signed human-review / revocation preview:** [A2 offline receipts and revocation design](rights_review/README.md) mathematically verifies case-bound Ed25519 human-review claims and independently signed revocation tombstones with adversarial tests. **No actual reviewer/trust key, creator license, private agreement or authoritative revocation ledger exists; media acquisition and YouTube writes remain disabled.**
- **A1→A2→A3 early pipeline handoff:** [source-to-rights-to-storage README](integration/a1-a2-a3/README.md) and a dedicated GitHub-only Actions gate cross-validate exact discovery SHA, every pending-rights case, the closed A3 storage configuration and public file inventory. This validates consistency, **not** authentic creator permission, source acquisition, a real private vault, OAuth or publishing.
- **A4→A5→A6→A8 integrated video rehearsal:** [integration README](integration/README.md) describes GitHub-hosted generation of a real original-only MP4, independent file-hash and FFprobe QA, storyboard provenance checking and mandatory quarantine. It publishes only a seven-day original demo artifact. **No third-party footage, real voiceover, signed license, YouTube upload or A9 licensed pilot**.
- **A5 original-only media lab:** [rendering and QA guide](a5/README.md), FFmpeg/Pillow source-free sample, 48kHz synthesized preview tones, visual-script SRT and ffprobe mobile-format checks; **not real licensed footage or voice narration**.
- **A4 original editorial studio:** [editorial README](editorial/README.md), the source-free YMH Ep347 concept fixture and `scripts/branch3_a4_editorial.py` with adversarial tests. This is a draft narrative workflow, **not licensed footage, a finished video or publishing approval**.
- **Overall progress:** [planning-weighted tracker](architecture/progress-tracker.json) estimates **62% implemented / 38% remaining** across A0–A10; partial components do not imply live functionality.
- **A6 release-security preflight:** [release README](release/README.md) documents exact MP4/metadata/rights/channel/schedule signatures and quarantine. Ephemeral Ed25519 test keys validate integrity checks; **no real owner signing key, final licensed asset or release authority** is enrolled.
- **A8 private-first dry-run:** [A8 README](a8/README.md) documents private-only future UTC scheduling, an exact release attempt hash, duplicate/ambiguous-upload quarantine and separate remote reconciliation. The code cannot upload or schedule and has **no durable atomic ledger or live Google write authorization**.
- **Protected Clivox read-only connection:** GitHub environment `clivox-readonly` is **created and API-verified** with reviewer `Tirthanand17`, selected `main` branch and administrator bypass disabled; no secrets have been added. [Owner connection setup](a7/OWNER_CONNECTION_SETUP.md) describes the remaining Google OAuth consent and protected environment secrets. The new manual-only workflow cannot upload or publish.
- **A7 read-only YouTube OAuth preflight:** [A7 README](a7/README.md) and `scripts/branch3_a7_readonly_youtube.py` support fixed-host OAuth refresh, `channels.list(mine=true)` exact Clivox identity verification, and bounded first-page upload inventory. All current fixtures are synthetic; **no live Clivox Google consent, dedicated credentials or authenticated YouTube identity readback exists; the GitHub `clivox-readonly` environment is configured separately**. No uploader is enabled.
- **Next development dependencies:** actual creator-granted licensing with game/music/guest rights; owner review of Content Rewards contract terms; approved confidential media location; and exact-source editorial verification.

## First creator-clipping pilot (2026-11-12)
- **Owner phone verification completed** and live YouTube Studio shows **Intermediate Enabled**; Advanced Eligible.
- **YMH 2 Bears 1 Cave Episode 347** now selected as the **primary research pilot**: official show page, episode source, creator invitation and a source-free original concept in `pilot_ymh_ep347.json`.
- **Rights and contract blocker:** Content Rewards Creator Terms §§17.2/17.6 place third-party rights clearance on participants and can assign approved final edits to the brand. Do not join or accept the contract on behalf of the owner; require informed approval and exact campaign-specific commercial clipping permission.
- New offline prelaunch validation: `scripts/branch3_validate_pilot_ymh.py` + tests; all publishing and downloading disabled.
- Full evidence: `content_rewards_contract_review_2026-11-12.md`.

- **A10 analytics (synthetic only):** [analytics and experiments README](a10/README.md) validates simulated YouTube Analytics response tables, keeps Studio feed measures unknown, tests category-and-hook comparisons without declaring fake winners, and generates privacy-safe CI reports. **No real Clivox channel analytics are connected.**

## Current first-content research status (2026-11-12)
- **Five public campaign leads** are logged in `clip_source_watchlist_2026-11-12.json` as research only: FaZe tournament, IShowSpeed x Expedia, YMH Studios 2 Bears 1 Cave, and two excluded/paused alternatives.
- **ZERO approved creators and ZERO authorized clips**. Public clip campaigns are not assumed to be a direct license from the original rights holder; campaign operator, underlying music/game IP, YouTube commercial scope and approval requirements must be verified separately.
- **YouTube intermediate features Enabled**, verified live after owner-completed phone verification on Nov 12; Advanced remains Eligible. No phone details are stored in GitHub.
- Read `first_clip_pipeline_plan.md` for first three rights-contingent concept treatments and research-backed analytics plan; `permission_request_templates.md` for non-sent official rights requests.

## Files
- `architecture/` and `contracts/`: full design, rights-aware state graph, schemas, implementation plan and tests
- `media_storage/`: A3 confidential media storage policy, unlicensed source manifest and fail-closed preflight; no private vault/footage stored
- `editorial/`: A4 original source-free storyboards and substantive-commentary planning; no unlicensed footage or fabricated quotes
- `a7/`: isolated read-only Google OAuth identity fixtures, tests and unconnected credentials plan
- `a8/`: private-first future scheduling and duplicate-retry dry-run; no uploader or live ledger
- `a10/`: synthetic-only Shorts analytics fixtures and experiment evaluation; no real channel data
- `integration/`: original-only GitHub A4–A5–A6–A8 real video evidence and quarantine rehearsal
- `channel_state.json`: verified creation, channel identity, branding and safety configuration
- `creator_permissions.json`: empty creator allowlist; no creators eligible by default
- `scripts/branch3_creator_permission_gate.py`: fail-closed candidate intake check; never upload permission
- `viral-content-strategy.json`: five content pillars, priority order, test signals, release blockers
- `pilot_ymh_ep347.json`: first source-free comedy pilot concept and exact rights gates
- `content_rewards_contract_review_2026-11-12.md`: primary Creator Terms evidence and IP assignment warning
- `clip_source_watchlist_2026-11-12.json`: five unverified campaign leads, not an allowlist
- `first_clip_pipeline_plan.md`: first three clip concepts and launch workflow
- `permission_request_templates.md`: creator/rightsholder outreach drafts, not sent
- `scripts/branch3_validate_clipping_watchlist.py`: fail-closed research-only candidate check
- `research.md`: policy evidence and strategy
- `channel-profile.md`: exact ready-to-paste description and visual configuration
- `rights-and-release.md`: source approval/claim handling
- `launch-checklist.md`: setup and first 30 days
- `source_registry.template.json`: empty rights ledger, not permission
- `branding/clivox-live-avatar.png` and `branding/clivox-live-banner-2560x1440.png`: actual YouTube-uploaded premium PNGs archived from the owner's Downloads folder
- `branding/`: additional original scalable SVG studies, no use of borrowed logos/faces

No raw downloaded third-party video, copyright media, refresh tokens, signed URLs or personal information may be committed to this public repository.

**Updated full-system estimate:** 54% engineering planning completion / 46% remaining across A0–A10; not a measure of live publishing readiness.

## A10 analytics prototype
The [A10 analytics README](a10/README.md) explains synthetic-only metric parsing and 1/3/7/14-day experiment reviews. Live Clivox OAuth/Analytics data and real published videos remain unconfigured. Overall engineering planning estimate: **54% implemented / 46% remaining**.

**Current full-system estimate:** 54% engineering implementation / 46% remaining, with A7 Google OAuth connection still unverified. See `architecture/progress-tracker.json`.
