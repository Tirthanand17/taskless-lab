"""Clivox A2 intake: produce UNVERIFIED creator-rights review cases from A1 metadata.

This is not rights verification. Human/rights-holder authenticated grants are
required by the *existing* branch3 creator permission gate. No network, no
contracts accepted, no creator approval, no video downloads and no uploads.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

CLIVOX_ID = "UCfPEvy0SefE_5nNlYlY_CyQ"
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
PENDING_CHECKS = (
    "actual_creator_or_rights_holder_identity",
    "rights_holder_authority_to_license_this_recording",
    "direct_written_grant_or_authenticated_creator_public_policy",
    "commercial_youtube_shorts_reuse_and_redistribution",
    "cropping_editing_original_commentary_and_sound_rights",
    "exact_video_and_source_timestamp_scope",
    "territory_duration_expiry_and_revocation_terms",
    "underlying_game_publisher_footage_rights_if_present",
    "separate_background_music_and_sound_effects_rights",
    "guest_face_voice_images_tv_movie_and_other_embedded_rights",
    "attribution_creator_link_and_required_sponsor_disclosures",
    "campaign_participation_eligibility_and_terms_if_applicable",
    "owner_review_of_contract_ip_assignment_and_claim_process",
    "human_review_of_source_context_and_deceptive_edit_risk",
)
BLOCKING_FIELDS = (
    "rights_holder_identity_verified",
    "clivox_commercial_clipping_rights_verified",
    "underlying_game_music_guest_rights_cleared",
    "source_media_download_allowed",
    "segment_selected",
    "quote_verified",
    "ready_to_publish",
    "youtube_upload_authorized",
)
MAX_CASES = 30


class RightsIntakeBlocked(ValueError):
    """A candidate claims verification or lacks a reliable public source ID."""


def require(value: bool, code: str) -> None:
    if not value:
        raise RightsIntakeBlocked("CLIVOX_A2_DENIED_" + code)


def build_rights_cases(discovery: object, *, generated_at_utc: str) -> dict:
    require(type(discovery) is dict, "INVALID_REPORT")
    require(discovery.get("schema_version") == 1, "WRONG_SCHEMA")
    require(discovery.get("channel_id") == CLIVOX_ID, "WRONG_CHANNEL")
    require(discovery.get("stage") == "A1_DISCOVERY_PUBLIC_METADATA_ONLY", "NOT_A1")
    require(discovery.get("mode") in ("fixture", "ids", "query"), "UNKNOWN_SOURCE_MODE")
    require(discovery.get("source_of_numbers") in (
        "synthetic_test_fixture", "youtube_data_api_v3_public_statistics"
    ), "UNKNOWN_PROVENANCE")
    synthetic = discovery.get("is_synthetic_fixture")
    require(type(synthetic) is bool, "MISSING_FIXTURE_MARKER")
    require((synthetic and discovery["mode"] == "fixture"
             and discovery["source_of_numbers"] == "synthetic_test_fixture")
            or (not synthetic and discovery["mode"] in ("ids", "query")
                and discovery["source_of_numbers"] == "youtube_data_api_v3_public_statistics"),
            "SYNTHETIC_PRETENDS_LIVE")
    require(discovery.get("all_candidates_permission_unverified") is True
            and discovery.get("release_or_media_acquisition_allowed") is False
            and discovery.get("youtube_api_write_calls") == 0, "SOURCE_RIGHTS_NOT_DENIED")
    require(type(generated_at_utc) is str and generated_at_utc.endswith("Z")
            and len(generated_at_utc) <= 35, "INVALID_REVIEW_TIME")
    try:
        dt = datetime.fromisoformat(generated_at_utc[:-1] + "+00:00")
        require(dt.tzinfo is not None, "INVALID_REVIEW_TIME")
    except ValueError:
        raise RightsIntakeBlocked("CLIVOX_A2_DENIED_INVALID_REVIEW_TIME") from None
    candidates = discovery.get("candidates")
    require(type(candidates) is list and len(candidates) <= MAX_CASES, "TOO_MANY_CANDIDATES")
    seen: set[str] = set()
    cases = []
    for c in candidates:
        require(type(c) is dict, "INVALID_CANDIDATE")
        vid = c.get("source_video_id")
        channel = c.get("source_channel_id")
        require(type(vid) is str and VIDEO_ID.fullmatch(vid) is not None, "BAD_VIDEO_ID")
        require(type(channel) is str and CHANNEL_ID.fullmatch(channel) is not None, "BAD_SOURCE_CHANNEL")
        require(vid not in seen, "DUPLICATE_SOURCE")
        seen.add(vid)
        require(c.get("source_url") == "https://www.youtube.com/watch?v=" + vid, "BAD_SOURCE_URL")
        require(c.get("sourcing_status") == "RESEARCH_ONLY_PUBLIC_METADATA"
                and c.get("permission_state") == "UNVERIFIED", "UNVERIFIED_REQUIRED")
        require(all(c.get(k) is False for k in BLOCKING_FIELDS), "UNAUTHORIZED_CLIP_FLAG")
        score = c.get("research_priority_score_0_to_100")
        require(type(score) is int and 0 <= score <= 100, "BAD_RESEARCH_SCORE")
        title = c.get("source_title")
        require(type(title) is str and 1 <= len(title) <= 160, "BAD_SOURCE_TITLE")
        cases.append({
            "case_id": "clivox_rights_" + vid,
            "channel_id": CLIVOX_ID,
            "source_video_id": vid,
            "source_channel_id": channel,
            "source_url": c["source_url"],
            "source_title": title,
            "source_category": discovery.get("category"),
            "research_priority_score_only": score,
            "case_state": "AWAITING_REAL_RIGHTS_HOLDER_VERIFICATION",
            "human_rights_reviewer_assigned": False,
            "actual_grant_document_available": False,
            "verified_creator_published_policy": False,
            "permission_evidence_reference": None,
            "permission_evidence_sha256": None,
            "license_expiry_utc": None,
            "creator_permissions_registry_updated": False,
            "required_checks": {key: "PENDING_HUMAN_VERIFICATION" for key in PENDING_CHECKS},
            "contract_acceptance_done": False,
            "contract_assignment_reviewed_by_owner": False,
            "media_acquisition_authorized": False,
            "edit_authorized": False,
            "owner_clip_release_signed": False,
            "youtube_upload_authorized": False,
            "youtube_publish_authorized": False,
            "next_step": "HUMAN_AUTHENTICATE_CREATOR_CLIPPING_POLICY_OR_DIRECT_GRANT",
            "case_is_synthetic": synthetic,
            "disclaimer": "A research case is NOT a license or an approval. Never store contracts or personal contacts in public GitHub."
        })
    source_sha = hashlib.sha256(
        json.dumps(discovery, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    cases.sort(key=lambda x: (-x["research_priority_score_only"], x["source_video_id"]))
    return {
        "schema_version": 1,
        "stage": "A2_RIGHTS_REVIEW_INTAKE_ONLY",
        "target_channel_id": CLIVOX_ID,
        "generated_at_utc": generated_at_utc,
        "source_report_sha256": source_sha,
        "is_synthetic_fixture": synthetic,
        "creator_permission_grants_issued_by_this_workflow": 0,
        "media_downloads": 0,
        "youtube_writes": 0,
        "cases_all_unverified": True,
        "pending_case_count": len(cases),
        "cases": cases,
        "release_enabled": False,
        "note": "Human authenticity review and owner contractual consent are outside this workflow; no automatic promotion to rights-approved state."
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Clivox A2 no-approval rights case intake")
    p.add_argument("--source-report", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        data = json.loads(args.source_report.read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        result = build_rights_cases(data, generated_at_utc=now)
        require(args.out.suffix.lower() == ".json", "OUTPUT_NOT_JSON")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("CLIVOX_A2_RIGHTS_INTAKE_ONLY pending_cases="
              + str(result["pending_case_count"])
              + " creator_grants=0 media_downloads=0 uploads=0")
    except (RightsIntakeBlocked, OSError, ValueError, TypeError, KeyError):
        raise SystemExit("CLIVOX_A2_RIGHTS_INTAKE_BLOCKED_UNVERIFIED_OR_INVALID_REPORT") from None


if __name__ == "__main__":
    main()
