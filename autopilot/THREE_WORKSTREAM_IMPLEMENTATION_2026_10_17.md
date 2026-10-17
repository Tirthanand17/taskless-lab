# FlowMinute Lab — implementation checkpoint, 17 October 2026

## Existing architecture
Reviewed taskless-lab public `autopilot/core.py`, `scout.py`, `growth.py` and the private control repository. Existing three fixed slots and receipt-based ledger remain intact. Scout currently produces unverified RSS leads. Growth scoring is observational and not connected to real-time Analytics. Public cloud render benchmarks are historical and do not prove a 90-video monthly production capacity. The private Cloudflare D1 OAuth grant was independently verified previously; private publishing is disabled.

## New modules
- `autopilot/calendar.py`: Asia/Kolkata draft calendar, 2 Shorts and 1 long daily, up to 6 Shorts and 3 long videos through a one-day override. Weekend, temporary, pause, extra Short, AI-tutorial-only and reset commands are parsed exactly. Conflicting reservations and overlapping overrides stop without modifying prior state. Shorts alternate energetic and explanatory narrator profiles as *planning metadata*.
- `autopilot/preview_calendar.py`: produces JSON previews only. A 30-day default generates 60 Shorts + 30 long draft slots; no uploads, no job scheduling and no backend update.
- `autopilot/editorial_gate.py`: draft-only QA for independently checked sources, original reproducible demonstrations, transaction truthfulness, simulated-interface labels, licensing, captions and privacy.
- `autopilot/launch_gate.py`: rejects unverified RSS headlines; requires independently reviewed official and nonofficial evidence before recommending a technology launch for editorial review.

## Verification
Executed 40/40 new Python offline unit tests in an isolated container. No network or OAuth tokens were used. Existing legacy repository-wide tests were not rerun in this environment.

Commands from the public repository root:
`python -m unittest autopilot.test_calendar autopilot.test_editorial_gate autopilot.test_launch_gate autopilot.test_preview_calendar`
`python -m autopilot.preview_calendar --date 2026-10-17 --days 30`

## Not yet complete
The new calendar is not wired into the existing `core.py` SQLite receipt ledger or a persistent authorized cloud command interface. No live YouTube scheduling has changed. Real publishing, current quota checks, Oct 18-19 video verification, analytics retrieval, production-quality 3D video rendering, licensed humanlike narration, private cloud media storage and full QA require further implementation and verified no-cost resources. Google OAuth External/Testing durability remains unresolved. Workstreams preserve ₹0/month, no laptop access, no new services, no credentials exposed and upload/scheduling OFF.

Do not equate a proposed slot or a verified story with a published video.
