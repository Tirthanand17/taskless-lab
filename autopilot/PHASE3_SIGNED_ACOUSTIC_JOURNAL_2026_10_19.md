# FlowMinute Lab — signed sidecar admission into the durable offline review journal

19 October 2026 | public DRAFT PR #5 | no release or live service

## Gap addressed

Previously the signed acoustic file-content inspector had no integration with the local SQLite review journal. A caller could submit valid detached Ed25519 review metadata without the journal persisting whether signed evidence files were actually opened. Older records must NOT be upgraded into claims of reviewed speech.

The optional strict method OfflineTranscriptReviewLedger.commit_sidecar_bound now:

1. Enters the existing SQLite BEGIN IMMEDIATE, audits prior events and selects the SQLite host-clock verification instant.
2. Re-validates the exact two Ed25519 roles and BEFORE consuming any receipt, securely opens both bounded reviewer sidecars via the existing inspector; it refuses missing, mismatched or tampered evidence files.
3. Includes sorted (role, reviewer_id, evidence_sha256) triples in the canonical event hash and writes indexed digest records in the SAME transaction.
4. Re-audits at admission and SQLite reopen; missing, altered, partial or orphaned digest records reject the audit.
5. Exposes signed_sidecar_digests_chained=True only for strict new records, and current_event_has_chained_sidecar_digests for the current event.

Backward compatibility: the older commit method remains a detached-only synthetic rehearsal. The legacy hash serialization is unchanged and its stricter evidence flag is false. A future exclusive trusted service must expose only commit_sidecar_bound, not the weaker legacy path. No such service is deployed.

## Synthetic tests

test_cloud_acoustic_review_journal.py checks acceptance plus SQLite reopen; absent and changed files with zero-event and zero-receipt rollback; altered stored digest; one deleted role; legacy entries clearly marked weaker. All keys, transcripts and reviewers are fictional, created in ephemeral test directories.

## Critical limitations

The SQLite DB, external public-key registry and local wall clock are not independently trusted. Cryptographic byte-integrity DOES NOT prove human listening, ASR operation, spoken Hindi/English correctness, caption sync, independent human identities, or media/narrator rights. Licensed voices, actual audio, durable verified free cloud capacity, authentic production DB, independent media clearance, channel-owned OAuth and publication all remain blocked.

No actual Google or Cloudflare call, upload, schedule change, provider connection, personal laptop usage, new charge or production service operation. Public PR #4/#5 remain DRAFT/unmerged and all production acceptance phases stay open under ₹0 recurring monthly infrastructure.
