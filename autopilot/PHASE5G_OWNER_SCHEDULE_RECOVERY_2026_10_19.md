# Phase 5G — Existing YouTube long-video schedule recovery and owner readback

**October 19, 2026. Existing DRAFT PR #5. Source and acceptance evidence separated.**

## Real Phase 5G owner API recovery

At approximately **21:50 IST on Oct 19**, using the already authorized desktop OAuth session solely to call `channels.list(mine=true)` and `videos.list` on the exact immutable private Hindi long video, owner readback returned:
- Correct FlowMinute Brand channel and expected long-video title
- `status.privacyStatus=private`, `status.uploadStatus=processed`, `processingDetails.processingStatus=succeeded`
- **`status.publishAt=2026-10-20T10:30:00Z` = 16:00 IST** for the existing Hindi long.
- Local publisher `reconcile_schedule.py fm_20261020_long_hi` wrote a `scheduled_verified` immutable local receipt, without calling `videos.update` or `videos.insert`. The local publisher ledger now says `scheduled_verified` and stores the correct UTC timestamp.
- The two Shorts were already verified by the official owner YouTube API earlier. Their existing receipts were preserved; the generic reconciliation script intentionally refuses to reprocess an already-scheduled episode. A separate current all-three readback had a transient desktop-connection error; do not claim it succeeded. The verified long was freshly rechecked.
- Private `flowminute-control-private/state/release-watch/2026-10-20.json` now has **three** scheduled release receipts. The previous long failure resulted from a temporary discrepancy between schedule-write response parsing and eventual owner readback, not a missing upload. **No second video upload, no second schedule write.**

## Offline recovery policy (this PR)

- `autopilot/phase5g_owner_schedule_recovery.py` + `autopilot/test_phase5g_owner_schedule_recovery.py` enforce exact three-slot owner-identity/title, immutable video IDs, fresh readback, processed Private status, local IST-to-UTC schedule, and safe failure for missing/conflicting `publishAt`. All outputs redact titles and YouTube video IDs.
- Even when 3/3 caller-supplied observations match, the software returns **`ALL_THREE_RECEIPTS_MATCHED_UNATTESTED`**. It does **not** attest cloud credentials, create local or D1 ledger rows, re-upload a video, make YouTube schedule writes, or set cloud readiness true. Real trusted channel evidence must come from the authorized Google owner connector before any production use.
- Tests execute offline, with fake IDs and no OAuth, D1 or YouTube API calls. The original cached public test fixtures may exist in older Git history; current source must use only synthetic IDs.

## Next blocker

- The Cloudflare D1 canonical `releases` and `release_events` tables are still **empty**, although the real October 20 YouTube release receipts are confirmed. Do not assume this release is durable or safely recoverable from D1.
- The existing production `release_date,slot_ist` index is not unique. A narrowly authorized ledger backfill/migration with verified channel/IDs, independent backup and fenced writer is a separate stage requiring explicit permission.
- Renewable cloud OAuth secrets, Cloudflare production Worker deployment, rights-checked cloud media rendering/storage and hard global ₹0 cost enforcement remain blocked.

**Scoped Phase 5G schedule recovery + local reconciliation accepted after owner readback.** Entire Phase 5 production autopilot and all major phases remain unchanged (2/8 = 25%). No GitHub action, Google API or Node fake-result tests grant real unattended publishing permission.
