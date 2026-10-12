# FlowMinute October 13 publishing status

Last checked: 2026-10-12 22:24 IST.

**Two videos are confirmed scheduled** for October 13. Exact read-only YouTube Data API verification of the intended channel and publishAt timestamp passed.

| Episode | Existing YouTube ID | Release (IST) | Verified status |
| --- | --- | --- | --- |
| pilot_017 | mxB4fNx0Ua4 | 11:00 | scheduled, private until release |
| long_008 | -_6iX5o3EfY | 16:00 | private, **still processing, NOT scheduled** |
| pilot_018 | -8B1X1n5XIU | 20:30 | scheduled, private until release |

Long 008: Previous resumable upload was interrupted by SSLEOFError after a 49.9% progress notification. YouTube's authenticated uploads playlist revealed the **same** original video ID. API `videos.list` independently confirmed same channel and title, private visibility, `uploadStatus=uploaded`, `processingStatus=processing`, zero unverified duration (`P0D`), and `fileDetails.fileSize=16826930`, exactly matching local MP4 bytes. The matching size is encouraging but **does not establish completed processing or playback**.

Private upload ledger remains fail-closed at `uploading_unresolved`. Never delete its reservation or blindly re-upload. No long video schedule receipt is permitted until YouTube fully processes this exact original video. An hourly deadline-bounded follow-up is active to check and complete the schedule if safe. It must preserve the 16:00 IST target, avoid all duplicate uploads, and report a deadline blocker if processing never finishes.

Long video thumbnail (approved creative): `C:\Users\Dell\Desktop\youtube con\oct13-production\long_008_thumbnail.jpg`; asset not yet uploaded.
The draft auto-timed subtitle files were **not** uploaded because their speech alignment is not reviewed.

YouTube publishing authority was explicitly approved by the owner in chat on 2026-10-12.