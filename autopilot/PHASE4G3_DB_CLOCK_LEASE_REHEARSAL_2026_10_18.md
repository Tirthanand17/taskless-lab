# Phase 4G.3 — database-clock fenced lease rehearsal, not deployment

**18 October 2026, GitHub draft PR #4. No live Cloudflare or Google connection.**

We added \`claim_db_clock_rehearsal\` to the pre-existing Phase 4A \`OfflineLedger\`. This avoids inventing a second release database, and creates one explicit reference path where **current UTC time comes from the same SQLite database connection inside \`BEGIN IMMEDIATE\`**, not from a request argument. The conditional compare-and-swap \`UPDATE\` requires correct channel, episode, version, nonterminal stage, and an absent/expired lease; it atomically raises the version/fence and logs a matching append-only lease claim.

The original \`claim(...,now_utc=...)\` remains to avoid breaking existing historical test fixtures. It is **unsafe for production** because a caller can supply an arbitrary timestamp, and the whole OfflineLedger class must remain unexposed except in offline tests. The new method has no \`now_utc\` parameter; requests that try to supply it fail. The SQLite VM uses its host system clock, which is **not independently verified real Cloudflare D1 server time**. A production writer must place the database-selected time and conditional mutation into a provider-supported atomic boundary and independently establish cloud writer identity/access and D1 actual schema.

Regression tests use actual SQLite in-memory and two ephemeral parallel connections. They confirm current database timestamp, no arbitrary client clock override, expired historical lease recovery, active lease exclusion, stale version denial, terminal quarantine denial, event-chain compatibility, and no video upload authority. No client-controlled clock has been promoted to trust.

Cloudflare currently documents bound D1 prepared statements and that \`batch\` runs transactional statements. Those docs do **not** prove a production D1 migration, schema, time source or a safe release-authorization mechanism; real implementation requires genuine authorized schema readback and schema-specific acceptance tests. Sources: https://developers.cloudflare.com/d1/worker-api/prepared-statements/ and https://developers.cloudflare.com/d1/worker-api/d1-database/

**Production gates:** Phase 4E live read-only Cloudflare D1 and exact-channel YouTube evidence; 4F actual backed-up, reversible migration; 4G separately owner-approved credentialed single writer with trusted provider UTC, independent readback and strictly guarded upload/scheduling. ALL remain OPEN. Neither this test nor simulated clock is publisher authorization.

**Hard constraints preserved:** ₹0/month recurring budget, no Nirala/laptop access, no new service/provider/OAuth consent, no Cloudflare mutation, no live database migration, no media upload/schedule/publish. PR #4 remains DRAFT/UNMERGED, PR #5 separate DRAFT. Overall 21 production acceptance subphases across 6 incomplete major phases remain.
