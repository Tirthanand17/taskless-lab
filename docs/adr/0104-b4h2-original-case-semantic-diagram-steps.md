# ADR-0104 — B4h2 map original fictional lessons to diagram steps, not only captions

**2026-11-07 IST | Branch 2 source-bound illustrative media | NO PUBLISH**

## Defect
B4h1 physically displays the source-validated fictional case name, while the case's visual **diagram** still used the same generic labels in nine editorial beat types for every case. A valid daily voiceover could therefore describe a calendar conflict while the graphics continued to say only INPUT / PROCESS / OUTPUT. This does not meet the aim of narration-relevant visuals.

## Implementation
- Add a bounded, authored mapping for **all 42 B4h0 cases**, each with exactly three short, distinct semantic tokens representing a start, decision/risk, and verification/recovery stage (example: *Double booking* → SLOT / CONFLICT / CHECK; *Public link* → PRIVATE / PUBLIC / CONFIRM).
- During rendering, revalidate the 42-case day/slot/title source lock from B4h1. The four distinct existing B4f9 diagram grammars (comparison, timeline, sample matrix, review gate) use the appropriate curated case steps in the nine synthetic lesson/example beats. The **SOURCE_SCOPE** and **FACT_AND_RIGHTS_GATE** beats retain their unchanged universal editorial warning text.
- Preserve exact 17 scenes, one-way progressive focus, native-pixel ASS subtitle panel, current PCM audio and SFX, published/private video isolation, 0 paid inference, 0 provider calls, 0 upload authority, and all physical QA checks. No new images, licensed content or scraped claims.
- Reject a mismatched or incomplete case-label library at module import rather than silently falling back to generic labels. Only 2–8 character uppercase card words are permitted and font bounds are independently tested for portrait and landscape.
- Verify that switching to the next authored case physically changes pixels **inside the educational diagram**, not merely in the title, while keeping subtitle safe-area pixels identical. Keep research/rights gate labels exactly unchanged.

## Reality check
Short case words and static diagrams are still a limited explanatory illustration, **not** independent real-world fact verification, a filmed reenactment, owner-approved art direction, unlimited generative scenes, a real source interpretation or an automatic publishing permission. More original visual mechanisms and actual owner playback remain needed before release.

**Production readiness remains 45/100; independently verified unattended releases 0/21.** Accept only after four exact-PR-head green no-publish workflows and a separate real main cloud run.
