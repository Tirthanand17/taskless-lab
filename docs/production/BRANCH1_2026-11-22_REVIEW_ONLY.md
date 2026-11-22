# Branch 1 — 2026-11-22 IST editorial review only
**Requested:** 2 original Shorts + 1 long video for FlowMinute Lab (`UCCcL9Q_jqVq6LJmnYUSAFZA`) on 2026-11-22 IST.
**Status:** Prepared offline review package (not committed to GitHub), **no YouTube upload, no approved masters, no API schedule, no Studio verification.**
**Do not publish from this note.** Branch 1 exact-file release policy still applies.

## Planned episodes (not confirmed on YouTube)
| Slot IST | Type | Subject | Draft length |
|---|---|---|---:|
| 11:00 | Short | CSV IDs: `00123` incorrectly treated as numeric; protect with `dtype={"order_id":"string"}` | 33 s |
| 16:00 | Long | Clean a deliberately messy generated sales CSV: preserve IDs, normalize nonbreaking spaces, remove only exact duplicates, flag conflicting orders/missing amount | 126 s |
| 20:30 | Short | Excel `TRIM` not removing NBSP/CHAR(160); `TRIM(SUBSTITUTE(A2,CHAR(160)," "))` | 34 s |

## Checked factual basis
- Original `orders_sample.csv` and `verified_demo.py` ran in an isolated environment: first ID `'00123'`, normalized first name `'Maya'`, **1** exact duplicate removed, **2** conflicting rows for review, **1** missing amount, **5** ready rows, sum **₹1,218**.
- Microsoft TRIM documentation: https://support.microsoft.com/en-us/excel/functions/trim-function (nonbreaking space not removed by TRIM alone).
- pandas documentation: https://pandas.pydata.org/docs/user_guide/text.html.
- Official scheduling: https://developers.google.com/youtube/data/reference/rest/v3/videos. Past-dated `publishAt` may immediately publish; never schedule a past slot.
- Shorts custom thumbnails in desktop Studio: https://support.google.com/youtubecreatorstudio/answer/72431.

## Physically created — review package only
Two silent vertical MP4 motion previews (33s and 34s), one silent landscape MP4 preview (126s), three PNG thumbnail designs, narration scripts, YouTube titles/descriptions/tags, generated sample CSV, executed Python demo, image contact sheets, SHA256 manifest, and explicit **NO UPLOAD** README. All previews are 720p-width review media with 24fps encoded outputs derived from 12fps frame generation and **no audio**; not upload masters. They contain visually reconstructed, clearly labeled output rather than actual screen capture.

## Hard failures and next requirements
- Natural narration not synthesized or listened through; audio track missing.
- External accurate SRT not created; captions need final audio synchronization.
- Authentic high-quality screen capture and stronger motion/retention polish not completed; visual review showed simple mostly static cards, so quality gate **FAIL**.
- No owner final-media approval and per-file signed release reservation.
- No successful owner-authenticated YouTube schedule inventory/remote readback or manual Studio inspection.
- Connected vidIQ channel identity independently confirmed, but its paid-credit operations returned **insufficient credits**, refreshing Dec 2. This cannot substitute for direct API authorization.
- No API upload attempted, no video IDs, no scheduled status.

**Verdict:** NOT READY. Do not use the silent preview files as release assets. Avoid silent publishAt retries. Complete original motion, full narrated media, listening QA, exact final SHA approval, owner OAuth, duplicate check, then private upload and remote readback before any schedule claim.
