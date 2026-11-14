"""CLIVOX V2 P3: licensing-scope intake/quarantine, NOT license approval.

Builds source-free and contact-free research questionnaires. Reuses real A2
pending-case/zero-grant policy validators and segregates synthetic source cases
from named public creator prospects, because creator-to-video legal ownership
has not been authenticated. NEVER promotes source rights, accepts contracts,
contacts anyone, fetches media or accesses YouTube write APIs.

Only synthetic source references from the existing A1 fixture are used in CI.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from scripts.branch3_discovery import build_report, mock_fixture
from scripts.branch3_rights_case_intake import build_rights_cases, PENDING_CHECKS
from scripts.branch3_a2_review_receipt import (
    POLICY, REGISTRY, validate_closed_policy, verify_pending_case, read_json
)
from scripts.branch3_v2_creator_prospect_intake import (
    DATA as PROSPECT_DATA, CHANNEL, compile_owner_research_packet,
    load_watchlist
)

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 200_000
EXPECTED_OUT = "clivox-v2-p3-unsigned-license-scope-HOLD.json"
CHECKS = tuple(PENDING_CHECKS) + (
    "real_prospect_identity_independently_authenticated",
    "prospect_to_source_channel_legal_link_verified",
    "source_video_specific_commercial_scope_approved",
    "authorized_source_delivery_without_platform_download",
    "commercial_monetization_and_revenue_share_terms_agreed",
    "clip_limit_and_allowed_timestamps_agreed",
    "creator_publication_review_and_approval_process_agreed",
    "contract_territories_and_platforms_exactly_agreed",
    "underlying_music_guest_publisher_sponsor_exclusions",
    "creator_royalty_payment_tax_and_invoicing_review",
    "license_restrictions_on_exclusivity_or_edit_ip_assignment",
    "claim_dispute_and_revocation_notice_sla",
    "legal_signatory_and_actual_contract_evidence_authenticated",
    "independently_enrolled_reviewer_key_and_complete_revocation_feed",
    "owner_private_media_vault_security_and_acl_approved",
    "exact_CLIVOX_owner_upload_consent_separately_approved",
)
REQUIRED_SCOPE_KEYS = frozenset({
    "requested_channel_id", "requested_platform",
    "commercial_youtube_redistribution_requested",
    "ads_monetization_requested", "original_commentary_requested",
    "edit_crop_caption_and_sound_requested", "number_of_private_pilot_clips",
    "requested_territory", "requested_term_days",
    "requested_source_delivery_route", "requested_attribution",
    "requested_creator_final_review", "request_only_not_agreement",
    "no_terms_accepted", "no_license_granted",
})
TERMS = {
    "requested_channel_id": CHANNEL,
    "requested_platform": "YOUTUBE_SHORTS_ONLY",
    "commercial_youtube_redistribution_requested": True,
    "ads_monetization_requested": True,
    "original_commentary_requested": True,
    "edit_crop_caption_and_sound_requested": True,
    "number_of_private_pilot_clips": 3,
    "requested_territory": "WORLDWIDE_SUBJECT_TO_WRITTEN_AGREEMENT",
    "requested_term_days": 90,
    "requested_source_delivery_route": "DIRECT_CREATOR_FILE_OR_AUTHORIZED_EDITOR",
    "requested_attribution": "CREATOR_AND_LICENSE_REQUIRED_CREDIT",
    "requested_creator_final_review": True,
    "request_only_not_agreement": True,
    "no_terms_accepted": True,
    "no_license_granted": True,
}
FORBIDDEN_FIELDS = frozenset({
    "rights_verified", "license_granted", "approved", "owner_approved",
    "human_approved", "creator_contacted", "creator_permission_verified",
    "media_download_authorized", "source_media_acquired",
    "publishing_authorized", "youtube_upload_authorized",
    "creator_grant_evidence_sha256", "creator_contract_text",
    "contract_document", "contact_email", "contact_phone",
    "source_rightsholder_signed", "verified_replay_peaks",
})
SHA = re.compile(r"[a-f0-9]{64}\Z")


class LicensingScopeDenied(ValueError):
    """Input claims authority or introduces private/off-policy source data."""


def require(value: bool, reason: str) -> None:
    if not value:
        raise LicensingScopeDenied("CLIVOX_V2_P3_DENIED_" + reason)


def canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def request_terms() -> dict:
    """Negotiating ASK, not a permission from the actual rights holder."""
    return dict(TERMS)


def validate_unsigned_request(request: object) -> dict:
    require(type(request) is dict and set(request) == REQUIRED_SCOPE_KEYS,
            "EXACT_REQUEST_TERMS_FIELDS")
    require(not (set(request) & FORBIDDEN_FIELDS), "UNTRUSTED_APPROVAL_FIELD")
    for key, expected in TERMS.items():
        require(type(request.get(key)) is type(expected)
                and request.get(key) == expected,
                "UNAUTHORIZED_SCOPE_OR_FAKE_AGREEMENT_" + key.upper())
    return dict(request)


def review_checklist() -> dict:
    """Human questions. All UNKNOWN, none is self-approvable by automation."""
    require(len(CHECKS) == len(set(CHECKS)), "DUPLICATE_CHECK")
    return {key: "PENDING_HUMAN_AUTHENTICATION_NO_GRANT" for key in CHECKS}


def verify_no_production_rights(policy: object, registry: object) -> None:
    # Upstream A2 uses real policy/registry validation; don't rewrite it.
    try:
        validate_closed_policy(policy, registry)
    except (ValueError, TypeError, KeyError) as exc:
        raise LicensingScopeDenied(
            "CLIVOX_V2_P3_DENIED_A2_POLICY_OR_APPROVED_CREATOR_FORGED"
        ) from None


def source_case_reference(case: object) -> dict:
    """Reference to an A2 case, deliberately NEVER attached to a prospect."""
    require(type(case) is dict, "A2_CASE_INVALID")
    try:
        case_sha = verify_pending_case(case)
    except (ValueError, TypeError, KeyError):
        raise LicensingScopeDenied("CLIVOX_V2_P3_DENIED_A2_CASE_NOT_PENDING") from None
    require(type(case.get("case_is_synthetic")) is bool,
            "CASE_SYNTHETIC_MARKER")
    return {
        "a2_case_id": case["case_id"],
        "source_video_id": case["source_video_id"],
        "source_channel_id": case["source_channel_id"],
        "a2_pending_case_sha256": case_sha,
        "synthetic_fixture": case["case_is_synthetic"],
        "potential_creator_prospect_id": None,
        "actual_source_to_prospect_ownership_verified": False,
        "source_authority_document_verified": False,
        "source_license_exists": False,
        "scope_review_checklist": review_checklist(),
        "ready_for_media_acquisition": False,
        "next_step": "HUMAN_LINK_SOURCE_TO_ACTUAL_RIGHTSHOLDER_WITH_PRIVATE_EVIDENCE",
    }


def compile_scope_packet(
    watchlist: object, policy: object, registry: object, *,
    now: datetime, unsigned_terms: dict | None = None
) -> dict:
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "AWARE_CLOCK")
    verify_no_production_rights(policy, registry)
    terms = validate_unsigned_request(
        request_terms() if unsigned_terms is None else unsigned_terms
    )
    # Reuse P2 validated public branded references without picking a real
    # human-authorized partner or preserving personal/business contact details.
    p2 = compile_owner_research_packet(watchlist, now=now)
    require(p2["channel_id"] == CHANNEL and p2["all_proposals_unsent"] is True
            and p2["human_shortlist_approved"] is False
            and p2["real_creator_contacts_sent"] == 0
            and p2["creator_grants_verified"] == 0
            and p2["licensed_source_media_access_authorized"] is False,
            "P2_CONTACT_OR_OWNER_APPROVAL_FORGED")
    rows = []
    for item in p2["review_queue"]:
        require(item["rights_review_case_state"] ==
                "NOT_STARTED_NO_CREATOR_GRANT"
                and item["proposed_outreach"]["sent"] is False
                and item["owner_shortlist_review_state"] ==
                    "PENDING_REAL_HUMAN_REVIEW",
                "P2_CASE_NOT_PENDING")
        rows.append({
            "prospect_id": item["id"],
            "research_source_page": item["creator_page"],
            "public_business_reference_page": item["business_reference_page"],
            "research_fingerprint_sha256": p2["research_input_sha256"],
            "identity_and_business_route_independently_authenticated": False,
            "human_owner_shortlist_selected": False,
            "creator_has_been_contacted": False,
            "creator_has_replied": False,
            "creator_signed_grant_received": False,
            "source_video_id": None,
            "source_video_rightsholder_link_verified": False,
            "a2_pending_source_case_id": None,
            "a2_pending_source_case_sha256": None,
            "unsigned_scope_request": dict(terms),
            "checklist": review_checklist(),
            "rights_review_state": "P3_SCOPE_QUESTIONS_ONLY_NOT_A_LICENSE",
            "licensing_authorized": False,
            "source_media_acquisition_authorized": False,
            "editing_authorized": False,
            "youtube_upload_authorized": False,
            "youtube_publish_authorized": False,
            "next_step": "OWNER_AUTHENTICATE_CREATOR_AND_SELECT_OUTREACH_PROSPECT",
        })
    return {
        "schema_version": 1,
        "stage": "CLIVOX_V2_P3_CONTRACT_SCOPE_INTAKE_QUARANTINED",
        "channel_id": CHANNEL,
        "p2_exact_research_sha256": p2["research_input_sha256"],
        "retrieved_at_utc": now.astimezone(timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z"),
        "research_prospects_count": len(rows),
        "rights_scope_checks_per_prospect": len(CHECKS),
        "questions_are_for_negotiation_only": True,
        "unsigned_requests_generated": len(rows),
        "creator_legal_identity_authenticated": False,
        "creator_to_source_ownership_authenticated": False,
        "actually_signed_contracts_received": 0,
        "actual_creator_grants_verified": 0,
        "owner_review_completed": False,
        "real_reviewer_key_enrolled": False,
        "real_revocation_head_pinned": False,
        "private_legal_vault_approved": False,
        "source_footage_delivered": False,
        "media_acquisition_authorized": False,
        "clivox_youtube_upload_authorized": False,
        "clivox_youtube_publish_authorized": False,
        "youtube_api_calls": 0,
        "creator_outreach_calls": 0,
        "source_media_downloads": 0,
        "public_output_contains_private_contracts": False,
        "source_case_binding_policy": "NO_CROSSWALK_UNTIL_INDEPENDENT_HUMAN_IDENTITY",
        "prospect_scope_review_queue": rows,
    }


def compile_a2_synthetic_source_examples(*, now: datetime) -> dict:
    """Exercise existing A1→A2→signed-review pending checks, not a creator link."""
    fixture = build_report(
        mock_fixture(), category="gaming", mode="fixture",
        query="", now=now, fixture=True
    )
    ts = now.astimezone(timezone.utc).isoformat(
        timespec="seconds").replace("+00:00", "Z")
    cases = build_rights_cases(fixture, generated_at_utc=ts)
    require(cases["creator_permission_grants_issued_by_this_workflow"] == 0
            and cases["youtube_writes"] == 0
            and cases["media_downloads"] == 0
            and cases["is_synthetic_fixture"] is True,
            "A2_SYNTHETIC_FIXTURE_NOT_SAFE")
    refs = [source_case_reference(c) for c in cases["cases"]]
    require(all(c["potential_creator_prospect_id"] is None
                and c["actual_source_to_prospect_ownership_verified"] is False
                and c["source_license_exists"] is False
                and c["ready_for_media_acquisition"] is False
                for c in refs), "UNAUTHORIZED_SOURCE_PROSPECT_LINK")
    return {
        "status": "SYNTHETIC_A2_PENDING_CASES_UNLINKED_TO_ANY_REAL_CREATOR",
        "a1_synthetic": True,
        "source_report_sha256": cases["source_report_sha256"],
        "source_case_count": len(refs),
        "real_source_licenses": 0,
        "synthetic_cases_only": refs,
    }


def build_p3_offline_handoff(
    *, watchlist: object, policy: object, registry: object, now: datetime
) -> dict:
    """No actual license can be created from public fixtures."""
    result = compile_scope_packet(watchlist, policy, registry, now=now)
    result["separate_unlinked_synthetic_a2_cases"] = (
        compile_a2_synthetic_source_examples(now=now)
    )
    # Digest does NOT sign or authenticate the owner or actual rights holder.
    result["research_only_packet_sha256"] = hashlib.sha256(
        canonical(result)
    ).hexdigest()
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=PROSPECT_DATA)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        target = args.out.absolute()
        require(
            target.name == EXPECTED_OUT
            and target.suffix == ".json"
            and not target.is_symlink() and not target.exists()
            and target.parent.is_dir()
            and ROOT not in target.parents,
            "EPHEMERAL_OUTSIDE_PUBLIC_REPO_NEW_FILE_REQUIRED"
        )
        packet = build_p3_offline_handoff(
            watchlist=load_watchlist(args.input),
            policy=read_json(POLICY), registry=read_json(REGISTRY),
            now=datetime.now(timezone.utc)
        )
        require(len(canonical(packet)) <= MAX_BYTES, "REPORT_TOO_LARGE")
        target.write_text(
            json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        try:
            target.chmod(0o600)
        except OSError:
            pass
        print(
            "CLIVOX_V2_P3_SCOPE_QUARANTINE"
            f" prospects={packet['research_prospects_count']}"
            f" pending_checks_each={packet['rights_scope_checks_per_prospect']}"
            " creator_contacts=0 grants=0 source_media=0 youtube_writes=0"
        )
    except (LicensingScopeDenied, ValueError, TypeError, KeyError, OSError):
        raise SystemExit(
            "CLIVOX_V2_P3_DENIED_NO_LIVE_RIGHTS_NO_MEDIA_NO_YOUTUBE"
        ) from None


if __name__ == "__main__":
    main()
