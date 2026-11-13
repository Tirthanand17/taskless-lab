# Clivox A3 — Private vault readback (owner-only, NOT media activation)

**Implemented:** 2026-11-13. **Current reality (updated):** A separate owner-controlled **private CLIVOX control-metadata repository** now exists and contains only two empty journal genesis files, with owner-only collaborator/visibility readback performed using GitHub CLI. It is **NOT** an approved licensed media repository. A3's dedicated protected read-only token has not been provisioned, and the separate three-request A2/A3 workflow has not run. There are zero creator grants, licensed assets or CLIVOX uploads.

This adds an **optional** one-time manually dispatched authenticated GitHub API privacy snapshot. It is not a mechanism for bypassing the A2 source rights, owner contract, A3 private-media ACL, A6 release signature or A7/A8 channel/upload requirements.

## Two separate jobs

- `branch3-clivox-a3-live-vault-qa.yml` is **PR-safe**: no secrets, no real private repo, no API network access and no media. Unit tests mock both GET responses and reject public vaults, wrong owner/org, malformed names, wrong branch/actor/workflow, missing opt-in, extra collaborators, pagination, token leaks and fake permissions.
- `branch3-clivox-a3-live-vault-readback.yml` is **manual-only on main**, requires owner actor and a fresh dispatch, and names the **now-created, owner-reviewed/main-only/admin-no-bypass** GitHub environment `clivox-vault-readonly` (**zero environment secrets so far**). It performs only `GET /repos/Tirthanand17/<approved-name>` and `GET /repos/Tirthanand17/<approved-name>/collaborators?affiliation=all&per_page=100&page=1`. Code fixes the hostname to `api.github.com` and never follows redirects or logs response bodies, tokens, collaborator names or the selected vault name.

A passing live snapshot proves **only** that GitHub returned a private, personal owner-controlled repository with the expected identity and an owner-only collaborator list at readback time. It does **not** establish that GitHub Apps, OAuth apps, backups, machine accounts, Actions permissions, previous object sharing, future ACL drift, media licensing or retention policies are safe. **No source access or media processing is enabled even if it passes.**

## Owner-controlled setup — private metadata repo and environment created; media activation NOT completed

1. Decide whether **GitHub private Releases** are appropriate for licensed original-source media and contract restrictions, or choose another encrypted storage provider. **Do not place contracts, recordings, clips or secrets in the public controller repo.** Ensure the genuine content owner explicitly allows the proposed platform and storage treatment. Review access and retention restrictions before any media.
2. If you choose a private GitHub repository, create it **personally**, with a name beginning `clivox-`, owned by your `Tirthanand17` individual account. No collaborators, forks or template mode. This script does **not** create repositories or change public visibility.
3. In `Tirthanand17/taskless-lab` → Settings → Environments, create `clivox-vault-readonly` with required reviewer `Tirthanand17`, selected deployment branch `main`, and no administrator bypass. Inspect readback of those rules using GitHub Settings/API before using the live job. **This environment does not currently have verified protection or secrets; the workflow must fail closed until it does.** Avoid assuming the workflow `environment:` field itself configures security. Self-review may be possible, so this is not independent dual approval.
4. Create a **fine-grained GitHub token restricted to just the chosen private vault**, with **Metadata: read** and no Contents, Releases, Actions or Administration write permissions. The token must be able to read repository metadata and collaborators. If permissions are insufficient or the collaborator endpoint denies access, STOP rather than broadening to unnecessary write privileges.
5. Add these three secrets to **the `clivox-vault-readonly` environment only**, not repository-wide secrets:
   - `CLIVOX_A3_OWNER_APPROVED_VAULT_NAME` — just the approved name (e.g. `clivox-owner-media-vault`, **not** an actual repo assertion).
   - `CLIVOX_A3_VAULT_METADATA_READ_TOKEN` — the dedicated vault Metadata-read fine-grained token.
   - `CLIVOX_A3_VAULT_READBACK_APPROVED` — exact non-sensitive sentinel `approved-a3-readonly-v1`.
6. Review the merged main code. Manually run Actions → **Clivox A3 Owner-Approved Private Vault Visibility READ-ONLY** on `main`, approve its required environment review and inspect only the sanitized result. There are no Actions artifacts. This workflow cannot download vault objects, inspect confidential media, upload releases or change ACLs.
7. If readback fails, inspect repository identity/visibility and token scopes privately; never paste tokens, private usernames, agreements or confidential media into GitHub issues, chat or the public repository. **A successful readback is NOT approval to move to the next A3 media stage.** A separate, owner-reviewed PR will be needed for full private ACL/app installation review, rights-specific object access, revocation handling and any later media flow.

## Security and scope notes

- GitHub REST repository metadata and collaborator endpoints allow fine-grained **Metadata: read** tokens when adequately authorized. Official references: https://docs.github.com/en/rest/repos/repos ; https://docs.github.com/en/rest/collaborators/collaborators .
- Required reviewers and protected environment secrets must be configured independently. Official reference: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments .
- GitHub's safety reference recommends least privilege, manual review of secret-bearing workflows, and minimizing PR secret access: https://docs.github.com/en/actions/reference/security/secure-use .
- The live job never receives the FlowMinute Lab OAuth token. A dedicated vault metadata token must never be reused for YouTube.
- No upload/scheduling, creator clip rights grant, owner media-release signature or real A9 pilot exists as a result of this phase.

**This work is a prerequisite verifier only. All previously closed CLIVOX production gates remain closed.**
