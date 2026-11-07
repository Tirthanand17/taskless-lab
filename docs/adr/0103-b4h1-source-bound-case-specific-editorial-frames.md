# ADR-0103 — B4h1 source-authored case identity appears in actual editorial frames

**2026-11-07 IST | Branch 2 original cinematic educational rehearsal | NO PUBLISH**

## Observed problem
Merged B4h0 (#120) now writes 42 author-controlled fictional teaching cases and rotates them over seven days. Real B4f9 storyboard artwork still used only 11 generic pedagogical headings. A new story name would affect the short voiceover/title but could leave all the explanatory visual labels identical across days; this weakens watchability and creates an apparent voice/visual mismatch.

## Decision and provenance
- The original B4d9 non-factual script includes the **synthetic case family** and its **authored short case title** in each episode. These two fields come exclusively from the seven-entry casebook for the current selection, not a news lead, public source title, web text or a model-generated claim.
- Preview and full 17-scene physical render plans carry exactly that case identity; the latter reconstructs the existing source/docket validation and checks it agrees with the preview.
- The full-resolution Pillow storyboard independently rederives the expected case title from the canonical episode date and slot and the fixed author-controlled casebook. Forged dates, cross-slot IDs, unsupported families, and injected/unapproved article titles are rejected.
- The lesson's **case name** appears above the diagram in each of the 4/9/4 scenes, below the original beat-specific editorial explanation. Its native-glyph dimensions fit both 1080x1920 portrait and 1920x1080 landscape. It does not intrude on the actual diagram, one-way phase highlights, source-PCM narration, or the ASS subtitle panel.
- Pixel tests compare neighboring-day case titles on equivalent actual storyboard frames and verify subtitle pixels are unchanged; 42 authored case labels are checked against real DejaVu glyph bounding boxes. This is a limited context-specific visual improvement, not a complete illustration of the detailed scenario mechanics.

## Safety boundaries
No external footage, title/feed sentences, article quotes, screenshots, downloaded graphics, voice model changes, paid inference, owner authorization, YouTube API, new secrets, scheduled/published video edits or workflow publication permissions. Exact and near-duplicate source-only script fingerprints still run before CPU voice/video work. The preview remains **non-factual and unapproved**, and the owner must still inspect real encoded outputs.

## Evidence requirement
Four exact-head no-publish GitHub CI checks including physical Pillow tests must succeed before merge. Post-merge main workflow success and real owner-reviewed three-MP4 evidence are separate milestones. No progress points or YouTube releases are credited for PR count alone.

**Production readiness remains conservatively 45/100; 0/21 independently verified unattended YouTube releases.**
