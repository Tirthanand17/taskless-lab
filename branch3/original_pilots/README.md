# CLIVOX — Original-first 2 Shorts + 1 longer arcade pilot REVIEW pack

**Status (2026-11-13):** All three original preview **and full-resolution** MP4s actually rendered successfully with FFprobe checks in GitHub Actions (runs [43380418384](https://github.com/Tirthanand17/taskless-lab/actions/runs/43380418384) and [43380650008](https://github.com/Tirthanand17/taskless-lab/actions/runs/43380650008)). Human playback/editorial review, final-voice/caption alignment, owner signing, private-first upload and publication are still **NOT complete**. A new A6 exact-asset owner review packet is added to all future renders; previous historical runs do not contain that new A6 packet. **NOT published, scheduled, approved for upload or licensed third-party clips.**

CLIVOX can create first-party material without borrowing a gaming streamer, another creator's reaction, Rockstar/Take-Two footage, podcast extracts, commercial audio or a game logo. This pack demonstrates that path and provides a concrete review artifact beyond the older source-free placeholder benchmark.

## A5 exact-SRT scene navigation for owner listening (unapproved)

New original-only review artifacts include an **offline, no-JavaScript scene index**
inside \`CLIVOX-REVIEW-START-HERE.html\`. The index has **5 + 5 + 13 = 23**
time-marked scene links for the complete 2-Shorts + 108-second landscape
review batch. Each row compares the storyboard's **planned narration** against
the actual SHA-bound **draft SRT text**, and links to the corresponding
relative MP4 with a standard media-fragment time range. Some local browsers
do not honor media fragments; open the main HTML player and scrub manually in
that case. Watch and listen to all three complete files, not just individual
links. A scene link never marks a scene watched or approved.

An independent source-free index validator refuses stale/missing/extra or
cross-scene SRT cues, text that differs from its own storyboard, suspicious
media paths, and injected HTML. Adversarial tests cover these cases and
the GitHub CI renderer checks **23 scene links** in the three-video pack.
This is only a convenient way for the real owner to identify errors in
mispronounced words, approximate cue timing, scene transitions, audio balance,
and artistic quality. **Matching planned text and SRT is not proof of spoken
word accuracy, phoneme timing, actual rights, owner consent or permission
to publish.** The exact WAV/MP4/SRT release continues to require fresh owner
listening, editing, licensing proof and a trusted A6 signature. All automated
upload/schedule/publication flags remain FALSE.

## Landscape headline-art clearance — second visual QA correction

The later full-resolution run [43558270457](https://github.com/Tirthanand17/taskless-lab/actions/runs/43558270457) confirmed the **two Shorts' illustrated controls are now visibly separated from spoken captions**, but its landscape contact sheet still showed parts of door/portal art touching orange subheadlines. The landscape geometry now reserves an additional upper safe region: icon graphics begin **below 43% of frame height** and finish before the lower caption zone. The Short geometry remains unchanged. This does not improve the synthetic voice or guarantee audience retention; another real video render and visual check are required before owner approval.

## Illustration clearance fix discovered by all-beat contact sheet

The first verified all-beat review artifact, [GitHub run 43557461327](https://github.com/Tirthanand17/taskless-lab/actions/runs/43557461327), confirmed 5 + 5 + 13 caption frames and provided a JPEG contact sheet per episode. Inspecting these **real MP4-derived** visual summaries exposed large portal rings and doors intruding into the same lower-screen area as spoken subtitles. They were technically visible but not visually separated.

The renderer now places original doors, portals, timer and abstract score icons inside a bounded **middle illustration slot**, reserved above the lower-third caption area. A new geometry invariant checks **both preview/full resolution and vertical/landscape** modes so every icon remains inside safe headroom and below-title spacing. The main GitHub render workflow must pass actual encoded-frame and A6 exact-video QA after this change; old review hashes must not be treated as approved. The sound and estimated text timing remain drafts pending owner listening and commercial asset/tool review.

## New every-beat visual QA and owner contact sheets (under test)

The previous independent subtitle-frame test sampled **only the first spoken cue** in each video. A later scene could lose its captions without the old check detecting it. The new test seeks directly into the **actual encoded MP4** and checks visible caption pixels in a lower-safe area for **every** storyboard beat: five scenes per Short, thirteen scenes in the landscape episode. It also fails if a scene lacks any corresponding SRT cue. The test confirms basic visibility, not exact word alignment or human editorial quality.

A new source-free storyboard contact-sheet generator uses one real frame per beat **plus the final outro** to make a visual JPEG overview of every Short and the 108-second long video. These `original-beat-review-contact-sheet.jpg` files are included in each GitHub Actions original review artifact and linked from the offline HTML player. They help catch late-scene overlap, off-screen text and inappropriate endings; they **do not replace complete human playback or voice/caption review**. Generation re-verifies exact MP4/WAV/SRT/metadata A6 hashes, real FFprobe QA, the all-false owner checklist and all-scene caption visibility before producing a derived JPEG. No external game footage, network assets, signing credentials or YouTube operations are used.

## Latest corrected full-resolution CLIVOX review package — visual inspection passed

**Current recommended review artifact:** [main GitHub Actions run 43555814059](https://github.com/Tirthanand17/taskless-lab/actions/runs/43555814059). This actual `main` push render completed successfully for all **three** original videos (2 × 36-second vertical and 108-second horizontal, at 1080×1920 and 1920×1080). Its ~24.4 MB seven-day GitHub artifact includes the offline `CLIVOX-REVIEW-START-HERE.html`, editable SRT files, exact MP4/WAV/metadata SHA-256 handoffs, independent frame-based subtitle safezone checks, and three unsigned owner review checklists.

The assistant additionally downloaded the real artifact into an ephemeral review environment and **inspected actual video frames** from both Shorts and the long episode. The old off-screen subtitle defect, giant long-video overlay and landscape logo/tagline overlap are visibly corrected; the isolated final outro word no longer lingers. **This is technical visual inspection, not the owner's viewing or final commercial/legal/audio approval.** The eSpeak NG voice and approximate per-line captions still need a real human listening pass. Do not sign the older faulty video hashes.

## A5 actual-video visual regression fix for captions and landscape brand

A frame-by-frame inspection of the full-resolution artifact from [GitHub run 43554270709](https://github.com/Tirthanand17/taskless-lab/actions/runs/43554270709) found a **real** typography problem: FFmpeg/libass `FontSize` and `MarginV` were mistakenly calculated using full output pixels, even though SRT subtitles are rendered using a small virtual subtitle coordinate system. As a result, the portrait Shorts' subtitles were off-screen and the landscape captions obscured the headline. The landscape CLIVOX brand/title also overlapped its descriptor.

The renderer now applies **bounded, native-ASS subtitle font/margin values** and proportionally scales the CLIVOX logo/tagline/footnotes for both aspect ratios. Beyond checking codec/SRT hashes, the independent A5 QA now decodes a real frame during a caption cue and requires visible high-contrast caption pixels in a **lower-middle safe region**. This is a regression check, **not** automatic proof of aesthetically perfect positioning, accurate spoken words or owner approval. Every corrected video gets a fresh SHA-256/A6 unsigned review packet. The older buggy review artifact should **not** be approved or published.

## Latest verified three-video spoken-boundary review master

**Use [GitHub Actions run 43562174869](https://github.com/Tirthanand17/taskless-lab/actions/runs/43562174869) as the current original CLIVOX owner review package.** The automatic `main` render completed successfully with two 1080×1920 Shorts, one 1920×1080 108-second long episode, all-beat frame-caption QA, sound energy/clipping tests, full A6 exact-hash handoffs, three unsigned owner checklists, and offline HTML5 video gallery. Its seven-day review artifact is ~23.8 MB.

Independent analysis of the **downloaded actual** `technical-review-qa.json` reports shows the new postmix waveform and SRT starts/ends agree within a maximum of **20 milliseconds across all 23 scene beats** (5 + 5 + 13), tighter than the enforced 140ms threshold. These measured *utterance boundaries* are not evidence that individual words or phrasing are accurate; real owner listening, professional narration, commercial permissions and exact-video signing are still uncompleted. Do not sign earlier, differently hashed review videos.

## A5 precise spoken-activity start/stop checks (still draft word timing)

An independent audit of actual mixed WAVs from [GitHub run 43560967644](https://github.com/Tirthanand17/taskless-lab/actions/runs/43560967644) found the old editable SRT ended about **0.29–0.34 seconds after genuinely active eSpeak speech** in the scenes checked. The renderer had already started timing the utterance by its PCM container rather than entire storyboard beats, but the file contained trailing silent PCM.

The next A5 change measures actual above-threshold *dry synthesized voice* activity in 20ms windows to remove silent samples from **draft cue start and end timestamps**. A separate post-render QA reopens the **final mixed WAV**, reconstructs/subtracts CLIVOX's original procedural tone and transition sting, and requires each scene's first/last SRT cue boundary to lie within **140ms** of the recovered active-speech envelope. This detects falsely aligned subtitles and a silent TTS track even when the background music/stings are audible.

Neither activity detector verifies words or phonemes, human listening, TTS quality, spoken accuracy, or sound/voice commercial rights. Individual cue durations are still estimated by character lengths; a human must correct them to actual speech before any A6 final approval. The change regenerates new exact SHA-256 hashes and unsigned review forms.

## A5 independent every-scene narration energy QA

The technical video check previously only proved that the **first second** of the WAV was non-silent. A new independent pure-Python 48 kHz/16-bit PCM verifier now checks **each storyboard beat** for three or more quarter-second windows of nontrivial audio energy and rejects near-full-scale clipping, wrong sample format, corrupt/truncated audio and missing/overlapping storyboard windows. This catches a video with a working introduction but silent or extremely quiet narration in a later scene.

This is an **acoustic-energy proxy**, not speech recognition or voice/caption alignment: a loud musical or sound effect could also pass. Human must still listen through the entire master to catch mispronunciations, irritating TTS, copyright/license issues, sound effects masking speech or badly aligned text. Each independently QA'd WAV remains SHA-bound to the exact A6 handoff; no publication rights are gained.

## A5 narration-window subtitles and on-screen reading improvements

The renderer previously spread subtitle cues across **whole screenplay beats**, even when its synthetic narration finished earlier. It now measures the **actual generated 48 kHz post-tempo voice PCM interval per beat** and assigns the editable SRT's cue windows within that interval, distributing estimated cue timing by text length. It also embeds those clearly marked **draft** subtitles into the review MP4 with safe-margin, high-contrast text, while keeping a separately editable SRT in the GitHub artifact.

This is an engineering improvement in speech-window timing, **not** word-by-word forced alignment or an audio transcription audit. No operator has verified the precise word timestamps or voice quality, and the subtitles now end when measured speech ends, leaving the static comment CTA visible without a stranded final word. A human must listen with the captions visible and correct misread/misaligned speech before signing any exact-video release. Any new render replaces the exact MP4/WAV/SRT hashes and requires a **new A6 owner review**. FFmpeg's [subtitle overlay](https://ffmpeg.org/ffmpeg-filters.html#subtitles-1) uses the `libass` library, installed in the ephemeral GitHub Actions renderer. On-screen text is consistent with [YouTube Shorts editing tips](https://support.google.com/youtube/answer/13380879), but is not evidence of additional audience retention or virality.

## Original program concept

**Series:** The Impossible Arcade — entirely imaginary gaming puzzles presented as interactive fiction, not footage of a real game.

| Episode | Format | Runtime | Original premise |
|---|---|---:|---|
| A Door That Opens Only When You IGNORE It | Vertical Short | 36s | Three options, but choosing no button wins |
| Only ONE Portal Is Safe... What Would You Pick? | Vertical Short | 36s | The broken-looking portal is the hidden exit |
| 3 Impossible Arcade Decisions That Reveal How You Play | Horizontal | 108s | Three quiz rounds, payoff, score and viewer comment prompt |

All scripts, metadata, vector drawings and synthesized procedural sound effects are authored within this project. The voice uses the open-source **eSpeak NG** synthesizer at render time; it is a synthetic narration **draft**, not a human-recorded final performance. The SRT derives from the screenplay with estimated beat timing; it is **not** forced aligned to the audio. Human audition/editing and rights/license review of final audio tools are still needed.

## GitHub-only artifact workflow

- Source blueprint: [arcade_trio.json](arcade_trio.json), with immutable Clivox channel ID and negative source-footage/creator-clip permission flags.
- Renderer: `scripts/branch3_original_arcade_pilots.py`. Original gradient/vector graphics, motion/caption artwork, generated speech and sound bed, H.264/AAC MP4 with high-resolution option. No media URLs or game assets.
- Actual FFprobe/hash QA: `scripts/branch3_original_arcade_qa.py`, including expected aspect, fps, AAC rate, video SHA, audio WAV format, draft captions and **every release flag false**.
- Adversarial unit tests: `scripts/test_branch3_original_arcade_pilots.py`. Wrong FlowMinute channel, unsupported footage, fake approval, bad clip timing, malformed captions, missing audio and wrong dimensions fail closed.
- Action: [Branch 3 Clivox Original Arcade 2 Shorts + Long REVIEW Renders](../../.github/workflows/branch3-clivox-original-arcade-pilots.yml). PR renders the **first Short only** at 540×960 24fps. A manual `workflow_dispatch` with `selection=all` and `render_mode=preview` renders **two Shorts plus the longer landscape episode** in GitHub-hosted ephemeral storage. `render_mode=full` produces 1080×1920 / 1920×1080 30fps review copies. **New:** a protected code merge affecting the original scripts, A6 handoff or render workflow now triggers a GitHub `push` run on `main` that renders **all three full-resolution** review videos and packages unsigned A6 forms automatically. PRs still render only one low-resolution Short; neither path can upload, schedule or publish.
- Artifacts: public-safe **original-only** MP4s, rendered scene cards, draft SRTs, SHA manifests and independent technical QA JSON. Seven-day retention; no copyrighted footage, confidential contract or OAuth token stored. The 48kHz synthetic narration is embedded as AAC in MP4; a synthetic-only intermediate WAV is included in the review artifact so the owner can check voice and exact SHA binding.

To view the videos, open the workflow run's **Artifacts** section, download `clivox-original-arcade-review-<run-id>`, and review each `original-review-preview.mp4` by episode directory. All files exist only in GitHub's hosted runner/artifact, **not on a user's laptop or in repository history**.

## Open the videos easily: offline CLIVOX reviewer gallery

After a new original render completes, download and **extract** the `clivox-original-arcade-review-<run-id>` ZIP from GitHub Actions and open `CLIVOX-REVIEW-START-HERE.html` in a desktop browser. Its dark, responsive CLIVOX-styled cards embed **local** MP4 controls for each episode and link the exact draft SRT file. It lists the exact MP4 SHA-256 digest and five pending owner checks, without ever claiming that you approved the video. There is **no JavaScript, external CDN, cookie, tracking, OAuth, YouTube link or upload control**. Do not open the HTML without extracting the video folders, because relative playback links will not resolve inside an unopened ZIP.

The gallery is constructed only after rerunning the actual A5 media FFprobe/QA, A6 video/WAV/SRT/metadata digest checks and unsigned worksheet verification; any changed video, subtitle, misleading metadata, or forged review flag fails closed. It is a local **viewing interface**, not a formal recorded approval/signature; the owner must still inspect every clip, voice, caption and copyright/licensing condition.

**Verified main automatic full 3-video run:** [GitHub run 43551704973](https://github.com/Tirthanand17/taskless-lab/actions/runs/43551704973) completed successfully with all real video/unsigned form QA and a 25 MB review artifact. That historical run predates this new gallery feature; a subsequent merge of gallery support will automatically generate a new full-resolution three-video artifact with the HTML included.

## New unsigned exact-video human editorial checklist

Every future three-video render produces an `owner-editorial-review-UNSIGNED.json` per episode in its seven-day GitHub review artifact. The form is bound to the exact real video, audio, subtitle, metadata and A6 handoff digest, but **all five review flags are false** until a human actually watches and checks the video. A new independent **read-only verifier** immediately reopens the finished full review package, re-runs FFprobe/A5 media QA and checks every unsigned form against its rebuilt A6 digest, without signing, uploading or changing media. It does **not** approve the draft synthetic narration or SRT timing; a change to the actual final audio or captions requires new hashes and review. [Owner-only editorial attestation guide](../release/ORIGINAL_EDITORIAL_OWNER_ATTESTATION.md) explains the optional offline signature math without a production key or publishing permission.

## New per-video A6 original exact-file review packet

Every new render run first recomputes the technical QA from the real MP4 and binds the exact MP4/WAV/SRT/catalog, metadata and QA SHA-256 values into `owner-handoff-quarantined.json`, alongside `metadata-preview.json`. The full run artifact contains all three packets. This is a **review evidence package only**; it does not establish owner rights, approval or permission to publish. See [A6 owner handoff instructions](../release/ORIGINAL_VIDEO_OWNER_REVIEW_HANDOFF.md).

## Mandatory creative review before release

1. Watch each actual video on mobile and desktop. Check legibility, clip pace, originality, audio loudness/clipping, grammatical accuracy, icon animations and beginning/end hooks.
2. Confirm eSpeak NG voice/artifact is appropriate for commercial use and audio accessibility; replace with a professional original/licensed narration and align captions to the final voice if necessary.
3. Ensure thumbnail, episode claim and description clearly call this a **fictional original mini-game**, not a real GTA VI feature or gameplay. Keep the series distinctly CLIVOX.
4. Owner approval of the final exact video SHA and truthful metadata is mandatory. These automated review copies **intentionally carry an on-screen ORIGINAL PREVIEW / HUMAN REVIEW REQUIRED label**.
5. A separate A6 signed exact-render release and A7/A8 private-first owner authorized YouTube flow must be implemented and actually verified. **No automatic publishing from this PR**.
6. Evaluate real viewer retention/watch data only after authenticated uploads. A strong mock video/render test cannot guarantee a viral result.

## Production status

The source-free original-first approach avoids the need to obtain a third-party clip grant **for these scripted fictional designs**, but does **not** waive asset, voice, music, logo, platform, copyright, QA or final owner responsibilities. These preview copies have no third-party gameplay, no externally downloaded audio, zero license claims, zero creator clipping permissions and zero YouTube uploads. A9 first **real licensed/published** pilot remains 0%. Branches 1 and 2 untouched.
