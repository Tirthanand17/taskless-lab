# FlowMinute Lab — durable exactly-once state transition receipts (offline)

**18 October 2026 · Public Draft PR #5 · No deployment, accounts, media or publishing**

## Failure mode and fix

The unified per-video staging coordinator already has a single local SQLite `BEGIN IMMEDIATE` transaction for task completion, but an interrupted worker could lose the response after COMMIT. Blindly retrying `complete()` would fail because the task is no longer RUNNING. The worker cannot tell if it failed or completed and can repeatedly attempt an unnecessary second job.

The updated `UnifiedStagingCoordinator.complete()` adds an **optional bounded `request_id`** for local staging handoff acknowledgement. When supplied, a canonical **request fingerprint** binds episode ID, original department actor label, current generation-fencing token and exact typed Handoff payload. A `completion_receipts` row with the immutable historical outcome, bounded canonical response and SHA-256 checksum is inserted **in the same transaction** as the persisted Handoff, dependency-unblocking transition, and any newly admitted video. Replaying the exact same key/payload on a restarted process returns the original recorded outcome without re-running the stage, consuming a lease, advancing the local clock, or creating another receipt. Reusing the key with changed payload, generation, actor or video is denied. The original no-key API remains supported for existing staging tests and callers.

Regressions cover lost response/restart replay, two independent workers racing to retry an acknowledged completion, changed-record and cross-episode key collision refusal, simulated failure partway through the transaction followed by verified total rollback, deliberately rehashed corrupt receipt disallowal and strict IDs/legacy compatibility. GitHub dedicated agent tests and Content Quality Gate exercise these cases.

## Explicit security and production boundaries

This is **idempotent local staging state mutation**, NOT exactly-once remote media rendering or YouTube upload. A malicious owner of the SQLite file can rewrite coherent local records/hashes, actor labels are unverified, timestamps are caller-supplied, and the historical result cannot be interpreted as new lease ownership or independent editorial/licensing approval. Real production requires authenticated remote workers, durable cloud datastore with trusted DB time, real-side-effect fencing, separate independent signed reviews, actual rights-cleared Hindi/English voices, and owner-authorized Google OAuth/readback. The private production release/nonce ledger remains unmodified. The public draft PRs #4/#5 remain unmerged; no Nirala/laptop, private Actions, new provider, D1 deployment, real upload, schedules, charges or publishing. Zero recurring spend ₹0/month, and 21 tracked production acceptance subphases over six incomplete phases remain open.
