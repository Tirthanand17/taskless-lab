# FlowMinute Lab — November 13–17, fifteen exact owner-review release candidates (NO YOUTUBE)

**Source audit:** The five trusted `main` H264/AAC render jobs **all succeeded** on November 11, 2026. Each job rendered exactly 2 Shorts and 1 long with actual decoded audio/video and SHA-256 checks. **All 15 new videos are still unapproved and unuploaded** at this point.

| IST date | Successful real 3-video source run | Real durations in that day's order (Short/Short/Long) |
| --- | --- | --- |
| November 13 | [42976444411](https://github.com/Tirthanand17/taskless-lab/actions/runs/42976444411) | 34.075s / 34.437s / 185.381s |
| November 14 | [42976449694](https://github.com/Tirthanand17/taskless-lab/actions/runs/42976449694) | 38.397s / 32.739s / 178.575s |
| November 15 | [42976454084](https://github.com/Tirthanand17/taskless-lab/actions/runs/42976454084) | 33.765s / 35.471s / 171.423s |
| November 16 | [42976458474](https://github.com/Tirthanand17/taskless-lab/actions/runs/42976458474) | 32.420s / 36.294s / 191.007s |
| November 17 | [42976462946](https://github.com/Tirthanand17/taskless-lab/actions/runs/42976462946) | 33.321s / 33.314s / 173.173s |

The sound-mastering issue previously found in the November 14 browser-permissions long was corrected under a strict postencode verification policy; the new full physical batch passed. This is **technical evidence**, not a human watch, copyright signoff or channel state.

## Exact schedule proposals (Asia/Kolkata -> YouTube UTC)

For **each date November 13, 14, 15, 16 and 17, 2026**, propose Short AM at **11:00 IST = 05:30:00Z**, Long at **16:00 IST = 10:30:00Z**, Short PM at **20:30 IST = 15:00:00Z**. Their release metadata files contain only the India clock time; the final exact Z timestamp belongs in the separately human-signed publishing manifest and the immutable publish dispatch, never in a public script key that implies owner approval.

All 15 `content/episodes/fm_2026111*_en.json` metadata files are source-script-locked with actual title/narration, current primary vendor docs, explicit illustration/voice provenance and false owner/write status.

## Packaging flow

The existing protected YouTube publisher requires *one flat artifact per video*, yet each successful render stores 3 videos in subfolders of one owner-review artifact. The new manual-only `.github/workflows/flowminute-b1-nov13-17-flat-candidates.yml` accepts `date_ist` and `source_run_id`, verifies via GitHub API that the source is a **successful workflow_dispatch main run** with exactly the original render workflow name and a concrete source SHA, downloads the exact correctly named GitHub owner-review artifact, and runs `scripts/prepare_b1_nov13_17_release_candidates.py`.

The script:
- Re-validates the source day's complete published-doc-backed script and expected FlowMinute channel.
- Requires the exact original episode IDs, titles, dates, original scene counts and original narration, 2 Shorts and 1 long, and the fixed no-release flags.
- Independently SHA-256 checks each real MP4, SRT, cover and original contact sheet, plus the day brief SHA and all release metadata.
- Requires exact post-encoded physical AAC SHA identity and conservative LUFS/true-peak acceptance, with human listening and release approval explicitly false.
- Stages **three independent flat 3-file owner-review candidates** (MP4/SRT/PNG), each with a provenance file and target UTC time, separate from the three actual original review folders.
- Has no YouTube OAuth tokens, upload commands, publication actions, owner signatures, laptop media writes or persisted weights. Uploaded review candidates expire after 7 days.

Dispatch per date from trusted main, with the source run in the table above:

`gh workflow run flowminute-b1-nov13-17-flat-candidates.yml --repo Tirthanand17/taskless-lab --ref main -f date_ist=2026-11-13 -f source_run_id=42976444411`

Repeat for November 14–17 with the matching real source run. **Do not confuse 3 SHA-bound flat candidates with 3 scheduled YouTube videos.**

## Remaining release blockers

1. Review the exact final MP4, voice, timed subtitles, primary facts, original media and rights. No tool can claim this owner's complete individual watch without evidence.
2. Restore owner channel publishing authorization. The prior GitHub OAuth refresh returned `OAUTH_REFRESH_FAILED`. Separately, connected vidIQ showed the correct channel **canPublish**, but a fresh `vidiq_authorize_with_youtube` call returned **`verification_required`**, requiring **the human owner to complete the provided Google/YouTube MFA link**. Neither source is an authenticated scheduling readback.
3. The GitHub `youtube-production` publisher additionally requires **owner-controlled Ed25519 exact MP4+SRT+thumbnail+metadata/time signing**, currently absent. The vidIQ workflow uses its own verified authorization and requires showing the final draft and owner approval of the exact media/time before `social_post_publish`.
4. Recheck owned-channel public and private inventories for duplicates and slot collisions, only then upload private, set each exact future `publishAt`, and independently verify YouTube video ID, processing, caption availability and scheduled time. Do not replace or edit already scheduled November 11 assets.
5. Never upload just because a source artifact, owner account connection, media import, draft or render succeeded.

**Actual confirmed additional November 13–17 scheduled releases: 0/15 until verified directly against YouTube.**
