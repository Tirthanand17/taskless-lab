"""CLIVOX A5 private source revision preview (NEVER a source apply/release).

Turns a *freshly revalidated* private editorial correction CSV into a
scene-by-scene proposed spoken-text change preview. Each proposal remains
inside an explicit private JSON output. This module NEVER patches the public
catalog, creates audio/MP4/SRT, authenticates a human, signs a release, or
calls YouTube. A candidate is only a suggestion to an independent editor.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import re

from scripts.branch3_a5_cue_correction_intake import (
    compile_private_issue_plan, private_write_report
)
from scripts.branch3_a5_cue_review_worksheet import AUDIO, SRT, VIDEO, normalized
from scripts.branch3_original_arcade_qa import cue_samples_all_cues
from scripts.branch3_a6_original_handoff import CATALOG, CHANNEL, sha
from scripts.branch3_original_arcade_pilots import validate_catalog


class RevisionPreviewDenied(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RevisionPreviewDenied("CLIVOX_A5_REVISION_PREVIEW_DENIED_" + reason)


def readable_words(text: str) -> str:
    """Restrict proposed spoken dialogue to the exact renderer's safe chars."""
    require(type(text) is str and 0 < len(text) <= 185,
            "PROPOSED_TEXT_BOUNDS")
    # The real catalog validator accepts only visible 7-bit ASCII and
    # forbids URLs and escapes in original spoken words. Be as strict here.
    require(all(31 < ord(c) < 127 for c in text)
            and "\\" not in text and "http" not in text.lower()
            and not text.lstrip().startswith(("=", "+", "-", "@")),
            "UNSAFE_PROPOSED_SPEECH")
    candidate = normalized(text)
    require(4 <= len(candidate) <= 185, "NORMALIZED_SPEECH_LENGTH")
    return candidate


def predicted_cue_count(spoken: str) -> int:
    """Estimate the new *count* using existing 35-char/2-line draft logic.

    NOTE: This is NOT a prediction of exact timestamps or audible words.
    Those only exist after a new voice render and real-media verification.
    """
    words = spoken.split(" ")
    chunks: list[str] = []
    line: list[str] = []
    for word in words:
        combined = " ".join([*line, word])
        if len(combined) > 35 and line:
            chunks.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        chunks.append(" ".join(line))
    return math.ceil(len(chunks) / 2)


def compile_private_revision_preview(
    review_root: Path, *, selection: str,
    episode_id: str, edited_csv: Path
) -> dict:
    """Revalidate the exact A6 package through the private intake first."""
    issue_plan = compile_private_issue_plan(
        review_root, selection=selection,
        episode_id=episode_id, edited_csv=edited_csv
    )
    require(
        issue_plan["channel_id"] == CHANNEL
        and issue_plan["episode_id"] == episode_id
        and issue_plan["human_review_identity_authenticated"] is False
        and issue_plan["owner_review_completed"] is False
        and issue_plan["ready_to_upload"] is False
        and issue_plan["ready_to_schedule"] is False
        and issue_plan["ready_to_publish"] is False
        and issue_plan["actual_youtube_api_calls"] == 0,
        "EXACT_NONRELEASE_INTAKE_REQUIRED"
    )

    catalog = json.loads(CATALOG.read_text("utf-8"))
    episodes = validate_catalog(catalog)
    choices = [ep for ep in episodes if ep["id"] == episode_id]
    require(len(choices) == 1, "ORIGINAL_EPISODE")
    episode = choices[0]
    folder = review_root / episode_id
    srt = (folder / SRT).read_text("utf-8")
    points = cue_samples_all_cues(
        srt, episode["beats"], episode["duration_seconds"]
    )
    parts = re.split(r"\n\s*\n", srt.strip())
    require(len(parts) == len(points) == issue_plan["total_cue_rows"],
            "EXACT_CUE_COVERAGE")
    source_cues = [normalized(" ".join(part.splitlines()[2:]))
                   for part in parts]
    source_by_beat: dict[int, list[int]] = {}
    for cue_index, item in enumerate(points):
        source_by_beat.setdefault(item["beat_index"], []).append(cue_index)
    require(len(source_by_beat) == len(episode["beats"]),
            "EVERY_BEAT_MAPPED")

    issue_by_index = {}
    for issue in issue_plan["proposed_editorial_changes_private"]:
        cue_number = issue["cue_number"]
        require(type(cue_number) is int
                and 1 <= cue_number <= len(points)
                and cue_number not in issue_by_index,
                "DUPLICATE_OR_INVALID_ISSUE_CUE")
        index = cue_number - 1
        require(issue["source_caption"] == source_cues[index]
                and issue["scene_number"] == points[index]["beat_index"] + 1,
                "ISSUE_CHANGED_AFTER_INTAKE")
        issue_by_index[cue_number] = issue

    candidate_catalog = deepcopy(catalog)
    edited_episode = next(ep for ep in candidate_catalog["episodes"]
                          if ep["id"] == episode_id)
    pending_tasks = []
    rewrite_cues = []
    beat_diffs = []
    for beat_index, beat in enumerate(episode["beats"]):
        cue_indices = source_by_beat[beat_index]
        updated = [source_cues[i] for i in cue_indices]
        changed_cue_numbers = []
        for offset, cue_index in enumerate(cue_indices):
            issue = issue_by_index.get(cue_index + 1)
            if issue is None:
                continue
            replacement = issue["suggested_replacement_caption"].strip()
            # A subtitle presentation/timing issue is not evidence that the
            # synthesized voice/script must change. Even a supplied new
            # caption remains an explicit MANUAL task unless voice/words
            # were marked ISSUE. Do not silently desynchronize audio.
            voice_or_words = (
                "actual_words_and_pronunciation" in issue["issue_categories"]
            )
            if not replacement or not voice_or_words:
                pending_tasks.append({
                    "cue_number": cue_index + 1,
                    "scene_number": beat_index + 1,
                    "issue_categories": issue["issue_categories"],
                    "suggested_replacement_caption": issue[
                        "suggested_replacement_caption"
                    ],
                    "reviewer_issue_notes": issue["reviewer_issue_notes"],
                    "reason": (
                        "NO_REPLACEMENT_DIALOGUE_PROPOSED" if not replacement
                        else "SUBTITLE_OR_LAYOUT_ONLY_REQUIRES_MANUAL_EDITOR"
                    ),
                    "requires_human_editor": True,
                })
                continue
            candidate = readable_words(replacement)
            require(candidate != source_cues[cue_index],
                    "SAME_AS_SOURCE_CUE_" + str(cue_index + 1))
            updated[offset] = candidate
            changed_cue_numbers.append(cue_index + 1)
            rewrite_cues.append(cue_index + 1)

        if not changed_cue_numbers:
            continue
        original = normalized(beat["spoken"])
        require(original == normalized(" ".join(
            source_cues[i] for i in cue_indices
        )), "ORIGINAL_SCRIPT_SRT_CHANGED_" + str(beat_index))
        proposed = readable_words(" ".join(updated))
        require(proposed != original, "NO_ACTUAL_SCENE_CHANGE")
        edited_episode["beats"][beat_index]["spoken"] = proposed
        before_count = len(cue_indices)
        after_count = predicted_cue_count(proposed)
        beat_diffs.append({
            "scene_number": beat_index + 1,
            "scene_start_s": beat["start_s"],
            "scene_end_s": beat["end_s"],
            "changed_cue_numbers": changed_cue_numbers,
            "original_spoken": original,
            "candidate_spoken_not_applied": proposed,
            "original_scene_cue_count": before_count,
            "predicted_rewrapped_cue_count_not_real_audio": after_count,
            "candidate_may_change_cue_index_and_all_timings": True,
            "human_editor_must_accept_or_rewrite": True,
            "fresh_voice_srt_mp4_a5_a6_verification_required": True,
        })

    # Even the in-memory hypothetical candidate MUST satisfy full original
    # catalog schema including original-media-only and all false rights
    # and YouTube approvals. The actual disk catalog is never written.
    try:
        validate_catalog(candidate_catalog)
    except (TypeError, ValueError, KeyError):
        raise RevisionPreviewDenied(
            "CLIVOX_A5_REVISION_PREVIEW_DENIED_CANDIDATE_CATALOG_VALIDATION"
        ) from None

    # Reject a modified exact-video review package even if tampered after
    # the previous comprehensive A5/A6 read-only verification.
    for file_name, expected_digest in (
        (VIDEO, issue_plan["exact_video_sha256"]),
        (AUDIO, issue_plan["exact_audio_sha256"]),
        (SRT, issue_plan["exact_srt_sha256"]),
    ):
        source = folder / file_name
        require(source.is_file() and not source.is_symlink()
                and sha(source) == expected_digest,
                "EXACT_MEDIA_CHANGED_DURING_PREVIEW_" + file_name)

    require(len(rewrite_cues) + len(pending_tasks)
            == issue_plan["issue_rows"], "EVERY_ISSUE_ACCOUNTED")
    return {
        "schema_version": 1,
        "domain": "CLIVOX-A5-PRIVATE-SCENE-REVISION-PREVIEW-NEVER-APPLY",
        "channel_id": CHANNEL,
        "episode_id": episode_id,
        "source_catalog_sha256": sha(CATALOG),
        "exact_review_packet_sha256": issue_plan[
            "exact_review_packet_sha256"
        ],
        "exact_review_video_sha256": issue_plan["exact_video_sha256"],
        "exact_review_audio_sha256": issue_plan["exact_audio_sha256"],
        "exact_review_srt_sha256": issue_plan["exact_srt_sha256"],
        "edited_correction_csv_sha256": issue_plan[
            "edited_correction_csv_sha256"
        ],
        "source_cue_count": len(points),
        "reported_issue_rows_untrusted_as_owner_identity":
            issue_plan["issue_rows"],
        "candidate_spoken_rewrites_count": len(rewrite_cues),
        "manual_editor_action_rows": len(pending_tasks),
        "pending_or_incomplete_rows": issue_plan[
            "pending_or_incomplete_rows"
        ],
        "candidate_scene_text_diffs_not_applied": beat_diffs,
        "private_manual_editor_tasks": pending_tasks,
        "original_source_catalog_modified": False,
        "original_mp4_wav_srt_modified": False,
        "candidate_catalog_saved_to_public_repo": False,
        "automatic_speech_or_srt_regeneration_performed": False,
        "actual_word_level_alignment_verified": False,
        "human_reviewer_identity_authenticated": False,
        "owner_review_completed": False,
        "commercial_tool_or_audio_rights_approved": False,
        "a6_release_signed": False,
        "ready_to_upload": False,
        "ready_to_schedule": False,
        "ready_to_publish": False,
        "actual_youtube_api_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--selection", choices=("one", "all"), default="all")
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--edited-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compile_private_revision_preview(
            args.review_root, selection=args.selection,
            episode_id=args.episode_id, edited_csv=args.edited_csv
        )
        # Never print or upload the actual private reviewer notes or new
        # proposed spoken dialogue. Write once to explicitly private path.
        private_write_report(args.output, report)
    except (ValueError, TypeError, KeyError, OSError, UnicodeError):
        raise SystemExit(
            "CLIVOX_A5_PRIVATE_REVISION_PREVIEW_BLOCKED_NO_APPLY_NO_UPLOAD"
        ) from None
    print(json.dumps({
        "episode_id": report["episode_id"],
        "candidate_spoken_rewrites_count":
            report["candidate_spoken_rewrites_count"],
        "manual_editor_action_rows":
            report["manual_editor_action_rows"],
        "original_source_catalog_modified": False,
        "original_mp4_wav_srt_modified": False,
        "owner_review_completed": False,
        "ready_to_upload": False,
        "ready_to_publish": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
