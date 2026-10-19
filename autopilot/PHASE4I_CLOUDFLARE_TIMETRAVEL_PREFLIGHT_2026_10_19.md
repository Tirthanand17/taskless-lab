# Phase 4I — Cloudflare D1 Free Time Travel: bookmark preflight, NOT restoration

19 October 2026 | public draft PR #5 | zero provider calls, offline policy only

## Official provider facts

1. Cloudflare exposes GET /accounts/{account_id}/d1/database/{database_id}/time_travel/bookmark with D1 Read permission. The returned opaque bookmark identifies a recovery state; it is not a timestamp or a proven backup. https://developers.cloudflare.com/api/resources/d1/subresources/database/subresources/time_travel/methods/get_bookmark/
2. A DIFFERENT endpoint, POST /time_travel/restore, can revert a production database. It is forbidden by this capability. https://developers.cloudflare.com/api/resources/d1/subresources/database/subresources/time_travel/methods/restore/
3. D1 Workers Free Time Travel retention is SEVEN days (Paid 30 days); this is not a durable historical archive. The actual Cloudflare account tier and database storage generation still require verification. https://developers.cloudflare.com/d1/platform/limits/
4. Export is a POST endpoint and may temporarily block D1 query traffic. It is not a harmless replacement for the authorized GET bookmark, and is excluded from this implementation. https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/export/
5. Cloudflare D1 Workers batch transactions are atomic over the batched SQL statements, and withSession supports sequential query consistency. Neither provides an atomic transaction with a remote YouTube upload. https://developers.cloudflare.com/d1/worker-api/d1-database/

## Offline code and tests

autopilot/cloud_d1_recovery_bookmark_policy.py strictly parses two already-provided untrusted GET-bookmark-shaped responses, validates the bounded opaque bookmark format and compares their values in memory. It returns no actual bookmark value, URL, channel ID, account, raw body or private token. Equal bookmark claims are insufficient to demonstrate snapshot isolation, and changed bookmarks require a hold.

All source authenticity, freshness, real usable backup, event-log recovery, actual restore, cloud writer fencing, D1 mutation, export/restore authority, safe upload retry and YouTube publishing fields remain FALSE. The module makes no network requests and writes no file.

autopilot/test_cloud_d1_recovery_bookmark_policy.py adds ten synthetic test methods: equal but untrusted markers, marker drift, bad plans, malformed error envelopes, leaked response fields, invalid or secret-bearing opaque values, oversized messages, missing historical restore and denied authorization fields.

The separate private draft repository has control/d1_bookmark_readonly.py: a dormant, separately owner-gated GET-only adapter with origin/no-redirect/size protections, plus a private redacted capsule and an offline pair comparison bridge. It has ten synthetic PRIVATE contract tests committed, but NOT EXECUTED while private Actions quota is unresolved. The public CI suite tests the pure policy, NOT the private HTTP collector nor any real Cloudflare bookmark.

## Production acceptance

No actual D1 bookmark, account plan, historical bookmark eligibility, Cloudflare storage generation, durable export, event-log restore, owner account, YouTube inventory or production backup was checked. A real restore would require separate authorization and a carefully isolated recovery procedure with a rollback plan. No automatic upload replay is authorized.

Existing 21 production acceptance subphases remain open across six unfinished major phases. Estimates ~45% software / ~20% live autonomous readiness, unchanged. Both public and private draft PR #5 remain unmerged. No Nirala use, provider connection, charge, Cloudflare mutation, OAuth change, YouTube upload, schedule or publication. Budget stays ₹0/month.
