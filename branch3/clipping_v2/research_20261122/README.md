# Clipping research and a reproducible Clivox benchmark

22 November 2026 · YouTube Shorts · Branch 3

**Build on the existing Clivox controller. Start with creator-delivered recordings, local faster-whisper, the existing acoustic candidate planner and FFmpeg. Spend on software only after measuring what slows an editor down.** A creator paying for approved edits gives the pilot a price and a buyer before the channel qualifies for ads. The first commercial dependency is a source owner willing to grant the intended rights and supply a master.

## What actually pays

| Route | Who pays and when | First evidence to collect |
| --- | --- | --- |
| Editing for a creator | The creator pays an agreed fee per approved edit or a retainer. Delivery to the creator's channel and redistribution on Clivox are separate contract terms. | A written pilot price, acceptance criteria, turnaround, permitted destinations and a delivered recording. |
| Performance campaign | A campaign pays under its brief. Minimum eligible views, verification, approval, geographical rules, caps and remaining budget can all affect settlement. | Record the actual brief, approval, counted views and settled payout. Keep a separate column for estimated earnings. [Campaign payout mechanics](https://b4e0vdqv6zgqeqj4pfgm.apps.whop.com/articles/clipping-campaign-budget) |
| Clivox Shorts advertising | YouTube reviews the channel. Its Shorts entry route lists 1,000 subscribers and 10 million qualified Shorts views in 90 days. The long-form alternative lists 4,000 qualifying watch hours in 12 months alongside 1,000 subscribers. The Shorts module must be accepted. | Verify the Earn tab and eligible engaged views. The creator share is 45% of the allocated pool amount. Geography, eligible views and the pool affect the result. [YPP eligibility](https://support.google.com/youtube/answer/72851) · [Shorts revenue sharing](https://support.google.com/youtube/answer/12504220?no_head=1) |

YouTube evaluates reused and mass-produced content at channel level. Permission addresses use of the recording. An editor still needs to add meaningful original analysis, commentary or storytelling for the Clivox format. A captioned crop can be a useful editing deliverable while leaving channel monetization uncertain. YouTube also announces a rolling qualified-view requirement for monthly Shorts pool eligibility from 1 February 2027. Account for that date when modelling a long-term ad business. [Channel policies](https://support.google.com/youtube/answer/1311392) · [Shorts policy announcement](https://support.google.com/youtube/answer/12504220?no_head=1)

**Illustrative unit economics in INR.** Suppose a creator pays ₹600 per accepted clip, an editor spends 25 minutes per attempt at ₹300/hour, and compute and storage cost ₹15 per attempt. Each attempt costs ₹140. At 50% acceptance the cost is ₹280 per accepted clip, leaving ₹320 before sales time, taxes and fees. At 20% acceptance the same work costs ₹700 per accepted clip and loses ₹100. Break-even acceptance under those assumptions is 140/600, or about 23.3%. These are hypothetical inputs. Replace each one with a measured cost or signed price. For a performance campaign, calculate payout from eligible views and its actual rate, floor and cap. A public view counter cannot establish what the campaign will pay.

## GitHub search coverage

Eight public GitHub repository searches returned 1,093 matches before cross-query deduplication and **1,041 distinct repositories**. The API reported complete results for every query. We fetched every results page for these queries, sorted by stars and excluded forks. Repository search indexes names, descriptions, topics and selected metadata. Unlabelled tools, non-English descriptions, forks and projects outside these terms can be missed. Search hits include adjacent and unrelated tools. Six projects received source inspection, two had components executed, and four more received a documentation review.

| Query, each with `fork:false` | Results |
| --- | ---: |
| youtube shorts clipping | 160 |
| "opus clip" | 115 |
| topic:ai-clipping | 23 |
| "long videos" "shorts" | 550 |
| "podcast" "highlights" | 170 |
| topic:youtube-shorts-generator | 24 |
| 自动切片 视频 | 12 |
| "highlight extraction" video | 39 |

Python led the inventory with 488 repositories. TypeScript accounted for 113, HTML 69, JavaScript 63 and 208 had no primary language recorded. GitHub identified 317 MIT licenses and returned no license identifier for 622. These describe repository metadata. Only a file and dependency review establishes how a project actually works. The inventory records repository URL, primary language, stars, detected license, archive status, last push and matching queries. The six-project shortlist covers a small CLI, a semantic library, a browser editor, a local ASR editor, a multistage pipeline and a full stack. Selection weighted unattended operation, evidence of working code, local cost and fit with the existing controller. [Inventory](inventory.json) · [Re-run the searches](survey.py)

## What the source revealed

| Project and inspected revision | Execution path | Decision for Clivox |
| --- | --- | --- |
| [AI-Youtube-Shorts-Generator · 8c9ac31](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator/blob/8c9ac3103a137e53669aeebfc2af8dbdd810c35a/shorts_generator/pipeline.py) | Default mode calls MuAPI. Local mode uses yt-dlp, faster-whisper, an OpenAI or Gemini key, FFmpeg cutting and an OpenCV largest-face crop. | Upstream cut/reframe executed successfully. Its final mux copied the intermediate MPEG-4 Part 2 video. Encode the final H.264 stream explicitly. Largest face can also be the listener in an interview. [Crop implementation](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator/blob/8c9ac3103a137e53669aeebfc2af8dbdd810c35a/shorts_generator/local/clipper.py) |
| [OpenShorts · 60e7714](https://github.com/mutonby/openshorts/blob/60e77143fabb54d9d4c7068ce9a65ef93a69be4d/clip_selection.py) | Windows transcripts, caps candidates, rejects overlap by the shorter clip's length and can align cuts to word boundaries. Compose runs a backend, frontend and renderer. | Best reference for a team wanting an editor. Its overlap function passed our fixture. A long-running three-service deployment adds maintenance for a one-creator pilot. [Compose](https://github.com/mutonby/openshorts/blob/60e77143fabb54d9d4c7068ce9a65ef93a69be4d/docker-compose.yml) |
| [ClipsAI · 8e73c8a](https://github.com/ClipsAI/clipsai/blob/8e73c8adc112c745b84ec240f11a91457bfd3141/clipsai/clip/clipfinder.py) | A Python library embeds text, applies TextTiling over several window sizes and removes duplicate time ranges. | A good semantic baseline for long discussions. Topic boundaries alone give weak evidence for a gaming reaction. Source inspected. |
| [FunClip · cdcb53f](https://github.com/modelscope/FunClip/blob/cdcb53fe3d4b37365178ae4f779296e72b7beb6a/funclip/videoclipper.py) | FunASR recognition yields timestamps. Text or speaker selection drives MoviePy editing, with subtitle and UI support. | Strong fit for an editor correcting transcript-selected cuts and for testing Chinese-language material. Clivox starts English-first. Source inspected. |
| [AutoClip · cd8e6be](https://github.com/zhouxiaoka/autoclip/blob/cd8e6bed18d87a81273d48bcd165751708ac715c/backend/pipeline/step3_scoring.py) | Separate outline, timeline, scoring, title, clustering and video stages. Scoring has a configurable backend, threshold, excerpt preparation and saved results. | Use stage outputs for diagnosis. The complete backend and model configuration are expensive operationally for a single pilot. Source inspected. |
| [miscoshorts-ai · 5bdeb93](https://github.com/JoaquinRuiz/miscoshorts-ai/blob/5bdeb93884d4b916f291624d924a068d3662ef62/miscoshorts/render.py) | MoviePy/Pillow render captions and reframe, with optional OpenCV tracking. Its render test verifies timing, dimensions, sound and caption pixels. | Adopt the decoded-output test idea. FFmpeg with libass can burn timed text in one encode. Source and upstream test inspected. [Upstream render test](https://github.com/JoaquinRuiz/miscoshorts-ai/blob/5bdeb93884d4b916f291624d924a068d3662ef62/tests/test_render.py) |

All six pinned sources reported MIT in GitHub metadata. The benchmark uses new implementation code and existing Branch 3 interfaces. Dependencies, models, recordings and publishing permissions must be assessed individually.

Four other designs help explain the tradeoffs.

- **OpenClip** documents Streamlit and CLI entry points, Whisper/Paraformer routing and optional compatible model endpoints. It is a useful editor-facing alternative when multilingual source handling dominates. [Project](https://github.com/linzzzzzz/openclip)
- **opensource-clipping** documents Whisper, Gemini, MediaPipe, pyannote and a Kaggle/Colab GPU worker with a FastAPI service. Tracking, diarization and animated captions add value when speaker framing is the measured failure. [Project](https://github.com/NaufalRizqullah/opensource-clipping)
- **Reelsfy** documents Python, FFmpeg, an OpenAI key and optional GPU. This is a comparison point for outsourced model selection. [Project](https://github.com/eddieoz/reels-clips-automator)
- **ai-clipping-generator** includes Next.js, Prisma, NextAuth, Stripe and credits. These solve customer accounts and billing for a SaaS business. A clipping channel can defer them. [Project](https://github.com/SamurAIGPT/ai-clipping-generator)

## What ran

| Check | Result and boundary |
| --- | --- |
| Upstream Anil local crop | Generated a 4-second 320×180 24 fps test pattern with a sine soundtrack. Called `crop_clip_local(source, 1, 3, "9:16", out)` on the pinned checkout. FFprobe returned 2.000 s, 100×180, MPEG-4 Part 2 and AAC. Exercised cutting, reframing and muxing. Hosted ranking and downloading were outside this test. |
| Upstream OpenShorts overlap | Passed three intervals (1–24, 4–27, 30–53 seconds) with predicted scores 3, 8 and 5 to the pinned `dedupe_overlapping`. It kept the higher-scored overlap and the disjoint interval. The full service was not deployed. |
| Branch 3 fixture timing | The benchmark generated two chapters, decoded the recording to 16 kHz mono PCM, measured half-second RMS and fed it to the existing P5 and P6 functions. Two unreviewed cards resulted. Supplied timestamps yielded two 30-second portrait clips. |
| Branch 3 real ASR on generated speech | A 64.75-second Windows synthesized recording passed through cached faster-whisper base INT8 on CPU. The two transcript-selected excerpts were 24.84 and 24.66 seconds. FFprobe checked H.264/AAC, 720×1280, and the duration tolerance. Decoded frames contained visible caption pixels. Seventeen existing P5/P6 tests passed. |
| Quality still to measure | Two invented chapters cannot establish multilingual accuracy, speaker-tracking quality, sports/gameplay selection, editor acceptance, retention or earnings. The CPU branch uses a flat matte to preserve faces and slides. It does not follow an active speaker. |

**Reproduce from the controller root.** Python 3.11, FFmpeg/FFprobe with libx264, AAC and libass are sufficient for the default fixture. The benchmark only generates its own inputs. GitHub Actions runs the deterministic fixture on pull requests touching this study. Temporary media expires with the test process. To keep a local preview, supply a new output directory.

```sh
python -B -m unittest -q scripts.test_branch3_v2_p5_longform_local_signal_planner scripts.test_branch3_v2_p6_longform_editorial_intake
python -B -m branch3.clipping_v2.research_20261122.benchmark --output ../clivox-fixture
```

For the spoken path, install faster-whisper 1.2.1, cache the base weights once, and install eSpeak NG on Linux or use Windows system speech. The measured model snapshot was `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`. Different voices and versions can shift timings. [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [Model snapshot](https://huggingface.co/Systran/faster-whisper-base/tree/ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66)

```sh
python -m pip install faster-whisper==1.2.1
python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-base', revision='ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66')"
python -B -m branch3.clipping_v2.research_20261122.benchmark --speech --output ../clivox-speech
```

## Full production pipeline and where this test fits

The deployment design covers worker placement, event contracts, queue recovery, private-first release, operating cost and rollout criteria. [Clivox automation architecture](AUTOMATION_ARCHITECTURE.md)

| Stage | Technology and output | What releases the next step |
| --- | --- | --- |
| Find and qualify a partner | Existing P1–P3 prospect and rights intake. Public metadata can identify candidates. A creator supplies a source master through the approved private system. | Authenticated rights for exact source, platforms, commercial use, duration and included third-party material. Use YouTube Studio or Takeout to export owned uploads. [Owner exports](https://support.google.com/youtube/answer/56100) |
| Ingest | P4 private worker, media hash, FFprobe, duration and decode validation. Keep the original source time base. | Match the delivered bytes to the approved recording and scope. [P4 and activation handoff](../REAL_PRODUCTION_ACTIVATION_OWNER_HANDOFF.md) |
| Find moments | Combine local acoustic or scene events, creator timestamps and faster-whisper word times. Transcript baseline scores complete openings/endings, speech density, duration and English cue words, then rejects overlap. | Compare against the existing P5 planner on the same licensed sources. A quiet punchline, several guests talking or an exciting silent play are diagnostic cases. [P5 evaluation](../EVALUATION_PROTOCOL.md) |
| Edit | P6 editor checks adjacent context, writes original Clivox analysis and records or clears the narration. P7 uses FFmpeg, H.264/AAC and timed subtitles, with 1080×1920 as the production target. | Viewer can understand the event, the commentary and the payoff. Correct names, captions and the active subject; review the exact cut on a phone. [Editorial bridge](../P5P6_LONGFORM_EDITORIAL_REVIEW_BRIDGE.md) |
| Release | P8 exact-media approval followed by P9 durable attempt tracking, channel identity check, explicit private upload and remote readback. Reconcile ambiguous upload outcomes via the existing release design. | Separate owner authorization for scheduling/publication. Keep secrets and media on the approved private worker. [Activation handoff](../REAL_PRODUCTION_ACTIVATION_OWNER_HANDOFF.md) · [YouTube resumable uploads](https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol) |
| Measure and repeat | P10 own-channel analytics and P11 supply/capacity. Record editor time, exports accepted, eligible views, settlement, cost and source-level margin. | Review at a consistent upload age. Compare clips within the same topic and channel, using engaged views and average percentage viewed where available. Publish volume follows rights supply and editor capacity. [Existing P10 setup](../../a10/OWNER_ANALYTICS_READONLY_SETUP.md) |

**GitHub runs the software tests.** Routine commercial clipping belongs on an approved private worker. GitHub restricts unrelated workloads on hosted runners. Its scheduled Actions run from the default branch. The PR adds a path-filtered test workflow and leaves production activation to the existing Clivox release process. [GitHub Actions terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features) · [GitHub scheduling](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## Pilot and spending decision

1. Select one English-language creator and one repeatable format. Agree a test price or a specific funded campaign brief. Confirm rights to guest appearances, music and commercial distribution.
2. Start with local CPU transcription and FFmpeg. Software subscription budget for the baseline is ₹0. Count electricity, disk, editor time and delivery. The test used existing local hardware. A real source-hour throughput measurement is still needed.
3. On licensed sources, build the project's proposed 40–60 human-labelled moments across episodes. Reserve whole episodes for evaluation. Compare acoustic, transcript and combined selections at the same review budget. Record the proportion of the first three suggestions that editors accept, seconds trimmed and editor minutes per accepted clip. Track false positives such as loud transitions and incomplete setup/payoff.
4. Spend on the bottleneck. If selection dominates review time, trial a bounded LLM shortlist against the same held-out episodes. If framing dominates, trial face/speaker tracking on multi-person shots. If compute dominates, test one rented GPU hour against a local CPU hour. A hypothetical ₹1,000 tool that saves five hours at ₹300/hour returns ₹500 of labour capacity before ancillary costs. The same tool saving one hour loses ₹700.
5. Make the next spending decision from accepted edits, actual cash receipts and contribution margin. Scale only after a repeatable source supply and editorial acceptance rate support the unit economics. Track ad income separately from creator service fees and campaign payouts.

The existing owner handoff records zero verified third-party grants or delivered creator masters at its last documented checkpoint. This research adds executable editing evidence. The next commercial milestone is securing a first authorized recording and price, then measuring results on that recording. [Branch 3 owner handoff](../REAL_PRODUCTION_ACTIVATION_OWNER_HANDOFF.md)
