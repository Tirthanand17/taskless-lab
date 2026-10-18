# FlowMinute — staging handoff lineage survives SQLite worker recovery

**18 Oct 2026 | public Draft PR #5, no deployment, no external service**

The prior SQLite `agent_staging_claims.py` worker prototype persisted the 64-hex artifact SHA only when a task completed. It did not preserve the evidence references, original producer, declared task type or unverified review label across restart. Therefore downstream agents could not reconstruct which exact completed parent artifacts they consumed.

The new **separate local `stage_handoffs` table** persists bounded canonical JSON metadata (≤4096 bytes, 1–12 distinct SHA-256 references) and its SHA-256 digest in **the same `BEGIN IMMEDIATE` transaction** as a task's fenced completion and promotion of ready dependent tasks. Recovery independently reparses and validates each metadata item against the original `TaskContract`, task owner, `UNVERIFIED_STAGING_ARTIFACT` state, stored artifact SHA and per-parent artifact digests; a downstream completion requires references to *all* its direct parent artifacts. No artifact bytes or actual user media are persisted.

Regression tests verify real reopen after completion, source→fact-review handoff with missing versus correct parent lineage, an invalid forged approval even if the attacker recomputes the local hash, rehashed child evidence lacking a completed parent's SHA, and oversized/duplicated references. The existing dedicated agent CI workflow now explicitly includes the local lease module/tests; no separate workflow or cloud deployment introduced.

**Security boundary:** The local hash detects incidental corruption and certain inconsistent states; someone with write access to the SQLite file can still forge coherent metadata, actor IDs are not independently authenticated, and the caller's wall clock is not trusted DB time. These records are not signed human fact/right/voice reviews and cannot authorize rendering, production D1 writes, billing or YouTube. This is a schema rehearsal for a future **single authorized** durable coordinator, not a competing production release ledger.

No new voice provider, OCR/media model, OAuth, private CI, user laptop/Nirala, Cloudflare deployment, private account, upload or publication was accessed. Both public PRs remain DRAFT/unmerged and budget recurring ₹0. **21 production acceptance subphases across six incomplete major phases still require independent verified production evidence.**


## End-to-end offline durability acceptance

A separate 18-stage integration regression now starts from the untouched original `episode_workflow()` DAG and reopens the SQLite store before and after **every specialist handoff**. Each synthetic stage attaches its own digest and every parent's prior persisted artifact SHA; the four-parent `release_review` stage explicitly tests a missing parent, confirms transactional rejection, then completes only with all four parent hashes bound. All 18 stages end in `complete` with empty ready/running queues, zero spending and publication disabled. This proves restart/lineage correctness only for synthetic metadata under a local trusted test harness; it does not attest independent human review, commercial rights or a real channel release.
