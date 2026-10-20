# FlowMinute Phase 5A — owner-only, three-slot YouTube readback candidate

**Date:** 2026-10-19. This is **staging code only** on draft PR #5; it is **not** the unattended laptop-independent publisher. No new provider, upload, schedule write, paid API or OAuth transfer is performed by this commit.

## Component

- `autopilot/owner_youtube_readonly_monitor.py` provides a read-only HTTP client, using an owner-authorized **short-lived access token** supplied to the process at runtime by an **already-approved secret manager**. The token is never printed, written to a manifest, encoded in URL query arguments or committed. It checks `channels.list(mine=true)` and then reads the exact three `videos.list` snapshots. OAuth bearer redirects are rejected before forwarding and responses are capped at 1 MiB.
- Three planned slots must have exact keys: `short_morning` (11:00 IST), `long` (16:00 IST), `short_evening` (20:30 IST). These are converted to exact UTC instants using `Asia/Kolkata`.
- Input is a local **private** JSON mapping of the three slot names to `{"video_id":"11_chars_or_null","title":"exact owner-approved title"}`. An absent video is `null`, not an invented ID. The program rejects unexpected fields, duplicate video IDs, bad date, missing title, incorrect channel/video identity, unprocessed videos and mismatched `publishAt`.
- A lane is `SCHEDULED_VERIFIED` **only** if the authorized owner API returns Private, processed, processing-succeeded, exact future `publishAt`, correct title and channel. After its due time, a Public state is labelled **`PUBLIC_STATUS_ONLY`**, never anonymous viewer playability or proof that scheduling occurred in advance.
- Network/API uncertainties and missing credentials **fail closed**. The module cannot upload, edit, schedule, charge or renew credentials. Aggregate numbers are read-only observations and **never** set `cloud_autopilot_ready=true`.

## Test and use

Synthetic and adversarial no-network tests: `python -m unittest autopilot.test_owner_youtube_readonly_monitor -v`. They cover duplicate upload ID risk, three exact local-to-UTC slots, two-of-three missing long behavior, correct owner, correct title, processed states, non-public/private overdue states, clock safety, input injection and OAuth error redaction.

Future approved cloud-only invocation after placing **only a short-lived token** in a protected environment variable (do not store the token in GitHub):

```bash
python -m autopilot.owner_youtube_readonly_monitor --date 2026-10-20 --manifest /private/safeguarded/flowminute-2026-10-20.json
```

The process reads `FLOWMINUTE_YOUTUBE_ACCESS_TOKEN` **at execution time**. The manifest belongs in private protected storage; the public repository does not contain personal OAuth or private video ledger data. Do **not** run this on public GitHub Actions with any owner token.

## Relation to live October 20 release

Prior authorized local YouTube publishing verified an **11:00 IST English Short** (video `[see private release ledger]`) and an **20:30 IST Hindi Short** (video `[see private release ledger]`). The long episode was **still rendering** at the previous real-time check, so its video ID is unknown and **not** counted. These direct/manual release results do not turn this cloud-only candidate into a deployed autopilot.

## Remaining blockers (unchanged)

- Cloud secret manager and renewable, owner-confirmed OAuth identity **not** connected to this read-only module.
- No laptop-independent durable private media storage with hard ₹0 ceiling.
- No cloud full-duration, voice/rights-cleared, independently reviewed daily content pipeline; software test evidence is not content legal/editorial approval.
- Existing Cloudflare D1 single writer and migration are unresolved; upload idempotency and live provider reconciliation are not deployed.
- No authorized unattended upload or recurring scheduled publication, no live owner Analytics ingested. Keep `FM_UPLOADS_ENABLED=0`, `FM_SCHEDULING_ENABLED=0` and draft PRs unmerged.

**Project milestones:** 8 phases (0–7); phase 0 and phase 1 accepted for software/audit scope; phases 2–7 retain uncompleted live acceptance. The previously tracked **21 outstanding production acceptance subphases remain open**, despite this nonpublishing component. No production-readiness percentage is earned by synthetic tests alone.
