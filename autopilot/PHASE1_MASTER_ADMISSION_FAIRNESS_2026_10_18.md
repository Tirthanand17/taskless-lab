# FlowMinute Lab — Master-gated staging task admission and fair scheduling

**18 October 2026 | Existing public Draft PR #5 | Staging software only**

## Actual coordination bugs

The initial 9-video/3-active master queue offered advisory `ready_assignments()` but had no master-level **claim** operation. A scheduler following the index could use the per-episode child store directly, bypassing master-active checks and the total task concurrency policy. When three videos had parallel ready specialists, the previous assignment algorithm exhausted tasks from video 1, then video 2, potentially giving video 3 zero work within a four-slot suggestion window.

## Implemented

`SQLiteStagingMasterQueue` now exposes bounded, transaction-backed **`claim_active`**, `heartbeat_active`, `complete_active`, `fail_active`, and `recover_expired_active` methods. Each checks that the exact episode is currently **active** under the master's `BEGIN IMMEDIATE` transaction. `claim_active` also rereads the *actual current running task counts* from all active child stores and refuses a fifth worker if **MAX_FANOUT=4** slots are occupied. Child worker generations, expiry, handoff lineage and retries retain their original fenced validations; a child from a different episode cannot substitute its handoff.

`ready_assignments` now distributes recommendations **one task per active episode per round** and reduces available suggestions according to the existing active worker count. This favors parallel progress on all three draft videos instead of starving the third when earlier videos have multiple ready tasks. It never starts workers itself.

Regression tests cover refused claims for unadmitted/queued/terminal episodes, successful claim only after the master admits the next queued video, fair three-video recommendation with two parallel tasks on earlier episodes, four globally active worker cap, reopening competing master coordinators claiming the same task, generation fencing on heartbeat/expiry/recovery, and rejected cross-episode handoffs. Existing nine-episode capacity, restart, source lineage, quarantine and no-publishing tests remain.

## Real limits

The underlying child SQLite file is still directly accessible to other code/processes. **These master methods are a safe convention for cooperative test workers, not an unbypassable security boundary**: production will need a single authenticated worker API that exclusively owns the storage and trusted database time. The master index and child files are not a globally atomic distributed transaction. The source and test handoffs are synthetic staging metadata, not independent human legal/fact/voice approvals, completed videos or publishing authorization.

No new services, laptop/Nirala use, production D1, external accounts, real media uploads or costs. Both existing public PRs remain DRAFT/unmerged. Monthly infrastructure budget ₹0 and 21 still-open production acceptance subphases across six incomplete top-level phases remain unchanged.
