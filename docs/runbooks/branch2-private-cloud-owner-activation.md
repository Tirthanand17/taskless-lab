# FlowMinute Branch 2 — private-cloud owner activation checklist (no activation performed)

**Prepared:** 2026-11-04. **Status:** design and security acceptance checklist ONLY. All development through GitHub, no user laptop or private credentials. Branch 1 assisted publishing remains separate.

## Owner decisions and external evidence required

Before any provider call or cloud provisioning is attempted, the owner must separately choose and approve:
- Exact AI provider and model, project/account, account classification (free/paid), explicit charges allowed or prohibited, real monthly/daily budgets in the account currency and what to do when provider billing caps are delayed.
- Exact sources/data classes allowed to leave private custody and provider data-improvement/training policy; record current terms, version/date, retention and any sensitive data restrictions. Do not send unpublished private scripts without specific approval.
- Cloud provider and region, data residency/retention periods, expected recurring cloud cost and account-level cost controls (prefer no-cost footprint until owner approves spending).
- Actual owner identity/key enrollment and independent fact/rights/creative reviewer identities; out-of-band public-key authority and revocation plan. Automated agents cannot self-certify as owners, truth reviewers, or copyright holders.
- Protected provider API key and later YouTube OAuth token custody, IAM/workload federation, secret access monitoring, key rotation, invalidation and recovery; never expose tokens in public repo, CI or laptop.
- Managed private database, role and network policy, backup retention, restore recovery targets, external immutable audit anchoring and operator separation. A GitHub Actions postgres container is not a durable service.

## Preflight acceptance for a production adapter

A future owner-authorized deployment must:
1. Verify real billing/entitlement terms independently of local counters; confirm current provider-side project charge constraints and owner approval of any residual overage risk.
2. Demonstrate independent authenticated workload identities for owner verifier, sole inference gateway, database writer, worker, source reviewer, rights auditor and YouTube publisher. Do not share a DB owner/superuser with a renderer, public PR runner or editor agent.
3. Prove a fenced one-shot request across **different authenticated cloud jobs or machines**, plus outage/restart and recovery, not only concurrent connections to disposable hosted CI Postgres.
4. Ensure physical private persistent storage and encrypted transport, real cloud secret-vault access policies with narrow resource scopes, separate admin/runtime/auditor database grants, protected backups and restore test.
5. Require a tamper-evident ledger receipt independently anchored outside the mutable DB, tied to the exact owner-approved source context, output, provider billable token usage and subsequent source/rights/final media adjudication.
6. Before any video upload, independently validate factual claims across title, thumbnail, every narration sentence/visual, rights and licensed voice/music, originality, platform synthetic-content disclosure decision, full watch/listen by real reviewer, encoded AV QA and final MP4/SRT/thumbnail/metadata SHA fingerprints. Renderer technical QA alone cannot attest editorial truth.
7. Separately approve a YouTube OAuth-capable private publisher. First upload as private with status.privacyStatus=private, verify remote ID/channel/processing/captions/thumbnail, then create future publishAt for 11:00 / 16:00 / 20:30 IST only after final approval. No duplicate requests after ambiguous upload responses.

## GitHub engineering scope while approvals are absent

Allowed now: source URL metadata capture, fake provider responses, synthetic Ed25519 keys in CI only, original educational executed demonstrations on invented rows, disposable hosted render tests, SQLite/Postgres concurrency and database role-security tests, docs/architecture and negative safety tests. No private secrets or real paid/YouTube calls.

Forbidden until owner activation: selecting a paid cloud tenant on behalf of the owner, provisioning real persistent databases/vaults, storing actual project keys, publishing on YouTube through the autonomous branch, or treating cryptographic mock receipts as factual/legal consent.

## Release proof required after activation

The seven-day independent workflow requires 21 substantively different independently approved uploads, evidence for each 11:00 / 16:00 / 20:30 IST slot, provider cost/usage receipts and cryptographic immutable media provenance, with the laptop shut off. Reuse the existing human-assisted Branch 1 track only for previously authorized assisted uploads and schedules.


## B3d4c2b3c1: protect production GitHub OIDC from public PRs (not activated)

The next owner-approved deployment must independently establish the **real** protected GitHub environment's branch rules, repository/owner immutable numeric identifiers, the owner-approved workflow path, cloud account/project and account-side billing/data terms. Only a designated approved deployment workflow on refs/heads/main may request a short-lived identity. Never give `id-token: write` to an ordinary public pull_request or pull_request_target workflow.

For AWS, verify the live IAM trust resource's exact OIDC issuer, audience, account and repository/environment subject, and independently audit the GitHub protected environment's branch restrictions because environment-subject alone does not bind the main branch. For GCP, verify the live WIF provider's stable repository/owner ID mappings and exact branch/workflow/event/environment attribute conditions, service account scopes, short-lived tokens and prevention of long-lived key creation. No arbitrary ambient PR claims or regex matching on repo display names should qualify.

Require separate narrowly scoped secret-level service identities for inference API credentials, database gateway and YouTube publisher, each limited to its own specific secret and a separately audited access policy. For PostgreSQL use libpq sslmode=verify-full, live hostname certificate check, current trusted CA and least-privilege runtime role; do not accept an encrypted connection as proof of the expected server.

**Proof still needed:** actual independently retrieved IAM readbacks, real signed JWT issuer/audience/expiry checks, owner-confirmed protected environment branch policy, real vault audit entries, account cost protections, actual Postgres verify-full TLS handshake and durable cross-job ledger. The offline B3d4c2b3c1 policy samples are no-credential design tests only, not deployment permission. Continue independent editorial/content approval engineering while external approvals are absent.


## B3d4c2d1: S3 object-escrow acceptance (local Moto only; not active)

A new S3 API adapter now exists in autopilot/private_versioned_media_escrow.py. It prepares exact original 43/127/43 media assets based on original source-docket SHA, uses conditional create, full SHA256, customer SSE-KMS selection, Object Lock COMPLIANCE per version, no retry and actual version-ID GET readback, and writes a final unapproved manifest last. Existing public GitHub Actions can exercise **only invented fake bytes against local Moto on 127.0.0.1**; an injected client for real AWS has not been supplied or authorized.

The owner must separately authorize actual account, bucket, region, exact KMS key, per-version compliance retention duration (which may be unshortenable and incur ongoing fees), storage/request/KMS budgets and privacy, data residency, source license, protected IAM/OIDC and identity permissions, CloudTrail/audit, source/model voice licensing, review enrollment, and independent S3 bucket configuration readback before any live upload. Set the botocore client to total_max_attempts=1 to prevent automatic uncertain PUT retries, monitor 412/409 and delete-marker semantics, pin every real VersionId and retain a separately anchored append-only commit ledger and backup/restore. Never run any S3 writes from an untrusted public PR with owner credentials. No workflow in this PR provisions or mutates a cloud bucket or calls YouTube.

Even an actual stored immutable version is not factual, rights, owner, AI-disclosure or human playback approval. Do not connect this staging receipt to a publisher until separate externally authenticated real humans and channel owner explicitly approve exact final media assets. Branch 1 remains unchanged; seven-day real unattended publication is not proven.


## B3d4c2d2: separate REAL human reviewer enrollment from synthetic S3 receipt signatures

The new version_pinned_review_boundary module independently re-fetches ALL exact original video/voice/SRT/thumbnail/scene object VersionIds and the unapproved final manifest from a S3-compatible interface before computing one complete review SHA. Synthetic Ed25519 review receipts must each bind that same source/visible-claims root and all object versions. No source SHA or client-supplied upload success report is accepted without exact remote bytes/readback.

**This is still a test mechanism.** Only fake seven-role reviewers sign with transient test keys in GitHub CI; no real reviewer, rightsholder or channel owner is enrolled. 21 valid fake signatures across three episodes do not mean human signoff or 21 videos published. Any real future deployment must authenticate the persons independently, independently own and revoke registry trust roots, prevent publisher/model/editor impersonation, prove actual source facts and metadata semantics, ensure legal voice/music/image rights, validate originality against the actual YouTube channel, document human complete playback and synthetic content disclosure, and obtain the real channel owner's separately authorized release intent. Hold all publication flags FALSE until then.

The readback-only reviewer needs separate least-privilege S3 s3:GetObjectVersion, HeadObject/GetObjectRetention and KMS decryption rights, but must NOT be granted S3 delete, retention bypass or PutObject rights. Confirm actual AWS IAM/KMS policies and exact S3 VersionId trust, external ledger anchor, private vault, backup and real billing prior to deployment. Public GitHub pull requests may use only local Moto, fake source media, transient fake Ed25519 keys and read-only repository checkout; no real cloud or YouTube credentials.
