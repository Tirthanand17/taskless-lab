# Branch 3 — Clivox (SECOND YouTube channel)

**Status:** research and channel-ready branding only. No YouTube channel creation verified; no content licensed; no uploads or publication authorized.

**Isolation:** Branch 1 (existing FlowMinute Lab scheduling) and Branch 2 (autonomous FlowMinute publishing) are paused. Do not change their code, channels, schedules or credentials. This branch shares the existing repository for planning and branding but uses completely separate channel identity, source-rights registry, approval process and future credentials.

## Channel identity (proposed, not claimed)
- Display name: **Clivox**
- Preferred handle: **@Clivox** (availability must be checked live on YouTube)
- Focus: original explanations of compelling moments from podcasts, interviews and long-form creator discussions
- Language: English first; no assumption of language rights
- Tagline: **Clips worth watching. Context worth knowing.**
- Video style: creator-approved excerpt + original commentary/critique/story, source attribution and clear factual context
- Profile and banner SVG: `branch3/branding/`
- Final channel About copy: `branch3/channel-profile.md`

## Explicit creator-permission rule
Only material covered by direct written creator/rights-holder permission or an authentic public clipping policy from that creator enters the candidate pipeline. We never treat a viral video, Fair Use speculation, a general downloadable link, third-party CC upload, or credit-only attribution as blanket permission. See `scripts/branch3_creator_permission_gate.py` and `creator_permissions.json` (empty by default). A permissions record can qualify a proposed candidate for human review; it **never** authorizes upload itself.

## Hard launch gates
1. Human owner creates/selects **new** channel through official YouTube channel creation flow and records its new channel ID. Never reuse the existing FlowMinute Lab channel.
2. Securely verify new channel owner access; do not copy existing FlowMinute Lab OAuth tokens to the new channel.
3. For every reused segment: prove original publisher's ownership, creator-issued written permission or an authenticated creator-published clipping policy for reuse **and** editing, redistribution, Shorts and commercial use where applicable; verify underlying third-party footage/music rights separately. Store only consent reference and non-sensitive metadata in repo.
4. Add substantial original educational/critical context. Avoid bare reuploads, generic templates and misleading crops.
5. Independent creator/rights/editorial and final playback review; no uploads while approval is missing.
6. No guarantee of zero Content ID claims, strikes or monetization eligibility.
7. Keep all publishing automation off until the user separately approves after channel creation.

## Files
- `creator_permissions.json`: initially empty creator allowlist; no creators eligible by default
- `scripts/branch3_creator_permission_gate.py`: fail-closed candidate intake check; never upload permission
- `research.md`: policy evidence and strategy
- `channel-profile.md`: exact ready-to-paste description and visual configuration
- `rights-and-release.md`: source approval/claim handling
- `launch-checklist.md`: setup and first 30 days
- `source_registry.template.json`: empty rights ledger, not permission
- `branding/`: scalable original SVG art, no use of borrowed logos/faces

No raw downloaded third-party video, copyright media, refresh tokens, signed URLs or personal information may be committed to this public repository.
