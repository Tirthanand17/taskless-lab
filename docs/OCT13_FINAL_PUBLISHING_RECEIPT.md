# FlowMinute Lab — 2026-10-13 Final YouTube Scheduling Receipt

**Result verified through authenticated YouTube Data API on October 13, 2026, ~07:40 IST. All 3 videos scheduled.**

| Episode | YouTube video ID | Planned release (Asia/Kolkata) | Current state |
| --- | --- | --- | --- |
| pilot_017 | [mxB4fNx0Ua4](https://youtube.com/shorts/mxB4fNx0Ua4) | Oct 13, 11:00 AM | PRIVATE, scheduled; processed |
| long_008 | [NCLp6YibFMs](https://youtu.be/NCLp6YibFMs) | Oct 13, 4:00 PM | PRIVATE, scheduled; processed; **custom thumbnail confirmed** |
| pilot_018 | [-8B1X1n5XIU](https://youtube.com/shorts/-8B1X1n5XIU) | Oct 13, 8:30 PM | PRIVATE, scheduled; processed |

## Live verification evidence
- Authenticated owner channel ID: `UCCcL9Q_jqVq6LJmnYUSAFZA`.
- `verify-queue --receipts-dir flowminute-oct11/state/scheduled --date 2026-10-13`: **checked=3, passed=3, needs_attention=0**.
- Long 008 read-only inspection: `ledger_state=scheduled_verified`, `remote_privacy=private`, `remote_upload_status=processed`, `remote_processing=succeeded`, `remote_publish_at=2026-10-13T10:30:00Z` (16:00 IST), `recorded_assets.thumbnail=confirmed`.
- Do not claim public playability until after the release times. Scheduling is successful but **public release is future**.
- Draft-caption timelines have not been independently aligned and were not uploaded as approved captions.

## Long 008 recovery
1. Original `-_6iX5o3EfY` was the first API upload. Network SSL EOF occurred after the first 49.9% resumable progress. YouTube listed the original as `uploaded` / `processing` with `duration=P0D` overnight.
2. Official YouTube support suggests re-export/re-upload after many hours stuck. Original video remains **Private, unscheduled** and must not be scheduled or published as a second copy.
3. Re-encoded same user-approved creative as `oct13-production/long_008_recovery_v2.mp4` (10,769,398 bytes; SHA-256 `01301b60f09c58765afb90b36af59b4ea91f42141d2108030df3ad97785f7e17`). Uses H.264 high profile, 1920x1080/24fps, standard Rec.709 limited-range yuv420p, AAC 48kHz/192k target, and faststart MP4. FFmpeg full decode passed.
4. Second private upload used smaller **1MiB resumable chunks**, succeeded and returned video ID `NCLp6YibFMs`. Processing completed successfully.
5. The first schedule write response was ambiguous due an immediate stale API read-back, but a fresh authenticated `videos.list` confirmed **Private with publishAt 2026-10-13T10:30:00Z**. The local fail-closed ledger was reconciled from that evidence; no second schedule write was made.
6. Custom thumbnail was then uploaded successfully. A one-line local publisher correction avoids eager dictionary-key evaluation in the thumbnail duplicate-attempt check. A backup of the existing publisher script is stored outside Git under `oct13-production`; unrelated preexisting publisher-worktree changes have not been committed.
7. Only `NCLp6YibFMs` is eligible for the canonical Long 008 release; the original is a private stalled artifact.

## Data locations
- Private publisher ledger and OAuth tokens: `C:\Users\Dell\Desktop\youtube con\.flowminute-private\` (never commit).
- Local finalized video and thumbnail: `C:\Users\Dell\Desktop\youtube con\oct13-production\`.
- Recovery release manifest: `oct13-production/manifests/long_008_recovery_v2.release.json`.
- Source and schedule receipt: `flowminute-oct11/content/episodes/long_008_recovery_v2.json`, `flowminute-oct11/state/scheduled/long_008.json`.
- The separate `state/reconciliation/2026-10-12-long008-upload-interrupted.json` remains the historical, accurate evidence of the original failed attempt.

## Post-release check required
At/after 16:00 IST, verify video `NCLp6YibFMs` becomes Public and plays successfully. Also confirm the original `-_6iX5o3EfY` remains Private. Never schedule the original. Update the release ledger with the actual post-release status after it occurs.

Reference: https://support.google.com/youtube/answer/4525858 (YouTube help) and https://developers.google.com/youtube/v3/docs/videos (YouTube Data API status semantics).
