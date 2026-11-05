# FlowMinute Phase 3 — original CSV visual-only MP4 proof, October 18 2026

**Status:** real motion video frames now exist and can be encoded/decode-tested. This is an incomplete **visual-only** prototype, absolutely **NOT** a publishable YouTube Short or a verified voice/rendering/autopilot solution.

## What is new

- `autopilot/phase3_csv_visual_preview.py` reads the fixed authored English CSV Short from `autopilot/research_briefs/2026-10-17_csv_bilingual_one_day_scripts_DRAFT.md`, extracts four timed narration lines, and creates a portrait motion-graphics MP4 **without any outside images, fonts, stock footage, account access, internet requests or API tokens**. It uses system-installed fonts, Pillow and FFmpeg.
- Visuals: original midnight navy/cyan/teal gradient, moving parallax grid/particles, pseudo-depth data cards, table/column values, safe-area draft captions, a pretend code demonstration and the fictional `20+30+8=58` total. Every capture includes explicit `ORIGINAL VISUAL STUDY`, `NO AUDIO` and `NOT FOR PUBLICATION` markings. Illustrative simulated UI is labelled.
- **No narration has been synthesized or recorded**; the visual-only output has no audio track. Captions are based on the written script and have **not** been synchronized with any real spoken audio. Different narrator A/B/C plans still need genuine independent voices, careful pronunciation, usage rights and audible review. A real video technical QA that requires AAC audio must **not** pass yet.
- CLI example (on disposable Linux cloud runner with dependencies already provisioned):
  `python -m autopilot.phase3_csv_visual_preview --output /tmp/flowminute-csv-visual-only.mp4 --duration 3 --fps 12 --width 360`.
- Full intended English visual-only draft length is 42 seconds, but every automated CI proof is initially short and bounded; do not report a full three-video production run based on a 2–3 second smoke.
- `autopilot/test_phase3_csv_visual_preview.py` tests four scenes, pixel animation/determinism, source script binding, invalid bounds and an **actual** bounded local FFmpeg/FFprobe MP4 encode/decode, checking that only an H.264 video stream exists and that audio/publishing authorization are explicitly absent.
- The existing public repo Cloud Render Smoke has a second renderer test on a standard public Ubuntu runner using Pillow/FFmpeg and **deletes** the encoded test file. There is no upload-artifact storage or new persistent cloud allocation. The original Remotion smoke remains separate.
- Public standard GitHub-hosted Actions minutes are currently described by GitHub as free for public repositories, but quota-limited artifact/cache storage can generate charges after allowance. We therefore create no additional workflow artifacts and cannot claim that future indefinite production storage is free. See https://docs.github.com/en/billing/concepts/product-billing/github-actions .

## Stage/phase acceptance

Phase **3R2** (original explanatory animation and real usable screen demonstrations): PARTIAL, procedural real visuals demonstrated; actual user-useful screen capture, motion direction quality and final images pending.

Phase **3R1** (natural, appropriately licensed independent voice): BLOCKED — no authentic licensed narration or proof of two distinguishable voices.

Phase **3R3** (two 42s Shorts + one 7m12s long rendered in cloud and stored safely for release): BLOCKED — one visual-only English Short prototype is NOT three finished pieces and no durable, cost-guaranteed cloud media handoff is verified.

Phase **3R4** (factual, spoken, synchronized subtitle, rights, video/audio and final human QA): BLOCKED.

Phase 2R1 real public source provenance and 2R2 independent factual verification also remain incomplete, as do Cloudflare D1 and YouTube OAuth/publishing phases.

**Do not merge the research draft PR merely because CI passes.** No production YouTube permissions, any external account connection, new billing, Google/Cloudflare mutation, desktop/Nirala access, private Actions minute use, video upload or scheduling has been authorized. ₹0 recurring cloud cost cap.

## Quality bar

This proof focuses on **visual execution truth**: actual generated frames, real FFmpeg encoding/decoding and explicit missing-audio reporting, rather than another fake MP4 metadata receipt. It is not yet photorealistic cinematic, real 3D, real product screenshots, natural human speech or final quality. Continue real visual refinement, native-language listening/editing and release rights before any autonomous publication.

**Outstanding production acceptance subphases stay at 21**. Completing a narrow technical subcomponent does not mean completing Phase 3R2 or Phase 3.
