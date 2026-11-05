# ADR-0038 — Branch 2 B4c2: manual owner Fargate task definition, no actual task/service

**Date:** 2026-11-05 IST. **Status:** Source-only deployable CloudFormation Fargate **task definition** and an inert non-network Python boot guard. NO cloud account connection, billing permission, CloudFormation stack, RunTask, scheduler, ECS service, IAM/secret resource creation, Google OAuth or YouTube upload. Branch 1 assisted scheduling unchanged.

## Motivation

Flowminute Lab Branch 2 aims at **two Shorts and one long video daily at 11:00 / 16:00 / 20:30 Asia/Kolkata** while the owner's laptop is off. Prior accepted work: B4b1 PostgreSQL attempt fence (PR #37), B4b2 no-network resumable session recovery (PR #38), B4b3 real encryption of fake handles in ephemeral PG CI (PR #39), and B4c1 owner-client capable but unconnected read-only STS/SecretsManager/KMS/YouTube channel gate (PR #40). None is deployed in a trusted production runner and none authorizes a real upload.

An ECS Fargate task definition is a real AWS resource type for registering **what a future task would run**. The **registration is not a task launch**. A full working owner private runtime also needs separately owner-created network, IAM, container image, log group and secrets. We create no active ECS task, ECS service, cron/CloudWatch EventBridge scheduler, network, managed database, credentials, media or paid AI calls.

## Source and controls

- Template: infra/aws/owner-readonly-fargate-taskdef.cfn.json. Exactly ONE AWS::ECS::TaskDefinition, no other resources, no defaults for any of seven owner-provided parameters and no stack deployment workflow.
- Valid FARGATE CPU 512 and Memory 1024 MiB; NetworkMode awsvpc; LINUX X86_64 runtime; Fargate-compatible operating system. This small CPU/memory combination is only for a **read-only preflight guard**, NOT for FFmpeg/animated video rendering or uploading.
- The image is constructed with SAME owner account and region ECR registry, owner-provided EcrRepositoryName and SHA256 digest pin. No mutable tag, third-party public ECR image, network package install or generated container source in CloudFormation. The owner must independently produce, sign/scan and verify the **actual** image containing autopilot.b4c2_runtime_boot_guard before deploying. A valid digest syntax alone proves no such image exists or is safe.
- ExecutionRoleArn and TaskRoleArn derive from the actual account ID and existing owner-chosen **distinct** IAM role names. A CloudFormation Rule rejects identical names. No IAM roles, grants, OIDC trust, CloudFormation CAPABILITY_NAMED_IAM, Secrets Manager, KMS grants or policy are created here. Real effective IAM policies must be independently evaluated, especially image-pull/logging vs. user-code read-only access.
- Task has one essential, **non-root UID 65532** container with ReadonlyRootFilesystem, no secret refs, environment files, secret values, exposed ports, volume mounts, privileged options, listener or sidecar. Entrypoint is exactly python -B -m autopilot.b4c2_runtime_boot_guard. All network/publish/owner-release/billable model flags set to OFF in the task definition. An existing owner-created CloudWatch Log Group must already exist; no implicit awslogs-create-group.
- Runtime module autopilot/b4c2_runtime_boot_guard.py parses only safe flag NAMES and constant OFF values; it has no HTTP client, OAuth, IAM or AWS SDK. It prints a sanitized JSON **BLOCKED** status and terminates successfully when inert; refusal returns exit code 70 with a constant error message. It rejects any unexpectedly supplied credential variable name, even a real owner token; never logs its value.
- Strict security lint autopilot/owner_fargate_taskdef_lint.py parses the template rejecting duplicate JSON keys, unexpected parameters/defaults, broader IAM references, moving ECR image to mutable tags, extra ECS resources, security flags, extra containers/secrets/mounts and output claiming publication. Tests cover adversarial mutations and direct guard invocation. Hosted CI includes separate official AWS CloudFormation cfn-lint schema validation. No cloud credential supplied to CI.

## AWS source documentation

- [AWS CloudFormation ECS TaskDefinition](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecs-taskdefinition.html) documents CPU/Memory, roles, awsvpc and Fargate registration.
- [AWS Fargate task networking](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html) requires the owner to select private subnets/security groups when RUNNING a task; a private container does not automatically have Google/YouTube internet egress. Amazon ECR image pulls, CloudWatch logs, Secrets Manager and external YouTube OAuth need separately reviewed routes, IAM permissions and/or VPC endpoints. NAT gateway/public IPv4 are not automatically created or paid for by this template; a NAT gateway can incur recurring cost.
- [AWS Fargate compatible task CPU/memory](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html) validates 512 CPU units with 1024 MiB RAM for a Linux guard. Future actual rendering requires independent memory/storage/cost benchmark.
- [AWS ECS task execution role vs task role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html) explains distinct container-agent image/log operations vs. the application's IAM permissions.

## Why this is NOT an autonomous publisher yet

Even if an AWS owner manually registers this task definition later:
- There is no ECS cluster, service, active task, task scheduler, private VPC, NAT, Fargate placement or protected network to serve real work.
- It can run only an inert boot guard, not a content renderer, LLM workflow, PostgreSQL publisher, authenticated owner channel reader, or actual YouTube videos.insert. No production Docker image has been produced or owner verified. CloudFormation gives no automatic production ID guarantee.
- There is no protected DB, durable lease and resumed-session vault for real sessions, no owner-selected KMS-backed OAuth secret, no least-privilege IAM verification, effective-cost control, CloudTrail, multi-region disaster recovery or release approvals.
- A plain task definition is a *registration*; task launches may incur billable Fargate charges, NAT, CloudWatch logs, ECR or KMS charges. Do not register or run anything until the owner approves exact account/region, cap, tax, network, retention, running cost, image trust and separate real human rights/reviewer obligations.
- This template and all GitHub-hosted CI never use the owner's laptop or connect to AWS or YouTube.

## Next production-critical owner-controlled steps

1. Separately owner-approve provider account, region, budget, security policy, retention and network topology. Verify real IAM role policies, exact ECR digest, signed image provenance and CloudWatch encryption/retention settings in a private environment. Provision only after permission.
2. Build, independently inspect and pin a production container image; perform real network/OAuth read-only B4c1 checks in owner-protected cloud, not a GitHub pull request job.
3. Connect separately encrypted real PostgreSQL + session-key rotation/secret vault and protected singleton publisher to owner-reviewed actual MP4/voice/SRT/thumb provenance. Never copy Google refresh tokens, real upload-session URLs or owner signing secrets to public PRs or code.
4. Add protected, cost-bounded event-driven scheduling for 3 verified owner-reviewed daily releases, private-first YouTube upload and remote processing/channel/rights/thumbnail/caption/scheduled IST readback. Audit real on-channel releases over seven full days (21 expected). No mock CI artifact counts as a release.

**Branch 2 estimated readiness stays 38% implemented / 62% remaining, with zero of 21 independently verified unattended actual YouTube uploads.** This milestone advances source/deployability only. Owner publishing requires separate written authorization.
