"""B4g1 validate exact per-scene PCM durations for three original MP4s.

No scene texts, source articles, OAuth, owner identity or publishing.
Only the physical per-scene audio boundaries; this does NOT establish
which word is spoken or that any reviewer has watched the video.
"""
from __future__ import annotations
import math


class SceneTimecodeRefused(ValueError):
    """Unknown/fabricated/altered source media scene clock."""


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise SceneTimecodeRefused(reason)


def build_audio_scene_timeline(durations: list[float], total: float,
                               expected_count: int) -> list[dict]:
    """Persist exact authored scene starts, derived from actual synthesized PCM.

    The final visual transitions are frame-quantized; a subframe timestamp
    discrepancy between FFmpeg and the PCM clock is expected, not authority.
    """
    _require(type(durations) is list and
             type(expected_count) is int and expected_count in (4,9) and
             len(durations)==expected_count and
             type(total) in (int,float) and math.isfinite(total) and
             20<=total<=340,
             "Missing exact actual 4/9 scene audio clock")
    _require(all(type(d) in (int,float) and math.isfinite(d) and
                 2<=d<=55 for d in durations) and
             abs(sum(durations)-total)<=.03,
             "Scene duration values do not reconstruct PCM")
    rows=[]
    start=0.0
    for i,duration in enumerate(durations,1):
        end=start+duration
        rows.append({
            "scene_number":i,
            "start_seconds":round(start,3),
            "end_seconds":round(total if i==expected_count else end,3),
        })
        start=end
    validate_audio_scene_timeline(rows,round(total,3),expected_count)
    return rows


def validate_audio_scene_timeline(rows: object, total: float,
                                  expected_count: int) -> list[dict]:
    """Validate a public owner-review navigation timeline, no approval."""
    _require(type(rows) is list and type(expected_count) is int
             and expected_count in (4,9) and len(rows)==expected_count
             and type(total) in (int,float) and math.isfinite(total)
             and 20<=total<=340,
             "Missing 4/9 immutable scene navigation entries")
    prev=0.0
    accepted=[]
    for n,row in enumerate(rows,1):
        _require(type(row) is dict and set(row)=={
            "scene_number","start_seconds","end_seconds"
        } and type(row["scene_number"]) is int and
            row["scene_number"]==n and
            type(row["start_seconds"]) in (int,float) and
            type(row["end_seconds"]) in (int,float) and
            math.isfinite(row["start_seconds"]) and
            math.isfinite(row["end_seconds"]),
            "Malformed or reordered scene navigation")
        a,b=row["start_seconds"],row["end_seconds"]
        _require(abs(a-prev)<=.004 and 0<=a<b<=total+.005 and
                 2<=b-a<=55.005 and
                 round(a,3)==a and round(b,3)==b,
                 "Invalid physical audio scene boundary")
        accepted.append({"scene_number":n,
                         "start_seconds":float(a),"end_seconds":float(b)})
        prev=b
    _require(abs(prev-total)<=.004,
             "All original audio scenes must cover full exact MP4 duration")
    return accepted
