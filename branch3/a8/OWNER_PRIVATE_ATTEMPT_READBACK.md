# CLIVOX A8 — owner-only private upload attempt journal live READ-ONLY

**Code implemented 2026-11-13.** The separate CLIVOX private GitHub control-metadata repository **really exists** and its canonical `clivox-private/upload-control/attempt-ledger-v1.json` genesis file was authenticated through the connected GitHub repo tool. Its recorded sequence was **0** and there were **0 upload-attempt events**. This milestone does **not** create the remote upload writer or approve any video upload.

## What is built

- `scripts/branch3_a8_live_attempt_readonly.py`: owner/main/manual-only runtime using **three fixed-host HTTPS GETs to api.github.com**. Queries exact private repository metadata, the owner-only collaborator list and `clivox-private/upload-control/attempt-ledger-v1.json?ref=main`. Rejects repository visibility/owner errors, other collaborators, ACL pagination, wrong path, unexpected contents mode, noncanonical file, byte-size or Git-blob SHA mismatch, event-chain/hash corruption and rollback against the owner-supplied prior head and sequence.
- `.github/workflows/branch3-clivox-a8-live-attempt-readonly.yml`: manually dispatched owner-only on public controller `main`, first attempt only, under the **already existing** `clivox-vault-readonly` environment. That environment was previously verified to require an owner reviewer and main-only branch, with admin bypass disabled. **It had zero secrets at the latest owner check.** This workflow does not upload artifacts or run for pull requests.
- `scripts/test_branch3_a8_live_attempt_readonly.py`, plus `.github/workflows/branch3-clivox-a8-live-attempt-qa.yml`: offline adversarial readback tests and no-secret PR CI; no protected token or real Google requests.

## Minimum owner setup — no credentials stored in this public repo

Before a real read, in GitHub **Settings → Environments → clivox-vault-readonly**, configure only independently audited credentials and the owner-specific opt-in sentinel:

| Protected environment secret | Value to supply securely |
|---|---|
| `CLIVOX_A8_APPROVED_PRIVATE_VAULT_NAME` | The exact owner-approved private CLIVOX control repo **name**, not full owner/name or a public repository |
| `CLIVOX_A8_PRIVATE_CONTENTS_READ_TOKEN` | Owner-controlled, repository-selected fine-grained token with **Contents: read** and **Metadata: read**; no repo write privileges. The authenticated user/app must also have sufficient repository role privilege to **list collaborators** |
| `CLIVOX_A8_ATTEMPT_LEDGER_READ_APPROVED` | The exact opt-in string `approved-clivox-a8-attempt-readonly-v1` |
| `CLIVOX_A8_OWNER_PINNED_ATTEMPT_SEQ` | Independently retained **trusted previous** global attempt sequence (at bootstrap 0, but must be maintained monotonically) |
| `CLIVOX_A8_OWNER_PINNED_ATTEMPT_SHA256` | Independently retained **trusted previous** event-chain head (at bootstrap the genuine A8 genesis digest, but the owner must independently verify its origin) |

**Important permission nuance:** GitHub documents `GET /repos/{owner}/{repo}/collaborators` as requiring the authenticated owner/maintainer with write/maintain/admin repository privileges; the fine-grained token permission is **Metadata: read**. `GET /repos/{owner}/{repo}/contents/{path}` requires **Contents: read**. A dedicated owner-held token selected for the single private repo with only these read permissions is the intended minimum; a token owned by a collaborator without sufficient underlying role will still fail. See [GitHub collaborators docs](https://docs.github.com/en/rest/collaborators/collaborators) and [repository contents docs](https://docs.github.com/en/rest/repos/contents).

To run: in public controller **Actions**, dispatch **Clivox A8 Owner-Reviewed Private Upload Attempt Ledger READ-ONLY** on **main** as the exact owner. Approve the existing protected environment. A missing opt-in, token, durable prior anchor or incorrect audience/owner context always stops before the GitHub requests. Missing permissions stop closed; they do not cause any fallback or retry.

## What a passing live job actually proves

- The authorized GitHub API returned a private owner-only collaborator repository snapshot and a real upload-attempt ledger file at a single requested moment.
- Its canonical bytes, Git object SHA and bounded SHA-256 event journal match the supplied prior head and sequence checkpoint; exact CLIVOX identity and duplicate attempt/release/media guards replay correctly.
- It returns **only sanitized counts** and safety booleans. No private repo slug, collaborator, journal content, event/media/video hash, token or raw error is printed.
- **There are zero GitHub remote writes, zero YouTube API requests, zero automatic retries and no production upload permission.**

This is **NOT** a transactional GitHub compare-and-swap writer; the journal can change after the read. The owner-supplied anchor may be stale, malicious, replaced or not truly durable. Its matching math does not independently establish secure immutable external storage. A true multi-runner atomic write/rollback-resistant controller remains separately unprovisioned. GitHub App installations/backups are not exhaustively audited by collaborator-list GET. A read-only ledger is not licensing, proof of an authentic signing key, evidence of actual human video approval, an authenticated Clivox Google inventory snapshot or upload permission.

**Required before A9:** real final-asset human QA, genuine owner exact-video signing, authenticated rights for any external footage/audio, owner-approved private storage policy, separate Clivox OAuth, a durable monotonic single-writer upload reservation system, trusted remote video ID matching, explicit owner review and private-first upload.

**Current reality:** owner-private metadata repository exists; code and synthetic QA exist; **zero protected A8 token secrets, zero execution of this live A8 workflow, zero YouTube video uploads, zero approved creator clips**. Branches 1 and 2 remain paused.
