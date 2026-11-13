# CLIVOX A8 — Owner-only read-only uploads inventory (bounded, no publishing)

**Implemented 2026-11-13:** GitHub-hosted manual/main-only YouTube **READ-ONLY** uploads playlist pagination and authenticated `videos.list` status verification. This is code and synthetic CI; **no real Clivox Google OAuth secrets are configured, and no live inventory run has occurred**.

## Why it is needed

A8's upload idempotency ledger must never infer from an ambiguous HTTP response that no YouTube video was created. The previous A7 owner bridge checked only the **first page** of the uploads playlist. This implementation checks **every returned page within a strict bound** (maximum 20 pages, 50 video IDs per page, 1000 total), and fetches those video IDs in separate `videos.list(part=snippet,status)` batches to validate authenticated channel ownership, visibility and private `publishAt` metadata.

Official Google documentation:
- [Channels: list](https://developers.google.com/youtube/v3/docs/channels/list): `mine=true` yields the authorized channel and uploads playlist.
- [PlaylistItems: list](https://developers.google.com/youtube/v3/docs/playlistItems/list): follow `nextPageToken`, with up to 50 results per page.
- [Videos: list](https://developers.google.com/youtube/v3/docs/videos/list): request `part=snippet,status&id=...` for video details.
- [Videos resource](https://developers.google.com/youtube/v3/docs/videos): the `status.privacyStatus` and `status.publishAt` fields describe publication state.

The code refuses missing pages, repeated page tokens, duplicate or missing video IDs, mismatched Clivox channel IDs, malformed privacy state, missing status records and any playlist with more than its supported 1000 returned records. It never emits private video IDs, OAuth tokens or raw Google responses to the public CI logs.

## Technical components

- `scripts/branch3_a8_exhaustive_inventory.py`: strictly allowlisted `oauth2.googleapis.com/token` refresh POST and `www.googleapis.com/youtube/v3` **GET-only** to `channels`, `playlistItems` and `videos`. Verifies exact `UCfPEvy0SefE_5nNlYlY_CyQ`; no FlowMinute fallback.
- `scripts/test_branch3_a8_exhaustive_inventory.py`: synthetic Google API mocks and adversarial pagination/status/account checks; no network calls in CI.
- `.github/workflows/branch3-clivox-a8-inventory-qa.yml`: unprivileged PR tests, no credentials or private artifacts.
- `.github/workflows/branch3-clivox-a8-inventory-readonly.yml`: optional future owner-triggered/main-only protected job using GitHub `clivox-readonly` environment, not an upload environment.

## Real owner-only prerequisite

1. Independently review the existing `clivox-readonly` environment protection and main-only branch restrictions; this workflow merely references the environment and does not create or prove its review rules.
2. In **protected environment secrets** (never chat, public repo, PR comments or video descriptions), configure the **separate Clivox** `CLIVOX_A7_READONLY_CLIENT_ID`, `CLIVOX_A7_READONLY_CLIENT_SECRET` and `CLIVOX_A7_READONLY_REFRESH_TOKEN` granted only `https://www.googleapis.com/auth/youtube.readonly`. No FlowMinute tokens. The OAuth consent flow must be authorized by the real owner selecting Clivox.
3. After code and scope review, set the exact owner opt-in environment secret `CLIVOX_A8_INVENTORY_READ_APPROVED=approved-a8-inventory-readonly-v1`.
4. Dispatch **Clivox A8 Owner-Reviewed COMPLETE BOUNDED Uploads READ-ONLY** from Actions on `main` as `Tirthanand17`, first run attempt only; review/approve the protected environment access as the owner.
5. Check that the sanitized result is from a live run and not a fixture. It emits only counts and explicitly denies uploading, scheduling, automated duplicates and source access.

## Critical limitations and recovery

- Even when pagination ends, a successful API snapshot is **not a transactional remote database lock, freshness guarantee or proof of all historical uploads**. Deleted videos, delayed indexing, other channel Brand Accounts, processing states and timing races can still exist.
- YouTube's metadata API does **not** independently verify the SHA-256 of original uploaded video binary. The digest in A8's attempt ledger is not a remote cryptographic content hash. This flow cannot automatically match an exact binary to a remote video solely from a title, timestamp, thumbnail or a locally invented marker.
- If any upload attempt was ambiguous, keep its reservation **held**. Compare the private attempt ledger with authenticated inventory and independently verified owner-held receipts/video IDs. Absence from the uploads snapshot alone NEVER permits automatic retry.
- Never schedule merely on a count or privacy status. Require separately authenticated owner release, exact licensed source, signed A6 final binary, protected Clivox uploader grant and current private-first readback.
- No real creator permissions, private vault, video or uploader credentials have been provisioned; no uploads have been attempted by this code.

**Current state:** A7/A8 code-only readback, zero authenticated real YouTube reads in this workflow, zero licensed creators, zero CLIVOX uploads, no publication. Branches 1 and 2 remain paused.
