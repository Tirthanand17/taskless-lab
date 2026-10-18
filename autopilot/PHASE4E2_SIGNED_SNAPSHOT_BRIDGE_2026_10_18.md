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
