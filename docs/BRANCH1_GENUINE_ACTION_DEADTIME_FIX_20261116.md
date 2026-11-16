# Branch 1 — fix genuine application chapter dead time (2026-11-16)

## Findings from actual media

- Earlier 10-second screen capture plus long voiceover: Calc 96.2% nearly unchanged source pixels, Chrome 90.6%. Both rejected.
- Longer authentic 48-second recording, five nine-second chapters: Calc 45.3%, Chrome 50.9%, still blocked.
- Full original action-window retiming in PR #249: Chrome improved to 41.5% and passed its *motion screen*, while Calc remained at 45.3%, both with visible opening activity.
- Added factual live worksheet captions in PR #250: Calc remained 45.3%, while Chrome 39.6%. The root issue wasn't captions.
- Source inspection identified the actual defect: each nine-second capture chapter performs its **six genuine software actions at seconds 0.1, 1.1, 2.1, 3.1, 4.1 and 5.1**, followed by nearly four seconds of idle GUI; the narrator subsequently compresses this whole window. This builds unnecessary static screen time into the original recording.

## Corrective behavior

Preserve all **six genuine app actions**, actual app code, source hashes, protected profile, no permission mutation and the five nine-second chapter structure. Spread them evenly across the genuine action window at **0.1, 1.6, 3.1, 4.6, 6.1, 7.6 seconds**. Now actual input, selection, calculation and settings navigation occupy the entire chapter without artificial animations or frozen filler.

This is a real source-capture timing fix, not a change in the 45% independent motion audit threshold. Unit tests assert 30 genuine actions, precise timing per chapter, first/last bounds, and fail closed without the live capture_started marker.

## Review and publishing boundary

Merge only after CI. Then render both original app stories on an isolated GitHub runner with real LibreOffice Calc/Chrome and pinned Kokoro voice. Run independent existing postrender source-pixel audit on **exact emitted MP4s**; do not silently reduce any threshold if Calc still fails. A motion screen pass is **not** proof of good hooks or human satisfaction: visual review of the exact finished video remains necessary, particularly because repeated Chrome settings-page navigation could be confusing.

No YouTube upload, no new scheduled video, no purchase, no customer data, no laptop disk. Earlier scheduled videos remain unchanged.
