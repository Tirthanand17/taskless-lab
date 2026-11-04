# ADR-0023 — B3d4c2b3b vault policy requirements and actually exercised recovery integrity

**Date:** 2026-11-04 Asia/Kolkata. **Track:** GitHub-only Branch 2 automation. **Decision:** implement cryptographic and least-privilege **preflight requirements** plus a real disposable PostgreSQL export/restore test. **Not** owner-approved cloud provisioning, a live secrets manager, durable DB, real paid-model access, authentic copyright review or YouTube publishing.

## Prior milestones and gap

PR #25 B3d4c2b3a verified distinct PostgreSQL gateway/worker/auditor logins and dedicated SECURITY DEFINER test procedures against actual ephemeral PostgreSQL 16. The CI owner can still modify the database, and a true private cloud vault and independently pinned backup/audit roots do not exist. A content-authoring agent must not be able to read the protected YouTube OAuth token, AI provider API key or owner signature. An on-disk DB dump is not useful unless a separate restore demonstrably reconstructs the expected ledger state.

## Current official reference research

- [AWS Secrets Manager best practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html): least-privilege identity/resource policies, rotation, KMS, avoid logging credentials, private endpoints and audit. A digest of an IAM policy is NOT proof the policy exists or restricts access.
- [Google Cloud Secret Manager access control](https://docs.cloud.google.com/secret-manager/docs/access-control): permissions should be granted at the individual secret when possible, not broadly at project/folder level; separation of purpose and a well-scoped identity are necessary.
- [Google Cloud Secret Manager best practices](https://docs.cloud.google.com/secret-manager/docs/best-practices): separate applications and environments, minimal rights and private network considerations.
- [PostgreSQL 16 pg_verifybackup documentation](https://www.postgresql.org/docs/16/app-pgverifybackup.html): physical base backup checksum verification cannot prove the DB actually recovers and still requires a test restore. **This PR uses pg_dump/pg_restore for a logical CI mock recovery**, not physical pg_basebackup/pg_verifybackup or production disaster recovery.
- [PostgreSQL 16 pg_dump/pg_restore reference](https://www.postgresql.org/docs/16/app-pgdump.html), [pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html): logical custom-format dumps can be replayed into a separate database. Verify row and audit-level fidelity after restore, not only the exit status.
- [GitHub Actions ephemeral service containers](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers): these are recreated per CI job and do not furnish a permanent shared cloud database, backup system, secret vault or tenant credentials.
- [Gemini API billing](https://ai.google.dev/gemini-api/docs/billing/): project spend caps may lag; an app-level zero-paid-request counter plus unverified free-tier attestation cannot guarantee no charges. Owner consent/account settings remain external prerequisites.

## Engineering decision

### 1. No-secret typed vault contract

autopilot/private_cloud_recovery_preflight.py accepts a typed, bounded PrivateCloudRequirements record for *either* AWS Secrets Manager or Google Cloud Secret Manager. It requires exactly three purpose-specific independent workload identity digests and logical handle paths: inference_gateway/gemini_draft_api_credential, ledger_gateway/postgres_mock_gateway_credential, and youtube_publisher/youtube_oauth_refresh_credential.

There must be no shared principal, broad read/write operation, loose/wildcard secret, mismatched cloud backend or region, missing resource/encryption/private-endpoint policy digest, missing access audit, missing workload identity, oversized session TTL or abandoned rotation interval. The proposed private DB requires TLS 1.3, a NOLOGIN owner, non-superuser runtime roles, separate backup reader, independent external audit anchor and bounded recovery point/time *targets*. These are desired design properties, **not actually observed cloud states**: a caller can invent hashes or requirements. The checker therefore always reports cloud_secret_actually_exists=false, cloud_iam_permissions_independently_verified=false, owner_provider_account_and_terms_approved=false, live_generative_inference_enabled=false, youtube_upload_enabled=false.

The publicly displayed logical handles begin with flowminute://vault/, not actual ARNs, Google resource versions or real credentials. The function deliberately does not fetch or return any secret bytes; there is no vault SDK, network call, IAM credential or decryption capability. Reviewer keys should be enrolled by a real independently authenticated human owner, not by an authoring model.

### 2. Signed external audit/backup integrity *test contract*

The module checks a bounded set of typed synthetic audit events, unique mock lease and episode burns, at-most-once close, contiguous ordering, and a SHA256 hash chain. It creates a canonical manifest binding exact backup bytes, ordered audit head, backup generation and previous manifest root. Later generations must carry forward the exact earlier sequence, preventing silent rewriting of already-recorded events when the previous root is known.

Verification requires the external pinned manifest SHA256, an Ed25519 signature domain-separated to this recovery protocol, an independently provided public key, and the expected generation/event count. A modified byte, missing/changed event, forged signature, untrusted signer, rollback, replay, no parent and wrong generation are denied. In public CI all signer keys, externally pinned hashes and original source data are **synthetic values generated by the test itself**; a verifiable signature proves cryptographic consistency only, not a real independent immutable external trust root or real-world owner identity. No production backup store or legally certified reviewer ledger is connected.

### 3. Actual disposable PostgreSQL dump/restore exercise

autopilot/ci_postgres_backup_restore_drill.py runs ONLY on the CI-named PostgreSQL service with Gemini/YouTube disabled. It uses the prior PR #25 role bootstrapping and gateway to burn three synthetic signed daily lease IDs, close one mock, and store four append-audit events. It invokes actual pg_dump custom archive of the fm_private_ci schema, computes and verifies an external *test signer* Ed25519 manifest over its actual raw archive, then deliberately alters one byte and requires a rejection.

The test creates an **independent second database inside the same disposable PostgreSQL 16 service** and runs pg_restore there, with --no-owner/--no-acl. Restored burn, day and audit rows are re-queried, independently canonicalized and compared to the source with every event's timestamp/lease identity intact. This demonstrates a concrete *logical restore drill*, not private-cloud durability, a multi-region failover, WORM retention, physical WAL recovery or tested RPO/RTO. Restored SECURITY DEFINER functions are not executed; --no-owner deliberately changes ownership to CI admin, so this is NOT a production role-safe restore procedure. Actual future private-cloud restoration must reapply owner/role grants under independent security verification before a service can use the restored DB.

The archive and signer key never leave the temporary CI job; no artifact upload is performed. GitHub Actions service containers are torn down after completion.

### 4. CI / visibility

- autopilot/private_cloud_recovery_preflight.py: provider-neutral requirements and signed synthetic backup/audit chain.
- autopilot/test_private_cloud_recovery_preflight.py: strict no-network negative cases for overbroad/shared-purpose access, changed policy scope, rollback/tampering, missing backup history, external signer key and signature mismatch.
- autopilot/ci_postgres_backup_restore_drill.py: real disposable PostgreSQL logical export→independent restore plus row and signed dump hash verification.
- .github/workflows/flowminute-b3d4c2b3b-vault-recovery.yml: unprivileged read-only PR with crypto-only checks and an actual Postgres 16 service job. No private secrets, Cloud SDK actions, YouTube OAuth, paid service, local laptop or persistent DB.
- docs/runbooks/branch2-private-cloud-owner-activation.md: external owner/account decision checklist.

Merge only when all GitHub-hosted CI checks (including repo quality, scout, old media smoke, new vault preflight and actual restore) pass. Unverified content and unapproved YouTube release are never unlocked by technical backup tests.

## Remaining real owner decision and production checklist

**B3d4c2b3c:** select an owner-approved real provider account/region, verify provider privacy and training/data-use terms and current zero-cost/charge policy; provision a private managed durable DB plus vault only after specific authorized budget approval, with secret-level IAM, KMS/VPC/TLS, rotation, immutable external backup audit roots and separate owner/reviewer enrollment. Test real cloud service identity plus restoration into another hardened tenant with reinstalled safe roles, authenticated cross-job/day persistence, backup snapshots, monitored usage, restore objectives and explicit compliance. No CI test identity can authorize this.

**B3d4c2c:** actual authorized generative model with three materially distinct complete fact/rights-reviewed original scripts for 2 Shorts + 1 long, source-linked examples, truly topic-specific animations, rights-cleared voice/music/SFX, captions, full human playback and independent signed final MP4/SRT/thumbnail/metadata checks. The B3d4c1 fixed synthetic CSV example suite is a technical renderer demonstration, not autonomous original daily content.

**B4:** owner-approved private YouTube OAuth vault and fenced uploader; upload PRIVATE, verify remote processing and captions/thumbnail then schedule exact future 11:00, 16:00 and 20:30 IST slots. **B5:** 7-day, 21-original-video laptop-off end-to-end published proof.

Branch 1 assisted scheduling stays separate and unchanged. No user laptop storage, paid provider or real YouTube action performed for this ADR.
