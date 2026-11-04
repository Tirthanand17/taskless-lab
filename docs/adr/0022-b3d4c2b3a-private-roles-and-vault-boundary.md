# ADR-0022 — B3d4c2b3a: least-privilege cloud database role boundary and vault architecture

**Date:** 2026-11-04 Asia/Kolkata. **Track:** Branch 2, GitHub-only engineering. **Status:** isolated GitHub-hosted PostgreSQL 16 security *contract tests*. NOT a deployed private database, owner entitlement, real AI inference or public media publishing.

## Background and decision

PR #24 proved single-use owner-signed mock inference reservations with a real PostgreSQL service and genuinely independent Python processes. However the test adapter connected as the database owner, who could rewrite or delete past burn rows and mint extra permissions. This is not acceptable for a deployed, laptop-off multi-agent runtime with separate creators, publisher, owner and auditor duties.

**Decision:** verify a separation-of-duties SQL design in an *ephemeral CI service*: the test DB superuser bootstraps a NOLOGIN owner, a non-superuser mock gateway, a non-superuser worker and a non-superuser audit reader. Only fixed-purpose, explicitly granted SECURITY DEFINER procedures can write reservations and close mock receipts. Normal workers and auditors see limited audited state; none of the runtime roles can SELECT, INSERT, UPDATE, DELETE, TRUNCATE or ALTER the underlying ledger tables.

## Current official research

- [PostgreSQL privileges](https://www.postgresql.org/docs/current/ddl-priv.html): ownership is inherently powerful, while grants/revokes protect non-owner roles; beware default PUBLIC function EXECUTE and inherited ownership.
- [PostgreSQL SECURITY DEFINER safety](https://www.postgresql.org/docs/current/sql-createfunction.html): privileged functions need a fixed trusted search_path with pg_temp last; create and REVOKE PUBLIC EXECUTE in a single transaction to avoid broad-access windows.
- [PostgreSQL RLS policy limitations](https://www.postgresql.org/docs/current/ddl-rowsecurity.html): table owners/superusers may bypass row-security rules; RLS alone is not a guarantee that a DBA cannot delete history. Here separate table ownership and no direct table grants are tested instead of claiming an absolutely immutable ledger.
- [AWS Secrets Manager best practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html): example provider controls are least-privilege workload identity, encryption and rotation, audit logs, private networking and restricted decrypt permissions. **No AWS service or cloud resources are provisioned by this PR.** This is a deployment options reference, not a selected provider.
- [AWS Secrets Manager policy review](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_resource-policies.html): block public resource policies and restrict actual principals/endpoint access. A string resembling a secret ARN or key is not proof of a secure vault.
- [Gemini API billing](https://ai.google.dev/gemini-api/docs/billing/): account/project spend caps can lag and experimental caps can overrun; neither an immutable ledger nor signed request counts can independently guarantee zero provider charges.

## Design and trust boundaries

The new migration **autopilot/sql/002_ci_least_privilege_ledger.sql** is explicitly CI-only and only applied to the isolated flowminute_fence_ci service under a test bootstrap admin role:

1. fm_ci_owner is NOLOGIN, NOINHERIT, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOBYPASSRLS; owns its dedicated schema, day ledger, burns and append-audit rows.
2. fm_ci_gateway, fm_ci_worker and fm_ci_auditor have independent LOGIN identities and no ownership role memberships or direct table grants. The bootstrap admin—not a media creator or production agent—allocates *synthetic disposable* CI passwords.
3. The mock gateway's B3d4c2a Python adapter revalidates the exact owner Ed25519 consent signature (test key), external anchor, episode and metadata-only prompt fingerprints before calling one database procedure to burn a lease. The database procedure itself is **not a cryptographic verifier**; a compromised gateway can submit fabricated approved-looking fields. That is why a genuine authenticated owner approval and separately restricted one-writer service will be essential before real inference is permitted.
4. PostgreSQL's burn_mock_once SECURITY DEFINER function validates strict identifier/hex scope, exact model/provider, locks the daily counter, commits the unique lease+episode burn and writes an append event in the same transaction. The close_mock_once procedure requires the ephemeral fence SHA256 and one-shot state transition, logging a second append event. No procedure recycles a burned slot after unknown state. Both restrict function EXECUTE and force search_path to pg_catalog, fm_private_ci, pg_temp.
5. read_mock_state exposes only lease state, episode ID and audit event count to the runtime worker/auditor; no raw table SELECT, token hash, full prompt, provider key or owner secret appears in status results. None of the app logins can DELETE/UPDATE/TRUNCATE the append-audit rows.
6. **A database superuser, table owner, backups operator or compromised security-definer gateway remains able to alter/forge state.** The public CI test cannot prove a tamper-proof, externally anchored, backup-restorable production ledger. A real system needs independent append-only external digest anchoring, DB roles/IAM not shared with creators, audited administrator privileges, backup and restore drills, and cross-job cloud durability checks.

autopilot/ci_protected_pg_boundary.py enforces the isolated test database name, exact login role and absence of broad privileges; its gateway methods return no actual billable model capability, secret or publishing authority. Tests create multiple PostgreSQL connections for real-role privilege enforcement, simulate hostile SQL, test a 22-attempt burn race and verify the read-only auditor cannot erase or change the log. Only synthetic local PostgreSQL credentials and detached Ed25519 fixture keys exist in the hosted job; everything is deleted with the job.

## Approved private cloud / credential architecture (future, not activated)

The following boundaries must be instantiated *only after explicit owner instructions and verified account eligibility*:

- **Credential custodian**: independent vault/KMS backed by owner-approved workload identity, no raw API key in public GitHub repository, PR/test logs, runner environment or laptop; prohibit plaintext secret outputs and ensure rotation/revocation and access monitoring. Choose actual provider/region/data residency/retention in writing, and avoid persistent internet-exposed database credentials.
- **Owner trust authority**: independently enroll the actual owner and claim/rights reviewer signing identities. Keep owner private keys separate from model agents; hold immutable externally anchored consent and provider project/terms version fingerprints. Test fixtures and key fingerprints do not establish real owner identity.
- **Durable DB gateway**: a private managed PostgreSQL or alternative transactional store with roles/ownership separation, protected DB TLS and private ingress, one-use fenced request state, single authoritative writer, externally pinned append-only audit, data retention, tested backup+restore, multi-worker contention and disaster recovery. Do not run the CI schema in production.
- **Provider account control**: actual tier/pricing/usage and data improvement terms must be verified by the owner and provider; a cryptographically valid zero-cost permission does not ensure free billable usage or prevent delayed charges. Make any live adapter default-deny until all private prerequisites, including account-side controls, are complete.
- **Publisher isolation**: the script agent, media renderer and factual reviewers must not hold YouTube OAuth. A separately owner-approved B4 single-writer publisher should rely on immutable final media+rights+fact approvals, private OAuth vault and verified remote upload/caption/thumbnail processing receipts.

## Non-capabilities and next steps

This PR **does not** deploy a live private DB, connect an actual vault, enroll real reviewers, perform Gemini requests, generate genuinely new original video scripts, approve rights/content, run human video watching/listening, or operate YouTube. The prior B3d4c1 narrated videos were synthetic, original test demonstrations and cannot be published on the strength of CI QA.

**B3d4c2b3b next:** owner-reviewed provider/cloud account options, actual cryptographic workload identity, secure secret/vault interface validation, TLS and immutable external ledger/backup restoration design. Implement no live service without explicit owner consent. Continue source-supported content/reviewer readiness work in a parallel unprivileged branch if no provider permission is available.

**B3d4c2c:** 3 distinct genuinely original, real-source-based complete scripts, relevant original calculations/animations, owner-approved live provider account, independent atomic factual and source review, verified creative originality, voice/music/SFX rights, human full playback and signed exact final video/SRT/thumbnail/metadata receipts.

**B4:** protect YouTube OAuth and original media in an authorized private store; one fenced uploader, videos.insert PRIVATE, remote processing and captions/thumbnail readback, verified IST schedule; **B5:** seven days/21 genuine unique independently reviewed releases, 11:00/16:00/20:30 IST, laptop off, no unauthorized charges.

Branch 1 assisted scheduling remains unchanged.
