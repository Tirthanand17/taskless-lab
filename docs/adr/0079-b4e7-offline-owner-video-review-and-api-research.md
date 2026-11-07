# ADR-0079 — B4e7 local review player and YouTube private-first research

**Date:** 2026-11-07 IST. **Branch 2, synthetic originals ONLY.** No actual YouTube publishing, owner review or rights approval claimed.

## Verified reason for this increment

B4e3 already retains three H.264/AAC MP4s for **one day only** when a human explicitly dispatches the default-branch GitHub workflow with `retain_rehearsal_review_artifact=true`. B4e5 adds a SHA256-bound, 17-scene (4/9/4) unfilled worksheet. B4e6 validates manually filled notes but no player was provided, leaving owner review cumbersome. Synthetic practice videos do not automatically become factual news.

## Implementation: offline, locally opening media

The existing explicit one-day review package now contains `OPEN_LOCAL_REVIEW_DASHBOARD.html`. This self-contained HTML lists the three **canonical relative MP4 filenames**, three SHA256 digests, real local video controls, each film's ten checks, scene-by-scene statuses and capture-from-video timecode buttons. Reviewer may download a *private* JSON copy for `python -m autopilot.review_worksheet_validator_b4e6 --manifest REVIEW_ONLY_NO_PUBLISH.json --worksheet FLOWMINUTE_PRIVATE_HUMAN_REVIEW.json`.

- No CDN, external imports, scripts, fonts, trackers, AJAX, fetch, iframe or web server. Strict CSP includes `connect-src 'none'`.
- Source article text, research headlines/URLs, account IDs, credentials, model weights, voice files and raw SRT never enter the package.
- The only writable browser output is the user's local JSON download. Its factual, rights, release and human-independent approval flags remain **false**. Review status is self-reported and cannot prove physical playback.
- The Python generator executes B4e6 structural validation, requires a blank 47-item worksheet, and escapes `<`, `>` and `&` in inline data. The package allowlist now consists of exactly 3 original MP4s, 2 safe text/JSON manifests, 1 blank worksheet and 1 local player.
- Scheduled/push/PR runs still **cannot retain** media. The optional `workflow_dispatch` flag defaults false. Clean all ephemeral files `if: always()` as before.
- Opening `file://` HTML may be subject to browser media sandbox differences; the three MP4 files must remain in the same extracted directory. Actual owner watch has not happened and must still be recorded manually.

## Research affecting future production publishing (NOT implemented by this PR)

As of the [YouTube Data API November 2, 2026 revision](https://developers.google.com/youtube/data/revision_history), videos inserted by unverified projects are **not automatically forced private**; when `status.privacyStatus` is missing, the API may default to **public**. The future authenticated gateway **must explicitly set `status.privacyStatus=private`** before any upload, and must bind exact future `status.publishAt` to the intended channel and IST slot. The [videos.update reference](https://developers.google.com/youtube/data/reference/rest/v3/videos/update) warns that updates to `status` can reset omitted properties; reconstruct and independently read back the full status if ever implementing updates.

The [resumable upload protocol](https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol) requires preserving one existing session across transient failures and querying received ranges rather than initiating another `videos.insert` after ambiguous responses. The repo's B4a mock-only contract and B4b PostgreSQL **CI-only** attempt fence demonstrate intended idempotency but **are not live production infrastructure**. New credentials, persistent protected state, independently authenticated owner readback, actual factual/source and rights approvals, private first encode verification, caption/thumbnail success and seven-day 21/21 production proof remain missing.

The [2026 granular quota system](https://developers.google.com/youtube/data/getting-started) uses method-specific `videos.insert` and `search.list` buckets; do not rely on the older blanket 1600-unit-per-insert assumptions.

## Acceptance boundaries

1. Exact-head CI: Daily Foundation tests incl. B4e7, repository-wide Content Quality, Cloud Scout, H.264/AAC smoke.
2. Merge only when checks pass. On main, normal push/daily runs must still emit **no optional review artifact**.
3. The owner independently runs `workflow_dispatch` with explicit opt-in on `main`, downloads and opens the exact MP4+HTML files, watches and listens, notes 17 scene defects and 30 checks, exports JSON and validates via B4e6.
4. Even perfect subjective review **does not** authorize factual publication. Zero live uploads/schedules from this change, and 0/21 independent unattended seven-day evidence.

