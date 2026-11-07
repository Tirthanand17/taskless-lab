# ADR-0081 — B4e9 fail-closed durable GitHub attempted-upload tags

**Date:** 2026-11-07 IST | Legacy/manual publisher hardening for the Branch 2 transition. No autonomous YouTube releases enabled.

## Observed bug, before this change

In `scripts/publish_youtube.py`, the old `*.pending.json` was created **only after videos.insert returned a video ID**. If YouTube accepted an upload but the process lost the response, the runner might end with no pending checkpoint. A later manual run could mistake that ambiguous result for a never-attempted upload and create a duplicate.

The existing GitHub Actions manual workflow is gated by `vars.PUBLISH_ENABLED == 'true'`, main-only manual dispatch and a `youtube-production` environment. The old direct-publication workflow remains disabled. This change does NOT set the variable, supply YouTube secrets, invoke the job or approve any media.

## Safer ordering

1. Keep all existing human approval, exact approved MP4 SHA, captions language, channel, and future `private` schedule preflights.
2. **Before any `videos.insert`**: create a local `*.pending.json` via exclusive O_CREAT|O_EXCL with mode 0600 and fsync; checkpoint is marked `POSSIBLY_SENT_NO_AUTOMATIC_RETRY`. An error does not erase it.
3. Reserve two GitHub **public digest-only tag references** using the official [Create a reference endpoint](https://docs.github.com/en/rest/git/refs) and the scoped GitHub Actions `GITHUB_TOKEN`: one hash for canonical (channel,episode); a second for canonical (channel,publishAt UTC). The API only permits a new ref, never updates/replaces an existing one in this code. Existing ref (422), conflict (409), transport timeout, 403 or any unrecognized response stops the upload **without retrying a GitHub POST or making videos.insert**. If only the first ref is confirmed, keep it reserved and refuse.
4. Only after both `201 Created` responses match the intended refs and `GITHUB_SHA` may the pre-existing (already approved) manual YouTube upload logic run. On successful video ID, overwrite local pending with a recoverable ID checkpoint, then verify private schedule, then make final receipt. The GitHub tags are never removed automatically.

**Privacy:** GitHub tags are readable in a public repo; hash names contain no raw channel ID, episode ID, source title, video, voice, notes, tokens or URLs. Predictable values may be guessable from hashes. Never place Google OAuth or resumable session URLs in tag names/logs. The GitHub token is available only to this already privileged manual job and is not persisted in any receipt.

## Limitations and remaining work

- GitHub refs can be intentionally **deleted or altered by repository administrators**. An account-wide durable protected database with write-once reservation and independently audited recovery is still the appropriate production design; the tags are a conservative repo-scoped cross-run guard, not a mathematical exactly-once guarantee or substitute for a protected ledger.
- GitHub API success/ref creation is not YouTube upload success; no repeated insert is safe after ambiguous network response. No active resumable session repair is implemented in the legacy publisher; B4e8 only models the protocol offline.
- Runner `*.pending.json` is local to a GitHub job, so an `if: always()` step still attempts to commit a recovery checkpoint to the repo. The tag refs remain when the receipt push fails or the runner dies.
- These attempts reserve **before** any insert, so some failed preflight/network/service incidents may permanently block a slot until careful authenticated owner-side reconciliation. This deliberate tradeoff is safer than blind duplicates.
- No content/fact/rights owner approval has been independently verified here; an editable approval manifest with five booleans is not an authenticated owner signature. Real production requires signed approval, protected persistent storage, actual YouTube OAuth, independent owned-channel readback, rights clearances and a 21/21 release acceptance.
- Current YouTube documentation (Nov 2, 2026) allows unverified projects' uploads to default public when `privacyStatus` omitted, so the existing explicit private-before-`publishAt` barrier is preserved: [revision history](https://developers.google.com/youtube/data/revision_history).

## Tests and rollout

- Offline injected GitHub REST `201`, duplicate `422`, timeout after first ref, scope/identity mismatch, malformed hashes, no remote request when invalid.
- OS-exclusive local crash marker test, refusal to overwrite, source-order inspection, GitHub workflow environment gate.
- Preflight workflow remains **NO SECRETS / PUBLISH_ENABLED=false** for all PR CI. No tag refs or YouTube API requests are made by these tests.
- Only consider enabling future real publication after independent owner-controlled live review, immutable factual and licensing approvals and protected production credential/state architecture.
