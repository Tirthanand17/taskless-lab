# CLIVOX A2 — Private GitHub revocation journal SHA-CAS protocol

**Implementation date:** 2026-11-13. **Status:** an executable, adversarially tested OFFLINE protocol, **not** a deployed revocation service, authentic creator license or media-release authorization. No private repository, live writer, durable owner-held anchor or signer has been provisioned.

## What changed

The previous A2 code verifies signed **per-receipt** checkpoint chains using synthetic signatures. A future operational system needs one global append-only revocation journal whose entries cannot be silently overwritten by two overlapping workers. This implementation adds:

- A bounded (250 entries, 220 KB) **global CLIVOX receipt-revocation journal**, chained from a fixed genesis digest; every event is separately Ed25519-signed with a distinct revocation domain. It contains only opaque case/receipt IDs, digest, reason code, timestamp and cryptographic signature, not raw contracts, names, OAuth data or footage.
- Deterministic strict JSON, content hashing, sequence checks, duplicate-receipt prevention, forged signature and future-date rejection, and cross-channel isolation. Once a signed revocation appears, no code in this module can remove or 'unrevoke' it.
- Strict GitHub Contents API file readback decoding. The response must be a regular JSON file at **`clivox-private/rights/revocation-journal-v1.json`**, have correct size/encoding and match Git blob SHA-1 bytes exactly.
- A **GitHub Contents REST update request contract** that includes the exact existing blob SHA (optimistic concurrency): a stale blob SHA or conflicting update is rejected by the simulated CAS test. GitHub API requires an existing `sha` when updating files. The current code generates only the payload; it never sends a network PUT.
- An independently supplied previous journal-head/sequence pin. A substituted old history fails if the caller has a genuinely newer head. In tests, this anchor is **not independent or durable**: it is merely caller-provided state, so a successful test does NOT prove the absence of unreported revocations.

Official GitHub REST references: <https://docs.github.com/en/rest/repos/contents> for the file GET, Base64 encoding and update PUT requiring the existing blob SHA; <https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments> for protecting any later secret-bearing main-only workflow.

## Code and CI

- `scripts/branch3_a2_private_ledger_cas.py` — strict journal validators, pure signer verification and append, GitHub GET blob checks, SHA-CAS request generation, deterministic simulated conflict test. **CLI only permits `--mode fixture`, no live transport.**
- `scripts/test_branch3_a2_private_ledger_cas.py` — synthetic ephemeral Ed25519 test keys, signed two-event history, stale concurrent write, missing tombstone rollback pin, altered hash/record, wrong key, mismatched repository owner/visibility, GitHub file corruption and deny-policy attacks.
- `branch3/rights_review/private-ledger-policy.json` — all real owner, storage, credential, external ledger and YouTube permissions remain disabled. A simple config-field edit cannot turn live I/O on.
- `.github/workflows/branch3-clivox-a2-private-ledger-cas.yml` — zero secrets, zero private Google/GitHub API calls, zero artifacts; runs A2 and A3 offline security tests.

## Follow-up: read-only remote bridge (code, not connected)

The [owner-reviewed live journal readback bridge](OWNER_LIVE_JOURNAL_READBACK.md) now implements only fixed-host authenticated GitHub GETs (owner metadata, collaborators and exact journal contents) in a protected manual/main workflow. It does not perform the Contents PUT modeled in this document, does not provision a vault or credentials, and does not prove real creator rights or the independent durability of supplied anchor material.

## Next necessary owner-controlled work — not implied by this PR

1. Obtain real commercial YouTube clipping permissions from the actual copyright holders, including relevant publisher, guest and embedded music rights. Until then `creator_permissions.json` stays empty.
2. Select and approve a **confidential** owner-controlled private repo and an appropriate retention/security policy. Existing A3's authenticated private-repo readback is a preliminary privacy check, not sufficient access or contract storage approval.
3. Independently enroll owner-vetted revocation signer keys and establish protected key rotation. Do not use test keys or copy tokens from the FlowMinute channel.
4. Bootstrap the first journal file in the approved **private** repository via a separately audited owner-controlled process; create a protected GitHub Actions environment and a fine-grained repository-scoped Contents write credential only with actual approval. No live writer exists now.
5. Create a **separately stored, nonrollbackable external head/sequence checkpoint** with authenticated updates. An owner editable Git branch, public PR artifact or a JSON `trusted_floor` supplied by the writer does not prove this. Implement reliable external readback and freshness checks. Failure to read the current anchor must block all actions.
6. Only then code and independently review a guarded `GET → verify → append signed event → PUT with prior blob SHA → confirm readback → update external pin` live sequence. Treat 409 conflicts and unknown results as **halt-and-reconcile**, not blind retry. A GitHub Contents file alone does not guarantee immutable storage or legal rights.
7. Integrate authentic rights revalidation at source acquisition, final rendering, owner-approved private-first upload and scheduled publication. Separate A6 owner video signature and A7/A8 CLIVOX OAuth are mandatory.

**Actual state:** zero verified grants, zero authorized media, no owner-vetted private journal, no live API writes, zero uploaded CLIVOX videos; A9 remains 0%. Branches 1/2 stay paused.
