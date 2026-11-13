# Clivox A8 — Private-first scheduling and upload idempotency (dry run)

**Status:** Engineering prototype only. No real Clivox owner OAuth, licensed source clip, finalized signed release, protected production environment, atomic persistent ledger, remote inventory reconciliation, YouTube upload or schedule.

## Goals and official API constraints
- `videos.insert` on YouTube must explicitly include `status.privacyStatus=private` (never rely on an unspecified default).
- `status.publishAt` may only be set on a **never-published, currently-private** video. A past timestamp can publish a video immediately; the planner requires a strictly future UTC time with a 30-minute margin.
- Idempotent uploads require a **durable attempt reservation and remotely reconciled video ID**: an HTTP timeout can occur after YouTube accepted the video. Never interpret a missing HTTP response as proof no upload occurred.
- YouTube only allows uploading after separate owner authorization, and the Clivox channel ID must match `UCfPEvy0SefE_5nNlYlY_CyQ` every time.
- Media rights, exact signed render approval, and Content ID checks remain separate from scheduling API validity.

Primary sources:
- https://developers.google.com/youtube/data/reference/rest/v3/videos
- https://developers.google.com/youtube/v3/docs/videos/insert
- https://developers.google.com/youtube/v3/docs/videos/update
- https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

## Implemented (all NO-SIDE-EFFECT)
- `scripts/branch3_a8_private_first_dryrun.py`: UTC schedule preflight, explicit `private` assertion, 30-minute safety margin, deterministic SHA256 attempt key for exact Clivox channel + release ID + video/metadata/rights digests.
- In-memory reservation preview demonstrates duplicate and ambiguous attempt denial. It **cannot** serialize network upload attempts, guarantee atomicity, call YouTube or reconcile remote state.
- `scripts/test_branch3_a8_private_first_dryrun.py`: future/past/tz cases, wrong channel, fake media rights/owner signature, public visibility, duplicate attempts and ambiguous transport response.
- `branch3/a8/fixtures/private-first-dryrun.json`: a **synthetic November 20, 2026 future date** with all approvals false; its `simulated_now_utc` is fixed November 12, 2026 for reproducible unit tests and is **not a live scheduling proposal**.
- `branch3/a8/fixtures/empty-upload-ledger.json`: intentionally empty with non-durable storage flags.
- `.github/workflows/branch3-clivox-a8-dryrun.yml`: GitHub-hosted read-only fixture QA, no OAuth secrets, no media and no YouTube requests; publishes only public-safe JSON report.

## Added 2026-11-13 — transactional one-runner atomic ledger rehearsal

[Transactional SQLite attempt-ledger engineering rehearsal](ATOMIC_ATTEMPT_LEDGER_REHEARSAL.md) now validates real atomic unique reservations and ambiguous-state hold using throwaway GitHub-hosted runner SQLite, with parallel-writer adversarial tests. This is **not cross-run durable storage** and no YouTube/Google media write or rightsholder verification is enabled. The original in-memory dry-run and its strict quarantine remain unchanged.

## Added 2026-11-13 — cross-run global SHA-CAS contract (still offline)

[Private global upload attempt ledger CAS contract](PRIVATE_CROSS_RUN_CAS_PROTOCOL.md) now models a bounded append-only journal in an owner-selected private GitHub repository, validates each global release/media uniqueness event and GitHub Contents byte/SHA integrity, and simulates concurrent conditional updates and unknown-write outcomes. **This is only a fixture-driven contract: no private store is provisioned, no live GET/PUT exists, no true distributed lock has been proven, and media/YouTube uploads remain impossible.**

## Added 2026-11-13: protected real private upload-attempt ledger READ-ONLY code

[Owner-only A8 private attempt ledger readback setup](OWNER_PRIVATE_ATTEMPT_READBACK.md) now performs three fixed GitHub API GETs for the private repository, owner-only collaborator list and exact canonical upload attempt journal file, then verifies its blob SHA, strict full event replay and owner-supplied prior anchor. The private genesis file **actually exists** with zero events; this GitHub Actions job **has not been run with a dedicated read-only token**, and its protected environment has zero such secrets. It never performs a remote update or clears an ambiguous upload. The production single-writer CAS, independently durable checkpoint and YouTube upload OAuth are still unconfigured.



[Owner's uploads inventory runbook](OWNER_UPLOAD_INVENTORY_READBACK.md) describes the protected manual-main read-only workflow which paginates Clivox's uploads playlist within a strict 1000-item bound and verifies each returned video status in batches. Synthetic CI prevents wrong-channel, missing/duplicate or incomplete results. **No live OAuth consent or remote inventory exists yet**, and a metadata snapshot alone cannot permit an ambiguous upload to be retried.

## Target production API transaction (not implemented here)
1. Check current verified creator-granted commercial rights and valid signed A6 release over exact media SHA/metadata SHA/rights receipt/channel/schedule.
2. Independently verify uploader has **new, separately authorized Clivox OAuth**, never FlowMinute Lab's token. Require a protected owner-reviewed GitHub environment with strict branch restrictions.
3. Reserve a unique release ID in an atomic durable ledger with a compare-and-swap lease and expiry/recovery protocol before beginning resumable upload.
4. Run one private-first YouTube insert with explicit `status.privacyStatus=private`; record resumable upload ID and attempt status before network calls; limit retries safely.
5. On errors/timeouts, obtain authenticated remote inventory/readback and reconcile before retry. Do **not** automatically create another video when the result is ambiguous.
6. Wait for real processing/status checks, review Content ID/copyright risks, and confirm the remote video has never been public. Don't assume private checks prevent later claims.
7. Only then set a strictly future UTC `publishAt` and verify the actual `status.privacyStatus`/`publishAt` fields through authenticated API readback. An owner-signed timestamp change requires a new signature.
8. Persist verified remote video ID and schedule readback in the release ledger. Later revisions/takedowns must be owner-approved.

## Safety limitations
- **No production uploader** exists in A8 dry run. `perform_upload_or_schedule()` always raises a blocked exception.
- A valid UTC timestamp is not a real scheduled YouTube video.
- A hash or fake JSON boolean is not a release signature or source permission.
- A dry-run list of in-memory attempts is not an atomic lock across GitHub Actions runners.
- The Clivox channel still has **0 verified creator licenses and no uploaded videos from this project**.
- Branches 1 and 2 remain paused and untouched.

## Next work
Before A8 can become live: owner Clivox OAuth setup (A7), authenticated uploader-specific scope in a separately protected environment, actual rights-granted source and private media vault (A2/A3), real voice/render/human QA (A4/A5), enrolled owner signing key (A6), and atomic persistence with authenticated remote readback.
