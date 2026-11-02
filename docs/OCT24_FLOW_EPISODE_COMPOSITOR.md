# FlowMinute: real-media composition, not a low-poly substitute

Status: draft GitHub feature branch. A working FFmpeg compositor is now available to JOIN real cinematic Flow clips and existing narrated instructional footage. It DOES NOT GENERATE any cinematic shot or auto-upload to YouTube.

## Contract

The input JSON names one approved episode ID from the October 24 storyboard set and an ordered sequence of real MP4s. Each segment supplies a named ID, an existing MP4 path, its actual SHA-256 hash, a source start in milliseconds and a used duration in milliseconds.

Example for an **incomplete test draft only** (the example below has placeholder hashes and MUST be replaced by a real file before use):

```json
{
  "schema_version": 1,
  "episode_id": "fm_20261024_short_en",
  "segments": [
    {
      "id": "opening_cinematic",
      "path": "/authorized/media/flow_take_01.mp4",
      "sha256": "REPLACE_WITH_ACTUAL_SHA256",
      "source_start_ms": 0,
      "duration_ms": 10000
    }
  ]
}
```

Run `python scripts/compose_flow_episode.py --manifest /authorized/episode.json --output /authorized/draft.mp4`. A normal invocation requires the ENTIRE storyboard duration: 48s English Short, 48s Hindi Short, or 300s Hindi long. **Missing segments block compilation**, rather than quietly adding silence, placeholder art or unreviewed stock scenes. The optional `--test-only` creates a visibly incomplete partial video and marks it `PARTIAL_TEST_DRAFT_ONLY`.

Every input needs one video and one audio stream. Files must be actual MP4s with matching content hashes and the correct aspect ratio. FFmpeg trims, normalizes to 720x1280 vertical or 1280x720 landscape, creates H.264/AAC intermediate clips, concatenates them and checks the final decode. This is an **editorial draft**, not final full-HD delivery. Input audio is present but does not prove natural speech or licensing.

## Integration and safety

- A real Flow source should first pass `scripts/flow_clip_intake.py` for its selected episode/scene, then independently pass face, hands, voice, disclosure, rights, fact and source review.
- The composer does not trust self-attested review fields in its input manifest: it **always** reports natural-voice, rights, factual and artistic QA as unverified, with publishing authorization false.
- The composed result is an original media draft stored only in the specified allowed output directory; no video or private file paths are committed to GitHub.
- This compositor is intentionally not wired to any YouTube uploader or scheduled release job.
- It does not access Nirala or external video services; no payment, Google Flow credits or API keys.
- 720p is intentionally a computationally economical preview export, not a claim of cinematic quality. Source clips must eventually be reviewed and exported at a separately validated 1080p production resolution.

## Critical blocker

No real Google Flow MP4 exists in the release records yet. The planned five-keyshot strategy would provide 10 seconds for each Short and 30 seconds of the five-minute Hindi lesson, leaving **38 + 38 + 270 seconds** of educational footage to create. No episode is complete or scheduled by this engineering change.
