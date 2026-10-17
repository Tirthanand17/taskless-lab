# FlowMinute Lab: Full Cloud Autopilot Architecture — 17 October 2026

**Integrated scope:** the three earlier FlowMinute briefs (high-engagement Shorts/long-form content, practical beginner-to-advanced Hindi/English tutorials with meaningful 3D and natural narration, and adaptive launch-aware publishing) plus the new hierarchical self-improving master-agent specification.

**Goal:** authentic educational engagement, watch time, returning viewers, and subscribers. No artificial engagement, fake metrics, guaranteed virality or filler videos. Default proposals: two Shorts and one long video per day, 90 draft slots per 30 days; temporary 6-Short/3-long days supported only if quality, capacity and permission gates pass. Cloud/laptop independence, no additional monthly charges (₹0), and no new service/billing/OAuth/security permissions without owner approval.

## A. Audit: reuse the working infrastructure

- Public source: Tirthanand17/taskless-lab. Existing autopilot/core.py has local duplicate-protected release reservations and media/topic gates. calendar.py and calendar_ledger.py include adaptive draft scheduling, UTC collision detection and local atomic reservations; preview_calendar.py can plan 90 monthly drafts. scout.py, launch_gate.py, editorial_gate.py, growth.py and engagement_metrics.py cover research leads and offline evidence/measurement logic. motion-v2 and render_inspection.py provide actual media rendering and FFmpeg inspection components.
- Private source: Tirthanand17/flowminute-control-private. Existing control/ledger.py requires durable persistent storage. Cloudflare Worker+D1 already hold an encrypted Google OAuth consent grant; the exact FlowMinute Lab channel is verified. OAuth lifetime is still blocked by Google External/Testing policies, and publishing/upload flags are OFF. Do not construct competing production release ledgers.
- Existing Google Apps Script is a read-only alternative prototype, not proof of durable or large-video uploads.
- Earlier 78 local technical/ledger regression tests have been described; this audit does not claim production cloud integration from those results.

## B. Current external constraints (official documentation)

- YouTube currently documents a default 100 videos.insert upload calls/day bucket, distinct from other API quota buckets. Verify project-specific allowance before media uploads: https://developers.google.com/youtube/data/determine_quota_cost
- Resumable uploads, exact video ID and authoritative API readback are required for interruption recovery. Never blindly create a second upload after timeout: https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol
- A video's scheduled publishAt requires the video to remain private and previously unpublished: https://developers.google.com/youtube/data/reference/rest/v3/videos
- External/Testing OAuth with YouTube permissions ordinarily has a seven-day refresh-token lifetime; the current Google Branding and verification dependencies are unresolved: https://developers.google.com/identity/protocols/oauth2/
- Cloudflare Workers Free: 10 ms CPU per invocation. Use it as lightweight orchestration, NOT FFmpeg/video processing: https://developers.cloudflare.com/workers/platform/limits/
- Cloudflare D1 Free has daily row limits; stop safely on exhaustion: https://developers.cloudflare.com/workers/platform/pricing/
- R2 includes 10 GB-month of Standard storage free, but can charge for overage and is NOT connected or approved. Do not activate a billable store as a presumed free fallback: https://developers.cloudflare.com/r2/pricing/
- Free public GitHub Actions runners can run software tests, but GitHub's terms prohibit unrelated hosted-runner workloads and disproportionate resource burden. Do NOT treat them as a general 24/7 free render farm: https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features
- YouTube Analytics provides source-measurable views, engaged views, likes, comments, shares, watch time and subscribers (subject to report coverage). Other Studio-only metrics remain unknown until verified: https://developers.google.com/youtube/analytics/metrics
- Multi-language audio and auto-dubbing are account/feature dependent; do not assume Studio features exist via YouTube upload API: https://support.google.com/youtube/answer/13338784

## C. Three-level hierarchy: single master, eight departments, bounded specialists

**Master Growth Orchestrator**: command interpretation, capacity, DAG and checkpoints, dependencies, priority and escalation, report assembly; never overrides safety/publishing rules.

| Department manager | Specialist role groups | Outputs and vetoes |
|---|---|---|
| 1 Research | Launch/evergreen/audience/scoring/source verification | Dated source-backed research package; external RSS is only a lead |
| 2 Creative | Hooks/Shorts/longform/retention/thumbnail/series | Original script, practical teaching example, truthful titles/thumbnails |
| 3 Hindi-English Language | English/Hindi/Hinglish/voice/subtitles/reviewer | Natural localized script, narrator profile, correct subtitle plan |
| 4 Visual/3D/Audio Production | Storyboard/real demo/3D/motion/audio/render/efficiency | Licensed assets, rendering and detailed scene plans |
| 5 Independent QA | Fact/media/audio/copyright/privacy/final release | Independent evidence; may veto any planned release |
| 6 Publishing Ops | Calendar/workflow/upload preparation/verification/recovery/cost | Controlled draft reservation and, later, exact authenticated release receipts |
| 7 Audience Analytics | Shorts/long-form/language/comments/engagement/report | Source-labelled metrics, comparable cohorts and language observations |
| 8 Learning and Engineering | Agent evaluation/prompts/experiments/regression/memory/release control | Testable improvements with rollback; never self-approve safety changes |

Roles are **logical specialist capability definitions** and are created on demand. Do not deploy dozens of separately billed AI processes. No unlimited self-spawning, and one accountable owner per task.

## D. Mandatory production workflow

Owner-approved policies → Master DAG → research → independent fact QA → original script and hook alternatives → Hindi/English localization → storyboard + real demo and 3D where educational → licensed narration → motion/FFmpeg render → independent media/audio/language/rights QA → validated media hash and private release ledger → optional owner-approved resumable upload → exact channel/video ID/processing/scheduled timestamp/public state readback → official Analytics → measured experiment candidates → regression, independent review and rollback.

Each task contract requires a stable ID, parent department, episode, objective, required input artifacts, accepted evidence, expected typed output, dependency IDs, priority, capped compute, deadlines when relevant, permissions, retry cap and escalation route. Artifacts use content hashes, source references and provenance; untrusted web text has no authority to issue commands. Quality review cannot certify itself and cannot call the publishing credentials.

Draft states: blocked → ready → running → staging complete; bounded failure → retry or quarantine. **Staging complete is NOT production QA approval.** The production release ledger uses independent authenticated receipt states, immutable YouTube IDs and no blind upload retries.

## E. Bilingual storytelling, visual quality and growth learning

- Produce English, Hindi or suitable Hinglish material deliberately, preserve technical terms, and provide correct subtitles. Default to one strong narration track plus secondary captions until verified Studio multi-language features are available; do not multiply low-value near-duplicate uploads.
- Two Shorts per day can use different licensed voice profiles. Every tutorial demonstrates a real task where possible (Excel, AI agents, programming, research, everyday tools), with meaningful diagrams/3D and no fabricated transactions.
- FFmpeg video stream, audio, durations, black frames, safe text placement, actual captions, pronunciation, natural narration and rights are separate QA gates. Technical PASS alone is never a publish PASS.
- Collect official metrics by episode, age and format. Compare Shorts to Shorts and similar long videos to long. Keep engagement denominators, view source, sample size, delayed reports and unknown values explicit. Optimize real subscriber conversion, shares, comments and returning viewers, not vanity engagement.
- An Improvement Agent may propose changing hook, voice, language, format, title or render template. Independent regression and QA review plus a valid comparable experiment are required; security rules, OAuth scopes, spend caps and upload privileges cannot self-modify.

## F. Zero-rupee control and compute architecture

1. Keep source, tests and software deployments in public GitHub without secrets/private media. Use GitHub Actions only for legitimate repository software CI and reasonable test benchmarks.
2. Keep credentials and the existing encrypted grant solely in the private existing Cloudflare vault. Never copy to public runners or specialist messages.
3. Cloudflare Worker Free handles short authenticated tasks, state/lease operations and bounded metadata requests. Resolve one authoritative D1/ledger migration before enabling new persistent release writes.
4. Full video rendering/storage must be benchmarked on **separately verified policy-compliant ₹0 capacity**. Do not assume 90 full videos per month are sustainable: calculate minutes, voice provider terms, storage duration, total bytes and licensed assets. If capacity fails, reduce work and report a blocker, not spend or use Nirala.
5. Fully unattended publishing remains blocked until stable OAuth, owner-approved pilot, media QA, capacity and upload/readback pass. Manual YouTube Studio scheduling is a fallback, not laptop-independent creation.

## G. Ordered phases, exit criteria and status

| Order | Owner | Phase | Exit evidence | Current status |
|---|---|---|---|---|
| 0 | Master | Inventory three briefs, new agent brief, two repos and quotas | No duplicate releases; risk register | Audited |
| 1 | Engineering | Bounded hierarchical agent organization, typed handoffs, dependency DAG, checkpoint | 17-stage mock episode, 9 queued/3 active, no permissions | **Implemented and GitHub CI tested** |
| 2 | Research + Creative + Language + QA | Typed source-backed research-to-bilingual-script staging adapters | Software CI, review hashes and non-publishing handoffs | **Staging integrated; real reviewer authentication and fact verification pending** |
| 3 | Production + QA | Storyboard/voice/narration/subtitle/render typed handoffs + FFprobe audio inspections | Full licensed, naturally reviewed Short and long MP4 with independent QA | **Staging code and synthetic technical tests implemented; real production and rights clearance pending** |
| 4 | Publishing + Security | Single durable state/lease migration; secure authenticated commands | Recovery/duplicate/replay tests and remote channel readback | Not deployed |
| 5 | Publishing + Owner | Durable OAuth and a separate approved private upload pilot | One private video ID + correct processing and schedule readback | Blocked |
| 6 | Growth + Learning | Authorized official Analytics and comparable experiments | Source-backed scorecards, rollback tested | Offline calculation only |
| 7 | Master + QA | Full no-laptop 3/day and 6+3-day simulation, outage and free-resource tests | Verified month capacity, receipts, operating controls | Unverified |

Current exact staging implementation:
- autopilot/agent_org.py: eight department managers, 48 limited specialists, one Master orchestrator, 18-stage bounded per-episode DAG (including independent bilingual review), up to nine episodes queued/three active, schema-checked evidence handoffs, deny-list of privileged actions, two retries, quarantine, local *test-only* SQLite checkpoints.
- autopilot/agent_org_demo.py: sample 1-, 3- or 9-video queue display. No models run, no videos made/uploaded/scheduled.
- autopilot/test_agent_org.py and flowminute-agent-foundation-ci.yml: safe software CI; source tests and preview.
- Existing calendar, source/creative quality, release ledger, FFmpeg and analytics modules are reused, not replaced.

**Phase 2 staging is now implemented and CI-tested:** source-backed ResearchPackage → separate FactReview → original CreativeScript and hook alternatives → English and Hindi drafts → independent LanguageReview, all bound by SHA-256 references and task-role permissions. The new 18-stage graph stops voice planning until the language review is recorded. See [Phase 2 validation and limitations](PHASE2_RESEARCH_LOCALIZATION_2026_10_17.md). **Not deployed as a cloud worker, not connected to an LLM or external fact checker, and no real localization/narration is generated.** Next: implement typed production storyboard/narration/subtitle plans and test actual representative media and rights, then plan a single verified durable production store. No new provider registration, laptop access, real video publishing or billing changes are authorized by this plan.

**Reporting vocabulary:** proposed / implemented / offline-tested / cloud-deployed / live-verified / blocked. Never infer live channel success from a mock result.


## Phase 3 staging checkpoint — 17 October 2026

Five additional typed steps now follow Phase 2's independently reviewed Hindi/English drafts:
`Storyboard`, `VoiceDirection`, `NarrationAssetRecord`, `SubtitleTimeline`, `RenderRecipe`.
Render planning now waits for storyboard **and** narration **and** subtitle plan. Visuals include safe overlays, contiguous scenes and labeled simulations; narrator profiles reference the exact reviewed language drafts; captions have bounded, nonoverlapping SRT timings. Existing `motion-v2/` and `render_inspection.py` are reused.

New `narration_inspection.py` runs actual FFprobe and FFmpeg full-decode on audio with SHA-256, sample rate, duration and silence checks; synthetic tone and silence fixtures test the tool, **not** human-sounding speech. Provider commercial rights, pronunciation, source fidelity, transcript alignment, actual rendered MP4, private storage and upload publishing remain unverified. No Cloudflare deployment, Nirala use, credentials or billable render APIs involved.

**Verified software CI:** [202 tests + 6 subtests pass](https://github.com/Tirthanand17/taskless-lab/actions/runs/39037503878).
See [Phase 3 media production and strict remaining gates](PHASE3_MEDIA_PRODUCTION_2026_10_17.md).


## Phase 3B actual-media and declared-rights evidence checkpoint — 17 October 2026

[Implementation and limitations](PHASE3B_MEDIA_RIGHTS_REVIEW_2026_10_17.md): `media_rights_review.py` rechecks the reviewed script/language contract, storyboard, narration, subtitle and render recipe hashes before inspecting actual media with FFprobe/FFmpeg. It compares the actual WAV hash to the declared audio asset, checks H.264/AAC MP4 codecs, and verifies that all used assets have local hashed rights-document evidence and an explicit claimed commercial-use permission.

**This is a stop-before-independent-review gate, not an AI copyright lawyer, voice naturalness inspector, final video approval or cloud rendering service.** Tests use three-second synthetic media and sample—not genuine—license documents. [GitHub CI run #39038547204: 221 tests + 6 subtests PASS](https://github.com/Tirthanand17/taskless-lab/actions/runs/39038547204).

**Next:** get real, separately reviewed voice/scene/caption evidence and confirm a compliant, sustainable ₹0 media compute/storage plan; then design a single trusted cloud ledger and prove authorization durability. No YouTube release flags have been enabled.
