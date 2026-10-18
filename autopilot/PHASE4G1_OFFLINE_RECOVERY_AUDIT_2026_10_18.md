# Phase 4G.1 — Recovery integrity audit, EXISTING offline writer, no deployment

**18 October 2026. Source-only, local-fixture checks; nothing is published or migrated.**

The legacy private ledger and the public Phase 4A in-memory SQLite simulation both lack live authenticated server-clock and provider-attested recovery. Phase 4A already has atomic leases, fencing, append-only events, upload-once state and no-blind retry. **Do not build a competing ledger.**

New \`autopilot/phase4g_recovery_audit.py\` reads ONLY an explicitly created \`OfflineLedger(offline_test_only=True)\` instance. It checks up to 256 releases/4096 event records inside a consistent SQLite snapshot, reconstructs every valid event version and stage, and rechecks original media hash, planned UTC slot, upload intent, YouTube ID, no repeated upload/schedule intent, fencing leases and terminal states. It returns counts only, and **no episode, media, video, user or credential values**.

The audit never calls an external service, writes rows, executes upload/schedule operations, or reports a simulator result as a verified remote status. In particular:
- An \`upload_uncertain\` remains uncertain after a crash or lease takeover. **No repeat upload**; an independently authorized exact-channel YouTube readback and recovery design are needed.
- A \`schedule_uncertain\` likewise never permits repeat scheduling.
- Caller-supplied \`now_utc\`, \`authenticated=True\` and \`playable=True\` in the test simulator have **zero security value** in production. Phase 4G deployment needs server-owned time, a trusted provider reader/collector, fenced atomic D1 updates and strict owner permissions.
- A fabricated row/value or event-chain mismatch fails closed; append-only event triggers protect the simulator but not an externally managed D1 provider.
- A clean \`public_verified\` reconstruction means only that a simulator accepted caller-supplied booleans; the audit NEVER claims a live published video.

Real SQLite regression tests check all critical states, expiry/reclaim, injected mutation of release stage/media/video/intent/version/fence/lease owner and fake orphan rows. They do not touch real user or Cloudflare database files.

**Exit blocker:** Phase 4E requires owner-approved live read-only schema and exact YouTube channel history; Phase 4F needs a backed-up schema-specific migration and rollback; Phase 4G needs a separately owner-approved authenticated D1 single writer with protected signing roots and trusted UTC. Still **21 production acceptance subphases** and **6 incomplete major phases**, public PR #4 remains DRAFT. Budget ₹0/month recurring, no laptop/Nirala, credentials, new service, cloud production writes or YouTube release.
