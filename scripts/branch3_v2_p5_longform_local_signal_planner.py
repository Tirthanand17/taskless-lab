"""CLIVOX V2 P5: offline long-form editorial *candidate* window planner.

Consumes local numeric measurements ONLY; no media, API metrics, downloads,
YouTube watch heatmaps, ASR quotes, creator permissions or viral prediction.
Output is an unapproved, media-unbound human-review suggestion.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
import hashlib
import json
import statistics

from scripts.branch3_v2_p4_synthetic_handoff_preflight import CHANNEL

STEP_MS = 500
MAX_MS = 2 * 60 * 60 * 1000
MAX_SCENES = 10000
MAX_MARKS = 100
MAX_CANDIDATES = 20
SCHEMA = frozenset((
    "schema_version", "channel_id", "source_measurements_state",
    "duration_ms", "rms_step_ms", "audio_rms", "scene_cuts_ms",
    "unverified_editor_marks_ms",
))
STATE = "LOCAL_UNAUTHENTICATED_SIGNAL_MEASUREMENTS_ONLY"
RIGHTS_HOLD = "CANDIDATES_NOT_BOUND_TO_LICENSED_SOURCE_OR_HUMAN_REVIEW"


class LongformDenied(ValueError):
    """Reject incompatible sources, API-derived claims and invalid signals."""


def need(ok: bool, code: str) -> None:
    if not ok:
        raise LongformDenied("CLIVOX_V2_P5_LONGFORM_DENIED_" + code)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _times(values: object, duration: int, cap: int, code: str) -> list[int]:
    need(type(values) is list and len(values) <= cap
         and all(type(t) is int and 0 <= t < duration for t in values)
         and values == sorted(set(values)), code)
    return values


def validate_measurements(doc: object) -> dict:
    need(type(doc) is dict and set(doc) == SCHEMA, "EXACT_FIELDS")
    need(type(doc["schema_version"]) is int and doc["schema_version"] == 1
         and doc["channel_id"] == CHANNEL
         and doc["source_measurements_state"] == STATE
         and type(doc["rms_step_ms"]) is int and doc["rms_step_ms"] == STEP_MS,
         "PROVENANCE_AND_CHANNEL")
    duration = doc["duration_ms"]
    need(type(duration) is int and 30000 <= duration <= MAX_MS,
         "DURATION_BOUNDS")
    samples = doc["audio_rms"]
    expected = (duration + STEP_MS - 1) // STEP_MS
    need(type(samples) is list and len(samples) == expected
         and all(type(v) is int and 0 <= v <= 32767 for v in samples),
         "HALF_SECOND_LOCAL_AUDIO_BINS")
    _times(doc["scene_cuts_ms"], duration, MAX_SCENES, "SCENE_TIMES")
    _times(doc["unverified_editor_marks_ms"], duration, MAX_MARKS,
           "EDITOR_MARK_TIMES")
    return doc


def _rise_events(rms: list[int]) -> list[int]:
    """Relative acoustic transitions only; NOT laughter/speech/surprise ID."""
    result = []
    for i in range(8, len(rms)):
        previous = rms[i - 8:i]
        local = statistics.median(previous)
        v = rms[i]
        if (v >= 700 and v > 1.9 * max(local, 1)
                and v > 1.8 * max(rms[i - 1], 1)):
            result.append(i * STEP_MS)
    return result


def plan_longform_candidates(doc: object) -> dict:
    validate_measurements(doc)
    duration = doc["duration_ms"]
    acoustic = _rise_events(doc["audio_rms"])
    marks = doc["unverified_editor_marks_ms"]
    observations = sorted(
        [(t, "ACOUSTIC_RISE_HEURISTIC") for t in acoustic]
        + [(t, "UNVERIFIED_EDITOR_MARK") for t in marks]
    )
    scenes = doc["scene_cuts_ms"]
    clips = []
    omitted = 0
    for when, kind in observations:
        span = min(36000, duration)
        start = min(max(0, when - 8000), duration - span)
        end = start + span
        if clips and start < clips[-1]["end_ms"] + 2500:
            evidence = clips[-1]["evidence_kinds"]
            clips[-1]["evidence_kinds"] = sorted(set(evidence + [kind]))
            continue
        if len(clips) >= MAX_CANDIDATES:
            omitted += 1
            continue
        idx = bisect_left(scenes, start)
        scene_support = idx < len(scenes) and scenes[idx] <= end
        kinds = [kind] + (["VIDEO_SCENE_CHANGE_SUPPORT"] if scene_support else [])
        clips.append({
            "candidate_id": "local_%02d" % (len(clips) + 1),
            "start_ms": start,
            "end_ms": end,
            "evidence_kinds": sorted(kinds),
            "source_media_sha256_authenticated": False,
            "creator_license_authenticated": False,
            "transcript_and_quote_verified": False,
            "human_editorial_context_review_completed": False,
            "original_clivox_story_approved": False,
            "clip_render_authorized": False,
            "youtube_upload_authorized": False,
            "viral_probability": None,
        })
    return {
        "stage": "CLIVOX_V2_P5_LOCAL_LONGFORM_CANDIDATE_DRAFT_ONLY",
        "channel_id": CHANNEL,
        "source_measurement_sha256_not_source_license":
            hashlib.sha256(canonical(doc)).hexdigest(),
        "duration_ms": duration,
        "local_acoustic_rise_count": len(acoustic),
        "operator_bookmark_count_unverified": len(marks),
        "candidate_count": len(clips),
        "candidate_overflow_omitted_count": omitted,
        "result_is_complete_editorial_selection": False,
        "source_media_authenticated": False,
        "creator_commercial_rights_authenticated": False,
        "ASR_transcript_obtained": False,
        "youtube_api_metrics_used": False,
        "youtube_most_replayed_heatmap_accessed": False,
        "actual_viral_performance_predicted": False,
        "human_editorial_review_completed": False,
        "ready_for_render": False,
        "youtube_upload_authorized": False,
        "p5_real_milestone_complete": False,
        "candidates": clips,
        "status": (RIGHTS_HOLD if clips else
                   "NO_CLEAR_LOCAL_SIGNAL_CANDIDATES_HUMAN_REVIEW_REQUIRED"),
    }


def synthetic_demo() -> dict:
    """Deterministic source-free measurement fixture, NEVER source footage."""
    rms = [120] * 360
    for i in (80, 218, 315):
        rms[i] = 7200
    return {
        "schema_version": 1,
        "channel_id": CHANNEL,
        "source_measurements_state": STATE,
        "duration_ms": 180000,
        "rms_step_ms": STEP_MS,
        "audio_rms": rms,
        "scene_cuts_ms": [40500, 110000, 158000],
        "unverified_editor_marks_ms": [175000],
    }


def production_clip_or_publish(*_args, **_kwargs) -> None:
    raise LongformDenied("CLIVOX_V2_P5_LONGFORM_DENIED_NO_REAL_RIGHTS_OR_EDITOR_APPROVAL")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("closed", "synthetic"), default="closed")
    args = p.parse_args()
    if args.mode == "closed":
        print(json.dumps({
            "stage": "CLIVOX_V2_P5_LOCAL_LONGFORM_CLOSED",
            "channel_id": CHANNEL,
            "creator_licenses": 0, "real_media_processed": 0,
            "youtube_uploads": 0,
        }, sort_keys=True))
        return
    report = plan_longform_candidates(synthetic_demo())
    need(report["candidate_count"] == 3
         and report["youtube_upload_authorized"] is False
         and report["p5_real_milestone_complete"] is False,
         "SYNTHETIC_TEST_CONTRACT")
    print(json.dumps({
        "stage": report["stage"],
        "source_free_fixture": True,
        "candidate_count": report["candidate_count"],
        "source_media_authenticated": False,
        "creator_commercial_rights_authenticated": False,
        "youtube_uploads": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
