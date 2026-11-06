# ADR-0063 — B4e6c fix science-v7 encoded-media evidence mismatch

**Date:** 2026-11-06 IST. **Scope:** safe CI/media proof only. No permission to publish, spend, deploy AWS or change Branch 1 videos.

## Observed physical failure

Trusted GitHub [main run 42186951098](https://github.com/Tirthanand17/taskless-lab/actions/runs/42186951098) downloaded checksum-pinned open voice assets and entered the real Kokoro/FFmpeg render. After the first episode the collector stopped at a media-report gate. The renderer's boolean field b4e4_source_exact_nonoverlapping_editorial_grid included the older cinematic_v3 and floating_v6 but omitted the new science_v7, even though its frame path uses the exact non-overlapping source title/ASS grid. This is a **false-negative metadata mapping**, not evidence of completed publishable videos.

## Source fix and falsification

- Include science_v7 in the renderer's exact nonoverlapping editorial grid status; preserve previous modes and native visual guard checks.
- Factor media-report validation into require_science_v7_media_report, requiring real codec/voice/caption/scene evidence and exact False for human review, upload, **schedule**, and release. Reject missing and int-for-boolean forged flags without revealing source content or credentials.
- Add negative tests for each required flag, altered status and wrong render mode. Do not bypass technical decoded-video QA, independent subtitle/voice checks or source hash verification.
- Run PR source/pixel tests and repo-wide CI. Only upon a trusted main push should GitHub create three full unapproved H264/AAC demos and store their bounded seven-day public review artifact. Verify run result, actual artifact and hashes; do not claim success based on source unit tests alone.

## Not accomplished

Not fresh daily research, human factual and copyright signoffs, full listen/watch, production cloud or account approval, live OAuth or YouTube publishing. Branch 1 schedule untouched. End-to-end approximate production capability remains **40/100**, independently verified Branch 2 unattended YouTube releases **0/21**.
