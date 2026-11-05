# Major Phase 4: D1-shaped one-way canonical upload reservation

20 October 2026. Existing draft PR #5. Source and synthetic tests ONLY; no production Cloudflare/YouTube mutation.

Uses exact canonical releases and release_events tables with Cloudflare D1 prepare/bind/run shaped calls. The live switch is hard-disabled. The synthetic fixture marker is not a real authentication boundary. No Worker HTTP/cron entrypoint or external API.

Admission requires a verified nonpartial UNIQUE (release_date,slot_ist) index named ux_release_date_slot, tested by fixed read-only PRAGMA statements. Previously observed production idx_release_date_slot is nonunique, so actual production must HOLD until independently approved migration and backup proof.

A single conditional UPDATE checks exact channel/episode/UTC slot/media SHA, MEDIA_QA_PASSED and youtube_id IS NULL, then changes state to UPLOAD_STARTED. Only after meta.changes is exactly 1 may a guarded INSERT SELECT attempt an audit event. They are two separate statements and NOT an atomic two-table transaction. Any unknown acknowledgement or audit-event error leaves UPLOAD_STARTED sticky and requires owner review; NO reupload/retry/unsafe compensation is authorized.

Cloudflare documents atomic batch transactions but does not explicitly guarantee cross-statement SQLite changes() semantics. This candidate does not rely on that unverified assumption. The event append is guarded and no actual upload can occur. Production D1 concurrency/fencing needs separate nonproduction provider-native validation.

Offline regression suite: 15 Node mocks, Python exact exported SQL executed against disposable SQLite, and a Python-to-Node bridge included in pytest. No real D1 calls, Worker deploys, OAuth, YouTube uploads, spending or database schema modifications.

Production requirements remain: recovered tested backup, all real Cloudflare writers and cron/route audit, hard zero-cost controls, owner-approved index/backfill, encrypted renewable OAuth, authorized one-video private cloud pilot and full Nirala-off acceptance.

Major-phase acceptance unchanged: 2/8 = 25%. Cloudflare reference: https://developers.cloudflare.com/d1/worker-api/d1-database/