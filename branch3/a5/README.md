# Clivox Branch 3 — A5 original-only rendering and AV QA

**Implementation milestone:** a professional **synthetic** 40-second vertical-video rendering benchmark. It is **NOT a creator clip, licensed edit, voiceover, production-ready episode, or YouTube upload candidate**. Creator rights, secure private source storage, channel OAuth, per-video editorial approval and publishing remain blocked.

## What A5 now renders

The fixture at `branch3/editorial/fixtures/ymh_ep347_source_free.json` is an original hypothetical, not a transcript of YMH's show. The A5 renderer creates five typographic editorial scenes using **original procedurally drawn graphics** and restrained silver/orange Clivox branding:

1. Immediate question hook.
2. Original context and imagery.
3. An intentionally **LOCKED / NO CREATOR FOOTAGE** 14-second source placeholder.
4. Independent explanation (nostalgia hypothesis).
5. Specific viewer question.

Every frame includes **DEMO ONLY / NOT CLEARED FOR YOUTUBE RELEASE**. Source audio, external media, copyrighted images and third-party clips are never downloaded or incorporated. Sound is a generated low-volume tone bed with original transition pulses, **not narration or licensed music**. The separate SRT contains proposed *visual editorial text*, **not a transcript of the audio**; it is not burned into the preview because no spoken narration exists.

The placeholder card avoids the repetitive spinning-circle defect reported in earlier FlowMinute videos. A gentle Ken Burns camera movement and dissolve between authored panels offers an early motion-quality benchmark without misleading game or celebrity imagery.

## GitHub-only implementation

- Renderer: `scripts/branch3_a5_render_original_demo.py` (Pillow original typography + FFmpeg H.264/AAC, 48kHz original synthesized tone).
- Technical QA: `scripts/branch3_a5_media_qa.py` (FFprobe actual track readback, dimensions, FPS, sample rate, duration, content hashes and bounded SRT cues).
- Tests: `scripts/test_branch3_a5_media.py` (bad codecs/resolutions, wrong channel, false authorizations, invalid captions).
- CI: `.github/workflows/branch3-clivox-a5-original-render.yml`, running on GitHub-hosted Ubuntu with `contents: read` and no secrets. PR mode renders a 540×960, 24 FPS *preview* for feedback and full mode is a separately manual 1080×1920, 30 FPS original-only quality exercise.
- Output storage: **ephemeral GitHub runner + 7-day public Action artifact containing only original demo assets**. Public GitHub must never store licensed footage or private agreements. No media is committed into the repo.

### Action run results expected
- `clivox-original-only-a5-demo.mp4`
- `on-screen-editorial-script-not-dialogue.srt`
- Five original `scene-XX.png` cards
- `synthetic-demo-manifest.json` with SHA-256
- `synthetic-technical-qa-report.json` based on FFprobe and SRT checks

## How to preview

Open the GitHub Actions run for **Branch 3 Clivox A5 Original-Only Render and Media QA**; retrieve the short-lived artifact from the run summary. The full-resolution run must be manually dispatched from GitHub using `render_mode=full`. That creates **only a synthetic demonstration**.

## What remains before any real licensed clip (A5 not complete)

- Confirm actual creator-issued YouTube commercial clip rights for an exact source, all underlying broadcast/game/music/guest material and any creator-specific restrictions.
- Owner-approved **private** media storage; do not use a public GitHub repository or public Actions artifacts for third-party footage.
- Verify speaker/source quotes and exact clip timestamps; obtain source through an authorized method, never general YouTube scraping.
- Add professional recorded or properly licensed voiceover, intentional sound mix, truthful subtitles matching speech, clip-specific original commentary, real final artistic QA and owner playback.
- Evolve from design benchmark to a separate **rights-gated confidential media** rendering pipeline. This PR intentionally does not have a function that can render external footage.
- Later A6 must sign a QA-reviewed exact video/hash before any uploader exists.

## Hard safety assertions

**No source downloads. No creator clipping permission implied. No production voiceover. No license verification. No private vault. No YouTube OAuth. No uploads, scheduling, or publishing. Branch 1 and 2 untouched and paused.**

Neither a passing FFprobe audit nor a polished visual preview is proof of copyright safety or YouTube Partner Program eligibility.
