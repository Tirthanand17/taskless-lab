# Phase 4F.1 — Actual synthetic SQLite migration and rollback rehearsal

18 October 2026. **Code-only developer rehearsal; NOT live database migration.**

The existing private \`flowminute-control-private/control/ledger.py\` defines a legacy SQLite release primary key \`(release_date, episode_id)\`. The already existing \`autopilot/phase4_offline_ledger.py\` defines the newer target \`(channel_id, episode_id)\`, with unique UTC release slots and immutable media SHA. These are **not equivalent**: a single episode can occupy multiple legacy days; different episodes may have the same UTC slot or media content, and an IST date does not specify an upload instant.

This step **reuses** the Phase 4A in-memory ledger simulator and Phase 4C IST conversion. A typed \`SyntheticLegacyRelease\` record explicitly pins the generated-fixture marker, exact IST date, episode ID, source media hash, and explicit UTC release instant. Inputs with any remote video ID, ambiguous upload state, QA claim, malformed timestamp, non-UTC instant, missing SHA or date mismatch are rejected, not silently "fixed."

\`autopilot/phase4f_synthetic_rehearsal.py\` creates **only a process-local \`:memory:\` SQLite instance** of the existing Phase 4A target and a synthetic legacy key table. It inserts test source rows, tests the real SQLite unique constraints by attempting target inserts under a named SAVEPOINT, optionally injects a failure mid-batch, then **ALWAYS ROLLS BACK every target row even on a clean run**. It verifies that zero target rows and events remain and the synthetic legacy source row count is unchanged, then closes the database. It produces aggregate counts and explicit *false* real-deployment/rights/YouTube authority flags; no SQL, hashes/IDs or fixture rows in result.

Regression tests exercise clean rollback, injected abort, same episode across different legacy dates, duplicate UTC slot, duplicate media hashes, duplicate legacy primary key, missing timing, unexpected remote/QA state, invalid markers and overlarge fixture.

**A passing fake rehearsal is not a reviewed real migration.** Actual 4E needs owner-authorized authenticated read-only D1 and channel-bound YouTube historical readback. Phase 4F production acceptance additionally needs a durable validated backup of actual existing data, versioned non-destructive migration tied to the **real D1 schema**, collision and row reconciliation, explicit owner approval, and a *verified* restore/rollback. Phase 4G remains undeployed; the release controller stays disabled. Neither cloud provider nor paid service has been connected; no token touched; no real YouTube uploads scheduled or published; no laptop/Nirala access.

Existing ₹0/month recurring cloud infrastructure hard limit, PR #4 draft/unmerged, PR #5 separate draft/unmerged. **21 production acceptance subphases across six incomplete major phases remain open.**
