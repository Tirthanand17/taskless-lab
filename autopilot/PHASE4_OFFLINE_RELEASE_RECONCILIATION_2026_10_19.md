# FlowMinute Lab — Phase 4 offline release/owner inventory reconciliation

19 October 2026 | public DRAFT PR #5 | read-only software compatibility, **NOT** a live cloud release migration

## Why the previous gates were insufficient

The private legacy release ledger defines the upload stages and prevents some duplicate remote IDs. The private authenticated YouTube inventory adapter can enumerate video ID, privacy, processing and schedule metadata; the D1 inspector can list schema details. But neither a schema inventory nor an API-shaped YouTube listing currently proves that **one verified durable cloud writer**, its historical release rows and the actual owner-channel state agree. A caller-supplied boolean such as verified_owner=True is not independently attested. A lost videos.insert response must **never** cause a blind retry.

## Implemented in the public, no-credentials repository

- cloud_release_snapshot_reconcile.py introduces strict typed ReleaseSnapshot and OwnerVideoSnapshot rows, bounded at 500 releases and 500 owner videos. Validates exact release-date/episode/media SHA/video ID fields, allowed state machine stages, globally unique original media and bound video IDs, sane UTC timestamps, owner channel equality and self-consistent readback uncertainty flags.
- reconcile_release_snapshots is a pure, no-IO dry-run evaluator. Upload-started with no verified ID becomes AMBIGUOUS_NEEDS_MANUAL_RECOVERY even if the remote list lacks a video; it explicitly returns safe_to_retry_any_ambiguous_upload=False.
- Detects a bound remote ID missing in inventory (not definitive proof of deletion), processing not succeeded, suspicious private/public transitions, changed or missing scheduled timestamp, public-state mismatch, duplicate cross-release original media, partial inventory, previously unmatched owner videos and impossible state-field combinations. Unmatched channel videos may be legacy, therefore remain lineage questions, not automatically reassigned releases.
- Output is aggregated code/category counts only. It never returns channel IDs, video IDs, exact episode identifiers, media hashes, dates, private titles, credentials or API result body. A perfect shape match is still UNTRUSTED: independent source authentication, a cross-provider consistent snapshot and verified D1 state have **not** occurred.
- reconcile_existing_private_shapes accepts the exact 6-column private control.ledger.Ledger get() SELECT tuple layout and the existing control.youtube_upload_inventory.inspect_owner_upload_inventory report schema. It checks the collector's explicit negative privilege flags, exact fields, owner-bound channel ID, local snapshot completeness claim, video and unknown-record counts, then invokes the same pure reconciler. It contains NO import or API call to the private repository. Use only in an authorized memory-only private runtime.
- There is no new cloud table, token use, OAuth interaction, metadata fetch, upload retry, publish/schedule action or local laptop execution.

## Tests

test_cloud_release_snapshot_reconcile.py exercises 19 synthetic no-network scenarios covering matches without release authority, upload_started, missing/changed/unknown videos, privacy and processing drift, changed schedule, public state, historical/legacy owner video ambiguity, duplicate local media/video IDs, malformed stage/dates/IDs/counts, incomplete provider reads, and private legacy tuple+report compatibility including forged permission flags and redacted error strings.

No private screenshots, YouTube credentials, channel titles, production database contents or real media appear in the tests.

## Explicit next blocked acceptance steps

1. Owner-authorized **read-only** source snapshot from live Cloudflare D1 release-row storage after safe schema inspection; the current private D1 collector provides schema only, NOT release rows. Verify a backup, D1 rows, unique constraints, wallet-free quotas and stage semantics before any write/migration.
2. Owner-authorized read-only authentic private owner upload inventory, with validated OAuth and source provenance. The existing adapter remains dormant. A derived report cannot prove a provider's identity or a consistent cross-provider instant.
3. Reconcile known D1 release IDs and timestamps to authoritative YouTube IDs, inspect legacy uploads and incomplete/resumable uploads manually, prove idempotent recovery. Any ambiguous upload remains quarantined.
4. Only then consider separately authorized single-writer durable D1 migration and an owner-approved private upload pilot; include secrets, no-overage, backup/rollback and independent QA gates.

**No production subphase can be claimed complete** from this report. The previously tracked 21 production acceptance subphases across six incomplete major phases remain open, and public PR #4/#5 and private PR #5 remain unmerged DRAFT. Recurring infrastructure budget stays ₹0; no permission exists to use Nirala, connect providers, create paid resources or upload/publish anything.
