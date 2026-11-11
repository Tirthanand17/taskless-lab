# Branch 1 — Nov 13–17 vidIQ MFA, media import, 15 draft schedule-readback blocker

**Observed November 11, 2026 — source: authenticated vidIQ connector (owner channel `UCCcL9Q_jqVq6LJmnYUSAFZA`).** Do not call these scheduled YouTube videos.

## Completed

- Channel MFA recheck returned `status=verified`. `vidiq_social_account_list` confirmed `connectionActive=true`, `canPublish=true`, and the exact intended channel.
- All fifteen final B1v4 MP4s from successful five-day SHA-verified main GitHub runs were re-hashed locally against their immutable physical-AAC release manifest and imported using `vidiq_video_upload`. **Every import returned `status=ready`**, with a unique `uploadId`. This only stages vidIQ media, not YouTube upload.
- Created fifteen distinct YouTube destination drafts using `vidiq_social_post_draft_create`, one file per draft, correct channel, explicit `privacyStatus=private`, official-source metadata title/description/tags, and intended UTC publishAt for the target date. Each **create** response returned `ready=true`, `status=draft`, and the requested `scheduledFor`.
- Independently read all 15 using `vidiq_social_post_draft_get`. Each returned `ready=true`, `status=draft`, and `media.videos=1` for the correct channel. **Every readback returned `scheduledFor=null`**. This is the unresolved provider schedule-persistence/readback mismatch; never submit a supposedly scheduled draft when the saved date cannot be confirmed.
- Retried one draft with `vidiq_social_post_draft_update` (both top-level and per-destination publishAt, then per-destination only). Each immediate update response showed the correct 2026-11-13T05:30:00Z, while subsequent independent `draft_get` still reported `scheduledFor=null`.
- `vidiq_social_post_list` filtered for this channel and Nov 11–19 future dated drafts/schedules returned **zero rows**. This corroborates the readback inconsistency. It does not mean the drafts are lost; per-ID draft-get returned all 15.
- Existing private YouTube inventory through vidIQ had no Nov 13–17 scheduled posts at this check.
- A temporary private GitHub DRAFT release was created for experimental media transfer when the first file-ID import failed. The local sandbox file path was subsequently found to work directly, making the temporary release unnecessary. The **private draft release was deleted** and readback reported `release not found`. The unused manual cloud upload workflow was removed in this branch. No media were published through that GitHub release.

## Exact intended daily schedule (Asia/Kolkata)

On **November 13, 14, 15, 16 and 17**:
- Short AM: **11:00 IST**, UTC **05:30Z**.
- Long: **16:00 IST**, UTC **10:30Z**.
- Short PM: **20:30 IST**, UTC **15:00Z**.

These are owner-requested future target times, **not persisted vidIQ or verified YouTube schedules**. All dates/times must remain future at actual publication.

## Safety / next work

1. **Do not call `vidiq_social_post_publish`** until user sees and explicitly approves exact finalized 15 destination drafts/media/times. The connector describes it as an irreversible operation, and the saved draft scheduling time is currently null.
2. Resolve provider schedule readback before any publish; do not rely on immediate `draft_create` or `draft_update` response alone. If needed, contact vidIQ via their support portal; avoid posting credentials, tokens, draft IDs, or private file URLs to public issues.
3. A **private-first** workaround (upload as private, verify channel/video ID, and then update `status.publishAt` via an authorized owner video-edit API) must also receive separate explicit approval and confirmation that the first upload cannot become public immediately. Do not silently downgrade to instant posting.
4. For the existing protected GitHub YouTube publisher, OAuth refresh had previously failed, and owner Ed25519 signed release proof remains absent; vidIQ's successful MFA does not repair GitHub OAuth.
5. After a real release, require authenticated YouTube per-video ID, processing and exact `status.publishAt` readback, then mark each completed slot. Do not equate a published draft with a YouTube schedule without this verification.

**Verified stage:** 15/15 real polished original videos, 15/15 imported to vidIQ media library, 15/15 draft-ready, **0/15 persisted publication dates confirmed, 0/15 YouTube schedules confirmed**.
