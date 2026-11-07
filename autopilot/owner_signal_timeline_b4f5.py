"""B4f5 bind B4f4 encoded-AV warnings to exact THREE original offline MP4s.

Converts strictly measured, per-MP4 black/freeze/silence intervals into
bounded, anonymous seek hints, never approval. A separate manual-only step
embeds these hints inside the existing offline HTML review dashboard.

NO network, SDK, transcripts, news, remote assets, YouTube, publish actions,
rights assertions, private keys, or auto-PASS human review statuses.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re

from autopilot.manual_rehearsal_review_export_b4e3 import (
    EXPORT_STATUS, SLOT_NAMES,
)
from autopilot.rehearsal_encoded_signal_review_b4f4 import (
    STATUS as SIGNAL_STATUS, REPORT_NAME, _sha_file,
)
from autopilot.review_worksheet_validator_b4e6 import inspect as review_inspect
from autopilot.offline_review_portal_b4e7 import PORTAL_FILE

STATUS = "B4F5_SHA_LOCKED_SEEKABLE_ENCODED_WARNING_HINTS_NO_REVIEW_APPROVAL"
SEEK_KINDS = (
    ("black_intervals", "BLACK_SEGMENT_REVIEW", "Possible black frame"),
    ("freeze_intervals", "POTENTIALLY_STATIC_OR_FROZEN_VISUAL_REVIEW",
     "Possible freeze / static frame"),
    ("audio_silence_intervals", "LONG_SILENCE_LISTEN_AND_CHECK",
     "Long silence"),
)
OTHER_CODES = {
    "SAMPLE_PEAK_NEAR_ZERO_CLIPPING_RISK",
    "AVERAGE_AUDIO_VERY_QUIET_CHECK",
}
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
MAX_HINTS_PER_VIDEO = 240


class TimelineRefused(ValueError):
    """Reject missing, altered, or publication-authorizing review evidence."""


def _need(ok: bool, reason: str) -> None:
    if not ok:
        raise TimelineRefused(reason)


def _real(x: object, minimum: float, maximum: float) -> bool:
    return (type(x) in (int, float) and math.isfinite(x)
            and minimum <= x <= maximum)


def _read_json(path: Path, max_bytes: int) -> dict:
    _need(not path.is_symlink() and path.is_file()
          and 20 <= path.stat().st_size <= max_bytes,
          "Missing/unsafe owner-review JSON input")
    try:
        result = json.loads(path.read_text(encoding="utf8"))
    except (UnicodeError, json.JSONDecodeError):
        raise TimelineRefused("Review JSON cannot be read safely") from None
    _need(type(result) is dict, "Expected bounded object")
    return result


def validate_signal_timeline(
    manifest: dict, worksheet: dict, diagnostics: dict,
) -> dict:
    """Bind every seek hint to exact trusted MP4 identity and no-release status."""
    try:
        proof = review_inspect(manifest, worksheet)
    except (ValueError, KeyError, TypeError):
        raise TimelineRefused("Review manifest/worksheet binding invalid") from None
    _need(proof["self_reported_reviewed_scenes"] == 0
          and proof["individual_checks_not_reviewed"] == 47
          and proof["individual_checks_pass"] == 0
          and proof["individual_checks_fail"] == 0
          and all(x.get("overall_human_decision") == "NOT_REVIEWED"
                  for x in worksheet["videos"]),
          "Owner review must begin totally blank")
    _need(type(diagnostics) is dict
          and diagnostics.get("status") == SIGNAL_STATUS
          and diagnostics.get(
              "physical_original_encoded_mp4s_independently_decoded_for_signals") == 3
          and diagnostics.get("original_scenes_represented") == 17
          and diagnostics.get("warnings_require_real_owner_playback") is True
          and diagnostics.get("sample_peak_is_not_oversampled_true_peak") is True
          and diagnostics.get("audio_quietness_is_not_integrated_lufs") is True
          and diagnostics.get("human_full_video_reviews") == 0
          and diagnostics.get("factual_and_rights_approvals") == 0
          and diagnostics.get("youtube_uploads_or_release_authority") == 0
          and type(diagnostics.get("videos")) is list
          and len(diagnostics["videos"]) == 3,
          "Only genuine final encoded unapproved QA report accepted")
    videos = []
    for (slot, filename, count), entry, worksheet_row, diag in zip(
            SLOT_NAMES, manifest["videos"], worksheet["videos"],
            diagnostics["videos"]):
        duration = entry["measured_audio_seconds"]
        digest = entry["sha256"]
        _need(type(diag) is dict
              and diag.get("slot") == slot
              and diag.get("original_voiced_scene_count") == count
              and diag.get("source_mp4_sha256") == digest
              and type(digest) is str and DIGEST.fullmatch(digest) is not None
              and _real(duration, 20, 340)
              and diag.get("measured_pcm_seconds") == duration
              and worksheet_row.get("sha256") == digest
              and worksheet_row.get("filename") == filename,
              "Warning sequence changed MP4, scene order, duration or SHA256")
        _need(diag.get("technical_anomaly_detector_is_not_a_human_judgment") is True
              and diag.get("human_full_audio_visual_watch_completed") is False
              and diag.get("final_rights_or_facts_approved") is False,
              "Technical warnings falsely upgraded to human or factual approval")
        sample_peak = diag.get("sample_peak_dbfs_not_true_peak")
        sample_mean = diag.get("sample_mean_dbfs_not_integrated_lufs")
        _need(_real(sample_peak, -100, 6)
              and _real(sample_mean, -100, sample_peak),
              "Missing or unsafe encoded audio sample metrics")
        codes = diag.get("warning_codes")
        _need(type(codes) is list and
              len(codes) == len(set(codes))
              and all(type(x) is str and x in (
                  {kind[1] for kind in SEEK_KINDS} | OTHER_CODES)
                  for x in codes),
              "Unexpected or duplicated warning code")
        expected_codes = []
        hints = []
        for field, code, label in SEEK_KINDS:
            items = diag.get(field)
            _need(type(items) is list and len(items) <= 80,
                  "Missing or oversized warning intervals")
            if items:
                expected_codes.append(code)
            previous_start = -1.
            for item in items:
                _need(type(item) is dict
                      and set(item) in (
                          {"start_seconds", "end_seconds", "duration_seconds"},
                          {"start_seconds", "end_seconds", "duration_seconds",
                           "unfinished_at_video_end"})
                      and (field == "freeze_intervals" or
                           "unfinished_at_video_end" not in item),
                      "Unsafe review warning entry")
                start, end, length = (
                    item["start_seconds"], item["end_seconds"],
                    item["duration_seconds"],
                )
                minimum = 5.0 if field == "freeze_intervals" else (
                    1.6 if field == "audio_silence_intervals" else 0.8)
                _need(_real(start, 0, duration+2)
                      and _real(end, 0, duration+2)
                      and _real(length, minimum-0.02, duration+2)
                      and end > start and start >= previous_start
                      and abs((end-start)-length) < 0.06,
                      "Warning timestamps not physical, sorted or in bounds")
                if "unfinished_at_video_end" in item:
                    _need(item["unfinished_at_video_end"] is True
                          and field == "freeze_intervals",
                          "Forged media-tail anomaly")
                previous_start = start
                hints.append({
                    "kind":code, "label":label,
                    "start_seconds":round(float(start), 2),
                    "end_seconds":round(float(end), 2),
                    "duration_seconds":round(float(length), 2),
                })
        if sample_peak >= -0.15:
            expected_codes.append("SAMPLE_PEAK_NEAR_ZERO_CLIPPING_RISK")
        if sample_mean < -31:
            expected_codes.append("AVERAGE_AUDIO_VERY_QUIET_CHECK")
        _need(codes == expected_codes,
              "Warning flags and physical anomalies disagree")
        _need(len(hints) <= MAX_HINTS_PER_VIDEO,
              "Too many encoded media signals")
        hints.sort(key=lambda x: (x["start_seconds"], x["end_seconds"], x["kind"]))
        videos.append({
            "slot":slot,
            "sha256":digest,
            "duration_seconds":duration,
            "sample_peak_dbfs_not_true_peak":sample_peak,
            "sample_mean_dbfs_not_lufs":sample_mean,
            "warning_codes":codes,
            "seek_hints":hints,
        })
    return {
        "status":STATUS,
        "videos":videos,
        "no_warning_is_not_human_approval":True,
        "technical_signal_not_semantic_spinner_detector":True,
        "human_full_watches":0,
        "factual_and_rights_approvals":0,
        "youtube_release_authorized":False,
    }


def annotate_existing_owner_player(folder: Path) -> dict:
    """Atomically embed validated source-bound diagnostics in preexisting player."""
    _need(isinstance(folder, Path) and folder.is_dir() and not folder.is_symlink(),
          "Expected original owner-review directory")
    manifest = _read_json(folder/"REVIEW_ONLY_NO_PUBLISH.json", 24000)
    worksheet = _read_json(folder/"HUMAN_REVIEW_WORKSHEET_UNFILLED.json", 60000)
    diagnostics = _read_json(folder/REPORT_NAME, 120000)
    timeline = validate_signal_timeline(manifest, worksheet, diagnostics)
    for (_, filename, _), entry in zip(SLOT_NAMES, manifest["videos"]):
        video = folder/filename
        _need(video.is_file() and not video.is_symlink()
              and 300_000 <= video.stat().st_size <= 240_000_000
              and _sha_file(video) == entry["sha256"],
              "MP4 bytes changed after actual FFmpeg diagnostic")
    # Refuse a replaced/tampered HTML, or repeat updates after the user has
    # started making review notes. Keep owner review 100% human-initiated.
    portal = folder/PORTAL_FILE
    _need(portal.is_file() and not portal.is_symlink()
          and 4000 <= portal.stat().st_size <= 100000,
          "Missing original safe local review player")
    from autopilot.offline_review_portal_b4e7 import build_portal
    baseline = build_portal(manifest, worksheet)
    _need(portal.read_text(encoding="utf8") == baseline,
          "Player was modified or already annotated")
    output = build_portal(manifest, worksheet, diagnostics=diagnostics)
    _need(len(output.encode("utf8")) <= 160000,
          "Unbounded owner HTML review page")
    temp = portal.with_name(portal.name + ".tmp")
    _need(not temp.exists() and not temp.is_symlink(), "Stale HTML temp file")
    try:
        fd=os.open(temp, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf8") as stream:
            stream.write(output)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, portal)
        if os.name == "posix":
            directory = os.open(folder, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except OSError:
        raise TimelineRefused("Local HTML timeline write failed") from None
    finally:
        if temp.exists():
            temp.unlink()
    return {
        "status":STATUS,
        "video_count":3,
        "scene_count":17,
        "seekable_warning_count":sum(len(v["seek_hints"])
                                     for v in timeline["videos"]),
        "owner_review_completed":False,
        "fact_or_rights_clearance":False,
        "youtube_release_authorized":False,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description="Bind owner-only final MP4 signals to offline player")
    parser.add_argument("--review-dir", required=True, type=Path)
    args=parser.parse_args()
    _need(os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
          and os.environ.get("GITHUB_REF") == "refs/heads/main"
          and os.environ.get("FLOWMINUTE_EXPLICIT_REVIEW_OPT_IN") == "true"
          and args.review_dir == Path("/tmp/flowminute-b4e3-unapproved-owner-review"),
          "B4f5 only runs after explicit manual original owner artifact creation")
    result=annotate_existing_owner_player(args.review_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
