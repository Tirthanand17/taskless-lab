"""Source-free owner decision matrix for CLIVOX creator pilots.

Produces deterministic UNAPPROVED review priorities from existing validated
P2/P3 evidence. This module never asserts legal approval or invokes network,
creator contact, video download or YouTube upload.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.branch3_v2_p2p3_pilot_owner_review import (
    AUDIT_FILE, CHANNEL, FIRST, ID_ORDER, OUT_NAME,
    compile_owner_pilot_packet, load_public_route_audit,
    validate_owner_packet,
)
from scripts.branch3_v2_creator_prospect_intake import DATA, load_watchlist
from scripts.branch3_a2_review_receipt import POLICY, REGISTRY, read_json

ROOT = Path(__file__).resolve().parents[1]
REPORT_NAME = "clivox-v2-p2p3-owner-decision-matrix-HOLD.json"
BLOCKED = "BLOCKED_PENDING_HUMAN_SELECTION_IDENTITY_AND_COMMERCIAL_GRANT"


def build_matrix(packet: dict, *, watchlist: dict, public_audit: dict,
                 policy: dict, registry: dict, now: datetime) -> dict:
    """Revalidate against originals; never trust supplied permission flags."""
    validate_owner_packet(packet, watchlist=watchlist, public_audit=public_audit,
                          policy=policy, registry=registry, now=now)
    groups = packet["owner_review_first_options"] + packet["deferred_or_format_only_options"]
    rows = []
    for position, item in enumerate(groups):
        assert item["prospect_id"] == ID_ORDER[position]
        rows.append({
            "prospect_id": item["prospect_id"],
            "owner_review_priority": "REVIEW_FIRST_NOT_APPROVED" if position < len(FIRST)
                                    else "DEFER_OR_FORMAT_ONLY",
            "public_reference": item["public_business_reference"],
            "owner_selection_recorded": False,
            "identity_authentication_complete": False,
            "legal_signatory_authenticated": False,
            "specific_source_media_rights_cleared": False,
            "commercial_youtube_short_license_verified": False,
            "underlying_music_guests_and_game_rights_cleared": False,
            "private_source_handoff_authorized": False,
            "owner_exact_media_release_signed": False,
            "outreach_authorized": False,
            "clip_generation_authorized": False,
            "youtube_upload_authorized": False,
            "youtube_publish_authorized": False,
            "pending_rights_questions": item["rights_checklist_pending_count"],
            "status": BLOCKED,
            "next_human_step": item["manual_due_diligence"],
        })
    return {
        "schema_version": 1,
        "stage": "CLIVOX_V2_P2P3_OWNER_DECISION_MATRIX_SOURCE_FREE_HOLD",
        "channel_id": CHANNEL,
        "research_observed_utc": packet["research_observed_utc"],
        "watchlist_sha256": packet["source_watchlist_sha256"],
        "route_audit_sha256": packet["public_route_audit_sha256"],
        "prospects_total": 5,
        "research_first_only": list(FIRST),
        "creator_outreach_sent": 0,
        "licensed_media_delivered": 0,
        "youtube_uploads": 0,
        "owner_approval_received": False,
        "license_received": False,
        "all_actions_blocked": True,
        "rows": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    out = args.out
    # Keep user decision artifacts ephemeral; GitHub repo is not a private contract vault.
    if (out.name != REPORT_NAME or out.exists() or out.is_symlink()
            or not out.parent.is_dir() or out.parent.is_symlink()
            or ROOT in out.absolute().parents):
        raise SystemExit("CLIVOX_OWNER_MATRIX_DENIED_UNSAFE_OUTPUT")
    now = datetime.now(timezone.utc)
    watch = load_watchlist(DATA)
    audit = load_public_route_audit()
    policy, registry = read_json(POLICY), read_json(REGISTRY)
    packet = compile_owner_pilot_packet(
        watchlist=watch, public_audit=audit, policy=policy,
        registry=registry, now=now
    )
    result = build_matrix(packet, watchlist=watch, public_audit=audit,
                          policy=policy, registry=registry, now=now)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    out.chmod(0o600)
    print("CLIVOX_V2_OWNER_MATRIX_REVIEW_ONLY_5_PROSPECTS_ZERO_GRANTS_OR_UPLOADS")


if __name__ == "__main__":
    main()
