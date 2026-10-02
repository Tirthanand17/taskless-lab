# FlowMinute Lab — V5 Retention + Visual Design Research

Date: 2026-10-02

## Decision

V5 keeps the existing Power Query "keep latest duplicate" topic, but its key lesson will be expressed as a visible state change:

**Sort → lock/freeze the sorted order → Distinct → verify.**

The realistic Power Query interface remains the primary teaching surface. The lock/freeze beat is a deterministic explanatory animation, not fake software UI.

## Evidence incorporated

### YouTube: optimize for engaged viewing, not raw starts

YouTube announced that beginning 2026-08-24 public views for non-Short formats are counted from the first frame, aligning counting across formats. The original continuation-based measure remains available as **Engaged views** in Advanced Analytics.

Source:
- https://support.google.com/youtube/thread/433409976

Therefore FlowMinute Lab should not treat raw starts as the main quality signal. For Shorts, prioritize:
- engaged views;
- stayed-to-watch / swiped away;
- average view duration;
- average percentage viewed;
- later retention shape when sample size is meaningful.

### YouTube: surface compelling material earlier

YouTube's retention guidance says dips mark skipping/abandonment and spikes can indicate rewatching/sharing. If a top moment occurs later, YouTube recommends introducing compelling material earlier.

Source:
- https://support.google.com/youtube/answer/9314415

V5 therefore opens with the wrong survivor immediately, before explaining Table.Distinct.

### YouTube: avoid interchangeable template videos

YouTube's monetization guidance says original/authentic content should not be mass-produced, generic, or repetitive. Template-like videos with only superficial changes can be ineligible.

Source:
- https://support.google.com/youtube/answer/1311392

V5 must have a topic-specific visual story rather than reusing V4's date-locale choreography.

### Microsoft: the core technical claim is documented

Microsoft states that Table.Distinct does not guarantee which duplicate is preserved because Power Query can fold or optimize operations. Microsoft recommends buffering the table first when predictable duplicate removal is required.

Source:
- https://learn.microsoft.com/en-us/powerquery-m/table-distinct

Table.Buffer loads the table into memory and isolates it from external changes during evaluation. Microsoft also warns that buffering can slow queries and prevents downstream folding, so the Short must present it as a correctness technique for this pattern, not a universal performance optimization.

Source:
- https://learn.microsoft.com/en-us/powerquery-m/table-buffer

## V5 signature visual: Row Lock

During the buffer step:
1. the sorted rows visibly settle into order;
2. a subtle bracket/rail closes around the table;
3. a small "ORDER LOCKED" badge appears;
4. row motion stops completely;
5. Distinct runs only after the lock is established.

The animation explains an invisible evaluation concept without pretending that Power Query itself displays a lock.

## Pacing target

- 0.0–1.5s: proof of failure — 01 Oct sorted first, 12 Sep survives.
- 1.5–6.5s: replay the real UI steps that produced the surprising result.
- 6.5–10.5s: explain that keep-first is not guaranteed.
- 10.5–20.5s: add Table.Buffer and show Row Lock animation.
- 20.5–26.5s: run Distinct again.
- 26.5–28.8s: verify 01 Oct remains.
- final beat: "Sort first. Lock the order. Then Distinct."

## Design constraints

- Real Power Query-looking UI remains >= 70% of visible teaching time.
- No full-screen title card after the first proof.
- Captions remain one line and below the teaching area.
- Use zoom only for failure and verification.
- Row Lock lasts roughly 1–2 seconds and exists only to explain buffering.
- No random particles, fake Excel menus, or decorative 3D.
- Sound: one warning cue, quiet UI clicks, one subtle mechanical lock cue, one confirmation cue.

## Following episode candidate

A strong current V6 candidate is "Excel X-Ray: the invisible CHAR(160) that makes matching values fail."

Signal:
- a 2026-09-17 r/excel discussion received visible engagement around TRIM failing on a non-breaking space;
- Microsoft documents that TRIM removes ASCII 32 spaces but does not remove the non-breaking space character 160.

Sources:
- https://www.reddit.com/r/excel/comments/1wj9281/blank_space_that_cannot_be_removed_by_trim/
- https://support.microsoft.com/en-us/excel/functions/trim-function

The proposed visual is an x-ray sweep over two identical-looking IDs, revealing the hidden character before the real Excel fix.
