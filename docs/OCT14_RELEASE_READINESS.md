# October 14, 2026 — video production technical QA and publication gates

**Status: 3 MP4s technically validated, NOT editorial/listening approved and NOT uploaded or scheduled to YouTube.**

Authenticated channel: `UCCcL9Q_jqVq6LJmnYUSAFZA`. Video and related files live only under `C:\Users\Dell\Desktop\youtube con\oct14-production`.

| Video | Target IST October 14 | MP4 length | Resolution | SHA-256 | Technical status |
|---|---|---:|---|---|---|
| pilot_019 | 11:00 | 42.00 s | 1080x1920 | `b70637a54c000e1bb8692d439402a94be5e5b08d28aa697950eb37f1eb4dc2b5` | **Pass** |
| long_009 | 16:00 | 211.00 s | 1920x1080 | `c5a15f3862bab81961d6b9ce7ceb12970eb3ea492ee179b4a0640f88a39c9587` | **Pass** |
| pilot_020 | 20:30 | 37.00 s | 1080x1920 | `e751c6d17761d3f7e9e4cc9e301dbdacf4978aa6fd2ddde837f7bb597bb6e70b` | **Pass** |

All MP4 files decoded fully with FFmpeg (H.264 video and AAC audio). Audio peak checks passed below clipping. Source/motion: `motion-v2/src/October14.tsx`. The long custom thumbnail is `oct14-production/long_009_thumbnail.jpg`. Final contact sheets: `oct14-production/pilot_019_contact_FINAL.jpg`, `long_009_contact_FINAL.jpg`, `pilot_020_contact_FINAL.jpg`.

Segments `pilot_019` / `pilot_020`: stock human-phone footage credited to RDNE Stock project via Pexels. Long `long_009`: licensed payment stock scene credited to ArtHouse Studio via Pexels. Actual Chrome product screens and actual paid transactions are **not** claimed; all screen mockups clearly say illustrative/concept interface.

**Human approval still needed:** Listen to all three complete synthetic voiceovers for naturalness and pronunciation, watch all MP4s end-to-end for timing/crops/content, and review exact subtitles before uploading. Local `captions/*_DRAFT_UNREVIEWED.srt` are NOT aligned and will not be uploaded unreviewed. This report is automated technical validation only, not a claim of human editorial review.

Release manifests are staged under `oct14-production/manifests/`, `qa_approved=false` until the owner reviews/approves. **No real YouTube video ID, no schedule receipt, no live upload attempt.** After genuine owner review, publisher sequence: prepare → private upload → thumbnail → schedule → independently verify `publishAt`, ensuring unique content hashes and no duplicates.

Growth rationale and official sourcing: [Editorial & growth audit](OCT14_EDITORIAL_AND_GROWTH_AUDIT.md), [Community interaction playbook](OCT14_COMMUNITY_PLAYBOOK.md). No guarantee of increased views/likes/subscribers.
