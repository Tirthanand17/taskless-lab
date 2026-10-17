# FlowMinute Lab — Phase 3: Visual, Narration and Subtitle Production Handoffs
**Checkpoint: 17 October 2026 | Zero-spend staging only**

## What is now implemented

This phase **reuses**, rather than replaces, the working Phase 2 script/language review and the existing 18-stage `agent_org.py` dependency graph. Source files:

- `autopilot/phase3_production.py`: five typed draft production handoffs with upstream SHA-256 bindings and stage-by-stage specialist ownership.
- `autopilot/narration_inspection.py`: reads a **real audio file** with FFprobe and FFmpeg, validates one audio stream, its sample rate, channel count, decode health, duration, SHA-256, large silence segments and maximum size.
- `autopilot/render_inspection.py`: existing real MP4 FFprobe/FFmpeg technical inspector (video stream, audio, dimensions, duration, black frames, file hash). Not equivalent to rights or creative approval.
- `autopilot/test_phase3_production.py`: 23 typed production gate regression tests.
- `autopilot/test_narration_inspection.py`: 10 tests, including **actual locally generated synthetic WAV** signal/silence files and Hindi SRT formatting.

**Full repository software CI:** [202 tests + 6 subtests passed](https://github.com/Tirthanand17/taskless-lab/actions/runs/39037503878). This is only software validation, not actual production or channel-readback validation.

## Five new typed handoffs

| Stage | Specialist | Inputs and constraints | Artifact output |
| --- | --- | --- | --- |
| `storyboard` | `production.storyboard_designer` | Current reviewed script and truthful hooks; contiguous scenes, one real or clearly labeled simulated demo, exact Short 1080×1920 / long 1920×1080 safe frames, no new unsupported factual claims | `Storyboard` |
| `voice_plan` | `language.voice_director` | Separate two-language reviewer record + matching selected-language draft, `energetic` or `explanatory` narration profile, declared rights reference and narration identity | `VoiceDirection` |
| `narration` | `production.audio_specialist` | Digest of voice plan, recorded audio hash, claimed duration and origin metadata. If storyboard is present, compare planned audio/visual duration. **Input is unverified metadata until an actual file is probed** | `NarrationAssetRecord` |
| `subtitle_plan` | `language.subtitle_specialist` | Current narration and localized-text digests, same language as selected narrator, non-overlapping safe one-line captions within planned audio timeline | `SubtitleTimeline` |
| `render_plan` | `production.renderer` | Requires storyboard **and narration and subtitles** to be complete; exact matching digests, bounded 1 GB estimate, FFmpeg Motion V2 / Remotion staging route, H264/AAC MP4 output | `RenderRecipe` |

A successful staging handoff **does not self-create** `qa.media_attestation`, `qa.rights_attestation` or `qa.release_attestation`. Those stages remain separate independent gates. All `publishing_enabled`, `uploads_enabled`, `scheduling_enabled` and `cloud_deployed` fields remain **false**.

## Motion V2 integration compatibility

Existing [`motion-v2/README.md`](../motion-v2/README.md) establishes continuous animation, 2.5D visual treatment, centered teaching visuals and subtitle safe areas. This phase's scene contracts allow purposeful `motion_2d`, `animation_3d`, actual `real_screen`, `explanatory_diagram` or a clearly labeled `labeled_simulation`. It does **not** call Motion V2 or Remotion automatically, fabricate a real product demo, or assume any particular cloud render capacity.

Existing [`motion-v2/natural_narration.py`](../motion-v2/natural_narration.py) uses English-focused voices and explicitly states synthetic speech is not guaranteed to sound natural. The Hindi branch requires additional real voice evaluation and **commercial-use/licensing verification**, even if a free text-to-speech API is technically reachable. A plan with a `rights_reference` alone is NOT independently authenticated rights clearance. Do not introduce paid voice providers or make an account connection without owner approval.

Subtitle conversion `subtitle_timeline_to_srt` can produce the **text format only**; it is not automatic speech recognition, forced alignment to audio, listening-based proofreading or uploaded YouTube captions. The tests use synthetic records, not genuine Hindi audio or a verified narrator.

## Test execution

From the public software project root:

```bash
python -m pytest -q autopilot/test_phase3_production.py autopilot/test_narration_inspection.py
python -m pytest -q
```

No live YouTube API calls, Google OAuth token use, account changes, billing changes, new cloud connections or Nirala access are part of these tests.

## What is still required for real independent Phase 3 release quality

1. **Generate or record one rights-cleared Short narration and one representative long narration**; inspect actual audio, listen for pronunciation, rhythm, language and naturalness. Maintain two meaningfully different Short narrator personalities without cloning an unauthorized person's voice.
2. **Render original educational scenes** (real reproducible screen demo, appropriate 2.5D/3D/animation), with accurate title/caption safe areas. Check actual scene/frame correspondence to the reviewed script.
3. **Run real subtitle/transcript alignment**, English/Hindi proofread and detect timing/safe-area collisions on the final frame sequence; a syntactically valid SRT is not sufficient.
4. **Independently validate media rights** (commercial permission for voices, music, video/graphics, third-party UI, attribution), and record a verifiable review decision. No imaginary licenses.
5. **Inspect a full Short and representative long-form MP4** with file-level QA plus independent human/editorial review. Current generated WAV fixtures are synthetic two-second tests only.
6. **Verify policy-compliant, durable ₹0 render and media storage capacity**, not the historical repository benchmark alone. Heavy GitHub-hosted runner jobs cannot be presumed an unlimited video farm.
7. After Phase 3, connect a single authoritative cloud task/release ledger, resolve the seven-day Google External/Testing OAuth limitation and separately obtain authorization for a controlled private upload pilot.

## Next engineering work

Stage a **media-and-rights independent review adapter** that receives actual FFmpeg file evidence and declared licenses, but cannot mark any release approved without auditable reviewers and external media/rights evidence. Evaluate budget-safe cloud execution only after that gate is tested.

**Never describe staged `RenderRecipe` as an actual video, or an audio-hash claim as a verified human-sounding narration.**
