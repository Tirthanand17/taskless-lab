# YouTube API authorization pilot — 2026-10-11

## Verified through official API
- Dedicated Google Cloud project and YouTube Data API v3 were enabled in the previous session.
- Google OAuth Desktop client credential JSON is stored **locally** outside GitHub, not in the repository.
- Owner accepted Google's app warning and approved the `youtube.readonly` OAuth scope for FlowMinute Lab.
- The local refresh token exists; no access tokens, refresh tokens, or OAuth client secrets are stored in GitHub.
- `scripts/youtube_publisher.py doctor` successfully verified channel `UCCcL9Q_jqVq6LJmnYUSAFZA` (FlowMinute Lab).
- Official `channels.list(mine=true)` returned exactly one channel: FlowMinute Lab.
- Official `videos.list` independently confirmed these three production video IDs are processed, private and scheduled:
  - `oN2PgprMbSE`: `2026-10-12T05:30:00Z` (11:00 IST).
  - `jbfNmbl3owA`: `2026-10-12T10:30:00Z` (16:00 IST).
  - `XEV1fz-75-M`: `2026-10-12T15:00:00Z` (20:30 IST).
- No live upload, metadata update, schedule update, or deletion occurred in this verification.

## Current gate
- **READ-ONLY connected:** yes.
- **PUBLISH OAuth authorization:** pending separate owner approval.
- **Private-only upload test:** not yet performed.
- **Automatic scheduling of new daily releases:** not enabled.
- Existing October 11–12 schedules are protected and must not be reuploaded.

## Notes
OAuth is in external Testing mode; its refresh token can expire after about seven days depending on Google restrictions. Do not assume unattended operation is ready. Keep all tokens and secrets local until secure credential storage and refresh testing pass.
