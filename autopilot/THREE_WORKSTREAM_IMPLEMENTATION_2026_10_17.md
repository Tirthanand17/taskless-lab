# FlowMinute Lab — implementation checkpoint, 17 October 2026

## Existing architecture
Reviewed taskless-lab public `autopilot/core.py`, `scout.py`, `growth.py` and the private control repository. Existing three fixed slots and receipt-based ledger remain intact. Scout currently produces unverified RSS leads. Growth scoring is observational and not connected to real-time Analytics. Public cloud render benchmarks are historical and do not prove a 90-video monthly production capacity. The private Cloudflare D1 OAuth grant was independently verified previously; private publishing is disabled.

## New modules
- `autopilot/calendar.py`: Asia/Kolkata draft calendar, 2 Shorts and 1 long daily, up to 6 Shorts and 3 long videos through a one-day override. Weekend, temporary, pause, extra Short, AI-tutorial-only and reset commands are parsed exactly. Conflicting reservations and overlapping overrides stop without modifying prior state. Shorts alternate energetic and explanatory narrator profiles as *planning metadata*.
- `autopilot/preview_calendar.py`: produces JSON previews only. A 30-day default generates 60 Shorts + 30 long draft slots; no uploads, no job scheduling and no backend update.
- `autopilot/editorial_gate.py`: draft-only QA for independently checked sources, original reproducible demonstrations, transaction truthfulness, simulated-interface labels, licensing, captions and privacy.
- `autopilot/launch_gate.py`: rejects unverified RSS headlines; requires independently reviewed official and nonofficial evidence before recommending a technology launch for editorial review.

## Verification
Executed **78/78 local isolated Python tests**, including the prior 49 tests, 21 additional adaptive calendar/ledger checks, and 8 FFmpeg-based media-file tests. The local integration tests use a mirror of the current ledger interfaces because the isolated container cannot clone GitHub. Source and regression tests are committed in the public repo; **the complete repository-wide CI run has not been verified**. No Google API, OAuth tokens, video uploads or paid providers were used.

Commands from the public repository root:
`python -m unittest discover -s autopilot -p 'test_*.py' -v`
`python -m autopilot.preview_calendar --date 2026-10-17 --days 30`

## 4. Provenance-aware growth metrics — `autopilot/engagement_metrics.py`

Adds source-labelled `official_api`, `studio_export`, or `manual_observation` records. Computes likes, comments, shares and new subscribers per 1,000 *engaged* views only when the denominator exists and is positive. Missing fields remain unavailable, not fabricated. Age-matched baseline comparisons require six authenticated videos with adequate engaged views; manual observations do not qualify for conclusions. Nine new offline tests passed; **not connected to live YouTube Analytics yet**.

## 5. Adaptive SQLite release-ledger bridge

Added `autopilot/calendar_ledger.py` and a backward-compatible `ReleaseLedger.reserve_prepared_batch` in `autopilot/core.py`. Media is reserved **only after** complete SHA-256, MediaQA, independent topic validation and a recent (10-minute maximum), correctly scoped channel snapshot. The exact existing UTC time is checked across *all* legacy and adaptive formats, not merely each format's unique index. One batch commits atomically or rolls back, is idempotent by episode ID, and is **PLANNED only**. The original `reserve` path is now protected against the reverse collision. YouTube's ISO timestamps ending in `Z` are normalized before comparing with `+00:00`. The snapshot is a caller-supplied claim until bound to the private authenticated YouTube API adapter—**not independent proof of a remote YouTube release**. The bridge has **not** been deployed or attached to production data.

## 6. Actual FFmpeg render-file inspection

Added `autopilot/render_inspection.py`, which uses FFprobe and FFmpeg full decoding to verify actual file dimensions, duration, frame rate, audio stream, media size, SHA-256, black segments and significant audio silence. Eight tests created synthetic locally generated MP4 test files and validated expected results, including malformed/no-audio/black cases. **Technical PASS never implies publishing clearance.** No real human voice, subtitle speech alignment, copyright audit, truthful tutorial source/visual QA, or completed production media is certified by those sample tests.

## Production architecture boundary

The public `taskless-lab` SQL ledger is a local research/testing component; the separate private `flowminute-control-private/control/ledger.py` requires a verified durable volume and is **not yet integrated with these new adaptive slots**. Cloudflare D1 is currently used for metadata and encrypted OAuth, not yet a verified video-production reservation service. Do not create another production state database without an authoritative reconciliation and migration plan.

## Not yet complete
The new calendar now has a local atomic adapter for `core.py` SQLite test reservations, but is **not** wired to the private persistent production ledger or Cloudflare backend. No live YouTube scheduling has changed. Real publishing, current quota checks, Oct 18-19 video verification, analytics retrieval, production-quality 3D video rendering, licensed humanlike narration, private cloud media storage and full QA require further implementation and verified no-cost resources. Google OAuth External/Testing durability remains unresolved. Workstreams preserve ₹0/month, no laptop access, no new services, no credentials exposed and upload/scheduling OFF.

Do not equate a proposed slot or a verified story with a published video.
