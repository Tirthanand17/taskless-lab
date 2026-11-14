# CLIVOX V2 P5→P6 — Long-form candidate-to-editorial review bridge (UNAPPROVED)

This integration is entirely source-free and uses only the numeric synthetic fixture already available in [P5 long-form planning](P5_LONGFORM_LOCAL_SIGNAL_CANDIDATE_PLANNER.md). It **does not watch videos**, verify creator rights, transcribe dialogue, write a real clip script, construct an EDL, render copyrighted footage, contact anyone or upload to YouTube.

## Specific problem fixed

The P5 planner previously decided a later event should be merged into the preceding proposal when the two *proposed windows overlapped*. That could add evidence of an event that occurred **after the first candidate's actual end time**. The resulting candidate falsely implied that the clip contained the marked moment.

Now P5 folds later evidence into the preceding candidate **only when the event's own timestamp falls inside that candidate's start/end interval**. If the event falls outside, P5 makes a separate candidate (possibly with overlapping context; that still requires human deduplication). The existing 20-proposal cap and explicit overflow reporting remain.

## P6 review intake, without falsely promoted rights

New `scripts/branch3_v2_p6_longform_editorial_intake.py` recomputes the entire P5 proposal report from the exact untrusted local measurements. A modified candidate ID, timecode, signal label, digest, count, flag, or added "licensed" field fails closed.

For each unapproved candidate, the module prepares a review card containing:
- Exact source-relative start/end proposed timecodes and measured event labels only.
- A **ten-check human queue**: original media identity and digest; creator's commercial grant; music/game/guest/publisher clearance; preceding/following context; actual quotes; human moment choice; distinct original CLIVOX commentary; accessibility/crop/caption review; attribution metadata; separate owner release.
- No invented speakers, quotes, narrative, virality rating, rights consent or proof of human approval. All flags for source authentication, license, human originality, rendering and YouTube remain `false`; synthetic "video-ready" state is never emitted.
- No candidates is an ordinary safe outcome. A test event, audio volume rise or public replay metric does **not** establish engagement, audience retention or a viral clip.

This is a review **intake document**, not an editor's completed decision. It has no production approval API; `production_editorial_approval()` always denies.

## Testing

```sh
python -B -m scripts.branch3_v2_p5_longform_local_signal_planner --mode synthetic
python -B -m scripts.branch3_v2_p6_longform_editorial_intake --mode synthetic
python -B -m unittest -v scripts.test_branch3_v2_p5_longform_local_signal_planner scripts.test_branch3_v2_p6_longform_editorial_intake
```

The existing `.github/workflows/branch3-clivox-v2-p5-synthetic-candidates-qa.yml` now exercises this bridge together with P5–P11 offline QA. No creator footage, private contract, secret, subscriber analytics or upload is used, and no media artifact is retained.

## Human / production boundary still missing

Actual owner review requires independent legal and source evidence: a verified creator-commercial license, approved private original master, intact full-source context, live human editor, independent original writing, approved rendered video and signed final-owner release. No input fixture or code pull request substitutes for that evidence.

**Real accepted roadmap progress remains P0/P1 = 2/12 (17%).** Do not mark real P5 or P6 complete on this technical test passing.
