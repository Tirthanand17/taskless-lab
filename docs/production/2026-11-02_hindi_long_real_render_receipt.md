# FLOWMINUTE LAB — Real Hindi Agent Permissions Landscape Film (2026-11-02)

**Status: TECHNICAL QA PASSED; OWNER/HUMAN FINAL APPROVAL NOT YET GIVEN; NO YOUTUBE PUBLICATION.**

## Finished media for owner preview
- Original 16:9 Hindi educational film topic: "AI Agent को कितनी Permission दें? Read-Only, Approval और Backup"
- Source code: `motion-v2/src/AgentPermissionLongHi.tsx` with timing `motion-v2/src/flowExplainLongHiTiming.json` generated from audio in an ephemeral GitHub runner.
- Original teaching narration: `content/flow/agent_permissions_long_hi_narration.json` — 6 chapters and **29 phrases**, approximately 390 whitespace-separated Hindi words.
- Review voice: Kokoro ONNX `hf_alpha` synthetic Hindi; voice total approximately **155.669 seconds** and phrase-timed SRT generated from the same audio stem. Human quality approval FALSE.
- Successful full cloud-render job: https://github.com/Tirthanand17/taskless-lab/actions/runs/41431772149
- GitHub Actions review artifact: `flowminute-hi-agent-permission-long-full-review-only` ID 13134682130, one-day retention. This artifact is NOT durable owner media storage.
- Real full original Remotion output: `FLOWMINUTE_AI_AGENT_HINDI_LONG_REVIEW_ONLY.mp4` SHA256 `518b44a137bbdddec32ee84e7f64cbe0c55e49ae52fab277f75d1bb3158fbb2c`.
- Original video **1920 × 1080**, **24 fps**, **3737 video frames**, **155.712 seconds (2 minutes 35.712 seconds)**, H.264 and AAC 48kHz. Complete FFmpeg decode succeeded; dynamic frame count and duration checks matched the generated narration.
- Source voice `flow-explain-long-hi.wav` SHA256 `869f40af5a79a663e2e92387f5c9bd0cfda1347f3d22d117008ad58f03223c0b`.
- Original mix measured approximately **−19.5 LUFS**, true peak **−3.3 dBTP**.
- ChatGPT sandbox review master: `FLOWMINUTE_HI_LONG_AUDIO_MASTER_REVIEW_ONLY.mp4` SHA256 `05cd121643df040727b9e8490341c4bf6e881d27728edea42e3c2de8aa16a213`. H.264 video copied unchanged and AAC audio adjusted to approximately **−18.1 LUFS**, **−1.7 dBTP**; entire encoded video/audio decoded successfully.
- Six sampled actual film frames visually inspected. Layout remains aligned and Devanagari correctly renders in the persistent dashboard. There is modest movement through chapter state/permission flow. This **does not establish reference-creator premium animation parity, voice naturalness, or all-frames mobile/UI inspection**.

## Owner review handoff
- `FLOWMINUTE_LAB_2026-11-02_THREE_VIDEO_REVIEW_PACKAGE.zip` exists in the conversation sandbox, containing English and Hindi Shorts **already accepted by the owner for upload**, plus this long film **NOT YET reviewed or approved**. The ZIP also includes three SRT tracks, two Short covers, one long film contact sheet, QA and SHA256 manifest.
- This conversation artifact is not stored in the repository and should not be assumed accessible to GitHub Actions. The long master is a **different binary hash** from the GitHub-rendered original; an eventual publisher must use the exact file the owner approves.
- Source metadata: `content/episodes/fm_20261102_agent_permissions_long_hi.json`.
- Fail-closed human approval record: `state/approvals/fm_20261102_agent_permissions_long_hi.json`, with owner approval / voice / exact captions / rights / factual / final creative flags all FALSE and `approved_video_sha256: null`.
- This is 16:9 standard YouTube video format, not a vertical Short. It is relatively concise for long-form: about 2m36, not a multi-minute deep tutorial.

## Release and safety
- No actual YouTube API call, video ID, uploaded private video, scheduled release or public post has occurred for any of the three new pieces in this chat.
- Protected API credential `YOUTUBE_TOKEN_JSON` may exist in GitHub Actions but is not available here. The connected GitHub tool does not support workflow dispatch; private control policy still records `publishing_enabled:false`.
- Existing production uploader Hindi caption bug was fixed in development branch via commit `6cdd8ab3597d7e8659da9a2b212f298d360b92d9`; separate no-secret publisher preflight CI passed, but code is not necessarily merged into production.
- No paid provider/API credits, new repo, personal laptop or Nirala access was used. No existing releases were overwritten or silently republished.
- Human review must listen to the full Hindi take, assess pronunciation/intonation, caption accuracy, licensed media, and whether chapter visuals sufficiently illustrate the content before finalizing this third release.
