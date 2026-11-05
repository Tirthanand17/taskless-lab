# FlowMinute Phase 3R3 — full native-HD silent Shorts from bounded segments

**18 October 2026 — technical media only. NOT a YouTube release.**

## What is implemented

`autopilot/phase3_full_hd_short_assembly.py` binds the two existing authored CSV Shorts (`csv_tutorial_short_en`, `csv_tutorial_short_hi`) to exactly **42 contiguous one-second H.264 video-only segments each**. Each segment uses the existing real original English or Devanagari-shaped Hindi animated infographic renderer, from the corresponding script/estimated SRT positions at 24 fps and 1080×1920 resolution.

The two individual renderers still **refuse to produce more than 36 native-HD frames per invocation**. The full movie assembler therefore creates and validates only 24 frames at a time, with no hidden increase to that guardrail.

The assembler:
- Rejects unknown episode IDs, output overwrites, symlinks, missing destination directories, missing FFmpeg or FFprobe, and insufficient scratch disk.
- Creates scene MP4s **inside an automatically removed temporary directory**, validating H264 codec, exactly one video stream, **no audio**, 1080×1920 dimensions, 24 fps, exact frames/duration per segment.
- Uses a locally generated relative-path `ffconcat` manifest and FFmpeg stream-copy to assemble a whole 42s portrait H.264 MP4. Rejects anything other than **1,008 frames, 42-second duration, silent video-only**, and independently decodes the complete output.
- Removes the final MP4 if the assembly, validation, decoding or resource cap fails. Only returns an unprivileged SHA256, size and timing receipt; no paid service, clip upload, personal data, external images or model weights.
- Has an internal 360-second render wall-clock stop and an additional 240-second **per Short** timeout in the public cloud smoke job; the existing GitHub standard-runner workflow cleans up all outputs even if validation fails.

Tests `autopilot/test_phase3_full_hd_short_assembly.py` cover original exact-script episode plans, 42×24 frames, 1,008-frame continuity, fail-closed paths, wrong/unknown long-form, real 24-frame full-HD H.264 encode/probe, and permanently FALSE release/speech/rights flags.

## Validation planned / acceptance boundary

The public `flowminute-cloud-render-smoke.yml` job now actually attempts **both complete English and Hindi silent 42s native-HD 1080×1920/24fps movies**, beyond the earlier one-second benchmark. A successful job must explicitly report these markers for the exact branch HEAD:

- `COMPLETE_NATIVE_HD_42S_ENGLISH_SILENT_SHORT_QA_PASSED`
- `COMPLETE_NATIVE_HD_42S_HINDI_SILENT_SHORT_QA_PASSED`

The prior 1-second native-HD benchmarking step also remains, as do the complete silent low-resolution 42s+42s+432s verification and synthetic-tone AAC mux check. Every resulting file is disposable and deleted. **Do not claim full HD completion until the exact run concludes successfully.**

## Unfinished production

Even successful **silent native-HD** video is not a finished monetizable release. No authentic natural Hindi/English licensed voice, two audibly distinct speaker recordings, real speech-to-SRT sync, truly professionally reviewed instructional VFX/photorealistic 3D, independent source factual approval and rights clearance, secure durable no-cost cloud media handoff, completed 1080p native-HD 7m12s long, OAuth/D1 release control or actual YouTube publishing. `publishing_authorized=false` is non-negotiable.

The user authorized **₹0/month recurring cloud infrastructure**, public GitHub standard runners only, no new model downloads/services/paid jobs, no Nirala/laptop, and no YouTube upload/schedule/publish without owner approval. Research PR #5 and controller PR #4 remain DRAFT and unmerged. **21 production acceptance subphases remain open**—native full-HD silent Short engineering is a subcomponent of Phase 3R3, not a completed delivery system.
