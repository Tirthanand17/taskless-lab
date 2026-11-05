# Branch 2 — B4d1 real GitHub daily research-receipt retention and honest progress accounting

**Prepared:** November 5, 2026 IST. **Status:** Implemented as source/PR. GitHub workflow run and uploaded artifact must be independently verified AFTER merge to claim operational deployment. Branch 1 existing assisted YouTube releases and schedules not modified.

## The user-visible percentage problem

The 38/100 production score was manually documented on November 4 in docs/status/branch2-completion-audit-2026-11-04.md. It was a **production-readiness score**, not an estimate of code merged or number of CI passes. PRs #35–#41 completed progressively useful but nondeployed source/template/synthetic CI contracts, so the same 38 was repeated rather than inflating a live score. Going forward, report TWO distinct measurements and cite concrete evidence:

1. **Production capability score** — original 100-point weighted rubric (architecture 14/15, research 6/15, physical AV 13/20, authenticated rights/editorial 2/15, owner cloud 3/15, real OAuth+YouTube 0/15, 7-day live cadence 0/5 = **38/100**). A new source-only PR cannot automatically increase this. Until a real GitHub run produces a *retained* metadata-only three-slot research artifact, B4d1 earns **no new production point**.
2. **Actual live delivery proof** — separately show 0/21 (0%) until 21 independently owner-authenticated YouTube scheduled/published reads exist. None of #35–#42 is itself a YouTube upload.
3. **Engineering source milestone ledger** — completed PRs #35 manual owner S3 KMS template, #36 B4a private-first mock, #37 B4b1 real disposable PG fencing, #38 B4b2 no-network recovery, #39 B4b3 AES-256-GCM fake sessions, #40 B4c1 owner-injected read-only OAuth preflight, #41 B4c2 inert manual Fargate task definition. These are **seven merged source/testing milestones**, not seven production deployments.

**Conditional rubric proposal:** once a **post-merge main-branch Actions run** visibly executes the public source scout/evidence + real three-slot daily plan, uploads a new sanitized machine-readable Actions artifact, and GitHub API independently lists that unexpired artifact, the research/topic pipeline score can rise by exactly **one point (6→7 of 15)** for tangible persisted cloud-draft evidence, yielding **39/100 production-capability score**. Still 0/21 YouTube. If no actual artifact exists, keep 38/100. This update is qualitative and conservative, not a claim of 39% of days or videos already published. The offline PR test alone is insufficient.

## What B4d1 actually changes

- Existing .github/workflows/flowminute-daily-cloud-foundation.yml already runs daily by default-branch cron at 13:17 UTC (18:47 IST), preparing **tomorrow's 11:00 Short A, 16:00 Long, 20:30 Short B**. It already contacted allowlisted public feed URLs, observed bounded public sources, produced an *unapproved* three-slot draft and deleted it. None of this was content research, reviewed facts, original scripts, media or uploaded YouTube videos.
- New autopilot/daily_evidence_bundle.py validates all three release slots, correct next-day IST and matching UTC times, 48 role/54 handoff draft structure, disabled content/rights/media/upload/billing flags, same-hour source/plan clocks, consistent bounded source-observation counts and review=false. It generates a single **small public metadata-only JSON** with hashes of the upstream draft and source observation, public publisher labels, observed counts, and explicit missing fact/rights/media/approval/YouTube status. It never copies raw headlines, URLs, article text, source bodies, model prompts, OAuth credentials, private media or approval receipts.
- A source SHA256 is a content integrity marker (NOT a real owner signature, immutable third-party anchor or factual source approval). Source reports and headlines are **not themselves archived**, only hashes and bounded counts.
- The existing daily workflow now runs the builder only on schedule, dispatch or qualifying main push (not on public PR), validates the 3-slot receipt and its release=false content and uploads it through actions/upload-artifact with 14-day retention and exact if-no-files-found:error behavior. Only the metadata-only receipt is retained, not media or raw scout feeds. Workflow scratch files are cleaned on all outcomes.
- New adversarial offline tests ensure no fake approvals, transformed slot times, wrong channel, extra synthetic handoff progress, forged factual claims/paid calls or malformed source reports may be saved. Existing daily workflow tests also run them.
- GitHub Actions storage/artifact retention settings apply. Public repository artifacts may be available to anyone who can access the workflow, so no sensitive or owner-private data is allowed. 14-day expiry means NOT permanent offsite recovery, versioned S3, a backup, or private cloud vault. Artifact storage and GitHub Actions usage may count against quotas or billable overages. Do not promise free/unlimited storage; owner must review account billing/retention before increasing use.

## Operational deployment proof to collect

On PR:
- Dedicated daily foundation tests complete; no network scout or artifact publish from PR.
- Existing repo Content Quality Gate, public cloud scout and cloud render smoke all succeed.

AFTER merge:
1. A **main-branch push** of the workflow file must trigger the Daily Cloud Autopilot Foundation (NO PUBLISH) workflow (GitHub path filter includes that YAML). It should run the same GitHub-hosted public real scout/evidence, create a TOMORROW plan and upload a single tiny sanitized artifact.
2. Use GitHub's workflow run jobs and **workflow run artifacts** API to independently verify successful publication of a new non-expired Actions receipt; inspect the actual runner logs for exact date, plan count and no-release marker. If the scout fails due to remote network, keep status blocked; do not invent an artifact.
3. The next day's scheduled cron is a future test of recurrence; one main-push run is NOT proof the cron will run seven days. GitHub's schedule may be delayed or missed under load; no hard realtime YouTube publication can rely only on this mechanism. The owner will eventually need independent protected scheduling and missed-run alerts.

## Remaining critical path

The next material production steps are **not additional mock review signatures**:
- Owner-selected real cloud account, region, budget and approved billing/data/copyright retention, actual private VPC/identity/ECR image, key/secret vault and independently inspected live IAM policies.
- Durable private media (actual licensed reviewed MP4/SRT/WAV/PNG) and PostgreSQL one-use session recovery under protected persistent credentials, real publisher-worker service and monitor.
- Independently reviewed current stories, claim-by-claim human fact checks, original voices/media licensing, actual watched AV final release and owner consent.
- Real owner OAuth, one-writer private-first videos.insert/same-session resumption, independent YouTube video/channel/caption/thumbnail/processing and future 11:00/16:00/20:30 IST readback.
- Full laptop-off seven-day continuous live proof, **21 genuinely distinct verified scheduled/published remote videos**.

**Public CI is not authorized to publish real videos or incur new paid cloud costs.** Code lives on GitHub; no owner's laptop was accessed.

Sources: [GitHub Actions artifact retention and storage](https://docs.github.com/en/actions/tutorials/store-and-share-data); [GitHub scheduled workflow delay/drop caveats](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
