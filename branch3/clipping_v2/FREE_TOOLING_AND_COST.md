# CLIVOX V2 — Zero-Subscription / Open-Source Technology Stack

**As of 2026-11-14.** "Free" applies to open-source software packages or included provider tiers—not to the right to reuse creators' videos, guaranteed hosted storage/compute, private video distribution, licensing fees or eventual API permissions. Do **not** purchase SaaS or install anything on the owner's PC as a hidden assumption. Public GitHub contains only code, models' license manifests, synthetic fixtures, public references and program metadata.

## A. Decision: use a modular open-source pipeline, not SaaS autoposting

### Core MVP, in order of dependency

| Task | Proposed free technology | License / account | What it does | Limit / risk |
|---|---|---|---|---|
| **Public YouTube video references** | Existing \`scripts/branch3_discovery.py\` API adapter, after derived-metric compliance fix | Free documented Google API quota, key needed for live query | Canonical IDs, published date/title, bounded public video discovery | API policy/retention, **NO public video download**, no Most replayed peaks |
| **Twitch existing clip references** | Twitch Helix \`Get Clips\` | Official Twitch app/user OAuth; rate limits | Lists broadcaster/game clips, titles, \`view_count\`, optional VOD offset | Not commercial reuse authorization, no unrestricted media file download |
| **Authorized Twitch clip source access** | Twitch Helix \`Get Clips Download\` | **Broadcaster/editor scoped authorization**, plus commercial source grant | Temporary portrait/landscape media URLs for approved editor | Requires \`editor:manage:clips\` or \`channel:manage:clips\`; do not use unauthorized token |
| **Creator video deliveries** | Approved private GitHub-controlled media handoff / vetted encrypted store + checksums | May incur private capacity/storage and workflow billing | Media from rights holder, verified SHA256, manifest and retention | Not present; must obtain rights & owner storage approval first |
| **Video editing engine** | FFmpeg + ffprobe, Python standard library, ASS subtitles | FFmpeg mainly LGPL with optional GPL components | Crop/split-screen, encode 9:16, audio ducking, burn subtitles, loudness/sync checks | Codec/FFmpeg build licensing, cpu cost and clip-source rights |
| **Speech-to-text** | faster-whisper \`tiny/base\` int8 CPU | MIT implementation, check model-weight terms | Transcript hypothesis from **licensed** audio | Hallucinates in screams/music; slower long audio; no guaranteed per-word alignment |
| **ASR fallback / low-dependency** | whisper.cpp small/base CPU | MIT implementation, model-weight check | Local no-paid-API transcription | CPU only and local model availability; keep model downloads pinned |
| **Speech-only regions** | Silero VAD (ONNX CPU) | MIT | Find speaking intervals cheaply | Does not detect jokes, screams or copyright owner |
| **Scene and cut changes** | PySceneDetect | BSD-3-Clause | Event anchors/scene cuts | Fast cuts are not evidence of retention or funniness |
| **Audio features** | FFmpeg filters \`astats\`, \`silencedetect\`, \`ebur128\`, loudness | Existing FFmpeg engine | Peaks, speech pauses, RMS/EBU levels, dynamic reactions | High amplitude = not always interesting; avoid loud/noisy videos |
| **Optional motion/face-framing** | OpenCV (license review for exact wheel/build) | Common free open-source tool | Sampled optical flow and visible subject location | Face tracking is not identity recognition; expensive/biased |
| **Optional transcript keyword events** | Python regex, simple TF-IDF on **private authorized transcript** | Standard library / optional scikit-learn | "wait", "no way", "did you see?", stakes/turns/payoff candidate generation | Language/style bias, may miss humor; don't infer original quotation |
| **Optional local LLM** | llama.cpp + locally approved weights (future, not default) | Implementation/model-specific license | Generate clip hook hypotheses and storyboard alternatives | Significant CPU/memory, hallucinations, privacy/model licensing; never factual source of truth |
| **Narration and voice** | Human licensed voice or original synthetic eSpeak NG as *draft* | Voice tool/speakers commercial-use terms require check | Commentary with original CLIVOX creative identity | Do not clone or impersonate actual streamers; synthetic draft voice may sound robotic |
| **Captions/crop layout** | ASS/FFmpeg + deterministic line-wrap and safe zones | FFmpeg library conditions | Native video 1080×1920, 30 fps, short mobile subtitles | Subtitles require manual word verification; font licenses/attribution |
| **Review / manual correction** | Existing source-free HTML gallery + exact SHA-bound CSV, private A5 sandbox | In repo, no subscription | Offline playback/scene/cue seek, revision preview | Not an owner signature; private partner media cannot be in public gallery artifact |
| **Music/SFX** | Creator-owned sound, original procedural tones, YouTube Studio Audio Library | Context-specific YouTube terms and attribution | Sound design without copying trending recordings | Existing stream music is independently licensed; always check context/license |
| **Optional local GUI editing** | Kdenlive; LosslessCut | GPL / open-source; GitHub download free | Editorial rescue, frame-by-frame manual cut in a trusted editor environment | Not a cloud CI dependency; no assumption user PC used |
| **Release security** | SHA-256 / Ed25519 signature math + existing A2/A6/A8 repo modules | Python/Open-source; private signing authority needed | Bind true approved video bytes to creator grant and exact Clivox OAuth | Off until real owner signing, protected approval, OAuth and remote inventory |
| **Analytics** | YouTube Analytics API + Studio only for **our CLIVOX channel** | Free quota/scopes when allowed | Real engaged views, retention/stayed-to-watch, subscriber lift | No authenticated channel access yet; not third-party public API-derived score |

### Source links and licensing checks

- [FFmpeg](https://github.com/FFmpeg/FFmpeg) — command line and probe; LGPL/GPL varies by build.
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) — BSD-3-Clause (v0.7.3 released Nov 8 2026).
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — MIT implementation, CPU \`int8\`; check Whisper model weights separately.
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) — MIT, optimized low-dependency CPU.
- [Silero VAD](https://github.com/snakers4/silero-vad) — MIT.
- [LosslessCut](https://github.com/mifi/lossless-cut) — free GitHub binaries/source, optional store editions paid.
- [Kdenlive](https://github.com/KDE/kdenlive) — GPL-3.
- [Twitch Clips API](https://dev.twitch.tv/docs/api/reference/clips) — official authorized editor model.
- [YouTube Audio Library](https://support.google.com/youtube/answer/3376882) — generally free for YouTube usage; attribution-required tracks marked.

**No dependency installed nor external media downloaded by this architecture-only PR.** All selections are design proposals pending a dependency/license review, SBOM and pinned release.

## B. Free vs paid/limited clipping SaaS

Common creator tools (e.g. OpusClip, Vizard, Klap, Vidyo, Eklipse, Framedrop, CapCut) can suggest hook candidates, reframe faces and add captions, but tiers/watermarks/minute caps/exports/availability/commercial permissions change. **Do not treat their free trials as a reliable zero-cost cloud architecture.** They do not convey rights to a famous creator's footage or immunize against reused-content policy. If evaluated manually later, score against a **fictional synthetic test video only** with no secret/partner data. Mainline pipeline remains FFmpeg + an approved local ASR/scene detector.

## C. Four zero-cost configurations (trade-offs)

### Mode 0 — docs + synthetic fixtures (currently feasible, GitHub public)
- Public repo, GitHub Actions standard hosted runners, original fictional audio, synthetic test videos; metadata research without real creator files.
- No new credentials or storage. **Zero real rights**; cannot publish any creator clip.

### Mode 1 — manually granted video reference + only private preview
- Creator supplies license, original file and owner approves a private storage facility. Use existing repo orchestration on protected runner, with **no public artifact**.
- Free only if private storage and Actions quota already suffice. Full legal/music clearance and human time not free by default.

### Mode 2 — limited licensed creator-pilot
- Run one approved 30–55s Short preview, exact review and a single **explicitly owner-authorized private** upload.
- Need Clivox-specific OAuth, trusted signed owner key/approval, rights grant, remote readback and release reconciliation. Still no assumption of zero expense.

### Mode 3 — daily production business
- Pool of several active creator licenses, higher-availability private media store, authenticated private runner scheduling, review capacity, rotation by source/genre, account-owned analytics.
- **Not zero-cost guaranteed**. Commercial deals, 2 Shorts/day plus long-form clips, data storage and compute may require time/money. Never claim daily automation is complete just because jobs run.

## D. Bound resource usage before any install

**Start with a single creator-delivered sample:** max source duration 10–30 min (not 12h); 720p analysis proxy for scene detection, 16-kHz mono for speech; run small/medium ASR only on human/editor-selected portions rather than entire source; keep CPU runtime measured and capped; downsample frame scoring to <= 2fps for initial heuristics. These are *engineering experiment budgets*, not guaranteed quality thresholds.

**Review artifact privacy:** Existing GitHub original-aracade review artifact is **public-source-free only**. Any future real licensed source clip, captions and voice recording are private until explicitly cleared for public release; private repo controls must be audited. Public Actions free compute does **not** imply acceptable access/storage for confidential licensed videos.

**Potential bandwidth/limitations:** GitHub standard public runner (currently 4 vCPU, 16GB RAM, 14GB SSD for Ubuntu standard) is limited; multi-hour streams easily exceed disk/time/CI artifact limits. Private repo billed/included usage and Actions cache storage vary by plan; verify at deployment. GitHub Actions is not an indefinitely running worker, cannot watch every livestream without explicitly scheduled checks and appropriate quotas.

**No local laptop memory** required by design; cloud-only in existing GitHub environment, but full licensed video automation remains blocked until secure media vault and eligible compute are approved.

## E. Tests to measure tools before adoption

1. Frame-accurate FFmpeg roundtrip: source 1080p/gameplay demo => 9:16 crop, facial subject visible, watermark/credit properly placed, H.264/AAC.
2. English/Hindi 10–20-minute **creator-approved sample** ASR WER/CER against manually annotated 100 sentences; silence/laughter/music false positives counted.
3. PySceneDetect F1 against at least 50 manual edit boundaries, not defined as "virality accuracy".
4. VAD recall on 100 short speech segments including stream overlays and game audio; false-positive speech classified.
5. Start/end time drift: all candidate cut boundaries within 2 video frames or manually documented rounding error.
6. Karaoke/caption alignment reviewed manually for actual spoken words; verify glyph safe zones, flashing, text speed, dynamic layout after facecam/game crop.
7. Originality review: CLIVOX script must stand alone with new explanation/critique/context; source credit accurate, thumbnail not implying creator endorsement.
8. Private source never appears in public repo, CI logs, public artifacts, model caches, analytics exports or unapproved cloud endpoints.
9. All unit and integration tests use **synthetic legally owned** videos until an actual creator grant exists; no "test downloader" against a famous channel.
10. Economic load test after rights/storage: cost/clip including ASR CPU minutes, FFmpeg encode duration, storage, API quota and human review time; require owner budget sign-off before scaling.

## F. What is intentionally out of scope for initial free MVP

- Non-consensual face/voice cloning, copyright-stripping, leaked GTA footage, impersonation or nonconsensual edits.
- Downloading arbitrary YouTube URLs with yt-dlp/HTTP workarounds. Open-source program existence does not equal platform download permission.
- Scraping the private YouTube most-replayed timeline; any unofficial replay heatmap extractor is an unstable, possibly noncompliant reverse-engineering dependency.
- Whisper ASR on a video/audio file without a legitimate right to receive and process it.
- GPU rental, paid LLM/cloud speech API subscriptions, paid clipping SaaS, unlicensed stock music, expensive private hosting or cross-channel analytics resale.
- Fully automatic creator contract acceptance, outreach sending, owner signing, release override and public YouTube upload.
