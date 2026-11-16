"""Fail-closed per-chapter authentic-action pacing budget for real app Shorts.

Checks the ACTUAL synthetic speech durations before allowing video_graph()
to clone any source frame. The prior 10-second pilot was 90–96% static
according to exact rendered MP4 ROI audit 43811573881 and is REJECTED.
"""
from __future__ import annotations

import json
import math

MAX_CLONED_SECONDS_PER_CHAPTER=1.25
MAX_CLONED_SOURCE_SHARE=0.25

class RealActionCoverageRefused(ValueError):
    """Real application evidence too short for the actual narration."""

def requirement_plan(source_windows,chapter_voice_seconds):
    if (type(source_windows) not in (list,tuple)
            or type(chapter_voice_seconds) not in (list,tuple)
            or len(source_windows)!=len(chapter_voice_seconds)
            or not 3<=len(source_windows)<=12):
        raise RealActionCoverageRefused("INVALID_REAL_APP_CHAPTER_SCHEDULE")
    windows=[]
    for (start,window),duration in zip(source_windows,chapter_voice_seconds):
        if (type(start) not in (int,float) or type(window) not in (int,float)
                or type(duration) not in (int,float)
                or not all(map(math.isfinite,(start,window,duration)))
                or not 0<=start<=90 or not .25<=window<=60
                or not 1<=duration<=60):
            raise RealActionCoverageRefused("INVALID_SOURCE_OR_VOICE_TIME")
        windows.append({
            "recording_start_seconds":round(start,3),
            "actual_source_seconds":round(window,3),
            "voice_seconds":round(duration,3),
            "clone_needed_seconds":round(max(0.,duration-window),3),
            "minimum_genuine_coverage_for_next_capture_seconds":
                round(max(.25,duration-MAX_CLONED_SECONDS_PER_CHAPTER),3),
        })
    total_voice=sum(float(x) for x in chapter_voice_seconds)
    total_clone=sum(max(0.,float(d)-float(w))
                    for (_,w),d in zip(source_windows,chapter_voice_seconds))
    ratio=total_clone/total_voice
    max_hold=max(item["clone_needed_seconds"] for item in windows)
    accepted=(ratio<=MAX_CLONED_SOURCE_SHARE and
              max_hold<=MAX_CLONED_SECONDS_PER_CHAPTER)
    return {
        "schema":"FLOWMINUTE_B1_REAL_ACTION_COVERAGE_V1",
        "status":("SOURCE_TIMELINE_COVERS_REAL_NARRATION"
                  if accepted else "RECORD_LONGER_REAL_APPLICATION_ACTIONS"),
        "narration_seconds":round(total_voice,3),
        "actual_reused_source_window_seconds":
            round(sum(float(w) for _,w in source_windows),3),
        "necessary_frozen_seconds":round(total_clone,3),
        "predicted_frozen_fraction":round(ratio,3),
        "worst_frozen_chapter_seconds":round(max_hold,3),
        "chapter_requirements":windows,
        "internal_screen_coverage_pass":accepted,
        "screen_motion_measured_from_pixels":False,
        "owner_approval":False,
        "youtube_uploads":0,
        "youtube_schedules":0,
    }

def require_coverage(source_windows,chapter_voice_seconds):
    report=requirement_plan(source_windows,chapter_voice_seconds)
    if not report["internal_screen_coverage_pass"]:
        raise RealActionCoverageRefused(
            "NO_PROLONGED_STATIC_GUI: "
            +json.dumps({
                "frozen_share":report["predicted_frozen_fraction"],
                "max_frozen_seconds":report["worst_frozen_chapter_seconds"],
                "needed_source_sec":[
                    x["minimum_genuine_coverage_for_next_capture_seconds"]
                    for x in report["chapter_requirements"]
                ]
            },sort_keys=True)
        )
    return report
