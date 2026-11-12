# Clivox A7 — Owner-approved, live READ-ONLY Google connection

**Phase:** Bridge implemented; **real OAuth consent, protected environment and secret enrollment not yet confirmed**. Does not upload, edit, schedule, delete, publish, download media, or authorize clipping rights.

## Verified reference
- Google web-server OAuth offline access: https://developers.google.com/identity/protocols/oauth2/web-server — owner consent with `access_type=offline` is required to obtain an offline refresh token.
- YouTube Data API OAuth: https://developers.google.com/youtube/data/guides/authentication — use exact channel owner OAuth and `https://www.googleapis.com/auth/youtube.readonly`, not an API key or FlowMinute Lab token.
- GitHub protected environments: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments — reviewers and branch allowlists must be configured in GitHub Settings, not assumed because a workflow names an environment.
- GitHub managing environments: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

## Source of truth and actual safeguards
- Existing offline A7 policy remains `OFFLINE_FIXTURE_ONLY_UNTIL_OWNER_OAUTH`. The new bridge deliberately has a **separate entrypoint**; the old offline mode must not be toggled on merely by editing a JSON field.
- `.github/workflows/branch3-clivox-a7-live-readonly.yml`: **workflow_dispatch only**, `main` only, no PR execution, no schedules, GitHub `contents:read` only; references separate `clivox-readonly` environment. No uploaded artifacts.
- `scripts/branch3_a7_live_readonly_bridge.py`: validates exact repository, branch, event, workflow file path and explicit owner opt-in. Then refreshes Google OAuth, verifies one exact channel `UCfPEvy0SefE_5nNlYlY_CyQ`, and samples its uploads playlist. All raw tokens and private video IDs stay out of logs.
- `scripts/test_branch3_a7_live_readonly_bridge.py`: mocked API tests; no real Google access. These reject wrong account, old FlowMinute account, broad OAuth scopes, missing credentials, PR runs and untrusted branch.
- `.github/workflows/branch3-clivox-a7-live-bridge-qa.yml`: PR-only offline CI with no secrets or Google requests.

## One-time actions required from the owner (NOT performed by the code)
1. In Google Cloud Console, create/select a **Clivox-specific** OAuth 2.0 client, enable YouTube Data API v3, and set an appropriate owner-facing consent screen. Use the correct Google/Brand Account for Clivox. The Google project, consent and verification status may impose extra restrictions.
2. Request **only** `https://www.googleapis.com/auth/youtube.readonly` and `access_type=offline` through a secure owner-controlled OAuth exchange. Do not paste authorization codes, passwords, client secrets or refresh tokens into chat, a public GitHub issue or commits. If Google returns a refresh token while the consent app is in Testing mode, confirm its expiration behavior and testing/production restrictions.
3. In the **public primary repository**, go to `Settings → Environments → New environment` and create `clivox-readonly` (different from `youtube-production` used by older FlowMinute work). Add **Required reviewers** and restrict selected deployment branches/tags to **only main**. If possible, block administrator bypass. Verify the actual settings in GitHub's UI before running any job.
4. In `clivox-readonly` **environment secrets only** (not repository-level secrets), install: `CLIVOX_A7_READONLY_CLIENT_ID`, `CLIVOX_A7_READONLY_CLIENT_SECRET`, `CLIVOX_A7_READONLY_REFRESH_TOKEN`. Use values for the *same* Clivox client and the read-only consent grant. Do not reuse any FlowMinute tokens.
5. Only after the owner has inspected the workflow and configured actual reviewer/branch protections, set the **environment secret** `CLIVOX_A7_CONNECT_APPROVED` to the exact non-sensitive sentinel `approved-readonly-clivox-v1`.
6. GitHub → Actions → **Clivox A7 Owner-Reviewed READ-ONLY YouTube Connection** → Run workflow; choose the `main` branch. Complete the GitHub environment reviewer approval (if configured). This performs exactly one OAuth refresh and **two read-only YouTube GETs**; it does not authorize publishing.
7. If a job fails with invalid credentials, scope, old channel or mismatched uploads playlist, **STOP**. Resolve consent/client identity privately; do not switch to the FlowMinute channel token as a shortcut. View the job result; it prints only a sanitized identity pass/fail, never tokens or private video IDs.

## Explicit remaining limitations
- A workflow merely naming a GitHub environment does **not** establish reviewer or branch protection. Those are owner-controlled GitHub settings that must be checked independently.
- The environment's explicit approval sentinel is not a cryptographic proof that a reviewer actually approved; the GitHub environment protection is the independent control.
- Actual read-only Google connection is not established until a successful live run verifies the channel; fixture tests cannot do so.
- The uploads-playlist response is a **first-page sample**, not a complete record of private/scheduled videos.
- Owner read-only OAuth **does not** grant `youtube.upload`, `youtube.force-ssl`, an Analytics scope, or licensing rights for creators' footage.
- A real uploader requires a separate owner-reviewed grant and A2/A3/A6/A8 protections. Branches 1/2 stay paused; Clivox publishing stays OFF.
