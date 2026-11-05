# ADR-0040 — B4d3 independent physical video review intake

**Date:** 2026-11-05 IST. **Branch:** 2 only. **Scope:** read-only source plus independent main-branch GitHub artifact intake; no YouTube publishing, owner approval, or local laptop use.

## Real source evidence behind 40/100

[Real three-video main GitHub Actions run #41970364138](https://github.com/Tirthanand17/taskless-lab/actions/runs/41970364138), SHA 0e230a842790b05616ffa007dea2f43f9cfaf4c3, completed SUCCESS for both security and real-video-generation jobs, including the full FFmpeg/animation/voice/caption inspection. GitHub independently returned artifact ID **13389693311**, name flowminute-unapproved-three-real-demo-videos-41970364138-1, nonexpired at check, 18,624,878 compressed bytes, created 2026-11-05T05:02:37Z, expires 2026-11-12T05:02:35Z, ZIP SHA256 4a90f0afe0247c0d96cb6e27bbfa0fc56fdd8ada7418bd47b013ee2686e2b675. The original runner checked 10 files: three playable H.264/AAC MP4 videos, three matching SRT subtitles, three original 1280x720 PNG thumbnails, and one unapproved source/hash manifest.

The earlier real retained planning receipt (PR #42) raised the research rubric 6 to 7/15 (38 to 39). This verified real video retention (PR #43) raises the media rubric 13 to 14/20 (39 to **40/100**). Current breakdown: architecture 14/15, research 7/15, physical media/retention 14/20, human fact/rights review 2/15, live secured cloud 3/15, actual YouTube OAuth/upload 0/15, 7-day live cadence 0/5 = **40/100**. Real unattended YouTube 0/21. This rubric does not measure percentage of actual uploads.

## B4d3 independent physical artifact verification and review handoff

Source file autopilot/independent_public_review_intake.py does NOT import the producer/render implementation. It reconstructs exact authored fixed NASA/NIST/USGS story identities, requires the original unapproved release flags, rejects extra directories/files/symlinks and malformed or duplicate-key manifests, and **re-hashes all nine physical media files** from a fresh GitHub runner. It separately executes ffprobe for actual H.264 + AAC + dimensions + duration, parses SRT cue timing/order, and validates the original PNG header and dimensions. It writes an unsigned JSON intake and a human Markdown review checklist tied to each actual video SHA. Technical media checks are NOT independent human watching/listening, legal licensing clearance, or factual verification.

Unit tests autopilot/test_independent_public_review_intake.py challenge source hash swaps, fake approval flags, duplicate episodes/files, symlink paths, corrupt media, misleading FFprobe replies, invalid SRT and wrong image dimensions. Test fake bytes are never playable MP4s.

GitHub workflow .github/workflows/flowminute-b4d3-independent-review-intake.yml is read-only (contents:read and actions:read) and has two jobs: PRs run unit checks only; a main-branch protected post-merge job verifies the exact existing GitHub artifact metadata including original main SHA, downloads only the exact video-artifact name from run #41970364138, rehashes/checks 9 files + source manifest, and stores only a small unsigned JSON/Markdown reviewer intake for 14 days. No raw media is stored again, no Google SDK or secrets imported, no YouTube uploader, no additional billable cloud resource. Downloads are deleted from ephemeral runner after inspection. Real media expires 2026-11-12: [get the three video previews](https://github.com/Tirthanand17/taskless-lab/actions/runs/41970364138/artifacts/13389693311).

## Tasks that remain genuinely owner-controlled

For EACH SHA-specific video, a real owner/reviewer must watch and listen to full video, check every narration/SRT claim against independently confirmed NASA/NIST/USGS primary sources, verify graphics/thumbnail/title/metadata accuracy, check artistic originality and licenses of voice/model/art/fonts/ambient, confirm proper synthetic-media disclosure and compare channel catalogue. If something fails, reject and remake the exact files. Human review must be authenticated and not inferred from an unchecked public Markdown checklist.

Real owner OAuth, cloud encrypted persistent database/session and private media storage, actual future 11:00/16:00/20:30 IST release schedule, readback of YouTube processing/captions/thumbnail/channel, and full 7-day 21-video unattended proof remain missing. No action in this PR grants permission to upload or schedule, no Branch 1 modifications.

## Exact acceptance proof

Require all exact-head PR workflows success (new unit tests plus quality/scout/render). The real second-run B4d3 verification is only counted as operational after a **main push** run confirms all 9 actual media SHA values, independent FFprobe/SRT/PNG readback and uploads a new unsigned intake artifact. If it fails or the original media artifact expires, keep the handoff blocked and do not claim operational reviewer readiness. **Even when B4d3 succeeds, the production score stays 40/100 and YouTube stays 0/21**, because there has been no human approval or external upload.

This is physical evidence for a human handoff, not a release signature or authorizing actor.
