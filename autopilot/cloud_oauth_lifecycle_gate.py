"""Phase 5B: cloud OAuth lifecycle risk screening from sanitized CLAIMS ONLY.

No token acquisition, refresh, YouTube calls, cloud provider connection,
secret resolution, uploads, publishing, or scheduling. Caller-supplied claims
NEVER constitute trusted provider proof or enable unattended publishing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
import re

CHANNEL_ID = "UCCcL9Q_jqVq6LJmnYUSAFZA"
READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
ALLOWED_SCOPES = frozenset({READONLY_SCOPE, UPLOAD_SCOPE})
FIELDS = frozenset({
    "channel_id", "oauth_app_mode", "token_kind", "access_expiry_utc",
    "refresh_observed_utc", "channel_observed_utc", "secret_store_kind",
    "scope_set", "owner_connection_approved", "refresh_observation_success",
    "channel_observation_success", "durable_private_storage_confirmed",
    "isolated_cloud_runtime_confirmed", "zero_overage_enforced",
})
_DENIED_KEY_FRAGMENT = re.compile(
    r"token(?!_kind)|secret(?!_store_kind)|password|authorization|private.key|"
    r"credential|cookie|bearer|client_id|session_uri", re.I
)


class OAuthScreenError(ValueError):
    """Safe error with no account or token content."""


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value
    ):
        raise OAuthScreenError("MALFORMED_UTC_OBSERVATION")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise OAuthScreenError("MALFORMED_UTC_OBSERVATION") from exc


def _check_shape(claim: Mapping[str, Any]) -> None:
    if not isinstance(claim, Mapping):
        raise OAuthScreenError("OBSERVATION_NOT_MAPPING")
    if set(claim) != FIELDS or any(not isinstance(k, str) for k in claim):
        raise OAuthScreenError("UNEXPECTED_OR_MISSING_OBSERVATION_FIELDS")
    if any(_DENIED_KEY_FRAGMENT.search(k) for k in claim):
        raise OAuthScreenError("FORBIDDEN_CREDENTIAL_FIELD")
    for key in ("owner_connection_approved", "refresh_observation_success",
                "channel_observation_success", "durable_private_storage_confirmed",
                "isolated_cloud_runtime_confirmed", "zero_overage_enforced"):
        if type(claim[key]) is not bool:
            raise OAuthScreenError("INVALID_BOOLEAN_OBSERVATION")
    if not isinstance(claim["scope_set"], list) or len(claim["scope_set"]) != len(set(
        x for x in claim["scope_set"] if isinstance(x, str)
    )):
        raise OAuthScreenError("INVALID_SCOPE_OBSERVATION")
    if any(not isinstance(s, str) or s not in ALLOWED_SCOPES for s in claim["scope_set"]):
        raise OAuthScreenError("INVALID_SCOPE_OBSERVATION")
    for key in ("channel_id", "oauth_app_mode", "token_kind", "secret_store_kind"):
        if not isinstance(claim[key], str) or len(claim[key]) > 128:
            raise OAuthScreenError("INVALID_OBSERVATION_ENUM")


def screen_claims(
    claim: Mapping[str, Any], *, purpose: str,
    now: datetime | None = None,
) -> dict:
    """Explain why a proposed cloud authorization is not safe to deploy.

    "ELIGIBLE_FOR_LIVE_READONLY_PROBE" is a *proposal*, not verified live
    eligibility. Nothing here can set publish_authorized True.
    """
    _check_shape(claim)
    if purpose not in ("read_only", "private_upload_pilot"):
        raise OAuthScreenError("UNKNOWN_PURPOSE")
    now = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise OAuthScreenError("TRUSTED_AWARE_CLOCK_REQUIRED")
    now = now.astimezone(timezone.utc)
    access_expiry = _utc(claim["access_expiry_utc"])
    refresh_observed = _utc(claim["refresh_observed_utc"])
    channel_observed = _utc(claim["channel_observed_utc"])
    reasons = []
    if claim["channel_id"] != CHANNEL_ID:
        reasons.append("WRONG_CHANNEL")
    if claim["token_kind"] != "user_oauth":
        reasons.append("NOT_OWNER_DELEGATED_OAUTH")
    if claim["oauth_app_mode"] != "production":
        reasons.append("OAUTH_TEST_MODE_OR_UNKNOWN_REFRESH_LIFETIME")
    if claim["secret_store_kind"] != "provider_managed_encrypted":
        reasons.append("PROTECTED_CLOUD_SECRET_STORE_UNVERIFIED")
    if not claim["owner_connection_approved"]:
        reasons.append("OWNER_CONNECTION_NOT_APPROVED")
    if not claim["isolated_cloud_runtime_confirmed"]:
        reasons.append("LAPTOP_INDEPENDENT_ISOLATION_UNVERIFIED")
    if not claim["durable_private_storage_confirmed"]:
        reasons.append("PRIVATE_MEDIA_STORAGE_UNVERIFIED")
    if not claim["zero_overage_enforced"]:
        reasons.append("ZERO_BUDGET_HARD_CAP_UNVERIFIED")
    if not claim["refresh_observation_success"]:
        reasons.append("OAUTH_REFRESH_HEALTH_UNVERIFIED")
    if not claim["channel_observation_success"]:
        reasons.append("CHANNEL_OWNER_LOOKUP_UNVERIFIED")
    if access_expiry <= now + timedelta(minutes=20):
        reasons.append("ACCESS_TOKEN_TOO_OLD_FOR_OPERATION")
    if refresh_observed > now or refresh_observed < now - timedelta(hours=24):
        reasons.append("REFRESH_OBSERVATION_OUTDATED_OR_FUTURE")
    if channel_observed > now or channel_observed < now - timedelta(hours=24):
        reasons.append("CHANNEL_OBSERVATION_OUTDATED_OR_FUTURE")
    required = READONLY_SCOPE if purpose == "read_only" else UPLOAD_SCOPE
    if required not in claim["scope_set"]:
        reasons.append("PURPOSE_SCOPE_MISSING")
    # Even an internally consistent assertion has no verified provenance:
    # provider collectors, durable grants, revocation checks and proof of an
    # authorized channel-specific OAuth session are OUTSIDE this module.
    reasons = tuple(dict.fromkeys(reasons))
    return {
        "purpose": purpose,
        "channel_id": CHANNEL_ID,
        "status": "ELIGIBLE_FOR_LIVE_READONLY_PROBE" if not reasons and purpose == "read_only"
                  else "ELIGIBLE_FOR_OWNER_APPROVED_PRIVATE_PILOT_REVIEW" if not reasons
                  else "BLOCKED",
        "claim_screen_pass": not reasons,
        "reasons": list(reasons),
        "mandatory_external_evidence": [
            "PROVIDER_AUTHENTICATED_TOKEN_AND_CHANNEL_READBACK",
            "OWNER_APPROVED_CLOUD_CONNECTION_AND_SECRET_PROVENANCE",
            "DURABLE_SINGLE_WRITER_RELEASE_STATE_AND_MEDIA_RIGHTS_QA",
            "PROVEN_HARD_ZERO_OVERAGE_COST_CEILING",
        ],
        "actual_provider_authenticated": False,
        "unattended_upload_authorized": False,
        "unattended_scheduling_authorized": False,
        "cloud_autopilot_ready": False,
        "secret_values_in_report": False,
        "source_trust": "UNTRUSTED_CALLER_SUPPLIED_SANITIZED_CLAIMS",
    }
