# ADR-0058 — B4c6 compositional owner inert cloud preflight (NO AWS)

**Date:** November 6, 2026 IST. **Status:** source-only synthetic GitHub testing. No AWS owner credentials, private cloud account, billable resources, ECR upload, ECS task launch, YouTube OAuth or release.

## Why compose these checks

B4c2 created a manual *inert* Fargate task-definition source, B4c3 tested private VPC routing and signed ECR provenance with fake client data, B4c4 built and executed one real no-network container on a GitHub-hosted runner, and B4c5 read back a synthetic least-privilege IAM role pair and repaired the Content Quality Gate (`main` merge #67). None of those is a real owner cloud deployment. Independent modules, if called with subtly different accounts or image repositories, can individually return green while the overall operator configuration remains incoherent.

B4c6 adds **a single fail-closed coordinator**, `autopilot/owner_inert_composite_preflight.py`, that validates all scopes and rejects mismatches BEFORE touching any injected read-only service. Only the following *existing* B4 checks are composed:
- Exact unchanged inert CloudFormation task source, using strict duplicate-key and no-publisher lint.
- An owner-supplied STS assumed-role readback constrained to the pinned account and independent inspection role (not the ECS execution or task role). A fake injected STS client remains possible.
- B4c5 zero-permission inert ECS task role and small exact inline ECR/log execution role, including ECS-only trust and complete policy enumeration.
- B4c3 two-AZ RFC1918 private network, endpoint, subnet, route and security-group readback, plus separate owner-key-fingerprint pinned Ed25519 ECR image metadata and completed scan.

The coordinator must receive a single `InertOwnerCompositeScope`, four already-authenticated read-only clients (`sts`, `iam`, `ec2`, `ecr`), an exact manual task template, a signer-controlled binary JSON attestation, signature, separately enrolled signer public key and fingerprint, and a timezone-aware inspection clock. It rejects conflicting account IDs, AWS Regions or ECR repositories. It does **not** fetch or assume credentials itself, mutate IAM, provision a task, download OAuth secrets, generate an AWS signing key, incur charges or upload content.

**Order of refusal:** scope + static template before service calls; injected STS role before IAM; IAM before private network; network before signed image/ECR. All known and unknown external failures are sanitized without exception chains, to avoid accidentally echoing secrets or provider-specific private metadata.

## No expansion of production trust

A returned `status` is an *injected-client structural result*, not proof the clients came from the correct AWS owner account, the encrypted image was actually deployed or reproducibly built, cloud credentials were protected, IAM resource policies/SCPs/endpoint policies grant only intended access, or the user approved billing. It intentionally emits **no account IDs, role names, private VPC addresses, source text, image hashes, public/private keys or OAuth material**, and always sets `release_authorized=false`, `real_ecs_task_launched=false`, `youtube_video_uploaded_or_scheduled=false`.

A VPC with no NAT/public egress can reach only the approved AWS endpoints, so this inert topology **cannot reach Google/YouTube**; never promote it to a video publisher. A production rendering/scheduling worker needs a *different*, owner-approved architecture, explicit safe egress, costs, durable private media/PG state, IAM, OAuth and auditable human source/media/rights reviews.

`autopilot/test_owner_inert_composite_preflight.py` runs fake STS/IAM/EC2/ECR responses and temporary synthetic Ed25519 signatures, tests spoofing/drift, overprivilege, route/signer/scan failures, and confirms no service reads before a failed earlier gate. Dedicated GitHub CI has contents-read only, no OIDC, no paid AI provider, no secrets or AWS clients. The existing standalone gates remain independently tested. A green PR does not warrant increased production capability: **approximately 40/100, and Branch 2 independent seven-day YouTube releases remain 0/21** until owner-authenticated real services are verified.

## Owner-only blockers for real use

1. Explicit owner selection and approval of AWS account ID, Region, max financial exposure/budget alerts, retention policy, audit roles, primary media store and separate reviewer identities.
2. Actual manually configured two-AZ private VPC endpoints, role trust, immutable ECR signed image and verified scan. Owner must inspect real injected SDK calls from a protected environment, plus independent effective-IAM/cloud evidence; never run on untrusted PR or on owner laptop.
3. Private durable PostgreSQL and encrypted media/session store, fact/rights/audio/video approval receipt, real Google production OAuth, a separate egress-controlled upload worker and remote channel/processing readbacks.
4. An explicitly authorized dry-run-to-private pilot with unknown results treated as unresolved, then 21 independently verified, distinct, laptop-off scheduled releases. **None of that is implemented by B4c6.**

## Existing authoritative references

- AWS ECS roles and source account trust: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
- AWS ECR VPC endpoints including S3 layer access: https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html
- AWS IAM effective permissions are broader than identity policy snapshots: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html
