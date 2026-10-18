# FlowMinute Phase 3 — real audiovisual mux proof + offline narrator feasibility (18 October 2026)

**Scope:** technical media plumbing only. No human narrator, no rights-certified speech, no final spoken subtitles, no uploaded/published YouTube video.

## Actual work

- `autopilot/phase3_quarantined_audio_mux.py` accepts only pre-existing *silent* H.264 MP4 plus *supplied* local 16-bit PCM WAV, with the fixed three CSV episode IDs and their language/narrator plans. It restricts video geometry, input size, no symlink or output overwrite, file duration <=8 seconds and existing folder. Outputs a separate, small **real H.264 video + AAC audio MP4** with full FFmpeg decode.
- Uses `autopilot/phase3_voice_subtitle_handoff.py` to check actual source PCM WAV bytes: file hash, channels, sample rate, length, measurable energy, and the screenplay's known episode/bounded draft SRT hash. It **does not** burn script subtitles onto the output because these are not aligned to real speech.
- All return values always say `actual_natural_speech_verified=false`, `two_distinct_narrators_verified=false`, `voice_rights_verified=false`, `audio_caption_alignment_verified=false`, `production_release_authorized=false` and `publishing_authorized=false`. Technical sound ≠ human speech. A synthetic sine wave can pass.
- `autopilot/test_phase3_quarantined_audio_mux.py` uses actual FFmpeg-generated H.264 visual clips and **explicit synthetic tone WAV**, tests two geometries, actual AAC stream and full decode, wrong episode, existing audio, bad geometry, silence, duration mismatch, symlink, overwrite, bad output directory, damaged MP4, and no release authority.
- Public Cloud Render Smoke additionally muxes the existing three-second original English CSV visual-only preview with a generated **synthetic sine wave**, probes real AAC, asserts zero voice/rights/alignment/upload approval, and deletes all temporary files. **There is no actual narration.**
- Does not create GitHub artifacts, permanent video storage, new cloud services, paid providers or authentication.

## Offline narration options — legal and practical research, NOT deployed

1. **Kokoro-82M v1.0** `hexgrad/Kokoro-82M`, upstream official model card https://huggingface.co/hexgrad/Kokoro-82M: weights labeled Apache 2.0, multilingual including English and Hindi in v1.0, 82M parameters. Candidate for a bounded **offline** English/Hindi naturalness benchmark with explicit original model/voice weight hash, legal review and a disposable cloud runner. Its license card is promising but does NOT prove our particular English/Hindi speech quality, exact asset attribution chain, safe CPU/memory performance, commercial rights in every external dataset/source or ₹0 sustained operating cost.
2. **SPRINGLab F5-Hindi-24KHz**, https://huggingface.co/SPRINGLab/F5-Hindi-24KHz, model card lists CC-BY-4.0 (research-targeted). Requires attribution/rights evaluation, actual listening and hardware budget proof; **not installed or deployed**.
3. **Piper** https://github.com/rhasspy/piper voice models must be checked on an individual MODEL_CARD; do not blanket claim every Piper voice is commercial-use safe.
4. **Noncommercial voice-cloning variants**, e.g. https://huggingface.co/dheeyantra/dhee-indic-f5, list CC-BY-NC-4.0. Never use in monetizable FlowMinute output without separate commercial license and speaker consent. No voice cloning of another person without their explicit consent.

**No TTS model downloaded or run, no HF account connected and no new provider enrolled in this session.** A future natural voice trial needs owner authorization for the model download/service connection, verified per-voice legal terms and an explicit hard resource/usage stop. Standard public Actions jobs and free disk/time quotas are not unlimited.

## Remaining blockages

- 3R1 natural/rights-cleared recordings by at least two audibly distinct Short narrators and approved Hindi long-form voice; independently listen/review all pronunciations and pauses.
- 3R4 true audio-to-phoneme/subtitle alignment and editorial/visual/audio/rights QA — text SRT estimates and sine-wave AAC test do not count.
- 3R3 original full-resolution, full-duration three-video batch, realistic visuals and sustainable encrypted ₹0 temporary/durable media handoff.
- 2R1/2R2 actual source capture and independent factual approval; 4E Cloudflare D1 readback and real YouTube private/publish/readback 5.
- Public research PR #5 and release-controller PR #4 stay DRAFT/UNMERGED. No YouTube publishing, Nirala, external account permissions, billing or Cloudflare mutations.

**Budget:** ₹0 recurring cloud infrastructure. **21 tracked production acceptance subphases still unfinished.** Code proof is a subcomponent, not production completion.

## CI evidence

Code/tests commit `f74499775630ac28e630799f3c7a66c8dcb71c92`: Content Quality Gate passed **442 tests + 48 subtests**: https://github.com/Tirthanand17/taskless-lab/actions/runs/39087813097

Latest Cloud Render Smoke workflow HEAD `1ec85f34f2a3397c44f7779a32bf79a481e8130e` must be independently confirmed before declaring end-to-end green.
