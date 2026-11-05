# FlowMinute Lab — crash-safe restart of offline agent staging tasks

**18 Oct 2026 | Phase 1 reliability hardening on existing public Draft PR #5; no production cloud deployment**

## Failure found

The 18-stage agent DAG could write a local test-only SQLite checkpoint with an individual task in `RUNNING`. If that Python process subsequently crashed, the old `Workflow.restore()` faithfully loaded `RUNNING` but had no attached worker to resume it. `claim()` requires `READY`, so the stage and its downstream research, bilingual scripts, QA, rendering plans and later draft schedule could remain permanently stuck.

## Applied engineering fix

- `autopilot/agent_org.py` now verifies ALL restored task status/retry combinations before recovery: valid stable states only, nonnegative **integer not Boolean** retry count within contract bounds, bounded last-failure labels, `QUARANTINED` only after allowed retry exhaustion, and a completed artifact only for `COMPLETE`.
- After reconstructing the complete DAG, the loader refuses impossible saved dependencies. A `READY`, `RUNNING`, `QUARANTINED` or `COMPLETE` task with an uncompleted dependency is rejected; a `BLOCKED` task with all dependencies already completed is also rejected. No downstream stage can gain apparent readiness from a changed local file.
- A legitimate orphan `RUNNING` staging task is converted on recovery to `READY` with exactly **one consumed retry** and a recorded bounded `INTERRUPTED_STAGING_RUN` failure event. When this exhausts `max_retries=2`, it is `QUARANTINED` with an explicit recovery event, with dependent stages still blocked. This function only supports the staging graph's capabilities, all of which are no-network/no-charge/no-upload by design.
- Recovery occurs **in memory only**; the caller must explicitly `checkpoint()` the recovered state before resuming execution. Re-loading an unchanged file repeats the same recovery from its prior persisted bytes, so this is not a cloud distributed lease or transactional restart guarantee.

## Verification and limits

New tests exercise single-crash recovery, checkpoint persistence and subsequent successful actor-bound task completion, one/second/third interrupted run and final quarantine, dependency graph tampering with a **recalculated local SHA-256**, invalid retry counters including Boolean coercion, and all existing role/capability/upload denials.

Local SQLite hashes are **not signatures**; someone who can rewrite the database can change other permitted-looking task/evidence records. This change stops obvious impossible states, not malicious production actor impersonation. It does not authenticate independent fact/rights reviewers, acquire voice models, create licensed speech, store cloud leases, modify Cloudflare D1, authorize a release, connect OAuth, or schedule/upload to YouTube. The existing trusted production ledger is separate, still unapproved for remote changes. No Nirala, external service, private CI, charges, or new media assets. Both PRs remain DRAFT/unmerged; ₹0/month recurring cloud budget and 21 tracked production acceptance subphases unchanged.
