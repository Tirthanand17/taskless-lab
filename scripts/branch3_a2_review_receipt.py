"""Clivox A2: signed reviewer receipt and revocation verification PREVIEW.

No real reviewer key is enrolled. No grant is authenticated by this script.
The only executable CLI validates unapproved A1->A2 cases and zero-license
policy. Mathematical Ed25519 checks are for offline tests and future
owner-reviewed integration; passing them NEVER authorizes media or YouTube.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re

from scripts.branch3_rights_case_intake import (
    build_rights_cases, PENDING_CHECKS, CLIVOX_ID
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "branch3/rights_review/review-policy.json"
REGISTRY = ROOT / "branch3/creator_permissions.json"
SHA = re.compile(r"[a-f0-9]{64}\Z")
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
KEY_ID = re.compile(r"[a-z][a-z0-9_-]{4,55}\Z")
B64 = re.compile(r"[A-Za-z0-9+/]+={0,2}\Z")
RECEIPT_FIELDS = frozenset({
    "schema_version", "channel_id", "case_id", "case_sha256",
    "source_channel_id", "source_video_id", "receipt_id",
    "reviewer_key_id", "creator_grant_evidence_sha256",
    "review_outcome", "reviewed_at_utc", "expires_at_utc",
    "source_is_synthetic", "required_human_checks"
})
REVOKE_FIELDS = frozenset({
    "schema_version", "channel_id", "case_sha256", "receipt_id",
    "revocation_sequence", "revoked_at_utc", "reason_code"
})
REVIEW_DOMAIN = b"CLIVOX-A2-HUMAN-REVIEW-PREVIEW-V1\n"
REVOKE_DOMAIN = b"CLIVOX-A2-REVOKE-PREVIEW-V1\n"
REASONS = frozenset({
    "CREATOR_WITHDREW_PERMISSION", "SCOPE_INCORRECT", "EXPIRED_GRANT",
    "EVIDENCE_DISPUTED", "EMBEDDED_RIGHTS_NOT_CLEARED", "OWNER_HOLD"
})
OUTCOME = "CONDITIONAL_REVIEW_CLAIM_NOT_LICENSE"


class ReviewDenied(ValueError):
    """Any bad provenance, signature, expiry or revocation fails closed."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ReviewDenied("CLIVOX_A2_REVIEW_DENIED_" + code)


def canonical(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(data: dict) -> str:
    return hashlib.sha256(canonical(data)).hexdigest()


def parse_utc(value: object) -> datetime:
    require(type(value) is str
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is not None,
            "EXACT_UTC_SECONDS")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ReviewDenied("CLIVOX_A2_REVIEW_DENIED_INVALID_UTC_DATE") from None


def verify_pending_case(case: dict) -> str:
    """Case is NOT rights verified; never convert it into approved registry."""
    require(type(case) is dict
            and case.get("channel_id") == CLIVOX_ID
            and case.get("case_state") == "AWAITING_REAL_RIGHTS_HOLDER_VERIFICATION",
            "CASE_NOT_PENDING_CLIVOX")
    video = case.get("source_video_id")
    require(type(video) is str and VIDEO_ID.fullmatch(video) is not None
            and case.get("case_id") == "clivox_rights_" + video
            and case.get("source_url") == "https://www.youtube.com/watch?v=" + video,
            "SOURCE_IDENTITY")
    require(type(case.get("source_channel_id")) is str
            and re.fullmatch(r"UC[A-Za-z0-9_-]{22}", case["source_channel_id"]) is not None,
            "SOURCE_CHANNEL")
    require(type(case.get("case_is_synthetic")) is bool,
            "SYNTHETIC_MARKER")
    checks = case.get("required_checks")
    require(type(checks) is dict and set(checks) == set(PENDING_CHECKS)
            and all(v == "PENDING_HUMAN_VERIFICATION" for v in checks.values()),
            "FAKE_HUMAN_REVIEW")
    for field in (
        "human_rights_reviewer_assigned", "actual_grant_document_available",
        "verified_creator_published_policy", "creator_permissions_registry_updated",
        "contract_acceptance_done", "contract_assignment_reviewed_by_owner",
        "media_acquisition_authorized", "edit_authorized",
        "owner_clip_release_signed", "youtube_upload_authorized",
        "youtube_publish_authorized"
    ):
        require(case.get(field) is False, "PREMATURE_CASE_FLAG_" + field)
    for field in ("permission_evidence_reference", "permission_evidence_sha256",
                  "license_expiry_utc"):
        require(case.get(field) is None, "PREMATURE_EVIDENCE_" + field)
    return digest(case)


def review_subject(case: dict, receipt: dict) -> bytes:
    """Bind a human-review CLAIM to the exact pending case, never issue a grant."""
    case_hash = verify_pending_case(case)
    require(type(receipt) is dict and set(receipt) == RECEIPT_FIELDS,
            "REVIEW_FIELDS")
    require(receipt["schema_version"] == 1
            and receipt["channel_id"] == CLIVOX_ID
            and receipt["case_id"] == case["case_id"]
            and receipt["case_sha256"] == case_hash
            and receipt["source_channel_id"] == case["source_channel_id"]
            and receipt["source_video_id"] == case["source_video_id"]
            and receipt["source_is_synthetic"] is case["case_is_synthetic"],
            "CASE_BINDING")
    require(receipt["review_outcome"] == OUTCOME, "INVALID_REVIEW_OUTCOME")
    require(type(receipt["receipt_id"]) is str
            and re.fullmatch(r"clivox_review_[a-z0-9_-]{10,75}", receipt["receipt_id"]) is not None,
            "RECEIPT_ID")
    require(type(receipt["reviewer_key_id"]) is str
            and KEY_ID.fullmatch(receipt["reviewer_key_id"]) is not None,
            "REVIEWER_KEY_ID")
    require(type(receipt["creator_grant_evidence_sha256"]) is str
            and SHA.fullmatch(receipt["creator_grant_evidence_sha256"]) is not None,
            "EVIDENCE_DIGEST")
    checks = receipt["required_human_checks"]
    require(type(checks) is dict and set(checks) == set(PENDING_CHECKS)
            and all(value == "REVIEWER_CLAIMS_COMPLETED_NOT_AUTHENTICATED"
                    for value in checks.values()), "HUMAN_CHECKS_NOT_BOUND")
    issued, expiry = parse_utc(receipt["reviewed_at_utc"]), parse_utc(receipt["expires_at_utc"])
    require(issued < expiry and expiry - issued <= timedelta(days=90),
            "REVIEW_TIME_RANGE")
    return REVIEW_DOMAIN + canonical(receipt)


def revocation_subject(receipt: dict, event: dict) -> bytes:
    """Bind explicit revocation to one exact reviewer receipt and sequence."""
    require(type(receipt) is dict and set(receipt) == RECEIPT_FIELDS,
            "RECEIPT_REQUIRED")
    require(type(event) is dict and set(event) == REVOKE_FIELDS,
            "REVOCATION_FIELDS")
    require(event["schema_version"] == 1
            and event["channel_id"] == CLIVOX_ID
            and event["case_sha256"] == receipt["case_sha256"]
            and event["receipt_id"] == receipt["receipt_id"], "REVOCATION_TARGET")
    require(type(event["revocation_sequence"]) is int
            and 1 <= event["revocation_sequence"] <= 1_000_000,
            "REVOCATION_SEQUENCE")
    require(event["reason_code"] in REASONS, "REVOCATION_REASON")
    parse_utc(event["revoked_at_utc"])
    return REVOKE_DOMAIN + canonical(event)


def verify_ed25519(payload: bytes, signature_b64: str,
                   trusted_key_raw: bytes, domain: bytes) -> bool:
    """Mathematical verification. Caller MUST independently enroll trust keys."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    require(type(payload) is bytes and payload.startswith(domain),
            "WRONG_SIGNING_DOMAIN")
    require(type(signature_b64) is str and len(signature_b64) <= 120
            and B64.fullmatch(signature_b64) is not None,
            "INVALID_SIGNATURE_ENCODING")
    require(type(trusted_key_raw) is bytes and len(trusted_key_raw) == 32,
            "MISSING_TRUSTED_PUBLIC_KEY")
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        require(len(signature) == 64, "SIGNATURE_LENGTH")
        Ed25519PublicKey.from_public_bytes(trusted_key_raw).verify(signature, payload)
        return True
    except (InvalidSignature, ValueError, binascii.Error):
        return False


def verify_offline_receipt_preview(
    *, case: dict, receipt: dict, signature_b64: str, reviewer_public_key: bytes,
    revocations: list[dict], revocation_public_key: bytes,
    now: datetime, last_trusted_revocation_sequence: int
) -> dict:
    """Tests key math, exact source and revocation events; NEVER authorizes use.

    Ledger freshness/completeness and public-key *identity* cannot be inferred
    from caller arguments: a real independently signed monotonic checkpoint
    and key enrollment remain missing.
    """
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "NAIVE_CLOCK")
    require(type(last_trusted_revocation_sequence) is int
            and last_trusted_revocation_sequence >= 0, "CHECKPOINT_SEQUENCE")
    signed = review_subject(case, receipt)
    require(verify_ed25519(signed, signature_b64, reviewer_public_key,
                           REVIEW_DOMAIN), "REVIEWER_SIGNATURE")
    now_utc = now.astimezone(timezone.utc)
    require(parse_utc(receipt["reviewed_at_utc"]) <= now_utc
            < parse_utc(receipt["expires_at_utc"]), "RECEIPT_EXPIRED_OR_FUTURE")
    require(type(revocations) is list and len(revocations) <= 200,
            "REVOCATION_LIST")
    sequence_set = set()
    observed_sequence = 0
    revoked = False
    for record in revocations:
        require(type(record) is dict and set(record) == {"event", "signature_base64"},
                "REVOCATION_RECORD_FIELDS")
        event = record["event"]
        payload = revocation_subject(receipt, event)
        require(verify_ed25519(payload, record["signature_base64"],
                               revocation_public_key, REVOKE_DOMAIN),
                "REVOCATION_SIGNATURE")
        n = event["revocation_sequence"]
        require(n not in sequence_set and n > observed_sequence,
                "REVOCATION_REPLAY_OR_DISORDER")
        sequence_set.add(n)
        observed_sequence = n
        require(parse_utc(event["revoked_at_utc"]) <= now_utc,
                "FUTURE_REVOCATION")
        revoked = True  # Every event for this receipt is a tombstone.
    # An unsigned/missing ledger cannot prove a receipt remains unrevoked.
    # An external lower bound is a test input, NOT a durable/verified checkpoint.
    require(observed_sequence >= last_trusted_revocation_sequence,
            "REVOCATION_ROLLBACK")
    require(not revoked, "RECEIPT_REVOKED")
    return {
        "stage": "A2_SIGNATURE_AND_REVOCATION_MATH_PREVIEW_ONLY",
        "channel_id": CLIVOX_ID,
        "review_signature_math_passed": True,
        "signed_receipt_case_sha256_matched": True,
        "revocation_events_supplied": len(revocations),
        "last_supplied_sequence_checked": last_trusted_revocation_sequence,
        "reviewer_identity_independently_enrolled": False,
        "complete_remote_revocation_ledger_verified": False,
        "durable_anti_rollback_checkpoint_verified": False,
        "creator_license_authenticity_verified": False,
        "media_acquisition_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
    }


def validate_closed_policy(policy: dict, registry: dict) -> None:
    require(type(policy) is dict and set(policy) == {
        "schema_version", "channel_id", "phase", "real_human_reviewer_key_enrolled",
        "real_revocation_authority_key_enrolled", "durable_revocation_ledger",
        "latest_trusted_revocation_sequence", "real_authentic_creator_grants",
        "real_human_reviews_completed", "actual_contract_storage_approved",
        "human_review_not_creator_license", "creator_registry_auto_promotion_enabled",
        "source_media_download_enabled", "youtube_write_enabled", "status"
    }, "POLICY_FIELDS")
    require(policy["schema_version"] == 1
            and policy["channel_id"] == CLIVOX_ID
            and policy["phase"] == "A2_SIGNED_REVIEW_PREVIEW_ONLY"
            and policy["status"] == "OFFLINE_TESTS_WITHOUT_PRODUCTION_TRUST",
            "POLICY_IDENTITY")
    require(policy["real_authentic_creator_grants"] == 0
            and policy["real_human_reviews_completed"] == 0
            and policy["latest_trusted_revocation_sequence"] is None
            and policy["human_review_not_creator_license"] is True,
            "CLAIMED_AUTHORITY")
    for key in (
        "real_human_reviewer_key_enrolled",
        "real_revocation_authority_key_enrolled",
        "durable_revocation_ledger", "actual_contract_storage_approved",
        "creator_registry_auto_promotion_enabled",
        "source_media_download_enabled", "youtube_write_enabled"
    ):
        require(policy[key] is False, "PREMATURE_ENABLE_" + key)
    require(type(registry) is dict and registry.get("schema_version") == 1
            and registry.get("policy") == "EXPLICIT_CREATOR_GRANT_ONLY"
            and registry.get("creators") == [], "REAL_REGISTRY_MUST_REMAIN_EMPTY")


def audit_pending_handoff(discovery: dict, rights_cases: dict,
                          policy: dict, registry: dict) -> dict:
    validate_closed_policy(policy, registry)
    require(type(rights_cases) is dict
            and type(rights_cases.get("generated_at_utc")) is str,
            "RIGHTS_INTAKE_REPORT")
    expected = build_rights_cases(
        discovery, generated_at_utc=rights_cases["generated_at_utc"]
    )
    require(rights_cases == expected, "A1_A2_REPORT_MISMATCH")
    for case in rights_cases["cases"]:
        verify_pending_case(case)
    return {
        "stage": "A2_PENDING_REVIEW_HUMAN_PROOF_AND_REVOCATION_GATES",
        "channel_id": CLIVOX_ID,
        "status": "QUARANTINED_NO_AUTHENTICATED_GRANTS_OR_REVIEWER_KEYS",
        "synthetic_fixture": rights_cases["is_synthetic_fixture"],
        "pending_review_cases": len(rights_cases["cases"]),
        "a1_report_sha256": rights_cases["source_report_sha256"],
        "cryptographic_preview_only": True,
        "actual_signed_human_review_receipts": 0,
        "authentic_creator_grants": 0,
        "durable_revocation_ledger_present": False,
        "live_owner_reviewed_keys_enrolled": False,
        "creator_registry_modified": False,
        "source_media_downloads": 0,
        "youtube_api_writes": 0,
        "source_media_acquisition_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "note": "A1->A2 cases still pending. Signatures in tests never establish legal rights."
    }


def read_json(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size < 350_000,
            "PUBLIC_INPUT_LOCATION_OR_SIZE")
    result = json.loads(path.read_text("utf-8"))
    require(type(result) is dict, "INPUT_NOT_OBJECT")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--discovery", type=Path, required=True)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        out = args.out.absolute()
        require(out.name == "a2-rights-quarantine-report.json"
                and ROOT not in out.parents and not out.is_symlink(),
                "PUBLIC_OUTPUT_NOT_ALLOWED")
        report = audit_pending_handoff(
            read_json(args.discovery), read_json(args.cases),
            read_json(POLICY), read_json(REGISTRY)
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", "utf-8")
    except (ReviewDenied, ValueError, OSError, TypeError, KeyError):
        raise SystemExit("CLIVOX_A2_REVIEW_QUARANTINED_NO_MEDIA_NO_YOUTUBE") from None
    print("CLIVOX_A2_SIGNED_REVIEW_PREVIEW_NO_REAL_RIGHTS_NO_MEDIA_NO_YOUTUBE")


if __name__ == "__main__":
    main()
