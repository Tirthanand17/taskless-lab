# Phase 4G.2 — Historical lease expiry and QA hash event-chain hardening

**18 October 2026. Existing OFFLINE SQLite simulator only; zero live provider or account integration.**

The 4G.1 read-only recovery audit checked stage/row/event consistency, but it did not reject forged lease-claim events occurring **before** the previous lease expired, operations placed outside the recorded lease, backwards timestamps, arbitrary approval-like event fields, or a replaced plausible QA digest in a release row. Such unchecked history could produce misleading "consistent" results after a crash.

This patch **strengthens the existing software**, not a new competing ledger:

- `phase4_offline_ledger.py`: on the synthetic `media_qa_passed` stage, put the existing `review_digest` into the append-only event detail as well as the release row. The digest proves only byte equality within an offline test; no independent editorial/legal approval or media authenticity.
- `phase4g_recovery_audit.py`: reconstruct event timestamps in monotonically non-decreasing order; require a lease claim to happen no earlier than the previous lease expiry; require an active lease for *every* non-claim mutation; require exact payload shape per action and historical QA digest equal to final row. Fail closed on suspicious event history.
- Adversarial unit tests insert **synthetic forged event/row data** using the offline simulator to ensure early takeover, backdated claims, expired mutations, invented approvals and review digest replacement are detected. Normal lease expiry/reclaim and full offline stage transitions remain tested.
- Any apparently "public_verified" state in this offline simulator is still a caller-authenticated boolean, NOT evidence that a video exists or can be played. Simulated `now_utc` remains caller-controlled; no real server clock or D1 atomic CAS is supplied by this patch.

**Phase 4E, 4F and 4G production acceptance remains OPEN**: require owner-authorized exact-channel YouTube and D1 read-only history; verified backup/restore and migration; separately authorized authenticated single writer using trusted server UTC, guarded transactional CAS and safe uncertainty reconciliation. No real Cloudflare or YouTube calls, no OAuth or provider changes, no paid resources, no laptop access and no upload or scheduling. GitHub draft PR #4 remains unmerged. **21 remaining production acceptance subphases across six unfinished top-level phases. ₹0 monthly recurring infrastructure.**
