# CLIVOX A5 — Private correction worksheet intake (NO RELEASE)

**Status:** GitHub-only source/CI engineering. No real reviewer-supplied edited
worksheet has been received, no spoken words have been confirmed by a human,
and no A6 owner signature, commercial rights clearance or YouTube publishing
authorization exists. This is NOT an automated editorial decision.

## Purpose

The CLIVOX GitHub Actions review artifact now contains one unsigned
CSV per video: 8 + 8 + 23 = **39** cue rows with scene numbers, original
caption text, timestamps, and the exact SHA-256 identities of the video,
narration WAV and SRT. The review gallery provides direct local video
seek links for every cue.

This new A5 intake reads a **separately edited copy** of one of those CSVs
and produces a PRIVATE, machine-readable **editorial issue plan**, not a
video or YouTube action. It can flag corrections that the human editor
must make to the authored screenplay, regenerated narration, SRT and MP4.

## One-episode owner/editor workflow (offline only)

1. Extract the **current exact** three-video GitHub review artifact into
   a private, unshared working directory. Do not upload edited CSVs, raw
   footage, commentary, identity or sensitive reviewer notes to public GitHub.
2. Open `CLIVOX-REVIEW-START-HERE.html`; watch/listen to the entire videos
   and individually inspect the 39 cue links. Verify actual spoken wording,
   pronunciation, timing and legibility using human judgment.
3. Keep each original `narration-caption-corrections-UNREVIEWED.csv` untouched
   and save a **separate copy** for edits. Do not modify the MP4, WAV, SRT,
   original A6 handoff, metadata or unsigned A6 checklist.
4. For each cue fill the three columns
   `actual_words_and_pronunciation`, `subtitle_timing` and
   `caption_visual_readability` with exactly `OK`, `ISSUE` or
   `NOT_REVIEWED`. In `correction_required`, enter:
   - `NO` **only when all three categories are OK** and the replacement
     caption is blank.
   - `YES` when at least one category is `ISSUE`; enter a concrete
     replacement caption and/or a useful private issue note.
   - `NOT_REVIEWED` only when **all three categories** are still
     `NOT_REVIEWED` and both the suggestion and notes are empty.
   A `YES` row can have other categories not reviewed, but is still
   counted pending; it must not be treated as complete.
5. From a trusted Python checkout with FFmpeg/FFprobe and the original
   A5/A6 verification dependencies installed, run:

   ```bash
   python -B -m scripts.branch3_a5_cue_correction_intake \
     --review-root "/private/clivox-extracted-artifact" \
     --selection all \
     --episode-id "clivox_original_door_choice_s01" \
     --edited-csv "/private/clivox-edited-short01.csv" \
     --output "/private/clivox-short01-issue-plan.json"
   ```

   Use a **new output path** each time. Do not use a shared/public location.
   Run separately for the other two episode IDs when human inputs exist.
6. Inspect the private JSON issue plan and manually decide which proposed
   screenplay, audio and subtitle changes to implement in a separate reviewed
   change. The script does **not** patch source files or claim the notes came
   from an authenticated owner. Apply revisions only through normal source
   review; rerender/revalidate all affected media and obtain new exact A6
   hashes. Real owner licensing and signing must occur through the separate
   trusted release process **after** full final human playback.

## Security and integration rules

- Always re-runs the full A6 **read-only** exact-media verification on the
  extracted package, including FFprobe, technical QA, file hashes and the
  original all-false owner review checklists. It will fail if the package
  is missing, stale, modified or cannot be reverified on the current code.
- Independently recalculates all immutable worksheet fields from the SRT,
  original screenplay beats and A6 hash-bound packet. Any altered episode
  ID, hash, cue ID, scene mapping, timestamp, caption text, missing or extra
  cue, or changed baseline fails closed.
- Rejects unsupported review labels and contradictory or partially completed
  worksheet claims. A `NO` decision cannot conceal an `ISSUE`.
- Rejects symlink inputs, public-repo paths, overwritten outputs and forged
  owner approval flags. The output JSON is created exclusively with private
  POSIX permissions (0600). No reviewer text is printed to CI logs.
- **Never** copies edited review notes into a GitHub PR, CI artifact,
  public repository, YouTube description, automation ledger or private
  consent/release proof. Original CI tests are **synthetic** and contain
  no real human reviews.
- Every report hard-codes `owner_review_completed=false`,
  `human_review_identity_authenticated=false`, all rights checks false,
  all YouTube upload/schedule/publish flags false and zero YouTube calls.
- Only the human editorial team can decide whether the *correct* words
  were spoken and whether the revised result is suitable for release.
  Changing CSV values or producing a report is **not a signature or
  upload permission**.

## Current verified reviewer master at implementation

The last verified three-video master was GitHub Actions
[run 43567628633](https://github.com/Tirthanand17/taskless-lab/actions/runs/43567628633).
It is a seven-day unsigned review artifact scheduled to expire on
**November 21, 2026**. The intake tool itself does not regenerate or change
that video or its underlying media hashes; it is independently tested in
the dedicated `branch3-clivox-cue-correction-intake.yml` no-network workflow.

No real reviewer-provided correction file has been processed. This is an
implementation of a safe interface for that future input, not completion
of actual editorial review or A9 YouTube publishing.
