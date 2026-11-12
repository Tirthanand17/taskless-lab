# Clivox — creator-permission-only clipping release policy

**Default: DENY ALL.** Only clips from YouTubers/podcasters who explicitly provide clipping permission can enter our workflow. This is stricter than a generic fair-use or public-domain analysis. Mere credit, downloading, remix tools, subtitles, low clip duration, a viral source, or someone else's reupload **is not permission**.

## Exactly two eligible proof types
1. **Direct written permission** issued by the verified creator/actual rights holder (or their authorized representative) to Clivox, expressly allowing excerpting and editing the specified source video(s), YouTube Shorts/standard videos, redistribution and commercial/monetized use. Keep the sensitive contract outside this public repo; include a non-sensitive source ID and SHA-256 fingerprint only.
2. **Creator-published public clipping policy**, hosted on a verified creator-controlled channel/site, explicitly granting third parties (including this channel) rights to excerpt and repost/edit relevant material on YouTube. Record the canonical policy URL, retrieval date, verifiable author identity, exact scope, commercial permissions, attribution and revocation/expiry terms. A third-party blog *claiming* they allow clips does **not** count. Cached snapshots are evidence only, not a substitute for checking the live policy.

**Not eligible by itself:** fair use speculation, short length, channel Creative Commons setting with no clear creator-authored clipping policy, public domain, downloaded video, reposts from fans, verbal hearsay, generalized sponsor/affiliate rights, guest permission without program owner rights, and “no copyright intended.” Such material is categorically outside this project's source policy.

## Mandatory creator-level and per-source checks
1. Verify permission issuer controls the original recording rights. Maintain a non-sensitive consent/creator identity reference in `creator_permissions.json`; default allowlist is empty.
2. Match exact original creator, original source YouTube video ID and timestamps to written grant or public policy scope.
3. Confirm permission explicitly authorizes clipping/editing, YouTube republication, the intended geography, commercial use/monetization and any mandated credit/links, and has not expired or been withdrawn.
4. Separately clear any background music, movie footage, sports broadcasts, sound effects, photographs or guest-provided material *not* included in the creator's grant. Exclude or substitute unlicensed elements before release.
5. Make original editorial analysis or narrative a meaningful part of each video. A plain subtitled repost may still fail YouTube's channel-wide reused-content monetization standard even with permission.
6. Confirm statements remain accurate in context, disclose edits where necessary, verify captions, accessibility, branding, rendering and final phone-screen playback.
7. Obtain a separate, exact-video owner/rights/editorial signoff and secure channel authorization; the source allowlist is **never a publishing authorization**.
8. Check Content ID and potential takedown notices; comply with authentic revocations and do not auto-dispute claims.

## Enforcement
- `scripts/branch3_creator_permission_gate.py` performs a strict preflight on a proposed creator and source record. Missing or ambiguous fields fail closed.
- `branch3/creator_permissions.json` is initially `[]`: **zero eligible third-party clips**.
- A passing machine preflight only means **eligible for further owner review**. It does not prove a legal grant, a human inspection, originality, or YouTube upload approval.
- No new uploads, automatic scraping, downloading, or publishing have been connected to this gate.

## Suggested request to copyright owner (send only after selecting a genuine contact)
**Subject:** Permission to make YouTube commentary clips from [show/episode]

Hello [creator or rights team], I operate Clivox, an independent commentary and clipping channel. I'm requesting your written permission to excerpt, edit and republish limited segments from [exact source URL or defined catalog] on YouTube Shorts and regular videos, adding my own commentary. Please confirm whether the license includes monetized YouTube uses, permitted length and dates, countries, required attribution/link, use of guest audio and likeness as shown, and whether all third-party music/footage is included. Please also specify restrictions, revocation rights or prior review requirements. I will not use the source without a valid permission grant.

## Primary policies
- YouTube copyright myths: https://support.google.com/youtube/answer/2797449
- YouTube copyright options and risks: https://support.google.com/youtube/answer/2797466
- YouTube monetization/reused content: https://support.google.com/youtube/answer/1311392
