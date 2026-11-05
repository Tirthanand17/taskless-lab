# FlowMinute Lab — Nine-episode / three-active durable offline staging queue

**18 October 2026 · Existing public Draft PR #5 · No live service or publication**

## Actual coordination gap

The master orchestration preview supported nine proposed episodes with three logically active, but after a crash the task-level SQLite staging lease proof had **no persistent multi-episode admission order or bounded slot index**. Two coordinator instances could each admit additional episodes outside the cap if run independently.

## What is implemented

`autopilot/agent_staging_master_queue.py` adds one **local transaction-serialized master queue index**, using `BEGIN IMMEDIATE` on SQLite. It stores an immutable fingerprint of 1–9 typed `EpisodeSpec` records, original channel identity, and hard disabled publishing/₹0 budget fields; its active state cannot exceed three. Priority order is stable (descending priority, then episode ID). It **reuses `SQLiteStagingClaims`** for the actual 18-stage per-episode task state, evidence lineage, generation-fenced claims and bounded retry/quarantine, rather than cloning it.

A `reconcile()` step checks all active per-episode staging stores: an episode transitions to **complete** only when all 18 source-contract tasks report complete with stored handoffs; a stage quarantine pauses the episode and releases its slot. The next queued episode is admitted in the same master-index transaction until there are at most three active. Two competing coordinator connections serialize admissions, and two competing specialist workers still rely on the child store's atomic fenced claim.

An interrupted activation can leave a valid per-episode SQLite store before master-index commit. The next `reconcile()` recovers that exact store after validating its original contract, **never truncating or overwriting it**. This is practical local crash recovery, but transactions across distinct SQLite files are **not** represented as globally atomic.

## Tests and limits

Regression tests cover nine episodes/three active, priority/reopen, concurrent competing admissions, two actual worker-claim races, all 18 synthetic specialist completions of an episode opening the next slot, quarantined episode eviction, interrupted admission recovery without data loss, invalid identities/priority and active-cap tampering, bounded task fanout, and every safety flag.

No LLM generations, genuine human approvals, signed facts/rights, licensed narration, authenticated workers, independently trusted server/database time, remotely durable Cloudflare D1 queues, persistent production media, private YouTube pilot or customer data are involved. An external service cannot claim production readiness from this local rehearsal. The production release ledger and PR #4 are untouched, and this queue is **not** a replacement ledger. Public repo CI is legitimate bounded software testing only, not a 24/7 render farm.

Both PR #4/#5 remain DRAFT/unmerged. The original **21 production acceptance subphases over six major incomplete phases** remain open. Monthly cloud recurring budget remains **₹0**; no Nirala laptop, new external provider, OAuth, Cloudflare deployment, D1 production write, video upload, schedule or public publication.
