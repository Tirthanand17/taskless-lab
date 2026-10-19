# Phase 5E — Cloudflare D1 read-only structural inventory candidate

**19 October 2026. Source-only, NOT deployed. Existing draft PR #5.**

## Scope

- No direct Cloudflare administration tool is available in this conversation. The user authorized *read-only inspection*, not new services, credits, Google OAuth grants, laptop access, new subscriptions, database migration or publishing.
- Existing private controller notes document Cloudflare D1 database `flowminute-controller-free`, a prior transient channel OAuth verification (2026-10-17), and *no independently audited current D1 schema*. Historical notes do not establish currently active cloud credentials.
- `autopilot/phase5e_cloudflare_d1_readonly_inventory.mjs` is a restricted Worker candidate. It exclusively uses constant `SELECT` from `sqlite_master` (five allowlisted object names) and constant `PRAGMA table_info` (four candidate release-ledger names). It reads zero application data rows, never touches encrypted OAuth values, and never issues SQL write statements.
- A successful response reports only the candidate table presence and approved safe column names; protected column names are counted but not emitted. It does not prove complete schema history, unique indexes, trusted Worker identity, global zero-overage billing, production migrations, or true media upload readiness.
- `/v1/d1/schema-inventory` accepts **POST with zero-length body**, no query parameters, a secret-backed high-entropy bearer key, five strict disable/authorization/budget flags and a native `FM_D1_RATE_LIMITER` binding. Auth and rate-limit failures result in no DB queries. `/health` is static.
- No public Cloudflare route or new credential binding should be created without a separate audited deployment approval. This source is not connected to the actual D1 database.

## Offline acceptance

- Node: `node --test autopilot/test_phase5e_cloudflare_d1_readonly_inventory.mjs`
- Synthetic tests exercise no-secret read-only SQL, protected-column redaction, missing/denied rate limiter, wrong flags, unauthorized key, request/body/path rejection, malicious catalog entries, malformed columns, and fixed no-migration output.
- Do not use a CI token or token material obtained from a local machine to run Cloudflare admin commands in public GitHub Actions. Do not upload private inventory exports to the public repository.

## Remaining gates

1. Approved authenticated provider-native read-only inspection on existing Cloudflare account; verify which Workers and D1 bindings actually exist, redacting encrypted Google credentials and private records.
2. D1 index constraints, schema compatibility, exact release ledger row reconciliation, backup and rollback review. **No production ALTER/CREATE/DELETE** without separate permission.
3. Secure cloud-only refresh token custody and renewable account authorization, media rights-cleared durable private storage, and proven nonbillable plan with no-overage controls.
4. Real cloud no-duplicate private YouTube upload/schedule pilot and processing/readback. This is separate from the earlier laptop-driven October 20 scheduling.

**Progress remains 25% (2/8 major phases). Original 21 production acceptance subphases remain open.** No claim of live Cloudflare access or autopilot deployment is made.

## Live authorized Phase 5E D1 inventory — 19 October 2026, approximately 21:05–21:15 IST

**Actual authenticated owner Cloudflare Dashboard inspection on Nirala, read-only only.** The existing production Worker `flowminute-brand-oauth-readonly-probe` has binding `DB` to Cloudflare D1 `flowminute-controller-free`. No Google OAuth secret/ciphertext values or private release-event rows were fetched; no SQL mutations or Worker deployments were made.

Observed from read-only Cloudflare D1 console queries:

- `sqlite_master` reported 11 total tables (including SQLite/Cloudflare internals); 5 names matched the `fm_%` pattern. The database overview separately displayed 9 tables and approximately 119 kB of storage at the time of viewing; the differing counts can reflect internal tables/provider UI definitions. Neither count proves account-wide billing protection.
- Existing **canonical** metadata ledger names: `releases` and `release_events`, plus `audit_heartbeats`, `youtube_release_observations` and `fm_upload_auth_attempts`. A previously verified `fm_oauth_channel_proofs` table is present. Credential-bearing records/tables were not inspected.
- Phase 5E's **former** four candidate table names (`fm_release_writer_lease`, `fm_writer_release_shadow`, `fm_releases_shadow`, `fm_releases`) are **not** in this production database. Do not create a duplicate ledger or migrate until authorized after reconciliation.
- `releases` schema (names/types only): `release_date` (PK part 1), `episode_id` (PK part 2), `channel_id`, `slot_ist`, `publish_at_utc`, `state`, `media_sha256`, `youtube_id`, `updated_at_utc`. The index list included nonunique `idx_release_state` and `idx_release_date_slot`, and unique primary-key and `youtube_id` autoindexes; `PRAGMA index_info('sqlite_autoindex_releases_2')` independently returned `youtube_id`. **A unique release-date/slot constraint was not observed.**
- `release_events` schema: `id` (PK), `release_date`, `episode_id`, `event_kind`, `detail_json`, `at_utc`. Index `idx_event_release` is nonunique. Event records and `detail_json` values were not opened.

**Decision:** Reuse the existing canonical `releases` / `release_events` schema for Phase 4 planning. Require audited single-writer CAS and explicit schedule-slot uniqueness semantics in a future separately authorized migration. Phase 5E has completed its **human-authorized read-only structural inventory**, not a verified credential, cost-cap review or publishing-service deployment. The source candidate now recognizes real table names while keeping the endpoint disabled.
