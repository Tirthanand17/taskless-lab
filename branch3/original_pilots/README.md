# CLIVOX — Original-first 2 Shorts + 1 longer arcade pilot REVIEW pack

**Status (2026-11-13):** All three original preview **and full-resolution** MP4s actually rendered successfully with FFprobe checks in GitHub Actions (runs [43380418384](https://github.com/Tirthanand17/taskless-lab/actions/runs/43380418384) and [43380650008](https://github.com/Tirthanand17/taskless-lab/actions/runs/43380650008)). Human playback/editorial review, final-voice/caption alignment, owner signing, private-first upload and publication are still **NOT complete**. A new A6 exact-asset owner review packet is added to all future renders; previous historical runs do not contain that new A6 packet. **NOT published, scheduled, approved for upload or licensed third-party clips.**

CLIVOX can create first-party material without borrowing a gaming streamer, another creator's reaction, Rockstar/Take-Two footage, podcast extracts, commercial audio or a game logo. This pack demonstrates that path and provides a concrete review artifact beyond the older source-free placeholder benchmark.

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
- Action: [Branch 3 Clivox Original Arcade 2 Shorts + Long REVIEW Renders](../../.github/workflows/branch3-clivox-original-arcade-pilots.yml). PR renders the **first Short only** at 540×960 24fps. A manual `workflow_dispatch` with `selection=all` and `render_mode=preview` renders **two Shorts plus the longer landscape episode** in GitHub-hosted ephemeral storage. `render_mode=full` produces 1080×1920 / 1920×1080 30fps review copies.
- Artifacts: public-safe **original-only** MP4s, rendered scene cards, draft SRTs, SHA manifests and independent technical QA JSON. Seven-day retention; no copyrighted footage, confidential contract or OAuth token stored. The 48kHz synthetic narration is embedded as AAC in MP4; the intermediate WAV is not uploaded.

To view the videos, open the workflow run's **Artifacts** section, download `clivox-original-arcade-review-<run-id>`, and review each `original-review-preview.mp4` by episode directory. All files exist only in GitHub's hosted runner/artifact, **not on a user's laptop or in repository history**.

## New unsigned exact-video human editorial checklist

Every future three-video render produces an `owner-editorial-review-UNSIGNED.json` per episode in its seven-day GitHub review artifact. The form is bound to the exact real video, audio, subtitle, metadata and A6 handoff digest, but **all five review flags are false** until a human actually watches and checks the video. It does **not** approve the draft synthetic narration or SRT timing; a change to the actual final audio or captions requires new hashes and review. [Owner-only editorial attestation guide](../release/ORIGINAL_EDITORIAL_OWNER_ATTESTATION.md) explains the optional offline signature math without a production key or publishing permission.

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
