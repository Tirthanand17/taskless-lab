# Phase 4E.4 — Complete untrusted YouTube pages and correct SQLite partial-index handling

18 October 2026 — existing GitHub draft PR #4. **No provider connection, live readback or publishing.**

## Two real interface defects repaired

1. The existing `phase4e_readonly_import.py` treated SQLite PRAGMA `unique=1` as **not** unique because it checked `is True`, although SQLite reports an integer. It also did not filter `partial=1` or explicit `WHERE` predicates, so partial uniqueness might be misreported as release-wide protection. The sanitizing importer now accepts only genuine boolean or 0/1 numeric unique flags, excludes known partial/WHERE-constrained indexes, rejects ambiguous partial metadata from promotion and never includes raw SQL/index predicates in its returned redacted shape. The Phase 4E.3 collision audit still treats all remaining index declarations as **untrusted observations, not live verified D1 constraints**. SQLite's official PRAGMA/index docs describe the 0/1 flags and partial-index limitations: https://www.sqlite.org/pragma.html and https://www.sqlite.org/partialindex.html .

2. The existing YouTube-shaped importer supported a **single** page; its own nextPageToken warning made even complete multi-page readback impossible to represent. New `phase4e4_complete_page_intake.py` supports up to 12 explicitly linked request/response pages, validates each supplied `nextPageToken` against the following requested page token, rejects missing/reordered/cyclic pages and repeated video IDs, restricts to 50 items/page and a maximum 500 in this preflight, strips channel titles and private video description, sorts only sanitized metadata, and returns the **exact redacted snapshot shape** expected by the existing Phase 4E.2 signed evidence bridge. No page token is returned. It rejects missing final pages rather than claiming a partial inventory is complete. Google official pagination design: https://developers.google.com/youtube/data/guides/implementation/pagination .

## Security meaning and tests

New `test_phase4e4_complete_page_intake.py` exercises raw integer PRAGMA flags, partial UNIQUE/WHERE exclusions, multipart page chains, wrong and replayed tokens, missing final page, duplicate videos, wrong channel, extra secret-bearing page fields, capacity caps and missing processing details. End-to-end sanitized output is checked against the existing `phase4e2_signed_snapshot_bridge._checked_youtube` schema contract.

**All report flags remain:** `saw_authenticated_provider_request=false`, `migration_authorized=false`, `publication_authorized=false`, zero network calls and zero database writes. Even a structurally complete and signed snapshot is NOT evidence that a real Google account or Cloudflare D1 was accessed. A real Phase 4E acceptance requires owner-approved, authenticated, exact-channel read-only provider access and a separately enrolled trusted capture mechanism, with protected video IDs kept out of this public repository. Historical live D1 rows/video ID reconciliation is not done.

No new provider, plugin, OAuth permission, laptop/Nirala, charge, D1 SQL, real YouTube upload, schedule or publish; ₹0/month recurring limit remains. PR #4 stays draft/unmerged. Production 4E/4F/4G and **21 whole production acceptance subphases across six incomplete major phases** remain OPEN.
