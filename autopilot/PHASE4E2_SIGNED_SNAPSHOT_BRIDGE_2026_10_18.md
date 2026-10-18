# Phase 4E.2 — offline signed sanitized readback compatibility bridge

**18 October 2026 — draft PR #4, no live provider access or migration.**

This is the next layer after Phase 4D (two independent Ed25519 receipt kinds and external public-key trust registry) and Phase 4E.1 (strict minimal-information D1 \`PRAGMA\` and YouTube-owned-video response parsers). The new \`autopilot/phase4e2_signed_snapshot_bridge.py\` **reuses both implementations**; it does not build another release database, generate SQL or connect OAuth.

## Implementation

- Accept exactly the shape of already-sanitized OFFLINE D1 and YouTube observations produced by 4E.1; unknown keys, protected table names/columns, leaked raw SQL/secret-bearing extra fields, wrong video owner, duplicates, miscounted pages, tampered status and exaggerated \`authenticated\` or \`migration_authorized\` flags are refused.
- Recompute SHA-256 over the exact sanitized metadata reports and validate two fresh detached Ed25519 signatures from distinct keys in an **externally provisioned** trust registry, with a request nonce and caller-supplied used-nonce set. The registry and nonce store do **not** exist as trusted deployed services.
- Produce only bounded counts, SHA-256 snapshot fingerprints and explicit blockers. No private video titles, video IDs, consent tokens, raw schema inventories or private filenames in output.
- Identify if an untrusted sanitized D1-looking table *has the right column names for a canonical release candidate*. This is **not** a verified real schema or a migration recommendation. No row data is read or reconciled.
- Fail closed when pagination incomplete, unknown processing or conflicting YouTube schedule statuses occur. These are diagnostics, not verified account history.

## Security and production truth

The exact source of provider-shaped input is still wholly untrusted. A caller may fabricate JSON and sign it with their own key, or even include plausible YouTube video IDs. The Ed25519 check proves only consistency with a key supplied to this verifier, **not** that the authorized owner enrolled that collector or that Cloudflare/Google actually returned the input.

**All results must say:** \`live_authenticated_d1_access_verified=false\`; \`live_authenticated_youtube_channel_owner_verified=false\`; \`migration_authorized=false\`; \`production_ledger_writer_deployed=false\`; \`private_upload_or_scheduling_authorized=false\`; \`public_publishing_authorized=false\`. No deployment, SQL, network or writes.

Phase 4E still requires a separately permitted provider-supported read-only capture of **real** D1 schema + release history and genuine exact-channel authorized YouTube video readback in an owner-controlled trusted environment, including review of trust roots/nonce replay and any sensitive metadata. Only then can 4F draft a reversible schema-specific diff. 4G cannot write until owner explicitly approves migration/rollout. Phase 5 YouTube private pilot requires separate authorization.

Full architecture still has **21 unfinished production acceptance subphases** and 6 incomplete top-level phases (2–7); this addition is 4E.2 staging, not production acceptance. Owner constraints remain ₹0 recurring, no Nirala/laptop, no paid service, OAuth modification, D1 mutation or video upload/schedule/publish. Public draft PR #4 is intentionally unmerged.


## Phase 4E.8 — public index-field parser fail-closed hardening (18 October 2026)

The public 4E.2 standalone verifier previously built `set(ix["columns"])` before checking that all elements were safe string identifiers. Arbitrary JSON nested lists and objects could raise an uncontrolled `TypeError`, even though the separate PRIVATE 4E.7a boundary now rejects them. This public verifier is also independently callable, so private sanitization alone is insufficient.

The branch now validates **every** index column element with `_safe_identifier` and known-column membership before attempting duplicate detection with a set. Regression tests pass malformed nested arrays, objects, null, integers, a protected-looking fake payload, repeated columns, nonidentifiers, and unknown columns directly to the public verifier. These must raise the same fixed `ObservationBlocked` category without echoing any hostile marker.

This is an offline input-validation fix, **not** a provider-origin or cryptographic trust improvement. Both signed-snapshot inputs remain UNAUTHENTICATED even with valid signatures; real D1/YouTube provider evidence, crosswalk, owner consent, reversible migration and single writer stay blocked. No private video/schema values were transferred to the public repo. No paid runner was deliberately started or new workflow added; CI status must be verified separately. Both PRs remain DRAFT/unmerged; budget ₹0/month recurring, no laptop, live API calls, D1 change, upload, scheduling or publication.


## Phase 4E.9 — independent signed-receipt time coherence and video-processing diagnostics (18 October 2026)

In the PUBLIC 4E.2 offline report, the Phase 4D signature verifier already enforces independent signing keys, fresh nonce matching, canonical signed times and a maximum receipt age, but it did **not** compare the two collectors' claimed collection times. The two independently signed snapshots could therefore have been many minutes apart and still form one report. The bridge now checks both *already verified* signed receipt timestamps and refuses any D1/YouTube claimed collection-time difference above **five minutes**. Exactly five minutes is accepted. The result includes only the integer `signed_receipt_claim_skew_seconds`, not timestamps, video IDs, schemas or keys. These timestamps are **collector-reported and cryptographically signed claims**, not authenticated proof of remote provider query execution, a synchronized D1/Google read or server-trusted clock. A malicious enrolled collector can lie about time.

The same existing bridge now counts non-succeeded video-processing claims across all supplied sanitized YouTube history: `processing`, `failed`, `terminated`, or `unknown`. This count is separately surfaced as `youtube_non_succeeded_processing_count` with blocker `NON_SUCCEEDED_YOUTUBE_PROCESSING_OBSERVED`; it does **not** change the meaning of the preexisting `uncertain_metadata` field or equate a historical channel video with the current release's candidate upload. No names, IDs or raw status rows are included. A clean processing count is not proof that channel history is complete or that a specific new upload finished processing.

Adversarial tests synthesize two valid separately signed receipts, one exactly five minutes older and another five minutes plus one second older, proving the latter is rejected even when signatures and independent Phase 4D TTL checks are valid. Additional tests distinguish complete processing from processing/failed/terminated/unknown and verify no video IDs or production authorization escape. The tests use synthetic Ed25519 keys and synthetic provider-shaped records only.

No private collector code, D1 schema or channel record was copied into public Actions. No provider APIs, OAuth, network calls by the module, databases, migrations, production writer, video uploads/scheduling/publishing, new service or laptop access are involved. 4E owner-approved authenticated provider reads and trusted collector enrollment, 4F backed-up migration, and 4G actual D1 writer remain OPEN, along with **21 production acceptance subphases across six incomplete major phases**. Keep both PRs draft and unmerged, and retain ₹0 monthly recurring budget and separate approval requirements.
