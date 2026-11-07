# ADR-0089 — B4f7 root-cause fix of real 1080×1920 caption clipping

**Observed evidence:** 2026-11-07 actual opt-in owner-review MP4s (GitHub workflow run [42344844198](https://github.com/Tirthanand17/taskless-lab/actions/runs/42344844198), original artifact ID 13563592148) were physically decoded and sampled. Both 1080×1920 Shorts had **giant white subtitles clipped off the frame's TOP edge and obscuring the first third of each scene**, despite previous B4e2 SRT line-count checks passing. The long clip showed less severe, but still material, diagram/text overlap. Sampled frames cannot replace full owner listening/watching. These artifacts are unapproved original synthetic exercises; no news fact or rights approval.

## Actual failure mechanism

The existing `full_original_rehearsal_media_b4e1._encode_full` used `subtitles=...srt:force_style='FontSize=27,MarginV=168...'` on a 1080×1920 Short. SRT is decoded through a synthetic libass presentation scale (typically 384×288) rather than pixels of the actual portrait MP4. Thus `FontSize=27` is not 27 output canvas pixels; text in original decoded Shorts ballooned toward 180 actual vertical pixels, blanketing foreground artwork, while the old validator only counted SRT lines and called the caption panel safe. Height-based `MarginV` did not rescue it.

## Implemented correction

New `autopilot/full_original_caption_ass_b4f7.py` composes true **native-pixel ASS** with `PlayResX: 1080; PlayResY: 1920` (Shorts) or `PlayResX:1920; PlayResY:1080` (long). It reuses proven `polished_caption_v2.caption_cards` to split **actual PCM-timed narrator sentences** into compact two-line microcards (short: ≤29 visible characters per line; long: ≤42). All original words, syllable timings, order and audio samples are preserved; no subtitles rewritten or AI-generated.

- Short caption style: fixed 43px DejaVu Sans, centered at (540,1680), protected original panel top 1530px, bottom 1792px, subtitle glyph band 1614–1764px.
- Long caption style: 36px at (960,883), dedicated expanded panel top 760px, bottom 952px, glyph band 829–935px.
- No synthetic SRT PlayRes; **only `ass=EPHEMERAL_NATIVE_PIXEL_VOICE_CAPTIONS.ass`** is burned in FFmpeg at 24fps before H.264/AAC encoding; the separately generated SRT remains optional reference/evidence but is never burned.
- Subtitle styles explicitly declare font family/size, outline and native resolution. Per-caption explicit center anchoring avoids inherited alignment/margins. No caption is allowed to escape the fixed protected panel to make room for a too-long phrase.
- A body progress-bar/panel collision fails closed rather than overlaying. No spinner, loader, repeating rotation, stock art, third-party copyrighted frame or upload operation is added.
- Old tests were upgraded to reject `subtitles=...force_style` reintroduction and require exact ASS script geometries; a new real FFmpeg physical-glyph test renders each ASS overlay against black source frames at the native 1080×1920 and 1920×1080 resolution and checks that every bright glyph pixel resides within the reserved band. Source-line count alone is no longer acceptance evidence.
- The 17-scene real GitHub cloud workflow will now assert `native_pixel_ass_burned_into_reserved_panel=true` and `max_original_spoken_caption_lines_physically_burned=2` on all 3 physical MP4s. No approval flags are changed.

## Acceptance and limits

1. Four exact-head GitHub CI checks pass, including the new physical pixel test, B4e2 staged-reveal regression, actual H.264/AAC smoke, unprivileged no-publish agent pipeline.
2. Merge, then manually opt in to a fresh one-day GitHub artifact. Physically inspect representative frames and listen to the three complete new MP4s, compare fixed visual captions to the previous artifact's obvious top-of-frame giant glyphs. Do not claim verified creative quality until the new output is actually inspected.
3. The serious issue is **Branch 2 rehearsal-only caption burn**; it does **not repair already scheduled Branch 1 YouTube Shorts**. In-place edits to published Youtube media are limited; modifying frames generally requires a new upload, separate factual rights signoff, and avoidance of duplicate scheduled Shorts.
4. Static cards and 25 FFmpeg freeze warnings in the previous artifact need editorial polish; eliminating caption clipping is necessary but not sufficient for original motion variety and engagement.
5. This is not a live publisher; original synthetic practice scenes have no factual, news, media-rights or human full-watch approval, no authenticated owner upload/readback, and the 7-day unattended 21/21 YouTube publication target remains 0/21.
