"""CLIVOX V2 P9: NO-NETWORK, fail-closed YouTube private-first upload preflight.

This is a *dry-run safety contract*, not an uploader. It consumes the exact
P8 UNSIGNED review packet for an original FFmpeg synthetic fixture, rechecks
the bytes, then proves that A6 ownership, A7 OAuth and A8 durable attempt
conditions are missing. No Google API, HTTP transport, credentials, upload,
resumable session, remote inventory or scheduler exists in this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from scripts.branch3_v2_p5_synthetic_moment_proposals import (
    CHANNEL, P5Denied, _probe_closed,
)
from scripts.branch3_v2_p8_synthetic_unsigned_review import (
    P8Denied, EDL_FILE, QA_FILE, REVIEW_FILE, MAX_JSON_BYTES,
    canonical, closed_release_boundary, _read_ephemeral,
    _hash_exact_synthetic_mp4, validate_unsigned_packet,
)
from scripts.branch3_a7_readonly_youtube import (
    ChannelBindingDenied, synthetic_fixture_report,
)
from scripts.branch3_a8_private_first_dryrun import (
    PLAN as A8_PLAN, LEDGER as A8_LEDGER, DryRunBlocked,
    validate_fixture, reserve_attempt_preview,
    reconcile_ambiguous_attempt, perform_upload_or_schedule,
)
from scripts.branch3_a8_private_cas_ledger import (
    POLICY as A8_CAS_POLICY, PrivateCASBlocked,
)
from scripts.branch3_a6_signed_release import (
    ReleaseBlocked, production_release,
)

DOMAIN = b"CLIVOX-V2-P9-UNAUTHORIZED-SYNTHETIC-ATTEMPT-V1\n"
STAGE = "CLIVOX_V2_P9_PRIVATE_FIRST_INERT_PREFLIGHT_ONLY"
ID = re.compile(r"[0-9a-f]{64}\Z")
OUTCOMES = frozenset((
    "NO_ATTEMPT",
    "DUPLICATE_LOCAL_PREVIEW",
    "UNKNOWN_REMOTE_COMMIT_PREVIEW",
))
TEMPLATE = {
    "mode": "INERT_MODEL_NOT_HTTP_REQUEST",
    "api_concept": "videos.insert",
    "channel_id": CHANNEL,
    "part": ["snippet", "status"],
    "snippet": {
        "title": "CLIVOX Synthetic Scene Timing Test - NOT FOR UPLOAD",
        "description": "Original black/white/sine benchmark. No real creator material.",
        "categoryId": "24",
    },
    "status": {
        "privacyStatus": "private",
        "publishAt": None,
    },
    "source_scope": "GENERATED_TEST_VIDEO_ONLY",
    "ready_to_send": False,
    "upload_session_created": False,
    "real_youtube_write_allowed": False,
}
PUBLIC_REPORT_FIELDS = frozenset({
    "stage", "channel_id", "source_scope", "p8_unsigned_packet_bound_to_exact_video",
    "owner_signature_independently_verified", "creator_commercial_rights_verified",
    "clivox_upload_oauth_verified", "durable_atomic_attempt_reservation_verified",
    "real_remote_inventory_reconciled", "inert_private_first_template_validated",
    "automatic_retry_enabled", "resume_session_created", "remote_http_calls",
    "actual_youtube_uploads", "youtube_upload_authorized",
    "youtube_schedule_authorized", "youtube_publish_authorized",
    "dryrun_outcome", "dryrun_duplicate_detected",
    "dryrun_remote_uncertainty_quarantined", "real_p9_milestone_complete", "status",
})


class P9Denied(ValueError):
    """An untrusted publication preflight must never permit a write."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise P9Denied("CLIVOX_V2_P9_DENIED_" + reason)


def _closed_live_policies() -> None:
    """Check *actual* policy files; fixture or flag changes never create rights."""
    closed_release_boundary()
    a7 = synthetic_fixture_report()  # public fixture only; no OAuth or network
    require(a7["channel_id"] == CHANNEL
            and a7["fixture_identity_check_passed"] is True
            and a7["actual_clivox_oauth_verified"] is False
            and a7["actual_api_requests"] == 0
            and a7["upload_authorized"] is False
            and a7["publish_authorized"] is False,
            "A7_REAL_OAUTH_MUST_BE_ABSENT")
    try:
        a8 = validate_fixture(
            json.loads(A8_PLAN.read_text(encoding="utf-8")),
            json.loads(A8_LEDGER.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError, DryRunBlocked):
        raise P9Denied("CLIVOX_V2_P9_DENIED_A8_DRYRUN_CONTRACT") from None
    require(a8["channel_id"] == CHANNEL
            and a8["persistent_atomic_upload_lock_implemented"] is False
            and a8["remote_video_inventory_reconciled"] is False
            and a8["real_exact_asset_signed"] is False
            and a8["actual_youtube_network_calls"] == 0
            and a8["youtube_upload_authorized"] is False
            and a8["youtube_schedule_authorized"] is False,
            "A8_DRYRUN_NOT_A_PRODUCTION_WRITE")
    try:
        policy = json.loads(A8_CAS_POLICY.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise P9Denied("CLIVOX_V2_P9_DENIED_A8_CAS_POLICY") from None
    require(type(policy) is dict and set(policy) == {
        "schema_version", "channel_id", "phase", "private_vault_name_selected",
        "owner_private_vault_approved", "private_upload_ledger_bootstrapped",
        "dedicated_contents_write_token_configured",
        "owner_protected_upload_environment_verified",
        "real_independent_ledger_anchor_enrolled",
        "actual_github_get_put_enabled",
        "cross_runner_durable_ledger_verified", "creator_licenses_authenticated",
        "real_owner_video_signatures_verified",
        "real_clivox_upload_oauth_configured", "youtube_api_writes_enabled",
        "source_media_downloads_enabled", "state",
    }, "CAS_POLICY_FIELDS")
    require(type(policy["schema_version"]) is int and
            policy["schema_version"] == 1
            and policy["channel_id"] == CHANNEL
            and policy["phase"] == "A8_PRIVATE_CAS_PROTOCOL_OFFLINE_ONLY"
            and policy["state"] == "NO_LIVE_UPLOADS_OR_CROSS_RUN_STORE",
            "A8_CAS_IDENTITY")
    for name in (
        "private_vault_name_selected", "owner_private_vault_approved",
        "private_upload_ledger_bootstrapped",
        "dedicated_contents_write_token_configured",
        "owner_protected_upload_environment_verified",
        "real_independent_ledger_anchor_enrolled",
        "actual_github_get_put_enabled", "cross_runner_durable_ledger_verified",
        "real_clivox_upload_oauth_configured", "youtube_api_writes_enabled",
        "source_media_downloads_enabled",
    ):
        require(policy[name] is False, "A8_CAS_CONTROL_" + name.upper())
    require(type(policy["creator_licenses_authenticated"]) is int
            and policy["creator_licenses_authenticated"] == 0
            and type(policy["real_owner_video_signatures_verified"]) is int
            and policy["real_owner_video_signatures_verified"] == 0,
            "A8_CAS_FALSE_AUTHORITY")


def validate_inert_template(template: object) -> dict:
    """No usable upload request can be built from untrusted caller metadata."""
    require(type(template) is dict and template == TEMPLATE
            and type(template.get("status")) is dict
            and set(template["status"]) == {"privacyStatus", "publishAt"}
            and template["status"]["privacyStatus"] == "private"
            and template["status"]["publishAt"] is None
            and type(template.get("snippet")) is dict
            and set(template["snippet"]) ==
            {"title", "description", "categoryId"}
            and template["ready_to_send"] is False
            and template["upload_session_created"] is False
            and template["real_youtube_write_allowed"] is False,
            "INERT_PRIVATE_FIRST_TEMPLATE")
    return template


def _read_unsigned(scratch: Path) -> dict:
    require(isinstance(scratch, Path) and scratch.is_dir()
            and not scratch.is_symlink(), "RUNNER_SCRATCH_ONLY")
    base = scratch.resolve(strict=True)
    target = base / REVIEW_FILE
    require(target.is_file() and not target.is_symlink()
            and target.resolve(strict=True).parent == base
            and 0 < target.stat().st_size <= MAX_JSON_BYTES,
            "FIXED_UNSIGNED_REQUEST_ONLY")
    try:
        packet = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise P9Denied("CLIVOX_V2_P9_DENIED_UNSIGNED_PACKET_FORMAT") from None
    require(type(packet) is dict, "UNSIGNED_PACKET_OBJECT")
    return packet


def validate_review_bridge(*, scratch: Path) -> dict:
    """Rehash exact ephemeral P7 bytes; P8 unsigned packet must still match."""
    _closed_live_policies()
    video_sha, video_bytes = _hash_exact_synthetic_mp4(scratch)
    edl = _read_ephemeral(scratch, EDL_FILE)
    qa = _read_ephemeral(scratch, QA_FILE)
    packet = _read_unsigned(scratch)
    try:
        validated = validate_unsigned_packet(
            packet, video_sha=video_sha, video_bytes=video_bytes,
            edl=edl, p7_report=qa)
    except (P8Denied, P5Denied, TypeError, ValueError, KeyError):
        raise P9Denied("CLIVOX_V2_P9_DENIED_UNSIGNED_REVIEW_BINDING") from None
    require(validated["channel_id"] == CHANNEL
            and validated["owner_release_signed"] is False
            and validated["human_owner_identity_verified"] is False
            and validated["detached_signature_base64"] is None
            and validated["source_rights_evidence_sha256"] is None
            and validated["youtube_upload_authorized"] is False
            and validated["publish_at_utc"] is None,
            "UNSIGNED_NEVER_RELEASE")
    # Fixed packet is a test-only review REQUEST, not an approved release.
    require(_hash_exact_synthetic_mp4(scratch) == (video_sha, video_bytes),
            "EXACT_VIDEO_CHANGED_AFTER_BRIDGE")
    return packet


def synthetic_attempt_fingerprint(packet: dict) -> str:
    """No third-party rights evidence: deliberately NOT the A8 live attempt key."""
    require(type(packet) is dict and
            packet.get("review_state") == "UNSIGNED_QUARANTINED_TEST_ONLY"
            and packet.get("channel_id") == CHANNEL
            and packet.get("owner_release_signed") is False
            and packet.get("youtube_upload_authorized") is False,
            "SYNTHETIC_UNSIGNED_SUBJECT")
    for field in (
        "exact_synthetic_video_sha256",
        "exact_p6_storyboard_sha256",
        "exact_p7_qa_report_sha256",
    ):
        require(type(packet.get(field)) is str
                and ID.fullmatch(packet[field]) is not None,
                "EXACT_DIGEST_" + field.upper())
    message = {
        "channel_id": CHANNEL,
        "original_source_scope": "LAVFI_GENERATED_ONLY",
        "video_sha256": packet["exact_synthetic_video_sha256"],
        "edl_sha256": packet["exact_p6_storyboard_sha256"],
        "qa_sha256": packet["exact_p7_qa_report_sha256"],
    }
    return hashlib.sha256(DOMAIN + canonical(message)).hexdigest()


def dryrun_decision(*, packet: dict, outcome: str) -> dict:
    """Exercise A8 existing preview & recovery. Every outcome is a HOLD."""
    require(type(outcome) is str and outcome in OUTCOMES,
            "KNOWN_DRYRUN_OUTCOME")
    attempt = synthetic_attempt_fingerprint(packet)
    existing = []
    if outcome == "DUPLICATE_LOCAL_PREVIEW":
        existing = [{"key": attempt, "status": "ATTEMPT_RESERVED"}]
    elif outcome == "UNKNOWN_REMOTE_COMMIT_PREVIEW":
        existing = [{"key": attempt, "status": "UNKNOWN_REMOTE_STATE_RECONCILE"}]
    preview = reserve_attempt_preview(existing, attempt)
    require(preview["upload_authorized"] is False
            and preview["automatic_retry_allowed"] is False,
            "A8_DUPLICATE_PREVIEW_CANNOT_AUTHORIZE")
    duplicate = outcome != "NO_ATTEMPT"
    require(preview["decision"] ==
            ("BLOCK_DUPLICATE_OR_AMBIGUOUS_ATTEMPT" if duplicate
             else "DRY_RUN_ONLY_KEY_NOT_PRESENT"),
            "A8_PREVIEW_UNEXPECTED_DECISION")
    unknown = outcome == "UNKNOWN_REMOTE_COMMIT_PREVIEW"
    if unknown:
        hold = reconcile_ambiguous_attempt(
            attempt_status="UNKNOWN_REMOTE_STATE_RECONCILE",
            remote_readback_verified=False)
        require(hold["blind_retry_allowed"] is False
                and hold["upload_authorized"] is False
                and hold["remote_readback_assertion_is_not_proof"] is True,
                "A8_AMBIGUITY_NEVER_APPROVES")
    return {
        "stage": STAGE, "channel_id": CHANNEL,
        "source_scope": "SYNTHETIC_ONLY_NOT_CREATOR_MEDIA",
        "p8_unsigned_packet_bound_to_exact_video": True,
        "owner_signature_independently_verified": False,
        "creator_commercial_rights_verified": False,
        "clivox_upload_oauth_verified": False,
        "durable_atomic_attempt_reservation_verified": False,
        "real_remote_inventory_reconciled": False,
        "inert_private_first_template_validated": True,
        "automatic_retry_enabled": False,
        "resume_session_created": False,
        "remote_http_calls": 0,
        "actual_youtube_uploads": 0,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "dryrun_outcome": outcome,
        "dryrun_duplicate_detected": duplicate,
        "dryrun_remote_uncertainty_quarantined": unknown,
        "real_p9_milestone_complete": False,
        "status": "HOLD_NO_OWNER_LICENSE_OAUTH_DURABLE_LEDGER_OR_REMOTE_READBACK",
    }


def run_source_free_preflight(*, scratch: Path) -> dict:
    """Real files and existing control policies checked; NO transport used."""
    _closed_live_policies()
    packet = validate_review_bridge(scratch=scratch)
    validate_inert_template(TEMPLATE)
    result = dryrun_decision(packet=packet, outcome="NO_ATTEMPT")
    require(type(result) is dict and set(result) == PUBLIC_REPORT_FIELDS,
            "PUBLIC_REPORT_SCHEMA")
    require(_hash_exact_synthetic_mp4(scratch)[0] ==
            packet["exact_synthetic_video_sha256"], "MEDIA_CHANGED")
    _closed_live_policies()
    return result


def production_upload_or_schedule(*_args, **_kwargs) -> None:
    """No caller can turn this prototype into a YouTube write."""
    raise P9Denied("CLIVOX_V2_P9_DENIED_NO_LIVE_UPLOAD_CONTROLLER")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "synthetic"), default="closed")
    parser.add_argument("--scratch", type=Path)
    args = parser.parse_args()
    try:
        _closed_live_policies()
        if args.mode == "closed":
            require(args.scratch is None, "CLOSED_NO_MEDIA_ARGS")
            output = {
                "stage": "CLIVOX_V2_P9_CLOSED_NO_YOUTUBE_WRITES",
                "channel_id": CHANNEL,
                "owner_signature_independently_verified": False,
                "creator_commercial_rights_verified": False,
                "youtube_upload_authorized": False,
                "youtube_schedule_authorized": False,
                "youtube_publish_authorized": False,
                "actual_youtube_uploads": 0,
            }
        else:
            require(args.scratch is not None, "ONLY_EPHEMERAL_SYNTHETIC_SCRATCH")
            output = run_source_free_preflight(scratch=args.scratch)
        print(json.dumps(output, sort_keys=True))
    except (P9Denied, P8Denied, P5Denied, ReleaseBlocked,
            DryRunBlocked, PrivateCASBlocked, ChannelBindingDenied,
            ValueError, TypeError, KeyError, OSError, UnicodeError):
        raise SystemExit(
            "CLIVOX_V2_P9_BLOCKED_NO_CREATOR_LICENSE_OWNER_RELEASE_OR_GOOGLE_WRITE"
        ) from None


if __name__ == "__main__":
    main()
