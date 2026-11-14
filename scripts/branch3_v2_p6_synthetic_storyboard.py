"""CLIVOX V2 P6: draft-only original storyboard for a generated P5 sample.

This creates a *written plan*, never a playable video, a licensed clip,
voice impersonation, an authorized editor decision, or YouTube content.
A3/P4/P5 media and rights remain CLOSED. No creator media is read here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.branch3_v2_p5_synthetic_moment_proposals import (
    CHANNEL, P5Denied, _probe_closed,
)
from scripts.branch3_v2_p5_synthetic_editorial_evaluation import (
    P5EvaluationDenied, _read_temp_report, assess_generated_p5_packet,
    validate_detector_report,
)

SYNTHETIC_DURATION_MS = 6000
EXPECTED_SIGNAL_TYPES = frozenset({"ACOUSTIC_RMS_RISE", "VIDEO_LUMA_CUT"})
INTERNAL_ONLY_STAGE = "CLIVOX_V2_P6_SYNTHETIC_ORIGINAL_STORYBOARD_DRAFT"
SHOT_SCHEMA = frozenset({
    "sequence", "source_start_ms", "source_end_ms", "target_start_ms",
    "target_end_ms", "source_visual", "original_clivox_overlay",
    "editorial_intent", "requires_human_review", "creator_dialogue_used",
    "licensed_media_inserted", "publisher_clearance_verified",
})
STORYBOARD_SCHEMA = frozenset({
    "stage", "channel_id", "synthetic_fixture_only",
    "original_story_brief", "original_value_statement", "candidate_reference",
    "source_duration_ms", "draft_duration_ms",
    "draft_canvas", "draft_shots", "real_creator_source_files",
    "creator_commercial_reuse_grants", "real_source_dialogue_verified",
    "human_editor_approved", "owner_final_media_approved",
    "real_editorial_context_confirmed", "licensed_clip_used",
    "video_rendered", "audio_rendered", "youtube_uploads",
    "youtube_publish_authorized", "status",
})


class P6Denied(ValueError):
    """No storyboard promotion without real-source human approval."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise P6Denied("CLIVOX_V2_P6_DENIED_" + reason)


def original_generated_shots() -> list[dict]:
    """Original editorial idea ABOUT synthetic black/white/sine fixture.

    The overlay is *original written commentary*, never alleged source speech.
    The timing is a draft and does not guarantee that text is readable.
    """
    shots = [
        (0, 2000, "SELF_GENERATED_BLACK",
         "Watch the scene switch.", "HOOK_OBSERVATION"),
        (2000, 3000, "SELF_GENERATED_WHITE_WITH_TONE",
         "Flash and tone.", "OBSERVED_SYNTHETIC_TURN"),
        (3000, 6000, "SELF_GENERATED_BLACK",
         "A sudden cut still needs context.", "ORIGINAL_CRITICAL_PAYOFF"),
    ]
    return [{
        "sequence": index,
        "source_start_ms": start,
        "source_end_ms": end,
        "target_start_ms": start,
        "target_end_ms": end,
        "source_visual": visual,
        "original_clivox_overlay": overlay,
        "editorial_intent": intent,
        "requires_human_review": True,
        "creator_dialogue_used": False,
        "licensed_media_inserted": False,
        "publisher_clearance_verified": False,
    } for index, (start, end, visual, overlay, intent)
        in enumerate(shots, start=1)]


def _candidate_has_generated_turn(report: dict) -> str:
    """Require actual reported measured evidence for the synthetic turn."""
    for item in report["synthetic_candidate_windows"]:
        if (set(item["evidence_kinds"]) == EXPECTED_SIGNAL_TYPES
                and item["start_ms"] <= 2000
                and item["end_ms"] >= 3000):
            return item["proposal_id"]
    raise P6Denied("CLIVOX_V2_P6_DENIED_NO_SUPPORTED_SYNTHETIC_TURN")


def validate_storyboard(packet: object) -> dict:
    """Enforce an immutable, source-free, non-release EDL schema."""
    _probe_closed()
    require(type(packet) is dict and set(packet) == STORYBOARD_SCHEMA,
            "STORYBOARD_SCHEMA")
    require(packet["stage"] == INTERNAL_ONLY_STAGE
            and packet["channel_id"] == CHANNEL
            and packet["status"] ==
            "SYNTHETIC_WRITTEN_DRAFT_ONLY_REAL_RIGHTS_EDITOR_APPROVAL_BLOCKED",
            "IDENTITY_OR_STATE")
    require(packet["synthetic_fixture_only"] is True
            and packet["source_duration_ms"] == SYNTHETIC_DURATION_MS
            and packet["draft_duration_ms"] == SYNTHETIC_DURATION_MS
            and packet["draft_canvas"] == {
                "width": 1080, "height": 1920,
                "rendered": False, "visual_cropping_validated": False,
            }, "SYNTHETIC_SCOPE")
    for field in ("real_creator_source_files",
                  "creator_commercial_reuse_grants", "youtube_uploads"):
        require(type(packet[field]) is int and packet[field] == 0,
                "FORGED_" + field.upper())
    for field in (
        "real_source_dialogue_verified", "human_editor_approved",
        "owner_final_media_approved", "real_editorial_context_confirmed",
        "licensed_clip_used", "video_rendered", "audio_rendered",
        "youtube_publish_authorized",
    ):
        require(packet[field] is False, "FORGED_" + field.upper())
    require(packet["original_story_brief"] ==
            "A deliberately generated black-to-white flash returns to black."
            and packet["original_value_statement"] ==
            "An observed cut is a cue, not proof of a complete narrative.",
            "WRITTEN_ORIGINAL_SCOPE")
    ref = packet["candidate_reference"]
    require(type(ref) is dict and set(ref) == {
        "proposal_id", "signal_kinds", "source_review_required",
        "validated_real_editorial_selection",
    } and type(ref["proposal_id"]) is str
        and ref["proposal_id"].startswith("synthetic_")
        and ref["signal_kinds"] == sorted(EXPECTED_SIGNAL_TYPES)
        and ref["source_review_required"] is True
        and ref["validated_real_editorial_selection"] is False,
        "CANDIDATE_REVIEW_STATE")
    shots = packet["draft_shots"]
    require(type(shots) is list and len(shots) == 3, "DRAFT_SHOT_COUNT")
    expected = original_generated_shots()
    for number, (shot, known) in enumerate(zip(shots, expected), start=1):
        require(type(shot) is dict and set(shot) == SHOT_SCHEMA
                and shot == known and type(shot["sequence"]) is int
                and shot["sequence"] == number, "SHOT_MISMATCH")
    require(shots[0]["target_start_ms"] == 0
            and shots[-1]["target_end_ms"] == SYNTHETIC_DURATION_MS
            and all(shots[i]["target_end_ms"] ==
                    shots[i + 1]["target_start_ms"]
                    for i in range(len(shots) - 1)),
            "UNSAFE_TIMELINE")
    return packet


def draft_synthetic_storyboard(report: object) -> dict:
    """P5 -> P6 proof of wiring using generated known test signal ONLY."""
    _probe_closed()  # rights and storage are checked *before* P5 packet use.
    validate_detector_report(report, duration_ms=SYNTHETIC_DURATION_MS)
    evaluation = assess_generated_p5_packet(report)
    require(evaluation["real_creator_sources"] == 0
            and evaluation["actual_human_editor_labels"] == 0
            and evaluation["p5_real_milestone_complete"] is False
            and evaluation["media_access_or_youtube_upload_authorized"] is False,
            "UPSTREAM_REAL_RIGHTS")
    require(evaluation["synthetic_test_metrics"][0]["matched_events"] >= 1,
            "NO_GENERATED_REFERENCE_MATCH")
    selected = _candidate_has_generated_turn(report)
    packet = {
        "stage": INTERNAL_ONLY_STAGE,
        "channel_id": CHANNEL,
        "synthetic_fixture_only": True,
        "original_story_brief":
            "A deliberately generated black-to-white flash returns to black.",
        "original_value_statement":
            "An observed cut is a cue, not proof of a complete narrative.",
        "candidate_reference": {
            "proposal_id": selected,
            "signal_kinds": sorted(EXPECTED_SIGNAL_TYPES),
            "source_review_required": True,
            "validated_real_editorial_selection": False,
        },
        "source_duration_ms": SYNTHETIC_DURATION_MS,
        "draft_duration_ms": SYNTHETIC_DURATION_MS,
        "draft_canvas": {
            "width": 1080, "height": 1920,
            "rendered": False, "visual_cropping_validated": False,
        },
        "draft_shots": original_generated_shots(),
        "real_creator_source_files": 0,
        "creator_commercial_reuse_grants": 0,
        "real_source_dialogue_verified": False,
        "human_editor_approved": False,
        "owner_final_media_approved": False,
        "real_editorial_context_confirmed": False,
        "licensed_clip_used": False,
        "video_rendered": False,
        "audio_rendered": False,
        "youtube_uploads": 0,
        "youtube_publish_authorized": False,
        "status": "SYNTHETIC_WRITTEN_DRAFT_ONLY_REAL_RIGHTS_EDITOR_APPROVAL_BLOCKED",
    }
    return validate_storyboard(packet)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "synthetic"), default="closed")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--report-file")
    args = parser.parse_args()
    try:
        _probe_closed()
        if args.mode == "closed":
            require(args.scratch is None and args.report_file is None,
                    "CLOSED_ARGS")
            output = {
                "stage": "CLIVOX_V2_P6_CLOSED_BEFORE_REAL_EDITORIAL",
                "channel_id": CHANNEL,
                "real_creator_source_files": 0,
                "creator_commercial_reuse_grants": 0,
                "human_editor_approved": False,
                "video_rendered": False,
                "youtube_uploads": 0,
            }
        else:
            require(args.scratch is not None and args.report_file is not None,
                    "SYNTHETIC_ARGS_REQUIRED")
            output = draft_synthetic_storyboard(
                _read_temp_report(args.scratch, args.report_file))
        print(json.dumps(output, sort_keys=True))
    except (P6Denied, P5Denied, P5EvaluationDenied, OSError, ValueError,
            TypeError, KeyError, UnicodeError):
        raise SystemExit(
            "CLIVOX_V2_P6_BLOCKED_NO_LICENSED_CREATOR_MEDIA_NO_OWNER_RELEASE"
        ) from None


if __name__ == "__main__":
    main()
