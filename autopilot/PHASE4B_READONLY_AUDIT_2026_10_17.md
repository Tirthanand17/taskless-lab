# Phase 4B — read-only schema inventory and release reconciliation

**17 October 2026. Offline software staging only; no live D1 administration, no YouTube API call, no schema migration, and no production writes.**

## Motivation: three distinct ledgers are not interchangeable

| Ledger | Identity | Format constraints | Real release authority |
| --- | --- | --- | --- |
| Private `control/ledger.py` SQLite | `(release_date, episode_id)` | stage, optional media SHA, optional immutable YouTube ID, optional publish time | No durable live volume verified |
| Public `autopilot/core.py` draft SQLite | `episode` | kind, planned UTC, unique SHA, channel, stage | None: local draft/test adapter |
| Phase 4A reference `phase4_releases` | `(channel_id, episode_id)` | version/fence/lease, immutable media and canonical UTC slot, upload uncertainty | None: test-only mock |
| Existing Cloudflare D1 deployment | **Unknown until authorized live inventory** | Existing encrypted Google grant and metadata audit; exact tables not observed | Must not be replaced by guesswork |

**Risk:** silently equating an old `release_date + episode_id` with a public draft `episode` can overwrite a legitimate scheduled release, bind the wrong YouTube video ID, or duplicate a resent upload. A D1 table name guessed from test fixtures is not proof of real deployment schema.

## New safe offline code

- `autopilot/phase4b_readonly_audit.py`: opens an existing disposable SQLite fixture using `mode=ro` and `query_only=ON`. Reads **schema metadata only**, never SELECTs data rows. Sensitive OAuth/secret/grant tables are redacted by a one-way short name digest; sensitive column names are masked. It does not contact Cloudflare or accept credentials.
- `known_ledger_compatibility()`: labels known private/public/Phase4A layouts only from supplied offline structural metadata and always returns **production_migration_ready=False**.
- `reconcile_claimed_releases()`: checks format-neutral episode records from proposed historical/local/YouTube sources for mismatched media hashes, YouTube IDs, UTC slots, ownership and missing IDs. The caller could forge a source label, so **safe_to_migrate=False** and **safe_to_publish=False** ALWAYS. This is a diagnostic comparison, not remote verification.
- `autopilot/test_phase4b_readonly_audit.py`: 18 additional isolated security and reconciliation tests using disposable SQLite fixtures. Distinct from the prior Phase 4A 18 tests.

## Approved-only future live D1 schema inventory

Cloudflare documentation explicitly supports schema metadata inspection, including `PRAGMA table_list`, `PRAGMA table_info("TableName")`, `PRAGMA index_list("TableName")`, `PRAGMA index_info("IndexName")`. Run them **only through an existing owner-approved read-only access path** in Cloudflare's provider-supported dashboard or API; a D1 Read-only token would require separate approval if no approved connection exists.

Do not run these commands from a public runner and do not paste D1 bindings, credentials or raw exports into chat/GitHub. Query only the _non-secret schema_ of release and metadata objects that are authorized for audit. Do not execute `SELECT *` against OAuth/token/grant tables, export database files, inspect ciphertext, or show encrypted authorization values. Avoid raw `CREATE TABLE` SQL dumps if they can expose defaults. No `ALTER`, `DELETE`, `INSERT`, `UPDATE`, `DROP`, `wrangler d1 migrations apply --remote`, or security-rule changes.

**Stop** if a Cloudflare 1010 client block prevents supported dashboard access; bypasses are not authorized. Workers URLs and real D1 table names remain unverified in this phase.

## Read-only identity reconciliation required before any migration proposal

1. Independently identify one exact FlowMinute channel `UCCcL9Q_jqVq6LJmnYUSAFZA` using approved YouTube read-only OAuth. Never infer ownership from title, public listing, channel handle, or a caller-supplied `authenticated=True`.
2. Read historical video IDs, YouTube processing/privacy status, scheduled time and actual public state through an authenticated read-only path. No upload or schedule changes.
3. Compare to existing D1 metadata, private historical ledger and GitHub draft data. Track per-source provenance, observation time and canonical UTC; never overwrite a blank remote ID with an arbitrary local value.
4. Flag collisions/mismatches, uncertain `upload_started` and scheduling retry states as **QUARANTINED_REQUIRES_MANUAL_RECONCILIATION**. Do not auto-reupload on missing response.
5. Back up and reconcile existing D1 schemas **before** producing a schema-specific migration diff. Preserve encrypted OAuth/grant tables untouched.
6. Prove rollback, single writer, atomic conditional transitions and trusted-clock fencing using D1's real supported semantics; reference SQLite `BEGIN IMMEDIATE` is not itself a D1 transaction recipe.
7. Request separate production migration approval. A later private-video publishing pilot also requires fully reviewed media, appropriate OAuth scopes, free secure private media storage and explicit authorization.

## Verified sources

- [Cloudflare D1 SQL statements / PRAGMA compatibility](https://developers.cloudflare.com/d1/sql-api/sql-statements/)
- [Cloudflare D1 Worker API](https://developers.cloudflare.com/d1/worker-api/)
- [Cloudflare D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/)
- [Cloudflare D1 Read-only API permission](https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/query/)

## Safety and status

`FM_UPLOADS_ENABLED=0`, `FM_SCHEDULING_ENABLED=0`, `publishing_enabled=false`. Cloud operations were **NOT RUN**. Nirala untouched. ₹0 recurring budget. No new provider, OAuth scopes, billing, storage activation or account changes. This implementation is a no-deploy offline compatibility audit, not an automatic YouTube publisher.

**Exit gate:** until owner-authorized actual D1 schema + authenticated YouTube readback arrive, mark **PHASE4B_OFFLINE_TESTED_LIVE_RECONCILIATION_BLOCKED**.
