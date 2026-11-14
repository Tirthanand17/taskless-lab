# CLIVOX V2 P5 — Long-form source-local candidate proposal engine

## What is implemented

`scripts/branch3_v2_p5_longform_local_signal_planner.py` adds a **pure, offline, no-network** time-window planner for local half-second acoustic RMS measurements and local scene-cut timestamps from a future authorized private worker.

- Accepts strict, untrusted JSON-shape measurement objects from 30 seconds to two hours, up to 14,400 RMS samples; rejects extra API view/like/ranking fields, stale schema, wrong CLIVOX channel, unsafe timing and malformed arrays.
- Finds sudden **relative** local audio-amplitude rises, treats provided operator bookmarks as *unverified*, and uses scene cuts only as supporting evidence. A scene cut alone is **not** a viral moment.
- Proposes chronologically ordered, deduplicated up-to-36-second source windows; max 20 proposals, explicit overflow count. It may return **zero**.
- Each proposal is a human suggestion with accurate source timecodes and flags for exact source identity, transcript/quotes, editing, rights, originality and YouTube all **false**. A machine-generated audio spike is not proof that anyone laughed, that words were spoken, or that a scene is worth uploading.
- Makes **no** YouTube public-statistics-derived score, access to creators' Most replayed curve, virality probability, expected revenue or copyright conclusion.
- The measurement SHA-256 tracks untrusted signal bytes only; it is **not** a creator source digest, signature or grant.
- There is no real-media CLI, downloader, upload API, model download or production publishing entry point. The separate `production_clip_or_publish()` always denies.

## Testing

The existing source-free P5–P11 GitHub Actions workflow executes:
```sh
python -B -m scripts.branch3_v2_p5_longform_local_signal_planner --mode closed
python -B -m scripts.branch3_v2_p5_longform_local_signal_planner --mode synthetic
python -B -m unittest -v scripts.test_branch3_v2_p5_longform_local_signal_planner
```

Adversarial tests cover false external API metrics, wrong channel, noncanonical sample timing, zero-event/scene-only rejection, unverified manual marks, 2-hour input, 20-proposal overflow, deterministic digest, duplicate timestamps, boolean-as-integer rejection, and all publication/rights flags staying false.

## What is still required for real P5

1. **P2/P3:** authenticated commercial creator license and independent human verification, plus publisher/game/music/guest rights; none exists yet.
2. **P4:** an actually approved private vault and creator-delivered original media, independently verified exact media SHA, private full decode, source ID and rights linkage.
3. **P5:** license-bound extraction of real RMS, scene changes and **fallible** ASR/VAD inside the private environment. This code does not extract them from real creator files. Reference editorial labels from 40–60 legal human-reviewed candidates are needed to evaluate the suggestions.
4. **P6:** a human verifies each source moment's quote context and selects candidates; substantial original CLIVOX writing, narration or critical analysis is required.
5. **P7–P9:** exact approved video QA, owner sign-off, current revocations and protected private-first CLIVOX upload remain independently blocked.

This is usable **engineering scaffolding** for long videos, not an operational autonomous clipping bot or a completed real P5 milestone. Project acceptance remains 2/12 (17%).

See [P5 synthetic signal QA](P5_SYNTHETIC_SIGNAL_CANDIDATE_QA.md), [P5 editor reference evaluation](P5_SYNTHETIC_REFERENCE_EVALUATION.md), [P4 master technical QA](P4_PRIVATE_DELIVERED_MASTER_TECHNICAL_QA.md), and [the real phase plan](PHASED_INTEGRATION_PLAN.md).
