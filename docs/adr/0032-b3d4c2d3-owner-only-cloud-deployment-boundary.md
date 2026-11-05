# ADR-0032 — Owner-only AWS private media infrastructure and read-only activation verification

**Date:** 2026-11-04 IST. **Track:** FlowMinute Lab Branch 2. **Decision:** commit an independently reviewable owner-only AWS S3/KMS CloudFormation stack and read-only external storage topology verifier. **Deployment status: NOT DEPLOYED.** No real AWS credentials, project IAM, paid providers, budget, owner identity enrollment, actual cloud media, human rights approval or YouTube action.

## Why this is the next real engineering dependency

PR #31 rendered and fully decoded three full original educational NASA/NIST/USGS narrated H264/AAC drafts with 70 spoken captions, 160 distinct animated frames, and 213 exact producer media files. All were deleted after GitHub-hosted rendering. PR #32 connected 210 literal narration/scene/SVG/thumbnail/proposed metadata text surfaces to 14 curated claims and six direct NASA/NIST/USGS primary HTTPS source pages. PRs #33–#34 used actual boto3 calls against GitHub-hosted localhost Moto S3 to stage and independently re-read 213 deliberately NONPLAYABLE synthetic media objects and three versioned manifests, plus 21 mathematically valid transient MOCK editor signatures; none constitutes actual cloud storage or human approval.

The remaining obstacle cannot be resolved by further mock Ed25519 keys. Production requires an owner-selected provider account, region, real storage/IAM/KMS and billing permission, independently enrolled real human reviewers and an immutable audit ledger. This milestone provides a concrete deployment template and separate read-only policy/topology gate without creating those resources.

## Official AWS sources and critical caveats

- [CloudFormation S3 Bucket](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-s3-bucket.html) permits versioning, Object Lock, four public-access block controls, ownership and SSE-KMS encryption; the bucket and key are configured with DeletionPolicy and UpdateReplacePolicy Retain, so removing the CloudFormation stack does NOT automatically remove billable evidence storage and keys.
- [ObjectLockConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-s3-bucket-objectlockconfiguration.html) documents default retention Rule with Mode COMPLIANCE and a Days period. Object Lock protects specific object VERSIONS and active COMPLIANCE retention cannot be arbitrarily shortened. The owner must explicitly choose a 1–30-day legal retention duration; this template has no default retention parameter or deployment job.
- [S3 SSE-KMS bucket encryption](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-s3-bucket-serversideencryptionrule.html) supports customer KMS key ARN and BucketKeyEnabled. Use the complete key ARN, not a cross-account alias.
- [AWS KMS key policy](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html) describes retaining owning account principal access to prevent irrecoverable loss. The owner must still audit the EFFECTIVE IAM/key policies, SCP and root/admin privileges and grant only S3-scoped crypto permissions to runtime roles.
- [S3 conditional write](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html) can be defeated by later current delete markers in a versioned bucket; it is NOT global one-use. Preserve externally anchored durable Postgres leases and exact VersionId records.
- [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) does not establish copyright rights or legal review, and Object Lock retention may continue costing money after CloudFormation rollback or deletion.

## Deployable TEMPLATE, never deployed

Path: infra/aws/owner-approved-private-media-escrow.cfn.json

All inputs have NO defaults: owner-selected globally unique suffix, exact existing IAM writer role NAME, different independent auditor role NAME, explicit compliance retention days 1–30, and owner-supplied out-of-band change-ticket reference. A syntactically valid ticket does NOT authenticate owner identity or consent. The role ARNs are derived from actual CloudFormation AWS AccountId at deployment, not from arbitrary cross-account principal parameters. Separate writer/auditor names are required; no IAM roles, OIDC trusts, credentials, keys for reviewers, Lambdas, GitHub Actions schedulers or publishers are created automatically.

Resources are a single customer-managed rotating KMS key, a versioned owner-private bucket with COMPLIANCE default retention, default SSE-KMS, BucketOwnerEnforced, four public block controls and Retain, and a restricted BucketPolicy. The policy explicitly denies insecure transport, non-KMS upload encryption header, a different KMS key and non-COMPLIANCE object uploads on the unapproved media prefix. Scoped writer can PUT and read back exact retained versions; separate reviewer can ONLY read object versions/retention plus nine bucket configuration GET APIs needed for the independent preflight (versioning, region, Object Lock, public access, encryption, ownership, policy status, bucket policy and tags), not PUT, delete, LIST or bypass retention. Both runtime roles are explicitly denied bucket/object deletion, bypass and tampering with versioning or Object Lock. The KMS key policy allows account administration, writer only S3-scoped GenerateDataKey/Encrypt/Decrypt/DescribeKey, and auditor S3-scoped Decrypt, plus a SEPARATE same-account read-only DescribeKey/GetKeyPolicy/GetKeyRotationStatus grant without kms:ViaService for direct inspector calls. No broad S3 public allow, identity publisher permissions or YouTube secrets are present.

**Template deployment is not implemented in a public PR.** Do not allow ordinary pull_request or pull_request_target events to assume any production cloud role. CloudTrail S3 data events, IAM principal identity policies, externally anchored backup/restore, real security budget monitoring, an owner-controlled secure admin deployment and private work orchestration are STILL MISSING.

## READ-ONLY preflight contract

Path: autopilot/owner_cloud_activation_preflight.py

A future separately owner-authorized protected runtime can inject three already authenticated AWS clients (STS, S3, KMS) and an independently selected exact account/region/bucket roles/KMS/ticket/retention. The verifier constructs NO clients, credentials, signers or outbound call by itself and makes ONLY get/describe operations:

1. STS GetCallerIdentity must report the correct same-account assumed AUDITOR role, not root, writer or model agent.
2. The actual bucket region, Enabled versioning and COMPLIANCE default retention must match the owner-declared days.
3. All four S3 public-block flags and BucketOwnerEnforced ownership must match, and GetBucketPolicyStatus must say not public.
4. Default S3 encryption must be SSE-KMS with the exact expected owner customer key ARN and S3 bucket key enabled.
5. Bucket resource policy must contain exactly the expected eight constrained Statements, including a separate auditor-only exact nine-action read-only bucket-configuration statement; no extra grant, public allow, missing TLS deny, broader object prefix, auditor write or account deletion/bypass rights.
6. Customer KMS key must be enabled, rotating, owned by exact account, symmetric encrypt/decrypt. KMS key policy must match four expected statements (owning account admin, S3-only writer crypto, S3-only read-auditor decrypt).
7. Bucket tag OwnerApprovalReference must match the selected ticket format, which is **not** a genuine signature or billing approval.

The output ALWAYS states real owner/identity issuance, full human fact/rights/disclosure/voice review, cross-region backup, media persistence, and publishing/release FALSE. A caller-supplied mocked client can forge these responses; further real signed credential-chain/provider/account readback and owner-controlled evidence anchoring must occur outside the public CI before production status can be asserted.

## Test scope and failure handling

- autopilot/test_owner_cloud_activation_preflight.py: parses exact template, resolves standard CloudFormation intrinsic values offline, tests non-default owner parameters, same-account role generation, key rotation and IAM separation; supplies only IN-MEMORY fake STS/S3/KMS responses. Negative cases reject cross-account roles, wrong identity, insecure policy/public access, removed compliance lock, shortened retention, missing versioning, wrong KMS/key rotation, duplicate/extra policy grants, reviewer PUT/delete/bypass, incorrect KMS root or key permissions, bad owner ticket and any service failure. Does not establish actual AWS controls.
- .github/workflows/flowminute-b3d4c2d3-owner-storage-preflight.yml: two no-secret read-only GitHub-hosted jobs. One runs adversarial local template/API shape tests, another installs CloudFormation cfn-lint and validates resource schema OFFLINE. Both have contents:read only, no id-token write, AWS role, signing keys, external cloud calls, model billing or YouTube publisher. Existing workflow regressions also run under GitHub path filters.

## Hard owner activation requirements

Before provisioning any bucket, KMS key, retention, backup, cloud database or API account, separately obtain explicit owner consent for exact account, region, provider and monthly request/storage/KMS costs, possible overruns, legally approved unshortenable COMPLIANCE retention, data residency/privacy, cloud audit, source/media/voice model license and copyright use, independent real reviewer enrollment and genuine channel owner authorization. Owner must confirm separate least-privilege IAM roles, CloudTrail logging, backend PostgreSQL/publisher fence, private key vault, protected GitHub branch/environment and signed out-of-band owner identity. Manual owner-operated deployment and independent real AWS readback are still required; this pull request CANNOT deploy.

**NEXT B3d4c2d4:** actual protected multi-account or owner-approved source/media audit anchor, real owner/reviewer enrollment and immutable commitments over the ACTUAL approved final MP4/WAV/SRT/thumb/title/description source bytes. Then separately authorized B4 YouTube OAuth private one-writer uploads and remote processing/thumbnail/caption/scheduled IST readback; B5 seven days of 21 genuinely approved laptop-off releases.

**Progress estimate: 38% technically implemented, 62% remaining; real independently verified autonomous YouTube releases 0/21.** Branch 1 assisted schedule not touched. An infrastructure template, even schema-valid, is NOT a cloud deployment or real approval.
