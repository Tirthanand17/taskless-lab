# FlowMinute Lab Phase 4A — offline single-writer ledger protocol

**17 October 2026. Implemented on a review branch; NOT a production D1 migration, Cloudflare deployment, OAuth repair or YouTube upload.**

## Why

The existing private Cloudflare D1 metadata store and encrypted OAuth grant must remain untouched until its tables, indexes, recent release receipts and authenticated YouTube state are inventoried. The private SQLite release ledger, public local calendar ledger and future D1 controller must **not** act as multiple independent publishing authorities.

This change implements a **test-only** SQLite reference protocol in `autopilot/phase4_offline_ledger.py`, with regression cases in `autopilot/test_phase4_offline_ledger.py`. Constructor requires `offline_test_only=True`. These `phase4_*` tables are **not production migration SQL** and are not created in Cloudflare D1.

## Protocol invariants covered by software simulation

- Exact FlowMinute channel `UCCcL9Q_jqVq6LJmnYUSAFZA`, stable episode identity, immutable final media digest, canonical UTC second precision.
- Unique schedule instant across every format, unique video ID and unique upload intent; same episode/same content is a read-only idempotent reservation.
- Stage order: planned → research_verified → script_verified → media_qa_passed → upload_uncertain → remote_private_verified → schedule_uncertain → scheduled_verified → public_verified, with terminal quarantine.
- Local media review stage requires a separate immutable **digest claim**; that digest does not authenticate a human review or demonstrate legal licensing.
- Every mutating step needs a compare-and-swap version, an unexpired single-owner lease and monotonically increasing fencing token. On expiry, a second worker can claim the row; the old worker cannot continue.
- Append-only stage/lease event log with blocked SQL UPDATE/DELETE, plus local atomic SQLite transactions.
- Intent recorded **before** any hypothetical upload or schedule operation. Uncertain crash/timeout states cannot be retried as a second upload/schedule attempt; they require independent reconciliation first.
- Remote private, scheduled and public stage simulation demands exact video ID, channel/privacy/processing/public evidence *arguments*; these arguments are fakeable by a caller and are **not** trusted remote observations in this offline library.

## Test evidence

`python -m unittest autopilot.test_phase4_offline_ledger -v` ran **18/18 locally** on disposable SQLite fixtures. Coverage includes collision rejection, media immutability, bad timezone, stage skipping, missing review digest, stale version, lease race, fencing, upload ambiguity, wrong hash, incorrect video owner/privacy, exact schedule mismatch, public playability, quarantines, event tamper, and reopen after crash.

Repository CI workflow `.github/workflows/quality.yml` triggers on all pushes/PRs and runs the full pytest suite. Record the live CI run URL and actual result once known; a local pass does not imply a GitHub CI pass.

## Production migration is explicitly NOT authorized by these tests

Before adapting this to the existing real D1:

1. Inventory Cloudflare D1 read-only with owner-approved authenticated access. Do not dump encrypted OAuth ciphertext, tokens or unrelated private media; do not ALTER existing tables.
2. Read the exact YouTube channel-owned IDs/processing and schedule snapshots with authorized read-only credentials; reconcile legacy private SQLite, current D1 and GitHub drafts without overwriting or backfilling guessed states.
3. Draft a schema compatibility matrix and a rollback proof. Never run the reference `CREATE TABLE` statements blindly: existing production objects/history may conflict.
4. Specify D1-supported atomic transactions/conditional writes and authenticated trusted-clock lease issuance, not caller-controlled `now_utc`. Prevent untrusted workers from asserting `authenticated=True` without verifying signed/provider-bound readback.
5. Establish a single credentialed writer in the **existing** protected Cloudflare controller, controlled by separate release authorization. Preserve the immutable YouTube ID, schedule, media hash and event chain.
6. Demonstrate no-charge, policy-compliant, private long-video storage and full media QA; separately resolve durable OAuth and obtain approval before any private upload pilot.

**Safety:** `publishing_enabled=false`, `FM_UPLOADS_ENABLED=0`, `FM_SCHEDULING_ENABLED=0`. No Nirala/desktop use. ₹0 monthly. No third-party connection, charge, production D1 write, actual video creation, upload or scheduling in this phase.
