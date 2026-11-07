"""B4e6 validate a human-edited rehearsal worksheet against exact MP4 manifest.

This is NOT an independent eyewitness, news fact check, rights signoff, or
permission to publish. No network, credentials, account access, or uploads.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from autopilot.manual_rehearsal_review_export_b4e3 import EXPORT_STATUS, SLOT_NAMES

SCHEMA = "B4E5_SHA_BOUND_BLANK_HUMAN_QA_WORKSHEET_V1"
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
TIMECODE = re.compile(r"([0-9]{2}):([0-9]{2})\Z")
ALLOWED = {"PASS", "FAIL", "NOT_REVIEWED"}
CHECKS = (
    "opening_hook_under_2_seconds",
    "every_scene_unique_and_no_rotating_spinner",
    "voice_clear_pronunciation_and_no_clipping",
    "caption_readability_mobile_safe_area_and_spelling",
    "audio_caption_sync_and_sound_effect_balance",
    "original_visual_labels_legible_and_not_cropped",
    "narrative_payoff_and_ending",
    "visual_audio_model_and_music_rights_verified",
    "factual_claims_primary_source_verified",
    "human_listened_and_watched_entire_clip",
)
MAX_DOC_BYTES = 60000


class ReviewValidationError(ValueError):
    """No reliable review evidence: stop and do not imply owner approval."""


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ReviewValidationError(message)


def _timecode(value: object, duration: float) -> bool:
    if type(value) is not str:
        return False
    found = TIMECODE.fullmatch(value)
    return found is not None and int(found[2]) < 60 and (
        60 * int(found[1]) + int(found[2]) <= duration + 1
    )


def _read(path: Path) -> dict:
    _require(not path.is_symlink() and path.is_file(), "Missing or symlinked JSON")
    _require(2 <= path.stat().st_size <= MAX_DOC_BYTES, "Invalid JSON size")
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReviewValidationError("Unreadable JSON") from error
    _require(type(result) is dict, "Expected JSON object")
    return result


def inspect(manifest: dict, worksheet: dict) -> dict:
    _require(type(manifest) is dict and manifest.get("status") == EXPORT_STATUS,
             "Not the official review-only export manifest")
    _require(manifest.get("publishing_authorized") is False and
             manifest.get("youtube_releases") == 0 and
             manifest.get("rights_and_owner_approvals") == 0 and
             manifest.get("factual_news_claims_reviewed") == 0,
             "Manifest attempts to imply rights or publishing approval")
    _require(type(manifest.get("videos")) is list and len(manifest["videos"]) == 3,
             "Expected 3 original MP4 manifest entries")
    _require(type(worksheet) is dict and worksheet.get("schema") == SCHEMA,
             "Unexpected worksheet version")
    for name, expected in (
        ("synthetic_educational_media_only", True),
        ("human_review_completed", False),
        ("factual_news_approved", False),
        ("rights_approved", False),
        ("youtube_publish_authorized", False),
    ):
        _require(worksheet.get(name) is expected, "Unsafe worksheet release flag: " + name)
    _require(type(worksheet.get("videos")) is list and len(worksheet["videos"]) == 3,
             "Expected exactly 3 worksheet videos")

    passed = failed = pending = 0
    notes = []
    reviewed_scenes = 0
    for (slot, filename, scene_count), video, entry in zip(
            SLOT_NAMES, worksheet["videos"], manifest["videos"]):
        _require(type(video) is dict and type(entry) is dict,
                 "Video and manifest entries must be objects")
        digest = entry.get("sha256")
        seconds = entry.get("measured_audio_seconds")
        _require(entry.get("slot") == slot and entry.get("file") == filename and
                 type(digest) is str and DIGEST.fullmatch(digest) is not None and
                 type(seconds) in (int, float) and 20 <= seconds <= 340 and
                 entry.get("original_voiced_scene_count") == scene_count and
                 entry.get("all_rights_and_fact_approvals") is False and
                 entry.get("youtube_upload_authorized") is False,
                 "Invalid or spoofed source media manifest")
        _require(video.get("slot") == slot and video.get("filename") == filename and
                 video.get("sha256") == digest and
                 type(video.get("duration_seconds_measured_pcm")) in (float, int) and
                 video["duration_seconds_measured_pcm"] == seconds,
                 "Worksheet not bound to source MP4 hash/duration")
        checks = video.get("checks")
        _require(type(checks) is dict and set(checks) == set(CHECKS),
                 "Exactly ten review checks are required")
        _require(type(video.get("scenes")) is list and
                 len(video["scenes"]) == scene_count,
                 "Incorrect canonical scene count")
        check_statuses = []
        for key in CHECKS:
            state = checks[key]
            _require(type(state) is str and state in ALLOWED, "Invalid review check state")
            check_statuses.append(state)
            if state == "FAIL":
                notes.append({"slot": slot, "kind": "check", "key": key})
            if state == "PASS":
                passed += 1
            elif state == "FAIL":
                failed += 1
            else:
                pending += 1

        for number, scene in enumerate(video["scenes"], start=1):
            _require(type(scene) is dict and scene.get("scene_number") == number,
                     "Missing, reordered or duplicated scene")
            state = scene.get("review_status")
            timestamp = scene.get("timecode_mm_ss")
            defect = scene.get("defect_notes")
            _require(type(state) is str and state in ALLOWED,
                     "Invalid scene assessment")
            _require(defect is None or (type(defect) is str and
                     1 <= len(defect.strip()) <= 500), "Invalid scene defect note")
            if state == "NOT_REVIEWED":
                _require(timestamp is None and defect is None,
                         "Unreviewed scenes must not claim inspection evidence")
                pending += 1
            else:
                _require(_timecode(timestamp, seconds),
                         "Reviewed scene needs valid in-bounds mm:ss")
                if state == "FAIL":
                    _require(type(defect) is str and len(defect.strip()) >= 8,
                             "Failed scene needs an actionable timestamped defect")
                    failed += 1
                    notes.append({"slot": slot, "kind": "scene", "scene": number,
                                  "timecode_mm_ss": timestamp})
                else:
                    passed += 1
                reviewed_scenes += 1
        decision = video.get("overall_human_decision")
        _require(decision in ALLOWED and type(decision) is str,
                 "Invalid overall human decision")
        if decision == "PASS":
            _require(all(x == "PASS" for x in check_statuses) and
                     all(x.get("review_status") == "PASS"
                         for x in video["scenes"]),
                     "Overall PASS requires every check and scene PASS")
        if decision == "FAIL":
            _require("FAIL" in check_statuses or any(
                x.get("review_status") == "FAIL" for x in video["scenes"]),
                "Overall FAIL requires a failing check or scene")
        if decision == "NOT_REVIEWED":
            _require(not all(x == "PASS" for x in check_statuses) or
                     not all(x.get("review_status") == "PASS"
                             for x in video["scenes"]),
                     "Complete self-reported PASS needs an explicit decision")
    # This is only a structural validation of self-reported watch notes.
    return {
        "status": "B4E6_HUMAN_WORKSHEET_CONSISTENCY_ONLY_NOT_RELEASE_AUTHORITY",
        "scene_count": 17,
        "self_reported_reviewed_scenes": reviewed_scenes,
        "individual_checks_pass": passed,
        "individual_checks_fail": failed,
        "individual_checks_not_reviewed": pending,
        "needs_defect_followup_count": len(notes),
        "defect_locations_without_private_notes": notes,
        "independent_human_observation_verified": False,
        "copyright_and_factual_source_verified": False,
        "youtube_release_authorized": False,
        "youtube_releases": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--worksheet", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(_read(args.manifest), _read(args.worksheet))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
