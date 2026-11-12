# Clivox Branch 3 — A4 original editorial studio (source-free)

**State:** Source-free editorial drafting and validation only. No creator quotes, licensed media, audio recording, render, uploads or publication.

## Why original commentary is central
YouTube's October 1, 2026 Shorts recommendation update prioritizes original contributions over copied clips. Its reused-content/inauthentic-content policies require genuine new storytelling, critique or entertainment value. Captions, crops and templates alone are not sufficient, and numeric scene ratios cannot prove monetization eligibility.

Official references: https://support.google.com/youtube/blog/470890423/prioritizing-original-content-on-shorts and https://support.google.com/youtube/answer/1311392

## Category-specific Clivox editorial approaches
| Category | Distinct original Clivox perspective | Rights and factual checks |
|---|---|---|
| Gaming / GTA VI | Explain *why* a notable play worked using original tactical diagrams | Streamer, publisher, broadcast audio, leaked footage/spoilers, match facts |
| Livestream | Explain verified setup and stakes of the genuine reaction | Recording rights holder, guests, sponsorship, music |
| Comedy | Original comic analysis or a clearly marked hypothetical | Publisher and performer, full context, permitted subjects, contracts |
| Entertainment | Distinguish verified event from rumor; an original interpretation | Film/TV/music, likeness, attribution |
| Podcast/interview | Explain nuance, significance or disagreements with original research | Episode rights, speaker context, accurately verified quotes |

One static interchangeable script is NOT originality; a human editor still decides if new viewer value is meaningful.

## Implemented in GitHub
- Original research-only YMH Episode 347 fixture: branch3/editorial/fixtures/ymh_ep347_source_free.json. The research chapter *suggests* an '80s restaurant conversation; the premise and exact quote/timestamps remain UNVERIFIED.
- Script storyboard checker: scripts/branch3_a4_editorial.py. Checks Clivox account identity, 9:16 timeline, source placeholder stays empty, original hook and commentary, source-free facts, safe-margin plan, all release flags false. Outputs a reproducible content digest and a HOLD report.
- Adversarial tests: scripts/test_branch3_a4_editorial.py. Check forged licenses, hallucinated source quotes/timestamps, unsafe captions/music, wrong channel and incomplete timelines.
- CI: .github/workflows/branch3-clivox-a4-editorial.yml. Read-only, offline, no secrets, video files, YouTube requests or publishing.

## Planned owner and licensing steps
1. Independently verify the source creator commercial clipping grant and separate music/game/guest rights; do not auto-join the Content Rewards marketplace.
2. Provision owner-approved private vault under A3; never place third-party footage in public GitHub/Actions artifacts.
3. Watch the exact licensed segment in context; establish true speaker quotes/timestamps and identify all restricted media.
4. Replace the empty segment slot only after clear permission and verified source context.
5. Record original narration, graphics and distinct narrative framing; test comprehension and watch on a phone.
6. Pass A5 audiovisual and subtitle QA, owner-review the exact render, and pursue A6 signed release.

**A4 reports are a source-free storyboard audit, NOT proof of originality, a legal grant or a production release.** The demo plan is 40 seconds, with an empty 14-second future source slot.
