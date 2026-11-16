# FlowMinute Lab — November 17, 2026 scheduling checkpoint

**Prepared on November 16, 2026, Asia/Kolkata. NO YouTube upload or schedule executed.** The creator asked to schedule the next day. The exact channel is `UCCcL9Q_jqVq6LJmnYUSAFZA`.

## Existing original November 17 program (planning records, not live YouTube confirmations)

| November 17 IST | Exact UTC target | Existing release candidate | Approval and live schedule |
|---|---|---|---|
| 11:00 Short | 2026-11-17T05:30:00Z | `fm_20261117_filter_view_short_en`, Google Sheets Filter Views | Original source render exists, owner exact release unsigned; **live schedule UNKNOWN** |
| 16:00 long | 2026-11-17T10:30:00Z | `fm_20261117_sheets_collaboration_long_en`, Google Sheets Team Collaboration | Original source render exists, owner exact release unsigned; **live schedule UNKNOWN** |
| 20:30 Short | 2026-11-17T15:00:00Z | `fm_20261117_protected_range_short_en`, Google Sheets Protected Ranges | Original source render exists, owner exact release unsigned; **live schedule UNKNOWN** |

These three belong to original November 17 source run [#42976462946](https://github.com/Tirthanand17/taskless-lab/actions/runs/42976462946). A successful render does NOT verify owner release or actual scheduling; the older video files may be beyond their short artifact retention window. Never guess they are unpublished, and never upload a duplicate.

## Newly approved original 3:35 Python tutorial — do not collide with the legacy long

The owner approved **the exact original real Python CSV long-form video** shown in prior conversation; not both Shorts or the existing Google Sheets trilogy. Video SHA-256 `1a20dedf886f3228445ed718e1f2e93a7e38cd74abf8aeb211540e32b6683f42`, subtitles SHA-256 `b4b317c8d1d9883294e9ebb32b23c6790a4cdb891be9bbd560fd459baa132a0e`, duration **214.833s**, proposed title **“Why Your CSV Total Is Wrong: 3 Data-Cleaning Bugs in Python”**. Original MP4/SRT/real-frame cover in [non-public private review artifact #14240127005](https://github.com/Tirthanand17/taskless-lab/actions/runs/43898583072/artifacts/14240127005), retained through **December 16, 2026**. See [`content/recovery_pilot/real_python_long_release_review_candidate.json`](../content/recovery_pilot/real_python_long_release_review_candidate.json).

**No publishAt set for this new approved long.** The existing Nov17 16:00 target already has a planned *different* long video, and the actual YouTube owner inventory is unavailable. Do not implicitly replace it, add a second competing upload or schedule at a guessed time. The single-audience growth test prioritizes the approved Python tutorial, but cannot justify a duplicate or a slot collision.

## Actual live scheduling prerequisites — current verified failures

1. **GitHub protected owner audit [#43907587948](https://github.com/Tirthanand17/taskless-lab/actions/runs/43907587948)** was dispatched on November 16 and finished **failure: `B4F6_REDACTED_FAILURE_CLASS=OAUTH_REFRESH_FAILED`**. That means the existing owner YouTube Data API `YOUTUBE_TOKEN_JSON` in GitHub's `youtube-production` environment cannot refresh. No authenticated `channels.list`, `videos.list`, duplicate inventory, or `publishAt` readback was obtained. This is a hard stop before any publisher.
2. Connected vidIQ account reports YouTube owner channel `@flowminutelab` with `canPublish=true`, but its connected-channel `vidIQ_user_videos` inventory costs 5 credits while **available credits are 0**, next refill reported **December 2, 2026**. The **free** connected vidIQ social-post list for Nov17–18 returned zero scheduled vidIQ posts. It is **not** a complete YouTube Studio inventory, and previous `vidIQ_social_post_publish` results with `scheduledFor=null` were not reliable scheduling receipts.
3. Connected Metricool account has no YouTube social connection; cannot presently schedule or certify uploads with it.
4. Each exact upload still needs its distinct final media/voice/caption/facts/rights approvals, protected release signing process and truthful exact publication metadata. One chat statement approving **the video** is not a forged Ed25519 release signature for multiple assets.
5. The existing GitHub publisher [`publish-artifact-youtube.yml`](../.github/workflows/publish-artifact-youtube.yml) is private-first and requires a future UTC time, exact MP4/SRT/cover, validated `YOUTUBE_TOKEN_JSON`, and signed approval. Never lower these gates.

## Next executable steps

- Owner securely reauthorizes the intended Google/YouTube account and refreshes the GitHub environment `YOUTUBE_TOKEN_JSON`; **do not paste any credentials in a chat, issue, commit or PR**.
- Re-run [owner-channel **read-only** workflow](../.github/workflows/flowminute-owner-readonly-channel-audit-b4f6.yml) to prove the actual intended YouTube channel and currently uploaded/scheduled video inventory. The existing read-only November 5–11 inventory doesn't cover all Nov17 slots; extend the coverage with proper real authenticated data before final dispatch.
- Reconcile the three legacy Nov17 episode titles/IDs and the approved Python long against live owner inventory. After deciding which long-format release to prioritize and obtaining any remaining exact-file signoff, select an **available future timestamp at least 15 minutes ahead** of actual dispatch. A past time cannot be rescheduled retroactively.
- Call the protected publisher exactly once with independently authorized and signed exact media; verify YouTube's returned real video ID, private visibility, precise `status.publishAt`, actual processing and captions. If any result is ambiguous, stop and reconcile rather than upload again.
- Only then call the release **scheduled**. After publication, observe 24h/72h/168h real Studio retention and Suggested/Browse sources via existing read-only growth pipeline; no claim of restored views without it.

**Outcome this turn: zero YouTube uploads, zero confirmed new Nov17 schedules, zero existing videos altered.** This is an operations hold, not a fake schedule.
