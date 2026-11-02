# FLOWMINUTE LAB — FLOW//EXPLAIN English A/V review receipt (2026-11-02)

## Scope
This receipt documents creation and verification of the **non-publishable** AI Agent File Permission explainer. It supersedes the preceding silent design previews for review, but does not approve their artwork, rights, voice naturalness, subtitles or publication.

## GitHub repository evidence
- Remotion design source: `motion-v2/src/AgentPermissionFlowExplain.tsx`, composition registered in `motion-v2/src/Root.tsx`, 1080×1920, 30fps, 1080 frames (36-second silent composition).
- Design contract: `docs/FLOWMINUTE_EXPLAIN_DESIGN_SYSTEM_2026-11-02.md`.
- Original voice script: `motion-v2/script-flow-explain-en.txt`, 72 words.
- Bounded Kokoro synthesizer: `scripts/produce_flow_explain_voice_review.py`.
- Free, no-secret, no-publish voice workflow: `.github/workflows/flowminute-flow-explain-voice-review.yml`.
- GitHub *actual* Remotion smoke: https://github.com/Tirthanand17/taskless-lab/actions/runs/41411412729 — **success**, six actual frames at 1080×1920, 30-frame motion decode at 1080×1920. Screenshot artifact ID 13124909340, one-day retention. Full 36-second Remotion export is NOT validated by the 30-frame smoke.
- GitHub *actual* Kokoro voice review: https://github.com/Tirthanand17/taskless-lab/actions/runs/41411985414 — generated a **synthetic voice listening review**, originally artifact ID 13125907942, one-day retention. NOT human voice approved.

## Voice metrics
- Source: Kokoro ONNX v1.0, `af_sarah` synthetic; 72-word original script.
- PCM speech-only length **27.141 s**, 48 kHz mono, SHA256 `92e3c61013b788a27451592c3c924be51f4ce19f0b92b11a98bbbdfca5086de4`.
- Automated speech-only >1.3s-gap check: **pass**. No claim of human/naturalness acceptance; performance and rights remain human-review pending.

## Two A/V sandbox renders (NOT repo or cloud media store)
1. English flow storyboard was produced as a 36.0s, 720×1280 24fps prototype using the separate bounded Pillow renderer. That preview is **not** the verified Remotion output; it has its own visual implementation.
2. New 27.6s 720×1280 24fps H.264/AAC A/V review used the **original existing Python-rendered visual prototype**, sped in six independently paced segments against inferred speech pause boundaries, followed by ~0.46s tail. Approximate voice-beat time boundaries: 0, 5.64, 10.75, 16.38, 21.58, 24.01, 27.14 s. These are editorial estimates, **not forced alignment or final synchronized captions**.
3. Local A/V without mastering SHA256 `3e5965b3ef892ff4fd4496bca2403a864a05ac3c4e9ccf5e2ebb43a5c5c7d746`.
4. Local mastered A/V review SHA256 `a1fd389828dbe120c2989eec7cb2010fe6e3cfd45e8a8bc4f087669b9d2730ab`; FFmpeg full decode succeeded, integrated loudness **-18.3 LUFS**, true peak **-1.4 dBFS**, H.264 video 720×1280 and AAC audio. This is only a listening/layout preview, and not the final approved media. It is delivered to this ChatGPT conversation's sandbox and **is not available in GitHub**, as there is no verified enduring authorized repo media store for this video.
5. This render deliberately does not include licensed music, sound effects or verbatim word-timed captions and is not equivalent to either Instagram reference's finished quality.

## Release gates outstanding
- Listen to the entire WAV and the mastered MP4; accept or reject pronunciation, inflection, pacing, mix, and clarity; human listening approval still FALSE.
- Review every frame at phone size for display overflow and meaningful animated causality (not just changing cards). Verify the rendered Remotion output and the eventual soundtrack as a *single* finished original film. Do not infer final Remotion correctness from the Pillow proxy.
- Generate properly synchronized literal English caption SRT; check word-for-word against the audio.
- Human factual, creative, five-part video and rights reviews remain FALSE.
- Resolve Cloud Scout missing dependency errors, branch integration, Hindi caption metadata, legacy publication bypass, OAuth/channel readback and release ledger as per prior audit. Do not publish automatically or bypass required gate checks.
- Owner may authorize separate publication only after every gate passes and verified account write access is available.

## Safety
No paid API credits, billing, Nirala, Desktop access, YouTube upload, scheduled release, or changes to legacy publisher were performed in this task. Prototype media created only in the temporary ChatGPT runtime, public GitHub code and GitHub Actions review artifacts.
