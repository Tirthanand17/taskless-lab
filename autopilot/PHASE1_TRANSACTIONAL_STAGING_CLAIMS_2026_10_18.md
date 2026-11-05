# FlowMinute Lab — local transactional staging-worker fencing prototype

**18 October 2026 | Offline Phase 1/4 compatibility rehearsal, existing public Draft PR #5.**

## Unattended-operation failure being addressed

The existing hierarchical agent graph can checkpoint and recover a single runner's Python `Workflow` instance, but **two resumed workers** each loading their own snapshot could both claim an identical `READY` task. A process-local claim is not safe under multi-worker execution. This is distinct from the existing **Phase 4E release ledger and its signed upload/nonce protections**. This implementation creates **no competing production release ledger**, no OAuth authorization and no actual YouTube release state.

## New prototype

`autopilot/agent_staging_claims.py` is a **single SQLite file, local-only** demonstration of atomic staging-worker reservations for the existing, unmodified 18-stage per-episode DAG. It reuses the exact typed task contracts, department-owner mapping and `Handoff.validate` requirements already in `agent_org.py`.

- Uses SQLite `BEGIN IMMEDIATE` transaction isolation across independent connections for each claim, heartbeat, completion, deliberate failure and expired-worker recovery.
- Only one contender can turn `READY→RUNNING`, with an increasing **generation fencing token**. A late task cannot mark itself complete after expiry, failure, or new ownership.
- Fixed 10–900-second local lease bounds, timezone-aware whole-second UTC input, simple no-backward-time protection across operations. The injected clock is **not an independent trusted server clock**, so these tests do **not** prove Cloudflare D1 lease timing.
- An expired or explicitly failed worker consumes one of the two permitted retries; a third interruption quarantines the task and its downstream work remains blocked.
- After a correctly fenced task supplies a valid **UNVERIFIED_STAGING_ARTIFACT** handoff, its dependents become ready atomically if and only if their original prerequisites have completed. Handoff hash and evidence references cannot impersonate a fact reviewer or grant publishing access.
- Reads never include raw user files, tokens, credentials, TTS models, actual videos or licensed voice assets. The local schema fixes the channel identity, exact DAG hash, `monthly_infrastructure_inr=0`, and disabled publisher fields.

## Evidence and limits

New `autopilot/test_agent_staging_claims.py` tests a real **two-connection concurrent claim race**, process reopen and persisted state, valid handoff/dependency unblocking, expired leases and stale token denial, heartbeat renewal, three crashes→quarantine, malformed review evidence, bad actor and failure categories, local time rollback and renewal fencing. The completed tests are an **offline software correctness proof only**. The SQLite file is never a deployed persistent Cloudflare D1 database.

**Material caveats:** a human or malicious runner with DB file access can forge stored rows; the caller-supplied worker owner label is not authenticated, and the local notion of time is not a trusted shared clock. Likewise a completed staging review is *not* an independent signed legal, factual or publication approval. Before deploying anything, migrate to the single separately approved authoritative ledger/worker service with authenticated worker enrollment, trusted DB time, atomic distributed leases and signed QA evidence—without copying release credentials into public CI.

Both public PRs remain DRAFT/unmerged; no Nirala/desktop, private Actions, external provider, new Cloudflare deployment, D1 write, YouTube read/write, publication or new cost. Monthly recurring budget remains **₹0**. Existing 21 production acceptance subphases across six incomplete major phases remain open.
