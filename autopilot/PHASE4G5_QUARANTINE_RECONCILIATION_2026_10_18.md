# Phase 4G.5 — Quarantine must never erase pending remote side effects

**18 Oct 2026. Code-only checkpoint on draft PR #4. No Cloudflare/YouTube account access.**

## Important safety gap found and fixed

The previous recovery inspector counted an uncertain upload or schedule from the **final ledger stage only**. Once a release was quarantined, the end-stage switched to `quarantined` and the `needs_real_provider_reconciliation_count` could incorrectly drop to zero, even though an upload or schedule intent had already been reserved and a remote request might have succeeded. This could conceal an unresolved duplicate-release hazard.

The existing `phase4g_recovery_audit.py` now reconstructs all remote request exposure from the entire append-only event chain. Quarantine cannot remove that history. Counts separately report: all releases that have ever reserved a remote intent (all require genuine live YouTube-channel reconciliation, as simulator `authenticated=True` is not meaningful); upload intents with no even simulated private readback; schedule intents with no even simulated schedule readback; quarantined releases with remote intents; quarantined releases with unresolved intents. The old `upload_uncertain_count` and `schedule_uncertain_count` are retained as **final-state-specific** metrics only.

The same existing OFFLINE SQLite ledger now provides `quarantine_db_clock_rehearsal` using its Phase 4G.4 conditional transaction with SQLite-selected time and exact owner/version/fence/lease stage checks. It is a terminal local test state, not a guarantee a video was never uploaded. It does not retry uploads or schedules.

Adversarial real SQLite tests cover quarantined initial release (no remote debt), quarantined upload/schedule uncertainty (debt preserved), simulated remote receipt then quarantine (still needs live readback), double quarantine, invalid worker/lease/clock injection, and redacted output. The preexisting versioned event chain and database-clock tests remain valid.

**Scope:** offline SQLite reference only. No provider identity, actual media, rights, live Cloudflare D1, YouTube OAuth or server-clock trust. Real production 4E/4F/4G remain OPEN. ₹0 recurring cloud infrastructure, no Nirala/laptop, external service connection, D1 mutation, upload, scheduling or publish. PR #4 stays DRAFT; separate PR #5 stays DRAFT. Overall **21 production acceptance subphases across 6 incomplete major phases** remain open.
