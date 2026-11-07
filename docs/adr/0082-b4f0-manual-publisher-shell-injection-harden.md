# ADR-0082 — B4f0 manually supplied workflow_dispatch shell injection boundary

**Date:** 2026-11-07 IST. Branch 2 manual YouTube bridge. No new live publishing authorization.

## Verified source-level problem

In `.github/workflows/publish-artifact-youtube.yml`, GitHub expressions such as `"\${{ inputs.source_run_id }}"`, `"incoming/\${{ inputs.video_file }}"`, `"\${{ inputs.episode }}"` and `"\${{ inputs.approval_manifest }}"` were embedded directly into Bash `run:` source text. GitHub expands these **before** Bash parses the script. A malicious or accidentally malformed manually supplied value containing command substitutions, a quote, semicolon or newline could alter a runner command and access the privileged workflow context. Quoting the GitHub expression with double quotes in the YAML is **not** a safe shell quoting boundary.

## Fix

- Move every untrusted workflow_dispatch input to job-scoped, consistently named `FM_*` **environment variables**. No literal `\${{ inputs.* }}` expression appears in any Bash run block. Bash treats expanded variable values as data rather than recursively evaluating their `$(...)`, backticks, quotes or command separators.
- Before any artifact download, execute stdlib-only `scripts.validate_publish_dispatch_b4f0 dispatch`: reject nonnumeric run IDs, path traversals, injected characters, unexpected types/suffixes, public/unlisted privacy, uppercase/wrong SHA256 and impossible/insufficient-future UTC dates.
- Read source workflow metadata using documented GitHub CLI `gh run view --json headBranch,headSha,conclusion,event` and reject runs not completed `success` on `main` with expected event and a 40-character commit SHA. A successful GitHub CI run is still **not** source/license/creative owner approval.
- Download into `incoming` using bounded quoted environment-variable arguments, then reject missing, symlinked, tiny and oversize media files. Existing exact video SHA, human approval flags, protected environment, expected channel, scheduled private status and two B4e9 duplicate attempt refs remain independently mandatory.
- All tests are offline, no real YouTube API, no OAuth tokens or file transfers; CI quality checks are the only smoke proof.

## Limits / next security milestones

1. This prevents shell source interpolation but **cannot authenticate five mutable owner-review booleans**. Next phase must bind signed owner authority, actual source facts/licenses and exact MP4/SRT/thumbnail/title hashes before any production upload.
2. Source run metadata being on `main` only proves repository provenance, not audiovisual correctness or permission. A later protected content pipeline must also validate artifact provenance at file and scene level.
3. Future autonomous publishing remains disabled without verified original content, channel OAuth, durable protected production ledger, owner release policy, and 21 real consecutive publish/readback successes.
4. The reviewed owner workspace still requires explicit manual artifact export: no hidden auto-upload or new GitHub secrets introduced.

## Regression acceptance

Publisher-preflight no-secrets CI must execute the B4f0 adversarial suite, including payloads with `$(...)`, backticks, quotes, newlines, `../`, traversal, invalid source events and symlinked media; static test fails if inline `\${{ inputs.* }}` ever returns to a `run: |` block.

References: [GitHub expression security](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#understanding-the-risk-of-script-injections), [GitHub CLI run view JSON](https://cli.github.com/manual/gh_run_view).
