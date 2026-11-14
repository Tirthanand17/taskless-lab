"""CLIVOX P5 source-free evaluator for synthetic candidate timecodes only.

No authorized third-party content or real human labels exist in this stage.
Score technical interval overlap on ORIGINAL synthetic fixtures, with exact
closed A3/P4/P5 gates, and report false positives/missed synthetic events.
These figures are NOT verified real editor agreement, viral predictions,
creator retention data, source permissions, or permission to publish.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from scripts.branch3_v2_p5_synthetic_moment_proposals import (
    CHANNEL, MAX_CANDIDATES, _probe_closed,
)

MAX_SOURCES = 12
MAX_REFERENCE_WINDOWS = 20
MAX_DURATION_MS = 10_000
IOU_REQUIRED = 0.50
SOURCE_ID = re.compile(r"synthetic_[a-z][a-z0-9_]{3,30}\Z")
EVIDENCE = frozenset({"ACOUSTIC_RMS_RISE", "VIDEO_LUMA_CUT"})
REPORT_BASENAME = "quarantined-signals-only.json"
DETECTOR_FIELDS = frozenset({
    "stage", "channel_id", "synthetic_original_fixture_only",
    "actual_creator_source_count", "real_creator_license_count",
    "third_party_video_downloads", "outreach_messages_sent",
    "youtube_api_calls", "youtube_uploads",
    "p5_real_licensed_pipeline_complete",
    "p5_real_editor_label_evaluation_complete", "ASR_or_VAD_performed",
    "speech_or_quotes_inferred", "youtube_replay_heatmap_inferred",
    "estimated_viral_performance", "human_source_context_required",
    "synthetic_technical_candidate_count", "synthetic_candidate_windows",
    "status",
})
CANDIDATE_FIELDS = frozenset({
    "start_ms", "end_ms", "evidence_kinds", "proposal_id",
    "machine_transcript", "transcript_verified", "creator_rights_verified",
    "ready_for_editorial_use", "human_context_review_required",
})


class P5EvaluationDenied(ValueError):
    """Untrusted source, forged rights or malformed synthetic references."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise P5EvaluationDenied("CLIVOX_P5_EVAL_DENIED_" + code)


def _time_window(start: object, end: object, duration_ms: int) -> bool:
    return (type(start) is int and type(end) is int and
            0 <= start < end <= duration_ms)


def validate_detector_report(report: object, *, duration_ms: int = 6000) -> list[dict]:
    """Exact strict P5 CLI contract; creator-media or authority assertions fail."""
    _probe_closed()
    require(type(duration_ms) is int and 1000 <= duration_ms <= MAX_DURATION_MS,
            "DURATION")
    require(type(report) is dict and set(report) == DETECTOR_FIELDS,
            "EXACT_DETECTOR_SCHEMA")
    require(report["stage"] == "CLIVOX_V2_P5_SYNTHETIC_SIGNAL_CANDIDATES_ONLY"
            and report["channel_id"] == CHANNEL
            and report["status"] == "PRIVATE_LICENSING_REQUIRED_NO_REAL_CLIP_RELEASE",
            "DETECTOR_IDENTITY")
    require(report["synthetic_original_fixture_only"] is True
            and report["human_source_context_required"] is True
            and report["estimated_viral_performance"] is None, "SYNTHETIC_ONLY")
    for field in ("actual_creator_source_count", "real_creator_license_count",
                  "third_party_video_downloads", "outreach_messages_sent",
                  "youtube_api_calls", "youtube_uploads"):
        require(type(report[field]) is int and report[field] == 0,
                "FALSE_AUTHORITY_" + field.upper())
    for field in ("p5_real_licensed_pipeline_complete",
                  "p5_real_editor_label_evaluation_complete", "ASR_or_VAD_performed",
                  "speech_or_quotes_inferred", "youtube_replay_heatmap_inferred"):
        require(report[field] is False, "UNVERIFIED_" + field.upper())
    predictions = report["synthetic_candidate_windows"]
    require(type(predictions) is list and len(predictions) <= MAX_CANDIDATES
            and type(report["synthetic_technical_candidate_count"]) is int
            and report["synthetic_technical_candidate_count"] == len(predictions),
            "CANDIDATE_COUNT")
    clean = []
    previous_end = -1
    for number, row in enumerate(predictions, start=1):
        require(type(row) is dict and set(row) == CANDIDATE_FIELDS,
                "CANDIDATE_SCHEMA")
        require(row["proposal_id"] == f"synthetic_{number:02d}"
                and _time_window(row["start_ms"], row["end_ms"], duration_ms)
                and row["start_ms"] > previous_end, "CANDIDATE_TIME_ORDER")
        require(row["machine_transcript"] is None
                and row["transcript_verified"] is False
                and row["creator_rights_verified"] is False
                and row["ready_for_editorial_use"] is False
                and row["human_context_review_required"] is True,
                "CANDIDATE_NOT_LICENSED")
        kinds = row["evidence_kinds"]
        require(type(kinds) is list and len(kinds) in (1, 2)
                and kinds == sorted(set(kinds))
                and set(kinds) <= EVIDENCE, "VALID_SIGNAL_TYPES")
        clean.append({"start_ms": row["start_ms"], "end_ms": row["end_ms"]})
        previous_end = row["end_ms"]
    return clean


def _validate_synthetic_sources(sources: object) -> list[dict]:
    """Do not accept platforms, real creator IDs, text or real labels."""
    require(type(sources) is list and 1 <= len(sources) <= MAX_SOURCES,
            "SOURCE_COUNT")
    seen = set()
    safe = []
    for source in sources:
        require(type(source) is dict and set(source) == {
            "source_id", "duration_ms", "reference_kind", "predictions",
            "reference_windows", "split", "actual_human_review_completed",
            "real_source_media_accessed",
        }, "SOURCE_FIELDS")
        sid = source["source_id"]
        require(type(sid) is str and SOURCE_ID.fullmatch(sid) is not None
                and sid not in seen, "SOURCE_ID_OR_DUPLICATE")
        seen.add(sid)
        duration = source["duration_ms"]
        require(type(duration) is int and 1000 <= duration <= MAX_DURATION_MS,
                "SOURCE_DURATION")
        require(source["reference_kind"] ==
                "SYNTHETIC_GOLDEN_EVENT_TIMECODES_NOT_EDITOR_LABELS"
                and source["split"] == "SYNTHETIC_HELDOUT_TEST"
                and source["actual_human_review_completed"] is False
                and source["real_source_media_accessed"] is False,
                "NO_REAL_SOURCE_OR_HUMAN_LABELS")
        predictions = source["predictions"]
        references = source["reference_windows"]
        require(type(predictions) is list and len(predictions) <= MAX_CANDIDATES
                and type(references) is list
                and len(references) <= MAX_REFERENCE_WINDOWS,
                "MOMENT_COUNTS")
        for name, windows, count in (
            ("PRED", predictions, MAX_CANDIDATES),
            ("REF", references, MAX_REFERENCE_WINDOWS),
        ):
            last_end = -1
            for row in windows:
                require(type(row) is dict and set(row) ==
                        {"start_ms", "end_ms"}, name + "_SCHEMA")
                require(_time_window(row["start_ms"], row["end_ms"], duration)
                        and row["start_ms"] > last_end, name + "_ORDER_OR_OVERLAP")
                last_end = row["end_ms"]
        safe.append(source)
    return safe


def _iou(a: dict, b: dict) -> float:
    intersection = max(0, min(a["end_ms"], b["end_ms"]) -
                       max(a["start_ms"], b["start_ms"]))
    union = max(a["end_ms"], b["end_ms"]) - min(
        a["start_ms"], b["start_ms"])
    return intersection / union if union else 0.0


def evaluate_synthetic_sources(sources: object) -> dict:
    """One-to-one IoU matching, per-source (not cross-owner statistics).

    Precision among up to five proposals: TP/min(5, proposals available).
    Recall: matched reference events / all synthetic golden events.
    Null means a denominator is absent; it is never a zero rating.
    """
    _probe_closed()
    rows = _validate_synthetic_sources(sources)
    per_source = []
    for row in rows:
        suggestions = row["predictions"][:5]
        gold = row["reference_windows"]
        possible = sorted(
            ((-_iou(proposal, ref), pi, ri)
             for pi, proposal in enumerate(suggestions)
             for ri, ref in enumerate(gold)
             if _iou(proposal, ref) >= IOU_REQUIRED),
            key=lambda x: (x[0], x[1], x[2]),
        )
        claimed_proposals, claimed_references = set(), set()
        for _, pi, ri in possible:
            if pi not in claimed_proposals and ri not in claimed_references:
                claimed_proposals.add(pi)
                claimed_references.add(ri)
        tp = len(claimed_proposals)
        per_source.append({
            "synthetic_source_id": row["source_id"],
            "proposals_considered_up_to_five": len(suggestions),
            "reference_events": len(gold),
            "matched_events": tp,
            "unmatched_proposals": len(suggestions) - tp,
            "missed_reference_events": len(gold) - tp,
            "precision_of_available_top_five": (
                round(tp / len(suggestions), 4) if suggestions else None),
            "recall_of_synthetic_reference_events": (
                round(tp / len(gold), 4) if gold else None),
        })
    return {
        "stage": "CLIVOX_V2_P5_SYNTHETIC_REFERENCE_EVALUATION_ONLY",
        "channel_id": CHANNEL,
        "reference_provenance": "GENERATED_FIXTURE_GOLD_NOT_REAL_HUMAN_REVIEW",
        "test_sources": len(rows),
        "source_split": "DISJOINT_SYNTHETIC_SOURCE_IDENTITIES_NO_TRAINING",
        "training_performed": False,
        "real_creator_sources": 0,
        "real_creator_licenses": 0,
        "actual_human_editor_labels": 0,
        "real_world_precision_recall_validated": False,
        "viral_performance_prediction": None,
        "media_access_or_youtube_upload_authorized": False,
        "aggregate_real_creator_api_statistics_computed": False,
        "human_context_and_rights_review_still_required": True,
        "synthetic_test_metrics": per_source,
        "p5_real_milestone_complete": False,
        "status": "SYNTHETIC_TEST_ONLY_NO_LIVE_CLIPPING",
    }


def assess_generated_p5_packet(report: object) -> dict:
    """Bridge actual synthetic detector output to one known test event."""
    proposals = validate_detector_report(report, duration_ms=6000)
    return evaluate_synthetic_sources([{
        "source_id": "synthetic_generated_scene_sine",
        "duration_ms": 6000,
        "reference_kind": "SYNTHETIC_GOLDEN_EVENT_TIMECODES_NOT_EDITOR_LABELS",
        "predictions": proposals,
        # Generated black/white scene 2-3s + tone 2-3s. The golden
        # event is synthetic by construction; NOT a human-rated highlight.
        "reference_windows": [{"start_ms": 1200, "end_ms": 4200}],
        "split": "SYNTHETIC_HELDOUT_TEST",
        "actual_human_review_completed": False,
        "real_source_media_accessed": False,
    }])


def _read_temp_report(scratch: Path, basename: str) -> object:
    require(isinstance(scratch, Path) and not scratch.is_symlink()
            and scratch.is_dir() and type(basename) is str
            and basename == REPORT_BASENAME, "TEMP_REPORT_ARGS")
    root = scratch.resolve(strict=True)
    target = root / basename
    require(target.is_file() and not target.is_symlink()
            and target.resolve(strict=True).parent == root
            and target.stat().st_size <= 32_768, "TEMP_REPORT_SAFE")
    return json.loads(target.read_text(encoding="utf-8"))


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
            result = {
                "stage": "CLIVOX_V2_P5_EVALUATION_CLOSED",
                "channel_id": CHANNEL,
                "actual_human_editor_labels": 0,
                "p5_real_milestone_complete": False,
                "youtube_upload_authorized": False,
            }
        else:
            require(args.scratch is not None and args.report_file is not None,
                    "SYNTHETIC_ARGS")
            result = assess_generated_p5_packet(
                _read_temp_report(args.scratch, args.report_file))
        print(json.dumps(result, sort_keys=True))
    except (P5EvaluationDenied, ValueError, OSError, KeyError, TypeError):
        raise SystemExit("CLIVOX_P5_EVAL_BLOCKED_NO_REAL_MEDIA_NO_RELEASE") from None


if __name__ == "__main__":
    main()
