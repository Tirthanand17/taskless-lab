# Clivox A2 — Rights-review intake automation (NO APPROVAL)

**Implementation:** 2026-11-12. A2 now has a **pending human-review case generator**, not a legal-rights verifier or a fully functioning campaign management system.

## What happens after every A1 discovery
The manually triggered \`branch3-clivox-a1-discovery.yml\` now produces **two public-safe JSON files** in its 7-day Actions artifact:
1. \`discovery.json\`: bounded public YouTube source metadata and a heuristic rank (A1).
2. \`rights-cases.json\`: a corresponding pending case for each video (A2 intake).

Every review case has:
- A source video ID, canonical YouTube URL, creator channel ID and title.
- Candidate category and source-level research priority (NOT a clip virality score).
- A *reproducible SHA-256 digest of the whole input A1 report* for provenance. This does not prove ownership or license validity.
- \`AWAITING_REAL_RIGHTS_HOLDER_VERIFICATION\` status with fourteen checks marked \`PENDING_HUMAN_VERIFICATION\`.
- All permission, media acquisition, edit, sign, upload and publish booleans **false**; zero creator license grants issued.
- A synthetic marker if the source data was a test fixture, prohibiting accidental use as real audience evidence.

## Human rights checks required (NO AI SELF-APPROVAL)
1. Confirm that the identified creator controls the actual recording/campaign rights.
2. Verify a direct written grant or an authentic creator-published *clipping* policy. Public video availability, view counts and a campaign advertisement are **not** sufficient.
3. Confirm explicit commercial YouTube Shorts reuse, cropping/editing, redistributing, worldwide scope and source-video-specific rights (or legitimate narrower territories as contractually permitted).
4. Clear game publisher rights (GTA VI especially), embedded music, guest faces/voices, film/TV and other third-party source media.
5. Confirm restrictions on dates, timestamps, source context, claims/takedowns, credits, sponsored status, platform terms, geographic audience and expiry/revocation.
6. **Owner must decide personally** on third-party platform registration, contract acceptance, rights/IP assignment, revenue and authorized participation. Content Rewards §17.6 can assign final edits to the brand.
7. Review full original recording for accurate dialogue and context before any meaningful clip editing.
8. If evidence is authentic and sufficient, a future A2 verified-rights approval mechanism may record **non-sensitive references** and a SHA-256 evidence fingerprint; legal grant documents and personal information must remain confidential.

**No current source is licensed.** \`branch3/creator_permissions.json\` remains empty. This case generator never modifies it and has no function to advance to \`RIGHTS_VERIFIED\`.

## Operational usage
The same Actions Run workflow for A1 creates cases after verifying A1 stage and its nonpublishing flags.

For an offline GitHub runner test:
\`\`\`sh
python -B scripts/branch3_discovery.py --mode fixture --category gaming --out /tmp/discovery.json
python -B scripts/branch3_rights_case_intake.py --source-report /tmp/discovery.json --out /tmp/rights-cases.json
\`\`\`

The fixture contains clearly synthetic statistics/channels. **No work occurs in the owner's laptop filesystem**; GitHub runners use ephemeral workspaces.

## Guards tested
- A1 wrong channel, fake source metadata, a source whose rights are already mysteriously \`VERIFIED\`, or a source marked download/upload allowed ⇒ **BLOCK**.
- Synthetic results disguised as real YouTube API data ⇒ **BLOCK**.
- Invalid or duplicate video IDs, malformed channel IDs, outside source URLs, >30 candidates ⇒ **BLOCK**.
- Missing/false documentary checks cannot be marked approved by any scoring algorithm ⇒ **BLOCK**.
- A source-score rank is not a license, a human attestation or an exact segment transcript.
- No secrets, personal email, contract contents, third-party recordings or transcripts are included in public GitHub metadata reports.

## Follow-up (2026-11-13): signed review and revocation OFFLINE preflight\n\n[Signed-review and revocation preview](../rights_review/README.md) now binds a proposed reviewer claim to an exact pending case, channel, source video and evidence digest with domain-separated Ed25519 verification, and separately tests signed revocation tombstones. This is synthetic/offline cryptographic validation, **not a validated reviewer identity, actual creator rights grant or complete revocation ledger**. Nothing can be promoted to `RIGHTS_VERIFIED` or sent to an uploader.\n\n## Remaining A2 work
- A verified identity/rights audit receipt with a real human reviewer, source grant signed by the actual rights holder (or authenticated policy), expiry and revocation handling.
- A private contract/evidence store approved by the owner; no sensitive agreements in this public repository.
- A privacy-preserving signed review ledger and rights-check revalidation before licensed media acquisition.
- UI for approvals; separate final per-video owner signature is still A6.
- No media production until A2 rights are actually verified and A3 private-media storage is approved.

A2 intake is **implemented and tested**. A2 real grant authentication/approval is **pending human evidence and future audited code**, not done.
