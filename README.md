# FlowMinute Lab

## FlowMinute two-track automation plan (2026-11-04)

Two separate Git branches and scopes keep existing YouTube releases safe while building an independent cloud pipeline:

- **Assisted releases:** [`track/assisted-youtube-releases`](https://github.com/Tirthanand17/taskless-lab/tree/track/assisted-youtube-releases) preserves the existing ChatGPT-assisted, SHA-pinned, owner-approved YouTube operations and recovery logic.
- **Independent cloud AI agents:** [`feature/flowminute-cloud-autopilot-v1`](https://github.com/Tirthanand17/taskless-lab/tree/feature/flowminute-cloud-autopilot-v1) is the separately developed cloud-only architecture; [research and deployment gates](docs/FLOWMINUTE_CLOUD_AUTOPILOT_2026-11-04.md).

**Currently operating on GitHub:** [daily GitHub-hosted NO-PUBLISH foundation](.github/workflows/flowminute-daily-cloud-foundation.yml), scheduled at 13:17 UTC (18:47 IST). It runs a bounded real public-lead scout, three next-day unverified research slots, prepares original fictional educational rehearsal scenes, and physically renders **two original 1080×1920 Shorts + one 1920×1080 long-form MP4 (17 total scenes)** with synthesized Kokoro voices, native ASS captions, progressive editorial graphics, low-level sound design, and FFmpeg decode/QA. On a normal scheduled/main-push run, these unapproved video assets are **deleted**, not uploaded to YouTube or persistently deployed. Only a main-branch **manual** workflow with explicit `retain_rehearsal_review_artifact=true` retains the three SHA-bound MP4s and offline review player for **one day**; artifacts can be accessible to repository readers. Live review, facts, rights and exact release authorization are separate.

**Production status:** Owner-approved facts and rights, independent full-video review, genuine AI agents operating autonomously rather than deterministic 48-role task contracts, durable private paid-cloud infrastructure and vault, refreshed authenticated YouTube OAuth, protected continuous publishing worker, and 7 consecutive days / 21 independently verified video releases are **not complete**. The [dated phase-by-phase audit and overall progress rubric](docs/status/flowminute-full-phase-audit-2026-11-07.md) provides the evidence rather than estimating progress from PR counts alone. Read-only GitHub-cloud [YouTube audit 42346682195](https://github.com/Tirthanand17/taskless-lab/actions/runs/42346682195) failed `OAUTH_REFRESH_FAILED`; none of the Branch 2 unattended releases are verified, and the existing Branch 1 assisted YouTube schedule is a separate, historically observed but **not currently reconciled** workstream.

**Workspace policy for current Branch 2:** Run unprivileged test/render/research jobs on GitHub Actions; do **not** use the user's laptop for project storage, rendering, OAuth secrets or media. An authenticated Desktop Commander / `gh` CLI can be used only to trigger and inspect GitHub remotely when connected. The legacy assisted Branch 1 workstation guidance in [Local Workspace Policy](docs/LOCAL_WORKSPACE_POLICY.md) describes the historical assisted path, **not** permission to restart laptop-based Branch 2 video processing. No existing scheduled/public YouTube file is replaced automatically.

A faceless, original micro-content brand about practical automation, data cleanup, and workflow efficiency.

**Local Windows workspace:** Keep all non-secret video assets, render outputs, QA media and Git worktrees inside the existing `C:\\Users\\Dell\\Desktop\\youtube con\\` folder. OAuth tokens and private upload receipts stay in the original restricted user-private folder. See [Local Workspace Policy](docs/LOCAL_WORKSPACE_POLICY.md).\n\n## Mission

Publish useful, original short-form videos that solve one repetitive-work problem at a time without relying on a personal identity, recycled clips, or mass-produced filler.

## Adopted growth and editorial standard (v2 — October 9, 2026)

**[Read the audited production standard](docs/FLOWMINUTE_GROWTH_PRODUCTION_STANDARD_V2.md).** This is the source of truth for future releases.

- Publish **informative + genuinely interesting** original tech stories, with practical proof, readable visuals, appropriate cinematic footage, and diagrams when helpful.
- When asked for a day's production package: research same-day/previous-day AI, ML, Excel, automation, agents, and software trends before choosing topics.
- Daily **target**: two distinct Shorts + one long video; extra trend coverage only when verified and valuable. Never lower quality or invent tests to hit a quota.
- Follow the documented research, story, visual QA, truthful synthetic-media labeling, verified YouTube scheduling, and 24-hour/48-hour/7-day analytics review process.
- The standard is **not** an automatic scheduled publishing task.

## Natural, human-style voiceovers (new standard — October 12, 2026)

**Every NEW Short and long video must use conversational, natural-paced, well-reviewed narration**, not a fixed-speed robotic reading. Scripts should sound spoken, with authentic pauses, clear pronunciation, controlled emphasis and compelling storytelling. Synthetic audio must never be mislabeled as a human recording. The new narrator defaults to natural mode, and older releases explicitly use legacy mode. No upload may be approved without a complete listening review. See [Natural Narration Standard](docs/NATURAL_NARRATION_STANDARD.md).

## Content model

- 30-60 second original Shorts/Reels/TikToks
- custom scripts and custom motion-graphic visuals
- synthetic narration is allowed, but every episode must add real instructional value
- no reused movie/TV/social clips
- no fake claims, fake earnings, or guaranteed results
- every video has one concrete takeaway

## Revenue paths

1. inbound automation/data-cleaning project leads
2. future digital templates/tools
3. relevant affiliate links only after testing and disclosure
4. YouTube Partner Program after eligibility
5. sponsorships only after audience fit exists

## Initial series

**Fix It in 45 Seconds** — small spreadsheet/data problems with a visible before/after.

See [CONTENT_PLAN.md](CONTENT_PLAN.md) and [MONETIZATION.md](MONETIZATION.md).
