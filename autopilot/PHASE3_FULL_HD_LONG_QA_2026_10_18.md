# FlowMinute Lab — Phase 3R3 full native-HD 432-second Hindi long render, silent QA

**Date:** 18 October 2026. Public development **DRAFT PR #5** `feature/flowminute-phase2-evidence-preflight`, no merge and no production deployment.

## Engineering design

- `autopilot/phase3_full_hd_long_assembly.py` renders the original authored 7m12s Hindi/Hinglish CSV educational video as **432 one-second, 24-frame segments** at **1920×1080 landscape, 24 fps**. This respects the pre-existing `MAX_HIRES_FRAMES=36` limit on every per-clip `render_hindi_visual_preview` call. The intended stitched output has exactly **10,368 frames** and lasts **432 seconds**.
- It validates actual original Hindi storyboard coverage and segment alignment; rejects unknown or altered scene lengths, existing media paths, symlink or non-existing output directories, inadequate temporary free space, missing FFmpeg/FFprobe, excessive run duration and unsupported video sizes.
- Each scene clip must be H264, **one video stream and NO AUDIO**, 1920×1080, exactly 24 frames/1 second and within a strict size cap. Stream-copy concat uses only fixed locally generated safe relative filenames; full movie must pass FFprobe for exact frame count/length/resolution/no audio and complete FFmpeg decoding. SHA256, size and measured render wall time form the report.
- Single job **780 seconds total internal runtime cap**; the public Actions QA uses an additional `timeout 850s` and `timeout-minutes: 18`. It runs a standard GitHub public Ubuntu runner with the already used open-source FFmpeg, Pillow, fonts-noto-core; no secrets, desktop, external content accounts, voice downloads, API service or paid machine.
- Temporary scene clips and final MP4 are never uploaded as an artifact. The separate QA job removes any output in an `if: always()` cleanup step, including failures. The user cannot download an ephemeral file after it is deleted.
- The output always declares **NO HUMAN VOICE, NO LICENSED MEDIA, NO INDEPENDENT FACT APPROVAL, NO AUDIO/SRT ALIGNMENT, NO PUBLISHING AUTHORITY**. This is a technical video proof, not cinematic quality/monetization approval.
- `autopilot/test_phase3_full_hd_long_assembly.py` tests exact 432-second timeline/10,368-frame plan, output overwrites, symlinks, missing folders, zero release authority, and a real FFmpeg 24-frame 1920×1080 Hindi scene with negative incorrect-frame probe.
- Existing separate public cloud render smoke already verified two 42-second native-HD silent Shorts at 1080×1920/24fps (1,008 frames each), plus three full-duration low-res silent movies. See https://github.com/Tirthanand17/taskless-lab/actions/runs/39091529781 .

## Acceptance truth

**Do NOT report the full 432-second 1920×1080 as rendered until the dedicated QA job has actually completed successfully and its log contains final `REAL_NATIVE_HD_432S_HINDI_SILENT_FULL_DECODE_NO_RELEASE` with 10,368 frames.** A passing source code test or scene sample is not evidence that the entire video rendered.

### Still unavailable for production

- Rights-cleared natural Hindi and English narration, two audibly distinct Short speakers, true speech-to-caption synchronization, final visual/cinematic quality/editorial factual review, licensed source/media/speech rights, durable free cloud video storage, authorized Cloudflare D1 and YouTube account OAuth/real private publishing pilot.
- Existing three-script CSV content is still a draft and the only viable proof is an original infographic video, not photorealistic real-world 3D.
- Public PR #5 and separate publishing controller PR #4 remain **DRAFT / UNMERGED**. No production upload, scheduling, YouTube change, OAuth connection, new paid service, external model download or Nirala/laptop access.

**Budget:** ₹0/month recurring infrastructure, standard public GitHub-hosted runner only, no billable larger runners or stored workflow artifacts. **21 tracked production acceptance subphases remain unfinished**, including genuine licensed full-media delivery.