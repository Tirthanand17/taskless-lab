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

## New A5 private candidate script revision preview — advisory only

After the correction intake has validated the original media and edited
worksheet, the new `scripts.branch3_a5_private_revision_preview` CLI can
propose precise spoken-scene text for a human editor **without writing or
changing** the public original arcade screenplay:

```bash
python -B -m scripts.branch3_a5_private_revision_preview \
  --review-root "/private/clivox-extracted-artifact" \
  --selection all \
  --episode-id "clivox_original_door_choice_s01" \
  --edited-csv "/private/clivox-edited-short01.csv" \
  --output "/private/clivox-short01-candidate-scene-diff.json"
```

The output is a private, new-file-only (0600 POSIX) JSON proposal. Its source
identity includes the exact public catalog digest plus the prior SHA-bound
A6 packet, MP4, WAV, SRT and the edited CSV digest. It re-runs the complete
read-only correction intake and independent A6 media verification.

For a cue with `actual_words_and_pronunciation=ISSUE` and a valid proposed
replacement caption, the preview rebuilds the scene's entire proposed
`spoken` string **in the original cue order** and checks that a hypothetical
copy of the full original-only catalog passes the same strict schema. The
report contains only *affected* original/proposed spoken-scene text and
estimates the **new number of draft subtitle cues** after text wrapping;
actual speech boundaries and SRT timings cannot be inferred before a new
voice render. Every proposed scene explicitly requires editor acceptance
and a fresh TTS/WAV/SRT/MP4/A5/A6 verification.

If an issue relates only to subtitle timing or readability, or if a speech
issue contains notes without safe replacement text, it becomes a
`private_manual_editor_tasks` entry. The system never silently changes
spoken dialogue based on an on-screen timing concern. Unsafe or unrenderable
proposed voice text (URLs, embedded markup, control/non-ASCII characters,
formula-looking text, overlong words, or text exceeding the catalog limits)
is rejected rather than applied.

**The report is neither a git patch nor a release artifact.** It cannot
claim an authenticated human review or automatically modify the original
public repository, voice, captions, graphics, title/description, rights
records, or YouTube account. Only an editor who actually listened to the
review master may choose which source revisions to author and submit for
normal review. After any approved source edit, rerender from scratch and
obtain **new exact-media A6 hashes and a genuinely reviewed owner release**.
Do not commit raw private reviewer notes or the generated JSON to GitHub.

## Next stage: quarantined original-only revision render (review simulation)

The A5 `scripts.branch3_a5_revision_sandbox` command is a non-production
simulation of the actual editing workflow. It re-runs the private exact-media
correction intake and independent unsigned A6 verification, reconstructs the
in-memory candidate scene dialogue, invokes the existing original-only
renderer with **no catalog write**, and independently decodes the new H.264
caption frames and analyzes the new mixed audio cues.

The original reviewed MP4/WAV/SRT and public catalog are verified unchanged
both before and after render. The output must be an **existing, empty,
non-symlink private directory**, disjoint from the extracted original
review pack and the public repository. It is a candidate only; its generated
files are never allowed to reuse old A6 owner handoffs or signed releases.

Run this **only after** an authentic reviewer has given a private corrected
CSV, and only with a separate, empty directory:

```bash
python -B -m scripts.branch3_a5_revision_sandbox \
  --review-root "/private/clivox-extracted-artifact" \
  --selection all \
  --episode-id "clivox_original_door_choice_s01" \
  --edited-csv "/private/clivox-edited-short01.csv" \
  --output-root "/private/clivox-new-quarantined-sandbox" \
  --mode preview
```

A successful sandbox creates only an unapproved private MP4, synthetic
WAV, draft SRT, scene graphics, independent technical QA, and a private
technical report (output JSON mode 0600 on POSIX). It does **not** issue
A6 owner sign-offs or automatically accept any proposed dialogue. The
output flags human acceptance, sound/tool rights and all YouTube operations
as false, regardless of whether technical QA passed.

The source-free GitHub Action uses a **distinct, labeled synthetic-only
dialogue change** created in the temporary runner from the unchanged
review worksheet; it renders and checks a genuinely different MP4/WAV/SRT
with independent cue frame/audio QA, but does **not** upload the rehearsal
media or put its private issue notes into PRs/artifacts. This is reproducible
**technical proof only**, not a claim of a human correction, improved
audience engagement or a newly approved owner master. If any of the future
real corrections cause narration overflow, poor captions, missing audio,
changed cue counts or unsafe layout, the sandbox fails and the human
editor must revise the candidate and retry offline.

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
