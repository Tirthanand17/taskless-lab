# ADR-0059 — B4c7 protected MANUAL owner-cloud read-only audit entry point

**November 6, 2026 IST. No AWS account, owner role, GitHub environment reviewers, secret, ECR repository or deployment is connected/created by this PR.**

## The material missing bridge after B4c6

B4c6 (#68) combined IAM, signed ECR image, VPC and template checks using *injected* fake clients, but provided no restricted way to conduct an actual owner AWS account readback. B4c7 adds a **manual-only, protected GitHub-hosted OIDC workflow** and a bounded, redacted Python adapter around the same B4c6 checks. This can perform an actual **read-only** account inspection ONLY AFTER the owner externally configures and authorizes the exact AWS IAM role, GitHub environment, reviewed signing public key and scope.

The code is **not an automated video agent, uploader, scheduler, Fargate deployment or billing approval**. Branch 1's November 6–11 YouTube schedule is not modified. A source merge does not cause the live audit to run.

## The manual workflow and synthetic CI are separate trust boundaries

- `.github/workflows/flowminute-b4c7-owner-live-readonly.yml` has **only** `workflow_dispatch`. It is gated to repository `Tirthanand17/taskless-lab`, default `main`, actor `Tirthanand17`, and an environment called `flowminute-owner-cloud-readonly`. **The owner must independently configure that environment's required reviewers and branch restrictions** before any real secrets or OIDC trust exist. The YAML naming an environment does NOT prove reviewer protection is active.
- The manual workflow checks exact schema, source/repository/ref/actor/region/change-reference and signed-data byte lengths **before** requesting OIDC credentials, and passes the secret scope in environment variables only to the validation steps, never as a GitHub artifact or generated file. A textual `OWNER-...` reference is **not cryptographic owner consent**.
- Only the separately reviewed owner AWS role can be assumed, using `aws-actions/configure-aws-credentials@v6.3.0` with ephemeral OIDC, `mask-aws-account-id: true`, a 900-second STS session, explicit `allowed-account-ids`, and a named read-only session. No access keys are stored as GitHub secrets. The specific IAM OIDC trust policy must constrain `aud`, exact repository **and environment subject**, and required permission scope. The OIDC `sub` format can differ by repository age and provider configuration; inspect actual GitHub issuer claims and pin them accurately rather than copying a guessed trust string. The role must never permit mutation, `iam:PassRole`, `sts:AssumeRole` to other roles, secrets, model endpoints, video services, or broad wildcard admin rights.
- `autopilot/owner_live_aws_readonly_audit.py` requires temporary AWS credentials and the complete protected input schema; creates only four AWS SDK clients `sts`, `iam`, `ec2`, `ecr`, each exposed to B4c6 through an explicit **read-method allowlist**. It never calls Create/Update/Put/Delete/RunTask/CloudFormation, Secrets Manager, KMS, Google or YouTube.
- All provider errors are converted to a constant refusal marker, without provider exception chaining. The successful console report contains **no account ID, role ARN, VPC ID, image digest, signature, exact source hash, token, private video ID, media title or secret fingerprint**. It explicitly marks `release_authorized=false`, `actual_fargate_task_launched=false` and `youtube_oauth_or_publish_performed=false`. It does not retain artifacts or channel metadata.
- `.github/workflows/flowminute-b4c7-owner-live-readonly-ci.yml` is completely **unprivileged**. It uses only invented fake STS/IAM/EC2/ECR objects and ephemeral synthetic Ed25519 keys. `contents: read` only, no OIDC token, no cloud credential and no external AWS service. It also checks that the protected workflow has no auto triggers, and that the PR workflow can never acquire OIDC or secrets.

## Owner-side prerequisites — NOT satisfied by this code

Before even an owner-authorized read-only live test, an actual human operator must:

1. **Select the exact authorized AWS account, Region, private network, two private subnets, task and endpoint security groups, immutable ECR image digest and an independently enrolled Ed25519 signer public key.** The B4c4 GitHub-only **local image configuration digest cannot be reused as a pushed ECR manifest digest**. The image must actually exist in approved private ECR with completed scan. No fake fixture is owner evidence.
2. In GitHub, create protected environment `flowminute-owner-cloud-readonly` with required approval reviewers and main-only deployment restrictions. Confirm repository workflow edit permissions, prevent untrusted code from reaching that environment, and isolate OAuth/media permissions. Verify the real GitHub OIDC `aud` and `sub` claims for this environment against a narrow AWS role trust policy; never authorize wildcards or all repos.
3. Add a GitHub **environment variable** `FLOWMINUTE_B4C7_AWS_REGION` and the following **environment secrets** (not repository variables or public file contents):

| Secret | Required value |
| --- | --- |
| `FLOWMINUTE_B4C7_AWS_ACCOUNT_ID` | Exact 12-digit owner AWS account expected by the OIDC action |
| `FLOWMINUTE_B4C7_AUDITOR_ROLE_ARN` | Exact least-privilege OIDC role ARN in that account |
| `FLOWMINUTE_B4C7_SCOPE_JSON` | Strict JSON schema `flowminute-b4c7-protected-owner-audit-scope-v1`; owner values below |
| `FLOWMINUTE_B4C7_SIGNED_IMAGE_B64` | Base64 of independently owner-signed, exact ECR image provenance JSON (not synthetic) |
| `FLOWMINUTE_B4C7_IMAGE_SIGNATURE_B64` | Detached Ed25519 signature base64 |
| `FLOWMINUTE_B4C7_SIGNER_PUBKEY_B64` | Separately enrolled trusted public key (not private signing material) |
| `FLOWMINUTE_B4C7_SIGNER_FINGERPRINT` | Out-of-band pinned SHA256 fingerprint of enrolled 32-byte public key |

The scope JSON requires exactly: `schema`, `aws_account_id`, `aws_region`, `inspector_role_name`, `execution_role_name`, `task_role_name`, `ecr_repository_name`, `existing_log_group_name`, `owner_change_reference`, `vpc_id`, `subnet_ids` (exactly two), `task_security_group_id`, `endpoint_security_group_id`, `image_digest`, `source_commit_sha`. **Do not copy live values into GitHub PRs, issues, public artifacts or chat.** Only approved reviewers should configure the environment secrets.

4. Independently review CloudWatch and billing/cost exposure, role policy/identity restrictions, S3/log resource policies, ECS effective task permissions, image registry signature (not merely the provenance JSON), and the limitations of strict isolated private routing. A metadata readback cannot establish effective permissions or zero charges.
5. After separately authorizing the read-only audit, manually choose the main-branch workflow and supply the **nonsecret** `owner_change_reference` matching the secret scope. Review redacted result and inspect actual AWS control-plane evidence in the owner's approved protected environment. The public synthetic CI result is never equivalent.

**Do not run this workflow until steps 1–5 are explicitly handled.** It will fail closed without required environment secrets/role; it does not self-provision or self-authorize.

## Decisions still blocking unattended YouTube publishing

An isolated private endpoint-only inert ECS task **cannot access Google's YouTube APIs** and cannot render videos. The real production architecture needs a separate cost-approved external-egress worker, actual licensed fresh daily video generation (2 Shorts + 1 long), human/rightful fact and media review, private media escrow, protected PostgreSQL writer fence, production OAuth, private-first resumable upload/reconciliation, future publishAt timezone/date safety and 21 independently verified laptop-off publications over seven days.

Current score remains **~40/100 production-readiness estimate; 0/21 actual independent YouTube releases** until genuinely authenticated external proof, not green tests, is available.

## Documentation reviewed

- GitHub OIDC in AWS: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
- Official AWS action v6.x OIDC and account masking: https://github.com/aws-actions/configure-aws-credentials
- AWS STS get_caller_identity limitations: https://docs.aws.amazon.com/boto3/latest/reference/services/sts/client/get_caller_identity.html
- AWS task IAM roles: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
