# ADR-0021 — Branch 2 B3d4c2b2: actual multi-worker PostgreSQL fencing test, not a production deployment

**Date:** 2026-11-04 Asia/Kolkata. **Branch:** cloud-only autonomous research→media→YouTube. **Scope:** security testing for the private inference request boundary, not live Gemini or YouTube API enablement.

## Prior work and gap

PR #23 (B3d4c2b1) implemented a SQLite one-use, ambiguous-request-no-retry burn, revalidating B3d4c2a's owner-signed consent and source-context digest. Its tests were confined to a single isolated local filesystem. A laptop-off production application with multiple independently scheduled agents needs a **shared private durable database** with transactional coordination across distinct processes and machines. A GitHub-hosted SQLite file does not provide that.

## Research: authoritative public documentation, 2026-11-04

- [PostgreSQL row-level locks](https://www.postgresql.org/docs/current/explicit-locking.html): SELECT FOR UPDATE holds a row lock until transaction end, serializing conflicting update operations. Combine a unique lease ID and unique episode ID with an explicit daily row guard; simple SELECT COUNT without a lock could be bypassed by concurrent writers.
- [PostgreSQL transactional constraints](https://www.postgresql.org/docs/current/sql-insert.html): INSERT failures caused by duplicate identifiers roll back the transaction; ON CONFLICT DO NOTHING establishes the daily row before locking.
- [GitHub Actions Postgres service containers](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers): actual Postgres can be run as an isolated ephemeral service container on an Ubuntu GitHub-hosted runner, with separate Python worker processes connecting by local TCP. The service container is destroyed after that job; **it is not a hosted production database or an across-day durable store**.
- [Gemini API billing](https://ai.google.dev/gemini-api/docs/billing/): project spend caps are experimental and may lag by ~10 minutes, causing overages. A transaction ledger cannot prove billing is zero, nor does a signed project SHA prove account eligibility.
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use): PR jobs should be unprivileged, read-only, no real provider credentials, no private owner signing keys, no customer data.

## Decision: real PostgreSQL concurrency and crash tests on GitHub CI

Implement a tightly scoped **test-only PostgresMockInferenceFence** with a tiny schema in the repository. The only allowed database is named flowminute_fence_ci with user flowminute_test; the connector is supplied as a dependency, and there is no public API taking a production DSN, vault token or Gemini key.

A writer revalidates the full B3d4c2a signed owner intent against an external digest, separate owner public-key registry and sanitized exact research context. In CI these are ephemeral signatures and artificial public metadata, **not a real person, private project entitlement or external account consent**.

Within the *same* PostgreSQL transaction, a writer:
1. Inserts a unique per-IST-day guard row with ON CONFLICT DO NOTHING. Concurrent creators wait for the first transaction.
2. Locks that row with SELECT FOR UPDATE, verifies the same purported owner/project/provider scope and a maximum of three total burnt slots.
3. Inserts a unique lease ID and episode ID. Rejects conflicting workers, changed context or duplicate attempts. Keeps the document's BURNED_UNCERTAIN_NO_RETRY state on durable commit.
4. Updates the day's consumed count and commits before the script mock is validated. No worker may reuse a burn after an ambiguous remote response or restart; **this is at-most-once intent, not guaranteed eventual delivery**.

An independent mock completion worker needs the 64-hex-character ephemeral fenced token, which is stored solely as SHA256 in the database. Another transaction locks the individual burn and transitions it one time to MOCK_DRAFT_VALIDATED_NO_RELEASE or MOCK_DRAFT_REJECTED_NO_RETRY. Two concurrently completing workers cannot both succeed. No local or DB-only result becomes an editorial, budget, rights or release authorization.

Integration tests use *actual* GitHub-hosted PostgreSQL 16 with multiple independent Python processes and distinct PostgreSQL connections: a 20-worker collision test, 24 competing attempts across the three slots, session restart and ambiguous outcome, cross-project signed scope mixing, forged token/receipt, invalid script burn, and no secret/prompt content in table rows.

The CI schema is installed only into its disposable service. It is **not an irreversible append-only production ledger**: the ephemeral test DB user owns its tables and can reset them; there is no multi-region failover, backups, third-party account check, DB IAM, TLS, separate write/admin roles, protected secret custody, audited migration, or durable provider account relationship.

## Technical artifacts

- autopilot/postgres_mock_inference_fence.py — real PostgreSQL row-locked reservation and fenced mock-only close, hard CI database identity, no provider or publisher client.
- autopilot/sql/001_postgres_ci_inference_fence.sql — mock PostgreSQL schema (unique keys, foreign key, daily guard and state checks) for unprivileged GitHub-hosted integration only.
- autopilot/test_postgres_mock_inference_fence.py — independent process/database-connection tests and fail-closed negative cases. Skipped when there is no CI PostgreSQL service; the dedicated workflow explicitly enables these tests and requires the service.
- .github/workflows/flowminute-b3d4c2b2-postgres-fence.yml — GitHub-hosted Postgres 16 service, synthetic local DB password (not a real account credential), psycopg v3, test signatures, no model or publishing secrets, and actual service assertions.

## What this proves and what it does not

**Proves:** code correctly coordinates independently connected worker processes for a single ephemeral PostgreSQL service and refuses duplicate/burned mock requests. Validates the SQL transaction boundary against real DB behavior, not an in-memory simulation. GitHub-hosted runners can independently connect to a disposable Postgres service and use the same unique constraints.

**Does NOT prove:** deployment of a permanently durable/private cloud database, real separately enrolled owner, acceptable real provider data-sharing terms, model access or free tier, real project billing limits, actual inference quality, human fact/rights review, full watch/listen, or working YouTube publishing/scheduling.

## Future order

**B3d4c2b3 private service deployment:** Owner must explicitly select/approve a genuine private cloud database, vault, data retention, account tier, terms and spend cap; production must provision separate DB admin and runtime roles, backup+restore drills, least privilege, region/residency, TLS and real tenant isolation. Only then enroll a real owner and provider account and test truly persistent multi-job/cloud-worker contention. Do not copy the mock CI account or expose private keys in public GitHub.

**B3d4c2c:** After external permissions and real entitlement verification, securely generate 3 genuinely distinct source-grounded original educational scripts and independently review every factual narration/thumbnail/visual surface. Construct topic-specific original animations/assets, licensed voice/music/SFX, fully timed captions and final video playback/rights approvals with externally pinned final MP4 + SRT + thumbnail + metadata receipts. No generic CSV demos for unrelated topics or repeated templated videos.

**B4:** private object storage, signed approval ledgers, OAuth and a fenced YouTube writer; verify status.privacyStatus=private, processing success, captions/thumbnail readback and future publishing windows. **B5:** 21 genuine original releases in seven consecutive days with laptop off and zero unauthorized spend.

**Branch 1 assisted YouTube uploads/schedules are independent and unchanged.** This PR performs no YouTube action.
