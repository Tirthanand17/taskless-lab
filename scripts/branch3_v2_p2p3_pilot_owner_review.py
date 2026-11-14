"""CLIVOX V2 real-workflow P2/P3 PUBLIC route audit -> owner-ready UNSENT packet.

This is refreshed public research, NOT a recipient list, a selected creator,
a business route guaranteed to reach a licensor, a signed grant, or a license.
It composes the original P2 prospective-inquiry writer and P3/A2 rights
quarantine without contacting anyone or acquiring media. Output is strictly
ephemeral and has no destination addresses. Public URLs are references only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from scripts.branch3_v2_creator_prospect_intake import (
    CHANNEL, DATA, clean_string, compile_owner_research_packet,
    instant, load_watchlist, ProspectDenied, MAX_PUBLIC_AGE_DAYS,
)
from scripts.branch3_v2_p3_licensing_scope_quarantine import (
    CHECKS, LicensingScopeDenied, compile_scope_packet, request_terms,
)
from scripts.branch3_a2_review_receipt import (
    POLICY, REGISTRY, read_json as a2_read_json,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = ROOT / "branch3/clipping_v2/prospects/p2p3-public-route-review-2026-11-14.json"
OUT_NAME = "clivox-v2-p2p3-pilot-owner-review-UNSENT.json"
STAGE = "CLIVOX_V2_P2P3_REFRESHED_PUBLIC_ROUTE_TO_UNSIGNED_OWNER_REVIEW"
ID_ORDER = (
    "ankitt_ps5", "eggmilk_streamer", "mandarriaxl",
    "mrjd_gaming", "caseoh_format",
)
FIRST = ("ankitt_ps5", "eggmilk_streamer", "mandarriaxl")
EXPECT = {
    "ankitt_ps5": (
        "https://ankitt.com/",
        "FIRST_PILOT_INQUIRY_RECOMMENDATION_NOT_APPROVAL",
        "PUBLIC_CREATOR_BRANDED_COLLABORATION_PAGE",
    ),
    "eggmilk_streamer": (
        "https://eggmilk.carrd.co/",
        "FIRST_PILOT_INQUIRY_RECOMMENDATION_NOT_APPROVAL",
        "PUBLIC_CREATOR_BRANDED_PARTNERSHIP_PAGE",
    ),
    "mandarriaxl": (
        "https://www.mandarriaxl.com/",
        "FIRST_PILOT_INQUIRY_RECOMMENDATION_NOT_APPROVAL",
        "PUBLIC_CREATOR_BRANDED_PARTNERSHIP_PAGE",
    ),
    "mrjd_gaming": (
        "https://mrjdgaming.com/contact/",
        "DEFER_SOURCE_OWNERSHIP_AND_LONGFORM_FIT_REVIEW",
        "PUBLIC_GENERAL_BUSINESS_INQUIRY_PAGE",
    ),
    "caseoh_format": (
        "https://caseoh.com/pages/about-me",
        "FAMOUS_FORMAT_REFERENCE_NOT_PILOT_REQUEST",
        "PUBLIC_CREATOR_BRANDED_BUSINESS_PAGE",
    ),
}
TOP = frozenset({
    "schema_version", "stage", "channel_id", "observed_at_utc",
    "source_watchlist", "official_platform_policy", "research_only",
    "public_creator_contact_routes_observed", "owner_shortlist_approved",
    "legal_identity_authenticated",
    "creator_to_specific_media_ownership_authenticated",
    "creator_outreach_sent", "creator_replies_received",
    "authenticated_commercial_rights_grants", "authorized_media_files",
    "youtube_uploads", "human_creator_consent_for_each_source",
    "options", "route_review_expires_after_days",
    "no_personal_email_or_phone_saved",
    "no_youtube_api_derived_creator_ranking",
    "no_media_download_or_contact_tool_called", "expected_release_state",
})
ROW = frozenset({
    "prospect_id", "owner_review_group", "public_evidence_url",
    "observed_route_type", "observed_fit", "key_human_verification",
    "route_publicly_observed", "independent_creator_identity_authenticated",
    "current_rightsholder_signatory_authenticated",
    "source_media_verified_owned", "commercial_clipping_license_granted",
    "revenue_share_terms_agreed", "human_owner_approved_outreach",
    "outreach_sent",
})
OUTPUT = frozenset({
    "stage", "channel_id", "research_observed_utc",
    "source_watchlist_sha256", "public_route_audit_sha256",
    "route_research_expires_after_days", "owner_review_first_count",
    "owner_review_first_options", "deferred_or_format_only_options",
    "proposed_private_pilot_clips_per_creator", "license_scope_questions_each",
    "unsigned_negotiation_terms", "all_proposals_unsent",
    "all_owner_shortlist_selections_unapproved",
    "all_legal_creator_identities_unverified",
    "all_creators_rightsholder_permissions_unverified",
    "all_source_rights_and_guest_music_game_not_cleared",
    "creator_messages_sent", "creator_replies_received",
    "authenticated_licenses_received",
    "creator_source_files_delivered", "youtube_uploads",
    "revenue_predictions_generated", "real_youtube_api_requests",
    "owner_release_signed", "licensing_authorized",
    "media_download_authorized", "video_editing_authorized",
    "youtube_upload_authorized", "youtube_publish_authorized",
    "next_step", "status",
})
PENDING = "PENDING_HUMAN_AUTHENTICATION_NO_GRANT"


class PilotDenied(ValueError):
    """Never promote a public website into commercial rights."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise PilotDenied("CLIVOX_V2_P2P3_PILOT_DENIED_" + code)


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError):
        raise PilotDenied("CLIVOX_V2_P2P3_PILOT_DENIED_CANONICAL") from None


def validate_public_route_audit(audit: object, watchlist: dict,
                                *, now: datetime) -> dict:
    """Fresh public pages observed, never an authenticated identity or grant."""
    require(type(audit) is dict and set(audit) == TOP, "EXACT_AUDIT_FIELDS")
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "CLOCK")
    d = compile_owner_research_packet(watchlist, now=now)
    require(audit["schema_version"] == 1
            and type(audit["schema_version"]) is int
            and audit["stage"] ==
                "CLIVOX_V2_P2P3_PUBLIC_ROUTE_RESEARCH_OWNER_REVIEW_ONLY"
            and audit["channel_id"] == CHANNEL
            and audit["observed_at_utc"] == d["source_research_date_utc"]
            and audit["source_watchlist"] ==
                "branch3/clipping_v2/prospects/public-business-pages-2026-11-14.json"
            and audit["official_platform_policy"] ==
                "https://support.google.com/youtube/answer/1311392"
            and audit["expected_release_state"] ==
                "BLOCKED_BEFORE_OWNER_VERIFIED_SHORTLIST_AND_SIGNED_GRANT",
            "SOURCE_LINKAGE_OR_STATUS")
    obs = instant(audit["observed_at_utc"])
    require(timedelta(0) <= now.astimezone(timezone.utc)-obs
            <= timedelta(days=MAX_PUBLIC_AGE_DAYS), "STALE_PUBLIC_ROUTE_RESEARCH")
    for k in (
        "research_only", "no_personal_email_or_phone_saved",
        "no_youtube_api_derived_creator_ranking",
        "no_media_download_or_contact_tool_called",
    ):
        require(audit[k] is True, "RESEARCH_FLAG_" + k.upper())
    for k in (
        "owner_shortlist_approved", "legal_identity_authenticated",
        "creator_to_specific_media_ownership_authenticated",
        "human_creator_consent_for_each_source",
    ):
        require(audit[k] is False, "FORGED_VERIFIED_" + k.upper())
    for k in ("creator_outreach_sent", "creator_replies_received",
              "authenticated_commercial_rights_grants", "authorized_media_files",
              "youtube_uploads"):
        require(type(audit[k]) is int and audit[k] == 0,
                "FORGED_COUNT_" + k.upper())
    require(type(audit["public_creator_contact_routes_observed"]) is int
            and audit["public_creator_contact_routes_observed"] == 5
            and type(audit["route_review_expires_after_days"]) is int
            and audit["route_review_expires_after_days"] == 30,
            "OBSERVATIONS_AND_EXPIRY")
    options = audit["options"]
    require(type(options) is list and len(options) == len(ID_ORDER),
            "EXACT_RESEARCH_OPTIONS")
    by_id = {q["id"]: q for q in d["review_queue"]}
    for idx, item in enumerate(options):
        require(type(item) is dict and set(item) == ROW, "PUBLIC_OPTION_SCHEMA")
        key = ID_ORDER[idx]
        expected = EXPECT[key]
        require(item["prospect_id"] == key
                and item["public_evidence_url"] == expected[0]
                and item["owner_review_group"] == expected[1]
                and item["observed_route_type"] == expected[2]
                and item["public_evidence_url"] ==
                    by_id[key]["business_reference_page"],
                "ROUTE_MUST_MATCH_ORIGINAL_P2")
        clean_string(item["observed_fit"], 190)
        clean_string(item["key_human_verification"], 190)
        require(item["route_publicly_observed"] is True,
                "PUBLIC_ROUTE_NOT_OBSERVED")
        for k in (
            "independent_creator_identity_authenticated",
            "current_rightsholder_signatory_authenticated",
            "source_media_verified_owned",
            "commercial_clipping_license_granted",
            "revenue_share_terms_agreed",
            "human_owner_approved_outreach",
            "outreach_sent",
        ):
            require(item[k] is False, "NO_REAL_GRANT_" + k.upper())
    require(
        b"@" not in canonical(audit) and b"access_token" not in canonical(audit)
        and b"youtube.com/watch?" not in canonical(audit),
        "NO_PRIVATE_CONTACT_OR_SOURCE_ID"
    )
    return audit


def load_public_route_audit(path: Path = AUDIT_FILE) -> dict:
    require(isinstance(path, Path) and path == AUDIT_FILE
            and path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= 25_000,
            "ONLY_CHECKED_IN_PUBLIC_AUDIT")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise PilotDenied("CLIVOX_V2_P2P3_PILOT_DENIED_AUDIT_JSON") from None
    return data


def _compose_owner_packet(*, watchlist: dict, public_audit: dict,
                          policy: dict, registry: dict,
                          now: datetime) -> dict:
    validate_public_route_audit(public_audit, watchlist, now=now)
    # Existing P3/A2 validator: all real grants/signatures/revocations remain
    # explicitly absent. Source IDs from synthetic A2 cases never attach here.
    p3 = compile_scope_packet(watchlist, policy, registry, now=now)
    require(p3["channel_id"] == CHANNEL
            and p3["actual_creator_grants_verified"] == 0
            and p3["actually_signed_contracts_received"] == 0
            and p3["creator_outreach_calls"] == 0
            and p3["source_footage_delivered"] is False
            and p3["clivox_youtube_upload_authorized"] is False
            and p3["source_case_binding_policy"] ==
                "NO_CROSSWALK_UNTIL_INDEPENDENT_HUMAN_IDENTITY",
            "P3_RELEASE_AND_SOURCE_QUARANTINE")
    p2 = compile_owner_research_packet(watchlist, now=now)
    by_p2 = {x["id"]: x for x in p2["review_queue"]}
    by_p3 = {x["prospect_id"]: x for x in p3["prospect_scope_review_queue"]}
    priority, held = [], []
    for row in public_audit["options"]:
        key = row["prospect_id"]
        p2row, p3row = by_p2[key], by_p3[key]
        require(p3row["unsigned_scope_request"] == request_terms()
                and len(p3row["checklist"]) == len(CHECKS)
                and all(x == PENDING for x in p3row["checklist"].values())
                and p3row["source_video_id"] is None
                and p3row["source_video_rightsholder_link_verified"] is False
                and p3row["creator_signed_grant_received"] is False,
                "P3_PENDING_AND_UNBOUND")
        draft = p2row["proposed_outreach"]
        require(draft["recipient_address"] is None
                and draft["state"] ==
                "UNSENT_DRAFT_FOR_OWNER_APPROVAL_ONLY"
                and draft["sent"] is False
                and draft["license_verified"] is False
                and draft["publishing_authorized"] is False,
                "P2_UNSENT_DRAFT_ONLY")
        option = {
            "prospect_id": key,
            "display_name": p2row["name"],
            "public_business_reference": row["public_evidence_url"],
            "research_lane": p2row["lane"],
            "research_rationale": row["observed_fit"],
            "manual_due_diligence": row["key_human_verification"],
            "research_group_not_owner_selection": row["owner_review_group"],
            "recipient_address": None,
            "unsent_subject": draft["subject"],
            "unsent_message": draft["body"],
            "actual_owner_shortlist_selected": False,
            "business_route_independently_authenticated": False,
            "actual_signatory_authorized": False,
            "source_video_grant_verified": False,
            "human_originality_editorial_approved": False,
            "commercial_youtube_license_granted": False,
            "rights_checklist_pending_count": len(CHECKS),
            "allow_contact": False,
            "allow_source_download": False,
            "allow_upload": False,
        }
        (priority if key in FIRST else held).append(option)
    require([x["prospect_id"] for x in priority] == list(FIRST)
            and [x["prospect_id"] for x in held] ==
                ["mrjd_gaming", "caseoh_format"],
            "RESEARCH_ORDER_NOT_OWNER_APPROVED")
    result = {
        "stage": STAGE,
        "channel_id": CHANNEL,
        "research_observed_utc": public_audit["observed_at_utc"],
        "source_watchlist_sha256": p2["research_input_sha256"],
        "public_route_audit_sha256":
            hashlib.sha256(canonical(public_audit)).hexdigest(),
        "route_research_expires_after_days": 30,
        "owner_review_first_count": 3,
        "owner_review_first_options": priority,
        "deferred_or_format_only_options": held,
        "proposed_private_pilot_clips_per_creator": 3,
        "license_scope_questions_each": len(CHECKS),
        "unsigned_negotiation_terms": request_terms(),
        "all_proposals_unsent": True,
        "all_owner_shortlist_selections_unapproved": True,
        "all_legal_creator_identities_unverified": True,
        "all_creators_rightsholder_permissions_unverified": True,
        "all_source_rights_and_guest_music_game_not_cleared": True,
        "creator_messages_sent": 0,
        "creator_replies_received": 0,
        "authenticated_licenses_received": 0,
        "creator_source_files_delivered": 0,
        "youtube_uploads": 0,
        "revenue_predictions_generated": False,
        "real_youtube_api_requests": 0,
        "owner_release_signed": False,
        "licensing_authorized": False,
        "media_download_authorized": False,
        "video_editing_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_publish_authorized": False,
        "next_step":
            "OWNER_INDEPENDENTLY_VERIFY_CREATOR_CHANNELS_RIGHTSHOLDER_IDENTITY_AND_SELECT_BEFORE_ANY_OUTREACH",
        "status":
            "PUBLIC_BUSINESS_ROUTE_REVIEW_ONLY_NO_OWNER_SELECTION_NO_LICENSE",
    }
    return result


def compile_owner_pilot_packet(*, watchlist: dict, public_audit: dict,
                               policy: dict, registry: dict,
                               now: datetime) -> dict:
    packet = _compose_owner_packet(
        watchlist=watchlist, public_audit=public_audit,
        policy=policy, registry=registry, now=now)
    return validate_owner_packet(
        packet, public_audit=public_audit, watchlist=watchlist,
        policy=policy, registry=registry, now=now)


def validate_owner_packet(packet: object, *, public_audit: dict,
                          watchlist: dict, policy: dict, registry: dict,
                          now: datetime) -> dict:
    """Reconstruct strict output from original P2/P3; forged fields fail."""
    require(type(packet) is dict and set(packet) == OUTPUT,
            "EXACT_OWNER_REVIEW_PACKET_FIELDS")
    # Independent deterministic reconstruction; no mutable global monkeypatch
    # or trust in caller-injected owner/signature/creator permission fields.
    reference = _compose_owner_packet(
        public_audit=public_audit, watchlist=watchlist, policy=policy,
        registry=registry, now=now
    )
    require(canonical(packet) == canonical(reference),
            "ANY_UNAUTHORIZED_OWNER_LICENSE_EDIT_OR_PUBLIC_CONTACT")
    return packet


def production_contact_license_or_clip(*_args, **_kwargs) -> None:
    raise PilotDenied(
        "CLIVOX_V2_P2P3_PILOT_DENIED_NO_REAL_OWNER_OR_CREATOR_GRANT"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "review"), default="closed")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        watchlist = load_watchlist(DATA)
        audit = load_public_route_audit()
        now = datetime.now(timezone.utc)
        validate_public_route_audit(audit, watchlist, now=now)
        policy, registry = a2_read_json(POLICY), a2_read_json(REGISTRY)
        if args.mode == "closed":
            require(args.out is None, "CLOSED_ARGS")
            response = {
                "stage": "CLIVOX_V2_P2P3_NO_CREATOR_CONTACT",
                "channel_id": CHANNEL,
                "owner_shortlist_approved": False,
                "commercial_rights_grants": 0,
                "media_downloads": 0, "youtube_uploads": 0,
            }
        else:
            target = args.out
            require(target is not None and target.name == OUT_NAME
                    and not target.exists() and not target.is_symlink()
                    and target.parent.is_dir()
                    and not target.parent.is_symlink()
                    and ROOT not in target.absolute().parents,
                    "OUTPUT_EPHEMERAL_UNSENT_ONLY")
            response = compile_owner_pilot_packet(
                watchlist=watchlist, public_audit=audit,
                policy=policy, registry=registry, now=now
            )
            target.write_text(json.dumps(response, indent=2) + "\n",
                              encoding="utf-8")
            target.chmod(0o600)
            response = {
                "stage": STAGE, "channel_id": CHANNEL,
                "research_review_first_count": 3,
                "other_research_or_deferred_count": 2,
                "pilot_drafts_created_in_ephemeral_dir_only": True,
                "outreach_sent": 0, "creator_rights_granted": 0,
                "media_downloads": 0, "youtube_uploads": 0,
                "owner_human_approval_verified": False,
            }
        print(json.dumps(response, sort_keys=True))
    except (PilotDenied, ProspectDenied, LicensingScopeDenied, OSError,
            TypeError, ValueError, KeyError, UnicodeError):
        raise SystemExit(
            "CLIVOX_V2_P2P3_DENIED_NO_CREATOR_RIGHTS_NO_CONTACT_NO_UPLOAD"
        ) from None


if __name__ == "__main__":
    main()
