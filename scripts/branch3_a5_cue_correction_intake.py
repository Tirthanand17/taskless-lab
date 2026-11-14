"""CLIVOX A5: fail-closed PRIVATE editorial correction intake, never release.

Consumes a reviewer-edited copy of a SHA-bound cue worksheet extracted from
a source-free CLIVOX GitHub review artifact. Independently rechecks original
A6 exact-media SHA / unsigned checklist before comparing *every immutable*
cue, time, scene and draft caption to the actual SRT and authored screenplay.

Emits an issue PLAN ONLY to an explicitly chosen local/private path. It does
not edit video/script/SRT, auto-mark human review, sign, authorize Google,
upload, schedule or publish. Review notes MUST NOT enter public CI or repos.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re

from scripts.branch3_a5_cue_review_worksheet import (
    AUDIO, FIELDS, SRT, VIDEO, WORKSHEET, normalized, safe_csv_cell, stamp
)
from scripts.branch3_a5_speech_boundaries import parse_srt_intervals
from scripts.branch3_original_arcade_qa import cue_samples_all_cues
from scripts.branch3_a6_original_handoff import (
    CATALOG, CHANNEL, PACKET_NAME, ROOT, read_json, sha
)
from scripts.branch3_a6_original_review_signature import verify_unsigned_requests
from scripts.branch3_original_arcade_pilots import validate_catalog

PURPOSE = "EDITORIAL_CORRECTION_ONLY_NOT_APPROVAL"
STATUS = frozenset(("NOT_REVIEWED", "OK", "ISSUE"))
DECISION = frozenset(("NOT_REVIEWED", "YES", "NO"))
ASSESSMENTS = (
    "actual_words_and_pronunciation",
    "subtitle_timing",
    "caption_visual_readability",
)


class CorrectionIntakeDenied(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise CorrectionIntakeDenied("CLIVOX_A5_CORRECTION_INTAKE_DENIED_" + code)


def private_path(path: Path, *, must_exist: bool) -> None:
    require(isinstance(path, Path) and path.is_absolute()
            and path != ROOT and ROOT not in path.parents,
            "OUTSIDE_PUBLIC_REPO")
    real = path.resolve(strict=False)
    require(real != ROOT and ROOT not in real.parents
            and not path.is_symlink(), "SYMLINK_OR_REPO")
    if must_exist:
        require(path.is_file() and 0 < path.stat().st_size <= 150_000,
                "EDITED_CSV_FILE")


def csv_rows(path: Path) -> list[dict[str, str]]:
    private_path(path, must_exist=True)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            require(tuple(reader.fieldnames or ()) == FIELDS, "CSV_HEADER")
            rows = list(reader)
    except (csv.Error, UnicodeError, OSError):
        raise CorrectionIntakeDenied("CLIVOX_A5_CORRECTION_INTAKE_DENIED_CSV_FORMAT") from None
    require(1 <= len(rows) <= 70, "CSV_ROW_COUNT")
    for row in rows:
        require(set(row) == set(FIELDS)
                and all(type(row[k]) is str and len(row[k]) <= 2000
                        and "\x00" not in row[k] for k in FIELDS),
                "CSV_CELL_SHAPE")
    return rows


def source_rows(episode: dict, packet: dict, srt_text: str) -> list[dict[str, str]]:
    """Re-derive each identity field from actual SRT + original screenplay."""
    cues = cue_samples_all_cues(
        srt_text, episode["beats"], episode["duration_seconds"]
    )
    times = parse_srt_intervals(srt_text)
    chunks = re.split(r"\n\s*\n", srt_text.strip())
    require(len(cues) == len(times) == len(chunks), "SOURCE_CUE_COUNT")
    scene_text: dict[int, list[str]] = {}
    facts = []
    for index, (cue, (start, end), chunk) in enumerate(
        zip(cues, times, chunks, strict=True)
    ):
        lines = chunk.splitlines()
        require(len(lines) in (3, 4) and lines[0] == str(index + 1),
                "SOURCE_CUE_FORMAT")
        spoken = normalized(" ".join(lines[2:]))
        scene = cue["beat_index"]
        scene_text.setdefault(scene, []).append(spoken)
        facts.append({
            "purpose": PURPOSE,
            "episode_id": episode["id"],
            "exact_video_sha256": packet["exact_video_sha256"],
            "exact_audio_sha256": packet["exact_audio_sha256"],
            "exact_srt_sha256": packet["exact_captions_sha256"],
            "cue_number": str(index + 1),
            "scene_number": str(scene + 1),
            "cue_start": stamp(start),
            "cue_end": stamp(end),
            "draft_caption": safe_csv_cell(spoken),
        })
    require(len(scene_text) == len(episode["beats"]),
            "SCENE_COVERAGE")
    for index, beat in enumerate(episode["beats"]):
        require(normalized(" ".join(scene_text[index])) ==
                normalized(beat["spoken"]), "SOURCE_SCRIPT_DIFFERS_" + str(index))
    return facts


def compile_private_issue_plan(
    review_root: Path, *, selection: str, episode_id: str,
    edited_csv: Path
) -> dict:
    """Read and verify only; never mutate source files or claim approval."""
    require(type(selection) is str and selection in ("all", "one")
            and isinstance(review_root, Path) and review_root.is_absolute()
            and review_root.is_dir() and not review_root.is_symlink(),
            "REVIEW_ROOT")
    real_root = review_root.resolve(strict=True)
    require(real_root != ROOT and ROOT not in real_root.parents,
            "PUBLIC_REPO_ROOT")
    private_path(edited_csv, must_exist=True)
    catalog = validate_catalog(json.loads(CATALOG.read_text("utf-8")))
    selected = catalog if selection == "all" else catalog[:1]
    matched = [ep for ep in selected if ep["id"] == episode_id]
    require(len(matched) == 1, "EPISODE_NOT_IN_VERIFIED_SELECTION")
    episode = matched[0]
    folder = review_root / episode_id
    require(folder.is_dir() and not folder.is_symlink()
            and folder.resolve(strict=True).parent == real_root,
            "EPISODE_DIRECTORY")
    baseline = folder / WORKSHEET
    require(edited_csv.resolve(strict=True) != baseline.resolve(strict=True),
            "REQUIRES_SEPARATE_EDITED_COPY")

    # The real verification re-runs FFprobe/A5 and A6 file hashes and checks
    # all owner review requests are byte-for-byte unsigned and still false.
    verified = verify_unsigned_requests(review_root, selection=selection)
    require(verified.get("all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed") is True
            and verified.get("unsigned_checklist_files_matched_exact_media") is True
            and verified.get("actual_human_video_approvals_verified") == 0
            and verified.get("youtube_upload_authorized") is False,
            "A6_MEDIA_NOT_VERIFIED")
    packet = read_json(folder / PACKET_NAME)
    require(packet.get("channel_id") == CHANNEL
            and packet.get("episode_id") == episode_id
            and packet.get("owner_detached_signature_present") is False
            and packet.get("youtube_upload_authorized") is False
            and packet.get("youtube_schedule_authorized") is False
            and packet.get("youtube_publish_authorized") is False,
            "WRONG_PACKET_IDENTITY_OR_APPROVAL")

    # Re-derive immutable columns from unmodified SHA-bound SRT and verify
    # both baseline and edited copy, so even a forged baseline cannot make
    # wrong scene indices, times, or transcription trusted.
    captions = (folder / SRT).read_text("utf-8")
    facts = source_rows(episode, packet, captions)
    previous = csv_rows(baseline)
    proposed = csv_rows(edited_csv)
    require(len(previous) == len(proposed) == len(facts),
            "ALL_CUES_REQUIRED")
    issues = []
    pending = 0
    reviewed_rows = 0
    for index, (base, edited, expected) in enumerate(
        zip(previous, proposed, facts, strict=True)
    ):
        for col, value in expected.items():
            require(base[col] == value and edited[col] == value,
                    "IMMUTABLE_CUE_CHANGED_" + str(index) + "_" + col)
        require(all(base[col] == "NOT_REVIEWED"
                    for col in (*ASSESSMENTS, "correction_required"))
                and base["suggested_replacement_caption"] == ""
                and base["reviewer_issue_notes"] == "",
                "BASELINE_NOT_UNREVIEWED")
        states = [edited[col] for col in ASSESSMENTS]
        decision = edited["correction_required"]
        suggestion = edited["suggested_replacement_caption"]
        notes = edited["reviewer_issue_notes"]
        require(all(status in STATUS for status in states)
                and decision in DECISION, "INVALID_REVIEW_VALUE_" + str(index))
        # Never silently convert a partial form into a claim that review
        # occurred. A row marked NO must have three explicit OK assessments.
        if decision == "NOT_REVIEWED":
            require(states == ["NOT_REVIEWED"] * 3
                    and suggestion == "" and notes == "",
                    "PARTIAL_ROW_REQUIRES_DECISION_" + str(index))
            pending += 1
            continue
        if decision == "NO":
            require(states == ["OK"] * 3 and suggestion == "",
                    "NEGATIVE_DECISION_REQUIRES_ALL_OK_" + str(index))
        else:
            require("ISSUE" in states and
                    (suggestion.strip() != "" or notes.strip() != ""),
                    "POSITIVE_DECISION_REQUIRES_ISSUE_NOTES_" + str(index))
        # Literal status is only a self-reported spreadsheet value; it
        # never authenticates who listened or reviews final media.
        if "NOT_REVIEWED" in states:
            pending += 1
        else:
            reviewed_rows += 1
        if decision == "YES":
            issues.append({
                "cue_number": index + 1,
                "scene_number": int(expected["scene_number"]),
                "cue_start": expected["cue_start"],
                "cue_end": expected["cue_end"],
                "source_caption": expected["draft_caption"],
                "issue_categories": [
                    key for key in ASSESSMENTS if edited[key] == "ISSUE"
                ],
                "suggested_replacement_caption": suggestion,
                "reviewer_issue_notes": notes,
                "requires_source_script_voice_srt_mp4_regeneration": True,
            })
    result = {
        "schema_version": 1,
        "domain": "CLIVOX-A5-PRIVATE-EDITORIAL-CORRECTION-PLAN-NOT-RELEASE",
        "channel_id": CHANNEL,
        "episode_id": episode_id,
        "exact_review_packet_sha256": packet["packet_sha256"],
        "exact_video_sha256": packet["exact_video_sha256"],
        "exact_audio_sha256": packet["exact_audio_sha256"],
        "exact_srt_sha256": packet["exact_captions_sha256"],
        "edited_correction_csv_sha256": sha(edited_csv),
        "total_cue_rows": len(facts),
        "self_reported_filled_rows_not_authenticated": reviewed_rows,
        "pending_or_incomplete_rows": pending,
        "issue_rows": len(issues),
        "proposed_editorial_changes_private": issues,
        "no_source_media_or_repository_files_modified": True,
        "human_review_identity_authenticated": False,
        "actual_spoken_words_verified_by_machine": False,
        "this_is_not_an_a6_owner_attestation": True,
        "owner_review_completed": False,
        "rights_licenses_validated": False,
        "ready_to_upload": False,
        "ready_to_schedule": False,
        "ready_to_publish": False,
        "actual_youtube_api_calls": 0,
    }
    return result


def private_write_report(target: Path, report: dict) -> None:
    require(isinstance(target, Path) and target.suffix == ".json",
            "JSON_DESTINATION")
    private_path(target, must_exist=False)
    parent = target.parent
    require(parent.is_dir() and not parent.is_symlink()
            and ROOT not in parent.resolve().parents
            and parent.resolve() != ROOT,
            "PRIVATE_DESTINATION_DIRECTORY")
    require(not target.exists() and not target.is_symlink(),
            "NO_OVERWRITE_EXISTING_REPORT")
    body = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    require(100 < len(body.encode("utf-8")) <= 80_000, "ISSUE_PLAN_BOUND")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                 | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--selection", choices=("one", "all"), default="all")
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--edited-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compile_private_issue_plan(
            args.review_root, selection=args.selection,
            episode_id=args.episode_id, edited_csv=args.edited_csv
        )
        private_write_report(args.output, report)
    except (ValueError, KeyError, TypeError, OSError, UnicodeError,
            json.JSONDecodeError):
        raise SystemExit(
            "CLIVOX_A5_EDITORIAL_CORRECTION_INTAKE_BLOCKED_NO_UPLOAD"
        ) from None
    # Never print raw reviewer notes or replacement scripts into GitHub logs.
    print(json.dumps({
        "episode_id": report["episode_id"],
        "total_cue_rows": report["total_cue_rows"],
        "pending_or_incomplete_rows": report["pending_or_incomplete_rows"],
        "issue_rows": report["issue_rows"],
        "report_written_to_private_explicit_destination": True,
        "actual_human_review_authenticated": False,
        "youtube_upload_authorized": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
