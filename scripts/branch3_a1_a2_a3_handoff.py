"""CLIVOX A1->A2->A3 provenance/rights/storage handoff (NO MEDIA/NO YOUTUBE).

This audits *consistency* between public discovery, the pending human-rights
cases, and the unprovisioned media vault. It does not authenticate a publisher,
a creator's legal grant, GitHub repository visibility, or live YouTube identity.
All outputs are sanitized public metadata. Nothing is permitted to download.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from scripts.branch3_rights_case_intake import build_rights_cases
from scripts.branch3_media_storage_preflight import (
    ROOT, POLICY, MANIFEST, CREATOR_PERMS, CHANNEL_STATE, CLIVOX,
    read_json as read_storage_json, validate_policy, validate_public_paths,
    BRANDING_ALLOWLIST,
)
from scripts.branch3_discovery import CATEGORIES

DISCOVERY_KEYS = frozenset((
    "schema_version", "channel_id", "channel_handle", "stage", "mode",
    "category", "query", "retrieved_at_utc", "is_synthetic_fixture",
    "source_of_numbers", "all_candidates_permission_unverified",
    "release_or_media_acquisition_allowed", "youtube_api_write_calls",
    "upstream_clip_rights_human_review_required", "method", "explanation",
    "candidates",
))
CANDIDATE_KEYS = frozenset((
    "source_video_id", "source_channel_id", "source_url", "source_title",
    "source_channel_title", "source_published_utc", "source_age_hours",
    "source_duration_seconds", "public_stats", "research_priority_score_0_to_100",
    "score_components", "permission_state", "rights_holder_identity_verified",
    "clivox_commercial_clipping_rights_verified",
    "underlying_game_music_guest_rights_cleared", "source_media_download_allowed",
    "segment_selected", "quote_verified", "ready_to_publish",
    "youtube_upload_authorized", "sourcing_status",
))
COMPONENT_KEYS = frozenset((
    "views_per_hour", "observed_engagement_ratio",
    "source_title_keyword_matches", "velocity_component",
    "engagement_component", "recency_component", "relevance_component",
))
MAX_BYTES = 350_000


class HandoffDenied(ValueError):
    """Never promote inconsistent evidence to source/media eligibility."""


def require(value: bool, reason: str) -> None:
    if not value:
        raise HandoffDenied("CLIVOX_A123_DENY_" + reason)


def utc_timestamp(value: object) -> datetime:
    require(type(value) is str and 19 <= len(value) <= 35
            and value.endswith("Z"), "TIME_NOT_UTC")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise HandoffDenied("CLIVOX_A123_DENY_BAD_TIMESTAMP") from None
    require(dt.utcoffset() == timedelta(0), "TIMEZONE")
    return dt


def public_discovery_shape(discovery: dict) -> None:
    """Additional allowlist prevents secret-like/extra data in public artifacts."""
    require(type(discovery) is dict and set(discovery) == DISCOVERY_KEYS,
            "DISCOVERY_PUBLIC_FIELDS")
    require(discovery["channel_id"] == CLIVOX
            and discovery["channel_handle"] == "@ClivoxPulse"
            and discovery["category"] in CATEGORIES
            and discovery["upstream_clip_rights_human_review_required"] is True,
            "DISCOVERY_IDENTITY_OR_POLICY")
    require(type(discovery["candidates"]) is list
            and len(discovery["candidates"]) <= 30, "CANDIDATE_LIMIT")
    if discovery["mode"] != "query":
        require(discovery["query"] is None, "UNEXPECTED_QUERY")
    else:
        require(type(discovery["query"]) is str
                and len(discovery["query"]) <= 90, "QUERY")
    utc_timestamp(discovery["retrieved_at_utc"])
    for item in discovery["candidates"]:
        require(type(item) is dict and set(item) == CANDIDATE_KEYS,
                "CANDIDATE_PUBLIC_FIELDS")
        require(type(item["public_stats"]) is dict
                and set(item["public_stats"]) == {"views", "likes", "comments"},
                "PUBLIC_STATS_FIELDS")
        for value in item["public_stats"].values():
            require(value is None or (type(value) is int and value >= 0),
                    "PUBLIC_STATS_VALUE")
        require(type(item["score_components"]) is dict
                and set(item["score_components"]) == COMPONENT_KEYS,
                "SCORE_COMPONENT_FIELDS")
        require(type(item["source_age_hours"]) in (int, float)
                and item["source_age_hours"] >= 0,
                "SOURCE_AGE")
        require(item["source_duration_seconds"] is None
                or (type(item["source_duration_seconds"]) is int
                    and item["source_duration_seconds"] > 0),
                "SOURCE_DURATION")
        require(type(item["source_channel_title"]) is str
                and len(item["source_channel_title"]) <= 100,
                "SOURCE_CHANNEL_TITLE")


def audit_handoff(
    *, discovery: dict, rights_cases: dict, storage_policy: dict,
    storage_manifest: dict, creator_registry: dict, channel_state: dict,
    public_paths: list[str],
) -> dict:
    """Check exact A1/A2 linkage, A3 quarantine and public inventory boundary."""
    public_discovery_shape(discovery)
    require(type(rights_cases) is dict, "RIGHTS_REPORT")
    generated_at = rights_cases.get("generated_at_utc")
    retrieved = utc_timestamp(discovery["retrieved_at_utc"])
    generated = utc_timestamp(generated_at)
    require(retrieved <= generated <= retrieved + timedelta(hours=24),
            "STALE_OR_PRE_SOURCE_RIGHTS_CASES")
    expected_cases = build_rights_cases(discovery, generated_at_utc=generated_at)
    # Exact byte-independent JSON object equality detects any removed checks,
    # copied cases, forged rights booleans or mismatched input digest.
    require(rights_cases == expected_cases, "A1_A2_PROVENANCE_OR_RIGHTS_TAMPER")
    require(rights_cases["target_channel_id"] == CLIVOX
            and rights_cases["creator_permission_grants_issued_by_this_workflow"] == 0
            and rights_cases["media_downloads"] == 0
            and rights_cases["youtube_writes"] == 0
            and rights_cases["release_enabled"] is False,
            "RIGHTS_RELEASE_FORGED")
    storage = validate_policy(
        storage_policy, storage_manifest, creator_registry, channel_state
    )
    inventory = validate_public_paths(
        public_paths, allowed_visuals=sorted(BRANDING_ALLOWLIST)
    )
    require(storage["source_download_authorized"] is False
            and storage["youtube_upload_authorized"] is False
            and storage["private_media_vault_provisioned"] is False
            and inventory["licensed_media_detected"] is False,
            "STORAGE_RELEASE_FORGED")
    source_sha = hashlib.sha256(json.dumps(
        discovery, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    require(source_sha == rights_cases["source_report_sha256"], "SOURCE_HASH")
    return {
        "stage": "A1_A2_A3_CROSS_STAGE_PUBLIC_METADATA_AUDIT",
        "target_channel_id": CLIVOX,
        "status": "CONSISTENT_PENDING_HUMAN_REVIEW_NO_LICENSE_NO_MEDIA",
        "source_report_sha256": source_sha,
        "synthetic_test_fixture": discovery["is_synthetic_fixture"],
        "pending_review_cases": len(rights_cases["cases"]),
        "source_candidates_count": len(discovery["candidates"]),
        "case_ids": [x["case_id"] for x in rights_cases["cases"]],
        "public_paths_checked": inventory["public_paths_checked"],
        "rights_holder_legal_identity_authenticated": False,
        "actual_creator_grants_verified": 0,
        "private_media_vault_provisioned": False,
        "source_media_downloads": 0,
        "google_or_youtube_api_writes": 0,
        "source_media_fetch_authorized": False,
        "original_editorial_release_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "notes": (
            "This checks A1/A2 consistency and A3 offline deny state only. "
            "Input metadata is not authenticated by this step. No source "
            "rights, actual private-vault ACL, OAuth identity or upload proven."
        ),
    }


def read_public_json(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= MAX_BYTES,
            "INPUT_PATH_OR_SIZE")
    try:
        data = json.loads(path.read_text("utf-8"))
    except (ValueError, UnicodeError):
        raise HandoffDenied("CLIVOX_A123_DENY_INPUT_JSON") from None
    require(type(data) is dict, "INPUT_NOT_OBJECT")
    return data


def inspect_files(discovery_path: Path, cases_path: Path) -> dict:
    require(discovery_path.resolve() != cases_path.resolve(), "SAME_INPUT_FILE")
    paths = [
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in (ROOT / "branch3").rglob("*") if p.is_file()
    ]
    return audit_handoff(
        discovery=read_public_json(discovery_path),
        rights_cases=read_public_json(cases_path),
        storage_policy=read_storage_json(POLICY),
        storage_manifest=read_storage_json(MANIFEST),
        creator_registry=read_storage_json(CREATOR_PERMS),
        channel_state=read_storage_json(CHANNEL_STATE),
        public_paths=paths,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--discovery", type=Path, required=True)
    p.add_argument("--rights-cases", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        out = args.out.absolute()
        require(out.name == "public-a1-a2-a3-handoff-report.json"
                and out.suffix == ".json"
                and not out.is_symlink()
                and ROOT not in out.parents,
                "REPORT_MUST_BE_EPHEMERAL_OUTSIDE_PUBLIC_REPO")
        report = inspect_files(args.discovery, args.rights_cases)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", "utf-8")
    except (HandoffDenied, ValueError, TypeError, KeyError, OSError):
        raise SystemExit("CLIVOX_A123_HANDOFF_DENIED_NO_RIGHTS_NO_MEDIA_NO_UPLOAD") from None
    print("CLIVOX_A123_HANDOFF_PASSED_PENDING_RIGHTS_NO_MEDIA_NO_UPLOAD")


if __name__ == "__main__":
    main()
