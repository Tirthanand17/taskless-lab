# FlowMinute Lab — Offline Google Flow clip intake

Development checkpoint: a real MP4 can now be inspected as an **editorial candidate**. This is not an automated Flow API, proof of ownership or YouTube uploader.

After downloading a clip from the Google Flow UI, run from the repository root in an authorized machine/container that already has Python, FFmpeg and FFprobe:

```bash
python scripts/flow_clip_intake.py --file /existing/directory/real_flow_clip.mp4 --episode fm_20261024_short_en --clip 01 --mode pilot
```

Optionally append `--report /existing/directory/report.json` to save a redacted JSON report. The input MP4 is **read-only**; a report is only written when requested. No credential, user-private path, or video file is written to GitHub.

Validation checks the planned episode/clip, full FFmpeg decode, SHA-256, orientation, duration (8–10.5 seconds), stream count, format, codec and frame rate. Missing source audio is flagged for narration. Non-H.264 source codecs require the final export pipeline. The strict YouTube export still must pass H.264/AAC, 1080p, subtitles and final QA.

**An intake pass is not permission to publish.** The tool does not independently verify that the file originated from Flow; source is a declaration, not a signature. It cannot judge realism, hands, facial continuity, speech, commercial rights, truthfulness or learner comprehension. All publication fields remain false.

Status of October 24 production: no real Google Flow file has been generated or ingested. The older low-poly 960×540 landscape preview remains rejected for the first 9:16 cinematic pilot. The three episodes are not scheduled.

Budget remains ₹0 new expenditure. No Nirala access and no Flow credit use.