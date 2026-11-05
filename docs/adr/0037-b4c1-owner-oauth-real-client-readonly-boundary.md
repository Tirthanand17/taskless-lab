# ADR-0037 — B4c1 owner-backed OAuth secret and YouTube read-only channel gate

**Date:** 2026-11-05 IST. **Status:** Real-client-capable read-only interface, exercised with synthetic clients in public CI only. NOT connected to any real AWS account, Secrets Manager record, Google OAuth token or YouTube API. No cloud deployment, upload, publishing or cost approval.

## Production problem and purpose

B4b1 (PR #37) proved the durable one-shot intent fence in disposable PostgreSQL 16. B4b2 (#38) modeled same-session resumable upload recovery. B4b3 (#39) encrypted fake session handles under an ephemeral test-only AES-256-GCM key. None proved which real YouTube channel an owner-stored credential authorizes. B4c1 adds the missing owner-bound, **read-only** AWS/Google client verification interface; it does not issue OAuth authorization or enable a video upload.

The new Python verify_owner_youtube_readonly API takes injected owner-authenticated STS, Secrets Manager, KMS clients and a trusted owner-provided Google client factory. It can use actual SDK clients when an owner runs it in their approved private runtime. GitHub CI passes fake in-memory clients; fake outputs cannot attest live owner control.

## Exact read-only sequence

1. STS GetCallerIdentity must return exactly the externally selected account and dedicated assumed role, not root, a writer or another region/account.
2. Secrets Manager DescribeSecret must match the full owner-selected secret ARN, the precise customer KMS key ARN, owner change-reference tags, a publication-disabled tag, absence of deletion and EXACTLY ONE AWSCURRENT secret version.
3. KMS DescribeKey must show an enabled symmetric customer-managed encrypt/decrypt key in the specified AWS account and region. This does not independently verify its entire effective key policy.
4. Secrets Manager GetSecretValue reads ONLY the pinned AWSCURRENT version, checks the returned version ID against DescribeSecret, rejects SecretBinary or mismatched ARN, and holds credential JSON in memory. This is a sensitive READ even though it makes no changes. ONLY execute in an owner-approved private runtime, never public CI. Do not log plaintext.
5. Strict duplicate-key-rejecting JSON verifies client ID, secret, refresh token, official token URL and exactly three narrowly chosen declared scopes: youtube.readonly, youtube.upload and youtube.force-ssl. Actual token scopes, grant validity and app verification are NOT independently proven from stored JSON. A trusted Google SDK factory must authenticate/refresh the same in-memory credential.
6. Only YouTube channels.list(part=id, mine=true, maxResults=50) is requested. It must return exactly one authenticated owned channel that matches the independently selected ID with no pagination. Any mismatch or API error fails closed. Provider exceptions are sanitized so fake secret material cannot appear in returned errors or normal output. Neither videos.insert nor captions upload/update nor schedule is available.

The resulting status object explicitly says real owner consent not cryptographically checked, signed AWS and Google credentials not independently verified by the module, production vault/database not deployed, actual YouTube upload not executed, release_authorized=false. A fake Google client may forge an owned channel ID, so this is structural CI evidence only until owner supplied real clients are used and independently audited.

## Least-privilege AWS example (NOT deployed)

infra/aws/owner-youtube-readonly-role-policy.example.json is only a JSON example with mandatory owner-fill placeholders for exact account, region, full secret ARN and KMS key. It grants secretsmanager:DescribeSecret and GetSecretValue for ONE secret; kms:DescribeKey directly for the exact key; kms:Decrypt for that key only through Secrets Manager service in that account. It grants no Put/Create/Delete/List/Update actions, no wildcard Resource, no IAM/OIDC trust, no cross-account permission or video publishing privilege. STS GetCallerIdentity requires no IAM grant.

Do not reuse the separate existing private S3-only KMS key in infra/aws/owner-approved-private-media-escrow.cfn.json for OAuth: that key is restricted to S3 service encryption. The existing S3 template is owner-deployable source but has not been deployed by this work. B4c1 does not create any new AWS service, Secrets Manager object, rotating key, protected runtime, CloudTrail, OAuth consent or billing.

## Up-to-date official references

- [YouTube API OAuth authentication and refresh tokens](https://developers.google.com/youtube/data/guides/authentication): OAuth refresh tokens must be protected and grants can be revoked.
- [YouTube channels.list](https://developers.google.com/youtube/v3/docs/channels/list): requires OAuth for mine=true, allows part=id; a read-only channel query.
- [YouTube videos.insert](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert): separate authorization and private-first production upload obligations.
- [AWS Secrets Manager encryption and KMS conditions](https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html): the GetSecretValue read needs KMS decrypt under an owner key and ViaService restrictions.
- [AWS DescribeSecret reference](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_DescribeSecret.html): metadata and secret version stages, not plaintext.
- [Secrets Manager IAM action reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_secretsmanager.html): resource-scoped DescribeSecret/GetSecretValue.

## CI and external owner prerequisites

- Python adversarial tests inject synthetic AWS and Google clients and verify principal/channel mismatches, wrong KMS/secret, duplicate AWSCURRENT versions, retired version, deleted secret, unexpected JSON/clients/scopes, wrong channel, ambiguous pagination, secret-bearing errors and absence of publishing. Public GitHub Actions installs no AWS/Google SDK, uses no user OAuth or AWS accounts, and has no tokens/secrets.
- Before genuine use, the real owner must separately choose AWS account ID, region, budget, provider billing, IAM/key policy, VPC/private runner, retention and security audit; create an encrypted OAuth Secret OUTSIDE GitHub; authorize Google OAuth scopes and verify exact channel/account; set independent fact/rights/media approvals and billing controls.
- Production Google client factory must use TLS and securely handle refresh/revocation without logging a token. The injected clients, resource tags and owner reference labels do not independently attest who approved them. A proper private identity chain and verified production implementation remain future work.
- No production cloud launch, OAuth token, credential, session URL or approval should ever be put in a public PR, workflow, chat, test artifact or laptop.

Branch 1 existing assisted releases and scheduling are untouched. Branch 2 estimated ~38% implemented/62% remaining; **0 of 21 independently verified autonomous real YouTube releases**. Passing synthetic read-only tests does not count as live publication.
