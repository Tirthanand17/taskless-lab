# FlowMinute Autopilot: research, architecture and deployment gates (2026-10-14)

## Audit of the existing project
- FlowMinute Lab channel: UCCcL9Q_jqVq6LJmnYUSAFZA.
- Repo taskless-lab is PUBLIC. It has Remotion 4 React compositions, FFmpeg quality scripts, natural/Edge and offline Kokoro narration and an authenticated YouTube publishing ledger.
- It also has many per-episode .github/workflows, e.g. qa-tomorrow-pack.yml hardcodes v7/v8/long003, while publish-artifact-youtube.yml is manual workflow_dispatch. This is why repeatedly saying "continue" has been necessary.
- A small number of real videos/subscribers is insufficient for reliable virality prediction; treat optimization as measurement-driven experiments, not promises.
- This prototype does not touch current live Oct16 production.

## Decisions from current official source research
- GitHub Pro (student pack) provides 3,000 included private Action minutes/month; public standard GitHub-hosted actions are free, but artifacts/storage and platform policies still apply. Pack ≠ guaranteed extra Action credits.
- Azure for Students advertises $100 credit and eligible services; Heroku offers $13 USD/month for 24 months; Appwrite Education enhanced plan. Offers must be redeemed, can expire and may restrict media/GPU workload.
- DigitalOcean student credits were retired July 31, 2026; do not design fallback based on them.
- GitHub Releases permits 1000 assets per release with individual files below 2 GiB, no release bandwidth cap, but repository git history should stay small; store final releases/assets here with rights/privacy considered, and production drafts in object storage.
- YouTube API scheduling requires a Private never-published video and status.publishAt. Past dates may trigger IMMEDIATE publication: prevent them. Unverified API projects may restrict uploads to private until audit.
- YouTube inauthentic/mass-produced generic content monetization policy: reusable brand acceptable, repetitive interchangeable educational filler not.
- Synthetic realistic visuals require appropriately accurate disclosures; never imply real product footage if animated.
- Self-hosted runner attached to public repository creates compromise risk; privileged publisher and secrets must be on a PRIVATE control repo/service, separate from the public site/content repo.

Official sources:
https://education.github.com/pack
https://docs.github.com/en/billing/concepts/product-billing/github-actions
https://github.com/github-education-resources/Student-Developer-Pack-Current-Partners-FAQ/blob/main/SDP-changelog.md
https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
https://docs.github.com/en/actions/reference/security/secure-use
https://developers.google.com/youtube/v3/docs/videos
https://developers.google.com/youtube/analytics/metrics
https://support.google.com/youtube/answer/1311392
https://blog.google/intl/en-in/products/platforms/improving-ai-labels-for-viewers-and-creators/

## Recommended architecture: one director with 8 bounded specialists

1. **Trend Scout** (nightly): official company feeds, Google Trends, community questions, search topic gaps. Timestamp and cite every factual assertion; rank topic novelty × viewer benefit × example feasibility × evidence confidence.
2. **Investigative Researcher**: cross-check news, feature eligibility, price, release date; two independent sources with one primary. Does not confuse announcements with measured tests.
3. **Script Editor**: write one long explanatory narrative plus two genuinely distinct short takeaways; hook → real problem → example → why it matters → one good comment question. Avoid repeated template storylines.
4. **Audio & Media Director**: preferred offline CPU Kokoro, then explicitly approved alternative providers based on actual rate limits and terms; source-licensed stock, original Remotion animations, motion storyboard tied to precise spoken audio.
5. **Quality Inspector**: full H264/AAC decode, loudness/peak, silence and end-word alignment, aspect/safe area, actual caption alignment, visual contact sheets, asset license, title/source audit, disclosure assessment, hash and signed manifest.
6. **Upload & Schedule Controller**: private-only upload, immutable episode/media hash, YouTube processing success and thumbnail verification, exact future IST publishAt, authenticated read-only reconciliation after ambiguous responses. Never blind retries, no duplicate IDs.
7. **Audience Scientist**: daily 24/72-hour and weekly 7/28-day YouTube Analytics, engaged views vs raw plays, Shorts stayed-to-watch, audienceWatchRatio graph, average percentage watched, first-30s long-form retention, impressions CTR, subscribers per 1000 engaged views, genuine comments per 100 engaged views. Require minimum sample sizes before changing strategy, no fake engagement.
8. **Reliability/Security Officer**: global lease (one owner per daily release), retry budgets, provider cooldown, approval/licence registry, secrets isolation, spend cap, alert and backup. If no approved provider or quality failed, quarantine and explain, not publish filler.

## Hosting and storage
**Control plane:** separate private repo + persistent low-cost scheduler (Render/Heroku if pricing/availability confirmed), or GitHub Actions standard public runner *only for unprivileged work*. Do not put OAuth refresh tokens in this public repo, GitHub Release assets, or logs.

**Worker:** hosted render machine/container when credit and CPU allow; existing Nirala PC is temporary fallback inside *youtube con* only, but it is not reliable as sole always-on production runner. Cloud render requires benchmark of CPU/RAM and media size before claiming 24/7 reliability.

**Media:** raw/render intermediates in protected object storage with TTL and optional cloud object store replication. Publish final MP4 and thumbnail to a private GitHub Release where size, privacy and rate limits allow. Use SHA256 checksums and immutable manifest; do not git-add new videos directly to source history.

**Database:** SQLite is sufficient for a single local worker, but move durable releases/jobs/leases to Postgres for multiple cloud workers. Transactional uniqueness on (episode_id, media_sha256, publication_slot) prevents doubles. Retain hard receipts.
**Rights/privacy:** no personal profiles, user account credentials or confidential video drafts on public assets; disallow downloading/repurposing competitors' footage without a license.

## Deterministic daily loop
At 18:30 IST research 8–15 candidates for day+1. Before 20:30 rank and select 1 long + 2 Shorts (quality over quota). By 05:00 next morning render QA, with 2h slack before first slot. Privately upload/verify before 09:00; final schedule slots are 11:00/16:00/20:30 IST. PublishAt must be *future* and 15+ min ahead; if missed, reschedule a new slot rather than retroactively force public. Check YouTube release success 30–45 min after each scheduled slot.

After 24h and 72h compare engagement to a rolling baseline by content type, age, and traffic source. Do not chase a Shorts view count without engaged view/watch-time context. Use only one controlled hook/thumbnail/topic-format test at a time and test several episodes before adopting.
Cost router chooses only paid providers explicitly budget-approved; when exhausted, use authorized zero-cost offline tool *if quality gate passes*, otherwise skip release, NOT rotate unapproved accounts.

## Phased implementation roadmap
P0: private privileged control project, credential inventory, content licence registry, money cap and quotas, confirm approved Student Pack offers. (Requires one-time user connection/approval.)
P1: this safe ledger, gates and source-quality checks, unit tests, dry-run. (In this feature branch.)
P2: adapter for existing Remotion/FFmpeg + voice generation and forced caption alignment; technical QA and provider router. 
P3: real autonomous topical researcher, evidence snapshots + differentiating scripts; humanless quality-passing production.
P4: YouTube Data + Analytics adapter, exact release monitor, archive final assets to GitHub Release/private cloud, operation alerts and retries.
P5: move from Nirala to cloud running 7d without missing a release; A/B experimentation and weekly science report.

## Hard limitations
Student offers aren't free unlimited GPUs. No tool routing can guarantee zero spending, infinite rendering, uninterrupted APIs, or viral subscriber growth. Continuous unattended publishing is conditional on valid OAuth/limits, copyright/licensing, cloud runtime and passing the quality inspector. The system does not impersonate human voice.
