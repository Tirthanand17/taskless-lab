"""CLIVOX A5 quarantined, source-free revision RENDER rehearsal.

The input is a private human-editor issue CSV, verified against unchanged
original full review MP4/WAV/SRT and A6 unsigned packet. Proposed dialogue is
rendered only IN MEMORY as an altered episode. The public screenplay/catalog
is never written; fresh media, QA and a non-authorizing report are written
only into a new private disposable directory. NOT a production master, an
A6 release, human acceptance, commercial license or YouTube upload.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from scripts.branch3_a5_private_revision_preview import (
    compile_private_revision_preview
)
from scripts.branch3_a5_cue_correction_intake import private_write_report
from scripts.branch3_a5_cue_review_worksheet import AUDIO, SRT, VIDEO
from scripts.branch3_original_arcade_pilots import (
    render_episode, validate_catalog
)
from scripts.branch3_original_arcade_qa import (
    probe, validate_episode_report
)
from scripts.branch3_a6_original_handoff import (
    CATALOG, ROOT, sha, digest
)


class RevisionSandboxDenied(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RevisionSandboxDenied(
            "CLIVOX_A5_QUARANTINED_REVISION_DENIED_" + reason
        )


def private_location(root: Path, forbidden: Path) -> None:
    require(isinstance(root, Path) and root.is_absolute()
            and root.is_dir() and not root.is_symlink()
            and root != ROOT and ROOT not in root.parents,
            "PRIVATE_ROOT")
    real = root.resolve(strict=True)
    forbidden_real = forbidden.resolve(strict=True)
    require(real != ROOT and ROOT not in real.parents
            and real != forbidden_real
            and real not in forbidden_real.parents
            and forbidden_real not in real.parents,
            "PUBLIC_OR_REVIEW_TREE_OVERLAP")


def stage_candidate_episode(
    preview: dict, *, episode_id: str, source: dict
) -> dict:
    """Apply only deterministic previewed spoken diffs to an in-memory copy."""
    require(type(preview) is dict
            and preview.get("episode_id") == episode_id
            and preview.get("domain") ==
            "CLIVOX-A5-PRIVATE-SCENE-REVISION-PREVIEW-NEVER-APPLY"
            and preview.get("source_catalog_sha256") == sha(CATALOG)
            and preview.get("candidate_spoken_rewrites_count", 0) >= 1
            and preview.get("original_source_catalog_modified") is False
            and preview.get("original_mp4_wav_srt_modified") is False
            and preview.get("human_reviewer_identity_authenticated") is False
            and preview.get("owner_review_completed") is False
            and preview.get("ready_to_upload") is False
            and preview.get("ready_to_schedule") is False
            and preview.get("ready_to_publish") is False
            and preview.get("actual_youtube_api_calls") == 0,
            "NONAUTHORIZING_SOURCE_PREVIEW_REQUIRED")
    require(type(source) is dict, "SOURCE_TYPE")
    proposed = deepcopy(source)
    original_eps = validate_catalog(source)
    revised_eps = validate_catalog(proposed)
    original = next((e for e in original_eps if e["id"] == episode_id), None)
    edited = next((e for e in revised_eps if e["id"] == episode_id), None)
    require(original is not None and edited is not None, "EPISODE_ID")
    diffs = preview.get("candidate_scene_text_diffs_not_applied")
    require(type(diffs) is list and 1 <= len(diffs) <= len(edited["beats"]),
            "SCENE_DIFFS")
    seen = set()
    count = 0
    for diff in diffs:
        require(type(diff) is dict
                and type(diff.get("scene_number")) is int
                and 1 <= diff["scene_number"] <= len(edited["beats"])
                and diff["scene_number"] not in seen
                and diff.get("fresh_voice_srt_mp4_a5_a6_verification_required")
                    is True
                and diff.get("human_editor_must_accept_or_rewrite") is True,
                "INVALID_SCENE_DIFF")
        index = diff["scene_number"] - 1
        seen.add(diff["scene_number"])
        before = original["beats"][index]["spoken"]
        after = diff.get("candidate_spoken_not_applied")
        require(diff.get("original_spoken") == before
                and type(after) is str and after != before
                and type(diff.get("changed_cue_numbers")) is list
                and len(diff["changed_cue_numbers"]) >= 1,
                "SOURCE_DIFF_IDENTITY")
        edited["beats"][index]["spoken"] = after
        count += len(diff["changed_cue_numbers"])
    require(count == preview["candidate_spoken_rewrites_count"],
            "REWRITE_CUE_COUNT")
    # Whole catalog is schema-validated, not just the changed fields.
    validate_catalog(proposed)
    for existing, candidate in zip(original_eps, revised_eps, strict=True):
        for i, (old, new) in enumerate(
            zip(existing["beats"], candidate["beats"], strict=True)
        ):
            if existing["id"] == episode_id and i + 1 in seen:
                require(
                    all(old[k] == new[k] for k in old if k != "spoken"),
                    "CHANGED_NON_SPEECH_FIELDS"
                )
            else:
                require(old == new, "CHANGED_UNSELECTED_BEAT")
    return edited


def rehearse_private_revision(
    review_root: Path, *, selection: str, episode_id: str,
    edited_csv: Path, output_root: Path, mode: str = "preview"
) -> dict:
    require(mode in ("preview", "full"), "RENDER_MODE")
    # Entire exact-file A6 package is authenticated cryptographically as
    # unchanged bytes (NOT authenticated as a human review or rights grant).
    preview = compile_private_revision_preview(
        review_root, selection=selection,
        episode_id=episode_id, edited_csv=edited_csv
    )
    private_location(output_root, review_root)
    require(not list(output_root.iterdir()), "EMPTY_NEW_OUTPUT_ROOT_REQUIRED")
    original_sha = sha(CATALOG)
    source = json.loads(CATALOG.read_text("utf-8"))
    candidate_ep = stage_candidate_episode(
        preview, episode_id=episode_id, source=source
    )
    original_episode = next(ep for ep in validate_catalog(source)
                            if ep["id"] == episode_id)
    require(candidate_ep != original_episode, "UNMODIFIED_CANDIDATE")
    prior = review_root / episode_id
    require(prior.is_dir() and not prior.is_symlink(), "PRIOR_EPISODE")
    original_hashes = {
        key: sha(prior / key) for key in (VIDEO, AUDIO, SRT)
    }
    require(original_hashes == {
        VIDEO: preview["exact_review_video_sha256"],
        AUDIO: preview["exact_review_audio_sha256"],
        SRT: preview["exact_review_srt_sha256"],
    }, "SOURCE_MEDIA_CHANGED_AFTER_PREVIEW")
    # Never reuse original media or its A6 release handoff. Only synthetic
    # draft output in a fresh private root.
    sandbox_dir = output_root / episode_id
    sandbox_dir.mkdir(mode=0o700, exist_ok=False)
    manifest = render_episode(candidate_ep, sandbox_dir, mode)
    video = sandbox_dir / VIDEO
    wav = sandbox_dir / AUDIO
    subtitle = sandbox_dir / SRT
    report = validate_episode_report(
        candidate_ep, manifest, probe(video), subtitle.read_text("utf-8"),
        video=video, audio=wav, captions=subtitle
    )
    captions = report["decoded_actual_frame_caption_safezone_qa"]
    speech = report["independent_mixed_audio_vs_srt_speech_boundary_qa"]
    cue_total = speech["draft_caption_cue_count"]
    require(
        report["actual_ffprobe_checks_passed"] is True
        and report["youtube_upload_authorized"] is False
        and report["youtube_schedule_authorized"] is False
        and report["youtube_publish_authorized"] is False
        and captions["every_draft_caption_cue_visible_in_safe_zone"] is True
        and captions["actual_encoded_frames_checked"] == cue_total
        and captions["draft_caption_cue_count"] == cue_total
        and len(captions["per_cue_samples"]) == cue_total
        and speech["all_draft_cues_have_recovered_speech_activity"] is True
        and len(speech["per_cue"]) == cue_total
        and speech["phoneme_forced_alignment_or_asr_performed"] is False,
        "ALL_NEW_REAL_MEDIA_QA_REQUIRED"
    )
    require(sha(CATALOG) == original_sha
            and {key: sha(prior / key) for key in original_hashes}
                == original_hashes,
            "SOURCE_REVIEW_MEDIA_OR_CATALOG_WAS_MODIFIED")
    require(sha(video) != original_hashes[VIDEO]
            and sha(wav) != original_hashes[AUDIO]
            and sha(subtitle) != original_hashes[SRT],
            "NEW_MEDIA_NOT_DISTINCT")
    # This is a fresh QA report, NOT a new A6 owner packet and never a
    # signed or review-accepted release. The original accepted owner
    # master is untouched.
    (sandbox_dir / "technical-review-qa.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    result = {
        "schema_version": 1,
        "domain": "CLIVOX-A5-PRIVATE-SYNTHETIC-REVISION-SANDBOX-NO-RELEASE",
        "episode_id": episode_id,
        "render_mode": mode,
        "original_catalog_sha256": original_sha,
        "candidate_in_memory_episode_sha256": digest(candidate_ep),
        "original_review_packet_sha256": preview[
            "exact_review_packet_sha256"
        ],
        "original_video_sha256": original_hashes[VIDEO],
        "candidate_video_sha256": sha(video),
        "candidate_audio_sha256": sha(wav),
        "candidate_subtitle_sha256": sha(subtitle),
        "edited_correction_csv_sha256": preview[
            "edited_correction_csv_sha256"
        ],
        "candidate_scene_changes": len(
            preview["candidate_scene_text_diffs_not_applied"]
        ),
        "candidate_spoken_rewrites_count": preview[
            "candidate_spoken_rewrites_count"
        ],
        "pending_or_incomplete_original_review_rows": preview[
            "pending_or_incomplete_rows"
        ],
        "new_real_encoded_subtitle_cues_checked": cue_total,
        "new_real_mixed_audio_cues_checked": cue_total,
        "full_independent_candidate_technical_qa_passed": True,
        "old_review_source_and_catalog_unchanged": True,
        "no_owner_a6_reuse_or_release_packet_created": True,
        "candidate_sandbox_is_not_release_master": True,
        "human_editorial_acceptance_verified": False,
        "original_signed_release_exists": False,
        "third_party_rights_or_licenses_verified": False,
        "human_voice_words_or_phoneme_alignment_verified": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "actual_google_api_calls": 0,
    }
    require(not (sandbox_dir / "owner-handoff-quarantined.json").exists()
            and not (sandbox_dir / "owner-editorial-review-UNSIGNED.json").exists(),
            "NO_A6_OWNER_PACKET_IN_SANDBOX")
    private_write_report(output_root / "PRIVATE-SANDBOX-TECHNICAL-REPORT.json",
                         result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--selection", choices=("one", "all"), default="all")
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--edited-csv", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("preview", "full"), default="preview")
    args = parser.parse_args()
    try:
        report = rehearse_private_revision(
            args.review_root, selection=args.selection,
            episode_id=args.episode_id, edited_csv=args.edited_csv,
            output_root=args.output_root, mode=args.mode
        )
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        raise SystemExit(
            "CLIVOX_A5_SANDBOX_DENIED_NO_SOURCE_CHANGE_NO_UPLOAD"
        ) from None
    # Never print reviewer text, revised dialogue or original media paths.
    print(json.dumps({
        "episode_id": report["episode_id"],
        "new_real_encoded_subtitle_cues_checked":
            report["new_real_encoded_subtitle_cues_checked"],
        "new_real_mixed_audio_cues_checked":
            report["new_real_mixed_audio_cues_checked"],
        "candidate_sandbox_is_not_release_master": True,
        "human_editorial_acceptance_verified": False,
        "youtube_upload_authorized": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
