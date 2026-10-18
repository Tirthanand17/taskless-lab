# FlowMinute Lab — Atomic unified offline staging coordinator

**18 October 2026 | Draft PR #5 only · Alternative proof, not production**

## Architectural problem closed within the OFFLINE prototype

The preceding offline `SQLiteStagingMasterQueue` used one master-index SQLite database plus up to nine separate per-episode `SQLiteStagingClaims` files. It serialized admission in the master but could not atomically commit master slot replacement and specialist-state changes because these were separate database transactions. Stale workers or partial crashes could leave child/master drift, even though the prior mitigation reopened leftover child files.

The new `autopilot/agent_staging_unified.py` is a **parallel, opt-in offline alternative**, not a replacement for the existing release ledger. All 1–9 video slots, every video's complete 18-stage contract inventory and all source-validated unverified staging handoffs live in **one local SQLite database**. Each operation executes under one `BEGIN IMMEDIATE` transaction. Admission of the next queued video occurs in the SAME transaction as the eighteenth specialist completion or third worker failure/quarantine with cancellation of still-running sibling leases. No cross-file repair/recovery needed. The queue still admits at most three active videos; task claims are globally limited to four, generation-fenced and retry/lease-bounded. Recommendations are round-robin across active videos. Every completed stage persists canonical bounded JSON evidence and its full direct-parent artifact references; reopen validates the original DAG and all state invariants.

Atomicity and concurrency acceptance use two to four competing SQLite clients, completion/restart of all eighteen specialists, three-active/four-task policy, exact parent hash checks, third failure abort and replacement, lease expiry and stale-token refusal, and clear zero-budget/no-publishing flags. Dedicated GitHub Agent CI also runs this suite. **This is a material reduction in architectural complexity of an offline scheduler, not proof of cloud cost, remote availability or actual video output.**

## Nonclaims and gates

All states are test-only, source hashes are not authenticated signatures, and worker actor strings are only labels. The clock is supplied by caller; deployment still needs trusted DB time, authenticated worker registration, actual side-effect fencing/cancellation and remote durability. No legal reviewer signatures, licensed natural Hindi/English voices, independent audio/caption QA, video upload or released video IDs are created. The production Phase 4E research ledger remains separate and unmodified. Existing Draft PR #4/#5 remain unmerged. No Nirala/laptop access, private Actions, new provider/Cloudflare deployment, production D1, YouTube API, billable resources or publication; ₹0/month budget intact. **21 production acceptance subphases across six incomplete major phases remain open.**
