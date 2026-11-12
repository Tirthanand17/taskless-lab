# Branch 3 — Clivox (SECOND YouTube channel)

**Status:** **Clivox was created and publicly verified on 2026-11-12**, with the exact chrome-and-orange logo, premium banner, About description and channel keywords live. The new channel has zero videos and zero approved third-party clip creators; publishing automation remains disabled.

**Isolation:** Branch 1 (existing FlowMinute Lab scheduling) and Branch 2 (autonomous FlowMinute publishing) are paused. Do not change their code, channels, schedules or credentials. This branch shares the existing repository for planning and branding but uses completely separate channel identity, source-rights registry, approval process and future credentials.

## Live channel identity (YouTube-verified)
- Display name: **Clivox**
- Verified handle: **@ClivoxPulse** (`@Clivox` was unavailable)
- Verified channel ID: `UCfPEvy0SefE_5nNlYlY_CyQ`
- Official channel: https://www.youtube.com/@ClivoxPulse
- Focus: **viral-worthy creator-approved highlights across gaming (including GTA VI), livestreams, comedy/jokes, entertainment, podcasts and interviews**, always with meaningful original editorial context
- Language: English first; no assumption of language rights
- Tagline: **Clips worth watching. Context worth knowing.**
- Video style: creator-approved excerpt + original commentary/critique/story, source attribution and clear factual context
- Profile and banner SVG: `branch3/branding/`
- Final channel About copy: `branch3/channel-profile.md`

## Viral-first multi-category content strategy
**Current content priorities:** (1) gaming/GTA VI, (2) livestream reactions, (3) comedy/jokes, (4) entertainment/pop culture, and (5) podcasts/interviews. The goal is to find the strongest original, shareable moment in a creator-permitted full video, podcast or livestream rather than copy its most-viewed excerpt. See `viral-content-strategy.json`. This is an editorial testing order, not an assertion that one category will go viral. Keep performance decisions tied to actual Clivox analytics after launch.

**GTA VI is a topic watchlist, not a license.** Rockstar/Take-Two's published fan-video guidance emphasizes non-commercial gameplay and excludes leaked pre-release footage and other restricted clips. Commercial Clivox clips need separately verified publisher/game footage rights when applicable, in addition to streamer permission; no leaks or spoiler compilations.

## Explicit creator-permission rule
Only material covered by direct written creator/rights-holder permission or an authentic public clipping policy from that creator enters the candidate pipeline. We never treat a viral video, Fair Use speculation, a general downloadable link, third-party CC upload, or credit-only attribution as blanket permission. See `scripts/branch3_creator_permission_gate.py` and `creator_permissions.json` (empty by default). A permissions record can qualify a proposed candidate for human review; it **never** authorizes upload itself.

## Hard launch gates
1. **DONE** — New channel created via YouTube UI and verified distinct from FlowMinute Lab; exact channel ID is recorded in `channel_state.json`.
2. **Studio owner UI access verified.** New channel publishing API OAuth is NOT configured; never copy existing FlowMinute Lab OAuth tokens to this channel.
3. For every reused segment: prove original publisher's ownership, creator-issued written permission or an authenticated creator-published clipping policy for reuse **and** editing, redistribution, Shorts and commercial use where applicable; verify underlying third-party footage/music rights separately. Store only consent reference and non-sensitive metadata in repo.
4. Add substantial original educational/critical context. Avoid bare reuploads, generic templates and misleading crops.
5. Independent creator/rights/editorial and final playback review; no uploads while approval is missing.
6. No guarantee of zero Content ID claims, strikes or monetization eligibility.
7. Keep all publishing automation off until the user separately approves after channel creation.

## Files
- `channel_state.json`: verified creation, channel identity, branding and safety configuration
- `creator_permissions.json`: empty creator allowlist; no creators eligible by default
- `scripts/branch3_creator_permission_gate.py`: fail-closed candidate intake check; never upload permission
- `viral-content-strategy.json`: five content pillars, priority order, test signals, release blockers
- `research.md`: policy evidence and strategy
- `channel-profile.md`: exact ready-to-paste description and visual configuration
- `rights-and-release.md`: source approval/claim handling
- `launch-checklist.md`: setup and first 30 days
- `source_registry.template.json`: empty rights ledger, not permission
- `branding/clivox-live-avatar.png` and `branding/clivox-live-banner-2560x1440.png`: actual YouTube-uploaded premium PNGs archived from the owner's Downloads folder
- `branding/`: additional original scalable SVG studies, no use of borrowed logos/faces

No raw downloaded third-party video, copyright media, refresh tokens, signed URLs or personal information may be committed to this public repository.
