# Architectural decision records (ADRs)

## ADR-001: One primary repo for orchestration, no public copyrighted media (ACCEPTED)
The existing Tirthanand17/taskless-lab owns code, CI, public-safe metadata and source fingerprints. Never commit copyrighted raw media, personal data or rights contracts. Future approved private media storage requires user review. Supports cloud-only execution; no desktop disk required for automation.

## ADR-002: Creator-issued permission only, stricter than fair use (ACCEPTED)
A verified direct grant or actual creator-published clipping policy is mandatory for Clivox even if an edit might otherwise qualify for a legal copyright exception. Recheck scope, revocation and all underlying music/game IP. A machine boolean cannot substitute for genuine verified evidence.

## ADR-003: No purely automated approval (ACCEPTED)
Agents recommend hooks/editing, but rights decisions, contract assent, original editing review and exact-media publishing consent are human acts. Versioned signed release metadata is later required.

## ADR-004: Primary target: short commentary-driven Shorts, not captioned reuploads (ACCEPTED)
Initial hypothesis: 25–55 s, vertical H.264 1080x1920, clear payoff and significant original commentary. Actual selection optimized by authentic audience analytics, no fake viral guarantees or rigid thresholds.

## ADR-005: Distinct Clivox OAuth identity (ACCEPTED)
The FlowMinute channel is paused and cannot share token. Confirm channels.list(mine=true) is the exact Clivox channel at each write. GitHub protected environment in later release deployment.

## ADR-006: Private-first scheduled release and atomic upload ledger (ACCEPTED)
Explicit privacyStatus=private even for new API uploads; a future publishAt, never an expired timestamp. Check duplicate inventory before retries, persist immutable remote video ID and actual status readback. Stronger than GitHub Actions concurrency alone.

## ADR-007: Do not bind to third-party clipping marketplace until user accepts terms (ACCEPTED)
YMH Content Rewards terms could assign final approved clip IP to brand. No automatic account opening, joining campaign, payments, submissions or contractual consent. Prefer creator direct independent grant if preservation of Clivox edit ownership is important.

## ADR-008: Public campaign pages are discovery, not rights registry (ACCEPTED)
Maintain researched candidates separate from creator_permissions.json. Need a reviewed rights case to move beyond DISCOVERED.

## ADR-009: Analytics measured only by real authenticated sources (ACCEPTED)
Use official YouTube Analytics/Studio metrics; keep unavailable fields null. Prioritize engaged views, swipe/view, retention, shares, subs not just starts. Never reward fake traffic.

## ADR-010: No premature production deployment (ACCEPTED)
Current architecture CI contains no secrets, no scheduled publishing and no YouTube upload code. Stage A8 requires a separate audited PR, verified actor, protected environment and explicit approval. Good preparation ≠ a released working system.

