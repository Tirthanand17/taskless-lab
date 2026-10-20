# FlowMinute Lab — strict-only acoustic review across an isolated Unix socket

19 October 2026 | public DRAFT PR #5 | no production deployment

## Implemented

An additional OFFLINE, synthetic-test-only service uses a separate OS process as the sole holder of a pre-provisioned SQLite transcript review ledger, episode source evidence and signed two-role reviewer records. An agent client receives a Unix socket path and an already signed HMAC request but no direct Python coordinator object, SQLite handle, raw acoustic review files or publication endpoint.

Only review.admit is recognized. The command is bounded at 2 KiB, parses UTF-8 JSON with duplicate-field rejection, rejects any extra fields including caller-supplied paths, requires an exact HMAC-SHA256 signature, bounded nonce, specified episode, optional current event compare-and-swap head and expiry within the next 300 seconds. The disposable service's Unix-domain socket defaults to 0600 and exposes no TCP or HTTP server. Unsupported actions such as youtube.upload or release.publish cannot be requested.

A trusted parent loads OfflineReviewBundle, including media / audio probes, signed reviewer attestations and safe evidence paths. A successful authenticated request invokes ONLY OfflineTranscriptReviewLedger.commit_sidecar_bound, which rechecks both signed sidecar file hashes under SQLite BEGIN IMMEDIATE, commits two role-bound file digests in the hash-linked event and consumes the two reviewer receipts atomically. The weaker legacy commit method is intentionally not exposed. The response redacts media/episode identifiers and records voice verification and publication flags FALSE.

## Tests

test_cloud_transcript_review_ipc.py exercises:
- Authenticated strict-only intake, with persisted sidecar digests and no fake speech or publishing approval.
- Tampered signatures, duplicate JSON keys, extra private file paths, unsupported upload/publish routes, stale / too-future expiry and unknown episodes.
- A corrupted evidence file leaving zero journal events, zero used receipts and zero sidecar rows.
- A spawned separate OS process with a mode-0600 Unix socket; the first HMAC-signed command is accepted and replay with the same signed reviewer receipts is rejected across the socket.

## Trust and cost limits

This is NOT a deployed or secure public service: the same test user can still read the SQLite database / evidence files; the test parent fabricates HMAC keys and signed reviewer keys; Accepted command nonces and signed expiries are now durably persisted, integrity-bound to the event hash and checked atomically with the exact reviewer receipts and sidecar digests using the same SQLite host-clock transaction. A command that fails before admission does not consume its nonce and may be retried within its valid expiry; an accepted nonce cannot be re-admitted. The host clock and database remain local and lack independently attested provenance. (a previously accepted reviewer receipt cannot be committed twice, but rejected commands could be retried until expiry). SQLite time is local host time, not externally attested. The pre-provisioned bundle is synthetic and there is no real narrator audio, ASR, human listening or independently trusted reviewer identities. No production ingress, Cloudflare D1 read/write, Google or YouTube OAuth, file upload, publish authorization, video generation or external connection occurs.

The existing 21 production acceptance subphases across six major incomplete phases remain OPEN, including independent speaker and media rights approval, genuine synchronized English/Hindi narration, sustainable free-tier capacity, trusted cloud runtime and authenticated release-state reconciliation. Public PR #4 and #5 remain DRAFT/unmerged. No Nirala, personal storage, OAuth or paid provider touched. ₹0 monthly recurring cloud infrastructure limit stays in force.

## 19 Oct 2026 — durable nonce gate, expiry reconciliation and socket lifecycle

The strict IPC now forwards its authenticated nonce and expiry into the ledger transaction, where the local SQLite host clock independently rejects expired or over-long validity windows (0–300 seconds). The accepted command nonce/expiry is stored in transcript_review_command_nonces (unique nonce and unique event link), included in the canonical chained event digest, and verified at each reopen alongside the original two sidecar hashes. Missing, changed or orphaned nonce rows invalidate the journal. Previous local detached-only/sidecar-only event hashes remain backward-compatible, without retroactive nonce-proof claims.

Five additional adversarial tests cover: accepted nonce survival across reopen plus tampered expiry denial; deleted nonce denial; forged host-clock stale expiry before consuming signed receipts; failed-sidecar retry without nonce consumption followed by durable one-use refusal; and socket 0600 cleanup on direct close. The Unix socket's inode is now captured inside its constructor so manual closes do not leave stale socket paths.

This is a signed-command software rehearsal only. HMAC key custody, remote attested clock, database ACLs, authorized reviewer enrollment, actual human listening, commercial narration rights and cloud deployment are NOT established. No API connection, upload, billing or owner-host computer action occurs.
