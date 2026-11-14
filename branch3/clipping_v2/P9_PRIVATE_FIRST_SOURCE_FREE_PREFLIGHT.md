# CLIVOX V2 P9 — Source-free private-first upload SECURITY preflight (NO YouTube API)

**2026-11-14 implementation:** A closed-rights **no-network, no-credential, no-upload** integration. It is NOT a live YouTube uploader, a dry-run Google request, a scheduled video, a creator permission grant, a real channel OAuth check, or a reliable multi-runner production ledger. The P0/P1 roadmap stays 2/12 = 17%; P9 real acceptance is blocked.

## Why the explicit private setting matters

Official YouTube API sources:
- [Videos.insert](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert) and [Videos resource](https://developers.google.com/youtube/data/reference/rest/v3/videos) require deliberate privacy handling. The current documentation says an omitted \`status.privacyStatus\` on upload can **default to public**. Never rely on account/project-dependent historical private defaults.
- [YouTube revision history (Nov 2, 2026)](https://developers.google.com/youtube/data/revision_history): unverified-project private-only limitation was reversed; omission can default public. This **does not** grant copyright rights or mean our controller may upload.
- [Resumable upload protocol](https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol): after interruptions or 5xx errors, clients may need status requests against the original upload session. A missing HTTP response **does not** prove that no video was created; a session has finite lifetime. Never blindly start a new upload after ambiguity.
- [Videos.update](https://developers.google.com/youtube/v3/docs/videos/update): scheduling a \`status.publishAt\` requires the video still be private and never previously published, with \`status.privacyStatus=private\` explicitly included. The P9 prototype never schedules and fixes the field to \`null\`.

The P9 \`TEMPLATE\` is an **inert conceptual model**, explicitly marked \`INERT_MODEL_NOT_HTTP_REQUEST\` and \`ready_to_send=false\`. It contains only a generic, entirely original synthetic test title and description; no remote endpoint, credentials, creator video, attempt lease, actual schedule, release authorization or HTTP executable. \`status.privacyStatus=private\` is mandatory and \`status.publishAt=null\` means **not scheduled**. Changing those values fails even in a dry run.

## Reuse of actual A6/A7/A8 source modules

Avoid building a second uploader or signer:
- **P8:** \`scripts/branch3_v2_p8_synthetic_unsigned_review.py\` exact P7 synthetic MP4 SHA and byte count, strict P6 editorial and P7 QA JSON-bound unsigned review request, all checklists unapproved. P9 reads only the **existing** \`owner-review-UNSIGNED-synthetic.json\` in the ephemeral test runner, rehashes the exact synthetic file and checks all original P8 false/null fields.
- **A6:** \`scripts/branch3_a6_signed_release.py\` + \`branch3/release/release-policy.json\` hard quarantines all owner releases. No actual owner key is independently enrolled and no genuine final review/rights sign-off exists. P9 invokes the P8 A6 quarantine gate; it does not sign or assert that any party gave consent.
- **A7:** \`scripts/branch3_a7_readonly_youtube.py\` synthetic fixture verifies the *shape* of a CLIVOX-only \`channels.mine\` response, **not real Google OAuth**. The separate A7 owner-only read-only capability is not upload OAuth. P9 checks that it has 0 live requests and cannot authorize uploads.
- **A8:** \`scripts/branch3_a8_private_first_dryrun.py\` verifies the existing private-only schedule fixture, all upload actions off, non-durable empty ledger and absent owner/OAuth. \`branch3/a8/private-cas-policy.json\` is separately required to remain fully offline (no durable global attempt CAS, protected write environment, signed releases or real upload OAuth). We reuse \`reserve_attempt_preview\` and \`reconcile_ambiguous_attempt\` only for **in-memory dry-run demonstrations** of duplicate/unknown-state holds.
- \`scripts/branch3_v2_p9_private_first_preflight.py\` contains **no socket, HTTP, Google client, token, uploader, scheduler or external media path**. \`production_upload_or_schedule()\` always raises, for all inputs.

## End-to-end exact source-free chain

1. Existing read-only GitHub Actions generates six seconds of original synthetic black/white/sine visuals, validates source format/integrity and discovers source-free scene and acoustic events (P4/P5).
2. P5 evaluates those signals against synthetic event timing. P6 emits an original written CLIVOX hook/event/payoff EDL. P7 actually renders a 270×480 H.264/AAC portrait test MP4 and independently verifies real caption pixels, scene/audio cues and codec/format. **This is not a 1080×1920 production video**.
3. P8 recomputes actual MP4 hash/size and P6/P7 JSON hashes, runs a second media inspection, and creates **unsigned** private-runner owner review with all human/licensing/signature/publish fields false/null.
4. P9 reads the **fixed P8 packet filename**, rehashes original MP4 identity, verifies the strict P8 packet and the actual public closed A6/A7/A8 policies, then validates an explicit **private-first, unscheduled, inert** template. It cannot accept real creator footage or any alternative media filename.
5. P9 simulates three outcomes: no attempt, an already reserved **duplicate**, or **unknown remote commit**. The last two are tested with the existing A8 hold/reconciliation helpers. Every case has the same effective decision: **hold, no Google requests, no retry, no upload, no scheduling or publishing**. The in-memory SHA-256 synthetic attempt fingerprint is **not** the real A8 release attempt key because no authentic rights SHA exists.
6. The report contains only static safe flags and counts. It deliberately omits video hashes, creator titles, media paths, contracts, live video IDs, access tokens, upload/session URLs and private inventory. Test MP4 and temporary JSON are discarded when the ephemeral runner ends.

## Security and operational limitations

- Validating a **synthetic API response fixture** is not verifying the actual signed-in CLIVOX account. Actual channel ID must be checked independently against live \`channels.mine\` in a protected, owner-approved environment immediately before any future write; it must exactly match \`UCfPEvy0SefE_5nNlYlY_CyQ\`. Never upload to the older FlowMinute channel by fallback.
- A source-free digest, report or metadata statement cannot substitute for an authentic signed creator commercial reuse grant, separate publisher/game/music/guest clearances, current revocation evidence, real human context review, an independently enrolled owner public key, signed exact-final media release, private source vault, durable rollback-resistant attempt CAS, protected OAuth with narrowly approved upload scopes or full authenticated remote inventory.
- Real YouTube resumable sessions are not created here. Real retry/recovery would need separate, audited private session handling, exact media digest, durable upload-attempt reservation and owner-confirmed remote reconciliation; a hypothetical read-back flag, empty inventory page, timeout or HTTP status must never clear the hold on its own.
- A synthetic checked hash confirms bytes relative to the packet, not authorized provenance, no copyright claims, Content ID or quality. The system must never promote these tests into an automatic creator-video clipping/publishing service.

## Actual production gate checklist (not accomplished)

P2 owner-verified rightsholder prospect; P3 signed current commercial license for the actual clip and underlying rights; P4 private audited media delivery; P5 human-labeled licensed-source candidates; P6 independent original commentary and reviewer decisions; P7 actual 1080×1920 secure edit and playback QA; P8 owner exact-final playback, current rights/revocations and authenticated detached Ed25519 approval; P9 owner-approved protected upload environment and **separate CLIVOX upload-scope OAuth**, private-first insertion and verified persistent attempt ledger; confirmed read-back of the actual private YouTube video before considering any separately signed public schedule.

**None of the real P9 prerequisites are fulfilled in this source-free integration.** No private media/OAuth keys are requested here. No changes to old FlowMinute Branches 1/2.

## Commands and proof

- \`python -B -m scripts.branch3_v2_p9_private_first_preflight --mode closed\`
- \`python -B -m unittest -v scripts.test_branch3_v2_p9_private_first_preflight\`
- Ephemeral CI after P8: \`python -B -m scripts.branch3_v2_p9_private_first_preflight --mode synthetic --scratch "$RUNNER_TEMP/clivox-p5-synthetic"\`
- Workflow \`.github/workflows/branch3-clivox-v2-p5-synthetic-candidates-qa.yml\` reuses the existing **read-only** P5→P8 pipeline and adds P9 negative cases. The source-free P9 path can be called only with fixed generated test inputs; no media artifact uploads.
- Only report this slice as technical CI verified after green feature-PR and independent merged-main jobs. Real phase progress remains **2/12 = 17%**.
