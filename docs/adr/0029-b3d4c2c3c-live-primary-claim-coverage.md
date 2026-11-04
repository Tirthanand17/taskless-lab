# ADR-0029 — B3d4c2c3c live public evidence and original claim-surface completeness (UNAPPROVED)

**Date:** 2026-11-04 IST. **Track:** Branch 2, GitHub-only. **Decision:** connect the existing 3 actual voiced video drafts to full sentence/visual/thumbnail/proposed metadata claim coverage and 6 primary agency page live HTTPS readbacks. **No independent human factual, audiovisual, copyright, voice, AI disclosure or owner approval.**

## Official primary research, checked November 4, 2026

- [NASA Moon Facts](https://science.nasa.gov/moon/facts/) — average Earth–Moon distance 384,400 km; the actual orbit position changes.
- [NIST CODATA](https://physics.nist.gov/cuu/Constants/Value/c.html) — exact vacuum light speed of 299,792,458 m/s. Rough Moon one-way 1.28 seconds and ideal roundtrip 2.56 seconds are original derived formulae, not real NASA communications observations.
- [USGS magnitude versus shaking](https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity) — per whole magnitude step approximately 10x seismogram amplitude, approximately 32x energy, and local shaking varies by conditions.
- [USGS relative energy explanation](https://earthquake.usgs.gov/education/how_much_bigger.php) — 10 to the power of 1.5 per magnitude step; 31.6x for one increment, 1000x for two.
- [NIST binary multiples](https://physics.nist.gov/cuu/Units/binary.html) — eight bits per byte, binary MiB of 1,048,576 bytes and decimal MB of 1,000,000 bytes.
- [NIST SI prefixes](https://www.nist.gov/pml/owm/metric-si-prefixes) — decimal mega is one million. The illustrative 100 MB vs 100 MiB transfers on a hypothetical ideal 20 Mb/s network are calculations, not live speed tests.

This milestone does NOT license or store full copyrighted source pages, scientific diagrams, third-party audio or source article bodies. The science source links come from trusted agencies, not model-generated unverified blogs.

## Live public-source readback contract

GitHub-hosted Python sends direct TLS-validated GET requests to precisely six hard-coded NASA/NIST/USGS HTTPS URLs. It rejects non-HTTPS URLs, unexpected final host or redirect, unexpectedly large data over 3 MB, invalid/oversized text, invalid content type and missing coarse factual markers. It computes full returned HTML SHA256 and normalized readable-text SHA256, saving only URLs, metadata, timestamps and response digests in ephemeral hosted CI logs.

Markers: NASA 384,400; NIST exact 299 792 458; USGS tenfold amplitude and 32 energy; USGS 10**1.5 energy; NIST 8 bit + 1 MiB/1 048 576; NIST mega/million/10^6. Presence of a marker on an agency page shows only that the named literal appears. This does not prove that every authored claim is semantically or contextually corroborated, timely or rights-cleared. Mock HTTP test fixtures are always marked MOCK_NO_LIVE_PROOF. A self-supplied source digest is not an externally signed timestamp or actual immutable private source archive.

## Exact script/graphics/metadata surface docket

Autopilot source_claim_surface_docket builds the three exact original NASA/NIST/USGS educational scripts from immutable repository-authored source calculation, not from external generated arbitrary text. It enumerates:

1. **70 exactly spoken narration sentence/SRT cues** across 32 separate scene beats, recording literal text, unique cue position, associated scene-claim IDs and each source link.
2. **64 scene title/number text surfaces** and **64 actually rendered early/late SVG text-node inventories** from the same source graphic renderer that produced PR #31 videos. Ever-present visual claims (e.g. long video 100 MB/40-second graphic) are explicitly bound even when a scene narrates another aspect.
3. The two literal graphic headlines on each of **three original thumbnails**, shared with the physical Pillow thumbnail renderer rather than separately invented. Actual original 1280x720 thumbnail pixels were encoded/hashed independently in PR #31.
4. New draft YouTube titles and descriptions for each of the three original topics, with cited claim IDs, explicit idealized-calculation and scene/video limitations. This module cannot upload or write to YouTube.
5. All **14 explicitly curated source claim IDs** classified as primary public fact, calculated result, hypothetical user-input assumption or explanatory limitation. Every claim must have actual original voiced uses and real primary-authority reference IDs, with a canonical full-docket SHA.

The exact real physical MP4, WAV, SRT, thumbnail, scenes and 160 moving SVG frame SHA inventory from the separate PR #31 rendering module now binds to this independently rederived unapproved visual/narration/metadata SHA. Producer/editorial flags always remain FALSE; a calculated hash does not mean a human watched every image or fact-checked each assertion.

## Implementation

- autopilot/primary_claim_surface_docket.py — full exact original spoken text, SVG, thumbnail and metadata provenance and 14 claim classifications, rederived signature-free deterministic inventory, no release.
- autopilot/public_primary_readback.py — six live agency HTTPS exact-source direct fetches with fail-closed coarse science marker checks; no untrusted external URL input, no publisher transport.
- autopilot/test_primary_claim_surface_docket.py — mocked agency HTML is never falsely labeled live, adversarial changed source/claim/cue/thumbnail/metadata, wrong URL/redirect, forged rights approval and unexpected body size/content.
- autopilot/primary_sourced_storyboards.py and autopilot/full_topic_narrated_pack.py — one canonical physical thumbnail copy and regenerated source-surface SHA bound to every original media file digest at encoded video QA edge.
- .github/workflows/flowminute-b3d4c2c3c-source-claim-evidence.yml — two read-only hosted jobs, one source/claim fixture and the other real direct primary page readback. Existing full authentic Kokoro three-video CI reruns on media code changes, with all voice/media files destroyed after hosted use.
- docs/status/branch2-completion-audit-2026-11-04.md — conservative updated progress. All new source/rights/human approval and publishing remain absent.

## Policy and limits

The real videos are technically encoded, NOT independently rights-cleared or approved. The signed mock human reviewer role suite from PR #29 remains ONLY synthetic. Actual source quotations, precise passage/context interpretation, independent external full fact review for narration/thumbnail/graphics/title, semantic visual accuracy, owner-controlled voice/model licensing and disclosure, human complete playback, durable private media/source vault, real provider payment and YouTube OAuth are still missing.

For [YouTube altered/synthetic disclosure](https://support.google.com/youtube/answer/14328491), the real owner/editorial human must review final appearance and choose correct declaration; the [YouTube videos resource](https://developers.google.com/youtube/data/reference/rest/v3/videos) exposes containsSyntheticMedia, but this module never requests it. [YouTube inauthentic content](https://support.google.com/youtube/answer/1311392) also requires substantive variation across actual daily channel content, not merely different MP4 SHA values.

**NEXT B3d4c2d:** choose explicitly owner-approved private cloud, secure billing/vault, protected durable video and source evidence storage, enroll real separate fact/rights/final-playback/channel owner reviewers and independently review source semantics against EXACT final title/description/MP4/SRT/thumb bytes. Signed cryptographic receipts require verifiable independently controlled identities and owner-controlled immutable roots. No mock CI key may authorize a real publish.

**B4/B5:** explicit owner-approved OAuth, one private YouTube uploader, remote processing/captions/thumbnail/status/IST future publication readback, then 21 genuinely original real 2 Shorts+1 long releases across 7 days without laptop power. Branch 1 assisted schedule remains unaffected.

No paid provider, real upload, user laptop process, private cloud resource or YouTube credential in this PR.
