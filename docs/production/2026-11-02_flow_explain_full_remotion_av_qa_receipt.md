# FLOWMINUTE LAB — Full English Remotion A/V QA Receipt (2026-11-02)

**Status: REAL VIDEO RENDERED AND TECHNICALLY VALIDATED. EDITORIAL REVIEW ONLY. NOT RELEASED OR APPROVED FOR YOUTUBE.**

## Canonical release status
User-requested topic: "Can an AI Agent Delete Your Files? Check This First".
Format: FLOW//EXPLAIN, original progressive dark-panel training example; NOT copied social footage. Sample folder names are imaginary and must not be mistaken for real file actions. Synthetic narration is always described as synthetic.

## GitHub versioned inputs
- Existing repository: `Tirthanand17/taskless-lab`
- Development branch: `feature/oct24-multicharacter-3d-lesson-contract`; existing draft PR #6, not merged
- `motion-v2/src/AgentPermissionFlowExplain.tsx` — actual Remotion UI and inline timed captions
- `motion-v2/src/flowExplainTiming.json` — static fallback timings; overwritten *ephemerally* from synthesized voice when CI renders; do not claim default JSON is voice synchronized
- `motion-v2/src/Root.tsx` — dynamic full duration and review-only audio flag
- `motion-v2/script-flow-explain-en.txt` — 72-word exact narration
- `scripts/generate_flow_explain_timed_narration.py` — 13 short synthetic voice segments; creates one 48-kHz narration stem, frame-timing JSON and phrase SRT from the same PCM timeline
- `.github/workflows/flowminute-flow-explain-av-review.yml` — no-publish, no-secrets full synthetic audio/video reviewer render and six-frame receipt
- `scripts/master_flow_explain_audio.sh` — audited FFmpeg audio review normalizer; no publish and no overwrite
- `docs/FLOWMINUTE_EXPLAIN_DESIGN_SYSTEM_2026-11-02.md` — style and safe area guide
- Prior reference study: `docs/reference_reels/2026-11-02_two_reels_verified_evidence.md`

## Independent GitHub proof
- GitHub Actions **successful** run: https://github.com/Tirthanand17/taskless-lab/actions/runs/41413756099
- Short-lived artifact: **flowminute-flow-explain-full-av-review-only** (artifact ID 13126781677, retention 1 day).
- Actual GitHub-generated source MP4: 1080x1920, **30 fps**, **896 frames**, **29.867 s**, H.264 video and AAC audio, complete FFmpeg decode pass; source media SHA256 `bf67d24af33f65e1892e2ad35fcbe9a984ae780841f6a2fb471db70b50d94c3f`.
- Caption SRT: **13 exact phrases** timed from individual generated TTS segments, not inferred proportional cuts of a single narration. *Not word-level forced alignment*. Phrase times span approx 00:00.120 to 00:29.299.
- Speech generator: Kokoro ONNX open-weight model `af_sarah` (synthetic). Voice timeline **29.849 seconds** with outro tail, 72 spoken words and 6 visual beat starts at frames **4,139,286,436,624,724**; PCM voice stem SHA256 `f65a8d281a1191a7c556b15801ba409daafef777e7725b4a53b32ed57db0d965`.
- Reviewer stills: actual six GitHub-produced frames, visually checked against 12 exported frames in local QA; layout shows consistent margins, limited subtitle lines and fixed file-browser + action inspector UI. This is an inspection sample, not a statistical guarantee of every frame being error-free.
- Source A/V loudness before local post-processing: **-23.83 LUFS**, peak **-6.39 dBTP** (too quiet for intended final mix).

## Separate mastered ChatGPT review copy
An audio-only re-encode of the above GitHub render was produced in the ChatGPT runtime, with the H.264 video stream **copied unchanged** and AAC audio mastered using `loudnorm=I=-18:TP=-1.5:LRA=9`; recorded measured output **-18.07 LUFS**, **-1.54 dBTP**. Full decode passed.
- Mastered review copy SHA256 `19f3c8a75e96a28c8318e37634a03a358f7f3ec09a8aeeefa59181c34f448ecb`.
- Local file: `FLOWMINUTE_AGENT_EXPLAIN_EN_V4_FULL_REMOTION_AUDIO_QA_REVIEW.mp4` in the ChatGPT conversation, NOT the GitHub repository or long-term media cloud storage. The script for reproducing its mastering method IS saved in GitHub.
- No licensed soundtrack, music/effects mix, user/narrator audition approval, media rights sign-off, full final-script fact review or final YouTube confirmation was completed.

## Quality assessment and open items
1. **Technical pass:** actual cloud Remotion full render, both codecs, complete decode, 1080p, measured duration and frame count, exact phrase SRT, volume correction.
2. **Visual improvement:** the old oversized cards have been replaced with a restrained, aligned interface that keeps the simulated file list persistent and changes inspector action/permissions/denial states. All 12 sampled screenshots looked aligned; some panel space is underused and animation is still too restrained to claim parity with the reference creators' premium motion graphics.
3. **Narration status:** machine silence and audio codec tests are NOT proof of natural intonation, rights or human approval. Phrase segmentation can sound choppy; check the actual take on phone and headphones and revise if needed.
4. **Subtitle status:** SRT phrases exactly match synthesized input; no independent audiovisual forced alignment or final mobile overlays validation was performed.
5. **Remaining production:** stronger meaningful animated request/permission transition, final voice audition, accurate fact/rights/creative gates, original sound design and mobile UI safe-area review; Hindi separate audio and typography pending.
6. **Publishing safety:** legacy publish path and account policy gaps noted in prior audit; no verified authorization to release this media. **No YouTube upload, video ID, channel readback, public schedule or approval is claimed.**
7. **Budget:** standard existing public GitHub Actions workflows, open-weight model, FFmpeg and ChatGPT execution only; no new paid services, credits, Nirala or local laptop resources used.

This document is a factual handoff for future AI agents, not a release approval.
