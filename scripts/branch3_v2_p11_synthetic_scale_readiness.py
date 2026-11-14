"""CLIVOX V2 P11: no-network synthetic weekly clip scale readiness gate.

Simulates the desired two Shorts + one long daily cadence. No creator is
contacted, no third-party source is opened, no rights are granted, no upload is
made and no monetary/YPP or engagement outcome is predicted.

Actual production remains BLOCKED: require authenticated commercial creator
agreements, underlying rights, human substantive editorial review and exact
owner-signed release regardless of theoretical human processing capacity.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from scripts.branch3_v2_p5_synthetic_moment_proposals import CHANNEL
from scripts.branch3_v2_p10_synthetic_analytics_gates import (
    P10Denied, closed_a10_and_p9,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "branch3/clipping_v2/p11-synthetic-weekly-capacity.json"
STAGE = "CLIVOX_V2_P11_SYNTHETIC_WEEKLY_RIGHTS_AND_EDITOR_CAPACITY_GATE"
EXPECTED_WEEK_START = "2027-03-01T00:00:00Z"
MODES = frozenset(("closed", "synthetic"))
SOURCE_CATEGORIES = (
    "gaming_livestream", "podcast_interview", "reaction_comedy"
)
FIELDS = frozenset({
    "schema_version", "channel_id", "stage", "execution_mode", "synthetic",
    "hypothetical_week_start_utc", "planning_days",
    "hypothetical_daily_targets", "human_minutes_per_item",
    "hypothetical_available_editor_minutes_per_week",
    "actual_committed_editor_minutes_per_week", "source_research_cases",
    "verified_rightsholder_agreements",
    "confirmed_licensed_source_media_files",
    "approved_private_source_vault",
    "real_editorial_owner_review_signatures",
    "real_publish_approved_videos",
    "live_clivox_upload_oauth_connected", "live_analytics_evidence_connected",
    "confirmed_youtube_monetization_eligibility",
    "actual_creator_outreach_messages_sent", "actual_media_downloads",
    "actual_youtube_uploads",
    "minimum_distinct_creator_partnerships_before_scale",
    "requires_substantive_original_commentary",
    "requires_human_licensed_source_context_review",
    "requires_current_rights_and_revocation_recheck_per_video",
    "requires_no_misleading_claims_or_unoriginal_template_reuploads",
    "expected_decision",
})
CATEGORY_FIELDS = frozenset({
    "category", "rights_state", "source_media_delivered",
    "human_context_originality_reviewed",
    "commercial_youtube_derivatives_licensed",
    "guest_music_game_rights_verified",
})
TIME_FIELDS = frozenset({
    "day", "hypothetical_date_utc", "target_shorts", "target_long_videos",
    "real_authorized_shorts", "real_authorized_long_videos",
    "human_context_review_completed", "rights_renewal_confirmed",
    "actual_scheduled_youtube_uploads",
})
RESULT_FIELDS = frozenset({
    "stage", "channel_id", "simulation_only", "source", "planning_days",
    "hypothetical_target_shorts", "hypothetical_target_long_videos",
    "hypothetical_total_assets", "hypothetical_editor_minutes_demand",
    "hypothetical_editor_hours_demand",
    "hypothetical_editor_minutes_available",
    "hypothetical_editor_capacity_gap_minutes",
    "actual_committed_editor_minutes",
    "research_only_category_count", "verified_creator_partnerships",
    "minimum_creator_partnerships_required",
    "real_licensed_source_files", "actual_editorial_signed_reviews",
    "actual_published_approved_pilots", "real_owned_analytics_observed",
    "real_creator_outreach_messages_sent", "real_source_downloads",
    "actual_youtube_uploads", "authorized_production_capacity_assets",
    "production_ready", "real_recurring_clip_scale_enabled",
    "real_license_rights_current", "copyright_clearance_complete",
    "human_originality_reviewed",
    "reused_content_ypp_safety_independently_verified",
    "youtube_partner_monetization_guaranteed",
    "cross_creator_automatic_reupload_enabled",
    "public_youtube_scheduler_enabled", "live_clivox_upload_oauth_verified",
    "approved_private_media_vault_verified",
    "owner_exact_video_release_signed", "youtube_publish_authorized",
    "no_monetization_or_viral_predictions_made",
    "creative_editorial_novelty_review_required",
    "copyright_license_does_not_equal_ypp_approval",
    "hypothetical_weekly_slots", "source_category_hold_register",
    "blockers", "real_p11_milestone_complete", "status",
})
BLOCKERS = (
    "NO_AUTHENTIC_VERIFIED_CREATOR_COMMERCIAL_AGREEMENTS",
    "NO_CLEARED_PUBLISHER_MUSIC_GUEST_GAME_SOURCE_RIGHTS",
    "NO_APPROVED_PRIVATE_LICENSED_SOURCE_FILES",
    "NO_ACTUAL_HUMAN_EDITOR_ORIGINALITY_OR_CONTEXT_APPROVAL",
    "NO_INDEPENDENTLY_VERIFIED_EDITOR_WORKFORCE_CAPACITY",
    "NO_EXACT_FINAL_VIDEO_OWNER_SIGNATURE",
    "NO_REAL_APPROVED_PRIVATE_CLIVOX_PILOT",
    "NO_LIVE_SEPARATE_UPLOAD_OAUTH_AND_DURABLE_LEDGER",
    "NO_REAL_CLIVOX_OWNER_ANALYTICS_FEEDBACK",
    "NO_INDEPENDENT_YPP_REUSED_CONTENT_ELIGIBILITY_DECISION",
)


class P11Denied(ValueError):
    """Do not reinterpret simulation as authority to license, produce or upload."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise P11Denied("CLIVOX_V2_P11_DENIED_" + reason)


def read_synthetic_fixture(path: Path = FIXTURE) -> dict:
    require(type(path) is Path and path == FIXTURE
            and path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= 12000,
            "ONLY_FIXED_OFFLINE_WEEKLY_FIXTURE")
    try:
        p = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise P11Denied("CLIVOX_V2_P11_DENIED_INVALID_JSON") from None
    return validate_fixture(p)


def validate_fixture(plan: object) -> dict:
    closed_a10_and_p9()
    require(type(plan) is dict and set(plan) == FIELDS,
            "PLAN_EXACT_FIELDS")
    require(type(plan["schema_version"]) is int
            and plan["schema_version"] == 1
            and plan["channel_id"] == CHANNEL
            and plan["stage"] ==
            "P11_WEEKLY_ORIGINAL_CLIP_SCALE_SOURCE_FREE_FIXTURE"
            and plan["execution_mode"] ==
            "SYNTHETIC_CAPACITY_PLANNING_NO_MEDIA_NO_CONTACT_NO_UPLOAD"
            and plan["synthetic"] is True
            and plan["hypothetical_week_start_utc"] == EXPECTED_WEEK_START
            and type(plan["planning_days"]) is int
            and plan["planning_days"] == 7,
            "FIXTURE_ONLY_NOT_REAL_WEEK")
    require(type(plan["hypothetical_daily_targets"]) is dict
            and plan["hypothetical_daily_targets"] ==
            {"shorts": 2, "long_form": 1}, "HYPOTHETICAL_CADENCE")
    require(type(plan["human_minutes_per_item"]) is dict
            and plan["human_minutes_per_item"] == {
                "shorts_edit": 55,
                "shorts_originality_and_rights_review": 20,
                "long_edit": 180,
                "long_originality_and_rights_review": 40,
            }, "HUMAN_WORKLOAD_ILLUSTRATIVE_ONLY")
    require(type(plan["hypothetical_available_editor_minutes_per_week"]) is int
            and plan["hypothetical_available_editor_minutes_per_week"] == 1200
            and type(plan["actual_committed_editor_minutes_per_week"]) is int
            and plan["actual_committed_editor_minutes_per_week"] == 0,
            "NO_REAL_STAFFING")
    cases = plan["source_research_cases"]
    require(type(cases) is list and len(cases) == len(SOURCE_CATEGORIES),
            "SOURCE_CATEGORY_COUNT")
    for category, case in zip(SOURCE_CATEGORIES, cases):
        require(type(case) is dict and set(case) == CATEGORY_FIELDS
                and case["category"] == category
                and case["rights_state"] == "PENDING_NO_CONTACT",
                "CASE_RESEARCH_ONLY")
        for k in (
            "source_media_delivered", "human_context_originality_reviewed",
            "commercial_youtube_derivatives_licensed",
            "guest_music_game_rights_verified",
        ):
            require(case[k] is False, "CASE_RIGHTS_UNVERIFIED_" + k.upper())
    for k in (
        "verified_rightsholder_agreements",
        "confirmed_licensed_source_media_files",
        "real_editorial_owner_review_signatures",
        "real_publish_approved_videos",
        "actual_creator_outreach_messages_sent", "actual_media_downloads",
        "actual_youtube_uploads",
    ):
        require(type(plan[k]) is int and plan[k] == 0,
                "FORGED_LIVE_COUNT_" + k.upper())
    for k in (
        "approved_private_source_vault",
        "live_clivox_upload_oauth_connected",
        "live_analytics_evidence_connected",
        "confirmed_youtube_monetization_eligibility",
    ):
        require(plan[k] is False, "FALSE_PRODUCTION_READINESS_" + k.upper())
    for k in (
        "requires_substantive_original_commentary",
        "requires_human_licensed_source_context_review",
        "requires_current_rights_and_revocation_recheck_per_video",
        "requires_no_misleading_claims_or_unoriginal_template_reuploads",
    ):
        require(plan[k] is True, "ORIGINALITY_SAFETY_MISSING_" + k.upper())
    require(type(plan["minimum_distinct_creator_partnerships_before_scale"]) is int
            and plan["minimum_distinct_creator_partnerships_before_scale"] == 2
            and plan["expected_decision"] ==
            "BLOCK_REAL_SCALING_AWAIT_AUTHENTIC_LICENSES_EDITOR_CAPACITY_AND_OWNER_RELEASE",
            "REAL_SCALE_MUST_STAY_BLOCKED")
    return plan


def weekly_slots(plan: dict) -> list[dict]:
    """A hypothetical demand outline; these are not video tasks or schedule."""
    validate_fixture(plan)
    start = datetime(2027, 3, 1, tzinfo=timezone.utc)
    return [
        {
            "day": i + 1,
            "hypothetical_date_utc":
                (start + timedelta(days=i)).strftime("%Y-%m-%d"),
            "target_shorts": 2, "target_long_videos": 1,
            "real_authorized_shorts": 0,
            "real_authorized_long_videos": 0,
            "human_context_review_completed": False,
            "rights_renewal_confirmed": False,
            "actual_scheduled_youtube_uploads": 0,
        } for i in range(7)
    ]


def evaluate_source_free_p11(plan: dict) -> dict:
    """Safe numbers are time/cadence only, never projected views or revenue."""
    validate_fixture(plan)
    shorts = plan["planning_days"] * plan["hypothetical_daily_targets"]["shorts"]
    long_count = plan["planning_days"] * plan["hypothetical_daily_targets"]["long_form"]
    shorts_minutes = (
        plan["human_minutes_per_item"]["shorts_edit"]
        + plan["human_minutes_per_item"]["shorts_originality_and_rights_review"]
    )
    long_minutes = (
        plan["human_minutes_per_item"]["long_edit"]
        + plan["human_minutes_per_item"]["long_originality_and_rights_review"]
    )
    demand = shorts * shorts_minutes + long_count * long_minutes
    assumed_available = plan["hypothetical_available_editor_minutes_per_week"]
    require((shorts, long_count, shorts_minutes, long_minutes, demand) ==
            (14, 7, 75, 220, 2590), "HYPOTHETICAL_WORKLOAD_CONTRACT")
    require(assumed_available == 1200, "HYPOTHETICAL_AVAILABILITY")
    result = {
        "stage": STAGE, "channel_id": CHANNEL,
        "simulation_only": True,
        "source": "FIXED_ORIGINAL_SOURCE_FREE_WEEKLY_CAPACITY_FIXTURE",
        "planning_days": 7,
        "hypothetical_target_shorts": shorts,
        "hypothetical_target_long_videos": long_count,
        "hypothetical_total_assets": shorts + long_count,
        "hypothetical_editor_minutes_demand": demand,
        "hypothetical_editor_hours_demand": round(demand / 60, 3),
        "hypothetical_editor_minutes_available": assumed_available,
        "hypothetical_editor_capacity_gap_minutes":
            max(0, demand - assumed_available),
        "actual_committed_editor_minutes": 0,
        "research_only_category_count": len(SOURCE_CATEGORIES),
        "verified_creator_partnerships": 0,
        "minimum_creator_partnerships_required": 2,
        "real_licensed_source_files": 0,
        "actual_editorial_signed_reviews": 0,
        "actual_published_approved_pilots": 0,
        "real_owned_analytics_observed": False,
        "real_creator_outreach_messages_sent": 0,
        "real_source_downloads": 0, "actual_youtube_uploads": 0,
        "authorized_production_capacity_assets": 0,
        "production_ready": False,
        "real_recurring_clip_scale_enabled": False,
        "real_license_rights_current": False,
        "copyright_clearance_complete": False,
        "human_originality_reviewed": False,
        "reused_content_ypp_safety_independently_verified": False,
        "youtube_partner_monetization_guaranteed": False,
        "cross_creator_automatic_reupload_enabled": False,
        "public_youtube_scheduler_enabled": False,
        "live_clivox_upload_oauth_verified": False,
        "approved_private_media_vault_verified": False,
        "owner_exact_video_release_signed": False,
        "youtube_publish_authorized": False,
        "no_monetization_or_viral_predictions_made": True,
        "creative_editorial_novelty_review_required": True,
        "copyright_license_does_not_equal_ypp_approval": True,
        "hypothetical_weekly_slots": weekly_slots(plan),
        "source_category_hold_register": [
            {"category": category,
             "research_only_no_creator_contact": True,
             "verified_commercial_reuse_license": False,
             "reviewed_original_storytelling": False,
             "production_source_access_allowed": False}
            for category in SOURCE_CATEGORIES
        ],
        "blockers": list(BLOCKERS),
        "real_p11_milestone_complete": False,
        "status": "CAPACITY_SIMULATION_ONLY_NO_CLIP_SUPPLY_RIGHTS_EDITOR_OR_YPP_RELEASE",
    }
    closed_a10_and_p9()
    return validate_report(result)


def validate_report(report: object) -> dict:
    """Adversarially refuse to promote illustrative capacity to real supply."""
    require(type(report) is dict and set(report) == RESULT_FIELDS,
            "REPORT_EXACT_FIELDS")
    require(report["stage"] == STAGE and report["channel_id"] == CHANNEL
            and report["source"] ==
            "FIXED_ORIGINAL_SOURCE_FREE_WEEKLY_CAPACITY_FIXTURE"
            and report["status"] ==
            "CAPACITY_SIMULATION_ONLY_NO_CLIP_SUPPLY_RIGHTS_EDITOR_OR_YPP_RELEASE"
            and report["simulation_only"] is True,
            "SOURCE_FREE_REPORT_ONLY")
    expected_counts = {
        "planning_days": 7, "hypothetical_target_shorts": 14,
        "hypothetical_target_long_videos": 7,
        "hypothetical_total_assets": 21,
        "hypothetical_editor_minutes_demand": 2590,
        "hypothetical_editor_hours_demand": round(2590/60, 3),
        "hypothetical_editor_minutes_available": 1200,
        "hypothetical_editor_capacity_gap_minutes": 1390,
        "actual_committed_editor_minutes": 0,
        "research_only_category_count": 3,
        "verified_creator_partnerships": 0,
        "minimum_creator_partnerships_required": 2,
        "real_licensed_source_files": 0,
        "actual_editorial_signed_reviews": 0,
        "actual_published_approved_pilots": 0,
        "real_creator_outreach_messages_sent": 0,
        "real_source_downloads": 0,
        "actual_youtube_uploads": 0,
        "authorized_production_capacity_assets": 0,
    }
    for name, value in expected_counts.items():
        require(type(report[name]) is type(value) and report[name] == value,
                "REPORT_WORKLOAD_OR_REAL_SUPPLY_" + name.upper())
    for name in (
        "real_owned_analytics_observed",
        "production_ready", "real_recurring_clip_scale_enabled",
        "real_license_rights_current",
        "copyright_clearance_complete", "human_originality_reviewed",
        "reused_content_ypp_safety_independently_verified",
        "youtube_partner_monetization_guaranteed",
        "cross_creator_automatic_reupload_enabled",
        "public_youtube_scheduler_enabled",
        "live_clivox_upload_oauth_verified",
        "approved_private_media_vault_verified",
        "owner_exact_video_release_signed",
        "youtube_publish_authorized",
        "real_p11_milestone_complete",
    ):
        require(report[name] is False, "FORGED_REAL_SCALE_" + name.upper())
    for name in (
        "no_monetization_or_viral_predictions_made",
        "creative_editorial_novelty_review_required",
        "copyright_license_does_not_equal_ypp_approval",
    ):
        require(report[name] is True, "REQUIRED_YPP_SAFETY_" + name.upper())
    slots = report["hypothetical_weekly_slots"]
    require(type(slots) is list and len(slots) == 7,
            "WEEKLY_SLOTS_LENGTH")
    expected_start = datetime(2027, 3, 1, tzinfo=timezone.utc)
    for i, slot in enumerate(slots):
        require(type(slot) is dict and set(slot) == TIME_FIELDS
                and type(slot["day"]) is int and slot["day"] == i+1
                and slot["hypothetical_date_utc"] ==
                (expected_start+timedelta(days=i)).strftime("%Y-%m-%d")
                and type(slot["target_shorts"]) is int
                and slot["target_shorts"] == 2
                and type(slot["target_long_videos"]) is int
                and slot["target_long_videos"] == 1
                and type(slot["real_authorized_shorts"]) is int
                and slot["real_authorized_shorts"] == 0
                and type(slot["real_authorized_long_videos"]) is int
                and slot["real_authorized_long_videos"] == 0
                and slot["human_context_review_completed"] is False
                and slot["rights_renewal_confirmed"] is False
                and type(slot["actual_scheduled_youtube_uploads"]) is int
                and slot["actual_scheduled_youtube_uploads"] == 0,
                "HYPOTHETICAL_NOT_REAL_UPLOAD_SLOT")
    register = report["source_category_hold_register"]
    require(type(register) is list and len(register) == 3,
            "HOLD_REGISTER")
    fields = {
        "category", "research_only_no_creator_contact",
        "verified_commercial_reuse_license",
        "reviewed_original_storytelling", "production_source_access_allowed",
    }
    for category, item in zip(SOURCE_CATEGORIES, register):
        require(type(item) is dict and set(item) == fields
                and item["category"] == category
                and item["research_only_no_creator_contact"] is True
                and item["verified_commercial_reuse_license"] is False
                and item["reviewed_original_storytelling"] is False
                and item["production_source_access_allowed"] is False,
                "FORGED_SOURCE_SUPPLY")
    require(type(report["blockers"]) is list
            and report["blockers"] == list(BLOCKERS),
            "REQUIRED_BLOCKERS")
    raw = json.dumps(report, sort_keys=True, allow_nan=False)
    for forbidden in (
        "creator_email", "youtube.com/watch?", "source_video_url",
        "private_key", "access_token", "revenue_estimate",
        "predicted_viral_views", "licensed_creator_name",
    ):
        require(forbidden not in raw, "FORBIDDEN_PRIVATE_OR_FALSE_SCALE_CLAIM")
    return report


def production_scale_or_contact(*_args, **_kwargs) -> None:
    raise P11Denied(
        "CLIVOX_V2_P11_DENIED_NO_CREATOR_LICENSE_EDITOR_OR_OWNER_RELEASE"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=tuple(sorted(MODES)), default="closed")
    args = parser.parse_args()
    try:
        closed_a10_and_p9()
        if args.mode == "closed":
            out = {
                "stage": "CLIVOX_V2_P11_CLOSED_UNLICENSED_SOURCE_NO_SCALE",
                "channel_id": CHANNEL,
                "real_creator_partnerships": 0,
                "real_youtube_uploads": 0,
                "production_scale_allowed": False,
            }
        else:
            out = evaluate_source_free_p11(read_synthetic_fixture())
        print(json.dumps(out, sort_keys=True, allow_nan=False))
    except (P11Denied, P10Denied, ValueError, OSError,
            TypeError, KeyError, UnicodeError):
        raise SystemExit(
            "CLIVOX_V2_P11_BLOCKED_RIGHTS_EDITOR_ORIGINALITY_AND_UPLOAD"
        ) from None


if __name__ == "__main__":
    main()
