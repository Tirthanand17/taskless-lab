# FlowMinute Branch 2 — CircleCI migration (NO DEPLOY, NO PUBLISH)

**Date:** 2026-11-04 IST. **State:** Configuration committed in .circleci/config.yml. The CircleCI project has NOT been connected and an actual CircleCI run has NOT been observed.

## Reason

GitHub Actions has had 13 jobs queued on PR #35 without runner assignment. The underlying cause, including whether GitHub Actions usage limits were exhausted, is NOT confirmed. To continue without the owner's laptop, this repository now includes a cloud-hosted CircleCI configuration suitable for execution after the owner connects GitHub to CircleCI. Switching CI does not automatically confer permissions for actual AWS deployment or YouTube publishing.

Official guidance:
- [Connect GitHub and set up a CircleCI project](https://circleci.com/docs/guides/getting-started/create-project/)
- [Configure GitHub App triggers](https://circleci.com/docs/guides/orchestrate/set-up-triggers/)
- [Trigger a CircleCI pipeline manually](https://circleci.com/docs/guides/orchestrate/triggers-overview/)
- [CircleCI configuration reference](https://circleci.com/docs/reference/configuration-reference/)
- [CircleCI credit limits and costs](https://circleci.com/docs/guides/plans-pricing/credits/)

## One-time owner CircleCI setup (web only, not laptop terminal)

1. Open https://app.circleci.com/ and sign in. In Org -> VCS Connections, authorize/install the CircleCI GitHub App for ONLY Tirthanand17/taskless-lab, subject to available selective repository permissions. A GitHub repository administrator may need to approve this connection.
2. Under Projects, create/follow the taskless-lab project. Set configuration source repository Tirthanand17/taskless-lab and path .circleci/config.yml, with an appropriate GitHub App push or PR trigger. Avoid duplicate OAuth/App triggers.
3. For PR #35, manually trigger the pipeline with configuration and checkout branch feature/flowminute-b3d4c2d3-owner-activation-storage-template. The default boolean parameter full_media_regression=false keeps the expensive full three-video Kokoro rendering OFF. Do not connect production AWS, YouTube, Gemini or other secrets/context to untrusted PR jobs.
4. On CircleCI Pipelines, inspect the actual five default job results, source checkout SHA, and logs. Record the real pipeline URL/results in PR #35. Only a SUCCESS conclusion from CircleCI qualifies as a real pass.
5. When compute quota/credits permit, manually trigger another run with full_media_regression=true only if full original narrated video regression is needed, such as after media code changes. The output remains transient technical drafts, never autonomous YouTube uploads.

## Default cloud-hosted CI jobs

- owner_cloud_stack_security — AWS CloudFormation official cfn-lint and 100% offline fake STS/S3/KMS owner configuration negative tests. Does NOT create any AWS stack.
- repository_quality — Full Python pytest Content Quality Gate and editorial-only episode JSON validation, with FFmpeg; no YouTube publishing.
- source_and_review_contracts — Primary NASA/NIST/USGS source and 210-surfaces claim/visual/thumbnail review tests; 7-role synthetic signature tests; public HTTPS readback. Does NOT imply independent human fact-check or rights.
- local_moto_versioned_s3 — Real boto3 HTTP to localhost-only Moto service: 213 NONPLAYABLE fake files, 3 fake manifests, 21 synthetic reviewer receipts. No real AWS.
- postgres_recovery — Separate PostgreSQL 16 service container, actual pg_dump/pg_restore and isolated least-privilege fake DB roles. No real cloud database.

Optional workflow explicit_opt_in_expensive_media runs an original 2 Shorts + 1 Long Kokoro/FFmpeg three-video test only when the pipeline boolean full_media_regression is explicitly true. Public model and voice hashes are pinned; no external paid model, actual upload or retained media.

## Safety and merge gate

CircleCI setup via a GitHub commit alone does not start tests. This chat does not have a CircleCI account connection or CircleCI token, so it CANNOT claim or trigger a real CircleCI pipeline until the owner connects the app. All publishing and real human rights/owner/cloud flags remain false.

Require five real CircleCI default jobs green against the exact PR #35 head, and run the optional media regression when a new renderer change warrants it. Correct actual linter/test failures in the PR. Do not silently bypass tests or merge unvalidated infrastructure changes. After a successful actual CircleCI run, consider disabling redundant GitHub Actions PR triggers to avoid double CI spending, but never change account billing/plan limits without owner consent.

Branch 1 is unaffected. Branch 2 remains approximately **38% implemented / 62% remaining** and **0/21 real independently verified autonomous YouTube uploads**.
