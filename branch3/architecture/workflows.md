# End-to-end workflow — agents, contracts and release process

Target architecture; not all jobs are built. **A1 discovery metadata adapter is implemented and manually runnable in GitHub**; production upload automation stays OFF.

## Nine stage production flow

| Stage | Trigger | Inputs | Output / owner | Mandatory block |
|---|---|---|---|---|
| 00 Discover | manual or rate-limited scheduled read-only scan | public source metadata, campaign links, topical trends | metadata-only SourceCandidate; Discovery agent | Never download third-party clips; unknown creator rights |
| 01 Verify | rights case queued | actual creator-authored grant, issuer identity, source ID, expiry, commercial rights | human-verified RightsGrant receipt; rights reviewer | Cannot infer permission from public promotion/campaign; contracts accepted by owner only |
| 02 Qualify | grant confirmed | source context, all game/music/guest clearances, restricted topics | segment shortlist and moment hypothesis | No unapproved source extraction |
| 03 Story | editorial review | segment facts, original research, transformation idea | first 2-s hook, 9:16 beat sheet, narration | No invented dialogue, misinformation, fake reactions |
| 04 Media | licensed source available privately | escrow source handle + exact allowed ranges, approved narration/assets | deterministic render SHA, isolated media manifest | No source files in public Git; provider/license restrictions |
| 05 QA | render ready | video/audio/SRT/metadata, clip provenance, full source review | evidence report + reject reasons; QA reviewer | no static-card spam, no loop/spinner, caption clipping, unlicensed music, low original value |
| 06 Approval | QA PASSED | exact file SHA, source grant fingerprint, metadata SHA, owner signoff | signed release receipt | every changed byte invalidates signature |
| 07 Upload + schedule | authorized, protected env | verified Clivox OAuth, signed release, ledger, future timestamp | private-first YouTube video ID, readback, schedule | no collision / wrong channel / past publishAt / unsupported upload |
| 08 Analytics | official time windows | verified video ID + API/Studio analytics | experiments and next editorial hypothesis | no engagement manipulation; do not overfit small sample |

## High-confidence gates
A. **Discovery** can be AI-generated; all candidates have zero rights.
B. **Grant issued by rights holder**, not AI; a public URL/policy must be authenticated and rechecked before release.
C. **Source acquisition** must be governed by legitimate rights and approved tool access; YouTube Data API is NOT a general tool to download third-party videos.
D. **Exact source fact-check:** original timestamp, quoted meaning, claims and audio context; game licensing per publisher.
E. **Originality:** at least one substantial new viewer benefit (analysis, perspective, reported context, critique, comedy framing). Qualitative reviewer decides, not an automatic percentage rule.
F. **Content QA:** video vertical 1080x1920, H.264, consistent FPS, AAC 48 kHz, loudness measured, mobile-safe subtitles, readable average line density, truthful metadata, no copyright music by default.
G. **Owner release:** explicit authorization for the exact immutable video, metadata, rights receipt and target channel, cryptographically signed with a separately controlled owner key.
H. **Remote channel check:** channels.list(mine=true) must include only/explicitly select UCfPEvy0SefE_5nNlYlY_CyQ; assert video status private on insert.
I. **Scheduling:** timezone-aware publishAt strictly future with safety margin; no "already published" videos; query YouTube inventory, reconcile upload responses, then write a future schedule.
J. **Observe:** real readback records remote video ID, privacy, schedule and processing; no "scheduled" claim based merely on API request submitted.

## Failure transitions and incident response
- RIGHTS_DENIED/EXPIRED/REVOKED: mark rights hold, quarantine, stop media rendering and all future scheduled publishing actions; prompt owner for takedown assessment of existing uploads.
- MEDIA_QA_FAILED: new SHA required after remediation; cannot reuse signoff.
- OAUTH_INVALID_GRANT: no retries against same rejected refresh token; request owner-mediated reauthorization, NO fallback to Branch 1/2 token.
- AMBIGUOUS_UPLOAD_5XX / timeout: do not blind retry. Read remote inventory using upload ledger and metadata, reconcile actual video first.
- DUPLICATE_SOURCE_OR_SCHEDULE: block, require owner decision. Content hash + source timestamp uniqueness alone are insufficient due to intentional legitimate alternate cuts.
- CONTENT_ID_CLAIM: hold schedule/release; investigate rights. Passing private checks does not guarantee future claim-free distribution.
- PUBLISH_AT_IN_PAST: fatal, never convert to immediate public.
- REVOKED_PERMISSION_AFTER_SCHEDULE: quarantine and remove scheduling only after reconciling private/public status with an owner-approved procedure.

## Data and immutability
Job ID = immutable UUID or collision-resistant slug. Source tuple = creator channel ID + video ID + in/out timestamps. Version = render bytes hash + metadata hash + rights grant fingerprint. State mutations append a transition event, never overwrite old evidence. Cross-run concurrency fence should have atomic compare-and-swap and a renewable lease, not GitHub Actions concurrency alone.

No agent can issue a human signoff or license. Model-generated confidence is never proof of rights, channel control, engagement or legal compliance.

## Proposed GitHub triggers
- **IMPLEMENTED A1:** manual `branch3-clivox-a1-discovery.yml` for safe synthetic tests and, once configured with a distinct restricted YouTube public-metadata API key, one public video-ID lookup or one bounded query. No cron has been installed. See `a1-discovery-implementation.md`.
- **Future possibility**: opt-in scheduled metadata discovery only after quota, abuse and cost limits are reviewed; not currently enabled.
- GitHub Issue/PR based rights review; only authorized human marks RightsGrant verified.
- workflow_dispatch editorial planning with source candidate ID (no copyrighted media).
- Manual secure/private media review upon approved rights.
- workflow_dispatch preflight/publish only **after separate implementation, environment protection and explicit owner release authorization**. This design PR does not create upload-capable Actions.

## Source clip example
Current candidate: 2 Bears 1 Cave Ep 347, source i6pmnpaOaZQ. The existing branch3/pilot_ymh_ep347.json is **SOURCE RESEARCH ONLY** with all rights false. It is not an editable asset or publishing candidate.

