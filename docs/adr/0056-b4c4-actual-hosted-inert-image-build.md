# ADR-0056 — B4c4 actual inert OCI container built and booted on GitHub Actions (no AWS deploy)

**Date:** November 6, 2026 IST. **Status at creation:** GitHub source workflow proposed. Do not claim a container actually executed until the Actions **job succeeds** and a post-merge run returns the output. No ECR push, ECS RunTask, CloudFormation deploy, managed database, provider model, protected OAuth or YouTube action in this milestone.

## From B4c2 task definition to an actual source-matched runnable image

Prior B4c2 created an inert source-only Fargate task definition that requires a pinned digest of a nonroot `autopilot.b4c2_runtime_boot_guard` image but had never built the image. B4c3 (merged GitHub PR #65) added independent read-only owner VPC + image source-authentication tests; the image's existence on ECR and real owner signing are **not verified**.

B4c4 moves beyond pure fake object tests by actually building an OCI image with the exact inert boot-guard source on an ephemeral **GitHub-hosted Docker runner**, then running that image in a highly restricted container. The owner's laptop and branch 1 YouTube schedule are not touched.

## Media and cloud safety boundaries

- **`infra/aws/B4C4.inert.Dockerfile`** declares `ARG BASE_IMAGE; FROM <owner/runner-supplied registry SHA256 digest>` without a mutable default. The hosted workflow first `docker pull`s the official public Python 3.11 slim bookworm base, reads its resolved **registry digest**, verifies the digest form, and then builds from the digest-pinned image reference. It records that exact base digest as ephemeral build provenance.
- The image copies **only the existing inert Python boot guard** into `/app/autopilot`. No installer, third-party network calls, SSH, Google API client, OAuth, media or private files are built into the image. Nonroot `USER 65532:65532`, Python `-B`, and nine explicit blocked publish/model/network/spend settings are pinned in image defaults.
- The workflow actually runs Docker using `--network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges --user=65532:65532 --pids-limit=64` and resource limits. It validates a genuine JSON execution result proving `release_authorized=false`, no network client permitted, no provider call, no actual media/output or publisher side effects.
- A second **real** container run overrides `FLOWMINUTE_ENABLE_PUBLISH=1` and must exit with code 70 and ONLY `B4C2_INERT_BOOT_GUARD_REFUSED`. Any claim of publishing competence from an inert image is a security test failure.
- A metadata-only GitHub artifact (7 days, public source context) contains source and Dockerfile SHA256, the actual ephemeral base registry digest, the new image **configuration digest** from the Docker builder, the actual GitHub checkout SHA, explicit Docker sandbox flags and **`owner_signed_attestation=false; ecr_image_pushed=false; aws_cloud_task_launched=false; youtube_upload_performed=false`**. The **local image config digest is NOT an ECR distribution manifest digest** and cannot be substituted as a future private ECR image address without actual push+independent readback.
- This workflow grants `contents: read` only, contains no public PR OIDC token request, no cloud secret, no YouTube OAuth and no scheduler. Image and runner scratch data are destroyed after the source-only test; only safe metadata is retained on GitHub Actions. GitHub-hosted compute and artifact use may count against plan quotas.

## B4c3 source-attestation alignment

The existing B4c3 owner image-signature contract now points to the real B4c4 **build workflow path**, not to the B4c2 CloudFormation linter. This is a source path anchor, **not an assertion that any actual ECR image has been externally owner signed**. A future protected owner build and ECR push must bind the **actual pushed ECR manifest digest**, exact source commit, account, Region and repository to a separately out-of-band enrolled owner Ed25519 key, plus completed ECR findings. The ephemeral synthetic test key and metadata artifact here cannot satisfy that production gate.

## What this advances and what it does not

A passed B4c4 job proves an actual laptop-off original inert boot image can be built and its entrypoint run under tight local Docker sandbox flags. It does **not** prove:
- functioning AWS private VPC, available IAM roles, private ECR registry or remote Fargate task launch;
- fully automated research, licensed media, independently enrolled human editorial review or cost-safe model inference;
- persistent cloud object/media vault, PostgreSQL upload lease or Google OAuth secret custody;
- any new automated YouTube upload or one week of independent scheduled publishing.

Maintain Branch 2's last externally evidenced baseline of **40/100 approximate production capability and 0/21 unattended releases** until real third-party production proof warrants a revised score. Branch 1's already repaired scheduled videos remain a separate, assisted workflow.

Next: B4c5 protected immutable OCI image promotion/signing into an explicitly **owner-approved account**, verified network/run-time IAM, private media + PG, real source/rights review, and a guarded private-first cloud YouTube publishing worker. Do not deploy or incur charges without owner account selection and spend approval.
