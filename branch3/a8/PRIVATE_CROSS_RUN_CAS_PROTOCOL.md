# CLIVOX A8 — Global cross-run upload-attempt ledger CAS contract

**2026-11-13 update:** The owner created a private CLIVOX control-metadata repo and the **canonical zero-event A8 genesis file** at the documented path. The Global CAS protocol is still **offline only**: no actual cross-run remote writer, signed owner authorization, immutable external anchor, uploader OAuth or real YouTube inventory.

## The exact problem

PR #168 implemented genuinely atomic SQLite writes to one local runner file. Independent GitHub Actions runners do not share that file, however. Two jobs starting at the same moment could each reserve the same video unless an owner-approved shared durable authority serializes them.

This milestone models one bounded **global attempt ledger** that would be stored at `clivox-private/upload-control/attempt-ledger-v1.json` inside an explicitly approved private repo, never inside public `taskless-lab`. The code has **no network transport**, uses no GitHub secret or OAuth token and cannot write any repository. Its `--mode fixture` CLI prints only a zero-rights, zero-upload status report.

## Implemented contracts

- `scripts/branch3_a8_private_cas_ledger.py`: strict CLIVOX-only canonical JSON event journal with 250-event limit, domain-separated SHA-256 chain and fixed genesis digest. Each `RESERVE_SYNTHETIC` event binds the same exact attempt key used by A8's existing private-first dry run: channel, release ID, final media, metadata and rights evidence SHA-256 values.
- Replaying the **whole** supplied ledger denies duplicate attempt keys, reused release IDs and reused exact video digests. It validates every field, time, append order and per-event hash. The only allowed second event is `MARK_UNKNOWN_NO_RETRY`, an irreversible hold that cannot authorize a retry.
- GitHub Contents response validation requires the exact private-path regular JSON file, canonical bytes, matching size, Base64 and independently computed Git blob SHA. A proposed update body includes the **previous** blob SHA and `main` branch. Synthetic compare-and-swap rejects a stale SHA and mismatched update.
- A supplied, previously observed journal head and sequence anchor is checked against reconstructed history; previously observed records cannot be silently deleted without failing that check. **The anchor is caller-supplied in tests and is not independent, immutable or durable.**
- After a simulated timeout with an unknown PUT result, the only two possible decisions are hold with reservation observed, or hold with commit not confirmed. Neither decision initiates a new upload, permits a blind retry or clears a release.
- `scripts/test_branch3_a8_private_cas_ledger.py` simulates six independent readers competing against one shared, locked, SHA-conditional test store and tests unknown-commit recovery, stale/forked history, manipulated SHA/body, wrong CLIVOX channel, reused media, illegal states and all owner trust flags disabled.
- `.github/workflows/branch3-clivox-a8-private-cas-qa.yml` runs this plus the previous SQLite/A8 dry-run suites in GitHub-hosted CI without credentials, private file access, Google calls or video assets.
- `branch3/a8/private-cas-policy.json` deliberately asserts no selected/approved vault, private upload ledger, dedicated Contents write token, external anchor, real owner video signature, rights grant, protected production environment or Clivox upload OAuth.

## Important trust boundaries

A valid blob SHA verifies the bytes of a single returned file, **not** that GitHub is presenting the latest state or that a separately trusted owner-held anchor exists. GitHub Contents optimistic-update behavior is modeled, not proven against a live private repository. A valid synthetic attempt key proves media identity binding only, **not** copyright permission or an A6 owner approval.

A private GitHub repo containing a JSON ledger alone is not necessarily an appropriately durable, rollback-resistant, audited multi-runner production store. Its change history, rulesets, backup/restore and branch protection would need independent review. GitHub Actions `concurrency` groups are not enough on their own.

The two prior production gates are still required: **authentic human-verified commercial creator rights**, and **an owner-approved exact rendered video release signed by an independently enrolled A6 key**. A7 separate Clivox OAuth and A8 remote YouTube inventory verification are additionally missing.

## Prerequisites for actual deployment (none completed by this PR)

1. Owner approves and provisions an appropriately protected private storage backend and retains a nonrollbackable journal head separately from the writer.
2. Audit real cross-run atomic compare-and-swap under concurrent live requests, including 409 and 422 behavior, ambiguous responses, authenticated readback and backup restoration. Test uniqueness across **all** reservations, release IDs and media digests.
3. Enroll production identities/roles with least privilege and a protected manual/main workflow, with an owner-reviewed recovery policy. Never write contracts, private source footage or OAuth tokens to the public repository.
4. Connect actual Clivox-only uploader credentials and Google readback **only after** licensed sources, A5 human video QA, A6 owner exact-video signature and private-first YouTube checks pass.
5. Keep an ambiguous upload blocked until authenticated remote inventory/owner decision. Do not reuse an attempt ID or automatically retry merely because a GitHub file lacks a video ID.
6. Add and test a safe operational disable/takedown and revocation propagation mechanism before any public scheduling.

**Current reality:** owner-only private **metadata** repo plus one empty A8 ledger now exists, but **NO** licensed-media vault, remote CAS writer, independent anchor, Clivox uploader OAuth or real YouTube inventory. 0 verified creator grants, 0 uploads and no publishing.
