# FlowMinute Lab — October 13, 2026 publication readiness

**Checked on 2026-10-12, India time. Status: rendered, NOT approved, NOT uploaded, NOT scheduled.**

Target YouTube channel: `UCCcL9Q_jqVq6LJmnYUSAFZA` (authenticated publishing token doctor PASS).

| Episode | Planned IST | Video duration | Dimensions | SHA-256 | Status |
| --- | --- | --- | --- | --- | --- |
| pilot_017 | Oct 13 11:00 | 37.0 s | 1080x1920 | `36655fae7a319d7c969c179025a99d3a29a5df22e86329aa0d52a91fd1da3e86` | MP4 technical decode PASS; quality approval PENDING |
| long_008 | Oct 13 16:00 | 170.0 s | 1920x1080 | `d097b3aa91d9972855f3cdfb2a6dc5731c4f2b7dea724e9d7231e78faed89448` | MP4 technical decode PASS; quality approval PENDING |
| pilot_018 | Oct 13 20:30 | 31.5 s | 1080x1920 | `da41ba1422bed3d59a4d6ab89f18f8b0aa4788ed68c84a23205134eb0e555739` | MP4 technical decode PASS; quality approval PENDING |

All files: `C:\Users\Dell\Desktop\youtube con\oct13-production\`.

Long thumbnail: `long_008_thumbnail.jpg` (164,218 bytes, within the publisher's 2 MB gate).
Shorts use portrait hook frames, not separately verified YouTube custom thumbnail.
Local contact images: `pilot_017_contact.jpg`, `pilot_018_contact.jpg`, `long_008_contact.jpg`.
Rendered videos have H.264 / AAC, and complete ffmpeg video+audio decode returned exit code 0.
Voice energy was examined as a *technical check only*: mean volumes near -20.3 / -19.6 / -20.4 dB, max peaks -4.7 dB (no digital clipping). This does not prove human-sounding intonation.
Narration recordings and synthesis QA JSON are at `oct13-production\audio\`.
Draft-only, **unreviewed approximate captions** are at `oct13-production\captions\`; do not import them as accurately timed until reviewed.

Release manifests have been staged in `oct13-production\manifests\`, and each deliberately has `qa_approved=false`, `captions_reviewed=false`. These manifests cannot be uploaded using the approved publisher's QA gate until actual review has occurred.
**No new YouTube video IDs or scheduling receipts exist. No upload attempt was made.**

## Gates remaining

1. Listen to the complete final MP3 or rendered MP4 on headphones and a phone: pronunciation, naturalness, cutoffs, joins and levels. Record owner/human approval.
2. Watch each full rendered MP4 to verify scene-to-speech alignment, typography, clip timing, visual variety, media rights and factual labeling. Contact sheets alone are insufficient. If any mismatch occurs, revise and rerender before scheduling.
3. Align each caption cue to the exact spoken words/timing; mark caption review only after successful human check.
4. Verify any realistic background photos/footage have suitable publication rights and YouTube altered/synthetic media disclosure.
5. Confirm title, metadata, thumbnail and approved files, then use the official publisher's **private upload → assets → schedule → independent verify** steps. Record exact channel, video IDs and schedule receipts.
6. Never claim scheduled until YouTube responds and independent read-only verification confirms each future `publishAt`. No duplicate uploads, no automatic retry after ambiguous responses.

**Never set qa_approved=true just to get past the publisher gate.** If a user deliberately changes the editorial acceptance criteria, document that decision transparently rather than misrepresenting a completed listening review.
