# FlowMinute Lab — Fail-closed service restart and abandoned lease recovery

**19 October 2026 | Public Draft PR #5 | Offline no-network only**

## Restart gap closed in the offline service

The process-separated Unix-domain staging server previously called `core.reconcile()` on startup. However, it did not reclaim workers that were already expired while the service was down. These stranded RUNNING rows could continue consuming the globally bounded four-task fanout or occupy an unfinished video slot until an operator manually recovered them.

New `preflight_offline_staging(core)` performs a read-only `PRAGMA quick_check(1)` and existing full manifest, evidence, receipt, task-status and DAG validation before **any startup lease recovery**. The service constructs its policy-bound signed command gateway and validates persistent key revocation/admin tables, then runs the preflight before binding its listening Unix socket. `UnifiedStagingCoordinator.recover_expired(now=None)` now uses SQLite host seconds **inside its atomic `BEGIN IMMEDIATE` task transaction**. Expired staging leases are fenced, retried or quarantined; independent sibling tasks are cancelled and next queued video admitted in the same transaction where a retry budget becomes terminal. Reconciliation follows, with explicit three-active/four-running/nonpublish/₹0 checks. Recovery is idempotent across repeated restarts.

Four new no-secret regressions cover a worker lease that expired while the service was offline and can then be reclaimed with a newer generation; a persisted impossible future clock that must cause startup refusal **before opening a socket**; corrupted task owner inventory preventing startup before accepting work; and third-expiry quarantine moving the next queued video into the newly free active slot, with idempotent subsequent preflight.

**Limits:** SQLite still uses local OS time, not independently trusted database-server time. Tests are synthetic; this does not turn worker credential security into a remotely owned cloud API, fix same-UID malware risk, stop external workers, create actual Hindi/English voices, validate video rights/quality or enable Google OAuth/YouTube publication. We do not build a free-tier-deployed always-on service because that requires a newly authorized account connection and a verified free-resource plan. Original 21 production acceptance subphases over six incomplete phases stay OPEN; both public PR #4/#5 DRAFT/unmerged and ₹0/month budget unchanged. No user laptop/Nirala, external APIs or charges.
