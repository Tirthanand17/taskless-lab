# Phase 4G — Two-round offline D1↔YouTube drift screening

19 October 2026 | public draft PR #5 | pure software, NOT a live provider read

## Problem

A bounded paginated D1 SELECT and independently paginated authenticated YouTube owner inventory are two unrelated read operations; neither returns an atomic cross-provider snapshot. A channel upload, schedule change, processing transition or ledger write can happen *during* a read. A single ID-matching snapshot is insufficient for safe durable cloud migration or duplicate-upload recovery.

## Implementation

autopilot/cloud_release_double_read.py adds compare_private_release_read_rounds with two sets of **private-shaped, caller-supplied** release-record tuples and owner upload-inventory reports. It calls the previously implemented reconcile_existing_private_shapes for BOTH rounds with local_ledger_snapshot_complete=False, so schema, channel identity, stage, media/video IDs, false authority claims and timestamps remain rigorously checked.

The comparator keys local rows by release-date and episode, and owner video rows by YouTube ID. It counts independently added, removed and modified release records and owner-video statuses, ignoring incidental page/item ordering. Unchanged bytes mean ONLY *two observationally matching, untrusted samples*, NOT authoritative history, atomic D1 read, authenticated Google consent or upload approval.

Permanent blockers identify missing independent source provenance, D1 backup/restore, exclusive durable writer and cross-provider atomicity. Observed drift adds named D1/YouTube change blockers; an upload_started in either pass adds a no-automatic-retry blocker; other mismatches, incomplete remote states and unmatched channel videos remain quarantined.

The output includes only aggregate counts, generic blocker codes, zero declared network calls, zero DB writes and permanently false source-verification, backup, writer, migration, upload, retry, scheduling and publishing flags. No channel IDs, private episode IDs, raw media hashes, OAuth values, inventory rows or source details are emitted.

## Public regression and validation

autopilot/test_cloud_release_double_read.py contains 13 synthetic tests: matching reads without authority, D1 stage/hash changes, owner privacy/schedule changes, added/removed releases, added/removed owner videos, reversed owner inventory ordering, unchanged but ambiguous upload_started, empty history, forged channel/publishing permissions, and invalid/duplicate second passes.

At exact public code commit effca1ddca734fa1d01b841cb6440a5568f4cd76, full Content Quality Gate succeeded: 909 passed, 2 skipped, 571 subtests passed (https://github.com/Tirthanand17/taskless-lab/actions/runs/39207144203). Independent Agent Architecture and Cloud Scout passed. Heavy media QA deliberately skipped on draft. No live Google/Cloudflare requests were made.

## Private bridge and remaining work

The private control/phase4g_private_double_read.py in private draft PR #5 consumes two already-collected in-memory D1 snapshot capsules and two owner inventories. It calls the existing private Phase4F safety bridge for each round before invoking this single PUBLIC pure comparator. A strict negative privilege interface plus arithmetic checks and private redacted status are enforced. It performs NO live data collection.

Ten private mock contract test methods are committed, but NOT run because private Actions quota remains unapproved. They do not count toward the public 909 tests.

Two agreeing reads can still miss concurrent or adversarial changes; there is no independent provider origin proof, D1 page-level snapshot isolation, real remote samples, authenticated owner inventory, D1 backup/restore drill, cloud single-writer/lease or OAuth durability proof. Each must be independently established before an owner-approved live migration or private publishing pilot. No production subphase was closed.

The ₹0 recurring infrastructure authorization remains intact. No Nirala/laptop, new service, live D1 access, OAuth change, media creation, YouTube upload or publishing. All 21 acceptance subphases across six incomplete major phases remain open; software ~45% / real autonomy ~20% unchanged pending actual externally evidenced milestones.
