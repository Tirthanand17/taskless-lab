# FlowMinute Lab — Laptop-off Autopilot Migration v2

**Status: CLOUD FOUNDATION ONLY; NOT YET A FULLY DEPLOYED VIDEO PUBLISHER.**
**Effective user boundary:** no access to Nirala or any user laptop unless the owner separately authorizes a *specific* action. The remote Desktop Commander connection is NOT a standing permission. Do not run, restart, update or clean Windows files/jobs remotely without permission.

## Findings (October 16, 2026)

- `taskless-lab` is a **PUBLIC** GitHub repository. It includes Remotion compositions, local publisher scripts, episode manifests and editorial assets. It should contain no OAuth refresh tokens, account passwords, private job data, or unpublished personal material.
- Earlier `feature/flowminute-autopilot-v1` implements a *local dry-run control plane* (state machine, topic/media gates, SQLite uniqueness and provider budgets), but NOT research APIs, cloud rendering, live analytics, cloud storage, production secrets or unattended Youtube publication.
- The Render workspace has existing **unrelated** applications. No dedicated FlowMinute Render cron job or media worker is deployed. Do not change those other applications.
- Existing local jobs on Nirala may continue until its owner disables them. **The cloud project must never assume they are off or attempt to use them.**
- GitHub Actions standard hosted minutes for public repos are documented as free, but artifact/cache storage, concurrency, API quotas and platform policies still constrain the workload. Public Actions may be appropriate for unprivileged research and QA; using them as an OAuth publisher is not approved.
- Render cron jobs have a minimum **$1/month per service** and metered CPU; separate media storage, bandwidth and licensed AI APIs may add cost. A Render free web service sleeping is not an acceptable always-on production scheduler.

## What is already coded in this branch

- `autopilot/core.py` + `autopilot/test_core.py`: previously audited immutable release gates and duplicate prevention, copied from the existing isolated prototype.
- `autopilot/scout.py`: public RSS/Atom candidate leads, fresh-source filtering, no fabricated facts, no OAuth. It only creates research **leads**, never finished scripts or videos.
- `autopilot/growth.py`: age-matched Shorts/long cohort insights and minimum samples, prevents interpreting raw views as retention.
- `autopilot/cloud_guard.py`: refuses local Windows paths, laptop usage, missing cloud services, unapproved budgets and missing private OAuth storage.
- `autopilot/test_cloud_foundation.py`: unit tests for feed parsing, novelty, sufficient engagement samples, budget and laptop restrictions.
- `.github/workflows/flowminute-cloud-scout.yml`: scheduled daily 13:15 UTC / 18:45 IST unprivileged research job and PR tests. It has `contents: read`, does not access OAuth, does not render, and does not publish. GitHub scheduled workflows only operate from the default branch **after merging**; the schedule may start later than the exact trigger.

## Fully autonomous target architecture (not yet running)

```
18:30 IST   trend scout -> official primary sources + independent reporting
20:30 IST   research verify -> source fact sheet -> choose differentiated stories
night      script editor -> voice casting Short A != Short B -> storyboard
overnight  private cloud media worker -> licensed stock + original Remotion graphics
            -> Kokoro or approved TTS -> H264/AAC -> captions -> QA
by 09:00  private credentials + durable ledger -> PRIVATE YouTube upload
            -> remote processing and thumbnail -> release schedule receipts
11/16/20:30 IST scheduled YouTube public releases, not direct instant publishing
day +1/3  YouTube Analytics API -> engaged views/retention/subscriber yield
weekly     test one hook/thumbnail/topic variable, archive evidence and update prompts
```

**Dedicated components needed**:
1. **Source-backed topical researcher**: real provider/data connector; source attribution; freshness and original examples. AI-written scripts must be independently grounded and must not invent real product demonstrations.
2. **Production container**: Python 3.11+, pinned FFmpeg, licensed Kokoro model/voices or approved natural TTS, Node/Remotion/Chromium with actual CPU/RAM and duration benchmark. Static design should adapt to evidence and safe area, rather than recycling a generic template every day.
3. **Security boundary**: separate *private* GitHub repo/project for privileged services and cloud secret manager. Never place YouTube OAuth refresh token, access key or raw personal analytics in the public `taskless-lab` repo. Read-only research workflows have no publishing permission.
4. **Durable cloud storage and lease**: cloud object store for intermediate videos, licensed sources, narration and thumbnails; Postgres/key-value release identity, job state, API receipts, and no duplicate upload after ambiguous responses. Local SQLite inside an ephemeral Render cron container is not durable.
5. **Official YouTube OAuth**: one-time owner action granting least-privilege upload/manage/analytics scopes; secure token renewal; separate per-video API verification; no credential retrieval from Nirala without explicit owner approval. Uploads are private first; schedule only after QA and remote processing.
6. **Audience scientist**: authorized `youtubeanalytics.googleapis.com/v2/reports` for `engagedViews`, `averageViewDuration`, `subscribersGained`, comments, watch ratio and audience retention when supported. Compare age-matched peers separately for Shorts and long; data may be too small for confident optimization.
7. **Policy/quality inspector**: accurate captions/audio, human-style **synthetic** voices distinct per Short, original demonstrative visual value, licensed asset provenance, real source verification, audio peak, full FFmpeg decode and contact sheets. Avoid YouTube's generic mass-produced/repetitive content pitfalls.
8. **Alerts**: if cost/source/audio/video/account quota fails, stop and report. Never publish low-quality filler, evade provider rate limits, call a locally-offline laptop, or silently pay a new provider.

## Hosting choices and real costs

**Option A (recommended to test first):** unprivileged editorial + CI on standard public GitHub Actions, plus a small **private cloud publishing worker** hosted as a Render cron service, with approved credentials and a durable object store. Render bills at least $1 monthly *per cron service*. Official Render pricing lists several compute tiers by minute; 512MiB RAM may be too small for Chrome+Remotion, and real costs require a rendering benchmark. An overnight render may span more than a single cron job's 12-hour maximum; timeouts and staggered component jobs required.

**Option B:** fully PRIVATE GitHub Actions for the privileged segment. Account included minutes/artifact quotas and billing constraints are not verified; user previously reported exhausted Actions allowance. Do **not** assume Student Pack means extra Actions quota.

**Option C:** Azure for Students / Heroku / Appwrite credit may help ONLY if actually redeemed, eligible, sufficient and still valid; neither free compute nor student offers are confirmed on this account.

Do not deploy paid Render cron jobs or enable cloud billing without user's explicit spend approval. Do not claim zero cost or viral subscriber growth.

## One-time authorizations needed before live cloud rollout

1. Create a **private** GitHub repo called `flowminute-control-private` (do not clone unrelated finance or personal repos). Only the owner and trusted deploy identities may access it. A user can do this in GitHub > New repository > Private; no laptop terminal is necessary.
2. Select cloud provider, confirm a firm **monthly spend ceiling** (could be $0 for research-only phase; a real video worker may need paid compute or verified credits). This system must default to $0 and refuse paid work until approved.
3. From the **cloud** (not from Nirala), authorize YouTube upload/manage and YouTube Analytics read-only OAuth through the project's dedicated verified app. Store credentials only in Render/secret manager; never paste them into chat, GitHub source or PR comments. Consent is separate from ordinary Google login.
4. Connect a protected media store. Configure provider model credits and voice/media licenses.
5. Dry-run 3 representative productions on hosted CPU: 1080x1920 Shorts twice, 1920x1080 long once. Check actual runtime, cost, peak RAM and persistence after restarts.
6. One shadow week: verify research facts, technical QA, audience analytics, source authenticity, publishing collisions and recoveries. Enable production writes only after successful verified dry runs.
7. Once cloud covers a complete release, turn off local Windows tasks. No remote PC access is required.

## How the owner can disable legacy Windows production (optional, locally run by owner)

Open PowerShell **on your PC** and run this exactly **if you want to stop the earlier scheduled automation**:

```powershell
$tasks = @(
  'FlowMinuteOct18Production', 'FlowMinuteOct18Watchdog',
  'FlowMinuteOct19Production', 'FlowMinuteOct19Watchdog'
)
foreach ($task in $tasks) {
  Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
  Disable-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
}
Get-ScheduledTask -TaskName $tasks -ErrorAction SilentlyContinue |
  Select-Object TaskName, State
```

This disables those jobs without deleting `youtube con` or its media. Other manually started Windows processes are not covered. If this user instruction supersedes an earlier permission, do not access the PC to perform it.

## Verification contract

- `PUBLIC_RESEARCH_ONLY`: source scout completed, unverified leads generated, no YouTube writes.
- `CLOUD_QA_READY`: hosted voice/render pipeline demonstrably passing tests; still no YouTube writes.
- `CLOUD_AUTHORIZED`: private secrets and persistent ledger verified, approved budget.
- `3/3_SCHEDULED_VERIFIED`: authenticated read-only YouTube API confirms channel, private status, processed succeeded, custom thumbnail, intended UTC publishAt and immutable video ID for each asset.
- `PUBLIC_VERIFIED`: each scheduled item is Public at its actual release time; never infer from a calendar plan.
- `ANALYTICS_ACTIVE`: official read-only Analytics scope and valid recent per-video reports, controlled experiments informed by actual data.

No stage may be described as complete before its verified evidence exists.
