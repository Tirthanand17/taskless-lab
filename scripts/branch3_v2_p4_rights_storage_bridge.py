"""CLIVOX V2 P2/P3 -> P4 private media handoff readiness (strict NO-GO).

This is a source-free dependency join, not a media intake service. It takes
existing validated public creator research, signed-grant CLOSED policy, and
existing A3/P4 storage quarantine. It cannot certify agreements, authenticate
parties, operate the private vault or accept a real source file.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json

from scripts.branch3_v2_creator_prospect_intake import DATA, load_watchlist
from scripts.branch3_a2_review_receipt import POLICY, REGISTRY, read_json
from scripts.branch3_v2_p2p3_pilot_owner_review import (
    CHANNEL, compile_owner_pilot_packet, load_public_route_audit,
)
from scripts.branch3_v2_p2p3_owner_decision_matrix import build_matrix
from scripts.branch3_v2_p4_synthetic_handoff_preflight import actual_closed_boundary
from scripts.branch3_a3_private_vault_readback import fixture_report

STAGE = "CLIVOX_V2_P4_P2P3_RIGHTS_TO_PRIVATE_SOURCE_BOUNDARY_HOLD"
HOLD = "NO_RIGHTSHOLDER_LICENSE_OR_OWNER_APPROVED_MEDIA_VAULT"
NEEDS = (
    "OWNER_INDEPENDENTLY_SELECTS_CREATOR_AND_AUTHENTICATES_REAL_SIGNATORY",
    "EXACT_SOURCE_AND_YOUTUBE_COMMERCIAL_DERIVATIVE_GRANT_VERIFIED_PRIVATELY",
    "GUEST_MUSIC_PUBLISHER_GAME_PLATFORM_AND_REVOCATION_RIGHTS_CLEARED",
    "OWNER_APPROVES_CONFIDENTIAL_VAULT_AND_ACCESS_RETENTION_PRIVACY_AUDIT",
    "CREATOR_DELIVERS_ORIGINAL_MASTER_THROUGH_APPROVED_PRIVATE_CHANNEL",
    "PRIVATE_RUNNER_AUTHENTICATES_RIGHTS_AND_HASHES_EXACT_DELIVERED_MEDIA",
    "SEPARATE_OWNER_FINAL_EDIT_REVIEW_AND_PRIVATE_FIRST_YOUTUBE_AUTHORIZATION",
)


class HandoffDenied(ValueError):
    """A public research document or storage fixture cannot unlock P4."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise HandoffDenied("CLIVOX_V2_P4_BRIDGE_DENIED_" + reason)


def build_handoff_hold(*, owner_matrix: dict, storage_gate: dict,
                       vault_fixture: dict) -> dict:
    """Compose only previously validated in-memory results, no file I/O."""
    require(type(owner_matrix) is dict
            and owner_matrix.get("stage") ==
                "CLIVOX_V2_P2P3_OWNER_DECISION_MATRIX_SOURCE_FREE_HOLD"
            and owner_matrix.get("channel_id") == CHANNEL
            and owner_matrix.get("all_actions_blocked") is True
            and type(owner_matrix.get("prospects_total")) is int
            and owner_matrix["prospects_total"] == 5
            and owner_matrix.get("owner_approval_received") is False
            and owner_matrix.get("license_received") is False
            and owner_matrix.get("creator_outreach_sent") == 0
            and owner_matrix.get("licensed_media_delivered") == 0
            and owner_matrix.get("youtube_uploads") == 0,
            "P2P3_CANNOT_RELEASE")
    rows = owner_matrix.get("rows")
    require(type(rows) is list and len(rows) == 5, "RESEARCH_ROW_COUNT")
    for row in rows:
        require(type(row) is dict
                and row.get("status") ==
                    "BLOCKED_PENDING_HUMAN_SELECTION_IDENTITY_AND_COMMERCIAL_GRANT"
                and type(row.get("pending_rights_questions")) is int
                and row["pending_rights_questions"] >= 25,
                "PROSPECT_REMAINS_PENDING")
        for key in (
            "owner_selection_recorded", "identity_authentication_complete",
            "legal_signatory_authenticated", "specific_source_media_rights_cleared",
            "commercial_youtube_short_license_verified",
            "underlying_music_guests_and_game_rights_cleared",
            "private_source_handoff_authorized",
            "owner_exact_media_release_signed", "outreach_authorized",
            "clip_generation_authorized", "youtube_upload_authorized",
            "youtube_publish_authorized",
        ):
            require(row.get(key) is False, "PROSPECT_FORGED_" + key.upper())
    require(type(storage_gate) is dict
            and storage_gate.get("stage") ==
                "CLIVOX_V2_P4_SYNTHETIC_MEDIA_HANDOFF_QUARANTINE"
            and storage_gate.get("channel_id") == CHANNEL
            and type(storage_gate.get("rights_grants_verified")) is int
            and storage_gate["rights_grants_verified"] == 0
            and type(storage_gate.get("real_media_delivered")) is int
            and storage_gate["real_media_delivered"] == 0
            and storage_gate.get("private_vault_activated") is False
            and storage_gate.get("creator_media_fetch_enabled") is False
            and storage_gate.get("creator_media_write_enabled") is False
            and storage_gate.get("youtube_upload_enabled") is False
            and storage_gate.get("youtube_publish_enabled") is False
            and storage_gate.get("p4_milestone_complete") is False,
            "P4_STORAGE_NOT_CLOSED")
    # A3 fixture is not an authenticated live readback. Compare the entire
    # immutable source-free contract to forbid applicant-supplied API claims.
    require(type(vault_fixture) is dict
            and vault_fixture == fixture_report()
            and vault_fixture.get("live_github_private_metadata_readback") is False
            and vault_fixture.get("vault_media_write_authorized", False) is False,
            "A3_IS_OFFLINE_FIXTURE_ONLY")
    return {
        "schema_version": 1,
        "stage": STAGE,
        "channel_id": CHANNEL,
        "source_free_readiness_only": True,
        "public_creator_research_count": 5,
        "suggested_review_first_not_owner_selected": len(owner_matrix["research_first_only"]),
        "public_watchlist_sha256": owner_matrix["watchlist_sha256"],
        "public_route_audit_sha256": owner_matrix["route_audit_sha256"],
        "creator_rightsholder_grants_verified": 0,
        "creator_original_masters_received": 0,
        "authenticated_private_media_vault_approved": False,
        "github_private_metadata_readback_performed": False,
        "source_ingestion_enabled": False,
        "media_render_enabled": False,
        "owner_exact_media_release_signed": False,
        "youtube_upload_enabled": False,
        "youtube_publish_enabled": False,
        "real_p4_milestone_complete": False,
        "missing_real_world_dependencies": list(NEEDS),
        "status": HOLD,
    }


def actual_source_free_readiness(*, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "CLOCK")
    watchlist = load_watchlist(DATA)
    audit = load_public_route_audit()
    policy, registry = read_json(POLICY), read_json(REGISTRY)
    packet = compile_owner_pilot_packet(
        watchlist=watchlist, public_audit=audit,
        policy=policy, registry=registry, now=now)
    matrix = build_matrix(
        packet, watchlist=watchlist, public_audit=audit,
        policy=policy, registry=registry, now=now)
    return build_handoff_hold(
        owner_matrix=matrix, storage_gate=actual_closed_boundary(),
        vault_fixture=fixture_report(),
    )


def production_media_ingest(*args, **kwargs) -> None:
    raise HandoffDenied("CLIVOX_V2_P4_BRIDGE_DENIED_NO_REAL_SOURCE_ACCEPTANCE")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("closed",), default="closed")
    p.parse_args()
    try:
        print(json.dumps(actual_source_free_readiness(), sort_keys=True))
    except (ValueError, TypeError, KeyError, OSError):
        raise SystemExit("CLIVOX_V2_P4_BRIDGE_BLOCKED_NO_MEDIA_NO_RELEASE") from None


if __name__ == "__main__":
    main()
