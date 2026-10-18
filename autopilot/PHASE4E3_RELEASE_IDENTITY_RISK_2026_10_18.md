# Phase 4E.3 — Offline release identity collision audit (18 Oct 2026)

Compared existing **code** definitions, not private account data: the current private ledger uses a legacy (release_date, episode_id) SQLite primary key; the draft single-writer ledger proposes channel+episode identity, exact UTC slot, media SHA, remote video ID and upload-intent uniqueness.

New `phase4e3_release_identity_risks.py` accepts the **already-sanitized untrusted** Phase 4E.1 D1-shaped metadata. It counts legacy/date-key tables and canonical-shaped candidate tables, checks the five **declared** uniqueness-column groups, and reports any gaps. It never returns table names, release rows or video identifiers. Synthetic tests cover legacy, incomplete indexes, falsely overlapping keys, multiple tables and forged write/verification flags.

**Critical limit:** Even five claimed unique indexes are NOT verification of global constraints: actual SQL index predicates, partial indexes, live rows, conflicts and provider authenticity are unknown. The older importer does not preserve partial index predicates. Therefore the new audit ALWAYS returns real_global_uniqueness_verified=false and migration_or_writes_authorized=false. Any real migration requires authenticated read-only provider metadata, row-specific duplicate review, separately approved backup/rollback and a trusted production single writer. Do not infer production approval from this staging diagnostic.

This checkpoint creates **no** new ledger, SQL, OAuth or Cloudflare connection. No live D1 reads/writes, provider registration, laptop access, paid infrastructure, YouTube uploading/scheduling/publishing. ₹0 recurring cloud budget and both draft/unmerged PRs remain unchanged. **21 production acceptance subphases remain.**
