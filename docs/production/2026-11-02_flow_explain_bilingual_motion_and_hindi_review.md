# FLOWMINUTE LAB — bilingual FLOW//EXPLAIN QA and continuation (2026-11-02)

**Status: Two real audiovisual reviewer renders; NOT owner-approved, NOT published, NOT a production channel upload receipt.**

## Original educational content
English topic: AI agent file permissions, request vs actual execution, least privilege, explicit checks, mock file browser. Hindi companion explains same concept with independent Devanagari script, not mechanically English-captioned.
Visuals are original React/Remotion and must not be represented as footage from either referenced Instagram Reel.

## Verifiable English V5 evidence
- Actual successful cloud-render: https://github.com/Tirthanand17/taskless-lab/actions/runs/41424412804
- GitHub artifact ID 13130668721, `flowminute-flow-explain-full-av-review-only`, **one-day retention**.
- H.264/AAC MP4 **1080x1920, 30 fps, 896 frames, 29.867 s**. Full video decode succeeded. SHA256 source `388b77c385d9b727c9be9fe4110396df58daa4f204ee97d4d00bb0a5b0ee0d03`.
- Audio mastered in ChatGPT runtime (video stream copied, AAC loudnorm), SHA256 `84077f0c47c71ab0334894f80cc4b33a2083b0dd743fcd7cf48f59deadddea35`. FFmpeg decode success; integrated about -18.1 LUFS; true peak -1.5 dBTP.
- Six actual Remotion sampled screenshots visually inspected; an animated request cursor travels to permission control and stops when the deletion request is blocked. File rows are preserved and visually marked safe.

## Verifiable Hindi first render evidence
- Actual successful cloud-render: https://github.com/Tirthanand17/taskless-lab/actions/runs/41425297700
- GitHub artifact ID 13131069634, `flowminute-flow-explain-hindi-full-av-review-only`, **one-day retention**.
- H.264/AAC MP4 **1080x1920, 30 fps, 1,112 frames, 37.077 s**. Full video decode succeeded. SHA256 unmastered source `c1b6419ab4c84690cacc60c2029fcc078866c436c037ac9bf4a48ce6da180870`.
- Kokoro synthetic Hindi `hf_alpha`, `lang=hi`; speech-only timeline 37.035s, 83 whitespace-delimited words, 13 phrases, PCM SHA256 `377743e6a85294f863a5f6ba1b48547b4075fd68c13add2685ddf8d293ea7325`. Timed phrase SRT comes from the same per-phrase generated audio, not word-level forced alignment.
- Six actual 1080p Remotion frames visually inspected: Devanagari font visibly rendered and panels aligned.
- Audio-mastered ChatGPT preview SHA256 `de9d62f96da21a8dbbeb4534aaab4301a98c0d1de8a9221c3862217a209c7128`. FFmpeg decode passed; integrated about -18.1 LUFS and -2.44 dBTP. The video frames were copied unchanged.

## Code added to the existing draft PR #6 branch
- `motion-v2/src/AgentPermissionFlowExplain.tsx`: bilingual captions/typography plus deterministic visual request path and clearly labelled simulated denial.
- `motion-v2/src/flowExplainTimingHi.json`: static fallback layout timings; not the actual voice-aligned timestamps (CI overwrites them in runner).
- `motion-v2/script-flow-explain-hi.txt`: separate Hindi language script with 13 selected phrases.
- `scripts/generate_flow_explain_timed_narration.py`: Kokoro `af_sarah` English / `hf_alpha` Hindi, 48-kHz audio, phrase timings and generated SRT with same source segments.
- `.github/workflows/flowminute-flow-explain-hindi-av-review.yml`: read-only, no secrets, no upload; explicitly checks full decode, codecs, dimensions, 13 captions and six actual stills.
- `motion-v2/src/Root.tsx`: original English composition preserved and Hindi composition added.

## Mobile readability change pending re-render
The first reviewer masters show captions somewhat small at phone scale. Commit `2cb2e82d7ae69518593f905c5c2db82dcfbea164` enlarges ONLY spoken captions to 38px English / 36px Hindi, increases the subtitle panel to 148px and preserves compact technical labels. English and Hindi GitHub render jobs will verify this change separately. Do not claim these two earlier V5/Hindi files contain this later caption patch.

## Hard gates still FALSE
- No human judgment of natural accent, Hindi pronunciation, English cadence, audio performance or final creative quality.
- No verified final soundtrack/SFX license or true final technical/factual/rights approval manifest.
- No final mobile UI overlay compatibility test across actual phone displays.
- No original-premium reference parity claim; the technical panels and progressive action lane are still less elaborate than the Instagram creators' work.
- No verified current YouTube owner credentials, publication approval, media hash authorization, final right-channel readback or released YouTube video ID.
- No committed durable source media binary into GitHub; review MP4s live in the ChatGPT sandbox and one-day GitHub Actions artifacts only. Permanent retention/storage needs the owner-approved existing GitHub policy.

## Explicit safety and budget
No paid API credits, new paid services, Desktop/Nirala operations, local laptop access, cloud ledger mutations or YouTube publication. Existing development branch preserved, no PR merged. Failing unrelated legacy Cloud Scout runs do not establish correctness of these audiovisual renders.

Prepared as an evidence handoff to future AI agents. Do not infer finished/released state from CI green checks alone.

## Final mobile-caption reviewer re-renders (supersede previous two media files)

**English Version 6**:
- GitHub run https://github.com/Tirthanand17/taskless-lab/actions/runs/41426295160 — completed successfully against commit `2cb2e82d7ae69518593f905c5c2db82dcfbea164`.
- Actual H.264/AAC GitHub MP4 1080x1920 at 30fps, **896 decoded frames**, **29.867 seconds**. Source SHA256 `196a46f1ff4685bc9b47e3050157e5da77160803acb3464ec4b9ec642b49248b`.
- Original frame-unchanged, audio-mastered local reviewer version SHA256 `1f1a740002aa035a1eaed8c7a308831efe0ea6a8950c61337ceaafda3a9386fc`. Measured audio **-18.10 LUFS**, **-1.38 dBTP**; full FFmpeg decode passed.
- English captions now 38px within a 148px caption panel. Six new actual screenshots inspected; no visible clipping in sampled frames. This does not prove every intermediate frame or device overlay is perfect.

**Hindi Version 2**:
- GitHub run https://github.com/Tirthanand17/taskless-lab/actions/runs/41426295175 — completed successfully against the same commit.
- Actual H.264/AAC GitHub MP4 1080x1920 at 30fps, **1112 decoded frames**, **37.077 seconds**. Source SHA256 `879db5d26d163c40b1b053edca3cf0974509cc4ba2bbd23a5586a9d4fa34bc2b`.
- Original frame-unchanged, audio-mastered local reviewer version SHA256 `ba27ed6b3af872b3c5973f4b371c6ff8abfb7885929def88d9e16dc890c0f772`. Measured audio **-18.07 LUFS**, **-2.45 dBTP**; full FFmpeg decode passed.
- Hindi narration uses 13 phrase-aligned caption cues. Devanagari caption text now 36px inside a 148px panel. Six actual screenshots inspected and visually rendered correctly at sampled frames; no confirmed independent native-speaker pronunciation approval.

**Review package**: `FLOWMINUTE_LAB_Bilingual_AI_Agent_Shorts_Review_V6_EN_V2_HI.zip` provided in ChatGPT conversation with two mastered MP4 review files, original phrase SRTs, voice QA JSON and new real render contact sheets. This ZIP is **not** hosted in the GitHub repo. GitHub code and this receipt are the project source of truth; short-lived GitHub Actions artifacts are not an approved long-term media store.

**Strict release state**: English and Hindi reviewers are both TECHNICAL_QA_PASSED / CREATIVE_AND_RIGHTS_QA_PENDING / YOUTUBE_NOT_PUBLISHED. Do not infer a public URL, video ID, private upload, scheduled release or automated channel integration. No paid API video provider was used and no laptop/Nirala access occurred.
