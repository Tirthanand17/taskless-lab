# CLIVOX A2/A3 — Owner-only private journal GitHub READBACK

**Code implemented:** 2026-11-13. **Private metadata bootstrap now exists:** the owner created a separate private CLIVOX GitHub repository with an **empty** global revocation journal; authenticated repo owner/collaborator metadata was independently read through GitHub CLI. The protected `clivox-vault-readonly` environment also exists and is owner-reviewed, main-only, admin-no-bypass with **0 secrets**. **No dedicated token, owner-enrolled signer or actual three-GET workflow readback exists** and no licensed video is authorized.

The public CLIVOX controller repository now contains an optional fixed-host owner-reviewed **read-only** verifier. It requires the separate `clivox-vault-readonly` GitHub Actions environment (now actually provisioned and protection settings independently verified), and refuses calls unless all selected secrets and the manual/main/owner execution context match. In live mode it performs exactly three GETs on `api.github.com` for the same owner-approved private repository:

1. `GET /repos/Tirthanand17/<private-clivox-vault>`: exact owner/identity, true private visibility, not archived/disabled/forked.
2. `GET /repos/Tirthanand17/<private-clivox-vault>/collaborators?affiliation=all&per_page=100&page=1`: only the expected owner with admin permissions; pagination is rejected.
3. `GET /repos/Tirthanand17/<private-clivox-vault>/contents/clivox-private/rights/revocation-journal-v1.json?ref=main`: strict regular JSON file, exact path, size, decoded bytes and Git blob SHA. Then verify every signed journal tombstone, exact Clivox identity and an owner-provided prior journal anchor.

**It never follows HTTP redirects, performs a GitHub PUT, obtains source videos, grants creator rights, or calls YouTube.** No artifacts or private identifiers/tokens are logged.

## Required owner setup (not automated)

1. Review legitimate commercial creator reuse rights and all underlying publisher/guest/music restrictions independently. Never treat the existence of a private journal as rights permission.
2. Choose a suitable confidential owner-controlled storage provider, and decide whether a private GitHub repo is acceptable for contract and revocation metadata. If so, **personally create/approve** a separate private personal repo named `clivox-...`, and manage retention, collaborators, GitHub Apps and access separately. Do **not** change the public `taskless-lab` repository visibility.
3. Set up a genuine signed global journal file on its default `main` branch at the fixed `clivox-private/rights/revocation-journal-v1.json` path. The current offline global-journal code is only a format/verification preview and is **not** a production writer, key authority or lifecycle system.
4. Independently enroll the **genuine revocation-signing public key** and maintain an external, durable **nonrollbackable** ledger anchor. A copied GitHub file, mutable repository secret, unverified environment variable or test key does **not** establish key identity or anchor durability.
5. In `Tirthanand17/taskless-lab` → Settings → Environments, create `clivox-vault-readonly` with owner-required reviewer, **main branch only**, and disable admin bypass. Inspect live protection settings before using the job. This is distinct from the existing `clivox-readonly` YouTube environment. A workflow naming a protected environment does not create approval rules. This environment is **not yet verified**, and zero secrets are configured here by this PR.
6. Create a **fine-grained read-only GitHub token scoped exclusively to the chosen private repo** with **Contents: read** and Metadata: read. Check that it can inspect collaborators. The token must not permit Contents write, Releases write, Administration, other repositories or YouTube access.
7. Put these **six environment secrets only** into `clivox-vault-readonly` (never source files, chat or public Actions artifacts):
   - `CLIVOX_A2_APPROVED_PRIVATE_VAULT_NAME` — just the approved `clivox-...` slug.
   - `CLIVOX_A2_PRIVATE_CONTENTS_READ_TOKEN` — dedicated private repo read-only token, not the workflow's `GITHUB_TOKEN`.
   - `CLIVOX_A2_JOURNAL_READ_APPROVED` — exact non-sensitive sentinel `approved-clivox-journal-readonly-v1`.
   - `CLIVOX_A2_PINNED_REVOCATION_PUBKEY_HEX` — owner-reviewed Ed25519 32-byte public key encoded as 64 lowercase hex characters.
   - `CLIVOX_A2_OWNER_PINNED_ANCHOR_SEQ` — owner-recorded prior chain sequence in decimal.
   - `CLIVOX_A2_OWNER_PINNED_ANCHOR_SHA256` — owner-recorded prior journal head SHA-256, 64 lowercase hex.
8. After reviewing the merged code and environment protections, manually dispatch **Clivox A2 Owner-Reviewed Private Journal READ-ONLY** on `main` and approve the environment review. It performs exactly three GitHub GETs; it does **not** publish or acquire media. A missing token, file, SHA, key, anchor, owner/admin, clean privacy or journal integrity fails closed.

## Important remaining security limits

- Even a successful readback is **only a contemporaneous read with supplied validation material**. It does not independently prove the signing key holder's legal role, private vault/contract owner consent, complete revocation history, a nonrollbackable external anchor, current license validity or future permission.
- The separate anchor must be advanced transactionally under an independently reviewed process. The bridge uses only the pinned sequence/head supplied by the owner; secrets and Actions cannot by themselves prove immutable historical publication.
- This is **not** a production upload/rights gate: its output has `genuine_creator_licenses_verified=0`, `source_media_download_authorized=false` and all YouTube-write authorizations `false`.
- The private metadata repository and protected environment have been created, but the owner has NOT yet approved licensed-media storage or provided dedicated read-only token, signer keys, external durable anchor, legal consent, final exact-render release, Clivox Google OAuth or production YouTube video. Branches 1 and 2 remain paused.

References: <https://docs.github.com/en/rest/repos/contents>, <https://docs.github.com/en/rest/collaborators/collaborators>, <https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments>.
