# ADR-0055 — Branch 1 B1q6: authenticated November 5–11 YouTube calendar verification

**2026-11-05 (IST). GitHub-only. Read-only, no YouTube mutations.**

## Why this matters

The owner reported a repeated circular motif on several uploaded Shorts, but the screenshots do not establish exact YouTube IDs. Previously rendered original replacement candidates are NOT necessarily those same videos. The original files on YouTube cannot be replaced under the same URL; any corrected upload must have a new ID. Official: https://support.google.com/youtube/answer/55770

## Archived local evidence (not current YouTube state)

November 5–11 daily goal is 11:00 Short, 16:00 long, 20:30 Short in IST, which makes 21 slots (14 Shorts and 7 long). Exactly FOUR GitHub historical release receipts exist in this window:

| Date IST | Slot | Archived topic |
| --- | --- | --- |
| Nov 5 | 20:30 Short | AI voice-cloning caller safety |
| Nov 6 | 11:00 Short | Photo GPS metadata |
| Nov 6 | 16:00 long | Passkey phishing explainer |
| Nov 7 | 11:00 Short | Incognito browsing |

The remaining 17 slots have no matching repository receipts. They are UNKNOWN, not proven vacant on YouTube. There is not yet a completed current authenticated YouTube owner readback.

## Three genuine previously tested new review candidates, not approved replacements

Protected main GitHub workflow run 42030043740 retained artifact 13415862216 with 3 original full portrait H264/AAC MP4s and source-bound captions. Original narrative frames, 21 subordinate asset hashes, exact PCM/visual scene alignment and FFmpeg full decoding passed. Human listening and rights reviews are not approved. The original uploaded video binaries or actual spinner-source projects are not archived in GitHub as exact originals.

| Candidate | New exact SHA-256 | Duration |
| --- | --- | --- |
| voice-cloning safety | 89de6d50fae8184848f1209077e208e5955762f52b8e6c07bf7c347e3ee4f6a2 | 38.708 sec |
| photo GPS privacy | abdee1fcc925c1d861b34ce11d984b47baab38f65ec8bc0f5eceec66593f4fea | 39.875 sec |
| incognito privacy | cf8a74661266d4207e6beebd2ed1335f52a04b38b1d1be157231dc951bbcd281 | 46.458 sec |

The November 6 long episode has NO new replacement in this artifact. Its schedule must not be modified by the three-Short review.

## Actual protected owner read-only calendar verifier

- autopilot/branch1_owner_schedule_readonly_v6.py takes an owner-authenticated YouTube client and ONLY executes channels.list, playlistItems.list and videos.list, using the channel's uploads playlist (official flow: https://developers.google.com/youtube/data/guides/implementation/videos).
- Verifies ownership of the expected FlowMinute Lab channel, exhaustively paginates uploaded video IDs to a bounded cap (otherwise fails), and checks current status.privacyStatus, status.publishAt and snippet.channelId. Four archived IDs are independently requested even if they are absent from uploads.
- All 21 expected IST slots receive owner-private-schedule counts, duplicate/collision diagnostics, and archived-ID comparison. Report is REDACTED; no private title, video ID, OAuth, description, account details or URLs are stored.
- Synthetic no-network mocks/test cases check 21-slot coverage, public/past video preservation, duplicate detection, wrong channel, pagination exhaustion and no private video ID leakage. Passing these tests IS NOT live owner verification.
- The new GitHub-only workflow runs no-secret PR checks. Protected-main authenticated check uses the existing youtube-production environment and secrets.YOUTUBE_TOKEN_JSON if configured. A missing/invalid secret or blocked protected environment yields an explicit unverified result, never fabricated confirmations. Ephemeral redacted output retained for 1 day only.
- Workflow disables publishing/deletion/updates and uses GitHub permissions contents:read. No personal laptop storage or new external SaaS required.

## Next step: safe one-by-one replacement only after verified owner readback

For any still-private/future original: establish exact old ID and source matching; obtain approved new media hash and full editorial/facts/audio/rights watch; private-first upload and processing/caption readback; independently confirm precise future publishAt; only then seek owner approval to alter the original's schedule and verify exactly one intended future release. No automatic deletion or schedule mutation in this branch.

Past slots cannot be retroactively scheduled; official YouTube API says setting publishAt in the past may publish immediately: https://developers.google.com/youtube/data/reference/rest/v3/videos

This branch does NOT claim any uploaded or scheduled video was changed.
