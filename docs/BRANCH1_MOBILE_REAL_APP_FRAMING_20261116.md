# Branch 1 — Mobile-readable real-application video framing

## Why this is necessary

The actual proof-first narrated videos from #43815333380 were technically valid, but visual evidence frames from the independent pixel audit #43815824444 exposed **poor mobile legibility**:

- LibreOffice Calc: important genuine cell values/formulas occupied the top few rows of a near-empty vertically stretched spreadsheet.
- Chrome: genuine settings text was relatively small and the unimportant automated-test banner appeared at the top of the recording.
- Static share remained close to the internal 45% threshold (Calc 47.2%; Chrome 49.1% in this run), despite a much better real-action recording. Passing a pixel-motion test alone would not prove the tutorial is readable or enjoyable.

## Genuine-pixel framing implemented

The new narrated Shorts editor uses two layouts, drawing **only from the originally captured and hash-bound real software MP4**:

1. **Calc** creates two separate timestamp-synchronized source views in one portrait video. The main panel is the real recorded data range from a 720x460 crop, shown at 1080x690. A second enlarged crop of the actual formula/result cells (420x230) is shown at 1080x591. Both are original real Calc pixels. These are *not generated representations, HTML mocks or reenacted screenshots*. A dark navy 1080x1920 background provides clear space for source-timed narration captions.
2. **Chrome** uses a centered 600x1067 crop of the original genuine settings recording, removing irrelevant browser header margins and increasing mobile text size. The actual permission settings UI is unmodified and remains the only video evidence.

Five narrative chapters retain the original source footage, pinned Kokoro voice, timed SRT and burned-in ASS captions, H.264/AAC validation, post-encoded loudness checks, and exact SHA receipts. No new copyright-protected source content or paid tools.

## Crucial quality boundaries

- The phone-readable layout is an **editorial hypothesis**, not evidence of higher YouTube views. Do not auto-approve it just because the crop looks sharper.
- Visually watch all resultant videos at mobile scale. Check data labels, FALSE/TRUE readings, text overflow, captions not obstructing the actual steps, Chrome permissions authenticity and voice-to-action timing.
- Re-run the full actual GPU/CPU-independent GitHub render and then the existing *independent real-pixel* gate on precisely those MP4s. Do not relax frozen-frame thresholds.
- Future original videos should vary their design according to subject; a two-panel Calc layout is appropriate for a spreadsheet, but shouldn't be blindly reused for gaming or interviews.
- Both pilot videos remain **review only**, without any owner rights/factual/release signing and without YouTube upload or scheduling.

Recorded source and final artifacts remain in GitHub Actions. Any ephemeral PC image inspection is deleted after viewing. New YouTube posts: 0. Paid tools purchased: 0.
