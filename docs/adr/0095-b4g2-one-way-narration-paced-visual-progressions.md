# ADR-0095 — B4g2 narration-paced one-way infographic phases (no spinner, no looping)

**2026-11-07 IST. Branch 2 creative quality. Original educational rehearsal only, NO PUBLISH.**

## Actual encoded-media reason

The first successful fully redesigned 3-MP4 artifact was [GitHub Actions 42349401200](https://github.com/Tirthanand17/taskless-lab/actions/runs/42349401200). The actual exact-SHA256 verified MP4s and sampled decoded video frames showed the original giant caption bug resolved, eleven distinct editorial beats visible and the four graphic grammars legible. Still, on-screen content was nearly static for most of the narration: previously `_encode_full` held a neutral base frame for 0.36s, switched to one highlighted frame and held that single screenshot for up to 55 seconds. The long video had a single 5.92-second detected static/frozen segment at 64.54–70.46s. The FFmpeg warning alone does not prove poor content quality; direct frame inspection identifies the underlying pacing issue.

## Source-locked new progression

This increment retains the **same** original 17 scenes, voiceover words, Kokoro voice and actual PCM timings, two-line native ASS caption placement, footer disclaimer, fact/rights gates and no-publish posture.

- For each of four existing original diagram grammars `compare`, `gate`, `steps`, `matrix`, define **one** semantic progression: no selected checkpoint, then checkpoint 1, then checkpoint 2; numbered steps and sample matrices finally reveal checkpoint 3. There is **no wraparound, return to checkpoint 1, continuous rotation, repeated animation or synthetic factual result**.
- `render_editorial_frame(... focus_index=...)` draws a bounded selected checkpoint using the same original full-res graphic. Invalid IDs, bool masquerading as int, focus index out of range or an active focus in the neutral phase are refused. The original static contact preview still uses its validated last-focus default.
- `physically_render_all_seventeen` paints 3 or 4 genuine different full-resolution frames **per scene**. SHA256 hashes must differ for all frames in a scene. The old first/last one-time reveal provenance remains, with newly explicit stage-count metadata in the QA report.
- `one_way_storyboard_timing_b4g2.stage_hold_seconds` derives FFconcat durations from actual source PCM scene length. A short orienting neutral frame lasts up to 0.36s; the remaining 2–3 original checkpoints hold for equal positive intervals summing exactly to that audio scene. This is **PCM-duration proportional**, not a claim of semantic or per-word speech alignment.
- FFmpeg still fully decodes H264/AAC, burns native-pixel ASS *after* storyboard composition, validates actual first scene changed pixels, and never touches the subtitle-safe panel with animation. No external asset, paid model, credential, user data, public channel or publishing call added.

## Tests and acceptance

The new adversarial suite validates 3/4 distinct stage IDs, physical full-res 17-scene before/after/intermediate PNG differences **confined to the allowed diagram**, exact untouched native ASS caption-card pixels, stage duration sums and noncycling ordering. The existing full MP4 FFconcat fixture is updated to require real staged sequences rather than the old two-frame hold. Other source, rights, voice text and channel gates remain unchanged. Hosted GitHub CI must pass before merge.

After merge, the owner must trigger a **new** main-branch three-MP4 cloud review export and inspect actual decoded scenes. Existing artifact 42349401200 contains the earlier two-stage version and is immutable; passing source tests here cannot certify improved creative engagement, speech/visual semantic synchronization, facts, licensing, owner signoff or real YouTube upload. A future actual 7-day independent 21-video posting test remains unverified.
