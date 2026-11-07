# ADR-0091 — B4f8 real 3-MP4 visual audit: fix subtitles covering original diagrams

**Date:** 2026-11-07 IST | Branch 2 creative QA; **no YouTube publishing or independent source/rights approval**.

## Actual proof — not a simulated quality score

The first real, manually opted-in, end-to-end owner-review export succeeded in [GitHub Actions run 42344844198](https://github.com/Tirthanand17/taskless-lab/actions/runs/42344844198), after the earlier FFmpeg freeze parser fix #104. The **actual artifact** is `flowminute-UNAPPROVED-owner-review-42344844198-1` (13,696,731 bytes ZIP). It contains three originally narrated, source-independent educational rehearsal MP4s (physical H.264/AAC, 1080×1920 Shorts at 59.469s and 57.297s; 1920×1080 long at 241.875s), 17 authored scenes, the 47-entry blank human worksheet, exact MP4 SHA256 manifest, a standalone seekable HTML video player, and physical FFmpeg black/freeze/silence event report.

Actual visual samples at multiple times from **all three final decoded MP4s**, rather than mock or intermediate PNGs, reveal a serious creative defect. Portrait subtitle text displays as enormous 4–6 lines across most of the image, cropping off the shot's title and covering the original teaching cards; landscape subtitles obscure the central diagram and header. This makes all three rehearsals unsuitable for publication **even though the previous source-only caption-line and safe-margin tests passed**.

The FFmpeg report saw **0 long black intervals, 0 long audio silences, and 25 static/frozen warnings** (3 morning, 19 long, 3 evening). These are advisory: a still teaching diagram may be intentional; human must judge when animation needs work. No reviewer, fact verifier or rightsholder has approved these MP4s.

## Root cause and actual fix

`autopilot/full_original_rehearsal_media_b4e1._encode_full` burned SRT with `subtitles=...:force_style='FontSize=27,MarginV=168'` on portrait and `FontSize=24,MarginV=148` on landscape. The FFmpeg/libass path converts SRT to ASS at an effectively virtual **288px script height**, so `FontSize` and `MarginV` are **virtual script units, not final 1080/1920-pixel offsets**. Applying the intended full-output-pixel values directly caused massive vertical/horizontal scaling and misplaced text. The SRT/PCM timestamps and speech coverage remained correct; the broken part was the burned-in *pixel positioning*.

Implemented `_safe_pixel_calibrated_srt_filter`: retain true physical `CAPTION_MARGIN_BOTTOM_PX` (168 portrait / 148 landscape) and convert to virtual style units with `round(pixel_margin * 288 / output_height)` → `MarginV=25` for portrait, `MarginV=39` for landscape. Set the empirically measured bounded font sizes `FontSize=7` portrait / `FontSize=9` landscape instead of 27/24. Use a compact border/shadow; remove the redundant `NARRATION: SOURCE-INDEPENDENT PRACTICE` panel header to reserve actual text space and avoid collision. Keep the original source/fictional disclaimer in the footer and the entire narration SRT untouched.

The physical FFmpeg probe used actual subtitles rendered into synthetic 1080×1920 and 1920×1080 frames and measured changed-pixel bounding boxes after identical color-space normalization:

- 4-line portrait stress: bbox approximately **(188, 1573, 893, 1753)** vs reserved card x=82..998, y=1530..1792.
- 2-line landscape stress: bbox approximately **(552, 871, 1368, 933)** vs reserved card x=82..1838, y=832..952.

The new CI regression *does not trust the authored font numbers alone*: it physically renders both canvas sizes with the real installed FFmpeg and the production-generated filter, then checks every changed subtitle pixel lies within the actual rendered caption card. It also prohibits old huge style values. This prevents the false source-only pass from recurring.

## Remaining validation / no publication

A passing renderer unit/FFmpeg probe **does not** mean the three previously delivered MP4s were repaired: those files are **immutable old outputs**. The next explicitly requested owner review export on the merged code must render all three again, inspect sample frames and actually demonstrate the subtitles stay inside both caption panels. Review of sound/pronunciation, creative motion/hold pacing, unverified facts, media rights, owner signoff, protected account OAuth and all 21 real releases remains necessary.

No live API calls, secrets, account changes, social posts or YouTube video modifications were performed by this patch.
