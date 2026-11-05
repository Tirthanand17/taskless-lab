# Phase 4H — offline shadow release backup and single-writer lease rehearsal

19 October 2026 | public DRAFT PR #5 | no live Cloudflare D1/YouTube access

## What these modules really do

1. autopilot/cloud_release_backup_rehearsal.py accepts a pre-supplied legacy six-column private-shape release record set, validates stage/date/episode/media SHA/video ID/time and refuses duplicate identities. It copies the bounded set of up to 500 records into one SQLite :memory: database. The SQLite online backup API backs that database up into a second, independent SQLite :memory: connection. Source is closed, restored records are re-read and verified by SHA256 plus complete tuple equality. Both disposable SQLite databases are closed. THIS DOES NOT BACK UP REAL CLOUDFLARE D1 OR THE PRIVATE LEDGER EVENT HISTORY.
2. autopilot/test_cloud_release_backup_rehearsal.py adds 12 synthetic tests for restored set parity, row reordering, deletion/addition, altered stage/media/video/time, ambiguous upload_started, duplicate media IDs, empty history, malformed rows, and memory-only SQLite connections.
3. autopilot/cloud_single_writer_lease_shadow.py models one temporary lease record shared by TWO distinct SQLite connections in mode=memory&cache=shared. A BEGIN IMMEDIATE claim increments a monotonic fencing epoch, denies conflicting owners and checks expiry. The synthetic old owner cannot reuse its stale epoch after another writer takes over. THIS IS NOT A DEPLOYED DISTRIBUTED LOCK OR A D1 TRANSACTIONAL LEASE.
4. autopilot/test_cloud_single_writer_lease_shadow.py adds 8 synthetic tests for conflicting ownership, monotonic takeover, stale/expired worker denial, bad clock/duration/owner/epoch, re-acquisition after rollback and memory-only connection URIs.

Outputs report only aggregate counts and generic blocker codes. No original channel ID, video ID, episode name, SHA, timestamps or private metadata are output. All flags for REAL database backup, cloud durability, single writer deployment, provider identity, event-log recovery, ownership consent, safe upload retry, migration, uploading, scheduling and public publishing remain FALSE.

## Why this does not close production recovery acceptance

The existing private legacy control/ledger.py has a caller-supplied durable_volume_verified flag, but no independently verified persistent volume or production cloud lease. A local SQLite shared-memory lease cannot be relied upon across Cloudflare D1/Workers processes, regions, network partitions, clock skew or external YouTube upload transactions. Claiming a lease before videos.insert does not prove the remote upload failed when its HTTP response was lost; no automatic replay is authorized.

The in-memory backup does not contain D1 historical events, verify Point-in-Time Recovery, backup retention, source provider authentication, an independently restorable production copy, or live YouTube state. A separately authorized isolated target and provider-specific backup/restore verification would be required. No actual D1, OAuth or channel data were accessed.

## Private integration and testing boundary

The private DRAFT branch now contains control/phase4h_private_shadow_restore.py, which accepts a pre-collected private D1 release capsule and calls the public in-memory rehearsal. All output is redacted and unable to authorize production. Its 8 mocked contract tests are committed but NOT executed because private Actions quota is unapproved. Public CI verifies the real synthetic SQLite roundtrip and lease model; it DOES NOT execute the private bridge.

These changes are code/QA safety progress only, not an approved production acceptance subphase. Previously tracked 21 production acceptance subphases across six incomplete phases remain OPEN. Approximate software progress ~45% and real autonomous readiness ~20%, unchanged. No Nirala laptop access, new service, external provider connection, D1 production write, OAuth change, upload, publishing or paid resource. Monthly recurring infrastructure authorization stays ₹0.
