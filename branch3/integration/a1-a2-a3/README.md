# CLIVOX — A1 → A2 → A3 public-metadata handoff

**Status:** This is an original **no-media, no-license, no-Google-writes** integration test. It connects the *existing* public YouTube discovery report (A1), pending creator-rights review cases (A2) and closed confidential-media storage boundary (A3). It does **not** advance an item to RIGHTS_VERIFIED, open a vault, download source video, sign a release or upload to YouTube.

## Why this exists

Previously, A1/A2 and A3 validated separately. A2 recorded the A1 digest but there was no cross-stage check that the actual discovery object still matched the currently presented rights cases, nor a single integration step tying both to the storage deny state. That made a consistent pending-case handoff harder to audit.

The new `scripts/branch3_a1_a2_a3_handoff.py`:

1. Allows only the defined public-metadata fields. Unexpected fields (including contact details, private contracts and tokens) cause a failure before the output report is created.
2. Requires exact CLIVOX channel identity and checks discovery time <= case-generation time <= 24 hours later.
3. Recomputes the A2 cases from the complete A1 object and compares **all** human-review checklists, case IDs, ordering, fields and SHA-256 digest. A changed A1 title, rightsholder claim, candidate, grant flag or removed A2 case stops the step.
4. Calls the existing A3 storage preflight against the real repository policy, unlicensed source manifest, empty creator-approval registry and channel state.
5. Checks the public `branch3/` file inventory against existing denied-media patterns and original-brand-art allowlist.
6. Emits a sanitized JSON *quarantine* report that explicitly states **zero verified grants, zero media downloads, zero network/API writes and zero publication privileges**.

**Limits:** A matching SHA-256 digest proves A1/A2 input consistency only, not that a YouTube API response or publisher identity was authentic. Public JSON booleans cannot prove legal grants or actual private-vault ACLs. Do not promote candidates based on passing this test.

## Run in GitHub

The workflow `.github/workflows/branch3-clivox-a123-provenance.yml` runs in GitHub-hosted CI, in a read-only public PR context, using synthetic A1 source statistics and two invented source IDs. It then creates real A2 pending-case JSON, audits the A3 closed boundary, runs adversarial unit tests and uploads **only** the sanitized source-free proof as a seven-day Actions artifact.

No owner-laptop files, secrets, Google OAuth, signed approval, video source download or YouTube API writes are used.

A manual dispatch is also available on the repository default branch. For a live public-metadata discovery (when a separately approved API key exists), the same checker can audit real A1/A2 files *without* changing license status; the public API key is not needed to execute this checker.

## Owner actions still required before actual third-party source handling

- Obtain independently verifiable creator/recording-owner commercial clip permission and separately check games, embedded music, guests and other rights.
- Approve private media storage; verify vault ownership, privacy and access rights using authenticated GitHub API readbacks in a protected workflow.
- Independently review actual source and commentary, and enroll exact-media owner signing.
- Grant distinct CLIVOX upload OAuth only after a separately reviewed release integration; use durable atomic upload leases and authenticated remote inventory reconciliation.

**No third-party content is authorized or available for editing/upload today.** A9 licensed pilot remains unstarted and Branches 1/2 remain unchanged.
