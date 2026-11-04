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
