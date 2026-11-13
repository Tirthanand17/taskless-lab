# Clivox A3 — Confidential media storage boundary

**Status (2026-11-12):** Media-storage **preflight implementation**, not an active licensed media vault. Public controller repository: Tirthanand17/taskless-lab. Clivox channel ID: UCfPEvy0SefE_5nNlYlY_CyQ. The real private vault has **not** been created, linked or approved; no third-party source media has been downloaded/stored.

## Why a public GitHub repository cannot be the raw media store

GitHub documents that a public repository is open to everyone, and Actions artifacts can be downloaded by people with read access to that repository. Public Git LFS, Issues and release attachments are likewise not confidential. Changing retention from 90 days to 1 day is *not* equivalent to access restriction. Never upload raw third-party recordings, license documents, private review renders or source-provider session tokens to the public repo/artifacts.

Primary sources checked 2026-11-12:
- Public/private repository visibility: https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories
- Workflow artifact download permission: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
- Artifact retention limits: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- Environment secrets and protection: https://docs.github.com/en/actions/concepts/security/secrets
- Deployment environment reviewer support limits: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## Proposed architecture, not provisioned

~~~mermaid
flowchart LR
  A[Public controller taskless-lab] --> B[Candidate + creator permission review]
  B --> C{Human rights holder proof and contract accepted?}
  C -- No --> D[STOP: no source download]
  C -- Yes --> E{Owner-approved private media vault exists?}
  E -- No --> D
  E -- Yes --> F[Authenticated private vault identity + ACL validation]
  F --> G[Ephemeral GitHub runner and integrity verification]
  G --> H[Licensed source clip processing]
  H --> I[Original commentary and release-signature review]
  I --> J[Private-first YouTube release only after distinct later approvals]
~~~

The primary repo contains *only code, checksums, sanitized source IDs and non-sensitive evidence metadata*. Proposed future media backend: **private owner-controlled GitHub repository with access-controlled GitHub Release assets**, subject to owner approval and a separate integration review. Release assets are an architectural option, not a guarantee that GitHub is suitable for all licensed media. Alternative: owner-approved encrypted cloud object storage, preferably using short-lived OIDC credentials.

**No private vault repository has been created** in this phase; this design deliberately avoids granting cross-repo tokens from untrusted public PR workflows.

## Files implemented in A3

- storage-policy.json — fixed identity and deny-by-default operating configuration.
- examples/unlicensed-source-manifest.json — source metadata only, all license/file/asset fields unset.
- scripts/branch3_media_storage_preflight.py — pure offline validator. Requires public repo storage restrictions, no source rights, disabled source/media/upload actions, and exact Clivox channel identity.
- scripts/test_branch3_media_storage_preflight.py — adversarial tests: public leaks, bad paths, wrong channel, forged rights, unauthorized backend, hypothetically private repo metadata misrepresented as permission.
- .github/workflows/branch3-clivox-a3-media-boundary.yml — read-only, no-secret GitHub Actions preflight. Stores a **JSON-only public-safe result**, not media or contract bytes.

A passing validator is not a legal clearance or a repository-permission attestation. A3 code explicitly throws on any attempted actual media operation.

## A3 authenticated private-vault metadata bridge — implementation only\n\nA protected, owner-triggered, read-only private GitHub repository and collaborator-list inspection is now implemented. Read [the owner's secure setup instructions](OWNER_PRIVATE_VAULT_READBACK.md). The new job has **not run against an actual private vault**: no repository, protected environment, owner consent, token or media has been provisioned or verified. Its success can never authorize media acquisition, license approval or YouTube publishing.\n\n## Planned storage activation: all conditions must be true

1. Verify a real creator-issued **commercial YouTube clipping license** for the exact source, with relevant time/territory/expiry terms and rights to edit/repost. Confirm music, game publisher, guests, broadcasts and embedded content separately. Campaign invites are not licenses.
2. Owner personally reviews contract rights and any **IP assignment** to clipping campaigns (Content Rewards Section 17.6); explicit consent/eligibility required before joining.
3. Owner chooses a **confidential storage provider** (private owner-controlled GitHub repo, or other approved private storage) and authorizes provisioning and scope; do not automatically create a new repository or modify visibility of the public primary repository.
4. Verify private repo identity/visibility/owner using **authenticated GitHub API readback**, not manually authored JSON. Review memberships, repository access, private GitHub Actions artifact policy, object retention and deletion obligations.
5. Configure separate vault-only read credentials/short-lived OIDC where feasible. **Never** reuse FlowMinute Lab's YouTube token and never grant untrusted PRs secret access.
6. At approved runtime, download only source files for the licensed segments using an authorized source-access method. YouTube Data API **does not** provide arbitrary download access to third-party media.
7. Verify source SHA-256, expected asset length/type, no symlinks, content provenance and active rights grant before extraction. Copy only to ephemeral job workspace and delete immediately after run.
8. Do not upload restricted media as public Actions artifacts, Git LFS blobs, public Releases, source commits or Issues. Private review sharing requires its own separate authorization.
9. The owner must sign the *exact rendered video SHA*, metadata and target Clivox channel before later private-first upload/scheduling.

## Risk table

| Risk | Mitigation |
|---|---|
| Public media exposure | Hard deny all Branch 3 binary media formats except the two previously published original Clivox branding PNGs |
| False private vault | Require authenticated metadata showing private visibility and verified owner identity; JSON fixture alone never allows download |
| Raw media in workflow artifacts | Only non-sensitive metadata JSON report; workflow has contents:read; never exports licensed footage |
| Forged "rights cleared" flag | Fails closed in source manifest; actual human-signed proof belongs to separate future integration |
| Wrong YouTube channel | Exact UCfPEvy0SefE_5nNlYlY_CyQ required; Branches 1–2 remain paused |
| Uploaded before owner consent | No upload or media fetch routine in A3 and all launch controls disabled |
| External source link with tokens | Only a canonical public YouTube URL, no signed downloads or secret query parameters in repo |
| Creator license revocation | Runtime design requires current license readback and expiry/revocation recheck before use |

## Next milestone

**A3 software boundary:** built and testable once CI passes.
**A3 private storage deployment:** still blocked by owner choice and genuine rights. After that: A4 scripted original commentary, A5 licensed-media rendering and technical QA, then A6–A10 publishing and analytics.
