# ADR-0057 — B4c5 independently inspect owner ECS IAM roles (NO AWS DEPLOY)

**November 6, 2026 IST — source-only safety gate.** B4c4 has a real GitHub-hosted digest-pinned, nonroot, read-only OCI sandbox smoke test (merged #66). It is emphatically **not** an ECR image, AWS task, automatic uploader or approved billing account. This ADR adds a narrowly scoped read-only IAM policy **inspection contract**, not owner cloud account access.

## Why this exact work now

Before any owner-authorized Fargate task registration or launch, the two existing owner-supplied IAM roles referenced by `infra/aws/owner-readonly-fargate-taskdef.cfn.json` need independent inspection. Task execution role (ECR and logs) must remain distinct from the application task role; an inert boot guard should never be able to read Secrets Manager, a database, KMS or YouTube credentials. Standard ECS execution policies can be broader than this specific boot test requires. An AWS account/region, role names, ECR repo, current log group and owner change reference are **required** inputs; nothing is auto-selected.

`autopilot/owner_inert_iam_preflight.py` takes an injected boto3-compatible **read-only** IAM client; production code has no `boto3.client`, implicit profile search, AssumeRole, IAM mutation, resource creation, AWS deployment, YouTube call or model inference. It checks both `get_role` trust documents for the ECS task service **plus account/region source ARN restrictions**; rejects unexpected paths, role policy attachments, task-role permissions and permission boundaries; enumerates both inline policy sets (rejects paginated/unreadable inventories rather than overlooking hidden grants). Only the execution role may have the single named inline policy `FlowMinuteInertExecutionV1`: ECR login token on `*` (AWS resource restriction unsupported for this action), image pull against a specific owner ECR repository and CloudWatch Logs stream writes under a specific existing owner log group/prefix. Unexpected conditions, `NotAction`, service wildcards, admin, S3, KMS, ECS control, Secrets Manager, Google token access or changed ECR/log ARNs fail closed.

The pure public GitHub Action `flowminute-b4c5-owner-iam-readonly.yml` executes adversarial tests with invented IAM responses only, `contents: read`, no GitHub OIDC token, no AWS credentials and no uploaded artifacts. The Python result always says `release_authorized=false`, `actual_ecs_task_deployed=false` and `youtube_upload_or_schedule_performed=false`. No live identity, actual role policy or verified account is claimed.

## Source and cloud limitations

- Exact policy-document equality is intentionally strict; it is **an example for an owner to provision separately**, not a managed policy being created here. Real AWS SDK must decode the role trust and inline policy documents as dictionaries. Fargate task-role absence of identity grants does **not** prove absence of resource-based grants or controls outside this inspection scope.
- Read-only snapshot does **not** attest the IAM client origin or prevent the owner from changing a role between readback and task launch. IAM conditions, SCPs, permissions boundaries, VPC endpoint policies, CloudTrail, CloudWatch log resource policies, resource-based grants and actual on-task identity need further independently approved checks. Even IAM simulation can differ from real effective permissions.
- The exact `aws:SourceArn` wildcard is intentionally scoped to the owner ECS account and region; per-cluster ECS task trust constraints require validation against AWS documented support. No ECS service/task started.
- Current B4c4 image uses a simple offline boot guard; it should **never be given this execution role's policy as an application task role**. A future actual publisher will require a distinct task identity and a separate rights/billing/OAuth release-gate implementation.
- This feature does not touch the owner's laptop, private Branch 1 videos, existing Nov 6–11 YouTube schedule, AWS billing account, owner secrets, existing cloud permissions, real media or production release. It creates GitHub source and CI only.

## Next stage (blocked by real owner decisions)

B4c6: after the owner selects and authorizes an exact AWS account/region, approved budget, IAM role trust policy, private VPC and media storage, inspect **real** account/network/ECR image digest and independently enrolled owner signature, actual log group and live IAM snapshots without publishing. Then an additional explicit owner-approved, capped and audited private deployment can evaluate the real runtime worker, KMS/Secrets Manager, PostgreSQL fence and YouTube private-first single-writer upload. An inert container cannot publish, and none of this source-only work demonstrates **2 Shorts + 1 long daily**.

**Production capability evidence score remains 40/100 (approximate); independently proven Branch 2 unattended releases remain 0/21.** Do not convert green synthetic tests into live deployment claims.

## Primary documentation

- AWS ECS execution/task role separation: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-iam-role-overview.html
- AWS ECS task trust and SourceAccount/SourceArn: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
- AWS IAM policy simulator limits: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html
- AWS ECS ECR pull/logging: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
