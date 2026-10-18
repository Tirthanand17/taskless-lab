# FlowMinute — quarantine cancels sibling staging workers before slot reuse

**18 October 2026 | Existing public Draft PR #5 | Local SQLite only**

## Failure found

The nine-video master queue previously marked an episode `quarantined` and freed one of its three video slots as soon as a single stage exhausted retry allowance, **even if another parallel specialist in the same episode remained RUNNING**. This could leave unaccounted stale work in a child SQLite store while a replacement video was being admitted, defeating the four-inflight worker-cap calculation.

## Fix

The pre-existing `SQLiteStagingClaims` no-network task backend now performs a transactional episode-abort cascade as soon as any stage becomes `quarantined`, including on expired lease exhaustion. Other `READY` or `RUNNING` specialists with completed prerequisites become **`cancelled`** (not incorrectly charged three individual failures). All their generation fences increment and running expiries clear, so stale heartbeats or handoffs cannot subsequently complete. Completed predecessor artifacts remain unchanged, and tasks with incomplete prerequisites remain BLOCKED. The operation is idempotent for reopen/reconciliation. The scheduler's existing `reconcile()` also repairs any previously interrupted cascade before freeing the slot and requires **zero running and zero ready** tasks before marking the entire episode quarantined.

This is a safeguard against stale local worker **state acceptance**, not proof that an already executing external process stopped consuming CPU; a future cloud worker will require cancellation propagation and actual resource tracking. Direct child-file access, actor-label spoofing and untrusted local wall clock remain deployment blockers.

Regression tests cover parallel script/hooks with script's third explicit failure, token-fenced cancellation of the still-running hooks, persisted state after reopen, and lease-expiry-driven abort while the other task holds an unexpired lease. The existing full 18-stage evidence-chain, competition and queue tests remain.

No licensed voices, deployment, Google OAuth, production D1, persistent media, YouTube uploads, user laptop, new paid service, or charges. Monthly recurring budget **₹0**, two public PRs still draft and unmerged, and the 21 tracked production acceptance subphases across six incomplete phases remain open.
