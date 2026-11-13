# CLIVOX A8 — real GitHub SHA-conditional update proof (sandbox only)

**Verified 2026-11-13** with the authenticated owner's connected GitHub tool against the **actual separate private Clivox control repository**. No local files, laptop media or third-party content were used.

## Confirmed real remote API behavior

1. Created a **separate private non-main sandbox branch** from the private metadata repository's main.
2. Created an isolated `clivox-private/sandbox/cas-probe-v1.json` file containing only a fixed CLIVOX channel ID, `test_only: true`, `production_ledger: false`, `youtube_upload_authorized: false` and a tiny monotonically numbered test value.
3. Authenticated the first update with the current file blob SHA; GitHub accepted the update and returned a new blob SHA.
4. Submitted a **second, stale SHA** update for the **same test-only path**, intentionally referring to the old blob SHA. GitHub returned **HTTP 409 Conflict**, and rejected it.
5. Fetched the file again: the first accepted test value was still present, and the rejected stale value was not present.
6. Canonicalized only this private **sandbox** JSON file for strict future API readback. The real private `clivox-private/upload-control/attempt-ledger-v1.json` on production `main` was never modified by this proof.

This verifies one actual **sequential stale-SHA rejection**. It is **not** proof of globally linearizable concurrent updates across runners, ABA/repository rollback resistance, complete journal retention, or production failure recovery. GitHub's [Contents API](https://docs.github.com/en/rest/repos/contents) requires a prior blob `sha` for an update and documents `409 Conflict` and `422 Validation failed` as possible responses. Concurrent writes and branch updates require independent live fault/race testing.

## New hardened optional sandbox-only writer

- `scripts/branch3_a8_cas_sandbox_writer.py` implements an **owner/main/first-attempt/manual** optional live GitHub transport that can GET private repo metadata, owner-only collaborators, and the exact one sandbox JSON file, perform **one** SHA-conditional PUT to that **non-main** file, and GET the same file again to compare readback. No other path/branch is accepted by the code.
- `.github/workflows/branch3-clivox-a8-cas-sandbox-verify.yml` is owner-manual and uses the new **real** `clivox-cas-sandbox` environment; it was created with owner required reviewer, `main` deployment policy, admin bypass disabled and **zero secrets**, all verified live through GitHub. The **workflow has not been executed with live secrets** and is blocked by default.
- `scripts/test_branch3_a8_cas_sandbox_writer.py` and the no-secret workflow `.github/workflows/branch3-clivox-a8-cas-sandbox-qa.yml` cover fake successful write/readback, stale pinned floor, 409 conflict, ambiguous/timeout response, forged file contents, public repo, bad ACL, untrusted commit confirmation, rollback-like readback, denied mutations to production paths and disabled YouTube flags.

## Optional owner configuration — do not share secrets in chat

The owner must independently review GitHub App installation access, private repo main/sandbox isolation, current sandbox file and all scopes. Configure these environment secrets only in `clivox-cas-sandbox`, not public code:

| Secret | Meaning |
|---|---|
| `CLIVOX_A8_CAS_SANDBOX_PRIVATE_REPO_NAME` | The owner's exact selected CLIVOX private metadata repository name |
| `CLIVOX_A8_CAS_SANDBOX_CONTENTS_WRITE_TOKEN` | Fine-grained single-repository **Contents: write** token owned by an admin/role that can also read the collaborators list. No Google, workflow, Actions, issues or admin scope |
| `CLIVOX_A8_CAS_SANDBOX_WRITE_APPROVED` | `approved-clivox-a8-cas-sandbox-no-youtube-v1` |
| `CLIVOX_A8_CAS_SANDBOX_EXPECTED_SERIAL` | The current **actual sandbox JSON** `write_serial` read from the private branch (currently 1 immediately after the original proof; future runs change it) |
| `CLIVOX_A8_CAS_SANDBOX_EXPECTED_BLOB_SHA` | The latest GitHub blob SHA of the exact **sandbox** file, pinned externally by the owner; changes on each accepted update |

After approval, dispatch the job **on controller `main`** as the owner. No retry after a 409 or ambiguous response. Human must inspect fresh private readback and update pinned sandbox checkpoint before a fresh authorized attempt. Reused old pins fail before PUT.

**No secrets currently installed**, and this demonstration does not modify the production upload ledger. Never grant this sandbox workflow access to footage, owner signing keys, YouTube OAuth or real creator rights documents.

## What still blocks actual production

This code cannot reserve any real video for upload: its hardcoded fixed-path allowlist denies `clivox-private/upload-control/attempt-ledger-v1.json`, production `main`, title, video bytes and Google endpoints. A separate owner-audited production uploader needs genuine rights approval (or fully first-party licensed original content), a reviewed/signed exact final asset, durable rollback-resistant cross-run reservation, tested real crash+concurrency recovery, Clivox-only owner Google OAuth and private-first inventory matching. **No automatic retry, upload or scheduling is enabled.**

**Progress is engineering planning only.** A9 real pilot remains 0%, videos uploaded by this project remain zero, and Branches 1/2 are paused.
