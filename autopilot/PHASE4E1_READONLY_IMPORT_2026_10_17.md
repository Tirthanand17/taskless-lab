# FlowMinute Lab Phase 4E.1 — safe provider-shaped read-only metadata import

**17 October 2026 — implementation is OFFLINE ONLY. Production Phase 4E is still blocked.**

## Completed in the review branch

`autopilot/phase4e_readonly_import.py` adds two bounded, dependency-free parsers that can consume **sanitized provider-shaped response dictionaries supplied by a caller**:

1. `parse_d1_schema_observation(table_list_rows, table_details)`: accepts the shape of D1 `PRAGMA table_list` and optional per-table `table_info`/`index_list`/`index_info` summaries. Never executes SQL, connects to Cloudflare, loads data rows, exposes default SQL expressions or reports protected OAuth/grant/token table and column names. Redacts indexes that depend on protected columns rather than incorrectly claiming they enforce uniqueness.
2. `parse_youtube_channel_video_observation(channel_response, video_response)`: reduces caller-provided `channels.list`/`videos.list`-shaped objects to exact video IDs, owner channel, privacy, processing status and UTC publish timestamps. Rejects wrong channels, malformed or duplicate video IDs, unsupported privacy states, invalid schedule instants; flags unknown processing and incomplete pagination. Does **not** include video titles, descriptions, comments, tokens or analytics.

These shapes are not actual authenticated API responses. A caller may fabricate `items`, `status` or `channelId`. Outputs unconditionally include `saw_authenticated_provider_request=false`, `migration_authorized=false` and `publication_authorized=false` (YouTube).

`autopilot/test_phase4e_readonly_import.py` contains 21 synthetic provider-shaped regression tests to check sanitization, size limits, ownership and schedule precision.

## Provider-backed read-only runbook (NOT performed)

**Prerequisite:** separately approved Cloudflare account/permission access and independently authorized YouTube OAuth read-only scope for exact channel `UCCcL9Q_jqVq6LJmnYUSAFZA`. No new provider connection/OAuth consent was authorized merely by adding code. Never paste bearer tokens or encrypted grant bytes into ChatGPT or GitHub.

### Cloudflare D1

Use an authenticated provider-supported **read-only** dashboard/API path to inspect metadata only:

- `PRAGMA table_list`
- `PRAGMA table_info("EXACT_EXISTING_NON_SECRET_TABLE_NAME")`
- `PRAGMA index_list("EXACT_EXISTING_NON_SECRET_TABLE_NAME")`
- `PRAGMA index_info("EXACT_EXISTING_NON_SECRET_INDEX_NAME")`

Identify table names first rather than guessing them. Inspect only authorized release/metadata objects. Do not `SELECT *` from grant/OAuth/token tables, `dump()` the database, export credentials, or run changes. Keep Cloudflare audit evidence in its protected owner-held environment, not in public CI logs. If access is blocked by provider security controls (including error 1010), STOP and use normal account support; no bypass.

### YouTube

A safe authorized reader must first verify the `channels.list` **mine** identity resolves exactly to the intended Brand Account channel, then paginate video IDs from the authenticated channel's uploads list and obtain owner-bound `videos.list` records for processing/private/schedule/public readback. Read every relevant page; never treat first-page results as exhaustive. Cross-check `snippet.channelId`, `status.privacyStatus`, `status.publishAt`, video ID and `processingDetails.processingStatus` if actually supplied.

YouTube published/processing truth remains unknown until an authorized provider call occurs. Public page scraping or GitHub draft files cannot confirm unpublished private videos. Never infer that a planned time means a video is scheduled.

Official references:
- https://developers.cloudflare.com/d1/sql-api/sql-statements/
- https://developers.cloudflare.com/d1/worker-api/d1-database/
- https://developers.google.com/youtube/data/reference/rest/v3/channels/list
- https://developers.google.com/youtube/data/reference/rest/v3/playlistItems/list
- https://developers.google.com/youtube/data/reference/rest/v3/videos/list

## Truth boundary

**4E.1 safe parser: implemented and tested.**
**4E.2 authenticated live Cloudflare/YouTube collection: not available.**
**4E.3 actual source reconciliation: blocked pending 4E.2.**

Existing 4D signed observations cannot make forged provider-shaped payloads authentic. A valid signature proves that a pinned key signed the claimed hash, NOT that Google/Cloudflare returned the content. True collector identity, provider trust chain and protected nonce memory still require a private reviewed deployment.

No production D1 reads/writes, OAuth changes, connection approvals, uploads, schedule/publication operations, paid provider, secret transfer or Nirala access. ₹0 monthly ceiling. Phase 4F is not ready and PR must remain draft.
