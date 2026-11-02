# FlowMinute Lab — Google Flow Takeout archive bridge

**New verified route, according to official Google help (October 2026):** Google Takeout supports Flow media backups containing `media/<media_id>.mp4` plus `media/<media_id>_metadata.json`, with project/character/scene JSON. Takeout may deliver the ZIP directly to the user's Google Drive without a computer download. Source: https://support.google.com/flow/answer/17571126

## What is implemented

`autopilot/flow_takeout_bridge.py` does a read-only ZIP safety scan and checks specifically mapped MP4/metadata pairs. It checks sizes, ZIP path traversal, symlinks, encrypted files, duplicate entries, ambiguous media IDs, MP4 header, SHA-256 and paired metadata. It does not print private prompts or unrelated Takeout data.

Use an explicit JSON mapping, such as:

```json
[{"episode_id":"fm_20261024_short_en","clip_id":"01","media_id":"COPY_FROM_ACTUAL_TAKEOUT_FILENAME"}]
```

The media ID must be confirmed from the real provider archive. Do NOT assign a random guessed ID. An archive ZIP must already exist in an authorized ephemeral/cloud runtime; Google Drive connection access does not automatically supply raw ZIP bytes to this GitHub runner.

Read-only scan:

```bash
python scripts/flow_takeout_import.py --archive /authorized/flow-takeout.zip --mapping /authorized/clip_mapping.json
```

Optionally import only the explicitly mapped MP4s into an EXISTING authorized directory; no overwrites or unrelated data extraction:

```bash
python scripts/flow_takeout_import.py --archive /authorized/flow-takeout.zip --mapping /authorized/clip_mapping.json --import-to /authorized/flow_clips
```

The importer stages files, executes the existing FFmpeg clip intake, checks their hashes against the ZIP scan, and atomically writes non-overwriting files. It rolls back staged outputs if any media fails technical checks. An imported MP4 remains **unapproved**: no AI video can be published until source ownership, content accuracy, rights, natural voices/lip sync, visuals and subtitles are independently reviewed.

## How to get the first Flow archive (one provider-side step)

Sign in to https://takeout.google.com with the SAME Google account that owns the Flow project. Choose **Deselect all → Flow → Next step → Add to Drive**, select ZIP and Create export. The archive arrives in Google Drive; Takeout can take time to prepare it. This is a **backup/import** method, not an on-demand or officially documented always-on Flow API, and it counts against Google Drive storage.

The connected Google Drive search on 2026-10-23 found **no Flow Takeout archive**. No real Flow video has been generated, downloaded, imported, approved or scheduled by this implementation. ₹0 additional spending, no Nirala, and no YouTube publish action.

Official reference: https://support.google.com/flow/answer/17571126
