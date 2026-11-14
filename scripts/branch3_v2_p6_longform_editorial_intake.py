"""CLIVOX V2 P5->P6: source-free long-form candidate editorial review intake.

Only previously computed local signal measurements and deterministic, unapproved
candidate windows. Recomputes the plan, rejects tampering, and asks for real
rights/context/editor checks. Does not claim real footage, ASR, quote accuracy,
human authorization, creator consent, media availability or viral probability.
"""
from __future__ import annotations

import argparse
import json

from scripts.branch3_v2_p5_longform_local_signal_planner import (
    CHANNEL, LongformDenied, plan_longform_candidates, synthetic_demo,
)

STAGE = "CLIVOX_V2_P6_LONGFORM_UNREVIEWED_EDITORIAL_INTAKE_ONLY"
HOLD = "NO_VERIFIED_SOURCE_LICENSE_CONTEXT_OR_HUMAN_EDITOR_SELECTION"
CHECKS = (
    "verify_actual_master_identity_and_source_sha_privately",
    "authenticate_creator_commercial_reuse_and_monetization_grant",
    "clear_music_game_guests_overlays_and_publisher_rights",
    "watch_original_before_and_after_to_confirm_context",
    "transcribe_and_listen_to_verify_exact_spoken_words",
    "human_select_or_reject_standalone_entertaining_moment",
    "write_new_substantive_clivox_commentary_or_analysis",
    "human_review_crop_accessibility_and_caption_accuracy",
    "verify_final_metadata_attribution_and_license_scope",
    "obtain_separate_owner_exact_media_review_before_release",
)


class EditorialIntakeDenied(ValueError):
    """A source-free model cannot be promoted to a human-approved edit."""


def need(ok: bool, code: str) -> None:
    if not ok:
        raise EditorialIntakeDenied("CLIVOX_V2_P6_LONGFORM_DENIED_" + code)


def verify_candidate_binding(measurements: object, report: object) -> dict:
    """Reject changed timing, fake evidence, added authority, or stale digest."""
    expected = plan_longform_candidates(measurements)
    need(type(report) is dict and report == expected,
         "EXACT_P5_MEASUREMENT_REPORT_RECOMPUTE")
    need(report["channel_id"] == CHANNEL
         and report["source_media_authenticated"] is False
         and report["creator_commercial_rights_authenticated"] is False
         and report["human_editorial_review_completed"] is False
         and report["ready_for_render"] is False
         and report["youtube_upload_authorized"] is False,
         "P5_RIGHTS_AND_RENDER_MUST_STAY_BLOCKED")
    return expected


def build_unreviewed_editorial_intake(*, measurements: object,
                                     report: object) -> dict:
    """Produce questions, not quotes/stories or a video/edit authorization."""
    p5 = verify_candidate_binding(measurements, report)
    rows = []
    for item in p5["candidates"]:
        need(item["creator_license_authenticated"] is False
             and item["transcript_and_quote_verified"] is False
             and item["human_editorial_context_review_completed"] is False
             and item["clip_render_authorized"] is False,
             "UPSTREAM_EDITORIAL_RIGHTS_NOT_CLOSED")
        rows.append({
            "candidate_id": item["candidate_id"],
            "source_start_ms": item["start_ms"],
            "source_end_ms": item["end_ms"],
            "measured_evidence_kinds_only": list(item["evidence_kinds"]),
            "human_review_state": "UNREVIEWED_NOT_HUMAN_SELECTED",
            "suggested_original_script_text": None,
            "actual_speaker_words": None,
            "viral_success_probability": None,
            "source_media_verified": False,
            "source_license_verified": False,
            "spoken_quote_verified": False,
            "human_editor_approved": False,
            "original_transformative_value_approved": False,
            "render_authorized": False,
            "youtube_upload_authorized": False,
            "youtube_publish_authorized": False,
            "pending_human_checks": {
                name: "NOT_PERFORMED_SOURCE_FREE_ONLY" for name in CHECKS
            },
        })
    return {
        "schema_version": 1,
        "stage": STAGE,
        "channel_id": CHANNEL,
        "measurement_sha256_is_not_original_media_provenance":
            p5["source_measurement_sha256_not_source_license"],
        "candidate_count": len(rows),
        "overflow_omitted_count": p5["candidate_overflow_omitted_count"],
        "source_media_received": 0,
        "creator_licenses_verified": 0,
        "editorial_approvals_received": 0,
        "youtube_uploads": 0,
        "human_editorial_review_completed": False,
        "real_p6_milestone_complete": False,
        "output_is_a_video_edl": False,
        "ready_to_render": False,
        "ready_to_publish": False,
        "cards": rows,
        "status": HOLD,
    }


def production_editorial_approval(*_args, **_kwargs) -> None:
    raise EditorialIntakeDenied(
        "CLIVOX_V2_P6_LONGFORM_DENIED_NO_AUTHENTIC_HUMAN_OR_CREATOR_RELEASE"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("closed", "synthetic"), default="closed")
    args = p.parse_args()
    if args.mode == "closed":
        print(json.dumps({
            "stage": "CLIVOX_V2_P6_LONGFORM_CLOSED",
            "channel_id": CHANNEL,
            "real_source_clips": 0, "human_editorial_approvals": 0,
            "youtube_uploads": 0,
        }, sort_keys=True))
        return
    measurements = synthetic_demo()
    report = plan_longform_candidates(measurements)
    packet = build_unreviewed_editorial_intake(
        measurements=measurements, report=report
    )
    need(packet["candidate_count"] == 3
         and packet["ready_to_render"] is False
         and packet["ready_to_publish"] is False, "SYNTHETIC_CONTRACT")
    print(json.dumps({
        "stage": packet["stage"],
        "candidate_review_cards": packet["candidate_count"],
        "synthetic_numeric_fixture_only": True,
        "creator_licenses": 0,
        "real_media_processed": 0,
        "youtube_uploads": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
