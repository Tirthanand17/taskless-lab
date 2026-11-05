# ADR-0034 — Branch 2 B4b1 PostgreSQL 16 persisted one-attempt YouTube fence (CI ONLY)

**Date:** 2026-11-05 IST  
**Status:** Proposed and unmerged until hosted real PostgreSQL checks are green. **No real YouTube publishing, OAuth, billable cloud or persistent production storage.**  
**Dependencies:** B4a private-first mock contract (merged PR #36), CI least privilege PostgreSQL roles (merged B3d4c2b3a), PR #35 manually owner-approved S3/KMS stack source (NOT deployed).

## Exact architectural problem

Branch 2 targets two Shorts (11:00 and 20:30 Asia/Kolkata) plus one long video (16:00 Asia/Kolkata) every day without an owner's laptop. Production YouTube can create an upload even if HTTP fails or the worker crashes before receiving a response. Retrying a fresh videos.insert may create a duplicate. B4a proved only an in-memory non-retry decision, which cannot survive two workers or a restart. B4b1 exercises genuine PostgreSQL unique constraints and SECURITY DEFINER permissions **in a disposable GitHub-hosted postgres:16 service**, but it is strictly mock-only and must not connect to a YouTube worker.

## PostgreSQL source and security design

- SQL: autopilot/sql/003_ci_youtube_mock_attempt_fence.sql. It requires existing disposable private schema and distinct roles from 002_ci_least_privilege_ledger.sql. Uses only a fake DB named flowminute_fence_ci.
- A committed reservation is atomic and durable *within the disposable PostgreSQL process*. UNIQUE constraints on (channel, episode), (channel, UTC slot), (channel, intended context SHA256), and (channel, MP4 SHA256) prevent competing attempts, including separate worker processes using new database connections. A unique remote ID also rejects a duplicate fake reported video ID.
- The first and **only** allowed reservation status is POSSIBLY_SENT_NO_RETRY. For this experiment it is committed before any simulated external step, and reservations are never automatically deleted/reset/retried. A remote ID can be recorded once, after which state becomes REMOTE_ID_REPORTED_UNVERIFIED; **never a real upload, media match, schedule or release.**
- A random mock nonce is returned only in an ephemeral ticket; PostgreSQL stores only a SHA256 of that nonce. No raw nonce or access token appears in audit tables, repr or logs.
- Only disposable role fm_ci_gateway may execute specific fenced reservation and one-ID-report functions. The separate fm_ci_auditor may execute a sanitized inspection function. fm_ci_worker cannot use either writer procedure. None of these roles receive direct SELECT/INSERT/UPDATE/DELETE/TRUNCATE on the private attempt tables.
- SECURITY DEFINER has a fixed trusted search_path (pg_catalog, fm_private_ci, pg_temp), and functions are created with PUBLIC EXECUTE revoked **within the same transaction**. Schema ownership is non-login fm_ci_owner. Every function checks caller session_user where it mutates state.
- The SQL also rejects unknown channel IDs, malformed fingerprints, invalid slot time in Asia/Kolkata and schedules less than 15 minutes in the future relative to the DB server's clock.
- Python autopilot/ci_youtube_attempt_fence.py independently re-derives the exact B4a context digest and rejects any test fixture claiming real OAuth, human consent or production release. It does not import Google APIs or make remote requests. The code is not a production connector.

## Test plan (dedicated GitHub Actions)

- Bootstrap 002 ephemeral PostgreSQL roles and verify existing least-privilege suite; apply 003 only to the isolated named fake DB.
- Real concurrent connections race 24 simulated workers against one exact context; verify exactly one winner. New connections/restarts cannot reserve the same episode or slot.
- Cross-episode collisions at the same slot or reusing identical MP4 fingerprints fail; duplicate remote IDs fail; a forged nonce or tampered/mock release flag cannot amend an attempt.
- Reject wrong IST slot through SQL even if Python preflight were bypassed. Verify missing remote IDs do not free the original fence.
- Verify all three test roles have no direct attempt/audit table privileges; auditor/worker cannot execute reservation functions; auditor cannot be impersonated with gateway credentials.
- Real hosted PostgreSQL job must fail on skipped tests, failed tests or bad role bootstrapping. Existing repository Content Quality Gate must also pass. No tests may exercise live OAuth/YouTube/AWS or turn on publishing.

## Research sources

- PostgreSQL 16 official [CREATE FUNCTION—SECURITY DEFINER](https://www.postgresql.org/docs/16/sql-createfunction.html) and [Privileges](https://www.postgresql.org/docs/16/ddl-priv.html): protected search_path, default PUBLIC function EXECUTE, revocation within one transaction, restricted grants.
- YouTube official [resumable upload recovery](https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol): interrupted session can be queried and resumed under the existing session; an expired/ambiguous session must be reconciled rather than blindly initiating another videos.insert.
- Prior [ADR-0033](0033-b4a-simulated-youtube-private-first-no-retry.md): privacy, precise scheduled publishAt, channel/processing/captions/thumbnail readback and owner trust boundaries.

## Security and production limitations

An ephemeral CI Postgres unique constraint is **not** an authenticated production deployment, replica recovery, a tamper-evident external audit anchor, cross-region distributed owner session, actual owner consent, media/cloud persistence, protected OAuth secret, or exactly-once YouTube semantics. There is no production publisher integration, no network calls, and zero new owner-authorized videos. The test auditor can inspect all synthetic records in this one fake DB; authentic per-channel authorization is still absent.

**Next milestone B4b2:** independently authenticated, owner-authorized cloud identity and private durable PostgreSQL with full disaster recovery/backup policy; real publisher OAuth stored via least-privilege protected vault, guaranteed singleton deployment, per-user channel separation, encrypted resumable session URI persisted before data transfer, recovery on ambiguous HTTP via exact existing session, remote private/processing/captions/thumbnail readbacks, real human approval + release gates. This must be manually authorized and cannot be accomplished by a public PR.

**Branch 2 measured status:** estimated 38% implementation/62% remaining (no points awarded simply for another mock CI contract). 0/21 independently verified real unattended uploads or published channel videos. Branch 1 assisted releases and schedules untouched.
