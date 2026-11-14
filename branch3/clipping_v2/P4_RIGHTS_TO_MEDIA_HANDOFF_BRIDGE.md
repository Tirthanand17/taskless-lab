# CLIVOX V2 — P2/P3 real creator rights → P4 private-source readiness bridge

**State:** source-free, offline **HOLD** engineering. No creator permission, private-media vault activation, source download, clip generation, signed final release, YouTube upload or publication. This is **not** a completed P4 milestone.

## Why this bridge exists

Existing P2/P3 research/owner decision tooling and A3/P4 private-storage quarantine had independent checks. This integration uses their **real current code paths** together, without inventing an agreement, to surface the exact blockers between "research about potential licensors" and "accept a creator-provided original media master."

- `scripts/branch3_v2_p4_rights_storage_bridge.py` reconstructs a **validated** P2/P3 five-prospect, all-unapproved matrix; checks current A3/P4 closed policy; validates the A3 **offline fixture** exactly. It creates a sanitized JSON report with 7 unmet real-world dependencies and every live operation disabled.
- `scripts/test_branch3_v2_p4_rights_storage_bridge.py` rejects fabricated owner shortlist approval, creator licensing, per-prospect consent, P4 vault activation, source fetch or write switches, as well as forged A3 live readback, and insists the production ingest entrypoint is unavailable.
- Existing P4 GitHub Actions checks the bridge in the no-secret, no-media runner plus existing synthetic H.264/AAC/FFmpeg checks. Nothing is transferred to or retained by GitHub artifacts.

## Owner-controlled real-world progression

1. **P2:** review and independently verify actual streamer identity, source channels, business affiliation and original long-form footage; owner selects a creator. Public contact pages are *not* legal rights evidence. Proposed creator messages remain UNSENT.
2. **P3:** communicate only after distinct owner authorization for outreach. Obtain a real signed commercial redistribution/monetization **grant for CLIVOX**, exact master recordings, permitted edit/transformation, platform, term, territory, attribution, restrictions and revocation process. Separately confirm guests, copyrighted music, game-publisher or platform contractual limitations.
3. **A3/P4:** choose a **private media storage service** that is contractually permissible. Review private ACLs, machine identities/installed apps, encryption, retention, quotas, ownership, egress, logging and revocation access. An observed private GitHub repository or an A3 metadata readback **does not authorize media storage**.
4. **P4:** the verified creator directly delivers the specifically licensed original master through the approved confidential handoff. Only a separately security-reviewed **private** runner can authenticate rights/signatures, current revocation state, exact file hash and malware/media decoding, with no public GitHub content, CI artifact or public logs.
5. **P5–P9:** continue with accurate human-checked moment selection, genuinely original CLIVOX commentary, secure render, exact final video/rights review and signed **separate** owner-approved private-first YouTube upload.

## How to verify (public repository, no creator media)

```sh
python -B -m unittest -v scripts.test_branch3_v2_p4_rights_storage_bridge
python -B -m scripts.branch3_v2_p4_rights_storage_bridge --mode closed
```

Dependencies are the existing Python project plus pinned `cryptography==46.0.3` used by the A2 closed rights validator. The CLI only prints sanitized status. It does **not** accept source paths, private vault IDs, licenses, recipient addresses, URLs, passwords, OAuth credentials or any action to modify creator material.

### Acceptance versus real completion

Passing this bridge means **only** that a source-free dependency graph correctly prevents unverified public prospect research from becoming real private media ingest. It does **not** establish a legally valid grant, an approved vault or an actual authorized media pipeline. Production checkpoints remain **2 of 12 = 17%**, with ten human/legal/production milestones still pending.

The original FlowMinute Branch 1 and 2 workflows are untouched.
