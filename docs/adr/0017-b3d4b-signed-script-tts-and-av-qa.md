# ADR-0017 — Branch 2 B3d4b: real original voice + exact signed script and independent A/V QA

**Decision:** 2026-11-04. **Track:** autonomous cloud Branch 2, GitHub only. **Status:** developer technical demo, not independently reviewed or publishable content.

## Reviewed existing evidence and upstream research

B3d4a PR #19 merged the first generic signed draft → half-resolution *silent* video-card preview bridge. It verified 2 Shorts + 1 long with original typography, but generated no actual speech. Earlier B3b has a working CPU-only Kokoro + original CSV fixture *full duration* H.264/AAC suite, signed pinned release files, actual speech-derived SRT captions, simple original scene transition tones, a moving-progress overlay, and independently decoded video/audio caption QA. This ADR **reuses** those existing reviewed components while replacing CSV-specific scenes with the actual signed model-proposed visual-beat storyboards.

Official sources:

- [kokoro-onnx v1.1 public model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1): published v1.0 int8 CPU model and voice pack; reuse repository pinned SHA256 after download, never unverified arbitrary weights.
- [kokoro-onnx package release 0.6.1](https://pypi.org/project/kokoro-onnx/0.6.1/): Python 3.11 supported. Pin this package version as previous B3b full-duration job already does.
- [official Kokoro English voice generation example](https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/with_voice.py): voice, sample rate, language and output data contract.
- [FFmpeg concat/encoding guidance](https://ffmpeg.org/faq.html#How-can-I-concatenate-video-files_003f): explicit scene order/timing requires a demuxed sequence and re-encode; trust measured output rather than planned duration.
- [GitHub Actions compromised runner security](https://docs.github.com/en/actions/concepts/security/compromised-runners): only unprivileged read-only pull_request workflow; do not expose real credentials or private media/rights ledgers to an untrusted runner.

**Copyright and voice rights:** publishing and monetization require an independently checked current model+voice license, final content-rights and synthetic/altered media disclosure decision. An available public model or the ability to synthesize audio is NOT proof of legal rights or user permission to produce real monetized uploads. This task uses only invented public-repo fixture scripts.

## Engineering integration

- Reconstruct the complete B3d1/B3d2/B3d3a signed script source-bound plan from independently provided candidate + observed sources + pinned anchor + trusted custodian key registry **at the final producer edge**, not merely compare a self-declared hash in a model output. Require canonical equality to the expected plan including title, narration, all visual-beat directions and no-publish flags.
- A deterministic per-slot voice contract uses *af_heart* for Morning Short, *am_michael* for Long and *bf_emma* for Evening Short. Each distinct actual script beat becomes an original 1080×1920 or 1920×1080 typographic storyboard frame, never copied stock or falsely attributed statistics. The content direction and words remain unverified; the process graphics never suggest new facts.
- Reuse B3b pinned Kokoro ONNX CPU and actual per-sentence speech synthesis with measured PCM sample counts, WAV, scene-specific SRT cues and original transition sounds. Generate a dynamic FFmpeg concat timeline matching actual speech length and encode H.264/AAC, burnt captions and moving progress accent, then fully decode.
- Apply an *independent existing* FFmpeg QA module against actual generated MP4 and original PNGs: codec/dimensions, loudness/true peak, silence, subtitle text/timing, actual burned-caption pixels and first-to-later scene visual differences. Do not equate programmatic media inspection with human watching/listening or Hindi voice quality review.
- 3 distinct examples test **only** the human-authored/repeated educational fixtures from upstream PR #14. No real external LLM call, provider key, video license, reviewer-backed article/source analysis or genuine autonomous editorial workflow is implied.
- The real test MP4s, WAV, SRT and PNG files are created solely in TemporaryDirectory on GitHub-hosted runners and deleted after testing. Public Kokoro release model/voice files are retrieved into job-owned /tmp with SHA256 check and deleted on completion or failure. **No workflow artifact upload or download link is produced.**

## Files, tests and safety

- autopilot/signed_narrated_cloud_pack.py — source/plan continuity validation; original dynamic storyboard frames; actual Kokoro speech/timed cues and FFmpeg encode, decode and measured quality metadata; permission outputs FALSE.
- autopilot/test_signed_narrated_cloud_pack.py — no-network unit tests for three slots, speech scene-span fidelity, wrong/replayed episode, source-plan title change, replaced beat, unauthorized flags, missing anchor checks and no overwrite of preexisting directories.
- autopilot/signed_narrated_cloud_smoke.py — hosted real three-video generator + independent encoded-file measurements, verifies all outputs are technically present and independent of human/rights approval, checks ephemeral destruction.
- .github/workflows/flowminute-b3d4b-signed-narration.yml — unprivileged standard PR, contents:read, two jobs: pure crypto/scene regressions and pinned Kokoro model + original video/voice/caption full-run and independent QA. Budget zero, no Gemini API/YouTube tokens.
- Existing repository Content Quality Gate / scout/render workflows must all pass before squash merge.

### Explicit no-release contract

All results must maintain:

- **No live generative script:** scripts are invented test fixtures and repeat examples, not fresh independently reviewed daily videos.
- **No human/editorial/source fact/rights approval:** all pending; exact signatures are test keys and cannot authenticate humans.
- **No production credentials, uploader, scheduled state or persistent media:** every preview is disposable and never uploaded.
- **No local laptop**, Nirala files, customer data, hidden paid models, or provider charges.
- Media exists **only transiently** in hosted CI, and machine-checked A/V is not enough to upload.

## Next true acceptance gates

**B3d4c:** real, owner-authorized model inference under explicit data use terms, actual model/voice rights evaluation, three distinct nonrepetitive source-supported scripts with independent human review, content-specific real worked examples beyond repeated fixture text, approved original animations, sound design and subtitles, real full-watch/listening, final original thumbnail, and signed media+fact+rights receipts. The signed review verifier B3d3b is only a receipt-verification library and not actual human adjudication.

**B4:** deploy approved private durable media storage/append-only trust ledger; authenticated reviewer enrollment, OAuth vault and scoped YouTube credentials, fenced exactly-once upload/schedule writer, explicit upload privacyStatus=private, readback, caption/thumbnail processing confirmation and future publishAt only after full authorization.

**B5:** 21 unique actually published and source/rights-cleared videos over seven consecutive days with zero laptop dependency, no duplicates, missed deadlines or unauthorized provider spend.

Branch 1 assisted video uploads/scheduling remain independent and untouched.
