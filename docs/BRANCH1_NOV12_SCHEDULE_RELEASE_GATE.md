# Flowminute Lab Branch 1 — 12 November 2026 release operations and BLOCKERS

**Status 2026-11-11:** Four actual original B1r3 H264/AAC videos, SRT captions and covers rendered successfully on GitHub main **run 42966721168** (manual workflow_dispatch; no YouTube). Owner said "continue to schedule" following four media reviews. This means proceed with secure preparation; it does **not** independently attest that the owner watched all exact media through, checked claims, rights and synced captions, nor constitute an Ed25519 signature. These approvals are not fabricated.

## Exact targeted private-first YouTube `publishAt`

| GitHub content/episodes metadata filename | Length | 2026-11-12 IST | Exact UTC `publishAt` |
| --- | --- | --- | --- |
| `nov12_short_a_excel_16digits.json` | ~32s | 11:00 | `2026-11-12T05:30:00Z` |
| `nov12_short_b_ai_fake_citations.json` | ~30s | 13:30 | `2026-11-12T08:00:00Z` |
| `nov12_long_excel_silent_errors.json` | ~241s | 16:00 | `2026-11-12T10:30:00Z` |
| `nov12_short_c_drive_link.json` | ~27s | 20:30 | `2026-11-12T15:00:00Z` |

All times are **proposals, not verified remote schedules**. Source scripts are in `content/nov12_2026/four_video_review_brief.json`. Four metadata files in `content/episodes/` are honest unapproved release candidates and do not claim ownership approval or YouTube state. English narration. Illustrated fictional examples only; owner must check exact spoken claims against primary source citations and ensure appropriate media rights.

## Why this staging workflow is needed

The existing protected `.github/workflows/publish-artifact-youtube.yml` **requires each source artifact to be at the root** with one MP4, SRT and thumbnail name, and only accepts successful `main` run IDs (not PR artifacts). The original four review media live in four nested folders of one GitHub artifact. Calling the publisher with that artifact would fail file layout validation; no scheduling would result.

`.github/workflows/flowminute-b1-nov12-flat-candidates.yml` takes the exact trusted successful **main** four-video owner-review source run, verifies source workflow name/event/branch/result, validates every recorded full-decode MP4+SRT+cover SHA256 (plus source brief SHA, captions, release flags and dates) and creates **four separate flat unapproved media artifacts** in GitHub Actions only. It has `contents:read`, `actions:read`, no YouTube credentials or mutating APIs, no upload, no schedule, and ephemeral file cleanup. Each exported candidate includes provenance with hash-locked file identifiers. It cannot attest creator approval.

After merging the staging workflow on main, an owner or trusted agent can dispatch:

`gh workflow run flowminute-b1-nov12-flat-candidates.yml --repo Tirthanand17/taskless-lab --ref main -f source_run_id=42966721168`

The staging workflow's four artifact names contain the **new candidate job's run ID**. For a future approved upload, select the matching artifact name and its publishing-input run ID; do **not** confuse source run 42966721168 with the packaging run.

## Real external production blockers (confirmed, not inferred)

1. **YouTube OAuth cannot refresh.** Nov 11 protected read-only manual channel check run **42959487882** explicitly reported `B4F6_REDACTED_FAILURE_CLASS=OAUTH_REFRESH_FAILED`, before channel ID verification. The November 11 B1 own-calendar check run **42955587586** also failed at real authorized readback. A syntactically valid JSON secret does **not** imply a currently usable refresh token. Reauthorize the intended **Flowminute Lab owner channel** via Google consent with the correct YouTube Data API scopes; replace `YOUTUBE_TOKEN_JSON` securely in GitHub's **`youtube-production` environment secret**, not in PRs, files, logs, issue comments or this chat. Confirm with protected read-only workflow `flowminute-owner-readonly-channel-audit-b4f6.yml`, ideally after reviewing which account/channel granted consent. Do not repeatedly run mutating publisher with a stale token.
2. **Per-video exact offline owner signature absent.** `scripts/owner_signed_release_b4f1.py` requires a designated independently controlled Ed25519 private signer; protected environment `FLOWMINUTE_OWNER_RELEASE_ED25519_PUBLIC_HEX` must hold the corresponding public verifier. Six explicit owner attestations must be true **only after actual voice playback, captions, rights, factual, final video and publication checks**. Every signed payload must SHA-pin exact MP4+SRT+PNG+metadata bytes, owner channel ID, UTC publishAt, signedAt and expiresAt (<=72h). Four independent signatures and matching `state/approvals/<episode-id>.json` manifests are needed. Never let assistant fabricate viewing/rights approvals or self-enroll a private signer.
3. **Publisher variable `PUBLISH_ENABLED` remains protected.** The manual `.github/workflows/publish-artifact-youtube.yml` must be invoked separately for each approved video from `main` and `youtube-production`, after schedule deduplication/readback. Default `private` until future `publishAt`. It keeps a persistent GitHub no-automatic-retry attempt fence before `videos.insert`, then requires independent owner channel, actual processing, caption serving and scheduling readback before success. A commit/CI success or upload request is not a YouTube schedule.
4. **Exact publication date is imminent.** The first November 12 05:30 UTC slot must still be more than 15 minutes in the future at actual upload dispatch. If owner approval/OAuth is not ready in time, reject the stale slot and request a new future time instead of immediate upload or retroactively claiming scheduled.

## Safe next-owner actions

- Verify the four actual final B1r3 videos, spoken citations, caption timing, copyright ownership and intended channel; give explicit attestations for each exact file.
- Restore the protected OAuth authorization and prove real `channels.list(mine=true)` readback matches `UCCcL9Q_jqVq6LJmnYUSAFZA`.
- Sign all four exact media+metadata+UTC payloads using owner-controlled external signer, with out-of-band key enrollment/verification. Keep private key entirely off GitHub/Actions/ChatGPT.
- Dispatch protected manual publisher for each **candidate artifact** individually and check YouTube `videos.list` private status, `publishAt`, processing/captions state and duplicate receipts. Do not claim publication until external readback.
- Gather Shorts feed *shown*, *stayed to watch*, engaged views and long-form impressions/CTR/first-30s retention after real publication; only then decide whether hooks worked.

**Verified scheduling at time of this document: 0/4.** Do not mark any proposed UTC time as achieved.
