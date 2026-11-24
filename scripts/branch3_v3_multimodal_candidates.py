"""CLIVOX V3: bounded multimodal candidate planning, source-free engineering.

Consumes numerical observations, not media or public platform metrics.
All candidates are unapproved. No rendering, source fetching or release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from bisect import bisect_left, bisect_right

from scripts.branch3_v2_p5_longform_local_signal_planner import (
    CHANNEL, canonical, plan_longform_candidates, STATE,
)
from scripts.branch3_v2_p5_synthetic_moment_proposals import _probe_closed

VERSION = 1
STEP = 500
MAX_DURATION = 7_200_000
MAX_EVENTS = 512
MAX_CLIPS = 20
PROFILES = {
    "gaming": {"audio": 2, "motion": 3, "semantic": 2, "mark": 3},
    "dialogue": {"audio": 1, "motion": 0, "semantic": 4, "mark": 3},
    "reaction": {"audio": 2, "motion": 2, "semantic": 3, "mark": 3},
}
FIELDS = {"schema_version", "channel_id", "state", "profile", "duration_ms",
          "step_ms", "audio_rms", "motion", "scene_cuts_ms",
          "semantic_events_ms", "editor_marks_ms"}
INPUT_STATE = "UNAUTHENTICATED_LOCAL_NUMERIC_OBSERVATIONS_ONLY"


def require(ok, code):
    if not ok:
        raise ValueError("CLIVOX_V3_DENIED_" + code)


def times(values, duration, cap):
    require(type(values) is list and len(values) <= cap and
            all(type(v) is int and 0 <= v < duration for v in values)
            and values == sorted(set(values)), "TIMES")
    return values


def samples(values, length, maximum):
    if values is None:
        return
    require(type(values) is list and len(values) == length and
            all(type(v) is int and 0 <= v <= maximum for v in values),
            "SAMPLES")


def validate(doc):
    require(type(doc) is dict and set(doc) == FIELDS, "FIELDS")
    require(type(doc["schema_version"]) is int and doc["schema_version"] == VERSION
            and doc["channel_id"] == CHANNEL and doc["state"] == INPUT_STATE
            and type(doc["step_ms"]) is int and doc["step_ms"] == STEP
            and type(doc["profile"]) is str and doc["profile"] in PROFILES, "CONTRACT")
    duration = doc["duration_ms"]
    require(type(duration) is int and 20_000 <= duration <= MAX_DURATION, "DURATION")
    n = (duration + STEP - 1) // STEP
    samples(doc["audio_rms"], n, 32767)
    samples(doc["motion"], n, 10000)
    times(doc["scene_cuts_ms"], duration, 10000)
    for key in ("semantic_events_ms", "editor_marks_ms"):
        if doc[key] is not None:
            times(doc[key], duration, MAX_EVENTS)
    return doc


def peaks(values, floor, cuts=()):
    """Adaptive local baseline; cuts cannot be mistaken for optical flow."""
    if values is None:
        return []
    result = []
    for i in range(8, len(values)):
        t = i * STEP
        j = bisect_left(cuts, max(0, t - STEP))
        if j < len(cuts) and cuts[j] <= t + STEP:
            continue
        history = values[max(0, i - 40):i]
        med = statistics.median(history)
        mad = statistics.median(abs(v - med) for v in history)
        threshold = med + max(floor, 4 * mad, med * .7)
        if values[i] >= threshold and values[i] > values[i - 1] + floor / 2:
            result.append(t)
    return result


def baseline(doc):
    """Reuse V2 planner on compatible observations; no inferred missing audio."""
    validate(doc)
    if doc["audio_rms"] is None or doc["duration_ms"] < 30000:
        return None
    return plan_longform_candidates({
        "schema_version": 1, "channel_id": CHANNEL,
        "source_measurements_state": STATE, "duration_ms": doc["duration_ms"],
        "rms_step_ms": STEP, "audio_rms": doc["audio_rms"],
        "scene_cuts_ms": doc["scene_cuts_ms"],
        "unverified_editor_marks_ms": (doc["editor_marks_ms"] or [])[:100],
    })


def propose(doc):
    _probe_closed()
    validate(doc)
    duration = doc["duration_ms"]
    weights = PROFILES[doc["profile"]]
    cuts = doc["scene_cuts_ms"]
    streams = {
        "audio": peaks(doc["audio_rms"], 700),
        "motion": peaks(doc["motion"], 200, cuts),
        "semantic": doc["semantic_events_ms"] or [],
        "mark": doc["editor_marks_ms"] or [],
    }
    events = sorted((t, kind) for kind, ts in streams.items() if weights[kind]
                    for t in ts)
    # Bound pathological inputs explicitly rather than silently selecting a prefix.
    require(len(events) <= 4 * MAX_EVENTS, "EVENT_OVERFLOW")
    times_only = [t for t, _ in events]
    drafts = []
    for t, kind in events:
        if kind == "audio" and doc["profile"] == "dialogue":
            # Audio-only energy is not adequate dialogue context.
            lo = bisect_left(times_only, t - 3000)
            hi = bisect_right(times_only, t + 3000)
            if not any(k in ("semantic", "mark") for _, k in events[lo:hi]):
                continue
        span = min(duration, 32000 if doc["profile"] == "dialogue" else 36000)
        start = min(max(0, t - 8000), duration - span)
        end = start + span
        left = bisect_left(times_only, max(start, t - 3000))
        right = bisect_left(times_only, min(end, t + 3001))
        evidence = sorted(set(events[left:right]))
        kinds = {k for _, k in evidence}
        priority = sum(weights[k] for k in kinds)
        drafts.append((priority, t, start, end, evidence))
    selected = []
    suppressed = 0
    overflow = 0
    for priority, t, start, end, evidence in sorted(drafts, key=lambda x: (-x[0], x[1], x[2])):
        if any(max(start, c["start_ms"]) < min(end, c["end_ms"]) for c in selected):
            suppressed += 1
            continue
        if len(selected) >= MAX_CLIPS:
            overflow += 1
            continue
        selected.append({
            "start_ms": start, "end_ms": end, "anchor_ms": t,
            "evidence": [{"time_ms": u, "kind": k} for u, k in evidence],
            "local_editorial_priority": priority, "viral_probability": None,
            "human_review_required": True, "render_authorized": False,
            "youtube_upload_authorized": False,
        })
    for i, c in enumerate(selected, 1):
        c["candidate_id"] = f"v3_{i:02}"
    _probe_closed()
    return {
        "schema_version": VERSION, "channel_id": CHANNEL,
        "stage": "CLIVOX_V3_UNREVIEWED_NUMERIC_CANDIDATES_ONLY",
        "profile": doc["profile"],
        "measurement_sha256_not_media_or_license": hashlib.sha256(canonical(doc)).hexdigest(),
        "missing_modalities": [k for k in ("audio_rms", "motion", "semantic_events_ms",
                                            "editor_marks_ms") if doc[k] is None],
        "event_counts": {k: len(ts) for k, ts in streams.items()},
        "suppressed_overlaps": suppressed, "omitted_capacity": overflow,
        "candidates": selected, "creator_rights_verified": False,
        "human_editor_approved": False, "source_media_authenticated": False,
        "ready_to_render": False, "youtube_upload_authorized": False,
        "real_milestone_complete": False, "viral_probability": None,
    }


def demo(profile="gaming"):
    audio, motion = [100] * 240, [10] * 240
    audio[60] = 7000
    motion[150] = 8000
    return {"schema_version": VERSION, "channel_id": CHANNEL, "state": INPUT_STATE,
            "profile": profile, "duration_ms": 120000, "step_ms": STEP,
            "audio_rms": audio, "motion": motion, "scene_cuts_ms": [],
            "semantic_events_ms": [75500], "editor_marks_ms": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    if not args.synthetic:
        print(json.dumps({"stage": "CLOSED", "youtube_upload_authorized": False}))
        return
    d = demo()
    old, new = baseline(d), propose(d)
    print(json.dumps({"fixture_only": True, "baseline_candidates": old["candidate_count"],
                      "multimodal_candidates": len(new["candidates"]),
                      "report": new}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
