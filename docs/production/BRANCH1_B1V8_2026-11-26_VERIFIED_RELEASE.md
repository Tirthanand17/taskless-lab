# B1v8 — 26 November 2026 release checkpoint

Owner authorized direct scheduling without owner preview. No claim of human playback or perfect subjective quality.

| Video | YouTube ID | IST | SHA-256 |
|---|---|---|---|
| Why ZIP Barely Shrinks Your Photos #Shorts | LhaGtwTb-N0 | 16:00 | 4c554aefbc5385e89a07b2cf3ef311cad7f71f90439fbabe6444882ac54bba9b |
| JPG vs PNG: Why Renaming a File Does Not Convert It (Real Test) | un4gPSoxrBs | 19:00 | b86ebac2c07cb679008e694a9311b79a76f4da023bb39f8c6ba9250cadd63c27 |
| Renaming JPG to PNG Does NOT Convert It #Shorts | Tip4smWJRnA | 21:00 | 89e9a12c0f5f67055a89a5ccbf2f2659acea3e2cad9bcc3a752b698663d539f4 |

All 3 final files passed full decode, exact asset hash checks, timed caption checks, speech audit, and 35 sampled decoded-frame inspections. All 3 YouTube API schedule readbacks passed, with English captions serving, custom thumbnails confirmed, correct language/title/description/hashtags/tags, and no duplicates. Not yet confirmed public; no manual Studio UI inspection claimed.

Voice selection: prior Nov24 USB-C Short had 267 views at today's owner API audit; reused its licensed Kokoro af_heart voice, not a claim that voice alone caused views. New original synthetic foley cues follow compression/format changes. Real sample photo from Pexels (https://www.pexels.com/photo/man-showing-usb-stick-on-hand-4792750/), executed local ZIP and Pillow tests; measured text compression 99.5%, JPEG compression 5.9%; rename byte hash unchanged; true PNG export changed format and decoded pixels matched. Results are sample-specific. Official references: https://support.microsoft.com/en-us/windows/experience/storage-filemanagement/common-file-name-extensions-in-windows ; https://support.microsoft.com/en-us/windows/experience/storage-filemanagement/zip-and-unzip-files.

Final production source: autopilot/b1v8/produce_b1v8.py (commit 3d677861614fb8ff8a14a8efe15d2042809c7f1d). Multiple review passes corrected ambiguous speech, lower-screen takeaways, and the final export instructions. Visuals are actual photo and explanatory graphics, not live camera footage; sound is synthesized, not human-recorded. Actual Shorts UI occlusion and human listening are not independently verified. Local evidence at nov26-b1v8/FINAL_TECHNICAL_AUDIT.json, AGENT_VISUAL_REVIEW.json, NOV26_RELEASE_RECEIPTS.json. Performance registry now contains 9 videos across B1v6–B1v8; audience outcomes still require measurement. No additional paid tools.