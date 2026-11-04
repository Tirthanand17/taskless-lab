# ADR-0020 — B3d4c2b1: atomic one-use inference intent fence (mock-only)

**Date:** 2026-11-04 Asia/Kolkata. **Track:** Branch 2; all work in GitHub, no laptop. **Decision:** implement and adversarially test the *transaction algorithm* with SQLite on ephemeral hosted CI; explicitly do not deploy a real private billing ledger or provider connection.

## Threat model and authoritative research

B3d4c2a PR #22 established cryptographic validity of an owner-signed lease scope but did **not** implement an atomic one-use transaction. Two cloud workers might consume the same request at once, an interrupted HTTP call might have reached the provider even when a client got a timeout, or retry logic might send a second billable request. A mere signed request_budget=1 does not prevent these outcomes.

Current external documentation read on 2026-11-04:

- [SQLite official transaction language](https://www.sqlite.org/lang_transaction.html): BEGIN IMMEDIATE starts a write transaction before checking existing lease IDs; SQLite serializes competing writers on the same database filesystem. FULL synchronous commit and the ordinary rollback journal offer a transaction-level test fixture, not a remotely managed production database.
- [GitHub Actions workflow syntax and runner lifecycle](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax): each GitHub-hosted job gets a fresh runner instance. A local SQLite file on one ephemeral GitHub runner is **not durable between days, other jobs, power losses of the host, other provider workers, or remote deployments**. It is never a safe laptop-off multi-worker production credential/budget ledger.
- [Gemini API billing and project spend caps](https://ai.google.dev/gemini-api/docs/billing/): real free/paid tier is determined by account/project settings; project spend caps are experimental, and accounting may lag by around ten minutes or overrun the cap. **An application-side "zero paid requests" counter or local budget flag cannot guarantee that Google charges zero.** Confirm actual current project account state independently and require owner consent/approvals and account-side safeguards before any API call.
- [Official GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use): never pass protected provider keys or private media to ordinary untrusted pull_request tests. Each test uses ephemeral synthetic signing keys and invented headline references.

## Decision and implementation

- Implement EphemeralOneUseLedger as a local test-only reference implementation with a file-based Python stdlib sqlite3 database inside a GitHub-hosted TemporaryDirectory, not an in-memory or public repository database. Only private 0600 regular files are permitted; reject invalid path/symlink.
- Each reservation rederives and verifies B3d4c2a's detached Ed25519 owner-signed exact planned episode and sanitized research metadata context. The externally authenticated anchor, owner registry, and authenticated agent exclusions are required as arguments. In CI these are intentionally **synthetic** and do not prove a human owner or a real provider billing project.
- Within a **BEGIN IMMEDIATE** write transaction, read the same-day request count and project/owner/provider fingerprint, then INSERT a uniquely keyed lease ID and a uniquely keyed episode ID. The single daily test pack may burn exactly the three planned slots; mixed provider projects/owners are rejected. No raw provider key, free-form prompt, source article or video file is stored. The only transient mock fence token is stored as SHA256.
- **Crucially, commit BURNED_UNCERTAIN_NO_RETRY *before* any mock validation.** Another worker, reopening the DB, receiving an ambiguous timeout, or a process crash cannot reserve that lease again. There is no automatic "expired lease recycle" and no retry backoff sending a second provider call. A private production operator would need an explicit owner-controlled adjudication procedure instead.
- close_mock() requires the original unlogged fence token and the original lease+episode pair, checks its fingerprint with constant-time comparison, and can atomically transition BURNED to either MOCK_DRAFT_VALIDATED_NO_RELEASE or MOCK_DRAFT_REJECTED_NO_RETRY once only. A second completion, forged token, altered result digest or changed scope fails closed.
- evaluate_one_synthetic_mock_script() is a purely local *structural script mock* that validates a caller-provided invented proposal only after consuming the signed lease and records a SHA256 of the proposed script. Invalid mock data also consumes the lease. **No HTTP client, API key, provider transport, actual generative response, cost, scheduler or YouTube uploader is included.**
- inspect() exposes only the normalized status and SHA256 digests, no fence secret or source text. Every receipt has explicit false flags for actual provider inference, real owner/account verification, private cloud ledger, factual rights and YouTube upload/release authorization.
- Unit tests exercise adversarial simultaneous worker contention, independent DB reopen after interrupted reservation, duplicate lease and episode attempts, changing key/project/owner, stale/tampered signature, invalid mock response burning the lease, forged completion token, retained ledger text inspection and no provider client exports. A dedicated Github Actions workflow also checks a full 3-slot burn and no network/publishing via ordinary hosted runners.

## Why this is NOT yet B3d4c2b production completion

The SQLite algorithm passes **one-filesystem transaction semantics** only. All simulated owner signatures are generated during tests; their content hashes of consent and provider tier are synthetic. This repo does **not** have an independent real owner enrollment service, actual Google project free tier determination, account-side billing enforcement, private secret vault, production database/transaction isolation service, private render artifact storage, or multi-day cloud continuity. A transcript hash or a signed receipt does not prove the facts in the source.

The B3d4a/b and B3d4c1 rendered test media remain ephemeral and nonpublishable. A mock provider script cannot be presented as a genuinely new AI-authored video. Never turn on the legacy live provider adapter based on the dry-run receipt; it remains unconditionally disabled except explicit in-process fake transport tests.

## Next steps in order

**B3d4c2b2:** Research and implement a deployment-ready, provider-neutral *private* durable lease interface and one-writer gateway. With explicit owner approval, select a paid/free account configuration, separately enroll the real owner and private cloud database, store consent/terms/legal decisions, apply actual account quota/charge controls and secret custody. Validate fencing and replay prevention across genuinely separate cloud workers. Stop if the account cannot guarantee the user's agreed spend cap. No secrets in GitHub PRs.

**B3d4c2c:** With verified authorized live model, generate three materially distinct complete source-grounded, high-quality scripts for the exact IST slots. Require primary-source provenance, real independent claim-level human reviewer and content/rights/voice license decisions, original episode-specific demonstrations, full playback, correct audio captions, synthetic disclosure decision and signed immutable final MP4/SRT/thumbnail/metadata digests. Do not treat model self-review or template-changing as originality.

**B4:** After separate YouTube OAuth approval and private durable storage, implement fenced uploader with privacyStatus=private, actual remote processing/SRT/thumbnail readback and verified future scheduling. **B5:** 21 actual unique source/rights-reviewed videos in seven consecutive days with the laptop fully off, no duplicates or charges outside the agreed cap.

Branch 1 assisted YouTube scheduling remains separate. B3d4c2b1 has no upload or publish permissions.
